<template>
  <div class="env-detail" v-loading="loading">
    <div class="page-header">
      <div style="display: flex; align-items: center; gap: 12px">
        <el-button text @click="router.push('/environments')">返回</el-button>
        <h2>{{ env?.name || '环境详情' }}</h2>
        <el-tag v-if="env" :type="statusTag(env.status)" size="small">{{ statusLabel(env.status) }}</el-tag>
      </div>
      <div style="display: flex; gap: 8px">
        <el-button @click="handleCheck" :loading="checking">健康检测</el-button>
        <el-button @click="handleSnapshot">创建快照</el-button>
      </div>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>基本信息</template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="环境类型">{{ typeLabel(env?.env_type) }}</el-descriptions-item>
            <el-descriptions-item label="区域">{{ env?.region || '-' }}</el-descriptions-item>
            <el-descriptions-item label="Base URL">{{ env?.base_url || '-' }}</el-descriptions-item>
            <el-descriptions-item label="MQTT Broker">{{ env?.mqtt_broker_url || '-' }}</el-descriptions-item>
            <el-descriptions-item label="数据库">{{ env?.db_url || '-' }}</el-descriptions-item>
            <el-descriptions-item label="Redis">{{ env?.redis_url || '-' }}</el-descriptions-item>
            <el-descriptions-item label="AI 服务">{{ env?.ai_evaluator_url || '-' }}</el-descriptions-item>
            <el-descriptions-item label="WireMock">{{ env?.wiremock_url || '-' }}</el-descriptions-item>
            <el-descriptions-item label="支付端点">{{ env?.payment_endpoint || '-' }}</el-descriptions-item>
            <el-descriptions-item label="描述">{{ env?.description || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>组件健康状态</template>
          <div v-if="healthChecks.length === 0" style="text-align: center; color: #999; padding: 40px 0">
            点击"健康检测"按钮开始检测
          </div>
          <div v-for="check in healthChecks" :key="check.id" class="health-row">
            <div class="health-component">
              <el-icon :size="16" :color="check.status === 'healthy' ? '#67c23a' : check.status === 'degraded' ? '#e6a23c' : '#f56c6c'">
                <CircleCheckFilled v-if="check.status === 'healthy'" />
                <WarningFilled v-else-if="check.status === 'degraded'" />
                <CircleCloseFilled v-else />
              </el-icon>
              <span>{{ check.component }}</span>
            </div>
            <div class="health-latency">{{ check.latency_ms != null ? check.latency_ms.toFixed(1) + ' ms' : '-' }}</div>
            <div class="health-detail">{{ check.details?.message || check.details?.error || '-' }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover">
      <template #header>环境快照</template>
      <el-table :data="snapshots" stripe>
        <el-table-column prop="name" label="快照名称" />
        <el-table-column prop="snapshot_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ { manual: '手动', auto: '自动', freeze: '冻结' }[row.snapshot_type] || row.snapshot_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="notes" label="备注" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="warning" @click="handleRestore(row)">恢复</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CircleCheckFilled, CircleCloseFilled, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getEnvironment,
  checkEnvironmentHealth,
  createSnapshot,
  getSnapshots,
  restoreSnapshot,
  type EnvironmentItem,
  type HealthCheckItem,
  type SnapshotItem,
} from '@/api/environment'
import { formatDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const envId = Number(route.params.id)

const loading = ref(false)
const checking = ref(false)
const env = ref<EnvironmentItem | null>(null)
const healthChecks = ref<HealthCheckItem[]>([])
const snapshots = ref<SnapshotItem[]>([])

function typeLabel(t?: string) {
  return { dev: '开发', staging: '测试', prod: '生产' }[t || ''] || t || '-'
}
function statusLabel(s: string) {
  return { healthy: '健康', degraded: '降级', down: '不可用', unknown: '未知' }[s] || s
}
function statusTag(s: string) {
  return { healthy: 'success', degraded: 'warning', down: 'danger', unknown: 'info' }[s] || 'info'
}

async function loadEnv() {
  loading.value = true
  try {
    env.value = await getEnvironment(envId)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadSnapshots() {
  try {
    snapshots.value = await getSnapshots(envId)
  } catch (e) {
    console.error(e)
  }
}

async function handleCheck() {
  checking.value = true
  try {
    healthChecks.value = await checkEnvironmentHealth(envId)
    await loadEnv()
    ElMessage.success('检测完成')
  } catch (e: any) {
    ElMessage.error(e.message || '检测失败')
  } finally {
    checking.value = false
  }
}

async function handleSnapshot() {
  const { value } = await ElMessageBox.prompt('请输入快照名称', '创建快照', {
    inputValue: `${env.value?.name}-${new Date().toISOString().slice(0, 10)}`,
  })
  if (!value) return
  try {
    await createSnapshot(envId, { name: value })
    ElMessage.success('快照已创建')
    loadSnapshots()
  } catch (e: any) {
    ElMessage.error(e.message || '创建失败')
  }
}

async function handleRestore(row: SnapshotItem) {
  await ElMessageBox.confirm(`确定恢复到快照「${row.name}」？当前环境配置将被覆盖。`, '提示', { type: 'warning' })
  try {
    await restoreSnapshot(row.id)
    ElMessage.success('已恢复')
    await loadEnv()
  } catch (e: any) {
    ElMessage.error(e.message || '恢复失败')
  }
}

onMounted(() => {
  loadEnv()
  loadSnapshots()
})
</script>

<style scoped lang="scss">
.env-detail {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    h2 { margin: 0; font-size: 20px; }
  }
}
.health-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
  border-bottom: 1px dashed #f5f5f5;
  &:last-child { border-bottom: none; }
  .health-component {
    width: 100px;
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
  }
  .health-latency {
    width: 80px;
    color: #666;
    font-size: 13px;
  }
  .health-detail {
    flex: 1;
    color: #999;
    font-size: 13px;
  }
}
</style>
