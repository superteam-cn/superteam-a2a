"""L3-6 §6.1 record/query 不可变结果容器 · frozen Pydantic BaseModel。

memory / items 是 deep-copied snapshot（§5.7 不变量 1），caller 不得修改返回对象。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from superteam_a2a.knowledge_memory.backend.memory import Memory


class MemoryRecordResult(BaseModel):
    """record_memory_async 返回值 · §6.1 line 953-954。

    memory: deep-copied snapshot；phase 由 caller 填入；
    effective_confidence ∈ [0, 1]；resource_version ≥ 1。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    memory: Memory
    phase: str = "Pending"
    effective_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    resource_version: int = Field(ge=1)


class QueryMemoryResult(BaseModel):
    """query_memory_async 返回值 · §6.1 line 957。

    items 是固定 (namespace, name) 排序的 deep-copied Memory 元组。
    total_count ≥ 0（visible 总数；不含 expired）。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    items: tuple[Memory, ...]
    total_count: int = Field(ge=0)


__all__ = ["MemoryRecordResult", "QueryMemoryResult"]
