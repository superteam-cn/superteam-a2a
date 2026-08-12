"""InheritRules value object · L3-5 §3.1."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from superteam_a2a.knowledge.crd.scope_level import ScopeLevel


class InheritRules(BaseModel):
    """4 级 scope 继承过滤规则（admission webhook 强制）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    include_types: list[str] | None = Field(default=None, max_length=11, alias="includeTypes")
    exclude_types: list[str] | None = Field(default=None, max_length=11, alias="excludeTypes")
    allowed_child_levels: list[ScopeLevel] = Field(default_factory=list, alias="allowedChildLevels")
    max_depth: int = Field(default=3, ge=0, le=3, alias="maxDepth")
    block_self_reference: bool = Field(default=False, alias="blockSelfReference")
