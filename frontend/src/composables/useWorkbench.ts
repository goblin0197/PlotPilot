import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { workflowApi } from '../api/workflow'
import { novelApi } from '../api/novel'
import { chapterApi } from '../api/chapter'
import { useStatsStore } from '../stores/statsStore'

// Constants
const STATS_DAYS = 30

/**
 * 执行 `formatApiErrorDetail` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `formatApiErrorDetail` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `error` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function formatApiErrorDetail(error: unknown): string {
  const e = error as { response?: { data?: { detail?: unknown } }; message?: string }
  const d = e?.response?.data?.detail
  if (typeof d === 'string' && d.trim()) return d
  if (Array.isArray(d)) {
    const parts = d.map((x: { msg?: string }) => (typeof x?.msg === 'string' ? x.msg : JSON.stringify(x)))
    return parts.join('; ') || ''
  }
  if (e?.message && typeof e.message === 'string') return e.message
  return ''
}

// Type definitions
export interface BookMeta {
  has_bible?: boolean
  has_outline?: boolean
}

export interface UseWorkbenchOptions {
  slug: string
}

/**
 * 执行 `useWorkbench` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `useWorkbench` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
export function useWorkbench(options: UseWorkbenchOptions) {
  const { slug } = options
  const router = useRouter()
  const message = useMessage()
  const statsStore = useStatsStore()

  // State - Business logic only, no UI state
  const bookTitle = ref('')
  const chapters = ref<{ id: number; number: number; title: string; word_count: number }[]>([])
  const bookMeta = ref<BookMeta>({})
  const pageLoading = ref(true)
  const currentChapterId = ref<number | null>(null)
  const chapterContent = ref('')
  const chapterLoading = ref(false)

  /** 右栏子面板 id，与 SettingsPanel 中 foundation / narrative / tactical 的 tab name 一致 */
  const rightPanel = ref<string>('bible')
  const biblePanelKey = ref(0)
  const currentJobId = ref<string | null>(null)


  const hasStructure = computed(() => {
    return bookMeta.value.has_bible || bookMeta.value.has_outline
  })

  /**
   * 执行 `setRightPanel` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `setRightPanel` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `panel` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const setRightPanel = (panel: string) => {
    rightPanel.value = panel
  }

  /**
   * 加载 `desk` 相关数据并同步到前端状态。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `loadDesk` 的状态推导、事件分发或异步调用。
   * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const loadDesk = async () => {
    // Use new novelApi and chapterApi instead of bookApi.getDesk
    const [novelData, chaptersData] = await Promise.all([
      novelApi.getNovel(slug),
      chapterApi.listChapters(slug)
    ])

    bookTitle.value = novelData.title || slug

    // Map ChapterDTO[] to the format expected by the UI
    chapters.value = chaptersData.map(ch => ({
      id: ch.number,
      number: ch.number,
      title: ch.title,
      word_count: ch.word_count || 0
    }))

    // Use metadata from NovelDTO
    bookMeta.value = {
      has_bible: novelData.has_bible,
      has_outline: novelData.has_outline,
    }
  }

  /**
   * 加载 `data` 相关数据并同步到前端状态。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `loadData` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `includeStats` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const loadData = async (includeStats = false) => {
    pageLoading.value = true
    try {
      const promises: Promise<unknown>[] = [loadDesk()]
      if (includeStats) {
        promises.push(statsStore.loadBookAllStats(slug, STATS_DAYS, true))
      }
      await Promise.all(promises)
    } finally {
      pageLoading.value = false
    }
  }

  /**
   * 响应 `job_completed` 相关的界面事件。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleJobCompleted` 的状态推导、事件分发或异步调用。
   * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const handleJobCompleted = async () => {
    // Notify stats store to invalidate cache and reload
    statsStore.onJobCompleted(slug)
    // Refresh workbench data
    await loadDesk()
    // Force Bible panel refresh if visible
    if (rightPanel.value === 'bible') {
      biblePanelKey.value += 1
    }
  }

  /**
   * 执行 `restoreJobState` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `restoreJobState` 的状态推导、事件分发或异步调用。
   * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const restoreJobState = () => {
    // Note: localStorage recovery not currently used in the architecture
    // Job state is managed through API polling and component lifecycle
    // This method is a no-op but preserved for future expansion
  }


  /**
   * 执行 `goHome` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `goHome` 的状态推导、事件分发或异步调用。
   * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const goHome = () => {
    router.push('/')
  }

  /**
   * 判断错误是否为 404（后端 EntityNotFoundError / HTTP 404）
   */
  function is404(error: unknown): boolean {
    const e = error as { response?: { status?: number }; message?: string }
    if (e?.response?.status === 404) return true
    const detail = formatApiErrorDetail(error)
    return /not\s*found|不存在/i.test(detail)
  }

  /**
   * 执行 `goToChapter` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `goToChapter` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `id` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求；可能触发用户提示。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const goToChapter = async (id: number, nodeTitle?: string) => {
    if (!Number.isFinite(id) || id < 1) {
      message.error('无效的章节号')
      return
    }

    chapterLoading.value = true
    try {
      let chapter = await chapterApi.getChapter(slug, id).catch(async (err) => {
        if (!is404(err)) throw err
        // 章节正文不存在：静默创建空白记录（对应结构树手动添加的节点）
        await chapterApi.ensureChapter(slug, id, nodeTitle ?? '')
        return chapterApi.getChapter(slug, id)
      })
      currentChapterId.value = id
      chapterContent.value = chapter.content || ''
      // 若刚刚是新建的空白章节，刷新侧栏章节列表
      const existed = chapters.value.some((c) => c.number === id)
      if (!existed) {
        await loadDesk()
      }
    } catch (error) {
      const detail = formatApiErrorDetail(error)
      currentChapterId.value = null
      chapterContent.value = ''
      message.error(
        detail
          ? `加载第 ${id} 章失败：${detail}`
          : `加载第 ${id} 章失败，请确认后端已启动。`
      )
    } finally {
      chapterLoading.value = false
    }
  }

  /**
   * 响应 `chapter_select` 相关的界面事件。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleChapterSelect` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `chapterId` 表示事件载荷、当前记录或调用上下文。 `title` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 可能发起异步请求。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const handleChapterSelect = async (chapterId: number, title = '') => {
    await goToChapter(chapterId, title)
  }

  /**
   * 响应 `settings` 相关的界面事件。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleUpdateSettings` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `_settings` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const handleUpdateSettings = async (_settings: Record<string, unknown>) => {
    // Settings are managed by child components (BiblePanel, KnowledgePanel)
    // This method provides a consistent interface for future use
    // Current architecture uses delegation pattern
  }

  return {
    // State
    bookTitle,
    chapters,
    rightPanel,
    biblePanelKey,
    pageLoading,
    bookMeta,
    currentJobId,
    currentChapterId,
    chapterContent,
    chapterLoading,

    // Methods
    setRightPanel,
    loadDesk,
    handleChapterSelect,
    goHome,
    goToChapter,
  }
}
