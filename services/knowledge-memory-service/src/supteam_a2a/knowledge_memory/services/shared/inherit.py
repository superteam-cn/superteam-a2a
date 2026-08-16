"""InheritService · 完整实装 · 4 级 scope 继承规则.

依据 PR-4c plan §2.3 + L3-5 §3.1 + L3-5 §5.5 4 级 scope 继承 + ADR-0002 §3.1。

4 级 scope 继承规则：
1. agent（葉節點）→ 不向上繼承
2. agentset（單個 agentset）→ 向上繼承到 workflow
3. workflow（單個 workflow）→ 向上繼承到 system
4. system（頂層）→ 不向上繼承（parent_ref=None）

parent_ref BFS + chain 遍历完整实装：
1. 从 scope_ref 開始 BFS 上溯（PR-4c traverse_scope_chain）
2. max_depth=3 限制（L3-5 §3.1 inheritRules.max_depth=3）
3. 命中自身 → KNOWLEDGE_OWNER_KIND_FORBIDDEN（環檢測）
4. 命中不存在 parent → KNOWLEDGE_SCOPE_NOT_FOUND
5. 返回 [scope_ref, parent1, parent2, ..., root] 鏈

PR-4b 阶段的 NotImplementedError 已替换为完整实装（PR-4c）。

宪法 §17 SOLID：
- SRP：本 service 仅负责 scope 继承链解析入口
- DIP：依赖 traverse_scope_chain + ScopeCache Protocol（scope_resolver 模块）
- ISP：InheritServiceProtocol 仅暴露 resolve_inherit_chain 方法
- CRP：构造参数 cache + max_depth 注入
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from superteam_a2a.knowledge_memory.scope_resolver import (
    ScopeCache,
    ScopeResolver,
    traverse_scope_chain,
)


@runtime_checkable
class InheritServiceProtocol(Protocol):
    """Scope 继承解析 Protocol · ISP 最小接口."""

    async def resolve_inherit_chain(
        self,
        scope_ref: Any,
    ) -> list[Any]:  # list[ScopeRef]
        ...


class InheritService:
    """InheritService 完整实装（PR-4c）.

    行为：
    - resolve_inherit_chain(scope_ref) · 4 级 scope 继承链解析
      1. scope_cache.get(scope_ref.name) 拿到起始 KnowledgeScope
      2. traverse_scope_chain(scope, scope_cache=cache, max_depth=3, block_self_reference=True)
      3. 返回 [scope_ref, parent1, parent2, ..., root] name chain

    构造参数：
    - scope_cache · ScopeCache · 4 级 scope 缓存（PR-4c 协议）
    - resolver · ScopeResolver 可选 · 默认 None（自动 cache 构造）

    返回：list[str] · scope 名继承链

    异常：
    - KnowledgeContractError(KNOWLEDGE_SCOPE_NOT_FOUND) · scope 或 parent 不存在
    - KnowledgeContractError(KNOWLEDGE_OWNER_KIND_FORBIDDEN) · cycle / max_depth 越界
    """

    def __init__(
        self,
        scope_cache: ScopeCache,
        *,
        resolver: ScopeResolver | None = None,
        max_depth: int = 3,
        block_self_reference: bool = True,
    ) -> None:
        """构造注入.

        参数：
        - scope_cache · ScopeCache Protocol
        - resolver · ScopeResolver 可选 · 默认 None（自动用 cache 构造）
        - max_depth · int · 默认 3（L3-5 §3.1 inheritRules.max_depth）
        - block_self_reference · bool · 默认 True（cycle 检测）
        """
        self._cache = scope_cache
        self._resolver = resolver if resolver is not None else ScopeResolver(scope_cache)
        self._max_depth = max_depth
        self._block_self_reference = block_self_reference

    async def resolve_inherit_chain(
        self,
        scope_ref: Any,
    ) -> list[Any]:
        """解析 scope 继承链 · 完整实装.

        参数：
        - scope_ref · ScopeReference（含 name）· 起点 scope 引用

        返回：
        - list[str] · 完整 scope 名字 chain（从起点到 root）

        算法：
        1. scope_cache.get(scope_ref.name) → 起点 KnowledgeScope
        2. traverse_scope_chain(scope, scope_cache=cache, max_depth=3)
        3. 返回 chain（[起点, parent1, parent2, ..., root]）

        异常：
        - KnowledgeContractError(KNOWLEDGE_SCOPE_NOT_FOUND) · scope 不存在
        - KnowledgeContractError(KNOWLEDGE_OWNER_KIND_FORBIDDEN) · cycle / max_depth 越界
        """
        # 步驟 1：cache 查询（miss → KNOWLEDGE_SCOPE_NOT_FOUND）
        scope_name = getattr(scope_ref, "name", None)
        if scope_name is None:
            # 退路：传入 scope 对象本身
            scope_name = getattr(getattr(scope_ref, "metadata", None), "name", None)
        if not scope_name:
            from superteam_a2a.knowledge.errors.codes import (
                KnowledgeContractError,
                KnowledgeErrorCode,
            )

            raise KnowledgeContractError(
                KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND,
                "scope_ref has no resolvable name",
            )

        start_scope = self._resolver.resolve_scope(scope_name)

        # 步驟 2：traverse_scope_chain 上溯 parent_ref 链
        return traverse_scope_chain(
            start_scope,
            scope_cache=self._cache,
            max_depth=self._max_depth,
            block_self_reference=self._block_self_reference,
        )


__all__ = [
    "InheritService",
    "InheritServiceProtocol",
]
