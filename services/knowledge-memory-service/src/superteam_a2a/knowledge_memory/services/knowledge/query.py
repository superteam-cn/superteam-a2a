"""KnowledgeQueryService · Protocol stub · BM25 倒排索引實裝推 PR-4c。

PR-4b plan §1 明確剔除 BM25 業務邏輯；本 service 僅提供 Protocol 定義 +
空實裝 stub（返回空列表），用於 PR-4c ASGI server 接入接口。

ISP：Protocol 僅暴露 execute 方法（輸入 dict · 輸出 list[KnowledgeItem]）。
PR-4c 實裝 BM25 倒排索引 + tokenization + TF-IDF 評分時替換 stub 即可。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class KnowledgeQueryServiceProtocol(Protocol):
    """Knowledge query 路徑 Protocol · ISP 最小接口。

    方法：
    - execute(query_dict, context) -> list[KnowledgeItem]
    """

    async def execute(
        self,
        query_dict: dict[str, Any],
    ) -> list[Any]:  # list[KnowledgeItem] · PR-4c 替換類型
        ...


class KnowledgeQueryService:
    """KnowledgeQueryService stub · PR-4b 階段實裝。

    行為：
    - execute 接收 query_dict（JSON-RPC 請求體）
    - 返回空列表（BM25 倒排索引實裝推 PR-4c）
    - 不拋 NotImplementedError（保持 service 接口可用 · PR-4c 替換實裝）

    PR-4c 實裝要點（依據 L3-5 §6 業務邏輯）：
    1. tokenization（BM25Tokenizer）
    2. 倒排索引構建（基於 scope_ref / agent_ref / tags）
    3. TF-IDF 評分（bm25 公式）
    4. scope/visibility 過濾
    """

    async def execute(
        self,
        query_dict: dict[str, Any],
    ) -> list[Any]:
        """查詢 KnowledgeItem · PR-4b stub 返回空列表。

        參數：
        - query_dict · JSON-RPC 請求體（含 query_text / scope_ref / visibility / tags）

        返回：
        - list[Any] · 空列表（PR-4b stub · PR-4c 實裝 BM25）

        不變量：
        - 不拋 NotImplementedError（service 層接口可用）
        - 返回值類型是 list[Any]（PR-4c 改為 list[KnowledgeItem]）
        """
        # PR-4b stub · 不實裝 BM25 · 等待 PR-4c 替換
        return []


__all__ = [
    "KnowledgeQueryService",
    "KnowledgeQueryServiceProtocol",
]
