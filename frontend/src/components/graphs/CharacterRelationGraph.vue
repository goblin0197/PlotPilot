<template>
  <div class="crg-root">
    <div class="crg-toolbar">
      <n-text depth="3" class="crg-hint">
        人物关系图：从三元组自动生成，节点颜色表示重要程度（红=主角，橙=重要配角，蓝=次要人物）
      </n-text>
      <n-space :size="8">
        <n-button size="small" quaternary :loading="loading" @click="reload">刷新</n-button>
        <n-button size="small" secondary @click="goToKnowledge">编辑三元组</n-button>
      </n-space>
    </div>
    <div class="crg-chart">
      <div v-if="emptyHint" class="crg-empty">
        <n-empty description="尚无人物三元组，请在「叙事与知识」中添加" size="small" />
      </div>
      <GraphChart v-else :nodes="graphData.nodes" :links="graphData.links" height="100%" @node-click="handleNodeClick" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { knowledgeApi } from '../../api/knowledge'
import GraphChart from '../charts/GraphChart.vue'
import { convertGraph, type VisNode, type VisEdge, type EChartsGraphData, type EChartsNode } from '../../utils/visToEcharts'
import {
  tripleStringAttrs,
  characterImportanceZh,
} from '../../utils/knowledgeFactDisplay'

const props = defineProps<{ slug: string }>()
const router = useRouter()

interface Fact {
  id: string
  subject: string
  predicate: string
  object: string
  chapter_id?: number | null
  note?: string
  entity_type?: 'character' | 'location'
  importance?: 'primary' | 'secondary' | 'minor'
  description?: string
  attributes?: Record<string, unknown>
}

const loading = ref(false)
const facts = ref<Fact[]>([])
const graphData = ref<EChartsGraphData>({ nodes: [], links: [] })

const emptyHint = computed(() => facts.value.length === 0 && !loading.value)

// 根据重要程度返回颜色
const getColorByImportance = (importance?: string) => {
  switch (importance) {
    case 'primary':
      return { background: '#fecaca', border: '#ef4444' } // 红色 - 主角
    case 'secondary':
      return { background: '#fed7aa', border: '#f97316' } // 橙色 - 重要配角
    case 'minor':
      return { background: '#bfdbfe', border: '#3b82f6' } // 蓝色 - 次要人物
    default:
      return { background: '#e0e7ff', border: '#6366f1' } // 默认紫色
  }
}

/**
 * 执行 `buildVisData` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `buildVisData` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const buildVisData = () => {
  const labelToId = new Map<string, string>()
  const labelToImportance = new Map<string, string>()
  let nextN = 0

  /**
   * 执行 `entityId` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `entityId` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `raw` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  const entityId = (raw: string, importance?: string) => {
    const label = (raw || '').trim() || '（空）'
    if (!labelToId.has(label)) {
      labelToId.set(label, `ent_${nextN++}`)
      if (importance) {
        labelToImportance.set(label, importance)
      }
    }
    return labelToId.get(label)!
  }

  const nodeSeen = new Set<string>()
  const nodes: VisNode[] = []
  const edges: VisEdge[] = []

  for (const f of facts.value) {
    // 只处理人物类型的三元组
    if (f.entity_type !== 'character') continue

    const a = tripleStringAttrs(f)
    const objImp = a.object_importance as 'primary' | 'secondary' | 'minor' | undefined

    const sid = entityId(f.subject, f.importance)
    const oid = entityId(f.object, objImp)

    if (!nodeSeen.has(sid)) {
      nodeSeen.add(sid)
      const lab = (f.subject || '').trim() || '（空）'
      const importance = labelToImportance.get(lab) || f.importance
      const izh = characterImportanceZh(importance)
      nodes.push({
        id: sid,
        label: lab.length > 42 ? `${lab.slice(0, 40)}…` : lab,
        title: [lab, izh && `重要程度：${izh}`, f.description].filter(Boolean).join('\n'),
        color: getColorByImportance(importance),
        font: { size: 14 },
        shape: 'box',
        borderWidth: 2,
      })
    }

    if (!nodeSeen.has(oid)) {
      nodeSeen.add(oid)
      const lab = (f.object || '').trim() || '（空）'
      const oimp = labelToImportance.get(lab) || objImp
      const ozh = characterImportanceZh(oimp)
      nodes.push({
        id: oid,
        label: lab.length > 42 ? `${lab.slice(0, 40)}…` : lab,
        title: [lab, ozh && `重要程度：${ozh}`].filter(Boolean).join('\n'),
        color: getColorByImportance(oimp),
        font: { size: 13 },
        shape: 'box',
        borderWidth: 2,
      })
    }

    const pred = (f.predicate || '').trim() || '—'
    const ch = f.chapter_id != null && f.chapter_id >= 1 ? `第${f.chapter_id}章` : ''
    const tip = [pred, f.note, f.description, ch].filter(Boolean).join('\n')
    edges.push({
      id: f.id,
      from: sid,
      to: oid,
      label: pred.length > 28 ? `${pred.slice(0, 26)}…` : pred,
      title: tip,
      arrows: 'to',
      font: { size: 11, align: 'middle' },
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
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const reload = async () => {
  loading.value = true
  try {
    const res = await knowledgeApi.getKnowledge(props.slug)
    facts.value = (res.facts || []) as Fact[]
    await redraw()
  } catch (error) {
    console.error('Failed to load character graph:', error)
    window.$message?.error('加载人物关系图失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

/**
 * 响应 `node_click` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleNodeClick` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `node` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const handleNodeClick = (node: EChartsNode) => {
  // 可以跳转到人物详情页
}

/**
 * 执行 `goToKnowledge` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `goToKnowledge` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const goToKnowledge = () => {
  router.push(`/book/${props.slug}/knowledge`)
}

watch(
  () => props.slug,
  () => {
    void reload()
  }
)

onMounted(async () => {
  await nextTick()
  await reload()
})
</script>

<style scoped>
.crg-root {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  position: relative;
  background: var(--app-surface-subtle);
  border-radius: 10px;
  border: 1px solid var(--app-border-strong);
  overflow: hidden;
}

.crg-toolbar {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  border-bottom: 1px solid var(--app-border);
  background: var(--app-surface);
}

.crg-hint {
  font-size: 11px;
  line-height: 1.45;
  max-width: min(100%, 480px);
}

.crg-chart {
  flex: 1;
  min-height: 400px;
  overflow: hidden;
  position: relative;
}

.crg-empty {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  z-index: 1;
}
</style>
