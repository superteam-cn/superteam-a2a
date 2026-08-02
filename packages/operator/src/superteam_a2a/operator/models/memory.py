"""Memory CRD Pydantic v2 schema · 依据 L3-1 Spec §6.2.1-§6.2.5.

wire YAML contract 与 L2-4 Spec §3.4 + L3-6 Spec §3 完全一致。
所有模型使用 ConfigDict(extra="forbid", populate_by_name=True) 强制 wire contract 严格。
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class MemoryPhase(StrEnum):
    """L3-1 §6.2.5 line 1827-1833 · Memory status.phase 状态机(5 态)。"""

    ACTIVE = "Active"  # effective_confidence > 0.5
    DECAYING = "Decaying"  # 0.01 <= effective_confidence <= 0.5
    PROMOTABLE = "Promotable"  # eligible_for_promotion = true
    EXPIRED = "Expired"  # effective_confidence < 0.01
    ERROR = "Error"  # reconcile 失败


class MemoryVisibility(StrEnum):
    """L3-1 §6.2.5 line 1836-1840 · Memory visibility 3 类(5 维矩阵)。"""

    SCOPE_ONLY = "scope-only"
    SCOPE_AND_CHILDREN = "scope-and-children"
    AGENT_PRIVATE = "agent-private"


class MemoryConditionType(StrEnum):
    """L3-1 §6.2.4 line 1797-1803 · Memory status.conditions[].type 枚举(5 类)。"""

    DECAYED = "Decayed"
    REINFORCED = "Reinforced"
    PROMOTED = "Promoted"
    ARCHIVED = "Archived"
    GARBAGE_COLLECTED = "GarbageCollected"


class ScopeReference(BaseModel):
    """L2-4 §3.4 占位 · 待 #76+ 落地完整实现。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)
    name: str = Field(min_length=1, max_length=128)
    level: str | None = None


class AgentReference(BaseModel):
    """L3-1 §6.2.2 line 1727-1731 · Agent(ServiceAccount)引用。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)
    kind: str = Field(default="ServiceAccount", description="固定为 ServiceAccount")
    name: str = Field(min_length=1, max_length=253)


class MemoryCondition(BaseModel):
    """L3-1 §6.2.4 line 1806-1813 · K8s-style condition。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    type: MemoryConditionType
    status: str = Field(pattern=r"^(True|False|Unknown)$")
    reason: str | None = Field(default=None, max_length=128)
    message: str | None = Field(default=None, max_length=512)
    last_transition_time: AwareDatetime = Field(alias="lastTransitionTime")


class MemorySpec(BaseModel):
    """L3-1 §6.2.2 line 1734-1752 · Memory CRD spec(12 字段)。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    scope_ref: ScopeReference = Field(alias="scopeRef")
    agent_ref: AgentReference = Field(
        alias="agentRef",
        description="必须 ServiceAccount;与 KI.User/Group 互斥(L2-4 Spec §3.4)",
    )
    content: dict[str, str] = Field(min_length=1, max_length=20)
    summary: str = Field(min_length=1, max_length=512)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    decay_days: int = Field(default=30, ge=1, le=3650, alias="decayDays")
    reinforced_count: int = Field(default=0, ge=0, alias="reinforcedCount")
    last_reinforced_at: AwareDatetime | None = Field(default=None, alias="lastReinforcedAt")
    memory_key_pattern: str | None = Field(default=None, alias="memoryKeyPattern", max_length=128)
    source_knowledge_ref: dict[str, Any] | None = Field(
        default=None,
        alias="sourceKnowledgeRef",
        description="追溯的 KnowledgeItem(dict 形式,避免循环 import L2-4)",
    )
    tags: list[str] | None = Field(default=None, max_length=10)
    visibility: MemoryVisibility = Field(default=MemoryVisibility.SCOPE_AND_CHILDREN)


class MemoryStatus(BaseModel):
    """L3-1 §6.2.3 line 1770-1781 · Memory CRD status(7 字段)。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    phase: MemoryPhase | None = None
    message: str | None = Field(default=None, max_length=512)
    conditions: list[MemoryCondition] = []  # Pydantic v2 deep-copies mutable defaults
    last_decayed_at: AwareDatetime | None = Field(default=None, alias="lastDecayedAt")
    last_reinforced_at: AwareDatetime | None = Field(default=None, alias="lastReinforcedAt")
    effective_confidence: float | None = Field(
        default=None, alias="effectiveConfidence", ge=0.0, le=1.0
    )
    eligible_for_promotion: bool | None = Field(default=None, alias="eligibleForPromotion")
    observed_generation: int | None = Field(default=None, alias="observedGeneration", ge=0)


__all__ = [
    "AgentReference",
    "MemoryCondition",
    "MemoryConditionType",
    "MemoryPhase",
    "MemorySpec",
    "MemoryStatus",
    "MemoryVisibility",
    "ScopeReference",
]
