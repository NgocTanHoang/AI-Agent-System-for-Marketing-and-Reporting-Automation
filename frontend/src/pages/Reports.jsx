import { useEffect } from "react"
import { useOutletContext } from "react-router-dom"
import { api } from "../api/api"

function Reports() {
  const { reports, activeReport, setActiveReport, refresh } = useOutletContext()

  useEffect(() => {
    if (!activeReport && reports.length > 0) {
      api.report(reports[0].id).then(setActiveReport).catch(console.error)
    }
  }, [reports, activeReport, setActiveReport])

  const handleSelect = async (report) => {
    const payload = await api.report(report.id)
    setActiveReport(payload)
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.45fr_0.55fr]">
      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
        <div className="flex items-center justify-between gap-4">
          <h2 className="font-headline text-2xl font-bold text-white">Reports</h2>
          <button type="button" onClick={() => refresh()} className="rounded-2xl border border-white/10 px-4 py-2 text-sm text-slate-300">
            Refresh
          </button>
        </div>
        <div className="mt-6 space-y-3">
          {reports.map((report) => (
            <button
              type="button"
              key={report.id}
              onClick={() => handleSelect(report)}
              className={`w-full rounded-2xl border p-4 text-left ${activeReport?.id === report.id ? "border-blue-400/40 bg-blue-500/10" : "border-white/10 bg-[#0f1220]"}`}
            >
              <p className="font-semibold text-white">{report.filename}</p>
              <p className="mt-2 text-xs text-slate-400">{new Date(report.created_at).toLocaleString()} · {report.size_kb} KB</p>
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
        <h2 className="font-headline text-2xl font-bold text-white">Selected Report</h2>
        {activeReport ? (
          <article className="prose prose-invert mt-6 max-w-none whitespace-pre-wrap text-sm text-slate-200">
            {activeReport.content || "Select a report to inspect the output."}
          </article>
        ) : (
          <p className="mt-6 text-slate-400">No report selected yet.</p>
        )}
      </section>
    </div>
  )
}

export default Reports
