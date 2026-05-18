<template>
  <div class="defect-list">
    <div class="page-header">
      <h2>缺陷管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">新建缺陷</el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-cards">
      <el-col :span="4">
        <el-card shadow="hover">
          <div class="stat-value">{{ stats.total || 0 }}</div>
          <div class="stat-label">总缺陷</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover">
          <div class="stat-value warning">{{ stats.by_status?.new || 0 }}</div>
          <div class="stat-label">新建</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover">
          <div class="stat-value primary">{{ stats.by_status?.in_progress || 0 }}</div>
          <div class="stat-label">处理中</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover">
          <div class="stat-value success">{{ stats.by_status?.fixed || 0 }}</div>
          <div class="stat-label">已修复</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover">
          <div class="stat-value danger">{{ stats.by_priority?.p0 || 0 }}</div>
          <div class="stat-label">P0 阻塞</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover">
          <div class="stat-value danger">{{ stats.by_priority?.p1 || 0 }}</div>
          <div class="stat-label">P1 严重</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选栏 -->
    <el-card style="margin-top: 16px">
      <el-form :inline="true" :model="filters">
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width: 140px">
            <el-option label="新建" value="new" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="已修复" value="fixed" />
            <el-option label="已关闭" value="closed" />
            <el-option label="重新打开" value="reopened" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filters.priority" clearable placeholder="全部" style="width: 120px">
            <el-option label="P0" value="p0" />
            <el-option label="P1" value="p1" />
            <el-option label="P2" value="p2" />
            <el-option label="P3" value="p3" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="filters.source" clearable placeholder="全部" style="width: 120px">
            <el-option label="测试发现" value="test" />
            <el-option label="自动创建" value="auto" />
            <el-option label="用户反馈" value="user" />
            <el-option label="监控告警" value="monitor" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadDefects">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 缺陷表格 -->
    <el-card style="margin-top: 16px">
      <el-table :data="defects" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="priorityType(row.priority)" size="small">{{ row.priority.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ sourceLabel(row.source) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="device_sn" label="设备" width="140" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
            <el-select
              v-if="getNextStatuses(row.status).length"
              v-model="row._nextStatus"
              size="small"
              style="width: 100px; margin: 0 8px"
              placeholder="流转状态"
              @change="handleStatusChange(row)"
            >
              <el-option
                v-for="s in getNextStatuses(row.status)"
                :key="s.value"
                :label="s.label"
                :value="s.value"
              />
            </el-select>
            <el-button size="small" type="warning" @click="showAssignDialog(row)">分配</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建缺陷弹窗 -->
    <el-dialog v-model="showCreateDialog" title="新建缺陷" width="600px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="createForm.title" placeholder="请输入缺陷标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="4" placeholder="详细描述缺陷" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="createForm.priority">
            <el-option label="P0 - 阻塞" value="p0" />
            <el-option label="P1 - 严重" value="p1" />
            <el-option label="P2 - 一般" value="p2" />
            <el-option label="P3 - 轻微" value="p3" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备SN">
          <el-input v-model="createForm.device_sn" placeholder="关联设备序列号" />
        </el-form-item>
        <el-form-item label="截图URL">
          <el-input v-model="createForm.screenshot_url" placeholder="截图链接" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 分配弹窗 -->
    <el-dialog v-model="showAssignVisible" title="分配责任人" width="400px">
      <el-select v-model="assignUserId" placeholder="选择用户" style="width: 100%">
        <el-option v-for="u in users" :key="u.id" :label="u.username" :value="u.id" />
      </el-select>
      <template #footer>
        <el-button @click="showAssignVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssign">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getDefects, createDefect, updateDefectStatus, assignDefect, getDefectStatistics } from '@/api/defect'
import { getSettingsUsers } from '@/api/settings'

const router = useRouter()
const loading = ref(false)
const defects = ref<any[]>([])
const stats = ref<any>({})
const users = ref<any[]>([])
const showCreateDialog = ref(false)
const showAssignVisible = ref(false)
const assignUserId = ref<number | null>(null)
const currentDefectId = ref<number | null>(null)

const filters = ref({
  status: '',
  priority: '',
  source: '',
})

const createForm = ref({
  title: '',
  description: '',
  priority: 'p2',
  device_sn: '',
  screenshot_url: '',
})

function statusType(s: string) {
  return { new: 'info', in_progress: 'warning', fixed: 'success', closed: '', reopened: 'danger' }[s] || 'info'
}

function statusLabel(s: string) {
  return { new: '新建', in_progress: '处理中', fixed: '已修复', closed: '已关闭', reopened: '重新打开' }[s] || s
}

function priorityType(p: string) {
  return { p0: 'danger', p1: 'warning', p2: '', p3: 'info' }[p] || ''
}

function sourceLabel(s: string) {
  return { test: '测试', auto: '自动', user: '用户', monitor: '监控' }[s] || s
}

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function getNextStatuses(current: string) {
  const map: Record<string, { value: string; label: string }[]> = {
    new: [{ value: 'in_progress', label: '处理中' }],
    in_progress: [{ value: 'fixed', label: '已修复' }, { value: 'closed', label: '关闭' }],
    fixed: [{ value: 'closed', label: '关闭' }, { value: 'reopened', label: '重新打开' }],
    reopened: [{ value: 'in_progress', label: '处理中' }],
    closed: [],
  }
  return map[current] || []
}

async function loadDefects() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.priority) params.priority = filters.value.priority
    if (filters.value.source) params.source = filters.value.source
    defects.value = await getDefects(params)
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  stats.value = await getDefectStatistics()
}

async function loadUsers() {
  try {
    users.value = await getSettingsUsers()
  } catch {
    users.value = []
  }
}

async function handleCreate() {
  if (!createForm.value.title) {
    ElMessage.warning('请输入标题')
    return
  }
  await createDefect(createForm.value)
  ElMessage.success('缺陷创建成功')
  showCreateDialog.value = false
  createForm.value = { title: '', description: '', priority: 'p2', device_sn: '', screenshot_url: '' }
  await loadDefects()
  await loadStats()
}

async function handleStatusChange(row: any) {
  if (!row._nextStatus) return
  await updateDefectStatus(row.id, row._nextStatus)
  ElMessage.success('状态更新成功')
  row._nextStatus = ''
  await loadDefects()
  await loadStats()
}

function showAssignDialog(row: any) {
  currentDefectId.value = row.id
  assignUserId.value = null
  showAssignVisible.value = true
}

async function handleAssign() {
  if (!assignUserId.value || !currentDefectId.value) return
  await assignDefect(currentDefectId.value, assignUserId.value)
  ElMessage.success('分配成功')
  showAssignVisible.value = false
  await loadDefects()
}

function viewDetail(row: any) {
  router.push(`/defects/${row.id}`)
}

onMounted(async () => {
  await Promise.all([loadDefects(), loadStats(), loadUsers()])
})
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.stat-value {
  font-size: 28px;
  font-weight: bold;
  text-align: center;
  color: #1890ff;
  &.warning { color: #e6a23c; }
  &.primary { color: #409eff; }
  &.success { color: #67c23a; }
  &.danger { color: #f56c6c; }
}
.stat-label {
  text-align: center;
  color: #909399;
  margin-top: 4px;
  font-size: 13px;
}
</style>
