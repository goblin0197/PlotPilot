import type { GlobalStats, ChapterStats, WritingProgress } from '../types/api'
import { legacyStatsHttp } from './config'
import { novelApi } from './novel'

const request = legacyStatsHttp

/**
 * 请求 `/stats/global` 查询接口并返回前端展示所需的数据。
 *
 * 职责: 作为前端 API 封装 `enc`，统一管理请求路径、参数形状和返回 Promise。
 * 关键输入输出: `slug` 由调用方传入，用于拼接路径、查询参数或请求体。 返回值遵循 HTTP 客户端泛型约定。
 * 副作用: 会发起只读 HTTP 请求；本函数不主动修改服务端状态。
 * 异常/边界: 网络错误、鉴权失败或服务端校验失败由 HTTP 客户端向上透传。
 */
function enc(slug: string): string {
  return encodeURIComponent(slug)
}

export const statsApi = {
  /**
   * Get global statistics across all books
   * GET /stats/global
   */
  getGlobal: () => request.get<GlobalStats>('/stats/global') as unknown as Promise<GlobalStats>,

  /**
   * Get statistics for a specific chapter
   * GET /stats/book/{slug}/chapter/{chapterId}
   */
  getChapter: (slug: string, chapterId: number) =>
    request.get<ChapterStats>(`/stats/book/${enc(slug)}/chapter/${chapterId}`) as unknown as Promise<ChapterStats>,

  /**
   * Get writing progress over time
   * GET /stats/book/{slug}/progress
   */
  getProgress: (slug: string, days = 30) =>
    request.get<WritingProgress[]>(`/stats/book/${enc(slug)}/progress`, {
      params: { days },
    }) as unknown as Promise<WritingProgress[]>,

  /**
   * 书目统计（v1 novel statistics）+ 写作进度（legacy /api/stats）
   */
  getBookAllStats: async (slug: string, days = 30) => {
    const [bookStats, progress] = await Promise.all([
      novelApi.getNovelStatistics(slug),
      statsApi.getProgress(slug, days),
    ])
    return { bookStats, progress }
  },
}
