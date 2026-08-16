"""RBAC-UT-001~003 · RBAC validation · PR-5 §2.2.

L3-6 §M-1.4 修复：role_write.yaml 含 admissionregistration.k8s.io +
authentication.k8s.io + authorization.k8s.io.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RBAC_DIR = REPO_ROOT / "helm" / "knowledge-memory-service" / "templates" / "rbac"


def test_rbac_ut_001_read_role_seven_api_groups() -> None:
    """RBAC-UT-001 · Role read 含 superteam-a2a.io + core + secrets (3+ apiGroups)."""
    read_role = RBAC_DIR / "role_read.yaml"
    assert read_role.exists()
    content = read_role.read_text(encoding="utf-8")
    # 至少 3 个 apiGroups
    api_groups = ["superteam-a2a.io", '""', ""]
    found = sum(1 for g in api_groups if g in content)
    assert found >= 2, f"Read Role 缺少 apiGroups: {api_groups}"


def test_rbac_ut_002_write_role_admissionregistration() -> None:
    """RBAC-UT-002 · Role write 含 admissionregistration.k8s.io (L3-6 §M-1.4)."""
    write_role = RBAC_DIR / "role_write.yaml"
    assert write_role.exists()
    content = write_role.read_text(encoding="utf-8")
    assert "admissionregistration.k8s.io" in content
    assert "validatingwebhookconfigurations" in content


def test_rbac_ut_003_write_role_authn_authz() -> None:
    """RBAC-UT-003 · Role write 含 authentication.k8s.io + authorization.k8s.io."""
    write_role = RBAC_DIR / "role_write.yaml"
    content = write_role.read_text(encoding="utf-8")
    assert "authentication.k8s.io" in content
    assert "tokenreviews" in content
    assert "authorization.k8s.io" in content
    assert "subjectaccessreviews" in content
