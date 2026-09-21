/**
 * API client — thin fetch wrapper for talking to FastAPI.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

// ---- Public API ---------------------------------------------------

export async function postSummarize() {
  return request('/summarize', { method: 'POST' });
}

export async function getDashboard() {
  return request('/dashboard');
}

export async function getTasks() {
  return request('/tasks');
}

export async function patchTask(id, updates) {
  return request(`/tasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
}

export async function getMessages() {
  return request('/messages');
}

export async function getReplies() {
  return request('/replies');
}

export async function regenerateReply(id, tone) {
  return request(`/replies/${id}/regenerate`, {
    method: 'POST',
    body: JSON.stringify({ tone }),
  });
}
