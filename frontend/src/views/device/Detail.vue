<template>
  <div class="page">
    <div class="page-header">
      <h2>设备详情 #{{ $route.params.id }}</h2>
      <el-button @click="router.push('/devices')">返回列表</el-button>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat"><el-tag :type="statusType(device.status)" size="large">{{ device.status || '-' }}</el-tag></div>
          <div class="stat-label">设备状态</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">{{ device.temperature || '-' }}°C</div>
          <div class="stat-label">温度</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">{{ device.firmware_version || '-' }}</div>
          <div class="stat-label">固件版本</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">{{ device.region || '-' }}</div>
          <div class="stat-label">区域</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-bottom: 16px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>设备信息</span>
          <div>
            <el-button size="small" @click="handleControl('open_door')">开门</el-button>
            <el-button size="small" @click="handleControl('restart')">重启</el-button>
            <el-button size="small" @click="handleControl('heartbeat')">心跳检测</el-button>
          </div>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="设备SN">{{ device.device_sn }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ device.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ device.device_type }}</el-descriptions-item>
        <el-descriptions-item label="IP 地址">{{ device.ip_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="区域">{{ device.region }}</el-descriptions-item>
        <el-descriptions-item label="温度">{{ device.temperature }}°C</el-descriptions-item>
        <el-descriptions-item label="固件版本">{{ device.firmware_version }}</el-descriptions-item>
        <el-descriptions-item label="最后心跳">{{ device.last_heartbeat }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ device.created_at }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ device.updated_at }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card>
      <template #header><span>设备事件日志</span></template>
      <el-timeline>
        <el-timeline-item
          v-for="(event, i) in events"
          :key="i"
          :timestamp="formatTime(event.created_at)"
          :type="event.event_type === 'error' || event.event_type === 'fault' ? 'danger' : event.event_type === 'warning' ? 'warning' : event.event_type === 'control' ? 'success' : 'primary'"
        >
          <el-tag :type="event.event_type === 'error' || event.event_type === 'fault' ? 'danger' : event.event_type === 'warning' ? 'warning' : 'info'" size="small" style="margin-right: 8px">
            {{ event.event_type }}
          </el-tag>
          {{ event.message }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="events.length === 0" description="暂无事件" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDevice, controlDevice, getDeviceEvents } from '@/api/device'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const device = ref<any>({})
const events = ref<any[]>([])

function statusType(s: string) {
  return { online: 'success', occupied: 'warning', offline: 'info', fault: 'danger', maintenance: '' }[s] || 'info'
}

function formatTime(t: string) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

async function handleControl(action: string) {
  try {
    await controlDevice(Number(route.params.id), action)
    ElMessage.success(`指令 '${action}' 已发送`)
    events.value = await getDeviceEvents(Number(route.params.id), 50).catch(() => [])
  } catch {
    ElMessage.error('指令发送失败')
  }
}

onMounted(async () => {
  try {
    const deviceId = Number(route.params.id)
    const [deviceData, eventData] = await Promise.all([
      getDevice(deviceId).catch(() => null),
      getDeviceEvents(deviceId, 50).catch(() => []),
    ])
    device.value = deviceData
    events.value = eventData
  } catch {
    // fallback
  }
})
</script>

<style scoped lang="scss">
.stat { font-size: 20px; font-weight: bold; text-align: center; }
.stat-label { text-align: center; color: #909399; margin-top: 4px; font-size: 13px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
