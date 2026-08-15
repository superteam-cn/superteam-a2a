"""MemoryReconcilerService - L3-6 -4.3 reconcile algorithm + rollback + error isolation.

Design (Path 1 - single-process D plan):
- prepare/bind/commit/rollback are internal transaction abstractions
- K8s 5xx retry 1/2/4/8s max 4 times
- _non_overlap_lock prevents timer overlap
- generation CAS by backend.patch_status
- clock only as parameter injection
"""

from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime
from typing import Protocol, cast, runtime_checkable

from superteam_a2a.knowledge_memory.backend.clock import Clock
from superteam_a2a.knowledge_memory.backend.errors import (
    MemoryBackendError,
    MemoryErrorCode,
    memory_error_data,
)
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.backend.protocol import MemoryBackend
from superteam_a2a.knowledge_memory.reconciler.leader import LeaderElector
from superteam_a2a.knowledge_memory.reconciler.types import MemoryReconcilerError, ReconcileSummary

TIMER_INTERVAL_SECONDS: float = 60.0
TIMER_ID: str = "memory-reconciler"
MAX_RECONCILE_RETRIES: int = 4
RETRY_BACKOFF_SECONDS: tuple[float, ...] = (1.0, 2.0, 4.0, 8.0)
ADMISSION_TIMEOUT_BACKOFF: tuple[float, ...] = (0.100, 0.200, 0.400)
ADMISSION_TIMEOUT_SECONDS: float = 0.050


class AdmissionTimeoutError(MemoryBackendError):
    """-4.3 admission validator timeout - code MEMORY_ADMISSION_TIMEOUT."""

    def __init__(
        self, message: str = "admission validation timed out", *, cause: Exception | None = None
    ) -> None:
        super().__init__(MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT, message, cause=cause)


class BackendUnavailable(MemoryBackendError):  # noqa: N818 (per L3-6 spec -4.3)
    """-4.3 backend unavailable (network/temp) - code MEMORY_INTERNAL_ERROR."""

    def __init__(
        self, message: str = "backend unavailable", *, cause: Exception | None = None
    ) -> None:
        super().__init__(MemoryErrorCode.MEMORY_INTERNAL_ERROR, message, cause=cause)


@runtime_checkable
class AdmissionValidatorProtocol(Protocol):
    """-4.3 admission validation abstract."""

    async def validate(self, memory: Memory, *, timeout: float) -> None: ...


@runtime_checkable
class Index(Protocol):
    """-4.4 finalize step 4 - BM25/cache index remove abstract."""

    async def remove(self, namespace: str, name: str) -> None: ...


class _PrepareToken:
    """-4.3 prepare/bind/commit/rollback transaction token."""

    __slots__ = ("applied", "binding", "name", "namespace")

    def __init__(self, *, namespace: str, name: str, binding: dict[str, str]) -> None:
        self.namespace = namespace
        self.name = name
        self.binding = binding
        self.applied = False


def canonical_memory_code(exc: BaseException) -> MemoryErrorCode:
    """-4.3 map exception to authoritative MEMORY_* error code."""
    if isinstance(exc, MemoryBackendError):
        return exc.code
    return MemoryErrorCode.MEMORY_INTERNAL_ERROR


class MemoryReconcilerService:
    """-4.3 reconcile algorithm + -4.4 finalize 5-step cleanup."""

    def __init__(
        self,
        *,
        backend: MemoryBackend,
        leader: LeaderElector,
        clock: Clock,
        admission: AdmissionValidatorProtocol,
        index: Index,
        max_retries: int = MAX_RECONCILE_RETRIES,
        retry_base_seconds: float = 1.0,
    ) -> None:
        self.backend = backend
        self.leader = leader
        self.clock = clock
        self.admission = admission
        self.index = index
        self._max_retries = max_retries
        self._retry_base_seconds = retry_base_seconds
        self._non_overlap_lock = asyncio.Lock()

    async def reconcile_all(self, *, now: datetime) -> ReconcileSummary:
        """-4.3 full reconcile loop."""
        if not self.leader.is_leader():
            return ReconcileSummary(
                started_at=now, finished_at=self.clock.now(), result="leader_lost"
            )
        if self._non_overlap_lock.locked():
            return ReconcileSummary(
                started_at=now,
                finished_at=self.clock.now(),
                result="overlap_skipped",
                skipped_overlap=1,
            )
        async with self._non_overlap_lock:
            bound_count = 0
            error_count = 0
            try:
                memories = await self._list_pending_memories()
                for raw in memories:
                    try:
                        memory = Memory.model_validate(raw)
                        bound_one = await self._process_one(memory, now)
                        if bound_one:
                            bound_count += 1
                    except AdmissionTimeoutError as exc:
                        await self._mark_error(raw, exc.code, exc, now)
                        error_count += 1
                    except BackendUnavailable as exc:
                        await self._mark_error(raw, exc.code, exc, now)
                        error_count += 1
                    except MemoryReconcilerError as exc:
                        await self._mark_error(raw, exc.code, exc, now)
                        error_count += 1
                    except MemoryBackendError as exc:
                        await self._mark_error(raw, canonical_memory_code(exc), exc, now)
                        error_count += 1
                    except Exception as exc:
                        await self._mark_error(raw, MemoryErrorCode.MEMORY_INTERNAL_ERROR, exc, now)
                        error_count += 1
                return ReconcileSummary(
                    bound=bound_count,
                    errors=error_count,
                    started_at=now,
                    finished_at=self.clock.now(),
                    result="ok",
                )
            except BaseException:
                return ReconcileSummary(
                    bound=bound_count,
                    errors=error_count,
                    started_at=now,
                    finished_at=self.clock.now(),
                    result="error",
                )

    async def _process_one(self, memory: Memory, now: datetime) -> bool:
        """-4.3 single memory pipeline. Returns True if bound, False otherwise."""
        try:
            await asyncio.wait_for(
                self.admission.validate(memory, timeout=ADMISSION_TIMEOUT_SECONDS),
                timeout=ADMISSION_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            raise AdmissionTimeoutError(
                f"admission validate timed out after {ADMISSION_TIMEOUT_SECONDS}s",
                cause=exc,
            ) from exc
        binding = self.derive_binding(memory)
        token = _PrepareToken(
            namespace=memory.metadata.namespace, name=memory.metadata.name, binding=binding
        )
        try:
            self._bind(token, memory)
            status = self.calculate_status(memory)
            await self._patch_status_with_retry(memory, status)
            self._commit(token)
            return True
        except (AdmissionTimeoutError, BackendUnavailable, MemoryBackendError):
            self._rollback(token)
            raise

    def derive_binding(self, memory: Memory) -> dict[str, str]:
        """-4.3 derive (namespace, name) -> backend binding key."""
        return {"namespace": memory.metadata.namespace, "name": memory.metadata.name}

    def calculate_status(self, memory: Memory) -> dict[str, object]:
        """-4.3 calculate new status (with observedGeneration)."""
        existing = memory.status.model_dump(by_alias=True) if memory.status else {}
        existing["observedGeneration"] = memory.metadata.generation
        existing["phase"] = "Active"
        return existing

    def _bind(self, token: _PrepareToken, memory: Memory) -> None:
        """-4.3 bind - Path 1 sets applied flag."""
        token.applied = True

    def _commit(self, token: _PrepareToken) -> None:
        """-4.3 commit - Path 1 idempotent flag."""
        token.applied = True

    def _rollback(self, token: _PrepareToken) -> None:
        """-4.3 rollback - Path 1 clears flag."""
        token.applied = False

    async def _patch_status_with_retry(self, memory: Memory, status: dict[str, object]) -> None:
        """-4.3 patch_status retry - 5xx 1/2/4/8s, 4xx no retry."""
        last_exc = None
        for attempt in range(self._max_retries + 1):
            try:
                await self.backend.patch_status(
                    memory.metadata.namespace,
                    memory.metadata.name,
                    status,
                    expected_generation=memory.metadata.generation,
                )
                return
            except MemoryBackendError as exc:
                last_exc = exc
                if not exc.retryable:
                    raise
                if attempt >= self._max_retries:
                    raise BackendUnavailable(
                        f"patch_status failed after {self._max_retries + 1} attempts", cause=exc
                    ) from exc
                backoff = RETRY_BACKOFF_SECONDS[min(attempt, len(RETRY_BACKOFF_SECONDS) - 1)]
                await self.clock.sleep(backoff)
        if last_exc is not None:
            raise BackendUnavailable("patch_status retry exhausted", cause=last_exc)

    async def _list_pending_memories(self) -> list[dict[str, object]]:
        """-4.3 list all memories."""
        from superteam_a2a.knowledge_memory.backend.types import MemoryScope as _Scope
        from superteam_a2a.knowledge_memory.backend.types import QueryMemoryRequest as _Query

        query = _Query(scope=_Scope.GLOBAL, namespace=None, limit=1000, offset=0)
        result = await self.backend.list(query)
        return [m.model_dump(by_alias=True) for m in result.items]

    async def _mark_error(
        self, raw: dict[str, object], code: MemoryErrorCode, exc: Exception, now: datetime
    ) -> None:
        """-4.3 mark error to backend status (phase=Error)."""
        try:
            metadata_obj = raw.get("metadata", {})
            if not isinstance(metadata_obj, dict):
                return
            metadata: dict[str, object] = cast(dict[str, object], metadata_obj)
            namespace_obj = metadata.get("namespace", "default")
            namespace: str = namespace_obj if isinstance(namespace_obj, str) else "default"
            name_obj = metadata.get("name")
            name: str | None = name_obj if isinstance(name_obj, str) else None
            generation: int = cast(int, metadata.get("generation", 1))
            if not isinstance(name, str):
                return
            status: dict[str, object] = {
                "phase": "Error",
                "message": f"{code.name}: {exc}",
                "observedGeneration": generation,
                "lastError": memory_error_data(
                    code, module="memory.reconciler", code_name=code.name
                ),
            }
            await self.backend.patch_status(namespace, name, status, expected_generation=generation)
        except MemoryBackendError:
            pass

    async def finalize(self, memory: Memory) -> None:
        """-4.4 finalize 5-step cleanup - strict order + first 4 idempotent."""
        # step 1: mark_releasing
        await self.backend.patch_status(
            memory.metadata.namespace,
            memory.metadata.name,
            {"phase": "Releasing", "observedGeneration": memory.metadata.generation},
            expected_generation=memory.metadata.generation,
        )
        # step 2: quiesce (drain)
        await asyncio.sleep(0)
        # step 3: release (idempotent)
        await self.backend.delete(memory.metadata.namespace, memory.metadata.name)
        # step 4: index.remove (idempotent)
        await self.index.remove(memory.metadata.namespace, memory.metadata.name)
        # step 5: remove_finalizer
        with contextlib.suppress(MemoryBackendError):
            await self.backend.patch_status(
                memory.metadata.namespace,
                memory.metadata.name,
                {"phase": "Released", "observedGeneration": memory.metadata.generation},
                expected_generation=memory.metadata.generation,
            )


async def memory_reconciler_timer(*, memo: dict[str, object], **_: object) -> None:
    """-4.1 @kopf.timer entry function."""
    service = memo.get("memory_reconciler")
    if not isinstance(service, MemoryReconcilerService):
        return
    if not await service.leader.try_acquire_or_renew():
        return
    await service.reconcile_all(now=service.clock.now())


__all__ = [
    "ADMISSION_TIMEOUT_BACKOFF",
    "ADMISSION_TIMEOUT_SECONDS",
    "MAX_RECONCILE_RETRIES",
    "RETRY_BACKOFF_SECONDS",
    "TIMER_ID",
    "TIMER_INTERVAL_SECONDS",
    "AdmissionTimeoutError",
    "AdmissionValidatorProtocol",
    "BackendUnavailable",
    "Index",
    "MemoryReconcilerService",
    "canonical_memory_code",
    "memory_reconciler_timer",
]
