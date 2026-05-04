/** 知识三元组在图表中的中文展示（与后端 importance / location_type 枚举对齐） */

export function tripleStringAttrs(t: { attributes?: Record<string, unknown> }): Record<string, string> {
  const a = t.attributes
  if (!a || typeof a !== 'object') return {}
  const out: Record<string, string> = {}
  for (const [k, v] of Object.entries(a)) {
    if (v !== undefined && v !== null) out[k] = String(v)
  }
  return out
}

/**
 * 执行 `characterImportanceZh` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `characterImportanceZh` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
export function characterImportanceZh(v?: string): string {
  switch (v) {
    case 'primary':
      return '主角'
    case 'secondary':
      return '重要配角'
    case 'minor':
      return '次要人物'
    default:
      return ''
  }
}

/**
 * 执行 `locationImportanceZh` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `locationImportanceZh` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
export function locationImportanceZh(v?: string): string {
  switch (v) {
    case 'core':
      return '核心'
    case 'important':
      return '重要'
    case 'normal':
      return '一般'
    default:
      return ''
  }
}

/**
 * 执行 `locationTypeZh` 对应的前端交互逻辑。
 *
 * 职责: 位于前端组件/组合式逻辑中，集中处理 `locationTypeZh` 的状态推导、事件分发或异步调用。
 * 关键输入输出: 主要读取当前组件的 props、ref、computed 或 store 状态。 返回值按函数签名或 Promise 约定交给调用方。
 * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
 * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
 */
export function locationTypeZh(v?: string): string {
  switch (v) {
    case 'city':
      return '城市'
    case 'region':
      return '区域'
    case 'building':
      return '建筑'
    case 'faction':
      return '势力'
    case 'realm':
      return '领域'
    default:
      return v || ''
  }
}
