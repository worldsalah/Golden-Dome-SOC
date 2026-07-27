interface StatusBadgeProps {
  status: string
}

const statusStyles: Record<string, string> = {
  new: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
  acknowledged: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20',
  investigating: 'bg-orange-400/10 text-orange-400 border-orange-400/20',
  resolved: 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20',
  false_positive: 'bg-gray-400/10 text-gray-400 border-gray-400/20',
  open: 'bg-red-400/10 text-red-400 border-red-400/20',
  in_progress: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20',
  closed: 'bg-gray-400/10 text-gray-400 border-gray-400/20',
  low: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
  medium: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20',
  high: 'bg-orange-400/10 text-orange-400 border-orange-400/20',
  critical: 'bg-red-400/10 text-red-400 border-red-400/20',
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const style = statusStyles[status.toLowerCase()] || statusStyles.new
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${style}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}
