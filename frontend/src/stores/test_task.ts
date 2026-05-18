import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTestTasks } from '@/api/test_task'

interface TestTask {
  id: number
  name: string
  status: string
  environment: string
  trigger_type: string
  created_at: string
}

export const useTestTaskStore = defineStore('test_task', () => {
  const tasks = ref<TestTask[]>([])

  async function fetchTasks(params?: Record<string, any>) {
    tasks.value = await getTestTasks(params)
  }

  return { tasks, fetchTasks }
})
