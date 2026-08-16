"""DOCKERFILE-UT-001 · Dockerfile validation · PR-5 §2.5.

multi-stage + non-root UID 1000 + HEALTHCHECK + EXPOSE 8080 + uvicorn --factory.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE = REPO_ROOT / "services" / "knowledge-memory-service" / "Dockerfile"


def test_dockerfile_ut_001_required_components() -> None:
    """DOCKERFILE-UT-001 · multi-stage + non-root + HEALTHCHECK + EXPOSE + uvicorn factory."""
    assert DOCKERFILE.exists()
    content = DOCKERFILE.read_text(encoding="utf-8")
    # multi-stage
    assert "FROM python:3.12-slim AS builder" in content
    assert "FROM python:3.12-slim AS runtime" in content
    # non-root UID 1000
    assert "useradd" in content
    assert "uid 1000" in content or "UID 1000" in content or "--uid 1000" in content
    assert "USER 1000" in content
    # EXPOSE 8080
    assert "EXPOSE 8080" in content
    # HEALTHCHECK
    assert "HEALTHCHECK" in content
    # uvicorn --factory
    assert "uvicorn" in content
    assert "--factory" in content
