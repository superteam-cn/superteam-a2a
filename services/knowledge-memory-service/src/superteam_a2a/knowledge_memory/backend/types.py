"""MemoryBackend 抽象层 Result 类型 · L3-6 §5.3-§5.6 返回值容器。

所有 Result 都是 frozen Pydantic BaseModel；记录字段为 deep-copied snapshot，
caller 不得修改返回对象（§5.7 不变量 1：不可变快照）。

注意：StoredMemory.memory 和 GET/LIST 返回的 memory 都是 Memory（顶层 CRD），
而非 MemorySpec——这样 caller 不用关心 metadata/status/spec 拆分。
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from superteam_a2a.knowledge_memory.backend.memory import Memory

# ============================================================================
# StoredMemory · backend 内部存储记录（memory + 时间戳 + version）
# ============================================================================


class StoredMemory(BaseModel):
    """backend 内部存储记录（§5.4 GET 输入）。"""

    model_config = ConfigDict(extra="forbid", frozen=True)
    memory: Memory
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int = Field(ge=1)
    expires_at: AwareDatetime | None = None
    idempotency_key: str | None = Field(default=None, max_length=128)


# ============================================================================
# QueryMemoryRequest · LIST 入参（§5.6）
# ============================================================================


class MemoryScope(StrEnum):
    """Memory scope 5 类（继承 L3-6 §3 + L2-4 §3.4）。"""

    AGENT = "agent"
    SCOPE = "scope"
    INDUSTRY = "industry"
    PROJECT = "project"
    GLOBAL = "global"


class QueryMemoryRequest(BaseModel):
    """LIST query 入参（§5.6 list_memories）。"""

    model_config = ConfigDict(extra="forbid", frozen=True)
    scope: MemoryScope
    namespace: str | None = Field(default=None, max_length=128)
    agent_ref: str | None = Field(default=None, max_length=253)
    tags: tuple[str, ...] = Field(default_factory=tuple, max_length=10)
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# ============================================================================
# Result Types · §5.3 PUT / §5.4 GET / §5.5 DELETE / §5.6 LIST
# ============================================================================


class PutResult(BaseModel):
    """PUT 返回（§5.3 line 837-839）。"""

    model_config = ConfigDict(extra="forbid", frozen=True)
    stored_at: AwareDatetime
    expires_at: AwareDatetime | None = None
    version: int = Field(ge=1)
    idempotency_key: str | None = None


class GetResult(BaseModel):
    """GET 返回（§5.4 line 850-851）。

    found=False 时 memory=None（NOT_FOUND 由 handler 决定空集合，不创造 MEMORY_*）。
    found=True 时 memory 是 deep copy of stored Memory。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    found: bool
    memory: Memory | None = None
    snapshot_at: AwareDatetime


class DeleteResult(BaseModel):
    """DELETE 返回（§5.5 line 862-866）。

    deleted=False 表示 key 不存在（幂等重放）；deleted=True 表示删除成功。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    deleted: bool
    deleted_at: AwareDatetime


class ListResult(BaseModel):
    """LIST 返回（§5.6 line 880-882）。

    items 是固定 (namespace, name) 排序的 deep-copied Memory 元组。
    total 是 visible 总数（不含 expired）。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    items: tuple[Memory, ...]
    total: int = Field(ge=0)
    snapshot_at: AwareDatetime


# ============================================================================
# MemoryBackend Metadata · §5.7 5 项不变量之 5：可替换语义
# ============================================================================


class BackendType(StrEnum):
    """L3-6 §3.2 backend 类型。"""

    IN_MEMORY = "in-memory"
    DICT = "dict"
    REDIS = "redis"


class BackendHealth(StrEnum):
    """backend 健康状态。"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class BackendMetadata(BaseModel):
    """backend 自描述（§5.7 5 项不变量之 5）。"""

    model_config = ConfigDict(extra="forbid", frozen=True)
    backend_type: BackendType
    version: str = Field(min_length=1, max_length=64)
    capabilities: frozenset[str] = Field(default_factory=frozenset)
    max_size: int = Field(ge=1)


__all__ = [
    "BackendHealth",
    "BackendMetadata",
    "BackendType",
    "DeleteResult",
    "GetResult",
    "ListResult",
    "MemoryScope",
    "PutResult",
    "QueryMemoryRequest",
    "StoredMemory",
]
