"""删章并重排序号后，各层「章号引用」的统一变换规则。

与 ``SqliteChapterRepository`` 内 SQL 更新语义对齐：
大于被删章号减 1；等于被删章号收束到 ``max(1, deleted-1)``；小于不变。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ChapterRenumberSpec:
    """一次删章事件对应的章号映射说明（供 JSON / 向量等扩展点共用）。"""

    novel_id: str
    deleted_chapter_number: int

    def shift_chapter_ref(self, chapter_number: int) -> int:
        """将「仍指向旧编号体系」的章号映射到删章后的新编号。"""
        d = self.deleted_chapter_number
        n = int(chapter_number)
        if n > d:
            return n - 1
        if n == d:
            return max(1, d - 1)
        return n

    def shift_optional_chapter_ref(self, chapter_number: Optional[int]) -> Optional[int]:
        """同步执行 `shift_optional_chapter_ref` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `shift_optional_chapter_ref` 这一入口。
        关键输入:
        - chapter_number: `Optional[int]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `Optional[int]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if chapter_number is None:
            return None
        return self.shift_chapter_ref(chapter_number)
