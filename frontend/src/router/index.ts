import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
    },
    {
      path: '/',
      component: () => import('@/views/Layout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/Index.vue'),
          meta: { title: '数据看板' },
        },
        {
          path: 'projects',
          name: 'Projects',
          component: () => import('@/views/project/List.vue'),
          meta: { title: '项目管理' },
        },
        {
          path: 'projects/:id',
          name: 'ProjectDetail',
          component: () => import('@/views/project/Detail.vue'),
          meta: { title: '项目详情' },
        },
        {
          path: 'devices',
          name: 'Devices',
          component: () => import('@/views/device/Farm.vue'),
          meta: { title: '设备农场' },
        },
        {
          path: 'devices/:id',
          name: 'DeviceDetail',
          component: () => import('@/views/device/Detail.vue'),
          meta: { title: '设备详情' },
        },
        {
          path: 'devices/mesh',
          name: 'DeviceMesh',
          component: () => import('@/views/device/Mesh.vue'),
          meta: { title: '设备网格' },
        },
        {
          path: 'test-cases',
          name: 'TestCases',
          component: () => import('@/views/test_case/List.vue'),
          meta: { title: '用例管理' },
        },
        {
          path: 'test-cases/:id/edit',
          name: 'TestCaseEditor',
          component: () => import('@/views/test_case/Editor.vue'),
          meta: { title: '编辑用例' },
        },
        {
          path: 'test-tasks',
          name: 'TestTasks',
          component: () => import('@/views/test_task/List.vue'),
          meta: { title: '任务管理' },
        },
        {
          path: 'test-tasks/create',
          name: 'CreateTestTask',
          component: () => import('@/views/test_task/Create.vue'),
          meta: { title: '创建任务' },
        },
        {
          path: 'test-tasks/:id',
          name: 'TestTaskDetail',
          component: () => import('@/views/test_task/Detail.vue'),
          meta: { title: '任务详情' },
        },
        {
          path: 'test-tasks/dag-editor',
          name: 'DAGEditor',
          component: () => import('@/views/test_task/DAGEditor.vue'),
          meta: { title: 'DAG 编排' },
        },
        {
          path: 'ai/datasets',
          name: 'AIDataSets',
          component: () => import('@/views/ai_verify/DataSet.vue'),
          meta: { title: '数据集管理' },
        },
        {
          path: 'ai/evaluations',
          name: 'AIEvaluations',
          component: () => import('@/views/ai_verify/Evaluation.vue'),
          meta: { title: 'AI 评测' },
        },
        {
          path: 'ai/compare',
          name: 'AICompare',
          component: () => import('@/views/ai_verify/Compare.vue'),
          meta: { title: '模型对比' },
        },
        {
          path: 'ai/copilot',
          name: 'AICopilot',
          component: () => import('@/views/ai_copilot/Index.vue'),
          meta: { title: 'AI 助手' },
        },
        {
          path: 'traces/:traceId',
          name: 'TraceViewer',
          component: () => import('@/views/trace/TraceViewer.vue'),
          meta: { title: '链路追踪' },
        },
        {
          path: 'quality/gate',
          name: 'QualityGate',
          component: () => import('@/views/quality/Gate.vue'),
          meta: { title: '质量门禁' },
        },
        {
          path: 'quality/report',
          name: 'QualityReport',
          component: () => import('@/views/quality/Report.vue'),
          meta: { title: '质量报告' },
        },
        {
          path: 'quality/health-score',
          name: 'HealthScore',
          component: () => import('@/views/quality/HealthScore.vue'),
          meta: { title: '健康评分' },
        },
        {
          path: 'quality/stability',
          name: 'Stability',
          component: () => import('@/views/stability/Index.vue'),
          meta: { title: '稳定性治理' },
        },
        {
          path: 'quality/loop',
          name: 'QualityLoop',
          component: () => import('@/views/quality/Loop.vue'),
          meta: { title: '质量闭环' },
        },
        {
          path: 'regions',
          name: 'GlobalMap',
          component: () => import('@/views/region/GlobalMap.vue'),
          meta: { title: '全球运营' },
        },
        {
          path: 'load-test',
          name: 'LoadTest',
          component: () => import('@/views/load_test/Index.vue'),
          meta: { title: '压测中心' },
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('@/views/settings/Index.vue'),
          meta: { title: '系统设置' },
        },
        {
          path: 'defects',
          name: 'Defects',
          component: () => import('@/views/defect/List.vue'),
          meta: { title: '缺陷管理' },
        },
        {
          path: 'defects/:id',
          name: 'DefectDetail',
          component: () => import('@/views/defect/Detail.vue'),
          meta: { title: '缺陷详情' },
        },
        {
          path: 'schedules',
          name: 'Schedules',
          component: () => import('@/views/schedule/List.vue'),
          meta: { title: '定时任务' },
        },
        {
          path: 'scenarios',
          name: 'ScenarioWorkbench',
          component: () => import('@/views/scenario/Workbench.vue'),
          meta: { title: '场景工作台' },
        },
        {
          path: 'scenarios/ai-generate',
          name: 'ScenarioAIGenerate',
          component: () => import('@/views/scenario/AIGenerator.vue'),
          meta: { title: 'AI 场景生成' },
        },
        {
          path: 'environments',
          name: 'Environments',
          component: () => import('@/views/environment/Index.vue'),
          meta: { title: '环境治理' },
        },
        {
          path: 'environments/:id',
          name: 'EnvironmentDetail',
          component: () => import('@/views/environment/Detail.vue'),
          meta: { title: '环境详情' },
        },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  if (to.path !== '/login' && !userStore.token) {
    next('/login')
  } else {
    next()
  }
})

export default router
