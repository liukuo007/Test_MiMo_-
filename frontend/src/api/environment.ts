import request from './request'

export interface EnvironmentItem {
  id: number
  name: string
  env_type: string
  region: string | null
  base_url: string | null
  mqtt_broker_url: string | null
  db_url: string | null
  redis_url: string | null
  ai_evaluator_url: string | null
  wiremock_url: string | null
  payment_endpoint: string | null
  status: string
  config: Record<string, any> | null
  description: string | null
  created_at: string
  updated_at: string
}

export interface HealthCheckItem {
  id: number
  env_id: number
  component: string
  status: string
  latency_ms: number | null
  details: Record<string, any> | null
  checked_at: string
}

export interface SnapshotItem {
  id: number
  env_id: number
  name: string
  snapshot_type: string
  state_data: Record<string, any> | null
  notes: string | null
  created_at: string
}

export function getEnvironments(params?: { env_type?: string; status?: string }) {
  return request.get('/environments', { params }) as Promise<EnvironmentItem[]>
}

export function getEnvironment(id: number) {
  return request.get(`/environments/${id}`) as Promise<EnvironmentItem>
}

export function createEnvironment(data: Partial<EnvironmentItem>) {
  return request.post('/environments', data) as Promise<EnvironmentItem>
}

export function updateEnvironment(id: number, data: Partial<EnvironmentItem>) {
  return request.put(`/environments/${id}`, data) as Promise<EnvironmentItem>
}

export function deleteEnvironment(id: number) {
  return request.delete(`/environments/${id}`) as Promise<{ ok: boolean }>
}

export function checkEnvironmentHealth(id: number) {
  return request.post(`/environments/${id}/health-check`) as Promise<HealthCheckItem[]>
}

export function createSnapshot(envId: number, data: { name: string; snapshot_type?: string; notes?: string }) {
  return request.post(`/environments/${envId}/snapshots`, data) as Promise<SnapshotItem>
}

export function getSnapshots(envId: number) {
  return request.get(`/environments/${envId}/snapshots`) as Promise<SnapshotItem[]>
}

export function restoreSnapshot(snapshotId: number) {
  return request.post(`/environments/snapshots/${snapshotId}/restore`) as Promise<EnvironmentItem>
}
