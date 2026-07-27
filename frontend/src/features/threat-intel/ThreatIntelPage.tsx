import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import {
  Bug,
  LayoutDashboard,
  Network,
  Search,
  Target,
  Users,
  Zap,
} from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { ThreatDashboard } from './ThreatDashboard'
import { IocExplorer } from './IocExplorer'
import { MalwareDatabase } from './MalwareDatabase'
import { ThreatActorProfiles } from './ThreatActorProfiles'
import { CampaignExplorer } from './CampaignExplorer'
import { VulnerabilityIntelligence } from './VulnerabilityIntelligence'
import { ThreatGraphPage } from './ThreatGraphPage'

const tabs = [
  { label: 'Dashboard', path: 'dashboard', icon: LayoutDashboard },
  { label: 'IOC Explorer', path: 'iocs', icon: Search },
  { label: 'Malware', path: 'malware', icon: Bug },
  { label: 'Actors', path: 'actors', icon: Users },
  { label: 'Campaigns', path: 'campaigns', icon: Target },
  { label: 'Vulnerabilities', path: 'vulnerabilities', icon: Zap },
  { label: 'Graph', path: 'graph', icon: Network },
]

export function ThreatIntelPage() {
  const location = useLocation()
  const activeTab = tabs.find((t) => location.pathname.endsWith(`/threat-intel/${t.path}`))?.path || 'dashboard'

  return (
    <div className="space-y-6">
      <PageHeader
        title="Threat Intelligence"
        subtitle="Investigate IOCs, correlate threats, and prioritize with transparent scoring."
      />

      <div className="flex flex-wrap gap-2 border-b border-gray-800 pb-1">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const active = activeTab === tab.path
          return (
            <Link
              key={tab.path}
              to={`/threat-intel/${tab.path}`}
              className={`flex items-center gap-2 rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                active
                  ? 'border-b-2 border-cyan-500 text-cyan-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </Link>
          )
        })}
      </div>

      <Routes>
        <Route index element={<Navigate to="/threat-intel/dashboard" replace />} />
        <Route path="dashboard" element={<ThreatDashboard />} />
        <Route path="iocs" element={<IocExplorer />} />
        <Route path="malware" element={<MalwareDatabase />} />
        <Route path="actors" element={<ThreatActorProfiles />} />
        <Route path="campaigns" element={<CampaignExplorer />} />
        <Route path="vulnerabilities" element={<VulnerabilityIntelligence />} />
        <Route path="graph" element={<ThreatGraphPage />} />
      </Routes>
    </div>
  )
}

