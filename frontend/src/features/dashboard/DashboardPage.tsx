import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import ReactECharts from 'echarts-for-react'
import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  Globe,
  Server,
  ShieldAlert,
  Siren,
  Target,
  TrendingUp,
  Zap,
} from 'lucide-react'
import { AnimatedCard } from '@/components/AnimatedCard'
import { ChartCard } from '@/components/ChartCard'
import { PageHeader } from '@/components/PageHeader'
import { EnterpriseAttackMap } from '@/components/EnterpriseAttackMap'
import apiClient from '@/services/api'
import { Alert, Asset, Incident } from '@/types'

const demoAlerts: Alert[] = [
  { id: 1, wazuh_alert_id: 'wazuh-1001', title: 'FortiGate deny to RDP', severity: 13, source_ip: '10.0.0.55', destination_ip: '192.168.1.10', rule_id: '100102', mitre_technique: 'T1190', status: 'new', created_at: '2024-07-25T10:00:00Z' },
  { id: 2, wazuh_alert_id: 'wazuh-1002', title: 'Port scan detected', severity: 12, source_ip: '10.0.0.55', destination_ip: '192.168.1.20', rule_id: '100101', mitre_technique: 'T1046', status: 'investigating', created_at: '2024-07-25T09:45:00Z' },
  { id: 3, wazuh_alert_id: 'wazuh-1003', title: 'Windows failed logon', severity: 8, source_ip: '192.168.1.100', rule_id: '60122', mitre_technique: 'T1110', status: 'acknowledged', created_at: '2024-07-25T08:30:00Z' },
  { id: 4, wazuh_alert_id: 'wazuh-1004', title: 'Linux sudo escalation', severity: 10, source_ip: '192.168.1.20', rule_id: '5402', mitre_technique: 'T1078', status: 'new', created_at: '2024-07-25T07:15:00Z' },
]

const demoAssets: Asset[] = [
  { id: 1, hostname: 'FortiGate-60F', ip_address: '192.168.1.1', type: 'firewall', operating_system: 'FortiOS', criticality: 95, risk_score: 62, last_seen: '2024-07-25T12:00:00Z', created_at: '2024-01-01' },
  { id: 2, hostname: 'Windows-Server-2019', ip_address: '192.168.1.10', type: 'windows_server', operating_system: 'Windows Server 2019', criticality: 85, risk_score: 78, last_seen: '2024-07-25T11:58:00Z', created_at: '2024-01-01' },
  { id: 3, hostname: 'Linux-Database-Server', ip_address: '192.168.1.20', type: 'database', operating_system: 'Ubuntu 22.04', criticality: 90, risk_score: 82, last_seen: '2024-07-25T11:55:00Z', created_at: '2024-01-01' },
]

const demoIncidents: Incident[] = [
  { id: 1, name: 'RDP brute-force campaign', severity: 'high', status: 'open', created_at: '2024-07-25T09:00:00Z' },
  { id: 2, name: 'Suspicious DNS exfiltration', severity: 'medium', status: 'in_progress', created_at: '2024-07-24T16:20:00Z' },
]

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
}

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0 },
}

function KpiCard({
  title,
  value,
  icon: Icon,
  trend,
  trendUp,
  color,
  delay = 0,
}: {
  title: string
  value: string | number
  icon: typeof AlertTriangle
  trend?: string
  trendUp?: boolean
  color: string
  delay?: number
}) {
  return (
    <motion.div
      variants={item}
      transition={{ delay }}
      whileHover={{ y: -4, boxShadow: `0 0 24px ${color}22` }}
      className="enterprise-panel relative overflow-hidden p-5"
    >
      <div className="absolute right-0 top-0 h-24 w-24 -translate-y-6 translate-x-6 rounded-full opacity-10" style={{ background: color }} />
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">{title}</p>
          <p className="mt-2 text-3xl font-bold text-white">{value}</p>
          {trend && (
            <p className={`mt-1 flex items-center gap-1 text-xs ${trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
              <TrendingUp className="h-3 w-3" />
              {trend}
            </p>
          )}
        </div>
        <div className="rounded-lg p-3" style={{ background: `${color}18` }}>
          <Icon className="h-6 w-6" style={{ color }} />
        </div>
      </div>
    </motion.div>
  )
}

export function DashboardPage() {
  const { data: alertsData } = useQuery({
    queryKey: ['alerts', { page: 1, limit: 100 }],
    queryFn: async () => {
      const { data } = await apiClient.get('/alerts', { params: { page: 1, limit: 100 } })
      return data as { data: Alert[] }
    },
    initialData: { data: demoAlerts },
  })

  const { data: assetsData } = useQuery({
    queryKey: ['assets', { page: 1, limit: 100 }],
    queryFn: async () => {
      const { data } = await apiClient.get('/assets', { params: { page: 1, limit: 100 } })
      return data as { data: Asset[] }
    },
    initialData: { data: demoAssets },
  })

  const { data: incidentsData } = useQuery({
    queryKey: ['incidents', { page: 1, limit: 10 }],
    queryFn: async () => {
      const { data } = await apiClient.get('/incidents', { params: { page: 1, limit: 10 } })
      return data as { data: Incident[] }
    },
    initialData: { data: demoIncidents },
  })

  const alerts = useMemo(() => alertsData?.data || [], [alertsData])
  const assets = useMemo(() => assetsData?.data || [], [assetsData])
  const incidents = useMemo(() => incidentsData?.data || [], [incidentsData])

  const criticalAlerts = alerts.filter((a) => a.severity >= 10).length
  const totalAssets = assets.length
  const openIncidents = incidents.filter((i) => i.status === 'open' || i.status === 'in_progress').length
  const avgRisk = assets.length ? Math.round(assets.reduce((s, a) => s + (a.risk_score || 0), 0) / assets.length) : 0

  const alertTrendOption = useMemo(
    () => ({
      backgroundColor: 'transparent',
      grid: { top: 20, right: 20, bottom: 30, left: 40 },
      xAxis: {
        type: 'category',
        data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
        axisLine: { lineStyle: { color: '#4b5563' } },
        axisLabel: { color: '#9ca3af' },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: '#374151' } },
        axisLabel: { color: '#9ca3af' },
      },
      series: [
        {
          data: [4, 7, 12, 9, 15, 8],
          type: 'line',
          smooth: true,
          areaStyle: { color: 'rgba(6,182,212,0.2)' },
          lineStyle: { color: '#06b6d4', width: 2 },
          itemStyle: { color: '#06b6d4' },
        },
      ],
    }),
    [],
  )

  const severityOption = useMemo(
    () => ({
      backgroundColor: 'transparent',
      color: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],
      series: [
        {
          type: 'pie',
          radius: ['45%', '70%'],
          avoidLabelOverlap: false,
          label: { show: false },
          data: [
            { value: criticalAlerts, name: 'Critical' },
            { value: alerts.filter((a) => a.severity >= 7 && a.severity < 10).length, name: 'High' },
            { value: alerts.filter((a) => a.severity >= 4 && a.severity < 7).length, name: 'Medium' },
            { value: alerts.filter((a) => a.severity < 4).length, name: 'Low' },
          ],
        },
      ],
    }),
    [alerts, criticalAlerts],
  )

  const mitreCoverageOption = useMemo(
    () => ({
      backgroundColor: 'transparent',
      color: ['#06b6d4'],
      grid: { top: 10, right: 20, bottom: 60, left: 130 },
      xAxis: {
        type: 'value',
        max: 100,
        splitLine: { lineStyle: { color: '#374151' } },
        axisLabel: { color: '#9ca3af' },
      },
      yAxis: {
        type: 'category',
        data: ['Initial Access', 'Execution', 'Persistence', 'Privilege Escalation', 'Defense Evasion', 'Credential Access', 'Discovery', 'Lateral Movement'],
        axisLine: { lineStyle: { color: '#4b5563' } },
        axisLabel: { color: '#9ca3af' },
      },
      series: [{ type: 'bar', data: [80, 60, 70, 55, 45, 90, 65, 50] }],
    }),
    [],
  )

  const attackTimeline = [
    { time: '10:32', event: 'Brute Force Detected', severity: 'critical' },
    { time: '10:35', event: 'Suspicious Login', severity: 'high' },
    { time: '10:40', event: 'Incident Created', severity: 'medium' },
    { time: '10:45', event: 'AI Investigation Started', severity: 'info' },
  ]

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <PageHeader
        title="SOC Command Center"
        subtitle="Real-time visibility into threats, assets, and AI-driven investigations"
      />

      <motion.div variants={item} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Critical Alerts" value={criticalAlerts} icon={Siren} trend="2 unassigned" trendUp={false} color="#ef4444" delay={0} />
        <KpiCard title="Active Incidents" value={openIncidents} icon={ShieldAlert} trend="-1 today" trendUp={false} color="#f97316" delay={0.05} />
        <KpiCard title="Global Risk Score" value={`${avgRisk}/100`} icon={Target} trend="+4% vs yesterday" trendUp={false} color="#06b6d4" delay={0.1} />
        <KpiCard title="Assets Monitored" value={totalAssets} icon={Server} trend="100% online" trendUp color="#10b981" delay={0.15} />
        <KpiCard title="MTTD" value="4m 12s" icon={Clock} trend="-18s" trendUp color="#8b5cf6" delay={0.2} />
        <KpiCard title="MTTR" value="23m 45s" icon={Zap} trend="+2m" trendUp={false} color="#eab308" delay={0.25} />
        <KpiCard title="Health Score" value="96%" icon={CheckCircle2} trend="All systems healthy" trendUp color="#22c55e" delay={0.3} />
        <KpiCard title="Threats Blocked" value="1,284" icon={Globe} trend="+84 today" trendUp color="#ec4899" delay={0.35} />
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <EnterpriseAttackMap />
        </div>

        <AnimatedCard className="enterprise-panel p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-200">Attack Timeline</h3>
          <div className="relative space-y-5 pl-4">
            <div className="absolute bottom-0 left-[19px] top-2 w-px bg-gray-800" />
            {attackTimeline.map((event, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + idx * 0.1 }}
                className="relative flex gap-4"
              >
                <span
                  className={`z-10 mt-1.5 h-2.5 w-2.5 rounded-full ${
                    event.severity === 'critical'
                      ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'
                      : event.severity === 'high'
                        ? 'bg-orange-500'
                        : event.severity === 'medium'
                          ? 'bg-yellow-500'
                          : 'bg-cyan-500'
                  }`}
                />
                <div>
                  <p className="text-xs text-cyan-400">{event.time}</p>
                  <p className="text-sm font-medium text-gray-200">{event.event}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </AnimatedCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard title="Alert Evolution" className="lg:col-span-2">
          <ReactECharts option={alertTrendOption} style={{ height: '260px' }} />
        </ChartCard>
        <ChartCard title="Severity Distribution">
          <ReactECharts option={severityOption} style={{ height: '260px' }} />
        </ChartCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard title="MITRE ATT&CK Coverage" className="lg:col-span-2">
          <ReactECharts option={mitreCoverageOption} style={{ height: '280px' }} />
        </ChartCard>
        <ChartCard title="Top Attacking IPs">
          <div className="space-y-3 pt-2">
            {['10.0.0.55', '192.168.1.200', '172.16.0.12'].map((ip, idx) => (
              <div key={ip} className="flex items-center justify-between rounded-md bg-gray-900/50 p-3 transition-colors hover:bg-gray-900">
                <div className="flex items-center gap-3">
                  <Globe className="h-4 w-4 text-gray-500" />
                  <span className="font-mono text-sm text-gray-200">{ip}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <span>{[14, 9, 5][idx]} alerts</span>
                  <TrendingUp className="h-4 w-4 text-red-400" />
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Most Targeted Assets">
          <div className="space-y-3 pt-2">
            {assets
              .sort((a, b) => b.risk_score - a.risk_score)
              .slice(0, 3)
              .map((asset) => (
                <div key={asset.id} className="flex items-center justify-between rounded-md bg-gray-900/50 p-3 transition-colors hover:bg-gray-900">
                  <div>
                    <p className="text-sm font-medium text-gray-200">{asset.hostname}</p>
                    <p className="text-xs text-gray-500">{asset.ip_address}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-24 rounded-full bg-gray-700">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${asset.risk_score}%` }}
                        transition={{ duration: 1 }}
                        className="h-2 rounded-full bg-cyan-500"
                      />
                    </div>
                    <span className="text-xs font-medium text-gray-300">{asset.risk_score}</span>
                  </div>
                </div>
              ))}
          </div>
        </ChartCard>
        <ChartCard title="Recent Incidents">
          <div className="space-y-3 pt-2">
            {incidents.slice(0, 3).map((incident) => (
              <div key={incident.id} className="flex items-center justify-between rounded-md bg-gray-900/50 p-3 transition-colors hover:bg-gray-900">
                <div>
                  <p className="text-sm font-medium text-gray-200">{incident.name}</p>
                  <p className="text-xs text-gray-500 capitalize">{incident.severity} · {incident.status.replace('_', ' ')}</p>
                </div>
                <ArrowUpRight className="h-4 w-4 text-gray-500" />
              </div>
            ))}
          </div>
        </ChartCard>
      </div>
    </motion.div>
  )
}
