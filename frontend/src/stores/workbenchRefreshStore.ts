import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 工作台右栏「软刷新」信号：不整页 remount，仅驱动各面板重新拉数。
 * 在 loadDesk 成功后由 Workbench 触发（全托管完章、保存、规划确认等同源）。
 */
export const useWorkbenchRefreshStore = defineStore('workbenchRefresh', () => {
  const foreshadowTick = ref(0)
  const chroniclesTick = ref(0)
  /** 通用：知识库、故事线·弧光、片场、宏观提示等统一监听 */
  const deskTick = ref(0)

  /**
   * 执行 `bumpForeshadowLedger` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `bumpForeshadowLedger` 的状态推导、事件分发或异步调用。
   * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  function bumpForeshadowLedger() {
    foreshadowTick.value += 1
  }

  /**
   * 执行 `bumpChronicles` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `bumpChronicles` 的状态推导、事件分发或异步调用。
   * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  function bumpChronicles() {
    chroniclesTick.value += 1
  }

  /**
   * 执行 `bumpDesk` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `bumpDesk` 的状态推导、事件分发或异步调用。
   * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  function bumpDesk() {
    deskTick.value += 1
  }

  /** 章节落库或结构变化后：伏笔、编年史、知识库、故事线等同源刷新 */
  function bumpAfterChapterDeskChange() {
    bumpForeshadowLedger()
    bumpChronicles()
    bumpDesk()
  }

  return {
    foreshadowTick,
    chroniclesTick,
    deskTick,
    bumpForeshadowLedger,
    bumpChronicles,
    bumpDesk,
    bumpAfterChapterDeskChange,
  }
})
