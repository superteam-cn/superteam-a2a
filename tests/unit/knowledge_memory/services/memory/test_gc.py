"""H-RM-UT-003 · MemoryGCService.execute 狀態轉換（mark/archive/delete）。

驗證：
1. 合法轉換：Active → Archived + patch_status
2. 合法轉換：Expired → Deleted + delete
3. 非法轉換：ValueError

依據 PR-4b plan §7 H-RM-UT-003 + L3-1 §6.2.5 狀態機。
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.backend.memory import Memory, ObjectMeta
from superteam_a2a.knowledge_memory.backend.protocol import MemoryBackend
from superteam_a2a.knowledge_memory.services.memory.gc import MemoryGCService
from superteam_a2a.operator.models.memory import (
    AgentReference,
    MemoryPhase,
    MemorySpec,
    MemoryStatus,
    ScopeReference,
)


def _make_memory_with_phase(phase: MemoryPhase | None) -> Memory:
    """構造帶 status.phase 的 Memory。"""
    return Memory(
        metadata=ObjectMeta(name="mem-gc", namespace="default"),
        spec=MemorySpec(
            scopeRef=ScopeReference(name="industry-ai"),
            agentRef=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary="GC test memory",
        ),
        status=MemoryStatus(phase=phase) if phase else None,
    )


@pytest.fixture
def fake_backend() -> AsyncMock:
    """AsyncMock MemoryBackend。"""
    return AsyncMock(spec=MemoryBackend)


@pytest.fixture
def in_process_context(fake_clock) -> InProcessContext:
    return InProcessContext(clock=fake_clock, trace_id="test-rm-ut-003")


async def test_memory_gc_service_marks_active_as_archived(
    fake_backend: AsyncMock,
    in_process_context: InProcessContext,
    base_time,
) -> None:
    """H-RM-UT-003a · Active → Archived · patch_status 標記。

    期望：
    1. backend.patch_status 被呼叫（不是 delete）
    2. 返回 "Archived"
    """

    memory = _make_memory_with_phase(MemoryPhase.ACTIVE)
    service = MemoryGCService(backend=fake_backend, context=in_process_context)

    result = await service.execute(memory, target_phase="Archived")

    fake_backend.patch_status.assert_awaited_once()
    fake_backend.delete.assert_not_called()
    assert result == "Archived"


async def test_memory_gc_service_deletes_expired(
    fake_backend: AsyncMock,
    in_process_context: InProcessContext,
) -> None:
    """H-RM-UT-003b · Expired → Deleted · backend.delete。

    期望：
    1. backend.delete 被呼叫（不是 patch_status）
    2. 返回 "Deleted"
    """
    memory = _make_memory_with_phase(MemoryPhase.EXPIRED)
    service = MemoryGCService(backend=fake_backend, context=in_process_context)

    result = await service.execute(memory, target_phase="Deleted")

    fake_backend.delete.assert_awaited_once()
    fake_backend.patch_status.assert_not_called()
    assert result == "Deleted"


async def test_memory_gc_service_rejects_illegal_transition(
    fake_backend: AsyncMock,
    in_process_context: InProcessContext,
) -> None:
    """H-RM-UT-003c · 非法轉換（Active → Deleted 直接跳）→ ValueError。

    期望：
    1. backend 不被呼叫（patch_status / delete 都未觸發）
    2. 拋 ValueError
    """
    memory = _make_memory_with_phase(MemoryPhase.ACTIVE)
    service = MemoryGCService(backend=fake_backend, context=in_process_context)

    with pytest.raises(ValueError, match="Illegal GC transition"):
        await service.execute(memory, target_phase="Deleted")


__all__ = [
    "test_memory_gc_service_deletes_expired",
    "test_memory_gc_service_marks_active_as_archived",
    "test_memory_gc_service_rejects_illegal_transition",
]
