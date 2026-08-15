"""4 级 scope resolver 主类 · system → workflow → agentset → agent 严格 1 级递增.

PR-4c plan §2.3 · L3-5 §3.1 + L3-6 §3 + ADR-0002 §3.1。

不变量：
- parent_ref 必须严格递增 1 级（system → workflow → agentset → agent）
- self-reference 检测（block_self_reference=true · L3-5 §3.1 inheritRules）
- max_depth 默认 3（L3-5 §3.1 inheritRules · 防止过深继承）
- scope 缓存通过 ScopeCache Protocol 注入（PR-4c 内存实现 · K8s 实装推 PR-5）

注意：KnowledgeScope 模型 metadata 由 K8s API server 注入（运行时 dict-like），
本模块接受既有调用风格：scope.metadata.name 通过 getattr 防御式访问（Pydantic
model_config extra="forbid" 限制 + K8s 实际 K8s object 通过 metadata 暴露名字）。
实际 K8s object 通过 Kopf / kubernetes-client 包装层暴露 metadata attributes。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from superteam_a2a.knowledge.crd.knowledgescope import KnowledgeScope
from superteam_a2a.knowledge.crd.scope_level import ScopeLevel
from superteam_a2a.knowledge.errors.codes import (
    KnowledgeContractError,
    KnowledgeErrorCode,
)
from superteam_a2a.knowledge_memory.scope_resolver.chain import traverse_scope_chain

# ============================================================================
# 严格 1 级递增约束（L3-5 §3.1 + ADR-0002 §3.1）
# ============================================================================

# child_level → expected parent_level（必须严格 1 级递增 · WireContract 零漂移）
_STRICT_INCREMENT: dict[ScopeLevel, ScopeLevel] = {
    ScopeLevel.AGENT: ScopeLevel.AGENT_SET,
    ScopeLevel.AGENT_SET: ScopeLevel.WORKFLOW,
    ScopeLevel.WORKFLOW: ScopeLevel.SYSTEM,
    # ScopeLevel.SYSTEM 没有 parent（顶层 · parent_ref=None 强制）
}


def _scope_name(scope: KnowledgeScope) -> str:
    """从 K8s object 提取 scope name · 防御式 getattr 访问 metadata.name."""
    metadata = getattr(scope, "metadata", None)
    if metadata is not None:
        name = getattr(metadata, "name", None)
        if name:
            return str(name)
    spec = getattr(scope, "spec", None)
    spec_name = getattr(spec, "name", None) if spec is not None else None
    if spec_name:
        return str(spec_name)
    raise KnowledgeContractError(
        KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND,
        "scope has no resolvable name (metadata.name and spec.name both empty)",
    )


@runtime_checkable
class ScopeCache(Protocol):
    """4 级 scope 缓存接口 Protocol（L3-5-followup-4 _SCOPE_CACHE 占位）.

    使用 typing.Protocol + ellipsis marker 而非 ABC。
    优势：
    - 避免 pyright reportImplicitOverride（Protocol 接口方法天然 abstract）
    - 单元测试可使用任何 duck-typed 实现
    """

    def get(self, scope_name: str) -> KnowledgeScope | None:
        """获取 scope by name · 返回 None 表示缓存未命中."""
        ...

    def add(self, scope: KnowledgeScope) -> None:
        """添加 scope 到缓存（unit test 装填用）."""
        ...


class InMemoryScopeCache:
    """内存实现 · dict-backed scope cache（满足 ScopeCache protocol）。

    单元测试用 · 生产环境用 K8s client 注入（PR-5 实装）。

    LSP：满足 ScopeCache Protocol · 可替换为 K8s 实现。
    """

    def __init__(self) -> None:
        self._scopes: dict[str, KnowledgeScope] = {}

    def add(self, scope: KnowledgeScope) -> None:
        """添加 scope 到 dict 缓存（O(1)）。"""
        self._scopes[_scope_name(scope)] = scope

    def get(self, scope_name: str) -> KnowledgeScope | None:
        """dict lookup · O(1) · 未命中返回 None。"""
        return self._scopes.get(scope_name)


class ScopeResolver:
    """4 级 scope resolver 主类 · 严格 1 级递增 + chain 遍历 + cache 查询."""

    def __init__(self, scope_cache: ScopeCache) -> None:
        self._cache = scope_cache

    def validate_parent(
        self,
        child_level: ScopeLevel,
        parent_level: ScopeLevel | None,
    ) -> bool:
        """验证 parent_ref 严格递增 1 级.

        Returns True if parent_ref is strictly one level above child:
            (WORKFLOW, SYSTEM)     → True
            (AGENT_SET, WORKFLOW)  → True
            (AGENT, AGENT_SET)     → True
            (SYSTEM, None)         → True (root)
            (SYSTEM, SYSTEM)       → False (same level)
            (AGENT, WORKFLOW)      → False (cross-level)
            (AGENT, None)          → False (non-system must have parent)
        """
        if parent_level is None:
            return child_level == ScopeLevel.SYSTEM
        expected_parent = _STRICT_INCREMENT.get(child_level)
        return expected_parent is not None and expected_parent == parent_level

    def resolve_chain(
        self,
        scope_name: str,
        *,
        max_depth: int = 3,
        block_self_reference: bool = True,
    ) -> list[str]:
        """返回 scope 继承链 [system, workflow, agentset, agent] 等."""
        start_scope = self.resolve_scope(scope_name)
        return traverse_scope_chain(
            start_scope,
            scope_cache=self._cache,
            max_depth=max_depth,
            block_self_reference=block_self_reference,
        )

    def resolve_scope(self, scope_name: str) -> KnowledgeScope:
        """获取 scope by name · 缓存未命中 raise KNOWLEDGE_SCOPE_NOT_FOUND."""
        scope: Any = self._cache.get(scope_name)
        if scope is None:
            raise KnowledgeContractError(
                KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND,
                f"scope {scope_name} not found in scope cache",
            )
        return scope  # type: ignore[return-value]


__all__ = [
    "InMemoryScopeCache",
    "ScopeCache",
    "ScopeResolver",
]
