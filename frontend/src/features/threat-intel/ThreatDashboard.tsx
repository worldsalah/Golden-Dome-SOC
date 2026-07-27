/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  AlertTriangle,
  Bug,
  Globe,
  Radio,
  ShieldCheck,
  Skull,
  Target,
  Zap,
  type LucideIcon,
} from 'lucide-react'
import { ChartCard } from '@/components/ChartCard'
import { getThreatDashboard } from '@/services/api'
import { severityClass, typeIcons, scoreColor } from './helpers'
import ReactECharts from 'echarts-for-react'

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: LucideIcon
  label: string
  value: string | number
  color: string
}) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-4">
      <div className="flex items-center justify-between">
        <div className={`rounded-md p-2 ${color}`}>
          <Icon className="h-5 w-5 text-white" />
        </div>
      </div>
      <p className="mt-3 text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-gray-400">{label}</p>
    </div>
  )
}

export function ThreatDashboard() {
  const { data: dash, isLoading } = useQuery({
    queryKey: ['threat', 'dashboard'],
    queryFn: getThreatDashboard,
  })

  const trendOption = useMemo(
    () => ({
      tooltip: { trigger: 'axis' },
      grid: { top: 10, right: 10, bottom: 20, left: 40 },
      xAxis: { type: 'category', data: dash?.ioc_trend?.map((d: any) => d.date) || [], axisLabel: { color: '#9ca3af' } },
      yAxis: { type: 'value', axisLabel: { color: '#9ca3af' }, splitLine: { lineStyle: { color: '#374151' } } },
      series: [{ data: dash?.ioc_trend?.map((d: any) => d.count) || [], type: 'line', smooth: true, itemStyle: { color: '#06b6d4' }, areaStyle: { opacity: 0.2 } }],
    }),
    [dash],
  )

  const distributionOption = useMemo(
    () => ({
      tooltip: { trigger: 'item' },
      grid: { top: 10, right: 10, bottom: 20, left: 40 },
      xAxis: { type: 'category', data: ['0-20', '21-40', '41-60', '61-80', '81-100'], axisLabel: { color: '#9ca3af' } },
      yAxis: { type: 'value', axisLabel: { color: '#9ca3af' }, splitLine: { lineStyle: { color: '#374151' } } },
      series: [{ data: dash?.score_distribution?.map((d: any) => d.count) || [0, 0, 0, 0, 0], type: 'bar', itemStyle: { color: (params: any) => ['#10b981', '#facc15', '#f59e0b', '#f97316', '#ef4444'][params.dataIndex] } }],
    }),
    [dash],
  )

  if (isLoading) return <p className="text-gray-400">Loading dashboard...</p>

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Globe} label="Total IOCs" value={dash?.total_iocs ?? 0} color="bg-cyan-600" />
        <StatCard icon={Skull} label="Malicious IOCs" value={dash?.malicious_iocs ?? 0} color="bg-red-600" />
        <StatCard icon={Activity} label="New IOCs (24h)" value={dash?.new_iocs_24h ?? 0} color="bg-emerald-600" />
        <StatCard icon={Radio} label="Healthy Feeds" value={dash?.feed_health?.filter((h: any) => h.healthy).length ?? 0} color="bg-blue-600" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="IOC Ingestion Trend">
          <ReactECharts option={trendOption} style={{ height: 240 }} />
        </ChartCard>
        <ChartCard title="Threat Score Distribution">
          <ReactECharts option={distributionOption} style={{ height: 240 }} />
        </ChartCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <ChartCard title="Top Malicious IPs">
          <div className="space-y-2">
            {dash?.top_malicious_ips?.length ? (
              dash.top_malicious_ips.map((ioc: any) => (
                <div key={ioc.id} className="flex items-center justify-between rounded-md border border-gray-800 bg-gray-900/50 px-3 py-2">
                  <div className="flex items-center gap-2">
                    {typeIcons[ioc.type] || typeIcons.default}
                    <span className="font-mono text-sm text-gray-200">{ioc.value}</span>
                  </div>
                  <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${severityClass(ioc.severity)}`}>{ioc.threat_score}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">No malicious IPs tracked yet.</p>
            )}
          </div>
        </ChartCard>

        <ChartCard title="Active Campaigns">
          <div className="space-y-2">
            {dash?.active_campaigns?.length ? (
              dash.active_campaigns.map((c: any) => (
                <div key={c.id} className="rounded-md border border-gray-800 bg-gray-900/50 px-3 py-2">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-sm font-medium text-white"><Target className="h-4 w-4 text-cyan-400" /> {c.campaign_name}</span>
                    <span className="text-xs text-gray-400">{c.status}</span>
                  </div>
                  <p className="mt-1 line-clamp-2 text-xs text-gray-400">{c.description}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">No active campaigns.</p>
            )}
          </div>
        </ChartCard>

        <ChartCard title="Feed Health">
          <div className="space-y-2">
            {dash?.feed_health?.map((feed: any) => (
              <div key={feed.name} className="flex items-center justify-between rounded-md border border-gray-800 bg-gray-900/50 px-3 py-2">
                <span className="text-sm text-gray-200 capitalize">{feed.name.replace(/_/g, ' ')}</span>
                {feed.healthy ? <ShieldCheck className="h-4 w-4 text-emerald-400" /> : <AlertTriangle className="h-4 w-4 text-red-400" />}
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Top Malware Families">
          <div className="space-y-2">
            {dash?.top_malware_families?.length ? (
              dash.top_malware_families.map((m: any) => (
                <div key={m.id} className="flex items-center gap-2 rounded-md border border-gray-800 bg-gray-900/50 px-3 py-2">
                  <Bug className="h-4 w-4 text-purple-400" />
                  <span className="text-sm text-gray-200">{m.family}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">No malware families indexed.</p>
            )}
          </div>
        </ChartCard>

        <ChartCard title="High-Risk Vulnerabilities">
          <div className="space-y-2">
            {dash?.high_risk_vulnerabilities?.length ? (
              dash.high_risk_vulnerabilities.map((v: any) => (
                <div key={v.id} className="rounded-md border border-gray-800 bg-gray-900/50 px-3 py-2">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-sm font-medium text-white"><Zap className="h-4 w-4 text-amber-400" /> {v.cve}</span>
                    <span className={`text-sm font-bold ${scoreColor(v.cvss_score || 0)}`}>{v.cvss_score ?? '—'}</span>
                  </div>
                  <p className="mt-1 text-xs text-gray-400">{v.description}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">No high-risk vulnerabilities.</p>
            )}
          </div>
        </ChartCard>
      </div>
    </div>
  )
}
