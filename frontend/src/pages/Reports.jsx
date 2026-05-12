import { useState, useEffect } from 'react'
import { reportsAPI } from '../api/api'
import GlassCard from '../components/GlassCard'
import MarkdownRenderer from '../components/MarkdownRenderer'

function Reports() {
  const [reports, setReports] = useState([])
  const [selectedReport, setSelectedReport] = useState(null)
  const [sections, setSections] = useState([])
  const [loading, setLoading] = useState(true)

  const loadReports = async () => {
    try {
      const data = await reportsAPI.list()
      if (data.reports) {
        setReports(data.reports)
      }
    } catch (e) {
      console.error('Reports error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReports()
  }, [])

  const openReport = async (filename) => {
    try {
      const data = await reportsAPI.get(filename)
      if (!data.error) {
        setSelectedReport(filename)
        setSections(data.sections || [])
      }
    } catch (e) {
      console.error('Open report error:', e)
    }
  }

  const closeViewer = () => {
    setSelectedReport(null)
    setSections([])
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <section className="space-y-2 mb-6">
        <div className="inline-flex items-center px-2 py-1 rounded-full bg-tertiary/10 border border-tertiary/20">
          <div className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse mr-2"></div>
          <span className="text-[10px] font-label font-bold uppercase tracking-widest text-tertiary">Document Archive</span>
        </div>
        <h1 className="font-headline text-3xl font-extrabold leading-tight tracking-tighter text-on-surface">
          Report<br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-tertiary to-primary">History</span>
        </h1>
      </section>

      {/* Reports List */}
      <div className="space-y-3">
        {loading ? (
          <GlassCard>
            <p className="text-on-surface-variant">Loading reports...</p>
          </GlassCard>
        ) : reports.length > 0 ? (
          reports.map((report, idx) => (
            <div
              key={idx}
              onClick={() => openReport(report.filename)}
              className="glass-card p-4 rounded-xl flex justify-between items-center hover:bg-surface-container transition-all cursor-pointer"
            >
              <div>
                <h4 className="font-headline font-bold text-sm text-on-surface">📄 {report.filename}</h4>
                <p className="text-[10px] text-on-surface-variant mt-1">
                  Cập nhật: {report.modified} · {report.size_kb} KB
                </p>
              </div>
              <span className="text-primary text-xs">Xem →</span>
            </div>
          ))
        ) : (
          <GlassCard>
            <p className="text-on-surface-variant">Chưa có báo cáo. Chạy Pipeline để tạo báo cáo đầu tiên.</p>
          </GlassCard>
        )}
      </div>

      {/* Report Viewer */}
      {selectedReport && (
        <GlassCard className="mt-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-headline font-bold text-lg">{selectedReport}</h3>
            <span
              className="text-xs text-on-surface-variant cursor-pointer hover:text-error transition-colors"
              onClick={closeViewer}
            >
              ✕ Đóng
            </span>
          </div>
          <div className="space-y-4">
            {sections.map((sec, idx) => (
              <div key={idx} className="mb-4">
                <h4 className="font-headline font-bold text-sm text-primary mb-2">{sec.heading}</h4>
                <div className="text-sm text-on-surface-variant leading-relaxed">
                  <MarkdownRenderer content={sec.body_html?.replace(/<[^>]+>/g, '') || ''} />
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  )
}

export default Reports
