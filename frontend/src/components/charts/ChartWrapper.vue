<template>
  <div
    class="chart-wrapper"
    :style="{ height: height }"
    role="img"
    :aria-label="ariaLabel"
  >
    <v-chart
      :option="option"
      :autoresize="true"
      :theme="theme"
      @click="handleClick"
    />
  </div>
</template>

<script setup lang="ts">
import VChart from 'vue-echarts'
import type { EChartsOption } from 'echarts'

const props = withDefaults(defineProps<{
  option: EChartsOption
  height?: string
  /** ECharts 内置主题名；由调用方基于 themeStore 传入，确保图表与 UI 主题同步 */
  theme?: string
  ariaLabel?: string
}>(), {
  height: '400px',
  theme: 'light',
  ariaLabel: 'Chart visualization'
})

const emit = defineEmits<{
  click: [params: any]
}>()

/**
 * 响应 `click` 相关的界面事件。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `handleClick` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `params` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 可能向父组件派发事件。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
const handleClick = (params: any) => {
  emit('click', params)
}
</script>

<style scoped>
.chart-wrapper {
  width: 100%;
}
</style>
