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
    <div className={`enterprise-panel p-4 ${className}`}>
      <div className="mb-4 flex items-center justify-between">
        {title && <h3 className="panel-title">{title}</h3>}
        {right}
      </div>
      {value !== undefined ? (
        <div className="flex items-center gap-3">
          {Icon && <Icon className="h-7 w-7 text-[#d8b17a]" strokeWidth={1.5} />}
          <div>
            <p className="font-mono text-2xl font-medium tabular-nums text-stone-100">{value}</p>
            {subtitle && <p className="text-xs text-stone-500">{subtitle}</p>}
          </div>
        </div>
      ) : (
        children
      )}
    </div>
  )
}
