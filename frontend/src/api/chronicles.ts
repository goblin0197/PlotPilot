/**
 * 双螺旋编年史 BFF
 * GET /api/v1/novels/{novel_id}/chronicles
 */
import { apiClient } from './config'

export interface ChronicleStoryEvent {
  note_id: string
  time: string
  title: string
  description: string
  source_chapter: number | null
}

export interface ChronicleSnapshot {
  id: string
  kind: string
  name: string
  branch_name: string
  created_at: string | null
  description: string | null
  anchor_chapter: number | null
}

export interface ChronicleRow {
  chapter_index: number
  story_events: ChronicleStoryEvent[]
  snapshots: ChronicleSnapshot[]
}

export interface ChroniclesResponse {
  rows: ChronicleRow[]
  max_chapter_in_book: number
  note: string
}

export interface SnapshotRollbackResponse {
  deleted_chapter_ids: string[]
  deleted_count: number
}

export const chroniclesApi = {
  /**
   * 加载 `get` 相关数据并同步到前端状态。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `get` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `novelId` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  get: (novelId: string) =>
    apiClient.get<ChroniclesResponse>(`/novels/${novelId}/chronicles`) as Promise<ChroniclesResponse>,

  /**
   * 执行 `rollbackToSnapshot` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `rollbackToSnapshot` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `novelId` 表示事件载荷、当前记录或调用上下文。 `snapshotId` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  rollbackToSnapshot: (novelId: string, snapshotId: string) =>
    apiClient.post<SnapshotRollbackResponse>(
      `/novels/${novelId}/snapshots/${snapshotId}/rollback`,
    ) as Promise<SnapshotRollbackResponse>,
}
