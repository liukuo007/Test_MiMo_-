<template>
  <div class="page">
    <div class="page-header">
      <h2>AI 模型评测</h2>
      <el-button type="primary" @click="showCreate = true">新建评测</el-button>
    </div>

    <el-table :data="evaluations" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="model_version_id" label="模型版本" width="120">
        <template #default="{ row }">
          {{ versionName(row.model_version_id) }}
        </template>
      </el-table-column>
      <el-table-column prop="dataset_name" label="数据集" width="120" />
      <el-table-column prop="accuracy" label="准确率" width="100">
        <template #default="{ row }">
          <span :style="{ color: row.accuracy >= 0.95 ? '#67c23a' : row.accuracy >= 0.9 ? '#e6a23c' : '#f56c6c' }">
            {{ (row.accuracy * 100).toFixed(1) }}%
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="recall" label="召回率" width="100">
        <template #default="{ row }">{{ row.recall ? (row.recall * 100).toFixed(1) + '%' : '-' }}</template>
      </el-table-column>
      <el-table-column prop="f1_score" label="F1" width="100">
        <template #default="{ row }">{{ row.f1_score ? (row.f1_score * 100).toFixed(1) + '%' : '-' }}</template>
      </el-table-column>
      <el-table-column prop="avg_latency_ms" label="平均延迟" width="100">
        <template #default="{ row }">{{ row.avg_latency_ms ? row.avg_latency_ms.toFixed(1) + 'ms' : '-' }}</template>
      </el-table-column>
      <el-table-column prop="total_samples" label="总样本" width="80" />
      <el-table-column prop="failed_samples" label="失败数" width="80">
        <template #default="{ row }">
          <span :style="{ color: row.failed_samples > 0 ? '#f56c6c' : '#67c23a' }">{{ row.failed_samples }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="评测时间" width="180" />
    </el-table>

    <el-dialog v-model="showCreate" title="新建 AI 评测" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="模型版本">
          <el-select v-model="form.model_version_id">
            <el-option v-for="v in versions" :key="v.id" :label="`v${v.id} - ${v.version}`" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据集">
          <el-select v-model="form.dataset_name">
            <el-option label="small (100样本)" value="small" />
            <el-option label="medium (500样本)" value="medium" />
            <el-option label="large (2000样本)" value="large" />
          </el-select>
        </el-form-item>
        <el-form-item label="准确率阈值">
          <el-slider v-model="form.threshold" :min="0.8" :max="1" :step="0.01" show-input :format-tooltip="(v: number) => (v * 100).toFixed(0) + '%'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">开始评测</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getEvaluations, createEvaluation, getModelVersions, getAIModels } from '@/api/ai_verify'
import { ElMessage } from 'element-plus'

const evaluations = ref<any[]>([])
const versions = ref<any[]>([])
const showCreate = ref(false)
const form = ref({ model_version_id: null as number | null, dataset_name: 'medium', threshold: 0.9 })

const versionMap = ref<Record<number, string>>({})
function versionName(id: number) {
  return versionMap.value[id] || `v${id}`
}

async function loadData() {
  try {
    const evalRes = await getEvaluations()
    evaluations.value = Array.isArray(evalRes) ? evalRes : (evalRes as any)?.items || []
    const models = await getAIModels() as any
    for (const m of (Array.isArray(models) ? models : [])) {
      try {
        const vers = await getModelVersions(m.id) as any
        for (const v of (Array.isArray(vers) ? vers : [])) {
          versions.value.push(v)
          versionMap.value[v.id] = `${m.name} ${v.version}`
        }
      } catch {
        // skip failed version fetch
      }
    }
  } catch {
    evaluations.value = []
  }
}

async function handleCreate() {
  if (!form.value.model_version_id) {
    ElMessage.warning('请选择模型版本')
    return
  }
  await createEvaluation(form.value)
  ElMessage.success('评测任务已创建')
  showCreate.value = false
  loadData()
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
