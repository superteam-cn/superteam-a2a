"""KS-CRD-UT-001 ~ KS-CRD-UT-005 · KnowledgeScope CRD schema tests.

依据 L3-5 Spec §3.1（KnowledgeScope CRD 6 spec + 6 status）。

注：测试 fixture 使用 alias kwargs（camelCase），以匹配 Pydantic v2 wire format ·
pyright 1.1.411 不完全支持 populate_by_name=True 的 snake_case kwargs 推断
（参考 #81 PR #20 修复模式）。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from superteam_a2a.knowledge.crd.inherit_rules import InheritRules
from superteam_a2a.knowledge.crd.knowledgescope import (
    KnowledgeScope,
    KnowledgeScopeSpec,
    KnowledgeScopeStatus,
    KnowledgeVisibility,
    ScopeLevel,
    SubjectKind,
    SubjectReference,
)
from superteam_a2a.knowledge.crd.scope_reference import ScopeReference


def test_ks_crd_ut_001_scope_level_enum() -> None:
    """KS-CRD-UT-001 · ScopeLevel StrEnum 4 值 + 字符串 round-trip."""
    # 4 值
    assert ScopeLevel.AGENT == "agent"
    assert ScopeLevel.AGENT_SET == "agentset"
    assert ScopeLevel.WORKFLOW == "workflow"
    assert ScopeLevel.SYSTEM == "system"
    # 字符串 round-trip
    assert ScopeLevel("agent") is ScopeLevel.AGENT
    assert ScopeLevel("system") is ScopeLevel.SYSTEM
    # 非法值抛错
    with pytest.raises(ValueError, match="invalid"):
        ScopeLevel("invalid")


def test_ks_crd_ut_002_subject_reference_frozen() -> None:
    """KS-CRD-UT-002 · SubjectReference frozen 实例不可变 + kind 枚举校验。"""
    sub_ref = SubjectReference.model_validate({"kind": "Agent", "name": "foo-agent"})
    assert sub_ref.kind == SubjectKind.AGENT
    assert sub_ref.name == "foo-agent"
    # frozen 实例不可变（属性赋值抛 ValidationError）
    with pytest.raises(ValidationError):
        sub_ref.name = "bar-agent"
    # 非法 kind 抛错
    with pytest.raises(ValidationError):
        SubjectReference.model_validate({"kind": "InvalidKind", "name": "foo"})
    # 合法 AgentSet
    sub2 = SubjectReference.model_validate({"kind": "AgentSet", "name": "agent-set-x"})
    assert sub2.kind == SubjectKind.AGENT_SET


def test_ks_crd_ut_003_scope_reference_validation() -> None:
    """KS-CRD-UT-003 · ScopeReference frozen + name 长度校验。"""
    scope_ref = ScopeReference.model_validate({"name": "agent-foo", "level": "agent"})
    assert scope_ref.name == "agent-foo"
    assert scope_ref.level == ScopeLevel.AGENT
    # 长度校验
    with pytest.raises(ValidationError):
        ScopeReference.model_validate({"name": ""})
    with pytest.raises(ValidationError):
        ScopeReference.model_validate({"name": "x" * 254})
    # 合法空 level
    sr2 = ScopeReference.model_validate({"name": "agent-foo"})
    assert sr2.level is None


def test_ks_crd_ut_004_inherit_rules_defaults_and_bounds() -> None:
    """KS-CRD-UT-004 · InheritRules 默认值 + maxDepth 边界（0-3）。"""
    rules = InheritRules.model_validate({})
    assert rules.max_depth == 3
    assert rules.allowed_child_levels == []
    assert rules.block_self_reference is False
    # by_alias 验证 wire 同步
    dumped = rules.model_dump(by_alias=True, exclude_none=True)
    assert dumped["maxDepth"] == 3
    assert dumped["allowedChildLevels"] == []
    assert dumped["blockSelfReference"] is False
    # 边界：maxDepth=4 越界
    with pytest.raises(ValidationError):
        InheritRules.model_validate({"maxDepth": 4})
    # 边界：maxDepth=-1 越界
    with pytest.raises(ValidationError):
        InheritRules.model_validate({"maxDepth": -1})
    # 边界：maxDepth=0 OK
    r0 = InheritRules.model_validate({"maxDepth": 0})
    assert r0.max_depth == 0
    # includeTypes max_length=11
    with pytest.raises(ValidationError):
        InheritRules.model_validate({"includeTypes": [f"t{i}" for i in range(12)]})


def test_ks_crd_ut_005_knowledge_visibility_5d_and_default() -> None:
    """KS-CRD-UT-005 · KnowledgeVisibility StrEnum 5 维 + spec 默认值 + alias round-trip。"""
    # 5 维
    assert KnowledgeVisibility.SCOPE_ONLY == "scope-only"
    assert KnowledgeVisibility.SCOPE_AND_CHILDREN == "scope-and-children"
    assert KnowledgeVisibility.PUBLIC_READABLE == "public-readable"
    assert KnowledgeVisibility.AGENT_PRIVATE == "agent-private"
    assert KnowledgeVisibility.SYSTEM_READONLY == "system-readonly"
    # spec 默认值（visible = SCOPE_AND_CHILDREN）
    spec = KnowledgeScopeSpec.model_validate(
        {
            "scopeLevel": "agent",
            "name": "agent-foo",
            "subjectRef": {"kind": "Agent", "name": "foo-agent"},
        }
    )
    assert spec.visibility == KnowledgeVisibility.SCOPE_AND_CHILDREN
    # by_alias dump 字段名 camelCase
    dumped = spec.model_dump(by_alias=True, exclude_none=True)
    assert "scopeLevel" in dumped
    assert "subjectRef" in dumped
    assert dumped["visibility"] == "scope-and-children"


def test_ks_crd_ut_006_knowledge_scope_wrapper_smoke() -> None:
    """KS-CRD-UT-006 (extra) · KnowledgeScope 顶层 wrapper 默认值 + status 可选。"""
    scope = KnowledgeScope.model_validate(
        {
            "spec": {
                "scopeLevel": "agent",
                "name": "agent-foo",
                "subjectRef": {"kind": "Agent", "name": "foo-agent"},
            }
        }
    )
    assert scope.api_version == "knowledge.superteam-a2a.io/v1alpha1"
    assert scope.kind == "KnowledgeScope"
    assert scope.status is None
    # status 显式赋值
    from superteam_a2a.knowledge.crd.scope_phase import ScopePhase

    status = KnowledgeScopeStatus.model_validate({"phase": "Active", "knowledgeItemCount": 3})
    assert status.phase == ScopePhase.ACTIVE
    assert status.knowledge_item_count == 3
