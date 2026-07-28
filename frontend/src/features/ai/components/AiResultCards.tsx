import { ChartCard } from '@/components/ChartCard'
import { StatusBadge } from '@/components/StatusBadge'
import type { AiAnalysis } from '@/types'
import { AlertTriangle, ThumbsDown, ThumbsUp } from 'lucide-react'

function RiskBadge({ classification, score }: { classification: string; score: number }) {
  const colors: Record<string, string> = {
    low: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  }
  const key = classification.toLowerCase()
  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-medium ${colors[key] || colors.medium}`}>
      <AlertTriangle className="h-4 w-4" />
      {classification.toUpperCase()} ({score}/100)
    </span>
  )
}

interface AlertAnalysisCardProps {
  analysis: AiAnalysis
  feedbackSent: boolean
  onHelpful: () => void
  onIncorrect: () => void
}

export function AlertAnalysisCard({ analysis, feedbackSent, onHelpful, onIncorrect }: AlertAnalysisCardProps) {
  return (
    <>
      <ChartCard
        title="Executive Summary"
        right={
          <div className="flex gap-2">
            <button onClick={onHelpful} disabled={feedbackSent} className="flex items-center gap-1 rounded-md bg-emerald-600/10 px-2 py-1 text-xs text-emerald-400 hover:bg-emerald-600/20 disabled:opacity-50">
              <ThumbsUp className="h-3 w-3" /> Helpful
            </button>
            <button onClick={onIncorrect} disabled={feedbackSent} className="flex items-center gap-1 rounded-md bg-red-600/10 px-2 py-1 text-xs text-red-400 hover:bg-red-600/20 disabled:opacity-50">
              <ThumbsDown className="h-3 w-3" /> Incorrect
            </button>
          </div>
        }
      >
        <p className="text-sm leading-relaxed text-gray-200">{analysis.executive_summary}</p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <RiskBadge classification={analysis.risk_classification} score={analysis.risk_score} />
          <span className="text-xs text-gray-500">Priority: {analysis.risk_assessment.priority}</span>
          <span className="text-xs text-gray-500">Confidence: {analysis.risk_assessment.confidence}%</span>
        </div>
      </ChartCard>

      <div className="grid gap-6 md:grid-cols-2">
        <ChartCard title="MITRE ATT&CK Mapping">
          <div className="space-y-2 text-sm">
            <p><span className="text-gray-500">Tactic:</span> <span className="text-white">{analysis.mitre_mapping.tactic}</span></p>
            <p><span className="text-gray-500">Technique:</span> <span className="text-white">{analysis.mitre_mapping.technique}</span></p>
            <p><span className="text-gray-500">ID:</span> <span className="rounded bg-[#d8b17a]/10 px-2 py-0.5 text-[#d8b17a]">{analysis.mitre_mapping.technique_id}</span></p>
          </div>
        </ChartCard>
        <ChartCard title="Technical Explanation">
          <ul className="list-disc space-y-1 pl-4 text-sm text-gray-300">
            {Object.entries(analysis.technical_explanation).map(([key, value]) => (
              <li key={key}>
                <span className="font-medium capitalize text-gray-400">{key.replace(/_/g, ' ')}:</span>{' '}
                {Array.isArray(value) ? value.join(', ') : typeof value === 'string' ? value : JSON.stringify(value)}
              </li>
            ))}
          </ul>
        </ChartCard>
      </div>

      <ChartCard title="Investigation Steps">
        <ol className="list-decimal space-y-1 pl-4 text-sm text-gray-300">
          {analysis.investigation_steps.map((step, i) => <li key={i}>{step}</li>)}
        </ol>
      </ChartCard>

      <ChartCard title="Recommended Response">
        <div className="grid gap-4 sm:grid-cols-3">
          {(['immediate', 'short_term', 'long_term'] as const).map((phase) => (
            <div key={phase} className="rounded-md border border-white/[0.1] bg-[#17181b] p-3">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">{phase.replace('_', ' ')}</h4>
              <ul className="list-disc space-y-1 pl-4 text-sm text-gray-300">
                {analysis.recommended_response[phase].map((item, i) => <li key={i}>{item}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </ChartCard>

      <ChartCard title="Analyst Notes">
        <p className="text-sm italic text-gray-400">{analysis.analyst_notes}</p>
        <p className="mt-2 text-xs text-gray-500">Source: {analysis.llm_source}</p>
      </ChartCard>
    </>
  )
}

interface IncidentInvestigationCardProps {
  report: {
    title?: string
    severity?: string
    summary?: string
    risk_score?: number
    risk_reason?: string
    affected_assets?: string[]
    indicators_of_compromise?: string[]
    recommended_remediation?: Record<string, string[]>
    timeline?: unknown[]
  }
}

export function IncidentInvestigationCard({ report }: IncidentInvestigationCardProps) {
  return (
    <>
      <ChartCard title={report.title || 'Incident Report'}>
        <div className="flex items-center gap-3">
          <StatusBadge status={report.severity || 'unknown'} />
          <span className="text-xs text-gray-500">Risk Score: {report.risk_score ?? '—'}</span>
        </div>
        <p className="mt-3 text-sm text-gray-300">{report.summary || 'No summary available.'}</p>
        {report.risk_reason && <p className="mt-2 text-xs text-gray-500">{report.risk_reason}</p>}
      </ChartCard>
      <ChartCard title="Root Cause & Affected Systems">
        <p className="text-sm text-gray-300">
          <span className="text-gray-500">Affected Assets:</span>{' '}
          {report.affected_assets?.length ? report.affected_assets.join(', ') : '—'}
        </p>
        <p className="mt-2 text-sm text-gray-300">
          <span className="text-gray-500">IOCs:</span>{' '}
          {report.indicators_of_compromise?.length ? report.indicators_of_compromise.join(', ') : '—'}
        </p>
      </ChartCard>
      <ChartCard title="Recommended Remediation">
        <div className="grid gap-4 sm:grid-cols-3">
          {(['immediate', 'short_term', 'long_term'] as const).map((phase) => {
            const rec = report.recommended_remediation?.[phase] ?? []
            return (
              <div key={phase} className="rounded-md border border-white/[0.1] bg-[#17181b] p-3">
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">{phase.replace('_', ' ')}</h4>
                <ul className="list-disc space-y-1 pl-4 text-sm text-gray-300">{rec.map((item, i) => <li key={i}>{item}</li>)}</ul>
              </div>
            )
          })}
        </div>
      </ChartCard>
      {!!report.timeline?.length && (
        <ChartCard title="Timeline">
          <div className="space-y-2">
            {report.timeline.map((event, idx) => (
              <div key={idx} className="border-l-2 border-[#c97848] pl-3 text-sm text-gray-300">
                {typeof event === 'string' ? event : JSON.stringify(event)}
              </div>
            ))}
          </div>
        </ChartCard>
      )}
    </>
  )
}

interface ThreatHuntCardProps {
  result: {
    summary: string
    hypotheses: string[]
    recommended_queries: string[]
    indicators_to_hunt: string[]
    mitre_techniques: string[]
    priority: string
    confidence: number
  }
}

export function ThreatHuntCard({ result }: ThreatHuntCardProps) {
  return (
    <>
      <ChartCard title="Hunt Summary">
        <p className="text-sm text-gray-200">{result.summary}</p>
        <div className="mt-3 flex flex-wrap gap-3 text-xs">
          <span className="text-gray-500">Priority: <span className="text-white">{result.priority}</span></span>
          <span className="text-gray-500">Confidence: <span className="text-white">{result.confidence}%</span></span>
        </div>
      </ChartCard>
      <div className="grid gap-6 md:grid-cols-2">
        <ChartCard title="Hypotheses">
          <ul className="list-disc space-y-1 pl-4 text-sm text-gray-300">{result.hypotheses.map((h, i) => <li key={i}>{h}</li>)}</ul>
        </ChartCard>
        <ChartCard title="Recommended Queries">
          <ul className="list-disc space-y-1 pl-4 text-sm text-gray-300">{result.recommended_queries.map((q, i) => <li key={i}>{q}</li>)}</ul>
        </ChartCard>
      </div>
      <ChartCard title="Indicators to Hunt">
        <div className="flex flex-wrap gap-2">
          {result.indicators_to_hunt.map((ind, i) => <span key={i} className="rounded-full bg-[#d8b17a]/10 px-3 py-1 text-xs text-[#d8b17a]">{ind}</span>)}
        </div>
      </ChartCard>
      {!!result.mitre_techniques.length && (
        <ChartCard title="MITRE Techniques">
          <div className="flex flex-wrap gap-2">
            {result.mitre_techniques.map((t, i) => <span key={i} className="rounded bg-violet-500/10 px-2 py-0.5 text-xs text-violet-400">{t}</span>)}
          </div>
        </ChartCard>
      )}
    </>
  )
}

interface PlaybookCardProps {
  playbook: {
    name: string
    description: string
    expected_outcome: string
    automation_notes: string
    actions: { action: string; params: Record<string, unknown> }[]
  }
}

export function PlaybookCard({ playbook }: PlaybookCardProps) {
  return (
    <>
      <ChartCard title={playbook.name}>
        <p className="text-sm text-gray-300">{playbook.description}</p>
        <p className="mt-2 text-xs text-gray-500">Expected outcome: {playbook.expected_outcome}</p>
        <p className="text-xs text-yellow-500">{playbook.automation_notes}</p>
      </ChartCard>
      <ChartCard title="Actions">
        <div className="space-y-2">
          {playbook.actions.map((action, i) => (
            <div key={i} className="flex items-center justify-between rounded-md border border-white/[0.1] bg-[#17181b] p-3">
              <span className="text-sm font-medium text-white">{action.action}</span>
              <span className="font-mono text-xs text-gray-500">{JSON.stringify(action.params)}</span>
            </div>
          ))}
        </div>
      </ChartCard>
    </>
  )
}

interface DailyReportCardProps {
  report: {
    title: string
    date: string
    executive_summary: string
    key_metrics: Record<string, number | string>
    top_threats: string[]
    recommendations: string[]
  }
}

export function DailyReportCard({ report }: DailyReportCardProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-white">{report.title}</h3>
        <p className="text-xs text-gray-500">{report.date}</p>
      </div>
      <p className="text-sm text-gray-200">{report.executive_summary}</p>
      <div className="grid gap-3 sm:grid-cols-4">
        {Object.entries(report.key_metrics).map(([k, v]) => (
          <div key={k} className="rounded-md border border-white/[0.1] bg-[#17181b] p-3 text-center">
            <p className="text-2xl font-bold text-white">{v}</p>
            <p className="text-xs text-gray-500 capitalize">{k.replace('_', ' ')}</p>
          </div>
        ))}
      </div>
      <ChartCard title="Top Threats">
        <ul className="list-disc space-y-1 pl-4 text-sm text-gray-300">{report.top_threats.map((t, i) => <li key={i}>{t}</li>)}</ul>
      </ChartCard>
      <ChartCard title="Recommendations">
        <ul className="list-disc space-y-1 pl-4 text-sm text-gray-300">{report.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul>
      </ChartCard>
    </div>
  )
}

interface AnomalyRecordProps {
  items: { source_ip: string; score: number; details?: string }[]
  title: string
}

export function AnomalyList({ items, title }: AnomalyRecordProps) {
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</h4>
      {items.length === 0 ? (
        <p className="text-sm text-gray-500">No {title.toLowerCase()} detected in the last 7 days.</p>
      ) : (
        <div className="space-y-2">
          {items.map((item, i) => (
            <div key={i} className="flex items-center justify-between rounded-md border border-white/[0.1] bg-[#17181b] p-3">
              <div>
                <p className="text-sm font-medium text-white">{item.source_ip}</p>
                {item.details && <p className="text-xs text-gray-500">{item.details}</p>}
              </div>
              <span className="rounded-full bg-orange-500/10 px-2 py-0.5 text-xs text-orange-400">Score: {item.score}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface FeedbackItem {
  id: number
  analysis_id: number
  helpful: boolean
  incorrect: boolean
  comment: string | null
}

interface FeedbackListProps {
  feedback: FeedbackItem[]
  loading: boolean
}

export function FeedbackList({ feedback, loading }: FeedbackListProps) {
  return (
    <ChartCard title="AI Feedback">
      {loading ? <p className="text-sm text-gray-500">Loading...</p> : (
        <div className="max-h-80 space-y-2 overflow-y-auto pr-2">
          {feedback.length === 0 && <p className="text-sm text-gray-500">No AI feedback yet.</p>}
          {feedback.map((f) => (
            <div key={f.id} className="rounded-md border border-white/[0.1] bg-[#17181b] p-3">
              <div className="flex items-center justify-between">
                <span className={`text-xs font-medium ${f.helpful ? 'text-emerald-400' : f.incorrect ? 'text-red-400' : 'text-gray-400'}`}>
                  {f.helpful ? 'Helpful' : f.incorrect ? 'Incorrect' : 'Neutral'}
                </span>
                <span className="text-xs text-gray-500">Analysis #{f.analysis_id}</span>
              </div>
              {f.comment && <p className="mt-1 text-xs text-gray-400">{f.comment}</p>}
            </div>
          ))}
        </div>
      )}
    </ChartCard>
  )
}
