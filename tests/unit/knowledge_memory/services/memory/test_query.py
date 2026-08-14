"""H-QM-UT-001~003 · MemoryQueryService 測試組（3 ID）。

驗證：
1. H-QM-UT-001 · service.execute 委託 InProcessService.query_memory_async
2. H-QM-UT-002 · scope=industry + 無 tag/confidence 透傳 MEMORY_QUERY_TOO_BROAD
3. H-QM-UT-003 · QueryMemoryResult frozen（model_config frozen=True）

依據 PR-4b plan §7 H-QM-UT + L3-6 §6.4 step 5 異常透傳規則。
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from superteam_a2a.knowledge_memory import (
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.api.results import QueryMemoryResult
from superteam_a2a.knowledge_memory.api.service import (
    MemoryBackendInProcessService,
)
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.backend.types import (
    MemoryScope,
    QueryMemoryRequest,
)
from superteam_a2a.knowledge_memory.services.memory.query import (
    MemoryQueryService,
)

# ============================================================================
# H-QM-UT-001 · service.execute 委託 InProcessService.query_memory_async
# ============================================================================


@pytest.fixture
def fake_in_process_service_query() -> AsyncMock:
    """AsyncMock MemoryBackendInProcessService（query 測試用）。"""
    return AsyncMock(spec=MemoryBackendInProcessService)


@pytest.fixture
def memory_query_service(fake_in_process_service_query, fake_clock) -> MemoryQueryService:
    """MemoryQueryService 構造。"""
    return MemoryQueryService(
        in_process_service=fake_in_process_service_query,
        clock=fake_clock,
        trace_id="test-qm-ut-001",
    )


async def test_memory_query_service_executes_scope_filter(
    memory_query_service: MemoryQueryService,
    fake_in_process_service_query: AsyncMock,
    sample_memory: Memory,
) -> None:
    """H-QM-UT-001 · service.execute 委託 InProcessService.query_memory_async。

    期望：
    1. fake_in_process_service.query_memory_async 被呼叫一次
    2. 傳入參數：request + context
    3. 返回值原樣從 service 返回
    """
    expected_result = QueryMemoryResult(items=(sample_memory,), total_count=1)
    fake_in_process_service_query.query_memory_async.return_value = expected_result

    request = QueryMemoryRequest(scope=MemoryScope.AGENT)
    result = await memory_query_service.execute(request)

    fake_in_process_service_query.query_memory_async.assert_awaited_once()
    call = fake_in_process_service_query.query_memory_async.await_args
    # request is positional, context is keyword
    assert call.args[0] == request
    assert call.kwargs["context"].clock is memory_query_service._clock

    assert result is expected_result


# ============================================================================
# H-QM-UT-002 · scope=industry + 無 tag/confidence 透傳 MEMORY_QUERY_TOO_BROAD
# ============================================================================


async def test_memory_query_service_passes_through_industry_filter(
    fake_in_process_service_query: AsyncMock,
    fake_clock,
) -> None:
    """H-QM-UT-002 · InProcessService 拋 MEMORY_QUERY_TOO_BROAD · service 透傳。

    期望：
    1. fake InProcessService.query_memory_async 拋 MemoryBackendError(MEMORY_QUERY_TOO_BROAD)
    2. service 不重映射異常 · 原樣透傳給 caller
    """
    fake_in_process_service_query.query_memory_async.side_effect = MemoryBackendError(
        MemoryErrorCode.MEMORY_QUERY_TOO_BROAD,
        "Memory query with scope=industry requires tag/confidence filter",
    )

    service = MemoryQueryService(
        in_process_service=fake_in_process_service_query,
        clock=fake_clock,
    )

    request = QueryMemoryRequest(scope=MemoryScope.INDUSTRY)
    with pytest.raises(MemoryBackendError) as exc_info:
        await service.execute(request)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_QUERY_TOO_BROAD


# ============================================================================
# H-QM-UT-003 · QueryMemoryResult frozen
# ============================================================================


def test_memory_query_service_returns_frozen_result(
    sample_memory: Memory,
    fake_clock,
) -> None:
    """H-QM-UT-003 · QueryMemoryResult frozen（model_config frozen=True）。

    期望：
    1. 構造 QueryMemoryResult(items=(memory,), total_count=1)
    2. 嘗試修改 result.items → ValidationError（frozen 保護）
    """
    result = QueryMemoryResult(items=(sample_memory,), total_count=1)

    # frozen 校驗
    with pytest.raises(ValidationError):
        result.items = ()  # type: ignore[misc]


__all__ = [
    "test_memory_query_service_executes_scope_filter",
    "test_memory_query_service_passes_through_industry_filter",
    "test_memory_query_service_returns_frozen_result",
]
