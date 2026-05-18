<template>
  <div class="ai-copilot-page">
    <div class="page-header">
      <h2>AI 测试助手</h2>
    </div>

    <el-row :gutter="16">
      <!-- 故障分析器 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>故障分析器</template>
          <el-form label-position="top">
            <el-form-item label="测试结果 ID">
              <el-input-number v-model="analyzeId" :min="1" style="width: 100%" />
            </el-form-item>
            <el-button type="primary" @click="handleAnalyze" :loading="analyzing" style="width: 100%">分析故障</el-button>
          </el-form>
          <div v-if="analysis" class="result-section">
            <el-divider />
            <div class="result-item">
              <span class="label">根因分类:</span>
              <el-tag>{{ categoryLabel(analysis.category) }}</el-tag>
            </div>
            <div class="result-item">
              <span class="label">置信度:</span>
              <el-progress :percentage="Math.round(analysis.confidence * 100)" :stroke-width="12" />
            </div>
            <div class="result-item">
              <span class="label">根因:</span>
              <span class="value">{{ analysis.root_cause }}</span>
            </div>
            <div class="result-item">
              <span class="label">建议:</span>
              <span class="value suggestion">{{ analysis.suggestion }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 测试生成器 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>测试生成器</template>
          <el-form label-position="top">
            <el-form-item label="描述你想要测试的场景">
              <el-input v-model="genDescription" type="textarea" :rows="3" placeholder="例如：测试货柜扫码购物和支付流程" />
            </el-form-item>
            <div style="display: flex; gap: 8px">
              <el-button type="primary" @click="handleGenerateTest" :loading="generating" style="flex: 1">生成测试</el-button>
              <el-button @click="handleGenerateScenario" :loading="generatingScenario" style="flex: 1">生成场景</el-button>
            </div>
          </el-form>
          <div v-if="generated" class="result-section">
            <el-divider />
            <div class="result-item">
              <span class="label">预估耗时:</span>
              <span>{{ (generated.estimated_duration_ms / 1000).toFixed(1) }} 秒</span>
            </div>
            <div class="result-item">
              <span class="label">步骤:</span>
            </div>
            <el-steps :active="generated.steps.length" direction="vertical" :space="40">
              <el-step v-for="step in generated.steps" :key="step.id" :title="step.description" :description="step.action" />
            </el-steps>
          </div>
        </el-card>
      </el-col>

      <!-- 选择器修复 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>选择器自动修复</template>
          <el-form label-position="top">
            <el-form-item label="失效的选择器">
              <el-input v-model="brokenSelector" placeholder="#my-button 或 //div[@class='xxx']" />
            </el-form-item>
            <el-button type="primary" @click="handleFixSelector" :loading="fixing" style="width: 100%">修复建议</el-button>
          </el-form>
          <div v-if="selectorFix" class="result-section">
            <el-divider />
            <div class="result-item">
              <span class="label">类型:</span>
              <el-tag>{{ selectorFix.selector_type }}</el-tag>
            </div>
            <div class="result-item">
              <span class="label">建议替换:</span>
            </div>
            <div v-for="(fix, idx) in selectorFix.suggested_fixes" :key="idx" class="fix-item">
              <code>{{ fix.selector }}</code>
              <span class="fix-reason">{{ fix.reason }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  analyzeFailure,
  generateTest,
  fixSelector,
  generateScenario,
  type FailureAnalysis,
  type GeneratedTest,
  type SelectorFix,
} from '@/api/ai_copilot'

// Failure analysis
const analyzeId = ref(1)
const analyzing = ref(false)
const analysis = ref<FailureAnalysis | null>(null)

// Test generation
const genDescription = ref('')
const generating = ref(false)
const generatingScenario = ref(false)
const generated = ref<GeneratedTest | null>(null)

// Selector fix
const brokenSelector = ref('')
const fixing = ref(false)
const selectorFix = ref<SelectorFix | null>(null)

function categoryLabel(cat: string) {
  const labels: Record<string, string> = {
    mqtt_timeout: 'MQTT 超时',
    ai_misprediction: 'AI 误判',
    payment_failure: '支付失败',
    network_error: '网络错误',
    config_issue: '配置问题',
    data_corruption: '数据异常',
    unknown: '未知',
  }
  return labels[cat] || cat
}

async function handleAnalyze() {
  analyzing.value = true
  try {
    analysis.value = await analyzeFailure(analyzeId.value)
    ElMessage.success('分析完成')
  } catch (e: any) {
    ElMessage.error(e.message || '分析失败')
  } finally {
    analyzing.value = false
  }
}

async function handleGenerateTest() {
  if (!genDescription.value.trim()) return ElMessage.warning('请输入场景描述')
  generating.value = true
  try {
    generated.value = await generateTest(genDescription.value)
    ElMessage.success('生成完成')
  } catch (e: any) {
    ElMessage.error(e.message || '生成失败')
  } finally {
    generating.value = false
  }
}

async function handleGenerateScenario() {
  if (!genDescription.value.trim()) return ElMessage.warning('请输入场景描述')
  generatingScenario.value = true
  try {
    const res = await generateScenario(genDescription.value)
    ElMessage.success(`场景「${res.name}」已生成，可前往场景工作台查看`)
  } catch (e: any) {
    ElMessage.error(e.message || '生成失败')
  } finally {
    generatingScenario.value = false
  }
}

async function handleFixSelector() {
  if (!brokenSelector.value.trim()) return ElMessage.warning('请输入选择器')
  fixing.value = true
  try {
    selectorFix.value = await fixSelector(brokenSelector.value)
    ElMessage.success('修复建议已生成')
  } catch (e: any) {
    ElMessage.error(e.message || '修复失败')
  } finally {
    fixing.value = false
  }
}
</script>

<style scoped lang="scss">
.ai-copilot-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    h2 { margin: 0; font-size: 20px; }
  }
}
.result-section {
  margin-top: 12px;
}
.result-item {
  margin-bottom: 8px;
  .label {
    font-weight: 500;
    margin-right: 8px;
    color: #666;
  }
  .value {
    font-size: 13px;
  }
  .suggestion {
    color: #409eff;
    display: block;
    margin-top: 4px;
    line-height: 1.5;
  }
}
.fix-item {
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 6px;
  code {
    display: block;
    font-size: 12px;
    color: #c7254e;
    margin-bottom: 4px;
    word-break: break-all;
  }
  .fix-reason {
    font-size: 12px;
    color: #999;
  }
}
</style>
