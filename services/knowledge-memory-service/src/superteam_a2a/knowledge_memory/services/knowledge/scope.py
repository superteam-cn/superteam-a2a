"""KnowledgeScopeService · Protocol stub + 基礎校驗 · 4 級 scope 實裝推 PR-4c。

依據 PR-4b plan §1 明確剔除：
- ❌ 4 級 scope resolver 業務邏輯（parent_ref 解析 + chain 遍歷）→ PR-4c

service 職責：
- validate_scope 接收 scope_ref（ScopeReference）
- 復用 PR-4a 已實裝的 VisibilityScopeValidator 做基礎校驗
  （visibility=public-readable → scope.level=industry /
   visibility=agent-private → scope.level=agent）
- 4 級 scope 解析（parent_ref 解析 + chain 遍歷）拋 NotImplementedError

ISP：Protocol 僅暴露 validate_scope 方法。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from superteam_a2a.knowledge.validation.validators import VisibilityScopeValidator


@runtime_checkable
class KnowledgeScopeServiceProtocol(Protocol):
    """Knowledge scope 校驗 Protocol · ISP 最小接口。"""

    async def validate_scope(
        self,
        scope_ref: Any,
        *,
        visibility: str,
    ) -> None: ...


class KnowledgeScopeService:
    """KnowledgeScopeService stub + 基礎校驗 · PR-4b 階段實裝。

    行為：
    - validate_scope 接收 scope_ref（ScopeReference） + visibility（str）
    - 復用 PR-4a VisibilityScopeValidator 做基礎校驗（raise KnowledgeContractError）
    - 4 級 scope 解析（parent_ref 解析 + chain 遍歷）拋 NotImplementedError

    PR-4c 實裝要點：
    1. scope.parent_ref BFS 解析（KnowledgeMemoryMutexValidator.detect_scope_ref_cycle 復用）
    2. max_depth=8 限制
    3. 命中自身 → 環檢測
    4. 命中不存在 parent → KNOWLEDGE_SCOPE_NOT_FOUND
    """

    async def validate_scope(
        self,
        scope_ref: Any,
        *,
        visibility: str,
    ) -> None:
        """校驗 Knowledge scope · 復用 PR-4a VisibilityScopeValidator + 4 級解析 stub。

        參數：
        - scope_ref · ScopeReference（含 name + level）
        - visibility · str（"public-readable" / "scope-only" / "scope-and-children" / "agent-private"）

        異常：
        - KnowledgeContractError(KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY / KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS)
          · VisibilityScopeValidator 校驗失敗
        - NotImplementedError · 4 級 scope 解析（PR-4c 實裝）

        PR-4a 已實裝的 VisibilityScopeValidator（位於
        packages/knowledge/src/superteam_a2a/knowledge/validation/validators.py）
        是本 service 的基礎校驗複用組件。
        """
        # 步驟 1：復用 PR-4a VisibilityScopeValidator 做基礎校驗（拋 KnowledgeContractError）
        level = getattr(scope_ref, "level", "agent") if scope_ref is not None else "agent"
        VisibilityScopeValidator(visibility=visibility, scope_level=level or "agent")

        # 步驟 2：4 級 scope 解析（PR-4c 實裝）
        raise NotImplementedError(
            "KnowledgeScopeService 4-level scope resolution is PR-4c scope "
            "(PR-4a VisibilityScopeValidator 基礎校驗已實裝)"
        )


__all__ = [
    "KnowledgeScopeService",
    "KnowledgeScopeServiceProtocol",
]
