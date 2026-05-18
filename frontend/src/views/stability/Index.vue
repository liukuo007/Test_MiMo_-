<template>
  <div class="stability-page">
    <div class="page-header">
      <h2>稳定性治理</h2>
      <div style="display: flex; gap: 8px">
        <el-button type="primary" @click="handleDetect" :loading="detecting">执行检测</el-button>
        <el-button :icon="Refresh" circle @click="loadAll" />
      </div>
    </div>

    <!-- 顶部统计 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>稳定性评分</template>
          <div class="stat-value" :style="{ color: summary.overall_stability_score >= 80 ? '#67c23a' : summary.overall_stability_score >= 50 ? '#e6a23c' : '#f56c6c' }">
            {{ summary.overall_stability_score.toFixed(0) }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>活跃 Flaky 用例</template>
          <div class="stat-value" style="color: #e6a23c">{{ summary.active_flaky }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>已解决</template>
          <div class="stat-value" style="color: #67c23a">{{ summary.resolved_flaky }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>总计 Flaky</template>
          <div class="stat-value">{{ summary.total_flaky }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 故障聚类 + 趋势 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>故障聚类</template>
          <div v-if="summary.clusters.length === 0" style="text-align: center; color: #999; padding: 40px 0">暂无数据</div>
          <div v-else style="height: 280px">
            <v-chart :option="clusterOption" autoresize />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>稳定性趋势</template>
          <div v-if="summary.trends.length === 0" style="text-align: center; color: #999; padding: 40px 0">暂无数据</div>
          <div v-else class="trend-cards">
            <div v-for="t in summary.trends" :key="t.id" class="trend-item">
              <div class="trend-label">{{ t.dimension }}: {{ t.dimension_value }}</div>
              <el-progress :percentage="t.stability_score" :color="t.stability_score >= 80 ? '#67c23a' : t.stability_score >= 50 ? '#e6a23c' : '#f56c6c'" :stroke-width="20" />
              <div class="trend-meta">
                <span>通过率 {{ t.pass_rate }}%</span>
                <span>Flaky {{ t.flaky_rate }}%</span>
                <span>共 {{ t.total_runs }} 次</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Flaky 用例列表 -->
    <el-card shadow="hover">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>Flaky 用例列表</span>
          <el-radio-group v-model="flakyFilter" size="small" @change="loadFlaky">
            <el-radio-button value="">全部</el-radio-button>
            <el-radio-button value="active">活跃</el-radio-button>
            <el-radio-button value="resolved">已解决</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <el-table :data="flakyList" stripe v-loading="flakyLoading">
        <el-table-column prop="test_case_name" label="用例名称" show-overflow-tooltip />
        <el-table-column prop="flaky_rate" label="Flaky 率" width="120">
          <template #default="{ row }">
            <el-progress :percentage="Math.round(row.flaky_rate * 100)" :color="row.flaky_rate > 0.3 ? '#f56c6c' : '#e6a23c'" :stroke-width="12" />
          </template>
        </el-table-column>
        <el-table-column prop="pattern.type" label="模式" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'warning' : 'success'" size="small">
              {{ row.status === 'active' ? '活跃' : '已解决' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detected_at" label="检测时间" width="170">
          <template #default="{ row }">{{ formatDate(row.detected_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button v-if="row.status === 'active'" size="small" type="success" @click="handleResolve(row)">标记解决</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import 'echarts'
import {
  getStabilitySummary,
  getFlakyList,
  resolveFlaky,
  triggerDetection,
  type FlakyTestCase,
  type StabilitySummary,
} from '@/api/stability'
import { formatDate } from '@/utils/format'

const detecting = ref(false)
const summary = ref<StabilitySummary>({
  total_flaky: 0,
  active_flaky: 0,
  resolved_flaky: 0,
  overall_stability_score: 100,
  clusters: [],
  trends: [],
})

const flakyFilter = ref('')
const flakyLoading = ref(false)
const flakyList = ref<FlakyTestCase[]>([])

const clusterOption = computed(() => {
  const clusters = summary.value.clusters || []
  return {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: clusters.map(c => ({
        name: c.cluster_name,
        value: c.sample_count,
      })),
      label: { formatter: '{b}: {d}%' },
    }],
  }
})

async function loadAll() {
  try {
    summary.value = await getStabilitySummary()
  } catch (e) {
    console.error(e)
  }
  loadFlaky()
}

async function loadFlaky() {
  flakyLoading.value = true
  try {
    flakyList.value = await getFlakyList(flakyFilter.value || undefined)
  } catch (e) {
    console.error(e)
  } finally {
    flakyLoading.value = false
  }
}

async function handleDetect() {
  detecting.value = true
  try {
    const res = await triggerDetection()
    ElMessage.success(`检测完成: ${res.flaky_detected} 个 Flaky, ${res.clusters_found} 个聚类`)
    loadAll()
  } catch (e: any) {
    ElMessage.error(e.message || '检测失败')
  } finally {
    detecting.value = false
  }
}

async function handleResolve(row: FlakyTestCase) {
  try {
    await resolveFlaky(row.id)
    ElMessage.success('已标记为解决')
    loadAll()
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  }
}

onMounted(loadAll)
</script>

<style scoped lang="scss">
.stability-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    h2 { margin: 0; font-size: 20px; }
  }
}
.stat-value {
  font-size: 36px;
  font-weight: bold;
  text-align: center;
  color: #1890ff;
}
.trend-cards {
  padding: 8px 0;
}
.trend-item {
  padding: 12px 0;
  border-bottom: 1px dashed #f5f5f5;
  &:last-child { border-bottom: none; }
  .trend-label { font-weight: 500; margin-bottom: 8px; font-size: 14px; }
  .trend-meta {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: #999;
    margin-top: 4px;
  }
}
</style>
