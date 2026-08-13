"""3 Pydantic v2 model_validator 入参校验 · VAL-UT-001~003.

PR-4a v0.2-draft 实装 · #111

注：plan §2.3 标注为「async validators」，实装为 sync（Pydantic v2.13 不支持
async model_validator 在 __init__ 路径自动 await — 必须通过 model_validate_async
且当前版本无此方法）。本测试覆盖 validator 行为的 sync 版本。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from superteam_a2a.knowledge.errors.codes import KnowledgeContractError
from superteam_a2a.knowledge.validation.validators import (
    ConfidenceDecayValidator,
    ContentValidator,
    VisibilityScopeValidator,
)


def _extract_knowledge_error(exc: BaseException) -> KnowledgeContractError | None:
    """从 Pydantic ValidationError 中提取嵌套的 KnowledgeContractError。"""
    if isinstance(exc, KnowledgeContractError):
        return exc
    if isinstance(exc, ValidationError):
        for err in exc.errors():
            ctx_err = err.get("ctx", {}).get("error")
            if isinstance(ctx_err, KnowledgeContractError):
                return ctx_err
            cause = err.get("ctx", {}).get("exception")
            if isinstance(cause, KnowledgeContractError):
                return cause
    cur: BaseException | None = exc
    while cur is not None:
        if isinstance(cur, KnowledgeContractError):
            return cur
        cur = cur.__cause__
    return None


# VAL-UT-001 · ContentValidator
def test_content_validator_accepts_short_content():
    """VAL-UT-001 (Part 1) · 短 content 通过。"""
    v = ContentValidator(content={"key": "value"})
    assert v.content == {"key": "value"}


def test_content_validator_accepts_short_string():
    """VAL-UT-001 (Part 2) · 字符串 content ≤ 65536 通过。"""
    v = ContentValidator(content="x" * 1000)
    assert isinstance(v.content, str)
    assert len(v.content) == 1000


def test_content_validator_accepts_none():
    """VAL-UT-001 (Part 3) · None content 通过。"""
    v = ContentValidator()
    assert v.content is None


def test_content_validator_rejects_too_many_keys():
    """VAL-UT-001 (Part 4) · content keys > 20 → KNOWLEDGE_QUERY_TOO_LONG。"""
    content = {f"k{i}": "v" for i in range(21)}
    with pytest.raises(KnowledgeContractError) as exc_info:
        ContentValidator(content=content)
    assert exc_info.value.code.name == "KNOWLEDGE_QUERY_TOO_LONG"


def test_content_validator_rejects_long_value():
    """VAL-UT-001 (Part 5) · content value > 4096 → KNOWLEDGE_QUERY_TOO_LONG。"""
    content = {"key": "x" * 4097}
    with pytest.raises(KnowledgeContractError) as exc_info:
        ContentValidator(content=content)
    assert exc_info.value.code.name == "KNOWLEDGE_QUERY_TOO_LONG"


def test_content_validator_rejects_long_string():
    """VAL-UT-001 (Part 6) · content string > 65536 → KNOWLEDGE_QUERY_TOO_LONG。"""
    with pytest.raises(KnowledgeContractError) as exc_info:
        ContentValidator(content="x" * 65537)
    assert exc_info.value.code.name == "KNOWLEDGE_QUERY_TOO_LONG"


def test_content_validator_rejects_too_many_list_items():
    """VAL-UT-001 (Part 7) · content list items > 20 → KNOWLEDGE_QUERY_TOO_LONG。"""
    with pytest.raises(KnowledgeContractError) as exc_info:
        ContentValidator(content=list(range(21)))
    assert exc_info.value.code.name == "KNOWLEDGE_QUERY_TOO_LONG"


# VAL-UT-002 · ConfidenceDecayValidator
def test_confidence_decay_accepts_high_confidence_short_decay():
    """VAL-UT-002 (Part 1) · confidence ≥ 0.9 + decay_days ≤ 365 通过。"""
    v = ConfidenceDecayValidator(confidence=0.95, decay_days=180)
    assert v.confidence == 0.95
    assert v.decay_days == 180


def test_confidence_decay_accepts_low_confidence_long_decay():
    """VAL-UT-002 (Part 2) · confidence < 0.9 + decay_days ≤ 3650 通过。"""
    v = ConfidenceDecayValidator(confidence=0.5, decay_days=1000)
    assert v.decay_days == 1000


def test_confidence_decay_accepts_defaults():
    """VAL-UT-002 (Part 3) · 默认值 confidence=1.0 + decay_days=30 通过。"""
    v = ConfidenceDecayValidator()
    assert v.confidence == 1.0
    assert v.decay_days == 30


def test_confidence_decay_rejects_high_confidence_long_decay():
    """VAL-UT-002 (Part 4) · confidence ≥ 0.9 + decay_days > 365 → KNOWLEDGE_INTERNAL_ERROR。"""
    with pytest.raises(KnowledgeContractError) as exc_info:
        ConfidenceDecayValidator(confidence=0.95, decay_days=500)
    assert exc_info.value.code.name == "KNOWLEDGE_INTERNAL_ERROR"


def test_confidence_decay_rejects_low_confidence_long_decay():
    """VAL-UT-002 (Part 5) · confidence < 0.9 + decay_days > 3650 → KNOWLEDGE_INTERNAL_ERROR。"""
    with pytest.raises(KnowledgeContractError) as exc_info:
        ConfidenceDecayValidator(confidence=0.5, decay_days=4000)
    assert exc_info.value.code.name == "KNOWLEDGE_INTERNAL_ERROR"


# VAL-UT-003 · VisibilityScopeValidator
def test_visibility_scope_accepts_public_industry():
    """VAL-UT-003 (Part 1) · visibility=public-readable + scope.level=industry 通过。"""
    v = VisibilityScopeValidator(visibility="public-readable", scope_level="industry")
    assert v.visibility == "public-readable"


def test_visibility_scope_accepts_agent_private_agent():
    """VAL-UT-003 (Part 2) · visibility=agent-private + scope.level=agent 通过。"""
    v = VisibilityScopeValidator(visibility="agent-private", scope_level="agent")
    assert v.scope_level == "agent"


def test_visibility_scope_accepts_scope_only():
    """VAL-UT-003 (Part 3) · 默认 scope-only + 任意 scope_level 通过。"""
    v = VisibilityScopeValidator()
    assert v.visibility == "scope-only"


def test_visibility_scope_rejects_public_non_industry():
    """VAL-UT-003 (Part 4) · visibility=public-readable + scope.level ≠ industry →
    KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY (-32015)。
    """
    with pytest.raises(KnowledgeContractError) as exc_info:
        VisibilityScopeValidator(visibility="public-readable", scope_level="agent")
    assert exc_info.value.code.name == "KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY"


def test_visibility_scope_rejects_agent_private_non_agent():
    """VAL-UT-003 (Part 5) · visibility=agent-private + scope.level ≠ agent →
    KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS (-32016)。
    """
    with pytest.raises(KnowledgeContractError) as exc_info:
        VisibilityScopeValidator(visibility="agent-private", scope_level="team")
    assert exc_info.value.code.name == "KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS"
