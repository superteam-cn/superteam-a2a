"""Leader election E2E tests for knowledge-memory-service.

Tests:
- LEADER-E2E-001: InProcess default spike (MemoryReconciler tick verification)
- LEADER-E2E-002: K8sLease spike (kind cluster + replicaCount=2 + leader switchover)

Reference: Phase 2 plan §3.4 + L2-4 §7.6 Lease 约束 + L3-6 §4.1 reconcile 算法.

NOTE: LEADER-E2E-002 requires Helm chart deployment.yaml which is currently
missing (Phase 2 PR-4.1 follow-up). Tests skip cleanly until chart is complete.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Path setup for service imports (matches tests/unit/knowledge_memory pattern)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
if str(_KM_SRC) not in sys.path:
    sys.path.insert(0, str(_KM_SRC))


@pytest.mark.e2e
async def test_leader_e2e_001_in_process_default_is_leader() -> None:
    """LEADER-E2E-001 · InProcess 默认 spike：单进程 leader 确定性。

    验证 InProcessLeaderElector 在单进程环境下的 acquire + renew 行为：
    - 初始 is_leader() == False（未获取）
    - 首次 try_acquire_or_renew() 成功 → is_leader() == True
    - 后续 try_acquire_or_renew() idempotent renew → 持续 is_leader() == True

    与 K8s 模式对比（LEADER-E2E-002 验证多副本切换）。

    不需 kind cluster · 不需 CRD · 纯进程内行为验证。
    """
    from superteam_a2a.knowledge_memory.reconciler.leader import InProcessLeaderElector

    leader = InProcessLeaderElector()
    assert leader.is_leader() is False  # 初始：未获取

    # 首次 acquire
    acquired = await leader.try_acquire_or_renew()
    assert acquired is True
    assert leader.is_leader() is True

    # 续约 idempotent
    renewed = await leader.try_acquire_or_renew()
    assert renewed is True
    assert leader.is_leader() is True


@pytest.mark.e2e
def test_leader_e2e_002_k8s_lease_spike_requires_chart(kind_cluster: str) -> None:
    """LEADER-E2E-002 · K8sLease spike：kind cluster + replicaCount=2 + leader 切换。

    验证 K8sLeaseLeaderElector 在真实 K8s 集群下的行为：
    1. helm install --set replicaCount=2 --set leaderElection.backend=k8s
    2. 启动 2 个 pod · 1 个持 Lease（leader）· 1 个非 leader
    3. kill leader pod · 30s 内另一个 pod 接管

    **SKIP 条件**：Helm chart 当前不完整（无 deployment.yaml + service.yaml）
    · 需要 Phase 2 PR-4.1 实装 deployment.yaml + service.yaml + Dockerfile + CRD
    · 当前 PR-4 仅验证 spike 基础设施可达性。
    """
    # chart_status fixture 提供 chart 完整性检查
    from tests.e2e.conftest import chart_status  # type: ignore[import-not-found]

    is_complete, missing = chart_status()
    if not is_complete:
        pytest.skip(
            f"Helm chart incomplete (missing: {missing}) · "
            "deferred to Phase 2 PR-4.1 · "
            "see MEMORY.md → Phase 2 PR-4 chart 缺口",
            allow_module_level=False,
        )

    # kind_cluster fixture 确保 kind cluster 已创建
    # 完整 spike 实装在 PR-4.1:
    # - helm install kmem CHART_PATH --set replicaCount=2 --set leaderElection.backend=k8s
    # - kubectl wait --for=condition=ready pod -l app=kmem --timeout=60s
    # - 获取 leader pod name + non-leader pod name
    # - kubectl delete pod <leader>
    # - 等待 30s · 验证新 leader
    pytest.fail(
        "LEADER-E2E-002 spike 实装 deferred to PR-4.1 · "
        "chart 现在不完整 · 当前 PR-4 仅创建 spike 基础设施"
    )
