import { useQuery } from '@tanstack/react-query'
import { Shield, TrendingUp, AlertTriangle, Target } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { getPosture } from '@/services/api'

export function PosturePage() {
  const { data, isLoading } = useQuery({ queryKey: ['posture'], queryFn: getPosture })

  const scores = data as Record<string, unknown> | undefined
  const overall = scores?.overall_score as number | undefined
  const grade = scores?.grade as string | undefined

  const getScoreColor = (score: number | undefined) => {
    if (score === undefined) return 'text-stone-600'
    if (score >= 80) return 'text-emerald-400'
    if (score >= 60) return 'text-amber-400'
    return 'text-red-400'
  }

  const components = [
    { key: 'asset_risk_score', label: 'Asset Risk', icon: Shield },
    { key: 'vulnerability_risk_score', label: 'Vulnerability Risk', icon: AlertTriangle },
    { key: 'detection_coverage_score', label: 'Detection Coverage', icon: Target },
    { key: 'compliance_score', label: 'Compliance', icon: CheckCircle },
    { key: 'attack_surface_score', label: 'Attack Surface', icon: TrendingUp },
    { key: 'maturity_score', label: 'Maturity', icon: Shield },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Security Posture" subtitle="Comprehensive security posture assessment and scoring" />

      <div className="grid gap-4 lg:grid-cols-4">
        <ChartCard title="Overall Score">
          <div className="text-center py-4">
            {isLoading ? (
              <p className="text-stone-600">Loading…</p>
            ) : (
              <>
                <p className={`text-5xl font-bold ${getScoreColor(overall)}`}>{overall !== undefined ? Math.round(overall) : '—'}</p>
                <p className="mt-2 text-xs uppercase tracking-wider text-stone-600">Grade: {grade || '—'}</p>
              </>
            )}
          </div>
        </ChartCard>

        {components.map((c) => {
          const val = scores?.[c.key] as number | undefined
          return (
            <ChartCard key={c.key} title={c.label}>
              <div className="text-center py-4">
                <c.icon className="mx-auto mb-2 h-5 w-5 text-stone-600" />
                <p className={`text-3xl font-bold ${getScoreColor(val)}`}>{val !== undefined ? Math.round(val) : '—'}</p>
              </div>
            </ChartCard>
          )
        })}
      </div>

      <ChartCard title="Posture Details">
        {isLoading ? (
          <p className="py-4 text-center text-sm text-stone-600">Loading posture data…</p>
        ) : (
          <pre className="overflow-x-auto rounded-md bg-[#0a0a0b] p-4 text-xs text-stone-400">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </ChartCard>
    </div>
  )
}

function CheckCircle({ className }: { className?: string }) {
  return <Shield className={className} />
}
