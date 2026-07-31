import { useQuery } from '@tanstack/react-query'
import { Hotel, ShieldCheck, FileText, Network } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { getHotelDashboard } from '@/services/api'

export function HotelSecurityPage() {
  const { data, isLoading } = useQuery({ queryKey: ['hotel-dashboard'], queryFn: getHotelDashboard })
  const d = data as Record<string, unknown> | undefined

  return (
    <div className="space-y-6">
      <PageHeader title="Hotel Security" subtitle="Hospitality industry compliance — PCI-DSS, GDPR, and hotel network security" />

      <div className="grid gap-4 lg:grid-cols-3">
        <ChartCard title="PCI-DSS Compliance">
          <div className="flex items-center gap-3 py-2">
            <ShieldCheck className="h-8 w-8 text-emerald-400/60" />
            <div>
              <p className="text-2xl font-bold text-stone-200">{d?.pci_compliance as string || '—'}</p>
              <p className="text-xs text-stone-600">12 requirements</p>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="GDPR Compliance">
          <div className="flex items-center gap-3 py-2">
            <FileText className="h-8 w-8 text-amber-400/60" />
            <div>
              <p className="text-2xl font-bold text-stone-200">{d?.gdpr_compliance as string || '—'}</p>
              <p className="text-xs text-stone-600">10 requirements</p>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Network Zones">
          <div className="flex items-center gap-3 py-2">
            <Network className="h-8 w-8 text-[#d8b17a]/60" />
            <div>
              <p className="text-2xl font-bold text-stone-200">{d?.network_zones as unknown as number || '—'}</p>
              <p className="text-xs text-stone-600">Zones configured</p>
            </div>
          </div>
        </ChartCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Hotel Asset Templates">
          <div className="space-y-2">
            {[
              { name: 'PMS Server', type: 'Server', criticality: 'High' },
              { name: 'POS Terminal', type: 'Endpoint', criticality: 'Critical' },
              { name: 'Guest Wi-Fi AP', type: 'Network', criticality: 'Medium' },
              { name: 'Door Lock Controller', type: 'IoT', criticality: 'High' },
              { name: 'IP Camera', type: 'IoT', criticality: 'Medium' },
            ].map((a) => (
              <div key={a.name} className="flex items-center justify-between rounded-md bg-[#17181b]/50 px-3 py-2">
                <div className="flex items-center gap-2">
                  <Hotel className="h-3.5 w-3.5 text-[#d8b17a]" />
                  <span className="text-sm text-stone-300">{a.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-stone-500">{a.type}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    a.criticality === 'Critical' ? 'bg-red-400/10 text-red-400' :
                    a.criticality === 'High' ? 'bg-amber-400/10 text-amber-400' :
                    'bg-stone-400/10 text-stone-400'
                  }`}>{a.criticality}</span>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Compliance Controls">
          <div className="space-y-2">
            {[
              { control: 'Firewall configuration', standard: 'PCI-DSS 1.1', status: 'Compliant' },
              { control: 'Encryption in transit', standard: 'PCI-DSS 4.1', status: 'Compliant' },
              { control: 'Access control policy', standard: 'PCI-DSS 7.1', status: 'Review needed' },
              { control: 'Data retention policy', standard: 'GDPR Art. 5', status: 'Compliant' },
              { control: 'Guest data isolation', standard: 'GDPR Art. 25', status: 'Compliant' },
              { control: 'Vulnerability scanning', standard: 'PCI-DSS 11.2', status: 'Action needed' },
            ].map((c) => (
              <div key={c.control} className="flex items-center justify-between rounded-md bg-[#17181b]/50 px-3 py-2">
                <div>
                  <p className="text-sm text-stone-300">{c.control}</p>
                  <p className="text-[10px] text-stone-600">{c.standard}</p>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  c.status === 'Compliant' ? 'bg-emerald-400/10 text-emerald-400' :
                  c.status === 'Review needed' ? 'bg-amber-400/10 text-amber-400' :
                  'bg-red-400/10 text-red-400'
                }`}>{c.status}</span>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      <ChartCard title="Dashboard Data">
        {isLoading ? (
          <p className="py-4 text-center text-sm text-stone-600">Loading…</p>
        ) : (
          <pre className="overflow-x-auto rounded-md bg-[#0a0a0b] p-4 text-xs text-stone-400">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </ChartCard>
    </div>
  )
}
