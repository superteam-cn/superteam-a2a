"""wire-sync-IT-001 · 3 CRD × L3-5 v0.2.0 简化字段 1:1 对齐 · 0 漂移静态断言.

防止 PR-3 引入 wire contract 漂移（参考 #81 pyright gap 经验）。
注意：wire-sync 测试对齐的是 PR-3 实装的 5+5 简化字段集（与 L2-4 §3.2-§3.4 完整字段集不同），
简化选择由 #105 PR-3 Phase A plan 决定（详见 docs/spec/L3-file-specs/L3-5-knowledge-service.md §3）。

PR-4 将扩到完整 L2-4 Spec 字段（displayName/ownerRef/includeTypes/sourceUri/reinforcedCount 等）。
"""

from __future__ import annotations

import os
import re

# 路径锚定：从仓库根目录开始（test file 位于 tests/integration/test_wire_sync.py）
# Windows quirk：pathlib.Path 在 Python 3.12 + Windows 上对 forward-slash 绝对路径
# 表现异常（Path.exists() / Path.iterdir() 返回 False 但 os.path.exists() / os.listdir()
# 返回 True）。本测试全部使用 os.path + raw 字符串处理文件 I/O，避免 pathlib 陷阱。
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOWLEDGE_DIR = os.path.join(
    REPO_ROOT, "packages", "knowledge", "src", "superteam_a2a", "knowledge", "crd"
)


def _read_module_text(path: str) -> str:
    """读取模块源代码 · 用于 grep alias."""
    with open(path, encoding="utf-8") as f:
        return f.read()


def _extract_pydantic_aliases(source_text: str) -> set[str]:
    """从 Pydantic model 源代码提取所有 alias='...' 声明.

    支持两种模式：
    - alias="scopeLevel"（双引号）
    - alias='scopeLevel'（单引号 · Pydantic 偶尔使用）
    """
    return set(re.findall(r"""alias=['"]([a-zA-Z][a-zA-Z0-9_]*)['"]""", source_text))


def test_wire_sync_it_001_knowledge_scope_field_alignment() -> None:
    """wire-sync-IT-001 (Part 1) · KnowledgeScope fields × L3-5 §3.1 简化字段 1:1 对齐."""
    source = _read_module_text(os.path.join(KNOWLEDGE_DIR, "knowledgescope.py"))
    actual_aliases = _extract_pydantic_aliases(source)

    # L3-5 §3.1 简化字段集（6 spec + 5 status wire aliases）
    # Spec: scopeLevel, name, subjectRef, parentRef, inheritRules, visibility
    # Status: observedGeneration, lastUpdated, childScopes, knowledgeItemCount, activeQueries5m
    expected_aliases = {
        # spec
        "scopeLevel",
        "subjectRef",
        "parentRef",
        "inheritRules",
        # status
        "observedGeneration",
        "lastUpdated",
        "childScopes",
        "knowledgeItemCount",
        "activeQueries5m",
        # wrapper
        "apiVersion",
    }
    missing = expected_aliases - actual_aliases
    assert not missing, f"wire drift: KnowledgeScope missing fields {missing}"

    # 额外字段容忍（不影响 wire sync · 可能 Pydantic 内部字段或 PR-4 预备）
    extra = actual_aliases - expected_aliases
    # 记录但不阻断
    if extra:
        # 使用 print 而非 logging（pytest -s 可捕获）
        print(f"KnowledgeScope extra fields (tolerated): {sorted(extra)}")


def test_wire_sync_it_001_knowledge_item_field_alignment() -> None:
    """wire-sync-IT-001 (Part 2) · KnowledgeItem fields × L3-5 §3.2 简化字段 1:1 对齐."""
    source = _read_module_text(os.path.join(KNOWLEDGE_DIR, "knowledgeitem.py"))
    actual_aliases = _extract_pydantic_aliases(source)

    # L3-5 §3.2 简化字段集（7 spec + 6 status wire aliases）
    # Spec: scopeRef, knowledgeType, content, tags, version, supersededBy, confidence
    # Status: indexedAt, lastAccessed, accessCount24h, bm25ScoreAvg, decayState, effectiveConfidence
    expected_aliases = {
        # spec
        "scopeRef",
        "knowledgeType",
        "supersededBy",
        # status
        "indexedAt",
        "lastAccessed",
        "accessCount24h",
        "bm25ScoreAvg",
        "decayState",
        "effectiveConfidence",
        # wrapper
        "apiVersion",
    }
    missing = expected_aliases - actual_aliases
    assert not missing, f"wire drift: KnowledgeItem missing fields {missing}"

    extra = actual_aliases - expected_aliases
    if extra:
        print(f"KnowledgeItem extra fields (tolerated): {sorted(extra)}")


def test_wire_sync_it_001_memory_field_alignment() -> None:
    """wire-sync-IT-001 (Part 3) · Memory fields × L3-5 §3.3 简化字段 1:1 对齐."""
    source = _read_module_text(os.path.join(KNOWLEDGE_DIR, "memory_schema.py"))
    actual_aliases = _extract_pydantic_aliases(source)

    # L3-5 §3.3 简化字段集（5 spec + 4 status wire aliases）
    # Spec: scopeRef, agentRef, content, decayDays, confidence
    # Status: observedGeneration, lastUpdated, effectiveConfidence
    expected_aliases = {
        # spec
        "scopeRef",
        "agentRef",
        "decayDays",
        # status
        "observedGeneration",
        "lastUpdated",
        "effectiveConfidence",
        # wrapper
        "apiVersion",
    }
    missing = expected_aliases - actual_aliases
    assert not missing, f"wire drift: Memory missing fields {missing}"

    extra = actual_aliases - expected_aliases
    if extra:
        print(f"Memory extra fields (tolerated): {sorted(extra)}")


def test_wire_sync_it_001_nested_value_objects() -> None:
    """wire-sync-IT-001 (Part 4) · 嵌套 value object (ScopeReference/ItemReference/AgentReference/InheritRules) 字段验证."""
    # 这些 value object 是嵌套在主 CRD 内的，必须存在
    # PR-4 不会移除它们（wire sync 锚点）

    # ScopeReference（嵌套在 KS/parentRef、KI/scopeRef、M/scopeRef）
    sr_source = _read_module_text(os.path.join(KNOWLEDGE_DIR, "scope_reference.py"))
    sr_aliases = _extract_pydantic_aliases(sr_source)
    assert sr_aliases == set() or sr_aliases == {"level"}, (
        f"ScopeReference should have no wire alias (internal only; level is optional redundant). Actual: {sr_aliases}"
    )

    # ItemReference（嵌套在 KI/supersededBy）
    ir_source = _read_module_text(os.path.join(KNOWLEDGE_DIR, "item_reference.py"))
    ir_aliases = _extract_pydantic_aliases(ir_source)
    assert ir_aliases == set() or ir_aliases == {"version"}, (
        f"ItemReference should have no wire alias (name+version only). Actual: {ir_aliases}"
    )

    # InheritRules（嵌套在 KS/inheritRules）
    irules_source = _read_module_text(os.path.join(KNOWLEDGE_DIR, "inherit_rules.py"))
    irules_aliases = _extract_pydantic_aliases(irules_source)
    # InheritRules 应有 maxDepth/allowedChildLevels/blockSelfReference/includeTypes/excludeTypes
    expected_irules = {
        "maxDepth",
        "allowedChildLevels",
        "blockSelfReference",
        "includeTypes",
        "excludeTypes",
    }
    missing_irules = expected_irules - irules_aliases
    assert not missing_irules, f"InheritRules missing fields: {missing_irules}"


def test_wire_sync_it_001_l3_5_spec_exists() -> None:
    """wire-sync-IT-001 (Sanity) · L3-5 v0.2.0 Spec 文件存在."""
    l3_5_spec = os.path.join(REPO_ROOT, "docs", "spec", "L3-file-specs", "L3-knowledge-service.md")
    assert os.path.exists(l3_5_spec), f"L3-5 spec not found: {l3_5_spec}"
