<template>
  <div class="page">
    <div class="page-header">
      <h2>质量门禁</h2>
      <el-button type="primary" @click="handleSave">保存规则</el-button>
    </div>

    <el-card style="margin-bottom: 16px">
      <template #header><span>门禁规则配置</span></template>
      <el-form label-width="160px" style="max-width: 700px">
        <el-divider content-position="left">自动化指标</el-divider>
        <el-form-item label="自动化用例通过率">
          <el-slider v-model="rules.auto_pass_rate" :min="80" :max="100" :step="1" show-input :format-tooltip="(v: number) => v + '%'" />
        </el-form-item>
        <el-form-item label="自动化覆盖率">
          <el-slider v-model="rules.auto_coverage" :min="50" :max="100" :step="1" show-input :format-tooltip="(v: number) => v + '%'" />
        </el-form-item>

        <el-divider content-position="left">AI 指标</el-divider>
        <el-form-item label="AI 识别准确率">
          <el-slider v-model="rules.ai_accuracy" :min="85" :max="100" :step="0.5" show-input :format-tooltip="(v: number) => v + '%'" />
        </el-form-item>
        <el-form-item label="AI 推理延迟上限">
          <el-input-number v-model="rules.ai_latency_max" :min="10" :max="200" :step="5" /> ms
        </el-form-item>

        <el-divider content-position="left">性能指标</el-divider>
        <el-form-item label="API 响应时间 P99">
          <el-input-number v-model="rules.api_p99_ms" :min="100" :max="10000" :step="100" /> ms
        </el-form-item>
        <el-form-item label="设备在线率">
          <el-slider v-model="rules.device_online_rate" :min="90" :max="100" :step="0.5" show-input :format-tooltip="(v: number) => v + '%'" />
        </el-form-item>

        <el-divider content-position="left">发布指标</el-divider>
        <el-form-item label="缺陷逃逸率上限">
          <el-slider v-model="rules.defect_escape_rate" :min="0" :max="10" :step="0.1" show-input :format-tooltip="(v: number) => v + '%'" />
        </el-form-item>
        <el-form-item label="发布成功率">
          <el-slider v-model="rules.release_success_rate" :min="90" :max="100" :step="0.5" show-input :format-tooltip="(v: number) => v + '%'" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header><span>当前门禁状态</span></template>
      <el-table :data="gateStatus" stripe>
        <el-table-column prop="rule" label="规则名称" />
        <el-table-column prop="threshold" label="阈值" width="120" />
        <el-table-column prop="current" label="当前值" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.passed ? 'success' : 'danger'" size="small">{{ row.passed ? '通过' : '未达标' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getQualityGateRules, updateQualityGateRules, getQualityGateStatus } from '@/api/quality_gate'

const rules = ref({
  auto_pass_rate: 95, auto_coverage: 80, ai_accuracy: 95, ai_latency_max: 50,
  api_p99_ms: 2000, device_online_rate: 99, defect_escape_rate: 2, release_success_rate: 98,
})

const gateStatus = ref<any[]>([])

onMounted(async () => {
  try {
    const [rulesData, statusData] = await Promise.all([
      getQualityGateRules(),
      getQualityGateStatus(),
    ])
    // rulesData is a list of {id, name, metric, threshold, operator, is_active}
    if (Array.isArray(rulesData)) {
      for (const rule of rulesData) {
        if (rule.metric && rule.threshold != null && rule.metric in rules.value) {
          ;(rules.value as any)[rule.metric] = Number(rule.threshold)
        }
      }
    }
    gateStatus.value = Array.isArray(statusData) ? statusData : (statusData as any)?.items || []
  } catch {
    // fallback to defaults
  }
})

async function handleSave() {
  try {
    await updateQualityGateRules(rules.value)
    const statusData = await getQualityGateStatus()
    gateStatus.value = statusData as any[]
    ElMessage.success('门禁规则已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}
</script>

<style scoped lang="scss">
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
