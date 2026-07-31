import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Loader2, Plus, Search, GitMerge } from 'lucide-react'
import { StatusBadge } from '@/components/StatusBadge'
import { ChartCard } from '@/components/ChartCard'
import { formatDate } from '@/utils/formatters'
import { createIncident, listIncidents, getCorrelatedIncidents } from '@/services/api'
import { Incident } from '@/types'

export function IncidentsPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [newIncident, setNewIncident] = useState<Partial<Incident>>({
    name: '',
    severity: 'medium',
    status: 'open',
    description: '',
  })

  const { data, isLoading } = useQuery<{ data: Incident[] }>({
    queryKey: ['incidents'],
    queryFn: listIncidents,
  })

  const { data: correlatedData, isLoading: correlatedLoading } = useQuery({
    queryKey: ['correlated-incidents'],
    queryFn: () => getCorrelatedIncidents(24, 2),
    refetchInterval: 30_000,
  })

  const createMutation = useMutation({
    mutationFn: createIncident,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] })
      setShowCreate(false)
      setNewIncident({ name: '', severity: 'medium', status: 'open', description: '' })
    },
  })

  const incidents = data?.data.filter((i) => {
    const matchesStatus = statusFilter ? i.status === statusFilter : true
    const matchesSearch = search ? (i.name ?? '').toLowerCase().includes(search.toLowerCase()) : true
    return matchesStatus && matchesSearch
  }) || []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Response · Case management</p>
          <h1 className="mt-1 text-2xl font-medium tracking-[-.03em] text-stone-100">Incident cases</h1>
        </div>
        <div className="flex items-center gap-6">
          <span className="text-sm"><b className="mr-1.5 font-mono text-lg text-[#e08585]">{data?.data.filter((i) => i.status === 'open').length ?? 0}</b><span className="text-xs text-stone-500">open</span></span>
          <span className="text-sm"><b className="mr-1.5 font-mono text-lg text-[#d8b17a]">{data?.data.filter((i) => i.status === 'in_progress').length ?? 0}</b><span className="text-xs text-stone-500">in progress</span></span>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="h-3.5 w-3.5" />
            New incident
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-[240px] flex-1">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-stone-600" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search incident cases…"
            className="control w-full py-2 pl-9"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="control py-2"
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div className="enterprise-panel overflow-hidden">
        <table className="table-shell">
          <thead>
            <tr>
              <th>Case</th>
              <th>Title</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Opened</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : incidents.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No incidents.</td></tr>
            ) : (
              incidents.map((incident) => (
                <tr key={incident.id}>
                  <td className="font-mono text-[#d8b17a]">
                    <Link to={`/incidents/${incident.id}`} className="hover:underline">INC-{String(incident.id).padStart(3, '0')}</Link>
                  </td>
                  <td className="font-medium text-stone-100">{incident.name}</td>
                  <td className="capitalize"><StatusBadge status={incident.severity} /></td>
                  <td><StatusBadge status={incident.status} /></td>
                  <td className="text-stone-500">{formatDate(incident.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <ChartCard title="Auto-Correlated Incidents from Live Wazuh Alerts" className="mt-6">
        <p className="mb-3 text-xs text-gray-500">
          Automatically clustered from Wazuh alerts by source IP, rule ID, agent, and MITRE technique (last 24h).
        </p>
        {correlatedLoading ? (
          <p className="text-sm text-gray-500">Correlating alerts...</p>
        ) : (correlatedData?.incidents || []).length === 0 ? (
          <p className="text-sm text-gray-500">
            No correlated incidents detected. Correlation requires at least 2 alerts sharing a common attribute (source IP, rule, agent, or MITRE technique).
          </p>
        ) : (
          <div className="space-y-3">
            {(correlatedData?.incidents || []).map((inc, i) => (
              <motion.div
                key={inc.cluster_key}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="rounded-md border border-white/[0.07] bg-[#17181b]/50 p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <GitMerge className="mt-0.5 h-4 w-4 text-[#c97848]" />
                    <div>
                      <p className="text-sm font-semibold text-white">{inc.name}</p>
                      <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                        <span className="capitalize"><StatusBadge status={inc.severity} /></span>
                        <span>·</span>
                        <span>{inc.alert_count} alerts</span>
                        {(inc.source_ips?.length ?? 0) > 0 && <span>· IPs: {inc.source_ips.join(', ')}</span>}
                        {(inc.affected_agents?.length ?? 0) > 0 && <span>· Agents: {inc.affected_agents.join(', ')}</span>}
                        {(inc.mitre_techniques?.length ?? 0) > 0 && <span>· MITRE: {inc.mitre_techniques.join(', ')}</span>}
                      </div>
                      {inc.first_seen && inc.last_seen && (
                        <p className="mt-1 text-[10px] text-stone-600">
                          {formatDate(inc.first_seen)} → {formatDate(inc.last_seen)}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
                {((inc.timeline?.length ?? 0) > 0) && (
                  <div className="mt-3 border-t border-white/[0.05] pt-2">
                    <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-stone-600">Timeline</p>
                    <div className="max-h-32 space-y-1 overflow-y-auto">
                      {(inc.timeline ?? []).slice(0, 10).map((t, j) => (
                        <div key={j} className="flex items-center gap-2 text-[11px] text-stone-500">
                          <span className="font-mono text-stone-600">{String(t?.timestamp ?? '').slice(11, 19)}</span>
                          <span className="text-stone-400">{t?.event ?? ''}</span>
                          <span className="ml-auto text-stone-600">L{t?.level ?? ''}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </ChartCard>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="w-full max-w-lg rounded-xl border border-white/[0.1] bg-[#17181b] p-6 shadow-2xl">
            <h3 className="mb-4 text-lg font-semibold text-white">Create Incident</h3>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs text-gray-400">Name</label>
                <input value={newIncident.name} onChange={(e) => setNewIncident({ ...newIncident, name: e.target.value })} className="w-full rounded-md border border-white/[0.1] bg-gray-950 px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs text-gray-400">Severity</label>
                  <select value={newIncident.severity} onChange={(e) => setNewIncident({ ...newIncident, severity: e.target.value as Incident['severity'] })} className="w-full rounded-md border border-white/[0.1] bg-gray-950 px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none">
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-400">Status</label>
                  <select value={newIncident.status} onChange={(e) => setNewIncident({ ...newIncident, status: e.target.value as Incident['status'] })} className="w-full rounded-md border border-white/[0.1] bg-gray-950 px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none">
                    <option value="open">Open</option>
                    <option value="in_progress">In Progress</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-400">Description</label>
                <textarea value={newIncident.description} onChange={(e) => setNewIncident({ ...newIncident, description: e.target.value })} rows={3} className="w-full rounded-md border border-white/[0.1] bg-gray-950 px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none" />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setShowCreate(false)} className="rounded-md border border-white/[0.1] bg-[#1c1e22] px-4 py-2 text-sm text-gray-300 hover:bg-white/[0.08]">Cancel</button>
              <button
                onClick={() => createMutation.mutate(newIncident)}
                disabled={!newIncident.name || createMutation.isPending}
                className="flex items-center gap-2 rounded-md bg-[#7c5540] px-4 py-2 text-sm text-white hover:bg-[#8d6350] disabled:opacity-50"
              >
                {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Create
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
