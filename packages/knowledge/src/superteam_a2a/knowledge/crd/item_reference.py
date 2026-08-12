"""ItemReference value object · L3-5 §3.2."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ItemReference(BaseModel):
    """KnowledgeItem 不可变引用（frozen · 含 version 用于 supersededBy 链）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    name: str = Field(min_length=1, max_length=253)
    version: int = Field(ge=1)
