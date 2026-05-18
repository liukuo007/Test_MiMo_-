<template>
  <div class="page">
    <h2 style="margin-bottom: 16px">系统设置</h2>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="基本信息" name="basic">
        <el-card>
          <el-form :model="basic" label-width="120px" style="max-width: 600px">
            <el-form-item label="平台名称">
              <el-input v-model="basic.name" />
            </el-form-item>
            <el-form-item label="平台描述">
              <el-input v-model="basic.description" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="默认环境">
              <el-select v-model="basic.default_env">
                <el-option label="开发环境" value="dev" />
                <el-option label="预发布环境" value="staging" />
                <el-option label="生产环境" value="prod" />
              </el-select>
            </el-form-item>
            <el-form-item label="时区">
              <el-select v-model="basic.timezone">
                <el-option label="Asia/Shanghai (UTC+8)" value="Asia/Shanghai" />
                <el-option label="America/New_York (UTC-5)" value="America/New_York" />
                <el-option label="Europe/London (UTC+0)" value="Europe/London" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSave('basic')">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="通知配置" name="notify">
        <el-card>
          <el-form :model="notify" label-width="120px" style="max-width: 600px">
            <el-form-item label="邮件通知">
              <el-switch v-model="notify.email_enabled" />
            </el-form-item>
            <el-form-item label="SMTP 服务器" v-if="notify.email_enabled">
              <el-input v-model="notify.smtp_host" placeholder="smtp.example.com" />
            </el-form-item>
            <el-form-item label="发件人" v-if="notify.email_enabled">
              <el-input v-model="notify.smtp_from" placeholder="noreply@mimo.local" />
            </el-form-item>
            <el-form-item label="Webhook 通知">
              <el-switch v-model="notify.webhook_enabled" />
            </el-form-item>
            <el-form-item label="Webhook URL" v-if="notify.webhook_enabled">
              <el-input v-model="notify.webhook_url" placeholder="https://hooks.example.com/xxx" />
            </el-form-item>
            <el-form-item label="通知事件" v-if="notify.webhook_enabled || notify.email_enabled">
              <el-checkbox-group v-model="notify.events">
                <el-checkbox label="task_completed">任务完成</el-checkbox>
                <el-checkbox label="task_failed">任务失败</el-checkbox>
                <el-checkbox label="quality_gate">质量门禁</el-checkbox>
                <el-checkbox label="device_offline">设备离线</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSave('notify')">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="引擎配置" name="engine">
        <el-card>
          <el-form :model="engine" label-width="140px" style="max-width: 600px">
            <el-form-item label="API 测试超时">
              <el-input-number v-model="engine.api_timeout" :min="5" :max="300" /> 秒
            </el-form-item>
            <el-form-item label="IoT 设备最大并发">
              <el-input-number v-model="engine.iot_max_concurrent" :min="1" :max="10000" />
            </el-form-item>
            <el-form-item label="AI 推理设备">
              <el-select v-model="engine.ai_device">
                <el-option label="CPU" value="cpu" />
                <el-option label="GPU (CUDA)" value="cuda" />
                <el-option label="MPS (Apple Silicon)" value="mps" />
              </el-select>
            </el-form-item>
            <el-form-item label="Web 测试引擎">
              <el-select v-model="engine.web_engine_type">
                <el-option label="Playwright" value="playwright" />
                <el-option label="Selenium" value="selenium" />
              </el-select>
            </el-form-item>
            <el-form-item label="Appium 服务地址">
              <el-input v-model="engine.appium_url" placeholder="http://localhost:4723" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSave('engine')">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="CI/CD 集成" name="cicd">
        <el-card>
          <el-form :model="cicd" label-width="140px" style="max-width: 600px">
            <el-form-item label="Webhook 触发地址">
              <el-input :model-value="cicd.webhook_url" disabled />
              <div class="form-hint">外部 CI 系统通过 POST 请求此地址触发测试</div>
            </el-form-item>
            <el-form-item label="回调 URL">
              <el-input v-model="cicd.callback_url" placeholder="https://ci.example.com/callback" />
              <div class="form-hint">任务完成后自动回调通知此地址</div>
            </el-form-item>
            <el-form-item label="默认分支">
              <el-input v-model="cicd.default_branch" placeholder="main" />
            </el-form-item>
            <el-form-item label="Commit SHA 传递">
              <el-switch v-model="cicd.pass_commit_sha" />
              <div class="form-hint">是否在回调中传递 commit SHA</div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSave('cicd')">保存</el-button>
            </el-form-item>
          </el-form>

          <el-divider />
          <h4>最近流水线执行</h4>
          <el-table :data="pipelines" stripe style="margin-top: 12px">
            <el-table-column prop="task_id" label="任务ID" width="80" />
            <el-table-column prop="branch" label="分支" width="120" />
            <el-table-column prop="commit_sha" label="Commit" width="120">
              <template #default="{ row }">{{ row.commit_sha?.substring(0, 8) || '-' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'passed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="pass_rate" label="通过率" width="100">
              <template #default="{ row }">{{ row.pass_rate || 0 }}%</template>
            </el-table-column>
            <el-table-column prop="triggered_at" label="触发时间" width="170">
              <template #default="{ row }">{{ formatTime(row.triggered_at) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="用户管理" name="users">
        <el-card>
          <el-table :data="users" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="full_name" label="姓名" />
            <el-table-column prop="role" label="角色" width="100">
              <template #default="{ row }"><el-tag size="small">{{ row.role }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="email" label="邮箱" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link type="primary" size="small">编辑</el-button>
                <el-button link type="danger" size="small" :disabled="row.username === 'admin'">禁用</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, updateSettings, getSettingsUsers } from '@/api/settings'

const activeTab = ref('basic')

const basic = ref({
  name: 'MiMo - 智能货柜全链路测试平台',
  description: '智能货柜质量基础设施',
  default_env: 'dev',
  timezone: 'Asia/Shanghai',
})

const notify = ref({
  email_enabled: true, smtp_host: 'smtp.mimo.local', smtp_from: 'noreply@mimo.local',
  webhook_enabled: false, webhook_url: '', events: ['task_completed', 'task_failed'],
})

const engine = ref({
  api_timeout: 30, iot_max_concurrent: 1000, ai_device: 'cuda',
  web_engine_type: 'playwright', appium_url: 'http://localhost:4723',
})

const cicd = ref({
  webhook_url: window.location.origin + '/api/v1/webhooks/trigger',
  callback_url: '',
  default_branch: 'main',
  pass_commit_sha: true,
})

const pipelines = ref<any[]>([])
const users = ref<any[]>([])

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(async () => {
  try {
    const [settingsData, usersData] = await Promise.all([
      getSettings(),
      getSettingsUsers(),
    ])
    if (settingsData) {
      const s = settingsData as any
      if (s.basic) Object.assign(basic.value, s.basic)
      if (s.notify) Object.assign(notify.value, s.notify)
      if (s.engine) Object.assign(engine.value, s.engine)
      if (s.cicd) Object.assign(cicd.value, s.cicd)
    }
    users.value = usersData as any[]
  } catch {
    // fallback
  }

  // 加载流水线记录
  try {
    const { default: request } = await import('@/api/request')
    pipelines.value = await request.get('/webhooks/pipelines')
  } catch {
    // fallback
  }
})

async function handleSave(section: string) {
  try {
    const data: Record<string, any> = {}
    if (section === 'basic') data.basic = basic.value
    else if (section === 'notify') data.notify = notify.value
    else if (section === 'engine') data.engine = engine.value
    else if (section === 'cicd') data.cicd = cicd.value
    await updateSettings(data)
    ElMessage.success(`${section} 配置已保存`)
  } catch {
    ElMessage.error('保存失败')
  }
}
</script>

<style scoped lang="scss">
.page { padding: 0; }
.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
