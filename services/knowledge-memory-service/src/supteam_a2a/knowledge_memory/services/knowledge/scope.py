"""KnowledgeScopeService · 完整实装 · 4 级 scope 解析.

依据 PR-4c plan §2.3 + L3-5 §3.1 + ADR-0002 §3.1。

Service 完整实装要点：
1. validate_scope(scope_ref, *, visibility) · 复 PR-4a VisibilityScopeValidator 基础校验
2. 4 级 scope 解析（chain 遍历）via ScopeResolver（PR-4c 复用）
3. parent_ref 严格 1 级递增（system → workflow → agentset → agent）

PR-4b 阶段的 NotImplementedError 已替换为完整实装（PR-4c）。

宪法 §17 SOLID：
- SRP：本 service 仅负责 Knowledge scope 校验 + 4 级解析入口
- DIP：依赖 ScopeResolver + VisibilityScopeValidator（PR-4a）+ ScopeCache Protocol
- ISP：KnowledgeScopeServiceProtocol 仅暴露 validate_scope 方法
- CRP：构造参数 cache + validator + resolver 注入
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from superteam_a2a.knowledge.crd.scope_level import ScopeLevel
from superteam_a2a.knowledge.errors.codes import KnowledgeContractError
from superteam_a2a.knowledge.validation.validators import VisibilityScopeValidator
from superteam_a2a.knowledge_memory.scope_resolver import (
    ScopeCache,
    ScopeResolver,
)


@runtime_checkable
class KnowledgeScopeServiceProtocol(Protocol):
    """Knowledge scope 校验 Protocol · ISP 最小接口."""

    async def validate_scope(
        self,
        scope_ref: Any,
        *,
        visibility: str,
    ) -> None: ...


class KnowledgeScopeService:
    """KnowledgeScopeService 完整实装（PR-4c）.

    行为：
    - validate_scope(scope_ref, *, visibility)
      1. 复用 PR-4a VisibilityScopeValidator 做基础校验（visibility vs scope.level）
      2. 4 级 scope 解析：ScopeResolver.validate_parent 验证 child_level vs parent_level
      3. 命中 scope self-reference → KnowledgeContractError(KNOWLEDGE_OWNER_KIND_FORBIDDEN)
      4. 命中不存在 parent → KnowledgeContractError(KNOWLEDGE_SCOPE_NOT_FOUND)

    构造参数：
    - scope_cache · ScopeCache · PR-4c 实装协议
    - resolver · ScopeResolver · 默认 None（自动用 cache 构造）

    异常：
    - KnowledgeContractError(KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY / KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS)
      · VisibilityScopeValidator 基础校验失败
    - KnowledgeContractError(KNOWLEDGE_SCOPE_NOT_FOUND) · parent 不存在
    - KnowledgeContractError(KNOWLEDGE_OWNER_KIND_FORBIDDEN) · 严格 1 级递增违反 / 环
    """

    def __init__(
        self,
        scope_cache: ScopeCache,
        *,
        resolver: ScopeResolver | None = None,
    ) -> None:
        """构造注入.

        参数：
        - scope_cache · ScopeCache Protocol · 4 级 scope 缓存
        - resolver · ScopeResolver 可选 · 默认 None（自动用 cache 构造）
        """
        self._cache = scope_cache
        self._resolver = resolver if resolver is not None else ScopeResolver(scope_cache)

    async def validate_scope(
        self,
        scope_ref: Any,
        *,
        visibility: str,
    ) -> None:
        """校验 Knowledge scope · 基础校验 + 4 级解析完整实装.

        参数：
        - scope_ref · ScopeReference（含 name + level）+ 可选 parent_ref 用于严格 1 级校验
        - visibility · str（"public-readable" / "scope-only" / "scope-and-children" / "agent-private" /
                  "system-readonly"）

        异常：
        - KnowledgeContractError · VisibilityScopeValidator / 4 级解析校验失败
        """
        # 步骤 1：复用 PR-4a VisibilityScopeValidator 做基础校验（抛 KnowledgeContractError）
        level = getattr(scope_ref, "level", "agent") if scope_ref is not None else "agent"
        VisibilityScopeValidator(visibility=visibility, scope_level=level or "agent")

        # 步骤 2：4 级 scope 严格 1 级解析
        # 2.1：scope_ref.parent_ref 存在 → 验证 child_level vs parent_level 严格 1 级
        spec = getattr(scope_ref, "spec", None) if hasattr(scope_ref, "spec") else None
        parent_ref = (
            getattr(spec, "parent_ref", None)
            if spec is not None
            else getattr(scope_ref, "parent_ref", None)
        )
        if parent_ref is not None:
            child_level_raw = level if level is not None else ScopeLevel.AGENT
            parent_level = getattr(parent_ref, "level", None)
            if not self._resolver.validate_parent(child_level_raw, parent_level):
                raise KnowledgeContractError(
                    _strict_one_level_code(level, parent_level),
                    f"scope parent_ref violates strict 1-level increment: "
                    f"child={child_level_raw} parent={parent_level}",
                )

        # 2.2：resolve_chain(scope_ref.name) → chain 遍历（4 级校验 + self-reference + max_depth）
        scope_name = getattr(scope_ref, "name", None)
        if scope_name:
            try:
                self._resolver.resolve_chain(scope_name)
            except KnowledgeContractError:
                # resolve_chain 内部已经抛出正确的错误码（KNOWLEDGE_SCOPE_NOT_FOUND /
                # KNOWLEDGE_OWNER_KIND_FORBIDDEN），直接透传
                raise


def _strict_one_level_code(
    child_level: Any,
    parent_level: Any,
) -> Any:
    """根据 child/parent level 关系返回适合的 KNOWLEDGE_* 错误码.

    - parent_level=None（仅 SYSTEM 合法）+ child != SYSTEM → KNOWLEDGE_OWNER_KIND_FORBIDDEN
    - 反向跨级 → KNOWLEDGE_OWNER_KIND_FORBIDDEN
    """
    # 延迟导入避免循环
    from superteam_a2a.knowledge.errors.codes import KnowledgeErrorCode

    return KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN


__all__ = [
    "KnowledgeScopeService",
    "KnowledgeScopeServiceProtocol",
]
