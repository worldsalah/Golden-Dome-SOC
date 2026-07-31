import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Building2, CheckCircle2, ArrowRight, Loader2 } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { runOnboardingWizard } from '@/services/api'

export function OnboardingWizardPage({ onComplete }: { onComplete?: () => void } = {}) {
  const [step, setStep] = useState(1)
  const [org, setOrg] = useState({ name: '', slug: '', industry: '', contact_email: '' })
  const [admin, setAdmin] = useState({ username: '', email: '', password: '' })
  const [result, setResult] = useState<{ organization_id: number; admin_user_id: number; connectors_created: number; assets_created: number; next_steps: string[] } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const wizardMut = useMutation({
    mutationFn: () => runOnboardingWizard({ org, admin, connectors: [], assets: [] }),
    onSuccess: (data) => {
      setResult(data)
      setStep(5)
      setError(null)
      setTimeout(() => onComplete?.(), 1500)
    },
    onError: (e: Error) => setError(e.message),
  })

  const steps = [
    { id: 1, title: 'Organization', icon: Building2 },
    { id: 2, title: 'Admin User', icon: Building2 },
    { id: 3, title: 'Review & Deploy', icon: CheckCircle2 },
  ]

  const canProceed = () => {
    if (step === 1) return org.name.length >= 2 && org.slug.length >= 2 && /^[a-z0-9-]+$/.test(org.slug)
    if (step === 2) return admin.username.length >= 3 && /\S+@\S+\.\S+/.test(admin.email) && admin.password.length >= 8
    return true
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader title="Customer Onboarding" subtitle="Set up a new organization with admin user and connectors" />

      <div className="flex items-center justify-between">
        {steps.map((s, i) => (
          <div key={s.id} className="flex flex-1 items-center">
            <div className="flex flex-col items-center">
              <div className={`grid h-9 w-9 place-items-center rounded-full border-2 ${
                step >= s.id ? 'border-[#c97848] bg-[#c97848]/10 text-[#d8b17a]' : 'border-white/[0.1] text-stone-600'
              }`}>
                {step > s.id ? <CheckCircle2 className="h-4 w-4" /> : <s.icon className="h-4 w-4" />}
              </div>
              <span className={`mt-1.5 text-[10px] font-medium ${step >= s.id ? 'text-stone-300' : 'text-stone-600'}`}>{s.title}</span>
            </div>
            {i < steps.length - 1 && (
              <div className={`mx-2 h-px flex-1 ${step > s.id ? 'bg-[#c97848]/40' : 'bg-white/[0.06]'}`} />
            )}
          </div>
        ))}
      </div>

      {step === 1 && (
        <ChartCard title="Organization Details">
          <div className="space-y-4">
            <Field label="Organization Name" value={org.name} onChange={(v) => setOrg({ ...org, name: v })} placeholder="Acme Security" />
            <Field label="Slug (lowercase, hyphens)" value={org.slug} onChange={(v) => setOrg({ ...org, slug: v })} placeholder="acme-security" />
            <Field label="Industry" value={org.industry} onChange={(v) => setOrg({ ...org, industry: v })} placeholder="technology" />
            <Field label="Contact Email" value={org.contact_email} onChange={(v) => setOrg({ ...org, contact_email: v })} placeholder="admin@acme.com" />
            <NavButtons onNext={() => setStep(2)} disabled={!canProceed()} />
          </div>
        </ChartCard>
      )}

      {step === 2 && (
        <ChartCard title="Admin User">
          <div className="space-y-4">
            <Field label="Username" value={admin.username} onChange={(v) => setAdmin({ ...admin, username: v })} placeholder="admin" />
            <Field label="Email" value={admin.email} onChange={(v) => setAdmin({ ...admin, email: v })} placeholder="admin@acme.com" />
            <Field label="Password (min 8 chars)" value={admin.password} onChange={(v) => setAdmin({ ...admin, password: v })} placeholder="••••••••" type="password" />
            <NavButtons onBack={() => setStep(1)} onNext={() => setStep(3)} disabled={!canProceed()} />
          </div>
        </ChartCard>
      )}

      {step === 3 && (
        <ChartCard title="Review & Deploy">
          <div className="space-y-3">
            <div className="rounded-md bg-[#17181b]/50 p-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-stone-500">Organization</p>
              <p className="text-sm text-stone-300">{org.name} <span className="text-stone-600">· {org.slug}</span></p>
              {org.industry && <p className="text-xs text-stone-500">{org.industry}</p>}
            </div>
            <div className="rounded-md bg-[#17181b]/50 p-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-stone-500">Admin User</p>
              <p className="text-sm text-stone-300">{admin.username} <span className="text-stone-600">· {admin.email}</span></p>
            </div>
            <button
              onClick={() => wizardMut.mutate()}
              disabled={wizardMut.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-emerald-600/80 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-600 disabled:opacity-50"
            >
              {wizardMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
              {wizardMut.isPending ? 'Deploying…' : 'Deploy Organization'}
            </button>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <button onClick={() => setStep(2)} className="w-full text-center text-xs text-stone-500 hover:text-stone-300">← Back</button>
          </div>
        </ChartCard>
      )}

      {step === 5 && result && (
        <ChartCard title="Onboarding Complete">
          <div className="space-y-4">
            <div className="flex flex-col items-center py-4">
              <CheckCircle2 className="h-12 w-12 text-emerald-400" />
              <p className="mt-2 text-lg font-medium text-stone-200">Organization deployed successfully</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Org ID" value={result.organization_id} />
              <Stat label="Admin User ID" value={result.admin_user_id} />
              <Stat label="Connectors" value={result.connectors_created} />
              <Stat label="Assets" value={result.assets_created} />
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-stone-500">Next Steps</p>
              <ul className="space-y-1.5">
                {result.next_steps.map((s, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-stone-400">
                    <ArrowRight className="h-3 w-3 text-[#c97848]" /> {s}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </ChartCard>
      )}
    </div>
  )
}

function Field({ label, value, onChange, placeholder, type = 'text' }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string; type?: string }) {
  return (
    <div>
      <label className="block text-sm font-medium text-stone-300">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full rounded-md border border-white/[0.1] bg-[#131417] px-3 py-2 text-sm text-stone-200 placeholder-stone-600 outline-none focus:border-[#b98947]/50"
      />
    </div>
  )
}

function NavButtons({ onBack, onNext, disabled }: { onBack?: () => void; onNext: () => void; disabled: boolean }) {
  return (
    <div className="flex justify-between">
      {onBack ? (
        <button onClick={onBack} className="text-xs text-stone-500 hover:text-stone-300">← Back</button>
      ) : <span />}
      <button
        onClick={onNext}
        disabled={disabled}
        className="flex items-center gap-1.5 rounded-md bg-[#c97848] px-4 py-2 text-sm font-medium text-white hover:bg-[#b66838] disabled:opacity-50"
      >
        Next <ArrowRight className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md bg-[#17181b]/50 p-3 text-center">
      <p className="text-2xl font-bold text-[#d8b17a]">{value}</p>
      <p className="mt-0.5 text-[10px] uppercase tracking-wider text-stone-600">{label}</p>
    </div>
  )
}
