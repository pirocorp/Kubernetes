import http from 'node:http';
import pg from 'pg';

if(!process.env.DATABASE_URL) throw new Error('DATABASE_URL must be configured');
const {Pool}=pg;
const pool=new Pool({
  connectionString:process.env.DATABASE_URL,
  max:5,connectionTimeoutMillis:3500,idleTimeoutMillis:10000
});
pool.on('error',error=>console.error('PostgreSQL connection error',error.message));
const port=Number(process.env.PORT||8080);
function json(res,status,value) {
  res.writeHead(status,{'content-type':'application/json; charset=utf-8',
    'cache-control':'no-store','x-content-type-options':'nosniff'});
  res.end(JSON.stringify(value));
}
const server=http.createServer(async(req,res)=>{
  const path=new URL(req.url,'http://localhost').pathname;
  if(req.method==='GET' && path==='/healthz'){
    res.writeHead(200,{'content-type':'text/plain'});return res.end('ok');
  }
  if(req.method==='GET' && path==='/readyz'){
    try {await pool.query('SELECT 1');res.writeHead(200,{'content-type':'text/plain'});return res.end('ready');}
    catch {return json(res,503,{code:'database_unavailable'});}
  }
  const match=path.match(/^\/r\/([A-Za-z0-9_-]{7,12})$/);
  if(req.method==='GET' && match) {
    try {
      const result=await pool.query('SELECT target_url FROM short_links WHERE code=$1',[match[1]]);
      if(!result.rows.length) return json(res,404,{code:'unknown_short_code'});
      const target=result.rows[0].target_url;
      if(!/^https?:\/\//i.test(target)) return json(res,502,{code:'unsafe_target'});
      res.writeHead(302,{'location':target,'cache-control':'no-store'});
      return res.end();
    }catch(error){console.error('Resolve failed',error.message);return json(res,503,{code:'database_unavailable'});}
  }
  return json(res,404,{code:'not_found'});
});
server.listen(port,'0.0.0.0',()=>console.log('Redirector listening on',port));
process.on('SIGTERM',()=>server.close(()=>pool.end()));
