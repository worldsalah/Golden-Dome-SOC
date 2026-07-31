import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { AlertTriangle, ShieldCheck } from 'lucide-react'
import { GlobalAttackMap } from '@/components/GlobalAttackMap'
import { getWazuhDashboard, getLatestAlerts } from '@/services/api'

export function CommandCenterPage() {
  const { data: dashboard } = useQuery({
    queryKey: ['wazuh-dashboard-cc', 24],
    queryFn: () => getWazuhDashboard(24),
    refetchInterval: 10_000,
  })

  const { data: latestData } = useQuery({
    queryKey: ['latest-alerts-cc'],
    queryFn: () => getLatestAlerts(5),
    refetchInterval: 10_000,
  })

  const severity = useMemo(() => dashboard?.severity || { critical: 0, high: 0, medium: 0, low: 0 }, [dashboard?.severity])
  const totalAlerts = dashboard?.total_alerts || 0
  const alertsToday = dashboard?.alerts_today || 0
  const activeAgents = dashboard?.active_agents || 0
  const totalAgents = dashboard?.total_agents || 0
  const postureScore = useMemo(() => {
    if (!totalAgents) return 0
    const agentHealth = Math.round((activeAgents / totalAgents) * 40)
    const alertPenalty = Math.min(severity.critical * 10 + severity.high * 5, 40)
    return Math.max(0, 60 + agentHealth - alertPenalty)
  }, [activeAgents, totalAgents, severity])

  const latestAlerts = (latestData?.alerts || []).slice(0, 5)

  return (
    <div className="min-h-full bg-[#090909] px-4 py-5 text-stone-100 md:px-7 md:py-7">
      <div className="mb-7 flex items-end justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[.2em] text-stone-500">Golden Dome / command center</p>
          <h1 className="mt-2 text-2xl font-medium tracking-tight">Security overview</h1>
        </div>
        <p className="hidden text-xs text-stone-500 md:block">
          <span className="text-emerald-400">Systems operational</span>
        </p>
      </div>

      <div className="grid gap-0 overflow-hidden border border-white/[.08] bg-[#0d0f0f] xl:grid-cols-[250px_minmax(0,1fr)_290px]">
        {/* Posture sidebar */}
        <aside className="border-b border-white/[.08] p-5 xl:border-b-0 xl:border-r">
          <p className="text-[10px] font-semibold uppercase tracking-[.16em] text-stone-500">Security posture</p>
          <div className="mt-8">
            <p className="text-5xl font-medium tracking-tighter">
              {postureScore}<span className="text-xl text-stone-600">/100</span>
            </p>
            <p className="mt-2 text-sm" style={{ color: postureScore >= 70 ? '#6ee7b7' : postureScore >= 40 ? '#c97948' : '#b94747' }}>
              {postureScore >= 70 ? 'Healthy' : postureScore >= 40 ? 'Elevated exposure' : 'Critical exposure'}
            </p>
          </div>
          <div className="mt-10 space-y-5">
            <div>
              <p className="text-[11px] text-stone-500">Critical alerts</p>
              <p className="mt-1 text-xl font-medium" style={{ color: severity.critical > 0 ? '#b94747' : '#6ee7b7' }}>
                {String(severity.critical).padStart(2, '0')}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-stone-500">High severity alerts</p>
              <p className="mt-1 text-xl font-medium" style={{ color: severity.high > 0 ? '#c97929' : '#6ee7b7' }}>
                {String(severity.high).padStart(2, '0')}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-stone-500">Monitored agents</p>
              <p className="mt-1 text-xl font-medium" style={{ color: '#6ee7b7' }}>{totalAgents}</p>
            </div>
          </div>
        </aside>

        {/* Attack map */}
        <section className="relative min-h-[560px] overflow-hidden px-4 py-6 md:px-8">
          <div className="absolute inset-0 opacity-35 [background-image:linear-gradient(rgba(255,255,255,.045)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.045)_1px,transparent_1px)] [background-size:46px_46px]" />
          <div className="relative z-10 flex items-start justify-between">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[.16em] text-stone-500">Attack intelligence</p>
              <h2 className="mt-1 text-lg font-medium">Global activity</h2>
            </div>
            <span className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-emerald-300">
              <i className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />Live
            </span>
          </div>
          <div className="relative z-10 mt-2 h-[455px]">
            <GlobalAttackMap />
          </div>
          <div className="relative z-10 flex justify-between border-t border-white/[.07] pt-4 text-[10px] uppercase tracking-wider text-stone-500">
            <span>{totalAlerts} total alerts</span>
            <span>Auto-refresh: 10s</span>
          </div>
        </section>

        {/* Live incident stream */}
        <aside className="border-t border-white/[.08] p-5 xl:border-l xl:border-t-0">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-semibold uppercase tracking-[.16em] text-stone-500">Live alert stream</p>
            <AlertTriangle size={15} className="text-[#c97948]" />
          </div>
          <div className="mt-5 divide-y divide-white/[.07]">
            {latestAlerts.length === 0 ? (
              <p className="py-4 text-xs text-stone-600">No recent alerts</p>
            ) : (
              latestAlerts.map((alert: Record<string, unknown>, index) => {
                const rule = (alert as Record<string, Record<string, unknown>>).rule || {}
                const data = (alert as Record<string, Record<string, unknown>>).data || {}
                const agent = (alert as Record<string, Record<string, unknown>>).agent || {}
                const level = Number(rule.level || 1)
                const sevColor = level >= 13 ? '#b94747' : level >= 10 ? '#c97929' : level >= 4 ? '#b08a2e' : '#6fbf95'
                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: 12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.12 }}
                    className="py-4"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[11px] text-stone-300">
                        {String(data.srcip || 'N/A')}
                      </span>
                      <span className="text-[10px] capitalize" style={{ color: sevColor }}>
                        L{level}
                      </span>
                    </div>
                    <p className="mt-2 text-sm">{String(rule.description || 'Unknown')}</p>
                    <p className="mt-1 text-[11px] text-stone-500">Agent: {String(agent.name || 'N/A')}</p>
                  </motion.div>
                )
              })
            )}
          </div>
        </aside>
      </div>

      {/* Bottom metrics */}
      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <div className="border-t border-white/[.1] py-5">
          <div className="flex items-center gap-2 text-xs text-stone-400">
            <ShieldCheck size={15} className="text-emerald-400" />
            Detection coverage
            <b className="ml-auto font-medium text-stone-200">
              {totalAgents > 0 ? `${Math.round((activeAgents / totalAgents) * 100)}%` : '0%'}
            </b>
          </div>
        </div>
        <div className="border-t border-white/[.1] py-5">
          <div className="flex items-center gap-2 text-xs text-stone-400">
            <AlertTriangle size={15} className="text-[#c97948]" />
            Alerts (24h)
            <b className="ml-auto font-medium text-stone-200">{alertsToday}</b>
          </div>
        </div>
      </div>
    </div>
  )
}
