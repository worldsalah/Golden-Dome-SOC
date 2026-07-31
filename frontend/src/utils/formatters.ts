import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

export function formatDate(value?: string | null): string {
  if (!value) return '—'
  return dayjs(value).format('YYYY-MM-DD HH:mm')
}

export function formatRelativeTime(value?: string | null): string {
  if (!value) return '—'
  return dayjs(value).fromNow()
}

export function formatTime(value?: string | null, opts?: Intl.DateTimeFormatOptions): string {
  if (!value) return '—'
  const d = new Date(value)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleTimeString(undefined, opts)
}

export function formatDateTime(value?: string | null, opts?: Intl.DateTimeFormatOptions): string {
  if (!value) return '—'
  const d = new Date(value)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleString(undefined, opts)
}

export function severityLabel(level: number): string {
  if (level >= 13) return 'Critical'
  if (level >= 10) return 'High'
  if (level >= 7) return 'Medium'
  if (level >= 4) return 'Low'
  return 'Info'
}

export function severityColor(level: number): string {
  if (level >= 13) return 'text-red-400 bg-red-400/10 border-red-400/20'
  if (level >= 10) return 'text-orange-400 bg-orange-400/10 border-orange-400/20'
  if (level >= 7) return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20'
  if (level >= 4) return 'text-blue-400 bg-blue-400/10 border-blue-400/20'
  return 'text-gray-400 bg-gray-400/10 border-gray-400/20'
}
