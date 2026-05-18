import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api/request'

export const useAIStore = defineStore('ai', () => {
  const models = ref<any[]>([])
  const evaluations = ref<any[]>([])
  const evaluationTotal = ref(0)

  async function fetchModels() {
    models.value = await request.get('/ai/models')
    return models.value
  }

  async function fetchModelVersions(modelId: number) {
    return request.get(`/ai/models/${modelId}/versions`)
  }

  async function createModel(data: Record<string, any>) {
    return request.post('/ai/models', data)
  }

  async function createModelVersion(data: Record<string, any>) {
    return request.post('/ai/models/versions', data)
  }

  async function fetchEvaluations(params?: Record<string, any>) {
    const res = await request.get('/ai/evaluations', { params })
    if (Array.isArray(res)) {
      evaluations.value = res
      evaluationTotal.value = res.length
    } else if (res?.items) {
      evaluations.value = res.items
      evaluationTotal.value = res.total ?? res.items.length
    }
    return res
  }

  async function createEvaluation(data: Record<string, any>) {
    return request.post('/ai/evaluations', data)
  }

  async function getEvaluation(id: number) {
    return request.get(`/ai/evaluations/${id}`)
  }

  async function compareModels(data: Record<string, any>) {
    return request.post('/ai/compare', data)
  }

  return {
    models, evaluations, evaluationTotal,
    fetchModels, fetchModelVersions, createModel, createModelVersion,
    fetchEvaluations, createEvaluation, getEvaluation, compareModels,
  }
})
