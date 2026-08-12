"""Memory CRD Pydantic v2 schema · 依据 L3-5 §3.3.

文件名使用 memory_schema.py 而非 memory.py，避免与 L2-4
`packages/memory/src/supteam_a2a/memory/apis/v1alpha1/memory.py` 命名冲突。

wire YAML contract 与 L2-4 Spec §3.4 字段 1:1 对齐（5+5 简化字段集）。
简化模式（参考 packages/operator/models/memory.py）：metadata 字段不放在 Pydantic Spec 中。

CRD YAML 单一来源：charts/superteam-a2a/crds/memory.yaml。
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from superteam_a2a.knowledge.crd.knowledgescope import (
    ScopeLevel,
    ScopeReference,
)


class MemoryPhase(StrEnum):
    """Memory status.phase 5 态状态机（ADR-0003 §3 + L2-4 Spec §3.4）。"""

    ACTIVE = "Active"
    DECAYING = "Decaying"
    PROMOTABLE = "Promotable"
    EXPIRED = "Expired"
    ERROR = "Error"


class GCState(StrEnum):
    """Memory GC 状态机（L3-6 详细落地 · L3-5 仅作为 schema 字段）。"""

    NONE = "None"
    PENDING = "Pending"
    CLEANED = "Cleaned"
    KEPT = "Kept"


class AgentReference(BaseModel):
    """Agent (ServiceAccount) 引用（frozen）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    kind: str = Field(default="ServiceAccount", description="固定为 ServiceAccount")
    name: str = Field(min_length=1, max_length=253)


class MemorySpec(BaseModel):
    """Memory CRD spec（5 字段 · L3-5 §3.3 line 728-754）。

    wire 同步矩阵（与 L2-4 Spec v0.2.0 §3.4 字段 1:1 对齐 · 5+5 简化字段集）：
    - scopeRef, agentRef, content (max 20 keys), decayDays, confidence。
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scope_ref: ScopeReference = Field(alias="scopeRef")
    agent_ref: AgentReference = Field(
        alias="agentRef",
        description="must be ServiceAccount; mutually exclusive with KI.User/Group (L2-4 Spec §3.4)",
    )
    content: dict[str, str] = Field(min_length=1, max_length=20)
    decay_days: int = Field(
        default=30, ge=0, le=3650, alias="decayDays", description="decay 半衰期"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="initial confidence; status.effective_confidence computed by decay formula",
    )


class MemoryStatus(BaseModel):
    """Memory CRD status（5 字段 · L3-5 §3.3 line 757-772）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    phase: MemoryPhase | None = None
    observed_generation: int | None = Field(default=None, alias="observedGeneration", ge=0)
    conditions: list[dict[str, str]] = Field(default_factory=list)
    last_updated: AwareDatetime | None = Field(default=None, alias="lastUpdated")
    effective_confidence: float | None = Field(
        default=None,
        alias="effectiveConfidence",
        ge=0.0,
        le=1.0,
        description="effectiveConfidence = confidence * exp(-elapsed_days / decayDays) (ADR-0003 §4.1)",
    )


class Memory(BaseModel):
    """Memory CRD 顶层 wrapper（含 apiVersion + kind + spec + status）。

    metadata 由 K8s API server 注入。
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    api_version: str = Field(default="memory.superteam-a2a.io/v1alpha1", alias="apiVersion")
    kind: str = Field(default="Memory")
    spec: MemorySpec
    status: MemoryStatus | None = None


__all__ = [
    "AgentReference",
    "GCState",
    "Memory",
    "MemoryPhase",
    "MemorySpec",
    "MemoryStatus",
    "ScopeLevel",
    "ScopeReference",
]
