import request from './request'

export interface ScenarioTemplate {
  id: number
  name: string
  description: string
  category: string
  icon: string
  color: string
  steps_definition: { steps: Array<{ name: string; event_type: string; message_tpl?: string; message?: string }> }
  params_schema: {
    fields: Array<{
      key: string
      label: string
      type: 'select' | 'number' | 'text'
      options?: string
      default?: any
      min?: number
      max?: number
    }>
  } | null
  wiremock_mapping: Record<string, any> | null
  sort_order: number
  is_active: boolean
  created_at: string
}

export interface ScenarioRunRequest {
  device_sns?: string[]
  device_type?: string
  product_key?: string
  quantity?: number
  payment_method?: string
  timeout_seconds?: number
}

export interface StepResult {
  step: number
  name: string
  status: 'passed' | 'failed'
  duration_ms: number
  detail: string
  error: string | null
}

export interface ScenarioRunResponse {
  execution_id: number
  batch_id: number | null
  template_id: number
  template_name: string
  device_sn: string
  device_name: string | null
  is_real_device: boolean
  run_params: Record<string, any> | null
  status: 'passed' | 'failed'
  total_duration_ms: number
  steps: StepResult[]
}

export interface BatchRunResponse {
  batch_id: number
  template_id: number
  template_name: string
  total_count: number
  status: string
  executions: ScenarioRunResponse[]
}

export interface ScenarioExecution {
  id: number
  batch_id: number | null
  template_id: number
  template_name: string
  device_sn: string
  device_name: string | null
  is_real_device: boolean
  run_params: Record<string, any> | null
  status: string
  steps_result: StepResult[] | null
  total_duration_ms: number | null
  error_message: string | null
  triggered_by_name: string | null
  created_at: string
  finished_at: string | null
}

export interface BatchRecord {
  id: number
  template_id: number
  template_name: string | null
  name: string
  total_count: number
  passed_count: number
  failed_count: number
  status: string
  run_params: Record<string, any> | null
  triggered_by_name: string | null
  created_at: string
  finished_at: string | null
}

export interface CatalogData {
  products: Array<{ key: string; name: string; sku: string; price: number }>
  device_types: Array<{ value: string; label: string; desc: string }>
  payment_methods: Array<{ value: string; label: string }>
}

export interface DevicePickItem {
  id: number
  device_sn: string
  name: string
  device_type: string
  status: string
  region: string | null
  temperature: number | null
  last_heartbeat: string | null
  firmware_version: string | null
}

export function getScenarioTemplates() {
  return request.get('/scenarios/templates') as Promise<ScenarioTemplate[]>
}

export function getScenarioCatalog() {
  return request.get('/scenarios/catalog') as Promise<CatalogData>
}

export function getScenarioDevices(params?: {
  search?: string
  status?: string
  device_type?: string
  region?: string
  limit?: number
}) {
  return request.get('/scenarios/devices', { params }) as Promise<DevicePickItem[]>
}

export function runScenario(templateId: number, params?: ScenarioRunRequest) {
  return request.post(`/scenarios/templates/${templateId}/run`, params || {}) as Promise<ScenarioRunResponse>
}

export function batchRunScenario(templateId: number, params: ScenarioRunRequest) {
  return request.post(`/scenarios/templates/${templateId}/batch-run`, params) as Promise<BatchRunResponse>
}

export function getScenarioExecutions(params?: {
  template_id?: number
  batch_id?: number
  skip?: number
  limit?: number
}) {
  return request.get('/scenarios/executions', { params }) as Promise<{ items: ScenarioExecution[]; total: number }>
}

export function getScenarioBatches(params?: {
  template_id?: number
  skip?: number
  limit?: number
}) {
  return request.get('/scenarios/batches', { params }) as Promise<{ items: BatchRecord[]; total: number }>
}

export function createScenarioTemplate(data: Partial<ScenarioTemplate>) {
  return request.post('/scenarios/templates', data) as Promise<ScenarioTemplate>
}

export function updateScenarioTemplate(id: number, data: Partial<ScenarioTemplate>) {
  return request.put(`/scenarios/templates/${id}`, data) as Promise<ScenarioTemplate>
}

export function deleteScenarioTemplate(id: number) {
  return request.delete(`/scenarios/templates/${id}`) as Promise<{ detail: string }>
}
