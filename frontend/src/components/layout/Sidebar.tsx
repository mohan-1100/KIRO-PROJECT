import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Network, Zap, AlertTriangle, RefreshCw, Server, History, Settings, ChevronLeft, ChevronRight } from 'lucide-react';

const NAV = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true as const },
  { to: '/dependency-map', label: 'Dependency Map', icon: Network, end: false as const },
  { to: '/simulator', label: 'Failure Simulator', icon: Zap, end: false as const },
  { to: '/incidents', label: 'Incident Analysis', icon: AlertTriangle, end: false as const },
  { to: '/recovery', label: 'Recovery Planner', icon: RefreshCw, end: false as const },
  { to: '/inventory', label: 'Infrastructure', icon: Server, end: false as const },
  { to: '/history', label: 'Sim History', icon: History, end: false as const },
  { to: '/settings', label: 'Settings and DQ', icon: Settings, end: false as const },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const w = collapsed ? 'w-16' : 'w-56';
  return (
    <aside className={w + ' shrink-0 bg-slate-900 border-r border-slate-700 flex flex-col transition-all duration-200'}>
      <button
        onClick={() => setCollapsed(c => !c)}
        className="flex items-center justify-end p-3 text-slate-400 hover:text-slate-100 border-b border-slate-800"
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>
      <nav className="flex-1 py-2">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to} to={to} end={end}
            className={({ isActive }) =>
              (isActive
                ? 'flex items-center gap-3 px-3 py-2.5 mx-2 rounded text-sm transition-colors bg-blue-900/50 text-blue-300'
                : 'flex items-center gap-3 px-3 py-2.5 mx-2 rounded text-sm transition-colors text-slate-400 hover:text-slate-100 hover:bg-slate-800'
              )
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
