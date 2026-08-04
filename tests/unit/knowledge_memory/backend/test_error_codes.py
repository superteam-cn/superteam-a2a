"""12 MEMORY_* 错误码集合相等静态断言 · TEST-MEM-052。

L3-6 §8.1 line 1150：ERR-MEM-CF-001 对三处 name/code 做集合相等比较，
不接受子集。CI 门禁顺序（§11.6）将 conformance → errors exact set 列为
强制步骤，集合不等即拒绝合并。
"""

from __future__ import annotations

import pytest
from superteam_a2a.knowledge_memory import MemoryErrorCode, is_retryable

# ============================================================================
# L2-4 v0.2.0 §9.1 权威错误码表（12 个 · 范围 -32101 ~ -32112）
# ============================================================================

L2_4_AUTHORITATIVE_NAMES: frozenset[str] = frozenset(
    {
        "MEMORY_SCOPE_NOT_FOUND",
        "MEMORY_INVALID_CONTENT",
        "MEMORY_FORBIDDEN",
        "MEMORY_RATE_LIMIT",
        "MEMORY_INTERNAL_ERROR",
        "MEMORY_QUERY_TOO_BROAD",
        "MEMORY_SOURCE_KI_NOT_FOUND",
        "MEMORY_SOURCE_KI_SCOPE_MISMATCH",
        "MEMORY_AGENT_PRIVATE_REQUIRES_NAME",
        "MEMORY_DECAY_DAYS_EXCEEDED",
        "MEMORY_AGENT_NOT_FOUND",
        "MEMORY_ADMISSION_TIMEOUT",
    }
)
L2_4_AUTHORITATIVE_CODES: frozenset[int] = frozenset(
    {
        -32101,
        -32102,
        -32103,
        -32104,
        -32105,
        -32106,
        -32107,
        -32108,
        -32109,
        -32110,
        -32111,
        -32112,
    }
)


# ============================================================================
# TEST-MEM-052 · 权威错误码封闭集静态检查
# ============================================================================


def test_memory_error_codes_match_l2_4_authoritative():
    """TEST-MEM-052 · MemoryErrorCode names 与 L2-4 v0.2.0 §9.1 100% 集合相等。

    不接受子集；任何漂移即拒绝合并。
    """
    actual_names = frozenset(m.name for m in MemoryErrorCode)
    actual_codes = frozenset(m.value for m in MemoryErrorCode)

    assert actual_names == L2_4_AUTHORITATIVE_NAMES, (
        f"MemoryErrorCode names drift from L2-4 authoritative:\n"
        f"  missing: {L2_4_AUTHORITATIVE_NAMES - actual_names}\n"
        f"  extra:   {actual_names - L2_4_AUTHORITATIVE_NAMES}"
    )
    assert actual_codes == L2_4_AUTHORITATIVE_CODES, (
        f"MemoryErrorCode codes drift from L2-4 authoritative:\n"
        f"  missing: {L2_4_AUTHORITATIVE_CODES - actual_codes}\n"
        f"  extra:   {actual_codes - L2_4_AUTHORITATIVE_CODES}"
    )


def test_memory_error_code_count_is_12():
    """TEST-MEM-052 配套 · 必须是恰好 12 个错误码（封闭集）。"""
    assert len(list(MemoryErrorCode)) == 12


def test_memory_error_code_values_in_valid_range():
    """TEST-MEM-052 配套 · 所有 code 在 [-32101, -32112] 范围内。"""
    for code in MemoryErrorCode:
        assert -32112 <= code.value <= -32101


# ============================================================================
# Retryable 矩阵（§8.3）
# ============================================================================


@pytest.mark.parametrize(
    ("code", "retryable"),
    [
        (MemoryErrorCode.MEMORY_SCOPE_NOT_FOUND, False),
        (MemoryErrorCode.MEMORY_INVALID_CONTENT, False),
        (MemoryErrorCode.MEMORY_FORBIDDEN, False),
        (MemoryErrorCode.MEMORY_RATE_LIMIT, True),
        (MemoryErrorCode.MEMORY_INTERNAL_ERROR, True),
        (MemoryErrorCode.MEMORY_QUERY_TOO_BROAD, False),
        (MemoryErrorCode.MEMORY_SOURCE_KI_NOT_FOUND, False),
        (MemoryErrorCode.MEMORY_SOURCE_KI_SCOPE_MISMATCH, False),
        (MemoryErrorCode.MEMORY_AGENT_PRIVATE_REQUIRES_NAME, False),
        (MemoryErrorCode.MEMORY_DECAY_DAYS_EXCEEDED, False),
        (MemoryErrorCode.MEMORY_AGENT_NOT_FOUND, False),
        (MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT, True),
    ],
)
def test_retryable_matrix_matches_spec(code, retryable):
    """TEST-MEM-052 配套 · §8.3 Retryable 矩阵。"""
    assert is_retryable(code) is retryable


def test_retryable_codes_exactly_three():
    """TEST-MEM-052 配套 · 可重试的恰好 3 个：RATE_LIMIT/INTERNAL_ERROR/ADMISSION_TIMEOUT。"""
    retryable = [c for c in MemoryErrorCode if is_retryable(c)]
    assert len(retryable) == 3
    assert set(retryable) == {
        MemoryErrorCode.MEMORY_RATE_LIMIT,
        MemoryErrorCode.MEMORY_INTERNAL_ERROR,
        MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT,
    }


# ============================================================================
# MemoryBackendError 构造验证
# ============================================================================


def test_memory_backend_error_rejects_non_enum_code():
    """MemoryBackendError 必须接受 MemoryErrorCode 枚举成员，拒绝裸整数。"""
    import pytest
    from superteam_a2a.knowledge_memory import MemoryBackendError

    with pytest.raises(TypeError, match="MemoryErrorCode"):
        MemoryBackendError(-32101, "test")  # type: ignore[arg-type]


def test_memory_backend_error_truncates_message():
    """MemoryBackendError message 截断到 1024 字符。"""
    from superteam_a2a.knowledge_memory import MemoryBackendError

    long_msg = "x" * 2048
    err = MemoryBackendError(MemoryErrorCode.MEMORY_INTERNAL_ERROR, long_msg)
    assert len(err.message) == 1024
