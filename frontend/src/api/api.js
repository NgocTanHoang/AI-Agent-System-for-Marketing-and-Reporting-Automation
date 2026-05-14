const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "")

function buildUrl(path) {
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path
}

async function fetchJson(path, options = {}) {
  const response = await fetch(buildUrl(path), options)
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.detail || payload.message || `Request failed: ${response.status}`)
  }

  return payload
}

export const api = {
  health: () => fetchJson("/api/health"),
  modelInfo: () => fetchJson("/api/model-info"),
  runPipeline: () => fetchJson("/api/run-pipeline", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ force: false }) }),
  pipelineStatus: () => fetchJson("/api/pipeline-status"),
  agentLogs: (runId = "") => fetchJson(`/api/agent-logs${runId ? `?run_id=${encodeURIComponent(runId)}` : ""}`),
  dashboardData: (runId = "") => fetchJson(`/api/dashboard-data${runId ? `?run_id=${encodeURIComponent(runId)}` : ""}`),
  reports: () => fetchJson("/api/reports"),
  report: (id) => fetchJson(`/api/report/${encodeURIComponent(id)}`),
}
