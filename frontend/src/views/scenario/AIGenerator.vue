<template>
  <div class="ai-generator-page">
    <div class="page-header">
      <h2>AI 场景生成</h2>
      <el-button text @click="router.push('/scenarios')">返回场景工作台</el-button>
    </div>

    <el-row :gutter="16">
      <!-- AI 生成 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>自然语言生成场景</template>
          <el-form label-position="top">
            <el-form-item label="描述你想要的测试场景">
              <el-input
                v-model="description"
                type="textarea"
                :rows="4"
                placeholder="例如：测试货柜的扫码开门、取货、关门、自动扣款全流程"
              />
            </el-form-item>
            <el-button type="primary" @click="handleGenerate" :loading="generating" style="width: 100%">
              AI 生成场景
            </el-button>
          </el-form>

          <div v-if="generated" class="result-section">
            <el-divider />
            <div class="result-header">
              <span class="result-name">{{ generated.name }}</span>
              <el-tag size="small" type="success">AI 生成</el-tag>
            </div>
            <div class="result-desc">{{ generated.description }}</div>
            <el-steps :active="generated.steps.length" direction="vertical" :space="50" style="margin-top: 16px">
              <el-step v-for="step in generated.steps" :key="step.id" :title="step.description">
                <template #description>
                  <div class="step-detail">
                    <code>{{ step.action }}</code>
                    <span v-if="Object.keys(step.params).length > 0" class="step-params">{{ JSON.stringify(step.params) }}</span>
                  </div>
                </template>
              </el-step>
            </el-steps>
            <el-button type="success" style="margin-top: 16px" @click="saveGenerated">保存到场景模板</el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 订单回放 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>订单回放</template>
          <el-form label-position="top">
            <el-form-item label="输入订单 ID 回放真实场景">
              <el-input v-model="orderId" placeholder="如 ORD-20260515-001" />
            </el-form-item>
            <el-button type="primary" @click="handleReplay" :loading="replaying" style="width: 100%">
              回放场景
            </el-button>
          </el-form>

          <div v-if="replayResult" class="result-section">
            <el-divider />
            <div class="result-header">
              <span class="result-name">订单 {{ replayResult.order_id }}</span>
              <el-tag size="small">{{ replayResult.event_count }} 个事件</el-tag>
            </div>
            <div class="timeline">
              <div v-for="step in replayResult.steps" :key="step.id" class="timeline-item">
                <div class="timeline-dot" />
                <div class="timeline-content">
                  <div class="timeline-action">{{ step.description }}</div>
                  <div class="timeline-meta">
                    <code>{{ step.action }}</code>
                    <span v-if="step.timestamp">{{ step.timestamp }}</span>
                  </div>
                </div>
              </div>
            </div>
            <el-button type="success" style="margin-top: 16px" @click="saveReplay">保存为场景模板</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { generateScenario, replayOrder, type GeneratedScenario, type ReplayResult } from '@/api/scenario_ai'
import request from '@/api/request'

const router = useRouter()

const description = ref('')
const generating = ref(false)
const generated = ref<GeneratedScenario | null>(null)

const orderId = ref('')
const replaying = ref(false)
const replayResult = ref<ReplayResult | null>(null)

async function handleGenerate() {
  if (!description.value.trim()) return ElMessage.warning('请输入场景描述')
  generating.value = true
  try {
    generated.value = await generateScenario(description.value)
    ElMessage.success('场景已生成')
  } catch (e: any) {
    ElMessage.error(e.message || '生成失败')
  } finally {
    generating.value = false
  }
}

async function handleReplay() {
  if (!orderId.value.trim()) return ElMessage.warning('请输入订单 ID')
  replaying.value = true
  try {
    replayResult.value = await replayOrder(orderId.value)
    ElMessage.success(`回放完成，共 ${replayResult.value.event_count} 个事件`)
  } catch (e: any) {
    ElMessage.error(e.message || '回放失败')
  } finally {
    replaying.value = false
  }
}

async function saveGenerated() {
  if (!generated.value) return
  try {
    await request.post('/scenarios/templates', {
      name: generated.value.name,
      description: generated.value.description,
      steps: generated.value.steps,
      source: 'ai_generated',
    })
    ElMessage.success('已保存到场景模板')
    router.push('/scenarios')
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}

async function saveReplay() {
  if (!replayResult.value) return
  try {
    await request.post('/scenarios/templates', {
      name: `回放 - ${replayResult.value.order_id}`,
      description: `从订单 ${replayResult.value.order_id} 回放的场景`,
      steps: replayResult.value.steps,
      source: 'replay',
    })
    ElMessage.success('已保存到场景模板')
    router.push('/scenarios')
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}
</script>

<style scoped lang="scss">
.ai-generator-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    h2 { margin: 0; font-size: 20px; }
  }
}
.result-section {
  margin-top: 8px;
}
.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  .result-name { font-weight: 500; font-size: 16px; }
}
.result-desc { font-size: 13px; color: #666; }
.step-detail {
  code { font-size: 11px; color: #c7254e; }
  .step-params { display: block; font-size: 11px; color: #999; margin-top: 2px; }
}
.timeline {
  margin-top: 12px;
  padding-left: 20px;
  border-left: 2px solid #e4e7ed;
}
.timeline-item {
  position: relative;
  padding: 8px 0 8px 16px;
}
.timeline-dot {
  position: absolute;
  left: -25px;
  top: 12px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #409eff;
}
.timeline-action { font-weight: 500; font-size: 14px; }
.timeline-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
  margin-top: 2px;
  code { color: #c7254e; }
}
</style>
