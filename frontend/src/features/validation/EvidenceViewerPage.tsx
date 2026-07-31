import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { RefreshCcw, Search, ShieldAlert } from 'lucide-react'
import { searchEvidence } from '@/services/api'
import { formatDateTime } from '@/utils/formatters'

export function EvidenceViewerPage() {
  const [q, setQ] = useState('')
  const [debounced, setDebounced] = useState('')
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['evidence', debounced],
    queryFn: () => searchEvidence({ q: debounced || undefined, limit: 100 }),
    retry: false,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setDebounced(q)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Detection Engineering · Sprint 5</p>
          <h1 className="mt-1 text-2xl font-medium tracking-[-.03em] text-stone-100">Evidence Viewer</h1>
          <p className="mt-1 text-xs text-stone-500">{data?.data_source ?? 'Search alert raw logs and workflow evidence.'}</p>
        </div>
        <button onClick={() => refetch()} className="btn-ghost py-2" disabled={isLoading}>
          <RefreshCcw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-500" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search raw logs, evidence content, titles…"
            className="w-full rounded-md border border-stone-800 bg-stone-900/50 py-2 pl-9 pr-3 text-sm text-stone-100 placeholder:text-stone-600 focus:border-[#d8b17a] focus:outline-none"
          />
        </div>
        <button type="submit" className="btn-ghost py-2">
          <Search className="h-3.5 w-3.5" />
          Search
        </button>
      </form>

      {isError && (
        <div className="enterprise-panel flex items-start gap-3 border-[#b94747]/30 p-4">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-[#e08585]" />
          <div>
            <p className="text-sm font-medium text-stone-100">Search failed</p>
            <p className="mt-1 text-xs text-stone-500">{(error as Error)?.message}</p>
          </div>
        </div>
      )}

      <div className="enterprise-panel overflow-hidden">
        <table className="table-shell">
          <thead>
            <tr>
              <th>Source</th>
              <th>Type</th>
              <th>Title</th>
              <th>Timestamp</th>
              <th>Preview</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="py-10 text-center text-stone-500">Searching evidence…</td></tr>
            ) : data?.evidence.length === 0 ? (
              <tr><td colSpan={5} className="py-10 text-center text-stone-500">No evidence found.</td></tr>
            ) : (
              data?.evidence.map((e) => (
                <tr key={`${e.source}-${e.id}`}>
                  <td className="text-xs text-stone-300">{e.source}</td>
                  <td className="text-xs text-stone-300">{e.type}</td>
                  <td className="font-medium text-stone-100">{e.title}</td>
                  <td className="font-mono text-xs text-stone-400">{formatDateTime(e.timestamp)}</td>
                  <td className="max-w-xs truncate text-xs text-stone-400">{e.snippet || '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {data && (
        <p className="text-right text-xs text-stone-500">{data.total} evidence items found</p>
      )}
    </div>
  )
}
