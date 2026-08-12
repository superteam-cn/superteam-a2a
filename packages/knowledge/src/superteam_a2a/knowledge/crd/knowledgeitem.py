"""KnowledgeItem CRD Pydantic v2 schema · 依据 L3-5 §3.2.

wire YAML contract 与 L2-4 Spec §3.3 字段 1:1 对齐。
简化模式（参考 packages/operator/models/memory.py）：metadata 字段不放在 Pydantic Spec 中。

CRD YAML 单一来源：charts/superteam-a2a/crds/knowledgeitem.yaml。
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from superteam_a2a.knowledge.crd.item_reference import ItemReference
from superteam_a2a.knowledge.crd.knowledgescope import (
    KnowledgeVisibility,
    ScopeReference,
)


class KnowledgeType(StrEnum):
    """KnowledgeItem 4 类枚举（ADR-0002 §3.2 · 与 L2-4 Spec §3.3 完全一致）。"""

    PROCEDURAL = "procedural"
    FACTUAL = "factual"
    EPISODIC = "episodic"
    CONCEPTUAL = "conceptual"


class ItemPhase(StrEnum):
    """KnowledgeItem status.phase 5 态状态机。"""

    INDEXING = "Indexing"
    ACTIVE = "Active"
    DECAYING = "Decaying"
    SUPERSEDED = "Superseded"
    ARCHIVED = "Archived"


class DecayState(BaseModel):
    """KnowledgeItem 衰减状态（status.effective_confidence 计算依据）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    last_accessed: AwareDatetime | None = Field(default=None, alias="lastAccessed")
    access_count_24h: int = Field(default=0, alias="accessCount24h", ge=0)
    decay_days: int = Field(default=90, ge=1, le=3650, alias="decayDays")


class KnowledgeItemSpec(BaseModel):
    """KnowledgeItem CRD spec（7 字段 · L3-5 §3.2 line 586-605）。

    wire 同步：scopeRef / knowledgeType / content / tags (max=20) /
    version / supersededBy (Optional) / confidence。
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scope_ref: ScopeReference = Field(alias="scopeRef")
    knowledge_type: KnowledgeType = Field(alias="knowledgeType")
    content: str = Field(min_length=1, max_length=65536, description="64KB Markdown body")
    tags: list[str] | None = Field(default=None, max_length=20)
    version: int = Field(default=1, ge=1)
    superseded_by: ItemReference | None = Field(
        default=None,
        alias="supersededBy",
        description="newer version reference; older version marked SUPERSEDED",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="initial confidence; status.effective_confidence computed by decay formula",
    )


class KnowledgeItemStatus(BaseModel):
    """KnowledgeItem CRD status（7 字段 · L3-5 §3.2 line 608-621）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    phase: ItemPhase | None = None
    indexed_at: AwareDatetime | None = Field(default=None, alias="indexedAt")
    last_accessed: AwareDatetime | None = Field(default=None, alias="lastAccessed")
    access_count_24h: int = Field(default=0, alias="accessCount24h", ge=0)
    bm25_score_avg: float | None = Field(default=None, alias="bm25ScoreAvg", ge=0.0)
    decay_state: DecayState | None = Field(default=None, alias="decayState")
    effective_confidence: float | None = Field(
        default=None, alias="effectiveConfidence", ge=0.0, le=1.0
    )


class KnowledgeItem(BaseModel):
    """KnowledgeItem CRD 顶层 wrapper（含 apiVersion + kind + spec + status）。

    metadata 由 K8s API server 注入。
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    api_version: str = Field(default="knowledge.superteam-a2a.io/v1alpha1", alias="apiVersion")
    kind: str = Field(default="KnowledgeItem")
    spec: KnowledgeItemSpec
    status: KnowledgeItemStatus | None = None


__all__ = [
    "DecayState",
    "ItemPhase",
    "ItemReference",
    "KnowledgeItem",
    "KnowledgeItemSpec",
    "KnowledgeItemStatus",
    "KnowledgeType",
    # re-export for convenience
    "KnowledgeVisibility",
    "ScopeReference",
]
