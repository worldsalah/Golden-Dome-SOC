/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Search, ShieldCheck } from 'lucide-react'
import { ChartCard } from '@/components/ChartCard'
import { enrichThreatIOC, listThreatIOCs, getThreatIOC } from '@/services/api'
import { formatDateTime } from '@/utils/formatters'
import { severityClass, scoreColor, typeIcons } from './helpers'

export function IocExplorer() {
  const [indicator, setIndicator] = useState('')
  const [type, setType] = useState('')
  const [detail, setDetail] = useState<any>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: iocs, isLoading } = useQuery({
    queryKey: ['threat', 'iocs', type],
    queryFn: () => listThreatIOCs(type || undefined, undefined, 50),
  })

  const enrichMutation = useMutation({
    mutationFn: () => enrichThreatIOC(indicator.trim(), type || undefined),
    onSuccess: (data) => {
      setDetail(data)
      setDetailOpen(true)
      queryClient.invalidateQueries({ queryKey: ['threat', 'iocs'] })
      queryClient.invalidateQueries({ queryKey: ['threat', 'dashboard'] })
    },
  })

  const lookup = () => {
    if (!indicator.trim()) return
    enrichMutation.mutate()
  }

  const openDetail = async (value: string) => {
    const data = await getThreatIOC(value)
    setDetail(data)
    setDetailOpen(true)
  }

  return (
    <div className="space-y-6">
      <ChartCard title="Enrich an IOC">
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            value={indicator}
            onChange={(e) => setIndicator(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && lookup()}
            placeholder="IP, domain, hash, URL, CVE, email..."
            className="flex-1 rounded-md border border-white/[0.1] bg-[#17181b] px-4 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none"
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="rounded-md border border-white/[0.1] bg-[#17181b] px-3 py-2 text-sm text-white focus:border-[#b98947]/60 focus:outline-none"
          >
            <option value="">Auto-detect</option>
            <option value="ip">IP</option>
            <option value="domain">Domain</option>
            <option value="hash">Hash</option>
            <option value="url">URL</option>
            <option value="cve">CVE</option>
            <option value="email">Email</option>
          </select>
          <button
            onClick={lookup}
            disabled={enrichMutation.isPending}
            className="flex items-center justify-center gap-2 rounded-md bg-[#7c5540] px-4 py-2 text-sm text-white hover:bg-[#8d6350] disabled:opacity-50"
          >
            {enrichMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            Enrich
          </button>
        </div>
        {enrichMutation.isError && (
          <p className="mt-3 text-sm text-red-400">Failed to enrich IOC. Ensure it is valid and try again.</p>
        )}
      </ChartCard>

      {detailOpen && detail && (
        <ChartCard title="IOC Enrichment Result">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#d8b17a]/10 text-[#d8b17a]">
                {typeIcons[detail.type] || typeIcons.default}
              </div>
              <div>
                <p className="font-mono text-sm text-white">{detail.indicator || detail.value}</p>
                <p className="text-xs text-gray-400 uppercase">{detail.type}</p>
              </div>
              <div className="ml-auto">
                <span className={`rounded-full border px-2 py-1 text-xs font-medium ${severityClass(detail.severity || (detail.reputation_score >= 70 ? 'high' : detail.reputation_score >= 40 ? 'medium' : 'low'))}`}>
                  {detail.malicious ? 'Malicious' : detail.reputation_score >= 40 ? 'Suspicious' : 'Clean'}
                </span>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-md border border-white/[0.07] bg-[#17181b]/50 p-3 text-center">
                <p className="text-xs text-gray-400">Reputation</p>
                <p className={`text-lg font-bold ${scoreColor(detail.reputation_score || 0)}`}>{detail.reputation_score ?? 0}</p>
              </div>
              <div className="rounded-md border border-white/[0.07] bg-[#17181b]/50 p-3 text-center">
                <p className="text-xs text-gray-400">Threat Score</p>
                <p className={`text-lg font-bold ${scoreColor(detail.threat_score || 0)}`}>{detail.threat_score ?? 0}</p>
              </div>
              <div className="rounded-md border border-white/[0.07] bg-[#17181b]/50 p-3 text-center">
                <p className="text-xs text-gray-400">Confidence</p>
                <p className={`text-lg font-bold ${scoreColor(detail.confidence || 0)}`}>{detail.confidence ?? 0}</p>
              </div>
            </div>
            <div className="grid gap-2 text-sm text-gray-300 sm:grid-cols-2">
              {detail.country && <p><span className="text-gray-500">Country:</span> {detail.country}</p>}
              {detail.asn && <p><span className="text-gray-500">ASN/ISP:</span> {detail.asn} {detail.isp ? `(${detail.isp})` : ''}</p>}
              {detail.threat_category && <p><span className="text-gray-500">Category:</span> {detail.threat_category}</p>}
              {detail.malware && <p><span className="text-gray-500">Malware:</span> {detail.malware}</p>}
            </div>
            <div>
              <p className="text-xs text-gray-500">Sources</p>
              <div className="mt-1 flex flex-wrap gap-2">
                {(detail.sources || []).map((src: any, i: number) => (
                  <span key={i} className="inline-flex items-center gap-1 rounded-full bg-[#1c1e22] px-2 py-1 text-xs text-gray-300">
                    <ShieldCheck className="h-3 w-3" /> {src.name} {src.score !== null && src.score !== undefined ? `(${src.score})` : ''}
                  </span>
                ))}
              </div>
            </div>
            {detail.scoring && detail.scoring.explanation && (
              <div className="rounded-md border border-white/[0.07] bg-[#17181b]/50 p-3">
                <p className="text-xs text-gray-500">Scoring Explanation</p>
                <p className="mt-1 text-sm text-gray-300">{detail.scoring.explanation}</p>
              </div>
            )}
            <button onClick={() => setDetailOpen(false)} className="text-sm text-[#d8b17a] hover:text-[#e2c495]">Close result</button>
          </div>
        </ChartCard>
      )}

      <ChartCard title="Local IOC Database">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-white/[0.07] text-gray-400">
              <tr>
                <th className="pb-2 font-medium">Value</th>
                <th className="pb-2 font-medium">Type</th>
                <th className="pb-2 font-medium">Score</th>
                <th className="pb-2 font-medium">Confidence</th>
                <th className="pb-2 font-medium">Sources</th>
                <th className="pb-2 font-medium">Last Seen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.06]">
              {isLoading ? (
                <tr><td colSpan={6} className="py-4 text-center text-gray-500"><Loader2 className="mx-auto h-4 w-4 animate-spin" /></td></tr>
              ) : iocs?.length ? (
                iocs.map((ioc: any) => (
                  <tr key={ioc.id} className="hover:bg-white/[0.03] cursor-pointer" onClick={() => openDetail(ioc.value)}>
                    <td className="py-3 font-mono text-gray-200">{ioc.value}</td>
                    <td className="py-3 text-gray-400">{ioc.type}</td>
                    <td className="py-3"><span className={`font-medium ${scoreColor(ioc.threat_score)}`}>{ioc.threat_score}</span></td>
                    <td className="py-3 text-gray-400">{ioc.confidence}</td>
                    <td className="py-3 text-gray-400">{ioc.source_count}</td>
                    <td className="py-3 text-gray-400">{formatDateTime(ioc.last_seen)}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={6} className="py-4 text-center text-gray-500">No IOCs stored yet. Enrich an indicator to populate the database.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </ChartCard>
    </div>
  )
}
