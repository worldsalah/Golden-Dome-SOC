import { motion } from 'framer-motion'
import { Server, MonitorCog, Cpu, MemoryStick, Container, Network, ArrowRight, type LucideIcon } from 'lucide-react'
import type { SystemInfoSnapshot } from '../types'

interface FormState {
  installation_name: string
  administrator_name: string
  administrator_email: string
  administrator_password: string
  company_name: string
}

function InfoCard({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 backdrop-blur-sm">
      <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-white/[0.08] bg-[#0e0f11]">
        <Icon className="h-4 w-4 text-[#d8b17a]" />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] uppercase tracking-wider text-stone-500">{label}</p>
        <p className="truncate text-sm font-medium text-stone-200">{value}</p>
      </div>
    </div>
  )
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  type?: string
}) {
  return (
    <div>
      <label className="block text-xs font-medium uppercase tracking-wider text-stone-500">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1.5 w-full rounded-lg border border-white/[0.08] bg-[#131417] px-3.5 py-2.5 text-sm text-stone-200 placeholder-stone-600 outline-none transition focus:border-[#c97848]/60"
      />
    </div>
  )
}

export function InfoStep({
  info,
  form,
  onChange,
  onNext,
  canProceed,
}: {
  info: SystemInfoSnapshot
  form: FormState
  onChange: (form: FormState) => void
  onNext: () => void
  canProceed: boolean
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8 backdrop-blur-md">
        <h2 className="mb-5 text-lg font-medium text-[#f2eee8]">Detected Environment</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <InfoCard icon={Server} label="Hostname" value={info.host.hostname} />
          <InfoCard icon={MonitorCog} label="Operating System" value={info.operating_system.distribution} />
          <InfoCard icon={Cpu} label="CPU" value={`${info.hardware.physical_cores} cores`} />
          <InfoCard icon={MemoryStick} label="Memory" value={info.hardware.ram_total} />
          <InfoCard icon={Container} label="Docker" value={info.docker.running ? 'Running' : info.docker.installed ? 'Installed' : 'Not Detected'} />
          <InfoCard icon={Network} label="Server IP" value={info.host.local_ip || 'Unknown'} />
        </div>
      </div>

      <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8 backdrop-blur-md">
        <h2 className="mb-5 text-lg font-medium text-[#f2eee8]">Installation Details</h2>
        <div className="space-y-4">
          <Field
            label="Installation Name"
            value={form.installation_name}
            onChange={(v) => onChange({ ...form, installation_name: v })}
            placeholder="Golden Dome Production"
          />
          <Field
            label="Administrator Name"
            value={form.administrator_name}
            onChange={(v) => onChange({ ...form, administrator_name: v })}
            placeholder="Jane Doe"
          />
          <Field
            label="Administrator Email"
            value={form.administrator_email}
            onChange={(v) => onChange({ ...form, administrator_email: v })}
            placeholder="admin@company.com"
          />
          <Field
            label="Administrator Password"
            value={form.administrator_password}
            onChange={(v) => onChange({ ...form, administrator_password: v })}
            placeholder="••••••••"
            type="password"
          />
          <Field
            label="Company Name (optional)"
            value={form.company_name}
            onChange={(v) => onChange({ ...form, company_name: v })}
            placeholder="Acme Corp"
          />
        </div>
        <button
          onClick={onNext}
          disabled={!canProceed}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#c97848] to-[#b66838] px-4 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-40"
        >
          Continue <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </motion.div>
  )
}
