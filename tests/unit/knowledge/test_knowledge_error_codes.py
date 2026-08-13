"""11 KNOWLEDGE_* 错误码集合相等静态断言 · KNOW-UT-001~005.

L3-5 §8.1 line 1808-1822 wire contract 严格封闭，IT 静态断言零漂移。
PR-4a v0.2-draft 实装 · #111
"""

from __future__ import annotations

import pytest
from superteam_a2a.knowledge.errors.codes import (
    REASON_HTTP_MAP,
    RETRYABLE_CODES,
    KnowledgeError,
    KnowledgeErrorCode,
    is_retryable,
    knowledge_error_data,
)

# ============================================================================
# L3-5 v0.2.0 §8.1 权威错误码表（11 个 · 范围 -32008 ~ -32018）
# ============================================================================

L3_5_AUTHORITATIVE_NAMES: frozenset[str] = frozenset(
    {
        "KNOWLEDGE_SCOPE_NOT_FOUND",
        "KNOWLEDGE_QUERY_TOO_LONG",
        "KNOWLEDGE_INVALID_TYPE",
        "KNOWLEDGE_INTERNAL_ERROR",
        "KNOWLEDGE_ITEM_NOT_FOUND",
        "KNOWLEDGE_VERSION_NOT_FOUND",
        "KNOWLEDGE_FORBIDDEN",
        "KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY",
        "KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS",
        "KNOWLEDGE_OWNER_KIND_FORBIDDEN",
        "KNOWLEDGE_ADMISSION_TIMEOUT",
    }
)
L3_5_AUTHORITATIVE_CODES: frozenset[int] = frozenset(
    {
        -32008,
        -32009,
        -32010,
        -32011,
        -32012,
        -32013,
        -32014,
        -32015,
        -32016,
        -32017,
        -32018,
    }
)


# KNOW-UT-001
def test_knowledge_error_codes_match_l3_5_authoritative():
    """KNOW-UT-001 · KnowledgeErrorCode names 与 L3-5 §8.1 100% 集合相等。

    不接受子集；任何漂移即拒绝合并。
    """
    actual_names = frozenset(m.name for m in KnowledgeErrorCode)
    actual_codes = frozenset(m.value for m in KnowledgeErrorCode)

    assert actual_names == L3_5_AUTHORITATIVE_NAMES, (
        f"KnowledgeErrorCode names drift from L3-5 authoritative:\n"
        f"  missing: {L3_5_AUTHORITATIVE_NAMES - actual_names}\n"
        f"  extra:   {actual_names - L3_5_AUTHORITATIVE_NAMES}"
    )
    assert actual_codes == L3_5_AUTHORITATIVE_CODES, (
        f"KnowledgeErrorCode codes drift from L3-5 authoritative:\n"
        f"  missing: {L3_5_AUTHORITATIVE_CODES - actual_codes}\n"
        f"  extra:   {actual_codes - L3_5_AUTHORITATIVE_CODES}"
    )


# KNOW-UT-002
def test_knowledge_error_code_count_is_11():
    """KNOW-UT-002 · 必须是恰好 11 个错误码（封闭集）。"""
    assert len(list(KnowledgeErrorCode)) == 11


# KNOW-UT-003
def test_knowledge_error_code_values_in_valid_range():
    """KNOW-UT-003 · 所有 code 在 [-32018, -32008] 范围内。"""
    for code in KnowledgeErrorCode:
        assert -32018 <= code.value <= -32008


# KNOW-UT-004
@pytest.mark.parametrize(
    ("code", "expected_http"),
    [
        (KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND, 404),
        (KnowledgeErrorCode.KNOWLEDGE_QUERY_TOO_LONG, 400),
        (KnowledgeErrorCode.KNOWLEDGE_INVALID_TYPE, 400),
        (KnowledgeErrorCode.KNOWLEDGE_INTERNAL_ERROR, 500),
        (KnowledgeErrorCode.KNOWLEDGE_ITEM_NOT_FOUND, 404),
        (KnowledgeErrorCode.KNOWLEDGE_VERSION_NOT_FOUND, 404),
        (KnowledgeErrorCode.KNOWLEDGE_FORBIDDEN, 403),
        (KnowledgeErrorCode.KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY, 400),
        (KnowledgeErrorCode.KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS, 400),
        (KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN, 400),
        (KnowledgeErrorCode.KNOWLEDGE_ADMISSION_TIMEOUT, 503),
    ],
)
def test_reason_http_map_matches_spec(code, expected_http):
    """KNOW-UT-004 · REASON_HTTP_MAP 与 L3-5 §8.1 HTTP status 列 1:1 对齐。"""
    assert REASON_HTTP_MAP[code] == expected_http


# KNOW-UT-005
@pytest.mark.parametrize(
    ("code", "retryable"),
    [
        (KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND, False),
        (KnowledgeErrorCode.KNOWLEDGE_QUERY_TOO_LONG, False),
        (KnowledgeErrorCode.KNOWLEDGE_INVALID_TYPE, False),
        (KnowledgeErrorCode.KNOWLEDGE_INTERNAL_ERROR, True),
        (KnowledgeErrorCode.KNOWLEDGE_ITEM_NOT_FOUND, False),
        (KnowledgeErrorCode.KNOWLEDGE_VERSION_NOT_FOUND, False),
        (KnowledgeErrorCode.KNOWLEDGE_FORBIDDEN, False),
        (KnowledgeErrorCode.KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY, False),
        (KnowledgeErrorCode.KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS, False),
        (KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN, False),
        (KnowledgeErrorCode.KNOWLEDGE_ADMISSION_TIMEOUT, True),
    ],
)
def test_retryable_matrix_matches_spec(code, retryable):
    """KNOW-UT-005 · Retryable 矩阵：仅 INTERNAL_ERROR + ADMISSION_TIMEOUT 可重试。"""
    assert is_retryable(code) is retryable


# ============================================================================
# KnowledgeError 构造验证
# ============================================================================


def test_knowledge_error_rejects_non_enum_code():
    """KnowledgeError 必须接受 KnowledgeErrorCode 枚举成员，拒绝裸整数。"""
    with pytest.raises(TypeError, match="KnowledgeErrorCode"):
        KnowledgeError(-32008, "test")  # type: ignore[arg-type]


def test_knowledge_error_truncates_message():
    """KnowledgeError message 截断到 1024 字符。"""
    long_msg = "x" * 2048
    err = KnowledgeError(KnowledgeErrorCode.KNOWLEDGE_INTERNAL_ERROR, long_msg)
    assert len(err.message) == 1024


def test_knowledge_error_data_helper():
    """knowledge_error_data 工厂返回 module + code_name。"""
    data = knowledge_error_data(KnowledgeErrorCode.KNOWLEDGE_FORBIDDEN, agent_id="a-1")
    assert data["module"] == "knowledge"
    assert data["code_name"] == "KNOWLEDGE_FORBIDDEN"
    assert data["agent_id"] == "a-1"


def test_retryable_codes_exactly_two():
    """可重试的恰好 2 个：INTERNAL_ERROR + ADMISSION_TIMEOUT。"""
    retryable = [c for c in KnowledgeErrorCode if is_retryable(c)]
    assert len(retryable) == 2
    assert set(retryable) == {
        KnowledgeErrorCode.KNOWLEDGE_INTERNAL_ERROR,
        KnowledgeErrorCode.KNOWLEDGE_ADMISSION_TIMEOUT,
    }
    assert frozenset(retryable) == RETRYABLE_CODES
