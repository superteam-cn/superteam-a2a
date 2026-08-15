"""L3-6 §6.1 MemoryBackendInProcessService · Protocol + 实现。

5 步 admitted_record_memory 契约（§6.4 line 998-1006）：
1. freeze input — memory.model_copy(deep=True)
2. 50ms validation — context.clock.monotonic() + 0.050 + asyncio.wait_for
3. admission validate — 通过可选注入的 validator fail-closed 校验
4. single handoff — 仅一次 backend.put + idempotency_key 防重
5. propagate/commit — 直接返回或抛权威异常；禁止 fail-open

实现层承担完整 step 1~5；admission 默认 None 以保持 PR #19 向后兼容。
"""

from __future__ import annotations

import asyncio
from typing import Protocol, runtime_checkable

from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.api.results import (
    MemoryRecordResult,
    QueryMemoryResult,
)
from superteam_a2a.knowledge_memory.backend.errors import (
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.backend.types import (
    MemoryScope,
    QueryMemoryRequest,
)

# §6.4 step 2 50ms admission deadline fail-closed
ADMISSION_TIMEOUT_SECONDS: float = 0.050


@runtime_checkable
class MemoryBackendInProcessService(Protocol):
    """L3-6 §6.1 in-process service Protocol。

    D 方案单进程：直接函数调用；<1μs；无 IPC 边界。
    """

    async def record_memory_async(
        self,
        memory: Memory,
        *,
        context: InProcessContext,
    ) -> MemoryRecordResult: ...

    async def query_memory_async(
        self,
        request: QueryMemoryRequest,
        *,
        context: InProcessContext,
    ) -> QueryMemoryResult: ...


class MemoryBackendInProcessServiceImpl:
    """委托底层 MemoryBackend Protocol + 5 步契约。

    本实现聚焦：
    - step 1 freeze input（deep copy）
    - step 2 50ms admission deadline（fail-closed → MEMORY_ADMISSION_TIMEOUT）
    - step 3 admission validate（可选注入；默认 None 跳过）
    - step 4 single handoff（idempotency_key = "{namespace}/{name}"）
    - step 5 propagate / commit（异常原样透传；禁止 fail-open）
    """

    def __init__(self, backend, *, admission=None) -> None:
        self._backend = backend
        self._admission = admission

    async def record_memory_async(
        self,
        memory: Memory,
        *,
        context: InProcessContext,
    ) -> MemoryRecordResult:
        """§6.1 record 路径 · 5 步契约。

        step 3 admission validate 通过 self._admission 注入（默认 None 跳过；
        典型实现见 handlers/admission_validator.py）。
        """
        # Step 1: freeze input
        frozen = memory.model_copy(deep=True)
        # Step 2: 50ms admission deadline（fail-closed）
        deadline = context.clock.monotonic() + ADMISSION_TIMEOUT_SECONDS
        # Step 3: admission validate（可选；None 时跳过；异常原样透传）
        if self._admission is not None:
            await self._admission.validate(frozen, timeout=ADMISSION_TIMEOUT_SECONDS)
        remaining = max(0.0, deadline - context.clock.monotonic())
        coro = self._backend.put(
            frozen,
            idempotency_key=f"{frozen.metadata.namespace}/{frozen.metadata.name}",
        )
        try:
            put_result = await asyncio.wait_for(coro, timeout=remaining)
        except TimeoutError as exc:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT,
                "Memory admission exceeded 50ms",
                cause=exc,
            ) from exc
        except MemoryBackendError:
            # §6.4 step 5 异常透传；禁止重映射 / fail-open
            raise
        # Step 5: propagate / commit
        return MemoryRecordResult(
            memory=frozen,
            phase=frozen.status.phase.value if frozen.status and frozen.status.phase else "Pending",
            effective_confidence=frozen.spec.confidence,
            resource_version=put_result.version,
        )

    async def query_memory_async(
        self,
        request: QueryMemoryRequest,
        *,
        context: InProcessContext,
    ) -> QueryMemoryResult:
        """§6.1 query 路径 · industry scope 预检 + 后置 confidence 过滤。

        §6.4 step 5：industry 无 tag/confidence 立即透传 MEMORY_QUERY_TOO_BROAD，
        且不进入 backend scan（TEST-MEM-060）。
        """
        if (
            request.scope == MemoryScope.INDUSTRY
            and not request.tags
            and request.min_confidence is None
        ):
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_QUERY_TOO_BROAD,
                "Memory query with scope=industry requires tag/confidence filter",
            )
        try:
            list_result = await self._backend.list(request)
        except MemoryBackendError:
            # §6.1 显式失败：原样透传，不重映射
            raise
        # 后置过滤：min_confidence
        threshold = request.min_confidence if request.min_confidence is not None else 0.0
        filtered = tuple(m for m in list_result.items if m.spec.confidence >= threshold)
        return QueryMemoryResult(items=filtered, total_count=len(filtered))


__all__ = [
    "ADMISSION_TIMEOUT_SECONDS",
    "MemoryBackendInProcessService",
    "MemoryBackendInProcessServiceImpl",
]
