import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api/request'

export const useDefectStore = defineStore('defect', () => {
  const defects = ref<any[]>([])
  const total = ref(0)
  const statistics = ref<Record<string, number>>({})

  async function fetchDefects(params?: Record<string, any>) {
    const res = await request.get('/defects', { params })
    if (Array.isArray(res)) {
      defects.value = res
      total.value = res.length
    } else if (res?.items) {
      defects.value = res.items
      total.value = res.total ?? res.items.length
    }
    return res
  }

  async function createDefect(data: Record<string, any>) {
    return request.post('/defects', data)
  }

  async function updateDefectStatus(id: number, status: string) {
    return request.put(`/defects/${id}`, { status })
  }

  async function assignDefect(id: number, assignee: number) {
    return request.put(`/defects/${id}`, { assigned_to: assignee })
  }

  async function fetchStatistics() {
    statistics.value = await request.get('/defects/statistics')
    return statistics.value
  }

  return { defects, total, statistics, fetchDefects, createDefect, updateDefectStatus, assignDefect, fetchStatistics }
})
