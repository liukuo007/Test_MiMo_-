<template>
  <div class="page">
    <div class="page-header">
      <h2>用例管理</h2>
      <el-button type="primary" @click="showCreate = true">创建用例</el-button>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="8">
        <el-input v-model="search" placeholder="搜索用例名称" clearable @clear="fetchTestCases" @keyup.enter="fetchTestCases">
          <template #append>
            <el-button @click="fetchTestCases">搜索</el-button>
          </template>
        </el-input>
      </el-col>
      <el-col :span="4">
        <el-select v-model="filterType" placeholder="类型筛选" clearable @change="fetchTestCases">
          <el-option v-for="(label, key) in TEST_TYPE_MAP" :key="key" :label="label" :value="key" />
        </el-select>
      </el-col>
      <el-col :span="4">
        <el-select v-model="filterPriority" placeholder="优先级筛选" clearable @change="fetchTestCases">
          <el-option label="P0" value="p0" />
          <el-option label="P1" value="p1" />
          <el-option label="P2" value="p2" />
          <el-option label="P3" value="p3" />
        </el-select>
      </el-col>
    </el-row>

    <el-table :data="testCases" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="用例名称" />
      <el-table-column prop="test_type" label="类型" width="100">
        <template #default="{ row }">{{ TEST_TYPE_MAP[row.test_type] || row.test_type }}</template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80">
        <template #default="{ row }">
          <el-tag :type="row.priority === 'p0' ? 'danger' : row.priority === 'p1' ? 'warning' : 'info'">
            {{ row.priority }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="module" label="模块" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/test-cases/${row.id}/edit`)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > pageSize"
      style="margin-top: 16px; justify-content: flex-end"
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="handlePageChange"
    />

    <el-dialog v-model="showCreate" title="创建用例" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.test_type">
            <el-option v-for="(label, key) in TEST_TYPE_MAP" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority">
            <el-option label="P0" value="p0" />
            <el-option label="P1" value="p1" />
            <el-option label="P2" value="p2" />
            <el-option label="P3" value="p3" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
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
import { getTestCases, createTestCase } from '@/api/test_case'
import { useProjectStore } from '@/stores/project'
import { TEST_TYPE_MAP } from '@/utils/constants'
import { formatDate } from '@/utils/format'
import { ElMessage } from 'element-plus'

const router = useRouter()
const projectStore = useProjectStore()
const testCases = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const search = ref('')
const filterType = ref('')
const filterPriority = ref('')
const showCreate = ref(false)
const form = ref({ name: '', test_type: 'api', priority: 'p1', description: '', project_id: projectStore.currentProject?.id || 1 })

async function fetchTestCases() {
  loading.value = true
  try {
    const params: any = { skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value }
    if (search.value) params.search = search.value
    if (filterType.value) params.test_type = filterType.value
    if (filterPriority.value) params.priority = filterPriority.value
    const result = await getTestCases(params)
    if (Array.isArray(result)) {
      testCases.value = result
      total.value = result.length
    } else if (result?.items) {
      testCases.value = result.items
      total.value = result.total ?? result.items.length
    } else {
      testCases.value = result
      total.value = result.length
    }
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchTestCases()
}

async function handleCreate() {
  await createTestCase(form.value)
  ElMessage.success('创建成功')
  showCreate.value = false
  fetchTestCases()
}

onMounted(fetchTestCases)
</script>
