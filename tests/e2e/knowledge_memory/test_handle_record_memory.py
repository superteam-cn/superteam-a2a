"""H-RM-E2E-001: A2A recordMemory end-to-end via kind cluster.

Reference: Phase 2 plan §3.4 + L3-5 §4.3 line 1178 + L2-4 §6.4 wire contract.

NOTE: This test requires a deployed knowledge-memory-service operator in the
kind cluster, which depends on:
1. Memory CRD installed (currently MISSING from repo)
2. Helm chart deployment.yaml (currently MISSING)
3. Helm chart service.yaml (currently MISSING)
4. Dockerfile (currently MISSING)

All 4 prerequisites deferred to Phase 2 PR-4.1. Test skips cleanly until then.
"""

from __future__ import annotations

import pytest


@pytest.mark.e2e
def test_h_rm_e2e_001_a2a_record_memory_via_a2a_call() -> None:
    """H-RM-E2E-001 · A2A recordMemory → K8s apply → effective_confidence → response。

    完整 E2E 验证：
    1. kubectl apply -f memory-cr.yaml (含 Memory spec fields)
    2. kopf operator 在 cluster 内 reconcile · 计算 effective_confidence
    3. A2A JSON-RPC envelope `recordMemory` 验证 response error.code == 0
       或 12 MEMORY_* 错误码之一（按场景）

    跳过条件：Memory CRD 未注册 + operator 未部署。
    """
    pytest.skip(
        "H-RM-E2E-001 deferred to Phase 2 PR-4.1 · "
        "需要 Memory CRD + deployment.yaml + service.yaml + Dockerfile · "
        "see MEMORY.md → Phase 2 PR-4 chart 缺口"
    )
