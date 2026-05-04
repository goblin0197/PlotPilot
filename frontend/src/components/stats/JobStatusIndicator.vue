<template>
  <n-card v-if="status" class="job-status-indicator">
    <div class="job-header">
      <n-spin size="small" />
      <span class="job-type">{{ jobTypeLabel }}</span>
    </div>
    <div class="job-message">{{ status.message }}</div>
    <n-progress
      v-if="status.phase && !status.done"
      type="line"
      :percentage="calculateProgress()"
      :show-indicator="true"
    />
    <n-button
      v-if="!status.done"
      size="small"
      @click="handleCancel"
      aria-label="取消任务"
    >
      取消
    </n-button>
  </n-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { NCard, NProgress, NButton, NSpin, useMessage } from 'naive-ui'
import { workflowApi } from '../../api/workflow'
import type { JobStatusResponse } from '../../types/api'

const POLL_INTERVAL_MS = 3000

interface Props {
  jobId: string
}

const props = defineProps<Props>()
const message = useMessage()

const emit = defineEmits<{
  completed: [status: JobStatusResponse]
}>()

const status = ref<JobStatusResponse | null>(null)
let pollInterval: number | null = null

const jobTypeLabel = computed(() => {
  if (!status.value) return ''
  const labels: Record<string, string> = {
    plan: '规划中',
    write: '写作中',
    run: '执行中'
  }
  return labels[status.value.kind] || status.value.kind
})

const calculateProgress = (): number => {
  if (!status.value) return 0
  if (status.value.done) return 100

  // Use phase if available for more accurate progress
  if (status.value.phase) {
    const phaseProgress: Record<string, number> = {
      'queued': 10,
      'planning': 30,
      'writing': 60,
      'reviewing': 80,
      'running': 50
    }
    return phaseProgress[status.value.phase] || 50
  }

  // Fallback to simple status-based progress
  return status.value.status === 'queued' ? 10 : 50
}

/**
 * 轮询 `status` 状态并刷新本地响应式数据。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `pollStatus` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能向父组件派发事件；可能发起异步请求。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const pollStatus = async () => {
  try {
    const result = await workflowApi.getJobStatus(props.jobId)
    status.value = result

    if (result.done) {
      stopPolling()
      emit('completed', result)
    }
  } catch (error) {
    console.error('Failed to poll job status:', error)
    // Continue polling even on error - the job might still be running
  }
}

/**
 * 驱动 `polling` 对应的前端操作流程。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `stopPolling` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能创建或清理计时器。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

/**
 * 响应 `handle_cancel` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleCancel` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能发起异步请求。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const handleCancel = async () => {
  if (!props.jobId) return

  // Stop polling optimistically
  stopPolling()

  try {
    await workflowApi.cancelJob(props.jobId)
  } catch (error) {
    console.error('Failed to cancel job:', error)
        message.error('取消任务失败，请稍后重试')
    // Don't restart polling - user intended to cancel
  }
}

onMounted(() => {
  pollStatus()
  pollInterval = window.setInterval(pollStatus, POLL_INTERVAL_MS)
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.job-status-indicator {
  margin-bottom: 16px;
}

.job-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.job-type {
  font-weight: 600;
  color: #667eea;
}

.job-message {
  margin-bottom: 12px;
  color: #666;
  font-size: 14px;
}
</style>
