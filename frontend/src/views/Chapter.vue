<template>
  <n-spin :show="pageLoading" class="chapter-spin" description="加载章节…">
  <div class="chapter">
    <header class="chapter-header">
      <n-space align="center" :wrap="false">
        <n-button quaternary round @click="goBack">
          <template #icon>
            <span class="ico-back">←</span>
          </template>
          工作台
        </n-button>
        <n-divider vertical />
        <h2 class="chapter-heading">第 {{ chapterId }} 章</h2>
        <n-tag :type="saveStatus === 'saved' ? 'success' : saveStatus === 'saving' ? 'warning' : 'default'" round size="small">
          {{ saveStatusText }}
        </n-tag>
      </n-space>

      <n-space :size="8" :wrap="false">
        <n-button-group>
          <n-button size="small" @click="prevChapter" :disabled="!canPrev">
            <template #icon>
              <span class="ico-tiny">◀</span>
            </template>
            上一章
          </n-button>
          <n-button size="small" @click="nextChapter" :disabled="!canNext">
            下一章
            <template #icon>
              <span class="ico-tiny">▶</span>
            </template>
          </n-button>
        </n-button-group>

        <n-dropdown :options="toolOptions" @select="handleToolSelect">
          <n-button size="small" secondary>工具</n-button>
        </n-dropdown>

        <n-button size="small" quaternary @click="goCastGraph">关系图</n-button>

        <n-button type="primary" size="small" round :loading="saving" @click="saveContent" :disabled="!contentDirty">
          保存
        </n-button>
      </n-space>
    </header>

    <n-split direction="horizontal" :default-size="0.72" :min="0.55" :max="0.88">
      <template #1>
        <div class="editor-area">
          <n-input
            v-model:value="content"
            type="textarea"
            class="content-editor"
            placeholder="开始写作…&#10;&#10;Ctrl+S 保存 · 自动保存约 30 秒"
            @update:value="onInput"
            :autosize="{ minRows: 22 }"
          />
          <div class="editor-footer">
            <n-space>
              <n-text depth="3">{{ wordCount }} 字</n-text>
              <n-divider vertical />
              <n-text depth="3">{{ lineCount }} 行</n-text>
              <n-divider vertical />
              <n-text depth="3" v-if="lastSaveTime">上次保存 {{ lastSaveTime }}</n-text>
            </n-space>
            <n-button size="small" quaternary @click="showPreview = !showPreview">
              {{ showPreview ? '隐藏预览' : 'Markdown 预览' }}
            </n-button>
          </div>

          <transition name="preview-slide">
            <div v-if="showPreview" class="preview-panel">
              <n-divider title-placement="left">预览</n-divider>
              <div class="preview-content markdown-body md-body" v-html="previewHtml" />
            </div>
          </transition>
        </div>
      </template>

      <template #2>
        <div class="review-panel">
          <n-tabs type="segment" animated class="review-tabs">
            <n-tab-pane name="review" tab="审定">
              <n-form label-placement="top" class="review-form">
                <n-form-item label="状态">
                  <n-radio-group v-model:value="reviewStatus" name="review-status">
                    <n-space>
                      <n-radio value="pending">待阅</n-radio>
                      <n-radio value="ok">已定稿</n-radio>
                      <n-radio value="revise">需修订</n-radio>
                    </n-space>
                  </n-radio-group>
                </n-form-item>
                <n-form-item label="批注">
                  <n-input v-model:value="reviewMemo" type="textarea" :rows="10" placeholder="审读意见…" />
                </n-form-item>
                <n-space vertical :size="8" style="width: 100%">
                  <n-button block :loading="savingAiReview" secondary @click="runAiReview(false)">
                    生成审读意见
                  </n-button>
                  <n-button block :loading="savingAiReview" type="info" secondary @click="runAiReview(true)">
                    生成并写入审定
                  </n-button>
                  <n-text depth="3" style="font-size: 11px; line-height: 1.45">
                    基于合并正文（含 chapters/NNN 下分场景 parts）与大纲一句纲；「生成意见」仅填入上方表单项。
                  </n-text>
                </n-space>
                <n-button type="primary" block round :loading="savingReview" @click="saveReview">保存审定</n-button>
              </n-form>
            </n-tab-pane>

            <n-tab-pane name="inference">
              <template #tab>
                <span data-testid="chapter-tab-inference">推断证据</span>
              </template>
              <n-spin :show="inferenceLoading">
                <n-space vertical :size="12" style="width: 100%">
                  <n-alert v-if="inferenceHint" type="info" :title="inferenceHintTitle" style="font-size: 12px">
                    {{ inferenceHint }}
                  </n-alert>
                  <n-space justify="space-between" align="center">
                    <n-text depth="3" style="font-size: 12px">
                      来自章节元素自动推断的 <code>chapter_inferred</code> 三元组及证据链
                    </n-text>
                    <n-space :size="8">
                      <n-button
                        size="tiny"
                        quaternary
                        data-testid="chapter-inference-refresh"
                        :loading="inferenceLoading"
                        @click="loadInferenceEvidence"
                      >
                        刷新
                      </n-button>
                      <n-popconfirm @positive-click="revokeAllInference">
                        <template #trigger>
                          <n-button
                            size="tiny"
                            type="error"
                            secondary
                            :disabled="!storyNodeId"
                            :loading="revokeAllLoading"
                          >
                            撤销本章全部推断
                          </n-button>
                        </template>
                        将删除本章节点下的溯源；无剩余证据的推断三元组会被移除。确定？
                      </n-popconfirm>
                    </n-space>
                  </n-space>
                  <n-empty v-if="!inferenceLoading && !inferenceFacts.length" description="暂无本章推断记录" size="small" />
                  <n-collapse v-else accordion>
                    <n-collapse-item
                      v-for="item in inferenceFacts"
                      :key="item.fact.id"
                      :title="`${item.fact.subject} —${item.fact.predicate}→ ${item.fact.object}`"
                      :name="item.fact.id"
                    >
                      <n-space vertical :size="8" style="width: 100%">
                        <n-descriptions label-placement="left" :column="1" size="small" bordered>
                          <n-descriptions-item label="ID">{{ item.fact.id }}</n-descriptions-item>
                          <n-descriptions-item label="置信度">
                            {{ item.fact.confidence != null ? item.fact.confidence : '—' }}
                          </n-descriptions-item>
                        </n-descriptions>
                        <n-text depth="3" style="font-size: 11px">证据链（rule / 元素行 / role）</n-text>
                        <ul class="inf-prov-list">
                          <li v-for="p in item.provenance" :key="p.id">
                            <code>{{ p.rule_id }}</code>
                            <span v-if="p.chapter_element_id"> · 元素 {{ p.chapter_element_id }}</span>
                            · {{ p.role }}
                          </li>
                        </ul>
                        <n-button
                          size="small"
                          type="warning"
                          secondary
                          :loading="revokingId === item.fact.id"
                          @click="revokeOneInference(item.fact.id)"
                        >
                          撤销此条推断
                        </n-button>
                      </n-space>
                    </n-collapse-item>
                  </n-collapse>
                </n-space>
              </n-spin>
            </n-tab-pane>

            <n-tab-pane name="info" tab="信息">
              <n-space vertical :size="16" class="info-stats">
                <n-statistic label="字数" :value="wordCount" />
                <n-statistic label="行数" :value="lineCount" />
                <n-statistic label="段落" :value="paragraphCount" />
                <n-divider />
                <div v-if="chapterStructure">
                  <n-statistic label="分析字数" :value="chapterStructure.word_count" />
                  <n-statistic label="分析段落" :value="chapterStructure.paragraph_count" />
                  <n-statistic label="对话占比" :value="(chapterStructure.dialogue_ratio * 100).toFixed(1) + '%'" />
                  <n-statistic label="场景数" :value="chapterStructure.scene_count" />
                  <n-text depth="3" class="meta-line">节奏：{{ chapterStructure.pacing }}</n-text>
                </div>
                <n-divider />
                <n-text depth="3" class="meta-line">创建：{{ createTime }}</n-text>
                <n-text depth="3" class="meta-line">修改：{{ updateTime }}</n-text>
              </n-space>
            </n-tab-pane>
          </n-tabs>
        </div>
      </template>
    </n-split>
  </div>
  </n-spin>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, useDialog } from 'naive-ui'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { chapterApi } from '../api/chapter'
import { knowledgeGraphApi, type InferenceFactBundle } from '../api/knowledgeGraph'
import { useStatsStore } from '../stores/statsStore'

// Status mapping: old API (pending/ok/revise) <-> new API (draft/reviewed/approved)
const statusToNew = (oldStatus: string): string => {
  const map: Record<string, string> = {
    'pending': 'draft',
    'ok': 'approved',
    'revise': 'reviewed'
  }
  return map[oldStatus] || 'draft'
}

const statusToOld = (newStatus: string): string => {
  const map: Record<string, string> = {
    'draft': 'pending',
    'approved': 'ok',
    'reviewed': 'revise'
  }
  return map[newStatus] || 'pending'
}

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const statsStore = useStatsStore()

const inferenceLoading = ref(false)
const inferenceFacts = ref<InferenceFactBundle[]>([])
const inferenceHint = ref('')
const inferenceHintTitle = ref('提示')
const storyNodeId = ref<string | null>(null)
const revokeAllLoading = ref(false)
const revokingId = ref<string | null>(null)

const slug = route.params.slug as string
const chapterId = computed(() => {
  const id = Number(route.params.id as string)
  if (isNaN(id) || id <= 0) {
    message.error('无效的章节ID')
    return null
  }
  return id
})

/**
 * 执行 `goHome` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `goHome` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const goHome = () => {
  const n = chapterId.value
  router.push(
    n != null
      ? { path: `/book/${slug}/workbench`, query: { chapter: String(n) } }
      : `/book/${slug}/workbench`
  )
}

watch(chapterId, (newId) => {
  if (newId === null) {
    goHome()
  }
}, { immediate: true })

const content = ref('')
const saving = ref(false)
const saveStatus = ref<'unsaved' | 'saving' | 'saved'>('saved')
const lastSaveTime = ref('')
const saveTimer = ref<ReturnType<typeof setTimeout> | null>(null)

const reviewStatus = ref('pending')
const reviewMemo = ref('')
const savingReview = ref(false)
const savingAiReview = ref(false)
const chapterStructure = ref<{
  word_count: number
  paragraph_count: number
  dialogue_ratio: number
  scene_count: number
  pacing: string
} | null>(null)

const showPreview = ref(false)
const chapterIds = ref<number[]>([])
const pageLoading = ref(true)

const wordCount = computed(() => content.value.replace(/\s/g, '').length)
const lineCount = computed(() => (content.value ? content.value.split('\n').length : 0))
const paragraphCount = computed(() =>
  content.value ? content.value.split(/\n\s*\n/).filter(p => p.trim()).length : 0
)

const previewHtml = ref<string>('')
const markdownDebounceTimer = ref<ReturnType<typeof setTimeout> | null>(null)

/**
 * 提交 `preview` 相关变更并同步界面反馈。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `updatePreview` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `debounce` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const updatePreview = (debounce = false) => {
  /**
   * 执行 `parseMarkdown` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `parseMarkdown` 的状态推导、事件分发或异步调用。
   * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态；可能创建或清理计时器。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const parseMarkdown = () => {
    const html = marked.parse(content.value, { breaks: true, async: false }) as string
    const sanitizedHtml = DOMPurify.sanitize(html)
    previewHtml.value = sanitizedHtml
  }

  if (debounce) {
    if (markdownDebounceTimer.value) clearTimeout(markdownDebounceTimer.value)
    markdownDebounceTimer.value = window.setTimeout(parseMarkdown, 300)
  } else {
    parseMarkdown()
  }
}

const saveStatusText = computed(() => {
  const map = { unsaved: '未保存', saving: '保存中…', saved: '已保存' }
  return map[saveStatus.value]
})

const contentDirty = computed(() => saveStatus.value === 'unsaved')

const currentChapterIndex = computed(() => {
  const cid = chapterId.value
  return cid == null ? -1 : chapterIds.value.indexOf(cid)
})

const canPrev = computed(() => {
  const i = currentChapterIndex.value
  return i > 0
})

const canNext = computed(() => {
  const i = currentChapterIndex.value
  return i >= 0 && i < chapterIds.value.length - 1
})

const createTime = ref('—')
const updateTime = ref('—')

const toolOptions = [
  { label: '复制全文', key: 'copy' },
  { label: '清空正文', key: 'clear' },
]

/**
 * 响应 `tool_select` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleToolSelect` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `key` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能触发用户提示。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const handleToolSelect = (key: string) => {
  if (key === 'copy') {
    void navigator.clipboard.writeText(content.value).then(
      () => message.success('已复制'),
      () => message.error('复制失败')
    )
  }
  if (key === 'clear') {
    content.value = ''
    onInput()
    updatePreview(false)
  }
}

/**
 * 响应 `input` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `onInput` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能创建或清理计时器。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const onInput = () => {
  saveStatus.value = 'unsaved'
  if (saveTimer.value) clearTimeout(saveTimer.value)
  saveTimer.value = window.setTimeout(() => {
    void saveContent()
  }, 30000)
  updatePreview(true)
}

/**
 * 提交 `content` 相关变更并同步界面反馈。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `saveContent` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const saveContent = async () => {
  const cid = chapterId.value
  if (cid == null || saving.value) return
  saving.value = true
  saveStatus.value = 'saving'

  try {
    await chapterApi.updateChapter(slug, cid, {
      content: content.value
    })
    saveStatus.value = 'saved'
    lastSaveTime.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    updateTime.value = new Date().toLocaleString('zh-CN', { hour12: false })
    message.success('已保存')
    // Refresh book stats after successful save
    statsStore.onChapterSaved(slug, cid)
  } catch (error) {
    console.error('Failed to save content:', error)
    saveStatus.value = 'unsaved'
    message.error('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

/**
 * 提交 `review` 相关变更并同步界面反馈。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `saveReview` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求；可能触发用户提示。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const saveReview = async () => {
  const cid = chapterId.value
  if (cid == null) return
  savingReview.value = true
  try {
    const newStatus = statusToNew(reviewStatus.value)
    await chapterApi.saveChapterReview(slug, cid, newStatus, reviewMemo.value)
    message.success('审定已保存')
    // Refresh book stats after successful save
    statsStore.onChapterSaved(slug, cid)
  } catch (error) {
    console.error('Failed to save review:', error)
    message.error('保存失败，请稍后重试')
  } finally {
    savingReview.value = false
  }
}

/**
 * 驱动 `ai_review` 对应的前端操作流程。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `runAiReview` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `save` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求；可能触发用户提示。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const runAiReview = async (save: boolean) => {
  const cid = chapterId.value
  if (cid == null) return
  savingAiReview.value = true
  try {
    const r = await chapterApi.reviewChapterAi(slug, cid, save)
    reviewStatus.value = statusToOld(r.status)
    reviewMemo.value = r.memo
    message.success(save ? '已写入审定意见' : '已填入审读意见')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '生成失败')
  } finally {
    savingAiReview.value = false
  }
}

/**
 * 执行 `goBack` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `goBack` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const goBack = () => {
  const n = chapterId.value
  router.push(
    n != null
      ? { path: `/book/${slug}/workbench`, query: { chapter: String(n) } }
      : `/book/${slug}/workbench`
  )
}

/**
 * 执行 `goCastGraph` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `goCastGraph` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const goCastGraph = () => {
  const cid = chapterId.value
  router.push({ path: `/book/${slug}/cast`, query: cid == null ? {} : { chapter: String(cid) } })
}

/**
 * 执行 `prevChapter` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `prevChapter` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const prevChapter = () => {
  const i = currentChapterIndex.value
  if (i > 0) router.push(`/book/${slug}/chapter/${chapterIds.value[i - 1]}`)
}

/**
 * 执行 `nextChapter` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `nextChapter` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const nextChapter = () => {
  const i = currentChapterIndex.value
  if (i >= 0 && i < chapterIds.value.length - 1) {
    router.push(`/book/${slug}/chapter/${chapterIds.value[i + 1]}`)
  }
}

/**
 * 响应 `key` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `onKeySave` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `e` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const onKeySave = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    void saveContent()
  }
}

/**
 * 加载 `chapter` 相关数据并同步到前端状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `loadChapter` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const loadChapter = async () => {
  const cid = chapterId.value
  if (cid === null) {
    return
  }

  // 章节列表用 v1 chapters；旧 /api/book/.../desk 在后端不存在
  const [chaptersList, chapterData, rev, structureResult] = await Promise.allSettled([
    chapterApi.listChapters(slug),
    chapterApi.getChapter(slug, cid),
    chapterApi.getChapterReview(slug, cid),
    chapterApi.getChapterStructure(slug, cid)
  ])

  if (chaptersList.status === 'fulfilled') {
    chapterIds.value = chaptersList.value.map(c => c.number).sort((a, b) => a - b)
  } else {
    console.error('Failed to load chapter list:', chaptersList.reason)
  }

  // Handle chapter data API result
  if (chapterData.status === 'fulfilled') {
    content.value = chapterData.value.content || ''
    if (content.value) {
      createTime.value = new Date(chapterData.value.created_at).toLocaleString('zh-CN', { hour12: false })
      updateTime.value = new Date(chapterData.value.updated_at).toLocaleString('zh-CN', { hour12: false })
    }
    updatePreview(false)
  } else {
    console.error('Failed to load chapter:', chapterData.reason)
  }

  // Handle review API result
  if (rev.status === 'fulfilled') {
    reviewStatus.value = statusToOld(rev.value.status)
    reviewMemo.value = rev.value.memo
  }

  // Handle structure API result (this one is optional, can fail gracefully)
  if (structureResult.status === 'fulfilled') {
    chapterStructure.value = {
      word_count: structureResult.value.word_count,
      paragraph_count: structureResult.value.paragraph_count,
      dialogue_ratio: structureResult.value.dialogue_ratio,
      scene_count: structureResult.value.scene_count,
      pacing: structureResult.value.pacing,
    }
  } else {
    console.warn('Failed to load chapter structure:', structureResult.reason)
    chapterStructure.value = null
  }

  saveStatus.value = 'saved'
  await loadInferenceEvidence()
}

/**
 * 加载 `inference_evidence` 相关数据并同步到前端状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `loadInferenceEvidence` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const loadInferenceEvidence = async () => {
  const cid = chapterId.value
  if (cid === null) return
  inferenceLoading.value = true
  inferenceHint.value = ''
  try {
    const res = await knowledgeGraphApi.getChapterInferenceEvidence(slug, cid)
    const d = res.data
    storyNodeId.value = d.story_node_id
    inferenceFacts.value = d.facts || []
    if (d.story_node_id) {
      inferenceHint.value = ''
    }
    if (d.hint) {
      inferenceHintTitle.value = '无结构节点'
      inferenceHint.value = d.hint
    } else if (!d.story_node_id) {
      inferenceHintTitle.value = '无结构节点'
      inferenceHint.value = '未匹配到故事结构中的章节节点，推断证据为空。'
    }
  } catch (e) {
    console.error('inference evidence', e)
    inferenceHintTitle.value = '加载失败'
    inferenceHint.value = '无法加载推断证据（请确认后端与 SQLite 可用）。'
    inferenceFacts.value = []
    storyNodeId.value = null
  } finally {
    inferenceLoading.value = false
  }
}

/**
 * 执行 `revokeOneInference` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `revokeOneInference` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `tripleId` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能触发用户提示。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const revokeOneInference = (tripleId: string) => {
  dialog.warning({
    title: '撤销此条推断',
    content: '将删除该 chapter_inferred 三元组及其溯源，确定？',
    positiveText: '撤销',
    negativeText: '取消',
    /**
     * 响应 `positive_click` 相关的界面事件。
     *
     * 职责: 位于前端组件/组合式逻辑中，集中处理 `onPositiveClick` 的状态推导、事件分发或异步调用。
     * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
     * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求；可能触发用户提示。
     * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
     */
    onPositiveClick: async () => {
      revokingId.value = tripleId
      try {
        await knowledgeGraphApi.revokeInferredTriple(slug, tripleId)
        message.success('已撤销')
        await loadInferenceEvidence()
      } catch (err: any) {
        message.error(err?.response?.data?.detail || '撤销失败')
      } finally {
        revokingId.value = null
      }
      return true
    },
  })
}

/**
 * 执行 `revokeAllInference` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `revokeAllInference` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求；可能触发用户提示。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const revokeAllInference = async () => {
  const cid = chapterId.value
  if (cid === null) return
  revokeAllLoading.value = true
  try {
    const r = await knowledgeGraphApi.revokeChapterInference(slug, cid)
    message.success(
      `已处理：删除 ${r.data.deleted_inferred_facts} 条推断三元组（涉及 ${r.data.removed_provenance_triples} 条证据关联）`
    )
    await loadInferenceEvidence()
  } catch (err: any) {
    message.error(err?.response?.data?.detail || '撤销失败')
  } finally {
    revokeAllLoading.value = false
  }
}

watch(
  () => route.params.id,
  async () => {
    if (route.name !== 'Chapter') return
    if (saveTimer.value) {
      clearTimeout(saveTimer.value)
      saveTimer.value = null
    }
    pageLoading.value = true
    try {
      await loadChapter()
    } catch (error) {
      console.error('Failed to load chapter:', error)
      message.error('加载章节失败')
    } finally {
      pageLoading.value = false
    }
  }
)

onMounted(async () => {
  window.addEventListener('keydown', onKeySave)
  try {
    await loadChapter()
  } catch (error) {
    console.error('Failed to load chapter:', error)
    message.error('加载章节失败')
  } finally {
    pageLoading.value = false
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeySave)
  if (saveTimer.value) clearTimeout(saveTimer.value)
  if (markdownDebounceTimer.value) clearTimeout(markdownDebounceTimer.value)
})
</script>

<style scoped>
.inf-prov-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  line-height: 1.5;
}

.chapter-spin {
  height: 100vh;
  min-height: 0;
}

.chapter-spin :deep(.n-spin-content) {
  min-height: 100%;
  height: 100%;
}

.chapter {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--app-page-bg, #f0f2f8);
}

.chapter :deep(.n-split) {
  flex: 1;
  min-height: 0;
}

.chapter-header {
  flex-shrink: 0;
  padding: 12px 18px;
  border-bottom: 1px solid var(--app-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  background: var(--app-surface);
}

.chapter-heading {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
}

.ico-back {
  font-size: 15px;
}

.ico-tiny {
  font-size: 10px;
  opacity: 0.8;
}

.editor-area {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 14px 16px;
  background: var(--app-surface);
}

.content-editor {
  flex: 1;
  min-height: 0;
  font-size: 16px;
  line-height: 1.85;
}

.content-editor :deep(textarea) {
  font-family: 'Source Han Serif SC', 'Noto Serif SC', Georgia, serif;
  line-height: 1.85;
}

.editor-footer {
  padding: 10px 0 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-slide-enter-active,
.preview-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.preview-slide-enter-from,
.preview-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.preview-panel {
  margin-top: 8px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--app-surface-subtle);
  border: 1px solid var(--app-border);
  max-height: 42vh;
  overflow: auto;
}

.preview-content {
  font-size: 14px;
}

.review-panel {
  height: 100%;
  min-height: 0;
  padding: 12px 14px;
  background: linear-gradient(180deg, var(--app-surface-subtle) 0%, rgba(99, 102, 241, 0.06) 100%);
  border-left: 1px solid var(--app-border);
}

.review-tabs {
  height: 100%;
}

.review-tabs :deep(.n-tab-pane) {
  padding-top: 12px;
}

.review-form {
  max-width: 100%;
}

.info-stats {
  padding: 8px 0;
}

.meta-line {
  font-size: 13px;
}

.meta-mono {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 12px;
  word-break: break-all;
}
</style>
