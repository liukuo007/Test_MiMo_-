import request from './request'

export function getDefects(params?: Record<string, any>) {
  return request.get('/defects', { params })
}

export function getDefect(id: number) {
  return request.get(`/defects/${id}`)
}

export function createDefect(data: Record<string, any>) {
  return request.post('/defects', data)
}

export function updateDefect(id: number, data: Record<string, any>) {
  return request.put(`/defects/${id}`, data)
}

export function updateDefectStatus(id: number, status: string) {
  return request.put(`/defects/${id}/status`, { status })
}

export function assignDefect(id: number, assigned_to: number) {
  return request.post(`/defects/${id}/assign`, { assigned_to })
}

export function getDefectStatistics() {
  return request.get('/defects/statistics')
}
