import request from './request'

export interface ReplayResult {
  order_id: string
  steps: { id: number; action: string; description: string; params: Record<string, any>; source_event?: string; timestamp?: string }[]
  event_count: number
  reconstructed: boolean
}

export interface GeneratedScenario {
  name: string
  description: string
  steps: { id: number; action: string; description: string; params: Record<string, any> }[]
  source: string
}

export function replayOrder(orderId: string) {
  return request.post('/scenario-ai/replay', { order_id: orderId }) as Promise<ReplayResult>
}

export function generateScenario(description: string) {
  return request.post('/scenario-ai/generate', { description }) as Promise<GeneratedScenario>
}

export function previewScenario(scenarioId: number) {
  return request.get(`/scenario-ai/preview/${scenarioId}`) as Promise<any>
}
