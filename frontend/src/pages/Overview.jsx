import { useOutletContext } from "react-router-dom"

function Overview() {
  const { health, dashboard, modelInfo } = useOutletContext()
  const cards = dashboard?.kpi_cards || []

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div key={card.key} className="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{card.label}</p>
            <p className="mt-3 font-headline text-3xl font-bold text-white">{card.display_value}</p>
            <p className={`mt-2 text-sm ${card.status === "missing" ? "text-amber-300" : "text-slate-400"}`}>{card.description}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-blue-500/15 to-violet-500/10 p-6">
          <p className="text-xs uppercase tracking-[0.22em] text-blue-200">Strategic Snapshot</p>
          <div className="mt-4 space-y-4 text-sm text-slate-200">
            {(dashboard?.insights || []).slice(0, 3).map((item, index) => (
              <p key={index}>{item}</p>
            ))}
          </div>
        </div>
        <div className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
          <p className="text-xs uppercase tracking-[0.22em] text-slate-400">System State</p>
          <dl className="mt-4 space-y-4 text-sm text-slate-300">
            <div className="flex justify-between gap-4">
              <dt>Health</dt>
              <dd>{health?.status || "unknown"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt>Latest Report</dt>
              <dd className="truncate text-right">{health?.latest_report || "None"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt>Primary Model</dt>
              <dd>{modelInfo?.primary_model?.name || "N/A"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt>Fallback Provider</dt>
              <dd>{modelInfo?.backup_provider?.name || "N/A"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt>Mock Mode</dt>
              <dd>{modelInfo?.router?.mock_mode ? "Enabled" : "Disabled"}</dd>
            </div>
          </dl>
        </div>
      </section>
    </div>
  )
}

export default Overview
