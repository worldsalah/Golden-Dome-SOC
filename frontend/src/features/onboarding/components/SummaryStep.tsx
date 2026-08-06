import { motion } from 'framer-motion'
import { CheckCircle2, Loader2, XCircle, ShieldCheck } from 'lucide-react'
import type { SystemInfoSnapshot, ServiceStatus } from '../types'

const STATUS_STYLES: Record<ServiceStatus, { dot: string; label: string }> = {
  online: { dot: 'bg-emerald-400', label: 'Online' },
  offline: { dot: 'bg-red-400', label: 'Offline' },
  warning: { dot: 'bg-amber-400', label: 'Warning' },
  unknown: { dot: 'bg-stone-500', label: 'Unknown' },
}

export function SummaryStep({
  info,
  installationName,
  administratorName,
  companyName,
  onComplete,
  isSubmitting,
  error,
}: {
  info: SystemInfoSnapshot
  installationName: string
  administratorName: string
  companyName: string
  onComplete: () => void
  isSubmitting: boolean
  error: string | null
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8 backdrop-blur-md">
        <h2 className="mb-5 text-lg font-medium text-[#f2eee8]">Deployment Summary</h2>

        <div className="mb-6 rounded-lg bg-[#131417]/50 p-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-stone-500">Installation Name</p>
          <p className="text-sm text-stone-200">{installationName}</p>
          <p className="mt-1 text-xs text-stone-500">
            {administratorName} {companyName ? `· ${companyName}` : ''}
          </p>
        </div>

        <div className="mb-6 rounded-lg bg-[#131417]/50 p-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-stone-500">Server Information</p>
          <div className="grid grid-cols-2 gap-2 text-xs text-stone-400">
            <p>Hostname: <span className="text-stone-200">{info.host.hostname}</span></p>
            <p>OS: <span className="text-stone-200">{info.operating_system.distribution}</span></p>
            <p>CPU: <span className="text-stone-200">{info.hardware.physical_cores} cores</span></p>
            <p>RAM: <span className="text-stone-200">{info.hardware.ram_total}</span></p>
            <p>Disk: <span className="text-stone-200">{info.hardware.disk_total}</span></p>
            <p>IP: <span className="text-stone-200">{info.host.local_ip || 'Unknown'}</span></p>
          </div>
        </div>

        <div>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-stone-500">Detected Services</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {info.services.map((s) => (
              <div key={s.name} className="flex items-center gap-2 rounded-md bg-[#131417]/50 px-3 py-2">
                <span className={`h-1.5 w-1.5 rounded-full ${STATUS_STYLES[s.status].dot}`} />
                <span className="truncate text-xs text-stone-300">{s.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <button
        onClick={onComplete}
        disabled={isSubmitting}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#c97848] to-[#b66838] px-4 py-3.5 text-sm font-medium text-white shadow-[0_0_30px_-10px_rgba(201,120,72,0.6)] transition hover:opacity-90 disabled:opacity-50"
      >
        {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
        {isSubmitting ? 'Deploying…' : 'Complete Installation'}
      </button>

      {error && (
        <p className="flex items-center gap-2 text-sm text-red-400">
          <XCircle className="h-4 w-4" /> {error}
        </p>
      )}
    </motion.div>
  )
}

export function SuccessStep() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center rounded-2xl border border-white/[0.06] bg-white/[0.02] p-12 text-center backdrop-blur-md"
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 260, damping: 20, delay: 0.1 }}
      >
        <CheckCircle2 className="h-16 w-16 text-emerald-400" />
      </motion.div>
      <h2 className="mt-4 text-2xl font-medium text-[#f2eee8]">Deployment Complete</h2>
      <p className="mt-2 text-sm text-stone-400">Redirecting to the dashboard…</p>
    </motion.div>
  )
}
