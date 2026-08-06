import { Container } from 'lucide-react'
import { ChartCard } from '@/components/ChartCard'
import type { ContainerMetric } from '../types'

function StatusDot({ status }: { status: string }) {
  const color = status === 'running' ? 'bg-emerald-400' : status === 'stopped' ? 'bg-red-400' : 'bg-stone-500'
  return <span className={`inline-block h-2 w-2 rounded-full ${color}`} />
}

export function ContainerTable({ containers }: { containers: ContainerMetric[] }) {
  return (
    <ChartCard title="Docker Containers">
      {containers.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <Container className="mb-2 h-8 w-8 text-stone-700" />
          <p className="text-sm text-stone-500">No container metrics available yet.</p>
          <p className="mt-1 text-xs text-stone-600">Deploy cAdvisor or mount the Docker socket to see live stats.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/[0.06] text-[10px] uppercase tracking-wider text-stone-500">
                <th className="pb-2 pr-4 font-medium">Container</th>
                <th className="pb-2 pr-4 font-medium">Status</th>
                <th className="pb-2 pr-4 font-medium">CPU</th>
                <th className="pb-2 pr-4 font-medium">Memory</th>
                <th className="pb-2 font-medium">Uptime</th>
              </tr>
            </thead>
            <tbody>
              {containers.map((c) => (
                <tr key={c.id} className="border-b border-white/[0.03] last:border-0">
                  <td className="py-2.5 pr-4 font-medium text-stone-200">{c.name.replace(/^goldendome-?/, '')}</td>
                  <td className="py-2.5 pr-4">
                    <span className="flex items-center gap-1.5 text-xs text-stone-400">
                      <StatusDot status={c.status} /> {c.status}
                    </span>
                  </td>
                  <td className="py-2.5 pr-4 font-mono text-stone-300">{c.cpu}</td>
                  <td className="py-2.5 pr-4 font-mono text-stone-300">{c.memory}</td>
                  <td className="py-2.5 text-xs text-stone-500">{c.uptime ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </ChartCard>
  )
}
