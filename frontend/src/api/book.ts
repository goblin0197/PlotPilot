import type {
  BookListItem,
  BookDeskResponse,
  CastGraph,
  CastSearchResponse,
  CastCoverage,
  StoryKnowledge,
  KnowledgeSearchResponse,
  Bible,
  ChapterBody,
  ChapterReview,
  ChapterReviewAiResponse,
  ChapterStructure,
  SimpleResponse,
  SlugResponse,
  JobCreateResponse,
  JobStatusResponse,
} from '../types/api'
import { legacyBookHttp } from './config'

// Legacy API client (old /api endpoints)
// DEPRECATED: This file is maintained for backward compatibility only.
// Do NOT use these APIs in new code.
//
// Migration Status (as of 2026-04-01):
// ✅ MIGRATED:
//   - Chapter content: Use chapterApi.getChapter() / updateChapter()
//   - Chapter review: Use chapterApi.getChapterReview() / saveChapterReview()
//   - Chapter AI review: Use chapterApi.reviewChapterAi()
//   - Chapter structure: Use chapterApi.getChapterStructure()
//
// ⚠️ PENDING MIGRATION:
//   - Bible operations: BiblePanel.vue still uses bookApi.getBible() / saveBible()
//     Reason: New Bible API lacks bulk update endpoint; needs backend enhancement
//   - Cast operations: Multiple components use bookApi cast methods
//   - Knowledge operations: Multiple components use bookApi knowledge methods
//   - Desk operations: useWorkbench.ts uses bookApi.getDesk()
//
// Current dependencies:
// - bookApi: BiblePanel.vue, CastGraphCompact.vue, KnowledgePanel.vue,
//            KnowledgeTripleGraph.vue, useWorkbench.ts, Cast.vue, Chapter.vue (desk only)
// - jobApi: 已迁移至 api/workflow.ts（workflowApi）
//
// For new code, use the RESTful API clients:
// - novelApi from './novel.ts' for novel operations
// - chapterApi from './chapter.ts' for chapter operations (✅ FULLY MIGRATED)
// - bibleApi from './bible.ts' for bible operations (partial - needs bulk update)
//
// TODO: Migrate existing components to new API clients before removing this file.

const request = legacyBookHttp

export const bookApi = {
  /**
   * 请求 `/books` 查询接口并返回前端展示所需的数据。
   *
   * 职责: 作为前端 API 封装 `getList`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: 不接收业务参数，直接访问固定接口。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起只读 HTTP 请求；本函数不主动修改服务端状态。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  getList: () => request.get<BookListItem[]>('/books') as unknown as Promise<BookListItem[]>,
  /**
   * 请求 `/jobs/create-book` 创建资源或触发服务端流程。
   *
   * 职责: 作为前端 API 封装 `create`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `data` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起 HTTP 写入/触发请求，服务端状态可能随请求结果变化。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  create: (data: unknown) => request.post<SlugResponse>('/jobs/create-book', data) as unknown as Promise<SlugResponse>,
  /**
   * 请求 `/book/${slug}` 删除服务端资源。
   *
   * 职责: 作为前端 API 封装 `deleteBook`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起 HTTP 删除请求，服务端状态可能随请求结果变化。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  deleteBook: (slug: string) => request.delete<SimpleResponse>(`/book/${slug}`) as unknown as Promise<SimpleResponse>,
  /**
   * 请求 `/book/${slug}/cast` 查询接口并返回前端展示所需的数据。
   *
   * 职责: 作为前端 API 封装 `getCast`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起只读 HTTP 请求；本函数不主动修改服务端状态。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  getCast: (slug: string) => request.get<CastGraph>(`/book/${slug}/cast`) as unknown as Promise<CastGraph>,
  /**
   * 请求 `/book/${slug}/cast` 更新服务端资源。
   *
   * 职责: 作为前端 API 封装 `putCast`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 `data` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起 HTTP 更新请求，服务端状态可能随请求结果变化。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  putCast: (slug: string, data: unknown) => request.put(`/book/${slug}/cast`, data),
  /**
   * 请求 `/book/${slug}/cast/search` 查询接口并返回前端展示所需的数据。
   *
   * 职责: 作为前端 API 封装 `searchCast`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 `q` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起只读 HTTP 请求；本函数不主动修改服务端状态。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  searchCast: (slug: string, q: string) =>
    request.get<CastSearchResponse>(`/book/${slug}/cast/search`, { params: { q } }) as unknown as Promise<CastSearchResponse>,
  /** 正文与关系图对照：章节出现、设定未入库、书名号未匹配等 */
  getCastCoverage: (slug: string) =>
    request.get<CastCoverage>(`/book/${slug}/cast/coverage`) as unknown as Promise<CastCoverage>,
  /**
   * 请求 `/book/${slug}/knowledge` 查询接口并返回前端展示所需的数据。
   *
   * 职责: 作为前端 API 封装 `getKnowledge`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起只读 HTTP 请求；本函数不主动修改服务端状态。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  getKnowledge: (slug: string) =>
    request.get<StoryKnowledge>(`/book/${slug}/knowledge`) as unknown as Promise<StoryKnowledge>,
  /**
   * 请求 `/book/${slug}/knowledge` 更新服务端资源。
   *
   * 职责: 作为前端 API 封装 `putKnowledge`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 `data` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起 HTTP 更新请求，服务端状态可能随请求结果变化。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  putKnowledge: (slug: string, data: unknown) => request.put(`/book/${slug}/knowledge`, data),
  /**
   * 请求 `/book/${slug}/knowledge/search` 查询接口并返回前端展示所需的数据。
   *
   * 职责: 作为前端 API 封装 `knowledgeSearch`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 `q` 由调用方传入，用于拼接路径、查询参数或请求体。 `k` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起只读 HTTP 请求；本函数不主动修改服务端状态。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  knowledgeSearch: (slug: string, q: string, k = 6) =>
    request.get<KnowledgeSearchResponse>(`/book/${slug}/knowledge/search`, { params: { q, k } }) as unknown as Promise<KnowledgeSearchResponse>,
  /**
   * 请求 `/book/${slug}/desk` 查询接口并返回前端展示所需的数据。
   *
   * 职责: 作为前端 API 封装 `getDesk`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起只读 HTTP 请求；本函数不主动修改服务端状态。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  getDesk: (slug: string) =>
    request.get<BookDeskResponse>(`/book/${slug}/desk`) as unknown as Promise<BookDeskResponse>,
  /** @deprecated Use bibleApi.getBible() - Note: New API has different structure, needs bulk update endpoint */
  getBible: (slug: string) => request.get<Bible>(`/book/${slug}/bible`) as unknown as Promise<Bible>,
  /** @deprecated Use bibleApi - Note: New API has different structure, needs bulk update endpoint */
  saveBible: (slug: string, data: unknown) => request.put(`/book/${slug}/bible`, data),
  /** @deprecated Use chapterApi.getChapter() instead */
  getChapterBody: (slug: string, chapterId: number) =>
    request.get<ChapterBody>(`/book/${slug}/chapter/${chapterId}/body`) as unknown as Promise<ChapterBody>,
  /** @deprecated Use chapterApi.updateChapter() instead */
  saveChapterBody: (slug: string, chapterId: number, content: string) =>
    request.put(`/book/${slug}/chapter/${chapterId}/body`, { content }),
  /** @deprecated Use chapterApi.getChapterReview() instead */
  getChapterReview: (slug: string, chapterId: number) =>
    request.get<ChapterReview>(`/book/${slug}/chapter/${chapterId}/review`) as unknown as Promise<ChapterReview>,
  /** @deprecated Use chapterApi.saveChapterReview() instead */
  saveChapterReview: (slug: string, chapterId: number, status: string, memo: string) =>
    request.put(`/book/${slug}/chapter/${chapterId}/review`, { status, memo }),
  /** @deprecated Use chapterApi.reviewChapterAi() instead - 自动审读：返回 status/memo；save=true 时写入 editorial */
  reviewChapterAi: (slug: string, chapterId: number, save = false) =>
    request.post<ChapterReviewAiResponse>(`/book/${slug}/chapter/${chapterId}/review-ai`, { save }) as unknown as Promise<ChapterReviewAiResponse>,
  /** @deprecated Use chapterApi.getChapterStructure() instead */
  getChapterStructure: (slug: string, chapterId: number) =>
    request.get<ChapterStructure>(`/book/${slug}/chapter/${chapterId}/structure`) as unknown as Promise<ChapterStructure>,
}

export const jobApi = {
  /**
   * 请求 `/jobs/${slug}/plan` 创建资源或触发服务端流程。
   *
   * 职责: 作为前端 API 封装 `startPlan`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 `dryRun` 由调用方传入，用于拼接路径、查询参数或请求体。 `mode` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起 HTTP 写入/触发请求，服务端状态可能随请求结果变化。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  startPlan: (slug: string, dryRun = false, mode: 'initial' | 'revise' = 'initial') =>
    request.post<JobCreateResponse>(`/jobs/${slug}/plan`, { dry_run: dryRun, mode }) as unknown as Promise<JobCreateResponse>,
  /**
   * 请求 `/jobs/${slug}/write` 创建资源或触发服务端流程。
   *
   * 职责: 作为前端 API 封装 `startWrite`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 `from` 由调用方传入，用于拼接路径、查询参数或请求体。 `dryRun` 由调用方传入，用于拼接路径、查询参数或请求体。 `continuity` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起 HTTP 写入/触发请求，服务端状态可能随请求结果变化。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  startWrite: (slug: string, from: number, to?: number, dryRun = false, continuity = false) =>
    request.post<JobCreateResponse>(`/jobs/${slug}/write`, { from_chapter: from, to_chapter: to, dry_run: dryRun, continuity }) as unknown as Promise<JobCreateResponse>,
  /**
   * 请求 `/jobs/${slug}/run` 创建资源或触发服务端流程。
   *
   * 职责: 作为前端 API 封装 `startRun`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 `dryRun` 由调用方传入，用于拼接路径、查询参数或请求体。 `continuity` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起 HTTP 写入/触发请求，服务端状态可能随请求结果变化。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  startRun: (slug: string, dryRun = false, continuity = false) =>
    request.post<JobCreateResponse>(`/jobs/${slug}/run`, { dry_run: dryRun, continuity }) as unknown as Promise<JobCreateResponse>,
  /**
   * 请求 `/jobs/${slug}/export` 创建资源或触发服务端流程。
   *
   * 职责: 作为前端 API 封装 `startExport`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起 HTTP 写入/触发请求，服务端状态可能随请求结果变化。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  startExport: (slug: string) => request.post(`/jobs/${slug}/export`, {}),
  /**
   * 请求 `/jobs/${jobId}/cancel` 创建资源或触发服务端流程。
   *
   * 职责: 作为前端 API 封装 `cancelJob`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `jobId` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起 HTTP 写入/触发请求，服务端状态可能随请求结果变化。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  cancelJob: (jobId: string) => request.post<SimpleResponse>(`/jobs/${jobId}/cancel`, {}) as unknown as Promise<SimpleResponse>,
  /**
   * 请求 `/jobs/${jobId}` 查询接口并返回前端展示所需的数据。
   *
   * 职责: 作为前端 API 封装 `getStatus`，统一管理请求路径、参数形状和返回 Promise。
   * 关键输入输出: `jobId` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
   * 副作用: 会发起只读 HTTP 请求；本函数不主动修改服务端状态。
   * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
   */
  getStatus: (jobId: string) =>
    request.get<JobStatusResponse>(`/jobs/${jobId}`) as unknown as Promise<JobStatusResponse>,
}
