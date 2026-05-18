import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getDevices } from '@/api/device'

interface Device {
  id: number
  name: string
  device_sn: string
  device_type: string
  status: string
  region: string
  firmware_version: string | null
  temperature: number | null
}

export const useDeviceStore = defineStore('device', () => {
  const devices = ref<Device[]>([])
  const onlineCount = ref(0)
  const occupiedCount = ref(0)

  async function fetchDevices(params?: Record<string, any>) {
    devices.value = await getDevices(params)
    onlineCount.value = devices.value.filter((d) => d.status === 'online').length
    occupiedCount.value = devices.value.filter((d) => d.status === 'occupied').length
  }

  return { devices, onlineCount, occupiedCount, fetchDevices }
})
