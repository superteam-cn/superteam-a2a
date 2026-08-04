"""superteam_a2a Knowledge-Memory Service · ADR-0006 D 方案单进程服务。

L4 Phase 1 MVP Core 入口；合并 L3-5 + L3-6 为单 Python 进程。

依据 L3-5 Spec v0.2.0 + v0.2.1 + L3-6 Spec v0.2.0 + v0.2.1。
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.backend import (
    RETRYABLE_CODES,
    BackendHealth,
    BackendMetadata,
    BackendType,
    Clock,
    ClockSkewError,
    DeleteResult,
    FakeClock,
    GetResult,
    InMemoryBackend,
    ItemReference,
    ListResult,
    Memory,
    MemoryBackend,
    MemoryBackendError,
    MemoryContractError,
    MemoryErrorCode,
    MemoryScope,
    ObjectMeta,
    PutResult,
    QueryMemoryRequest,
    StoredMemory,
    SystemClock,
    canonical_key,
    canonical_key_parts,
    elapsed_non_negative,
    is_retryable,
    memory_error_data,
    pure_delete,
    pure_get,
    pure_list_memories,
    pure_put,
)

__version__ = "0.1.0"

__all__ = [
    "RETRYABLE_CODES",
    "BackendHealth",
    "BackendMetadata",
    "BackendType",
    "Clock",
    "ClockSkewError",
    "DeleteResult",
    "FakeClock",
    "GetResult",
    "InMemoryBackend",
    "ItemReference",
    "ListResult",
    "Memory",
    "MemoryBackend",
    "MemoryBackendError",
    "MemoryContractError",
    "MemoryErrorCode",
    "MemoryScope",
    "ObjectMeta",
    "PutResult",
    "QueryMemoryRequest",
    "StoredMemory",
    "SystemClock",
    "__version__",
    "canonical_key",
    "canonical_key_parts",
    "elapsed_non_negative",
    "is_retryable",
    "memory_error_data",
    "pure_delete",
    "pure_get",
    "pure_list_memories",
    "pure_put",
]
