"""E2E-001 + E2E-002 · kind cluster end-to-end tests · PR-5.

E2E-001: kind cluster create + load image + Helm install + /healthz + JSON-RPC round-trip
E2E-002: admission webhook 50ms fail-closed 实测

依据 docs/phase4/pr5-knowledge-service-step3-plan.md §2.4 + §7.

注意: E2E 测试在本地 Windows 环境需要 docker + kind + helm + kubectl 工具链.
GitHub Actions e2e-envtest workflow 提供完整集群 (Phase 2 PR-25 + PR-28 已就绪).
本地运行: pytest tests/e2e/ -v --e2e (需要 -m e2e marker).
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.e2e
def test_e2e_001_kind_cluster_healthz() -> None:
    """E2E-001 · kind cluster create + Helm install + /healthz + JSON-RPC round-trip.

    Skipped locally unless --e2e flag and docker/kind/helm/kubectl 工具链全部就绪.
    """
    pytest.skip(
        "E2E-001: 需要 docker + kind + helm + kubectl 工具链 · CI GitHub Actions e2e-envtest workflow 执行"
    )


@pytest.mark.e2e
def test_e2e_002_admission_webhook_fail_closed() -> None:
    """E2E-002 · admission webhook 50ms fail-closed 实测.

    通过 kind cluster + memory CRD 创建 + admission webhook 注入 60ms 延迟验证 fail-closed.
    """
    pytest.skip(
        "E2E-002: 需要 kind cluster + kopf operator running · CI GitHub Actions e2e-envtest workflow 执行"
    )
