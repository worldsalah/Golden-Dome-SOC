import { Bug, Globe, Link2, Radar, Shield, Skull, Users, Zap } from 'lucide-react'

export const typeIcons: Record<string, React.ReactNode> = {
  ip: <Globe className="h-4 w-4" />,
  domain: <Link2 className="h-4 w-4" />,
  hash: <Bug className="h-4 w-4" />,
  url: <Link2 className="h-4 w-4" />,
  cve: <Zap className="h-4 w-4" />,
  email: <Users className="h-4 w-4" />,
  mitre_technique: <Shield className="h-4 w-4" />,
  default: <Radar className="h-4 w-4" />,
}

export function severityClass(severity: string) {
  switch (severity) {
    case 'extreme':
      return 'bg-red-500/10 text-red-400 border-red-500/20'
    case 'critical':
      return 'bg-orange-500/10 text-orange-400 border-orange-500/20'
    case 'high':
      return 'bg-amber-500/10 text-amber-400 border-amber-500/20'
    case 'medium':
      return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
    default:
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
  }
}

export function scoreColor(score: number) {
  if (score >= 80) return 'text-red-400'
  if (score >= 60) return 'text-orange-400'
  if (score >= 40) return 'text-amber-400'
  if (score >= 20) return 'text-yellow-400'
  return 'text-emerald-400'
}

export function threatIcon(severity: string) {
  if (severity === 'extreme' || severity === 'critical') return <Skull className="h-5 w-5 text-red-400" />
  return <Shield className="h-5 w-5 text-cyan-400" />
}
