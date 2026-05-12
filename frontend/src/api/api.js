const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

function buildUrl(path) {
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path
}

async function fetchJson(path, options) {
  const response = await fetch(buildUrl(path), options)
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = payload.message || payload.detail || `Request failed with status ${response.status}`
    throw new Error(message)
  }

  return payload
}

export const healthAPI = {
  getStatus: async () => fetchJson('/api/health')
}

export const kpiAPI = {
  getSummary: async (brand = '', region = '') => {
    const params = new URLSearchParams()
    if (brand) params.append('brand', brand)
    if (region) params.append('region', region)
    const suffix = params.toString() ? `?${params.toString()}` : ''
    return fetchJson(`/api/kpi-summary${suffix}`)
  }
}

export const dashboardAPI = {
  getData: async (brand = '', region = '') => {
    const params = new URLSearchParams()
    if (brand) params.append('brand', brand)
    if (region) params.append('region', region)
    const suffix = params.toString() ? `?${params.toString()}` : ''
    return fetchJson(`/api/dashboard-data${suffix}`)
  }
}

export const pipelineAPI = {
  run: async () => fetchJson('/run', { method: 'POST' }),
  getStatus: async () => fetchJson('/api/pipeline-status'),
  getLogs: async () => fetchJson('/api/pipeline-logs')
}

export const reportsAPI = {
  list: async () => fetchJson('/api/reports'),
  get: async (filename) => fetchJson(`/api/report/${encodeURIComponent(filename)}`),
  rate: async (filename, rating) => fetchJson('/api/rate-report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, rating })
  })
}

export const modelAPI = {
  getInfo: async () => fetchJson('/api/model-info')
}
