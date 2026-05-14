import { useOutletContext } from "react-router-dom"

function Research() {
  const { dashboard, modelInfo } = useOutletContext()

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
        <h2 className="font-headline text-2xl font-bold text-white">Market & Technology Signals</h2>
        <div className="mt-6 space-y-4">
          {(dashboard?.insights || []).filter((_, index) => index === 1 || index === 4).map((item, index) => (
            <div key={index} className="rounded-2xl border border-white/10 bg-[#0f1220] p-4 text-sm text-slate-300">
              {item}
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
        <h2 className="font-headline text-2xl font-bold text-white">Recommendations</h2>
        <div className="mt-6 space-y-4">
          {(dashboard?.recommendations || []).map((item) => (
            <div key={item.campaign_name} className="rounded-2xl border border-white/10 bg-[#0f1220] p-4">
              <p className="font-semibold text-white">{item.campaign_name}</p>
              <p className="mt-2 text-sm text-slate-300">{item.rationale}</p>
              <ul className="mt-3 space-y-1 text-sm text-slate-400">
                <li>Audience: {item.target_audience}</li>
                <li>Product: {item.product_focus}</li>
                <li>Channel: {item.channel}</li>
                <li>Budget: {item.budget_suggestion}</li>
                <li>KPI Target: {item.kpi_target}</li>
                <li>Risk: {item.risk}</li>
              </ul>
            </div>
          ))}
          <div className="rounded-2xl border border-blue-400/20 bg-blue-500/10 p-4 text-sm text-blue-100">
            DDGS Enabled: {modelInfo?.router?.mock_mode ? "Mock LLM active; research may be deterministic." : "Live routing active where credentials are available."}
          </div>
        </div>
      </section>
    </div>
  )
}

export default Research
