import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Server } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { formatDate } from '@/utils/formatters'
import apiClient from '@/services/api'
import { Asset } from '@/types'

const demoAssets: Asset[] = [
  { id: 1, hostname: 'FortiGate-60F', ip_address: '192.168.1.1', type: 'firewall', operating_system: 'FortiOS', criticality: 95, risk_score: 62, last_seen: '2024-07-25T12:00:00Z', created_at: '2024-01-01' },
  { id: 2, hostname: 'Windows-Server-2019', ip_address: '192.168.1.10', type: 'windows_server', operating_system: 'Windows Server 2019', criticality: 85, risk_score: 78, last_seen: '2024-07-25T11:58:00Z', created_at: '2024-01-01' },
  { id: 3, hostname: 'Linux-Database-Server', ip_address: '192.168.1.20', type: 'database', operating_system: 'Ubuntu 22.04', criticality: 90, risk_score: 82, last_seen: '2024-07-25T11:55:00Z', created_at: '2024-01-01' },
]

export function AssetsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['assets'],
    queryFn: async () => {
      const { data } = await apiClient.get('/assets')
      return data as { data: Asset[] }
    },
    initialData: { data: demoAssets },
  })

  const assets = data?.data || []

  return (
    <div className="space-y-6">
      <PageHeader title="Assets" subtitle="Inventory of monitored infrastructure" />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          <div className="col-span-full text-gray-500">Loading assets...</div>
        ) : assets.length === 0 ? (
          <div className="col-span-full text-gray-500">No assets found.</div>
        ) : (
          assets.map((asset) => (
            <Link
              key={asset.id}
              to={`/assets/${asset.id}`}
              className="rounded-lg border border-white/[0.07] bg-soc-panel p-5 transition-colors hover:border-[#b98947]/60/50"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-md bg-[#d8b17a]/10 p-2">
                    <Server className="h-5 w-5 text-[#d8b17a]" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{asset.hostname}</h3>
                    <p className="text-xs text-gray-500 capitalize">{asset.type.replace('_', ' ')}</p>
                  </div>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${asset.risk_score >= 80 ? 'bg-red-400/10 text-red-400' : asset.risk_score >= 50 ? 'bg-yellow-400/10 text-yellow-400' : 'bg-emerald-400/10 text-emerald-400'}`}>
                  Risk {asset.risk_score}
                </span>
              </div>
              <div className="mt-4 space-y-1 text-sm text-gray-400">
                <p><span className="text-gray-600">IP:</span> {asset.ip_address}</p>
                <p><span className="text-gray-600">OS:</span> {asset.operating_system}</p>
                <p><span className="text-gray-600">Last seen:</span> {formatDate(asset.last_seen)}</p>
              </div>
              <div className="mt-4">
                <div className="h-2 w-full rounded-full bg-gray-700">
                  <div
                    className="h-2 rounded-full bg-[#c97848]"
                    style={{ width: `${asset.risk_score}%` }}
                  />
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
