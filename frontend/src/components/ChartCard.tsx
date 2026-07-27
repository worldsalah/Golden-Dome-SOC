import { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

interface ChartCardProps {
  title?: string
  children?: ReactNode
  className?: string
  right?: ReactNode
  value?: string | number
  subtitle?: string
  icon?: LucideIcon
}

export function ChartCard({ title, children, className = '', right, value, subtitle, icon: Icon }: ChartCardProps) {
  return (
    <div className={`rounded-lg border border-gray-800 bg-soc-panel p-4 ${className}`}>
      <div className="mb-4 flex items-center justify-between">
        {title && <h3 className="text-sm font-semibold text-gray-200">{title}</h3>}
        {right}
      </div>
      {value !== undefined ? (
        <div className="flex items-center gap-3">
          {Icon && <Icon className="h-8 w-8 text-cyan-400" />}
          <div>
            <p className="text-2xl font-semibold text-white">{value}</p>
            {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
          </div>
        </div>
      ) : (
        children
      )}
    </div>
  )
}
