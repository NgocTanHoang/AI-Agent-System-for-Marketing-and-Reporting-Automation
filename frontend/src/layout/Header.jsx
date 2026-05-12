import { useState } from 'react'

function Header({ theme, toggleTheme }) {
  const [search, setSearch] = useState('')

  return (
    <header className="fixed top-0 left-64 right-0 z-40 bg-surface/80 backdrop-blur-xl border-b border-outline-variant px-6 h-16 flex items-center justify-between shadow-lg">
      {/* Search */}
      <div className="flex-1 max-w-md">
        <div className="flex items-center gap-2 bg-surface-container-highest rounded-full px-4 py-2 border border-outline-variant">
          <span className="material-symbols-outlined text-on-surface-variant text-sm">search</span>
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent border-none outline-none text-on-surface text-sm flex-1 font-body"
          />
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="w-10 h-10 rounded-xl bg-surface-container-highest border border-outline-variant flex items-center justify-center hover:bg-surface-container transition-all"
          title={theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
        >
          <span className="material-symbols-outlined text-on-surface-variant">
            {theme === 'dark' ? 'light_mode' : 'dark_mode'}
          </span>
        </button>

        {/* Notifications */}
        <button className="w-10 h-10 rounded-xl bg-surface-container-highest border border-outline-variant flex items-center justify-center hover:bg-surface-container transition-all relative">
          <span className="material-symbols-outlined text-on-surface-variant">notifications</span>
          <div className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full"></div>
        </button>

        {/* User Avatar */}
        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary to-secondary flex items-center justify-center text-surface font-bold cursor-pointer">
          👤
        </div>
      </div>
    </header>
  )
}

export default Header
