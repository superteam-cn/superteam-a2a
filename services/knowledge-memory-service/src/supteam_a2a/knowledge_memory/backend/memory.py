"""Memory 顶层 Pydantic v2 模型 · L3-6 §3.4 + §3.5 wire contract。

包含 ObjectMeta / ItemReference / Memory 顶层（metadata + spec + status）。
MemorySpec + MemoryStatus + ScopeReference + AgentReference 从 operator 复用，
保持与 L4 Step 1 落地实现一致。
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from superteam_a2a.operator.models.memory import (
    MemorySpec,
    MemoryStatus,
)

# ============================================================================
# DNS / Label 正则（§3.2 ObjectMeta）
# ============================================================================

DNS_LABEL = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
LABEL_KEY = re.compile(
    r"^([a-zA-Z0-9]([-a-zA-Z0-9_.]*[a-zA-Z0-9])?)/([a-zA-Z0-9]([-a-zA-Z0-9_.]*[a-zA-Z0-9])?)$"
)
LABEL_VALUE = re.compile(r"^(([a-zA-Z0-9]([-a-zA-Z0-9_.]*[a-zA-Z0-9])?)?)$")


# ============================================================================
# §3.2 ObjectMeta
# ============================================================================


class ObjectMeta(BaseModel):
    """K8s-style metadata（§3.2 line 399-423）。"""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    name: str = Field(min_length=1, max_length=253)
    namespace: str = Field(default="default", min_length=1, max_length=253)
    labels: dict[str, str] = Field(default_factory=dict, max_length=64)
    annotations: dict[str, str] = Field(default_factory=dict, max_length=64)
    generation: int = Field(default=1, ge=1)
    creation_timestamp: AwareDatetime | None = Field(default=None, alias="creationTimestamp")
    finalizers: tuple[str, ...] = ()

    @field_validator("name", "namespace")
    @classmethod
    def valid_dns_label(cls, value: str) -> str:
        if not DNS_LABEL.fullmatch(value):
            raise ValueError("must be a lowercase DNS-1123 label")
        return value

    @field_validator("labels")
    @classmethod
    def valid_labels(cls, value: dict[str, str]) -> dict[str, str]:
        for k in value:
            if len(k) > 253 or not LABEL_KEY.fullmatch(k):
                raise ValueError(f"invalid Kubernetes label key: {k!r}")
        for v in value.values():
            if len(v) > 63 or not LABEL_VALUE.fullmatch(v):
                raise ValueError(f"invalid Kubernetes label value: {v!r}")
        return value


# ============================================================================
# §3.3 ItemReference
# ============================================================================


class ItemReference(BaseModel):
    """ItemReference（§3.3 line 441-444）· KnowledgeItem 引用。"""

    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(min_length=1, max_length=253)
    namespace: str | None = Field(default=None, min_length=1, max_length=253)


# ============================================================================
# §3.4 Memory 顶层
# ============================================================================


class Memory(BaseModel):
    """Memory 顶层 CRD（§3.4 line 573-581）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    api_version: Literal["memory.superteam-a2a.io/v1alpha1"] = Field(
        default="memory.superteam-a2a.io/v1alpha1", alias="apiVersion"
    )
    kind: Literal["Memory"] = "Memory"
    metadata: ObjectMeta
    spec: MemorySpec
    status: MemoryStatus | None = None


# ============================================================================
# canonical_key · §5.3-§5.5 内部 key 函数
# ============================================================================


def canonical_key(memory: Memory) -> tuple[str, str]:
    """Memory 的 canonical key = (namespace, name)。

    §5.3 PUT / §5.4 GET / §5.5 DELETE 均使用 (namespace, name) 作为 key。
    """
    return (memory.metadata.namespace, memory.metadata.name)


def canonical_key_parts(namespace: str, name: str) -> tuple[str, str]:
    """§5.4 GET / §5.5 DELETE 的 key 构造（直接传 namespace/name）。"""
    return (namespace, name)


__all__ = [
    "DNS_LABEL",
    "LABEL_KEY",
    "LABEL_VALUE",
    "ItemReference",
    "Memory",
    "ObjectMeta",
    "canonical_key",
    "canonical_key_parts",
]
