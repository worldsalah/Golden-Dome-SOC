import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Download, Loader2, RefreshCw, Search } from 'lucide-react'
import { motion } from 'framer-motion'
import { PageHeader } from '@/components/PageHeader'
import { severityLabel } from '@/utils/formatters'
import apiClient, { syncAlerts, updateAlertStatus } from '@/services/api'
import { Alert } from '@/types'

const demoAlerts: Alert[] = [
  { id: 1, wazuh_alert_id: 'wazuh-1001', title: 'FortiGate deny to RDP', severity: 13, source_ip: '10.0.0.55', destination_ip: '192.168.1.10', rule_id: '100102', mitre_technique: 'T1190', status: 'new', created_at: '2024-07-25T10:00:00Z' },
  { id: 2, wazuh_alert_id: 'wazuh-1002', title: 'Port scan detected', severity: 12, source_ip: '10.0.0.55', destination_ip: '192.168.1.20', rule_id: '100101', mitre_technique: 'T1046', status: 'investigating', created_at: '2024-07-25T09:45:00Z' },
  { id: 3, wazuh_alert_id: 'wazuh-1003', title: 'Windows failed logon', severity: 8, source_ip: '192.168.1.100', rule_id: '60122', mitre_technique: 'T1110', status: 'acknowledged', created_at: '2024-07-25T08:30:00Z' },
  { id: 4, wazuh_alert_id: 'wazuh-1004', title: 'Linux sudo escalation', severity: 10, source_ip: '192.168.1.20', rule_id: '5402', mitre_technique: 'T1078', status: 'new', created_at: '2024-07-25T07:15:00Z' },
]

const statusOptions: Alert['status'][] = ['new', 'acknowledged', 'investigating', 'resolved', 'false_positive']

export function AlertsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['alerts', { page: 1, limit: 50 }],
    queryFn: async () => {
      const { data } = await apiClient.get('/alerts', { params: { page: 1, limit: 50 } })
      return data as { data: Alert[] }
    },
    initialData: { data: demoAlerts },
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => updateAlertStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  const syncMutation = useMutation({
    mutationFn: () => syncAlerts(50),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  const filteredAlerts = data.data.filter((alert) => {
    const matchesSearch =
      alert.title.toLowerCase().includes(search.toLowerCase()) ||
      alert.source_ip?.includes(search) ||
      alert.wazuh_alert_id.includes(search) ||
      alert.mitre_technique?.includes(search)
    const matchesStatus = statusFilter ? alert.status === statusFilter : true
    const matchesSeverity = severityFilter ? severityLabel(alert.severity).toLowerCase() === severityFilter : true
    return matchesSearch && matchesStatus && matchesSeverity
  })

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

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader title="Alerts" subtitle="Investigate and triage security alerts from Wazuh" />

      <div className="flex flex-col gap-4 rounded-lg border border-gray-800 bg-soc-panel p-4 md:flex-row md:items-center md:justify-between">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search title, IP, alert ID, MITRE..."
            className="w-full rounded-md border border-gray-700 bg-gray-900 py-2 pl-10 pr-4 text-sm text-white focus:border-cyan-500 focus:outline-none"
          />
        </div>
        <div className="flex flex-wrap gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
          >
            <option value="">All statuses</option>
            {statusOptions.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
          </select>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
          >
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <button
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
            className="flex items-center gap-2 rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white hover:bg-gray-700 disabled:opacity-50"
          >
            {syncMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Sync Wazuh
          </button>
          <button onClick={exportCsv} className="flex items-center gap-2 rounded-md bg-cyan-600 px-3 py-2 text-sm text-white hover:bg-cyan-500">
            <Download className="h-4 w-4" />
            Export
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-gray-800 bg-soc-panel">
        <table className="w-full text-left text-sm text-gray-300">
          <thead className="bg-gray-800/50 text-xs uppercase text-gray-400">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Source</th>
              <th className="px-4 py-3">Destination</th>
              <th className="px-4 py-3">Rule</th>
              <th className="px-4 py-3">MITRE</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading ? (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-gray-500">Loading alerts...</td>
              </tr>
            ) : filteredAlerts.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-gray-500">No alerts found.</td>
              </tr>
            ) : (
              filteredAlerts.map((alert) => (
                <tr key={alert.id} className="hover:bg-gray-800/30">
                  <td className="px-4 py-3 font-mono text-cyan-400">
                    <Link to={`/alerts/${alert.id}`} className="hover:underline">
                      #{alert.id}
                    </Link>
                  </td>
                  <td className="px-4 py-3 font-medium text-white">{alert.title}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-semibold ${alert.severity >= 10 ? 'text-red-400' : alert.severity >= 7 ? 'text-orange-400' : 'text-blue-400'}`}>
                      {severityLabel(alert.severity)}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono">{alert.source_ip || '—'}</td>
                  <td className="px-4 py-3 font-mono">{alert.destination_ip || '—'}</td>
                  <td className="px-4 py-3 font-mono text-gray-400">{alert.rule_id || '—'}</td>
                  <td className="px-4 py-3 font-mono text-cyan-300">{alert.mitre_technique || '—'}</td>
                  <td className="px-4 py-3">
                    <select
                      value={alert.status}
                      onChange={(e) => statusMutation.mutate({ id: alert.id, status: e.target.value })}
                      className="rounded-md border border-gray-700 bg-gray-900 px-2 py-1 text-xs text-white focus:border-cyan-500 focus:outline-none"
                    >
                      {statusOptions.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                    </select>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{new Date(alert.created_at).toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
