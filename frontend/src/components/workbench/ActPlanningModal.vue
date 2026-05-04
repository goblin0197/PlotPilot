<template>
  <n-modal
    v-model:show="show"
    preset="card"
    style="width: min(720px, 96vw)"
    :mask-closable="false"
    :segmented="{ content: true, footer: 'soft' }"
    :title="`规划章节 — ${actTitle}`"
  >
    <template #header-extra>
      <n-text depth="3" style="font-size: 12px">AI 为本幕生成章节大纲，确认后写入结构树</n-text>
    </template>

    <!-- 生成前：配置 -->
    <n-space v-if="!generated" vertical :size="16">
      <n-alert type="info" :show-icon="true">
        AI 将根据本幕的叙事目标与 Bible 信息，自动为每章生成标题和大纲。生成后可编辑再确认。
      </n-alert>

      <n-form-item label="本幕章节数" :show-feedback="false">
        <n-input-number
          v-model:value="chapterCount"
          :min="2"
          :max="20"
          :disabled="loading"
          style="width: 120px"
        />
        <n-text depth="3" style="margin-left: 8px; font-size: 12px">（不填则由 AI 自主决定）</n-text>
      </n-form-item>

      <n-space justify="end" :size="10">
        <n-button :disabled="loading" @click="close">取消</n-button>
        <n-button type="primary" :loading="loading" @click="generate">AI 生成章节规划</n-button>
      </n-space>
    </n-space>

    <!-- 生成后：预览 + 编辑 -->
    <n-space v-else vertical :size="16">
      <n-alert type="success" :show-icon="true">
        已生成 {{ chapters.length }} 章规划，可在下方直接修改标题或大纲后确认。
      </n-alert>

      <n-scrollbar style="max-height: 52vh">
        <n-space vertical :size="8" style="padding-right: 8px">
          <n-card
            v-for="(ch, idx) in chapters"
            :key="idx"
            size="small"
            :bordered="true"
            style="background: var(--n-color)"
          >
            <n-space vertical :size="6">
              <n-input
                v-model:value="ch.title"
                placeholder="章节标题"
                :disabled="confirming"
                size="small"
              />
              <n-input
                v-model:value="ch.outline"
                type="textarea"
                placeholder="本章大纲"
                :autosize="{ minRows: 2, maxRows: 5 }"
                :disabled="confirming"
                size="small"
              />
              <n-space :size="6">
                <n-tag v-for="el in ch.bible_elements" :key="el" size="small" round>{{ el }}</n-tag>
              </n-space>
            </n-space>
          </n-card>
        </n-space>
      </n-scrollbar>

      <n-space justify="end" :size="10">
        <n-button :disabled="confirming" @click="reset">重新生成</n-button>
        <n-button :disabled="confirming" @click="close">取消</n-button>
        <n-button type="primary" :loading="confirming" @click="confirm">确认并保存到结构树</n-button>
      </n-space>
    </n-space>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { planningApi } from '../../api/planning'

interface ChapterDraft {
  title: string
  outline: string
  bible_elements: string[]
  [key: string]: unknown
}

const props = defineProps<{
  show: boolean
  actId: string
  actTitle: string
}>()

const emit = defineEmits<{
  (e: 'update:show', v: boolean): void
  (e: 'confirmed'): void
}>()

const message = useMessage()

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

const loading = ref(false)
const confirming = ref(false)
const generated = ref(false)
const chapterCount = ref<number | null>(null)
const chapters = ref<ChapterDraft[]>([])

watch(
  () => props.show,
  (v) => { if (!v) reset() }
)

/**
 * 清理 `reset` 相关的本地状态或定时器。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `reset` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function reset() {
  generated.value = false
  chapters.value = []
  loading.value = false
  confirming.value = false
}

/**
 * 关闭 `close` 对应的弹窗、面板或交互状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `close` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能向父组件派发事件。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function close() {
  emit('update:show', false)
}

/**
 * 执行 `generate` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `generate` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
async function generate() {
  loading.value = true
  try {
    const res = await planningApi.generateActChapters(props.actId, {
      chapter_count: chapterCount.value ?? undefined,
    }) as any
    const raw: any[] = res.chapters ?? res.data?.chapters ?? []
    chapters.value = raw.map((c: any) => ({
      title: c.title ?? '',
      outline: c.outline ?? c.description ?? '',
      bible_elements: c.bible_elements ?? [],
      ...c,
    }))
    if (!chapters.value.length) {
      message.warning('AI 未返回章节数据，请重试')
      return
    }
    generated.value = true
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '生成失败，请检查 API Key')
  } finally {
    loading.value = false
  }
}

/**
 * 执行 `confirm` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `confirm` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能向父组件派发事件；可能发起异步请求；可能触发用户提示。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
async function confirm() {
  confirming.value = true
  try {
    await planningApi.confirmActChapters(props.actId, { chapters: chapters.value })
    message.success('章节已写入结构树')
    emit('confirmed')
    emit('update:show', false)
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '保存失败')
  } finally {
    confirming.value = false
  }
}
</script>
