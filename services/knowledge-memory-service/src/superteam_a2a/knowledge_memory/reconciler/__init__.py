"""MemoryReconciler - L3-6 -4 - 60s kopf.timer + Leader Election + finalize 5-step.

ADR-0006 v1.0 Accepted D plan - single-process - MemoryBackend abstraction (PR #17 merged at bf1ca4b).

Public API (15 symbols):
- types: ReconcileSummary, MemoryReconcilerError
- leader: LeaderElector (Protocol), InProcessLeaderElector, K8sLeaseLeaderElector
- timer constants: TIMER_INTERVAL_SECONDS=60.0, TIMER_ID="memory-reconciler"
- finalize: MEMORY_FINALIZER, finalize_memory (kopf.on.delete logic)
- entry: MemoryReconcilerService, memory_reconciler_timer (kopf.timer logic)

L4-Step3: complete implementation - all 5 files (types, leader, memory_reconciler,
finalize, __init__). TEST-MEM-016~030 in tests/unit/knowledge_memory/reconciler/
"""

from __future__ import annotations

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
    ADMISSION_TIMEOUT_BACKOFF,
    ADMISSION_TIMEOUT_SECONDS,
    MAX_RECONCILE_RETRIES,
    RETRY_BACKOFF_SECONDS,
    TIMER_ID,
    TIMER_INTERVAL_SECONDS,
    AdmissionTimeoutError,
    AdmissionValidatorProtocol,
    BackendUnavailable,
    Index,
    MemoryReconcilerService,
    canonical_memory_code,
    memory_reconciler_timer,
)
from superteam_a2a.knowledge_memory.reconciler.types import (
    MemoryReconcilerError,
    ReconcileSummary,
)

__all__ = [
    "ADMISSION_TIMEOUT_BACKOFF",
    "ADMISSION_TIMEOUT_SECONDS",
    "MAX_RECONCILE_RETRIES",
    "MEMORY_FINALIZER",
    "RETRY_BACKOFF_SECONDS",
    "TIMER_ID",
    "TIMER_INTERVAL_SECONDS",
    "AdmissionTimeoutError",
    "AdmissionValidatorProtocol",
    "BackendUnavailable",
    "InProcessLeaderElector",
    "Index",
    "K8sLeaseLeaderElector",
    "LeaderElector",
    "MemoryReconcilerError",
    "MemoryReconcilerService",
    "ReconcileSummary",
    "canonical_memory_code",
    "finalize_memory",
    "memory_reconciler_timer",
]
