import request from './request'

export function getTestTasks(params?: Record<string, any>) {
  return request.get('/test-tasks', { params })
}

export function getTestTask(id: number) {
  return request.get(`/test-tasks/${id}`)
}

export function createTestTask(data: Record<string, any>) {
  return request.post('/test-tasks', data)
}

export function executeTestTask(id: number) {
  return request.post(`/test-tasks/${id}/execute`)
}

export function cancelTestTask(id: number) {
  return request.post(`/test-tasks/${id}/cancel`)
}

export function deleteTestTask(id: number) {
  return request.delete(`/test-tasks/${id}`)
}

export function updateTestTask(id: number, data: Record<string, any>) {
  return request.put(`/test-tasks/${id}`, data)
}

export function saveDAGConfig(taskId: number, dagConfig: Record<string, any>) {
  return request.put(`/test-tasks/${taskId}`, { dag_config: dagConfig })
}
