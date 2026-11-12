import http from 'node:http';
import { randomBytes } from 'node:crypto';
import pg from 'pg';

if (!process.env.DATABASE_URL) throw new Error('DATABASE_URL must be configured');
const { Pool } = pg;
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 5,
  connectionTimeoutMillis: 3500,
  idleTimeoutMillis: 10000
});
pool.on('error', error => console.error('Unexpected PostgreSQL connection error', error.message));
const port = Number(process.env.PORT || 8080);

function reply(res, status, body, type = 'application/json; charset=utf-8') {
  res.writeHead(status, {
    'content-type': type, 'cache-control':'no-store', 'x-content-type-options':'nosniff'
  });
  res.end(typeof body === 'string' ? body : JSON.stringify(body));
}
async function readJson(req) {
  let length = 0; const chunks = [];
  for await (const chunk of req) {
    length += chunk.length;
    if (length > 4096) {const e=new Error('Body too large'); e.status=413; throw e;}
    chunks.push(chunk);
  }
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8')); }
  catch { const e = new Error('Invalid JSON'); e.status=400; throw e; }
}
function checkUrl(text) {
  if (typeof text !== 'string' || text.length === 0 || text.length > 2048) return null;
  try {
    const url = new URL(text);
    if (!['http:','https:'].includes(url.protocol) || url.username || url.password || !url.hostname) return null;
    return url.href;
  } catch { return null; }
}
const server = http.createServer(async (req,res) => {
  const path = new URL(req.url,'http://localhost').pathname;
  if (req.method==='GET' && path==='/healthz') return reply(res,200,'ok','text/plain');
  if (req.method==='GET' && path==='/readyz') {
    try { await pool.query('SELECT 1'); return reply(res,200,'ready','text/plain'); }
    catch { return reply(res,503,{code:'database_unavailable'}); }
  }
  if (req.method==='POST' && path==='/shorten') {
    let json;
    try {json = await readJson(req);}
    catch (e) {return reply(res,e.status||400,{code:e.status===413?'payload_too_large':'invalid_json'});}
    const target = checkUrl(json?.url);
    if (!target) return reply(res,400,{code:'invalid_url',message:'An absolute http(s) URL without credentials is required'});
    try {
      for(let attempt=0;attempt<6;attempt++) {
        const code=randomBytes(5).toString('base64url');
        const result=await pool.query(
          'INSERT INTO short_links(code,target_url) VALUES($1,$2) ON CONFLICT(code) DO NOTHING RETURNING code',
          [code,target]
        );
        if(result.rows.length) return reply(res,201,{code,path:'/r/'+code});
      }
      return reply(res,503,{code:'code_generation_retry_exhausted'});
    } catch (e) {
      console.error('Short link insert failed:',e.message);
      return reply(res,503,{code:'database_unavailable'});
    }
  }
  return reply(res,404,{code:'not_found'});
});
server.listen(port,'0.0.0.0',()=>console.log('Backend listening on',port));
process.on('SIGTERM',()=>server.close(()=>pool.end()));
