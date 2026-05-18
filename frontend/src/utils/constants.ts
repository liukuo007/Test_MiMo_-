export const DEVICE_STATUS_MAP: Record<string, { label: string; color: string }> = {
  online: { label: '在线', color: '#52c41a' },
  offline: { label: '离线', color: '#999' },
  occupied: { label: '占用中', color: '#faad14' },
  maintenance: { label: '维护中', color: '#1890ff' },
  fault: { label: '故障', color: '#f5222d' },
}

export const TASK_STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending: { label: '待执行', color: '#999' },
  running: { label: '执行中', color: '#1890ff' },
  passed: { label: '通过', color: '#52c41a' },
  failed: { label: '失败', color: '#f5222d' },
  cancelled: { label: '已取消', color: '#999' },
  timeout: { label: '超时', color: '#faad14' },
}

export const TEST_TYPE_MAP: Record<string, string> = {
  api: 'API 测试',
  iot: 'IoT 仿真',
  ai: 'AI 验证',
  web: 'Web 自动化',
  app: 'App 自动化',
  e2e: '端到端',
}
