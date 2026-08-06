import { Cpu, MemoryStick, HardDrive, ArrowDownToLine, ArrowUpFromLine } from 'lucide-react'
import type { ServerMetrics } from '../types'

function GaugeBar({ pct, color }: { pct: number; color: string }) {
  return (
    <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/[0.06]">
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{ width: `${Math.min(100, Math.max(0, pct))}%`, backgroundColor: color }}
      />
    </div>
  )
}

function colorFor(pct: number) {
  if (pct >= 90) return '#ef4444'
  if (pct >= 70) return '#f59e0b'
  return '#c97848'
}

export function ServerResourceCards({ metrics }: { metrics: ServerMetrics }) {
  const cpu = metrics.cpu_usage ?? 0
  const mem = metrics.memory_usage ?? 0
  const disk = metrics.disk_usage ?? 0

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div className="enterprise-panel p-5">
        <div className="flex items-center justify-between">
          <span className="panel-title flex items-center gap-2">
            <Cpu className="h-4 w-4 text-[#d8b17a]" /> CPU
          </span>
          <span className="text-xs text-stone-500">{metrics.cores} cores</span>
        </div>
        <p className="mt-2 font-mono text-3xl font-medium tabular-nums text-stone-100">
          {metrics.cpu_usage !== null ? `${cpu.toFixed(0)}%` : '—'}
        </p>
        <GaugeBar pct={cpu} color={colorFor(cpu)} />
      </div>

      <div className="enterprise-panel p-5">
        <div className="flex items-center justify-between">
          <span className="panel-title flex items-center gap-2">
            <MemoryStick className="h-4 w-4 text-[#d8b17a]" /> RAM
          </span>
        </div>
        <p className="mt-2 font-mono text-3xl font-medium tabular-nums text-stone-100">
          {metrics.memory_usage !== null ? `${mem.toFixed(0)}%` : '—'}
        </p>
        <p className="mt-0.5 text-xs text-stone-500">{metrics.ram_total}</p>
        <GaugeBar pct={mem} color={colorFor(mem)} />
      </div>

      <div className="enterprise-panel p-5">
        <div className="flex items-center justify-between">
          <span className="panel-title flex items-center gap-2">
            <HardDrive className="h-4 w-4 text-[#d8b17a]" /> Disk
          </span>
        </div>
        <p className="mt-2 font-mono text-3xl font-medium tabular-nums text-stone-100">
          {metrics.disk_usage !== null ? `${disk.toFixed(0)}%` : '—'}
        </p>
        <p className="mt-0.5 text-xs text-stone-500">{metrics.disk_total}</p>
        <GaugeBar pct={disk} color={colorFor(disk)} />
      </div>

      <div className="enterprise-panel p-5">
        <span className="panel-title">Network</span>
        <div className="mt-3 space-y-2">
          <div className="flex items-center gap-2">
            <ArrowDownToLine className="h-3.5 w-3.5 text-emerald-400" />
            <span className="font-mono text-sm text-stone-200">{metrics.network_in ?? '—'}</span>
          </div>
          <div className="flex items-center gap-2">
            <ArrowUpFromLine className="h-3.5 w-3.5 text-[#c97848]" />
            <span className="font-mono text-sm text-stone-200">{metrics.network_out ?? '—'}</span>
          </div>
        </div>
        <p className="mt-3 text-xs text-stone-500">Uptime: {metrics.uptime ?? 'Unknown'}</p>
      </div>
    </div>
  )
}
