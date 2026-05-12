import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

function Layout({ theme, toggleTheme }) {
  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar />
      <div className="flex-1 ml-64">
        <Header theme={theme} toggleTheme={toggleTheme} />
        <main className="p-6 pt-24">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
