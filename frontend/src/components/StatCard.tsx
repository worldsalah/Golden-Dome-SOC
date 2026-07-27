import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: string
  trendUp?: boolean
  color?: 'blue' | 'cyan' | 'green' | 'yellow' | 'red'
}

const colorMap = {
  blue: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
  cyan: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20',
  green: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
  yellow: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
  red: 'text-red-400 bg-red-400/10 border-red-400/20',
}

export function StatCard({ title, value, icon: Icon, trend, trendUp, color = 'blue' }: StatCardProps) {
  return (
    <div className={`rounded-lg border p-5 ${colorMap[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-400">{title}</p>
          <p className="mt-1 text-2xl font-bold text-white">{value}</p>
          {trend && (
            <p className={`mt-1 text-xs ${trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
              {trend}
            </p>
          )}
        </div>
        <div className="rounded-md bg-white/5 p-3">
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  )
}
