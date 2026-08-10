"""superteam_a2a Knowledge-Memory Service · ADR-0006 D 方案单进程服务。

L4 Phase 1 MVP Core 入口；合并 L3-5 + L3-6 为单 Python 进程。

依据 L3-5 Spec v0.2.0 + v0.2.1 + L3-6 Spec v0.2.0 + v0.2.1。
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.api.results import (
    MemoryRecordResult,
    QueryMemoryResult,
)
from superteam_a2a.knowledge_memory.api.service import (
    ADMISSION_TIMEOUT_SECONDS,
    MemoryBackendInProcessService,
    MemoryBackendInProcessServiceImpl,
)
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
    K8sBackend,
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
from superteam_a2a.knowledge_memory.handlers.admission_validator import (
    AdmissionValidatorImpl,
)
from superteam_a2a.knowledge_memory.handlers.memory_handler import (
    handle_query_memory,
    on_memory_create,
    on_memory_update,
)
from superteam_a2a.knowledge_memory.index.bm25_index import BM25Index
from superteam_a2a.knowledge_memory.reconciler.finalize import (
    MEMORY_FINALIZER,
    finalize_memory,
)
from superteam_a2a.knowledge_memory.reconciler.leader import (
    InProcessLeaderElector,
    K8sLeaseLeaderElector,
    LeaderElector,
)
from superteam_a2a.knowledge_memory.reconciler.memory_reconciler import (
    AdmissionValidatorProtocol,
    MemoryReconcilerService,
    memory_reconciler_timer,
)
from superteam_a2a.knowledge_memory.reconciler.types import (
    MemoryReconcilerError,
    ReconcileSummary,
)

__version__ = "0.1.0"

__all__ = [
    "ADMISSION_TIMEOUT_SECONDS",
    "MEMORY_FINALIZER",
    "RETRYABLE_CODES",
    "AdmissionValidatorImpl",
    "AdmissionValidatorProtocol",
    "BM25Index",
    "BackendHealth",
    "BackendMetadata",
    "BackendType",
    "Clock",
    "ClockSkewError",
    "DeleteResult",
    "FakeClock",
    "GetResult",
    "InMemoryBackend",
    "InProcessContext",
    "InProcessLeaderElector",
    "ItemReference",
    "K8sBackend",
    "K8sLeaseLeaderElector",
    "LeaderElector",
    "ListResult",
    "Memory",
    "MemoryBackend",
    "MemoryBackendError",
    "MemoryBackendInProcessService",
    "MemoryBackendInProcessServiceImpl",
    "MemoryContractError",
    "MemoryErrorCode",
    "MemoryReconcilerError",
    "MemoryReconcilerService",
    "MemoryRecordResult",
    "MemoryScope",
    "ObjectMeta",
    "PutResult",
    "QueryMemoryRequest",
    "QueryMemoryResult",
    "ReconcileSummary",
    "StoredMemory",
    "SystemClock",
    "__version__",
    "canonical_key",
    "canonical_key_parts",
    "elapsed_non_negative",
    "finalize_memory",
    "handle_query_memory",
    "is_retryable",
    "memory_error_data",
    "memory_reconciler_timer",
    "on_memory_create",
    "on_memory_update",
    "pure_delete",
    "pure_get",
    "pure_list_memories",
    "pure_put",
]
