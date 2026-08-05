"""InProcessContext unit tests · 3 测试 · 验证 frozen + extra=forbid + deadline 校验。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from superteam_a2a.knowledge_memory import FakeClock
from superteam_a2a.knowledge_memory.api.context import InProcessContext


def test_in_process_context_is_frozen(fake_clock):
    """构造后修改 clock 字段应抛 ValidationError（frozen=True）。"""
    ctx = InProcessContext(clock=fake_clock)
    with pytest.raises(ValidationError):
        ctx.clock = FakeClock(fake_clock.now())  # type: ignore[misc]


def test_in_process_context_rejects_extra_field(fake_clock):
    """构造时传入未声明字段应抛 ValidationError（extra=forbid）。"""
    with pytest.raises(ValidationError):
        InProcessContext(clock=fake_clock, bogus_field=42)  # type: ignore[call-arg]


def test_in_process_context_validates_deadline_negative(fake_clock):
    """构造 deadline_monotonic=-1.0 应抛 ValidationError（ge=0.0）。"""
    with pytest.raises(ValidationError):
        InProcessContext(clock=fake_clock, deadline_monotonic=-1.0)
