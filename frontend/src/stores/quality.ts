import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api/request'

export const useQualityStore = defineStore('quality', () => {
  const gateRules = ref<any[]>([])
  const gateStatus = ref<any[]>([])
  const reports = ref<any[]>([])
  const reportTotal = ref(0)

  async function fetchRules() {
    gateRules.value = await request.get('/quality-gate/rules')
    return gateRules.value
  }

  async function updateRules(data: Record<string, number>) {
    gateRules.value = await request.put('/quality-gate/rules', data)
    return gateRules.value
  }

  async function fetchGateStatus() {
    gateStatus.value = await request.get('/quality-gate/status')
    return gateStatus.value
  }

  async function fetchReports(params?: Record<string, any>) {
    const res = await request.get('/quality-reports', { params })
    if (Array.isArray(res)) {
      reports.value = res
      reportTotal.value = res.length
    } else if (res?.items) {
      reports.value = res.items
      reportTotal.value = res.total ?? res.items.length
    }
    return res
  }

  async function generateReport() {
    return request.post('/quality-reports/generate')
  }

  return {
    gateRules, gateStatus, reports, reportTotal,
    fetchRules, updateRules, fetchGateStatus, fetchReports, generateReport,
  }
})
