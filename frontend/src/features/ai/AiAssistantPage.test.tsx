import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AiAssistantPage } from './AiAssistantPage'

vi.mock('@/services/api', () => ({
  analyzeAlert: vi.fn(),
  askSentinel: vi.fn(),
  generateAIDailyReport: vi.fn(),
  generateAIPlaybook: vi.fn(),
  getAIAuditLogs: vi.fn(),
  getAIAnomalies: vi.fn(),
  getAIFeedback: vi.fn(),
  getAIHealth: vi.fn().mockResolvedValue({ ollama: { status: 'ok' } }),
  getAIHistory: vi.fn(),
  investigateIncidentWithAI: vi.fn(),
  submitAIFeedback: vi.fn(),
  threatHuntWithAI: vi.fn(),
}))

describe('AiAssistantPage', () => {
  it('renders the Sentinel AI dashboard tabs', () => {
    render(<AiAssistantPage />)
    expect(screen.getByText('Sentinel AI')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /chat/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /alert analysis/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /anomalies/i })).toBeInTheDocument()
  })
})
