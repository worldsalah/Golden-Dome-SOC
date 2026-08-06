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
export interface AlertListItem {
  id: number
  wazuh_alert_id: string
  title: string
  severity: number
  status: string
  rule_id: string | null
  created_at: string
}

export interface AlertsListResponse {
  data: AlertListItem[]
  meta: { page: number; limit: number; total: number }
}

export async function getAlerts(params?: { page?: number; limit?: number; status?: string; search?: string }) {
  const { data } = await apiClient.get('/alerts', { params })
  return data as AlertsListResponse
}

export interface ReplayAlertResponse {
  alert_id: number
  original_event: Record<string, unknown>
  current_rule: Record<string, unknown> | null
  verdict: string
  match_count_24h: number
  last_trigger: string | null
  suggestions: string[]
  data_source: string
  generated_at: string
}

export async function replayAlert(alertId: number) {
  const { data } = await apiClient.post(`/validation/replay/${alertId}`)
  return data as ReplayAlertResponse
}

export async function updateAlertStatus(alertId: number, status: string) {
  const { data } = await apiClient.patch(`/alerts/${alertId}/status`, { status })
  return data as import('@/types').Alert
}

export async function syncAlerts(size = 50) {
  const { data } = await apiClient.post('/alerts/sync', null, { params: { size } })
  return data as { created: number; skipped: number; total_processed: number }
}

// Wazuh
export interface WazuhDashboardResponse {
  active_agents: number
  total_agents: number
  agents: { id?: string; name?: string; ip?: string; status?: string; os?: { name?: string } }[]
  total_alerts: number
  alerts_today: number
  alerts_last_24h: number
  severity: { critical: number; high: number; medium: number; low: number }
  top_rules: { rule_id: string; count: number }[]
  top_source_ips: { ip: string; count: number }[]
  top_mitre_techniques: { technique: string; count: number }[]
  top_os: { os: string; count: number }[]
  alerts_per_hour: { hour: string; count: number }[]
  generated_at: string
}

export async function getWazuhDashboard(hours = 24) {
  const { data } = await apiClient.get('/wazuh/dashboard', { params: { hours } })
  return data as WazuhDashboardResponse
}

export interface AttackMapEntry {
  source_ip: string
  country: string
  latitude: number | null
  longitude: number | null
  rule_description: string
  rule_level: number
  rule_id: string
  agent_name: string
  timestamp: string
  count: number
}

export interface AttackMapResponse {
  attacks: AttackMapEntry[]
  total_unique_sources: number
  has_geoip: boolean
  generated_at: string
}

export async function getAttackMap(hours = 24, size = 200) {
  const { data } = await apiClient.get('/wazuh/attack-map', { params: { hours, size } })
  return data as AttackMapResponse
}

export interface CorrelatedIncident {
  cluster_key: string
  name: string
  severity: string
  status: string
  alert_count: number
  source_ips: string[]
  affected_agents: string[]
  rule_ids: string[]
  mitre_techniques: string[]
  first_seen: string | null
  last_seen: string | null
  timeline: { timestamp: string; event: string; level: number }[]
  alerts: Record<string, unknown>[]
}

export async function getCorrelatedIncidents(hours = 24, minClusterSize = 2) {
  const { data } = await apiClient.get('/wazuh/correlate-incidents', { params: { hours, min_cluster_size: minClusterSize } })
  return data as { incidents: CorrelatedIncident[]; total: number }
}

export interface GlobalSearchResults {
  results: {
    alerts: { id: string; title: string; severity: number; timestamp: string; source_ip: string; agent: string; type: string }[]
    agents: { id: string; name: string; ip: string; status: string; type: string }[]
    vulnerabilities: { id: string; cve: string; package: string; agent: string; type: string }[]
    techniques: Record<string, unknown>[]
  }
  total: number
  query: string
}

export async function globalSearch(q: string, limit = 50) {
  const { data } = await apiClient.get('/wazuh/search', { params: { q, limit } })
  return data as GlobalSearchResults
}

export async function getLatestAlerts(size = 10) {
  const { data } = await apiClient.get('/wazuh/latest-alerts', { params: { size } })
  return data as { alerts: Record<string, unknown>[]; total: number }
}

export async function exportReportCsv(params?: { hours?: number; severity?: number; agent_id?: string; rule_id?: string; mitre_technique?: string }) {
  const { data } = await apiClient.get('/reports/export/csv', { params, responseType: 'blob' })
  const blob = new Blob([data as BlobPart], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `alerts_report_${new Date().toISOString().slice(0, 10)}.csv`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export async function exportReportExcel(params?: { hours?: number; severity?: number; agent_id?: string; rule_id?: string; mitre_technique?: string }) {
  const { data } = await apiClient.get('/reports/export/excel', { params, responseType: 'blob' })
  const blob = new Blob([data as BlobPart], { type: 'application/vnd.ms-excel' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `alerts_report_${new Date().toISOString().slice(0, 10)}.xls`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export async function exportReportPdf(params?: { hours?: number; severity?: number }) {
  const { data } = await apiClient.get('/reports/export/pdf', { params, responseType: 'blob' })
  const blob = new Blob([data as BlobPart], { type: 'application/pdf' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `alerts_report_${new Date().toISOString().slice(0, 10)}.pdf`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export async function getWazuhVulnerabilities(params?: { agent_id?: string; page?: number; limit?: number }) {
  const { data } = await apiClient.get('/wazuh/vulnerabilities', { params })
  return data as { data: { id?: string; cve?: string; cvss3_score?: number; severity?: string; package_name?: string; architecture?: string; version?: string; condition?: string; title?: string; agent_name?: string; agent_id?: string; os?: string; description?: string; classification?: string; category?: string; references?: string[] }[] }
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

export interface FalsePositiveRuleAnalysis {
  rule_id: string
  detection_name: string
  alert_count: number
  real_incidents: number
  false_positive_count: number
  false_positive_rate: number | null
  repeated_alerts: number
  confidence: number
  suggestions: string[]
}

export interface FalsePositiveAnalysisResponse {
  rules: FalsePositiveRuleAnalysis[]
  total_rules_analyzed: number
  rules_with_disposition_data: number
  avg_false_positive_rate: number | null
  data_source: string
  generated_at: string
}

export async function getFalsePositiveAnalysis(group = 'goldendome') {
  const { data } = await apiClient.get('/validation/false-positive-analysis', { params: { group } })
  return data as FalsePositiveAnalysisResponse
}

export interface DaemonHealth {
  name: string
  status: string
}

export interface DetectionPerformanceResponse {
  api_latency_ms: number
  indexer_latency_ms: number
  events_per_second: number | null
  events_dropped_per_hour: number | null
  drop_percentage: number | null
  alerts_per_hour: number | null
  alerts_written_24h: number | null
  indexer_alert_volume_24h: number | null
  daemon_health: DaemonHealth[]
  manager_stats_raw: Record<string, unknown>
  data_source: string
  generated_at: string
}

export async function getDetectionPerformance() {
  const { data } = await apiClient.get('/validation/performance')
  return data as DetectionPerformanceResponse
}

export interface RuleOptimizerEntry {
  rule_id: string
  detection_name: string
  alert_count: number
  suggestion: string
}

export interface DuplicateRuleGroup {
  key: string
  type: string
  rule_ids: string[]
  suggestion: string
}

export interface RuleOptimizerResponse {
  never_triggered: RuleOptimizerEntry[]
  rarely_triggered: RuleOptimizerEntry[]
  frequently_triggered: RuleOptimizerEntry[]
  inefficient: RuleOptimizerEntry[]
  duplicate_groups: DuplicateRuleGroup[]
  total_rules: number
  data_source: string
  generated_at: string
}

export async function getRuleOptimizer(group = 'goldendome') {
  const { data } = await apiClient.get('/validation/rule-optimizer', { params: { group } })
  return data as RuleOptimizerResponse
}

export interface SocHealthComponents {
  detection_validation: number
  attack_coverage: number
  false_positive_control: number
  backlog: number
  platform_performance: number
}

export interface SocHealthScoreResponse {
  grade: string
  overall_score: number
  components: SocHealthComponents
  open_alerts: number
  open_incidents: number
  data_source: string
  generated_at: string
}

export async function getSocHealthScore(group = 'goldendome') {
  const { data } = await apiClient.get('/validation/health-score', { params: { group } })
  return data as SocHealthScoreResponse
}

export interface EvidenceEntry {
  id: number
  source: string
  type: string
  title: string
  timestamp: string | null
  snippet: string
  rule_id: string | null
  severity: number | null
  file_path: string | null
  raw: string | null
}

export interface EvidenceSearchResponse {
  evidence: EvidenceEntry[]
  query: string | null
  source: string | null
  total: number
  data_source: string
  generated_at: string
}

export async function searchEvidence(params?: { q?: string; source?: string; limit?: number }) {
  const { data } = await apiClient.get('/validation/evidence', { params })
  return data as EvidenceSearchResponse
}

export async function downloadValidationReport(group = 'goldendome') {
  const { data } = await apiClient.get('/validation/reports/pdf', { params: { group }, responseType: 'blob' })
  const blob = new Blob([data as BlobPart], { type: 'application/pdf' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `validation_report_${new Date().toISOString().slice(0, 10)}.pdf`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
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

// ─── Sprint 7 APIs ────────────────────────────────────────────────

// MFA
export async function enrollMFA() {
  const { data } = await apiClient.post('/auth/mfa/enroll')
  return data as { secret: string; qr_uri: string; backup_codes: string[] }
}

export async function verifyMFA(code: string) {
  const { data } = await apiClient.post('/auth/mfa/verify', { code })
  return data as { verified: boolean; message: string }
}

export async function disableMFA(code: string) {
  const { data } = await apiClient.post('/auth/mfa/disable', { code })
  return data as { verified: boolean; message: string }
}

// Security & API Keys
export async function getSecurityHeaders() {
  const { data } = await apiClient.get('/security/headers')
  return data as { headers: Record<string, string>; cors: Record<string, unknown>; rate_limiting: Record<string, string> }
}

export async function createApiKey(payload: { name: string; scopes: string[] }) {
  const { data } = await apiClient.post('/security/api-keys', payload)
  return data as { key: string; key_prefix: string; name: string; scopes: string[]; message: string }
}

export async function listApiKeys() {
  const { data } = await apiClient.get('/security/api-keys')
  return data as { id: number; key_prefix: string; name: string; scopes: string[]; is_active: boolean; created_at: string | null }[]
}

export async function revokeApiKey(keyPrefix: string) {
  await apiClient.delete(`/security/api-keys/${keyPrefix}`)
}

export async function getSecurityAuditSummary() {
  const { data } = await apiClient.get('/security/audit-summary')
  return data as { event_counts: Record<string, number>; failed_logins: number; active_api_keys: number }
}

// Deployment
export async function getDeploymentInfo() {
  const { data } = await apiClient.get('/deployment/info')
  return data as { app_name: string; version: string; debug: boolean; database: Record<string, string>; redis: Record<string, string>; ollama: Record<string, string>; deployment_type: string; timestamp: string }
}

export async function getDeploymentHealth() {
  const { data } = await apiClient.get('/deployment/health-summary')
  return data as { status: string; checks: Record<string, unknown>; timestamp: string }
}

export async function createBackup() {
  const { data } = await apiClient.post('/deployment/backup')
  return data as { status: string; backup_id: string; metadata: Record<string, unknown>; instructions: string }
}

// Posture
export async function getPosture() {
  const { data } = await apiClient.get('/posture')
  return data as Record<string, unknown>
}

// Hotel
export async function getHotelDashboard() {
  const { data } = await apiClient.get('/hotel/dashboard')
  return data as Record<string, unknown>
}

// Connectors
export async function listConnectors() {
  const { data } = await apiClient.get('/connectors')
  return data as { data: Record<string, unknown>[] }
}

export async function listConnectorTypes() {
  const { data } = await apiClient.get('/connectors/catalog')
  return data as { type: string; category: string; display_name: string; description: string; icon: string | null; config_schema: Record<string, unknown>; supported_actions: string[] }[]
}

export async function testConnector(id: number) {
  const { data } = await apiClient.post(`/connectors/${id}/test`)
  return data as { healthy: boolean; status: string; [key: string]: unknown }
}

// Monitoring
export async function getServerMetrics() {
  const { data } = await apiClient.get('/monitoring/server')
  return data as {
    cpu_usage: number | null
    memory_usage: number | null
    disk_usage: number | null
    network_in: string | null
    network_out: string | null
    uptime: string | null
    cores: number
    ram_total: string
    disk_total: string
    source: string
  }
}

export async function getContainerMetrics() {
  const { data } = await apiClient.get('/monitoring/containers')
  return data as { id: string; name: string; status: string; raw_status: string | null; image: string | null; uptime: string | null; cpu: string; memory: string }[]
}

export async function getMonitoringServiceHealth() {
  const { data } = await apiClient.get('/monitoring/services')
  return data as Record<string, 'online' | 'offline' | 'warning' | 'unknown'>
}

export async function getMetricsHistory(metric: 'cpu' | 'memory' | 'network', range: '1h' | '24h' | '7d') {
  const { data } = await apiClient.get('/monitoring/history', { params: { metric, range } })
  return data as { metric: string; range: string; points: { timestamp: number; value: number }[]; available: boolean }
}

// Onboarding
export async function getOnboardingSteps() {
  const { data } = await apiClient.get('/onboarding/wizard/steps')
  return data as { steps: { id: number; title: string; description: string; fields: string[]; available_connectors?: unknown[] }[] }
}

export async function runOnboardingWizard(payload: Record<string, unknown>) {
  const { data } = await apiClient.post('/onboarding/wizard', payload)
  return data as { organization_id: number; admin_user_id: number; connectors_created: number; assets_created: number; next_steps: string[] }
}

// Organizations
export async function listOrganizations() {
  const { data } = await apiClient.get('/organizations')
  return data as { data: Record<string, unknown>[] }
}

// Audit
export async function listAuditLogs(params?: { page?: number; limit?: number; action?: string }) {
  const { data } = await apiClient.get('/audit/logs', { params })
  return data as { data: Record<string, unknown>[]; meta: { page: number; limit: number; total: number } }
}

// AI Attack Chain & Detection Review
export async function analyzeAttackChain(alertIds: number[]) {
  const { data } = await apiClient.post('/ai/attack-chain', { alert_ids: alertIds })
  return data as Record<string, unknown>
}

export async function reviewDetection(ruleId?: number) {
  const { data } = await apiClient.post('/ai/detection-review', { rule_id: ruleId })
  return data as Record<string, unknown>
}
