<template>
  <div class="defect-detail" v-loading="loading">
    <div class="page-header">
      <el-button @click="router.push('/defects')">返回列表</el-button>
      <h2>缺陷 #{{ defect.id }} - {{ defect.title }}</h2>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：基本信息 -->
      <el-col :span="16">
        <el-card>
          <template #header>基本信息</template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="ID">{{ defect.id }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusType(defect.status)">{{ statusLabel(defect.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="优先级">
              <el-tag :type="priorityType(defect.priority)">{{ defect.priority?.toUpperCase() }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="来源">{{ sourceLabel(defect.source) }}</el-descriptions-item>
            <el-descriptions-item label="责任人">{{ defect.assignee_name || '未分配' }}</el-descriptions-item>
            <el-descriptions-item label="创建人">{{ defect.creator_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="设备SN">{{ defect.device_sn || '-' }}</el-descriptions-item>
            <el-descriptions-item label="关联用例">
              <router-link v-if="defect.test_case_id" :to="`/test-cases/${defect.test_case_id}/edit`">
                用例 #{{ defect.test_case_id }}
              </router-link>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatTime(defect.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ formatTime(defect.updated_at) }}</el-descriptions-item>
            <el-descriptions-item label="修复时间">{{ formatTime(defect.resolved_at) }}</el-descriptions-item>
            <el-descriptions-item label="关闭时间">{{ formatTime(defect.closed_at) }}</el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">
              <div style="white-space: pre-wrap">{{ defect.description || '无描述' }}</div>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 截图预览 -->
        <el-card v-if="defect.screenshot_url" style="margin-top: 16px">
          <template #header>截图</template>
          <el-image :src="defect.screenshot_url" :preview-src-list="[defect.screenshot_url]" style="max-width: 100%" />
        </el-card>
      </el-col>

      <!-- 右侧：操作 -->
      <el-col :span="8">
        <!-- 状态流转 -->
        <el-card>
          <template #header>状态流转</template>
          <div class="status-actions">
            <el-button
              v-for="s in getNextStatuses(defect.status)"
              :key="s.value"
              :type="s.value === 'fixed' ? 'success' : s.value === 'closed' ? 'info' : 'primary'"
              @click="handleStatusChange(s.value)"
              style="margin-bottom: 8px; width: 100%"
            >
              {{ s.label }}
            </el-button>
            <el-empty v-if="!getNextStatuses(defect.status).length" description="无可用操作" :image-size="60" />
          </div>
        </el-card>

        <!-- 分配责任人 -->
        <el-card style="margin-top: 16px">
          <template #header>分配责任人</template>
          <el-select v-model="assignUserId" placeholder="选择用户" style="width: 100%">
            <el-option v-for="u in users" :key="u.id" :label="u.username" :value="u.id" />
          </el-select>
          <el-button type="primary" style="margin-top: 8px; width: 100%" @click="handleAssign" :disabled="!assignUserId">
            分配
          </el-button>
        </el-card>

        <!-- 关联信息 -->
        <el-card style="margin-top: 16px">
          <template #header>关联信息</template>
          <div v-if="defect.test_result_id" style="margin-bottom: 8px">
            <span class="label">测试结果: </span>
            <router-link :to="`/traces/${defect.test_result_id}`">结果 #{{ defect.test_result_id }}</router-link>
          </div>
          <div v-if="defect.tags && Object.keys(defect.tags).length">
            <span class="label">标签: </span>
            <el-tag v-for="(v, k) in defect.tags" :key="k" size="small" style="margin-right: 4px">{{ k }}: {{ v }}</el-tag>
          </div>
          <el-empty v-if="!defect.test_result_id && (!defect.tags || !Object.keys(defect.tags).length)" description="无关联信息" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getDefect, updateDefectStatus, assignDefect } from '@/api/defect'
import { getSettingsUsers } from '@/api/settings'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const defect = ref<any>({})
const users = ref<any[]>([])
const assignUserId = ref<number | null>(null)

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
  return { test: '测试发现', auto: '自动创建', user: '用户反馈', monitor: '监控告警' }[s] || s
}

function formatTime(t: string | null) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function getNextStatuses(current: string) {
  const map: Record<string, { value: string; label: string }[]> = {
    new: [{ value: 'in_progress', label: '开始处理' }],
    in_progress: [{ value: 'fixed', label: '标记已修复' }, { value: 'closed', label: '关闭' }],
    fixed: [{ value: 'closed', label: '确认关闭' }, { value: 'reopened', label: '重新打开' }],
    reopened: [{ value: 'in_progress', label: '重新处理' }],
    closed: [],
  }
  return map[current] || []
}

async function loadDefect() {
  loading.value = true
  try {
    defect.value = await getDefect(Number(route.params.id))
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  try {
    users.value = await getSettingsUsers()
  } catch {
    users.value = []
  }
}

async function handleStatusChange(status: string) {
  await updateDefectStatus(defect.value.id, status)
  ElMessage.success('状态更新成功')
  await loadDefect()
}

async function handleAssign() {
  if (!assignUserId.value) return
  await assignDefect(defect.value.id, assignUserId.value)
  ElMessage.success('分配成功')
  await loadDefect()
}

onMounted(async () => {
  await Promise.all([loadDefect(), loadUsers()])
})
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  h2 { margin: 0; }
}
.label {
  color: #909399;
  margin-right: 4px;
}
</style>
