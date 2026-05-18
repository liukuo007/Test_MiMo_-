<template>
  <div class="page">
    <div class="page-header">
      <h2>链路追踪</h2>
      <el-button type="primary" @click="fetchTraces">刷新</el-button>
    </div>

    <el-card style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="服务">
          <el-select v-model="filters.service" clearable placeholder="全部" style="width: 160px">
            <el-option v-for="s in services" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width: 120px">
            <el-option label="成功" value="ok" />
            <el-option label="错误" value="error" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchTraces">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="traces" stripe @row-click="handleRowClick" highlight-current-row>
        <el-table-column prop="trace_id" label="Trace ID" width="200" show-overflow-tooltip />
        <el-table-column prop="service" label="服务" width="140">
          <template #default="{ row }"><el-tag size="small">{{ row.service }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="operation" label="操作" width="160" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ok' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="started_at" label="开始时间" width="180" />
      </el-table>
    </el-card>

    <el-drawer v-model="showDetail" title="Trace 详情" size="60%">
      <div v-if="selectedTrace">
        <el-descriptions :column="2" border style="margin-bottom: 16px">
          <el-descriptions-item label="Trace ID">{{ selectedTrace.trace_id }}</el-descriptions-item>
          <el-descriptions-item label="服务">{{ selectedTrace.service }}</el-descriptions-item>
          <el-descriptions-item label="操作">{{ selectedTrace.operation }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedTrace.status === 'ok' ? 'success' : 'danger'">{{ selectedTrace.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总耗时">{{ selectedTrace.duration_ms }}ms</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ selectedTrace.started_at }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-bottom: 12px">Span 时间线</h4>
        <div class="timeline-container">
          <div v-for="span in detailSpans" :key="span.span_id" class="span-row">
            <div class="span-info">
              <div class="span-name">
                <el-tag :type="span.status === 'ok' ? 'success' : 'danger'" size="small" style="margin-right: 8px">{{ span.service }}</el-tag>
                {{ span.operation }}
              </div>
              <div class="span-meta">{{ span.duration_ms }}ms</div>
            </div>
            <div class="span-bar-container">
              <div class="span-bar" :style="spanBarStyle(span)" :class="span.status === 'ok' ? 'bar-ok' : 'bar-error'" />
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getTraces, getTraceDetail } from '@/api/trace'

const traces = ref<any[]>([])
const services = ref(['api-gateway', 'device-service', 'ai-service', 'payment-service', 'order-service'])
const filters = ref({ service: '', status: '' })
const showDetail = ref(false)
const selectedTrace = ref<any>(null)
const detailSpans = ref<any[]>([])

function spanBarStyle(span: any) {
  const total = selectedTrace.value?.duration_ms || 1000
  const width = Math.max(5, (span.duration_ms / total) * 100)
  const offset = span.started_at && selectedTrace.value?.started_at
    ? ((new Date(span.started_at).getTime() - new Date(selectedTrace.value.started_at).getTime()) / total) * 100
    : 0
  return { width: `${width}%`, marginLeft: `${offset}%` }
}

async function fetchTraces() {
  try {
    const params: any = {}
    if (filters.value.service) params.service = filters.value.service
    if (filters.value.status) params.status = filters.value.status
    traces.value = await getTraces(params) as any
  } catch {
    traces.value = []
  }
}

async function handleRowClick(row: any) {
  try {
    selectedTrace.value = row
    const detail = await getTraceDetail(row.trace_id) as any
    detailSpans.value = detail?.spans || []
    showDetail.value = true
  } catch {
    detailSpans.value = []
  }
}

onMounted(fetchTraces)
</script>

<style scoped lang="scss">
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.timeline-container { max-height: 500px; overflow-y: auto; }
.span-row { margin-bottom: 8px; }
.span-info { display: flex; justify-content: space-between; margin-bottom: 2px; }
.span-name { font-size: 13px; }
.span-meta { font-size: 12px; color: #909399; }
.span-bar-container { height: 20px; background: #f5f7fa; border-radius: 4px; overflow: hidden; }
.span-bar { height: 100%; border-radius: 4px; min-width: 4px; }
.bar-ok { background: #67c23a; }
.bar-error { background: #f56c6c; }
</style>
