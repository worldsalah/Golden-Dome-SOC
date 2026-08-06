import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, Loader2, Cpu, HardDrive, MemoryStick, MonitorCog, Network, Container, Database, Sparkles } from 'lucide-react'
import { getSystemInfo } from '../services/onboardingApi'
import type { SystemInfoSnapshot } from '../types'

const SCAN_ITEMS = [
  { key: 'os', label: 'Operating System', icon: MonitorCog },
  { key: 'cpu', label: 'CPU', icon: Cpu },
  { key: 'memory', label: 'Memory', icon: MemoryStick },
  { key: 'disk', label: 'Disk', icon: HardDrive },
  { key: 'docker', label: 'Docker', icon: Container },
  { key: 'network', label: 'Network', icon: Network },
  { key: 'services', label: 'Platform Services', icon: Database },
]

export function ScanStep({ onComplete }: { onComplete: (info: SystemInfoSnapshot) => void }) {
  const [revealed, setRevealed] = useState(0)
  const [done, setDone] = useState(false)

  const { data, isSuccess } = useQuery({
    queryKey: ['system-info'],
    queryFn: getSystemInfo,
    staleTime: Infinity,
    retry: 1,
  })

  useEffect(() => {
    if (revealed >= SCAN_ITEMS.length) {
      setDone(true)
      return
    }
    const t = setTimeout(() => setRevealed((r) => r + 1), 420)
    return () => clearTimeout(t)
  }, [revealed])

  useEffect(() => {
    if (done && isSuccess && data) {
      const t = setTimeout(() => onComplete(data), 700)
      return () => clearTimeout(t)
    }
  }, [done, isSuccess, data, onComplete])

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-10 backdrop-blur-md"
    >
      <div className="mb-8 flex items-center gap-3">
        <Sparkles className="h-5 w-5 text-[#d8b17a]" />
        <h2 className="text-lg font-medium text-[#f2eee8]">Scanning environment…</h2>
      </div>

      <div className="space-y-3">
        {SCAN_ITEMS.map((item, i) => {
          const isRevealed = i < revealed
          const Icon = item.icon
          return (
            <motion.div
              key={item.key}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: isRevealed ? 1 : 0.3, x: 0 }}
              transition={{ duration: 0.3 }}
              className="flex items-center gap-3 rounded-lg border border-white/[0.04] bg-[#131417]/40 px-4 py-3"
            >
              <Icon className="h-4 w-4 text-stone-500" />
              <span className="flex-1 text-sm text-stone-300">{item.label}</span>
              <AnimatePresence mode="wait">
                {isRevealed ? (
                  <motion.div
                    key="check"
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                  >
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  </motion.div>
                ) : (
                  <Loader2 className="h-4 w-4 animate-spin text-stone-600" />
                )}
              </AnimatePresence>
            </motion.div>
          )
        })}
      </div>

      {done && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-6 text-center text-sm font-medium text-emerald-400"
        >
          {isSuccess ? 'Scan completed' : 'Finalizing scan…'}
        </motion.p>
      )}
    </motion.div>
  )
}
