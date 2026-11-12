const form = document.getElementById('form');
const result = document.getElementById('result');
const health = document.getElementById('health');

async function updateStatus() {
  try {
    const response = await fetch('/api/status', { cache: 'no-store' });
    if (!response.ok) throw new Error('Unable to read status');
    const data = await response.json();
    health.textContent = Object.entries(data).map(([name, value]) =>
      name + ': ' + (value ? 'ready' : 'unavailable')).join('\n');
  } catch {
    health.textContent = 'Status unavailable';
  }
}
form.addEventListener('submit', async event => {
  event.preventDefault();
  result.textContent = 'Creating short link…';
  const button = form.querySelector('button');
  button.disabled = true;
  try {
    const response = await fetch('/api/shorten', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({url: document.getElementById('url').value})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.code || 'Unable to shorten URL');
    const link = new URL(data.path, window.location.origin).href;
    const anchor = document.createElement('a');
    anchor.href = link;
    anchor.textContent = link;
    result.replaceChildren(anchor);
  } catch (error) { result.textContent = error.message; }
  finally { button.disabled = false; updateStatus(); }
});
updateStatus();
