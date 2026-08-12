"""ScopeReference value object · L3-5 §3.1."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from superteam_a2a.knowledge.crd.scope_level import ScopeLevel


class ScopeReference(BaseModel):
    """KnowledgeScope 不可变引用（frozen · 含可选 level 冗余缓存）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str = Field(min_length=1, max_length=253)
    level: ScopeLevel | None = None
