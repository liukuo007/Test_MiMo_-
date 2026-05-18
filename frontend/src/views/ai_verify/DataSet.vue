<template>
  <div class="page">
    <div class="page-header">
      <h2>数据集管理</h2>
      <el-button type="primary" @click="showCreate = true">上传数据集</el-button>
    </div>

    <el-table :data="datasets" stripe>
      <el-table-column prop="name" label="数据集名称" />
      <el-table-column prop="type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag size="small">{{ row.type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="sample_count" label="样本数" width="100" />
      <el-table-column prop="class_count" label="类别数" width="80" />
      <el-table-column prop="size_bytes" label="大小" width="100">
        <template #default="{ row }">{{ row.size_bytes ? (row.size_bytes / 1024 / 1024).toFixed(1) + ' MB' : '-' }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="handlePreview(row)">预览</el-button>
          <el-button link type="warning" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" title="上传数据集" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="数据集名称">
          <el-input v-model="form.name" placeholder="如: sku-dataset-v3" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type">
            <el-option label="SKU 图片" value="sku_images" />
            <el-option label="人脸图片" value="face_images" />
            <el-option label="手势视频" value="gesture_videos" />
            <el-option label="混合数据" value="mixed" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="标注格式">
          <el-select v-model="form.annotation_format">
            <el-option label="COCO" value="coco" />
            <el-option label="VOC" value="voc" />
            <el-option label="YOLO" value="yolo" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">确认上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showPreview" title="数据集预览" width="700px">
      <el-descriptions :column="2" border style="margin-bottom: 16px">
        <el-descriptions-item label="名称">{{ previewData.name }}</el-descriptions-item>
        <el-descriptions-item label="样本数">{{ previewData.sample_count }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ previewData.type }}</el-descriptions-item>
        <el-descriptions-item label="类别数">{{ previewData.class_count }}</el-descriptions-item>
      </el-descriptions>
      <h4>类别分布</h4>
      <div class="class-list">
        <div v-for="cls in previewData.class_list" :key="cls.name" class="class-item">
          <span>{{ cls.name }}</span>
          <el-progress :percentage="cls.percent" :stroke-width="16" :text-inside="true" />
          <span class="count">{{ cls.count }} 张</span>
        </div>
      </div>
      <el-empty v-if="!previewData.class_list?.length" description="暂无类别分布数据" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDatasets, createDataset, deleteDataset } from '@/api/datasets'

const showCreate = ref(false)
const showPreview = ref(false)
const form = ref({ name: '', type: 'sku_images', description: '', annotation_format: 'coco' })
const previewData = ref<any>({})
const datasets = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await getDatasets()
    datasets.value = Array.isArray(res) ? res : (res as any).items || []
  } catch {
    // fallback
  }
})

function handlePreview(row: any) {
  previewData.value = row
  showPreview.value = true
}

function handleEdit(row: any) {
  ElMessage.info('编辑功能开发中')
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm(`确认删除数据集 "${row.name}"?`, '提示', { type: 'warning' })
  try {
    await deleteDataset(row.id)
    datasets.value = datasets.value.filter((d: any) => d.id !== row.id)
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

async function handleCreate() {
  try {
    const newDataset = await createDataset(form.value)
    datasets.value.unshift(newDataset as any)
    showCreate.value = false
    form.value = { name: '', type: 'sku_images', description: '', annotation_format: 'coco' }
    ElMessage.success('数据集已创建')
  } catch {
    ElMessage.error('创建失败')
  }
}
</script>

<style scoped lang="scss">
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.class-list { max-height: 400px; overflow-y: auto; }
.class-item { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.class-item span:first-child { width: 140px; font-size: 13px; }
.class-item .count { width: 60px; text-align: right; font-size: 13px; color: #909399; }
.class-item .el-progress { flex: 1; }
</style>
