export async function api(path, opts = {}) {
  const res = await fetch('/api' + path, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    ...opts,
    body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
  });
  const data = await res.json().catch(() => ({ error: 'Phản hồi không hợp lệ từ Flask.' }));
  if (!res.ok) throw new Error(data.error || `Lỗi ${res.status}`);
  return data;
}

export const post = (path, body = {}) => api(path, { method: 'POST', body });

export const fmt = (v) => (v == null ? '—' : String(v));
