import { Fragment, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, Lightbulb, RefreshCcw, WifiOff } from 'lucide-react'
import { getFalsePositiveAnalysis } from '@/services/api'

function fpColor(rate: number | null): string {
  if (rate === null) return '#78716c'
  if (rate >= 50) return '#e08585'
  if (rate >= 25) return '#e2c495'
  return '#7cc9a5'
}

export function FalsePositiveReductionPage() {
  const [expanded, setExpanded] = useState<string | null>(null)

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['fp-reduction'],
    queryFn: () => getFalsePositiveAnalysis(),
    retry: false,
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Detection Engineering · Sprint 5</p>
          <h1 className="mt-1 text-2xl font-medium tracking-[-.03em] text-stone-100">False Positive Reduction</h1>
          <p className="mt-1 text-xs text-stone-500">{data?.data_source ?? 'Analyzing real analyst dispositions and alert history per rule.'}</p>
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

      {data && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Rules analyzed</p>
            <p className="mt-1 font-mono text-2xl text-stone-100">{data.total_rules_analyzed}</p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">With disposition data</p>
            <p className="mt-1 font-mono text-2xl text-stone-100">{data.rules_with_disposition_data}</p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Avg false positive rate</p>
            <p className="mt-1 font-mono text-2xl" style={{ color: fpColor(data.avg_false_positive_rate) }}>
              {data.avg_false_positive_rate === null ? '—' : `${data.avg_false_positive_rate}%`}
            </p>
          </div>
        </div>
      )}

      <div className="enterprise-panel overflow-hidden">
        <table className="table-shell">
          <thead>
            <tr>
              <th />
              <th>Rule</th>
              <th>Alerts</th>
              <th>Real incidents</th>
              <th>False positives</th>
              <th>FP rate</th>
              <th>Repeated alerts</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={8} className="py-10 text-center text-stone-500">Analyzing real alert history…</td></tr>
            ) : isError ? (
              <tr><td colSpan={8} className="py-10 text-center text-stone-500">No data — Wazuh unreachable.</td></tr>
            ) : data?.rules.length === 0 ? (
              <tr><td colSpan={8} className="py-10 text-center text-stone-500">No rules found.</td></tr>
            ) : (
              data?.rules.map((r) => (
                <Fragment key={r.rule_id}>
                  <tr className="cursor-pointer" onClick={() => setExpanded(expanded === r.rule_id ? null : r.rule_id)}>
                    <td className="w-6">{expanded === r.rule_id ? <ChevronDown className="h-3.5 w-3.5 text-stone-500" /> : <ChevronRight className="h-3.5 w-3.5 text-stone-500" />}</td>
                    <td className="font-medium text-stone-100">{r.detection_name} <span className="ml-1 font-mono text-[11px] text-[#d8b17a]">{r.rule_id}</span></td>
                    <td className="font-mono tabular-nums text-stone-300">{r.alert_count.toLocaleString()}</td>
                    <td className="font-mono tabular-nums text-stone-300">{r.real_incidents}</td>
                    <td className="font-mono tabular-nums text-stone-300">{r.false_positive_count}</td>
                    <td className="font-mono text-xs" style={{ color: fpColor(r.false_positive_rate) }}>
                      {r.false_positive_rate === null ? 'n/a' : `${r.false_positive_rate}%`}
                    </td>
                    <td className="font-mono tabular-nums text-stone-300">{r.repeated_alerts}</td>
                    <td className="font-mono tabular-nums text-stone-300">{r.confidence.toFixed(0)}%</td>
                  </tr>
                  {expanded === r.rule_id && (
                    <tr>
                      <td colSpan={8} className="bg-white/[0.02] px-4 py-3">
                        <div className="space-y-1.5">
                          {r.suggestions.map((s, i) => (
                            <div key={i} className="flex items-start gap-2 text-xs text-stone-300">
                              <Lightbulb className="mt-0.5 h-3 w-3 shrink-0 text-[#d8b17a]" />
                              {s}
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
