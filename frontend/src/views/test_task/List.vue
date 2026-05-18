<template>
  <div class="page">
    <div class="page-header">
      <h2>任务管理</h2>
      <el-button type="primary" @click="router.push('/test-tasks/create')">创建任务</el-button>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="8">
        <el-input v-model="search" placeholder="搜索任务名称" clearable @clear="fetchTasks" @keyup.enter="fetchTasks">
          <template #append>
            <el-button @click="fetchTasks">搜索</el-button>
          </template>
        </el-input>
      </el-col>
      <el-col :span="4">
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="fetchTasks">
          <el-option v-for="(v, k) in TASK_STATUS_MAP" :key="k" :label="v.label" :value="k" />
        </el-select>
      </el-col>
    </el-row>

    <el-table :data="tasks" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="任务名称" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ TASK_STATUS_MAP[row.status]?.label || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="environment" label="环境" width="100" />
      <el-table-column prop="trigger_type" label="触发方式" width="100" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleExecute(row.id)">执行</el-button>
          <el-button link @click="router.push(`/test-tasks/${row.id}`)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > pageSize"
      style="margin-top: 16px; justify-content: flex-end"
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="handlePageChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getTestTasks, executeTestTask } from '@/api/test_task'
import { TASK_STATUS_MAP } from '@/utils/constants'
import { formatDate } from '@/utils/format'
import { ElMessage } from 'element-plus'

const router = useRouter()
const tasks = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const search = ref('')
const filterStatus = ref('')

function statusTagType(status: string) {
  const map: Record<string, string> = { running: 'warning', passed: 'success', failed: 'danger', pending: 'info', cancelled: 'info' }
  return map[status] || 'info'
}

async function fetchTasks() {
  loading.value = true
  try {
    const params: any = { skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value }
    if (search.value) params.search = search.value
    if (filterStatus.value) params.status = filterStatus.value
    const result = await getTestTasks(params)
    if (Array.isArray(result)) {
      tasks.value = result
      total.value = result.length
    } else if (result?.items) {
      tasks.value = result.items
      total.value = result.total ?? result.items.length
    } else {
      tasks.value = result
      total.value = result.length
    }
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchTasks()
}

async function handleExecute(id: number) {
  await executeTestTask(id)
  ElMessage.success('任务已触发执行')
  fetchTasks()
}

onMounted(fetchTasks)
</script>
