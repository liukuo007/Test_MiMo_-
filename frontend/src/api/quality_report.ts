import request from './request'

export function getQualityReports() {
  return request.get('/quality-reports')
}

export function generateQualityReport() {
  return request.post('/quality-reports/generate')
}
