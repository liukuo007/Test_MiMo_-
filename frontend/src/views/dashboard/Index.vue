<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h2>数据看板</h2>
      <el-button
        type="primary"
        size="large"
        :loading="smokeRunning"
        :icon="smokeRunning ? undefined : 'Monitor'"
        @click="handleSmokeTest"
      >
        {{ smokeRunning ? '冒烟测试执行中...' : '一键启动冒烟测试' }}
      </el-button>
    </div>

    <!-- 冒烟测试进度条 -->
    <el-card v-if="smokeSteps.length > 0" class="smoke-progress-card" style="margin-top: 16px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>冒烟测试进度</span>
          <el-tag :type="smokeOverall === 'passed' ? 'success' : smokeOverall === 'failed' ? 'danger' : 'info'" size="small">
            {{ smokeOverall === 'passed' ? '全部通过' : smokeOverall === 'failed' ? '存在失败' : '执行中' }}
          </el-tag>
        </div>
      </template>
      <el-steps :active="smokeActiveStep" finish-status="success" align-center>
        <el-step
          v-for="step in smokeSteps"
          :key="step.step"
          :title="step.name"
          :status="getStepStatus(step)"
          :description="getStepDescription(step)"
        />
      </el-steps>
    </el-card>

    <el-row :gutter="16" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>在线设备</template>
          <div class="stat-value">{{ overview.devices?.online || 0 }}</div>
          <div class="stat-sub">总计 {{ overview.devices?.total || 0 }} 台</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>运行中任务</template>
          <div class="stat-value">{{ overview.tasks?.running || 0 }}</div>
          <div class="stat-sub">总计 {{ overview.tasks?.total || 0 }} 个</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>测试通过率</template>
          <div class="stat-value">{{ overview.results?.pass_rate || 0 }}%</div>
          <div class="stat-sub">共 {{ overview.results?.total || 0 }} 条结果</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="clickable-card" @click="router.push('/quality/health-score')">
          <template #header>质量评分</template>
          <div class="stat-value">{{ qualityScore.overall_score || 0 }}</div>
          <div class="stat-sub">综合评分</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>测试趋势</span>
              <el-radio-group v-model="trendDays" size="small" @change="fetchTrend">
                <el-radio-button :value="7">7天</el-radio-button>
                <el-radio-button :value="30">30天</el-radio-button>
                <el-radio-button :value="90">90天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div style="height: 300px">
            <v-chart :option="trendOption" autoresize />
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>质量维度</template>
          <div style="height: 300px">
            <v-chart :option="radarOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>活跃告警</span>
              <el-badge :value="alerts.length" :max="99" type="danger">
                <el-button size="small" @click="fetchAlerts">刷新</el-button>
              </el-badge>
            </div>
          </template>
          <el-table :data="alerts" stripe v-loading="alertsLoading" max-height="300">
            <el-table-column prop="level" label="级别" width="100">
              <template #default="{ row }">
                <el-tag :type="row.level === 'critical' ? 'danger' : row.level === 'error' ? 'warning' : 'info'" size="small">
                  {{ row.level === 'critical' ? '严重' : row.level === 'error' ? '错误' : '警告' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag size="small" type="info">{{ { defect: '缺陷', device: '设备', task: '任务' }[row.type] || row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="告警信息" />
            <el-table-column prop="created_at" label="时间" width="170">
              <template #default="{ row }">{{ row.created_at ? formatDate(row.created_at) : '-' }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 冒烟测试结果弹窗 -->
    <el-dialog v-model="smokeDialogVisible" title="冒烟测试结果" width="520px" :close-on-click-modal="false">
      <div v-if="smokeResult" class="smoke-result">
        <div class="smoke-result-header" :class="smokeResult.status === 'passed' ? 'smoke-passed' : 'smoke-failed'">
          <el-icon :size="48">
            <template v-if="smokeResult.status === 'passed'"><CircleCheckFilled /></template>
            <template v-else><CircleCloseFilled /></template>
          </el-icon>
          <div class="smoke-result-title">
            {{ smokeResult.status === 'passed' ? '全部通过' : '存在失败' }}
          </div>
          <div class="smoke-result-duration">
            总耗时: {{ smokeResult.total_duration_ms.toFixed(0) }} ms
          </div>
        </div>
        <el-divider />
        <div v-for="step in smokeResult.steps" :key="step.step" class="smoke-step-detail">
          <div class="smoke-step-row">
            <el-icon :size="16" :color="step.status === 'passed' ? '#67c23a' : '#f56c6c'">
              <template v-if="step.status === 'passed'"><CircleCheckFilled /></template>
              <template v-else><CircleCloseFilled /></template>
            </el-icon>
            <span class="smoke-step-name">{{ step.step }}. {{ step.name }}</span>
            <span class="smoke-step-time">{{ step.duration_ms.toFixed(0) }} ms</span>
          </div>
          <div v-if="step.detail" class="smoke-step-detail-text">{{ step.detail }}</div>
          <div v-if="step.error" class="smoke-step-error">{{ step.error }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="smokeDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleSmokeTest">重新执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import 'echarts'
import { getOverview, getQualityScore, getTrend, getRadar } from '@/api/dashboard'
import { runSmokeTest, type SmokeStepResult, type SmokeTestResponse } from '@/api/smoke_test'
import { formatDate } from '@/utils/format'
import request from '@/api/request'

const router = useRouter()
const overview = ref<Record<string, any>>({})
const qualityScore = ref<Record<string, any>>({})
const trendDays = ref(7)
const alerts = ref<any[]>([])
const alertsLoading = ref(false)

// --- 冒烟测试 ---
const smokeRunning = ref(false)
const smokeSteps = ref<SmokeStepResult[]>([])
const smokeOverall = ref<'passed' | 'failed' | ''>('')
const smokeDialogVisible = ref(false)
const smokeResult = ref<SmokeTestResponse | null>(null)

const smokeActiveStep = computed(() => {
  const lastFinished = smokeSteps.value.filter(s => s.status === 'passed' || s.status === 'failed').length
  return lastFinished
})

function getStepStatus(step: SmokeStepResult): string {
  if (step.status === 'passed') return 'success'
  if (step.status === 'failed') return 'error'
  if (step.status === 'running') return 'process'
  return 'wait'
}

function getStepDescription(step: SmokeStepResult): string {
  if (step.status === 'passed') return `${step.duration_ms.toFixed(0)} ms`
  if (step.status === 'failed') return step.error || '执行失败'
  if (step.status === 'running') return '执行中...'
  return '等待中'
}

async function handleSmokeTest() {
  smokeRunning.value = true
  smokeSteps.value = [
    { step: 1, name: '虚拟设备初始化', status: 'running', duration_ms: 0, detail: '', error: null },
    { step: 2, name: '模拟购物事件', status: 'pending', duration_ms: 0, detail: '', error: null },
    { step: 3, name: '校验支付 Mock', status: 'pending', duration_ms: 0, detail: '', error: null },
  ]
  smokeOverall.value = ''
  try {
    const res = await runSmokeTest()
    smokeSteps.value = res.steps
    smokeOverall.value = res.status
    smokeResult.value = res
    smokeDialogVisible.value = true
    if (res.status === 'passed') {
      ElMessage.success(`冒烟测试全部通过，耗时 ${res.total_duration_ms.toFixed(0)} ms`)
    } else {
      ElMessage.warning('冒烟测试存在失败项，请查看详情')
    }
  } catch (e: any) {
    ElMessage.error('冒烟测试请求失败: ' + (e.message || '未知错误'))
    smokeSteps.value = smokeSteps.value.map(s => s.status === 'running' || s.status === 'pending' ? { ...s, status: 'failed' as const, error: '请求异常' } : s)
    smokeOverall.value = 'failed'
  } finally {
    smokeRunning.value = false
  }
}

const trendOption = ref({
  tooltip: { trigger: 'axis' },
  legend: { data: ['通过', '失败'] },
  xAxis: { type: 'category', data: [] as string[] },
  yAxis: { type: 'value' },
  series: [
    { name: '通过', type: 'line', data: [] as number[], smooth: true, areaStyle: { opacity: 0.15 } },
    { name: '失败', type: 'line', data: [] as number[], smooth: true, areaStyle: { opacity: 0.15 } },
  ],
})

const radarOption = ref({
  radar: {
    indicator: [] as { name: string; max: number }[],
  },
  series: [
    {
      type: 'radar',
      data: [
        {
          value: [] as number[],
          name: '质量维度',
        },
      ],
    },
  ],
})

async function fetchTrend() {
  try {
    const trend = await getTrend(trendDays.value)
    trendOption.value.xAxis.data = trend.dates || []
    trendOption.value.series[0].data = trend.passed || []
    trendOption.value.series[1].data = trend.failed || []
  } catch (e) {
    console.error('[Dashboard] fetchTrend failed:', e)
  }
}

async function fetchAlerts() {
  alertsLoading.value = true
  try {
    const res = await request.get('/dashboard/alerts')
    alerts.value = res.alerts || []
  } catch (e) {
    console.error('[Dashboard] fetchAlerts failed:', e)
    alerts.value = []
  } finally {
    alertsLoading.value = false
  }
}

onMounted(async () => {
  try {
    const [radar] = await Promise.all([getRadar()])
    radarOption.value.radar.indicator = radar.indicators || []
    radarOption.value.series[0].data[0].value = radar.values || []
  } catch (e) {
    console.error('[Dashboard] fetchRadar failed:', e)
  }

  await fetchTrend()

  try {
    overview.value = await getOverview()
  } catch (e) {
    console.error('[Dashboard] fetchOverview failed:', e)
  }

  try {
    qualityScore.value = await getQualityScore()
  } catch (e) {
    console.error('[Dashboard] fetchQualityScore failed:', e)
  }

  await fetchAlerts()
})
</script>

<style scoped lang="scss">
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  h2 {
    margin: 0;
    font-size: 20px;
  }
}
.clickable-card {
  cursor: pointer;
  transition: box-shadow 0.2s;
  &:hover { box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15); }
}
.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #1890ff;
}
.stat-sub {
  color: #999;
  margin-top: 8px;
}
.smoke-progress-card {
  :deep(.el-step__title) {
    font-size: 14px;
  }
  :deep(.el-step__description) {
    font-size: 12px;
  }
}
.smoke-result {
  .smoke-result-header {
    text-align: center;
    padding: 16px 0;
    &.smoke-passed { color: #67c23a; }
    &.smoke-failed { color: #f56c6c; }
    .smoke-result-title {
      font-size: 22px;
      font-weight: bold;
      margin-top: 8px;
    }
    .smoke-result-duration {
      font-size: 14px;
      color: #999;
      margin-top: 4px;
    }
  }
  .smoke-step-detail {
    padding: 8px 0;
    border-bottom: 1px dashed #eee;
    &:last-child { border-bottom: none; }
    .smoke-step-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .smoke-step-name {
      flex: 1;
      font-size: 14px;
    }
    .smoke-step-time {
      font-size: 12px;
      color: #999;
    }
    .smoke-step-detail-text {
      margin-left: 24px;
      font-size: 12px;
      color: #666;
      margin-top: 4px;
    }
    .smoke-step-error {
      margin-left: 24px;
      font-size: 12px;
      color: #f56c6c;
      margin-top: 4px;
    }
  }
}
</style>
