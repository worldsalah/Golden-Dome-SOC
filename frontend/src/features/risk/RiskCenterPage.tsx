import { useState } from 'react'
import { AlertTriangle, Loader2, RefreshCw, ShieldAlert } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { getAlertRisk, getAssetRisk, getIncidentRisk, getTopRiskyAssets } from '@/services/api'
import type { RiskScore } from '@/types'

function classificationColor(classification: string) {
  switch (classification) {
    case 'critical':
      return 'text-red-400 bg-red-400/10 border-red-400/20'
    case 'high':
      return 'text-orange-400 bg-orange-400/10 border-orange-400/20'
    case 'medium':
      return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20'
    default:
      return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20'
  }
}

function RiskCard({ title, score, classification }: { title: string; score: number; classification: string }) {
  return (
    <div className="rounded-lg border border-gray-800 bg-soc-panel p-4">
      <p className="text-xs text-gray-400">{title}</p>
      <div className="mt-2 flex items-end gap-3">
        <span className="text-3xl font-bold text-white">{score}</span>
        <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${classificationColor(classification)}`}>
          {classification.toUpperCase()}
        </span>
      </div>
      <div className="mt-3 h-2 w-full rounded-full bg-gray-800">
        <div
          className={`h-2 rounded-full ${score > 75 ? 'bg-red-500' : score > 50 ? 'bg-orange-500' : score > 25 ? 'bg-yellow-500' : 'bg-emerald-500'}`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
    </div>
  )
}

export function RiskCenterPage() {
  const [targetType, setTargetType] = useState<'asset' | 'alert' | 'incident'>('asset')
  const [targetId, setTargetId] = useState('')
  const [loading, setLoading] = useState(false)
  const [riskResult, setRiskResult] = useState<RiskScore | null>(null)

  const { data: topAssets, isLoading: topLoading } = useQuery({
    queryKey: ['risk', 'top-assets'],
    queryFn: () => getTopRiskyAssets(10),
  })

  const calculate = async () => {
    const id = parseInt(targetId, 10)
    if (Number.isNaN(id)) return
    setLoading(true)
    try {
      let data: RiskScore | null = null
      if (targetType === 'asset') data = await getAssetRisk(id)
      if (targetType === 'alert') data = await getAlertRisk(id)
      if (targetType === 'incident') data = await getIncidentRisk(id)
      setRiskResult(data)
    } catch {
      setRiskResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Risk Center"
        subtitle="Explainable risk scoring for alerts, assets, and incidents"
      />

      <div className="grid gap-6 md:grid-cols-3">
        <RiskCard title="Critical Threshold" score={75} classification="critical" />
        <RiskCard title="High Threshold" score={50} classification="high" />
        <RiskCard title="Medium Threshold" score={25} classification="medium" />
      </div>

      <ChartCard title="Calculate Risk Score">
        <div className="flex flex-col gap-3 sm:flex-row">
          <select
            value={targetType}
            onChange={(e) => setTargetType(e.target.value as 'asset' | 'alert' | 'incident')}
            className="rounded-md border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
          >
            <option value="asset">Asset</option>
            <option value="alert">Alert</option>
            <option value="incident">Incident</option>
          </select>
          <input
            type="number"
            value={targetId}
            onChange={(e) => setTargetId(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && calculate()}
            placeholder={`Enter ${targetType} ID...`}
            className="flex-1 rounded-md border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
          />
          <button
            onClick={calculate}
            disabled={loading || !targetId}
            className="flex items-center justify-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-sm text-white hover:bg-cyan-500 disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Calculate
          </button>
        </div>

        {riskResult && (
          <div className="mt-6 grid gap-6 md:grid-cols-2">
            <div className="rounded-md border border-gray-700 bg-gray-900 p-4">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-8 w-8 text-cyan-400" />
                <div>
                  <p className="text-sm text-gray-400">{riskResult.target_type} #{riskResult.target_id}</p>
                  <p className="text-2xl font-bold text-white">{riskResult.score}/100</p>
                </div>
                <span className={`ml-auto rounded-full border px-3 py-1 text-xs font-medium ${classificationColor(riskResult.classification)}`}>
                  {riskResult.classification.toUpperCase()}
                </span>
              </div>
            </div>
            <div className="rounded-md border border-gray-700 bg-gray-900 p-4">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Reasoning</h4>
              <ul className="space-y-1 text-sm text-gray-300">
                {Object.entries(riskResult.reason).map(([key, value]) => (
                  <li key={key}>
                    <span className="capitalize text-gray-400">{key.replace(/_/g, ' ')}:</span>{' '}
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </ChartCard>

      <ChartCard title="Top Risky Assets">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-800 text-gray-400">
              <tr>
                <th className="pb-2 font-medium">Hostname</th>
                <th className="pb-2 font-medium">Risk Score</th>
                <th className="pb-2 font-medium">Criticality</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {topLoading ? (
                <tr><td colSpan={3} className="py-4 text-center text-gray-500">Loading...</td></tr>
              ) : topAssets?.data?.length ? (
                topAssets.data.map((asset: { id: number; hostname: string; risk_score: number; criticality: number }) => (
                  <tr key={asset.id} className="hover:bg-gray-800/30">
                    <td className="py-3 text-gray-200">{asset.hostname}</td>
                    <td className="py-3">
                      <span className="inline-flex items-center gap-2">
                        <ShieldAlert className="h-4 w-4 text-orange-400" />
                        {asset.risk_score}
                      </span>
                    </td>
                    <td className="py-3 text-gray-400">{asset.criticality}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className="py-4 text-center text-gray-500">
                    No assets found. Run risk scoring from the asset details page.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </ChartCard>
    </div>
  )
}
