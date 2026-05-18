<template>
  <div class="health-score-page">
    <div class="page-header">
      <h2>质量健康评分</h2>
      <div class="header-actions">
        <el-select v-model="timeRange" size="small" style="width: 100px" @change="loadTrend">
          <el-option label="7 天" :value="7" />
          <el-option label="30 天" :value="30" />
          <el-option label="90 天" :value="90" />
        </el-select>
        <el-button :icon="Refresh" circle size="small" @click="loadAll" />
      </div>
    </div>

    <!-- 顶部：健康分 + 发布门禁 -->
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="12">
        <el-card shadow="hover">
          <div class="score-card">
            <div class="score-gauge">
              <div class="score-number" :class="scoreClass">{{ score?.overall_score ?? '-' }}</div>
              <div class="score-label">质量健康分</div>
            </div>
            <div class="score-bar">
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: (score?.overall_score || 0) + '%', background: scoreColor }" />
                <div class="bar-threshold" :style="{ left: (score?.release_threshold || 80) + '%' }">
                  <span class="threshold-label">发布线 {{ score?.release_threshold || 80 }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <div class="gate-card">
            <el-icon :size="48" :color="gate?.release_allowed ? '#67c23a' : '#f56c6c'">
              <CircleCheckFilled v-if="gate?.release_allowed" />
              <CircleCloseFilled v-else />
            </el-icon>
            <div class="gate-info">
              <div class="gate-status" :style="{ color: gate?.release_allowed ? '#67c23a' : '#f56c6c' }">
                {{ gate?.release_allowed ? '允许发布' : '禁止发布' }}
              </div>
              <div class="gate-detail">
                当前 {{ gate?.overall_score ?? '-' }} 分，
                {{ gate?.release_allowed ? '已达到' : '未达到' }}发布阈值 {{ gate?.threshold ?? 80 }}
              </div>
              <div v-if="gate?.failing_dimensions?.length" class="gate-failing">
                <el-tag v-for="dim in gate.failing_dimensions" :key="dim" type="danger" size="small" style="margin-right: 4px">
                  {{ dim }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 中部：7 维雷达图 + 维度明细 -->
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="10">
        <el-card shadow="hover">
          <template #header>7 维质量雷达</template>
          <v-chart :option="radarOption" style="height: 320px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card shadow="hover">
          <template #header>维度明细</template>
          <div v-for="dim in score?.dimensions" :key="dim.key" class="dimension-row">
            <div class="dim-info">
              <span class="dim-name">{{ dim.name }}</span>
              <span class="dim-weight">权重 {{ (dim.weight * 100).toFixed(0) }}%</span>
            </div>
            <div class="dim-bar">
              <el-progress
                :percentage="dim.value"
                :color="dimColor(dim.status)"
                :stroke-width="18"
                :text-inside="true"
              />
            </div>
            <div class="dim-score">
              <el-tag :type="dimTagType(dim.status)" size="small">{{ dim.score.toFixed(1) }}</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部：趋势线 -->
    <el-card shadow="hover">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>健康分趋势</span>
          <el-radio-group v-model="timeRange" size="small" @change="loadTrend">
            <el-radio-button :value="7">7 天</el-radio-button>
            <el-radio-button :value="30">30 天</el-radio-button>
            <el-radio-button :value="90">90 天</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <v-chart :option="trendOption" style="height: 280px" autoresize />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Refresh, CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent, RadarComponent } from 'echarts/components'
import { useHealthStore } from '@/stores/health'

use([CanvasRenderer, RadarChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, RadarComponent])

const healthStore = useHealthStore()
const timeRange = ref(7)

const score = computed(() => healthStore.currentScore)
const gate = computed(() => healthStore.releaseGate)
const trend = computed(() => healthStore.trend)

const scoreClass = computed(() => {
  const s = score.value?.overall_score ?? 0
  if (s >= 90) return 'score-good'
  if (s >= 70) return 'score-warn'
  return 'score-bad'
})

const scoreColor = computed(() => {
  const s = score.value?.overall_score ?? 0
  if (s >= 90) return '#67c23a'
  if (s >= 70) return '#e6a23c'
  return '#f56c6c'
})

function dimColor(status: string): string {
  if (status === 'good') return '#67c23a'
  if (status === 'warn') return '#e6a23c'
  return '#f56c6c'
}

function dimTagType(status: string): string {
  if (status === 'good') return 'success'
  if (status === 'warn') return 'warning'
  return 'danger'
}

const radarOption = computed(() => {
  const dims = score.value?.dimensions || []
  return {
    tooltip: {},
    radar: {
      indicator: dims.map(d => ({ name: d.name, max: 100 })),
      radius: '65%',
    },
    series: [{
      type: 'radar',
      data: [{
        value: dims.map(d => d.value),
        name: '当前分数',
        areaStyle: { opacity: 0.15 },
        lineStyle: { width: 2 },
      }],
    }],
  }
})

const trendOption = computed(() => {
  const items = trend.value || []
  return {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: items.map(i => {
        const d = new Date(i.computed_at)
        return `${d.getMonth() + 1}/${d.getDate()}`
      }),
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      splitLine: { lineStyle: { type: 'dashed' } },
    },
    series: [{
      type: 'line',
      data: items.map(i => i.overall_score),
      smooth: true,
      lineStyle: { width: 2 },
      areaStyle: { opacity: 0.1 },
      markLine: {
        data: [{ yAxis: 80, name: '发布线', lineStyle: { color: '#f56c6c', type: 'dashed' } }],
        label: { formatter: '发布线 80' },
      },
    }],
  }
})

async function loadAll() {
  await Promise.all([
    healthStore.fetchHealthScore(),
    healthStore.fetchReleaseGate(),
    healthStore.fetchTrend(timeRange.value),
  ])
}

async function loadTrend() {
  await healthStore.fetchTrend(timeRange.value)
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped lang="scss">
.health-score-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    h2 { margin: 0; font-size: 20px; }
    .header-actions { display: flex; gap: 8px; align-items: center; }
  }
}

.score-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 0;
  .score-gauge { text-align: center; margin-bottom: 16px; }
  .score-number {
    font-size: 56px;
    font-weight: bold;
    line-height: 1;
    &.score-good { color: #67c23a; }
    &.score-warn { color: #e6a23c; }
    &.score-bad { color: #f56c6c; }
  }
  .score-label { font-size: 14px; color: #999; margin-top: 8px; }
  .score-bar { width: 100%; }
  .bar-track {
    position: relative;
    height: 12px;
    background: #f0f0f0;
    border-radius: 6px;
    overflow: visible;
  }
  .bar-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 0.6s ease;
  }
  .bar-threshold {
    position: absolute;
    top: -6px;
    width: 2px;
    height: 24px;
    background: #f56c6c;
    .threshold-label {
      position: absolute;
      top: -18px;
      left: 50%;
      transform: translateX(-50%);
      font-size: 11px;
      color: #f56c6c;
      white-space: nowrap;
    }
  }
}

.gate-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  .gate-info { flex: 1; }
  .gate-status { font-size: 24px; font-weight: bold; margin-bottom: 8px; }
  .gate-detail { font-size: 14px; color: #666; margin-bottom: 8px; }
  .gate-failing { margin-top: 8px; }
}

.dimension-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px dashed #f5f5f5;
  &:last-child { border-bottom: none; }
  .dim-info {
    width: 140px;
    .dim-name { font-size: 13px; font-weight: 500; }
    .dim-weight { display: block; font-size: 11px; color: #999; }
  }
  .dim-bar { flex: 1; }
  .dim-score { width: 50px; text-align: right; }
}
</style>
