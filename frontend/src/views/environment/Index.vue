<template>
  <div class="environment-page">
    <div class="page-header">
      <h2>环境治理中心</h2>
      <el-button type="primary" @click="showCreate">新建环境</el-button>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-select v-model="filterType" placeholder="环境类型" clearable @change="loadEnvs" style="width: 100%">
          <el-option label="开发" value="dev" />
          <el-option label="测试" value="staging" />
          <el-option label="生产" value="prod" />
        </el-select>
      </el-col>
      <el-col :span="6">
        <el-select v-model="filterStatus" placeholder="状态" clearable @change="loadEnvs" style="width: 100%">
          <el-option label="健康" value="healthy" />
          <el-option label="降级" value="degraded" />
          <el-option label="不可用" value="down" />
          <el-option label="未知" value="unknown" />
        </el-select>
      </el-col>
    </el-row>

    <el-table :data="envs" v-loading="loading" stripe>
      <el-table-column prop="name" label="环境名称" width="160">
        <template #default="{ row }">
          <el-link type="primary" @click="router.push(`/environments/${row.id}`)">{{ row.name }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="env_type" label="类型" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="typeTag(row.env_type)">{{ typeLabel(row.env_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="region" label="区域" width="80" />
      <el-table-column prop="base_url" label="Base URL" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">
            <el-icon style="margin-right: 4px"><CircleCheckFilled v-if="row.status === 'healthy'" /><WarningFilled v-else-if="row.status === 'degraded'" /><CircleCloseFilled v-else /></el-icon>
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="handleCheck(row)">健康检测</el-button>
          <el-button size="small" @click="handleSnapshot(row)">快照</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑环境' : '新建环境'" width="600px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="环境名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="环境类型">
          <el-select v-model="form.env_type" style="width: 100%">
            <el-option label="开发" value="dev" />
            <el-option label="测试" value="staging" />
            <el-option label="生产" value="prod" />
          </el-select>
        </el-form-item>
        <el-form-item label="区域">
          <el-input v-model="form.region" placeholder="如 SG / US / EU" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" />
        </el-form-item>
        <el-form-item label="MQTT Broker">
          <el-input v-model="form.mqtt_broker_url" />
        </el-form-item>
        <el-form-item label="数据库 URL">
          <el-input v-model="form.db_url" />
        </el-form-item>
        <el-form-item label="Redis URL">
          <el-input v-model="form.redis_url" />
        </el-form-item>
        <el-form-item label="AI 服务 URL">
          <el-input v-model="form.ai_evaluator_url" />
        </el-form-item>
        <el-form-item label="WireMock URL">
          <el-input v-model="form.wiremock_url" />
        </el-form-item>
        <el-form-item label="支付端点">
          <el-input v-model="form.payment_endpoint" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 健康检测结果弹窗 -->
    <el-dialog v-model="healthDialogVisible" title="健康检测结果" width="600px">
      <el-table :data="healthChecks" stripe>
        <el-table-column prop="component" label="组件" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="latency_ms" label="延迟" width="100">
          <template #default="{ row }">{{ row.latency_ms != null ? row.latency_ms.toFixed(1) + ' ms' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="details" label="详情" show-overflow-tooltip>
          <template #default="{ row }">{{ row.details?.message || row.details?.error || JSON.stringify(row.details || {}) }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 快照弹窗 -->
    <el-dialog v-model="snapshotDialogVisible" title="创建环境快照" width="400px">
      <el-form :model="snapshotForm" label-width="80px">
        <el-form-item label="快照名称" required>
          <el-input v-model="snapshotForm.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="snapshotForm.snapshot_type" style="width: 100%">
            <el-option label="手动" value="manual" />
            <el-option label="自动" value="auto" />
            <el-option label="冻结" value="freeze" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="snapshotForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="snapshotDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveSnapshot" :loading="savingSnapshot">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { CircleCheckFilled, CircleCloseFilled, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getEnvironments,
  createEnvironment,
  updateEnvironment,
  deleteEnvironment,
  checkEnvironmentHealth,
  createSnapshot,
  type EnvironmentItem,
  type HealthCheckItem,
} from '@/api/environment'

const router = useRouter()
const loading = ref(false)
const envs = ref<EnvironmentItem[]>([])
const filterType = ref('')
const filterStatus = ref('')

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = ref({
  name: '',
  env_type: 'staging',
  region: '',
  base_url: '',
  mqtt_broker_url: '',
  db_url: '',
  redis_url: '',
  ai_evaluator_url: '',
  wiremock_url: '',
  payment_endpoint: '',
  description: '',
})

const healthDialogVisible = ref(false)
const healthChecks = ref<HealthCheckItem[]>([])

const snapshotDialogVisible = ref(false)
const savingSnapshot = ref(false)
const snapshotEnvId = ref(0)
const snapshotForm = ref({ name: '', snapshot_type: 'manual', notes: '' })

function typeLabel(t: string) {
  return { dev: '开发', staging: '测试', prod: '生产' }[t] || t
}
function typeTag(t: string) {
  return { dev: 'info', staging: '', prod: 'danger' }[t] || 'info'
}
function statusLabel(s: string) {
  return { healthy: '健康', degraded: '降级', down: '不可用', unknown: '未知' }[s] || s
}
function statusTag(s: string) {
  return { healthy: 'success', degraded: 'warning', down: 'danger', unknown: 'info' }[s] || 'info'
}

async function loadEnvs() {
  loading.value = true
  try {
    const params: any = {}
    if (filterType.value) params.env_type = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    envs.value = await getEnvironments(params)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function showCreate() {
  editingId.value = null
  form.value = { name: '', env_type: 'staging', region: '', base_url: '', mqtt_broker_url: '', db_url: '', redis_url: '', ai_evaluator_url: '', wiremock_url: '', payment_endpoint: '', description: '' }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.name) return ElMessage.warning('请输入环境名称')
  saving.value = true
  try {
    if (editingId.value) {
      await updateEnvironment(editingId.value, form.value)
    } else {
      await createEnvironment(form.value)
    }
    dialogVisible.value = false
    ElMessage.success('保存成功')
    loadEnvs()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: EnvironmentItem) {
  await ElMessageBox.confirm(`确定删除环境「${row.name}」？`, '提示', { type: 'warning' })
  try {
    await deleteEnvironment(row.id)
    ElMessage.success('已删除')
    loadEnvs()
  } catch (e: any) {
    ElMessage.error(e.message || '删除失败')
  }
}

async function handleCheck(row: EnvironmentItem) {
  try {
    healthChecks.value = await checkEnvironmentHealth(row.id)
    healthDialogVisible.value = true
    loadEnvs()
  } catch (e: any) {
    ElMessage.error(e.message || '检测失败')
  }
}

function handleSnapshot(row: EnvironmentItem) {
  snapshotEnvId.value = row.id
  snapshotForm.value = { name: `${row.name}-${new Date().toISOString().slice(0, 10)}`, snapshot_type: 'manual', notes: '' }
  snapshotDialogVisible.value = true
}

async function handleSaveSnapshot() {
  if (!snapshotForm.value.name) return ElMessage.warning('请输入快照名称')
  savingSnapshot.value = true
  try {
    await createSnapshot(snapshotEnvId.value, snapshotForm.value)
    snapshotDialogVisible.value = false
    ElMessage.success('快照已创建')
  } catch (e: any) {
    ElMessage.error(e.message || '创建失败')
  } finally {
    savingSnapshot.value = false
  }
}

onMounted(loadEnvs)
</script>

<style scoped lang="scss">
.environment-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    h2 { margin: 0; font-size: 20px; }
  }
}
</style>
