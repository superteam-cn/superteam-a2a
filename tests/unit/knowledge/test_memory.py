"""MEM-CRD-UT-001 ~ MEM-CRD-UT-005 · Memory CRD schema tests.

依据 L3-5 Spec §3.3（Memory schema 5 spec + 5 status）。

注：测试 fixture 使用 alias kwargs（camelCase），以匹配 Pydantic v2 wire format ·
pyright 1.1.411 不完全支持 populate_by_name=True 的 snake_case kwargs 推断
（参考 #81 PR #20 修复模式）。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from superteam_a2a.knowledge.crd.memory_schema import (
    AgentReference,
    GCState,
    Memory,
    MemoryPhase,
    MemorySpec,
    MemoryStatus,
)


def test_mem_crd_ut_001_spec_5_fields() -> None:
    """MEM-CRD-UT-001 · MemorySpec 5 字段校验 + 默认值。"""
    spec = MemorySpec.model_validate(
        {
            "scopeRef": {"name": "agent-foo"},
            "agentRef": {"kind": "ServiceAccount", "name": "foo-agent"},
            "content": {"key1": "value1"},
            "decayDays": 30,
            "confidence": 0.8,
        }
    )
    assert spec.decay_days == 30
    assert spec.confidence == 0.8
    assert spec.scope_ref.name == "agent-foo"
    assert spec.agent_ref.name == "foo-agent"
    assert spec.content == {"key1": "value1"}
    # 默认值
    spec_default = MemorySpec.model_validate(
        {
            "scopeRef": {"name": "agent-foo"},
            "agentRef": {"name": "foo-agent"},
            "content": {"k": "v"},
        }
    )
    assert spec_default.confidence == 1.0
    assert spec_default.decay_days == 30


def test_mem_crd_ut_002_memory_phase_5_states() -> None:
    """MEM-CRD-UT-002 · MemoryPhase StrEnum 5 态。"""
    assert MemoryPhase.ACTIVE == "Active"
    assert MemoryPhase.DECAYING == "Decaying"
    assert MemoryPhase.PROMOTABLE == "Promotable"
    assert MemoryPhase.EXPIRED == "Expired"
    assert MemoryPhase.ERROR == "Error"
    # round-trip
    assert MemoryPhase("Promotable") is MemoryPhase.PROMOTABLE
    with pytest.raises(ValueError, match="invalid"):
        MemoryPhase("invalid")
    # status 默认值
    status = MemoryStatus.model_validate({})
    assert status.phase is None
    # status 显式
    status2 = MemoryStatus.model_validate({"phase": "Decaying"})
    assert status2.phase == MemoryPhase.DECAYING


def test_mem_crd_ut_003_gc_state_4_states() -> None:
    """MEM-CRD-UT-003 · GCState StrEnum 4 态（None/Pending/Cleaned/Kept）。"""
    assert GCState.NONE == "None"
    assert GCState.PENDING == "Pending"
    assert GCState.CLEANED == "Cleaned"
    assert GCState.KEPT == "Kept"
    # GCState 不暴露在 MemoryStatus（spec 字段集外），仅作 enum 测试
    # spec 字段集：phase / observedGeneration / conditions / lastUpdated / effectiveConfidence


def test_mem_crd_ut_004_decay_days_and_confidence_bounds() -> None:
    """MEM-CRD-UT-004 · decayDays 边界（0-3650）+ confidence 边界（0.0-1.0）。"""
    base = {
        "scopeRef": {"name": "agent-foo"},
        "agentRef": {"name": "foo-agent"},
        "content": {"k": "v"},
    }
    # 边界 0 OK
    spec0 = MemorySpec.model_validate({**base, "decayDays": 0, "confidence": 0.0})
    assert spec0.decay_days == 0
    assert spec0.confidence == 0.0
    # 边界 3650 OK
    spec_max = MemorySpec.model_validate({**base, "decayDays": 3650, "confidence": 1.0})
    assert spec_max.decay_days == 3650
    # 超界 3651 失败
    with pytest.raises(ValidationError):
        MemorySpec.model_validate({**base, "decayDays": 3651})
    # 超界 1.1 失败
    with pytest.raises(ValidationError):
        MemorySpec.model_validate({**base, "confidence": 1.1})
    # 负值失败
    with pytest.raises(ValidationError):
        MemorySpec.model_validate({**base, "decayDays": -1})
    with pytest.raises(ValidationError):
        MemorySpec.model_validate({**base, "confidence": -0.1})


def test_mem_crd_ut_005_status_defaults_and_effective_confidence() -> None:
    """MEM-CRD-UT-005 · MemoryStatus 默认值 + effectiveConfidence 边界 + alias wire。"""
    # 默认值
    status = MemoryStatus.model_validate({})
    assert status.phase is None
    assert status.observed_generation is None
    assert status.conditions == []
    assert status.last_updated is None
    assert status.effective_confidence is None
    # by_alias dump（不 exclude_none，确保所有 wire 字段存在）
    dumped = status.model_dump(by_alias=True)
    assert dumped["phase"] is None
    assert dumped["observedGeneration"] is None
    assert dumped["lastUpdated"] is None
    assert dumped["effectiveConfidence"] is None
    assert dumped["conditions"] == []
    # 衰减公式仅作为 schema 字段定义；纯函数推迟到 PR-4
    # 验证 effectiveConfidence 接受 [0.0, 1.0]
    status_ok = MemoryStatus.model_validate({"effectiveConfidence": 0.5})
    assert status_ok.effective_confidence == 0.5


def test_mem_crd_ut_006_content_max_20_keys() -> None:
    """MEM-CRD-UT-006 (extra) · content max_length=20 keys + min_length=1。"""
    base = {
        "scopeRef": {"name": "agent-foo"},
        "agentRef": {"name": "foo-agent"},
    }
    # 0 keys 失败
    with pytest.raises(ValidationError):
        MemorySpec.model_validate({**base, "content": {}})
    # 21 keys 失败
    with pytest.raises(ValidationError):
        MemorySpec.model_validate({**base, "content": {f"k{i}": "v" for i in range(21)}})
    # 20 keys OK
    spec20 = MemorySpec.model_validate({**base, "content": {f"k{i}": "v" for i in range(20)}})
    assert len(spec20.content) == 20


def test_mem_crd_ut_007_wrapper_smoke() -> None:
    """MEM-CRD-UT-007 (extra) · Memory 顶层 wrapper 默认值。"""
    mem = Memory.model_validate(
        {
            "spec": {
                "scopeRef": {"name": "agent-foo"},
                "agentRef": {"name": "foo-agent"},
                "content": {"k": "v"},
            }
        }
    )
    assert mem.api_version == "memory.superteam-a2a.io/v1alpha1"
    assert mem.kind == "Memory"
    assert mem.status is None


def test_mem_crd_ut_008_agent_reference_default_kind() -> None:
    """MEM-CRD-UT-008 (extra) · AgentReference kind 默认 ServiceAccount。"""
    ar = AgentReference.model_validate({"name": "foo-agent"})
    assert ar.kind == "ServiceAccount"
    # frozen 实例不可变
    with pytest.raises(ValidationError):
        ar.name = "bar-agent"
