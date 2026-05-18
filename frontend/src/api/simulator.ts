import request from './request'

export interface LocustStartParams {
  host?: string
  users?: number
  spawn_rate?: number
  run_time?: string
  tags?: string
}

export function startLocust(params: LocustStartParams) {
  return request.post('/simulator/start', params)
}

export function stopLocust() {
  return request.post('/simulator/stop')
}

export function getLocustStatus() {
  return request.get('/simulator/status')
}

export function getLocustResults() {
  return request.get('/simulator/results')
}
