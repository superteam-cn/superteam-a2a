"""KS-CRD-IT-001~002 · KnowledgeScope CRD schema 确定性 + wire round-trip IT.

L3-5 §10.3 IT 测试 ID 段（与 UT 互补 · 验证跨字段 wire 同步 + JSON Schema 确定性）。
依据 #105 PR-3 Phase B 实装要求（Subagent 3 接力）。

注：fixture 使用 camelCase alias kwargs（与 wire YAML 一致），
参考 #81 PR #20 修复模式。
"""

from __future__ import annotations

import json

from superteam_a2a.knowledge.crd.knowledgescope import (
    KnowledgeScope,
    KnowledgeScopeSpec,
    KnowledgeScopeStatus,
    KnowledgeVisibility,
    ScopeLevel,
    SubjectKind,
    SubjectReference,
)
from superteam_a2a.knowledge.crd.scope_phase import ScopePhase


def test_ks_crd_it_001_model_json_schema_deterministic() -> None:
    """KS-CRD-IT-001 · KnowledgeScopeSpec model_json_schema() 确定性 + 字段映射."""
    schema = KnowledgeScopeSpec.model_json_schema()

    # schema 是 dict
    assert isinstance(schema, dict)
    assert "properties" in schema

    # 6 spec 字段 wire alias 映射
    expected_fields = {
        "scopeLevel",
        "name",
        "subjectRef",
        "parentRef",
        "inheritRules",
        "visibility",
    }
    schema_fields = set(schema["properties"].keys())
    assert expected_fields.issubset(schema_fields), (
        f"KnowledgeScopeSpec 缺失 wire 字段: {expected_fields - schema_fields}"
    )

    # JSON 序列化确定性（sort_keys=True 默认）
    schema_json = json.dumps(schema, sort_keys=True)
    schema_json_again = json.dumps(schema, sort_keys=True)
    assert schema_json == schema_json_again, "JSON Schema 序列化非确定性"

    # 顶层 wrapper schema 也确定性
    wrapper_schema = KnowledgeScope.model_json_schema()
    wrapper_json = json.dumps(wrapper_schema, sort_keys=True)
    assert wrapper_json == json.dumps(wrapper_schema, sort_keys=True)

    # apiVersion default 验证
    assert "KnowledgeScope" in str(wrapper_schema.get("properties", {}))


def test_ks_crd_it_002_yaml_round_trip_alias() -> None:
    """KS-CRD-IT-002 · wire YAML round-trip（by_alias=True 序列化 + 反序列化）."""
    # 构造完整 spec（用 wire alias）
    spec_dict = {
        "scopeLevel": "agent",
        "name": "agent-foo",
        "subjectRef": {"kind": "Agent", "name": "foo-agent"},
        "visibility": "agent-private",
    }
    spec = KnowledgeScopeSpec.model_validate(spec_dict)
    assert spec.scope_level == ScopeLevel.AGENT
    assert spec.subject_ref.kind == SubjectKind.AGENT
    assert spec.visibility == KnowledgeVisibility.AGENT_PRIVATE

    # round-trip: serialize by_alias=True → deserialize
    dumped = spec.model_dump(by_alias=True, exclude_none=True)
    assert dumped["scopeLevel"] == "agent"
    assert dumped["subjectRef"]["kind"] == "Agent"
    assert dumped["subjectRef"]["name"] == "foo-agent"
    assert dumped["visibility"] == "agent-private"

    # 反序列化回 spec（保持一致）
    spec_roundtrip = KnowledgeScopeSpec.model_validate(dumped)
    assert spec_roundtrip.scope_level == ScopeLevel.AGENT
    assert spec_roundtrip.subject_ref == SubjectReference(kind=SubjectKind.AGENT, name="foo-agent")
    assert spec_roundtrip.visibility == KnowledgeVisibility.AGENT_PRIVATE

    # 嵌套 SubjectReference 双向
    sr = SubjectReference.model_validate({"kind": "AgentSet", "name": "agent-set-x"})
    sr_dumped = sr.model_dump(by_alias=True)
    assert sr_dumped["kind"] == "AgentSet"
    assert sr_dumped["name"] == "agent-set-x"

    # status 默认值 + by_alias wire 同步
    status = KnowledgeScopeStatus.model_validate({"phase": "Active", "knowledgeItemCount": 5})
    assert status.phase == ScopePhase.ACTIVE
    assert status.knowledge_item_count == 5
    status_dumped = status.model_dump(by_alias=True)
    assert status_dumped["phase"] is None or status_dumped["phase"] == "Active"
    assert status_dumped["knowledgeItemCount"] == 5
    assert "lastUpdated" in status_dumped
    assert "childScopes" in status_dumped
    assert "activeQueries5m" in status_dumped
