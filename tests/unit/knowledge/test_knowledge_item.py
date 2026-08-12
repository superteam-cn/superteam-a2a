"""KI-CRD-UT-001 ~ KI-CRD-UT-007 · KnowledgeItem CRD schema tests.

依据 L3-5 Spec §3.2（KnowledgeItem CRD 7 spec + 7 status）。

注：测试 fixture 使用 alias kwargs（camelCase），以匹配 Pydantic v2 wire format ·
pyright 1.1.411 不完全支持 populate_by_name=True 的 snake_case kwargs 推断
（参考 #81 PR #20 修复模式）。populate_by_name 双向已在 #81 UT-04 验证。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from superteam_a2a.knowledge.crd.knowledgeitem import (
    DecayState,
    ItemPhase,
    ItemReference,
    KnowledgeItem,
    KnowledgeItemSpec,
    KnowledgeItemStatus,
    KnowledgeType,
)


def test_ki_crd_ut_001_spec_7_fields() -> None:
    """KI-CRD-UT-001 · KnowledgeItemSpec 7 字段 Pydantic 校验。"""
    spec = KnowledgeItemSpec.model_validate(
        {
            "scopeRef": {"name": "agent-foo", "level": "agent"},
            "knowledgeType": "procedural",
            "content": "step 1: do X; step 2: do Y",
            "tags": ["onboarding", "core"],
            "version": 2,
            "confidence": 0.9,
        }
    )
    assert spec.knowledge_type == KnowledgeType.PROCEDURAL
    assert spec.content == "step 1: do X; step 2: do Y"
    assert spec.tags == ["onboarding", "core"]
    assert spec.version == 2
    assert spec.confidence == 0.9
    # default
    assert spec.superseded_by is None


def test_ki_crd_ut_002_knowledge_type_4_values() -> None:
    """KI-CRD-UT-002 · KnowledgeType StrEnum 4 类（procedural/factual/episodic/conceptual）。"""
    assert KnowledgeType.PROCEDURAL == "procedural"
    assert KnowledgeType.FACTUAL == "factual"
    assert KnowledgeType.EPISODIC == "episodic"
    assert KnowledgeType.CONCEPTUAL == "conceptual"
    # round-trip
    assert KnowledgeType("episodic") is KnowledgeType.EPISODIC
    with pytest.raises(ValueError, match="invalid"):
        KnowledgeType("invalid")


def test_ki_crd_ut_003_item_reference_frozen() -> None:
    """KI-CRD-UT-003 · ItemReference frozen + version 必填 + version 边界（ge=1）。"""
    ref = ItemReference.model_validate({"name": "item-v2", "version": 2})
    assert ref.name == "item-v2"
    assert ref.version == 2
    # frozen 实例不可变
    with pytest.raises(ValidationError):
        ref.name = "item-v3"
    # version ge=1 校验
    with pytest.raises(ValidationError):
        ItemReference.model_validate({"name": "item-x", "version": 0})
    with pytest.raises(ValidationError):
        ItemReference.model_validate({"name": "item-x", "version": -1})


def test_ki_crd_ut_004_decay_state_nested() -> None:
    """KI-CRD-UT-004 · DecayState 嵌套字段 + 默认值 + decayDays 边界。"""
    # 默认值
    ds = DecayState.model_validate({})
    assert ds.access_count_24h == 0
    assert ds.decay_days == 90
    assert ds.last_accessed is None
    # 自定义
    ds2 = DecayState.model_validate({"decayDays": 30, "accessCount24h": 5})
    assert ds2.decay_days == 30
    assert ds2.access_count_24h == 5
    # decayDays 边界（1-3650）
    with pytest.raises(ValidationError):
        DecayState.model_validate({"decayDays": 0})
    with pytest.raises(ValidationError):
        DecayState.model_validate({"decayDays": 3651})
    # by_alias
    dumped = ds2.model_dump(by_alias=True, exclude_none=True)
    assert "decayDays" in dumped
    assert "accessCount24h" in dumped


def test_ki_crd_ut_005_superseded_by_chain_wire() -> None:
    """KI-CRD-UT-005 · supersededBy 链 wire 同步 + by_alias dump。"""
    spec = KnowledgeItemSpec.model_validate(
        {
            "scopeRef": {"name": "agent-foo"},
            "knowledgeType": "factual",
            "content": "some content",
            "supersededBy": {"name": "item-v3", "version": 3},
        }
    )
    assert spec.superseded_by is not None
    assert spec.superseded_by.name == "item-v3"
    # by_alias
    dumped = spec.model_dump(by_alias=True, exclude_none=True)
    assert "supersededBy" in dumped
    assert dumped["supersededBy"]["name"] == "item-v3"
    assert dumped["supersededBy"]["version"] == 3


def test_ki_crd_ut_006_tags_length_max_20() -> None:
    """KI-CRD-UT-006 · tags 长度校验（max_length=20）+ default None。"""
    # 默认 None
    spec0 = KnowledgeItemSpec.model_validate(
        {
            "scopeRef": {"name": "agent-foo"},
            "knowledgeType": "factual",
            "content": "x",
        }
    )
    assert spec0.tags is None
    # 20 OK
    spec20 = KnowledgeItemSpec.model_validate(
        {
            "scopeRef": {"name": "agent-foo"},
            "knowledgeType": "factual",
            "content": "x",
            "tags": [f"t{i}" for i in range(20)],
        }
    )
    assert spec20.tags is not None
    assert len(spec20.tags) == 20
    # 21 失败
    with pytest.raises(ValidationError):
        KnowledgeItemSpec.model_validate(
            {
                "scopeRef": {"name": "agent-foo"},
                "knowledgeType": "factual",
                "content": "x",
                "tags": [f"t{i}" for i in range(21)],
            }
        )


def test_ki_crd_ut_007_item_phase_state_machine() -> None:
    """KI-CRD-UT-007 · ItemPhase StrEnum 5 态（Indexing/Active/Decaying/Superseded/Archived）。"""
    assert ItemPhase.INDEXING == "Indexing"
    assert ItemPhase.ACTIVE == "Active"
    assert ItemPhase.DECAYING == "Decaying"
    assert ItemPhase.SUPERSEDED == "Superseded"
    assert ItemPhase.ARCHIVED == "Archived"
    # status 默认值
    status = KnowledgeItemStatus.model_validate({})
    assert status.phase is None
    assert status.access_count_24h == 0
    assert status.effective_confidence is None
    # status 显式赋值
    status2 = KnowledgeItemStatus.model_validate({"phase": "Decaying", "effectiveConfidence": 0.4})
    assert status2.phase == ItemPhase.DECAYING
    assert status2.effective_confidence == 0.4
    # effectiveConfidence 边界（0-1）
    with pytest.raises(ValidationError):
        KnowledgeItemStatus.model_validate({"effectiveConfidence": -0.1})
    with pytest.raises(ValidationError):
        KnowledgeItemStatus.model_validate({"effectiveConfidence": 1.1})


def test_ki_crd_ut_008_content_length_bounds() -> None:
    """KI-CRD-UT-008 (extra) · content min/max 长度校验（1-65536）。"""
    base = {
        "scopeRef": {"name": "agent-foo"},
        "knowledgeType": "factual",
    }
    # content="" 失败（min=1）
    with pytest.raises(ValidationError):
        KnowledgeItemSpec.model_validate({**base, "content": ""})
    # content 65537 失败（max=65536）
    with pytest.raises(ValidationError):
        KnowledgeItemSpec.model_validate({**base, "content": "x" * 65537})
    # content 1 OK
    spec1 = KnowledgeItemSpec.model_validate({**base, "content": "x"})
    assert spec1.content == "x"


def test_ki_crd_ut_009_wrapper_smoke() -> None:
    """KI-CRD-UT-009 (extra) · KnowledgeItem 顶层 wrapper 默认值。"""
    item = KnowledgeItem.model_validate(
        {
            "spec": {
                "scopeRef": {"name": "agent-foo"},
                "knowledgeType": "factual",
                "content": "x",
            }
        }
    )
    assert item.api_version == "knowledge.superteam-a2a.io/v1alpha1"
    assert item.kind == "KnowledgeItem"
    assert item.status is None
