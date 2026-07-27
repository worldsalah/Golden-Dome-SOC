import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { DataWorkspace, DataWorkspaceColumn } from '@/components/DataWorkspace'
import { motion } from 'framer-motion'
import {
  AlertTriangle,
  CheckCircle2,
  Edit3,
  Play,
  Plus,
  RefreshCw,
  Shield,
  Trash2,
  XCircle,
} from 'lucide-react'
import { AnimatedCard } from '@/components/AnimatedCard'
import { ChartCard } from '@/components/ChartCard'
import { PageHeader } from '@/components/PageHeader'
import {
  createDetectionRule,
  deleteDetectionRule,
  evaluateDetectionScenarios,
  getDetectionCoverage,
  getSigmaExport,
  listDetectionRules,
  testDetectionRule,
  toggleDetectionRule,
  updateDetectionRule,
} from '@/services/api'
import { DetectionRule, DetectionRuleTestResult } from '@/types'

const CATEGORIES = ['Authentication', 'Privilege Escalation', 'Execution', 'Persistence', 'Network', 'Lateral Movement', 'Malware', 'Web Security']
const SOURCES = ['Wazuh', 'FortiGate', 'Windows', 'Linux', 'IDS/IPS', 'Application']

const STATUS_STYLES: Record<string, string> = {
  active: 'bg-emerald-500/10 text-emerald-400',
  disabled: 'bg-gray-500/10 text-gray-400',
  draft: 'bg-yellow-500/10 text-yellow-400',
  archived: 'bg-red-500/10 text-red-400',
}

export function DetectionCenterPage() {
  const queryClient = useQueryClient()
  const [selectedRule, setSelectedRule] = useState<DetectionRule | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [testEvent, setTestEvent] = useState<string>('{"rule": {"id": "200001", "level": 10}}')
  const [testResult, setTestResult] = useState<DetectionRuleTestResult | null>(null)
  const [sigmaYaml, setSigmaYaml] = useState<string | null>(null)
  const [scenariosText, setScenariosText] = useState<string>(
    '[\n  {\n    "name": "valid match",\n    "event": {"rule": {"id": "200001", "level": 10}},\n    "expected_match": true\n  },\n  {\n    "name": "no match",\n    "event": {"rule": {"id": "999999"}},\n    "expected_match": false\n  }\n]'
  )
  const [scenarioResult, setScenarioResult] = useState<Awaited<ReturnType<typeof evaluateDetectionScenarios>> | null>(null)
  const [formData, setFormData] = useState<Partial<DetectionRule>>({
    name: '',
    description: '',
    severity: 5,
    category: 'Authentication',
    source: 'Wazuh',
    logic: '',
    mitre_attack_id: '',
    status: 'draft',
  })

  const { data: rulesData } = useQuery({
    queryKey: ['detection-rules'],
    queryFn: () => listDetectionRules({ limit: 100 }),
  })

  const { data: coverageData } = useQuery({
    queryKey: ['detection-coverage'],
    queryFn: getDetectionCoverage,
  })

  const rules = useMemo(() => rulesData?.data || [], [rulesData])
  const coverage = useMemo(() => coverageData, [coverageData])

  const createMutation = useMutation({
    mutationFn: createDetectionRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['detection-rules'] })
      resetForm()
      setIsEditing(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<DetectionRule> }) =>
      updateDetectionRule(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['detection-rules'] })
      resetForm()
      setIsEditing(false)
      setSelectedRule(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteDetectionRule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['detection-rules'] }),
  })

  const toggleMutation = useMutation({
    mutationFn: toggleDetectionRule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['detection-rules'] }),
  })

  const testMutation = useMutation({
    mutationFn: ({ id, event }: { id: number; event: Record<string, unknown> }) =>
      testDetectionRule(id, event),
    onSuccess: (result) => setTestResult(result),
  })

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      severity: 5,
      category: 'Authentication',
      source: 'Wazuh',
      logic: '',
      mitre_attack_id: '',
      status: 'draft',
    })
    setTestResult(null)
  }

  const openCreate = () => {
    resetForm()
    setSelectedRule(null)
    setIsEditing(true)
  }

  const openEdit = (rule: DetectionRule) => {
    setSelectedRule(rule)
    setFormData({ ...rule })
    setIsEditing(true)
  }

  const handleSave = () => {
    const payload = { ...formData }
    if (selectedRule) {
      updateMutation.mutate({ id: selectedRule.id, payload })
    } else {
      createMutation.mutate(payload as Partial<DetectionRule>)
    }
  }

  const columns: DataWorkspaceColumn<DetectionRule>[] = [
    { field: 'name', headerName: 'Rule', flex: 1.5, renderCell: (params) => <span className="font-medium text-gray-200">{String(params.value)}</span> },
    { field: 'category', headerName: 'Category', flex: 1 },
    { field: 'source', headerName: 'Source', flex: 0.8 },
    { field: 'severity', headerName: 'Severity', flex: 0.6, renderCell: (params) => <SeverityBadge severity={params.value as number} /> },
    { field: 'mitre_attack_id', headerName: 'MITRE', flex: 0.8 },
    {
      field: 'status',
      headerName: 'Status',
      flex: 0.8,
      renderCell: (params) => (
        <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_STYLES[params.value as string] || STATUS_STYLES.draft}`}>
          {String(params.value)}
        </span>
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      flex: 1.2,
      sortable: false,
      renderCell: (params) => (
        <div className="flex items-center gap-1">
          <button onClick={() => openEdit(params.row as DetectionRule)} className="rounded p-1 text-gray-400 hover:bg-gray-800 hover:text-cyan-400"><Edit3 className="h-4 w-4" /></button>
          <button onClick={() => toggleMutation.mutate(params.row.id)} className="rounded p-1 text-gray-400 hover:bg-gray-800 hover:text-emerald-400"><RefreshCw className="h-4 w-4" /></button>
          <button onClick={() => deleteMutation.mutate(params.row.id)} className="rounded p-1 text-gray-400 hover:bg-gray-800 hover:text-red-400"><Trash2 className="h-4 w-4" /></button>
        </div>
      ),
    },
  ]

  const coverageByTactic = coverage?.tactic_coverage || {}

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader title="Detection Engineering Center" subtitle="Build, test, and tune SOC detection rules" />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard icon={Shield} label="Total Rules" value={rules.length} color="#06b6d4" />
        <KpiCard icon={CheckCircle2} label="Active Rules" value={rules.filter((r) => r.status === 'active').length} color="#22c55e" />
        <KpiCard icon={XCircle} label="Disabled" value={rules.filter((r) => r.status === 'disabled').length} color="#ef4444" />
        <KpiCard icon={AlertTriangle} label="MITRE Coverage" value={`${coverage?.coverage_percentage || 0}%`} color="#f59e0b" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard title="MITRE ATT&CK Coverage by Tactic" className="lg:col-span-2">
          <div className="grid gap-3 pt-2 sm:grid-cols-2">
            {Object.entries(coverageByTactic).map(([tactic, count]) => (
              <div key={tactic} className="rounded-md bg-gray-900/50 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-200">{tactic}</span>
                  <span className="text-xs text-cyan-400">{count as number} techniques</span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-gray-800">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, ((count as number) / 5) * 100)}%` }}
                    transition={{ duration: 0.8 }}
                    className="h-2 rounded-full bg-cyan-500"
                  />
                </div>
              </div>
            ))}
            {Object.keys(coverageByTactic).length === 0 && <p className="text-sm text-gray-500">No coverage data available.</p>}
          </div>
        </ChartCard>
        <AnimatedCard className="p-5">
          <h3 className="mb-3 text-sm font-semibold text-gray-200">Detection Categories</h3>
          <div className="space-y-2">
            {CATEGORIES.map((cat) => (
              <div key={cat} className="flex items-center justify-between rounded-md bg-gray-900/50 px-3 py-2">
                <span className="text-sm text-gray-300">{cat}</span>
                <span className="text-xs text-gray-500">{rules.filter((r) => r.category === cat).length}</span>
              </div>
            ))}
          </div>
        </AnimatedCard>
      </div>

      <ChartCard title="Detection Rules" right={<button onClick={openCreate} className="flex items-center gap-1 rounded-md bg-cyan-600 px-3 py-1.5 text-sm text-white hover:bg-cyan-500"><Plus className="h-4 w-4" /> New Rule</button>}>
        <div className="mt-2 max-h-[520px]">
          <DataWorkspace rows={rules} columns={columns} />
        </div>
      </ChartCard>

      {isEditing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="w-full max-w-2xl rounded-xl border border-gray-700 bg-gray-900 p-6 shadow-2xl">
            <h3 className="mb-4 text-lg font-semibold text-white">{selectedRule ? 'Edit Rule' : 'Create Detection Rule'}</h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-gray-400">Name</label>
                <input value={formData.name || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-400">Severity</label>
                <input type="number" min={1} max={15} value={formData.severity || 5} onChange={(e) => setFormData({ ...formData, severity: parseInt(e.target.value) })} className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-400">Category</label>
                <select value={formData.category} onChange={(e) => setFormData({ ...formData, category: e.target.value })} className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none">
                  {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-400">Source</label>
                <select value={formData.source} onChange={(e) => setFormData({ ...formData, source: e.target.value })} className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none">
                  {SOURCES.map((s) => <option key={s}>{s}</option>)}
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1 block text-xs text-gray-400">MITRE Technique ID</label>
                <input value={formData.mitre_attack_id || ''} onChange={(e) => setFormData({ ...formData, mitre_attack_id: e.target.value })} placeholder="e.g. T1110" className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1 block text-xs text-gray-400">Description</label>
                <textarea value={formData.description || ''} onChange={(e) => setFormData({ ...formData, description: e.target.value })} rows={2} className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1 block text-xs text-gray-400">Logic (Python expression using <code>event</code>)</label>
                <textarea value={formData.logic || ''} onChange={(e) => setFormData({ ...formData, logic: e.target.value })} rows={3} placeholder="event.get('rule', {}).get('id') == '200001'" className="font-mono w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1 block text-xs text-gray-400">Status</label>
                <select value={formData.status} onChange={(e) => setFormData({ ...formData, status: e.target.value as DetectionRule['status'] })} className="w-full rounded-md border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none">
                  <option>active</option>
                  <option>disabled</option>
                  <option>draft</option>
                  <option>archived</option>
                </select>
              </div>
            </div>

            {selectedRule && (
              <>
                <div className="mt-4 rounded-md border border-gray-700 bg-gray-950 p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <label className="text-xs text-gray-400">Test Rule</label>
                    <button
                      onClick={async () => {
                        const result = await getSigmaExport(selectedRule.id)
                        setSigmaYaml(result.sigma_yaml)
                      }}
                      className="rounded-md bg-violet-600 px-2 py-1 text-xs text-white hover:bg-violet-500"
                    >
                      Export Sigma
                    </button>
                  </div>
                  <div className="flex gap-2">
                    <textarea value={testEvent} onChange={(e) => setTestEvent(e.target.value)} rows={2} className="font-mono flex-1 rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none" />
                    <button
                      onClick={() => {
                        try {
                          const event = JSON.parse(testEvent)
                          testMutation.mutate({ id: selectedRule.id, event })
                        } catch { setTestResult({ matched: false, reason: 'Invalid JSON', extracted_fields: {} }) }
                      }}
                      className="flex items-center gap-1 rounded-md bg-emerald-600 px-3 py-2 text-sm text-white hover:bg-emerald-500"
                    >
                      <Play className="h-4 w-4" /> Run
                    </button>
                  </div>
                  {testResult && (
                    <div className={`mt-2 rounded-md px-3 py-2 text-sm ${testResult.matched ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                      {testResult.matched ? 'Matched' : 'Did not match'}: {testResult.reason}
                    </div>
                  )}
                </div>

                {sigmaYaml && (
                  <div className="mt-4 rounded-md border border-gray-700 bg-gray-950 p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <label className="text-xs text-gray-400">Sigma Rule Export</label>
                      <button
                        onClick={() => {
                          const blob = new Blob([sigmaYaml], { type: 'text/yaml' })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = `${selectedRule.name.replace(/\s+/g, '_').toLowerCase()}.yml`
                          a.click()
                          URL.revokeObjectURL(url)
                        }}
                        className="rounded-md bg-gray-800 px-2 py-1 text-xs text-white hover:bg-gray-700"
                      >
                        Download
                      </button>
                    </div>
                    <pre className="max-h-48 overflow-auto rounded-md bg-gray-900 p-2 text-xs font-mono text-gray-300">{sigmaYaml}</pre>
                  </div>
                )}

                <div className="mt-4 rounded-md border border-gray-700 bg-gray-950 p-3">
                  <label className="mb-1 block text-xs text-gray-400">Scenario Evaluation (False Positive Analysis)</label>
                  <textarea value={scenariosText} onChange={(e) => setScenariosText(e.target.value)} rows={5} className="font-mono w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none" />
                  <button
                    onClick={async () => {
                      try {
                        const scenarios = JSON.parse(scenariosText)
                        const result = await evaluateDetectionScenarios(selectedRule.id, scenarios)
                        setScenarioResult(result)
                      } catch {
                        setScenarioResult({ total_scenarios: 0, true_positives: 0, false_positives: 0, false_negatives: 0, precision: 0, recall: 0, recommendation: 'Invalid scenario JSON', results: [] })
                      }
                    }}
                    className="mt-2 rounded-md bg-cyan-600 px-3 py-1.5 text-xs text-white hover:bg-cyan-500"
                  >
                    Evaluate Scenarios
                  </button>
                  {scenarioResult && (
                    <div className="mt-3 space-y-2 text-sm">
                      <div className="flex flex-wrap gap-3 text-xs">
                        <span className="text-gray-400">Precision: <span className="text-white">{scenarioResult.precision}%</span></span>
                        <span className="text-gray-400">Recall: <span className="text-white">{scenarioResult.recall}%</span></span>
                        <span className="text-gray-400">FP: <span className="text-red-400">{scenarioResult.false_positives}</span></span>
                        <span className="text-gray-400">FN: <span className="text-yellow-400">{scenarioResult.false_negatives}</span></span>
                      </div>
                      <p className="text-gray-300">{scenarioResult.recommendation}</p>
                    </div>
                  )}
                </div>
              </>
            )}

            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setIsEditing(false)} className="rounded-md border border-gray-700 bg-gray-800 px-4 py-2 text-sm text-gray-300 hover:bg-gray-700">Cancel</button>
              <button onClick={handleSave} className="rounded-md bg-cyan-600 px-4 py-2 text-sm text-white hover:bg-cyan-500">Save Rule</button>
            </div>
          </motion.div>
        </div>
      )}
    </motion.div>
  )
}

function KpiCard({ icon: Icon, label, value, color }: { icon: typeof Shield; label: string; value: number | string; color: string }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-soc-panel/80 p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-gray-500">{label}</p>
          <p className="mt-1 text-2xl font-bold text-white">{value}</p>
        </div>
        <div className="rounded-lg p-2" style={{ background: `${color}18` }}>
          <Icon className="h-5 w-5" style={{ color }} />
        </div>
      </div>
    </div>
  )
}

function SeverityBadge({ severity }: { severity: number }) {
  let color = 'bg-emerald-500/10 text-emerald-400'
  if (severity >= 13) color = 'bg-red-500/10 text-red-400'
  else if (severity >= 10) color = 'bg-orange-500/10 text-orange-400'
  else if (severity >= 7) color = 'bg-yellow-500/10 text-yellow-400'
  return <span className={`rounded-full px-2 py-0.5 text-xs ${color}`}>{severity}</span>
}
