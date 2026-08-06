import { motion } from 'framer-motion'
import { ShieldCheck, ArrowRight } from 'lucide-react'

export function WelcomeStep({ onBegin }: { onBegin: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center rounded-2xl border border-white/[0.06] bg-white/[0.02] p-12 text-center backdrop-blur-md"
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className="mb-6 grid h-20 w-20 place-items-center rounded-2xl border border-white/[0.08] bg-white/[0.03]"
      >
        <ShieldCheck className="h-9 w-9 text-[#d8b17a]" />
      </motion.div>

      <h1 className="text-3xl font-medium tracking-tight text-[#f2eee8]">Welcome to Golden Dome</h1>
      <p className="mt-2 text-sm font-medium uppercase tracking-[0.2em] text-[#c97848]">
        Enterprise AI Security Operations Center
      </p>
      <p className="mt-4 max-w-md text-sm leading-relaxed text-stone-400">
        This wizard will scan your environment, detect connected services, and configure your
        deployment in a few short steps.
      </p>

      <button
        onClick={onBegin}
        className="mt-8 flex items-center gap-2 rounded-full bg-gradient-to-r from-[#c97848] to-[#b66838] px-8 py-3 text-sm font-medium text-white shadow-[0_0_30px_-10px_rgba(201,120,72,0.6)] transition hover:opacity-90"
      >
        Begin Installation <ArrowRight className="h-4 w-4" />
      </button>
    </motion.div>
  )
}
