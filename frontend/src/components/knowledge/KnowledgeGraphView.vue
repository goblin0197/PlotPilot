<template>
  <div class="kgv-root">
    <div v-if="emptyHint" class="kgv-empty">
      <n-empty description="尚无三元组，可打开「三元组表格」添加，或使用 kg_upsert_fact" size="small" />
    </div>
    <GraphChart v-else :nodes="graphData.nodes" :links="graphData.links" height="100%" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watchEffect, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { knowledgeApi } from '../../api/knowledge'
import GraphChart from '../charts/GraphChart.vue'
import { convertGraph, type VisNode, type VisEdge, type EChartsGraphData } from '../../utils/visToEcharts'
import { useThemeStore } from '../../stores/themeStore'

const props = defineProps<{ slug: string }>()
const emit = defineEmits<{ reload: [] }>()
const message = useMessage()
const themeStore = useThemeStore()

interface Fact {
  id: string
  subject: string
  predicate: string
  object: string
  chapter_id?: number | null
  note?: string
  entity_type?: 'character' | 'location' | null
}

const loading = ref(false)
const facts = ref<Fact[]>([])
const graphData = ref<EChartsGraphData>({ nodes: [], links: [] })

const emptyHint = computed(() => facts.value.length === 0 && !loading.value)

/** 主题色计算为 computed，使主题切换时图谱颜色即时响应 */
const themeColors = computed(() => {
  const { isDark, isAnchor } = themeStore

  if (isAnchor) {
    return {
      subject: { background: '#1c1810', border: '#c9a227' },
      object: { background: '#1a0f08', border: '#d97706' },
      labelColor: '#f0ead6',
      edgeColor: '#8a8070',
    }
  }
  if (isDark) {
    return {
      subject: { background: '#1e1b4b', border: '#818cf8' },
      object: { background: '#500724', border: '#f472b6' },
      labelColor: '#e2e8f0',
      edgeColor: '#94a3b8',
    }
  }
  return {
    subject: { background: '#e0e7ff', border: '#4f46e5' },
    object: { background: '#fce7f3', border: '#be185d' },
    labelColor: '#0f172a',
    edgeColor: '#475569',
  }
})

/**
 * 执行 `buildVisData` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `buildVisData` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const buildVisData = () => {
  const colors = themeColors.value
  const labelToId = new Map<string, string>()
  let nextN = 0

  /**
   * 执行 `entityId` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `entityId` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `raw` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const entityId = (raw: string) => {
    const label = (raw || '').trim() || '（空）'
    if (!labelToId.has(label)) {
      labelToId.set(label, `ent_${nextN++}`)
    }
    return labelToId.get(label)!
  }

  const nodeSeen = new Set<string>()
  const nodes: VisNode[] = []
  const edges: VisEdge[] = []

  for (const f of facts.value) {
    const sid = entityId(f.subject)
    const oid = entityId(f.object)
    if (!nodeSeen.has(sid)) {
      nodeSeen.add(sid)
      const lab = (f.subject || '').trim() || '（空）'
      nodes.push({
        id: sid,
        label: lab.length > 42 ? `${lab.slice(0, 40)}…` : lab,
        title: lab,
        color: colors.subject,
        font: { size: 13, color: colors.labelColor },
        itemStyle: {
          color: colors.subject.background,
          borderColor: colors.subject.border,
          borderWidth: 1.5,
        }
      })
    }
    if (!nodeSeen.has(oid)) {
      nodeSeen.add(oid)
      const lab = (f.object || '').trim() || '（空）'
      nodes.push({
        id: oid,
        label: lab.length > 42 ? `${lab.slice(0, 40)}…` : lab,
        title: lab,
        color: colors.object,
        font: { size: 13, color: colors.labelColor },
        itemStyle: {
          color: colors.object.background,
          borderColor: colors.object.border,
          borderWidth: 1.5,
        }
      })
    }
    const pred = (f.predicate || '').trim() || '—'
    const ch = f.chapter_id != null && f.chapter_id >= 1 ? `第${f.chapter_id}章` : ''
    const tip = [pred, f.note, ch].filter(Boolean).join('\n')
    edges.push({
      id: f.id,
      from: sid,
      to: oid,
      label: pred.length > 28 ? `${pred.slice(0, 26)}…` : pred,
      title: tip,
      arrows: 'to',
      color: colors.edgeColor,
      font: { size: 12, align: 'middle', color: colors.edgeColor },
    })
  }

  return convertGraph(nodes, edges)
}

/**
 * 执行 `redraw` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `redraw` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const redraw = async () => {
  await nextTick()
  graphData.value = buildVisData()
}

/**
 * 执行 `reload` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `reload` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求；可能触发用户提示。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const reload = async () => {
  loading.value = true
  try {
    const data = await knowledgeApi.getKnowledge(props.slug)
    facts.value = data.facts || []
    await redraw()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

/**
 * 响应 `reload_event` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleReloadEvent` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const handleReloadEvent = () => {
  reload()
}

// 数据变化时立即重绘
watch(facts, () => {
  if (facts.value.length > 0) void redraw()
}, { deep: false })

// 主题切换时延迟 200ms 重绘，避免在主题过渡动画期间阻塞主线程
let themeRedrawTimer: ReturnType<typeof setTimeout> | null = null
watchEffect(() => {
  // 建立对 themeColors 的追踪；facts.length 只做守卫
  const colors = themeColors.value
  const hasData = facts.value.length > 0
  if (!hasData || !colors) return

  if (themeRedrawTimer) clearTimeout(themeRedrawTimer)
  themeRedrawTimer = setTimeout(() => {
    themeRedrawTimer = null
    void redraw()
  }, 200)
})

onMounted(() => {
  reload()
  window.addEventListener('aitext:knowledge:reload', handleReloadEvent)
})

onUnmounted(() => {
  window.removeEventListener('aitext:knowledge:reload', handleReloadEvent)
  if (themeRedrawTimer) clearTimeout(themeRedrawTimer)
})
</script>

<style scoped>
.kgv-root {
  flex: 1;
  min-height: 500px;
  position: relative;
  display: flex;
  flex-direction: column;
}

.kgv-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 500px;
}
</style>
