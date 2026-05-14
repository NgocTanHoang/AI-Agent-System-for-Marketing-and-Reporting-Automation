import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  RadialLinearScale,
  Title,
  Tooltip,
} from "chart.js"
import { Bar, Doughnut, Line, Radar, Scatter } from "react-chartjs-2"

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Tooltip,
  Legend,
  Title,
  Filler,
)

function chartComponent(type) {
  switch (type) {
    case "line":
      return Line
    case "doughnut":
      return Doughnut
    case "radar":
      return Radar
    case "scatter":
      return Scatter
    default:
      return Bar
  }
}

function ChartPanel({ chart }) {
  if (!chart) {
    return null
  }

  const Component = chartComponent(chart.chart_type)
  const data = {
    labels: chart.labels,
    datasets: chart.datasets,
  }

  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-slate-300">{chart.title}</h3>
      <div className="h-[300px]">
        <Component
          data={data}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                labels: { color: "#cbd5e1" },
              },
            },
            scales: chart.chart_type === "radar" || chart.chart_type === "doughnut" ? undefined : {
              x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.12)" } },
              y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.12)" } },
            },
          }}
        />
      </div>
    </div>
  )
}

export default ChartPanel
