import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { AnimatePresence } from 'framer-motion'
import { StepIndicator } from '../components/StepIndicator'
import { WelcomeStep } from '../components/WelcomeStep'
import { ScanStep } from '../components/ScanStep'
import { InfoStep } from '../components/InfoStep'
import { SummaryStep, SuccessStep } from '../components/SummaryStep'
import { submitOnboarding } from '../services/onboardingApi'
import type { SystemInfoSnapshot } from '../types'

const STEPS = [
  { id: 1, title: 'Welcome' },
  { id: 2, title: 'Scan' },
  { id: 3, title: 'Details' },
  { id: 4, title: 'Summary' },
]

interface FormState {
  installation_name: string
  administrator_name: string
  administrator_email: string
  administrator_password: string
  company_name: string
}

export function OnboardingWizardPage({ onComplete }: { onComplete?: () => void } = {}) {
  const [step, setStep] = useState(1)
  const [systemInfo, setSystemInfo] = useState<SystemInfoSnapshot | null>(null)
  const [form, setForm] = useState<FormState>({
    installation_name: '',
    administrator_name: '',
    administrator_email: '',
    administrator_password: '',
    company_name: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const mutation = useMutation({
    mutationFn: () =>
      submitOnboarding({
        installation_name: form.installation_name,
        administrator_name: form.administrator_name,
        administrator_email: form.administrator_email,
        administrator_password: form.administrator_password,
        company_name: form.company_name || undefined,
      }),
    onSuccess: () => {
      setError(null)
      setSuccess(true)
      setTimeout(() => onComplete?.(), 1800)
    },
    onError: (e: Error) => setError(e.message),
  })

  const canProceedInfo =
    form.installation_name.length >= 2 &&
    form.administrator_name.length >= 2 &&
    /\S+@\S+\.\S+/.test(form.administrator_email) &&
    form.administrator_password.length >= 8

  return (
    <div className="mx-auto max-w-2xl">
      {step <= STEPS.length && !success && <StepIndicator steps={STEPS} current={step} />}

      <AnimatePresence mode="wait">
        {success ? (
          <SuccessStep key="success" />
        ) : step === 1 ? (
          <WelcomeStep key="welcome" onBegin={() => setStep(2)} />
        ) : step === 2 ? (
          <ScanStep
            key="scan"
            onComplete={(info) => {
              setSystemInfo(info)
              setStep(3)
            }}
          />
        ) : step === 3 && systemInfo ? (
          <InfoStep
            key="info"
            info={systemInfo}
            form={form}
            onChange={setForm}
            onNext={() => setStep(4)}
            canProceed={canProceedInfo}
          />
        ) : step === 4 && systemInfo ? (
          <SummaryStep
            key="summary"
            info={systemInfo}
            installationName={form.installation_name}
            administratorName={form.administrator_name}
            companyName={form.company_name}
            onComplete={() => mutation.mutate()}
            isSubmitting={mutation.isPending}
            error={error}
          />
        ) : null}
      </AnimatePresence>
    </div>
  )
}
