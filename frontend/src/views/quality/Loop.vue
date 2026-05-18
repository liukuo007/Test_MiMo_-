<template>
  <div class="quality-loop-page">
    <div class="page-header">
      <h2>质量闭环</h2>
      <div style="display: flex; gap: 8px">
        <el-button type="primary" @click="showCreateRule">新建规则</el-button>
        <el-button @click="handleEvaluate" :loading="evaluating">立即评估</el-button>
      </div>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <!-- 规则列表 -->
      <el-col :span="10">
        <el-card shadow="hover">
          <template #header>闭环规则</template>
          <div v-if="rules.length === 0" style="text-align: center; color: #999; padding: 20px">暂无规则</div>
          <div
            v-for="rule in rules"
            :key="rule.id"
            class="rule-item"
            :class="{ active: selectedRule?.id === rule.id }"
            @click="selectedRule = rule"
          >
            <div class="rule-header">
              <span class="rule-name">{{ rule.name }}</span>
              <el-switch v-model="rule.enabled" size="small" @change="toggleRule(rule)" @click.stop />
            </div>
            <div class="rule-condition">
              {{ metricLabel(rule.trigger_metric) }} {{ rule.operator }} {{ rule.threshold }}
            </div>
            <div class="rule-actions">
              <el-button size="small" @click.stop="handleTrigger(rule)" :loading="triggeringId === rule.id">手动触发</el-button>
              <el-button size="small" type="danger" @click.stop="handleDeleteRule(rule)">删除</el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 执行历史 -->
      <el-col :span="14">
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>执行历史</span>
              <el-select v-model="execFilter" size="small" style="width: 120px" @change="loadExecutions">
                <el-option label="全部" value="" />
                <el-option label="运行中" value="running" />
                <el-option label="已完成" value="completed" />
                <el-option label="失败" value="failed" />
              </el-select>
            </div>
          </template>
          <el-table :data="executions" stripe v-loading="execLoading">
            <el-table-column prop="rule_name" label="规则" width="140" />
            <el-table-column prop="trigger_value" label="触发值" width="80" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="execStatusTag(row.status)" size="small">{{ execStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="进度" width="120">
              <template #default="{ row }">
                <el-progress :percentage="row.total_steps > 0 ? Math.round(row.current_step / row.total_steps * 100) : 0" :stroke-width="8" />
              </template>
            </el-table-column>
            <el-table-column prop="defect_id" label="关联缺陷" width="100">
              <template #default="{ row }">
                <el-link v-if="row.defect_id" type="primary" @click="router.push(`/defects/${row.defect_id}`)">#{{ row.defect_id }}</el-link>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="started_at" label="开始时间" width="170">
              <template #default="{ row }">{{ formatDate(row.started_at) }}</template>
            </el-table-column>
            <el-table-column label="详情" width="80">
              <template #default="{ row }">
                <el-button size="small" @click="showExecutionDetail(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建规则弹窗 -->
    <el-dialog v-model="ruleDialogVisible" title="新建闭环规则" width="500px">
      <el-form :model="ruleForm" label-width="100px">
        <el-form-item label="规则名称" required>
          <el-input v-model="ruleForm.name" />
        </el-form-item>
        <el-form-item label="触发指标">
          <el-select v-model="ruleForm.trigger_metric" style="width: 100%">
            <el-option label="健康分" value="health_score" />
            <el-option label="通过率" value="pass_rate" />
            <el-option label="Flaky 数" value="flaky_rate" />
          </el-select>
        </el-form-item>
        <el-form-item label="条件">
          <div style="display: flex; gap: 8px">
            <el-select v-model="ruleForm.operator" style="width: 80px">
              <el-option label="<" value="<" />
              <el-option label=">" value=">" />
              <el-option label="<=" value="<=" />
              <el-option label=">=" value=">=" />
            </el-select>
            <el-input-number v-model="ruleForm.threshold" style="flex: 1" />
          </div>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="ruleForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateRule">创建</el-button>
      </template>
    </el-dialog>

    <!-- 执行详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="执行详情" width="600px">
      <div v-if="detailExecution">
        <el-descriptions :column="2" border size="small" style="margin-bottom: 16px">
          <el-descriptions-item label="规则">{{ detailExecution.rule_name }}</el-descriptions-item>
          <el-descriptions-item label="触发值">{{ detailExecution.trigger_value }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="execStatusTag(detailExecution.status)" size="small">{{ execStatusLabel(detailExecution.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="关联缺陷">
            <el-link v-if="detailExecution.defect_id" type="primary">#{{ detailExecution.defect_id }}</el-link>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="detailExecution.steps_log">
          <div v-for="step in detailExecution.steps_log.steps" :key="step.step" class="step-row">
            <el-icon :size="16" :color="step.status === 'completed' ? '#67c23a' : step.status === 'failed' ? '#f56c6c' : '#909399'">
              <CircleCheckFilled v-if="step.status === 'completed'" />
              <CircleCloseFilled v-else-if="step.status === 'failed'" />
              <InfoFilled v-else />
            </el-icon>
            <span class="step-action">{{ step.action }}</span>
            <span class="step-detail">{{ step.detail }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { CircleCheckFilled, CircleCloseFilled, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getLoopRules,
  createLoopRule,
  updateLoopRule,
  deleteLoopRule,
  triggerRule,
  getLoopExecutions,
  evaluateRules,
  type LoopRule,
  type LoopExecution,
} from '@/api/quality_loop'
import { formatDate } from '@/utils/format'

const router = useRouter()
const rules = ref<LoopRule[]>([])
const selectedRule = ref<LoopRule | null>(null)
const executions = ref<LoopExecution[]>([])
const execLoading = ref(false)
const execFilter = ref('')
const evaluating = ref(false)
const triggeringId = ref<number | null>(null)

const ruleDialogVisible = ref(false)
const ruleForm = ref({
  name: '',
  trigger_metric: 'health_score',
  threshold: 80,
  operator: '<',
  enabled: true,
})

const detailDialogVisible = ref(false)
const detailExecution = ref<LoopExecution | null>(null)

function metricLabel(m: string) {
  return { health_score: '健康分', pass_rate: '通过率', flaky_rate: 'Flaky 数', crash_rate: '崩溃率' }[m] || m
}
function execStatusLabel(s: string) {
  return { running: '运行中', completed: '已完成', failed: '失败', cancelled: '已取消' }[s] || s
}
function execStatusTag(s: string) {
  return { running: 'info', completed: 'success', failed: 'danger', cancelled: 'warning' }[s] || 'info'
}

async function loadRules() {
  try {
    rules.value = await getLoopRules()
  } catch (e) {
    console.error(e)
  }
}

async function loadExecutions() {
  execLoading.value = true
  try {
    const params: any = {}
    if (selectedRule.value) params.rule_id = selectedRule.value.id
    if (execFilter.value) params.status = execFilter.value
    executions.value = await getLoopExecutions(params)
  } catch (e) {
    console.error(e)
  } finally {
    execLoading.value = false
  }
}

function showCreateRule() {
  ruleForm.value = { name: '', trigger_metric: 'health_score', threshold: 80, operator: '<', enabled: true }
  ruleDialogVisible.value = true
}

async function handleCreateRule() {
  if (!ruleForm.value.name) return ElMessage.warning('请输入规则名称')
  try {
    await createLoopRule(ruleForm.value)
    ruleDialogVisible.value = false
    ElMessage.success('创建成功')
    loadRules()
  } catch (e: any) {
    ElMessage.error(e.message || '创建失败')
  }
}

async function toggleRule(rule: LoopRule) {
  try {
    await updateLoopRule(rule.id, { enabled: rule.enabled })
  } catch (e: any) {
    ElMessage.error(e.message || '更新失败')
    rule.enabled = !rule.enabled
  }
}

async function handleDeleteRule(rule: LoopRule) {
  await ElMessageBox.confirm(`确定删除规则「${rule.name}」？`, '提示', { type: 'warning' })
  try {
    await deleteLoopRule(rule.id)
    ElMessage.success('已删除')
    if (selectedRule.value?.id === rule.id) selectedRule.value = null
    loadRules()
    loadExecutions()
  } catch (e: any) {
    ElMessage.error(e.message || '删除失败')
  }
}

async function handleTrigger(rule: LoopRule) {
  triggeringId.value = rule.id
  try {
    await triggerRule(rule.id)
    ElMessage.success('触发成功')
    loadExecutions()
  } catch (e: any) {
    ElMessage.error(e.message || '触发失败')
  } finally {
    triggeringId.value = null
  }
}

async function handleEvaluate() {
  evaluating.value = true
  try {
    const res = await evaluateRules()
    ElMessage.success(`评估完成，触发 ${res.triggered} 条规则`)
    loadExecutions()
  } catch (e: any) {
    ElMessage.error(e.message || '评估失败')
  } finally {
    evaluating.value = false
  }
}

function showExecutionDetail(exec: LoopExecution) {
  detailExecution.value = exec
  detailDialogVisible.value = true
}

onMounted(() => {
  loadRules()
  loadExecutions()
})
</script>

<style scoped lang="scss">
.quality-loop-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    h2 { margin: 0; font-size: 20px; }
  }
}
.rule-item {
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  &:hover { border-color: #409eff; }
  &.active { border-color: #409eff; background: #ecf5ff; }
  .rule-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
    .rule-name { font-weight: 500; }
  }
  .rule-condition { font-size: 12px; color: #999; margin-bottom: 8px; }
  .rule-actions { display: flex; gap: 4px; }
}
.step-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px dashed #f5f5f5;
  &:last-child { border-bottom: none; }
  .step-action { font-weight: 500; width: 120px; font-size: 13px; }
  .step-detail { flex: 1; font-size: 13px; color: #666; }
}
</style>
