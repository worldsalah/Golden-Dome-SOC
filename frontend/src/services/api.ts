import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          localStorage.setItem('access_token', data.access_token)
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          }
          return apiClient(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }

    return Promise.reject(error)
  },
)

export default apiClient

export async function login(username: string, password: string) {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)
  const { data } = await axios.post(`${API_BASE_URL}/auth/login`, formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export async function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

// Sentinel AI
export async function analyzeAlert(alertId: number) {
  const { data } = await apiClient.post('/ai/analyze-alert', { alert_id: alertId })
  return data as import('@/types').AiAnalysis
}

export async function askSentinel(question: string, alertId?: number) {
  const { data } = await apiClient.post('/ai/chat', { question, alert_id: alertId })
  return data as { answer: string; source: string }
}

export async function investigateIncidentWithAI(incidentId: number) {
  const { data } = await apiClient.post('/ai/investigate-incident', { incident_id: incidentId })
  return data as Record<string, unknown>
}

export async function threatHuntWithAI(query: string) {
  const { data } = await apiClient.post('/ai/threat-hunt', { query })
  return data as {
    summary: string
    hypotheses: string[]
    recommended_queries: string[]
    indicators_to_hunt: string[]
    mitre_techniques: string[]
    priority: string
    confidence: number
    rag_sources?: { source: string; title: string; score: number }[]
  }
}

export async function generateAIPlaybook(payload: { alert_description: string; mitre_technique?: string; severity?: number }) {
  const { data } = await apiClient.post('/ai/generate-playbook', payload)
  return data as { name: string; description: string; trigger: string; actions: { action: string; params: Record<string, unknown> }[]; expected_outcome: string; automation_notes: string }
}

export async function generateAIDailyReport() {
  const { data } = await apiClient.post('/ai/generate-report', {})
  return data as { title: string; date: string; executive_summary: string; key_metrics: Record<string, number>; top_threats: string[]; incident_status: { id: number; name: string; status: string; severity: string }[]; recommendations: string[] }
}

export async function submitAIFeedback(analysisId: number, feedback: { helpful: boolean; incorrect: boolean; comment?: string }) {
  const { data } = await apiClient.post('/ai/feedback', { analysis_id: analysisId, ...feedback })
  return data as { feedback_id: number; status: string }
}

export async function getAIHistory(limit = 100) {
  const { data } = await apiClient.get('/ai/history', { params: { limit } })
  return data as { data: import('@/types').AiAnalysis[] }
}

export async function getAIAuditLogs(limit = 100) {
  const { data } = await apiClient.get('/ai/audit-logs', { params: { limit } })
  return data as { data: { id: number; endpoint: string; request_payload: string; response_summary: string; source: string; created_at: string }[] }
}

export async function getAIHealth() {
  const { data } = await apiClient.get('/ai/health')
  return data as { ollama: { status: string; data?: unknown; error?: string } }
}

export async function getAIAnomalies(hours = 168) {
  const { data } = await apiClient.get('/ai/anomalies', { params: { hours } })
  return data as { auth: { source_ip: string; score: number; details?: string }[]; traffic: { source_ip: string; score: number; details?: string }[] }
}

export async function getAIFeedback(limit = 100) {
  const { data } = await apiClient.get('/ai/feedback', { params: { limit } })
  return data as { data: { id: number; analysis_id: number; user_id: number | null; helpful: boolean; incorrect: boolean; comment: string | null; created_at: string }[] }
}

// Threat Intelligence
export async function lookupThreatIntel(indicator: string, type?: string) {
  const { data } = await apiClient.get(`/threat-intelligence/${encodeURIComponent(indicator)}`, {
    params: type ? { type } : undefined,
  })
  return data
}

export async function listThreatIntelIndicators(page = 1, limit = 20) {
  const { data } = await apiClient.get('/threat-intelligence/', { params: { page, limit } })
  return data
}

export async function getThreatDashboard() {
  const { data } = await apiClient.get('/threat/dashboard')
  return data
}

export async function searchThreats(q: string, limit = 20) {
  const { data } = await apiClient.get('/threat/search', { params: { q, limit } })
  return data
}

export async function enrichThreatIOC(indicator: string, type?: string) {
  const { data } = await apiClient.post('/threat/enrich', { indicator, type })
  return data
}

export async function getThreatIOC(value: string) {
  const { data } = await apiClient.get(`/threat/ioc/${encodeURIComponent(value)}`)
  return data
}

export async function listThreatIOCs(type?: string, malicious?: boolean, limit = 50) {
  const { data } = await apiClient.get('/threat/iocs', { params: { type, malicious, limit } })
  return data
}

export async function listThreatMalware(limit = 50) {
  const { data } = await apiClient.get('/threat/malware', { params: { limit } })
  return data
}

export async function getThreatMalware(id: number) {
  const { data } = await apiClient.get(`/threat/malware/${id}`)
  return data
}

export async function listThreatActors(limit = 50) {
  const { data } = await apiClient.get('/threat/actors', { params: { limit } })
  return data
}

export async function getThreatActor(id: number) {
  const { data } = await apiClient.get(`/threat/actors/${id}`)
  return data
}

export async function listThreatCampaigns(limit = 50) {
  const { data } = await apiClient.get('/threat/campaigns', { params: { limit } })
  return data
}

export async function getThreatCampaign(id: number) {
  const { data } = await apiClient.get(`/threat/campaigns/${id}`)
  return data
}

export async function listThreatVulnerabilities(limit = 50) {
  const { data } = await apiClient.get('/threat/vulnerabilities', { params: { limit } })
  return data
}

export async function getThreatVulnerability(cve: string) {
  const { data } = await apiClient.get(`/threat/vulnerabilities/${encodeURIComponent(cve)}`)
  return data
}

export async function getThreatGraph(limit = 200) {
  const { data } = await apiClient.get('/threat/graph', { params: { limit } })
  return data
}

export async function getThreatMap() {
  const { data } = await apiClient.get('/threat/map')
  return data
}

// Risk Center
export async function getAssetRisk(assetId: number) {
  const { data } = await apiClient.get(`/risk/asset/${assetId}`)
  return data
}

export async function getAlertRisk(alertId: number) {
  const { data } = await apiClient.get(`/risk/alert/${alertId}`)
  return data
}

export async function getIncidentRisk(incidentId: number) {
  const { data } = await apiClient.get(`/risk/incident/${incidentId}`)
  return data
}

export async function getTopRiskyAssets(limit = 10) {
  const { data } = await apiClient.get('/risk/top-assets', { params: { limit } })
  return data
}

// Incident Reports
export async function generateIncidentReport(incidentId: number) {
  const { data } = await apiClient.post(`/incidents/${incidentId}/generate-report`)
  return data
}

export async function listReports(page = 1, limit = 20) {
  const { data } = await apiClient.get('/reports', { params: { page, limit } })
  return data as { data: import('@/types').Report[]; meta: { page: number; limit: number; total: number } }
}

export async function deleteReport(reportId: number) {
  await apiClient.delete(`/reports/${reportId}`)
}

// Incidents
export async function listIncidents() {
  const { data } = await apiClient.get('/incidents')
  return data as { data: import('@/types').Incident[] }
}

export async function createIncident(payload: Partial<import('@/types').Incident> & { alert_ids?: number[] }) {
  const { data } = await apiClient.post('/incidents', payload)
  return data as import('@/types').Incident
}

export async function updateIncident(id: number, payload: Partial<import('@/types').Incident>) {
  const { data } = await apiClient.patch(`/incidents/${id}`, payload)
  return data as import('@/types').Incident
}

export async function assignIncident(id: number, userId: number) {
  const { data } = await apiClient.post(`/incidents/${id}/assign`, null, { params: { user_id: userId } })
  return data as import('@/types').Incident
}

export async function addIncidentTimelineNote(id: number, note: string) {
  const { data } = await apiClient.post(`/incidents/${id}/timeline`, { note })
  return data as import('@/types').Incident
}

// Assets
export async function listAssets() {
  const { data } = await apiClient.get('/assets')
  return data as { data: import('@/types').Asset[] }
}

export async function getAssetDetails(assetId: number) {
  const { data } = await apiClient.get(`/assets/${assetId}/details`)
  return data as { asset: import('@/types').Asset; vulnerabilities: import('@/types').AssetVulnerability[]; alerts: import('@/types').Alert[] }
}

export async function calculateAssetRisk(assetId: number) {
  const { data } = await apiClient.post(`/assets/${assetId}/calculate-risk`)
  return data as { asset_id: number; risk_score: number }
}

// MITRE
export async function getMitreMatrix() {
  const { data } = await apiClient.get('/mitre/matrix')
  return data as { tactics: string[]; matrix: Record<string, import('@/types').MitreTechnique[]>; total_techniques: number; detected_techniques: number }
}

// SOAR
export async function listPlaybooks() {
  const { data } = await apiClient.get('/soar/playbooks')
  return data as { data: import('@/types').Playbook[]; meta: { total: number } }
}

export async function createPlaybook(payload: Partial<import('@/types').Playbook>) {
  const { data } = await apiClient.post('/soar/playbooks', payload)
  return data as import('@/types').Playbook
}

export async function updatePlaybook(id: number, payload: Partial<import('@/types').Playbook>) {
  const { data } = await apiClient.patch(`/soar/playbooks/${id}`, payload)
  return data as import('@/types').Playbook
}

export async function deletePlaybook(id: number) {
  await apiClient.delete(`/soar/playbooks/${id}`)
}

export async function listPlaybookActionTypes() {
  const { data } = await apiClient.get('/soar/playbooks/action-types')
  return data as string[]
}

export async function exportPlaybook(id: number) {
  const { data } = await apiClient.get(`/soar/playbooks/${id}/export`)
  return data as { format_version: string; exported_at: string; playbook: import('@/types').Playbook }
}

export async function importPlaybook(payload: Record<string, unknown>) {
  const { data } = await apiClient.post('/soar/playbooks/import', payload)
  return data as import('@/types').Playbook
}

export async function runPlaybook(id: number, inputData?: Record<string, unknown>, triggerEvent?: string) {
  const { data } = await apiClient.post(`/soar/playbooks/${id}/run`, { input_data: inputData || {}, trigger_event: triggerEvent })
  return data as import('@/types').PlaybookExecution
}

export async function listExecutions(playbookId?: number) {
  const { data } = await apiClient.get('/soar/executions', { params: playbookId ? { playbook_id: playbookId } : undefined })
  return data as { data: import('@/types').PlaybookExecution[] }
}

export async function getExecution(id: number) {
  const { data } = await apiClient.get(`/soar/executions/${id}`)
  return data as import('@/types').PlaybookExecution
}

export async function getExecutionTimeline(id: number) {
  const { data } = await apiClient.get(`/soar/executions/${id}/timeline`)
  return data as import('@/types').WorkflowTimelineEvent[]
}

export async function getExecutionEvidence(id: number) {
  const { data } = await apiClient.get(`/soar/executions/${id}/evidence`)
  return data as import('@/types').WorkflowEvidence[]
}

export async function getExecutionLogs(id: number) {
  const { data } = await apiClient.get(`/soar/executions/${id}/logs`)
  return data as import('@/types').WorkflowActionLog[]
}

export async function listApprovals(status?: string) {
  const { data } = await apiClient.get('/soar/approvals', { params: status ? { status } : undefined })
  return data as import('@/types').WorkflowApproval[]
}

export async function decideApproval(id: number, decision: 'approved' | 'denied') {
  const { data } = await apiClient.post(`/soar/approvals/${id}/decision`, { decision })
  return data as import('@/types').WorkflowApproval
}

export async function getSOARStatistics() {
  const { data } = await apiClient.get('/soar/statistics')
  return data as import('@/types').SOARStatistics
}

// Alerts
export async function updateAlertStatus(alertId: number, status: string) {
  const { data } = await apiClient.patch(`/alerts/${alertId}/status`, { status })
  return data as import('@/types').Alert
}

export async function syncAlerts(size = 50) {
  const { data } = await apiClient.post('/alerts/sync', null, { params: { size } })
  return data as { created: number; skipped: number; total_processed: number }
}

// Wazuh
export async function getWazuhVulnerabilities(params?: { agent_id?: string; page?: number; limit?: number }) {
  const { data } = await apiClient.get('/wazuh/vulnerabilities', { params })
  return data as { data: { id?: string; cve?: string; cvss3_score?: number; severity?: string; package_name?: string; architecture?: string; version?: string; condition?: string; title?: string }[] }
}

// Detection Validation Center
export interface DetectionValidationEntry {
  rule_id: string
  detection_name: string
  mitre_technique: string | null
  severity: number
  alert_count: number
  last_trigger: string | null
  status: string
  validation_status: 'validated' | 'pending' | 'stale' | 'failed' | 'no_data'
  coverage_percentage: number
  false_positive_rate: number | null
  false_positive_sample_size: number
  detection_confidence: number
  groups: string[]
}

export interface ValidationSummary {
  total_detections: number
  validated: number
  pending: number
  no_data: number
  avg_false_positive_rate: number | null
  avg_confidence: number
  total_alerts_observed: number
  data_source: string
  generated_at: string
}

export async function getValidationCenter(group = 'goldendome') {
  const { data } = await apiClient.get('/validation/detections', { params: { group } })
  return data as { summary: ValidationSummary; detections: DetectionValidationEntry[] }
}

export interface AttackCoverageTechnique {
  technique_id: string
  name: string
  tactic: string
  state: 'validated' | 'implemented' | 'failed' | 'missing_detection'
  mapped_rule_count: number
  mapped_rule_ids: string[]
  last_tested: string | null
  coverage_percentage: number
}

export interface AttackCoverageResponse {
  techniques: AttackCoverageTechnique[]
  tactic_summary: Record<string, { total: number; validated: number; implemented: number; failed: number; missing_detection: number }>
  total_techniques: number
  validated_techniques: number
  overall_coverage_percentage: number
  data_source: string
  generated_at: string
}

export async function getAttackCoverage(group = 'goldendome') {
  const { data } = await apiClient.get('/validation/coverage', { params: { group } })
  return data as AttackCoverageResponse
}

// Detection Rules
export async function listDetectionRules(params?: { page?: number; limit?: number; category?: string; status?: string; search?: string }) {
  const { data } = await apiClient.get('/detection-rules', { params })
  return data as { data: import('@/types').DetectionRule[]; meta: { page: number; limit: number; total: number } }
}

export async function createDetectionRule(payload: Partial<import('@/types').DetectionRule>) {
  const { data } = await apiClient.post('/detection-rules', payload)
  return data as import('@/types').DetectionRule
}

export async function updateDetectionRule(id: number, payload: Partial<import('@/types').DetectionRule>) {
  const { data } = await apiClient.patch(`/detection-rules/${id}`, payload)
  return data as import('@/types').DetectionRule
}

export async function deleteDetectionRule(id: number) {
  await apiClient.delete(`/detection-rules/${id}`)
}

export async function testDetectionRule(id: number, event: Record<string, unknown>) {
  const { data } = await apiClient.post(`/detection-rules/${id}/test`, { event })
  return data as import('@/types').DetectionRuleTestResult
}

export async function toggleDetectionRule(id: number) {
  const { data } = await apiClient.patch(`/detection-rules/${id}/toggle`)
  return data as import('@/types').DetectionRule
}

export async function getDetectionCoverage() {
  const { data } = await apiClient.get('/detection-rules/coverage/summary')
  return data as { total_techniques: number; detected_techniques: number; coverage_percentage: number; tactic_coverage: Record<string, number> }
}

// Alert enrichment
export async function enrichAlert(alertId: number, createIncident = false) {
  const { data } = await apiClient.post(`/alerts/${alertId}/enrich`, null, { params: { create_incident: createIncident } })
  return data as { mitre?: unknown; threat_intelligence: unknown[]; ai_analysis: unknown; incident?: { id: number; name: string } }
}

export async function getSigmaExport(ruleId: number) {
  const { data } = await apiClient.get(`/detection-rules/${ruleId}/sigma`)
  return data as { rule_id: number; sigma_yaml: string }
}

export async function evaluateDetectionScenarios(ruleId: number, scenarios: { name: string; event: Record<string, unknown>; expected_match: boolean }[]) {
  const { data } = await apiClient.post(`/detection-rules/${ruleId}/evaluate-scenarios`, { scenarios })
  return data as { total_scenarios: number; true_positives: number; false_positives: number; false_negatives: number; precision: number; recall: number; recommendation: string; results: { name: string; expected: boolean; actual: boolean; matched: { matched: boolean; reason: string } }[] }
}
