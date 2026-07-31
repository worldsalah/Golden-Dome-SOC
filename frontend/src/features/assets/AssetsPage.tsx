import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Server } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { formatDate } from '@/utils/formatters'
import apiClient from '@/services/api'
import { Asset } from '@/types'

export function AssetsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['assets'],
    queryFn: async () => {
      const { data } = await apiClient.get('/assets')
      return data as { data: Asset[] }
    },
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
