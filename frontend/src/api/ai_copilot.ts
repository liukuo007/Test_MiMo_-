import request from './request'

export interface FailureAnalysis {
  test_result_id: number
  root_cause: string
  category: string
  confidence: number
  related_events: Record<string, any>[]
  related_traces: Record<string, any>[]
  suggestion: string
}

export interface GeneratedTest {
  description: string
  steps: { id: number; action: string; description: string; params: Record<string, any> }[]
  estimated_duration_ms: number
  suggested_devices: string[]
}

export interface SelectorFix {
  original_selector: string
  selector_type: string
  suggested_fixes: { selector: string; reason: string }[]
  confidence: number
}

export interface GeneratedScenario {
  name: string
  description: string
  steps: { id: number; action: string; description: string; params: Record<string, any> }[]
  source: string
}

export function analyzeFailure(testResultId: number) {
  return request.post('/ai-copilot/analyze-failure', { test_result_id: testResultId }) as Promise<FailureAnalysis>
}

export function generateTest(description: string) {
  return request.post('/ai-copilot/generate-test', { description }) as Promise<GeneratedTest>
}

export function fixSelector(selector: string, context?: string) {
  return request.post('/ai-copilot/fix-selector', { selector, context }) as Promise<SelectorFix>
}

export function generateScenario(description: string) {
  return request.post('/ai-copilot/generate-scenario', { description }) as Promise<GeneratedScenario>
}
