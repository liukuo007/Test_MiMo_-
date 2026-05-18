import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getHealthScore,
  getHealthScoreTrend,
  getReleaseGate,
  type HealthScoreResponse,
  type HealthScoreTrendItem,
  type ReleaseGateResponse,
} from '@/api/health_score'

export const useHealthStore = defineStore('health', () => {
  const currentScore = ref<HealthScoreResponse | null>(null)
  const trend = ref<HealthScoreTrendItem[]>([])
  const releaseGate = ref<ReleaseGateResponse | null>(null)
  const loading = ref(false)

  async function fetchHealthScore(params?: { project_id?: number; region?: string }) {
    loading.value = true
    try {
      currentScore.value = await getHealthScore(params)
    } catch (e) {
      console.error('[HealthStore] fetchHealthScore failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchTrend(days: number = 7, project_id?: number) {
    try {
      const res = await getHealthScoreTrend({ days, project_id })
      trend.value = res.items || []
    } catch (e) {
      console.error('[HealthStore] fetchTrend failed:', e)
    }
  }

  async function fetchReleaseGate(params?: { project_id?: number; region?: string }) {
    try {
      releaseGate.value = await getReleaseGate(params)
    } catch (e) {
      console.error('[HealthStore] fetchReleaseGate failed:', e)
    }
  }

  return { currentScore, trend, releaseGate, loading, fetchHealthScore, fetchTrend, fetchReleaseGate }
})
