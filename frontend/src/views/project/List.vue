<template>
  <div class="page">
    <div class="page-header">
      <h2>项目管理</h2>
      <el-button type="primary" @click="showCreate = true">创建项目</el-button>
    </div>
    <el-table :data="projects" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="项目名称" />
      <el-table-column prop="environment" label="环境" width="100" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/projects/${row.id}`)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" title="创建项目">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="环境">
          <el-select v-model="form.environment">
            <el-option label="开发" value="dev" />
            <el-option label="测试" value="staging" />
            <el-option label="预发布" value="pre_prod" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getProjects, createProject } from '@/api/project'
import { ElMessage } from 'element-plus'

const router = useRouter()
const projects = ref<any[]>([])
const showCreate = ref(false)
const form = ref({ name: '', description: '', environment: 'dev' })

async function fetchProjects() {
  try {
    projects.value = await getProjects()
  } catch {
    projects.value = []
  }
}

async function handleCreate() {
  try {
    await createProject(form.value)
    ElMessage.success('创建成功')
    showCreate.value = false
    fetchProjects()
  } catch {
    ElMessage.error('创建失败')
  }
}

onMounted(fetchProjects)
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
