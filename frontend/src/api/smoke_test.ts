import request from './request'

export interface SmokeStepResult {
  step: number
  name: string
  status: 'passed' | 'failed' | 'running' | 'pending'
  duration_ms: number
  detail: string
  error: string | null
}

export interface SmokeTestResponse {
  status: 'passed' | 'failed'
  total_duration_ms: number
  steps: SmokeStepResult[]
}

export function runSmokeTest() {
  return request.post('/smoke-test/run') as Promise<SmokeTestResponse>
}
