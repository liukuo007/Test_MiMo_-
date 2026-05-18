import request from './request'

export function getSchedules(params?: Record<string, any>) {
  return request.get('/schedules', { params })
}

export function getSchedule(id: number) {
  return request.get(`/schedules/${id}`)
}

export function createSchedule(data: Record<string, any>) {
  return request.post('/schedules', data)
}

export function updateSchedule(id: number, data: Record<string, any>) {
  return request.put(`/schedules/${id}`, data)
}

export function deleteSchedule(id: number) {
  return request.delete(`/schedules/${id}`)
}

export function triggerSchedule(id: number) {
  return request.post(`/schedules/${id}/trigger`)
}
