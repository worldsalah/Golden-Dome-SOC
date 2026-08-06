export interface ServerMetrics {
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

export interface ContainerMetric {
  id: string
  name: string
  status: string
  raw_status: string | null
  image: string | null
  uptime: string | null
  cpu: string
  memory: string
}

export type ServiceState = 'online' | 'offline' | 'warning' | 'unknown'

export type ServiceHealthMap = Record<string, ServiceState>

export interface HistoryPoint {
  timestamp: number
  value: number
}

export interface HistoryResponse {
  metric: string
  range: string
  points: HistoryPoint[]
  available: boolean
}
