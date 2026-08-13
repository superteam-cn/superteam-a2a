"""L3-5 §5.1 入参校验 · 3 个 Pydantic v2 model_validator.

依据 L3-5 Spec §5.1 入参校验要求 + L3-5 §8.1 line 1808-1822 错误码权威映射。
PR-4a v0.2-draft 实装 · #111

不变量：
- 三个 validator 都用 @model_validator(mode="after") 同步校验
  （Pydantic v2 不支持 async model_validator；plan §2.3 的「async」指 validator 入口
  调用语义，不是 Pydantic 内部 async — 实装为 sync 函数以保证 __init__ 路径生效）
- 验证失败抛出 KnowledgeContractError(code=..., message=...) 携带对应 KNOWLEDGE_* 错误码
- 校验通过返回 self（不变）
- validators.py 集中实现，便于 PR-4b handler 复用
"""

from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, model_validator
from superteam_a2a.knowledge.errors.codes import (
    KnowledgeContractError,
    KnowledgeErrorCode,
)

# ============================================================================
# 1. ContentValidator · content 字段数 ≤ 20 + 每个 value 字符串长度 ≤ 4096
# ============================================================================


class ContentValidator(BaseModel):
    """L3-5 §5.1 内容字段校验（content keys ≤ 20 + value 长度 ≤ 4096）。

    验证失败 → KnowledgeContractError(KNOWLEDGE_QUERY_TOO_LONG, ...)
    """

    model_config = {"extra": "forbid", "populate_by_name": True}

    content: dict[str, Any] | str | list[Any] | None = None

    @model_validator(mode="after")
    def _validate_content(self) -> Self:
        if self.content is None:
            return self
        if isinstance(self.content, dict):
            if len(self.content) > 20:
                raise KnowledgeContractError(
                    KnowledgeErrorCode.KNOWLEDGE_QUERY_TOO_LONG,
                    f"content keys count > 20 (got {len(self.content)})",
                )
            for k, v in self.content.items():
                if isinstance(v, str) and len(v) > 4096:
                    raise KnowledgeContractError(
                        KnowledgeErrorCode.KNOWLEDGE_QUERY_TOO_LONG,
                        f"content['{k}'] value length > 4096 (got {len(v)})",
                    )
        elif isinstance(self.content, str):
            if len(self.content) > 65536:
                raise KnowledgeContractError(
                    KnowledgeErrorCode.KNOWLEDGE_QUERY_TOO_LONG,
                    f"content string length > 65536 (got {len(self.content)})",
                )
        elif isinstance(self.content, list):
            if len(self.content) > 20:
                raise KnowledgeContractError(
                    KnowledgeErrorCode.KNOWLEDGE_QUERY_TOO_LONG,
                    f"content list items > 20 (got {len(self.content)})",
                )
        return self


# ============================================================================
# 2. ConfidenceDecayValidator · confidence × decay_days 数学一致性
# ============================================================================


class ConfidenceDecayValidator(BaseModel):
    """L3-5 §5.1 confidence × decay_days 校验。

    规则：confidence ≥ 0.9 → decay_days ≤ 365；< 0.9 → ≤ 3650
    """

    model_config = {"extra": "forbid", "populate_by_name": True}

    confidence: float = 1.0
    decay_days: int = 30

    @model_validator(mode="after")
    def _validate_confidence_decay(self) -> Self:
        if self.confidence >= 0.9 and self.decay_days > 365:
            raise KnowledgeContractError(
                KnowledgeErrorCode.KNOWLEDGE_INTERNAL_ERROR,
                f"confidence >= 0.9 requires decay_days <= 365 (got {self.decay_days})",
            )
        if self.confidence < 0.9 and self.decay_days > 3650:
            raise KnowledgeContractError(
                KnowledgeErrorCode.KNOWLEDGE_INTERNAL_ERROR,
                f"confidence < 0.9 requires decay_days <= 3650 (got {self.decay_days})",
            )
        return self


# ============================================================================
# 3. VisibilityScopeValidator · visibility 与 scope_ref.level 一致性
# ============================================================================


class VisibilityScopeValidator(BaseModel):
    """L3-5 §5.1 visibility × scope.level 校验。

    规则：
    - visibility=public-readable → scope.level=industry ·
      违反 → KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY (-32015)
    - visibility=agent-private → scope.level=agent ·
      违反 → KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS (-32016) (v0.5+ 才支持)
    """

    model_config = {"extra": "forbid", "populate_by_name": True}

    visibility: str = "scope-only"
    scope_level: str = "agent"

    @model_validator(mode="after")
    def _validate_visibility_scope(self) -> Self:
        if self.visibility == "public-readable" and self.scope_level != "industry":
            raise KnowledgeContractError(
                KnowledgeErrorCode.KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY,
                f"visibility=public-readable requires scope.level=industry (got {self.scope_level})",
            )
        if self.visibility == "agent-private" and self.scope_level != "agent":
            raise KnowledgeContractError(
                KnowledgeErrorCode.KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS,
                f"visibility=agent-private requires scope.level=agent (got {self.scope_level})",
            )
        return self


__all__ = [
    "ConfidenceDecayValidator",
    "ContentValidator",
    "VisibilityScopeValidator",
]
