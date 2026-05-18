<template>
  <div class="page">
    <div class="page-header">
      <h2>任务详情 #{{ $route.params.id }}</h2>
      <div>
        <el-button v-if="task.status === 'pending'" type="primary" @click="handleExecute">执行</el-button>
        <el-button v-if="task.status === 'running'" type="warning" @click="handleCancel">取消</el-button>
        <el-button @click="router.push('/test-tasks')">返回列表</el-button>
      </div>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat"><el-tag :type="statusType(task.status)" size="large">{{ task.status || '-' }}</el-tag></div>
          <div class="stat-label">任务状态</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">{{ task.environment || '-' }}</div>
          <div class="stat-label">环境</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">{{ task.branch || '-' }}</div>
          <div class="stat-label">分支</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">{{ task.trigger_type || '-' }}</div>
          <div class="stat-label">触发方式</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-bottom: 16px">
      <template #header><span>任务信息</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务名称">{{ task.name }}</el-descriptions-item>
        <el-descriptions-item label="状态"><el-tag :type="statusType(task.status)">{{ task.status }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="环境">{{ task.environment }}</el-descriptions-item>
        <el-descriptions-item label="分支">{{ task.branch }}</el-descriptions-item>
        <el-descriptions-item label="触发方式">{{ task.trigger_type }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ task.description || '无' }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ task.started_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ task.finished_at || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><span>执行步骤</span></template>
      <el-steps :active="activeStep" finish-status="success" align-center>
        <el-step v-for="step in steps" :key="step.id" :title="step.name"
          :status="stepStatus(step.status)" :description="step.finished_at || ''" />
      </el-steps>
    </el-card>

    <el-card>
      <template #header><span>测试结果</span></template>
      <el-table :data="results" stripe size="small">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="test_case_id" label="用例ID" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'passed' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="device_sn" label="设备SN" width="180" />
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
      </el-table>
      <el-empty v-if="results.length === 0" description="暂无结果" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTestTask, executeTestTask, cancelTestTask } from '@/api/test_task'
import { getTestResults } from '@/api/test_result'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const task = ref<any>({})
const steps = ref<any[]>([])
const results = ref<any[]>([])

const activeStep = computed(() => {
  const idx = steps.value.findIndex(s => s.status === 'running')
  return idx >= 0 ? idx : steps.value.filter(s => s.status === 'passed').length
})

function statusType(s: string) {
  return { passed: 'success', failed: 'danger', running: 'warning', pending: 'info', cancelled: '', timeout: 'danger' }[s] || 'info'
}
function stepStatus(s: string) {
  return { passed: 'success', failed: 'error', running: 'process', pending: 'wait' }[s] || 'wait'
}

async function handleExecute() {
  await executeTestTask(Number(route.params.id))
  ElMessage.success('任务已开始执行')
  loadData()
}
async function handleCancel() {
  await cancelTestTask(Number(route.params.id))
  ElMessage.success('任务已取消')
  loadData()
}

async function loadData() {
  const id = Number(route.params.id)
  task.value = await getTestTask(id)
  steps.value = (task.value as any).steps || []
  const res = await getTestResults({ task_id: id }) as any
  results.value = Array.isArray(res) ? res : []
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.stat { font-size: 20px; font-weight: bold; text-align: center; }
.stat-label { text-align: center; color: #909399; margin-top: 4px; font-size: 13px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
