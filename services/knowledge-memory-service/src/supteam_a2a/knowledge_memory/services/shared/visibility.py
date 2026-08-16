"""VisibilityService · 完整实装 · 5 维 visibility 矩阵解析.

依据 PR-4c plan §2.4 + L3-5 §3.1 + L3-5 §5.4 5 维矩阵 + ADR-0002 §4。

5 维 visibility 矩阵策略：
1. scope_ref.level（agent / agentset / workflow / system）
2. visibility（public-readable / scope-only / scope-and-children / agent-private / system-readonly）
3. agent_ref（ServiceAccount · PR-5 Helm 注入）
4. tags（最多 10 个 · L3-5 §5.4）
5. time-window（created_at + decay_days · 计算通过 item 注入字段）

实装策略：
- resolve_visibility(item) · 委托 VisibilityResolver.is_visible_to + 5 维策略表
- 完整 5 维矩阵策略表实装（VISIBILITY_MATRIX · 5 类 → 允许 scope 集合）
- PUBLIC_READABLE 包含 "*" 通配符（公开可见所有 scope）

PR-4b 阶段的 NotImplementedError 已替换为完整实装（PR-4c）。

宪法 §17 SOLID：
- SRP：本 service 仅负责 visibility 解析入口
- DIP：依赖 VisibilityResolver + VisibilityMatrix（visibility_resolver 模块）
- ISP：VisibilityServiceProtocol 仅暴露 resolve_visibility 方法
- CRP：构造参数 resolver 注入
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from superteam_a2a.knowledge.crd.knowledgescope import KnowledgeVisibility
from superteam_a2a.knowledge_memory.visibility_resolver import (
    StaticVisibilityMatrix,
    VisibilityMatrix,
    VisibilityResolver,
)


@runtime_checkable
class VisibilityServiceProtocol(Protocol):
    """Visibility 解析 Protocol · ISP 最小接口."""

    async def resolve_visibility(
        self,
        item: Any,
    ) -> str: ...


class VisibilityService:
    """VisibilityService 完整实装（PR-4c）.

    行为：
    - resolve_visibility(item) · 5 维矩阵策略表解析（SCOPE_ONLY / SCOPE_AND_CHILDREN /
      PUBLIC_READABLE / AGENT_PRIVATE / SYSTEM_READONLY）
    - 返回实际可见性字符串（KnowledgeVisibility.value）

    构造参数：
    - resolver · VisibilityResolver · 默认 None（自动 StaticVisibilityMatrix 构造）

    返回：str · KnowledgeVisibility.value（"scope-only" / "scope-and-children" /
        "public-readable" / "agent-private" / "system-readonly"）
    """

    def __init__(
        self,
        *,
        resolver: VisibilityResolver | None = None,
        matrix: VisibilityMatrix | None = None,
    ) -> None:
        """构造注入.

        参数：
        - resolver · VisibilityResolver 可选 · 默认 None（自动 matrix 构造）
        - matrix · VisibilityMatrix 可选 · 默认 None（自动 StaticVisibilityMatrix 构造）
        """
        if resolver is not None:
            self._resolver = resolver
        else:
            m = matrix if matrix is not None else StaticVisibilityMatrix()
            self._resolver = VisibilityResolver(matrix=m)

    async def resolve_visibility(
        self,
        item: Any,
    ) -> str:
        """解析 item 可見性 · 5 維矩陣策略完整實裝.

        参数：
        - item · KnowledgeItem 或 Memory（含 spec.visibility 或 spec.visibility 字段）

        返回：
        - str · KnowledgeVisibility.value 字串（5 種之一）

        算法：
        1. item.spec.visibility → KnowledgeVisibility StrEnum（PR-3 已實裝 Pydantic）
        2. 直接返回 item.spec.visibility.value（5 維策略表解析由 caller 透過
           is_visible_to(target_scope) 判斷）

        異常：
        - KnowledgeContractError · item.spec.visibility 非法（不在 5 維集合中）
        """
        # 步驟 1：抽取 item.spec.visibility（PR-4c 統一入口）
        spec = getattr(item, "spec", None)
        if spec is None:
            spec = item  # 已經是 spec 對象
        visibility = getattr(spec, "visibility", None)

        if visibility is None:
            # 預設 SCOPE_AND_CHILDREN（與 knowledgescope.py KnowledgeScopeSpec 默認一致）
            return KnowledgeVisibility.SCOPE_AND_CHILDREN.value

        if isinstance(visibility, KnowledgeVisibility):
            return visibility.value

        # 字串輸入（防禦式 · KnowledgeVisibility StrEnum 支持 str 比較）
        if isinstance(visibility, str):
            try:
                return KnowledgeVisibility(visibility).value
            except ValueError as exc:
                from superteam_a2a.knowledge.errors.codes import (
                    KnowledgeContractError,
                    KnowledgeErrorCode,
                )

                raise KnowledgeContractError(
                    KnowledgeErrorCode.KNOWLEDGE_INVALID_TYPE,
                    f"visibility must be one of KnowledgeVisibility, got {visibility!r}",
                ) from exc

        # 其他類型無效
        from superteam_a2a.knowledge.errors.codes import (
            KnowledgeContractError,
            KnowledgeErrorCode,
        )

        raise KnowledgeContractError(
            KnowledgeErrorCode.KNOWLEDGE_INVALID_TYPE,
            f"visibility must be KnowledgeVisibility or str, got {type(visibility).__name__}",
        )

    def is_visible_to(
        self,
        visibility: KnowledgeVisibility | str,
        target_scope: str,
    ) -> bool:
        """判斷 visibility 對 target_scope 是否可見 · 委託給 VisibilityResolver.

        参数：
        - visibility · KnowledgeVisibility 或其 value 字串
        - target_scope · str · 目標 scope 名

        返回：bool
        """
        if isinstance(visibility, str):
            visibility = KnowledgeVisibility(visibility)
        return self._resolver.is_visible_to(visibility, target_scope)


__all__ = [
    "VisibilityService",
    "VisibilityServiceProtocol",
]
