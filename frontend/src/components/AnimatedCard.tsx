import { type ReactNode } from 'react'
import { motion } from 'framer-motion'

interface AnimatedCardProps {
  children: ReactNode
  className?: string
  delay?: number
}

export function AnimatedCard({ children, className = '', delay = 0 }: AnimatedCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ y: -4, boxShadow: '0 0 24px rgba(6,182,212,0.12)' }}
      className={`rounded-xl border border-gray-800/80 bg-soc-panel/80 backdrop-blur-sm ${className}`}
    >
      {children}
    </motion.div>
  )
}
