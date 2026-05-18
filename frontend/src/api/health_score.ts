import request from './request'

export interface DimensionDetail {
  name: string
  key: string
  weight: number
  value: number
  score: number
  status: 'good' | 'warn' | 'bad'
}

export interface HealthScoreResponse {
  overall_score: number
  release_allowed: boolean
  release_threshold: number
  dimensions: DimensionDetail[]
  computed_at: string | null
}

export interface HealthScoreTrendItem {
  overall_score: number
  release_allowed: boolean
  computed_at: string
}

export interface ReleaseGateResponse {
  release_allowed: boolean
  overall_score: number
  threshold: number
  failing_dimensions: string[]
}

export function getHealthScore(params?: { project_id?: number; region?: string }) {
  return request.get('/health-score', { params }) as Promise<HealthScoreResponse>
}

export function getHealthScoreTrend(params?: { days?: number; project_id?: number }) {
  return request.get('/health-score/trend', { params }) as Promise<{ items: HealthScoreTrendItem[] }>
}

export function getReleaseGate(params?: { project_id?: number; region?: string }) {
  return request.get('/health-score/release-gate', { params }) as Promise<ReleaseGateResponse>
}
