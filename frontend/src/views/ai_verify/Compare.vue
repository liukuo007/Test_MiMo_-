<template>
  <div class="page">
    <div class="page-header">
      <h2>模型对比</h2>
      <el-button type="primary" @click="handleCompare" :loading="comparing">开始对比</el-button>
    </div>

    <el-card style="margin-bottom: 16px">
      <el-form :inline="true" :model="form" label-width="80px">
        <el-form-item label="模型A">
          <el-select v-model="form.model_a" placeholder="选择版本">
            <el-option v-for="v in versions" :key="v.id" :label="versionName(v.id)" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型B">
          <el-select v-model="form.model_b" placeholder="选择版本">
            <el-option v-for="v in versions" :key="v.id" :label="versionName(v.id)" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据集">
          <el-select v-model="form.dataset">
            <el-option label="small" value="small" />
            <el-option label="medium" value="medium" />
            <el-option label="large" value="large" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" v-if="result" style="margin-bottom: 16px">
      <el-col :span="8">
        <el-card>
          <template #header><span>模型 A: {{ versionName(form.model_a!) }}</span></template>
          <div class="metric-row"><span>准确率</span><span class="metric-val">{{ (result.model_a.accuracy * 100).toFixed(1) }}%</span></div>
          <div class="metric-row"><span>召回率</span><span class="metric-val">{{ (result.model_a.recall * 100).toFixed(1) }}%</span></div>
          <div class="metric-row"><span>平均延迟</span><span class="metric-val">{{ result.model_a.avg_latency_ms.toFixed(1) }}ms</span></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>模型 B: {{ versionName(form.model_b!) }}</span></template>
          <div class="metric-row"><span>准确率</span><span class="metric-val">{{ (result.model_b.accuracy * 100).toFixed(1) }}%</span></div>
          <div class="metric-row"><span>召回率</span><span class="metric-val">{{ (result.model_b.recall * 100).toFixed(1) }}%</span></div>
          <div class="metric-row"><span>平均延迟</span><span class="metric-val">{{ result.model_b.avg_latency_ms.toFixed(1) }}ms</span></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>差异</span></template>
          <div class="metric-row">
            <span>准确率变化</span>
            <span :class="['metric-val', result.delta.accuracy >= 0 ? 'positive' : 'negative']">
              {{ result.delta.accuracy >= 0 ? '+' : '' }}{{ (result.delta.accuracy * 100).toFixed(2) }}%
            </span>
          </div>
          <div class="metric-row">
            <span>召回率变化</span>
            <span :class="['metric-val', result.delta.recall >= 0 ? 'positive' : 'negative']">
              {{ result.delta.recall >= 0 ? '+' : '' }}{{ (result.delta.recall * 100).toFixed(2) }}%
            </span>
          </div>
          <div class="metric-row">
            <span>延迟变化</span>
            <span :class="['metric-val', result.delta.avg_latency_ms <= 0 ? 'positive' : 'negative']">
              {{ result.delta.avg_latency_ms >= 0 ? '+' : '' }}{{ result.delta.avg_latency_ms.toFixed(1) }}ms
            </span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="result">
      <el-alert
        :type="result.regression_detected ? 'error' : 'success'"
        :title="result.regression_detected ? '检测到回归' : '未检测到回归'"
        :description="result.recommendation"
        show-icon
        :closable="false"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getModelVersions, getAIModels } from '@/api/ai_verify'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const versions = ref<any[]>([])
const versionMap = ref<Record<number, string>>({})
const comparing = ref(false)
const form = ref({ model_a: null as number | null, model_b: null as number | null, dataset: 'medium' })
const result = ref<any>(null)

function versionName(id: number) {
  return versionMap.value[id] || `v${id}`
}

async function handleCompare() {
  if (!form.value.model_a || !form.value.model_b) {
    ElMessage.warning('请选择两个模型版本')
    return
  }
  comparing.value = true
  try {
    const va = versions.value.find(v => v.id === form.value.model_a)
    const vb = versions.value.find(v => v.id === form.value.model_b)
    result.value = await request.post('/ai/compare', {
      model_a_version: va?.version || 'v2.0',
      model_b_version: vb?.version || 'v3.0',
      dataset_path: form.value.dataset,
    })
  } finally {
    comparing.value = false
  }
}

onMounted(async () => {
  const models = await getAIModels() as any
  for (const m of (Array.isArray(models) ? models : [])) {
    const vers = await getModelVersions(m.id) as any
    for (const v of (Array.isArray(vers) ? vers : [])) {
      versions.value.push(v)
      versionMap.value[v.id] = `${m.name} ${v.version}`
    }
  }
})
</script>

<style scoped lang="scss">
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.metric-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #ebeef5; }
.metric-row:last-child { border-bottom: none; }
.metric-val { font-weight: bold; }
.positive { color: #67c23a; }
.negative { color: #f56c6c; }
</style>
