import { useOutletContext } from "react-router-dom"

function Agents() {
  const { dashboard, logs, status } = useOutletContext()
  const agents = dashboard?.agent_status || status?.agent_status || []

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
        <h2 className="font-headline text-2xl font-bold text-white">Agent Status</h2>
        <div className="mt-6 space-y-4">
          {agents.map((agent) => (
            <div key={agent.name} className="rounded-2xl border border-white/10 bg-[#0f1220] p-4">
              <div className="flex items-center justify-between gap-4">
                <p className="font-semibold text-white">{agent.name}</p>
                <span className="rounded-full bg-blue-500/15 px-3 py-1 text-xs uppercase tracking-[0.2em] text-blue-200">{agent.status}</span>
              </div>
              <p className="mt-3 text-sm text-slate-300">{agent.summary || "No summary yet."}</p>
              <p className="mt-2 text-xs text-slate-500">
                Provider: {agent.provider || "n/a"} | Model: {agent.model || "n/a"} | Latency: {agent.latency_ms ?? 0} ms
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
        <h2 className="font-headline text-2xl font-bold text-white">Execution Log</h2>
        <div className="mt-6 max-h-[680px] space-y-3 overflow-auto pr-2">
          {logs.map((log, index) => (
            <div key={`${log.timestamp}-${index}`} className="rounded-2xl border border-white/10 bg-[#0f1220] p-4">
              <div className="flex items-center justify-between gap-4">
                <p className="text-sm font-semibold text-white">{log.agent_name}</p>
                <span className="text-xs text-slate-500">{new Date(log.timestamp).toLocaleString()}</span>
              </div>
              <p className="mt-2 text-sm text-slate-300">{log.message}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default Agents
