"""VisibilityService · Protocol stub · 5 維矩陣策略實裝推 PR-4c。

依據 L3-5 §5.4 5 維矩陣：
1. scope_ref.level（agent / scope / industry / project / global）
2. visibility（public-readable / scope-only / scope-and-children / agent-private）
3. agent_ref（ServiceAccount）
4. tags（最多 10 個）
5. time-window（created_at + decay_days）

5 維矩陣策略執行推 PR-4c（需引入時間計算 + agent 解析）。

ISP：Protocol 僅暴露 resolve_visibility 方法。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class VisibilityServiceProtocol(Protocol):
    """Visibility 解析 Protocol · ISP 最小接口。"""

    async def resolve_visibility(
        self,
        item: Any,
    ) -> str: ...


class VisibilityService:
    """VisibilityService stub · PR-4b 階段實裝。

    行為：
    - resolve_visibility 接收 item（KnowledgeItem 或 Memory）
    - 拋 NotImplementedError（5 維矩陣策略實裝推 PR-4c）

    PR-4c 實裝要點：
    1. 5 維矩陣策略表構建（依據 L3-5 §5.4 line 1500-1580）
    2. agent_ref + scope_ref.level 解析
    3. time-window 計算（decay_days + created_at）
    4. 返回實際可見性（"public-readable" / "scope-only" / "scope-and-children" / "agent-private"）
    """

    async def resolve_visibility(
        self,
        item: Any,
    ) -> str:
        """解析 item 可見性 · PR-4b stub 拋 NotImplementedError。

        參數：
        - item · KnowledgeItem 或 Memory

        返回：
        - str · 可見性字符串

        異常：
        - NotImplementedError · 5 維矩陣策略實裝推 PR-4c
        """
        raise NotImplementedError(
            "VisibilityService 5-dim matrix strategy is PR-4c scope (依據 L3-5 §5.4 5 維矩陣)"
        )


__all__ = [
    "VisibilityService",
    "VisibilityServiceProtocol",
]
