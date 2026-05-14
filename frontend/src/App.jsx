import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import Layout from "./layout/Layout"
import Overview from "./pages/Overview"
import Analytics from "./pages/Analytics"
import Agents from "./pages/Agents"
import Research from "./pages/Research"
import Reports from "./pages/Reports"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="overview" element={<Overview />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="agents" element={<Agents />} />
          <Route path="research" element={<Research />} />
          <Route path="reports" element={<Reports />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
