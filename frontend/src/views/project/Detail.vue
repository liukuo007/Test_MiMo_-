<template>
  <div class="page">
    <div class="page-header">
      <h2>项目详情 #{{ $route.params.id }}</h2>
      <el-button @click="router.push('/projects')">返回列表</el-button>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">{{ project.name || '-' }}</div>
          <div class="stat-label">项目名称</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat"><el-tag>{{ project.environment }}</el-tag></div>
          <div class="stat-label">环境</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">{{ devices.length }}</div>
          <div class="stat-label">关联设备</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">{{ testCases.length }}</div>
          <div class="stat-label">测试用例</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-bottom: 16px">
      <template #header><span>项目信息</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="项目名称">{{ project.name }}</el-descriptions-item>
        <el-descriptions-item label="环境">{{ project.environment }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ project.description || '无' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ project.created_at }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ project.updated_at }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><span>关联设备</span></template>
      <el-table :data="devices" stripe size="small">
        <el-table-column prop="device_sn" label="设备SN" width="180" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="region" label="区域" width="80" />
      </el-table>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><span>测试用例</span></template>
      <el-table :data="testCases" stripe size="small">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="用例名称" />
        <el-table-column prop="test_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.test_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="priorityType(row.priority)" size="small">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="120" />
      </el-table>
    </el-card>

    <el-card>
      <template #header><span>测试任务</span></template>
      <el-table :data="tasks" stripe size="small">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="任务名称" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="taskStatusType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="environment" label="环境" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject } from '@/api/project'
import { getDevices } from '@/api/device'
import { getTestCases } from '@/api/test_case'
import { getTestTasks } from '@/api/test_task'

const route = useRoute()
const router = useRouter()
const project = ref<any>({})
const devices = ref<any[]>([])
const testCases = ref<any[]>([])
const tasks = ref<any[]>([])

function statusType(s: string) {
  return { online: 'success', occupied: 'warning', offline: 'info', fault: 'danger', maintenance: '' }[s] || 'info'
}
function priorityType(p: string) {
  return { p0: 'danger', p1: 'warning', p2: '', p3: 'info' }[p] || ''
}
function taskStatusType(s: string) {
  return { passed: 'success', failed: 'danger', running: 'warning', pending: 'info', cancelled: '' }[s] || 'info'
}

onMounted(async () => {
  try {
    const id = Number(route.params.id)
    project.value = await getProject(id)
    const [devRes, caseRes, taskRes] = await Promise.all([
      getDevices({ project_id: id }).catch(() => []),
      getTestCases({ project_id: id }).catch(() => []),
      getTestTasks({ project_id: id }).catch(() => []),
    ])
    devices.value = Array.isArray(devRes) ? devRes : (devRes as any)?.items || []
    testCases.value = Array.isArray(caseRes) ? caseRes : (caseRes as any)?.items || []
    tasks.value = Array.isArray(taskRes) ? taskRes : (taskRes as any)?.items || []
  } catch {
    // fallback
  }
})
</script>

<style scoped lang="scss">
.stat { font-size: 20px; font-weight: bold; text-align: center; }
.stat-label { text-align: center; color: #909399; margin-top: 4px; font-size: 13px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
