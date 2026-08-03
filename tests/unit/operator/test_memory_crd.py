"""Memory CRD 单元测试 · 覆盖 UT-MD-ME-01 ~ UT-MD-ME-12 子集。

依据 L3-1 Spec §6.2.1-§6.2.5 + 测试矩阵 L3-1 §9.2。
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from superteam_a2a.operator.models.memory import (
    AgentReference,
    MemoryCondition,
    MemoryConditionType,
    MemoryPhase,
    MemorySpec,
    MemoryStatus,
    MemoryVisibility,
    ScopeReference,
)


def _spec_kwargs(**overrides):
    """Return MemorySpec required-field kwargs (allows overrides)."""
    base = {
        "scope_ref": ScopeReference(name="industry-ai"),
        "agent_ref": AgentReference(name="hello-agent-sa"),
        "content": {"key1": "value1"},
        "summary": "Test memory",
    }
    base.update(overrides)
    return base


# UT-MD-ME-01
def test_memory_spec_happy_path():
    """TC1 · 12-field happy-path construction validates all defaults and required fields."""
    spec = MemorySpec(**_spec_kwargs())
    # Required fields preserved
    assert spec.scope_ref.name == "industry-ai"
    assert spec.agent_ref.name == "hello-agent-sa"
    assert spec.agent_ref.kind == "ServiceAccount"
    assert spec.content == {"key1": "value1"}
    assert spec.summary == "Test memory"
    # Defaults
    assert spec.confidence == 1.0
    assert spec.decay_days == 30
    assert spec.reinforced_count == 0
    assert spec.visibility == MemoryVisibility.SCOPE_AND_CHILDREN
    # Optional defaults (None)
    assert spec.last_reinforced_at is None
    assert spec.memory_key_pattern is None
    assert spec.source_knowledge_ref is None
    assert spec.tags is None


# UT-MD-ME-02
def test_memory_spec_rejects_extra_fields():
    """TC2 · extra='forbid' rejects unknown fields."""
    with pytest.raises(ValidationError) as exc:
        MemorySpec(**_spec_kwargs(unknown_field="bad"))
    msg = str(exc.value).lower()
    assert "extra" in msg or "forbid" in msg


# UT-MD-ME-03
def test_memory_spec_requires_scope_ref_and_agent_ref():
    """TC3 · scope_ref and agent_ref are required."""
    # missing scope_ref
    kwargs = _spec_kwargs()
    kwargs.pop("scope_ref")
    with pytest.raises(ValidationError):
        MemorySpec(**kwargs)
    # missing agent_ref
    kwargs = _spec_kwargs()
    kwargs.pop("agent_ref")
    with pytest.raises(ValidationError):
        MemorySpec(**kwargs)


# UT-MD-ME-04
def test_memory_spec_content_max_20_keys():
    """TC4 · content keys must be in [1, 20]."""
    # 0 keys -> ValidationError
    with pytest.raises(ValidationError):
        MemorySpec(**_spec_kwargs(content={}))
    # 21 keys -> ValidationError
    with pytest.raises(ValidationError):
        MemorySpec(**_spec_kwargs(content={f"k{i}": "v" for i in range(21)}))
    # 1 key OK
    spec = MemorySpec(**_spec_kwargs(content={"k": "v"}))
    assert spec.content == {"k": "v"}
    # 20 keys OK
    spec = MemorySpec(**_spec_kwargs(content={f"k{i}": "v" for i in range(20)}))
    assert len(spec.content) == 20


# UT-MD-ME-05
def test_memory_spec_confidence_bounds():
    """TC5 · confidence in [0.0, 1.0]."""
    spec = MemorySpec(**_spec_kwargs(confidence=0.0))
    assert spec.confidence == 0.0
    spec = MemorySpec(**_spec_kwargs(confidence=1.0))
    assert spec.confidence == 1.0
    with pytest.raises(ValidationError):
        MemorySpec(**_spec_kwargs(confidence=-0.01))
    with pytest.raises(ValidationError):
        MemorySpec(**_spec_kwargs(confidence=1.01))


# UT-MD-ME-06
def test_memory_spec_decay_days_bounds():
    """TC6 · decay_days in [1, 3650]."""
    spec = MemorySpec(**_spec_kwargs(decay_days=1))
    assert spec.decay_days == 1
    spec = MemorySpec(**_spec_kwargs(decay_days=3650))
    assert spec.decay_days == 3650
    with pytest.raises(ValidationError):
        MemorySpec(**_spec_kwargs(decay_days=0))
    with pytest.raises(ValidationError):
        MemorySpec(**_spec_kwargs(decay_days=3651))


# UT-MD-ME-07
def test_memory_spec_tags_max_10():
    """TC7 · tags max 10 entries."""
    spec = MemorySpec(**_spec_kwargs(tags=[f"t{i}" for i in range(10)]))
    assert spec.tags is not None
    assert len(spec.tags) == 10
    with pytest.raises(ValidationError):
        MemorySpec(**_spec_kwargs(tags=[f"t{i}" for i in range(11)]))
    # Empty list OK
    spec = MemorySpec(**_spec_kwargs(tags=[]))
    assert spec.tags == []


# UT-MD-ME-08
def test_memory_spec_visibility_default():
    """TC8 · visibility default is SCOPE_AND_CHILDREN."""
    spec = MemorySpec(**_spec_kwargs())
    assert spec.visibility == MemoryVisibility.SCOPE_AND_CHILDREN
    # All 3 values accepted
    for v in [
        MemoryVisibility.SCOPE_ONLY,
        MemoryVisibility.SCOPE_AND_CHILDREN,
        MemoryVisibility.AGENT_PRIVATE,
    ]:
        spec = MemorySpec(**_spec_kwargs(visibility=v))
        assert spec.visibility == v


# UT-MD-ME-09
def test_memory_status_phase_enum():
    """TC9 · MemoryPhase 5-value enum serialisation."""
    phases = [
        MemoryPhase.ACTIVE,
        MemoryPhase.DECAYING,
        MemoryPhase.PROMOTABLE,
        MemoryPhase.EXPIRED,
        MemoryPhase.ERROR,
    ]
    expected_values = {"Active", "Decaying", "Promotable", "Expired", "Error"}
    for phase in phases:
        status = MemoryStatus(phase=phase)
        assert status.phase == phase
    # Verify all 5 distinct values match expected wire strings
    assert {p.value for p in phases} == expected_values


# UT-MD-ME-10
def test_memory_condition_required_transition_time():
    """TC10 · MemoryCondition 5 types + last_transition_time required & tz-aware."""
    ctypes = [
        MemoryConditionType.DECAYED,
        MemoryConditionType.REINFORCED,
        MemoryConditionType.PROMOTED,
        MemoryConditionType.ARCHIVED,
        MemoryConditionType.GARBAGE_COLLECTED,
    ]
    ts = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)
    for ctype in ctypes:
        cond = MemoryCondition(type=ctype, status="True", lastTransitionTime=ts)
        assert cond.type == ctype
        assert cond.last_transition_time is not None
        assert cond.last_transition_time.tzinfo is not None
        assert cond.last_transition_time == ts
    # missing lastTransitionTime -> ValidationError
    with pytest.raises(ValidationError):
        MemoryCondition(type=MemoryConditionType.DECAYED, status="True")  # type: ignore[call-arg]
    # naive datetime -> ValidationError (AwareDatetime enforcement)
    with pytest.raises(ValidationError):
        MemoryCondition(
            type=MemoryConditionType.DECAYED,
            status="True",
            lastTransitionTime=datetime(2026, 8, 1, 12, 0, 0),  # type: ignore[arg-type]
        )


# UT-MD-ME-11
def test_memory_spec_alias_dump_camel_case():
    """TC11 · model_dump(by_alias=True) emits wire YAML field names."""
    spec = MemorySpec(
        **_spec_kwargs(
            decay_days=60,
            reinforced_count=5,
            memory_key_pattern="pattern:x",
        )
    )
    dumped = spec.model_dump(by_alias=True, exclude_none=True)
    # Alias keys present
    assert "scopeRef" in dumped
    assert "agentRef" in dumped
    assert "decayDays" in dumped
    assert "reinforcedCount" in dumped
    assert "memoryKeyPattern" in dumped
    # Alias values correct
    assert dumped["decayDays"] == 60
    assert dumped["reinforcedCount"] == 5
    assert dumped["memoryKeyPattern"] == "pattern:x"
    # snake_case keys must NOT appear in wire YAML
    assert "scope_ref" not in dumped
    assert "agent_ref" not in dumped
    assert "decay_days" not in dumped
    assert "reinforced_count" not in dumped
    assert "memory_key_pattern" not in dumped


# UT-MD-ME-12
def test_memory_spec_json_schema_deterministic():
    """TC12 · model_json_schema() emits camelCase properties & correct required set."""
    schema = MemorySpec.model_json_schema()
    props = schema["properties"]
    # camelCase wire fields present
    assert "scopeRef" in props
    assert "agentRef" in props
    assert "decayDays" in props
    assert "reinforcedCount" in props
    assert "lastReinforcedAt" in props
    assert "memoryKeyPattern" in props
    assert "sourceKnowledgeRef" in props
    # snake_case Python names must NOT appear
    assert "scope_ref" not in props
    assert "agent_ref" not in props
    assert "decay_days" not in props
    assert "reinforced_count" not in props
    # required field set
    assert "required" in schema
    assert set(schema["required"]) == {"scopeRef", "agentRef", "content", "summary"}
    # additionalProperties: false (extra=forbid)
    assert schema.get("additionalProperties") is False
