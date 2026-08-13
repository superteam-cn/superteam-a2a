"""Knowledge 错误码 · 11 个 KNOWLEDGE_* 与 L3-5 §8.1 line 1808-1822 零漂移。

依据 L3-5 Spec §8.1 权威错误码表（11 个 · 范围 -32008 ~ -32018）。
wire contract 严格封闭，禁止任何本地新增同义错误码；新增必须先修改 L3-5 权威表。

PR-4a v0.2-draft 实装 · #111
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any

# ============================================================================
# §8.1 权威错误码（11 个 · 范围 -32008 ~ -32018）
# ============================================================================


class KnowledgeErrorCode(IntEnum):
    """L3-5 v0.2.0 §8.1 line 1808-1822 权威错误码表（零漂移）。"""

    KNOWLEDGE_SCOPE_NOT_FOUND = -32008
    KNOWLEDGE_QUERY_TOO_LONG = -32009
    KNOWLEDGE_INVALID_TYPE = -32010
    KNOWLEDGE_INTERNAL_ERROR = -32011
    KNOWLEDGE_ITEM_NOT_FOUND = -32012
    KNOWLEDGE_VERSION_NOT_FOUND = -32013
    KNOWLEDGE_FORBIDDEN = -32014
    KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY = -32015
    KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS = -32016
    KNOWLEDGE_OWNER_KIND_FORBIDDEN = -32017
    KNOWLEDGE_ADMISSION_TIMEOUT = -32018


# ============================================================================
# HTTP 状态映射（§8.1 配套）
# ============================================================================

REASON_HTTP_MAP: dict[KnowledgeErrorCode, int] = {
    KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND: 404,
    KnowledgeErrorCode.KNOWLEDGE_QUERY_TOO_LONG: 400,
    KnowledgeErrorCode.KNOWLEDGE_INVALID_TYPE: 400,
    KnowledgeErrorCode.KNOWLEDGE_INTERNAL_ERROR: 500,
    KnowledgeErrorCode.KNOWLEDGE_ITEM_NOT_FOUND: 404,
    KnowledgeErrorCode.KNOWLEDGE_VERSION_NOT_FOUND: 404,
    KnowledgeErrorCode.KNOWLEDGE_FORBIDDEN: 403,
    KnowledgeErrorCode.KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY: 400,
    KnowledgeErrorCode.KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS: 400,
    KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN: 400,
    KnowledgeErrorCode.KNOWLEDGE_ADMISSION_TIMEOUT: 503,
}


# ============================================================================
# §8.1 Retryable 矩阵（错误码文档化）
# ============================================================================

RETRYABLE_CODES: frozenset[KnowledgeErrorCode] = frozenset(
    {
        KnowledgeErrorCode.KNOWLEDGE_INTERNAL_ERROR,
        KnowledgeErrorCode.KNOWLEDGE_ADMISSION_TIMEOUT,
    }
)


def is_retryable(code: KnowledgeErrorCode) -> bool:
    """§8.3 Retryable 矩阵查询。"""
    return code in RETRYABLE_CODES


# ============================================================================
# 异常类（与 backend/errors.py 风格镜像）
# ============================================================================


class KnowledgeError(Exception):
    """Knowledge 统一异常 · code 必须是 KnowledgeErrorCode 枚举成员。

    与 backend MemoryBackendError 镜像。cause 字段保留原始异常链。
    """

    def __init__(
        self,
        code: KnowledgeErrorCode,
        message: str,
        *,
        retryable: bool | None = None,
        cause: Exception | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        if not isinstance(code, KnowledgeErrorCode):
            raise TypeError(
                f"code must be KnowledgeErrorCode enum member, got {type(code).__name__}"
            )
        super().__init__(f"[{code.name}]({code.value}): {message}")
        self.code = code
        self.message = message[:1024]
        self.retryable = is_retryable(code) if retryable is None else retryable
        self.cause = cause
        self.data: dict[str, Any] = dict(data or {})
        self.data.setdefault("module", "knowledge")
        self.data.setdefault("code_name", code.name)


class KnowledgeContractError(KnowledgeError):
    """契约违反（容量 / 幂等 / schema）· §5.1 入参校验异常入口。"""


# ============================================================================
# §8.2 helper：A2AError.data 工厂（与 backend/errors.py 镜像）
# ============================================================================


def knowledge_error_data(code: KnowledgeErrorCode, **extra: Any) -> dict[str, Any]:
    """构造 A2AError.data · module + code_name + 允许的额外字段。"""
    data: dict[str, Any] = {"module": "knowledge", "code_name": code.name}
    data.update(extra)
    return data


__all__ = [
    "REASON_HTTP_MAP",
    "RETRYABLE_CODES",
    "KnowledgeContractError",
    "KnowledgeError",
    "KnowledgeErrorCode",
    "is_retryable",
    "knowledge_error_data",
]
