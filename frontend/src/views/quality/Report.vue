<template>
  <div class="page">
    <div class="page-header">
      <h2>质量报告</h2>
      <el-button type="primary" :loading="generating" @click="handleGenerate">生成报告</el-button>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat">{{ latestReport?.summary?.overall_score ?? '--' }}</div>
          <div class="stat-label">综合质量分</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat" style="color:#67c23a">{{ latestReport?.summary?.pass_rate ?? '--' }}%</div>
          <div class="stat-label">自动化通过率</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat" style="color:#e6a23c">{{ latestReport?.summary?.defect_escape_rate ?? '--' }}%</div>
          <div class="stat-label">缺陷逃逸率</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat" style="color:#67c23a">{{ latestReport?.summary?.release_success_rate ?? '--' }}%</div>
          <div class="stat-label">发布成功率</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-bottom: 16px">
      <template #header><span>质量维度评分</span></template>
      <el-table :data="dimensions" stripe>
        <el-table-column prop="name" label="维度" />
        <el-table-column prop="score" label="得分" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.score >= 90 ? '#67c23a' : row.score >= 80 ? '#e6a23c' : '#f56c6c', fontWeight: 'bold' }">
              {{ row.score }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="300">
          <template #default="{ row }">
            <el-progress :percentage="row.score" :color="row.score >= 90 ? '#67c23a' : row.score >= 80 ? '#e6a23c' : '#f56c6c'" />
          </template>
        </el-table-column>
        <el-table-column prop="trend" label="趋势" width="80">
          <template #default="{ row }">
            <span :style="{ color: row.trend === 'up' ? '#67c23a' : row.trend === 'down' ? '#f56c6c' : '#909399' }">
              {{ row.trend === 'up' ? '↑' : row.trend === 'down' ? '↓' : '→' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="说明" />
      </el-table>
    </el-card>

    <el-card style="margin-bottom: 16px">
      <template #header><span>近期报告</span></template>
      <el-table :data="reports" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="报告名称" />
        <el-table-column prop="report_type" label="类型" width="120">
          <template #default="{ row }"><el-tag size="small">{{ row.report_type }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="overall_score" label="质量分" width="100" />
        <el-table-column prop="generated_at" label="生成时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">查看</el-button>
            <el-button link type="warning" @click="handleDownload(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getQualityReports, generateQualityReport } from '@/api/quality_report'

const generating = ref(false)
const reports = ref<any[]>([])
const latestReport = computed(() => reports.value[0] || null)
const dimensions = computed(() => latestReport.value?.dimensions || [])

onMounted(async () => {
  try {
    const res = await getQualityReports()
    reports.value = Array.isArray(res) ? res : (res as any).items || []
  } catch {
    // fallback
  }
})

async function handleGenerate() {
  generating.value = true
  try {
    const report = await generateQualityReport()
    reports.value.unshift(report as any)
    ElMessage.success('报告生成成功')
  } catch {
    ElMessage.error('报告生成失败')
  } finally {
    generating.value = false
  }
}

function handleView(row: any) {
  ElMessage.info(`查看报告: ${row.name}`)
}

function handleDownload(row: any) {
  ElMessage.success(`报告 ${row.name} 已开始下载`)
}
</script>

<style scoped lang="scss">
.stat { font-size: 24px; font-weight: bold; text-align: center; }
.stat-label { text-align: center; color: #909399; margin-top: 4px; font-size: 13px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
