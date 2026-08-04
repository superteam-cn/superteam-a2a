"""Clock + SystemClock + FakeClock 单元测试 · TEST-MEM-031~034。

L3-6 §5.1 line 778：wall clock 仅用于 wire timestamps；deadline/节流/重试使用 monotonic()
                  漂移 <=5s 钳制为 0；>5s 显式失败并映射 MEMORY_INTERNAL_ERROR
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from superteam_a2a.knowledge_memory import (
    ClockSkewError,
    FakeClock,
    MemoryErrorCode,
    SystemClock,
    elapsed_non_negative,
)

# ============================================================================
# TEST-MEM-031 · SystemClock 返回 UTC aware datetime
# ============================================================================


def test_system_clock_returns_utc_aware_datetime():
    """TEST-MEM-031 · SystemClock.now() 必须是 UTC tz-aware datetime。"""
    clock = SystemClock()
    now = clock.now()
    assert isinstance(now, datetime)
    assert now.tzinfo is not None
    assert now.tzinfo == UTC


def test_system_clock_monotonic_is_float():
    """TEST-MEM-031 配套 · SystemClock.monotonic() 返回非负 float。"""
    clock = SystemClock()
    m = clock.monotonic()
    assert isinstance(m, float)
    assert m >= 0.0


# ============================================================================
# TEST-MEM-032 · FakeClock now/sleep/monotonic 同步推进
# ============================================================================


def test_fake_clock_now_returns_initial_time(base_time):
    """TEST-MEM-032 · FakeClock(base_time).now() == base_time。"""
    clock = FakeClock(base_time)
    assert clock.now() == base_time
    assert clock.now().tzinfo == UTC


def test_fake_clock_advance_updates_now_and_mono(fake_clock):
    """TEST-MEM-032 · advance(delta) 同时推进 now 与 monotonic。"""
    fake_clock.advance(timedelta(seconds=10))
    assert fake_clock.monotonic() == 10.0
    assert fake_clock.now() == datetime(2026, 8, 1, 12, 0, 10, tzinfo=UTC)


async def test_fake_clock_sleep_advances_time(fake_clock):
    """TEST-MEM-032 · await sleep(5) 等价于 advance(5s)。"""
    await fake_clock.sleep(5)
    assert fake_clock.monotonic() == 5.0


# ============================================================================
# TEST-MEM-033 · FakeClock 拒绝倒退
# ============================================================================


def test_fake_clock_rejects_naive_datetime():
    """TEST-MEM-033 · FakeClock 构造时拒绝 naive datetime。"""
    with pytest.raises(ValueError, match="aware datetime"):
        FakeClock(datetime(2026, 8, 1))  # type: ignore[arg-type]


def test_fake_clock_rejects_backward_advance(fake_clock):
    """TEST-MEM-033 · advance(负 delta) 抛 ValueError。"""
    with pytest.raises(ValueError, match="monotonic"):
        fake_clock.advance(timedelta(seconds=-1))


# ============================================================================
# TEST-MEM-034 · <=5s skew 钳制为 0；>5s 显式失败
# ============================================================================


def test_elapsed_non_negative_positive(base_time):
    """TEST-MEM-034 · 正常前进 → 返回正值。"""
    end = base_time + timedelta(seconds=30)
    assert elapsed_non_negative(base_time, end) == 30.0


def test_elapsed_non_negative_clamps_small_backward(base_time):
    """TEST-MEM-034 · 倒退 3s（<=5s tolerance）→ 钳制为 0。"""
    end = base_time - timedelta(seconds=3)
    assert elapsed_non_negative(base_time, end) == 0.0


def test_elapsed_non_negative_raises_on_large_backward(base_time):
    """TEST-MEM-034 · 倒退 10s（>5s tolerance）→ 抛 ClockSkewError。"""
    end = base_time - timedelta(seconds=10)
    with pytest.raises(ClockSkewError) as exc:
        elapsed_non_negative(base_time, end)
    assert exc.value.code == MemoryErrorCode.MEMORY_INTERNAL_ERROR
    assert exc.value.retryable is True


def test_elapsed_non_negative_custom_tolerance(base_time):
    """TEST-MEM-034 · 自定义 tolerance=30s。"""
    end = base_time - timedelta(seconds=10)
    assert elapsed_non_negative(base_time, end, tolerance_seconds=30.0) == 0.0
    with pytest.raises(ClockSkewError):
        elapsed_non_negative(base_time, end, tolerance_seconds=5.0)
