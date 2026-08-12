"""KnowledgeScope CRD Pydantic v2 schema · 依据 L3-5 §3.1.

wire YAML contract 与 L2-4 Spec §3.2 字段 1:1 对齐。
简化模式（参考 packages/operator/models/memory.py）：metadata 字段不放在 Pydantic Spec 中
（K8s API server 注入），仅保留领域字段 spec + status + 顶层 wrapper。

CRD YAML 单一来源：charts/superteam-a2a/crds/knowledgescope.yaml。
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from superteam_a2a.knowledge.crd.inherit_rules import InheritRules
from superteam_a2a.knowledge.crd.scope_phase import ScopePhase
from superteam_a2a.knowledge.crd.scope_reference import ScopeReference


class ScopeLevel(StrEnum):
    """4 级 scope 枚举（ADR-0002 §3.1 + L2-4 Spec §3.2）。"""

    AGENT = "agent"
    AGENT_SET = "agentset"
    WORKFLOW = "workflow"
    SYSTEM = "system"


class SubjectKind(StrEnum):
    """subjectRef.kind 枚举（Agent/AgentSet）。"""

    AGENT = "Agent"
    AGENT_SET = "AgentSet"


class KnowledgeVisibility(StrEnum):
    """5 维 visibility 矩阵（ADR-0002 §4 + L2-4 Spec §4.5）。"""

    SCOPE_ONLY = "scope-only"
    SCOPE_AND_CHILDREN = "scope-and-children"
    PUBLIC_READABLE = "public-readable"
    AGENT_PRIVATE = "agent-private"
    SYSTEM_READONLY = "system-readonly"


class SubjectReference(BaseModel):
    """指向 Agent / AgentSet 的不可变引用。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    kind: SubjectKind = Field(description="subjectRef.kind type: Agent / AgentSet")
    name: str = Field(min_length=1, max_length=253)


class KnowledgeScopeSpec(BaseModel):
    """KnowledgeScope CRD spec（6 字段 · L3-5 §3.1 line 360-470）。

    wire 同步矩阵与 L2-4 Spec v0.2.0 §3.2 字段 1:1 对齐：
    - scopeLevel, name, subjectRef, parentRef (Optional), inheritRules (Optional), visibility
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scope_level: ScopeLevel = Field(alias="scopeLevel", description="作用域级别")
    name: str = Field(min_length=1, max_length=64)
    subject_ref: SubjectReference = Field(
        alias="subjectRef", description="Agent / AgentSet 主体引用"
    )
    parent_ref: ScopeReference | None = Field(
        default=None,
        alias="parentRef",
        description="system must be None; other levels strictly increase by 1",
    )
    inherit_rules: InheritRules | None = Field(
        default=None, alias="inheritRules", description="4 级 scope 继承过滤规则"
    )
    visibility: KnowledgeVisibility = Field(
        default=KnowledgeVisibility.SCOPE_AND_CHILDREN,
        description="5-dimensional visibility matrix; PUBLIC_READABLE allowed only for system scope",
    )


class KnowledgeScopeStatus(BaseModel):
    """KnowledgeScope CRD status（6 字段 · L3-5 §3.1 line 463-473）。

    wire 同步：phase / observedGeneration / lastUpdated / childScopes /
    knowledgeItemCount / activeQueries5m。
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    phase: ScopePhase | None = None
    observed_generation: int | None = Field(default=None, alias="observedGeneration", ge=0)
    last_updated: AwareDatetime | None = Field(default=None, alias="lastUpdated")
    child_scopes: list[ScopeReference] = Field(default_factory=list, alias="childScopes")
    knowledge_item_count: int | None = Field(default=None, alias="knowledgeItemCount", ge=0)
    active_queries_5m: int | None = Field(default=None, alias="activeQueries5m", ge=0)


class KnowledgeScope(BaseModel):
    """KnowledgeScope CRD 顶层 wrapper（含 apiVersion + kind + spec + status）。

    metadata 由 K8s API server 注入，不在本 Pydantic schema 中。
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    api_version: str = Field(default="knowledge.superteam-a2a.io/v1alpha1", alias="apiVersion")
    kind: str = Field(default="KnowledgeScope")
    spec: KnowledgeScopeSpec
    status: KnowledgeScopeStatus | None = None


__all__ = [
    "KnowledgeScope",
    "KnowledgeScopeSpec",
    "KnowledgeScopeStatus",
    "KnowledgeVisibility",
    "ScopeLevel",
    "SubjectKind",
    "SubjectReference",
]
