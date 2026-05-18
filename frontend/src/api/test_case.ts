import request from './request'

export function getTestCases(params?: Record<string, any>) {
  return request.get('/test-cases', { params })
}

export function getTestCase(id: number) {
  return request.get(`/test-cases/${id}`)
}

export function createTestCase(data: Record<string, any>) {
  return request.post('/test-cases', data)
}

export function updateTestCase(id: number, data: Record<string, any>) {
  return request.put(`/test-cases/${id}`, data)
}

export function deleteTestCase(id: number) {
  return request.delete(`/test-cases/${id}`)
}
