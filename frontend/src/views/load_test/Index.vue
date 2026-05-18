<template>
  <div class="load-test-page">
    <div class="page-header">
      <h2>压测中心</h2>
      <el-button type="primary" @click="showCreateProfile">创建流量模型</el-button>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <!-- 流量模型 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>流量模型</template>
          <div v-if="profiles.length === 0" style="text-align: center; color: #999; padding: 20px">暂无模型</div>
          <div
            v-for="p in profiles"
            :key="p.id"
            class="profile-item"
            :class="{ active: selectedProfile?.id === p.id }"
            @click="selectedProfile = p"
          >
            <div class="profile-name">{{ p.name }}</div>
            <div class="profile-meta">时长 {{ p.duration_seconds }}s</div>
            <div class="profile-desc" v-if="p.description">{{ p.description }}</div>
          </div>
        </el-card>
      </el-col>

      <!-- 配置 & 执行 -->
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>执行压测</template>
          <el-form label-width="120px">
            <el-form-item label="流量模型">
              <el-select v-model="runForm.profile_id" style="width: 100%">
                <el-option v-for="p in profiles" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="实体设备数">
              <el-input-number v-model="runForm.device_count" :min="0" :max="1000" />
            </el-form-item>
            <el-form-item label="虚拟设备数">
              <el-slider v-model="runForm.virtual_device_count" :min="10" :max="100000" :step="10" show-input />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleCreateRun" :loading="creating">创建并执行</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 执行结果 -->
        <el-card shadow="hover" style="margin-top: 16px" v-if="currentRun">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>运行 #{{ currentRun.id }} — {{ currentRun.profile_name }}</span>
              <el-tag :type="currentRun.status === 'completed' ? 'success' : currentRun.status === 'running' ? 'warning' : 'info'" size="small">
                {{ { pending: '待执行', running: '执行中', completed: '已完成', failed: '失败' }[currentRun.status] || currentRun.status }}
              </el-tag>
            </div>
          </template>
          <el-row :gutter="16">
            <el-col :span="6">
              <div class="run-stat">
                <div class="run-stat-value">{{ currentRun.total_requests.toLocaleString() }}</div>
                <div class="run-stat-label">总请求数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="run-stat">
                <div class="run-stat-value" style="color: #f56c6c">{{ currentRun.error_count.toLocaleString() }}</div>
                <div class="run-stat-label">错误数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="run-stat">
                <div class="run-stat-value">{{ currentRun.avg_latency_ms.toFixed(0) }} ms</div>
                <div class="run-stat-label">平均延迟</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="run-stat">
                <div class="run-stat-value" style="color: #e6a23c">{{ currentRun.p99_latency_ms.toFixed(0) }} ms</div>
                <div class="run-stat-label">P99 延迟</div>
              </div>
            </el-col>
          </el-row>

          <!-- 指标图表 -->
          <div v-if="metrics.length > 0" style="margin-top: 16px">
            <div style="height: 250px">
              <v-chart :option="rpsChartOption" autoresize />
            </div>
            <div style="height: 250px; margin-top: 8px">
              <v-chart :option="latencyChartOption" autoresize />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 历史记录 -->
    <el-card shadow="hover">
      <template #header>历史记录</template>
      <el-table :data="runs" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="profile_name" label="流量模型" width="150" />
        <el-table-column prop="device_count" label="实体设备" width="100" />
        <el-table-column prop="virtual_device_count" label="虚拟设备" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'running' ? 'warning' : 'info'" size="small">
              {{ { pending: '待执行', running: '执行中', completed: '已完成', failed: '失败' }[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_requests" label="总请求" width="100" />
        <el-table-column prop="avg_latency_ms" label="平均延迟" width="100">
          <template #default="{ row }">{{ row.avg_latency_ms.toFixed(0) }} ms</template>
        </el-table-column>
        <el-table-column prop="p99_latency_ms" label="P99" width="100">
          <template #default="{ row }">{{ row.p99_latency_ms.toFixed(0) }} ms</template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="viewRun(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建流量模型弹窗 -->
    <el-dialog v-model="profileDialogVisible" title="创建流量模型" width="500px">
      <el-form :model="profileForm" label-width="100px">
        <el-form-item label="模型名称" required>
          <el-input v-model="profileForm.name" />
        </el-form-item>
        <el-form-item label="持续时间(秒)">
          <el-input-number v-model="profileForm.duration_seconds" :min="30" :max="3600" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="profileForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateProfile">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import 'echarts'
import {
  getProfiles,
  createProfile,
  getRuns,
  createRun,
  executeRun,
  getRunMetrics,
  type TrafficProfile,
  type LoadTestRun,
  type LoadTestMetric,
} from '@/api/load_test'

const profiles = ref<TrafficProfile[]>([])
const selectedProfile = ref<TrafficProfile | null>(null)
const runs = ref<LoadTestRun[]>([])
const currentRun = ref<LoadTestRun | null>(null)
const metrics = ref<LoadTestMetric[]>([])
const creating = ref(false)

const runForm = ref({
  profile_id: 0,
  device_count: 0,
  virtual_device_count: 100,
})

const profileDialogVisible = ref(false)
const profileForm = ref({ name: '', duration_seconds: 300, description: '' })

const rpsChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: metrics.value.map((_, i) => `${i * 5}s`) },
  yAxis: { type: 'value', name: 'RPS' },
  series: [{
    type: 'line',
    data: metrics.value.map(m => m.rps),
    smooth: true,
    areaStyle: { opacity: 0.15 },
  }],
}))

const latencyChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['平均延迟', 'P99 延迟'] },
  xAxis: { type: 'category', data: metrics.value.map((_, i) => `${i * 5}s`) },
  yAxis: { type: 'value', name: 'ms' },
  series: [
    { name: '平均延迟', type: 'line', data: metrics.value.map(m => m.avg_latency_ms), smooth: true },
    { name: 'P99 延迟', type: 'line', data: metrics.value.map(m => m.p99_latency_ms), smooth: true, lineStyle: { type: 'dashed' } },
  ],
}))

async function loadData() {
  try {
    profiles.value = await getProfiles()
    runs.value = await getRuns()
  } catch (e) {
    console.error(e)
  }
}

function showCreateProfile() {
  profileForm.value = { name: '', duration_seconds: 300, description: '' }
  profileDialogVisible.value = true
}

async function handleCreateProfile() {
  if (!profileForm.value.name) return ElMessage.warning('请输入名称')
  try {
    await createProfile(profileForm.value)
    profileDialogVisible.value = false
    ElMessage.success('创建成功')
    loadData()
  } catch (e: any) {
    ElMessage.error(e.message || '创建失败')
  }
}

async function handleCreateRun() {
  if (!runForm.value.profile_id) return ElMessage.warning('请选择流量模型')
  creating.value = true
  try {
    const run = await createRun(runForm.value)
    ElMessage.success('已创建，开始执行...')
    const executed = await executeRun(run.id)
    currentRun.value = executed
    metrics.value = await getRunMetrics(run.id)
    loadData()
  } catch (e: any) {
    ElMessage.error(e.message || '执行失败')
  } finally {
    creating.value = false
  }
}

async function viewRun(run: LoadTestRun) {
  currentRun.value = run
  try {
    metrics.value = await getRunMetrics(run.id)
  } catch (e) {
    console.error(e)
  }
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.load-test-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    h2 { margin: 0; font-size: 20px; }
  }
}
.profile-item {
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  &:hover { border-color: #409eff; }
  &.active { border-color: #409eff; background: #ecf5ff; }
  .profile-name { font-weight: 500; }
  .profile-meta { font-size: 12px; color: #999; }
  .profile-desc { font-size: 12px; color: #666; margin-top: 4px; }
}
.run-stat {
  text-align: center;
  .run-stat-value { font-size: 24px; font-weight: bold; color: #409eff; }
  .run-stat-label { font-size: 12px; color: #999; margin-top: 4px; }
}
</style>
