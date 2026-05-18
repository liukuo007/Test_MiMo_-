import request from './request'

export function getDatasets(params?: Record<string, any>) {
  return request.get('/datasets', { params })
}

export function createDataset(data: Record<string, any>) {
  return request.post('/datasets', data)
}

export function updateDataset(id: number, data: Record<string, any>) {
  return request.put(`/datasets/${id}`, data)
}

export function deleteDataset(id: number) {
  return request.delete(`/datasets/${id}`)
}
