"""scope 继承链遍历函数 · 4 级校验 + self-reference 检测.

PR-4c plan §2.3 · L3-5 §3.1 inheritRules + L3-6 §3 + ADR-0002 §3.1。
"""

from __future__ import annotations

from typing import Any

from superteam_a2a.knowledge.crd.knowledgescope import KnowledgeScope
from superteam_a2a.knowledge.errors.codes import (
    KnowledgeContractError,
    KnowledgeErrorCode,
)


def traverse_scope_chain(
    scope: KnowledgeScope,
    *,
    scope_cache: Any,
    max_depth: int = 3,
    block_self_reference: bool = True,
) -> list[str]:
    """遍历 scope 继承链 · 4 级校验 + self-reference + max_depth.

    Parameters:
    - scope: starting KnowledgeScope
    - scope_cache: ScopeCache Protocol with .get(name) method
    - max_depth: default 3 (L3-5 §3.1 inheritRules.max_depth)
    - block_self_reference: default True (cycle detection)

    Returns list[str] of scope names from start to root.

    Raises:
    - KnowledgeContractError(KNOWLEDGE_SCOPE_NOT_FOUND) when parent doesn't exist
    - KnowledgeContractError(KNOWLEDGE_OWNER_KIND_FORBIDDEN) on cycle or max_depth exceeded
    """
    visited: set[str] = set()
    chain: list[str] = []
    current: KnowledgeScope | None = scope
    depth = 0

    while current is not None:
        current_name = _extract_scope_name(current)

        # Step 2: self-reference detection
        if block_self_reference and current_name in visited:
            raise KnowledgeContractError(
                KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN,
                f"scope_ref cycle detected at depth {depth} (node={current_name})",
            )
        visited.add(current_name)
        chain.append(current_name)

        # Step 3: max_depth enforcement (before traversing to next parent)
        if depth >= max_depth:
            raise KnowledgeContractError(
                KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN,
                f"scope_ref depth > {max_depth} (node={current_name})",
            )

        # Step 1: get parent_ref from spec
        spec = getattr(current, "spec", None)
        parent_ref = getattr(spec, "parent_ref", None) if spec is not None else None
        if parent_ref is None:
            break  # reached root

        parent_name = getattr(parent_ref, "name", None)
        if parent_name is None or parent_name == "":
            break

        # Step 4: look up parent in cache
        parent = scope_cache.get(parent_name)
        if parent is None:
            raise KnowledgeContractError(
                KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND,
                f"scope parent {parent_name} not found in scope cache",
            )

        current = parent
        depth += 1

    return chain


def _extract_scope_name(scope: KnowledgeScope) -> str:
    """Extract scope name from K8s object via defensive getattr."""
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


__all__ = ["traverse_scope_chain"]
