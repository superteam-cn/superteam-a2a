"""L4-Phase3 PR-3 10 单元测试（OBS-MEM-UT-001~010）。

依据 L3-6 §7.1 line 1047-1060 权威表逐项验证：
- name 精确匹配（prometheus_client 0.20+ Counter 自动剥离 _total 后缀存储在 _name
  · 完整名在 _original_name；Histogram / Gauge 直接使用 _name）
- type 正确（Counter / Histogram / Gauge）
- labels 维度
- help text 非空
- Histogram buckets 精确匹配（reconcile: 13 元素 · admission: 12 元素）
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from prometheus_client import Counter, Gauge, Histogram

# ============================================================================
# 路径前置
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

from superteam_a2a.knowledge_memory.observability.metrics import (  # noqa: E402
    MEMORY_ADMISSION_DURATION_SECONDS,
    MEMORY_BM25_INDEX_SIZE,
    MEMORY_DECAY_APPLIED_TOTAL,
    MEMORY_GC_CLEANED_TOTAL,
    MEMORY_IN_PROCESS_CALL_TOTAL,
    MEMORY_PROMOTION_ELIGIBLE_TOTAL,
    MEMORY_RATE_LIMITED_TOTAL,
    MEMORY_RECONCILE_DURATION_SECONDS,
    MEMORY_RECONCILE_TOTAL,
    MEMORY_REINFORCE_TOTAL,
)

# ============================================================================
# Helpers
# ============================================================================

EXPECTED_RECONCILE_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1,
    2.5,
    5,
    10,
    30,
    50,
)
EXPECTED_ADMISSION_BUCKETS = (
    0.001,
    0.0025,
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1,
    2.5,
    5,
)


def _full_name(metric: object) -> str:
    """获取 prometheus_client 指标的完整名称。

    Counter 在 0.20+ 自动剥离 _total 后缀，完整名在 _original_name。
    Histogram / Gauge 直接用 _name。
    """
    if isinstance(metric, Counter):
        return metric._original_name  # type: ignore[attr-defined]
    return metric._name  # type: ignore[attr-defined]


# ============================================================================
# OBS-MEM-UT-001: MEMORY_RECONCILE_TOTAL
# ============================================================================


def test_obs_mem_ut_001_reconcile_total() -> None:
    """OBS-MEM-UT-001 · superteam_memory_reconcile_total · Counter(phase, result)。"""
    assert _full_name(MEMORY_RECONCILE_TOTAL) == "superteam_memory_reconcile_total"
    assert isinstance(MEMORY_RECONCILE_TOTAL, Counter)
    assert set(MEMORY_RECONCILE_TOTAL._labelnames) == {"phase", "result"}  # type: ignore[attr-defined]
    assert MEMORY_RECONCILE_TOTAL._documentation  # type: ignore[attr-defined]
    assert MEMORY_RECONCILE_TOTAL._documentation == "Total Memory reconcile attempts."  # type: ignore[attr-defined]


# ============================================================================
# OBS-MEM-UT-002: MEMORY_RECONCILE_DURATION_SECONDS
# ============================================================================


def test_obs_mem_ut_002_reconcile_duration_seconds() -> None:
    """OBS-MEM-UT-002 · superteam_memory_reconcile_duration_seconds · Histogram(phase) · 13 buckets。"""
    assert (
        _full_name(MEMORY_RECONCILE_DURATION_SECONDS)
        == "superteam_memory_reconcile_duration_seconds"
    )
    assert isinstance(MEMORY_RECONCILE_DURATION_SECONDS, Histogram)
    assert set(MEMORY_RECONCILE_DURATION_SECONDS._labelnames) == {"phase"}  # type: ignore[attr-defined]
    assert MEMORY_RECONCILE_DURATION_SECONDS._documentation  # type: ignore[attr-defined]
    # 13 元素 buckets（prometheus_client 0.20+ 自动追加 +inf 作为最后桶）
    raw_buckets = list(MEMORY_RECONCILE_DURATION_SECONDS._upper_bounds)  # type: ignore[attr-defined]
    # 去掉 +inf 后比较
    finite_buckets = tuple(b for b in raw_buckets if b != float("inf"))
    assert finite_buckets == EXPECTED_RECONCILE_BUCKETS
    assert len(finite_buckets) == 13


# ============================================================================
# OBS-MEM-UT-003: MEMORY_DECAY_APPLIED_TOTAL
# ============================================================================


def test_obs_mem_ut_003_decay_applied_total() -> None:
    """OBS-MEM-UT-003 · superteam_memory_decay_applied_total · Counter(phase_from, phase_to)。"""
    assert _full_name(MEMORY_DECAY_APPLIED_TOTAL) == "superteam_memory_decay_applied_total"
    assert isinstance(MEMORY_DECAY_APPLIED_TOTAL, Counter)
    assert set(MEMORY_DECAY_APPLIED_TOTAL._labelnames) == {"phase_from", "phase_to"}  # type: ignore[attr-defined]
    assert MEMORY_DECAY_APPLIED_TOTAL._documentation  # type: ignore[attr-defined]


# ============================================================================
# OBS-MEM-UT-004: MEMORY_REINFORCE_TOTAL
# ============================================================================


def test_obs_mem_ut_004_reinforce_total() -> None:
    """OBS-MEM-UT-004 · superteam_memory_reinforce_total · Counter(result)。"""
    assert _full_name(MEMORY_REINFORCE_TOTAL) == "superteam_memory_reinforce_total"
    assert isinstance(MEMORY_REINFORCE_TOTAL, Counter)
    assert set(MEMORY_REINFORCE_TOTAL._labelnames) == {"result"}  # type: ignore[attr-defined]
    assert MEMORY_REINFORCE_TOTAL._documentation  # type: ignore[attr-defined]


# ============================================================================
# OBS-MEM-UT-005: MEMORY_GC_CLEANED_TOTAL
# ============================================================================


def test_obs_mem_ut_005_gc_cleaned_total() -> None:
    """OBS-MEM-UT-005 · superteam_memory_gc_cleaned_total · Counter(gc_state)。"""
    assert _full_name(MEMORY_GC_CLEANED_TOTAL) == "superteam_memory_gc_cleaned_total"
    assert isinstance(MEMORY_GC_CLEANED_TOTAL, Counter)
    assert set(MEMORY_GC_CLEANED_TOTAL._labelnames) == {"gc_state"}  # type: ignore[attr-defined]
    assert MEMORY_GC_CLEANED_TOTAL._documentation  # type: ignore[attr-defined]


# ============================================================================
# OBS-MEM-UT-006: MEMORY_PROMOTION_ELIGIBLE_TOTAL
# ============================================================================


def test_obs_mem_ut_006_promotion_eligible_total() -> None:
    """OBS-MEM-UT-006 · superteam_memory_promotion_eligible_total · Gauge(visibility)。"""
    assert (
        _full_name(MEMORY_PROMOTION_ELIGIBLE_TOTAL) == "superteam_memory_promotion_eligible_total"
    )
    assert isinstance(MEMORY_PROMOTION_ELIGIBLE_TOTAL, Gauge)
    assert set(MEMORY_PROMOTION_ELIGIBLE_TOTAL._labelnames) == {"visibility"}  # type: ignore[attr-defined]
    assert MEMORY_PROMOTION_ELIGIBLE_TOTAL._documentation  # type: ignore[attr-defined]


# ============================================================================
# OBS-MEM-UT-007: MEMORY_BM25_INDEX_SIZE
# ============================================================================


def test_obs_mem_ut_007_bm25_index_size() -> None:
    """OBS-MEM-UT-007 · superteam_memory_bm25_index_size · Gauge(scope_level)。"""
    assert _full_name(MEMORY_BM25_INDEX_SIZE) == "superteam_memory_bm25_index_size"
    assert isinstance(MEMORY_BM25_INDEX_SIZE, Gauge)
    assert set(MEMORY_BM25_INDEX_SIZE._labelnames) == {"scope_level"}  # type: ignore[attr-defined]
    assert MEMORY_BM25_INDEX_SIZE._documentation  # type: ignore[attr-defined]


# ============================================================================
# OBS-MEM-UT-008: MEMORY_ADMISSION_DURATION_SECONDS
# ============================================================================


def test_obs_mem_ut_008_admission_duration_seconds() -> None:
    """OBS-MEM-UT-008 · superteam_memory_admission_duration_seconds · Histogram(validator) · 12 buckets。"""
    assert (
        _full_name(MEMORY_ADMISSION_DURATION_SECONDS)
        == "superteam_memory_admission_duration_seconds"
    )
    assert isinstance(MEMORY_ADMISSION_DURATION_SECONDS, Histogram)
    assert set(MEMORY_ADMISSION_DURATION_SECONDS._labelnames) == {"validator"}  # type: ignore[attr-defined]
    assert MEMORY_ADMISSION_DURATION_SECONDS._documentation  # type: ignore[attr-defined]
    # 12 元素 buckets（prometheus_client 0.20+ 自动追加 +inf 作为最后桶）
    raw_buckets = list(MEMORY_ADMISSION_DURATION_SECONDS._upper_bounds)  # type: ignore[attr-defined]
    finite_buckets = tuple(b for b in raw_buckets if b != float("inf"))
    assert finite_buckets == EXPECTED_ADMISSION_BUCKETS
    assert len(finite_buckets) == 12


# ============================================================================
# OBS-MEM-UT-009: MEMORY_IN_PROCESS_CALL_TOTAL
# ============================================================================


def test_obs_mem_ut_009_in_process_call_total() -> None:
    """OBS-MEM-UT-009 · superteam_memory_in_process_call_total · Counter(method, result)。"""
    assert _full_name(MEMORY_IN_PROCESS_CALL_TOTAL) == "superteam_memory_in_process_call_total"
    assert isinstance(MEMORY_IN_PROCESS_CALL_TOTAL, Counter)
    assert set(MEMORY_IN_PROCESS_CALL_TOTAL._labelnames) == {"method", "result"}  # type: ignore[attr-defined]
    assert MEMORY_IN_PROCESS_CALL_TOTAL._documentation  # type: ignore[attr-defined]


# ============================================================================
# OBS-MEM-UT-010: MEMORY_RATE_LIMITED_TOTAL
# ============================================================================


def test_obs_mem_ut_010_rate_limited_total() -> None:
    """OBS-MEM-UT-010 · superteam_memory_rate_limited_total · Counter(principal_type)。"""
    assert _full_name(MEMORY_RATE_LIMITED_TOTAL) == "superteam_memory_rate_limited_total"
    assert isinstance(MEMORY_RATE_LIMITED_TOTAL, Counter)
    assert set(MEMORY_RATE_LIMITED_TOTAL._labelnames) == {"principal_type"}  # type: ignore[attr-defined]
    assert MEMORY_RATE_LIMITED_TOTAL._documentation  # type: ignore[attr-defined]


# ============================================================================
# 集成断言（10 指标类型分布）
# ============================================================================


def test_metrics_type_distribution() -> None:
    """验证 10 指标类型分布：6 Counter + 2 Histogram + 2 Gauge。"""
    counters = {
        MEMORY_RECONCILE_TOTAL,
        MEMORY_DECAY_APPLIED_TOTAL,
        MEMORY_REINFORCE_TOTAL,
        MEMORY_GC_CLEANED_TOTAL,
        MEMORY_IN_PROCESS_CALL_TOTAL,
        MEMORY_RATE_LIMITED_TOTAL,
    }
    histograms = {
        MEMORY_RECONCILE_DURATION_SECONDS,
        MEMORY_ADMISSION_DURATION_SECONDS,
    }
    gauges = {
        MEMORY_PROMOTION_ELIGIBLE_TOTAL,
        MEMORY_BM25_INDEX_SIZE,
    }
    for c in counters:
        assert isinstance(c, Counter)
    for h in histograms:
        assert isinstance(h, Histogram)
    for g in gauges:
        assert isinstance(g, Gauge)


# pyright 兼容性：pytest 强制 import
_ = pytest
