import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowUpRight, Download, Loader2, RefreshCw, Search } from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'
import { severityLabel, formatTime } from '@/utils/formatters'
import apiClient, { syncAlerts, updateAlertStatus } from '@/services/api'
import { Alert } from '@/types'

const statusOptions: Alert['status'][] = ['new', 'acknowledged', 'investigating', 'resolved', 'false_positive']

function severityClass(severity: number) {
  if (severity >= 12) return 'sev-critical'
  if (severity >= 10) return 'sev-high'
  if (severity >= 7) return 'sev-medium'
  return 'sev-low'
}

export function AlertsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['alerts', { page: 1, limit: 50 }],
    queryFn: async () => {
      const { data } = await apiClient.get('/alerts', { params: { page: 1, limit: 50 } })
      return data as { data: Alert[] }
    },
    refetchInterval: 10_000,
  })

  const alerts = useMemo(() => data?.data || [], [data])

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => updateAlertStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  const syncMutation = useMutation({
    mutationFn: () => syncAlerts(50),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  const filteredAlerts = useMemo(
    () =>
      alerts.filter((alert) => {
        const matchesSearch =
          (alert.title ?? '').toLowerCase().includes(search.toLowerCase()) ||
          (alert.source_ip ?? '').includes(search) ||
          (alert.wazuh_alert_id ?? '').includes(search) ||
          (alert.mitre_technique ?? '').includes(search)
        const matchesStatus = statusFilter ? alert.status === statusFilter : true
        const matchesSeverity = severityFilter ? severityLabel(alert.severity).toLowerCase() === severityFilter : true
        return matchesSearch && matchesStatus && matchesSeverity
      }),
    [alerts, search, statusFilter, severityFilter],
  )

  const selected = filteredAlerts.find((a) => a.id === selectedId) ?? filteredAlerts[0] ?? null

  const exportCsv = () => {
    const headers = ['id', 'title', 'severity', 'status', 'source_ip', 'destination_ip', 'rule_id', 'mitre_technique', 'created_at']
    const rows = filteredAlerts.map((a) => headers.map((h) => `"${String((a as unknown as Record<string, unknown>)[h] ?? '').replace(/"/g, '\\"')}"`).join(','))
    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `alerts-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const counts = useMemo(() => {
    const critical = alerts.filter((a) => a.severity >= 12).length
    const open = alerts.filter((a) => a.status === 'new' || a.status === 'investigating').length
    return { total: alerts.length, critical, open }
  }, [alerts])

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Detection · Triage</p>
          <h1 className="mt-1 text-2xl font-medium tracking-[-.03em] text-stone-100">Alert queue</h1>
        </div>
        <div className="flex items-center gap-6 text-sm">
          <span><b className="mr-1.5 font-mono text-lg text-stone-100">{counts.total}</b><span className="text-xs text-stone-500">in queue</span></span>
          <span><b className="mr-1.5 font-mono text-lg text-[#e08585]">{counts.critical}</b><span className="text-xs text-stone-500">critical</span></span>
          <span><b className="mr-1.5 font-mono text-lg text-[#d8b17a]">{counts.open}</b><span className="text-xs text-stone-500">open</span></span>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-[240px] flex-1">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-stone-600" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search title, IP, alert ID, MITRE technique…"
            className="control w-full py-2 pl-9"
          />
        </div>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="control py-2">
          <option value="">All statuses</option>
          {statusOptions.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
        <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="control py-2">
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <button onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending} className="btn-ghost py-2">
          {syncMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
          Sync Wazuh
        </button>
        <button onClick={exportCsv} className="btn-primary py-2">
          <Download className="h-3.5 w-3.5" /> Export
        </button>
      </div>

      {/* Workspace: queue + investigation */}
      <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        {/* Queue */}
        <div className="enterprise-panel overflow-hidden">
          <div className="panel-header">
            <span className="panel-title">Live queue</span>
            <span className="text-[10px] text-stone-600">{filteredAlerts.length} shown</span>
          </div>
          <div className="max-h-[62vh] overflow-y-auto">
            {isLoading ? (
              <p className="px-4 py-10 text-center text-sm text-stone-600">Loading alerts…</p>
            ) : filteredAlerts.length === 0 ? (
              <p className="px-4 py-10 text-center text-sm text-stone-600">No alerts match the current filters.</p>
            ) : (
              filteredAlerts.map((alert) => {
                const active = selected?.id === alert.id
                return (
                  <button
                    key={alert.id}
                    onClick={() => setSelectedId(alert.id)}
                    className={`block w-full border-b border-white/[0.05] px-4 py-3 text-left transition-colors ${
                      active ? 'bg-white/[0.05]' : 'hover:bg-white/[0.02]'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex min-w-0 items-center gap-3">
                        <span className={`pill ${severityClass(alert.severity)}`}>{severityLabel(alert.severity)}</span>
                        <span className="truncate text-[13px] font-medium text-stone-200">{alert.title}</span>
                      </div>
                      <span className="shrink-0 font-mono text-[10px] text-stone-600">
                        {formatTime(alert.created_at)}
                      </span>
                    </div>
                    <div className="mt-1.5 flex items-center gap-4 font-mono text-[11px] text-stone-500">
                      <span>#{alert.id}</span>
                      {alert.source_ip && <span>{alert.source_ip}</span>}
                      {alert.mitre_technique && <span className="text-[#d8b17a]">{alert.mitre_technique}</span>}
                      <span className="ml-auto capitalize text-stone-600">{(alert.status ?? '').replace('_', ' ')}</span>
                    </div>
                  </button>
                )
              })
            )}
          </div>
        </div>

        {/* Investigation panel */}
        <div className="enterprise-panel h-fit overflow-hidden">
          <div className="panel-header">
            <span className="panel-title">Investigation</span>
            {selected && (
              <Link to={`/alerts/${selected.id}`} className="flex items-center gap-1 text-[11px] text-[#d8b17a] transition hover:text-[#e8d2af]">
                Full case view <ArrowUpRight className="h-3 w-3" />
              </Link>
            )}
          </div>
          <AnimatePresence mode="wait">
            {selected ? (
              <motion.div
                key={selected.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.18 }}
                className="p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-base font-medium text-stone-100">{selected.title}</h2>
                  <span className={`pill ${severityClass(selected.severity)}`}>{severityLabel(selected.severity)}</span>
                </div>
                <p className="mt-1 font-mono text-[11px] text-stone-600">{selected.wazuh_alert_id}</p>

                <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-4">
                  <div><dt>Source IP</dt><dd className="font-mono text-sm">{selected.source_ip || '—'}</dd></div>
                  <div><dt>Destination IP</dt><dd className="font-mono text-sm">{selected.destination_ip || '—'}</dd></div>
                  <div><dt>Rule</dt><dd className="font-mono text-sm">{selected.rule_id || '—'}</dd></div>
                  <div><dt>MITRE technique</dt><dd className="font-mono text-sm text-[#d8b17a]">{selected.mitre_technique || '—'}</dd></div>
                  <div><dt>Detected</dt><dd className="text-sm">{new Date(selected.created_at).toLocaleString()}</dd></div>
                  <div>
                    <dt>Status</dt>
                    <dd>
                      <select
                        value={selected.status}
                        onChange={(e) => statusMutation.mutate({ id: selected.id, status: e.target.value })}
                        className="control mt-0.5"
                      >
                        {statusOptions.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                      </select>
                    </dd>
                  </div>
                </dl>

                <div className="mt-6 border-t border-white/[0.07] pt-4">
                  <p className="eyebrow">Recommended next steps</p>
                  <ul className="mt-3 space-y-2 text-[13px] text-stone-400">
                    <li className="flex gap-2"><span className="text-[#c97848]">01</span> Validate source reputation in Threat Intelligence.</li>
                    <li className="flex gap-2"><span className="text-[#c97848]">02</span> Review related events on the affected asset.</li>
                    <li className="flex gap-2"><span className="text-[#c97848]">03</span> Escalate to an incident if activity is confirmed.</li>
                  </ul>
                  <div className="mt-5 flex gap-2">
                    <Link to={`/alerts/${selected.id}`} className="btn-primary">Open investigation</Link>
                    <Link to="/ai" className="btn-ghost">Ask AI analyst</Link>
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.p key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="px-4 py-10 text-center text-sm text-stone-600">
                Select an alert to open the investigation panel.
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
