<template>
  <div class="workbench">
    <div class="workbench-header">
      <div>
        <h2>业务场景工作台</h2>
        <p class="subtitle">零代码 · 一键运行 · 手动指定设备 · 批量巡检</p>
      </div>
      <div style="display: flex; gap: 8px">
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">新建场景</el-button>
        <el-button :icon="Refresh" circle @click="loadTemplates" />
      </div>
    </div>

    <!-- 场景模板卡片 -->
    <el-row :gutter="20" class="template-cards">
      <el-col v-for="tpl in templates" :key="tpl.id" :xs="24" :sm="12" :lg="8">
        <el-card
          class="template-card"
          shadow="hover"
          :class="{ 'is-running': runningId === tpl.id }"
        >
          <div class="card-header">
            <div class="card-icon" :style="{ background: tpl.color + '18', color: tpl.color }">
              <el-icon :size="28"><component :is="tpl.icon" /></el-icon>
            </div>
            <el-tag
              :type="tpl.category === 'shopping' ? 'success' : 'warning'"
              size="small"
              effect="plain"
            >
              {{ tpl.category === 'shopping' ? '正常流程' : '异常场景' }}
            </el-tag>
          </div>
          <h3 class="card-title">{{ tpl.name }}</h3>
          <p class="card-desc">{{ tpl.description }}</p>

          <div class="card-steps">
            <div v-for="(step, idx) in tpl.steps_definition.steps" :key="idx" class="step-item">
              <span class="step-dot" :style="{ background: tpl.color }" />
              <span class="step-text">{{ step.name }}</span>
              <span v-if="idx < tpl.steps_definition.steps.length - 1" class="step-arrow">→</span>
            </div>
          </div>

          <div class="card-actions">
            <el-button
              type="primary"
              size="large"
              class="run-btn"
              :loading="runningId === tpl.id"
              :disabled="runningId !== null && runningId !== tpl.id"
              @click="handleQuickRun(tpl)"
            >
              <el-icon v-if="runningId !== tpl.id" style="margin-right: 6px"><VideoPlay /></el-icon>
              {{ runningId === tpl.id ? '执行中...' : '虚拟设备运行' }}
            </el-button>
            <el-button
              size="large"
              class="config-btn"
              :disabled="runningId !== null"
              @click="openDevicePicker(tpl)"
            >
              <el-icon style="margin-right: 4px"><Monitor /></el-icon>
              选择设备
            </el-button>
            <el-dropdown trigger="click" @command="(cmd: string) => handleCardAction(cmd, tpl)">
              <el-button size="large" :disabled="runningId !== null">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit"><el-icon><Edit /></el-icon>编辑</el-dropdown-item>
                  <el-dropdown-item command="delete" divided><el-icon><Delete /></el-icon>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 设备选择抽屉 -->
    <el-drawer
      v-model="pickerVisible"
      title="选择测试设备"
      size="680px"
      :close-on-click-modal="false"
    >
      <div v-if="pickerTemplate">
        <el-descriptions :column="2" border size="small" style="margin-bottom: 16px">
          <el-descriptions-item label="场景">{{ pickerTemplate.name }}</el-descriptions-item>
          <el-descriptions-item label="已选设备">
            <el-tag type="primary" size="small">{{ selectedDevices.length }} 台</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 设备筛选 -->
        <el-form :inline="true" size="small" style="margin-bottom: 12px">
          <el-form-item label="搜索">
            <el-input
              v-model="deviceSearch"
              placeholder="SN / 名称"
              clearable
              style="width: 180px"
              @clear="loadDevices"
              @keyup.enter="loadDevices"
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="deviceStatusFilter" placeholder="全部" clearable style="width: 110px" @change="loadDevices">
              <el-option label="在线" value="online" />
              <el-option label="离线" value="offline" />
              <el-option label="占用" value="occupied" />
            </el-select>
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="deviceTypeFilter" placeholder="全部" clearable style="width: 130px" @change="loadDevices">
              <el-option label="真实设备" value="real" />
              <el-option label="V1 虚拟" value="virtual_l1" />
              <el-option label="V2 虚拟" value="virtual_l2" />
              <el-option label="V3 虚拟" value="virtual_l3" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="loadDevices">查询</el-button>
          </el-form-item>
        </el-form>

        <!-- 设备列表 -->
        <el-table
          ref="deviceTableRef"
          :data="deviceList"
          v-loading="deviceLoading"
          stripe
          height="360"
          empty-text="暂无匹配设备"
          @selection-change="handleDeviceSelect"
          row-key="device_sn"
        >
          <el-table-column type="selection" width="45" :selectable="isDeviceSelectable" />
          <el-table-column prop="device_sn" label="设备 SN" width="170">
            <template #default="{ row }">
              <span style="font-family: monospace; font-size: 12px">{{ row.device_sn }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="名称" width="140" />
          <el-table-column prop="device_type" label="类型" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="row.device_type === 'real' ? '' : 'info'">
                {{ row.device_type === 'real' ? '真实' : row.device_type.replace('virtual_', '虚拟').toUpperCase() }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="region" label="区域" width="80" />
          <el-table-column prop="temperature" label="温度" width="70">
            <template #default="{ row }">
              {{ row.temperature != null ? row.temperature + '°C' : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="last_heartbeat" label="最后心跳" min-width="140">
            <template #default="{ row }">
              {{ row.last_heartbeat ? formatDate(row.last_heartbeat) : '-' }}
            </template>
          </el-table-column>
        </el-table>

        <!-- 参数配置 -->
        <el-divider>运行参数</el-divider>
        <el-form label-position="top" size="default">
          <template v-for="field in pickerFields" :key="field.key">
            <el-form-item v-if="field.key === 'device_type'" :label="field.label">
              <el-radio-group v-model="pickerForm.device_type">
                <el-radio-button v-for="dt in catalog.device_types" :key="dt.value" :value="dt.value">
                  {{ dt.label }}
                </el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-else-if="field.key === 'product_key'" :label="field.label">
              <el-select v-model="pickerForm.product_key" style="width: 100%">
                <el-option
                  v-for="p in catalog.products"
                  :key="p.key"
                  :value="p.key"
                  :label="`${p.name} — ¥${p.price}`"
                />
              </el-select>
            </el-form-item>
            <el-form-item v-else-if="field.key === 'quantity'" :label="field.label">
              <el-input-number v-model="pickerForm.quantity" :min="field.min || 1" :max="field.max || 10" />
            </el-form-item>
            <el-form-item v-else-if="field.key === 'payment_method'" :label="field.label">
              <el-select v-model="pickerForm.payment_method" style="width: 100%">
                <el-option v-for="pm in catalog.payment_methods" :key="pm.value" :value="pm.value" :label="pm.label" />
              </el-select>
            </el-form-item>
            <el-form-item v-else-if="field.key === 'timeout_seconds'" :label="field.label">
              <el-input-number v-model="pickerForm.timeout_seconds" :min="field.min || 30" :max="field.max || 600" :step="30" />
            </el-form-item>
          </template>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="pickerVisible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="selectedDevices.length === 0"
          :loading="runningId === pickerTemplate?.id"
          @click="handleBatchRun"
        >
          <el-icon style="margin-right: 4px"><VideoPlay /></el-icon>
          在 {{ selectedDevices.length }} 台设备上运行
        </el-button>
      </template>
    </el-drawer>

    <!-- 参数配置抽屉（快速运行前的参数调整） -->
    <el-drawer v-model="configVisible" title="场景参数配置" size="420px" :close-on-click-modal="false">
      <div v-if="configTemplate">
        <el-descriptions :column="1" border size="small" style="margin-bottom: 20px">
          <el-descriptions-item label="场景">{{ configTemplate.name }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ configTemplate.category === 'shopping' ? '正常流程' : '异常场景' }}</el-descriptions-item>
        </el-descriptions>

        <el-form label-position="top" size="default">
          <template v-for="field in configFields" :key="field.key">
            <el-form-item v-if="field.key === 'device_type'" :label="field.label">
              <el-radio-group v-model="configForm.device_type" class="device-radio">
                <el-radio-button v-for="dt in catalog.device_types" :key="dt.value" :value="dt.value">
                  {{ dt.label }}
                </el-radio-button>
              </el-radio-group>
              <div class="field-hint">{{ catalog.device_types.find(d => d.value === configForm.device_type)?.desc }}</div>
            </el-form-item>
            <el-form-item v-else-if="field.key === 'product_key'" :label="field.label">
              <el-select v-model="configForm.product_key" style="width: 100%" @change="onProductChange">
                <el-option
                  v-for="p in catalog.products"
                  :key="p.key"
                  :value="p.key"
                  :label="`${p.name} — ¥${p.price}`"
                />
              </el-select>
            </el-form-item>
            <el-form-item v-else-if="field.key === 'quantity'" :label="field.label">
              <el-input-number v-model="configForm.quantity" :min="field.min || 1" :max="field.max || 10" />
              <div v-if="currentProduct" class="field-hint">
                小计: ¥{{ (currentProduct.price * configForm.quantity).toFixed(2) }}
              </div>
            </el-form-item>
            <el-form-item v-else-if="field.key === 'payment_method'" :label="field.label">
              <el-select v-model="configForm.payment_method" style="width: 100%">
                <el-option v-for="pm in catalog.payment_methods" :key="pm.value" :value="pm.value" :label="pm.label" />
              </el-select>
            </el-form-item>
            <el-form-item v-else-if="field.key === 'timeout_seconds'" :label="field.label">
              <el-input-number v-model="configForm.timeout_seconds" :min="field.min || 30" :max="field.max || 600" :step="30" />
              <div class="field-hint">秒</div>
            </el-form-item>
            <el-form-item v-else-if="field.type === 'number'" :label="field.label">
              <el-input-number v-model="configForm[field.key]" :min="field.min" :max="field.max" />
            </el-form-item>
          </template>
        </el-form>

        <el-divider>步骤预览</el-divider>
        <div class="preview-steps">
          <div v-for="(step, idx) in configTemplate.steps_definition.steps" :key="idx" class="preview-step">
            <el-icon :size="14" :color="configTemplate.color"><CircleCheck /></el-icon>
            <span class="preview-step-name">{{ step.name }}</span>
            <span class="preview-step-msg">{{ previewMessage(step.message_tpl || step.message || '') }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="configVisible = false">取消</el-button>
        <el-button type="primary" :loading="runningId === configTemplate?.id" @click="handleConfigRun">
          <el-icon style="margin-right: 4px"><VideoPlay /></el-icon>
          确认运行
        </el-button>
      </template>
    </el-drawer>

    <!-- 执行进度弹窗 -->
    <el-dialog
      v-model="progressVisible"
      title="场景执行中"
      width="640px"
      :close-on-click-modal="false"
      :show-close="false"
    >
      <div v-if="batchResult">
        <!-- 批量执行进度 -->
        <div class="batch-progress-header">
          <el-tag :type="batchResult.status === 'passed' ? 'success' : batchResult.status === 'partial' ? 'warning' : 'danger'" size="default">
            {{ batchStatusLabel(batchResult.status) }}
          </el-tag>
          <span style="margin-left: 12px; color: #666">
            共 {{ batchResult.total_count }} 台 · 通过 {{ batchResult.executions.filter(e => e.status === 'passed').length }}
            · 失败 {{ batchResult.executions.filter(e => e.status === 'failed').length }}
          </span>
        </div>
        <el-table :data="batchResult.executions" stripe size="small" style="margin-top: 12px">
          <el-table-column prop="device_sn" label="设备 SN" width="180">
            <template #default="{ row }">
              <span style="font-family: monospace; font-size: 12px">{{ row.device_sn }}</span>
              <el-tag v-if="row.is_real_device" size="small" type="warning" style="margin-left: 4px">真实</el-tag>
              <el-tag v-else size="small" type="info" style="margin-left: 4px">虚拟</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'passed' ? 'success' : 'danger'" size="small">
                {{ row.status === 'passed' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total_duration_ms" label="耗时" width="90">
            <template #default="{ row }">{{ row.total_duration_ms.toFixed(0) }} ms</template>
          </el-table-column>
          <el-table-column label="步骤" min-width="200">
            <template #default="{ row }">
              <span v-for="(step, idx) in row.steps" :key="idx" style="margin-right: 6px">
                <el-icon :size="13" :color="step.status === 'passed' ? '#67c23a' : '#f56c6c'">
                  <CircleCheckFilled v-if="step.status === 'passed'" />
                  <CircleCloseFilled v-else />
                </el-icon>
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else-if="currentRun" class="run-progress">
        <div class="run-info">
          <el-tag :type="currentRun.is_real_device ? 'warning' : 'info'" size="small">
            {{ currentRun.is_real_device ? '真实设备' : '虚拟设备' }}
          </el-tag>
          <el-tag type="info" size="small" style="margin-left: 8px">
            {{ currentRun.device_name || currentRun.device_sn }}
          </el-tag>
        </div>
        <el-steps :active="progressActiveStep" finish-status="success" align-center style="margin-top: 20px">
          <el-step
            v-for="step in progressSteps"
            :key="step.step"
            :title="step.name"
            :status="stepStatus(step)"
            :description="stepDesc(step)"
          />
        </el-steps>
      </div>
      <template #footer>
        <el-button v-if="runFinished" @click="progressVisible = false">关闭</el-button>
        <el-button v-if="runFinished && batchResult" type="primary" @click="showBatchDetail">查看详情</el-button>
      </template>
    </el-dialog>

    <!-- 单设备执行结果弹窗 -->
    <el-dialog v-model="resultVisible" title="执行结果" width="580px">
      <div v-if="lastResult" class="result-panel">
        <div class="result-header" :class="lastResult.status === 'passed' ? 'result-pass' : 'result-fail'">
          <el-icon :size="44">
            <CircleCheckFilled v-if="lastResult.status === 'passed'" />
            <CircleCloseFilled v-else />
          </el-icon>
          <div class="result-summary">
            <div class="result-status">{{ lastResult.status === 'passed' ? '执行成功' : '执行失败' }}</div>
            <div class="result-meta">
              场景: {{ lastResult.template_name }} · 耗时 {{ lastResult.total_duration_ms.toFixed(0) }} ms
            </div>
            <div class="result-meta">
              <el-tag :type="lastResult.is_real_device ? 'warning' : 'info'" size="small">
                {{ lastResult.is_real_device ? '真实设备' : '虚拟设备' }}
              </el-tag>
              {{ lastResult.device_name || lastResult.device_sn }}
            </div>
            <div v-if="lastResult.run_params" class="result-meta">
              商品 {{ lastResult.run_params.product_name }} x{{ lastResult.run_params.quantity }}
              · {{ lastResult.run_params.payment_label }} · ¥{{ lastResult.run_params.total_price }}
            </div>
          </div>
        </div>
        <el-divider />
        <div v-for="step in lastResult.steps" :key="step.step" class="result-step">
          <div class="result-step-row">
            <el-icon :size="15" :color="step.status === 'passed' ? '#67c23a' : '#f56c6c'">
              <CircleCheckFilled v-if="step.status === 'passed'" />
              <CircleCloseFilled v-else />
            </el-icon>
            <span class="result-step-name">{{ step.step }}. {{ step.name }}</span>
            <span class="result-step-time">{{ step.duration_ms.toFixed(0) }} ms</span>
          </div>
          <div v-if="step.detail" class="result-step-detail">{{ step.detail }}</div>
          <div v-if="step.error" class="result-step-error">{{ step.error }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="resultVisible = false">关闭</el-button>
        <el-button v-if="lastResult" type="primary" @click="handleRunById(lastResult.template_id)">重新运行</el-button>
      </template>
    </el-dialog>

    <!-- 批次详情弹窗 -->
    <el-dialog v-model="batchDetailVisible" title="批次执行详情" width="800px">
      <div v-if="batchDetailData">
        <el-descriptions :column="3" border size="small" style="margin-bottom: 16px">
          <el-descriptions-item label="批次名称">{{ batchDetailData.name }}</el-descriptions-item>
          <el-descriptions-item label="场景">{{ batchDetailData.template_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="batchDetailData.status === 'passed' ? 'success' : batchDetailData.status === 'partial' ? 'warning' : 'danger'" size="small">
              {{ batchStatusLabel(batchDetailData.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总数">{{ batchDetailData.total_count }}</el-descriptions-item>
          <el-descriptions-item label="通过">
            <span style="color: #67c23a; font-weight: bold">{{ batchDetailData.passed_count }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="失败">
            <span style="color: #f56c6c; font-weight: bold">{{ batchDetailData.failed_count }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-table :data="batchExecutions" stripe size="small" v-loading="batchExecLoading">
          <el-table-column prop="device_sn" label="设备 SN" width="170">
            <template #default="{ row }">
              <span style="font-family: monospace; font-size: 12px">{{ row.device_sn }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="device_name" label="设备名称" width="130" />
          <el-table-column label="类型" width="70">
            <template #default="{ row }">
              <el-tag v-if="row.is_real_device" size="small" type="warning">真实</el-tag>
              <el-tag v-else size="small" type="info">虚拟</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="结果" width="70">
            <template #default="{ row }">
              <el-tag :type="row.status === 'passed' ? 'success' : 'danger'" size="small">
                {{ row.status === 'passed' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total_duration_ms" label="耗时" width="80">
            <template #default="{ row }">
              {{ row.total_duration_ms ? row.total_duration_ms.toFixed(0) + ' ms' : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="执行时间" min-width="150">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 新建/编辑自定义场景对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      :title="editingTemplate ? '编辑场景' : '新建自定义场景'"
      width="720px"
      :close-on-click-modal="false"
    >
      <el-form :model="createForm" label-position="top" ref="createFormRef">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="场景名称" prop="name" :rules="[{ required: true, message: '请输入场景名称' }]">
              <el-input v-model="createForm.name" placeholder="如：自定义异常恢复测试" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="分类">
              <el-select v-model="createForm.category" style="width: 100%">
                <el-option label="正常流程" value="shopping" />
                <el-option label="异常场景" value="exception" />
                <el-option label="压力测试" value="stress" />
                <el-option label="自定义" value="custom" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="颜色">
              <el-color-picker v-model="createForm.color" :predefine="['#67c23a', '#e6a23c', '#f56c6c', '#1890ff', '#909399', '#8B5CF6']" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" placeholder="场景描述..." />
        </el-form-item>

        <el-divider>场景步骤</el-divider>
        <div class="step-editor">
          <div v-for="(step, idx) in createForm.steps" :key="idx" class="step-editor-row">
            <span class="step-num">{{ idx + 1 }}</span>
            <el-input v-model="step.name" placeholder="步骤名称" style="width: 160px" />
            <el-select v-model="step.event_type" placeholder="事件类型" style="width: 150px">
              <el-option label="开门" value="door_open" />
              <el-option label="关门" value="door_close" />
              <el-option label="商品检测" value="item_detected" />
              <el-option label="支付" value="payment" />
              <el-option label="AI 识别" value="ai_recognition" />
              <el-option label="心跳" value="heartbeat" />
              <el-option label="故障" value="fault" />
              <el-option label="错误" value="error" />
              <el-option label="警告" value="warning" />
              <el-option label="信息" value="info" />
              <el-option label="控制指令" value="control" />
            </el-select>
            <el-input v-model="step.message_tpl" placeholder="消息模板 (可选)" style="flex: 1" />
            <el-button :icon="Delete" circle size="small" type="danger" @click="removeStep(idx)" :disabled="createForm.steps.length <= 1" />
          </div>
          <el-button type="primary" link :icon="Plus" @click="addStep" style="margin-top: 8px">添加步骤</el-button>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createSaving" @click="handleSaveTemplate">
          {{ editingTemplate ? '保存修改' : '创建场景' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 公共执行历史 -->
    <el-card class="history-card" style="margin-top: 24px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <div>
            <span>公共执行历史</span>
            <el-radio-group v-model="historyTab" size="small" style="margin-left: 16px" @change="switchHistory">
              <el-radio-button value="executions">单次执行</el-radio-button>
              <el-radio-button value="batches">批量批次</el-radio-button>
            </el-radio-group>
          </div>
          <el-button size="small" :icon="Refresh" @click="loadHistory">刷新</el-button>
        </div>
      </template>

      <!-- 单次执行历史 -->
      <el-table v-if="historyTab === 'executions'" :data="history" stripe v-loading="historyLoading" empty-text="暂无执行记录">
        <el-table-column prop="triggered_by_name" label="执行人" width="100">
          <template #default="{ row }">
            <el-icon style="margin-right: 4px; vertical-align: middle"><User /></el-icon>
            {{ row.triggered_by_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="template_name" label="场景" width="160" />
        <el-table-column label="设备" width="180">
          <template #default="{ row }">
            <span style="font-family: monospace; font-size: 12px">{{ row.device_sn }}</span>
            <el-tag v-if="row.is_real_device" size="small" type="warning" style="margin-left: 4px">真实</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="参数" width="180">
          <template #default="{ row }">
            <template v-if="row.run_params">
              <el-tag size="small" type="info">{{ row.run_params.product_name || '-' }}</el-tag>
              <span v-if="row.run_params.quantity" style="margin-left: 4px; font-size: 12px; color: #999">x{{ row.run_params.quantity }}</span>
            </template>
            <span v-else style="color: #ccc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="结果" width="70">
          <template #default="{ row }">
            <el-tag :type="row.status === 'passed' ? 'success' : 'danger'" size="small">
              {{ row.status === 'passed' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_duration_ms" label="耗时" width="80">
          <template #default="{ row }">
            {{ row.total_duration_ms ? row.total_duration_ms.toFixed(0) + ' ms' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="执行时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <!-- 批量批次历史 -->
      <el-table v-else :data="batchHistory" stripe v-loading="historyLoading" empty-text="暂无批量执行记录" @row-click="openBatchDetail">
        <el-table-column prop="triggered_by_name" label="执行人" width="100">
          <template #default="{ row }">
            <el-icon style="margin-right: 4px; vertical-align: middle"><User /></el-icon>
            {{ row.triggered_by_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="template_name" label="场景" width="160" />
        <el-table-column prop="name" label="批次名称" width="200" />
        <el-table-column label="设备数" width="80">
          <template #default="{ row }">{{ row.total_count }} 台</template>
        </el-table-column>
        <el-table-column label="通过率" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.total_count > 0 ? Math.round(row.passed_count / row.total_count * 100) : 0"
              :color="row.failed_count === 0 ? '#67c23a' : '#e6a23c'"
              :stroke-width="14"
              :text-inside="true"
            />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'passed' ? 'success' : row.status === 'partial' ? 'warning' : 'danger'" size="small">
              {{ batchStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="执行时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click.stop="openBatchDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import {
  Refresh, VideoPlay, User, Setting, Monitor, Search, Plus, Delete, Edit, MoreFilled,
  CircleCheck, CircleCheckFilled, CircleCloseFilled,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getScenarioTemplates,
  getScenarioCatalog,
  getScenarioDevices,
  runScenario,
  batchRunScenario,
  getScenarioExecutions,
  getScenarioBatches,
  createScenarioTemplate,
  updateScenarioTemplate,
  deleteScenarioTemplate,
  type ScenarioTemplate,
  type ScenarioRunResponse,
  type BatchRunResponse,
  type ScenarioExecution,
  type BatchRecord,
  type StepResult,
  type CatalogData,
  type ScenarioRunRequest,
  type DevicePickItem,
} from '@/api/scenario'
import { formatDate } from '@/utils/format'

const templates = ref<ScenarioTemplate[]>([])
const history = ref<ScenarioExecution[]>([])
const batchHistory = ref<BatchRecord[]>([])
const historyLoading = ref(false)
const historyTab = ref<'executions' | 'batches'>('executions')
const catalog = ref<CatalogData>({ products: [], device_types: [], payment_methods: [] })

const runningId = ref<number | null>(null)
const progressVisible = ref(false)
const resultVisible = ref(false)
const currentRun = ref<ScenarioRunResponse | null>(null)
const lastResult = ref<ScenarioRunResponse | null>(null)
const batchResult = ref<BatchRunResponse | null>(null)
const runFinished = ref(false)

// 设备选择器
const pickerVisible = ref(false)
const pickerTemplate = ref<ScenarioTemplate | null>(null)
const deviceList = ref<DevicePickItem[]>([])
const deviceLoading = ref(false)
const deviceSearch = ref('')
const deviceStatusFilter = ref('')
const deviceTypeFilter = ref('')
const selectedDevices = ref<DevicePickItem[]>([])
const deviceTableRef = ref<any>(null)

const pickerForm = reactive<Record<string, any>>({
  device_type: 'V1',
  product_key: 'cola',
  quantity: 2,
  payment_method: 'wechat',
  timeout_seconds: 120,
})

// 快速运行参数配置
const configVisible = ref(false)
const configTemplate = ref<ScenarioTemplate | null>(null)
const configForm = reactive<Record<string, any>>({
  device_type: 'V1',
  product_key: 'cola',
  quantity: 2,
  payment_method: 'wechat',
  timeout_seconds: 120,
})

// 批次详情
const batchDetailVisible = ref(false)
const batchDetailData = ref<BatchRecord | null>(null)
const batchExecutions = ref<ScenarioExecution[]>([])
const batchExecLoading = ref(false)

// 新建/编辑场景
const createDialogVisible = ref(false)
const createSaving = ref(false)
const editingTemplate = ref<ScenarioTemplate | null>(null)
const createFormRef = ref<any>(null)
const createForm = reactive({
  name: '',
  description: '',
  category: 'custom',
  color: '#1890ff',
  steps: [{ name: '', event_type: 'info', message_tpl: '' }] as Array<{ name: string; event_type: string; message_tpl: string }>,
})

const configFields = computed(() => configTemplate.value?.params_schema?.fields || [])
const pickerFields = computed(() => pickerTemplate.value?.params_schema?.fields || [])
const currentProduct = computed(() => catalog.value.products.find(p => p.key === configForm.product_key))

const progressSteps = computed(() => currentRun.value?.steps || [])
const progressActiveStep = computed(() => {
  if (!currentRun.value) return 0
  return currentRun.value.steps.filter(s => s.status === 'passed' || s.status === 'failed').length
})

function stepStatus(step: StepResult): string {
  if (step.status === 'passed') return 'success'
  if (step.status === 'failed') return 'error'
  return 'wait'
}

function stepDesc(step: StepResult): string {
  if (step.status === 'passed') return step.detail || `${step.duration_ms.toFixed(0)} ms`
  if (step.status === 'failed') return step.error || '执行失败'
  return '等待中'
}

function statusType(status: string): string {
  if (status === 'online') return 'success'
  if (status === 'offline') return 'info'
  if (status === 'occupied') return 'warning'
  if (status === 'fault') return 'danger'
  return 'info'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = { online: '在线', offline: '离线', occupied: '占用', maintenance: '维护', fault: '故障' }
  return map[status] || status
}

function batchStatusLabel(status: string): string {
  const map: Record<string, string> = { running: '执行中', passed: '全部通过', partial: '部分通过', failed: '全部失败' }
  return map[status] || status
}

function isDeviceSelectable(row: DevicePickItem): boolean {
  return row.status !== 'maintenance' && row.status !== 'fault'
}

function onProductChange() {}

function previewMessage(tpl: string): string {
  try {
    const product = currentProduct.value
    const pm = catalog.value.payment_methods.find(m => m.value === configForm.payment_method)
    const dt = catalog.value.device_types.find(d => d.value === configForm.device_type)
    const total = product ? (product.price * configForm.quantity).toFixed(2) : '0.00'
    return tpl
      .replace('{device_type}', dt?.label || configForm.device_type)
      .replace('{product_name}', product?.name || configForm.product_key)
      .replace('{quantity}', String(configForm.quantity))
      .replace('{total_price}', total)
      .replace('{payment_label}', pm?.label || configForm.payment_method)
      .replace('{timeout_seconds}', String(configForm.timeout_seconds))
      .replace('{confidence}', '97')
  } catch {
    return tpl
  }
}

// ── 数据加载 ──────────────────────────────────────────────────

async function loadTemplates() {
  try {
    templates.value = await getScenarioTemplates()
  } catch (e) {
    console.error('[Workbench] loadTemplates failed:', e)
  }
}

async function loadCatalog() {
  try {
    catalog.value = await getScenarioCatalog()
  } catch (e) {
    console.error('[Workbench] loadCatalog failed:', e)
  }
}

async function loadDevices() {
  deviceLoading.value = true
  try {
    const params: Record<string, any> = { limit: 100 }
    if (deviceSearch.value) params.search = deviceSearch.value
    if (deviceStatusFilter.value) params.status = deviceStatusFilter.value
    if (deviceTypeFilter.value) params.device_type = deviceTypeFilter.value
    deviceList.value = await getScenarioDevices(params)
  } catch (e) {
    console.error('[Workbench] loadDevices failed:', e)
  } finally {
    deviceLoading.value = false
  }
}

function handleDeviceSelect(rows: DevicePickItem[]) {
  selectedDevices.value = rows
}

async function loadHistory() {
  historyLoading.value = true
  try {
    if (historyTab.value === 'executions') {
      const res = await getScenarioExecutions({ limit: 50 })
      history.value = res.items || []
    } else {
      const res = await getScenarioBatches({ limit: 50 })
      batchHistory.value = res.items || []
    }
  } catch (e) {
    console.error('[Workbench] loadHistory failed:', e)
  } finally {
    historyLoading.value = false
  }
}

function switchHistory() {
  loadHistory()
}

// ── 设备选择 & 批量运行 ──────────────────────────────────────

function openDevicePicker(tpl: ScenarioTemplate) {
  pickerTemplate.value = tpl
  // 重置表单默认值
  const fields = tpl.params_schema?.fields || []
  for (const f of fields) {
    if (f.default !== undefined) pickerForm[f.key] = f.default
  }
  selectedDevices.value = []
  deviceSearch.value = ''
  deviceStatusFilter.value = ''
  deviceTypeFilter.value = ''
  pickerVisible.value = true
  loadDevices()
}

function handleBatchRun() {
  if (!pickerTemplate.value || selectedDevices.value.length === 0) return
  pickerVisible.value = false

  const params: ScenarioRunRequest = {
    device_sns: selectedDevices.value.map(d => d.device_sn),
    device_type: pickerForm.device_type,
    product_key: pickerForm.product_key,
    quantity: pickerForm.quantity,
    payment_method: pickerForm.payment_method,
    timeout_seconds: pickerForm.timeout_seconds,
  }

  doBatchRun(pickerTemplate.value, params)
}

async function doBatchRun(tpl: ScenarioTemplate, params: ScenarioRunRequest) {
  runningId.value = tpl.id
  runFinished.value = false
  resultVisible.value = false
  batchResult.value = null
  progressVisible.value = true

  try {
    const res = await batchRunScenario(tpl.id, params)
    batchResult.value = res
    runFinished.value = true

    if (res.status === 'passed') {
      ElMessage.success(`批量执行完成：${res.total_count} 台设备全部通过`)
    } else if (res.status === 'partial') {
      ElMessage.warning(`批量执行完成：${res.executions.filter(e => e.status === 'passed').length}/${res.total_count} 台通过`)
    } else {
      ElMessage.error(`批量执行完成：${res.total_count} 台设备全部失败`)
    }
    loadHistory()
  } catch (e: any) {
    ElMessage.error('批量执行失败: ' + (e.message || '未知错误'))
    runFinished.value = true
  } finally {
    runningId.value = null
  }
}

// ── 快速运行（虚拟设备）──────────────────────────────────────

function openConfig(tpl: ScenarioTemplate) {
  configTemplate.value = tpl
  const fields = tpl.params_schema?.fields || []
  for (const f of fields) {
    if (f.default !== undefined) configForm[f.key] = f.default
  }
  configVisible.value = true
}

function buildRunParams(): ScenarioRunRequest {
  return {
    device_sns: [],
    device_type: configForm.device_type,
    product_key: configForm.product_key,
    quantity: configForm.quantity,
    payment_method: configForm.payment_method,
    timeout_seconds: configForm.timeout_seconds,
  }
}

function handleQuickRun(tpl: ScenarioTemplate) {
  configTemplate.value = tpl
  const fields = tpl.params_schema?.fields || []
  for (const f of fields) {
    if (f.default !== undefined) configForm[f.key] = f.default
  }
  doRun(tpl, buildRunParams())
}

function handleConfigRun() {
  if (!configTemplate.value) return
  configVisible.value = false
  doRun(configTemplate.value, buildRunParams())
}

function handleRunById(templateId: number) {
  const tpl = templates.value.find(t => t.id === templateId)
  if (tpl) handleQuickRun(tpl)
}

async function doRun(tpl: ScenarioTemplate, params: ScenarioRunRequest) {
  runningId.value = tpl.id
  runFinished.value = false
  resultVisible.value = false
  batchResult.value = null

  currentRun.value = {
    execution_id: 0,
    batch_id: null,
    template_id: tpl.id,
    template_name: tpl.name,
    device_sn: '...',
    device_name: null,
    is_real_device: false,
    run_params: null,
    status: 'passed',
    total_duration_ms: 0,
    steps: tpl.steps_definition.steps.map((s, i) => ({
      step: i + 1,
      name: s.name,
      status: 'passed' as const,
      duration_ms: 0,
      detail: '',
      error: null,
    })),
  }
  progressVisible.value = true

  try {
    const res = await runScenario(tpl.id, params)
    currentRun.value = res
    lastResult.value = res
    runFinished.value = true

    setTimeout(() => {
      progressVisible.value = false
      resultVisible.value = true
    }, 600)

    if (res.status === 'passed') {
      ElMessage.success(`场景「${tpl.name}」执行成功`)
    } else {
      ElMessage.warning(`场景「${tpl.name}」存在失败步骤`)
    }
    loadHistory()
  } catch (e: any) {
    ElMessage.error('场景执行失败: ' + (e.message || '未知错误'))
    runFinished.value = true
  } finally {
    runningId.value = null
  }
}

// ── 批次详情 ─────────────────────────────────────────────────

function showBatchDetail() {
  if (!batchResult.value) return
  progressVisible.value = false
  batchDetailData.value = {
    id: batchResult.value.batch_id,
    template_id: batchResult.value.template_id,
    template_name: batchResult.value.template_name,
    name: `批次 #${batchResult.value.batch_id}`,
    total_count: batchResult.value.total_count,
    passed_count: batchResult.value.executions.filter(e => e.status === 'passed').length,
    failed_count: batchResult.value.executions.filter(e => e.status === 'failed').length,
    status: batchResult.value.status,
    run_params: null,
    triggered_by_name: null,
    created_at: new Date().toISOString(),
    finished_at: new Date().toISOString(),
  }
  batchExecutions.value = batchResult.value.executions.map(e => ({
    id: e.execution_id,
    batch_id: e.batch_id,
    template_id: e.template_id,
    template_name: e.template_name,
    device_sn: e.device_sn,
    device_name: e.device_name,
    is_real_device: e.is_real_device,
    run_params: e.run_params,
    status: e.status,
    steps_result: e.steps,
    total_duration_ms: e.total_duration_ms,
    error_message: null,
    triggered_by_name: null,
    created_at: new Date().toISOString(),
    finished_at: new Date().toISOString(),
  }))
  batchDetailVisible.value = true
}

async function openBatchDetail(row: BatchRecord) {
  batchDetailData.value = row
  batchExecLoading.value = true
  batchDetailVisible.value = true
  try {
    const res = await getScenarioExecutions({ batch_id: row.id, limit: 200 })
    batchExecutions.value = res.items || []
  } catch (e) {
    console.error('[Workbench] loadBatchExecutions failed:', e)
  } finally {
    batchExecLoading.value = false
  }
}

// ── 自定义场景 CRUD ────────────────────────────────────────────

function openCreateDialog() {
  editingTemplate.value = null
  createForm.name = ''
  createForm.description = ''
  createForm.category = 'custom'
  createForm.color = '#1890ff'
  createForm.steps = [{ name: '', event_type: 'info', message_tpl: '' }]
  createDialogVisible.value = true
}

function openEditDialog(tpl: ScenarioTemplate) {
  editingTemplate.value = tpl
  createForm.name = tpl.name
  createForm.description = tpl.description
  createForm.category = tpl.category
  createForm.color = tpl.color
  createForm.steps = (tpl.steps_definition?.steps || []).map(s => ({
    name: s.name || '',
    event_type: s.event_type || 'info',
    message_tpl: s.message_tpl || s.message || '',
  }))
  if (createForm.steps.length === 0) {
    createForm.steps = [{ name: '', event_type: 'info', message_tpl: '' }]
  }
  createDialogVisible.value = true
}

function addStep() {
  createForm.steps.push({ name: '', event_type: 'info', message_tpl: '' })
}

function removeStep(idx: number) {
  createForm.steps.splice(idx, 1)
}

async function handleSaveTemplate() {
  if (!createForm.name.trim()) {
    ElMessage.warning('请输入场景名称')
    return
  }
  const validSteps = createForm.steps.filter(s => s.name.trim())
  if (validSteps.length === 0) {
    ElMessage.warning('至少添加一个步骤')
    return
  }

  createSaving.value = true
  try {
    const data: Partial<ScenarioTemplate> = {
      name: createForm.name,
      description: createForm.description,
      category: createForm.category,
      color: createForm.color,
      icon: 'Setting',
      steps_definition: { steps: validSteps },
      params_schema: null,
      wiremock_mapping: null,
      sort_order: 99,
      is_active: true,
    }

    if (editingTemplate.value) {
      await updateScenarioTemplate(editingTemplate.value.id, data)
      ElMessage.success('场景已更新')
    } else {
      await createScenarioTemplate(data)
      ElMessage.success('场景已创建')
    }
    createDialogVisible.value = false
    loadTemplates()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  } finally {
    createSaving.value = false
  }
}

function handleCardAction(cmd: string, tpl: ScenarioTemplate) {
  if (cmd === 'edit') {
    openEditDialog(tpl)
  } else if (cmd === 'delete') {
    ElMessageBox.confirm(`确定删除场景「${tpl.name}」？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    }).then(async () => {
      try {
        await deleteScenarioTemplate(tpl.id)
        ElMessage.success('已删除')
        loadTemplates()
      } catch (e: any) {
        ElMessage.error('删除失败: ' + (e.message || '未知错误'))
      }
    }).catch(() => {})
  }
}

onMounted(() => {
  loadTemplates()
  loadCatalog()
  loadHistory()
})
</script>

<style scoped lang="scss">
.workbench-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  h2 { margin: 0; font-size: 22px; }
  .subtitle { color: #999; margin: 4px 0 0; font-size: 14px; }
}

.template-cards {
  .template-card {
    margin-bottom: 20px;
    transition: all 0.3s;
    &:hover { transform: translateY(-4px); }
    &.is-running { border-color: #1890ff; box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.15); }
  }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  .card-icon {
    width: 48px; height: 48px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
  }
  .card-title { margin: 0 0 8px; font-size: 18px; font-weight: 600; }
  .card-desc {
    color: #666; font-size: 13px; line-height: 1.6;
    margin: 0 0 16px; min-height: 42px;
  }
  .card-steps {
    display: flex; flex-wrap: wrap; align-items: center; gap: 4px; margin-bottom: 16px;
    .step-item { display: flex; align-items: center; gap: 4px; }
    .step-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
    .step-text { font-size: 12px; color: #666; }
    .step-arrow { color: #ccc; font-size: 12px; margin: 0 2px; }
  }
  .card-actions {
    display: flex; gap: 8px;
    .run-btn { flex: 1; }
    .config-btn { flex-shrink: 0; }
  }
}

.device-radio {
  :deep(.el-radio-button__inner) { padding: 8px 16px; }
}
.field-hint { font-size: 12px; color: #999; margin-top: 4px; }

.preview-steps {
  .preview-step {
    display: flex; align-items: flex-start; gap: 8px; padding: 6px 0;
    border-bottom: 1px dashed #f5f5f5;
    &:last-child { border-bottom: none; }
    .preview-step-name { font-weight: 500; font-size: 13px; white-space: nowrap; }
    .preview-step-msg { font-size: 12px; color: #666; word-break: break-all; }
  }
}

.batch-progress-header {
  display: flex; align-items: center; margin-bottom: 8px;
}

.run-progress {
  .run-info { text-align: center; }
}

.result-panel {
  .result-header {
    display: flex; align-items: center; gap: 16px; padding: 12px 0;
    &.result-pass { color: #67c23a; }
    &.result-fail { color: #f56c6c; }
    .result-status { font-size: 20px; font-weight: bold; }
    .result-meta { font-size: 13px; color: #999; margin-top: 2px; }
  }
  .result-step {
    padding: 8px 0; border-bottom: 1px dashed #f0f0f0;
    &:last-child { border-bottom: none; }
    .result-step-row { display: flex; align-items: center; gap: 8px; }
    .result-step-name { flex: 1; font-size: 14px; }
    .result-step-time { font-size: 12px; color: #999; }
    .result-step-detail { margin-left: 23px; font-size: 12px; color: #666; margin-top: 4px; }
    .result-step-error { margin-left: 23px; font-size: 12px; color: #f56c6c; margin-top: 4px; }
  }
}

.step-editor {
  .step-editor-row {
    display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
    .step-num {
      width: 24px; height: 24px; border-radius: 50%; background: #f0f0f0;
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; font-weight: 600; color: #666; flex-shrink: 0;
    }
  }
}
</style>
