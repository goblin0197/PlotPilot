import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'anchor' | 'auto'

const STORAGE_KEY = 'aitext-theme-mode'

/**
 * 加载 `stored_theme` 相关数据并同步到前端状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `getStoredTheme` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function getStoredTheme(): ThemeMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'light' || stored === 'dark' || stored === 'anchor' || stored === 'auto') return stored
  } catch { /* ignore */ }
  return 'light'
}

/**
 * 加载 `system_dark` 相关数据并同步到前端状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `getSystemDark` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function getSystemDark(): boolean {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>(getStoredTheme())

  // 独立追踪 OS 偏好，使 auto 模式下 isDark 能响应系统变化
  const systemDark = ref(getSystemDark())

  const isDark = computed(() => {
    if (mode.value === 'auto') return systemDark.value
    return mode.value === 'dark' || mode.value === 'anchor'
  })

  /** 是否为黑金（主播限定色）模式 */
  const isAnchor = computed(() => mode.value === 'anchor')

  /** 实际生效的主题名，供 naive-ui / CSS 使用 */
  const effectiveTheme = computed<'light' | 'dark'>(() =>
    isDark.value ? 'dark' : 'light'
  )

  /**
   * 执行 `setTheme` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `setTheme` 的状态推导、事件分发或异步调用。
   * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  function setTheme(newMode: ThemeMode) {
    mode.value = newMode
    try {
      localStorage.setItem(STORAGE_KEY, newMode)
    } catch { /* ignore */ }
  }

  // 监听系统主题变化，更新响应式 systemDark 使 auto 模式即时生效
  if (typeof window !== 'undefined' && window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      systemDark.value = e.matches
    })
  }

  /**
   * 执行 `applyThemeToDOM` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `applyThemeToDOM` 的状态推导、事件分发或异步调用。
   * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  function applyThemeToDOM() {
    const root = document.documentElement
    if (isDark.value) {
      root.classList.add('dark')
      root.setAttribute('data-theme', isAnchor.value ? 'anchor' : 'dark')
    } else {
      root.classList.remove('dark')
      root.setAttribute('data-theme', 'light')
    }
  }

  // 监听 isDark + mode，覆盖所有变化路径：
  // - 手动切换 mode（light/dark/anchor/auto）
  // - auto 模式下 OS 偏好变化（systemDark 改变 → isDark 改变）
  watch([isDark, mode], applyThemeToDOM, { immediate: true })

  return { mode, isDark, isAnchor, effectiveTheme, setTheme }
})
