const BASE_URL = 'http://localhost:8000'

export const kpiAPI = {
  getSummary: async (brand = '', region = '') => {
    const params = new URLSearchParams()
    if (brand) params.append('brand', brand)
    if (region) params.append('region', region)
    const res = await fetch(`${BASE_URL}/api/kpi-summary?${params}`)
    return res.json()
  }
}

export const dashboardAPI = {
  getData: async (brand = '', region = '') => {
    const params = new URLSearchParams()
    if (brand) params.append('brand', brand)
    if (region) params.append('region', region)
    const res = await fetch(`${BASE_URL}/api/dashboard-data?${params}`)
    return res.json()
  }
}

export const pipelineAPI = {
  run: async () => {
    const res = await fetch(`${BASE_URL}/run`, { method: 'POST' })
    return res.json()
  },
  getStatus: async () => {
    const res = await fetch(`${BASE_URL}/api/pipeline-status`)
    return res.json()
  },
  getLogs: async () => {
    const res = await fetch(`${BASE_URL}/api/pipeline-logs`)
    return res.json()
  }
}

export const reportsAPI = {
  list: async () => {
    const res = await fetch(`${BASE_URL}/api/reports`)
    return res.json()
  },
  get: async (filename) => {
    const res = await fetch(`${BASE_URL}/api/report/${filename}`)
    return res.json()
  },
  rate: async (filename, rating) => {
    const res = await fetch(`${BASE_URL}/api/rate-report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename, rating })
    })
    return res.json()
  }
}

export const modelAPI = {
  getInfo: async () => {
    const res = await fetch(`${BASE_URL}/api/model-info`)
    return res.json()
  }
}
