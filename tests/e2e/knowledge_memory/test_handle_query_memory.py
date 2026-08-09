"""H-QM-E2E-001: A2A queryMemory end-to-end via kind cluster.

Reference: Phase 2 plan §3.4 + L3-5 §4.4 line 1289 + L2-4 §6.5 wire contract.

NOTE: Same skip conditions as H-RM-E2E-001 — requires Memory CRD + operator
deployment. Deferred to Phase 2 PR-4.1.
"""

from __future__ import annotations

import pytest


@pytest.mark.e2e
def test_h_qm_e2e_001_a2a_query_memory_via_a2a_call() -> None:
    """H-QM-E2E-001 · A2A queryMemory → backend list → 5 维过滤 → response。

    完整 E2E 验证：
    1. apply 3 个 Memory CR（含 scopeRef / agentRef / industry / content / confidence 不同）
    2. A2A JSON-RPC envelope `queryMemory` with filters:
       - scopeRef / agentRef / industry / content 关键词 / confidence threshold
    3. response.result.memories 包含过滤后子集

    跳过条件：Memory CRD 未注册 + operator 未部署。
    """
    pytest.skip(
        "H-QM-E2E-001 deferred to Phase 2 PR-4.1 · "
        "需要 Memory CRD + deployment.yaml + service.yaml + Dockerfile · "
        "see MEMORY.md → Phase 2 PR-4 chart 缺口"
    )
