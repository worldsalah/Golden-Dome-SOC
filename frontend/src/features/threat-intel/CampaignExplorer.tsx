/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronRight, Loader2, Search, Target } from 'lucide-react'
import { ChartCard } from '@/components/ChartCard'
import { listThreatCampaigns, getThreatCampaign } from '@/services/api'
import { formatDate } from '@/utils/formatters'
import { typeIcons, scoreColor } from './helpers'

export function CampaignExplorer() {
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<any>(null)

  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['threat', 'campaigns'],
    queryFn: () => listThreatCampaigns(100),
  })

  const open = async (id: number) => {
    const data = await getThreatCampaign(id)
    setSelected(data)
  }

  const filtered = (campaigns || []).filter((c: any) =>
    (c.campaign_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
    (c.description || '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <ChartCard title="Threat Campaigns">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search campaign name or description..."
            className="w-full rounded-md border border-white/[0.1] bg-[#17181b] py-2 pl-10 pr-4 text-sm text-white focus:border-[#b98947]/60 focus:outline-none"
          />
        </div>
        <div className="space-y-2">
          {isLoading ? (
            <Loader2 className="mx-auto h-5 w-5 animate-spin text-gray-400" />
          ) : filtered.length ? (
            filtered.map((c: any) => (
              <button
                key={c.id}
                onClick={() => open(c.id)}
                className="flex w-full items-center justify-between rounded-md border border-white/[0.07] bg-[#17181b]/50 px-4 py-3 text-left hover:border-[#b98947]/60/50"
              >
                <div className="flex items-center gap-3">
                  <Target className="h-5 w-5 text-[#d8b17a]" />
                  <div>
                    <p className="text-sm font-medium text-white">{c.campaign_name}</p>
                    <p className="text-xs text-gray-400">{c.status} • {c.start_date ? formatDate(c.start_date) : 'Unknown start'}</p>
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 text-gray-500" />
              </button>
            ))
          ) : (
            <p className="text-sm text-gray-500">No campaigns found.</p>
          )}
        </div>
      </ChartCard>

      {selected && (
        <ChartCard title={selected.campaign_name}>
          <div className="space-y-4 text-sm text-gray-300">
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Status:</span>
              <span className="rounded-full bg-[#d8b17a]/10 px-2 py-0.5 text-xs text-[#d8b17a]">{selected.status}</span>
            </div>
            {selected.description && <p><span className="text-gray-500">Description:</span> {selected.description}</p>}
            {selected.targeted_sectors && <p><span className="text-gray-500">Targeted Sectors:</span> {selected.targeted_sectors}</p>}
            {selected.targeted_regions && <p><span className="text-gray-500">Targeted Regions:</span> {selected.targeted_regions}</p>}
            {selected.actors?.length > 0 && (
              <div>
                <p className="text-gray-500">Attributed Actors:</p>
                <ul className="ml-4 mt-1 list-disc">
                  {selected.actors.map((a: any) => <li key={a.id}>{a.name}</li>)}
                </ul>
              </div>
            )}
            {selected.malware?.length > 0 && (
              <div>
                <p className="text-gray-500">Associated Malware:</p>
                <ul className="ml-4 mt-1 list-disc">
                  {selected.malware.map((m: any) => <li key={m.id}>{m.family}</li>)}
                </ul>
              </div>
            )}
            {selected.iocs?.length > 0 && (
              <div>
                <p className="text-gray-500">Observed IOCs:</p>
                <div className="mt-1 space-y-1">
                  {selected.iocs.slice(0, 20).map((ioc: any) => (
                    <div key={ioc.id} className="flex items-center gap-2 rounded-md border border-white/[0.07] bg-[#17181b]/50 px-3 py-2">
                      {typeIcons[ioc.type] || typeIcons.default}
                      <span className="font-mono text-xs text-gray-200">{ioc.value}</span>
                      <span className={`ml-auto text-xs font-bold ${scoreColor(ioc.threat_score)}`}>{ioc.threat_score}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <button onClick={() => setSelected(null)} className="text-[#d8b17a] hover:text-[#e2c495]">Close</button>
          </div>
        </ChartCard>
      )}
    </div>
  )
}
