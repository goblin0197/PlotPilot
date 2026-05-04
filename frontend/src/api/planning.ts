/**
 * 统一的规划 API
 */

import { apiClient } from './config'

// ==================== 类型定义 ====================

export interface StructurePreference {
  parts: number
  volumes_per_part: number
  acts_per_volume: number
}

export interface MacroPlanRequest {
  target_chapters: number
  structure: StructurePreference
}

export interface MacroActNode {
  title: string
  description?: string
  [key: string]: unknown
}

export interface MacroVolumeNode {
  title: string
  description?: string
  acts?: MacroActNode[]
  [key: string]: unknown
}

export interface MacroPartNode {
  title: string
  description?: string
  volumes?: MacroVolumeNode[]
  [key: string]: unknown
}

export interface MacroPlanGenerateResponse {
  success: boolean
  task_started: boolean
  novel_id: string
  [key: string]: unknown
}

export interface MacroPlanProgress {
  status: 'idle' | 'running' | 'completed' | 'failed'
  current: number
  total: number
  percent: number
  message: string
}

export interface MacroPlanResultPayload {
  success: boolean
  structure: MacroPartNode[]
  quality_metrics?: Record<string, unknown>
  generation_time?: number
  [key: string]: unknown
}

export interface MacroPlanResultResponse {
  ready: boolean
  result: MacroPlanResultPayload | null
  error: string | null
}

export interface ActChaptersRequest {
  chapter_count?: number
}

export interface ContinuePlanningRequest {
  current_chapter: number
}

export interface ContinuePlanResult {
  /** 当前幕是否写完 */
  is_act_complete: boolean
  /** 是否需要创建下一幕 */
  needs_next_act: boolean
  /** 当前幕 story_node id（用于 createNextAct） */
  current_act_id: string | null
  /** 当前幕标题 */
  current_act_title?: string
  /** 当前章号在幕内的进度说明 */
  progress_message?: string
  /** 幕内已写章节数 */
  completed_chapters?: number
  /** 幕内总规划章节数 */
  total_chapters?: number
  /** 后端原始消息（兜底） */
  message?: string
  [key: string]: unknown
}

/** story_node 结构节点（树形，与后端 to_dict / 层级树一致） */
export interface StoryNode {
  id: string
  novel_id?: string
  node_type: 'part' | 'volume' | 'act' | 'chapter'
  title: string
  number?: number
  description?: string
  outline?: string
  children?: StoryNode[]
  /** 章节：视角角色 id、时间线等 */
  pov_character_id?: string | null
  timeline_start?: string | null
  timeline_end?: string | null
  metadata?: Record<string, unknown>
  [key: string]: unknown
}

/** GET /planning/novels/:id/structure 的 data 载荷 */
export interface PlanningStructurePayload {
  novel_id: string
  nodes: StoryNode[]
}

// ==================== API ====================

export const planningApi = {
  // ==================== 宏观规划 ====================

  generateMacro: (novelId: string, data: MacroPlanRequest) =>
    apiClient.post<MacroPlanGenerateResponse>(
      `/planning/novels/${novelId}/macro/generate`,
      data,
      { timeout: 300000 }
    ) as unknown as Promise<MacroPlanGenerateResponse>,

  /**
   * 加载 `macro_progress` 相关数据并同步到前端状态。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `getMacroProgress` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `novelId` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  getMacroProgress: (novelId: string) =>
    apiClient.get<{ success: boolean; data: MacroPlanProgress }>(
      `/planning/novels/${novelId}/macro/progress`
    ) as unknown as Promise<{ success: boolean; data: MacroPlanProgress }>,

  /**
   * 加载 `macro_result` 相关数据并同步到前端状态。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `getMacroResult` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `novelId` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  getMacroResult: (novelId: string) =>
    apiClient.get<{ success: boolean; data: MacroPlanResultResponse }>(
      `/planning/novels/${novelId}/macro/result`
    ) as unknown as Promise<{ success: boolean; data: MacroPlanResultResponse }>,

  /**
   * 执行 `confirmMacro` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `confirmMacro` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `novelId` 表示事件载荷、当前记录或调用上下文。 `data` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  confirmMacro: (novelId: string, data: { structure: Record<string, unknown>[] }) =>
    apiClient.post(`/planning/novels/${novelId}/macro/confirm`, data),

  // ==================== 幕级规划 ====================

  generateActChapters: (actId: string, data: ActChaptersRequest) =>
    apiClient.post(`/planning/acts/${actId}/chapters/generate`, data),

  /**
   * 执行 `confirmActChapters` 对应的前端交互逻辑。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `confirmActChapters` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `actId` 表示事件载荷、当前记录或调用上下文。 `data` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  confirmActChapters: (actId: string, data: { chapters: Record<string, unknown>[] }) =>
    apiClient.post(`/planning/acts/${actId}/chapters/confirm`, data),

  // ==================== AI 续规划 ====================

  continuePlanning: (novelId: string, data: ContinuePlanningRequest) =>
    apiClient.post<ContinuePlanResult>(`/planning/novels/${novelId}/continue`, data) as unknown as Promise<ContinuePlanResult>,

  /**
   * 提交 `next_act` 相关变更并同步界面反馈。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `createNextAct` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `actId` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  createNextAct: (actId: string) =>
    apiClient.post<Record<string, unknown>>(`/planning/acts/${actId}/create-next`) as unknown as Promise<Record<string, unknown>>,

  // ==================== 查询 ====================

  getStructure: (novelId: string) =>
    apiClient.get<{ success: boolean; data: PlanningStructurePayload }>(
      `/planning/novels/${novelId}/structure`
    ) as unknown as Promise<{ success: boolean; data: PlanningStructurePayload }>,

  /**
   * 加载 `act_detail` 相关数据并同步到前端状态。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `getActDetail` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `actId` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  getActDetail: (actId: string) =>
    apiClient.get<{ success: boolean; data: StoryNode }>(`/planning/acts/${actId}`) as unknown as Promise<{ success: boolean; data: StoryNode }>,

  /**
   * 加载 `chapter_detail` 相关数据并同步到前端状态。
   *
   * 职责: 位于前端组件/组合式逻辑中，集中处理 `getChapterDetail` 的状态推导、事件分发或异步调用。
   * 关键输入输出: `chapterId` 表示事件载荷、当前记录或调用上下文。 返回值按函数签名或 Promise 约定交给调用方。
   * 副作用: 不主动修改外部状态，主要返回计算结果或整理后的数据。
   * 异常/边界: 缺少当前章节、slug、选中项或接口失败时按函数内的提前返回、提示或上层错误处理执行。
   */
  getChapterDetail: (chapterId: string) =>
    apiClient.get<{ success: boolean; data: { chapter: StoryNode; elements: unknown[] } }>(`/planning/chapters/${chapterId}`) as unknown as Promise<{ success: boolean; data: { chapter: StoryNode; elements: unknown[] } }>,
}
