"""H-QK-IT-001 · queryKnowledge handler 端到端 IT 測試。

PR-4b plan §7 IT 增量：H-QK-IT-001 · queryKnowledge 端到端（JSON-RPC round-trip + BM25 stub 空列表）。

驗證：
1. JSON-RPC request["params"]["query"] dict 提取
2. KnowledgeQueryService.execute stub 返回空列表
3. handler 序列化 → result.items = [] + total_count = 0
4. 不拋 NotImplementedError（保持 service 接口可用 · PR-4c 替換實裝）
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock

# 路径前置
_REPO_ROOT = Path(__file__).resolve().parents[5]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

from superteam_a2a.knowledge_memory.handlers.query_knowledge import (  # noqa: E402
    query_knowledge_handler,
)
from superteam_a2a.knowledge_memory.services.knowledge.query import (  # noqa: E402
    KnowledgeQueryService,
)


# H-QK-IT-001
async def test_query_knowledge_round_trip_with_bm25_stub_empty(
    sample_request_query_knowledge,
    in_process_context,
):
    """H-QK-IT-001 · queryKnowledge 端到端 · BM25 stub 空列表。

    驗證：
    1. request["params"]["query"] dict 提取成功
    2. KnowledgeQueryService.execute stub 返回 []（PR-4b stub 行為）
    3. handler 序列化 → {"items": [], "total_count": 0}
    4. 不拋 NotImplementedError（保持 service 接口可用）
    """
    # arrange · KnowledgeQueryService stub 返回空列表
    knowledge_service = AsyncMock(spec=KnowledgeQueryService)
    knowledge_service.execute.return_value = []

    # act
    response = await query_knowledge_handler(
        sample_request_query_knowledge,
        context=in_process_context,
        knowledge_service=knowledge_service,
    )

    # assert · service.execute 被呼叫一次
    knowledge_service.execute.assert_awaited_once()

    # assert · response 是 result dict（非 error）
    assert "items" in response
    assert "total_count" in response
    assert response["items"] == []
    assert response["total_count"] == 0
    assert "error" not in response


__all__ = [
    "test_query_knowledge_round_trip_with_bm25_stub_empty",
]
