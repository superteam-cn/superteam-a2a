"""H-QK-UT-002 · KnowledgeScopeService 復用 PR-4a VisibilityScopeValidator。

驗證：
1. visibility=public-readable + scope.level=industry → 通過基礎校驗
2. visibility=public-readable + scope.level!=industry → 拋 KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY
3. visibility=agent-private + scope.level=agent → 通過基礎校驗
4. 4 級 scope 解析拋 NotImplementedError

依據 PR-4b plan §7 H-QK-UT-002 + PR-4a VisibilityScopeValidator。
"""

from __future__ import annotations

from typing import NamedTuple

import pytest
from superteam_a2a.knowledge.errors.codes import (
    KnowledgeContractError,
    KnowledgeErrorCode,
)
from superteam_a2a.knowledge_memory.services.knowledge.scope import (
    KnowledgeScopeService,
)


class _ScopeRef(NamedTuple):
    """測試用 ScopeReference 替身。"""

    name: str
    level: str


async def test_knowledge_scope_service_validates_via_pydantic_industry() -> None:
    """H-QK-UT-002a · visibility=public-readable + scope.level=industry → � NotImplementedError（4 級解析 stub）。

    期望：
    1. VisibilityScopeValidator 基礎校驗通過（public-readable → industry 符合規則）
    2. 4 級 scope 解析拋 NotImplementedError（PR-4c scope）
    """
    service = KnowledgeScopeService()
    scope = _ScopeRef(name="industry-ai", level="industry")

    with pytest.raises(NotImplementedError) as exc_info:
        await service.validate_scope(scope, visibility="public-readable")
    assert "PR-4c scope" in str(exc_info.value)


async def test_knowledge_scope_service_rejects_public_requires_industry() -> None:
    """H-QK-UT-002b · visibility=public-readable + scope.level!=industry → 拋 KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY。

    期望：
    1. VisibilityScopeValidator 基礎校驗失敗
    2. 拋 KnowledgeContractError(KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY)
    """
    service = KnowledgeScopeService()
    scope = _ScopeRef(name="scope-1", level="scope")  # level=scope 違反 public-readable 規則

    with pytest.raises(KnowledgeContractError) as exc_info:
        await service.validate_scope(scope, visibility="public-readable")
    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY


async def test_knowledge_scope_service_rejects_agent_private_requires_agent() -> None:
    """H-QK-UT-002c · visibility=agent-private + scope.level!=agent → 拋 KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS。"""
    service = KnowledgeScopeService()
    scope = _ScopeRef(name="scope-1", level="scope")  # level=scope 違反 agent-private 規則

    with pytest.raises(KnowledgeContractError) as exc_info:
        await service.validate_scope(scope, visibility="agent-private")
    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS


__all__ = [
    "test_knowledge_scope_service_rejects_agent_private_requires_agent",
    "test_knowledge_scope_service_rejects_public_requires_industry",
    "test_knowledge_scope_service_validates_via_pydantic_industry",
]
