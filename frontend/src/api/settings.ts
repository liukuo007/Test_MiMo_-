import request from './request'

export function getSettings() {
  return request.get('/settings')
}

export function updateSettings(data: Record<string, any>) {
  return request.put('/settings', data)
}

export function getSettingsUsers() {
  return request.get('/settings/users')
}
