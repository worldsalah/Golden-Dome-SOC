import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Activity, AlertTriangle, Loader2, Server, ShieldCheck } from 'lucide-react'
import { motion } from 'framer-motion'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { StatusBadge } from '@/components/StatusBadge'
import { formatDate } from '@/utils/formatters'
import { calculateAssetRisk, getAssetDetails } from '@/services/api'

export function AssetDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const assetId = Number(id)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['asset', assetId, 'details'],
    queryFn: () => getAssetDetails(assetId),
  })

  const riskMutation = useMutation({
    mutationFn: () => calculateAssetRisk(assetId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['asset', assetId] }),
  })

  if (isLoading) return <div className="p-8 text-gray-500">Loading asset...</div>
  if (!data?.asset) return <div className="p-8 text-red-400">Asset not found.</div>

  const asset = data.asset
  const vulnerabilities = data.vulnerabilities || []
  const alerts = data.alerts || []

  return (
    <div className="space-y-6">
      <PageHeader title={asset.hostname} subtitle={`Asset #${asset.id}`} />

      <div className="grid gap-4 lg:grid-cols-3">
        <ChartCard title="Asset Overview" className="lg:col-span-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-md bg-[#d8b17a]/10 p-3">
                <Server className="h-8 w-8 text-[#d8b17a]" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">{asset.hostname}</h2>
                <p className="text-sm text-gray-500 capitalize">{(asset.type ?? '').replace('_', ' ')}</p>
              </div>
            </div>
            <button
              onClick={() => riskMutation.mutate()}
              disabled={riskMutation.isPending}
              className="flex items-center gap-2 rounded-md border border-white/[0.1] bg-[#1c1e22] px-3 py-2 text-sm text-white hover:bg-white/[0.08] disabled:opacity-50"
            >
              {riskMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Activity className="h-4 w-4" />}
              Recalc Risk
            </button>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-xs text-gray-500">IP Address</p>
              <p className="font-mono text-white">{asset.ip_address}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Operating System</p>
              <p className="text-white">{asset.operating_system}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Criticality</p>
              <p className="text-white">{asset.criticality}/100</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Last Seen</p>
              <p className="text-white">{formatDate(asset.last_seen)}</p>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Risk Score">
          <div className="flex flex-col items-center justify-center py-4">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="text-4xl font-bold text-white"
            >
              {asset.risk_score}
            </motion.div>
            <p className="mt-1 text-sm text-gray-500">out of 100</p>
            <div className="mt-4 h-3 w-full rounded-full bg-gray-700">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${asset.risk_score}%` }}
                transition={{ duration: 0.8 }}
                className={`h-3 rounded-full ${asset.risk_score >= 80 ? 'bg-red-500' : asset.risk_score >= 50 ? 'bg-yellow-500' : 'bg-emerald-500'}`}
              />
            </div>
            <p className="mt-2 text-xs text-gray-500">Based on criticality, vulnerabilities, and recent alerts</p>
          </div>
        </ChartCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title={`Vulnerabilities (${vulnerabilities.length})`}>
          {vulnerabilities.length === 0 ? (
            <p className="text-sm text-gray-500">No vulnerabilities found.</p>
          ) : (
            <div className="space-y-2">
              {vulnerabilities.map((vuln) => (
                <div key={vuln.id} className="flex items-center justify-between rounded-md bg-[#17181b]/50 p-3">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-yellow-400" />
                    <div>
                      <p className="font-mono text-sm font-medium text-white">{vuln.cve}</p>
                      <p className="text-xs text-gray-500">{vuln.description || 'No description'}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-white">{vuln.cvss_score || '—'}</p>
                    <p className="text-xs text-gray-500 capitalize">{vuln.severity}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ChartCard>

        <ChartCard title={`Recent Alerts (${alerts.length})`}>
          {alerts.length === 0 ? (
            <p className="text-sm text-gray-500">No recent alerts for this asset.</p>
          ) : (
            <div className="space-y-2">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between rounded-md bg-[#17181b]/50 p-3">
                  <div className="flex items-center gap-3">
                    <ShieldCheck className="h-5 w-5 text-[#d8b17a]" />
                    <div>
                      <p className="text-sm font-medium text-white">{alert.title}</p>
                      <p className="text-xs text-gray-500">{alert.mitre_technique || 'No MITRE'} • {formatDate(alert.created_at)}</p>
                    </div>
                  </div>
                  <StatusBadge status={alert.status} />
                </div>
              ))}
            </div>
          )}
        </ChartCard>
      </div>
    </div>
  )
}
