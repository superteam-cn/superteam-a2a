"""H-QM-IT-001 · queryMemory handler 端到端 IT 測試。

PR-4b plan §7 IT 增量：H-QM-IT-001 · queryMemory 端到端（JSON-RPC round-trip + MEMORY_QUERY_TOO_BROAD 觸發）。

驗證：
1. JSON-RPC request["params"]["query"] dict → QueryMemoryRequest 解析
2. MemoryQueryService.execute 被呼叫
3. service 拋 MemoryBackendError(MEMORY_QUERY_TOO_BROAD) → handler 映射到 JSON-RPC error.code -32106
4. response error dict 含 code + message + data.module + data.code_name
5. 成功路徑 → result.items + total_count 序列化
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

from superteam_a2a.knowledge_memory.api.results import QueryMemoryResult  # noqa: E402
from superteam_a2a.knowledge_memory.backend.errors import (  # noqa: E402
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.handlers.query_memory import (  # noqa: E402
    query_memory_handler,
)
from superteam_a2a.knowledge_memory.services.memory.query import (  # noqa: E402
    MemoryQueryService,
)


# H-QM-IT-001
async def test_query_memory_round_trip_with_industry_broad_rejection(
    sample_request_query_broad,
    in_process_context,
):
    """H-QM-IT-001 · queryMemory 端到端 · MEMORY_QUERY_TOO_BROAD 觸發。

    驗證：
    1. industry scope 無 tags/confidence → service 拋 MEMORY_QUERY_TOO_BROAD
    2. handler 捕獲異常 → JSON-RPC error.code = -32106
    3. error dict 含 code + message + data.module + data.code_name
    """
    # arrange
    query_service = AsyncMock(spec=MemoryQueryService)
    query_service.execute.side_effect = MemoryBackendError(
        MemoryErrorCode.MEMORY_QUERY_TOO_BROAD,
        "Memory query with scope=industry requires tag/confidence filter",
    )

    # act
    response = await query_memory_handler(
        sample_request_query_broad,
        context=in_process_context,
        query_service=query_service,
    )

    # assert · service.execute 被呼叫
    query_service.execute.assert_awaited_once()

    # assert · response 是 error dict
    assert "error" in response
    assert response["error"]["code"] == -32106
    assert response["error"]["message"]
    assert response["error"]["data"]["module"] == "memory"
    assert response["error"]["data"]["code_name"] == "MEMORY_QUERY_TOO_BROAD"


# H-QM-IT-001a · 成功路徑
async def test_query_memory_success_returns_items_and_total_count(
    sample_request_query,
    sample_memory,
    in_process_context,
):
    """H-QM-IT-001a · queryMemory 成功路徑 · 返回 items + total_count。

    驗證：
    1. service 返回 QueryMemoryResult(items=tuple, total_count=N)
    2. response 包含 items（list 序列化）+ total_count
    """
    # arrange
    expected_result = QueryMemoryResult(
        items=(sample_memory,),
        total_count=1,
    )
    query_service = AsyncMock(spec=MemoryQueryService)
    query_service.execute.return_value = expected_result

    # act
    response = await query_memory_handler(
        sample_request_query,
        context=in_process_context,
        query_service=query_service,
    )

    # assert · 成功路徑返回 result dict
    assert "items" in response
    assert response["total_count"] == 1
    assert len(response["items"]) == 1


__all__ = [
    "test_query_memory_round_trip_with_industry_broad_rejection",
    "test_query_memory_success_returns_items_and_total_count",
]
