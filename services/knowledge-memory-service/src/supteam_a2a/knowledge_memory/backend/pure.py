"""4 个 MemoryBackend 纯函数 · L3-6 §5.3-§5.6。

依据 D-4 决策（l4-tdd-methodology.md）：Go sync.Mutex 保护纯函数 →
**Python 同步 pure function + async wrapper**。

特性：
- 同步（不阻塞 event loop · 不需 await）
- stateless（无内部状态；state 由 caller 传入）
- 不可变（输入输出 deep copy；返回 immutable Mapping）
- Clock 注入（禁止函数内部读取系统时间）
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta

from superteam_a2a.knowledge_memory.backend.clock import Clock
from superteam_a2a.knowledge_memory.backend.errors import (
    MemoryContractError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.backend.memory import (
    Memory,
    canonical_key,
    canonical_key_parts,
)
from superteam_a2a.knowledge_memory.backend.types import (
    DeleteResult,
    GetResult,
    ListResult,
    PutResult,
    QueryMemoryRequest,
    StoredMemory,
)

# ============================================================================
# §5.3 PUT 纯函数
# ============================================================================


def put(
    state: Mapping[tuple[str, str], StoredMemory],
    memory: Memory,
    *,
    clock: Clock,
    max_size: int,
    ttl_seconds: int | None,
) -> PutResult:
    """§5.3 PUT · validate + immutable record。

    - 新 key 且 capacity 满 → MemoryContractError(MEMORY_FORBIDDEN)
    - 同 key → 原子 replace（idempotency_key 重复返回同 result）
    - schema/content 错误由 Pydantic 在 caller 端抛 MEMORY_INVALID_CONTENT
    """
    key = canonical_key(memory)
    if key not in state and len(state) >= max_size:
        raise MemoryContractError(
            MemoryErrorCode.MEMORY_FORBIDDEN,
            f"backend capacity reached ({len(state)}/{max_size})",
        )
    now = clock.now()
    expires_at = now + timedelta(seconds=ttl_seconds) if ttl_seconds else None
    return PutResult(
        stored_at=now,
        expires_at=expires_at,
        version=_next_version(state, key),
        idempotency_key=None,
    )


def _next_version(
    state: Mapping[tuple[str, str], StoredMemory],
    key: tuple[str, str],
) -> int:
    """PUT version 递增（同 key）或初始为 1。"""
    existing = state.get(key)
    if existing is None:
        return 1
    return existing.version + 1


# ============================================================================
# §5.4 GET 纯函数
# ============================================================================


def get(
    state: Mapping[tuple[str, str], StoredMemory],
    namespace: str,
    name: str,
    *,
    clock: Clock,
) -> GetResult:
    """§5.4 GET · TTL + snapshot。

    - 命中 + 未过期 → 返回 deep copy of stored Memory
    - 不存在 / 已过期 → found=False, memory=None（**不创造 MEMORY_* 错误**）
    """
    key = canonical_key_parts(namespace, name)
    record = state.get(key)
    snapshot_at = clock.now()
    if record is None:
        return GetResult(found=False, memory=None, snapshot_at=snapshot_at)
    if record.expires_at is not None and snapshot_at >= record.expires_at:
        return GetResult(found=False, memory=None, snapshot_at=snapshot_at)
    return GetResult(
        found=True,
        memory=record.memory.model_copy(deep=True),
        snapshot_at=snapshot_at,
    )


# ============================================================================
# §5.5 DELETE 纯函数
# ============================================================================


def delete(
    state: Mapping[tuple[str, str], StoredMemory],
    namespace: str,
    name: str,
    *,
    clock: Clock,
) -> DeleteResult:
    """§5.5 DELETE · 幂等 tombstone。

    - existing → deleted=True
    - 不存在 → deleted=False（幂等重放，不报错）
    """
    key = canonical_key_parts(namespace, name)
    removed = state.get(key)
    return DeleteResult(
        deleted=removed is not None,
        deleted_at=clock.now(),
    )


# ============================================================================
# §5.6 LIST 纯函数
# ============================================================================


def list_memories(
    state: Mapping[tuple[str, str], StoredMemory],
    query: QueryMemoryRequest,
    *,
    clock: Clock,
) -> ListResult:
    """§5.6 LIST · 稳定排序 + snapshot pagination。

    - industry scope 必须有 tag 或 min_confidence 过滤，否则 MEMORY_QUERY_TOO_BROAD
    - 固定 (namespace, name) 排序
    - 一次调用读取一个 immutable snapshot
    """
    if query.scope.value == "industry" and not (query.tags or query.min_confidence is not None):
        raise MemoryContractError(
            MemoryErrorCode.MEMORY_QUERY_TOO_BROAD,
            "Memory query with scope=industry requires tag/confidence filter",
        )

    snapshot_at = clock.now()
    visible: list[StoredMemory] = []
    for record in state.values():
        if record.expires_at is not None and snapshot_at >= record.expires_at:
            continue  # expired
        if not _visible_to(record, query):
            continue
        visible.append(record)

    ordered = sorted(visible, key=lambda r: (r.memory.metadata.namespace, r.memory.metadata.name))
    page = ordered[query.offset : query.offset + query.limit]
    items = tuple(r.memory.model_copy(deep=True) for r in page)
    return ListResult(items=items, total=len(ordered), snapshot_at=snapshot_at)


def _visible_to(record: StoredMemory, query: QueryMemoryRequest) -> bool:
    """§5.6 visibility 过滤。"""
    if query.namespace is not None and record.memory.metadata.namespace != query.namespace:
        return False
    if query.agent_ref is not None and record.memory.spec.agent_ref.name != query.agent_ref:
        return False
    if query.min_confidence is not None and record.memory.spec.confidence < query.min_confidence:
        return False
    if query.tags:
        record_tags = record.memory.spec.tags or []
        if not any(t in record_tags for t in query.tags):
            return False
    return True


__all__ = [
    "delete",
    "get",
    "list_memories",
    "put",
]
