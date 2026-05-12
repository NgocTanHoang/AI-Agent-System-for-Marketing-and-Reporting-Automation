import { useState, useEffect, useRef } from 'react'
import { Chart, registerables } from 'chart.js'
import { dashboardAPI } from '../api/api'
import ChartCard from '../components/ChartCard'

Chart.register(...registerables)

const P = '#91abff'
const S = '#dd8bfb'
const T = '#ffbb81'
const E = '#ff6e84'
const G = '#34d399'
const C = '#396bee'

function Analytics() {
  const [filters, setFilters] = useState({ brand: '', region: '' })

  // Chart refs
  const topRevenueRef = useRef(null)
  const topSalesRef = useRef(null)
  const bottomRevenueRef = useRef(null)
  const bottomSalesRef = useRef(null)
  const paymentDonutRef = useRef(null)
  const paymentAgeRef = useRef(null)
  const heatmapRef = useRef(null)
  const marketingRef = useRef(null)

  const loadData = async () => {
    try {
      const data = await dashboardAPI.getData(filters.brand, filters.region)
      if (data.error) return

      // Top Revenue
      if (topRevenueRef.current) {
        new Chart(topRevenueRef.current, {
          type: 'bar',
          data: {
            labels: data.top_revenue?.map(x => x.product_name) || [],
            datasets: [{ label: 'Doanh thu', data: data.top_revenue?.map(x => x.revenue) || [], backgroundColor: [P,S,T,C,G], barThickness: 12, borderRadius: 4 }]
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
          }
        })
      }

      // Top Sales
      if (topSalesRef.current) {
        new Chart(topSalesRef.current, {
          type: 'bar',
          data: {
            labels: data.top_sales?.map(x => x.product_name) || [],
            datasets: [{ label: 'Units', data: data.top_sales?.map(x => x.units_sold) || [], backgroundColor: [P,S,T,C,G], barThickness: 12, borderRadius: 4 }]
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
          }
        })
      }

      // Bottom Revenue
      if (bottomRevenueRef.current) {
        new Chart(bottomRevenueRef.current, {
          type: 'bar',
          data: {
            labels: data.bottom_revenue?.map(x => x.product_name) || [],
            datasets: [{ label: 'Revenue', data: data.bottom_revenue?.map(x => x.revenue) || [], backgroundColor: E, barThickness: 12, borderRadius: 4 }]
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
          }
        })
      }

      // Bottom Sales
      if (bottomSalesRef.current) {
        new Chart(bottomSalesRef.current, {
          type: 'bar',
          data: {
            labels: data.bottom_sales?.map(x => x.product_name) || [],
            datasets: [{ label: 'Units', data: data.bottom_sales?.map(x => x.units_sold) || [], backgroundColor: E, barThickness: 12, borderRadius: 4 }]
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
          }
        })
      }

      // Payment Donut
      if (paymentDonutRef.current) {
        new Chart(paymentDonutRef.current, {
          type: 'doughnut',
          data: {
            labels: data.payment_donut?.map(x => x.payment_method) || [],
            datasets: [{ data: data.payment_donut?.map(x => x.count) || [], backgroundColor: [P,S,T,G,C], borderWidth: 0 }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '80%',
            plugins: { legend: { position: 'right' } }
          }
        })
      }

      // Payment Age
      if (paymentAgeRef.current && data.payment_age) {
        const ageGroups = [...new Set(data.payment_age.map(x => x.customer_age_group))]
        const payMethods = [...new Set(data.payment_age.map(x => x.payment_method))]
        new Chart(paymentAgeRef.current, {
          type: 'bar',
          data: {
            labels: ageGroups,
            datasets: payMethods.map((pm, i) => ({
              label: pm,
              data: ageGroups.map(ag => {
                const f = data.payment_age.find(x => x.customer_age_group === ag && x.payment_method === pm)
                return f ? f.count : 0
              }),
              backgroundColor: [P,S,T,G,C,E][i % 5],
              borderRadius: 4,
              barThickness: 18
            }))
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: { x: { stacked: true }, y: { stacked: true } }
          }
        })
      }

      // Heatmap (Price × Age)
      if (heatmapRef.current && data.price_age_heatmap) {
        const ageCols = [...new Set(data.price_age_heatmap.map(x => x.customer_age_group))]
        const priceBins = ['Dưới 5 triệu', '5-10 triệu', '10-20 triệu', 'Trên 20 triệu'].filter(pb => data.price_age_heatmap.some(x => x.price_bin === pb))
        new Chart(heatmapRef.current, {
          type: 'bar',
          data: {
            labels: ageCols,
            datasets: priceBins.map((pb, i) => ({
              label: pb,
              data: ageCols.map(ag => {
                const f = data.price_age_heatmap.find(x => x.customer_age_group === ag && x.price_bin === pb)
                return f ? f.count : 0
              }),
              backgroundColor: [P,S,T,C][i % 4],
              borderRadius: 4,
              barThickness: 24
            }))
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: { x: { stacked: true }, y: { stacked: true } }
          }
        })
      }

      // Marketing (CPA + ROI)
      if (marketingRef.current && data.marketing_efficiency) {
        const channels = data.marketing_efficiency.map(x => x.channel)
        new Chart(marketingRef.current, {
          type: 'bar',
          data: {
            labels: channels,
            datasets: [
              {
                label: 'CPA (VNĐ)',
                data: data.marketing_efficiency.map(x => x.avg_cpa),
                backgroundColor: E,
                borderRadius: 4,
                barThickness: 12,
                yAxisID: 'y'
              },
              {
                label: 'ROI (x)',
                data: data.marketing_efficiency.map(x => x.avg_roi),
                backgroundColor: P,
                borderRadius: 4,
                barThickness: 12,
                yAxisID: 'y1'
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: {
              x: { grid: { display: false } },
              y: { position: 'left', grid: { display: false } },
              y1: { position: 'right', grid: { display: false } }
            }
          }
        })
      }
    } catch (e) {
      console.error('Analytics Error:', e)
    }
  }

  useEffect(() => {
    loadData()
  }, [filters])

  return (
    <div className="space-y-6">
      <section className="space-y-2 mb-6">
        <div className="inline-flex items-center px-2 py-1 rounded-full bg-secondary/10 border border-secondary/20">
          <div className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse mr-2"></div>
          <span className="text-[10px] font-label font-bold uppercase tracking-widest text-secondary">Data Exploration</span>
        </div>
        <h1 className="font-headline text-3xl font-extrabold leading-tight tracking-tighter text-on-surface">
          Analytics<br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-secondary to-tertiary">Center</span>
        </h1>
      </section>

      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={filters.brand}
          onChange={(e) => setFilters(prev => ({ ...prev, brand: e.target.value }))}
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
          value={filters.region}
          onChange={(e) => setFilters(prev => ({ ...prev, region: e.target.value }))}
          className="bg-surface-container-highest border border-outline-variant text-on-surface text-xs rounded-xl px-4 py-2 font-label uppercase tracking-wider focus:outline-none focus:border-primary/50"
        >
          <option value="">Tất cả Khu vực</option>
          <option value="North">Miền Bắc</option>
          <option value="South">Miền Nam</option>
          <option value="Central">Miền Trung</option>
          <option value="Highlands">Tây Nguyên</option>
        </select>
      </div>

      {/* Module 1: Performance Ranking */}
      <div>
        <p className="font-label text-[10px] font-bold uppercase tracking-widest text-primary mb-4">📊 Module 1 — Performance Ranking</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ChartCard title="Top 5 — Doanh Thu Cao Nhất"><canvas ref={topRevenueRef}></canvas></ChartCard>
          <ChartCard title="Top 5 — Doanh Số Cao Nhất"><canvas ref={topSalesRef}></canvas></ChartCard>
          <ChartCard title="Bottom 5 — Doanh Thu Thấp Nhất"><canvas ref={bottomRevenueRef}></canvas></ChartCard>
          <ChartCard title="Bottom 5 — Doanh Số Thấp Nhất"><canvas ref={bottomSalesRef}></canvas></ChartCard>
        </div>
      </div>

      {/* Module 2: Payment Dynamics */}
      <div>
        <p className="font-label text-[10px] font-bold uppercase tracking-widest text-secondary mb-4">💳 Module 2 — Payment Dynamics</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ChartCard title="Tỷ Lệ Thanh Toán" subtitle="donut"><canvas ref={paymentDonutRef}></canvas></ChartCard>
          <ChartCard title="Thanh Toán Theo Độ Tuổi" subtitle="stacked bar"><canvas ref={paymentAgeRef}></canvas></ChartCard>
        </div>
      </div>

      {/* Module 3: Customer Profiles */}
      <div>
        <p className="font-label text-[10px] font-bold uppercase tracking-widest text-tertiary mb-4">👥 Module 3 — Customer Profiles</p>
        <ChartCard title="Heatmap: Tầm Giá × Độ Tuổi" subtitle="age × price"><canvas ref={heatmapRef}></canvas></ChartCard>
      </div>

      {/* Module 4: Marketing Efficiency */}
      <div>
        <p className="font-label text-[10px] font-bold uppercase tracking-widest text-primary mb-4">🚀 Module 4 — Marketing Efficiency</p>
        <ChartCard title="CPA & ROI Theo Kênh" subtitle="grouped bar"><canvas ref={marketingRef}></canvas></ChartCard>
      </div>
    </div>
  )
}

export default Analytics
