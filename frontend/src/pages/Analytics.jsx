import { useOutletContext } from "react-router-dom"
import ChartPanel from "../components/ChartPanel"

function Analytics() {
  const { dashboard } = useOutletContext()
  const charts = dashboard?.charts || {}

  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <ChartPanel chart={charts.revenue_by_campaign} />
      <ChartPanel chart={charts.product_sales_ranking} />
      <ChartPanel chart={charts.campaign_roi} />
      <ChartPanel chart={charts.sales_trend} />
      <ChartPanel chart={charts.product_matrix} />
      <ChartPanel chart={charts.channel_performance} />
    </div>
  )
}

export default Analytics
