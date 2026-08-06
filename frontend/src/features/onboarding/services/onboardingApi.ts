import axios from 'axios'
import type { DeploymentWizardPayload, DeploymentWizardResult, OnboardingStatus, SystemInfoSnapshot } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function getOnboardingStatus(): Promise<OnboardingStatus> {
  const { data } = await client.get('/onboarding/status')
  return data
}

export async function getSystemInfo(): Promise<SystemInfoSnapshot> {
  const { data } = await client.get('/system/info')
  return data
}

export async function submitOnboarding(payload: DeploymentWizardPayload): Promise<DeploymentWizardResult> {
  const { data } = await client.post('/onboarding', payload)
  return data
}

export async function resetOnboarding(): Promise<{ reset: boolean }> {
  const { data } = await client.post('/onboarding/reset')
  return data
}
