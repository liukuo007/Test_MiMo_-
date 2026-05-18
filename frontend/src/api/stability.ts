import request from './request'

export interface FlakyTestCase {
  id: number
  test_case_id: number
  test_case_name: string | null
  flaky_rate: number
  pattern: Record<string, any> | null
  status: string
  detected_at: string
  resolved_at: string | null
}

export interface FailureCluster {
  id: number
  cluster_name: string
  root_cause_category: string
  sample_count: number
  percentage: number
  sample_errors: Record<string, any> | null
  keywords: Record<string, any> | null
  computed_at: string
}

export interface StabilityTrend {
  id: number
  dimension: string
  dimension_value: string
  stability_score: number
  pass_rate: number
  flaky_rate: number
  total_runs: number
  computed_at: string
}

export interface StabilitySummary {
  total_flaky: number
  active_flaky: number
  resolved_flaky: number
  overall_stability_score: number
  clusters: FailureCluster[]
  trends: StabilityTrend[]
}

export function getStabilitySummary() {
  return request.get('/stability/summary') as Promise<StabilitySummary>
}

export function getFlakyList(status?: string) {
  return request.get('/stability/flaky', { params: { status } }) as Promise<FlakyTestCase[]>
}

export function resolveFlaky(id: number) {
  return request.post(`/stability/flaky/${id}/resolve`) as Promise<{ ok: boolean }>
}

export function triggerDetection() {
  return request.post('/stability/detect') as Promise<{ flaky_detected: number; clusters_found: number; trends_computed: number }>
}

export function getClusters() {
  return request.get('/stability/clusters') as Promise<FailureCluster[]>
}

export function getTrends() {
  return request.get('/stability/trends') as Promise<StabilityTrend[]>
}
