import request from './request'

export interface DevicePool {
  id: number
  name: string
  pool_type: string
  auto_assign: boolean
  max_devices: number
  description: string | null
  config: Record<string, any> | null
  device_count: number
  created_at: string
  updated_at: string
}

export interface PoolDevice {
  member_id: number
  device_id: number
  name: string
  sn: string
  status: string
  device_type: string
  added_at: string
}

export interface DeviceTag {
  id: number
  device_id: number
  tag_key: string
  tag_value: string
  created_at: string
}

export interface DeviceHealthScore {
  id: number
  device_id: number
  score: number
  factors: Record<string, number> | null
  computed_at: string
}

export function getPools() {
  return request.get('/device-mesh/pools') as Promise<DevicePool[]>
}

export function createPool(data: Partial<DevicePool>) {
  return request.post('/device-mesh/pools', data) as Promise<DevicePool>
}

export function updatePool(id: number, data: Partial<DevicePool>) {
  return request.put(`/device-mesh/pools/${id}`, data) as Promise<DevicePool>
}

export function deletePool(id: number) {
  return request.delete(`/device-mesh/pools/${id}`) as Promise<{ ok: boolean }>
}

export function getPoolDevices(poolId: number) {
  return request.get(`/device-mesh/pools/${poolId}/devices`) as Promise<PoolDevice[]>
}

export function assignDevices(poolId: number, deviceIds: number[]) {
  return request.post(`/device-mesh/pools/${poolId}/assign`, { device_ids: deviceIds }) as Promise<{ assigned: number }>
}

export function removePoolDevice(poolId: number, deviceId: number) {
  return request.delete(`/device-mesh/pools/${poolId}/devices/${deviceId}`) as Promise<{ ok: boolean }>
}

export function autoSchedule(poolId: number, strategy: string, count: number) {
  return request.post(`/device-mesh/pools/${poolId}/schedule`, { strategy, count }) as Promise<{ devices: PoolDevice[] }>
}

export function addDeviceTags(deviceId: number, tags: { tag_key: string; tag_value: string }[]) {
  return request.post(`/device-mesh/devices/${deviceId}/tags`, tags) as Promise<DeviceTag[]>
}

export function getDeviceTags(deviceId: number) {
  return request.get(`/device-mesh/devices/${deviceId}/tags`) as Promise<DeviceTag[]>
}

export function getDeviceHealth(deviceId: number) {
  return request.get(`/device-mesh/devices/${deviceId}/health`) as Promise<DeviceHealthScore>
}
