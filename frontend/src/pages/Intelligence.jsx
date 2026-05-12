import { useState, useEffect, useCallback } from 'react'
import { kpiAPI, reportsAPI } from '../api/api'
import KPICard from '../components/KPICard'
import GlassCard from '../components/GlassCard'
import MarkdownRenderer from '../components/MarkdownRenderer'

function Intelligence() {
  const [kpi, setKpi] = useState({
    total_revenue: 0,
    top_channel: 'N/A',
    top_complaint: 'N/A',
    total_units: 0,
    avg_roi: 0,
    avg_sentiment: 0
  })
  const [brand, setBrand] = useState('')
  const [region, setRegion] = useState('')
  const [reportName, setReportName] = useState('')
  const [sections, setSections] = useState([])
  const [loading, setLoading] = useState(true)

  const loadKPI = useCallback(async () => {
    try {
      const data = await kpiAPI.getSummary(brand, region)
      if (!data.error) {
        setKpi(data)
      }
    } catch (e) {
      console.error('KPI Error:', e)
    }
  }, [brand, region])

  const loadReport = useCallback(async () => {
    try {
      const d = await reportsAPI.list()
      if (d.reports && d.reports.length > 0) {
        const latest = d.reports[0]
        setReportName(latest.filename)
        const res = await reportsAPI.get(latest.filename)
        setSections(res.sections || [])
      }
    } catch (e) {
      console.error('Report Error:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadKPI()
  }, [loadKPI])

  useEffect(() => {
    loadReport()
  }, [loadReport])

  const handleRate = async (filename, rating) => {
    await reportsAPI.rate(filename, rating)
    alert(rating === 'up' ? 'Cảm ơn! Đã lưu vào Vector DB.' : 'Đã ghi nhận.')
  }

  const fmtVND = (v) => {
    if (v >= 1e12) return (v/1e12).toFixed(1) + ' nghìn tỷ'
    if (v >= 1e9) return (v/1e9).toFixed(1) + ' tỷ'
    if (v >= 1e6) return (v/1e6).toFixed(0) + ' triệu'
    return v.toLocaleString('vi-VN')
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <section className="space-y-2">
        <div className="inline-flex items-center px-2 py-1 rounded-full bg-primary/10 border border-primary/20">
          <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse mr-2"></div>
          <span className="text-[10px] font-label font-bold uppercase tracking-widest text-primary">Live Intel Feed</span>
        </div>
        <h1 className="font-headline text-3xl font-extrabold leading-tight tracking-tighter text-on-surface">
          Báo cáo Chiến lược<br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-secondary to-tertiary">Bán lẻ Smartphone</span>
        </h1>
      </section>

      {/* Filters and Actions */}
      <div className="flex flex-wrap gap-3 items-center">
        <select
          value={brand}
          onChange={(e) => setBrand(e.target.value)}
          className="bg-surface-container-highest border border-outline-variant text-on-surface text-xs rounded-xl px-4 py-2 font-label uppercase tracking-wider focus:outline-none focus:border-primary/50"
        >
          <option value="">Tất cả Thương hiệu</option>
          <option value="Apple">Apple</option>
          <option value="Samsung">Samsung</option>
          <option value="Xiaomi">Xiaomi</option>
          <option value="Oppo">Oppo</option>
          <option value="Google">Google</option>
        </select>
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          className="bg-surface-container-highest border border-outline-variant text-on-surface text-xs rounded-xl px-4 py-2 font-label uppercase tracking-wider focus:outline-none focus:border-primary/50"
        >
          <option value="">Tất cả Khu vực</option>
          <option value="North">Miền Bắc</option>
          <option value="South">Miền Nam</option>
          <option value="Central">Miền Trung</option>
          <option value="Highlands">Tây Nguyên</option>
        </select>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <KPICard icon="payments" title="Tổng Doanh Thu" value={fmtVND(kpi.total_revenue)} borderColor="border-primary" />
        <KPICard icon="rocket_launch" title="Kênh ROI Cao" value={kpi.top_channel} borderColor="border-secondary" badge={kpi.avg_roi.toFixed(2)+'x'} />
        <KPICard icon="sentiment_satisfied" title="Sentiment" value={kpi.avg_sentiment+'%'} borderColor="border-tertiary" />
        <KPICard icon="inventory" title="Tổng Bán Ra" value={kpi.total_units.toLocaleString('vi-VN') + ' máy'} borderColor="border-primary" />
        <KPICard icon="trending_up" title="ROI TB" value={kpi.avg_roi.toFixed(2)+'x'} borderColor="border-secondary" />
        <KPICard icon="chat_bubble" title="Hot Topic" value={kpi.top_complaint} borderColor="border-tertiary" />
      </div>

      {/* AI Report */}
      <section className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="font-headline text-xl font-bold flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary">auto_awesome</span>
            Kế Hoạch Hành Động & Báo Cáo AI
          </h2>
          {reportName && (
            <div className="flex gap-2">
              <button
                onClick={() => handleRate(reportName, 'up')}
                className="px-4 py-2 bg-surface-container-highest border border-[#4ade80]/30 rounded-xl text-[10px] font-bold uppercase tracking-wider text-[#4ade80] hover:bg-[#4ade80]/10 transition-all"
              >
                👍 Tốt
              </button>
              <button
                onClick={() => handleRate(reportName, 'down')}
                className="px-4 py-2 bg-surface-container-highest border border-[#f87171]/30 rounded-xl text-[10px] font-bold uppercase tracking-wider text-[#f87171] hover:bg-[#f87171]/10 transition-all"
              >
                👎 Kém
              </button>
            </div>
          )}
        </div>
        {loading ? (
          <GlassCard>
            <p className="text-on-surface-variant">Đang tải báo cáo...</p>
          </GlassCard>
        ) : sections.length > 0 ? (
          sections.map((sec, idx) => (
            <GlassCard key={idx} className="mb-4">
              <h4 className="font-headline font-bold text-lg text-primary border-b border-white/5 pb-3 mb-3">{sec.heading}</h4>
              <MarkdownRenderer content={sec.body_html?.replace(/<[^>]+>/g, '') || ''} />
            </GlassCard>
          ))
        ) : (
          <GlassCard>
            <h4 className="font-headline font-bold text-lg">Chưa có báo cáo</h4>
            <p className="text-sm text-on-surface-variant mt-2">Nhấn "Run Pipeline" để AI bắt đầu phân tích.</p>
          </GlassCard>
        )}
      </section>
    </div>
  )
}

export default Intelligence
