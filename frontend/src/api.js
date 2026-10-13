// Thin API client for the FastAPI betting backend.
const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  health: () => request('/health'),
  listPlugins: () => request('/plugins'),
  listEvents: () => request('/events'),
  createEvent: (payload) =>
    request('/events', { method: 'POST', body: JSON.stringify(payload) }),
  settleEvent: (id, outcome) =>
    request(`/events/${id}/settle`, {
      method: 'POST',
      body: JSON.stringify({ outcome }),
    }),
  listBets: (eventId) =>
    request(eventId ? `/bets?event_id=${eventId}` : '/bets'),
  placeBet: (payload) =>
    request('/bets', { method: 'POST', body: JSON.stringify(payload) }),
  getChain: () => request('/chain'),
}
