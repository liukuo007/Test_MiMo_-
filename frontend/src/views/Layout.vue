<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
      <div class="logo" @click="router.push('/')">
        <span v-if="!isCollapse">MiMo</span>
        <span v-else>M</span>
      </div>
      <el-menu :default-active="route.path" router :collapse="isCollapse" class="side-menu">
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item index="/scenarios">
          <el-icon><MagicStick /></el-icon>
          <span>场景工作台</span>
        </el-menu-item>
        <el-menu-item index="/projects">
          <el-icon><Folder /></el-icon>
          <span>项目管理</span>
        </el-menu-item>
        <el-sub-menu index="devices-menu">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>设备农场</span>
          </template>
          <el-menu-item index="/devices">设备列表</el-menu-item>
          <el-menu-item index="/devices/mesh">设备网格</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/environments">
          <el-icon><OfficeBuilding /></el-icon>
          <span>环境治理</span>
        </el-menu-item>
        <el-menu-item index="/test-cases">
          <el-icon><Document /></el-icon>
          <span>用例管理</span>
        </el-menu-item>
        <el-menu-item index="/test-tasks">
          <el-icon><List /></el-icon>
          <span>任务管理</span>
        </el-menu-item>
        <el-menu-item index="/defects">
          <el-icon><Warning /></el-icon>
          <span>缺陷管理</span>
        </el-menu-item>
        <el-menu-item index="/schedules">
          <el-icon><Clock /></el-icon>
          <span>定时任务</span>
        </el-menu-item>
        <el-sub-menu index="ai">
          <template #title>
            <el-icon><Cpu /></el-icon>
            <span>AI 验证</span>
          </template>
          <el-menu-item index="/ai/datasets">数据集管理</el-menu-item>
          <el-menu-item index="/ai/evaluations">模型评测</el-menu-item>
          <el-menu-item index="/ai/compare">模型对比</el-menu-item>
          <el-menu-item index="/ai/copilot">AI 助手</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="quality">
          <template #title>
            <el-icon><Trophy /></el-icon>
            <span>质量管理</span>
          </template>
          <el-menu-item index="/quality/gate">质量门禁</el-menu-item>
          <el-menu-item index="/quality/report">质量报告</el-menu-item>
          <el-menu-item index="/quality/health-score">健康评分</el-menu-item>
          <el-menu-item index="/quality/stability">稳定性治理</el-menu-item>
          <el-menu-item index="/quality/loop">质量闭环</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/regions">
          <el-icon><Globe /></el-icon>
          <span>全球运营</span>
        </el-menu-item>
        <el-menu-item index="/load-test">
          <el-icon><Odometer /></el-icon>
          <span>压测中心</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown>
            <span class="user-info">
              {{ userStore.userInfo?.full_name || userStore.userInfo?.username }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(false)

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
}
.layout-aside {
  background: #304156;
  transition: width 0.3s;
  overflow: hidden;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
  font-weight: bold;
  cursor: pointer;
}
.side-menu {
  border-right: none;
  background: #304156;
  :deep(.el-menu-item),
  :deep(.el-sub-menu__title) {
    color: #bfcbd9;
    &:hover {
      background: #263445;
    }
  }
  :deep(.el-menu-item.is-active) {
    background: #1890ff !important;
    color: #fff;
  }
}
.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #eee;
  background: #fff;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.collapse-btn {
  font-size: 20px;
  cursor: pointer;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}
.layout-main {
  background: #f0f2f5;
  padding: 20px;
}
</style>
