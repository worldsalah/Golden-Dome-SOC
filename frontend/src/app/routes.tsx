import { Navigate, Route, Routes } from 'react-router-dom'

import { MainLayout } from '@/layouts/MainLayout'
import { ProtectedRoute } from '@/components/ProtectedRoute'

import { LoginPage } from '@/features/authentication/LoginPage'
import { ExperiencePage } from '@/features/experience/ExperiencePage'
import { ProfilePage } from '@/features/profile/ProfilePage'
import { CommandCenterPage } from '@/features/dashboard/CommandCenterPage'
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
import { ValidationCenterPage } from '@/features/validation/ValidationCenterPage'
import { AttackCoveragePage } from '@/features/validation/AttackCoveragePage'
import { FalsePositiveReductionPage } from '@/features/validation/FalsePositiveReductionPage'
import { DetectionPerformancePage } from '@/features/validation/DetectionPerformancePage'
import { SocHealthScorePage } from '@/features/validation/SocHealthScorePage'
import { ValidationReportsPage } from '@/features/validation/ValidationReportsPage'
import { EvidenceViewerPage } from '@/features/validation/EvidenceViewerPage'
import { ReplayEnginePage } from '@/features/validation/ReplayEnginePage'
import { ThreatIntelPage } from '@/features/threat-intel/ThreatIntelPage'
import { RiskCenterPage } from '@/features/risk/RiskCenterPage'
import { SOARAutomationPage } from '@/features/soar/SOARAutomationPage'
import { SettingsPage } from '@/features/settings/SettingsPage'
import { SecurityCenterPage } from '@/features/security/SecurityCenterPage'
import { ConnectorsPage } from '@/features/connectors/ConnectorsPage'
import { OnboardingWizardPage } from '@/features/onboarding/OnboardingWizardPage'
import { PosturePage } from '@/features/posture/PosturePage'
import { HotelSecurityPage } from '@/features/hotel/HotelSecurityPage'
import { DeploymentPage } from '@/features/deployment/DeploymentPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<ExperiencePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
        <Route path="workspace" element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<CommandCenterPage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="alerts/:id" element={<AlertDetailsPage />} />
        <Route path="detection-center" element={<DetectionCenterPage />} />
        <Route path="validation" element={<ValidationCenterPage />} />
        <Route path="attack-coverage" element={<AttackCoveragePage />} />
        <Route path="false-positive-reduction" element={<FalsePositiveReductionPage />} />
        <Route path="detection-performance" element={<DetectionPerformancePage />} />
        <Route path="soc-health-score" element={<SocHealthScorePage />} />
        <Route path="validation-reports" element={<ValidationReportsPage />} />
        <Route path="evidence-viewer" element={<EvidenceViewerPage />} />
        <Route path="replay-engine" element={<ReplayEnginePage />} />
        <Route path="incidents" element={<IncidentsPage />} />
        <Route path="incidents/:id" element={<IncidentDetailsPage />} />
        <Route path="assets" element={<AssetsPage />} />
        <Route path="assets/:id" element={<AssetDetailsPage />} />
        <Route path="mitre" element={<MitrePage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="ai" element={<AiAssistantPage />} />
        <Route path="threat-intel/*" element={<ThreatIntelPage />} />
        <Route path="risk" element={<RiskCenterPage />} />
        <Route path="soar" element={<SOARAutomationPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="security-center" element={<SecurityCenterPage />} />
        <Route path="connectors" element={<ConnectorsPage />} />
        <Route path="onboarding" element={<OnboardingWizardPage />} />
        <Route path="posture" element={<PosturePage />} />
        <Route path="hotel-security" element={<HotelSecurityPage />} />
        <Route path="deployment" element={<DeploymentPage />} />
      </Route>
    </Routes>
  )
}
