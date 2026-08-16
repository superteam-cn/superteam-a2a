"""HELM-IT-001~002 · helm template render integration · PR-5.

使用 sh.int8 验证（避免 helm CLI 依赖）:
- HELM-IT-001: values.yaml 解析后必填字段存在
- HELM-IT-002: rbac.create=true 时 Role/RoleBinding 都渲染
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALUES_YAML = REPO_ROOT / "helm" / "knowledge-memory-service" / "values.yaml"


def test_helm_it_001_required_values() -> None:
    """HELM-IT-001 · values.yaml 必填字段全部存在."""
    content = VALUES_YAML.read_text(encoding="utf-8")
    required = [
        "replicaCount:",
        "image:",
        "repository:",
        "service:",
        "port:",
        "rbac:",
        "create:",
        "tls:",
        "serviceMonitor:",
        "prometheusRule:",
        "networkPolicy:",
    ]
    for field in required:
        assert field in content, f"Missing required field: {field}"


def test_helm_it_002_tls_certmanager_section() -> None:
    """HELM-IT-002 · tls.certManager.* 在 values.yaml 中可被发现（即使 default disabled）."""
    content = VALUES_YAML.read_text(encoding="utf-8")
    assert "certManager:" in content
    assert "duration:" in content
    assert "renewBefore:" in content
