<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ isEdit ? '编辑用例' : '创建用例' }}</h2>
      <el-button @click="router.push('/test-cases')">返回列表</el-button>
    </div>

    <el-card>
      <el-form :model="form" label-width="100px" style="max-width: 700px">
        <el-form-item label="用例名称" required>
          <el-input v-model="form.name" placeholder="输入用例名称" />
        </el-form-item>
        <el-form-item label="测试类型" required>
          <el-select v-model="form.test_type" placeholder="选择类型">
            <el-option label="API 测试" value="api" />
            <el-option label="IoT 测试" value="iot" />
            <el-option label="AI 评测" value="ai" />
            <el-option label="Web 测试" value="web" />
            <el-option label="App 测试" value="app" />
            <el-option label="端到端" value="e2e" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority">
            <el-option label="P0 - 阻塞" value="p0" />
            <el-option label="P1 - 严重" value="p1" />
            <el-option label="P2 - 一般" value="p2" />
            <el-option label="P3 - 低" value="p3" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属模块">
          <el-input v-model="form.module" placeholder="如: 支付模块、设备控制" />
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select v-model="form.project_id" placeholder="选择项目">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="用例描述" />
        </el-form-item>
        <el-form-item label="预期结果">
          <el-input v-model="form.expected_result" type="textarea" :rows="2" placeholder="预期结果描述" />
        </el-form-item>
        <el-form-item label="测试步骤">
          <div style="width:100%">
            <div v-for="(step, i) in steps" :key="i" style="display:flex;gap:8px;margin-bottom:8px;align-items:center">
              <el-input v-model="step.name" placeholder="步骤名称" style="width:200px" />
              <el-select v-model="step.action" placeholder="操作" style="width:150px">
                <el-option label="发送请求" value="send_request" />
                <el-option label="等待状态" value="wait_state" />
                <el-option label="断言" value="assert" />
                <el-option label="截图" value="screenshot" />
              </el-select>
              <el-input v-model="step.value" placeholder="参数值" style="flex:1" />
              <el-button type="danger" link @click="steps.splice(i, 1)">删除</el-button>
            </div>
            <el-button @click="steps.push({ name: '', action: 'send_request', value: '' })">+ 添加步骤</el-button>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave">{{ isEdit ? '保存修改' : '创建用例' }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTestCase, createTestCase, updateTestCase } from '@/api/test_case'
import { getProjects } from '@/api/project'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id && route.params.id !== '0')

const form = ref({
  name: '', test_type: 'api', priority: 'p1', module: '',
  project_id: null as number | null, description: '', expected_result: '',
})
const steps = ref<any[]>([{ name: '', action: 'send_request', value: '' }])
const projects = ref<any[]>([])

async function handleSave() {
  try {
    const data = { ...form.value, steps: steps.value, tags: [] }
    if (isEdit.value) {
      await updateTestCase(Number(route.params.id), data)
      ElMessage.success('用例已更新')
    } else {
      await createTestCase(data)
      ElMessage.success('用例已创建')
    }
    router.push('/test-cases')
  } catch {
    ElMessage.error('保存失败')
  }
}

onMounted(async () => {
  try {
    projects.value = await getProjects() as any
  } catch {
    projects.value = []
  }
  if (isEdit.value) {
    try {
      const caseData = await getTestCase(Number(route.params.id)) as any
      form.value = {
        name: caseData.name, test_type: caseData.test_type, priority: caseData.priority,
        module: caseData.module, project_id: caseData.project_id,
        description: caseData.description || '', expected_result: caseData.expected_result || '',
      }
      if (Array.isArray(caseData.steps)) {
        steps.value = caseData.steps.map((s: any) => ({
          name: s.name || '', action: s.action || 'send_request', value: s.value || '',
        }))
      }
    } catch {
      ElMessage.error('加载用例失败')
    }
  }
})
</script>

<style scoped lang="scss">
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
