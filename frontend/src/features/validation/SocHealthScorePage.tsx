import { useQuery } from '@tanstack/react-query'
import { Activity, Award, Clock, RefreshCcw, ShieldAlert, WifiOff } from 'lucide-react'
import { getSocHealthScore } from '@/services/api'

const componentLabels: Record<string, string> = {
  detection_validation: 'Detection validation',
  attack_coverage: 'ATT&CK coverage',
  false_positive_control: 'False-positive control',
  backlog: 'Alert/incident backlog',
  platform_performance: 'Platform performance',
}

const componentIcons: Record<string, typeof Activity> = {
  detection_validation: ShieldAlert,
  attack_coverage: Award,
  false_positive_control: ShieldAlert,
  backlog: Clock,
  platform_performance: Activity,
}

const gradeColor: Record<string, string> = {
  'A+': 'text-[#7cc9a5]',
  A: 'text-[#7cc9a5]',
  B: 'text-[#e2c495]',
  C: 'text-[#e08585]',
  D: 'text-[#e08585]',
}

export function SocHealthScorePage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['soc-health-score'],
    queryFn: () => getSocHealthScore(),
    retry: false,
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Detection Engineering · Sprint 5</p>
          <h1 className="mt-1 text-2xl font-medium tracking-[-.03em] text-stone-100">SOC Health Score</h1>
          <p className="mt-1 text-xs text-stone-500">{data?.data_source ?? 'Aggregated grade from real detection, coverage, backlog and performance metrics.'}</p>
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

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="enterprise-panel flex flex-col items-center justify-center p-8">
          <p className="eyebrow">Overall grade</p>
          {isLoading ? (
            <div className="mt-4 h-20 w-20 animate-pulse rounded-full bg-stone-800" />
          ) : (
            <div className={`mt-2 font-mono text-8xl font-semibold tracking-tight ${data ? gradeColor[data.grade] || 'text-stone-100' : 'text-stone-100'}`}>
              {data?.grade ?? '—'}
            </div>
          )}
          <p className="mt-4 font-mono text-3xl text-stone-100">{data ? data.overall_score.toFixed(1) : '—'}<span className="text-sm text-stone-500">/100</span></p>
        </div>

        <div className="enterprise-panel p-6 lg:col-span-2">
          <p className="eyebrow mb-4">Component scores</p>
          <div className="space-y-4">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-6 animate-pulse rounded bg-stone-800" />
              ))
            ) : (
              data && Object.entries(data.components).map(([key, score]) => {
                const Icon = componentIcons[key] || Activity
                return (
                  <div key={key} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2 text-stone-300">
                        <Icon className="h-3.5 w-3.5" />
                        {componentLabels[key] || key}
                      </div>
                      <span className="font-mono text-stone-100">{score.toFixed(1)}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-stone-800">
                      <div
                        className="h-full rounded-full bg-[#d8b17a]"
                        style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                      />
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>

      {data && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Open alerts</p>
            <p className="mt-2 font-mono text-2xl text-stone-100">{data.open_alerts.toLocaleString()}</p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Open incidents</p>
            <p className="mt-2 font-mono text-2xl text-stone-100">{data.open_incidents.toLocaleString()}</p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Detection validation</p>
            <p className="mt-2 font-mono text-2xl text-stone-100">{data.components.detection_validation.toFixed(1)}</p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">ATT&CK coverage</p>
            <p className="mt-2 font-mono text-2xl text-stone-100">{data.components.attack_coverage.toFixed(1)}</p>
          </div>
        </div>
      )}
    </div>
  )
}
