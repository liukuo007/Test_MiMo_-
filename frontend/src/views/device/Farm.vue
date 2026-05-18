<template>
  <div class="page">
    <div class="page-header">
      <h2>设备农场</h2>
      <div>
        <el-button @click="showCreateVirtual = true">创建虚拟设备</el-button>
        <el-button type="primary" @click="fetchDevices">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-input v-model="search" placeholder="搜索设备名称/SN" clearable @clear="fetchDevices" @keyup.enter="fetchDevices">
          <template #append>
            <el-button @click="fetchDevices">搜索</el-button>
          </template>
        </el-input>
      </el-col>
      <el-col :span="4">
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="fetchDevices">
          <el-option v-for="(v, k) in DEVICE_STATUS_MAP" :key="k" :label="v.label" :value="k" />
        </el-select>
      </el-col>
      <el-col :span="4">
        <el-select v-model="filterRegion" placeholder="区域筛选" clearable @change="fetchDevices">
          <el-option label="中国" value="cn" />
          <el-option label="美国" value="us" />
          <el-option label="东南亚" value="sea" />
        </el-select>
      </el-col>
      <el-col :span="4" :offset="6">
        <el-card shadow="hover">
          <div class="stat">在线: {{ onlineCount }} / {{ total }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-table :data="devices" stripe v-loading="loading">
      <el-table-column prop="device_sn" label="设备SN" width="200" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="device_type" label="类型" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ DEVICE_STATUS_MAP[row.status]?.label || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="region" label="区域" width="80" />
      <el-table-column prop="temperature" label="温度" width="80">
        <template #default="{ row }">{{ row.temperature != null ? row.temperature + '°C' : '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleControl(row.id, 'open_door')">开门</el-button>
          <el-button link type="warning" @click="handleControl(row.id, 'restart')">重启</el-button>
          <el-button link @click="router.push(`/devices/${row.id}`)">详情</el-button>
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

    <el-dialog v-model="showCreateVirtual" title="创建虚拟设备">
      <el-form :model="virtualForm" label-width="80px">
        <el-form-item label="数量">
          <el-input-number v-model="virtualForm.count" :min="1" :max="1000" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="virtualForm.device_type">
            <el-option label="L1 协议仿真" value="virtual_l1" />
            <el-option label="L2 状态仿真" value="virtual_l2" />
            <el-option label="L3 物理仿真" value="virtual_l3" />
          </el-select>
        </el-form-item>
        <el-form-item label="区域">
          <el-select v-model="virtualForm.region">
            <el-option label="中国" value="cn" />
            <el-option label="美国" value="us" />
            <el-option label="东南亚" value="sea" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateVirtual = false">取消</el-button>
        <el-button type="primary" @click="handleCreateVirtual">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getDevices, createVirtualDevices, controlDevice } from '@/api/device'
import { DEVICE_STATUS_MAP } from '@/utils/constants'
import { ElMessage } from 'element-plus'

const router = useRouter()
const devices = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const search = ref('')
const filterStatus = ref('')
const filterRegion = ref('')
const showCreateVirtual = ref(false)
const virtualForm = ref({ count: 10, device_type: 'virtual_l2', region: 'cn' })

const onlineCount = computed(() => devices.value.filter((d) => d.status === 'online').length)

function statusTagType(status: string) {
  const map: Record<string, string> = { online: 'success', occupied: 'warning', offline: 'info', fault: 'danger' }
  return map[status] || 'info'
}

async function fetchDevices() {
  loading.value = true
  try {
    const params: any = { skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value }
    if (search.value) params.search = search.value
    if (filterStatus.value) params.status = filterStatus.value
    if (filterRegion.value) params.region = filterRegion.value
    const result = await getDevices(params)
    if (Array.isArray(result)) {
      devices.value = result
      total.value = result.length
    } else if (result?.items) {
      devices.value = result.items
      total.value = result.total ?? result.items.length
    } else {
      devices.value = result
      total.value = result.length
    }
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchDevices()
}

async function handleCreateVirtual() {
  await createVirtualDevices(virtualForm.value)
  ElMessage.success('虚拟设备创建成功')
  showCreateVirtual.value = false
  fetchDevices()
}

async function handleControl(id: number, action: string) {
  await controlDevice(id, action)
  ElMessage.success('指令已发送')
}

onMounted(fetchDevices)
</script>

<style scoped lang="scss">
.stat {
  font-size: 18px;
  font-weight: bold;
  text-align: center;
}
</style>
