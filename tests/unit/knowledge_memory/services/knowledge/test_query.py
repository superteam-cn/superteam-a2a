"""H-QK-UT-001 · KnowledgeQueryService stub 返回空列表。

驗證：
1. KnowledgeQueryService().execute(query_dict) 返回 list
2. 返回空列表（BM25 倒排索引實裝推 PR-4c）
3. 不拋 NotImplementedError（service.execute 接口可用）

依據 PR-4b plan §7 H-QK-UT-001 + PR-4b §1 明確剔除 BM25 業務邏輯。
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.services.knowledge.query import (
    KnowledgeQueryService,
    KnowledgeQueryServiceProtocol,
)


async def test_knowledge_query_service_stub_returns_empty() -> None:
    """H-QK-UT-001 · KnowledgeQueryService.execute 返回空列表。

    期望：
    1. 構造 KnowledgeQueryService
    2. execute({"query_text": "test"}) 返回 list
    3. 返回空列表 · 不拋 NotImplementedError
    """
    service = KnowledgeQueryService()
    result = await service.execute({"query_text": "test"})

    assert isinstance(result, list)
    assert result == []


async def test_knowledge_query_service_protocol_runtime_checkable() -> None:
    """H-GKI-UT 補充 · KnowledgeQueryServiceProtocol 允許 isinstance 檢查。

    期望：
    1. KnowledgeQueryService 實例通過 isinstance(..., KnowledgeQueryServiceProtocol)
    """
    service = KnowledgeQueryService()
    assert isinstance(service, KnowledgeQueryServiceProtocol)


__all__ = [
    "test_knowledge_query_service_protocol_runtime_checkable",
    "test_knowledge_query_service_stub_returns_empty",
]
