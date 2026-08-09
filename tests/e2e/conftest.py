"""E2E test fixtures for knowledge-memory-service.

Provides session-scoped kind cluster + function-scoped namespace isolation
+ helm/kubectl availability checks. Tests that depend on missing chart
resources (deployment.yaml, service.yaml, CRD, Dockerfile) skip cleanly.

Reference:
- docs/phase2/l4-phase2-spike-plan.md §3.4
- Phase 2 PR-4 spike infrastructure (Path A — honest infra + skip mechanism)

NOTE: Helm chart is currently incomplete (no deployment.yaml, no service.yaml,
no CRD definition, no Dockerfile). See MEMORY.md → "Phase 2 PR-4 chart 缺口"
for follow-up PR-4.1 plan.
"""

from __future__ import annotations

import shutil
import subprocess
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

# ============================================================================
# 常量（与 Phase 2 plan §2.4 + §3.4 保持一致）
# ============================================================================

KIND_IMAGE = "kindest/node:v1.30.0"
E2E_NAMESPACE_PREFIX = "e2e-h-"
LEASE_NAMESPACE = "superteam-a2a-system"
CHART_PATH = Path(__file__).resolve().parents[2] / "helm" / "knowledge-memory-service"

# Chart minimal required templates for deployment-dependent E2E
REQUIRED_CHART_FILES: tuple[str, ...] = (
    "templates/deployment.yaml",
    "templates/service.yaml",
)


# ============================================================================
# 工具函数：CLI 可用性检测
# ============================================================================


def _cli_version(*args: str, timeout: int = 10) -> str | None:
    """Return CLI version output if available, else None."""
    binary = args[0]
    if shutil.which(binary) is None:
        return None
    try:
        result = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    return result.stdout.strip()


@pytest.fixture(scope="session")
def kind_version() -> str:
    """Skip session if kind CLI is unavailable."""
    version = _cli_version("kind", "version")
    if version is None:
        pytest.skip(
            "kind CLI not available · install via "
            "https://kind.sigs.k8s.io/docs/user/quick-start/#installation",
            allow_module_level=False,
        )
    return version


@pytest.fixture(scope="session")
def kubectl_client() -> str:
    """Skip session if kubectl is unavailable."""
    version = _cli_version("kubectl", "version", "--client=true")
    if version is None:
        pytest.skip(
            "kubectl not available · install via https://kubernetes.io/docs/tasks/tools/",
            allow_module_level=False,
        )
    return version


@pytest.fixture(scope="session")
def helm_client() -> str:
    """Skip session if helm is unavailable."""
    version = _cli_version("helm", "version", "--short")
    if version is None:
        pytest.skip(
            "helm not available · install via https://helm.sh/docs/intro/install/",
            allow_module_level=False,
        )
    return version


@pytest.fixture(scope="session")
def chart_status() -> tuple[bool, list[str]]:
    """Return chart completeness status.

    Returns (is_complete, missing_files). Deployment-dependent E2E tests
    skip when is_complete is False.
    """
    missing = [p for p in REQUIRED_CHART_FILES if not (CHART_PATH / p).exists()]
    return (len(missing) == 0, missing)


# ============================================================================
# Session-scoped kind cluster
# ============================================================================


@pytest.fixture(scope="session")
def kind_cluster(
    tmp_path_factory: pytest.TempPathFactory,
    kind_version: str,
    kubectl_client: str,
) -> Iterator[str]:
    """Session-scoped kind cluster with kubeconfig path.

    Creates cluster on first call, reuses on subsequent tests in the session.
    Cleanup runs on session teardown (always, even on failure).
    """
    cluster_name = f"e2e-{uuid.uuid4().hex[:8]}"
    kubeconfig_dir = tmp_path_factory.mktemp("kind-kubeconfig")
    kubeconfig_path = str(kubeconfig_dir / "config")

    subprocess.run(
        [
            "kind",
            "create",
            "cluster",
            f"--name={cluster_name}",
            f"--image={KIND_IMAGE}",
            f"--kubeconfig={kubeconfig_path}",
        ],
        check=True,
        capture_output=True,
        timeout=180,
    )

    yield kubeconfig_path

    subprocess.run(
        ["kind", "delete", "cluster", f"--name={cluster_name}"],
        check=False,
        capture_output=True,
        timeout=60,
    )


# ============================================================================
# Function-scoped isolation
# ============================================================================


@pytest.fixture
def e2e_namespace(kind_cluster: str) -> Iterator[str]:
    """Function-scoped unique namespace.

    Cleanup deletes the namespace (best-effort, ignore-not-found).
    """
    name = f"{E2E_NAMESPACE_PREFIX}-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        [
            "kubectl",
            "create",
            "namespace",
            name,
            f"--kubeconfig={kind_cluster}",
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )

    yield name

    subprocess.run(
        [
            "kubectl",
            "delete",
            "namespace",
            name,
            "--ignore-not-found",
            "--wait=false",
            f"--kubeconfig={kind_cluster}",
        ],
        check=False,
        capture_output=True,
        timeout=30,
    )


@pytest.fixture
def per_test_lease(kind_cluster: str) -> Iterator[str]:
    """Per-test Lease name with uuid isolation (Phase 2 §2.4).

    Cleanup deletes the Lease resource (best-effort).
    """
    name = f"e2e-le-{uuid.uuid4().hex[:8]}"
    yield name
    subprocess.run(
        [
            "kubectl",
            "delete",
            "lease",
            name,
            "-n",
            LEASE_NAMESPACE,
            "--ignore-not-found",
            f"--kubeconfig={kind_cluster}",
        ],
        check=False,
        capture_output=True,
        timeout=30,
    )
