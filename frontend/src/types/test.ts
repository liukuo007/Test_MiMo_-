export type TestType = 'api' | 'iot' | 'ai' | 'web' | 'app' | 'e2e'
export type Priority = 'p0' | 'p1' | 'p2' | 'p3'
export type TaskStatus = 'pending' | 'running' | 'passed' | 'failed' | 'cancelled' | 'timeout'

export interface TestCase {
  id: number
  name: string
  test_type: TestType
  priority: Priority
  module: string | null
  project_id: number
  created_at: string
}

export interface TestTask {
  id: number
  name: string
  status: TaskStatus
  environment: string
  trigger_type: string
  project_id: number
  created_at: string
}
