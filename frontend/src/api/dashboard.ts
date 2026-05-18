import request from './request'

export function getOverview() {
  return request.get('/dashboard/overview')
}

export function getQualityScore() {
  return request.get('/dashboard/quality-score')
}

export function getTrend(days?: number) {
  return request.get('/dashboard/trend', { params: { days } })
}

export function getRadar() {
  return request.get('/dashboard/radar')
}

export function getAlerts() {
  return request.get('/dashboard/alerts')
}
