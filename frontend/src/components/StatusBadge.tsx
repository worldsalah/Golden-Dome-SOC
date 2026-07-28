interface StatusBadgeProps {
  status: string
}

const statusStyles: Record<string, string> = {
  new: 'bg-[#8d7ab5]/10 text-[#a996d3] border-[#8d7ab5]/25',
  acknowledged: 'bg-[#d8b17a]/10 text-[#e2c495] border-[#d8b17a]/25',
  investigating: 'bg-[#c97848]/10 text-[#dfa07a] border-[#c97848]/25',
  resolved: 'bg-[#3ba676]/10 text-[#7cc9a5] border-[#3ba676]/25',
  false_positive: 'bg-stone-400/10 text-stone-400 border-stone-400/20',
  open: 'bg-[#b94747]/10 text-[#e08585] border-[#b94747]/25',
  in_progress: 'bg-[#d8b17a]/10 text-[#e2c495] border-[#d8b17a]/25',
  closed: 'bg-stone-400/10 text-stone-400 border-stone-400/20',
  low: 'bg-[#3ba676]/10 text-[#7cc9a5] border-[#3ba676]/25',
  medium: 'bg-[#d8b17a]/10 text-[#e2c495] border-[#d8b17a]/25',
  high: 'bg-[#c97848]/10 text-[#dfa07a] border-[#c97848]/25',
  critical: 'bg-[#b94747]/10 text-[#e08585] border-[#b94747]/25',
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const style = statusStyles[status.toLowerCase()] || statusStyles.new
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${style}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}
