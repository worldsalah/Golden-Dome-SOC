export type UserRole = 'admin' | 'soc_analyst' | 'security_engineer' | 'viewer'

export interface User {
  id: number
  username: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface PaginatedResponse<T> {
  data: T[]
  meta: {
    page: number
    limit: number
    total: number
  }
}

export interface Alert {
  id: number
  wazuh_alert_id: string
  title: string
  description?: string
  severity: number
  source_ip?: string
  destination_ip?: string
  rule_id?: string
  mitre_technique?: string
  status: 'new' | 'acknowledged' | 'investigating' | 'resolved' | 'false_positive'
  assigned_user_id?: number
  asset_id?: number
  raw_log?: string
  created_at: string
}

export interface IncidentTimelineEvent {
  id: number
  action: string
  note?: string
  actor_id?: number
  timestamp: string
}

export interface Incident {
  id: number
  name: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'open' | 'in_progress' | 'resolved' | 'closed'
  assigned_user_id?: number
  description?: string
  created_at: string
  resolved_at?: string
  timeline?: IncidentTimelineEvent[]
  alerts?: Alert[]
}

export interface Asset {
  id: number
  hostname: string
  ip_address?: string
  type: string
  operating_system?: string
  criticality: number
  risk_score: number
  last_seen?: string
  wazuh_agent_id?: string
  created_at: string
}

export interface AssetVulnerability {
  id: number
  cve: string
  severity: string
  cvss_score?: number | null
  description?: string
  detected_at: string
}

export interface MitreTechnique {
  technique_id: string
  name: string
  tactic: string
  alert_count: number
  detection_status: 'detected' | 'partial' | 'planned' | 'not_applicable' | string
  description?: string
  associated_rules?: string
}

export interface DetectionRule {
  id: number
  name: string
  description?: string
  severity: number
  category: string
  source: string
  logic: string
  mitre_attack_id?: string
  status: 'active' | 'disabled' | 'draft' | 'archived'
  created_by?: number
  created_at: string
  updated_at: string
}

export interface DetectionRuleTestResult {
  matched: boolean
  reason?: string
  extracted_fields: Record<string, unknown>
}

export interface Report {
  id: number
  title: string
  content?: string
  report_type: string
  created_by_id?: number
  file_path?: string
  created_at: string
}

export interface AiAnalysis {
  analysis_id?: number
  executive_summary: string
  technical_explanation: Record<string, unknown>
  mitre_mapping: { tactic: string; technique: string; technique_id: string }
  risk_assessment: { severity: string; confidence: number; business_impact: string; priority: string }
  risk_score: number
  risk_classification: string
  investigation_steps: string[]
  recommended_response: { immediate: string[]; short_term: string[]; long_term: string[] }
  analyst_notes: string
  llm_source: string
}

export interface ThreatIntelIndicator {
  indicator: string
  type: string
  sources: { name: string;[key: string]: unknown }[]
  reputation_score: number
  confidence: number
  country?: string | null
  asn?: string | null
  threat_category?: string | null
  malware?: string | null
  first_seen?: string | null
  last_seen?: string | null
}

export interface IocRecord {
  id: number
  value: string
  type: string
  category?: string
  confidence: number
  first_seen?: string
  last_seen?: string
  sources?: string
}

export interface RiskScore {
  target_type: string
  target_id: number
  score: number
  classification: string
  reason: Record<string, unknown>
}

export interface IncidentReport {
  report: Record<string, unknown>
  llm_source: string
  generated_at: string
  markdown: string
  pdf_base64?: string
}

export interface PlaybookAction {
  action: string
  params: Record<string, unknown>
}

export interface PlaybookNode {
  id: string
  type: string
  name: string
  config: Record<string, unknown>
  next_nodes: string[]
  condition?: string
}

export interface Playbook {
  id: number
  name: string
  description?: string
  trigger: string
  trigger_config?: Record<string, unknown>
  status: 'active' | 'disabled'
  category: string
  version: string
  tags?: string
  is_builtin: boolean
  actions: PlaybookAction[]
  nodes: PlaybookNode[]
  created_by?: number
  created_at: string
  updated_at: string
}

export interface PlaybookExecution {
  id: number
  playbook_id: number
  status: string
  triggered_by?: string
  trigger_event?: string
  input_data?: string
  output_log?: string
  context?: string
  current_node_id?: string
  node_states?: string
  results?: string
  logs?: string
  approval_status: string
  requires_approval: boolean
  started_at: string
  completed_at?: string
  updated_at: string
}

export interface WorkflowApproval {
  id: number
  execution_id: number
  playbook_id?: number
  node_id?: string
  action_summary?: string
  risk_level: string
  status: string
  requested_by?: string
  approved_by?: string
  approved_at?: string
  details?: string
  created_at: string
  updated_at: string
}

export interface WorkflowTimelineEvent {
  id: number
  execution_id: number
  node_id?: string
  event_type: string
  message?: string
  actor?: string
  metadata?: string
  timestamp: string
}

export interface WorkflowEvidence {
  id: number
  execution_id: number
  node_id?: string
  evidence_type: string
  source?: string
  content?: string
  file_path?: string
  created_at: string
}

export interface WorkflowActionLog {
  id: number
  execution_id: number
  node_id?: string
  action_type: string
  status: string
  input_data?: string
  output_data?: string
  duration_ms?: number
  created_at: string
}

export interface SOARStatistics {
  total_playbooks: number
  active_playbooks: number
  total_executions: number
  completed_executions: number
  failed_executions: number
  pending_approvals: number
  avg_execution_time_ms: number
  execution_status_counts: Record<string, number>
  most_executed_playbooks: { playbook_id: number; name: string; count: number }[]
}
