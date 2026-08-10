"""8 个 label 维度封闭枚举（L3-6 §7.1 line 1060 强类型约束）。

禁止 `memory_name` / `service_account` / `scope_name` / `request_id` 进入 label。
"""

from __future__ import annotations

from enum import StrEnum


class Phase(StrEnum):
    """reconcile 阶段（MEMORY_RECONCILE_TOTAL labels / MEMORY_RECONCILE_DURATION_SECONDS labels）"""

    ADMIT = "admit"
    RECONCILE = "reconcile"
    FINALIZE = "finalize"


class Result(StrEnum):
    """操作结果（MEMORY_RECONCILE_TOTAL / MEMORY_REINFORCE_TOTAL / MEMORY_IN_PROCESS_CALL_TOTAL labels）"""

    SUCCESS = "success"
    ERROR = "error"
    CONFLICT = "conflict"
    CANCELLED = "cancelled"


class GCState(StrEnum):
    """GC 状态（MEMORY_GC_CLEANED_TOTAL labels）"""

    EXPIRED = "expired"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class Visibility(StrEnum):
    """可见性（MEMORY_PROMOTION_ELIGIBLE_TOTAL labels）"""

    PRIVATE = "private"
    TEAM = "team"
    ORG = "org"
    INDUSTRY = "industry"


class ScopeLevel(StrEnum):
    """Scope 级别（MEMORY_BM25_INDEX_SIZE labels）"""

    AGENT = "agent"
    TEAM = "team"
    ORG = "org"
    INDUSTRY = "industry"
    GLOBAL = "global"


class Validator(StrEnum):
    """Admission 验证器（MEMORY_ADMISSION_DURATION_SECONDS labels）"""

    SCHEMA = "schema"
    SCOPE = "scope"
    CONTENT = "content"
    RATE = "rate"


class Method(StrEnum):
    """L3-5 to L3-6 in-process method（MEMORY_IN_PROCESS_CALL_TOTAL labels）"""

    RECORD_MEMORY = "record_memory"
    QUERY_MEMORY = "query_memory"


class PrincipalType(StrEnum):
    """Rate-limit principal（MEMORY_RATE_LIMITED_TOTAL labels）"""

    SERVICE_ACCOUNT = "service_account"
    USER = "user"
    AGENT = "agent"
