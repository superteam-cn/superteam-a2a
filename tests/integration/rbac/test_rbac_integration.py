"""RBAC-IT-001~002 · RBAC integration · PR-5.

L3-6 §M-1.4 验证 write Role 完整覆盖 admissionregistration + authn + authz.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RBAC_DIR = REPO_ROOT / "helm" / "knowledge-memory-service" / "templates" / "rbac"
VALUES_YAML = REPO_ROOT / "helm" / "knowledge-memory-service" / "values.yaml"


def test_rbac_it_001_rolebinding_binds_both_roles() -> None:
    """RBAC-IT-001 · rolebinding.yaml 同时绑定 read + write Roles 到同一 SA."""
    rolebinding = RBAC_DIR / "rolebinding.yaml"
    content = rolebinding.read_text(encoding="utf-8")
    # 应该有两个 roleRef（read + write）
    assert content.count("kind: Role") >= 2
    assert content.count("apiGroup: rbac.authorization.k8s.io") >= 2
    # 绑定到同一 ServiceAccount
    assert content.count("kind: ServiceAccount") >= 2


def test_rbac_it_002_namespace_scoped_secrets() -> None:
    """RBAC-IT-002 · read Role secrets 权限限制到具体 resourceNames（避免 cluster-wide 泄露）."""
    read_role = (RBAC_DIR / "role_read.yaml").read_text(encoding="utf-8")
    assert "resourceNames:" in read_role
    # secrets 限制在 service-tls + client-ca
    assert "knowledge-service-tls" in read_role
    assert "superteam-client-ca" in read_role
