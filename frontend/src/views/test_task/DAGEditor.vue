<template>
  <div class="page">
    <div class="page-header">
      <h2>DAG 流程编排</h2>
      <div>
        <el-select v-model="newNodeType" style="width: 140px; margin-right: 8px" placeholder="节点类型">
          <el-option-group label="执行节点">
            <el-option v-for="t in executionStepTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-option-group>
          <el-option-group label="流控节点 (RunnerGo)">
            <el-option v-for="t in flowControlTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-option-group>
        </el-select>
        <el-button @click="addNode">添加节点</el-button>
        <el-button type="primary" @click="handleSave">保存 DAG</el-button>
      </div>
    </div>
    <el-card>
      <div class="dag-container">
        <vue-flow
          :nodes="nodes"
          :edges="edges"
          :node-types="nodeTypes"
          @nodes-change="onNodesChange"
          @edges-change="onEdgesChange"
          @connect="onConnect"
        />
      </div>
    </el-card>

    <!-- 节点配置抽屉 -->
    <el-drawer v-model="showNodeConfig" :title="`节点配置: ${selectedNode?.label || ''}`" size="450px">
      <template v-if="selectedNode">
        <el-form label-width="100px">
          <el-form-item label="节点名称">
            <el-input v-model="selectedNode.label" />
          </el-form-item>
          <el-form-item label="节点类型">
            <el-tag>{{ stepTypeLabelMap[selectedNode.data?.step_type] || selectedNode.data?.step_type }}</el-tag>
          </el-form-item>

          <!-- 条件分支配置 -->
          <template v-if="selectedNode.data?.step_type === 'condition'">
            <el-divider>条件分支配置</el-divider>
            <el-form-item label="判断字段">
              <el-input v-model="selectedNode.data.condition.field" placeholder="如: api_status_code" />
            </el-form-item>
            <el-form-item label="运算符">
              <el-select v-model="selectedNode.data.condition.operator">
                <el-option label="等于 (==)" value="eq" />
                <el-option label="不等于 (!=)" value="neq" />
                <el-option label="大于 (>)" value="gt" />
                <el-option label="大于等于 (>=)" value="gte" />
                <el-option label="小于 (<)" value="lt" />
                <el-option label="小于等于 (<=)" value="lte" />
                <el-option label="包含" value="contains" />
                <el-option label="正则匹配" value="regex" />
                <el-option label="为空" value="is_null" />
                <el-option label="不为空" value="is_not_null" />
                <el-option label="在列表中" value="in" />
              </el-select>
            </el-form-item>
            <el-form-item label="比较值">
              <el-input v-model="selectedNode.data.condition.value" placeholder="期望值" />
            </el-form-item>
            <el-form-item label="True 分支">
              <el-select v-model="selectedNode.data.condition.true_branch" clearable placeholder="条件为真时执行">
                <el-option v-for="n in otherNodes" :key="n.id" :label="n.label" :value="n.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="False 分支">
              <el-select v-model="selectedNode.data.condition.false_branch" clearable placeholder="条件为假时执行">
                <el-option v-for="n in otherNodes" :key="n.id" :label="n.label" :value="n.id" />
              </el-select>
            </el-form-item>
          </template>

          <!-- 循环配置 -->
          <template v-if="selectedNode.data?.step_type === 'loop'">
            <el-divider>循环配置</el-divider>
            <el-form-item label="遍历数据">
              <el-input v-model="selectedNode.data.loop.items_field" placeholder="上下文中的列表字段名" />
            </el-form-item>
            <el-form-item label="最大迭代">
              <el-input-number v-model="selectedNode.data.loop.max_iterations" :min="1" :max="1000" />
            </el-form-item>
            <el-divider>中断条件</el-divider>
            <el-form-item label="判断字段">
              <el-input v-model="selectedNode.data.loop.break_condition.field" placeholder="如: error_count" />
            </el-form-item>
            <el-form-item label="运算符">
              <el-select v-model="selectedNode.data.loop.break_condition.operator">
                <el-option label="等于" value="eq" />
                <el-option label="大于" value="gt" />
                <el-option label="小于" value="lt" />
                <el-option label="大于等于" value="gte" />
                <el-option label="小于等于" value="lte" />
              </el-select>
            </el-form-item>
            <el-form-item label="中断值">
              <el-input v-model="selectedNode.data.loop.break_condition.value" placeholder="满足此条件时中断" />
            </el-form-item>
            <el-divider>子步骤</el-divider>
            <el-form-item label="子步骤类型">
              <el-select v-model="selectedNode.data.loop.sub_step.type">
                <el-option v-for="t in executionStepTypes" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
            </el-form-item>
          </template>

          <!-- 通用配置 JSON 编辑 -->
          <template v-if="!['condition', 'loop'].includes(selectedNode.data?.step_type)">
            <el-divider>步骤配置 (JSON)</el-divider>
            <el-form-item>
              <el-input
                v-model="configJson"
                type="textarea"
                :rows="8"
                placeholder='{"base_url": "...", "steps": [...]}'
              />
            </el-form-item>
          </template>
        </el-form>
      </template>
    </el-drawer>

    <el-card style="margin-top: 16px">
      <template #header><span>DAG 配置预览</span></template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="节点数">{{ nodes.length }}</el-descriptions-item>
        <el-descriptions-item label="边数">{{ edges.length }}</el-descriptions-item>
        <el-descriptions-item label="流控节点">{{ flowControlCount }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top: 12px">
        <el-tag
          v-for="node in nodes"
          :key="node.id"
          :type="getTagType(node.data?.step_type)"
          style="margin: 2px 4px; cursor: pointer"
          @click="openNodeConfig(node)"
        >
          {{ node.label }}
          <span v-if="node.data?.step_type === 'condition'" style="margin-left: 4px">&#9670;</span>
          <span v-if="node.data?.step_type === 'loop'" style="margin-left: 4px">&#8635;</span>
        </el-tag>
      </div>
      <div style="margin-top: 12px">
        <el-button size="small" @click="exportConfig">导出 JSON</el-button>
        <el-button size="small" @click="showImportDialog = true">导入 JSON</el-button>
      </div>
    </el-card>

    <!-- 导入对话框 -->
    <el-dialog v-model="showImportDialog" title="导入 DAG 配置" width="600px">
      <el-input v-model="importJson" type="textarea" :rows="12" placeholder="粘贴 DAG JSON 配置" />
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="importConfig">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import { VueFlow, type NodeChange, type EdgeChange, type Connection } from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'
import { getTestTask, updateTestTask } from '@/api/test_task'

let nodeCounter = 10
const newNodeType = ref('api')
const showNodeConfig = ref(false)
const selectedNode = ref<any>(null)
const configJson = ref('{}')
const showImportDialog = ref(false)
const importJson = ref('')

const executionStepTypes = [
  { value: 'api', label: 'API 测试' },
  { value: 'iot', label: 'IoT 仿真' },
  { value: 'ai_eval', label: 'AI 验证' },
  { value: 'web', label: 'Web 测试' },
  { value: 'app', label: 'App 测试' },
  { value: 'chaos', label: '混沌测试' },
  { value: 'payment', label: '支付模拟' },
  { value: 'sms', label: '短信模拟' },
  { value: 'sso', label: 'SSO 模拟' },
  { value: 'wait', label: '等待' },
  { value: 'assert', label: '断言' },
]

const flowControlTypes = [
  { value: 'condition', label: '条件分支' },
  { value: 'loop', label: '循环' },
]

const allStepTypes = [...executionStepTypes, ...flowControlTypes]
const stepTypeLabelMap = Object.fromEntries(allStepTypes.map(t => [t.value, t.label]))

// 自定义节点样式
const ConditionNode = (props: { data: any }) => {
  return h('div', {
    style: 'padding: 8px 16px; background: #e6f7ff; border: 2px solid #1890ff; border-radius: 8px; min-width: 120px; text-align: center; cursor: pointer;',
    onClick: () => openNodeConfig(nodes.value.find(n => n.id === props.data?.nodeId)),
  }, [
    h('div', { style: 'font-size: 16px; margin-bottom: 4px;' }, '&#9670;'),
    h('div', { style: 'font-size: 12px; font-weight: bold;' }, props.data?.label || '条件分支'),
    h('div', { style: 'font-size: 10px; color: #666;' }, `${props.data?.condition?.field || '?'} ${props.data?.condition?.operator || '?'} ${props.data?.condition?.value || '?'}`),
  ])
}

const LoopNode = (props: { data: any }) => {
  return h('div', {
    style: 'padding: 8px 16px; background: #fff7e6; border: 2px solid #fa8c16; border-radius: 8px; min-width: 120px; text-align: center; cursor: pointer;',
    onClick: () => openNodeConfig(nodes.value.find(n => n.id === props.data?.nodeId)),
  }, [
    h('div', { style: 'font-size: 16px; margin-bottom: 4px;' }, '&#8635;'),
    h('div', { style: 'font-size: 12px; font-weight: bold;' }, props.data?.label || '循环'),
    h('div', { style: 'font-size: 10px; color: #666;' }, `最大 ${props.data?.loop?.max_iterations || 10} 次`),
  ])
}

const nodeTypes = {
  condition: ConditionNode,
  loop: LoopNode,
}

const nodes = ref([
  { id: '1', type: 'input', label: 'API 测试', position: { x: 250, y: 5 }, data: { step_type: 'api' } },
  { id: '2', label: 'IoT 仿真', position: { x: 100, y: 150 }, data: { step_type: 'iot' } },
  { id: '3', label: 'AI 验证', position: { x: 400, y: 150 }, data: { step_type: 'ai_eval' } },
  { id: '4', type: 'output', label: '生成报告', position: { x: 250, y: 300 }, data: { step_type: 'wait' } },
])

const edges = ref([
  { id: 'e1-2', source: '1', target: '2' },
  { id: 'e1-3', source: '1', target: '3' },
  { id: 'e2-4', source: '2', target: '4' },
  { id: 'e3-4', source: '3', target: '4' },
])

const otherNodes = computed(() =>
  nodes.value.filter(n => n.id !== selectedNode.value?.id)
)

const flowControlCount = computed(() =>
  nodes.value.filter(n => ['condition', 'loop'].includes(n.data?.step_type)).length
)

function getTagType(stepType: string) {
  const map: Record<string, string> = {
    condition: 'primary',
    loop: 'warning',
    api: '',
    iot: 'success',
    ai_eval: 'success',
    web: '',
    app: '',
    chaos: 'danger',
    payment: 'info',
    sms: 'info',
    sso: 'info',
    wait: 'info',
    assert: 'danger',
  }
  return map[stepType] || ''
}

function getDefaultData(stepType: string) {
  const base = { step_type: stepType }
  if (stepType === 'condition') {
    return {
      ...base,
      condition: { field: '', operator: 'eq', value: '', true_branch: '', false_branch: '' },
    }
  }
  if (stepType === 'loop') {
    return {
      ...base,
      loop: {
        items_field: '',
        max_iterations: 10,
        break_condition: { field: '', operator: 'gt', value: '' },
        sub_step: { type: 'api', config: {} },
      },
    }
  }
  return base
}

function addNode() {
  const stepType = newNodeType.value
  const label = stepTypeLabelMap[stepType] || stepType
  const id = String(nodeCounter++)
  const y = Math.max(...nodes.value.map(n => n.position.y)) + 100
  const nodeData = getDefaultData(stepType)

  const node: any = {
    id,
    label: `${label} (${id})`,
    position: { x: 250, y },
    data: nodeData,
  }

  if (stepType === 'condition' || stepType === 'loop') {
    node.type = stepType
    node.data.nodeId = id
    node.data.label = `${label} (${id})`
  }

  nodes.value.push(node)
}

function onNodesChange(changes: NodeChange[]) {
  for (const change of changes) {
    if (change.type === 'position' && change.position) {
      const node = nodes.value.find(n => n.id === change.id)
      if (node) node.position = change.position
    }
  }
}

function onEdgesChange(changes: EdgeChange[]) {
  for (const change of changes) {
    if (change.type === 'remove') {
      edges.value = edges.value.filter(e => e.id !== change.id)
    }
  }
}

function onConnect(connection: Connection) {
  const id = `e${connection.source}-${connection.target}`
  if (!edges.value.find(e => e.id === id)) {
    edges.value.push({
      id,
      source: connection.source!,
      target: connection.target!,
    })
  }
}

function openNodeConfig(node: any) {
  if (!node) return
  selectedNode.value = node
  if (!['condition', 'loop'].includes(node.data?.step_type)) {
    configJson.value = JSON.stringify(node.data?.config || {}, null, 2)
  }
  showNodeConfig.value = true
}

function buildDagConfig() {
  return {
    steps: nodes.value.map(n => {
      const step: any = {
        id: n.id,
        name: n.label,
        type: n.data?.step_type || 'api',
        config: n.data?.config || {},
        dependencies: edges.value.filter(e => e.target === n.id).map(e => e.source),
      }
      if (n.data?.step_type === 'condition') {
        step.condition = n.data.condition
      }
      if (n.data?.step_type === 'loop') {
        step.loop = n.data.loop
      }
      return step
    }),
  }
}

const route = useRoute()

async function handleSave() {
  const dagConfig = buildDagConfig()
  const taskId = route.query.taskId as string
  if (taskId) {
    try {
      await updateTestTask(Number(taskId), { dag_config: dagConfig })
      ElMessage.success('DAG 配置已保存到任务')
    } catch (e: any) {
      ElMessage.error('保存失败: ' + (e.message || '未知错误'))
    }
  } else {
    ElMessage.success('DAG 配置已保存（本地）')
    console.log('DAG Config:', JSON.stringify(dagConfig, null, 2))
  }
}

onMounted(async () => {
  const taskId = route.query.taskId as string
  if (taskId) {
    try {
      const task = await getTestTask(Number(taskId)) as any
      if (task.dag_config?.steps) {
        loadFromConfig(task.dag_config)
      }
    } catch (e) {
      // 任务不存在或加载失败，使用默认配置
    }
  }
})

function loadFromConfig(config: any) {
  const newNodes = config.steps.map((step: any, i: number) => ({
    id: step.id,
    label: step.name || step.id,
    position: { x: 250, y: i * 150 },
    data: {
      step_type: step.type,
      ...(step.condition ? { condition: step.condition, nodeId: step.id } : {}),
      ...(step.loop ? { loop: step.loop, nodeId: step.id } : {}),
      config: step.config || {},
    },
    ...(step.type === 'condition' ? { type: 'condition' } : {}),
    ...(step.type === 'loop' ? { type: 'loop' } : {}),
  }))
  const newEdges: any[] = []
  for (const step of config.steps) {
    for (const dep of (step.dependencies || [])) {
      newEdges.push({ id: `e${dep}-${step.id}`, source: dep, target: step.id })
    }
  }
  nodes.value = newNodes
  edges.value = newEdges
}

function exportConfig() {
  const config = buildDagConfig()
  const text = JSON.stringify(config, null, 2)
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制到剪贴板')
}

function importConfig() {
  try {
    const config = JSON.parse(importJson.value)
    if (!config.steps || !Array.isArray(config.steps)) {
      throw new Error('Invalid format: missing steps array')
    }
    const newNodes = config.steps.map((step: any, i: number) => ({
      id: step.id,
      label: step.name || step.id,
      position: { x: 250, y: i * 150 },
      data: {
        step_type: step.type,
        ...(step.condition ? { condition: step.condition, nodeId: step.id } : {}),
        ...(step.loop ? { loop: step.loop, nodeId: step.id } : {}),
        config: step.config || {},
      },
      ...(step.type === 'condition' ? { type: 'condition' } : {}),
      ...(step.type === 'loop' ? { type: 'loop' } : {}),
    }))
    const newEdges: any[] = []
    for (const step of config.steps) {
      for (const dep of (step.dependencies || [])) {
        newEdges.push({ id: `e${dep}-${step.id}`, source: dep, target: step.id })
      }
    }
    nodes.value = newNodes
    edges.value = newEdges
    showImportDialog.value = false
    ElMessage.success('导入成功')
  } catch (e: any) {
    ElMessage.error(`导入失败: ${e.message}`)
  }
}
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.dag-container {
  height: 500px;
  border: 1px solid #eee;
  border-radius: 4px;
}
</style>
