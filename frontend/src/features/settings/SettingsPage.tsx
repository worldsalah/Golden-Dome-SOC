import { useState } from 'react'
import { Bell, Lock, Shield, User } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'

export function SettingsPage() {
  const [tab, setTab] = useState('general')

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" subtitle="Configure platform preferences and integrations" />

      <div className="flex gap-2 border-b border-white/[0.07]">
        {[
          { id: 'general', label: 'General', icon: Shield },
          { id: 'profile', label: 'Profile', icon: User },
          { id: 'security', label: 'Security', icon: Lock },
          { id: 'notifications', label: 'Notifications', icon: Bell },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.id ? 'border-[#c97848] text-[#d8b17a]' : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Platform Preferences">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300">Theme</label>
              <select className="mt-1 w-full rounded-md border border-white/[0.1] bg-[#17181b] px-3 py-2 text-sm text-white">
                <option>Dark SOC</option>
                <option>Light</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300">Default landing page</label>
              <select className="mt-1 w-full rounded-md border border-white/[0.1] bg-[#17181b] px-3 py-2 text-sm text-white">
                <option>Dashboard</option>
                <option>Alerts</option>
              </select>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Integrations">
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-md bg-[#17181b]/50 p-3">
              <div>
                <p className="text-sm font-medium text-white">Wazuh API</p>
                <p className="text-xs text-gray-500">https://127.0.0.1:55000</p>
              </div>
              <span className="rounded-full bg-emerald-400/10 px-2 py-1 text-xs font-medium text-emerald-400">Connected</span>
            </div>
            <div className="flex items-center justify-between rounded-md bg-[#17181b]/50 p-3">
              <div>
                <p className="text-sm font-medium text-white">OpenSearch</p>
                <p className="text-xs text-gray-500">https://127.0.0.1:9200</p>
              </div>
              <span className="rounded-full bg-emerald-400/10 px-2 py-1 text-xs font-medium text-emerald-400">Connected</span>
            </div>
          </div>
        </ChartCard>
      </div>
    </div>
  )
}
