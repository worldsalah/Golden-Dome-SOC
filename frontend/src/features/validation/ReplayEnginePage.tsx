import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Play, RefreshCcw, ShieldCheck, ShieldX, WifiOff } from 'lucide-react'
import { getAlerts, replayAlert, type ReplayAlertResponse } from '@/services/api'
import { formatDateTime } from '@/utils/formatters'

const verdictLabels: Record<string, { color: string; text: string }> = {
  still_fires: { color: 'text-[#7cc9a5]', text: 'Still fires' },
  rule_present_no_recent_fire: { color: 'text-[#e2c495]', text: 'Rule present, no recent fire' },
  rule_missing: { color: 'text-[#e08585]', text: 'Rule missing' },
  unknown: { color: 'text-stone-400', text: 'Unknown' },
}

export function ReplayEnginePage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['alerts-replay'],
    queryFn: () => getAlerts({ limit: 25 }),
    retry: false,
  })
  const [result, setResult] = useState<ReplayAlertResponse | null>(null)
  const [replayingId, setReplayingId] = useState<number | null>(null)

  const handleReplay = async (alertId: number) => {
    setReplayingId(alertId)
    try {
      const res = await replayAlert(alertId)
      setResult(res)
    } finally {
      setReplayingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Detection Engineering · Sprint 5</p>
          <h1 className="mt-1 text-2xl font-medium tracking-[-.03em] text-stone-100">Replay Engine</h1>
          <p className="mt-1 text-xs text-stone-500">Re-evaluate existing Wazuh alerts against the current rule set without executing any real event.</p>
        </div>
        <button onClick={() => refetch()} className="btn-ghost py-2" disabled={isLoading}>
          <RefreshCcw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {isError && (
        <div className="enterprise-panel flex items-start gap-3 border-[#b94747]/30 p-4">
          <WifiOff className="mt-0.5 h-4 w-4 shrink-0 text-[#e08585]" />
          <div>
            <p className="text-sm font-medium text-stone-100">Cannot load alerts</p>
            <p className="mt-1 text-xs text-stone-500">{(error as Error)?.message}</p>
          </div>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="enterprise-panel overflow-hidden">
          <table className="table-shell">
            <thead>
              <tr>
                <th>Alert</th>
                <th>Rule</th>
                <th>Severity</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={4} className="py-10 text-center text-stone-500">Loading alerts…</td></tr>
              ) : data?.data.length === 0 ? (
                <tr><td colSpan={4} className="py-10 text-center text-stone-500">No alerts available.</td></tr>
              ) : (
                data?.data.map((a) => (
                  <tr key={a.id}>
                    <td className="font-medium text-stone-100">{a.title} <span className="font-mono text-[11px] text-stone-500">#{a.id}</span></td>
                    <td className="font-mono text-xs text-stone-300">{a.rule_id ?? '—'}</td>
                    <td className="text-stone-300">{a.severity}</td>
                    <td className="w-10">
                      <button
                        onClick={() => handleReplay(a.id)}
                        disabled={replayingId === a.id}
                        className="btn-ghost p-1.5 disabled:opacity-50"
                        title="Replay against current rules"
                      >
                        <Play className="h-3.5 w-3.5 fill-current" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="enterprise-panel p-5">
          <p className="eyebrow mb-3">Replay result</p>
          {result ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                {result.verdict === 'still_fires' ? <ShieldCheck className="h-5 w-5 text-[#7cc9a5]" /> : <ShieldX className="h-5 w-5 text-[#e2c495]" />}
                <span className={`text-lg font-semibold ${verdictLabels[result.verdict]?.color || 'text-stone-100'}`}>
                  {verdictLabels[result.verdict]?.text || result.verdict}
                </span>
              </div>
              <div className="space-y-1 text-sm text-stone-300">
                <p><span className="text-stone-500">Alert:</span> {String((result.original_event as any).title)}</p>
                <p><span className="text-stone-500">Rule ID:</span> {String((result.original_event as any).rule_id)}</p>
                <p><span className="text-stone-500">24h matches:</span> {result.match_count_24h}</p>
                <p><span className="text-stone-500">Last trigger:</span> {formatDateTime(result.last_trigger)}</p>
              </div>
              {result.suggestions.map((s, i) => (
                <p key={i} className="text-xs text-stone-400">• {s}</p>
              ))}
            </div>
          ) : (
            <p className="text-sm text-stone-500">Select an alert and press the replay button to see how it would be handled by the current Wazuh rule set.</p>
          )}
        </div>
      </div>
    </div>
  )
}
