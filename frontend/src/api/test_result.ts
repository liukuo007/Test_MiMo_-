import request from './request'

export function getTestResults(params?: Record<string, any>) {
  return request.get('/test-results', { params })
}

export function getTestResult(id: number) {
  return request.get(`/test-results/${id}`)
}
