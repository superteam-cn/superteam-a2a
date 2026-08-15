"""L4-Phase3 PR-3 observability 子包 · 10 Memory 业务指标 + starlette /metrics 集成。

依据 L3-6 §7.1 line 1047-1060 权威表 + L3-2 §9.1 line 1295-1309 复用 15 指标。
合计 25 指标 · HELM-DEPLOY-007 单一 ServiceMonitor 可见 · 8 PrometheusRule alerts 触发。
"""

from superteam_a2a.knowledge_memory.observability.binding import bind_metrics_to_app
from superteam_a2a.knowledge_memory.observability.labels import (
    GCState,
    Method,
    Phase,
    PrincipalType,
    Result,
    ScopeLevel,
    Validator,
    Visibility,
)
from superteam_a2a.knowledge_memory.observability.metrics import (
    MEMORY_ADMISSION_DURATION_SECONDS,
    MEMORY_BM25_INDEX_SIZE,
    MEMORY_DECAY_APPLIED_TOTAL,
    MEMORY_GC_CLEANED_TOTAL,
    MEMORY_IN_PROCESS_CALL_TOTAL,
    MEMORY_PROMOTION_ELIGIBLE_TOTAL,
    MEMORY_RATE_LIMITED_TOTAL,
    MEMORY_RECONCILE_DURATION_SECONDS,
    MEMORY_RECONCILE_TOTAL,
    MEMORY_REINFORCE_TOTAL,
)

__all__ = [
    "MEMORY_ADMISSION_DURATION_SECONDS",
    "MEMORY_BM25_INDEX_SIZE",
    "MEMORY_DECAY_APPLIED_TOTAL",
    "MEMORY_GC_CLEANED_TOTAL",
    "MEMORY_IN_PROCESS_CALL_TOTAL",
    "MEMORY_PROMOTION_ELIGIBLE_TOTAL",
    "MEMORY_RATE_LIMITED_TOTAL",
    "MEMORY_RECONCILE_DURATION_SECONDS",
    "MEMORY_RECONCILE_TOTAL",
    "MEMORY_REINFORCE_TOTAL",
    "GCState",
    "Method",
    "Phase",
    "PrincipalType",
    "Result",
    "ScopeLevel",
    "Validator",
    "Visibility",
    "bind_metrics_to_app",
]
