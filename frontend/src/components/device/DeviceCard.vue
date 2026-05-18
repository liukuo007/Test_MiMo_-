<template>
  <el-card shadow="hover" class="device-card">
    <div class="device-info">
      <div class="device-name">{{ device.name }}</div>
      <div class="device-sn">{{ device.device_sn }}</div>
      <el-tag :type="statusType" size="small">{{ device.status }}</el-tag>
    </div>
    <div class="device-meta">
      <span>{{ device.region }}</span>
      <span v-if="device.temperature">{{ device.temperature }}°C</span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  device: {
    name: string
    device_sn: string
    status: string
    region: string
    temperature: number | null
  }
}>()

const statusType = computed(() => {
  const map: Record<string, string> = { online: 'success', occupied: 'warning', offline: 'info', fault: 'danger' }
  return (map[props.device.status] || 'info') as any
})
</script>

<style scoped lang="scss">
.device-card {
  cursor: pointer;
}
.device-name {
  font-weight: bold;
  margin-bottom: 4px;
}
.device-sn {
  color: #999;
  font-size: 12px;
  margin-bottom: 8px;
}
.device-meta {
  display: flex;
  justify-content: space-between;
  color: #666;
  font-size: 12px;
  margin-top: 8px;
}
</style>
