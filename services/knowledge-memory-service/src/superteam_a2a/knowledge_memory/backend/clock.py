"""Clock Protocol + SystemClock + FakeClock · L3-6 §5.1 + §5.2。

- 计算函数同步、stateless、不可变；I/O 仅在 MemoryBackend adapter 中
- Clock 作为参数注入，禁止函数内部读取系统时间
- wall clock 仅用于 wire timestamps；deadline/节流/重试使用 monotonic()
- 漂移 <=5s 钳制为 0，>5s 显式失败映射 MEMORY_INTERNAL_ERROR
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta
from typing import Protocol, runtime_checkable

from superteam_a2a.knowledge_memory.backend.errors import (
    ClockSkewError,
    MemoryErrorCode,
)

# ============================================================================
# §5.1 Clock Protocol
# ============================================================================


@runtime_checkable
class Clock(Protocol):
    """时间源抽象。production 注入 SystemClock，测试注入 FakeClock。"""

    def now(self) -> datetime:
        """UTC aware datetime · 用于 wire timestamps。"""
        ...

    async def sleep(self, delay: float) -> None:
        """async sleep · 不阻塞 caller event loop。"""
        ...

    def monotonic(self) -> float:
        """单调时钟秒数 · 用于 deadline/节流/重试（不被 wall clock skew 影响）。"""
        ...


# ============================================================================
# §5.1 elapsed_non_negative · clock-skew 容忍
# ============================================================================


def elapsed_non_negative(
    start: datetime,
    end: datetime,
    *,
    tolerance_seconds: float = 5.0,
) -> float:
    """计算 elapsed seconds · 钳制负漂移到 0；超出 tolerance 显式失败。

    依据 §5.1 line 778：wall clock 仅用于 wire timestamps；
    漂移 <=5s 钳制为 0，>5s 显式失败并映射 MEMORY_INTERNAL_ERROR。
    """
    skew = (end - start).total_seconds()
    if skew < -tolerance_seconds:
        raise ClockSkewError(
            MemoryErrorCode.MEMORY_INTERNAL_ERROR,
            f"wall clock moved backward beyond tolerance ({tolerance_seconds}s)",
        )
    return max(skew, 0.0)


# ============================================================================
# §5.2 SystemClock · 生产实现
# ============================================================================


class SystemClock:
    """生产 Clock · 包装 datetime.now(UTC) + asyncio.sleep + time.monotonic。"""

    def now(self) -> datetime:
        return datetime.now(UTC)

    async def sleep(self, delay: float) -> None:
        await asyncio.sleep(delay)

    def monotonic(self) -> float:
        return time.monotonic()


# ============================================================================
# §5.2 FakeClock · 测试实现（不得 monkeypatch datetime.now）
# ============================================================================


class FakeClock:
    """测试 Clock · 显式 advance；不允许倒退（§5.2 line 810-814）。"""

    def __init__(self, start: datetime) -> None:
        if start.tzinfo is None:
            raise ValueError("FakeClock requires aware datetime")
        self._now: datetime = start.astimezone(UTC)
        self._mono: float = 0.0

    def now(self) -> datetime:
        return self._now

    async def sleep(self, delay: float) -> None:
        self.advance(timedelta(seconds=delay))

    def monotonic(self) -> float:
        return self._mono

    def advance(self, delta: timedelta) -> None:
        if delta.total_seconds() < 0:
            raise ValueError("FakeClock is monotonic")
        self._now += delta
        self._mono += delta.total_seconds()


__all__ = [
    "Clock",
    "FakeClock",
    "SystemClock",
    "elapsed_non_negative",
]
