const API_BASE = '/api';

async function fetchJSON(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API Error ${res.status}: ${err}`);
  }
  return res.json();
}

export const api = {
  getStations: () => fetchJSON('/stations'),
  getStation: (id) => fetchJSON(`/stations/${id}`),
  getMetrics: () => fetchJSON('/metrics'),
  getSimulationState: () => fetchJSON('/simulation/state'),

  forecast: (body = {}) => fetchJSON('/forecast', { method: 'POST', body: JSON.stringify(body) }),

  allocate: (body) => fetchJSON('/allocate', { method: 'POST', body: JSON.stringify(body) }),

  schedule: (body) => fetchJSON('/schedule', { method: 'POST', body: JSON.stringify(body) }),

  simulatePeak: () => fetchJSON('/simulate/peak', { method: 'POST' }),
  simulateGridConstraint: () => fetchJSON('/simulate/grid-constraint', { method: 'POST' }),
  simulateOptimize: () => fetchJSON('/simulate/optimize', { method: 'POST' }),
  simulateReset: () => fetchJSON('/simulate/reset', { method: 'POST' }),
};
