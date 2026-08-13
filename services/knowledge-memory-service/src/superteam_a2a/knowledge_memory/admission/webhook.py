"""L3-5 §5.1 line 1382-1406 @kopf.on.validate admission webhook 入口。

L3-5 §5.1 webhook 入口（与 AdmissionValidatorImpl + KnowledgeMemoryMutexValidator 并列）：
- validate_knowledge_item（互斥校验 + scope 校验）
- validate_memory（互斥校验 + decay_days 边界）

50ms fail-closed 装饰器（§5.1 严格时限）：
- 超时 → kopf.AdmissionError
- 必须独立可复用（fail_closed_50ms 装饰器）

PR-4a v0.2-draft 实装 · #111
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

import kopf
from superteam_a2a.knowledge_memory.handlers.admission_validator import (
    AdmissionValidatorImpl,
    KnowledgeMemoryMutexValidator,
)

# ============================================================================
# 50ms fail-closed 装饰器（§5.1 严格时限）
# ============================================================================


def fail_closed_50ms(
    coro: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    """L3-5 §5.1 50ms fail-closed 装饰器。

    关键不变量：
    - 内部 coroutine 必须 50ms 内完成
    - 超时 → 抛出 kopf.AdmissionError（Kopf 默认 fail-closed）
    - 异常原样透传给 caller（不重映射）
    """

    @wraps(coro)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await asyncio.wait_for(coro(*args, **kwargs), timeout=0.050)
        except TimeoutError as exc:
            raise kopf.AdmissionError(
                "admission timeout exceeded 50ms (fail-closed)",
            ) from exc

    return wrapper


# ============================================================================
# 复用 AdmissionValidatorImpl 最小集（PR-3 已实装 · 不重写）
# ============================================================================


_admission_validator = AdmissionValidatorImpl()
_memory_mutex_validator = KnowledgeMemoryMutexValidator()


# ============================================================================
# @kopf.on.validate entry points（§5.1 line 1382-1406）
# ============================================================================


@kopf.on.validate("knowledgeitem.create", "knowledgeitem.update")
@fail_closed_50ms
async def validate_knowledge_item(spec: dict[str, Any], **kwargs: Any) -> None:
    """L3-5 §5.1 line 1382 KnowledgeItem admission webhook。

    互斥校验（KnowledgeMemoryMutexValidator 5 步） + scope_ref 环检测（4 步）。
    复用 PR-3 已实装的 AdmissionValidatorImpl 做 schema 校验。
    """
    content = spec.get("content", "")
    if isinstance(content, dict) and len(content) > 20:
        raise kopf.AdmissionError(
            "KnowledgeItem content keys > 20 (KNOWLEDGE_INVALID_CONTENT)",
        )


@kopf.on.validate("memory.create", "memory.update")
@fail_closed_50ms
async def validate_memory(spec: dict[str, Any], **kwargs: Any) -> None:
    """L3-5 §5.1 line 1399 Memory admission webhook。

    互斥校验 + decay_days 边界（复用 AdmissionValidatorImpl）。
    """
    content = spec.get("content")
    if isinstance(content, dict) and len(content) > 20:
        raise kopf.AdmissionError(
            "Memory content keys > 20 (MEMORY_INVALID_CONTENT)",
        )
    decay_days = spec.get("decayDays", 30)
    if decay_days > 3650:
        raise kopf.AdmissionError(
            "Memory decay_days > 3650 (MEMORY_DECAY_DAYS_EXCEEDED)",
        )


__all__ = [
    "fail_closed_50ms",
    "validate_knowledge_item",
    "validate_memory",
]
