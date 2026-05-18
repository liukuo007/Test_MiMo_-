import request from './request'

export interface LoopRule {
  id: number
  name: string
  trigger_metric: string
  threshold: number
  operator: string
  action_chain: Record<string, any> | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface LoopExecution {
  id: number
  rule_id: number
  rule_name: string | null
  trigger_value: number
  current_step: number
  total_steps: number
  status: string
  steps_log: { steps: { step: number; action: string; status: string; detail: string }[] } | null
  defect_id: number | null
  started_at: string
  completed_at: string | null
}

export function getLoopRules() {
  return request.get('/quality-loop/rules') as Promise<LoopRule[]>
}

export function createLoopRule(data: Partial<LoopRule>) {
  return request.post('/quality-loop/rules', data) as Promise<LoopRule>
}

export function updateLoopRule(id: number, data: Partial<LoopRule>) {
  return request.put(`/quality-loop/rules/${id}`, data) as Promise<LoopRule>
}

export function deleteLoopRule(id: number) {
  return request.delete(`/quality-loop/rules/${id}`) as Promise<{ ok: boolean }>
}

export function triggerRule(id: number) {
  return request.post(`/quality-loop/rules/${id}/trigger`) as Promise<LoopExecution>
}

export function getLoopExecutions(params?: { rule_id?: number; status?: string }) {
  return request.get('/quality-loop/executions', { params }) as Promise<LoopExecution[]>
}

export function evaluateRules() {
  return request.post('/quality-loop/evaluate') as Promise<{ triggered: number }>
}
