import { useAuthStore } from '@/store/authStore'
import { ROLE_LABELS } from '@/utils/roles'
import { PageHeader } from '@/components/PageHeader'
import { ChartCard } from '@/components/ChartCard'
import { User } from 'lucide-react'

export function ProfilePage() {
  const { user } = useAuthStore()

  return (
    <div className="space-y-6">
      <PageHeader title="User Profile" subtitle="Manage your account details" />

      <div className="flex items-start gap-6 rounded-lg border border-white/[0.07] bg-soc-panel p-6">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[#d8b17a]/10">
          <User className="h-10 w-10 text-[#d8b17a]" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-white">{user?.username || 'Analyst'}</h2>
          <p className="text-sm text-gray-400">{user?.email || 'analyst@goldendome.local'}</p>
          <p className="mt-2 inline-block rounded-full bg-[#1c1e22] px-3 py-1 text-xs font-medium text-[#d8b17a]">
            {user?.role ? ROLE_LABELS[user.role as keyof typeof ROLE_LABELS] : 'SOC Analyst'}
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <ChartCard title="Account Information">
          <div className="space-y-3 text-sm">
            <p><span className="text-gray-500">Username:</span> <span className="text-white">{user?.username}</span></p>
            <p><span className="text-gray-500">Role:</span> <span className="text-white">{user?.role}</span></p>
            <p><span className="text-gray-500">Joined:</span> <span className="text-white">2024-01-01</span></p>
          </div>
        </ChartCard>
        <ChartCard title="Permissions">
          <ul className="list-inside list-disc space-y-1 text-sm text-gray-300">
            <li>View alerts and incidents</li>
            <li>Update alert status</li>
            <li>Generate reports</li>
            <li>View asset inventory</li>
          </ul>
        </ChartCard>
      </div>
    </div>
  )
}
