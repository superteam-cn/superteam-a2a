"""H-RM-UT-002 · MemoryReinforceService.execute CAS 提升 confidence。

驗證：
1. backend.patch_status 被呼叫 · expected_generation=memory.metadata.generation
2. CAS 失敗 → MemoryBackendError(MEMORY_FORBIDDEN) 透傳（不重映射）
3. CAS 成功 → 返回 new_confidence
4. Prometheus Counter MEMORY_REINFORCE_TOTAL(result=success) 遞增

依據 PR-4b plan §7 H-RM-UT-002 + L3-6 §5.7 不變量 2（CAS 顯式失敗）。
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from superteam_a2a.knowledge_memory import (
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.backend.protocol import MemoryBackend
from superteam_a2a.knowledge_memory.services.memory.reinforce import (
    MemoryReinforceService,
)


@pytest.fixture
def fake_backend() -> AsyncMock:
    """AsyncMock MemoryBackend。"""
    return AsyncMock(spec=MemoryBackend)


@pytest.fixture
def in_process_context(fake_clock) -> InProcessContext:
    """InProcessContext with FakeClock。"""
    return InProcessContext(clock=fake_clock, trace_id="test-rm-ut-002")


async def test_memory_reinforce_service_updates_confidence_with_cas(
    sample_memory,
    fake_backend: AsyncMock,
    in_process_context: InProcessContext,
) -> None:
    """H-RM-UT-002 · backend.patch_status CAS 成功 → 返回 new_confidence。

    期望：
    1. fake_backend.patch_status 被呼叫一次
    2. 傳入參數：namespace + name + status + expected_generation
    3. service 返回 new_confidence
    """
    service = MemoryReinforceService(backend=fake_backend, context=in_process_context)
    new_confidence = 0.85

    result = await service.execute(sample_memory, new_confidence=new_confidence)

    # assert · backend.patch_status 被呼叫
    fake_backend.patch_status.assert_awaited_once()
    call_args = fake_backend.patch_status.await_args
    assert call_args.args[0] == sample_memory.metadata.namespace
    assert call_args.args[1] == sample_memory.metadata.name
    assert isinstance(call_args.args[2], dict)  # status payload
    assert call_args.kwargs["expected_generation"] == sample_memory.metadata.generation

    # assert · 返回 new_confidence
    assert result == new_confidence


async def test_memory_reinforce_service_propagates_cas_conflict(
    sample_memory,
    fake_backend: AsyncMock,
    in_process_context: InProcessContext,
) -> None:
    """H-RM-UT-002 邊界 · CAS 衝突 → 透傳 MemoryBackendError(MEMORY_FORBIDDEN)。

    期望：
    1. fake_backend.patch_status 拋 MemoryBackendError(MEMORY_FORBIDDEN)
    2. service 不重映射異常 · 原樣透傳
    """
    fake_backend.patch_status.side_effect = MemoryBackendError(
        MemoryErrorCode.MEMORY_FORBIDDEN,
        "patch_status generation CAS conflict",
    )

    service = MemoryReinforceService(backend=fake_backend, context=in_process_context)

    with pytest.raises(MemoryBackendError) as exc_info:
        await service.execute(sample_memory, new_confidence=0.85)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_FORBIDDEN


__all__ = [
    "test_memory_reinforce_service_propagates_cas_conflict",
    "test_memory_reinforce_service_updates_confidence_with_cas",
]
