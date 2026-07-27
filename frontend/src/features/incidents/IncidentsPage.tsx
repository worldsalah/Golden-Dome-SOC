import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Loader2, Plus, Search } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { StatusBadge } from '@/components/StatusBadge'
import { formatDate } from '@/utils/formatters'
import { createIncident, listIncidents } from '@/services/api'
import { Incident } from '@/types'

const demoIncidents: Incident[] = [
  { id: 1, name: 'RDP brute-force campaign', severity: 'high', status: 'open', created_at: '2024-07-25T09:00:00Z' },
  { id: 2, name: 'Suspicious DNS exfiltration', severity: 'medium', status: 'in_progress', created_at: '2024-07-24T16:20:00Z' },
]

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

  const { data, isLoading } = useQuery({
    queryKey: ['incidents'],
    queryFn: listIncidents,
    initialData: { data: demoIncidents },
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
    const matchesSearch = search ? i.name.toLowerCase().includes(search.toLowerCase()) : true
    return matchesStatus && matchesSearch
  }) || []

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <PageHeader title="Incidents" subtitle="Manage and track security incidents" />
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-sm text-white hover:bg-cyan-500"
        >
          <Plus className="h-4 w-4" />
          New Incident
        </button>
      </div>

      <div className="flex flex-col gap-3 rounded-lg border border-gray-800 bg-soc-panel p-4 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search incidents..."
            className="w-full rounded-md border border-gray-700 bg-gray-900 py-2 pl-10 pr-4 text-sm text-white focus:border-cyan-500 focus:outline-none"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div className="overflow-hidden rounded-lg border border-gray-800 bg-soc-panel">
        <table className="w-full text-left text-sm text-gray-300">
          <thead className="bg-gray-800/50 text-xs uppercase text-gray-400">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : incidents.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No incidents.</td></tr>
            ) : (
              incidents.map((incident) => (
                <tr key={incident.id} className="hover:bg-gray-800/30">
                  <td className="px-4 py-3 font-mono text-cyan-400">
                    <Link to={`/incidents/${incident.id}`} className="hover:underline">#{incident.id}</Link>
                  </td>
                  <td className="px-4 py-3 font-medium text-white">{incident.name}</td>
                  <td className="px-4 py-3 capitalize"><StatusBadge status={incident.severity} /></td>
                  <td className="px-4 py-3"><StatusBadge status={incident.status} /></td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(incident.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="w-full max-w-lg rounded-xl border border-gray-700 bg-gray-900 p-6 shadow-2xl">
            <h3 className="mb-4 text-lg font-semibold text-white">Create Incident</h3>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs text-gray-400">Name</label>
                <input value={newIncident.name} onChange={(e) => setNewIncident({ ...newIncident, name: e.target.value })} className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs text-gray-400">Severity</label>
                  <select value={newIncident.severity} onChange={(e) => setNewIncident({ ...newIncident, severity: e.target.value as Incident['severity'] })} className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none">
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-400">Status</label>
                  <select value={newIncident.status} onChange={(e) => setNewIncident({ ...newIncident, status: e.target.value as Incident['status'] })} className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none">
                    <option value="open">Open</option>
                    <option value="in_progress">In Progress</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-400">Description</label>
                <textarea value={newIncident.description} onChange={(e) => setNewIncident({ ...newIncident, description: e.target.value })} rows={3} className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setShowCreate(false)} className="rounded-md border border-gray-700 bg-gray-800 px-4 py-2 text-sm text-gray-300 hover:bg-gray-700">Cancel</button>
              <button
                onClick={() => createMutation.mutate(newIncident)}
                disabled={!newIncident.name || createMutation.isPending}
                className="flex items-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-sm text-white hover:bg-cyan-500 disabled:opacity-50"
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
