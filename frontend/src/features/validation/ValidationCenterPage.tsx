import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { RefreshCcw, ShieldQuestion, Wifi, WifiOff } from 'lucide-react'
import { getValidationCenter } from '@/services/api'
import { formatDate } from '@/utils/formatters'

const statusPill: Record<string, string> = {
  validated: 'sev-low',
  pending: 'sev-medium',
  stale: 'sev-high',
  failed: 'sev-critical',
  no_data: 'sev-medium',
}

function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 70 ? '#3ba676' : value >= 40 ? '#d8b17a' : '#b94747'
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-white/[0.08]">
        <div className="h-full rounded-full" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="font-mono text-[11px] tabular-nums text-stone-400">{value.toFixed(0)}%</span>
    </div>
  )
}

export function ValidationCenterPage() {
  const [group, setGroup] = useState('goldendome')

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['validation-center', group],
    queryFn: () => getValidationCenter(group),
    retry: false,
  })

  const summary = data?.summary
  const detections = data?.detections ?? []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Detection Engineering · Sprint 5</p>
          <h1 className="mt-1 text-2xl font-medium tracking-[-.03em] text-stone-100">Detection Validation Center</h1>
          <p className="mt-1 text-xs text-stone-500">
            {summary ? summary.data_source : 'Live data pulled directly from the Wazuh Manager API and Wazuh Indexer — no hardcoded values.'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            value={group}
            onChange={(e) => setGroup(e.target.value)}
            className="control py-2"
            placeholder="rule group"
            title="Wazuh rule group to validate"
          />
          <button onClick={() => refetch()} className="btn-ghost py-2" disabled={isFetching}>
            <RefreshCcw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {isError && (
        <div className="enterprise-panel flex items-start gap-3 border-[#b94747]/30 p-4">
          <WifiOff className="mt-0.5 h-4 w-4 shrink-0 text-[#e08585]" />
          <div>
            <p className="text-sm font-medium text-stone-100">Cannot reach Wazuh Manager / Indexer</p>
            <p className="mt-1 text-xs text-stone-500">
              {(error as Error)?.message || 'Confirm WAZUH_API_URL / OPENSEARCH_URL point to the real lab and that the backend has network access to it.'}
            </p>
          </div>
        </div>
      )}

      {summary && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-6">
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Detections</p>
            <p className="mt-1 font-mono text-2xl text-stone-100">{summary.total_detections}</p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Validated</p>
            <p className="mt-1 font-mono text-2xl text-[#7cc9a5]">{summary.validated}</p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Pending</p>
            <p className="mt-1 font-mono text-2xl text-[#e2c495]">{summary.pending}</p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Needs review</p>
            <p className="mt-1 font-mono text-2xl text-[#e08585]">{summary.no_data}</p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Avg false positive</p>
            <p className="mt-1 font-mono text-2xl text-stone-100">
              {summary.avg_false_positive_rate === null ? '—' : `${summary.avg_false_positive_rate}%`}
            </p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Alerts observed</p>
            <p className="mt-1 font-mono text-2xl text-stone-100">{summary.total_alerts_observed.toLocaleString()}</p>
          </div>
        </div>
      )}

      <div className="enterprise-panel overflow-x-auto">
        <table className="table-shell">
          <thead>
            <tr>
              <th>Detection</th>
              <th>Rule ID</th>
              <th>MITRE</th>
              <th>Severity</th>
              <th>Alerts</th>
              <th>Last trigger</th>
              <th>Status</th>
              <th>Validation</th>
              <th>Coverage</th>
              <th>FP rate</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={11} className="py-10 text-center text-stone-500">Querying Wazuh…</td></tr>
            ) : isError ? (
              <tr><td colSpan={11} className="py-10 text-center text-stone-500">No data — Wazuh unreachable.</td></tr>
            ) : detections.length === 0 ? (
              <tr><td colSpan={11} className="py-10 text-center text-stone-500">No rules found in group &quot;{group}&quot;.</td></tr>
            ) : (
              detections.map((d) => (
                <tr key={d.rule_id}>
                  <td className="max-w-[280px] font-medium text-stone-100">{d.detection_name}</td>
                  <td className="font-mono text-[#d8b17a]">{d.rule_id}</td>
                  <td className="font-mono text-xs text-stone-400">{d.mitre_technique ?? '—'}</td>
                  <td className="font-mono text-stone-300">{d.severity}</td>
                  <td className="font-mono tabular-nums text-stone-300">{(d.alert_count ?? 0).toLocaleString()}</td>
                  <td className="text-xs text-stone-500">{d.last_trigger ? formatDate(d.last_trigger) : 'Never'}</td>
                  <td>
                    <span className="pill" style={{ color: d.status === 'enabled' ? '#7cc9a5' : '#78716c' }}>
                      {d.status === 'enabled' ? <Wifi className="mr-1 inline h-3 w-3" /> : <WifiOff className="mr-1 inline h-3 w-3" />}
                      {d.status}
                    </span>
                  </td>
                  <td><span className={`pill ${statusPill[d.validation_status ?? '']}`}>{(d.validation_status ?? '').replace('_', ' ')}</span></td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-14 overflow-hidden rounded-full bg-white/[0.08]">
                        <div className="h-full rounded-full bg-[#c97848]" style={{ width: `${d.coverage_percentage ?? 0}%` }} />
                      </div>
                      <span className="font-mono text-[11px] text-stone-400">{(d.coverage_percentage ?? 0).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="font-mono text-xs text-stone-300">
                    {d.false_positive_rate === null ? (
                      <span className="inline-flex items-center gap-1 text-stone-600"><ShieldQuestion className="h-3 w-3" />n/a</span>
                    ) : (
                      `${d.false_positive_rate}% (${d.false_positive_sample_size})`
                    )}
                  </td>
                  <td><ConfidenceBar value={d.detection_confidence} /></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
