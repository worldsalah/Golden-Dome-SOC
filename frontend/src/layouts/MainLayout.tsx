import { useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  Bell,
  BrainCircuit,
  Bug,
  ChevronLeft,
  ChevronRight,
  Crosshair,
  FileText,
  Gauge,
  LayoutDashboard,
  LogOut,
  Menu,
  Network,
  Radar,
  Search,
  Server,
  Settings,
  Shield,
  ShieldAlert,
  User,
  Workflow,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { ROLE_LABELS } from '@/utils/roles'

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Alerts', path: '/alerts', icon: AlertTriangle },
  { name: 'AI Security Analyst', path: '/ai', icon: BrainCircuit },
  { name: 'Detection Center', path: '/detection-center', icon: Crosshair },
  { name: 'Incidents', path: '/incidents', icon: ShieldAlert },
  { name: 'Assets', path: '/assets', icon: Server },
  { name: 'Threat Intelligence', path: '/threat-intel', icon: Radar },
  { name: 'Vulnerability Management', path: '/vulnerabilities', icon: Bug },
  { name: 'MITRE ATT&CK', path: '/mitre', icon: Network },
  { name: 'SOAR Automation', path: '/soar', icon: Workflow },
  { name: 'Reports', path: '/reports', icon: FileText },
  { name: 'Risk Center', path: '/risk', icon: Gauge },
  { name: 'Settings', path: '/settings', icon: Settings },
]

export function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const { user, clearAuth } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    clearAuth()
    navigate('/login')
  }

  const notifications = [
    { id: 1, title: 'Critical alert: Brute force detected', time: '2 min ago', read: false },
    { id: 2, title: 'Incident INC-001 assigned to you', time: '15 min ago', read: false },
    { id: 3, title: 'Asset Windows-Server-2019 offline', time: '1 hr ago', read: true },
  ]

  return (
    <div className="flex h-screen overflow-hidden bg-soc-bg">
      {/* Sidebar desktop */}
      <aside
        className={`hidden md:flex flex-col border-r border-gray-800 bg-soc-panel transition-all duration-300 ${
          sidebarOpen ? 'w-64' : 'w-20'
        }`}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b border-gray-800">
          {sidebarOpen && (
            <Link to="/dashboard" className="flex items-center gap-2 text-slate-100">
              <Shield className="h-6 w-6" />
              <span className="font-bold text-lg tracking-tight">Golden Dome</span>
            </Link>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="rounded p-1 text-gray-400 hover:bg-gray-800 hover:text-white"
          >
            {sidebarOpen ? <ChevronLeft className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-2">
            {navItems.map((item) => {
              const active = location.pathname.startsWith(item.path)
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${
                      active
                        ? 'bg-emerald-500/10 text-emerald-300 ring-1 ring-inset ring-emerald-500/20'
                        : 'text-gray-400 hover:bg-white/[0.04] hover:text-white'
                    }`}
                  >
                    <item.icon className="h-5 w-5 flex-shrink-0" />
                    {sidebarOpen && <span>{item.name}</span>}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>

        <div className="border-t border-gray-800 p-3">
          <div className={`rounded-md bg-gray-800/50 p-3 ${sidebarOpen ? '' : 'flex justify-center'}`}>
            {sidebarOpen ? (
              <div>
                <p className="text-sm font-medium text-white">{user?.username || 'Analyst'}</p>
                <p className="text-xs text-gray-400">{user?.role ? ROLE_LABELS[user.role as keyof typeof ROLE_LABELS] : 'SOC Analyst'}</p>
              </div>
            ) : (
              <User className="h-5 w-5 text-gray-400" />
            )}
          </div>
        </div>
      </aside>

      {/* Mobile header */}
      <div className="flex flex-1 flex-col md:hidden">
        <header className="flex h-16 items-center justify-between border-b border-gray-800 bg-soc-panel px-4">
          <div className="flex items-center gap-2 text-cyan-400">
            <Shield className="h-6 w-6" />
            <span className="font-bold">Golden Dome</span>
          </div>
          <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="text-gray-300">
            <Menu className="h-6 w-6" />
          </button>
        </header>
        {mobileMenuOpen && (
          <nav className="border-b border-gray-800 bg-soc-panel px-4 py-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 py-2 text-sm text-gray-300"
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </Link>
            ))}
          </nav>
        )}
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Top bar */}
        <header className="hidden h-16 items-center justify-between border-b border-gray-800 bg-soc-panel px-6 md:flex">
          <div className="flex items-center gap-4 flex-1">
            <div className="relative w-96">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                placeholder="Search alerts, incidents, assets..."
                className="w-full rounded-md border border-gray-700 bg-gray-900 py-1.5 pl-10 pr-4 text-sm text-white placeholder-gray-500 focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden items-center gap-2 text-sm text-gray-400 md:flex">
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
              Wazuh connected
            </div>

            <div className="relative">
              <button
                onClick={() => setNotificationsOpen((v) => !v)}
                className="relative rounded-md p-2 text-gray-400 hover:bg-gray-800 hover:text-white"
              >
                <Bell className="h-5 w-5" />
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500" />
              </button>
              {notificationsOpen && (
                <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-lg border border-gray-700 bg-gray-900 py-2 shadow-xl">
                  <div className="px-4 py-2 text-sm font-semibold text-gray-200">Notifications</div>
                  {notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`px-4 py-2 hover:bg-gray-800 ${n.read ? 'opacity-60' : ''}`}
                    >
                      <p className="text-sm text-gray-200">{n.title}</p>
                      <p className="text-xs text-gray-500">{n.time}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="relative">
              <button
                onClick={() => setProfileOpen((v) => !v)}
                className="flex items-center gap-2 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm text-gray-200 hover:border-gray-600"
              >
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-700 text-xs font-semibold text-white">
                  {user?.username?.charAt(0).toUpperCase() || 'A'}
                </div>
                <span className="hidden lg:inline">{user?.username || 'Analyst'}</span>
              </button>
              {profileOpen && (
                <div className="absolute right-0 top-full z-50 mt-2 w-48 rounded-lg border border-gray-700 bg-gray-900 py-1 shadow-xl">
                  <Link
                    to="/profile"
                    onClick={() => setProfileOpen(false)}
                    className="block px-4 py-2 text-sm text-gray-200 hover:bg-gray-800"
                  >
                    Profile
                  </Link>
                  <Link
                    to="/settings"
                    onClick={() => setProfileOpen(false)}
                    className="block px-4 py-2 text-sm text-gray-200 hover:bg-gray-800"
                  >
                    Settings
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-red-400 hover:bg-gray-800"
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-6"><Outlet /></main>
      </div>
    </div>
  )
}
