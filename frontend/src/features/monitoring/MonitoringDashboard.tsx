import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Gauge } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { getServerMetrics, getContainerMetrics, getMonitoringServiceHealth } from '@/services/api'
import { StatusHeader } from './components/StatusHeader'
import { ServerResourceCards } from './components/ServerResourceCards'
import { ContainerTable } from './components/ContainerTable'
import { ServiceHealthGrid } from './components/ServiceHealthGrid'
import { MonitoringCharts } from './components/Charts'

const GRAFANA_URL = import.meta.env.VITE_GRAFANA_URL as string | undefined

export function MonitoringDashboard() {
  const [tab, setTab] = useState<'overview' | 'advanced'>('overview')

  const { data: server } = useQuery({
    queryKey: ['monitoring-server'],
    queryFn: getServerMetrics,
    refetchInterval: 7000,
  })

  const { data: containers } = useQuery({
    queryKey: ['monitoring-containers'],
    queryFn: getContainerMetrics,
    refetchInterval: 10000,
  })

  const { data: services } = useQuery({
    queryKey: ['monitoring-services'],
    queryFn: getMonitoringServiceHealth,
    refetchInterval: 7000,
  })

  return (
    <div className="space-y-6">
      <PageHeader title="Infrastructure Monitoring" subtitle="Real-time health of the Golden Dome SOC platform" />

      <div className="flex items-center gap-1 rounded-lg border border-white/[0.08] bg-[#131417] p-1 w-fit">
        <button
          onClick={() => setTab('overview')}
          className={`flex items-center gap-1.5 rounded-md px-3.5 py-1.5 text-xs font-medium transition ${
            tab === 'overview' ? 'bg-[#c97848] text-white' : 'text-stone-500 hover:text-stone-300'
          }`}
        >
          <Gauge className="h-3.5 w-3.5" /> Overview
        </button>
        <button
          onClick={() => setTab('advanced')}
          className={`flex items-center gap-1.5 rounded-md px-3.5 py-1.5 text-xs font-medium transition ${
            tab === 'advanced' ? 'bg-[#c97848] text-white' : 'text-stone-500 hover:text-stone-300'
          }`}
        >
          <LineChart className="h-3.5 w-3.5" /> Advanced Metrics (Grafana)
        </button>
      </div>

      {tab === 'overview' ? (
        <div className="space-y-6">
          {services && <StatusHeader services={services} lastUpdated={Date.now()} />}
          {server && <ServerResourceCards metrics={server} />}
          <MonitoringCharts />
          <ContainerTable containers={containers || []} />
          {services && <ServiceHealthGrid services={services} />}
        </div>
      ) : (
        <div className="enterprise-panel p-0 overflow-hidden">
          {GRAFANA_URL ? (
            <iframe title="Grafana" src={GRAFANA_URL} className="h-[80vh] w-full border-0" />
          ) : (
            <div className="flex h-64 flex-col items-center justify-center gap-2 text-center">
              <LineChart className="h-8 w-8 text-stone-700" />
              <p className="text-sm text-stone-500">Grafana is not configured.</p>
              <p className="max-w-sm text-xs text-stone-600">
                Set VITE_GRAFANA_URL to embed the advanced Grafana dashboards here, or deploy Grafana
                alongside Prometheus using docker-compose.monitoring.yml.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
