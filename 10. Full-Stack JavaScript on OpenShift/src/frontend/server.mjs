import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const port = Number(process.env.PORT || 8080);
const backend = process.env.BACKEND_URL || 'http://127.0.0.1:3111';
const redirector = process.env.REDIRECTOR_URL || 'http://127.0.0.1:3112';
const root = new URL('./public/', import.meta.url);
const files = {
  '/': ['index.html', 'text/html; charset=utf-8'],
  '/app.js': ['app.js', 'text/javascript; charset=utf-8'],
  '/styles.css': ['styles.css', 'text/css; charset=utf-8']
};
function write(res, status, value, type = 'application/json; charset=utf-8') {
  const body = typeof value === 'string' ? value : JSON.stringify(value);
  res.writeHead(status, {
    'content-type': type,
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff'
  });
  res.end(body);
}
async function upstreamHealth(url, path) {
  try {
    const r = await fetch(new URL(path, url), { signal: AbortSignal.timeout(3000) });
    return r.ok;
  } catch { return false; }
}
async function readBody(req, max = 4096) {
  const chunks = []; let size = 0;
  for await (const part of req) {
    size += part.length;
    if (size > max) { const error = new Error('Request too large'); error.status = 413; throw error; }
    chunks.push(part);
  }
  return Buffer.concat(chunks).toString('utf8');
}
const server = http.createServer(async (req, res) => {
  const { pathname } = new URL(req.url, 'http://localhost');
  if (req.method === 'GET' && pathname === '/healthz') return write(res, 200, 'ok', 'text/plain');
  if (req.method === 'GET' && pathname === '/api/status') {
    const [api, database, redirects] = await Promise.all([
      upstreamHealth(backend, '/healthz'),
      upstreamHealth(backend, '/readyz'),
      upstreamHealth(redirector, '/readyz')
    ]);
    return write(res, 200, { frontend: true, backend: api, database, redirector: redirects });
  }
  if (req.method === 'GET' && Object.hasOwn(files, pathname)) {
    const [name, contentType] = files[pathname];
    try {
      const body = await readFile(new URL(name, root));
      res.writeHead(200, {'content-type': contentType, 'x-content-type-options':'nosniff'});
      return res.end(body);
    } catch { return write(res, 500, { code: 'static_content_unavailable' }); }
  }
  if (req.method === 'POST' && pathname === '/api/shorten') {
    try {
      const body = await readBody(req);
      const response = await fetch(new URL('/shorten', backend), {
        method: 'POST', headers: {'content-type': 'application/json'},
        body, redirect: 'manual', signal: AbortSignal.timeout(7000)
      });
      const text = await response.text();
      res.writeHead(response.status, {'content-type':'application/json; charset=utf-8','cache-control':'no-store'});
      return res.end(text);
    } catch (error) {
      return write(res, error.status || 502, { code: error.status ? 'payload_too_large' : 'backend_unavailable' });
    }
  }
  const match = pathname.match(/^\/r\/([A-Za-z0-9_-]{7,12})$/);
  if (req.method === 'GET' && match) {
    try {
      const response = await fetch(new URL('/r/' + match[1], redirector), {
        redirect: 'manual', signal: AbortSignal.timeout(7000)
      });
      if (response.status === 302) {
        const target = response.headers.get('location');
        if (!target || !/^https?:\/\//i.test(target)) return write(res, 502, {code:'invalid_redirect'});
        res.writeHead(302, { location: target, 'cache-control': 'no-store' });
        return res.end();
      }
      return write(res, response.status === 404 ? 404 : 502, {
        code: response.status === 404 ? 'not_found' : 'redirector_unavailable'
      });
    } catch { return write(res, 502, {code:'redirector_unavailable'}); }
  }
  return write(res, 404, {code:'not_found'});
});
server.listen(port, '0.0.0.0', () => console.log('Frontend listening on', port));
process.on('SIGTERM', () => server.close());
