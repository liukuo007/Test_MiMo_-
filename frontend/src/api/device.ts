import request from './request'

export function getDevices(params?: Record<string, any>) {
  return request.get('/devices', { params })
}

export function getDevice(id: number) {
  return request.get(`/devices/${id}`)
}

export function createDevice(data: Record<string, any>) {
  return request.post('/devices', data)
}

export function createVirtualDevices(data: Record<string, any>) {
  return request.post('/devices/virtual', data)
}

export function controlDevice(id: number, action: string) {
  return request.post(`/devices/${id}/control`, { action })
}

export function getDeviceEvents(id: number, limit?: number) {
  return request.get(`/devices/${id}/events`, { params: { limit } })
}
