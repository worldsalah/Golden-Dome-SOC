import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plug, Plus, CheckCircle2, XCircle, Loader2, Settings2 } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { listConnectors, listConnectorTypes, testConnector } from '@/services/api'

export function ConnectorsPage() {
  const [showAdd, setShowAdd] = useState(false)
  const { data: connectors } = useQuery({ queryKey: ['connectors'], queryFn: listConnectors })
  const { data: types } = useQuery({ queryKey: ['connector-types'], queryFn: listConnectorTypes })

  return (
    <div className="space-y-6">
      <PageHeader title="Connectors" subtitle="Manage integrations with security tools, cloud platforms, and ticketing systems" />

      <div className="flex justify-end">
        <button
          onClick={() => setShowAdd((v) => !v)}
          className="flex items-center gap-2 rounded-md bg-[#c97848] px-4 py-2 text-sm font-medium text-white hover:bg-[#b66838]"
        >
          <Plus className="h-4 w-4" /> Add Connector
        </button>
      </div>

      {showAdd && (
        <ChartCard title="Available Connector Types">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {types?.map((t) => (
              <div key={t.type} className="rounded-md border border-white/[0.06] bg-[#17181b]/50 p-4">
                <div className="flex items-center gap-2">
                  <Plug className="h-4 w-4 text-[#d8b17a]" />
                  <span className="text-sm font-medium text-stone-200">{t.display_name}</span>
                </div>
                <p className="mt-1 text-xs text-stone-500">{t.description}</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  <span className="rounded-full bg-[#b98947]/10 px-2 py-0.5 text-[10px] font-medium text-[#d8b17a]">{t.category}</span>
                  {t.supported_actions.slice(0, 2).map((a) => (
                    <span key={a} className="rounded-full bg-white/[0.04] px-2 py-0.5 text-[10px] text-stone-500">{a}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      )}

      <ChartCard title="Configured Connectors">
        <div className="space-y-2">
          {connectors?.data?.length === 0 && (
            <p className="py-6 text-center text-sm text-stone-600">No connectors configured yet</p>
          )}
          {connectors?.data?.map((c: Record<string, unknown>) => (
            <ConnectorRow key={c.id as number} connector={c} />
          ))}
        </div>
      </ChartCard>
    </div>
  )
}

function ConnectorRow({ connector }: { connector: Record<string, unknown> }) {
  const qc = useQueryClient()
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<{ healthy: boolean; status: string } | null>(null)

  const testMut = useMutation({
    mutationFn: () => testConnector(connector.id as number),
    onMutate: () => setTesting(true),
    onSuccess: (data) => {
      setResult(data)
      setTesting(false)
      qc.invalidateQueries({ queryKey: ['connectors'] })
    },
    onError: (e: Error) => {
      setResult({ healthy: false, status: e.message })
      setTesting(false)
    },
  })

  const status = connector.status as string
  const statusColor = status === 'connected' ? 'text-emerald-400' : status === 'configured' ? 'text-amber-400' : 'text-stone-500'

  return (
    <div className="flex items-center justify-between rounded-md border border-white/[0.06] bg-[#17181b]/50 p-3">
      <div className="flex items-center gap-3">
        <div className="grid h-8 w-8 place-items-center rounded-md bg-[#b98947]/10">
          <Plug className="h-4 w-4 text-[#d8b17a]" />
        </div>
        <div>
          <p className="text-sm font-medium text-stone-200">{connector.name as string}</p>
          <p className="text-xs text-stone-500">{connector.connector_type as string} · {connector.category as string}</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {result && (
          <div className="flex items-center gap-1.5 text-xs">
            {result.healthy ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-400" />
            )}
            <span className={result.healthy ? 'text-emerald-400' : 'text-red-400'}>{result.status}</span>
          </div>
        )}

        <span className={`text-xs font-medium ${statusColor}`}>{status}</span>

        <button
          onClick={() => testMut.mutate()}
          disabled={testing}
          className="flex items-center gap-1.5 rounded-md border border-white/[0.1] px-3 py-1.5 text-xs text-stone-300 hover:border-white/20 disabled:opacity-50"
        >
          {testing ? <Loader2 className="h-3 w-3 animate-spin" /> : <Settings2 className="h-3 w-3" />}
          Test
        </button>
      </div>
    </div>
  )
}
