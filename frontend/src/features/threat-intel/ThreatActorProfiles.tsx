/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronRight, Loader2, Search, UserRoundX } from 'lucide-react'
import { ChartCard } from '@/components/ChartCard'
import { listThreatActors, getThreatActor } from '@/services/api'

export function ThreatActorProfiles() {
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<any>(null)

  const { data: actors, isLoading } = useQuery({
    queryKey: ['threat', 'actors'],
    queryFn: () => listThreatActors(100),
  })

  const open = async (id: number) => {
    const data = await getThreatActor(id)
    setSelected(data)
  }

  const filtered = (actors || []).filter((a: any) =>
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    (a.country || '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <ChartCard title="Threat Actors">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search actor, country, or motivation..."
            className="w-full rounded-md border border-gray-700 bg-gray-900 py-2 pl-10 pr-4 text-sm text-white focus:border-cyan-500 focus:outline-none"
          />
        </div>
        <div className="space-y-2">
          {isLoading ? (
            <Loader2 className="mx-auto h-5 w-5 animate-spin text-gray-400" />
          ) : filtered.length ? (
            filtered.map((a: any) => (
              <button
                key={a.id}
                onClick={() => open(a.id)}
                className="flex w-full items-center justify-between rounded-md border border-gray-800 bg-gray-900/50 px-4 py-3 text-left hover:border-cyan-500/50"
              >
                <div className="flex items-center gap-3">
                  <UserRoundX className="h-5 w-5 text-red-400" />
                  <div>
                    <p className="text-sm font-medium text-white">{a.name}</p>
                    <p className="text-xs text-gray-400">{a.country || 'Unknown origin'} • {a.motivation || 'Unknown motivation'}</p>
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 text-gray-500" />
              </button>
            ))
          ) : (
            <p className="text-sm text-gray-500">No threat actors found.</p>
          )}
        </div>
      </ChartCard>

      {selected && (
        <ChartCard title={selected.name}>
          <div className="space-y-4 text-sm text-gray-300">
            {selected.aliases && <p><span className="text-gray-500">Aliases:</span> {selected.aliases}</p>}
            {selected.country && <p><span className="text-gray-500">Country:</span> {selected.country}</p>}
            {selected.motivation && <p><span className="text-gray-500">Motivation:</span> {selected.motivation}</p>}
            {selected.description && <p><span className="text-gray-500">Profile:</span> {selected.description}</p>}
            {selected.targeted_sectors && <p><span className="text-gray-500">Targeted Sectors:</span> {selected.targeted_sectors}</p>}
            {selected.targeted_regions && <p><span className="text-gray-500">Targeted Regions:</span> {selected.targeted_regions}</p>}
            {selected.techniques && <p><span className="text-gray-500">MITRE Techniques:</span> {selected.techniques}</p>}
            <button onClick={() => setSelected(null)} className="text-cyan-400 hover:text-cyan-300">Close</button>
          </div>
        </ChartCard>
      )}
    </div>
  )
}
