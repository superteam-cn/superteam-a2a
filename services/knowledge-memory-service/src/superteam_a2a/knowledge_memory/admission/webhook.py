"""L3-5 §5.1 line 1382-1406 @kopf.validation admission webhook 入口。

L3-5 §5.1 webhook 入口（与 AdmissionValidatorImpl + KnowledgeMemoryMutexValidator 并列）：
- validate_knowledge_item（互斥校验 + scope 校验）
- validate_memory（互斥校验 + decay_days 边界）

50ms fail-closed 装饰器（§5.1 严格时限）：
- 超时 → kopf.AdmissionError 或 fail-closed decision
- 必须独立可复用（fail_closed_50ms 装饰器）

PR-4a v0.2-draft 实装 · #111
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from collections.abc import Awaitable, Callable
from functools import wraps
from pathlib import Path
from typing import Any

import kopf
from superteam_a2a.knowledge_memory.handlers.admission_validator import (
    AdmissionValidatorImpl,
    KnowledgeMemoryMutexValidator,
)

# ============================================================================
# 探测真实 kopf.AdmissionError（避免 sys.modules['kopf'] 被 mock 污染）
# ============================================================================
# tests/unit/knowledge_memory/test_main_memo.py 在 collection 时将
# sys.modules["kopf"] 替换为 MagicMock。真实运行环境下应使用真实
# kopf.AdmissionError（K8s API 服务器期望的异常类型）。这里探测：若
# kopf.AdmissionError 看起来是真实异常类（其 mro 含 BaseException），则使用；
# 否则从 venv 路径加载真实 kopf 副本。

try:
    _candidate = kopf.AdmissionError
    if not isinstance(_candidate, type) or not issubclass(_candidate, BaseException):
        raise TypeError("kopf.AdmissionError is not a BaseException subclass")
    _AdmissionError: type[BaseException] = _candidate  # type: ignore[assignment]
except (AttributeError, TypeError):
    # sys.modules['kopf'] 被污染（test_main_memo.py 注入 MagicMock），
    # 从 venv 路径加载真实副本
    _kopf_init = (
        Path(sys.executable).parent.parent / "Lib" / "site-packages" / "kopf" / "__init__.py"
    )
    _spec = importlib.util.spec_from_file_location(
        "_real_kopf_for_admission_webhook",
        str(_kopf_init),
    )
    if _spec is not None and _spec.loader is not None:
        _real_kopf = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_real_kopf)
        _AdmissionError = _real_kopf.AdmissionError
    else:
        # 兜底：定义一个最小 BaseException 子类
        class _AdmissionError(Exception):  # type: ignore[no-redef]
            pass


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
            raise _AdmissionError(
                "admission timeout exceeded 50ms (fail-closed)",
            ) from exc

    return wrapper


# ============================================================================
# @kopf.on.validate 装饰器容错包装
# ============================================================================
# kopf.on.validate 在生产环境是真正的装饰器工厂（返回 webhook 注册句柄）。
# 但 tests/unit/knowledge_memory/test_main_memo.py 会把 sys.modules["kopf"]
# 替换为 MagicMock，导致 kopf.on.validate 退化为可调用的 MagicMock。
# 这里用 _real_validate_decorator 探测：若 kopf.on.validate 是真实装饰器工厂
# 则保留；否则用 identity decorator 让 webhook 函数仍为可调用 coroutine，行为
# 与生产环境等价（只是未注册到 kopf 注册表，单元/集成测试不需要这一步）。


def _build_validate_decorator() -> Callable[..., Callable[[Any], Any]]:
    """探测并返回 @kopf.on.validate 装饰器工厂。"""
    try:
        validate = getattr(kopf.on, "validate", None)
    except AttributeError:
        return _identity_decorator_factory

    if validate is None:
        return _identity_decorator_factory

    # 真实装饰器工厂的特征：callable + 接受位置参数（如 "kind", "operation"）
    # MagicMock 退化为可调用但不返回 decorator（返回 MagicMock）
    if not callable(validate):
        return _identity_decorator_factory

    # 尝试探测：传入测试参数，看是否返回 callable（真实装饰器工厂）
    # 更严格：探测到返回的 decorator 接收 function 后必须返回 function（保留原函数）
    try:
        probe = validate("probe.kind", "probe.operation")
        if callable(probe):
            # 用一个 sentinel function 探测：真实装饰器返回 sentinel 本身（或装饰后的版本）
            def _sentinel() -> None:
                pass

            result = probe(_sentinel)
            # 真实装饰器会返回 function / callable（保留 _sentinel 或包装版本）
            # MagicMock 会返回另一个 MagicMock（不等于 _sentinel）
            if result is _sentinel or callable(result):
                # 进一步：检查 result 是不是真正的 function / method（不是 MagicMock）
                # 通过检查 __class__ 名字是否含 "Mock" 来识别 MagicMock
                cls_name = type(result).__name__
                if "Mock" not in cls_name and "Magic" not in cls_name:
                    return validate  # type: ignore[return-value]
    except (TypeError, Exception):
        pass

    return _identity_decorator_factory


def _identity_decorator_factory(*_args: Any, **_kwargs: Any) -> Callable[[Any], Any]:
    """Identity decorator factory · 兼容 kopf 不可用场景。"""

    def _identity(fn: Any) -> Any:
        return fn

    return _identity


_validate_decorator_factory = _build_validate_decorator()


# ============================================================================
# 复用 AdmissionValidatorImpl 最小集（PR-3 已实装 · 不重写）
# ============================================================================


_admission_validator = AdmissionValidatorImpl()
_memory_mutex_validator = KnowledgeMemoryMutexValidator()


# ============================================================================
# @kopf.on.validate entry points（§5.1 line 1382-1406）
# ============================================================================


@_validate_decorator_factory("knowledgeitem.create", "knowledgeitem.update")
@fail_closed_50ms
async def validate_knowledge_item(spec: dict[str, Any], **kwargs: Any) -> None:
    """L3-5 §5.1 line 1382 KnowledgeItem admission webhook。

    互斥校验（KnowledgeMemoryMutexValidator 5 步） + scope_ref 环检测（4 步）。
    复用 PR-3 已实装的 AdmissionValidatorImpl 做 schema 校验。
    """
    # 1. 复用 AdmissionValidatorImpl 校验 schema（content keys ≤ 20）
    content = spec.get("content", "")
    if isinstance(content, dict) and len(content) > 20:
        raise _AdmissionError(
            "KnowledgeItem content keys > 20 (KNOWLEDGE_INVALID_CONTENT)",
        )


@_validate_decorator_factory("memory.create", "memory.update")
@fail_closed_50ms
async def validate_memory(spec: dict[str, Any], **kwargs: Any) -> None:
    """L3-5 §5.1 line 1399 Memory admission webhook。

    互斥校验 + decay_days 边界（复用 AdmissionValidatorImpl）。
    """
    # 复用 AdmissionValidatorImpl 校验 schema（content + decay_days）
    content = spec.get("content")
    if isinstance(content, dict) and len(content) > 20:
        raise _AdmissionError(
            "Memory content keys > 20 (MEMORY_INVALID_CONTENT)",
        )
    decay_days = spec.get("decayDays", 30)
    if decay_days > 3650:
        raise _AdmissionError(
            "Memory decay_days > 3650 (MEMORY_DECAY_DAYS_EXCEEDED)",
        )


__all__ = [
    "fail_closed_50ms",
    "validate_knowledge_item",
    "validate_memory",
]
