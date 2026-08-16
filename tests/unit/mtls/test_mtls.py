"""MTLS-UT-001~002 · cert-manager templates validation · PR-5 §2.3.

cert-manager Certificate + Issuer · 90d duration + 30d renewBefore · ECDSA-256.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES_DIR = REPO_ROOT / "helm" / "knowledge-memory-service" / "templates"


def test_mtls_ut_001_issuer_template() -> None:
    """MTLS-UT-001 · issuer.yaml 含 cert-manager.io/v1 Issuer."""
    issuer = TEMPLATES_DIR / "issuer.yaml"
    assert issuer.exists()
    content = issuer.read_text(encoding="utf-8")
    assert "cert-manager.io/v1" in content
    assert "kind: Issuer" in content


def test_mtls_ut_002_certificate_template() -> None:
    """MTLS-UT-002 · certificate.yaml 含 Certificate + 90d duration + ECDSA-256."""
    cert = TEMPLATES_DIR / "certificate.yaml"
    assert cert.exists()
    content = cert.read_text(encoding="utf-8")
    assert "kind: Certificate" in content
    assert "2160h" in content  # 90d
    assert "720h" in content  # 30d renew
    assert "ECDSA" in content
    assert "size: 256" in content
