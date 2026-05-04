<template>
  <div class="character-graph-page">
    <n-page-header @back="handleBack" title="人物关系图">
      <template #extra>
        <n-space>
          <n-button @click="handleRefresh" :loading="loading">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <div class="graph-container">
      <CharacterRelationGraph
        v-if="novelId"
        :slug="novelId"
        @loading="loading = $event"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NPageHeader, NButton, NSpace, NIcon } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import CharacterRelationGraph from '../components/graphs/CharacterRelationGraph.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)

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
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const handleRefresh = () => {
  window.location.reload()
}
</script>

<style scoped>
.character-graph-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--app-page-bg);
}

.graph-container {
  flex: 1;
  overflow: hidden;
  padding: 16px;
}
</style>
