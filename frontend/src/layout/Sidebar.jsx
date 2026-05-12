import { NavLink } from 'react-router-dom'
import { useState } from 'react'

const menuItems = [
  { path: '/intelligence', icon: 'psychology', label: 'Intelligence' },
  { path: '/analytics', icon: 'insights', label: 'Analytics' },
  { path: '/pipelines', icon: 'sensors', label: 'Pipelines' },
  { path: '/models', icon: 'smart_toy', label: 'Models' },
  { path: '/reports', icon: 'description', label: 'Reports' },
]

function Sidebar({ theme }) {
  const [runStatus, setRunStatus] = useState('IDLE')

  const handleRunPipeline = async () => {
    setRunStatus('RUNNING')
    try {
      const res = await fetch('http://localhost:8000/run', { method: 'POST' })
      if (res.ok) {
        // Polling status
        const poll = setInterval(async () => {
          const sRes = await fetch('http://localhost:8000/api/pipeline-status')
          const data = await sRes.json()
          setRunStatus(data.status)
          if (data.status !== 'RUNNING') {
            clearInterval(poll)
          }
        }, 3000)
      }
    } catch (e) {
      setRunStatus('FAILED')
    }
  }

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-surface-container-low border-r border-outline-variant z-50 flex flex-col">
      {/* Logo */}
      <div className="p-6 flex items-center gap-3">
        <div className="w-10 h-10 bg-gradient-to-r from-primary to-secondary rounded-lg flex items-center justify-center text-surface font-bold">
          S
        </div>
        <div>
          <h1 className="font-brand text-sm font-bold text-primary tracking-tighter uppercase">NEURAL_STRAT</h1>
          <p className="text-[10px] text-on-surface-variant uppercase tracking-wider">Marketing Intel</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {menuItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
          >
            <span className="material-symbols-outlined text-xl">{item.icon}</span>
            <span className="font-label text-sm">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Run Pipeline Button */}
      <div className="p-4 border-t border-outline-variant">
        <button
          onClick={handleRunPipeline}
          disabled={runStatus === 'RUNNING'}
          className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {runStatus === 'RUNNING' && <div className="spinner"></div>}
          {runStatus === 'RUNNING' ? 'RUNNING...' : '▶ Run Pipeline'}
        </button>
        <div className="mt-2 text-center">
          <span className={`status-tag status-${runStatus.toLowerCase()}`}>{runStatus}</span>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
