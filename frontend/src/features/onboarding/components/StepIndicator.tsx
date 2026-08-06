import { motion } from 'framer-motion'
import { Check } from 'lucide-react'

interface Step {
  id: number
  title: string
}

export function StepIndicator({ steps, current }: { steps: Step[]; current: number }) {
  const progress = ((current - 1) / (steps.length - 1)) * 100

  return (
    <div className="mb-10">
      <div className="relative mb-6 h-1 w-full overflow-hidden rounded-full bg-white/[0.06]">
        <motion.div
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-[#c97848] to-[#d8b17a]"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeInOut' }}
        />
      </div>
      <div className="flex items-center justify-between">
        {steps.map((s) => (
          <div key={s.id} className="flex flex-col items-center gap-2">
            <motion.div
              animate={{
                scale: current === s.id ? 1.1 : 1,
                borderColor: current >= s.id ? 'rgba(201,120,72,0.6)' : 'rgba(255,255,255,0.08)',
              }}
              className={`grid h-9 w-9 place-items-center rounded-full border-2 text-xs font-semibold transition-colors ${
                current >= s.id ? 'bg-[#c97848]/10 text-[#d8b17a]' : 'text-stone-600'
              }`}
            >
              {current > s.id ? <Check className="h-4 w-4" /> : s.id}
            </motion.div>
            <span
              className={`text-[10px] font-medium uppercase tracking-wider ${
                current >= s.id ? 'text-stone-300' : 'text-stone-600'
              }`}
            >
              {s.title}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
