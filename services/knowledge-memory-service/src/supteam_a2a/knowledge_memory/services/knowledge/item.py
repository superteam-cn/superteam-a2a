"""KnowledgeItemService · Protocol stub · superseded_by chain 實裝推 PR-4c。

依據 L3-5 §6 KnowledgeItem 業務邏輯：
- get_item · 單個 KnowledgeItem 查詢（含 superseded_by chain 遍歷）
- chain 推 PR-4c（需 BM25 索引 + scope 解析 + version 對齊）

ISP：Protocol 僅暴露 get_item 方法。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class KnowledgeItemServiceProtocol(Protocol):
    """KnowledgeItem get 路徑 Protocol · ISP 最小接口。"""

    async def get_item(
        self,
        item_ref: Any,
    ) -> Any:  # KnowledgeItem | None
        ...


class KnowledgeItemService:
    """KnowledgeItemService stub · PR-4b 階段實裝。

    行為：
    - get_item 接收 item_ref（KnowledgeItem 引用）
    - 返回 None（PR-4c 實裝時通過 BM25 索引 + scope 解析獲取）

    PR-4c 實裝要點：
    1. 通過 item_ref 從 BM25 索引獲取 KnowledgeItem
    2. 遍歷 superseded_by chain（直到 chain 末端）
    3. 返回當前最新版 KnowledgeItem
    """

    async def get_item(
        self,
        item_ref: Any,
    ) -> Any:
        """獲取 KnowledgeItem · PR-4b stub 返回 None。

        參數：
        - item_ref · KnowledgeItem 引用（含 name / namespace / version）

        返回：
        - Any · None（PR-4b stub · PR-4c 實裝返回 KnowledgeItem）

        不變量：
        - 不拋 NotImplementedError（service 層接口可用）
        """
        # PR-4b stub · superseded_by chain 推 PR-4c
        return None


__all__ = [
    "KnowledgeItemService",
    "KnowledgeItemServiceProtocol",
]
