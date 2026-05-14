import { useEffect, useMemo, useState } from "react"
import { NavLink, Outlet } from "react-router-dom"
import { api } from "../api/api"

const NAV_ITEMS = [
  { to: "/overview", label: "Overview", icon: "◉" },
  { to: "/analytics", label: "Analytics", icon: "△" },
  { to: "/agents", label: "Agents", icon: "◎" },
  { to: "/research", label: "Research", icon: "◇" },
  { to: "/reports", label: "Reports", icon: "▣" },
]

function Layout() {
  const [health, setHealth] = useState(null)
  const [modelInfo, setModelInfo] = useState(null)
  const [status, setStatus] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [reports, setReports] = useState([])
  const [logs, setLogs] = useState([])
  const [activeReport, setActiveReport] = useState(null)
  const [busy, setBusy] = useState(false)
  const runId = status?.run_id || dashboard?.last_run?.run_id || ""

  const loadAll = async () => {
    const [healthData, modelData, statusData, dashboardData, reportData] = await Promise.all([
      api.health(),
      api.modelInfo(),
      api.pipelineStatus(),
      api.dashboardData(),
      api.reports(),
    ])
    const logData = await api.agentLogs(statusData?.run_id || dashboardData?.last_run?.run_id || "")
    setHealth(healthData)
    setModelInfo(modelData)
    setStatus(statusData)
    setDashboard(dashboardData)
    setReports(reportData.reports || [])
    setLogs(logData.logs || [])
  }

  useEffect(() => {
    loadAll().catch(console.error)
  }, [])

  useEffect(() => {
    if (!status || status.status !== "RUNNING") {
      return
    }
    const timer = setInterval(() => {
      loadAll().catch(console.error)
    }, 3000)
    return () => clearInterval(timer)
  }, [status?.status, runId])

  const runPipeline = async () => {
    setBusy(true)
    try {
      await api.runPipeline()
      await loadAll()
    } catch (error) {
      window.alert(error.message)
    } finally {
      setBusy(false)
    }
  }

  const context = useMemo(() => ({
    health,
    modelInfo,
    status,
    dashboard,
    reports,
    logs,
    activeReport,
    setActiveReport,
    refresh: loadAll,
    runPipeline,
    busy,
  }), [health, modelInfo, status, dashboard, reports, logs, activeReport, busy])

  return (
    <div className="min-h-screen bg-[#080a10] text-white">
      <div className="mx-auto flex min-h-screen max-w-[1600px]">
        <aside className="hidden w-72 border-r border-white/10 bg-white/5 p-6 backdrop-blur-xl lg:block">
          <div className="mb-10">
            <p className="font-headline text-3xl font-bold text-white">Obsidian</p>
            <p className="mt-2 text-sm text-slate-400">Intelligence System</p>
          </div>
          <nav className="space-y-3">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition ${isActive ? "bg-gradient-to-r from-blue-500/25 to-violet-500/25 text-white shadow-[0_0_20px_rgba(99,102,241,0.25)]" : "text-slate-300 hover:bg-white/5"}`
                }
              >
                <span className="text-lg">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </aside>

        <div className="flex-1">
          <header className="sticky top-0 z-20 border-b border-white/10 bg-[#080a10]/80 px-4 py-4 backdrop-blur-xl md:px-8">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h1 className="font-headline text-2xl font-bold tracking-tight text-white">Obsidian Intelligence System</h1>
                <p className="text-sm text-slate-400">AI Marketing Agent Dashboard V2.0</p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <div className="rounded-full border border-blue-400/30 bg-blue-500/10 px-4 py-2 text-xs text-blue-100">
                  Status: {status?.status || "IDLE"}
                </div>
                <button
                  type="button"
                  onClick={runPipeline}
                  disabled={busy || status?.status === "RUNNING"}
                  className="rounded-2xl bg-gradient-to-r from-blue-500 to-violet-500 px-5 py-3 text-sm font-semibold text-white shadow-[0_0_30px_rgba(79,70,229,0.35)] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {busy || status?.status === "RUNNING" ? "Pipeline Running..." : "Run Pipeline"}
                </button>
              </div>
            </div>
          </header>

          <main className="px-4 pb-28 pt-6 md:px-8">
            <Outlet context={context} />
          </main>

          <nav className="fixed bottom-0 left-0 right-0 z-30 border-t border-white/10 bg-[#080a10]/95 px-3 py-2 backdrop-blur-xl lg:hidden">
            <div className="mx-auto flex max-w-xl justify-between">
              {NAV_ITEMS.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex min-w-[64px] flex-col items-center gap-1 rounded-2xl px-3 py-2 text-[11px] ${isActive ? "text-blue-300" : "text-slate-400"}`
                  }
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          </nav>
        </div>
      </div>
    </div>
  )
}

export default Layout
