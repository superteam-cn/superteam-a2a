"""MemoryBackend 抽象层公共 API · L3-6 §5 + §8。

子包：
- errors: 12 MEMORY_* 错误码 + MemoryBackendError
- clock: Clock Protocol + SystemClock + FakeClock
- types: Result + Query + Stored + BackendMetadata
- memory: Memory 顶层 + ObjectMeta + ItemReference
- protocol: MemoryBackend Protocol
- pure: 4 纯函数 (sync, stateless)
- in_memory: InMemoryBackend (默认 dict-backed async wrapper)
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.backend.clock import (
    Clock,
    FakeClock,
    SystemClock,
    elapsed_non_negative,
)
from superteam_a2a.knowledge_memory.backend.errors import (
    RETRYABLE_CODES,
    ClockSkewError,
    MemoryBackendError,
    MemoryContractError,
    MemoryErrorCode,
    is_retryable,
    memory_error_data,
)
from superteam_a2a.knowledge_memory.backend.in_memory import InMemoryBackend
from superteam_a2a.knowledge_memory.backend.memory import (
    ItemReference,
    Memory,
    ObjectMeta,
    canonical_key,
    canonical_key_parts,
)
from superteam_a2a.knowledge_memory.backend.protocol import MemoryBackend
from superteam_a2a.knowledge_memory.backend.pure import (
    delete as pure_delete,
)
from superteam_a2a.knowledge_memory.backend.pure import (
    get as pure_get,
)
from superteam_a2a.knowledge_memory.backend.pure import (
    list_memories as pure_list_memories,
)
from superteam_a2a.knowledge_memory.backend.pure import (
    put as pure_put,
)
from superteam_a2a.knowledge_memory.backend.types import (
    BackendHealth,
    BackendMetadata,
    BackendType,
    DeleteResult,
    GetResult,
    ListResult,
    MemoryScope,
    PutResult,
    QueryMemoryRequest,
    StoredMemory,
)

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
