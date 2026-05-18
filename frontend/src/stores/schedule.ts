import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api/request'

export const useScheduleStore = defineStore('schedule', () => {
  const schedules = ref<any[]>([])
  const total = ref(0)

  async function fetchSchedules(params?: Record<string, any>) {
    const res = await request.get('/schedules', { params })
    if (Array.isArray(res)) {
      schedules.value = res
      total.value = res.length
    } else if (res?.items) {
      schedules.value = res.items
      total.value = res.total ?? res.items.length
    }
    return res
  }

  async function createSchedule(data: Record<string, any>) {
    return request.post('/schedules', data)
  }

  async function updateSchedule(id: number, data: Record<string, any>) {
    return request.put(`/schedules/${id}`, data)
  }

  async function deleteSchedule(id: number) {
    return request.delete(`/schedules/${id}`)
  }

  async function triggerSchedule(id: number) {
    return request.post(`/schedules/${id}/trigger`)
  }

  return { schedules, total, fetchSchedules, createSchedule, updateSchedule, deleteSchedule, triggerSchedule }
})
