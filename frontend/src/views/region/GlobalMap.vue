<template>
  <div class="global-map-page">
    <div class="page-header">
      <h2>全球运营</h2>
      <el-button type="primary" @click="showCreate">添加区域</el-button>
    </div>

    <!-- 区域卡片 -->
    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="6" v-for="region in regions" :key="region.id">
        <el-card shadow="hover" class="region-card" @click="viewRegion(region)">
          <div class="region-header">
            <span class="region-code">{{ region.code }}</span>
            <el-tag :type="region.status === 'active' ? 'success' : region.status === 'degraded' ? 'warning' : 'info'" size="small">
              {{ region.status === 'active' ? '活跃' : region.status === 'degraded' ? '降级' : '停用' }}
            </el-tag>
          </div>
          <div class="region-name">{{ region.name }}</div>
          <div class="region-score" :style="{ color: getScoreColor(mapData[region.code]?.overall_score) }">
            {{ mapData[region.code]?.overall_score?.toFixed(0) ?? '-' }}
          </div>
          <div class="region-label">质量评分</div>
          <div class="region-metrics" v-if="mapData[region.code]?.metrics">
            <div v-for="(val, key) in mapData[region.code].metrics" :key="key" class="metric-item">
              <span class="metric-key">{{ metricLabel(key) }}</span>
              <span class="metric-val">{{ formatMetric(key, val) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6" v-if="regions.length === 0">
        <el-card shadow="hover" style="text-align: center; padding: 40px 0; color: #999">
          暂无区域，点击"添加区域"创建
        </el-card>
      </el-col>
    </el-row>

    <!-- 全球质量地图 -->
    <el-card shadow="hover">
      <template #header>全球质量分布</template>
      <div v-if="regions.length > 0" style="height: 400px">
        <v-chart :option="mapChartOption" autoresize />
      </div>
      <div v-else style="text-align: center; color: #999; padding: 60px 0">暂无数据</div>
    </el-card>

    <!-- 区域详情弹窗 -->
    <el-dialog v-model="detailVisible" :title="detailRegion?.name + ' - 区域详情'" width="600px">
      <div v-if="detailRegion && regionHealth">
        <el-descriptions :column="2" border size="small" style="margin-bottom: 16px">
          <el-descriptions-item label="区域代码">{{ detailRegion.code }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ detailRegion.status }}</el-descriptions-item>
          <el-descriptions-item label="MQTT Broker">{{ detailRegion.mqtt_broker_url || '-' }}</el-descriptions-item>
          <el-descriptions-item label="支付端点">{{ detailRegion.payment_endpoint || '-' }}</el-descriptions-item>
          <el-descriptions-item label="AI 端点">{{ detailRegion.ai_endpoint || '-' }}</el-descriptions-item>
          <el-descriptions-item label="质量评分">
            <span :style="{ color: getScoreColor(regionHealth.overall_score), fontWeight: 'bold', fontSize: '18px' }">
              {{ regionHealth.overall_score?.toFixed(0) ?? '-' }}
            </span>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="regionHealth.metrics">
          <div v-for="(val, key) in regionHealth.metrics" :key="key" class="detail-metric">
            <span class="dm-label">{{ metricLabel(key) }}</span>
            <el-progress :percentage="typeof val === 'number' && val <= 100 ? val : 100" :color="getScoreColor(val)" />
            <span class="dm-value">{{ formatMetric(key, val) }}</span>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 创建区域弹窗 -->
    <el-dialog v-model="createVisible" title="添加区域" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="区域代码" required>
          <el-input v-model="createForm.code" placeholder="如 SG / US / EU / JP" />
        </el-form-item>
        <el-form-item label="区域名称" required>
          <el-input v-model="createForm.name" />
        </el-form-item>
        <el-form-item label="MQTT Broker">
          <el-input v-model="createForm.mqtt_broker_url" />
        </el-form-item>
        <el-form-item label="支付端点">
          <el-input v-model="createForm.payment_endpoint" />
        </el-form-item>
        <el-form-item label="AI 端点">
          <el-input v-model="createForm.ai_endpoint" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
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
  getRegions,
  createRegion,
  getRegionHealth,
  getGlobalQualityMap,
  type Region,
  type RegionHealth,
  type GlobalMapItem,
} from '@/api/region'

const regions = ref<Region[]>([])
const mapData = ref<Record<string, GlobalMapItem>>({})

const detailVisible = ref(false)
const detailRegion = ref<Region | null>(null)
const regionHealth = ref<RegionHealth | null>(null)

const createVisible = ref(false)
const createForm = ref({
  code: '',
  name: '',
  mqtt_broker_url: '',
  payment_endpoint: '',
  ai_endpoint: '',
  description: '',
})

function getScoreColor(score?: number) {
  if (score == null) return '#999'
  if (score >= 80) return '#67c23a'
  if (score >= 50) return '#e6a23c'
  return '#f56c6c'
}

function metricLabel(key: string) {
  const labels: Record<string, string> = {
    health_score: '健康分',
    device_online_rate: '设备在线率',
    device_count: '设备数',
    pass_rate: '通过率',
    latency: '延迟',
  }
  return labels[key] || key
}

function formatMetric(key: string, val: number) {
  if (key === 'device_count') return `${val} 台`
  if (key === 'latency') return `${val.toFixed(0)} ms`
  return `${val.toFixed(1)}%`
}

// Simple bar chart for regions since we don't have world map geoJSON
const mapChartOption = computed(() => {
  const items = regions.value.map(r => ({
    name: r.name,
    value: mapData.value[r.code]?.overall_score ?? 0,
  }))
  return {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: items.map(i => i.name),
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      name: '质量评分',
    },
    series: [{
      type: 'bar',
      data: items.map(i => ({
        value: i.value,
        itemStyle: { color: getScoreColor(i.value) },
      })),
      barWidth: '40%',
      label: { show: true, position: 'top', formatter: '{c}' },
    }],
  }
})

async function loadData() {
  try {
    regions.value = await getRegions()
    const mapItems = await getGlobalQualityMap()
    mapData.value = {}
    for (const item of mapItems) {
      mapData.value[item.code] = item
    }
  } catch (e) {
    console.error(e)
  }
}

async function viewRegion(region: Region) {
  detailRegion.value = region
  try {
    regionHealth.value = await getRegionHealth(region.id)
    detailVisible.value = true
  } catch (e: any) {
    ElMessage.error(e.message || '加载失败')
  }
}

function showCreate() {
  createForm.value = { code: '', name: '', mqtt_broker_url: '', payment_endpoint: '', ai_endpoint: '', description: '' }
  createVisible.value = true
}

async function handleCreate() {
  if (!createForm.value.code || !createForm.value.name) return ElMessage.warning('请填写代码和名称')
  try {
    await createRegion(createForm.value)
    createVisible.value = false
    ElMessage.success('创建成功')
    loadData()
  } catch (e: any) {
    ElMessage.error(e.message || '创建失败')
  }
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.global-map-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    h2 { margin: 0; font-size: 20px; }
  }
}
.region-card {
  cursor: pointer;
  transition: all 0.2s;
  &:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.12); }
  .region-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  .region-code { font-size: 24px; font-weight: bold; color: #409eff; }
  .region-name { font-size: 14px; color: #666; margin-bottom: 12px; }
  .region-score { font-size: 36px; font-weight: bold; text-align: center; line-height: 1; }
  .region-label { text-align: center; font-size: 12px; color: #999; margin: 4px 0 12px; }
  .region-metrics { border-top: 1px dashed #eee; padding-top: 8px; }
  .metric-item {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    padding: 2px 0;
    .metric-key { color: #999; }
    .metric-val { font-weight: 500; }
  }
}
.detail-metric {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  .dm-label { width: 80px; font-size: 13px; color: #666; }
  :deep(.el-progress) { flex: 1; }
  .dm-value { width: 60px; text-align: right; font-size: 13px; font-weight: 500; }
}
</style>
