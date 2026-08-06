import { CheckCircle2, XCircle, AlertTriangle, HelpCircle } from 'lucide-react'
import { ChartCard } from '@/components/ChartCard'
import type { ServiceHealthMap, ServiceState } from '../types'

const LABELS: Record<string, string> = {
  backend: 'Backend API',
  frontend: 'Frontend',
  postgresql: 'PostgreSQL',
  wazuh_manager: 'Wazuh Manager',
  wazuh_indexer: 'Wazuh Indexer',
  wazuh_dashboard: 'Wazuh Dashboard',
  ollama: 'AI Engine (Ollama)',
  prometheus: 'Prometheus',
  grafana: 'Grafana',
}

const STATE_META: Record<ServiceState, { icon: typeof CheckCircle2; color: string; label: string }> = {
  online: { icon: CheckCircle2, color: 'text-emerald-400', label: 'Online' },
  offline: { icon: XCircle, color: 'text-red-400', label: 'Offline' },
  warning: { icon: AlertTriangle, color: 'text-amber-400', label: 'Warning' },
  unknown: { icon: HelpCircle, color: 'text-stone-500', label: 'Unknown' },
}

export function ServiceHealthGrid({ services }: { services: ServiceHealthMap }) {
  const entries = Object.entries(services)

  return (
    <ChartCard title="Service Health">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {entries.map(([key, state]) => {
          const meta = STATE_META[state] || STATE_META.unknown
          const Icon = meta.icon
          return (
            <div key={key} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-4">
              <p className="text-xs font-medium text-stone-300">{LABELS[key] || key}</p>
              <div className={`mt-2 flex items-center gap-1.5 text-sm font-medium ${meta.color}`}>
                <Icon className="h-4 w-4" /> {meta.label}
              </div>
            </div>
          )
        })}
      </div>
    </ChartCard>
  )
}
