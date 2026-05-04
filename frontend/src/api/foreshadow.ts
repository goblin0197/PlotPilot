/**
 * 伏笔手账本 API：当下的疑问，本阶段兑现即可
 * /api/v1/novels/{novel_id}/foreshadow-ledger
 */
import { apiClient } from './config'

export interface ForeshadowEntry {
  id: string
  chapter: number
  character_id: string
  /** 主角或读者当下的疑问（宜短句） */
  question: string
  status: 'pending' | 'consumed'
  consumed_at_chapter: number | null
  suggested_resolve_chapter: number | null
  resolve_chapter_window: number | null
  importance: 'low' | 'medium' | 'high' | 'critical'
  created_at: string
}

export interface CreateForeshadowPayload {
  entry_id: string
  chapter: number
  character_id: string
  question: string
  suggested_resolve_chapter?: number
  resolve_chapter_window?: number
  importance?: 'low' | 'medium' | 'high' | 'critical'
}

export interface UpdateForeshadowPayload {
  chapter?: number
  character_id?: string
  question?: string
  status?: 'pending' | 'consumed'
  consumed_at_chapter?: number
  suggested_resolve_chapter?: number
  resolve_chapter_window?: number
  importance?: 'low' | 'medium' | 'high' | 'critical'
}

export const foreshadowApi = {
  /**
   * 执行 `list` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `list` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `novelId` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  list: (novelId: string, status?: 'pending' | 'consumed') =>
    apiClient.get<ForeshadowEntry[]>(`/novels/${novelId}/foreshadow-ledger`, {
      params: status ? { status } : {},
    }) as Promise<ForeshadowEntry[]>,

  /**
   * 加载 `get` 相关数据并同步到前端状态。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `get` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `novelId` 表示事件载荷、当前记录或调用上下文。 `entryId` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  get: (novelId: string, entryId: string) =>
    apiClient.get<ForeshadowEntry>(`/novels/${novelId}/foreshadow-ledger/${entryId}`) as Promise<ForeshadowEntry>,

  /**
   * 提交 `create` 相关变更并同步界面反馈。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `create` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `novelId` 表示事件载荷、当前记录或调用上下文。 `payload` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  create: (novelId: string, payload: CreateForeshadowPayload) =>
    apiClient.post<ForeshadowEntry>(`/novels/${novelId}/foreshadow-ledger`, payload) as Promise<ForeshadowEntry>,

  /**
   * 提交 `update` 相关变更并同步界面反馈。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `update` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `novelId` 表示事件载荷、当前记录或调用上下文。 `entryId` 表示事件载荷、当前记录或调用上下文。 `patch` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  update: (novelId: string, entryId: string, patch: UpdateForeshadowPayload) =>
    apiClient.put<ForeshadowEntry>(`/novels/${novelId}/foreshadow-ledger/${entryId}`, patch) as Promise<ForeshadowEntry>,

  /**
   * 提交 `remove` 相关变更并同步界面反馈。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `remove` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `novelId` 表示事件载荷、当前记录或调用上下文。 `entryId` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  remove: (novelId: string, entryId: string) =>
    apiClient.delete(`/novels/${novelId}/foreshadow-ledger/${entryId}`) as Promise<void>,

  /**
   * 执行 `markConsumed` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `markConsumed` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `novelId` 表示事件载荷、当前记录或调用上下文。 `entryId` 表示事件载荷、当前记录或调用上下文。 `consumedAtChapter` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  markConsumed: (novelId: string, entryId: string, consumedAtChapter: number) =>
    foreshadowApi.update(novelId, entryId, {
      status: 'consumed',
      consumed_at_chapter: consumedAtChapter,
    }),
}
