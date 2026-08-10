"""L4-Phase3 PR-3 8 枚举封闭性测试（L3-6 §7.1 line 1060 强类型约束）。

依据 docs/phase3/pr3-25-metrics-plan.md §4 阶段 D 测试要求：
- 8 测试函数（每个枚举 1 个）· 集合精确匹配
- + 1 个测试：8 枚举都是 StrEnum 子类
- 禁止 `memory_name` / `service_account` / `scope_name` / `request_id` 进入 label
"""

from __future__ import annotations

import sys
from enum import StrEnum
from pathlib import Path

# ============================================================================
# 路径前置（与 api/conftest.py 模式一致）
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

from superteam_a2a.knowledge_memory.observability.labels import (  # noqa: E402
    GCState,
    Method,
    Phase,
    PrincipalType,
    Result,
    ScopeLevel,
    Validator,
    Visibility,
)

# ============================================================================
# 8 枚举封闭性测试
# ============================================================================


def test_phase_enum_closed() -> None:
    """Phase 枚举封闭集合 = {admit, reconcile, finalize}（L3-6 §7.1 line 1060）。"""
    assert {p.value for p in Phase} == {"admit", "reconcile", "finalize"}


def test_result_enum_closed() -> None:
    """Result 枚举封闭集合 = {success, error, conflict, cancelled}。"""
    assert {r.value for r in Result} == {"success", "error", "conflict", "cancelled"}


def test_gc_state_enum_closed() -> None:
    """GCState 枚举封闭集合 = {expired, archived, superseded}。"""
    assert {g.value for g in GCState} == {"expired", "archived", "superseded"}


def test_visibility_enum_closed() -> None:
    """Visibility 枚举封闭集合 = {private, team, org, industry}。"""
    assert {v.value for v in Visibility} == {"private", "team", "org", "industry"}


def test_scope_level_enum_closed() -> None:
    """ScopeLevel 枚举封闭集合 = {agent, team, org, industry, global}。"""
    assert {s.value for s in ScopeLevel} == {
        "agent",
        "team",
        "org",
        "industry",
        "global",
    }


def test_validator_enum_closed() -> None:
    """Validator 枚举封闭集合 = {schema, scope, content, rate}。"""
    assert {v.value for v in Validator} == {"schema", "scope", "content", "rate"}


def test_method_enum_closed() -> None:
    """Method 枚举封闭集合 = {record_memory, query_memory}。"""
    assert {m.value for m in Method} == {"record_memory", "query_memory"}


def test_principal_type_enum_closed() -> None:
    """PrincipalType 枚举封闭集合 = {service_account, user, agent}。"""
    assert {p.value for p in PrincipalType} == {"service_account", "user", "agent"}


# ============================================================================
# 类型断言（所有枚举均为 StrEnum 子类）
# ============================================================================


def test_all_enums_are_strenum() -> None:
    """8 枚举都是 StrEnum 子类（强类型约束）。"""
    for enum_cls in (
        Phase,
        Result,
        GCState,
        Visibility,
        ScopeLevel,
        Validator,
        Method,
        PrincipalType,
    ):
        assert issubclass(enum_cls, StrEnum), f"{enum_cls.__name__} is not a StrEnum subclass"
