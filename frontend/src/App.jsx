import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './layout/Layout'
import Intelligence from './pages/Intelligence'
import Analytics from './pages/Analytics'
import Pipelines from './pages/Pipelines'
import Models from './pages/Models'
import Reports from './pages/Reports'

function App() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme')
    return saved || 'dark'
  })

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
      root.classList.remove('light')
    } else {
      root.classList.add('light')
      root.classList.remove('dark')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout theme={theme} toggleTheme={toggleTheme} />}>
          <Route index element={<Navigate to="/intelligence" replace />} />
          <Route path="intelligence" element={<Intelligence />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="pipelines" element={<Pipelines />} />
          <Route path="models" element={<Models />} />
          <Route path="reports" element={<Reports />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
