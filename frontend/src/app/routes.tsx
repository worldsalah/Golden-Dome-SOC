import { Navigate, Route, Routes } from 'react-router-dom'

import { MainLayout } from '@/layouts/MainLayout'
import { ProtectedRoute } from '@/components/ProtectedRoute'

import { LoginPage } from '@/features/authentication/LoginPage'
import { ProfilePage } from '@/features/profile/ProfilePage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { AlertsPage } from '@/features/alerts/AlertsPage'
import { AlertDetailsPage } from '@/features/alerts/AlertDetailsPage'
import { IncidentsPage } from '@/features/incidents/IncidentsPage'
import { IncidentDetailsPage } from '@/features/incidents/IncidentDetailsPage'
import { AssetsPage } from '@/features/assets/AssetsPage'
import { AssetDetailsPage } from '@/features/assets/AssetDetailsPage'
import { MitrePage } from '@/features/mitre/MitrePage'
import { ReportsPage } from '@/features/reports/ReportsPage'
import { AiAssistantPage } from '@/features/ai/AiAssistantPage'
import { DetectionCenterPage } from '@/features/detection-center/DetectionCenterPage'
import { ThreatIntelPage } from '@/features/threat-intel/ThreatIntelPage'
import { RiskCenterPage } from '@/features/risk/RiskCenterPage'
import { VulnerabilityManagementPage } from '@/features/vulnerabilities/VulnerabilityManagementPage'
import { SOARAutomationPage } from '@/features/soar/SOARAutomationPage'
import { SettingsPage } from '@/features/settings/SettingsPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="alerts/:id" element={<AlertDetailsPage />} />
        <Route path="detection-center" element={<DetectionCenterPage />} />
        <Route path="incidents" element={<IncidentsPage />} />
        <Route path="incidents/:id" element={<IncidentDetailsPage />} />
        <Route path="assets" element={<AssetsPage />} />
        <Route path="assets/:id" element={<AssetDetailsPage />} />
        <Route path="mitre" element={<MitrePage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="ai" element={<AiAssistantPage />} />
        <Route path="threat-intel/*" element={<ThreatIntelPage />} />
        <Route path="risk" element={<RiskCenterPage />} />
        <Route path="vulnerabilities" element={<VulnerabilityManagementPage />} />
        <Route path="soar" element={<SOARAutomationPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
    </Routes>
  )
}
