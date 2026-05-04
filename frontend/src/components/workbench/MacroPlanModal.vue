<template>
  <n-modal
    v-model:show="show"
    preset="card"
    class="macro-plan-modal"
    style="width: min(560px, 96vw); max-height: min(92vh, 860px)"
    :mask-closable="false"
    :segmented="{ content: true, footer: 'soft' }"
    title="🎯 启动结构规划"
  >
    <template #header-extra>
      <span class="macro-plan-header-extra">一键生成骨架，无需填写部 / 卷 / 幕</span>
    </template>

    <div class="macro-plan-body">
      <p class="macro-plan-lead">
        将根据本书的<strong class="macro-plan-strong">世界观、人物与梗概</strong>，生成宏观叙事结构并写入左侧结构树。
        篇幅与节奏以<strong class="macro-plan-strong">创建书目时的设定</strong>为准；此处不再做「精密乘法」。
      </p>

      <div class="macro-plan-card">
        <div class="macro-plan-card-title">更适合</div>
        <ul class="macro-plan-list">
          <li>想先有一副骨架再动笔</li>
          <li>愿意交给 AI 搭结构、自己跟进度与成稿</li>
          <li>需要一版可编辑的部–卷–幕草稿</li>
        </ul>
      </div>
    </div>

    <template #footer>
      <n-space justify="space-between">
        <n-button @click="handleClose" :disabled="loading">取消</n-button>
        <n-button type="primary" :loading="loading" @click="doGenerate">生成叙事骨架</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { workflowApi } from '../../api/workflow'

const props = defineProps<{ show: boolean; novelId: string }>()
const emit = defineEmits<{
  'update:show': [v: boolean]
  confirmed: []
}>()

const show = computed({
  /**
   * 加载 `get` 相关数据并同步到前端状态。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `get` 的状态推导、事件分发或异步调用。
   * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态；可能向父组件派发事件。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  get: () => props.show,
  /**
   * 执行 `set` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `set` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `v` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态；可能向父组件派发事件。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  set: (v) => emit('update:show', v),
})

const message = useMessage()
const loading = ref(false)

/**
 * 执行 `doGenerate` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `doGenerate` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能向父组件派发事件；可能发起异步请求；可能创建或清理计时器；可能触发用户提示。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const doGenerate = async () => {
  loading.value = true
  try {
    await workflowApi.planNovel(props.novelId, 'initial', false)
    message.success('叙事结构已生成并写入，正在刷新…', { duration: 2000 })
    await new Promise((resolve) => setTimeout(resolve, 500))
    emit('confirmed')
    show.value = false
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    message.error(err?.response?.data?.detail || '生成失败，请确认 AI 密钥已配置')
  } finally {
    loading.value = false
  }
}

/**
 * 响应 `handle_close` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleClose` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const handleClose = () => {
  if (loading.value) return
  show.value = false
}
</script>

<style scoped>
.macro-plan-header-extra {
  font-size: 12px;
  line-height: 1.45;
  color: var(--app-text-secondary, #475569);
}

.macro-plan-body {
  padding: 4px 0 10px;
}

.macro-plan-lead {
  margin: 0 0 16px;
  font-size: 14px;
  line-height: 1.65;
  color: var(--app-text-primary, #111827);
}

.macro-plan-strong {
  font-weight: 600;
  color: var(--app-text-primary, #111827);
}

.macro-plan-card {
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--aitext-split-border, rgba(15, 23, 42, 0.12));
  background: var(--app-surface-subtle, #f8fafc);
}

.macro-plan-card-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--app-text-primary, #111827);
}

.macro-plan-list {
  margin: 0;
  padding-left: 1.15rem;
  font-size: 13px;
  line-height: 1.55;
  color: var(--app-text-secondary, #334155);
}

.macro-plan-list li + li {
  margin-top: 4px;
}
</style>
