import { useQuery } from '@tanstack/react-query'
import { Activity, AlertTriangle, BarChart3, Database, Gauge, RefreshCcw, Server, WifiOff } from 'lucide-react'
import { getDetectionPerformance } from '@/services/api'

export function DetectionPerformancePage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['detection-performance'],
    queryFn: () => getDetectionPerformance(),
    retry: false,
  })

  const stats = [
    { label: 'Manager API latency', value: data ? `${data.api_latency_ms.toFixed(1)} ms` : '—', icon: Server, color: data && data.api_latency_ms < 500 ? 'text-[#7cc9a5]' : 'text-[#e2c495]' },
    { label: 'Indexer latency', value: data ? `${data.indexer_latency_ms.toFixed(1)} ms` : '—', icon: Database, color: data && data.indexer_latency_ms < 500 ? 'text-[#7cc9a5]' : 'text-[#e2c495]' },
    { label: 'Events / second', value: data?.events_per_second?.toFixed(2) ?? '—', icon: BarChart3, color: 'text-stone-100' },
    { label: 'Alerts / hour', value: data?.alerts_per_hour?.toFixed(2) ?? '—', icon: Activity, color: 'text-stone-100' },
    { label: 'Indexer volume 24h', value: data?.indexer_alert_volume_24h?.toLocaleString() ?? '—', icon: Gauge, color: 'text-stone-100' },
    { label: 'Drop %', value: data?.drop_percentage !== null && data?.drop_percentage !== undefined ? `${data.drop_percentage}%` : '—', icon: AlertTriangle, color: data && (data.drop_percentage ?? 0) > 5 ? 'text-[#e08585]' : 'text-[#7cc9a5]' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Detection Engineering · Sprint 5</p>
          <h1 className="mt-1 text-2xl font-medium tracking-[-.03em] text-stone-100">Detection Performance</h1>
          <p className="mt-1 text-xs text-stone-500">{data?.data_source ?? 'Real-time throughput and latency from Wazuh Manager API and Indexer.'}</p>
        </div>
        <button onClick={() => refetch()} className="btn-ghost py-2" disabled={isFetching}>
          <RefreshCcw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {isError && (
        <div className="enterprise-panel flex items-start gap-3 border-[#b94747]/30 p-4">
          <WifiOff className="mt-0.5 h-4 w-4 shrink-0 text-[#e08585]" />
          <div>
            <p className="text-sm font-medium text-stone-100">Cannot reach Wazuh Manager / Indexer</p>
            <p className="mt-1 text-xs text-stone-500">{(error as Error)?.message}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        {stats.map((s) => (
          <div key={s.label} className="enterprise-panel p-4">
            <div className="flex items-center gap-2 text-stone-500">
              <s.icon className="h-3.5 w-3.5" />
              <p className="eyebrow">{s.label}</p>
            </div>
            <p className={`mt-2 font-mono text-2xl ${isLoading ? 'animate-pulse text-stone-600' : s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      <div className="enterprise-panel overflow-hidden">
        <table className="table-shell">
          <thead>
            <tr>
              <th>Daemon</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={2} className="py-10 text-center text-stone-500">Probing Wazuh Manager status…</td></tr>
            ) : isError ? (
              <tr><td colSpan={2} className="py-10 text-center text-stone-500">No data — Wazuh unreachable.</td></tr>
            ) : data?.daemon_health.length === 0 ? (
              <tr><td colSpan={2} className="py-10 text-center text-stone-500">No daemon status returned.</td></tr>
            ) : (
              data?.daemon_health.map((d) => (
                <tr key={d.name}>
                  <td className="font-mono text-sm text-stone-100">{d.name}</td>
                  <td className="text-sm">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${(d.status ?? '').toLowerCase() === 'running' ? 'bg-[#4b6a52]/20 text-[#7cc9a5]' : 'bg-[#7a3f3f]/20 text-[#e08585]'}`}>
                      {d.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {data?.manager_stats_raw && Object.keys(data.manager_stats_raw).length > 0 && (
        <div className="enterprise-panel p-4">
          <p className="eyebrow mb-2">Latest manager stats snapshot</p>
          <pre className="max-h-64 overflow-auto rounded-md bg-black/30 p-3 font-mono text-xs text-stone-300">
            {JSON.stringify(data.manager_stats_raw, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
