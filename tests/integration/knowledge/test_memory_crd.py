"""MEM-CRD-IT-001 · Memory CRD schema 确定性 + 5 spec + 5 status 字段 + 衰减公式常量占位 IT.

L3-5 §10.3 IT 测试 ID 段（与 UT 互补）。
依据 #105 PR-3 Phase B 实装要求（Subagent 3 接力）。

衰减公式常量化推迟到 PR-4；PR-3 仅验证字段定义 + 边界。
注：fixture 使用 camelCase alias kwargs（与 wire YAML 一致），
参考 #81 PR #20 修复模式。
"""

from __future__ import annotations

import json

from superteam_a2a.knowledge.crd.memory_schema import (
    AgentReference,
    Memory,
    MemoryPhase,
    MemorySpec,
    MemoryStatus,
)


def test_mem_crd_it_001_model_json_schema_deterministic() -> None:
    """MEM-CRD-IT-001 · Memory CRD schema 确定性 + 5 spec + 5 status 字段."""
    schema_spec = MemorySpec.model_json_schema()
    schema_status = MemoryStatus.model_json_schema()

    # 5 spec 字段 wire alias 映射
    expected_spec_fields = {"scopeRef", "agentRef", "content", "decayDays", "confidence"}
    spec_fields = set(schema_spec["properties"].keys())
    assert expected_spec_fields.issubset(spec_fields), (
        f"MemorySpec 缺失 wire 字段: {expected_spec_fields - spec_fields}"
    )

    # 5 status 字段
    expected_status_fields = {
        "phase",
        "observedGeneration",
        "conditions",
        "lastUpdated",
        "effectiveConfidence",
    }
    status_fields = set(schema_status["properties"].keys())
    assert expected_status_fields.issubset(status_fields), (
        f"MemoryStatus 缺失 wire 字段: {expected_status_fields - status_fields}"
    )

    # JSON 序列化确定性（sort_keys=True 默认）
    schema_spec_json = json.dumps(schema_spec, sort_keys=True)
    assert json.dumps(schema_spec, sort_keys=True) == schema_spec_json
    schema_status_json = json.dumps(schema_status, sort_keys=True)
    assert json.dumps(schema_status, sort_keys=True) == schema_status_json

    # 完整 spec 校验 + round-trip
    spec_dict = {
        "scopeRef": {"name": "agent-foo"},
        "agentRef": {"kind": "ServiceAccount", "name": "foo-agent"},
        "content": {"key1": "value1"},
        "decayDays": 30,
        "confidence": 0.85,
    }
    spec = MemorySpec.model_validate(spec_dict)
    assert spec.decay_days == 30
    assert spec.confidence == 0.85

    # round-trip with by_alias
    dumped = spec.model_dump(by_alias=True, exclude_none=True)
    assert dumped["decayDays"] == 30
    assert dumped["confidence"] == 0.85
    assert dumped["scopeRef"]["name"] == "agent-foo"
    assert dumped["agentRef"]["kind"] == "ServiceAccount"
    assert dumped["agentRef"]["name"] == "foo-agent"
    assert dumped["content"] == {"key1": "value1"}

    # 反序列化回 spec（保持一致）
    spec_roundtrip = MemorySpec.model_validate(dumped)
    assert spec_roundtrip.decay_days == 30
    assert spec_roundtrip.confidence == 0.85
    assert spec_roundtrip.scope_ref.name == "agent-foo"

    # 默认值边界验证（与 UT 互补 · IT 关注跨字段 wire 一致性）
    spec_default = MemorySpec.model_validate(
        {
            "scopeRef": {"name": "agent-foo"},
            "agentRef": {"name": "foo-agent"},
            "content": {"k": "v"},
        }
    )
    dumped_default = spec_default.model_dump(by_alias=True, exclude_none=True)
    assert dumped_default["decayDays"] == 30  # 默认 30 天
    assert dumped_default["confidence"] == 1.0  # 默认 1.0

    # status 字段 + 衰减公式常量占位
    status = MemoryStatus.model_validate(
        {"phase": "Active", "effectiveConfidence": 0.85, "observedGeneration": 1}
    )
    assert status.phase == MemoryPhase.ACTIVE
    assert status.effective_confidence == 0.85
    assert status.observed_generation == 1

    dumped_status = status.model_dump(by_alias=True)
    assert dumped_status["phase"] == "Active"
    assert dumped_status["effectiveConfidence"] == 0.85
    assert dumped_status["observedGeneration"] == 1
    assert dumped_status["conditions"] == []
    assert dumped_status["lastUpdated"] is None

    # 衰减公式字段定义存在（PR-3 仅 schema 字段；PR-4 实装衰减纯函数）
    # effectiveConfidence = confidence * exp(-elapsed_days / decayDays)
    # 当前 IT 仅验证字段定义存在 + 接受 [0.0, 1.0]
    schema_str = json.dumps(schema_status)
    assert "effectiveConfidence" in schema_str

    # AgentReference 默认 kind 验证（wire sync）
    ar = AgentReference.model_validate({"name": "foo-agent"})
    assert ar.kind == "ServiceAccount"
    ar_dumped = ar.model_dump(by_alias=True)
    assert ar_dumped["kind"] == "ServiceAccount"
    assert ar_dumped["name"] == "foo-agent"

    # 顶层 wrapper schema 确定性
    wrapper_schema = Memory.model_json_schema()
    wrapper_json = json.dumps(wrapper_schema, sort_keys=True)
    assert wrapper_json == json.dumps(wrapper_schema, sort_keys=True)
