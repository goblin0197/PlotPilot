<template>
  <teleport to="body">
    <div
      class="global-llm-shell"
      :class="[
        `dock-${dockSide}`,
        `mode-${mode}`,
        { 'is-dragging': dragging, 'is-hovered': hovering },
      ]"
      :style="shellStyle"
    >
      <div
        class="global-llm-actions"
        :class="`dock-${dockSide}`"
        :style="actionsStyle"
        @mouseenter="setHovering(true)"
        @mouseleave="scheduleHideHover"
      >
        <button
          type="button"
          class="global-llm-action"
          :title="mode === 'expanded' ? '最小化' : '展开'"
          @pointerdown.stop
          @click.stop="toggleMinimize"
        >
          <n-icon v-if="mode === 'expanded'"><RemoveOutline /></n-icon>
          <n-icon v-else><ExpandOutline /></n-icon>
        </button>
      </div>

      <button
        ref="buttonRef"
        type="button"
        class="global-llm-main"
        :class="[`dock-${dockSide}`, `mode-${mode}`]"
        aria-label="打开全局 LLM 配置面板"
        @mouseenter="setHovering(true)"
        @mouseleave="scheduleHideHover"
        @pointerdown="onPointerDown"
        @keydown.enter.prevent="openPanel"
        @keydown.space.prevent="openPanel"
      >
        <span class="global-llm-glow"></span>

        <span class="global-llm-main-content">
          <span class="global-llm-icon-core">
            <span class="global-llm-icon-grid"></span>
            <n-icon class="global-llm-icon-chip"><HardwareChipOutline /></n-icon>
            <n-icon class="global-llm-icon-spark"><SparklesOutline /></n-icon>
          </span>

          <span v-if="mode === 'expanded'" class="global-llm-copy">
            <span class="global-llm-title-row">
              <span class="global-llm-title">AI 控制台</span>
              <span class="global-llm-status"></span>
            </span>
            <span class="global-llm-subtitle">LLM Gateway · OpenAI / Claude / Gemini</span>
          </span>
        </span>
      </button>
    </div>

    <n-modal
      v-model:show="showPanel"
      preset="card"
      title=""
      :style="aiConsoleModalStyle"
      :bordered="true"
      :segmented="{ content: true, footer: 'soft' }"
      :mask-closable="true"
      :close-on-esc="true"
      @update:show="handleModalShowChange"
    >
      <template #header>
        <div class="fab-llm-modal-header">
          <div class="modal-header">
            <div class="modal-header-left">
              <span class="modal-header-icon modal-header-icon-llm" aria-hidden="true">AI</span>
              <span class="modal-header-title">AI 控制台</span>
              <n-tag
                size="small"
                :type="runtimeSummary?.using_mock ? 'warning' : 'info'"
                :bordered="false"
              >
                {{
                  runtimeLoading
                    ? '读取中…'
                    : runtimeSummary?.using_mock
                      ? 'Mock'
                      : (runtimeSummary?.protocol || '未连接')
                }}
              </n-tag>
            </div>
          </div>
          <div class="fab-llm-modal-subtitle">
            统一控制当前项目的模型网关、协议与激活配置
          </div>
          <div class="global-llm-runtime-bar" :class="{ 'is-mock': runtimeSummary?.using_mock }">
            <div class="global-llm-runtime-main">
              <span class="global-llm-runtime-label">当前激活模型</span>
              <span class="global-llm-runtime-model">
                {{ runtimeSummary?.model || (runtimeLoading ? '读取中…' : '未配置') }}
              </span>
            </div>
            <div class="global-llm-runtime-meta">
              <span class="global-llm-runtime-chip">
                {{ runtimeSummary?.protocol || (runtimeLoading ? 'loading' : 'mock') }}
              </span>
              <span class="global-llm-runtime-name">
                {{ runtimeSummary?.active_profile_name || runtimeSummary?.reason || '未激活任何配置' }}
              </span>
            </div>
          </div>
        </div>
      </template>
      <div class="modal-body fab-llm-modal-body">
        <LLMControlPanel
          scroll-state-key="global-fab-modal"
          @panel-updated="handlePanelUpdated"
        />
      </div>
      <template #footer>
        <div class="modal-footer-hint">
          完整能力（含嵌入模型）请从侧栏或顶栏打开 AI 控制台。
        </div>
      </template>
    </n-modal>
  </teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { NModal, NTag, NIcon } from 'naive-ui'
import {
  ExpandOutline,
  HardwareChipOutline,
  RemoveOutline,
  SparklesOutline,
} from '@vicons/ionicons5'
import {
  llmControlApi,
  type LLMControlPanelData,
  type LLMRuntimeSummary,
} from '../../api/llmControl'
import LLMControlPanel from '../workbench/LLMControlPanel.vue'

type DockSide = 'left' | 'right'
type FabMode = 'expanded' | 'minimized'

interface PersistedFabState {
  version: 4
  dock: DockSide
  yRatio: number
  mode: FabMode
}

const STORAGE_KEY = 'plotpilot.global-llm-fab.state.v4'
const EDGE_GAP = 10
const TOP_SAFE_GAP = 88
const BOTTOM_SAFE_GAP = 24
const CLICK_THRESHOLD = 6

const showPanel = ref(false)
const dragging = ref(false)
const hovering = ref(false)
const runtimeLoading = ref(false)
const buttonRef = ref<HTMLElement | null>(null)
const viewportWidth = ref(getViewportWidth())
const viewportHeight = ref(getViewportHeight())
const position = ref({ x: 0, y: 0 })
const dockSide = ref<DockSide>('right')
const mode = ref<FabMode>('expanded')
const yRatio = ref(0.84)
const runtimeSummary = ref<LLMRuntimeSummary | null>(null)

const dragState = {
  active: false,
  moved: false,
  startX: 0,
  startY: 0,
  originX: 0,
  originY: 0,
}

let hoverHideTimer: ReturnType<typeof setTimeout> | null = null

/**
 * 加载 `viewport_width` 相关数据并同步到前端状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `getViewportWidth` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function getViewportWidth(): number {
  if (typeof window === 'undefined') return 1440
  return document.documentElement?.clientWidth || window.innerWidth || 1440
}

/**
 * 加载 `viewport_height` 相关数据并同步到前端状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `getViewportHeight` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function getViewportHeight(): number {
  if (typeof window === 'undefined') return 900
  return document.documentElement?.clientHeight || window.innerHeight || 900
}

const aiConsoleModalStyle = {
  width: '92vw',
  maxWidth: '1100px',
  height: '85vh',
  marginTop: '5vh',
} as const

const shellStyle = computed(() => ({
  left: `${position.value.x}px`,
  top: `${position.value.y}px`,
}))

const actionsStyle = computed(() =>
  dockSide.value === 'left' ? { left: '0' } : { right: '0' }
)

/**
 * 加载 `fallback_size` 相关数据并同步到前端状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `getFallbackSize` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function getFallbackSize() {
  if (mode.value === 'minimized') return { width: 62, height: 62 }
  return { width: 248, height: 70 }
}

/**
 * 加载 `button_size` 相关数据并同步到前端状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `getButtonSize` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function getButtonSize() {
  const rect = buttonRef.value?.getBoundingClientRect()
  if (!rect || !rect.width || !rect.height) return getFallbackSize()
  return {
    width: rect.width,
    height: rect.height,
  }
}

/**
 * 加载 `vertical_bounds` 相关数据并同步到前端状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `getVerticalBounds` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function getVerticalBounds(height: number) {
  const minY = TOP_SAFE_GAP
  const maxY = Math.max(minY, viewportHeight.value - height - BOTTOM_SAFE_GAP)
  return { minY, maxY }
}

/**
 * 加载 `docked_x` 相关数据并同步到前端状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `getDockedX` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function getDockedX(width: number) {
  return dockSide.value === 'left'
    ? EDGE_GAP
    : Math.max(EDGE_GAP, viewportWidth.value - width - EDGE_GAP)
}

/**
 * 加载 `y_ratio` 相关数据并同步到前端状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `getYFromRatio` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function getYFromRatio(height: number) {
  const { minY, maxY } = getVerticalBounds(height)
  if (maxY <= minY) return minY
  const ratio = Math.min(Math.max(yRatio.value, 0), 1)
  return minY + (maxY - minY) * ratio
}

/**
 * 执行 `setRatioFromY` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `setRatioFromY` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function setRatioFromY(y: number, height: number) {
  const { minY, maxY } = getVerticalBounds(height)
  if (maxY <= minY) {
    yRatio.value = 0
    return
  }
  const safeY = Math.min(Math.max(minY, y), maxY)
  yRatio.value = (safeY - minY) / (maxY - minY)
}

/**
 * 执行 `clampFreePosition` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `clampFreePosition` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function clampFreePosition(nextX: number, nextY: number) {
  const { width, height } = getButtonSize()
  const maxX = Math.max(0, viewportWidth.value - width)
  const { minY, maxY } = getVerticalBounds(height)
  return {
    x: Math.min(Math.max(0, nextX), maxX),
    y: Math.min(Math.max(minY, nextY), maxY),
  }
}

/**
 * 提交 `state` 相关变更并同步界面反馈。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `saveState` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function saveState() {
  const payload: PersistedFabState = {
    version: 4,
    dock: dockSide.value,
    yRatio: Number(yRatio.value.toFixed(4)),
    mode: mode.value,
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
}

/**
 * 执行 `applyDockPosition` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `applyDockPosition` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function applyDockPosition(shouldPersist = false) {
  const { width, height } = getButtonSize()
  position.value = {
    x: getDockedX(width),
    y: getYFromRatio(height),
  }
  if (shouldPersist) saveState()
}

/**
 * 执行 `defaultState` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `defaultState` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function defaultState() {
  dockSide.value = 'right'
  mode.value = 'expanded'
  yRatio.value = 0.84
}

/**
 * 执行 `restoreState` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `restoreState` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function restoreState() {
  defaultState()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw) as Partial<PersistedFabState> & { mode?: string }
    if (parsed.dock === 'left' || parsed.dock === 'right') {
      dockSide.value = parsed.dock
    }
    if (parsed.mode === 'expanded' || parsed.mode === 'minimized') {
      mode.value = parsed.mode
    }
    if (typeof parsed.yRatio === 'number' && Number.isFinite(parsed.yRatio)) {
      yRatio.value = Math.min(Math.max(parsed.yRatio, 0), 1)
    }
  } catch {
    defaultState()
  }
}

/**
 * 打开 `panel` 对应的弹窗、面板或交互状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `openPanel` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function openPanel() {
  void refreshRuntimeSummary()
  showPanel.value = true
}

/**
 * 执行 `refreshRuntimeSummary` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `refreshRuntimeSummary` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
async function refreshRuntimeSummary() {
  runtimeLoading.value = true
  try {
    const data = await llmControlApi.getPanel()
    runtimeSummary.value = data.runtime
  } catch {
    runtimeSummary.value = null
  } finally {
    runtimeLoading.value = false
  }
}

/**
 * 响应 `panel_updated` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `handlePanelUpdated` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function handlePanelUpdated(data: LLMControlPanelData) {
  runtimeSummary.value = data.runtime
}

/**
 * 响应 `modal_show_change` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleModalShowChange` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function handleModalShowChange(value: boolean) {
  showPanel.value = value
  if (value) {
    void refreshRuntimeSummary()
  }
}

/**
 * 清理 `hover_hide_timer` 相关的本地状态或定时器。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `clearHoverHideTimer` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能创建或清理计时器。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function clearHoverHideTimer() {
  if (hoverHideTimer) {
    clearTimeout(hoverHideTimer)
    hoverHideTimer = null
  }
}

/**
 * 执行 `setHovering` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `setHovering` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function setHovering(value: boolean) {
  clearHoverHideTimer()
  hovering.value = value
}

/**
 * 执行 `scheduleHideHover` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `scheduleHideHover` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能创建或清理计时器。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function scheduleHideHover() {
  clearHoverHideTimer()
  hoverHideTimer = setTimeout(() => {
    hovering.value = false
  }, 160)
}

/**
 * 切换 `minimize` 对应的界面状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `toggleMinimize` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function toggleMinimize() {
  mode.value = mode.value === 'expanded' ? 'minimized' : 'expanded'
}

/**
 * 执行 `syncViewport` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `syncViewport` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function syncViewport() {
  viewportWidth.value = getViewportWidth()
  viewportHeight.value = getViewportHeight()
  applyDockPosition()
}

/**
 * 驱动 `dragging` 对应的前端操作流程。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `stopDragging` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function stopDragging() {
  dragState.active = false
  dragging.value = false
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
  window.removeEventListener('pointercancel', onPointerCancel)
}

/**
 * 响应 `pointer_move` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `onPointerMove` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function onPointerMove(event: PointerEvent) {
  if (!dragState.active) return
  const dx = event.clientX - dragState.startX
  const dy = event.clientY - dragState.startY
  if (!dragState.moved && (Math.abs(dx) >= CLICK_THRESHOLD || Math.abs(dy) >= CLICK_THRESHOLD)) {
    dragState.moved = true
    dragging.value = true
  }
  if (!dragState.moved) return
  position.value = clampFreePosition(dragState.originX + dx, dragState.originY + dy)
}

/**
 * 执行 `snapToEdge` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `snapToEdge` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function snapToEdge() {
  const { width, height } = getButtonSize()
  const centerX = position.value.x + width / 2
  dockSide.value = centerX < viewportWidth.value / 2 ? 'left' : 'right'
  setRatioFromY(position.value.y, height)
  applyDockPosition(true)
}

/**
 * 响应 `pointer_up` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `onPointerUp` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function onPointerUp() {
  const moved = dragState.moved
  stopDragging()
  if (moved) {
    snapToEdge()
    return
  }
  openPanel()
}

/**
 * 响应 `pointer` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `onPointerCancel` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function onPointerCancel() {
  stopDragging()
  applyDockPosition()
}

/**
 * 响应 `pointer_down` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `onPointerDown` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function onPointerDown(event: PointerEvent) {
  if (event.button !== 0) return
  dragState.active = true
  dragState.moved = false
  dragState.startX = event.clientX
  dragState.startY = event.clientY
  dragState.originX = position.value.x
  dragState.originY = position.value.y
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
  window.addEventListener('pointercancel', onPointerCancel)
}

watch(mode, async () => {
  await nextTick()
  applyDockPosition(true)
})

onMounted(async () => {
  restoreState()
  await nextTick()
  applyDockPosition()
  window.addEventListener('resize', syncViewport)
  void refreshRuntimeSummary()
})

onBeforeUnmount(() => {
  clearHoverHideTimer()
  stopDragging()
  window.removeEventListener('resize', syncViewport)
})
</script>

<style scoped>
.global-llm-shell {
  position: fixed;
  z-index: 1200;
  user-select: none;
  touch-action: none;
  will-change: left, top, transform;
  transition:
    left 0.34s cubic-bezier(0.22, 1, 0.36, 1),
    top 0.34s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.18s ease;
}

.global-llm-shell.is-dragging {
  transition: none;
}

.global-llm-main {
  position: relative;
  display: block;
  z-index: 1;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background:
    radial-gradient(circle at 18% 18%, rgba(129, 140, 248, 0.32), transparent 28%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(49, 46, 129, 0.95) 55%, rgba(37, 99, 235, 0.9));
  color: var(--app-text-inverse, #fff);
  box-shadow:
    0 12px 30px rgba(30, 41, 59, 0.2),
    0 10px 26px rgba(79, 70, 229, 0.22);
  backdrop-filter: blur(12px);
  cursor: grab;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    opacity 0.18s ease,
    border-color 0.18s ease,
    width 0.22s ease,
    min-height 0.22s ease,
    height 0.22s ease,
    border-radius 0.22s ease,
    padding 0.22s ease;
}

.global-llm-main:hover {
  transform: translateY(-1px);
  border-color: rgba(191, 219, 254, 0.45);
  box-shadow:
    0 14px 34px rgba(30, 41, 59, 0.24),
    0 14px 32px rgba(79, 70, 229, 0.28);
}

.global-llm-shell.is-dragging .global-llm-main {
  cursor: grabbing;
  transform: scale(1.02);
}

.global-llm-main.mode-expanded {
  width: 248px;
  min-height: 68px;
  padding: 12px 14px;
  border-radius: 20px;
}

.global-llm-main.mode-minimized {
  width: 62px;
  height: 62px;
  padding: 0;
  border-radius: 50%;
}

.global-llm-glow {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.18), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.06), transparent 45%);
  pointer-events: none;
}

.global-llm-main-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.global-llm-icon-core {
  position: relative;
  flex: 0 0 auto;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.5), rgba(15, 23, 42, 0.16));
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.mode-minimized .global-llm-icon-core {
  width: 62px;
  height: 62px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 30%, rgba(96, 165, 250, 0.3), transparent 34%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.5), rgba(15, 23, 42, 0.18));
}

.global-llm-icon-grid {
  position: absolute;
  inset: 8px;
  border-radius: inherit;
  opacity: 0.35;
  background-image:
    linear-gradient(rgba(191, 219, 254, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(191, 219, 254, 0.12) 1px, transparent 1px);
  background-size: 7px 7px;
}

.global-llm-icon-chip,
.global-llm-icon-spark {
  position: relative;
  z-index: 1;
}

.global-llm-icon-chip {
  font-size: 20px;
}

.mode-minimized .global-llm-icon-chip {
  font-size: 24px;
}

.global-llm-icon-spark {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 13px;
  color: #fef08a;
  filter: drop-shadow(0 0 6px rgba(253, 224, 71, 0.4));
}

.mode-minimized .global-llm-icon-spark {
  top: 10px;
  right: 10px;
}

.global-llm-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.global-llm-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.global-llm-title {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.global-llm-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(180deg, #86efac, #22c55e);
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.14);
}

.global-llm-subtitle {
  max-width: 170px;
  color: rgba(226, 232, 240, 0.82);
  font-size: 11px;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.global-llm-actions {
  position: absolute;
  z-index: 2;
  bottom: calc(100% + 10px);
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
  padding: 8px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.56);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.18);
  backdrop-filter: blur(14px);
  transform: translateY(6px) scale(0.96);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.global-llm-shell.is-hovered .global-llm-actions,
.global-llm-shell.is-dragging .global-llm-actions {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0) scale(1);
}

.global-llm-action {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.16s ease, background 0.16s ease, color 0.16s ease;
}

.global-llm-action:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.16);
  color: var(--app-text-inverse, #fff);
}

.fab-llm-modal-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.modal-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
}

.modal-header-icon-llm {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-brand), var(--color-brand-hover));
  color: var(--app-text-inverse);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.modal-header-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text-primary);
}

.fab-llm-modal-subtitle {
  font-size: 12px;
  line-height: 1.45;
  color: var(--app-text-muted);
}

.modal-body.fab-llm-modal-body {
  height: calc(85vh - 220px);
  min-height: 260px;
  overflow: hidden;
  border-radius: var(--app-radius-md, 8px);
}

.modal-footer-hint {
  font-size: 12px;
  color: var(--app-text-muted);
  line-height: 1.55;
}

.global-llm-runtime-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background:
    linear-gradient(135deg, rgba(79, 70, 229, 0.08), rgba(59, 130, 246, 0.08)),
    var(--app-surface-subtle);
  border: 1px solid rgba(99, 102, 241, 0.1);
}

.global-llm-runtime-bar.is-mock {
  background:
    linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(249, 115, 22, 0.1)),
    var(--color-gold-dim);
  border-color: rgba(245, 158, 11, 0.18);
}

.global-llm-runtime-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.global-llm-runtime-label {
  font-size: 11px;
  line-height: 1;
  color: var(--app-text-muted);
}

.global-llm-runtime-model {
  font-size: 15px;
  font-weight: 700;
  line-height: 1.25;
  color: var(--app-text-primary);
}

.global-llm-runtime-meta {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.global-llm-runtime-chip {
  flex-shrink: 0;
  padding: 4px 9px;
  border-radius: 999px;
  background: rgba(79, 70, 229, 0.1);
  color: #4338ca;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.global-llm-runtime-name {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--app-text-secondary);
  font-size: 12px;
}

@media (max-width: 768px) {
  .global-llm-runtime-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .global-llm-runtime-meta {
    width: 100%;
    flex-wrap: wrap;
  }

  .global-llm-runtime-name {
    max-width: 100%;
    white-space: normal;
  }
}
</style>
