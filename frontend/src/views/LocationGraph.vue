<template>
  <div class="location-graph-page">
    <n-page-header @back="handleBack" title="地点关系图">
      <template #extra>
        <n-space>
          <n-button type="primary" @click="openTriplesDrawer()">三元组表格</n-button>
          <n-button @click="handleRefresh" :loading="loading">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <div class="graph-body">
      <div class="graph-main">
        <LocationRelationGraph
          v-if="novelId"
          ref="locGraphRef"
          :slug="novelId"
          @loading="loading = $event"
          @node-click="handleNodeClick"
        />
      </div>
      <aside class="graph-side">
        <n-tabs v-model:value="activeTab" type="segment" animated>
          <n-tab-pane name="node" tab="地点详情">
            <div v-if="selectedNode" class="side-form">
              <n-button
                block
                type="primary"
                size="small"
                style="margin-bottom: 12px"
                @click="openTriplesDrawer(selectedNode.name)"
              >
                编辑此地点相关三元组
              </n-button>
              <n-descriptions label-placement="left" :column="1" bordered size="small">
                <n-descriptions-item label="名称">{{ selectedNode.name }}</n-descriptions-item>
                <n-descriptions-item label="类型" v-if="selectedNode.location_type">
                  {{ locationTypeLabel(selectedNode.location_type) }}
                </n-descriptions-item>
                <n-descriptions-item label="重要程度" v-if="selectedNode.importance">
                  <n-tag :type="importanceTagType(selectedNode.importance)" size="small">
                    {{ importanceLabel(selectedNode.importance) }}
                  </n-tag>
                </n-descriptions-item>
                <n-descriptions-item label="描述" v-if="selectedNode.description">
                  {{ selectedNode.description }}
                </n-descriptions-item>
                <n-descriptions-item label="首次出现" v-if="selectedNode.first_appearance">
                  第 {{ selectedNode.first_appearance }} 章
                </n-descriptions-item>
                <n-descriptions-item label="相关章节" v-if="selectedNode.related_chapters?.length">
                  <n-space size="small">
                    <n-tag v-for="ch in selectedNode.related_chapters" :key="ch" size="small">
                      第 {{ ch }} 章
                    </n-tag>
                  </n-space>
                </n-descriptions-item>
                <n-descriptions-item label="标签" v-if="selectedNode.tags?.length">
                  <n-space size="small">
                    <n-tag v-for="tag in selectedNode.tags" :key="tag" size="small" type="info">
                      {{ tag }}
                    </n-tag>
                  </n-space>
                </n-descriptions-item>
                <n-descriptions-item label="属性" v-if="selectedNode.attributes && Object.keys(selectedNode.attributes).length">
                  <div class="attributes-list">
                    <div v-for="(value, key) in selectedNode.attributes" :key="key" class="attr-item">
                      <span class="attr-key">{{ key }}:</span>
                      <span class="attr-value">{{ value }}</span>
                    </div>
                  </div>
                </n-descriptions-item>
              </n-descriptions>
            </div>
            <n-empty v-else description="点击图中节点查看地点详情" size="small" style="margin-top: 40px;" />
          </n-tab-pane>
        </n-tabs>
      </aside>
    </div>

    <n-drawer v-model:show="triplesDrawerOpen" :width="920" placement="right" display-directive="if">
      <n-drawer-content title="地点相关三元组" closable>
        <KnowledgeTriplesTableEditor
          v-if="triplesDrawerOpen"
          :key="triplesDrawerKey"
          :slug="novelId"
          default-entity-filter="location"
          :focus-entity-name="triplesDrawerFocus"
          @saved="onTriplesSaved"
        />
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NPageHeader,
  NButton,
  NSpace,
  NIcon,
  NTabs,
  NTabPane,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NEmpty,
  NDrawer,
  NDrawerContent,
} from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import LocationRelationGraph from '../components/graphs/LocationRelationGraph.vue'
import KnowledgeTriplesTableEditor from '../components/knowledge/KnowledgeTriplesTableEditor.vue'
import type { EChartsNode } from '../utils/visToEcharts'
import type { ComponentPublicInstance } from 'vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const activeTab = ref<'node'>('node')

const locGraphRef = ref<ComponentPublicInstance<{ reload: () => Promise<void> }> | null>(null)
const triplesDrawerOpen = ref(false)
const triplesDrawerFocus = ref('')
const triplesDrawerKey = ref(0)

interface LocationNode extends EChartsNode {
  location_type?: string
  importance?: string
  description?: string
  first_appearance?: number
  related_chapters?: number[]
  tags?: string[]
  attributes?: Record<string, any>
}

const selectedNode = ref<LocationNode | null>(null)

const novelId = computed(() => route.params.slug as string)

/**
 * 响应 `back` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleBack` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const handleBack = () => {
  router.push(`/book/${novelId.value}/workbench`)
}

/**
 * 响应 `refresh` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleRefresh` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const handleRefresh = () => {
  window.location.reload()
}

/**
 * 响应 `node_click` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleNodeClick` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `node` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const handleNodeClick = (node: EChartsNode) => {
  selectedNode.value = node as LocationNode
  activeTab.value = 'node'
}

/**
 * 打开 `triples_drawer` 对应的弹窗、面板或交互状态。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `openTriplesDrawer` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const openTriplesDrawer = (focusName?: string) => {
  triplesDrawerFocus.value = (focusName || '').trim()
  triplesDrawerKey.value += 1
  triplesDrawerOpen.value = true
}

/**
 * 响应 `triples_saved` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `onTriplesSaved` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能更新 Vue 响应式状态；可能发起异步请求。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const onTriplesSaved = async () => {
  await locGraphRef.value?.reload?.()
}

/**
 * 执行 `locationTypeLabel` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `locationTypeLabel` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `type` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const locationTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    city: '城市',
    region: '区域',
    building: '建筑',
    faction: '势力',
    realm: '境界/领域'
  }
  return labels[type] || type
}

/**
 * 执行 `importanceLabel` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `importanceLabel` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `importance` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const importanceLabel = (importance: string) => {
  const labels: Record<string, string> = {
    core: '核心地点',
    important: '重要地点',
    normal: '一般地点'
  }
  return labels[importance] || importance
}

/**
 * 执行 `importanceTagType` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `importanceTagType` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `importance` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const importanceTagType = (importance: string) => {
  const types: Record<string, 'success' | 'warning' | 'default'> = {
    core: 'success',
    important: 'warning',
    normal: 'default'
  }
  return types[importance] || 'default'
}
</script>

<style scoped>
.location-graph-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--app-page-bg);
}

.graph-body {
  flex: 1;
  min-height: 0;
  display: flex;
}

.graph-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding: 16px;
  background: #f5f5f5;
}

.graph-side {
  width: min(400px, 42vw);
  flex-shrink: 0;
  padding: 12px;
  overflow: auto;
  background: var(--app-surface);
  border-left: 1px solid #e5e7eb;
}

.side-form {
  padding-top: 8px;
}

.attributes-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.attr-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
}

.attr-key {
  font-weight: 500;
  color: #64748b;
}

.attr-value {
  color: #0f172a;
}
</style>
