import { useEffect, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  AlertTriangle,
  Bell,
  BrainCircuit,
  Bug,
  ChevronLeft,
  Crosshair,
  FileText,
  Gauge,
  LayoutDashboard,
  LogOut,
  Menu,
  Network,
  Radar,
  Moon,
  Search,
  Server,
  Settings,
  ShieldAlert,
  Sun,
  User,
  Workflow,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useThemeStore } from '@/store/themeStore'
import { ROLE_LABELS } from '@/utils/roles'

const navSections: { label: string; items: { name: string; path: string; icon: typeof LayoutDashboard }[] }[] = [
  {
    label: 'Operations',
    items: [
      { name: 'Command Center', path: '/dashboard', icon: LayoutDashboard },
      { name: 'Alerts', path: '/alerts', icon: AlertTriangle },
      { name: 'Incidents', path: '/incidents', icon: ShieldAlert },
      { name: 'AI Analyst', path: '/ai', icon: BrainCircuit },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { name: 'Detection Center', path: '/detection-center', icon: Crosshair },
      { name: 'Threat Intelligence', path: '/threat-intel', icon: Radar },
      { name: 'MITRE ATT&CK', path: '/mitre', icon: Network },
      { name: 'Risk Center', path: '/risk', icon: Gauge },
    ],
  },
  {
    label: 'Estate',
    items: [
      { name: 'Assets', path: '/assets', icon: Server },
      { name: 'Vulnerabilities', path: '/vulnerabilities', icon: Bug },
      { name: 'SOAR Automation', path: '/soar', icon: Workflow },
    ],
  },
  {
    label: 'Governance',
    items: [
      { name: 'Reports', path: '/reports', icon: FileText },
      { name: 'Settings', path: '/settings', icon: Settings },
    ],
  },
]

function useClock() {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  return now
}

export function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const { user, clearAuth } = useAuthStore()
  const { theme, toggleTheme } = useThemeStore()
  const location = useLocation()
  const navigate = useNavigate()
  const now = useClock()

  useEffect(() => {
    setNotificationsOpen(false)
    setProfileOpen(false)
    setMobileMenuOpen(false)
  }, [location.pathname])

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
    <div className="flex h-screen overflow-hidden bg-[#0a0a0b] text-stone-200">
      {/* Sidebar */}
      <motion.aside
        animate={{ width: collapsed ? 60 : 232 }}
        transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
        className="hidden shrink-0 flex-col border-r border-white/[0.07] bg-[#0e0f11] md:flex"
      >
        <div className="flex h-14 items-center justify-between border-b border-white/[0.07] px-3.5">
          {!collapsed && (
            <Link to="/dashboard" className="flex items-baseline gap-1.5 overflow-hidden whitespace-nowrap">
              <span className="text-[13px] font-bold tracking-tight text-stone-100">GOLDEN DOME</span>
              <span className="text-[9px] font-semibold uppercase tracking-[.18em] text-[#b98947]">SOC</span>
            </Link>
          )}
          <button
            onClick={() => setCollapsed((v) => !v)}
            className="icon-button"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <motion.span animate={{ rotate: collapsed ? 180 : 0 }} transition={{ duration: 0.25 }}>
              <ChevronLeft className="h-3.5 w-3.5" />
            </motion.span>
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto overflow-x-hidden py-3">
          {navSections.map((section) => (
            <div key={section.label} className="mb-4 px-2.5">
              {!collapsed && (
                <p className="mb-1.5 px-2 text-[9px] font-semibold uppercase tracking-[.18em] text-stone-600">
                  {section.label}
                </p>
              )}
              <ul className="space-y-0.5">
                {section.items.map((item) => {
                  const active = location.pathname.startsWith(item.path)
                  return (
                    <li key={item.path}>
                      <Link
                        to={item.path}
                        title={collapsed ? item.name : undefined}
                        className={`group relative flex items-center gap-2.5 rounded-md px-2 py-2 text-[13px] font-medium transition-colors duration-150 ${
                          active
                            ? 'bg-white/[0.06] text-stone-100'
                            : 'text-stone-500 hover:bg-white/[0.03] hover:text-stone-300'
                        }`}
                      >
                        {active && (
                          <motion.span
                            layoutId="nav-indicator"
                            className="absolute left-0 top-1/2 h-4 w-[2px] -translate-y-1/2 rounded-full bg-[#c97848]"
                          />
                        )}
                        <item.icon
                          className={`h-[17px] w-[17px] shrink-0 ${active ? 'text-[#d8b17a]' : 'text-stone-600 group-hover:text-stone-400'}`}
                          strokeWidth={1.75}
                        />
                        {!collapsed && <span className="truncate">{item.name}</span>}
                      </Link>
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className="border-t border-white/[0.07] p-2.5">
          <div className={`flex items-center gap-2.5 rounded-md px-2 py-2 ${collapsed ? 'justify-center' : ''}`}>
            <div className="grid h-7 w-7 shrink-0 place-items-center rounded-full border border-[#d8b17a]/40 text-[11px] font-semibold text-[#e8d2af]">
              {user?.username?.charAt(0).toUpperCase() || 'A'}
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <p className="truncate text-xs font-medium text-stone-200">{user?.username || 'Analyst'}</p>
                <p className="truncate text-[10px] text-stone-600">
                  {user?.role ? ROLE_LABELS[user.role as keyof typeof ROLE_LABELS] : 'SOC Analyst'}
                </p>
              </div>
            )}
          </div>
        </div>
      </motion.aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top bar */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-white/[0.07] bg-[#0e0f11] px-4">
          <div className="flex items-center gap-3 md:hidden">
            <button onClick={() => setMobileMenuOpen((v) => !v)} className="icon-button">
              <Menu className="h-4 w-4" />
            </button>
            <span className="text-[13px] font-bold tracking-tight">GOLDEN DOME</span>
          </div>

          <div className="hidden flex-1 items-center gap-4 md:flex">
            <div className="relative w-[380px]">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-stone-600" />
              <input
                type="text"
                placeholder="Search alerts, incidents, assets, indicators…"
                className="w-full rounded-md border border-white/[0.08] bg-[#131417] py-1.5 pl-9 pr-14 text-xs text-stone-300 placeholder-stone-600 outline-none transition focus:border-[#b98947]/50"
              />
              <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded border border-white/[0.1] px-1.5 py-0.5 text-[9px] font-medium text-stone-600">
                ⌘K
              </kbd>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-4 lg:flex">
              <span className="font-mono text-[11px] tabular-nums text-stone-500">
                {now.toUTCString().slice(17, 25)} UTC
              </span>
              <span className="flex items-center gap-1.5 text-[11px] text-stone-500">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#3ba676]" />
                Pipeline live
              </span>
            </div>

            <button
              onClick={toggleTheme}
              className="icon-button"
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
            </button>

            <div className="relative">
              <button onClick={() => setNotificationsOpen((v) => !v)} className="icon-button relative">
                <Bell className="h-3.5 w-3.5" />
                <span className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full bg-[#b94747]" />
              </button>
              <AnimatePresence>
                {notificationsOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -6, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -6, scale: 0.98 }}
                    transition={{ duration: 0.18 }}
                    className="absolute right-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-lg border border-white/[0.1] bg-[#141518] shadow-2xl shadow-black/60"
                  >
                    <div className="panel-header">
                      <span className="panel-title">Notifications</span>
                      <span className="pill sev-critical">2 new</span>
                    </div>
                    {notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`border-b border-white/[0.05] px-4 py-2.5 transition hover:bg-white/[0.03] ${n.read ? 'opacity-50' : ''}`}
                      >
                        <p className="text-xs text-stone-300">{n.title}</p>
                        <p className="mt-0.5 text-[10px] text-stone-600">{n.time}</p>
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="relative">
              <button
                onClick={() => setProfileOpen((v) => !v)}
                className="flex items-center gap-2 rounded-md border border-white/[0.1] px-2 py-1 text-xs text-stone-300 transition hover:border-white/20"
              >
                <span className="grid h-5 w-5 place-items-center rounded-full border border-[#d8b17a]/40 text-[10px] font-semibold text-[#e8d2af]">
                  {user?.username?.charAt(0).toUpperCase() || 'A'}
                </span>
                <span className="hidden lg:inline">{user?.username || 'Analyst'}</span>
              </button>
              <AnimatePresence>
                {profileOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -6, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -6, scale: 0.98 }}
                    transition={{ duration: 0.18 }}
                    className="absolute right-0 top-full z-50 mt-2 w-44 overflow-hidden rounded-lg border border-white/[0.1] bg-[#141518] py-1 shadow-2xl shadow-black/60"
                  >
                    <Link to="/profile" className="flex items-center gap-2 px-3.5 py-2 text-xs text-stone-300 transition hover:bg-white/[0.04]">
                      <User className="h-3.5 w-3.5 text-stone-500" /> Profile
                    </Link>
                    <Link to="/settings" className="flex items-center gap-2 px-3.5 py-2 text-xs text-stone-300 transition hover:bg-white/[0.04]">
                      <Settings className="h-3.5 w-3.5 text-stone-500" /> Settings
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="flex w-full items-center gap-2 px-3.5 py-2 text-left text-xs text-[#e08585] transition hover:bg-white/[0.04]"
                    >
                      <LogOut className="h-3.5 w-3.5" /> Log out
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </header>

        {/* Mobile nav drawer */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.nav
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden border-b border-white/[0.07] bg-[#0e0f11] md:hidden"
            >
              {navSections.flatMap((s) => s.items).map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className="flex items-center gap-3 px-4 py-2.5 text-sm text-stone-400"
                >
                  <item.icon className="h-4 w-4" strokeWidth={1.75} />
                  {item.name}
                </Link>
              ))}
            </motion.nav>
          )}
        </AnimatePresence>

        <main className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
              className="p-4 md:p-6"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
