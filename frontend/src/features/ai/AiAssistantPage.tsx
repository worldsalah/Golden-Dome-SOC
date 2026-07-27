import { useState } from 'react'
import {
  analyzeAlert,
  askSentinel,
  generateAIDailyReport,
  generateAIPlaybook,
  getAIAuditLogs,
  getAIAnomalies,
  getAIFeedback,
  getAIHealth,
  getAIHistory,
  investigateIncidentWithAI,
  submitAIFeedback,
  threatHuntWithAI,
} from '@/services/api'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { StatusBadge } from '@/components/StatusBadge'
import type { AiAnalysis } from '@/types'
import {
  Activity,
  Bot,
  ClipboardList,
  Crosshair,
  FileText,
  History,
  Loader2,
  MessageSquare,
  Play,
  Search,
  Send,
  ShieldAlert,
  Sparkles,
  User,
  Wrench,
} from 'lucide-react'
import {
  AlertAnalysisCard,
  AnomalyList,
  DailyReportCard,
  FeedbackList,
  IncidentInvestigationCard,
  PlaybookCard,
  ThreatHuntCard,
} from './components/AiResultCards'

interface Message {
  role: 'user' | 'assistant'
  text: string
}

const tabs = [
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'alert', label: 'Alert Analysis', icon: ShieldAlert },
  { id: 'incident', label: 'Incident Investigator', icon: ClipboardList },
  { id: 'hunt', label: 'Threat Hunt', icon: Crosshair },
  { id: 'playbook', label: 'Playbook Generator', icon: Wrench },
  { id: 'report', label: 'Daily Report', icon: FileText },
  { id: 'anomalies', label: 'Anomalies', icon: Activity },
  { id: 'history', label: 'History & Audit', icon: History },
]

export function AiAssistantPage() {
  const [activeTab, setActiveTab] = useState('chat')

  // Chat
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', text: 'Hello, I am Sentinel AI — your junior SOC analyst. Ask me about alerts, incidents, MITRE, or request automated analysis.' },
  ])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)

  // Alert analysis
  const [alertId, setAlertId] = useState('')
  const [analysis, setAnalysis] = useState<AiAnalysis | null>(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [feedbackSent, setFeedbackSent] = useState(false)

  // Incident investigation
  const [incidentId, setIncidentId] = useState('')
  const [incidentReport, setIncidentReport] = useState<Record<string, unknown> | null>(null)
  const [incidentLoading, setIncidentLoading] = useState(false)

  // Threat hunt
  const [huntQuery, setHuntQuery] = useState('')
  const [huntResult, setHuntResult] = useState<Awaited<ReturnType<typeof threatHuntWithAI>> | null>(null)
  const [huntLoading, setHuntLoading] = useState(false)

  // Playbook generator
  const [pbDesc, setPbDesc] = useState('')
  const [pbMitre, setPbMitre] = useState('')
  const [pbSeverity, setPbSeverity] = useState(5)
  const [pbResult, setPbResult] = useState<Awaited<ReturnType<typeof generateAIPlaybook>> | null>(null)
  const [pbLoading, setPbLoading] = useState(false)

  // Daily report
  const [dailyReport, setDailyReport] = useState<Awaited<ReturnType<typeof generateAIDailyReport>> | null>(null)
  const [reportLoading, setReportLoading] = useState(false)

  // Anomalies
  const [anomalies, setAnomalies] = useState<Awaited<ReturnType<typeof getAIAnomalies>> | null>(null)
  const [anomaliesLoading, setAnomaliesLoading] = useState(false)

  // History / audit / feedback
  const [history, setHistory] = useState<AiAnalysis[]>([])
  const [auditLogs, setAuditLogs] = useState<{ id: number; endpoint: string; response_summary: string; source: string; created_at: string }[]>([])
  const [feedback, setFeedback] = useState<Awaited<ReturnType<typeof getAIFeedback>>['data']>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historySubTab, setHistorySubTab] = useState<'history' | 'audit' | 'feedback'>('history')
  const [aiHealth, setAiHealth] = useState<{ status: string; error?: string } | null>(null)

  const sendChat = async () => {
    if (!chatInput.trim()) return
    const question = chatInput.trim()
    setMessages((prev) => [...prev, { role: 'user', text: question }])
    setChatInput('')
    setChatLoading(true)
    try {
      const idMatch = question.match(/alert\s*#?(\d+)/i)
      const alertIdNum = idMatch ? parseInt(idMatch[1], 10) : undefined
      const res = await askSentinel(question, alertIdNum)
      setMessages((prev) => [...prev, { role: 'assistant', text: res.answer }])
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', text: 'Sorry, Sentinel AI encountered an error. Please try again.' }])
    } finally {
      setChatLoading(false)
    }
  }

  const runAlertAnalysis = async () => {
    const id = parseInt(alertId, 10)
    if (Number.isNaN(id)) return
    setAnalysisLoading(true)
    setFeedbackSent(false)
    try {
      const data = await analyzeAlert(id)
      setAnalysis(data)
    } catch {
      setAnalysis(null)
    } finally {
      setAnalysisLoading(false)
    }
  }

  const runIncidentInvestigation = async () => {
    const id = parseInt(incidentId, 10)
    if (Number.isNaN(id)) return
    setIncidentLoading(true)
    try {
      const data = await investigateIncidentWithAI(id)
      setIncidentReport(data)
    } catch {
      setIncidentReport(null)
    } finally {
      setIncidentLoading(false)
    }
  }

  const runThreatHunt = async () => {
    if (!huntQuery.trim()) return
    setHuntLoading(true)
    try {
      const data = await threatHuntWithAI(huntQuery)
      setHuntResult(data)
    } catch {
      setHuntResult(null)
    } finally {
      setHuntLoading(false)
    }
  }

  const runPlaybookGen = async () => {
    if (!pbDesc.trim()) return
    setPbLoading(true)
    try {
      const data = await generateAIPlaybook({ alert_description: pbDesc, mitre_technique: pbMitre || undefined, severity: pbSeverity })
      setPbResult(data)
    } catch {
      setPbResult(null)
    } finally {
      setPbLoading(false)
    }
  }

  const runDailyReport = async () => {
    setReportLoading(true)
    try {
      const data = await generateAIDailyReport()
      setDailyReport(data)
    } catch {
      setDailyReport(null)
    } finally {
      setReportLoading(false)
    }
  }

  const loadHistory = async () => {
    setHistoryLoading(true)
    try {
      const h = await getAIHistory(50)
      setHistory(h.data)
      const a = await getAIAuditLogs(50)
      setAuditLogs(a.data)
      const health = await getAIHealth()
      setAiHealth(health.ollama)
    } finally {
      setHistoryLoading(false)
    }
  }

  const sendFeedback = async (helpful: boolean, incorrect: boolean) => {
    if (!analysis?.analysis_id) return
    await submitAIFeedback(analysis.analysis_id, { helpful, incorrect })
    setFeedbackSent(true)
  }

  const loadAnomalies = async () => {
    setAnomaliesLoading(true)
    try {
      const data = await getAIAnomalies(168)
      setAnomalies(data)
    } catch {
      setAnomalies(null)
    } finally {
      setAnomaliesLoading(false)
    }
  }

  const loadFeedback = async () => {
    try {
      const data = await getAIFeedback(50)
      setFeedback(data.data)
    } catch {
      setFeedback([])
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Sentinel AI" subtitle="AI Security Analyst Copilot — triage, investigate, hunt, and respond" />

      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id)
                if (tab.id === 'history') {
                  loadHistory()
                  loadFeedback()
                }
                if (tab.id === 'report' && !dailyReport) runDailyReport()
                if (tab.id === 'anomalies' && !anomalies) loadAnomalies()
              }}
              className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.id ? 'bg-cyan-600 text-white' : 'border border-gray-700 bg-gray-900 text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {activeTab === 'chat' && (
        <div className="grid gap-6 lg:grid-cols-3">
          <ChartCard title="Conversation" className="lg:col-span-1 flex h-[calc(100vh-16rem)] flex-col">
            <div className="flex-1 space-y-4 overflow-y-auto pr-2">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-800">
                    {msg.role === 'user' ? <User className="h-4 w-4 text-gray-300" /> : <Bot className="h-4 w-4 text-cyan-400" />}
                  </div>
                  <div className={`max-w-md rounded-lg px-4 py-2 text-sm ${msg.role === 'user' ? 'bg-cyan-600 text-white' : 'bg-gray-800 text-gray-200'}`}>{msg.text}</div>
                </div>
              ))}
              {chatLoading && (
                <div className="flex gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-800"><Bot className="h-4 w-4 text-cyan-400" /></div>
                  <div className="flex items-center gap-2 rounded-lg bg-gray-800 px-4 py-2 text-sm text-gray-400"><Loader2 className="h-4 w-4 animate-spin" /> Sentinel AI is thinking...</div>
                </div>
              )}
            </div>
            <div className="mt-4 flex gap-2 border-t border-gray-800 pt-4">
              <input value={chatInput} onChange={(e) => setChatInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && sendChat()} placeholder="Ask Sentinel AI..." className="flex-1 rounded-md border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              <button onClick={sendChat} className="rounded-md bg-cyan-600 px-3 py-2 text-white hover:bg-cyan-500"><Send className="h-4 w-4" /></button>
            </div>
          </ChartCard>

          <div className="space-y-6 lg:col-span-2">
            <ChartCard title="Quick Actions">
              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  'What is the MITRE ATT&CK technique for brute force?',
                  'How do I investigate a FortiGate deny to RDP alert?',
                  'What immediate response steps are safe for a suspected brute force alert?',
                  'Analyze alert 1',
                ].map((q) => (
                  <button key={q} onClick={() => setChatInput(q)} className="rounded-md border border-gray-700 bg-gray-900 p-4 text-left text-sm text-gray-300 hover:border-cyan-500 hover:text-white">{q}</button>
                ))}
              </div>
            </ChartCard>
            <ChartCard title="Context Panel">
              <p className="text-sm text-gray-400">Sentinel AI can reference the current alert, incident, asset, and MITRE knowledge when you ask a question that includes an alert ID.</p>
            </ChartCard>
          </div>
        </div>
      )}

      {activeTab === 'alert' && (
        <div className="space-y-6">
          <ChartCard title="Analyze Alert with AI">
            <div className="flex gap-2">
              <input value={alertId} onChange={(e) => setAlertId(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && runAlertAnalysis()} placeholder="Alert ID..." className="rounded-md border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              <button onClick={runAlertAnalysis} disabled={analysisLoading} className="flex items-center gap-2 rounded-md bg-violet-600 px-4 py-2 text-sm text-white hover:bg-violet-500 disabled:opacity-50">
                {analysisLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />} Analyze
              </button>
            </div>
          </ChartCard>

          {analysis && (
            <AlertAnalysisCard
              analysis={analysis}
              feedbackSent={feedbackSent}
              onHelpful={() => sendFeedback(true, false)}
              onIncorrect={() => sendFeedback(false, true)}
            />
          )}
        </div>
      )}

      {activeTab === 'incident' && (
        <div className="space-y-6">
          <ChartCard title="Investigate Incident with AI">
            <div className="flex gap-2">
              <input value={incidentId} onChange={(e) => setIncidentId(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && runIncidentInvestigation()} placeholder="Incident ID..." className="rounded-md border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              <button onClick={runIncidentInvestigation} disabled={incidentLoading} className="flex items-center gap-2 rounded-md bg-violet-600 px-4 py-2 text-sm text-white hover:bg-violet-500 disabled:opacity-50">
                {incidentLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />} Investigate
              </button>
            </div>
          </ChartCard>
          {incidentReport && <IncidentInvestigationCard report={incidentReport} />}
        </div>
      )}

      {activeTab === 'hunt' && (
        <div className="space-y-6">
          <ChartCard title="AI Threat Hunting Assistant">
            <div className="flex gap-2">
              <input value={huntQuery} onChange={(e) => setHuntQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && runThreatHunt()} placeholder="e.g. Find suspicious login activity" className="flex-1 rounded-md border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              <button onClick={runThreatHunt} disabled={huntLoading} className="flex items-center gap-2 rounded-md bg-violet-600 px-4 py-2 text-sm text-white hover:bg-violet-500 disabled:opacity-50">
                {huntLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />} Hunt
              </button>
            </div>
          </ChartCard>
          {huntResult && <ThreatHuntCard result={huntResult} />}
        </div>
      )}

      {activeTab === 'playbook' && (
        <div className="space-y-6">
          <ChartCard title="AI Playbook Generator">
            <div className="space-y-3">
              <textarea value={pbDesc} onChange={(e) => setPbDesc(e.target.value)} placeholder="Describe the alert or incident scenario..." rows={3} className="w-full rounded-md border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
              <div className="flex gap-3">
                <input value={pbMitre} onChange={(e) => setPbMitre(e.target.value)} placeholder="MITRE technique e.g. T1110" className="rounded-md border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
                <input type="number" min={1} max={15} value={pbSeverity} onChange={(e) => setPbSeverity(parseInt(e.target.value, 10))} className="w-24 rounded-md border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none" />
                <button onClick={runPlaybookGen} disabled={pbLoading} className="flex items-center gap-2 rounded-md bg-violet-600 px-4 py-2 text-sm text-white hover:bg-violet-500 disabled:opacity-50">
                  {pbLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />} Generate
                </button>
              </div>
            </div>
          </ChartCard>
          {pbResult && <PlaybookCard playbook={pbResult} />}
        </div>
      )}

      {activeTab === 'report' && (
        <div className="space-y-6">
          <ChartCard title="Daily SOC Report" right={
            <button onClick={runDailyReport} disabled={reportLoading} className="flex items-center gap-2 rounded-md bg-cyan-600 px-3 py-1.5 text-xs text-white hover:bg-cyan-500 disabled:opacity-50">
              {reportLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <FileText className="h-3 w-3" />} Regenerate
            </button>
          }>
            {reportLoading && <p className="text-sm text-gray-500">Generating report...</p>}
            {dailyReport && <DailyReportCard report={dailyReport} />}
          </ChartCard>
        </div>
      )}

      {activeTab === 'anomalies' && (
        <div className="space-y-6">
          <ChartCard title="ML Anomaly Detection" right={
            <button onClick={loadAnomalies} disabled={anomaliesLoading} className="flex items-center gap-2 rounded-md bg-cyan-600 px-3 py-1.5 text-xs text-white hover:bg-cyan-500 disabled:opacity-50">
              {anomaliesLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Activity className="h-3 w-3" />} Refresh
            </button>
          }>
            {anomaliesLoading && <p className="text-sm text-gray-500">Running anomaly detection...</p>}
            {!anomaliesLoading && anomalies && (
              <div className="space-y-6">
                <AnomalyList title="Authentication Anomalies" items={anomalies.auth} />
                <AnomalyList title="Traffic Anomalies" items={anomalies.traffic} />
              </div>
            )}
          </ChartCard>
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-200">AI Health</h3>
            {aiHealth ? <span className={`rounded-full px-2 py-0.5 text-xs ${aiHealth.status === 'ok' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{aiHealth.status}</span> : <span className="text-xs text-gray-500">Unknown</span>}
          </div>
          <div className="flex gap-2">
            {(['history', 'audit', 'feedback'] as const).map((sub) => (
              <button key={sub} onClick={() => setHistorySubTab(sub)} className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${historySubTab === sub ? 'bg-cyan-600 text-white' : 'border border-gray-700 bg-gray-900 text-gray-400 hover:bg-gray-800 hover:text-white'}`}>
                {sub === 'history' ? 'Analysis History' : sub === 'audit' ? 'Audit Logs' : 'Feedback'}
              </button>
            ))}
          </div>
          {historySubTab === 'history' && (
          <ChartCard title="Analysis History">
            {historyLoading ? <Loader2 className="h-5 w-5 animate-spin text-gray-500" /> : (
              <div className="max-h-80 space-y-2 overflow-y-auto pr-2">
                {history.length === 0 && <p className="text-sm text-gray-500">No AI analyses yet.</p>}
                {history.map((h) => (
                  <div key={h.analysis_id} className="rounded-md border border-gray-700 bg-gray-900 p-3">
                    <p className="text-sm font-medium text-white">Analysis #{h.analysis_id}</p>
                    <p className="text-xs text-gray-500">{h.executive_summary.slice(0, 120)}...</p>
                    <div className="mt-2 flex gap-2 text-xs">
                      <StatusBadge status={h.risk_classification} />
                      <span className="text-gray-500">{h.mitre_mapping.technique_id}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ChartCard>
          )}
          {historySubTab === 'audit' && (
          <ChartCard title="Audit Logs">
            {historyLoading ? <Loader2 className="h-5 w-5 animate-spin text-gray-500" /> : (
              <div className="max-h-80 space-y-2 overflow-y-auto pr-2">
                {auditLogs.length === 0 && <p className="text-sm text-gray-500">No AI audit logs yet.</p>}
                {auditLogs.map((log) => (
                  <div key={log.id} className="rounded-md border border-gray-700 bg-gray-900 p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-cyan-400">{log.endpoint}</span>
                      <span className="text-xs text-gray-500">{new Date(log.created_at).toLocaleString()}</span>
                    </div>
                    <p className="mt-1 text-xs text-gray-400">{log.response_summary.slice(0, 120)}...</p>
                    <p className="text-xs text-gray-600">Source: {log.source}</p>
                  </div>
                ))}
              </div>
            )}
          </ChartCard>
          )}
          {historySubTab === 'feedback' && <FeedbackList feedback={feedback} loading={historyLoading} />}
        </div>
      )}
    </div>
  )
}
