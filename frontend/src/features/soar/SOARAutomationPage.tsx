import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Activity,
  CheckCircle,
  LayoutDashboard,
  Loader2,
  Play,
  Plus,
  ShieldAlert,
  Trash2,
  X,
  Zap,
} from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import ReactECharts from 'echarts-for-react'
import * as echarts from 'echarts'
import {
  createPlaybook,
  decideApproval,
  deletePlaybook,
  exportPlaybook,
  getExecutionEvidence,
  getExecutionLogs,
  getExecutionTimeline,
  getSOARStatistics,
  importPlaybook,
  listApprovals,
  listExecutions,
  listPlaybooks,
  runPlaybook,
  updatePlaybook,
} from '@/services/api'
import { type Playbook, type PlaybookExecution, type WorkflowApproval } from '@/types'
import { PlaybookBuilder } from './PlaybookBuilder'

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'playbooks', label: 'Playbooks', icon: Zap },
  { id: 'executions', label: 'Executions', icon: Activity },
  { id: 'approvals', label: 'Approvals', icon: ShieldAlert },
]

const emptyPlaybook = (): Partial<Playbook> => ({
  name: '',
  description: '',
  trigger: 'manual',
  status: 'active',
  category: 'response',
  version: '1.0.0',
  tags: '',
  actions: [],
  nodes: [{ id: 'trigger', type: 'trigger', name: 'Start', config: {}, next_nodes: ['end'] }, { id: 'end', type: 'end', name: 'End', config: {}, next_nodes: [] }],
})

export function SOARAutomationPage() {
  const [tab, setTab] = useState('dashboard')
  const queryClient = useQueryClient()

  const { data: stats } = useQuery({ queryKey: ['soar-statistics'], queryFn: getSOARStatistics })
  const { data: playbooksData, isLoading: playbooksLoading } = useQuery({ queryKey: ['playbooks'], queryFn: listPlaybooks })
  const { data: executionsData } = useQuery({ queryKey: ['playbook-executions'], queryFn: () => listExecutions() })
  const { data: approvalsData } = useQuery({ queryKey: ['workflow-approvals'], queryFn: () => listApprovals('pending') })

  const createMutation = useMutation({
    mutationFn: createPlaybook,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['playbooks'] }); setEditing(null) },
  })
  const updateMutation = useMutation({
    mutationFn: (pb: Playbook) => updatePlaybook(pb.id, pb),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['playbooks'] }); setEditing(null) },
  })
  const deleteMutation = useMutation({
    mutationFn: deletePlaybook,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['playbooks'] }),
  })
  const runMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input?: Record<string, unknown> }) => runPlaybook(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['playbook-executions'] }),
  })
  const approvalMutation = useMutation({
    mutationFn: ({ id, decision }: { id: number; decision: 'approved' | 'denied' }) => decideApproval(id, decision),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['workflow-approvals'] }); queryClient.invalidateQueries({ queryKey: ['playbook-executions'] }) },
  })

  const [editing, setEditing] = useState<Partial<Playbook> | null>(null)
  const [form, setForm] = useState<Partial<Playbook>>(emptyPlaybook())
  const [selectedExecution, setSelectedExecution] = useState<PlaybookExecution | null>(null)

  const { data: timeline } = useQuery({
    queryKey: ['execution-timeline', selectedExecution?.id],
    queryFn: () => getExecutionTimeline(selectedExecution!.id),
    enabled: !!selectedExecution,
  })
  const { data: evidence } = useQuery({
    queryKey: ['execution-evidence', selectedExecution?.id],
    queryFn: () => getExecutionEvidence(selectedExecution!.id),
    enabled: !!selectedExecution,
  })
  const { data: logs } = useQuery({
    queryKey: ['execution-logs', selectedExecution?.id],
    queryFn: () => getExecutionLogs(selectedExecution!.id),
    enabled: !!selectedExecution,
  })

  const playbooks = playbooksData?.data || []
  const executions = executionsData?.data || []
  const approvals = approvalsData || []

  const openCreate = () => {
    setForm(emptyPlaybook())
    setEditing({ id: 0, ...emptyPlaybook() } as unknown as Partial<Playbook>)
  }

  const openEdit = (pb: Playbook) => {
    setEditing(pb)
    setForm({ ...pb })
  }

  const save = () => {
    if (!form.name) return
    if (editing && (editing as Playbook).id > 0) {
      updateMutation.mutate({ ...(editing as Playbook), ...form } as Playbook)
    } else {
      createMutation.mutate(form)
    }
  }

  const statusColor = (status: string) => {
    if (status === 'completed') return 'bg-emerald-500/10 text-emerald-400'
    if (status === 'failed' || status === 'cancelled') return 'bg-red-500/10 text-red-400'
    if (status === 'awaiting_approval') return 'bg-yellow-500/10 text-yellow-400'
    return 'bg-[#d8b17a]/10 text-[#d8b17a]'
  }

  const statusChartOption = useMemo(() => {
    if (!stats) return {}
    const counts = stats.execution_status_counts
    const entries = Object.entries(counts)
    return {
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: entries.map(([k]) => k), axisLine: { lineStyle: { color: '#6b7280' } } },
      yAxis: { type: 'value', axisLine: { lineStyle: { color: '#6b7280' } }, splitLine: { lineStyle: { color: '#374151' } } },
      series: [{ data: entries.map(([, v]) => v), type: 'bar', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#c97848' }, { offset: 1, color: '#0891b2' }]) } }],
    }
  }, [stats])

  const topPlaybooksOption = useMemo(() => {
    if (!stats) return {}
    return {
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value', axisLine: { lineStyle: { color: '#6b7280' } }, splitLine: { lineStyle: { color: '#374151' } } },
      yAxis: { type: 'category', data: [...stats.most_executed_playbooks.map((p) => p.name)].reverse(), axisLine: { lineStyle: { color: '#6b7280' } } },
      series: [{ data: [...stats.most_executed_playbooks.map((p) => p.count)].reverse(), type: 'bar', itemStyle: { color: '#10b981' } }],
    }
  }, [stats])

  const addAction = () => {
    setForm({ ...form, actions: [...(form.actions || []), { action: 'block_ip', params: {} }] })
  }

  const updateAction = (index: number, action: { action: string; params: Record<string, unknown> }) => {
    const actions = [...(form.actions || [])]
    actions[index] = action
    setForm({ ...form, actions })
  }

  const removeAction = (index: number) => {
    const actions = [...(form.actions || [])]
    actions.splice(index, 1)
    setForm({ ...form, actions })
  }

  return (
    <div className="space-y-6">
      <PageHeader title="SOAR Automation" subtitle="Orchestrate incident response with intelligent playbooks" />

      <div className="flex items-center gap-2 border-b border-white/[0.07] pb-1">
        {TABS.map((t) => {
          const Icon = t.icon
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${tab === t.id ? 'border-b-2 border-[#c97848] text-[#d8b17a]' : 'text-gray-400 hover:text-gray-200'}`}
            >
              <Icon className="h-4 w-4" /> {t.label}
            </button>
          )
        })}
      </div>

      {tab === 'dashboard' && (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <ChartCard title="Playbooks" value={stats?.total_playbooks ?? '-'} subtitle={`${stats?.active_playbooks ?? 0} active`} icon={Zap} />
            <ChartCard title="Executions" value={stats?.total_executions ?? '-'} subtitle={`${stats?.completed_executions ?? 0} completed`} icon={Activity} />
            <ChartCard title="Failed" value={stats?.failed_executions ?? '-'} subtitle="Last 24h pipeline" icon={ShieldAlert} />
            <ChartCard title="Pending Approvals" value={stats?.pending_approvals ?? '-'} subtitle="Awaiting analyst" icon={CheckCircle} />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <ChartCard title="Execution Status Distribution">
              <ReactECharts option={statusChartOption} style={{ height: 250 }} />
            </ChartCard>
            <ChartCard title="Most Executed Playbooks">
              <ReactECharts option={topPlaybooksOption} style={{ height: 250 }} />
            </ChartCard>
          </div>
          {stats && (
            <div className="rounded-lg border border-white/[0.07] bg-soc-panel p-4">
              <h4 className="text-sm font-semibold text-gray-200">Automation Health</h4>
              <div className="mt-2 grid gap-4 md:grid-cols-3">
                <div>
                  <p className="text-xs text-gray-500">Avg Execution Time</p>
                  <p className="text-lg font-semibold text-white">{stats.avg_execution_time_ms.toFixed(0)} ms</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Automation Success Rate</p>
                  <p className="text-lg font-semibold text-white">
                    {stats.total_executions ? ((stats.completed_executions / stats.total_executions) * 100).toFixed(1) : 0}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Manual vs Automated</p>
                  <p className="text-lg font-semibold text-white">
                    {stats.total_executions - stats.pending_approvals} / {stats.pending_approvals}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'playbooks' && (
        <div className="space-y-4">
          <div className="flex justify-end gap-2">
            <label className="flex cursor-pointer items-center gap-2 rounded-md border border-white/[0.1] bg-[#1c1e22] px-4 py-2 text-sm text-white hover:bg-white/[0.08]">
              <Plus className="h-4 w-4" /> Import
              <input
                type="file"
                accept="application/json"
                className="hidden"
                onChange={async (e) => {
                  const file = e.target.files?.[0]
                  if (!file) return
                  const text = await file.text()
                  try {
                    const json = JSON.parse(text)
                    await importPlaybook(json)
                    queryClient.invalidateQueries({ queryKey: ['playbooks'] })
                  } catch {
                    // ignore invalid JSON
                  }
                  e.target.value = ''
                }}
              />
            </label>
            <button onClick={openCreate} className="flex items-center gap-2 rounded-md bg-[#7c5540] px-4 py-2 text-sm text-white hover:bg-[#8d6350]">
              <Plus className="h-4 w-4" /> New Playbook
            </button>
          </div>
          {playbooksLoading ? (
            <p className="text-sm text-gray-500">Loading playbooks...</p>
          ) : playbooks.length === 0 ? (
            <p className="text-sm text-gray-500">No playbooks found.</p>
          ) : (
            <div className="grid gap-4">
              {playbooks.map((pb) => (
                <motion.div key={pb.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="rounded-lg border border-white/[0.07] bg-soc-panel p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-white">{pb.name}</h4>
                        {pb.is_builtin && <span className="rounded-full bg-[#d8b17a]/10 px-2 py-0.5 text-xs text-[#d8b17a]">Built-in</span>}
                        <span className={`rounded-full px-2 py-0.5 text-xs ${pb.status === 'active' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-700 text-gray-300'}`}>{pb.status}</span>
                      </div>
                      <p className="text-xs text-gray-500 capitalize">{pb.trigger} • {pb.category} • v{pb.version}</p>
                      <p className="mt-1 text-sm text-gray-400">{pb.description}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {pb.actions.map((a, idx) => (
                          <span key={idx} className="rounded-full bg-[#1c1e22] px-2 py-0.5 text-xs text-[#d8b17a]">{a.action}</span>
                        ))}
                        {pb.nodes.map((n) => (
                          <span key={n.id} className="rounded-full bg-[#1c1e22] px-2 py-0.5 text-xs text-emerald-400">{n.type}</span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={async () => {
                        const data = await exportPlaybook(pb.id)
                        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `${pb.name.replace(/\s+/g, '_').toLowerCase()}_playbook.json`
                        a.click()
                        URL.revokeObjectURL(url)
                      }} className="rounded-md border border-white/[0.1] bg-[#1c1e22] px-3 py-1.5 text-xs text-white hover:bg-white/[0.08]" title="Export">Export</button>
                      <button onClick={() => openEdit(pb)} className="rounded-md border border-white/[0.1] bg-[#1c1e22] px-3 py-1.5 text-xs text-white hover:bg-white/[0.08]">Edit</button>
                      <button onClick={() => runMutation.mutate({ id: pb.id, input: { ip: '10.0.0.55', host: 'workstation-01' } })} disabled={pb.status !== 'active' || runMutation.isPending} className="flex items-center gap-1 rounded-md bg-emerald-600 px-3 py-1.5 text-xs text-white hover:bg-emerald-500 disabled:opacity-50">
                        {runMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />} Run
                      </button>
                      {!pb.is_builtin && (
                        <button onClick={() => deleteMutation.mutate(pb.id)} className="rounded-md bg-red-600/10 p-1.5 text-red-400 hover:bg-red-600/20"><Trash2 className="h-4 w-4" /></button>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'executions' && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-3 lg:col-span-1">
            <h3 className="text-sm font-semibold text-gray-200">Recent Executions</h3>
            {executions.length === 0 && <p className="text-sm text-gray-500">No executions yet.</p>}
            {executions.map((exec: PlaybookExecution) => (
              <button key={exec.id} onClick={() => setSelectedExecution(exec)} className={`w-full rounded-md border p-3 text-left transition ${selectedExecution?.id === exec.id ? 'border-[#c97848] bg-[#2a2320]' : 'border-white/[0.07] bg-[#17181b]/50 hover:bg-[#17181b]'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-white">Run #{exec.id}</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs ${statusColor(exec.status)}`}>{exec.status}</span>
                </div>
                <p className="mt-1 text-xs text-gray-500">Playbook {exec.playbook_id} • {new Date(exec.started_at).toLocaleString()}</p>
                {exec.current_node_id && <p className="mt-1 text-xs text-yellow-400">Node: {exec.current_node_id}</p>}
              </button>
            ))}
          </div>
          <div className="lg:col-span-2 space-y-4">
            {selectedExecution ? (
              <>
                <div className="rounded-lg border border-white/[0.07] bg-soc-panel p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-white">Execution #{selectedExecution.id}</h3>
                    <button onClick={() => setSelectedExecution(null)} className="text-gray-500 hover:text-gray-300"><X className="h-4 w-4" /></button>
                  </div>
                  <p className="mt-1 text-xs text-gray-400">Status: <span className={statusColor(selectedExecution.status)}>{selectedExecution.status}</span></p>
                  <p className="mt-1 text-xs text-gray-500">Input: {selectedExecution.input_data}</p>
                  {selectedExecution.output_log && (
                    <pre className="mt-3 max-h-48 overflow-auto rounded-md bg-gray-950 p-3 text-xs text-gray-300">{JSON.stringify(JSON.parse(selectedExecution.output_log || '{}'), null, 2)}</pre>
                  )}
                </div>
                <div className="rounded-lg border border-white/[0.07] bg-soc-panel p-4">
                  <h4 className="text-sm font-semibold text-gray-200">Timeline</h4>
                  <div className="mt-2 space-y-2">
                    {(timeline || []).map((ev) => (
                      <div key={ev.id} className="flex gap-3 border-l-2 border-[#d8b17a]/30 pl-3 text-sm">
                        <span className="text-xs text-gray-500">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                        <span className="text-gray-300">{ev.event_type}: {ev.message}</span>
                      </div>
                    ))}
                    {!timeline?.length && <p className="text-xs text-gray-500">No timeline events.</p>}
                  </div>
                </div>
                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="rounded-lg border border-white/[0.07] bg-soc-panel p-4">
                    <h4 className="text-sm font-semibold text-gray-200">Evidence</h4>
                    <div className="mt-2 space-y-2">
                      {(evidence || []).map((ev) => (
                        <div key={ev.id} className="rounded-md bg-gray-950 p-2 text-xs">
                          <span className="font-medium text-[#d8b17a]">{ev.evidence_type}</span>
                          <p className="text-gray-500">{ev.source}</p>
                        </div>
                      ))}
                      {!evidence?.length && <p className="text-xs text-gray-500">No evidence collected.</p>}
                    </div>
                  </div>
                  <div className="rounded-lg border border-white/[0.07] bg-soc-panel p-4">
                    <h4 className="text-sm font-semibold text-gray-200">Action Logs</h4>
                    <div className="mt-2 space-y-2">
                      {(logs || []).map((lg) => (
                        <div key={lg.id} className="rounded-md bg-gray-950 p-2 text-xs">
                          <span className={`font-medium ${lg.status === 'ok' ? 'text-emerald-400' : 'text-red-400'}`}>{lg.action_type}</span>
                          <span className="ml-2 text-gray-500">{lg.duration_ms}ms</span>
                        </div>
                      ))}
                      {!logs?.length && <p className="text-xs text-gray-500">No action logs.</p>}
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <p className="text-sm text-gray-500">Select an execution to inspect details.</p>
            )}
          </div>
        </div>
      )}

      {tab === 'approvals' && (
        <div className="space-y-4">
          {approvals.length === 0 ? (
            <p className="text-sm text-gray-500">No pending approvals.</p>
          ) : (
            <div className="grid gap-4">
              {approvals.map((ap: WorkflowApproval) => (
                <motion.div key={ap.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="rounded-lg border border-white/[0.07] bg-soc-panel p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold text-white">{ap.action_summary || 'Approval Request'}</h4>
                      <p className="text-xs text-gray-500">Execution {ap.execution_id} • Node {ap.node_id} • Risk: <span className={`capitalize ${ap.risk_level === 'critical' ? 'text-red-400' : ap.risk_level === 'high' ? 'text-orange-400' : 'text-yellow-400'}`}>{ap.risk_level}</span></p>
                      <p className="mt-1 text-xs text-gray-400">Requested by {ap.requested_by || 'system'} at {new Date(ap.created_at).toLocaleString()}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={() => approvalMutation.mutate({ id: ap.id, decision: 'approved' })} disabled={approvalMutation.isPending} className="flex items-center gap-1 rounded-md bg-emerald-600 px-3 py-1.5 text-xs text-white hover:bg-emerald-500 disabled:opacity-50">
                        <CheckCircle className="h-3 w-3" /> Approve
                      </button>
                      <button onClick={() => approvalMutation.mutate({ id: ap.id, decision: 'denied' })} disabled={approvalMutation.isPending} className="flex items-center gap-1 rounded-md bg-red-600 px-3 py-1.5 text-xs text-white hover:bg-red-500 disabled:opacity-50">
                        <X className="h-3 w-3" /> Deny
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}

      {editing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-xl border border-white/[0.1] bg-[#17181b] p-6 shadow-2xl">
            <div className="mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5 text-[#d8b17a]" />
              <h3 className="text-lg font-semibold text-white">{(editing as Playbook).id ? 'Edit Playbook' : 'New Playbook'}</h3>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs text-gray-400">Name</label>
                  <input value={form.name || ''} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full rounded-md border border-white/[0.1] bg-gray-950 px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none" />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-400">Category</label>
                  <input value={form.category || ''} onChange={(e) => setForm({ ...form, category: e.target.value })} className="w-full rounded-md border border-white/[0.1] bg-gray-950 px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none" />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-400">Description</label>
                <textarea value={form.description || ''} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="w-full rounded-md border border-white/[0.1] bg-gray-950 px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none" />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="mb-1 block text-xs text-gray-400">Trigger</label>
                  <select value={form.trigger || 'manual'} onChange={(e) => setForm({ ...form, trigger: e.target.value })} className="w-full rounded-md border border-white/[0.1] bg-gray-950 px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none">
                    <option value="manual">Manual</option>
                    <option value="alert">Alert</option>
                    <option value="schedule">Schedule</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-400">Status</label>
                  <select value={form.status || 'active'} onChange={(e) => setForm({ ...form, status: e.target.value as 'active' | 'disabled' })} className="w-full rounded-md border border-white/[0.1] bg-gray-950 px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none">
                    <option value="active">Active</option>
                    <option value="disabled">Disabled</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-400">Version</label>
                  <input value={form.version || ''} onChange={(e) => setForm({ ...form, version: e.target.value })} className="w-full rounded-md border border-white/[0.1] bg-gray-950 px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none" />
                </div>
              </div>

              <div className="rounded-md border border-white/[0.07] bg-gray-950 p-3">
                <label className="mb-2 block text-xs font-medium text-gray-300">Workflow Builder</label>
                <PlaybookBuilder nodes={form.nodes || []} onChange={(nodes) => setForm({ ...form, nodes })} />
              </div>

              <div className="rounded-md border border-white/[0.07] bg-gray-950 p-3">
                <div className="mb-2 flex items-center justify-between">
                  <label className="text-xs font-medium text-gray-300">Legacy Actions (fallback)</label>
                  <button onClick={addAction} className="rounded-md bg-[#7c5540] px-2 py-1 text-xs text-white hover:bg-[#8d6350]">+ Add Action</button>
                </div>
                <div className="space-y-2">
                  {(form.actions || []).map((action, idx) => (
                    <div key={idx} className="grid grid-cols-12 gap-2 rounded-md border border-white/[0.07] bg-[#17181b] p-2">
                      <div className="col-span-4"><input value={action.action} onChange={(e) => updateAction(idx, { ...action, action: e.target.value })} placeholder="action" className="w-full rounded border border-white/[0.1] bg-gray-950 px-2 py-1 text-xs text-white" /></div>
                      <div className="col-span-7"><input value={JSON.stringify(action.params)} onChange={(e) => { try { updateAction(idx, { ...action, params: JSON.parse(e.target.value) }) } catch { /* ignore malformed JSON while typing */ } }} placeholder='{"ip":"10.0.0.55"}' className="w-full rounded border border-white/[0.1] bg-gray-950 px-2 py-1 font-mono text-xs text-white" /></div>
                      <div className="col-span-1 flex items-center justify-end"><button onClick={() => removeAction(idx)} className="text-red-400 hover:text-red-300"><Trash2 className="h-4 w-4" /></button></div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setEditing(null)} className="rounded-md border border-white/[0.1] bg-[#1c1e22] px-4 py-2 text-sm text-gray-300 hover:bg-white/[0.08]">Cancel</button>
              <button onClick={save} disabled={!form.name || createMutation.isPending || updateMutation.isPending} className="rounded-md bg-[#7c5540] px-4 py-2 text-sm text-white hover:bg-[#8d6350] disabled:opacity-50">
                {createMutation.isPending || updateMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Playbook'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
