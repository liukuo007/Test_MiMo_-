<template>
  <div class="page">
    <h2>创建测试任务</h2>
    <el-card>
      <el-form :model="form" label-width="100px" style="max-width: 600px">
        <el-form-item label="任务名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="测试环境">
          <el-select v-model="form.environment">
            <el-option label="开发环境" value="dev" />
            <el-option label="测试环境" value="staging" />
            <el-option label="预发布环境" value="pre_prod" />
          </el-select>
        </el-form-item>
        <el-form-item label="分支版本">
          <el-input v-model="form.branch" placeholder="main" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleCreate">创建</el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createTestTask } from '@/api/test_task'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'

const router = useRouter()
const projectStore = useProjectStore()
const form = ref({ name: '', environment: 'dev', branch: 'main', description: '', project_id: projectStore.currentProject?.id || 1 })

async function handleCreate() {
  try {
    await createTestTask(form.value)
    ElMessage.success('创建成功')
    router.push('/test-tasks')
  } catch {
    ElMessage.error('创建失败')
  }
}
</script>
