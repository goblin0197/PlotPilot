import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// Naive UI
import naive from 'naive-ui'

// ECharts
import installECharts from './plugins/echarts'

// 样式
import './assets/styles/main.css'

// Tauri API 初始化（动态端口、环境检测）
import { initApiClient } from './api/config'

/**
 * 执行 `bootstrap` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `bootstrap` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
async function bootstrap() {
  const app = createApp(App)

  app.use(createPinia())
  app.use(router)
  app.use(naive)
  app.use(installECharts)

  // Tauri 下须先拿到真实端口再挂路由，否则首屏请求会打到错误 origin（抽屉/广场像「没连上库」）
  try {
    await initApiClient()
  } catch (err) {
    console.warn('[Init] API 客户端初始化失败（可稍后重试）:', err)
  }

  app.mount('#app')
}

void bootstrap()
