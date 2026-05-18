import request from './request'

export function getProjects(params?: Record<string, any>) {
  return request.get('/projects', { params })
}

export function getProject(id: number) {
  return request.get(`/projects/${id}`)
}

export function createProject(data: Record<string, any>) {
  return request.post('/projects', data)
}

export function updateProject(id: number, data: Record<string, any>) {
  return request.put(`/projects/${id}`, data)
}
