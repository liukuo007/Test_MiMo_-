<template>
  <div class="device-mesh-page">
    <div class="page-header">
      <h2>设备资源网格</h2>
      <el-button type="primary" @click="showCreatePool">创建设备池</el-button>
    </div>

    <el-row :gutter="16">
      <!-- 设备池列表 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>设备池</template>
          <div v-if="pools.length === 0" style="text-align: center; color: #999; padding: 20px">暂无设备池</div>
          <div
            v-for="pool in pools"
            :key="pool.id"
            class="pool-item"
            :class="{ active: selectedPool?.id === pool.id }"
            @click="selectPool(pool)"
          >
            <div class="pool-name">{{ pool.name }}</div>
            <div class="pool-meta">
              <el-tag size="small" :type="pool.pool_type === 'auto' ? 'success' : 'info'">{{ pool.pool_type === 'auto' ? '自动' : '手动' }}</el-tag>
              <span class="pool-count">{{ pool.device_count }} 台设备</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 池详情 -->
      <el-col :span="16">
        <el-card shadow="hover" v-if="selectedPool">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>{{ selectedPool.name }} — 设备列表</span>
              <div style="display: flex; gap: 8px">
                <el-button size="small" @click="showAssign">添加设备</el-button>
                <el-button size="small" @click="handleSchedule">智能调度</el-button>
                <el-button size="small" type="danger" @click="handleDeletePool">删除池</el-button>
              </div>
            </div>
          </template>
          <el-table :data="poolDevices" stripe v-loading="devicesLoading">
            <el-table-column prop="name" label="设备名称" />
            <el-table-column prop="sn" label="序列号" width="160" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'online' ? 'success' : row.status === 'busy' ? 'warning' : 'info'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="device_type" label="类型" width="100" />
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button size="small" @click="viewHealth(row.device_id)">健康分</el-button>
                <el-button size="small" type="danger" @click="handleRemoveDevice(row.device_id)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        <el-card shadow="hover" v-else>
          <div style="text-align: center; color: #999; padding: 60px 0">选择左侧设备池查看详情</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建池弹窗 -->
    <el-dialog v-model="poolDialogVisible" title="创建设备池" width="400px">
      <el-form :model="poolForm" label-width="80px">
        <el-form-item label="池名称" required>
          <el-input v-model="poolForm.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="poolForm.pool_type" style="width: 100%">
            <el-option label="手动" value="manual" />
            <el-option label="自动" value="auto" />
          </el-select>
        </el-form-item>
        <el-form-item label="自动分配">
          <el-switch v-model="poolForm.auto_assign" />
        </el-form-item>
        <el-form-item label="最大设备">
          <el-input-number v-model="poolForm.max_devices" :min="0" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="poolForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="poolDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreatePool">创建</el-button>
      </template>
    </el-dialog>

    <!-- 添加设备弹窗 -->
    <el-dialog v-model="assignDialogVisible" title="添加设备到池" width="600px">
      <el-table :data="allDevices" stripe @selection-change="onDeviceSelect" max-height="400">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="name" label="设备名称" />
        <el-table-column prop="sn" label="序列号" width="160" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssign" :loading="assigning">添加 ({{ selectedDeviceIds.length }})</el-button>
      </template>
    </el-dialog>

    <!-- 智能调度弹窗 -->
    <el-dialog v-model="scheduleDialogVisible" title="智能调度" width="400px">
      <el-form label-width="80px">
        <el-form-item label="调度策略">
          <el-select v-model="scheduleStrategy" style="width: 100%">
            <el-option label="最空闲" value="least_busy" />
            <el-option label="最稳定" value="most_stable" />
            <el-option label="最近最少使用" value="least_recently_checked" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="scheduleCount" :min="1" :max="20" />
        </el-form-item>
      </el-form>
      <div v-if="scheduledDevices.length > 0" style="margin-top: 12px">
        <el-tag v-for="d in scheduledDevices" :key="d.device_id" style="margin: 2px">{{ d.name }} ({{ d.sn }})</el-tag>
      </div>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="executeSchedule" :loading="scheduling">执行调度</el-button>
      </template>
    </el-dialog>

    <!-- 健康分弹窗 -->
    <el-dialog v-model="healthDialogVisible" title="设备健康分" width="400px">
      <div v-if="healthScore" style="text-align: center">
        <div class="health-score-big" :style="{ color: healthScore.score >= 80 ? '#67c23a' : healthScore.score >= 50 ? '#e6a23c' : '#f56c6c' }">
          {{ healthScore.score.toFixed(0) }}
        </div>
        <div style="color: #999; margin-bottom: 16px">健康分</div>
        <div v-if="healthScore.factors">
          <div v-for="(val, key) in healthScore.factors" :key="key" class="factor-row">
            <span class="factor-key">{{ factorLabel(key) }}</span>
            <el-progress :percentage="val" :color="val >= 80 ? '#67c23a' : val >= 50 ? '#e6a23c' : '#f56c6c'" />
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getPools,
  createPool,
  deletePool,
  getPoolDevices,
  assignDevices,
  removePoolDevice,
  autoSchedule,
  getDeviceHealth,
  type DevicePool,
  type PoolDevice,
  type DeviceHealthScore,
} from '@/api/device_mesh'
import request from '@/api/request'

const pools = ref<DevicePool[]>([])
const selectedPool = ref<DevicePool | null>(null)
const poolDevices = ref<PoolDevice[]>([])
const devicesLoading = ref(false)

const poolDialogVisible = ref(false)
const poolForm = ref({ name: '', pool_type: 'manual', auto_assign: false, max_devices: 0, description: '' })

const assignDialogVisible = ref(false)
const allDevices = ref<any[]>([])
const selectedDeviceIds = ref<number[]>([])
const assigning = ref(false)

const scheduleDialogVisible = ref(false)
const scheduleStrategy = ref('least_busy')
const scheduleCount = ref(1)
const scheduledDevices = ref<PoolDevice[]>([])
const scheduling = ref(false)

const healthDialogVisible = ref(false)
const healthScore = ref<DeviceHealthScore | null>(null)

function factorLabel(key: string) {
  return { online: '在线状态', heartbeat: '心跳新鲜度', temperature: '温度', error_rate: '成功率' }[key] || key
}

async function loadPools() {
  try {
    pools.value = await getPools()
    if (selectedPool.value) {
      selectedPool.value = pools.value.find(p => p.id === selectedPool.value!.id) || null
    }
  } catch (e) {
    console.error(e)
  }
}

async function selectPool(pool: DevicePool) {
  selectedPool.value = pool
  devicesLoading.value = true
  try {
    poolDevices.value = await getPoolDevices(pool.id)
  } catch (e) {
    console.error(e)
  } finally {
    devicesLoading.value = false
  }
}

function showCreatePool() {
  poolForm.value = { name: '', pool_type: 'manual', auto_assign: false, max_devices: 0, description: '' }
  poolDialogVisible.value = true
}

async function handleCreatePool() {
  if (!poolForm.value.name) return ElMessage.warning('请输入池名称')
  try {
    await createPool(poolForm.value)
    poolDialogVisible.value = false
    ElMessage.success('创建成功')
    loadPools()
  } catch (e: any) {
    ElMessage.error(e.message || '创建失败')
  }
}

async function handleDeletePool() {
  if (!selectedPool.value) return
  await ElMessageBox.confirm(`确定删除设备池「${selectedPool.value.name}」？`, '提示', { type: 'warning' })
  try {
    await deletePool(selectedPool.value.id)
    selectedPool.value = null
    poolDevices.value = []
    ElMessage.success('已删除')
    loadPools()
  } catch (e: any) {
    ElMessage.error(e.message || '删除失败')
  }
}

async function showAssign() {
  try {
    const res = await request.get('/devices')
    allDevices.value = res.items || res || []
    selectedDeviceIds.value = []
    assignDialogVisible.value = true
  } catch (e) {
    ElMessage.error('加载设备列表失败')
  }
}

function onDeviceSelect(rows: any[]) {
  selectedDeviceIds.value = rows.map(r => r.id)
}

async function handleAssign() {
  if (!selectedPool.value || !selectedDeviceIds.value.length) return
  assigning.value = true
  try {
    await assignDevices(selectedPool.value.id, selectedDeviceIds.value)
    assignDialogVisible.value = false
    ElMessage.success(`已添加 ${selectedDeviceIds.value.length} 台设备`)
    selectPool(selectedPool.value)
    loadPools()
  } catch (e: any) {
    ElMessage.error(e.message || '添加失败')
  } finally {
    assigning.value = false
  }
}

async function handleRemoveDevice(deviceId: number) {
  if (!selectedPool.value) return
  try {
    await removePoolDevice(selectedPool.value.id, deviceId)
    ElMessage.success('已移除')
    selectPool(selectedPool.value)
    loadPools()
  } catch (e: any) {
    ElMessage.error(e.message || '移除失败')
  }
}

function handleSchedule() {
  scheduledDevices.value = []
  scheduleDialogVisible.value = true
}

async function executeSchedule() {
  if (!selectedPool.value) return
  scheduling.value = true
  try {
    const res = await autoSchedule(selectedPool.value.id, scheduleStrategy.value, scheduleCount.value)
    scheduledDevices.value = res.devices || []
    if (scheduledDevices.value.length === 0) {
      ElMessage.warning('没有可用设备')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '调度失败')
  } finally {
    scheduling.value = false
  }
}

async function viewHealth(deviceId: number) {
  try {
    healthScore.value = await getDeviceHealth(deviceId)
    healthDialogVisible.value = true
  } catch (e: any) {
    ElMessage.error(e.message || '获取健康分失败')
  }
}

onMounted(loadPools)
</script>

<style scoped lang="scss">
.device-mesh-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    h2 { margin: 0; font-size: 20px; }
  }
}
.pool-item {
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  &:hover { border-color: #409eff; }
  &.active { border-color: #409eff; background: #ecf5ff; }
  .pool-name { font-weight: 500; margin-bottom: 4px; }
  .pool-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #999; }
}
.health-score-big {
  font-size: 64px;
  font-weight: bold;
  line-height: 1;
}
.factor-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
  .factor-key { width: 80px; font-size: 13px; }
  :deep(.el-progress) { flex: 1; }
}
</style>
