<template>
  <div v-if="report" class="cr-panel">
    <div class="cr-head">
      <span class="cr-title">一致性报告</span>
      <n-text v-if="tokenCount != null" depth="3" class="cr-meta">约 {{ tokenCount }} tokens</n-text>
    </div>

    <n-collapse
      v-if="hasAnyContent"
      :default-expanded-names="defaultExpanded"
      display-directive="show"
    >
      <n-collapse-item v-if="report.issues?.length" title="问题" name="issues">
        <ul class="cr-list">
          <li
            v-for="(it, i) in report.issues"
            :key="'i-' + i"
            class="cr-item"
          >
            <n-space align="center" :size="8" wrap>
              <n-tag size="small" :type="severityTag(it.severity)" round>
                {{ severityLabel(it.severity) }}
              </n-tag>
              <n-tag size="tiny" :bordered="false">{{ it.type }}</n-tag>
              <n-button
                v-if="it.location != null"
                size="tiny"
                quaternary
                @click="$emit('location-click', it.location)"
              >
                位置 {{ it.location }}
              </n-button>
            </n-space>
            <p class="cr-desc">{{ it.description }}</p>
          </li>
        </ul>
      </n-collapse-item>

      <n-collapse-item v-if="report.warnings?.length" title="警告" name="warnings">
        <ul class="cr-list">
          <li v-for="(it, i) in report.warnings" :key="'w-' + i" class="cr-item">
            <n-space align="center" :size="8" wrap>
              <n-tag size="small" :type="severityTag(it.severity)" round>
                {{ severityLabel(it.severity) }}
              </n-tag>
              <n-tag size="tiny" :bordered="false">{{ it.type }}</n-tag>
              <n-button
                v-if="it.location != null"
                size="tiny"
                quaternary
                @click="$emit('location-click', it.location)"
              >
                位置 {{ it.location }}
              </n-button>
            </n-space>
            <p class="cr-desc">{{ it.description }}</p>
          </li>
        </ul>
      </n-collapse-item>

      <n-collapse-item v-if="report.suggestions?.length" title="建议" name="suggestions">
        <ol class="cr-suggestions">
          <li v-for="(s, i) in report.suggestions" :key="'s-' + i">{{ s }}</li>
        </ol>
      </n-collapse-item>
    </n-collapse>

    <n-empty v-else description="暂无一致性问题或建议" size="small" class="cr-empty" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ConsistencyReportDTO } from '../../api/workflow'

interface Props {
  report: ConsistencyReportDTO | null
  tokenCount?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  tokenCount: null,
})

defineEmits<{
  (e: 'location-click', location: number): void
}>()

const hasAnyContent = computed(() => {
  const r = props.report
  if (!r) return false
  return (
    (r.issues?.length ?? 0) > 0 ||
    (r.warnings?.length ?? 0) > 0 ||
    (r.suggestions?.length ?? 0) > 0
  )
})

const defaultExpanded = computed(() => {
  const names: string[] = []
  if (props.report?.issues?.length) names.push('issues')
  if (props.report?.warnings?.length) names.push('warnings')
  if (props.report?.suggestions?.length) names.push('suggestions')
  return names.length ? names : ['issues']
})

/**
 * 执行 `normSeverity` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `normSeverity` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `s` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function normSeverity(s: string): string {
  return (s || '').toLowerCase()
}

/**
 * 执行 `severityTag` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `severityTag` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `sev` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function severityTag(sev: string): 'error' | 'warning' | 'info' | 'default' {
  const s = normSeverity(sev)
  if (s === 'critical') return 'error'
  if (s === 'important') return 'warning'
  if (s === 'minor') return 'info'
  return 'default'
}

/**
 * 执行 `severityLabel` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `severityLabel` 的状态推导、事件分发或异步调用。
 * 关键输入输出: `sev` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
function severityLabel(sev: string): string {
  const s = normSeverity(sev)
  if (s === 'critical') return '严重'
  if (s === 'important') return '重要'
  if (s === 'minor') return '轻微'
  return sev || '—'
}
</script>

<style scoped>
.cr-panel {
  border: 1px solid var(--aitext-split-border, #e0e0e6);
  border-radius: 8px;
  padding: 10px 12px;
  background: var(--aitext-panel-muted, rgba(0, 0, 0, 0.02));
  max-height: min(52vh, 480px);
  overflow: auto;
}

.cr-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.cr-title {
  font-weight: 600;
  font-size: 14px;
}

.cr-meta {
  font-size: 12px;
}

.cr-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.cr-item + .cr-item {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--aitext-split-border, #e0e0e6);
}

.cr-desc {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--n-text-color);
}

.cr-suggestions {
  margin: 0;
  padding-left: 1.2em;
  font-size: 13px;
  line-height: 1.55;
}

.cr-suggestions li + li {
  margin-top: 6px;
}

.cr-empty {
  padding: 12px 0;
}
</style>
