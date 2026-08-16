"""InMemoryBackend · L3-6 §5.7 dict-backed 默认实现 + D 方案单进程 Card-driven 单实例。

依据 ADR-0006 D 方案 + L1 v0.2.0 §4.1 C-7：single Python process ·
services/knowledge-memory-service 单 Deployment。

特性：
- dict[str, StoredMemory] 存储
- 异步 wrapper（asyncio.Lock 保证 PUT/DELETE 原子）
- 委托 pure.py 计算
- patch_status CAS（generation 冲突抛 MEMORY_INTERNAL_ERROR retryable）
"""

from __future__ import annotations

import asyncio

from superteam_a2a.knowledge_memory.backend import pure
from superteam_a2a.knowledge_memory.backend.clock import Clock, SystemClock
from superteam_a2a.knowledge_memory.backend.errors import (
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.backend.types import (
    BackendHealth,
    BackendMetadata,
    BackendType,
    DeleteResult,
    ListResult,
    PutResult,
    QueryMemoryRequest,
    StoredMemory,
)

# ============================================================================
# InMemoryBackend · 默认 backend（dict-backed）
# ============================================================================


class InMemoryBackend:
    """§5.7 dict-backed 默认 backend · Card-driven 单实例。

    与 ADR-0006 D 方案一致：单进程 · asyncio.Lock 保证 PUT/DELETE 原子。
    """

    DEFAULT_MAX_SIZE = 65_536  # §3 BackendBindingSpec in-memory size 上限

    def __init__(
        self,
        *,
        clock: Clock | None = None,
        max_size: int = DEFAULT_MAX_SIZE,
        default_ttl_seconds: int | None = None,
    ) -> None:
        self._clock = clock or SystemClock()
        self._max_size = max_size
        self._default_ttl_seconds = default_ttl_seconds
        self._state: dict[tuple[str, str], StoredMemory] = {}
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # §5.7 MemoryBackend Protocol 实现
    # ------------------------------------------------------------------

    async def put(
        self,
        memory: Memory,
        *,
        idempotency_key: str | None = None,
    ) -> PutResult:
        """§5.3 PUT async wrapper。"""
        async with self._lock:
            key = (memory.metadata.namespace, memory.metadata.name)
            result = pure.put(
                state=self._state,
                memory=memory,
                clock=self._clock,
                max_size=self._max_size,
                ttl_seconds=self._default_ttl_seconds,
            )
            # 写入 state
            existing = self._state.get(key)
            self._state[key] = StoredMemory(
                memory=memory.model_copy(deep=True),
                created_at=existing.created_at if existing else result.stored_at,
                updated_at=result.stored_at,
                version=result.version,
                expires_at=result.expires_at,
                idempotency_key=idempotency_key,
            )
            return result

    async def get(self, namespace: str, name: str) -> Memory | None:
        """§5.4 GET async wrapper。"""
        result = pure.get(
            state=self._state,
            namespace=namespace,
            name=name,
            clock=self._clock,
        )
        if not result.found or result.memory is None:
            return None
        # 重建完整 Memory（spec → Memory 顶层）
        record = self._state[(namespace, name)]
        return record.memory.model_copy(deep=True)

    async def delete(self, namespace: str, name: str) -> DeleteResult:
        """§5.5 DELETE async wrapper。"""
        async with self._lock:
            result = pure.delete(
                state=self._state,
                namespace=namespace,
                name=name,
                clock=self._clock,
            )
            if result.deleted:
                self._state.pop((namespace, name), None)
            return result

    async def list(self, query: QueryMemoryRequest) -> ListResult:
        """§5.6 LIST async wrapper。"""
        return pure.list_memories(
            state=self._state,
            query=query,
            clock=self._clock,
        )

    async def patch_status(
        self,
        namespace: str,
        name: str,
        status: object,
        *,
        expected_generation: int,
    ) -> None:
        """§5.7 patch_status · generation CAS。

        generation 不匹配 → MemoryBackendError(MEMORY_INTERNAL_ERROR, retryable=True)。
        """
        async with self._lock:
            key = (namespace, name)
            record = self._state.get(key)
            if record is None:
                raise MemoryBackendError(
                    MemoryErrorCode.MEMORY_INTERNAL_ERROR,
                    f"Memory {namespace}/{name} not found for patch_status",
                )
            if record.memory.metadata.generation != expected_generation:
                raise MemoryBackendError(
                    MemoryErrorCode.MEMORY_INTERNAL_ERROR,
                    f"Memory {namespace}/{name} generation CAS conflict "
                    f"(expected={expected_generation}, actual={record.memory.metadata.generation})",
                )
            # status 更新（caller 提供 status 对象）
            new_memory = record.memory.model_copy(deep=True)
            new_memory.status = status  # type: ignore[assignment]
            self._state[key] = StoredMemory(
                memory=new_memory,
                created_at=record.created_at,
                updated_at=self._clock.now(),
                version=record.version + 1,
                expires_at=record.expires_at,
                idempotency_key=record.idempotency_key,
            )

    async def health(self) -> BackendHealth:
        """§5.7 health · in-memory 始终 healthy（除非 state 异常）。"""
        return BackendHealth.HEALTHY

    async def metadata(self) -> BackendMetadata:
        """§5.7 metadata · self-describing。"""
        return BackendMetadata(
            backend_type=BackendType.IN_MEMORY,
            version="0.1.0",
            capabilities=frozenset({"put", "get", "delete", "list", "patch_status"}),
            max_size=self._max_size,
        )

    # ------------------------------------------------------------------
    # 辅助方法（测试 / 调试）
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """当前 entry 数（§5.7 不变量 5：可替换语义）。"""
        return len(self._state)


__all__ = ["InMemoryBackend"]
