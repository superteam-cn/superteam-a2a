"""H-RM-E2E-001: A2A recordMemory end-to-end via kind cluster.

Reference: Phase 2 plan §3.4 + L3-5 §4.3 line 1178 + L2-4 §6.4 wire contract.

Phase 2 PR-4.1.1 #91 状态：
- chart 完整（PR #27 #89 #90 已 merged · CRD + deployment + service + Dockerfile）
- main.py 加 kopf liveness_endpoint（PR-4.1.1 main.py 改动）
- 但 **A2A HTTP JSON-RPC server 未实装**（仅 kopf in-process operator · 无 HTTP/JSON-RPC endpoint）
- Phase 3 OPEN-MEMORY-002 候选（K8sBackend 完整实装 + A2A HTTP server）

测试跳过原因：A2A HTTP server 未实装 → 无法通过 JSON-RPC envelope `recordMemory`
验证 response error.code。Phase 2 PR-4.1.1 仅启用 LEADER + LIFECYCLE E2E。
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

    跳过条件：A2A HTTP JSON-RPC server 未实装（OPEN-MEMORY-002 · Phase 3 候选）。
    """
    pytest.skip(
        "H-RM-E2E-001 deferred to Phase 3 OPEN-MEMORY-002 · "
        "A2A HTTP JSON-RPC server not implemented · "
        "Phase 2 PR-4.1.1 仅启用 LEADER-E2E-001/002 + LIFECYCLE-E2E-001/002"
    )
