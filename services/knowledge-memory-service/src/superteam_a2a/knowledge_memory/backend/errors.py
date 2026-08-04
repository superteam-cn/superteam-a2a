"""Memory 错误码 · 12 个 MEMORY_* 与 L2-4 v0.2.0 §9.1 零漂移。

依据 L3-6 Spec §8.1 权威错误码表 + §8.2 helper。wire contract 严格封闭，
禁止任何本地新增同义错误码；新增必须先修改 L2-4 权威表并通过 ADR/兼容性评审。
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any

# ============================================================================
# §8.1 权威错误码（12 个 · 范围 -32101 ~ -32112）
# ============================================================================


class MemoryErrorCode(IntEnum):
    """L2-4 v0.2.0 §9.1 + L3-6 §8.1 权威错误码表（零漂移）。"""

    MEMORY_SCOPE_NOT_FOUND = -32101
    MEMORY_INVALID_CONTENT = -32102
    MEMORY_FORBIDDEN = -32103
    MEMORY_RATE_LIMIT = -32104
    MEMORY_INTERNAL_ERROR = -32105
    MEMORY_QUERY_TOO_BROAD = -32106
    MEMORY_SOURCE_KI_NOT_FOUND = -32107
    MEMORY_SOURCE_KI_SCOPE_MISMATCH = -32108
    MEMORY_AGENT_PRIVATE_REQUIRES_NAME = -32109
    MEMORY_DECAY_DAYS_EXCEEDED = -32110
    MEMORY_AGENT_NOT_FOUND = -32111
    MEMORY_ADMISSION_TIMEOUT = -32112


# ============================================================================
# §8.1 Retryable 矩阵（与权威表 1:1 对应）
# ============================================================================

RETRYABLE_CODES: frozenset[MemoryErrorCode] = frozenset(
    {
        MemoryErrorCode.MEMORY_RATE_LIMIT,
        MemoryErrorCode.MEMORY_INTERNAL_ERROR,
        MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT,
    }
)


def is_retryable(code: MemoryErrorCode) -> bool:
    """§8.3 Retryable 矩阵查询。"""
    return code in RETRYABLE_CODES


# ============================================================================
# 异常类（§5.7 5 项不变量之 4：错误码封闭集）
# ============================================================================


class MemoryBackendError(Exception):
    """Memory backend 统一异常 · code 必须是 MemoryErrorCode 枚举成员。

    adapter 直接 import §9.1 的 12 个 MemoryErrorCode，禁止裸整数或本地新增。
    cause 字段保留原始异常链（§5.7 不变量 4）。
    """

    def __init__(
        self,
        code: MemoryErrorCode,
        message: str,
        *,
        retryable: bool | None = None,
        cause: Exception | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        if not isinstance(code, MemoryErrorCode):
            raise TypeError(f"code must be MemoryErrorCode enum member, got {type(code).__name__}")
        super().__init__(f"[{code.name}]({code.value}): {message}")
        self.code = code
        self.message = message[:1024]  # §5.7 1KB 上限
        self.retryable = is_retryable(code) if retryable is None else retryable
        self.cause = cause
        self.data: dict[str, Any] = dict(data or {})
        self.data.setdefault("module", "memory")
        self.data.setdefault("code_name", code.name)


class MemoryContractError(MemoryBackendError):
    """契约违反（容量 / 幂等 / schema）· §5.7 不变量 4 入口。"""


class ClockSkewError(MemoryBackendError):
    """Wall clock 漂移 > tolerance · §5.1 elapsed_non_negative。"""


# ============================================================================
# §8.2 helper：A2AError 工厂（与 L3-5 §8.2 镜像）
# ============================================================================


def memory_error_data(code: MemoryErrorCode, **extra: Any) -> dict[str, Any]:
    """构造 A2AError.data · module + code_name + 允许的额外字段。

    禁止 content/token/Secret；超长 message 在 caller 端截断到 1024。
    """
    data: dict[str, Any] = {"module": "memory", "code_name": code.name}
    data.update(extra)
    return data


__all__ = [
    "RETRYABLE_CODES",
    "ClockSkewError",
    "MemoryBackendError",
    "MemoryContractError",
    "MemoryErrorCode",
    "is_retryable",
    "memory_error_data",
]
