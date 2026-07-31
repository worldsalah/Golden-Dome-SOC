import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { CheckCircle2, FileText, Loader2, MessageSquare, Sparkles, StickyNote, User } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { StatusBadge } from '@/components/StatusBadge'
import { ChartCard } from '@/components/ChartCard'
import { formatDate, formatDateTime } from '@/utils/formatters'
import apiClient, { addIncidentTimelineNote, generateIncidentReport, investigateIncidentWithAI, updateIncident } from '@/services/api'
import { Incident } from '@/types'

const statusOptions: Incident['status'][] = ['open', 'in_progress', 'resolved', 'closed']
const severityOptions: Incident['severity'][] = ['low', 'medium', 'high', 'critical']

export function IncidentDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const incidentId = Number(id)
  const queryClient = useQueryClient()
  const [note, setNote] = useState('')
  const [report, setReport] = useState<{ markdown: string; generated_at: string } | null>(null)
  const [aiReport, setAiReport] = useState<Record<string, unknown> | null>(null)

  const { data: incident, isLoading } = useQuery<Incident>({
    queryKey: ['incident', incidentId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/incidents/${incidentId}`)
      return data as Incident
    },
  })

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<Incident>) => updateIncident(incidentId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['incident', incidentId] }),
  })

  const noteMutation = useMutation({
    mutationFn: (n: string) => addIncidentTimelineNote(incidentId, n),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incident', incidentId] })
      setNote('')
    },
  })

  const reportMutation = useMutation({
    mutationFn: () => generateIncidentReport(incidentId),
    onSuccess: (data) => {
      setReport({ markdown: data.markdown as string, generated_at: data.generated_at as string })
    },
  })

  const aiInvestigateMutation = useMutation({
    mutationFn: () => investigateIncidentWithAI(incidentId),
    onSuccess: (data) => setAiReport(data),
  })

  if (isLoading) return <div className="p-8 text-gray-500">Loading incident...</div>
  if (!incident) return <div className="p-8 text-red-400">Incident not found.</div>

  const timeline = incident.timeline || []
  const alerts = incident.alerts || []

  return (
    <div className="space-y-6">
      <PageHeader title={incident.name} subtitle={`Incident #${incident.id}`} />

      <div className="grid gap-4 lg:grid-cols-3">
        <ChartCard title="Details" className="lg:col-span-2">
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs text-gray-500">Severity</p>
              <StatusBadge status={incident.severity} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Status</p>
              <StatusBadge status={incident.status} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Created</p>
              <p className="text-white">{formatDate(incident.created_at)}</p>
            </div>
          </div>
          <p className="mt-4 text-sm text-gray-300">{incident.description}</p>
        </ChartCard>

        <ChartCard title="Actions">
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-gray-400">Update Status</label>
              <select
                value={incident.status}
                onChange={(e) => updateMutation.mutate({ status: e.target.value as Incident['status'] })}
                className="w-full rounded-md border border-white/[0.1] bg-[#17181b] px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none"
              >
                {statusOptions.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">Severity</label>
              <select
                value={incident.severity}
                onChange={(e) => updateMutation.mutate({ severity: e.target.value as Incident['severity'] })}
                className="w-full rounded-md border border-white/[0.1] bg-[#17181b] px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none"
              >
                {severityOptions.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <button
              onClick={() => reportMutation.mutate()}
              disabled={reportMutation.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-[#6d5a96] py-2 text-sm text-white hover:bg-[#7d69ab] disabled:opacity-50"
            >
              {reportMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
              Generate Report
            </button>
            <button
              onClick={() => aiInvestigateMutation.mutate()}
              disabled={aiInvestigateMutation.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-[#7c5540] py-2 text-sm text-white hover:bg-[#8d6350] disabled:opacity-50"
            >
              {aiInvestigateMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              AI Investigation
            </button>
          </div>
        </ChartCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Timeline" className="lg:col-span-1">
          <div className="space-y-4 border-l-2 border-white/[0.1] pl-4">
            {timeline.length === 0 && <p className="text-sm text-gray-500">No timeline events.</p>}
            {timeline.map((event) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="relative"
              >
                <span className="absolute -left-[21px] top-1 h-3 w-3 rounded-full bg-[#c97848]"></span>
                <div className="flex items-start gap-2">
                  {event.action === 'created' && <CheckCircle2 className="h-4 w-4 text-emerald-400" />}
                  {event.action === 'updated' && <StickyNote className="h-4 w-4 text-yellow-400" />}
                  {event.action === 'assigned' && <User className="h-4 w-4 text-violet-400" />}
                  {event.action === 'note' && <MessageSquare className="h-4 w-4 text-[#d8b17a]" />}
                  <div>
                    <p className="text-sm text-white">{event.note || event.action}</p>
                    <p className="text-xs text-gray-500">{formatDate(event.timestamp)}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="mt-4 flex gap-2">
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && note && noteMutation.mutate(note)}
              placeholder="Add a note..."
              className="flex-1 rounded-md border border-white/[0.1] bg-[#17181b] px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none"
            />
            <button
              onClick={() => note && noteMutation.mutate(note)}
              disabled={!note || noteMutation.isPending}
              className="rounded-md bg-[#7c5540] px-3 py-2 text-sm text-white hover:bg-[#8d6350] disabled:opacity-50"
            >
              Add
            </button>
          </div>
        </ChartCard>

        <ChartCard title="Linked Alerts" className="lg:col-span-1">
          {alerts.length === 0 ? (
            <p className="text-sm text-gray-500">No alerts linked to this incident.</p>
          ) : (
            <div className="space-y-2">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between rounded-md bg-[#17181b]/50 p-3">
                  <div>
                    <p className="text-sm font-medium text-white">{alert.title}</p>
                    <p className="text-xs text-gray-500">Severity {alert.severity} • {alert.mitre_technique || 'No MITRE'}</p>
                  </div>
                  <StatusBadge status={alert.status} />
                </div>
              ))}
            </div>
          )}
        </ChartCard>
      </div>

      {aiReport && (
        <>
          <ChartCard title="AI Investigation Summary">
            <p className="text-sm text-gray-200">{String(aiReport.summary || '')}</p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-gray-500">
              <span>Severity: <span className="text-white">{String(aiReport.severity || '—')}</span></span>
              <span>Risk Score: <span className="text-white">{String(aiReport.risk_score || '—')}</span></span>
            </div>
          </ChartCard>
          {Array.isArray(aiReport.recommended_remediation) && (
            <ChartCard title="AI Recommended Remediation">
              <div className="grid gap-4 sm:grid-cols-3">
                {(['immediate', 'short_term', 'long_term'] as const).map((phase) => {
                  const rec = (aiReport.recommended_remediation as Record<string, string[]> | undefined)?.[phase] || []
                  return (
                    <div key={phase} className="rounded-md border border-white/[0.1] bg-[#17181b] p-3">
                      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">{phase.replace('_', ' ')}</h4>
                      <ul className="list-disc space-y-1 pl-4 text-sm text-gray-300">{rec.map((item, i) => <li key={i}>{item}</li>)}</ul>
                    </div>
                  )
                })}
              </div>
            </ChartCard>
          )}
        </>
      )}

      {report && (
        <ChartCard title="Generated Report">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs text-gray-500">Generated at {formatDateTime(report.generated_at)}</p>
            <button
              onClick={() => {
                const blob = new Blob([report.markdown], { type: 'text/markdown' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `incident-${incidentId}-report.md`
                a.click()
                URL.revokeObjectURL(url)
              }}
              className="flex items-center gap-1 rounded-md bg-[#1c1e22] px-3 py-1 text-xs text-white hover:bg-white/[0.08]"
            >
              <FileText className="h-3 w-3" /> Download MD
            </button>
          </div>
          <pre className="max-h-96 overflow-auto rounded-md bg-gray-950 p-4 text-xs text-gray-300 font-mono whitespace-pre-wrap">
            {report.markdown}
          </pre>
        </ChartCard>
      )}
    </div>
  )
}
