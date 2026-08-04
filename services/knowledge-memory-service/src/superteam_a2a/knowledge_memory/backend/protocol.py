"""MemoryBackend Protocol · L3-6 §5.7 6 抽象方法 + 5 项不变量。

@runtime_checkable Protocol；dict/in-memory/redis 后端必须通过同一 contract suite。
后端仅抛 MemoryBackendError(code: MemoryErrorCode, retryable, cause)。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from superteam_a2a.knowledge_memory.backend.errors import MemoryErrorCode
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.backend.types import (
    BackendHealth,
    BackendMetadata,
    DeleteResult,
    ListResult,
    PutResult,
    QueryMemoryRequest,
)


@runtime_checkable
class MemoryBackend(Protocol):
    """L3-6 §5.7 MemoryBackend Protocol · 6 抽象方法。

    5 项不变量：
    1. 不可变快照：输入与返回对象 deep copy/frozen
    2. 线性化单 key 写：PUT/DELETE/patch_status 原子；CAS 冲突显式失败
    3. Clock 唯一时间源：TTL/节流/deadline 使用注入 Clock
    4. 错误码封闭集：仅 L2-4 §9.1 12 个 MEMORY_*；禁止任何新增同义错误码
    5. 可替换语义：切换 backendType 不改变排序/TTL/幂等/caller 可观察结果
    """

    async def put(
        self,
        memory: Memory,
        *,
        idempotency_key: str | None = None,
    ) -> PutResult:
        """§5.7 PUT · 原子写入。capacity 满抛 MEMORY_FORBIDDEN，schema 错抛 MEMORY_INVALID_CONTENT。"""
        ...

    async def get(self, namespace: str, name: str) -> Memory | None:
        """§5.7 GET · 返回 deep copy 或 None（不存在不算 MEMORY_* 错误）。"""
        ...

    async def delete(self, namespace: str, name: str) -> DeleteResult:
        """§5.7 DELETE · 幂等；deleted=False 表示 key 不存在。"""
        ...

    async def list(self, query: QueryMemoryRequest) -> ListResult:
        """§5.7 LIST · 稳定 (namespace, name) 排序；industry 无过滤抛 MEMORY_QUERY_TOO_BROAD。"""
        ...

    async def patch_status(
        self,
        namespace: str,
        name: str,
        status: object,
        *,
        expected_generation: int,
    ) -> None:
        """§5.7 patch_status · generation CAS；冲突显式失败（§4.3 CAS 规则）。"""
        ...

    async def health(self) -> BackendHealth:
        """§5.7 health · 用于健康检查端点。"""
        ...

    async def metadata(self) -> BackendMetadata:
        """§5.7 metadata · backend 自描述（backend_type/version/capabilities/max_size）。"""
        ...


def require_memory_error_code(code: object) -> MemoryErrorCode:
    """§5.7 不变量 4 守护：抛出前检查 code 是 MemoryErrorCode 枚举成员。"""
    if not isinstance(code, MemoryErrorCode):
        raise TypeError(
            f"MemoryBackend code must be MemoryErrorCode, got {type(code).__name__}: {code!r}"
        )
    return code


__all__ = [
    "MemoryBackend",
    "require_memory_error_code",
]
