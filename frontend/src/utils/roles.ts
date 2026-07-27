import { UserRole } from '@/types'

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: 'Administrator',
  soc_analyst: 'SOC Analyst',
  security_engineer: 'Security Engineer',
  viewer: 'Viewer',
}

export const ROLE_HIERARCHY: Record<UserRole, number> = {
  viewer: 1,
  soc_analyst: 2,
  security_engineer: 2,
  admin: 3,
}

export function canAccess(userRole: UserRole, requiredRole: UserRole): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole]
}
