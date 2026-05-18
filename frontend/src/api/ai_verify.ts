import request from './request'

export function getAIModels() {
  return request.get('/ai/models')
}

export function createAIModel(data: Record<string, any>) {
  return request.post('/ai/models', data)
}

export function getModelVersions(modelId: number) {
  return request.get(`/ai/models/${modelId}/versions`)
}

export function createModelVersion(data: Record<string, any>) {
  return request.post('/ai/models/versions', data)
}

export function getEvaluations(params?: Record<string, any>) {
  return request.get('/ai/evaluations', { params })
}

export function createEvaluation(data: Record<string, any>) {
  return request.post('/ai/evaluations', data)
}

export function getEvaluation(id: number) {
  return request.get(`/ai/evaluations/${id}`)
}

export function compareModels(data: Record<string, any>) {
  return request.post('/ai/compare', data)
}
