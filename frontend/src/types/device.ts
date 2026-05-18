export interface Device {
  id: number
  name: string
  device_sn: string
  device_type: 'real' | 'virtual_l1' | 'virtual_l2' | 'virtual_l3'
  status: 'offline' | 'online' | 'occupied' | 'maintenance' | 'fault'
  region: string
  firmware_version: string | null
  temperature: number | null
  project_id: number | null
  occupied_by: number | null
  last_heartbeat: string | null
  created_at: string
}
