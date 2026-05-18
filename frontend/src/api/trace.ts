import request from './request'

export function getTraces(params?: Record<string, any>) {
  return request.get('/traces', { params })
}

export function getTraceDetail(traceId: string) {
  return request.get(`/traces/${traceId}`)
}
