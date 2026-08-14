"""InheritService · Protocol stub · 4 級 scope 繼承規則實裝推 PR-4c。

依據 L3-5 §5.5 4 級 scope 繼承：
1. agent（葉節點）→ 不向上繼承
2. scope（單個 scope）
3. industry（跨 scope 聚合）
4. project（project 邊界隔離）

4 級 scope 繼承規則（parent_ref BFS + chain 遍歷）實裝推 PR-4c。

ISP：Protocol 僅暴露 resolve_inherit_chain 方法。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class InheritServiceProtocol(Protocol):
    """Scope 繼承解析 Protocol · ISP 最小接口。"""

    async def resolve_inherit_chain(
        self,
        scope_ref: Any,
    ) -> list[Any]:  # list[ScopeRef]
        ...


class InheritService:
    """InheritService stub · PR-4b 階段實裝。

    行為：
    - resolve_inherit_chain 接收 scope_ref（ScopeReference）
    - 拋 NotImplementedError（4 級 scope 繼承規則實裝推 PR-4c）

    PR-4c 實裝要點：
    1. parent_ref BFS（從 scope_ref 開始）
    2. max_depth=8 限制（PR-4a KnowledgeMemoryMutexValidator 復用）
    3. 命中自身 → 環檢測（KNOWLEDGE_OWNER_KIND_FORBIDDEN）
    4. 命中不存在 parent → KNOWLEDGE_SCOPE_NOT_FOUND
    5. 返回 [scope_ref, parent1, parent2, ..., root] 鏈
    """

    async def resolve_inherit_chain(
        self,
        scope_ref: Any,
    ) -> list[Any]:
        """解析 scope 繼承鏈 · PR-4b stub 拋 NotImplementedError。

        參數：
        - scope_ref · ScopeReference（含 name + level + 可選 parent_ref）

        返回：
        - list[Any] · 從 scope_ref 到根的繼承鏈

        異常：
        - NotImplementedError · 4 級 scope 繼承規則實裝推 PR-4c
        """
        raise NotImplementedError(
            "InheritService 4-level scope inheritance is PR-4c scope "
            "(依據 L3-5 §5.5 4 級 scope 繼承規則)"
        )


__all__ = [
    "InheritService",
    "InheritServiceProtocol",
]
