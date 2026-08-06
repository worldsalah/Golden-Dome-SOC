export interface OsInfo {
  distribution: string
  version: string
  architecture: string
  kernel: string
  platform: string
}

export interface HostInfo {
  hostname: string
  fqdn: string
  domain: string | null
  local_ip: string | null
  public_ip: string | null
}

export interface HardwareInfo {
  cpu_model: string
  physical_cores: number
  logical_cores: number
  ram_total: string
  ram_available: string
  ram_total_bytes: number
  disk_total: string
  disk_free: string
  disk_total_bytes: number
}

export interface DockerInfo {
  installed: boolean
  running: boolean
  version: string | null
  compose_version: string | null
}

export interface ContainerInfo {
  name: string
  status: string
  image: string
  ports: string
  uptime: string
}

export interface NetworkInterface {
  name: string
  addresses: string[]
}

export interface NetworkInfo {
  interfaces: NetworkInterface[]
  gateway: string | null
}

export type ServiceStatus = 'online' | 'offline' | 'warning' | 'unknown'

export interface PlatformService {
  name: string
  status: ServiceStatus
}

export interface SystemInfoSnapshot {
  operating_system: OsInfo
  host: HostInfo
  hardware: HardwareInfo
  docker: DockerInfo
  containers: ContainerInfo[]
  network: NetworkInfo
  services: PlatformService[]
}

export interface OnboardingStatus {
  completed: boolean
  needs_setup: boolean
  users_count: number
  organizations_count: number
}

export interface DeploymentWizardPayload {
  installation_name: string
  administrator_name: string
  administrator_email: string
  administrator_password: string
  company_name?: string
}

export interface DeploymentWizardResult {
  id: number
  installation_name: string
  completed: boolean
  deployment_date: string
}
