import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { RefreshCcw, WifiOff, X } from 'lucide-react'
import { getAttackCoverage, type AttackCoverageTechnique } from '@/services/api'
import { formatDate } from '@/utils/formatters'

const STATE_COLOR: Record<string, string> = {
  validated: '#3ba676',
  implemented: '#d8b17a',
  failed: '#b94747',
  missing_detection: '#3f3d38',
}

const STATE_LABEL: Record<string, string> = {
  validated: 'Validated',
  implemented: 'Implemented',
  failed: 'Failed',
  missing_detection: 'Missing detection',
}

const TACTIC_ORDER = [
  'Initial Access', 'Execution', 'Persistence', 'Privilege Escalation',
  'Defense Evasion', 'Credential Access', 'Discovery', 'Lateral Movement',
  'Collection', 'Command and Control', 'Impact',
]

export function AttackCoveragePage() {
  const [selected, setSelected] = useState<AttackCoverageTechnique | null>(null)

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['attack-coverage'],
    queryFn: () => getAttackCoverage(),
    retry: false,
  })

  const byTactic = useMemo(() => {
    const map = new Map<string, AttackCoverageTechnique[]>()
    for (const t of data?.techniques ?? []) {
      for (const tactic of t.tactic.split(',').map((s) => s.trim())) {
        if (!map.has(tactic)) map.set(tactic, [])
        map.get(tactic)!.push(t)
      }
    }
    return map
  }, [data])

  const tactics = useMemo(() => {
    const present = Array.from(byTactic.keys())
    return TACTIC_ORDER.filter((t) => present.includes(t)).concat(present.filter((t) => !TACTIC_ORDER.includes(t)))
  }, [byTactic])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Detection Engineering · Sprint 5</p>
          <h1 className="mt-1 text-2xl font-medium tracking-[-.03em] text-stone-100">ATT&amp;CK Coverage Heatmap</h1>
          <p className="mt-1 text-xs text-stone-500">{data?.data_source ?? 'Cross-referencing real MITRE technique catalog against live Wazuh detections.'}</p>
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
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Techniques tracked</p>
            <p className="mt-1 font-mono text-2xl text-stone-100">{data.total_techniques}</p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Validated</p>
            <p className="mt-1 font-mono text-2xl text-[#7cc9a5]">{data.validated_techniques}</p>
          </div>
          <div className="enterprise-panel p-4">
            <p className="eyebrow">Overall coverage</p>
            <p className="mt-1 font-mono text-2xl text-[#d8b17a]">{data.overall_coverage_percentage}%</p>
          </div>
          <div className="enterprise-panel flex items-center gap-3 p-4">
            {Object.entries(STATE_LABEL).map(([state, label]) => (
              <span key={state} className="flex items-center gap-1.5 text-[10px] text-stone-500">
                <span className="h-2 w-2 rounded-sm" style={{ background: STATE_COLOR[state] }} />
                {label}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="enterprise-panel overflow-x-auto p-4">
        {isLoading ? (
          <p className="py-10 text-center text-sm text-stone-500">Loading real ATT&amp;CK coverage…</p>
        ) : isError ? (
          <p className="py-10 text-center text-sm text-stone-500">No data — Wazuh unreachable.</p>
        ) : (
          <div className="flex gap-3" style={{ minWidth: tactics.length * 176 }}>
            {tactics.map((tactic) => {
              const techniques = byTactic.get(tactic) ?? []
              return (
                <div key={tactic} className="flex w-40 shrink-0 flex-col gap-1.5">
                  <h3 className="mb-1 truncate text-center text-[10px] font-semibold uppercase tracking-[.1em] text-stone-500" title={tactic}>
                    {tactic}
                  </h3>
                  {techniques.map((t) => (
                    <button
                      key={t.technique_id}
                      onClick={() => setSelected(t)}
                      className="rounded border p-2 text-left transition hover:scale-[1.02]"
                      style={{ background: `${STATE_COLOR[t.state]}22`, borderColor: `${STATE_COLOR[t.state]}55` }}
                    >
                      <p className="font-mono text-[10px] text-stone-300">{t.technique_id}</p>
                      <p className="mt-0.5 line-clamp-2 text-[11px] leading-tight text-stone-200">{t.name}</p>
                    </button>
                  ))}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" onClick={() => setSelected(null)}>
          <div className="w-full max-w-md rounded-xl border border-white/[0.1] bg-[#17181b] p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-[#d8b17a]">{selected.tactic}</p>
                <h3 className="text-lg font-semibold text-white">{selected.technique_id} — {selected.name}</h3>
              </div>
              <button onClick={() => setSelected(null)} className="text-stone-400 hover:text-white"><X className="h-5 w-5" /></button>
            </div>
            <span className="pill" style={{ background: `${STATE_COLOR[selected.state]}22`, color: STATE_COLOR[selected.state], border: `1px solid ${STATE_COLOR[selected.state]}55` }}>
              {STATE_LABEL[selected.state]}
            </span>
            <div className="mt-4 space-y-2 text-sm text-stone-300">
              <p><span className="text-stone-500">Mapped rules: </span>{selected.mapped_rule_count === 0 ? 'None' : selected.mapped_rule_ids.join(', ')}</p>
              <p><span className="text-stone-500">Coverage: </span>{selected.coverage_percentage.toFixed(0)}%</p>
              <p><span className="text-stone-500">Last tested: </span>{selected.last_tested ? formatDate(selected.last_tested) : 'Never'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
