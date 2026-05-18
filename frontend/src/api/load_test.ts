import request from './request'

export interface TrafficProfile {
  id: number
  name: string
  pattern: Record<string, any> | null
  duration_seconds: number
  description: string | null
  created_at: string
}

export interface LoadTestRun {
  id: number
  profile_id: number | null
  profile_name: string | null
  device_count: number
  virtual_device_count: number
  status: string
  total_requests: number
  error_count: number
  avg_latency_ms: number
  p99_latency_ms: number
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface LoadTestMetric {
  id: number
  run_id: number
  timestamp: string
  rps: number
  avg_latency_ms: number
  p99_latency_ms: number
  error_rate: number
  active_users: number
}

export function getProfiles() {
  return request.get('/load-test/profiles') as Promise<TrafficProfile[]>
}

export function createProfile(data: Partial<TrafficProfile>) {
  return request.post('/load-test/profiles', data) as Promise<TrafficProfile>
}

export function deleteProfile(id: number) {
  return request.delete(`/load-test/profiles/${id}`) as Promise<{ ok: boolean }>
}

export function getRuns() {
  return request.get('/load-test/runs') as Promise<LoadTestRun[]>
}

export function createRun(data: { profile_id: number; device_count?: number; virtual_device_count?: number }) {
  return request.post('/load-test/runs', data) as Promise<LoadTestRun>
}

export function executeRun(runId: number) {
  return request.post(`/load-test/runs/${runId}/execute`) as Promise<LoadTestRun>
}

export function getRunMetrics(runId: number) {
  return request.get(`/load-test/runs/${runId}/metrics`) as Promise<LoadTestMetric[]>
}
