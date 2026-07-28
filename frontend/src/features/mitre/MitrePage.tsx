import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { ShieldCheck, Target, X } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { getMitreMatrix, getDetectionCoverage } from '@/services/api'
import type { MitreTechnique } from '@/types'

export function MitrePage() {
  const [selected, setSelected] = useState<{ tactic: string; tech: MitreTechnique } | null>(null)

  const { data: matrixData, isLoading: matrixLoading } = useQuery({
    queryKey: ['mitre-matrix'],
    queryFn: getMitreMatrix,
  })

  const { data: coverage } = useQuery({
    queryKey: ['detection-coverage'],
    queryFn: getDetectionCoverage,
  })

  const tactics = matrixData?.tactics || []
  const matrix = matrixData?.matrix || {}
  const totalTechniques = matrixData?.total_techniques || 0
  const detectedTechniques = matrixData?.detected_techniques || 0

  const statusStyle = (status: string) => {
    switch (status) {
      case 'detected':
        return 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
      case 'partial':
        return 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300'
      case 'planned':
        return 'bg-gray-700/50 border-gray-600 text-gray-400'
      default:
        return 'bg-[#1c1e22] border-white/[0.1] text-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="MITRE ATT&CK Matrix" subtitle="Interactive technique coverage and detection status" />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-white/[0.07] bg-soc-panel p-4">
          <p className="text-xs text-gray-500">Total Techniques</p>
          <p className="text-2xl font-bold text-white">{totalTechniques}</p>
        </div>
        <div className="rounded-lg border border-white/[0.07] bg-soc-panel p-4">
          <p className="text-xs text-gray-500">Detected / Partial</p>
          <p className="text-2xl font-bold text-emerald-400">{detectedTechniques}</p>
        </div>
        <div className="rounded-lg border border-white/[0.07] bg-soc-panel p-4">
          <p className="text-xs text-gray-500">Coverage</p>
          <p className="text-2xl font-bold text-[#d8b17a]">{coverage?.coverage_percentage || 0}%</p>
        </div>
        <div className="rounded-lg border border-white/[0.07] bg-soc-panel p-4">
          <p className="text-xs text-gray-500">Tactics</p>
          <p className="text-2xl font-bold text-white">{tactics.length}</p>
        </div>
      </div>

      <ChartCard title="Technique Matrix">
        {matrixLoading ? (
          <p className="text-sm text-gray-500">Loading matrix...</p>
        ) : tactics.length === 0 ? (
          <p className="text-sm text-gray-500">No MITRE techniques seeded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${tactics.length}, minmax(160px, 1fr))` }}>
              {tactics.map((tactic) => (
                <div key={tactic} className="flex flex-col gap-2">
                  <h3 className="text-center text-xs font-semibold uppercase tracking-wide text-[#d8b17a]">{tactic}</h3>
                  {(matrix[tactic] || []).map((tech) => (
                    <motion.button
                      key={tech.technique_id}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setSelected({ tactic, tech })}
                      className={`rounded-md border p-2 text-left transition-colors ${statusStyle(tech.detection_status || 'planned')}`}
                    >
                      <div className="flex items-center gap-1">
                        {(tech.detection_status || 'planned') === 'detected' ? <ShieldCheck className="h-3 w-3" /> : <Target className="h-3 w-3" />}
                        <span className="font-mono text-[10px]">{tech.technique_id}</span>
                      </div>
                      <p className="mt-1 text-xs font-medium leading-tight">{tech.name}</p>
                      {(tech.alert_count || 0) > 0 && <p className="mt-1 text-[10px] opacity-80">{tech.alert_count} alerts</p>}
                    </motion.button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </ChartCard>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="w-full max-w-md rounded-xl border border-white/[0.1] bg-[#17181b] p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-[#d8b17a]">{selected.tactic}</p>
                <h3 className="text-lg font-semibold text-white">{selected.tech.technique_id} — {selected.tech.name}</h3>
              </div>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-white"><X className="h-5 w-5" /></button>
            </div>
            <p className="text-sm text-gray-300">{selected.tech.description || 'No description available.'}</p>
            <div className="mt-4 flex items-center gap-3">
              <span className={`rounded-full px-2 py-0.5 text-xs ${statusStyle(selected.tech.detection_status)}`}>{selected.tech.detection_status}</span>
              <span className="text-xs text-gray-500">{selected.tech.alert_count} alert(s)</span>
            </div>
            {selected.tech.associated_rules && (
              <div className="mt-4">
                <p className="text-xs text-gray-500">Associated Rules</p>
                <p className="text-sm text-gray-300">{selected.tech.associated_rules}</p>
              </div>
            )}
          </motion.div>
        </div>
      )}
    </div>
  )
}
