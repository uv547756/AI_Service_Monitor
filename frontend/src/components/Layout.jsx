import { NavLink, Outlet, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/machines', label: 'Machines', icon: '🖥️' },
  { path: '/logs', label: 'Logs', icon: '📋' },
  { path: '/issues', label: 'Issues', icon: '⚠️' },
  { path: '/commands', label: 'Commands', icon: '⚡' },
];

export default function Layout() {
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 flex flex-col border-r"
        style={{ background: 'var(--color-surface-800)', borderColor: 'var(--color-border)' }}>
        
        {/* Logo */}
        <div className="p-5 border-b" style={{ borderColor: 'var(--color-border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center text-lg"
              style={{ background: 'linear-gradient(135deg, var(--color-accent-blue), var(--color-accent-purple))' }}>
              🔍
            </div>
            <div>
              <h1 className="text-base font-bold" style={{ color: 'var(--color-text-primary)' }}>LogWatch</h1>
              <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Monitoring System</p>
            </div>
          </div>
        </div>

        {/* Nav links */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ path, label, icon }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <span className="text-lg">{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t text-xs" style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}>
          <div className="flex items-center gap-2">
            <span className="status-dot healthy"></span>
            <span>System Online</span>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-6" style={{ background: 'var(--color-surface-900)' }}>
        <Outlet />
      </main>
    </div>
  );
}
