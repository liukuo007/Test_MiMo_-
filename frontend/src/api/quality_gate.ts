import request from './request'

export function getQualityGateRules() {
  return request.get('/quality-gate/rules')
}

export function updateQualityGateRules(rules: Record<string, any>) {
  return request.put('/quality-gate/rules', rules)
}

export function getQualityGateStatus() {
  return request.get('/quality-gate/status')
}
