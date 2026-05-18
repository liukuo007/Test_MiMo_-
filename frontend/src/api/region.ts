import request from './request'

export interface Region {
  id: number
  code: string
  name: string
  mqtt_broker_url: string | null
  payment_endpoint: string | null
  ai_endpoint: string | null
  base_url: string | null
  status: string
  config: Record<string, any> | null
  description: string | null
  created_at: string
}

export interface RegionHealth {
  region: Region
  metrics: Record<string, number>
  overall_score: number
}

export interface GlobalMapItem {
  code: string
  name: string
  status: string
  overall_score: number
  metrics: Record<string, number>
}

export function getRegions() {
  return request.get('/regions') as Promise<Region[]>
}

export function createRegion(data: Partial<Region>) {
  return request.post('/regions', data) as Promise<Region>
}

export function updateRegion(id: number, data: Partial<Region>) {
  return request.put(`/regions/${id}`, data) as Promise<Region>
}

export function getRegionHealth(id: number) {
  return request.get(`/regions/${id}/health`) as Promise<RegionHealth>
}

export function getGlobalQualityMap() {
  return request.get('/regions/global-map') as Promise<GlobalMapItem[]>
}
