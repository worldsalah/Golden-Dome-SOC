import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Activity, BrainCircuit, Globe, Link as LinkIcon, Loader2, Network, ShieldCheck, Sparkles, StickyNote } from 'lucide-react'
import { motion } from 'framer-motion'
import { PageHeader } from '@/components/PageHeader'
import { StatusBadge } from '@/components/StatusBadge'
import { ChartCard } from '@/components/ChartCard'
import { severityLabel } from '@/utils/formatters'
import apiClient, { analyzeAlert, enrichAlert } from '@/services/api'
import { Alert, AiAnalysis } from '@/types'

export function AlertDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const alertId = Number(id)
  const queryClient = useQueryClient()
  const [enrichment, setEnrichment] = useState<Record<string, unknown> | null>(null)
  const [aiAnalysis, setAiAnalysis] = useState<AiAnalysis | null>(null)

  const { data: alert, isLoading } = useQuery<Alert>({
    queryKey: ['alert', alertId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/alerts/${alertId}`)
      return data as Alert
    },
  })

  const enrichMutation = useMutation({
    mutationFn: (createIncident: boolean) => enrichAlert(alertId, createIncident),
    onSuccess: (data) => {
      setEnrichment(data)
      queryClient.invalidateQueries({ queryKey: ['alert', alertId] })
    },
  })

  const analyzeMutation = useMutation({
    mutationFn: () => analyzeAlert(alertId),
    onSuccess: (data) => {
      setAiAnalysis(data)
      queryClient.invalidateQueries({ queryKey: ['alert', alertId] })
    },
  })

  if (isLoading) return <div className="p-8 text-gray-500">Loading alert...</div>
  if (!alert) return <div className="p-8 text-red-400">Alert not found.</div>

  const rawLog = alert.raw_log || '{}'

  return (
    <div className="space-y-6">
      <PageHeader title={`Alert #${alert.id}`} subtitle={alert.title} />

      <div className="grid gap-4 lg:grid-cols-3">
        <ChartCard title="Alert Summary" className="lg:col-span-2">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-xs text-gray-500">Severity</p>
              <p className="text-lg font-semibold text-white">{severityLabel(alert.severity)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Status</p>
              <StatusBadge status={alert.status} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Source IP</p>
              <p className="font-mono text-white">{alert.source_ip || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Destination IP</p>
              <p className="font-mono text-white">{alert.destination_ip || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Rule ID</p>
              <p className="font-mono text-white">{alert.rule_id || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">MITRE Technique</p>
              <p className="font-mono text-[#e2c495]">{alert.mitre_technique || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Wazuh Alert ID</p>
              <p className="font-mono text-gray-300">{alert.wazuh_alert_id}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Created</p>
              <p className="text-white">{new Date(alert.created_at).toLocaleString()}</p>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Investigation Actions">
          <div className="space-y-3">
            <button
              onClick={() => enrichMutation.mutate(false)}
              disabled={enrichMutation.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-[#7c5540] py-2 text-sm text-white hover:bg-[#8d6350] disabled:opacity-50"
            >
              {enrichMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Enrich Alert
            </button>
            <button
              onClick={() => enrichMutation.mutate(true)}
              disabled={enrichMutation.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-md border border-[#b98947]/50 py-2 text-sm text-[#d8b17a] hover:bg-[#2a2320] disabled:opacity-50"
            >
              Enrich + Create Incident
            </button>
            <button
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-[#6d5a96] py-2 text-sm text-white hover:bg-[#7d69ab] disabled:opacity-50"
            >
              {analyzeMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <BrainCircuit className="h-4 w-4" />}
              AI Analysis
            </button>
          </div>

          <ul className="mt-4 space-y-2 text-sm text-gray-300">
            <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-emerald-400" /> Verify source IP reputation</li>
            <li className="flex items-center gap-2"><Network className="h-4 w-4 text-emerald-400" /> Check firewall logs for pattern</li>
            <li className="flex items-center gap-2"><Activity className="h-4 w-4 text-emerald-400" /> Escalate if repeated attempts</li>
          </ul>
        </ChartCard>
      </div>

      {enrichment && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid gap-4 lg:grid-cols-3">
          <ChartCard title="MITRE Enrichment" className="lg:col-span-1">
            {enrichment.mitre ? (
              <div className="space-y-2 text-sm text-gray-200">
                <p><span className="text-[#d8b17a]">{((enrichment.mitre as Record<string, unknown>).technique_id as string)}</span> — {(enrichment.mitre as Record<string, unknown>).name as string}</p>
                <p className="text-xs text-gray-400">Tactic: {(enrichment.mitre as Record<string, unknown>).tactic as string}</p>
                <p className="text-xs text-gray-500">{(enrichment.mitre as Record<string, unknown>).description as string}</p>
              </div>
            ) : <p className="text-sm text-gray-500">No MITRE mapping found.</p>}
          </ChartCard>

          <ChartCard title="Threat Intelligence" className="lg:col-span-1">
            {(enrichment.threat_intelligence as unknown[]).length ? (
              <div className="space-y-2">
                {(enrichment.threat_intelligence as unknown[]).map((ti: unknown, idx) => {
                  const intel = ti as { indicator: string; reputation_score: number; type: string }
                  return (
                    <div key={idx} className="rounded-md bg-[#17181b]/50 p-2 text-sm">
                      <div className="flex items-center gap-2">
                        {intel.type === 'ip' ? <Globe className="h-3 w-3 text-[#d8b17a]" /> : <LinkIcon className="h-3 w-3 text-[#d8b17a]" />}
                        <span className="font-mono text-gray-200">{intel.indicator}</span>
                      </div>
                      <p className="text-xs text-gray-500">Reputation {intel.reputation_score}/100</p>
                    </div>
                  )
                })}
              </div>
            ) : <p className="text-sm text-gray-500">No TI results.</p>}
          </ChartCard>

          <ChartCard title="AI Analysis" className="lg:col-span-1">
            {enrichment.ai_analysis ? (
              <div className="space-y-2 text-sm text-gray-200">
                <p>{((enrichment.ai_analysis as Record<string, unknown>).summary as string) || 'No summary'}</p>
                <p className="text-xs text-gray-400">Risk: {String((enrichment.ai_analysis as Record<string, unknown>).risk_score || '—')}</p>
                <p className="text-xs text-gray-400">Severity: {String((enrichment.ai_analysis as Record<string, unknown>).severity || '—')}</p>
              </div>
            ) : <p className="text-sm text-gray-500">No AI analysis.</p>}
          </ChartCard>

          {(enrichment.incident as { id: number; name: string }) && (
            <ChartCard title="Auto-Generated Incident" className="lg:col-span-3">
              <div className="flex items-center gap-2 text-sm text-gray-200">
                <StickyNote className="h-4 w-4 text-[#d8b17a]" />
                Incident #{((enrichment.incident as { id: number }).id)} — {((enrichment.incident as { name: string }).name)}
              </div>
            </ChartCard>
          )}
        </motion.div>
      )}

      {aiAnalysis && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid gap-4 lg:grid-cols-3">
          <ChartCard title="AI Executive Summary" className="lg:col-span-3">
            <p className="text-sm text-gray-200">{aiAnalysis.executive_summary}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-xs">
              <StatusBadge status={aiAnalysis.risk_classification} />
              <span className="text-gray-500">Priority: {aiAnalysis.risk_assessment.priority}</span>
              <span className="text-gray-500">Confidence: {aiAnalysis.risk_assessment.confidence}%</span>
            </div>
          </ChartCard>
          <ChartCard title="MITRE Mapping">
            <div className="space-y-1 text-sm">
              <p><span className="text-gray-500">Tactic:</span> {aiAnalysis.mitre_mapping.tactic}</p>
              <p><span className="text-gray-500">Technique:</span> {aiAnalysis.mitre_mapping.technique}</p>
              <p><span className="text-[#d8b17a]">{aiAnalysis.mitre_mapping.technique_id}</span></p>
            </div>
          </ChartCard>
          <ChartCard title="Recommended Response" className="lg:col-span-2">
            <div className="grid gap-3 sm:grid-cols-3 text-sm text-gray-300">
              {(['immediate', 'short_term', 'long_term'] as const).map((phase) => (
                <div key={phase}>
                  <h4 className="mb-1 text-xs uppercase text-gray-500">{phase.replace('_', ' ')}</h4>
                  <ul className="list-disc space-y-0.5 pl-4">
                    {aiAnalysis.recommended_response[phase].map((item, i) => <li key={i}>{item}</li>)}
                  </ul>
                </div>
              ))}
            </div>
          </ChartCard>
        </motion.div>
      )}

      <ChartCard title="Raw Event" className="lg:col-span-3">
        <pre className="max-h-96 overflow-auto rounded-md bg-gray-950 p-4 text-xs text-emerald-300 font-mono">
          {JSON.stringify(JSON.parse(rawLog), null, 2)}
        </pre>
      </ChartCard>
    </div>
  )
}
