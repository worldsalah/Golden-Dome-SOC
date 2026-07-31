import { useMutation, useQuery } from '@tanstack/react-query'
import { Server, Database, Cpu, HardDrive, Activity, Download, Loader2 } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { getDeploymentInfo, getDeploymentHealth, createBackup } from '@/services/api'

export function DeploymentPage() {
  const { data: info } = useQuery({ queryKey: ['deployment-info'], queryFn: getDeploymentInfo })
  const { data: health, refetch: refetchHealth } = useQuery({ queryKey: ['deployment-health'], queryFn: getDeploymentHealth, refetchInterval: 30_000 })

  const backupMut = useMutation({
    mutationFn: createBackup,
    onSuccess: () => refetchHealth(),
  })

  const h = health as Record<string, unknown> | undefined
  const checks = h?.checks as Record<string, unknown> | undefined

  return (
    <div className="space-y-6">
      <PageHeader title="Deployment" subtitle="System info, health checks, and backup management" />

      <div className="grid gap-4 lg:grid-cols-4">
        <ChartCard title="App Version">
          <div className="flex items-center gap-3 py-2">
            <Server className="h-7 w-7 text-[#d8b17a]/60" />
            <div>
              <p className="text-xl font-bold text-stone-200">{info?.version || '—'}</p>
              <p className="text-xs text-stone-600">{info?.app_name}</p>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Database">
          <div className="flex items-center gap-3 py-2">
            <Database className="h-7 w-7 text-emerald-400/60" />
            <div>
              <p className="text-sm font-medium text-stone-200">{checks?.database ? 'Healthy' : '—'}</p>
              <p className="text-xs text-stone-600">{info?.database?.version?.toString().split(' ')[0] || '—'}</p>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Redis">
          <div className="flex items-center gap-3 py-2">
            <Cpu className="h-7 w-7 text-amber-400/60" />
            <div>
              <p className="text-sm font-medium text-stone-200">Cache</p>
              <p className="text-xs text-stone-600">{info?.redis?.url_masked || '—'}</p>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Ollama AI">
          <div className="flex items-center gap-3 py-2">
            <HardDrive className="h-7 w-7 text-[#c97848]/60" />
            <div>
              <p className="text-sm font-medium text-stone-200">{info?.ollama?.model || '—'}</p>
              <p className="text-xs text-stone-600">{info?.ollama?.base_url || '—'}</p>
            </div>
          </div>
        </ChartCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Health Summary">
          <div className="space-y-2">
            <div className="flex items-center justify-between rounded-md bg-[#17181b]/50 px-3 py-2">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-stone-600" />
                <span className="text-sm text-stone-400">Overall Status</span>
              </div>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                h?.status === 'healthy' ? 'bg-emerald-400/10 text-emerald-400' : 'bg-amber-400/10 text-amber-400'
              }`}>{(h?.status as string) || '—'}</span>
            </div>

            {checks && Object.entries(checks).map(([key, val]) => (
              <div key={key} className="flex items-center justify-between rounded-md bg-[#17181b]/30 px-3 py-1.5">
                <code className="text-xs text-stone-500">{key}</code>
                <span className="text-xs text-stone-400">{typeof val === 'object' ? JSON.stringify(val) : String(val)}</span>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Backup & Recovery">
          <div className="space-y-3">
            <button
              onClick={() => backupMut.mutate()}
              disabled={backupMut.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-[#c97848] px-4 py-2.5 text-sm font-medium text-white hover:bg-[#b66838] disabled:opacity-50"
            >
              {backupMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              {backupMut.isPending ? 'Creating backup…' : 'Create Backup'}
            </button>

            {backupMut.data && (
              <div className="rounded-md border border-emerald-500/20 bg-emerald-500/5 p-3">
                <p className="text-sm text-emerald-400">Backup created: {backupMut.data.backup_id}</p>
                <p className="mt-1 text-xs text-stone-500">{backupMut.data.instructions}</p>
              </div>
            )}

            <div className="rounded-md bg-[#17181b]/50 p-3">
              <p className="text-xs text-stone-500">
                Backups include table-level row counts for verification. For full database backup, run pg_dump from the host.
              </p>
            </div>
          </div>
        </ChartCard>
      </div>
    </div>
  )
}
