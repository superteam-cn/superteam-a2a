"""Leader election E2E tests for knowledge-memory-service.

Tests:
- LEADER-E2E-001: InProcess default spike (MemoryReconciler tick verification)
- LEADER-E2E-002: K8sLease spike (kind cluster + replicaCount=2 + leader switchover)

Reference: Phase 2 plan §3.4 + L2-4 §7.6 Lease 约束 + L3-6 §4.1 reconcile 算法.

Phase 2 PR-4.1.1 #91 实装（PR #27 chart 完整化后）：
- LEADER-E2E-001 保持 in-process 验证（不需 cluster）
- LEADER-E2E-002 实装 kind cluster + helm install rc=2 + leader switchover
"""

from __future__ import annotations

import subprocess
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
def test_leader_e2e_002_k8s_lease_spike(
    kind_cluster: str,
    chart_status: tuple[bool, list[str]],
    helm_client: str,
    kubectl_client: str,
) -> None:
    """LEADER-E2E-002 · K8sLease spike：kind cluster + replicaCount=2 + leader 切换。

    验证 K8sLeaseLeaderElector 在真实 K8s 集群下的行为：
    1. helm install --set replicaCount=2 --set leaderElection.backend=k8s
    2. 等 2 个 pod Ready
    3. 查找持有 Lease `memory-reconciler-leader` 的 pod（leader）
    4. kubectl delete pod <leader>
    5. 等待 30s 内新 leader 接管

    **依赖**：
    - chart 完整（PR #27 merged）：deployment.yaml + service.yaml + CRD + Dockerfile
    - kopf liveness_endpoint 健康（PR-4.1.1 main.py 修改）
    - e2e-envtest workflow 已 build + load image 到 kind（PR-4.1.1 #90）

    跳过条件：chart 不完整 · helm/kubectl 不可用
    """
    if not chart_status[0]:
        pytest.skip(
            f"Helm chart incomplete (missing: {chart_status[1]})",
            allow_module_level=False,
        )

    from tests.e2e.conftest import CHART_PATH  # type: ignore[import-not-found]

    namespace = "superteam-a2a-system"
    release_name = "kmem-leader-test"
    selector = "app.kubernetes.io/name=knowledge-memory-service"

    # 1. helm install with replicaCount=2 + leaderElection.backend=k8s
    install_result = subprocess.run(
        [
            "helm",
            "install",
            release_name,
            str(CHART_PATH),
            "--kubeconfig",
            kind_cluster,
            "--namespace",
            namespace,
            "--create-namespace",
            "--set",
            "replicaCount=2",
            "--set",
            "leaderElection.backend=k8s",
            "--set",
            "image.pullPolicy=Never",
            "--wait",
            "--timeout",
            "120s",
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert install_result.returncode == 0, f"helm install failed: {install_result.stderr}"

    try:
        # 2. 等待 2 个 pod Ready
        wait_result = subprocess.run(
            [
                "kubectl",
                "wait",
                "--for=condition=ready",
                "pod",
                "-l",
                selector,
                "-n",
                namespace,
                "--kubeconfig",
                kind_cluster,
                "--timeout",
                "120s",
            ],
            capture_output=True,
            text=True,
            timeout=150,
        )
        assert wait_result.returncode == 0, f"kubectl wait failed: {wait_result.stderr}"

        # 3. 获取两个 pod name
        pods_result = subprocess.run(
            [
                "kubectl",
                "get",
                "pods",
                "-l",
                selector,
                "-n",
                namespace,
                "--kubeconfig",
                kind_cluster,
                "-o",
                "jsonpath={.items[*].metadata.name}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert pods_result.returncode == 0
        pod_names = pods_result.stdout.split()
        assert len(pod_names) == 2, f"Expected 2 pods · got {len(pod_names)}: {pod_names}"

        # 4. 通过 Lease 持有者识别 leader pod
        lease_holder_result = subprocess.run(
            [
                "kubectl",
                "get",
                "lease",
                "memory-reconciler-leader",
                "-n",
                namespace,
                "--kubeconfig",
                kind_cluster,
                "-o",
                "jsonpath={.spec.holderIdentity}",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert lease_holder_result.returncode == 0
        holder = lease_holder_result.stdout.strip()
        assert holder, "Lease holderIdentity empty (no leader acquired yet)"
        assert any(holder in p for p in pod_names), f"Lease holder {holder} not in pods {pod_names}"

        leader_pod = next(p for p in pod_names if holder in p)

        # 5. 删除 leader pod
        delete_result = subprocess.run(
            [
                "kubectl",
                "delete",
                "pod",
                leader_pod,
                "-n",
                namespace,
                "--kubeconfig",
                kind_cluster,
                "--wait=false",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert delete_result.returncode == 0

        # 6. 等新 leader pod Ready（rollout 重建 + Lease 抢占）
        # L3-6 §4.1: leaseDuration 30s + renewDeadline 15s → 30s 内应切换
        new_ready_result = subprocess.run(
            [
                "kubectl",
                "wait",
                "--for=condition=ready",
                "pod",
                "-l",
                selector,
                "-n",
                namespace,
                "--kubeconfig",
                kind_cluster,
                "--timeout",
                "60s",
            ],
            capture_output=True,
            text=True,
            timeout=80,
        )
        assert new_ready_result.returncode == 0, (
            f"new leader pod not ready within 60s: {new_ready_result.stderr}"
        )

        # 7. 验证新 Lease 持有者 ≠ 旧 leader
        new_holder_result = subprocess.run(
            [
                "kubectl",
                "get",
                "lease",
                "memory-reconciler-leader",
                "-n",
                namespace,
                "--kubeconfig",
                kind_cluster,
                "-o",
                "jsonpath={.spec.holderIdentity}",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert new_holder_result.returncode == 0
        new_holder = new_holder_result.stdout.strip()
        assert new_holder, "New Lease holderIdentity empty after switchover"
        assert new_holder != holder, f"Leader did not switch: old={holder} new={new_holder}"

    finally:
        # Cleanup: uninstall release (best-effort)
        subprocess.run(
            [
                "helm",
                "uninstall",
                release_name,
                "--kubeconfig",
                kind_cluster,
                "--namespace",
                namespace,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
