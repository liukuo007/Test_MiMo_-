<template>
  <div class="schedule-list">
    <div class="page-header">
      <h2>定时任务</h2>
      <el-button type="primary" @click="showCreateDialog = true">创建定时任务</el-button>
    </div>

    <el-card>
      <el-table :data="schedules" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="名称" min-width="180" />
        <el-table-column prop="task_id" label="关联任务" width="100">
          <template #default="{ row }">
            <router-link :to="`/test-tasks/${row.task_id}`">任务 #{{ row.task_id }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="cron_expression" label="Cron 表达式" width="150">
          <template #default="{ row }">
            <el-tag type="info">{{ row.cron_expression }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="上次执行" width="170">
          <template #default="{ row }">{{ formatTime(row.last_run_at) }}</template>
        </el-table-column>
        <el-table-column prop="next_run_at" label="下次执行" width="170">
          <template #default="{ row }">{{ formatTime(row.next_run_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleTrigger(row)">立即执行</el-button>
            <el-button size="small" @click="handleToggle(row)">{{ row.is_active ? '禁用' : '启用' }}</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建弹窗 -->
    <el-dialog v-model="showCreateDialog" title="创建定时任务" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="定时任务名称" />
        </el-form-item>
        <el-form-item label="关联任务" required>
          <el-select v-model="createForm.task_id" placeholder="选择测试任务" style="width: 100%">
            <el-option v-for="t in tasks" :key="t.id" :label="`#${t.id} ${t.name}`" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron 表达式" required>
          <el-input v-model="createForm.cron_expression" placeholder="例如: 0 9 * * 1-5 (工作日9点)" />
          <div class="cron-hint">
            格式: 分 时 日 月 周几<br />
            示例: <code>0 9 * * *</code> 每天9点 | <code>*/30 * * * *</code> 每30分钟 | <code>0 9 * * 1-5</code> 工作日9点
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSchedules, createSchedule, updateSchedule, deleteSchedule, triggerSchedule } from '@/api/schedule'
import { getTestTasks } from '@/api/test_task'

const loading = ref(false)
const schedules = ref<any[]>([])
const tasks = ref<any[]>([])
const showCreateDialog = ref(false)

const createForm = ref({
  name: '',
  task_id: null as number | null,
  cron_expression: '',
})

function formatTime(t: string | null) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

async function loadSchedules() {
  loading.value = true
  try {
    schedules.value = await getSchedules()
  } finally {
    loading.value = false
  }
}

async function loadTasks() {
  try {
    tasks.value = await getTestTasks()
  } catch {
    tasks.value = []
  }
}

async function handleCreate() {
  if (!createForm.value.name || !createForm.value.task_id || !createForm.value.cron_expression) {
    ElMessage.warning('请填写完整信息')
    return
  }
  await createSchedule(createForm.value)
  ElMessage.success('创建成功')
  showCreateDialog.value = false
  createForm.value = { name: '', task_id: null, cron_expression: '' }
  await loadSchedules()
}

async function handleTrigger(row: any) {
  const result = await triggerSchedule(row.id)
  ElMessage.success(`任务已触发: Task #${result.task_id}`)
}

async function handleToggle(row: any) {
  await updateSchedule(row.id, { is_active: !row.is_active })
  ElMessage.success(row.is_active ? '已禁用' : '已启用')
  await loadSchedules()
}

async function handleDelete(row: any) {
  await deleteSchedule(row.id)
  ElMessage.success('已删除')
  await loadSchedules()
}

onMounted(async () => {
  await Promise.all([loadSchedules(), loadTasks()])
})
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.cron-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
  code {
    background: #f5f5f5;
    padding: 2px 6px;
    border-radius: 3px;
  }
}
</style>
