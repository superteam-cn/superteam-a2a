"""KI-CRD-IT-001~002 · KnowledgeItem CRD schema 确定性 + supersededBy 链 wire 同步 IT.

L3-5 §10.3 IT 测试 ID 段（与 UT 互补）。
依据 #105 PR-3 Phase B 实装要求（Subagent 3 接力）。

注：fixture 使用 camelCase alias kwargs（与 wire YAML 一致），
参考 #81 PR #20 修复模式。
"""

from __future__ import annotations

import json

from superteam_a2a.knowledge.crd.knowledgeitem import (
    DecayState,
    ItemPhase,
    ItemReference,
    KnowledgeItem,
    KnowledgeItemSpec,
    KnowledgeItemStatus,
    KnowledgeType,
)
from superteam_a2a.knowledge.crd.knowledgescope import ScopeReference


def test_ki_crd_it_001_model_json_schema_deterministic() -> None:
    """KI-CRD-IT-001 · KnowledgeItemSpec model_json_schema() 确定性 + 7 spec 字段."""
    schema = KnowledgeItemSpec.model_json_schema()

    # schema 是 dict
    assert isinstance(schema, dict)
    assert "properties" in schema

    # 7 spec 字段 wire alias 映射
    expected_fields = {
        "scopeRef",
        "knowledgeType",
        "content",
        "tags",
        "version",
        "supersededBy",
        "confidence",
    }
    schema_fields = set(schema["properties"].keys())
    assert expected_fields.issubset(schema_fields), (
        f"KnowledgeItemSpec 缺失 wire 字段: {expected_fields - schema_fields}"
    )

    # JSON 序列化确定性（sort_keys=True 默认）
    schema_json = json.dumps(schema, sort_keys=True)
    schema_json_again = json.dumps(schema, sort_keys=True)
    assert schema_json == schema_json_again, "JSON Schema 序列化非确定性"

    # status 7 字段（默认 fields）
    status_schema = KnowledgeItemStatus.model_json_schema()
    expected_status_fields = {
        "phase",
        "indexedAt",
        "lastAccessed",
        "accessCount24h",
        "bm25ScoreAvg",
        "decayState",
        "effectiveConfidence",
    }
    status_fields = set(status_schema["properties"].keys())
    assert expected_status_fields.issubset(status_fields), (
        f"KnowledgeItemStatus 缺失 wire 字段: {expected_status_fields - status_fields}"
    )

    # 顶层 wrapper schema 也确定性
    wrapper_schema = KnowledgeItem.model_json_schema()
    wrapper_json = json.dumps(wrapper_schema, sort_keys=True)
    assert wrapper_json == json.dumps(wrapper_schema, sort_keys=True)


def test_ki_crd_it_002_superseded_by_chain_wire_sync() -> None:
    """KI-CRD-IT-002 · supersededBy 链 wire 同步 + 7 spec 字段 round-trip + 7 status 字段."""
    # 构造完整 KI（带 supersededBy 链）
    spec_dict = {
        "scopeRef": {"name": "agent-foo", "level": "agent"},
        "knowledgeType": "factual",
        "content": "step 1: do X; step 2: do Y",
        "tags": ["onboarding", "core"],
        "version": 2,
        "supersededBy": {"name": "item-v3", "version": 3},
        "confidence": 0.9,
    }
    spec = KnowledgeItemSpec.model_validate(spec_dict)
    assert spec.knowledge_type == KnowledgeType.FACTUAL
    assert spec.superseded_by is not None
    assert spec.superseded_by == ItemReference(name="item-v3", version=3)

    # round-trip with by_alias
    dumped = spec.model_dump(by_alias=True, exclude_none=True)
    assert "supersededBy" in dumped
    assert dumped["supersededBy"]["name"] == "item-v3"
    assert dumped["supersededBy"]["version"] == 3
    assert dumped["knowledgeType"] == "factual"
    assert dumped["scopeRef"]["name"] == "agent-foo"
    assert dumped["scopeRef"]["level"] == "agent"
    assert dumped["tags"] == ["onboarding", "core"]
    assert dumped["confidence"] == 0.9

    # 反序列化回 spec（保持一致）
    spec_roundtrip = KnowledgeItemSpec.model_validate(dumped)
    assert spec_roundtrip.knowledge_type == KnowledgeType.FACTUAL
    assert spec_roundtrip.superseded_by == ItemReference(name="item-v3", version=3)
    assert spec_roundtrip.tags == ["onboarding", "core"]

    # status 字段验证 + 嵌套 DecayState alias wire 同步
    ds = DecayState.model_validate({"decayDays": 30, "accessCount24h": 5})
    status = KnowledgeItemStatus.model_validate(
        {"phase": "Active", "effectiveConfidence": 0.85, "decayState": {"decayDays": 30}}
    )
    assert status.phase == ItemPhase.ACTIVE
    assert status.effective_confidence == 0.85
    assert status.decay_state is not None
    assert status.decay_state.decay_days == 30

    dumped_status = status.model_dump(by_alias=True)
    assert dumped_status["phase"] == "Active"
    assert dumped_status["effectiveConfidence"] == 0.85
    assert dumped_status["decayState"]["decayDays"] == 30
    assert dumped_status["decayState"]["accessCount24h"] == 0

    # DecayState by_alias
    ds_dumped = ds.model_dump(by_alias=True, exclude_none=True)
    assert ds_dumped["decayDays"] == 30
    assert ds_dumped["accessCount24h"] == 5

    # 显式 visibility cross-ref（KI 复用 KS visibility 5 维）
    spec2 = KnowledgeItemSpec.model_validate(
        {
            "scopeRef": {"name": "agent-foo"},
            "knowledgeType": "factual",
            "content": "x",
        }
    )
    # KI 没有自己的 visibility 字段（KI 由 scopeRef 继承 visibility 矩阵）
    assert not hasattr(spec2, "visibility")

    # ScopeReference wire sync sanity
    sr = ScopeReference.model_validate({"name": "scope-x", "level": "system"})
    assert sr.name == "scope-x"
    assert sr.level is not None
    assert sr.level.value == "system"
