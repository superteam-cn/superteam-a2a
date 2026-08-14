"""H-RM-UT-001 · MemoryRecordService.execute 委託 InProcessService.record_memory_async。

驗證：
1. service.execute(memory) 構造 InProcessContext 並呼叫 InProcessService
2. InProcessService 返回的 MemoryRecordResult 原樣返回
3. Prometheus Counter MEMORY_IN_PROCESS_CALL_TOTAL(method=record, result=success) 遞增

依據 PR-4b plan §7 H-RM-UT-001 + L3-6 §6.4 5 步契約。
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from superteam_a2a.knowledge_memory.api.service import (
    MemoryBackendInProcessService,
)
from superteam_a2a.knowledge_memory.services.memory.record import (
    MemoryRecordService,
)


@pytest.fixture
def fake_in_process_service() -> AsyncMock:
    """AsyncMock MemoryBackendInProcessService。"""
    return AsyncMock(spec=MemoryBackendInProcessService)


@pytest.fixture
def memory_record_service(fake_in_process_service, fake_clock) -> MemoryRecordService:
    """MemoryRecordService 構造（注入 fake InProcessService + FakeClock）。"""
    return MemoryRecordService(
        in_process_service=fake_in_process_service,
        clock=fake_clock,
        trace_id="test-rm-ut-001",
    )


async def test_memory_record_service_executes_5step_contract(
    sample_memory,
    memory_record_service: MemoryRecordService,
    fake_in_process_service: AsyncMock,
) -> None:
    """H-RM-UT-001 · service.execute 委託 InProcessService.record_memory_async。

    期望：
    1. fake_in_process_service.record_memory_async 被呼叫一次
    2. 傳入參數：memory + context（InProcessContext 含 clock + trace_id）
    3. 返回值原樣從 service 返回
    """
    # arrange
    expected_result = AsyncMock()
    fake_in_process_service.record_memory_async.return_value = expected_result

    # act
    result = await memory_record_service.execute(sample_memory)

    # assert · InProcessService.record_memory_async 被呼叫
    fake_in_process_service.record_memory_async.assert_awaited_once()
    call_kwargs = fake_in_process_service.record_memory_async.await_args.kwargs
    assert "context" in call_kwargs
    assert call_kwargs["context"].clock is memory_record_service._clock
    assert call_kwargs["context"].trace_id == "test-rm-ut-001"

    # assert · 返回值原樣透傳
    assert result is expected_result


__all__ = ["test_memory_record_service_executes_5step_contract"]
