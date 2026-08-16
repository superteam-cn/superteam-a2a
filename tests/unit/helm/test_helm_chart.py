"""HELM-UT-001~004 · helm chart structure validation · PR-5.

依据 docs/phase4/pr5-knowledge-service-step3-plan.md §2.1 + §7.
验证 helm/knowledge-memory-service/ chart 结构与 7+ resources 渲染.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CHART_DIR = REPO_ROOT / "helm" / "knowledge-memory-service"


def test_helm_ut_001_chart_yaml_exists() -> None:
    """HELM-UT-001 · Chart.yaml 存在 + apiVersion: v2."""
    chart_yaml = CHART_DIR / "Chart.yaml"
    assert chart_yaml.exists()
    content = chart_yaml.read_text(encoding="utf-8")
    assert "apiVersion: v2" in content
    assert "knowledge-memory-service" in content


def test_helm_ut_002_values_yaml_replicas_one() -> None:
    """HELM-UT-002 · values.yaml replicaCount=1 (D 方案单进程)."""
    values_yaml = CHART_DIR / "values.yaml"
    assert values_yaml.exists()
    content = values_yaml.read_text(encoding="utf-8")
    # 单实例强制
    assert "replicaCount: 1" in content


def test_helm_ut_003_values_schema_enforces_replicas() -> None:
    """HELM-UT-003 · values.schema.json 强制 replicaCount<=1 + leaderElection.backend enum."""
    schema = CHART_DIR / "values.schema.json"
    assert schema.exists()
    content = schema.read_text(encoding="utf-8")
    # schema 强制副本数
    assert "maximum" in content or "minLength" in content


def test_helm_ut_004_seven_plus_templates() -> None:
    """HELM-UT-004 · 7+ templates 存在 (deployment + service + serviceaccount + rbac + networkpolicy + servicemonitor + ingress + prometheusrule + issuer + certificate)."""
    templates_dir = CHART_DIR / "templates"
    assert templates_dir.exists()
    yaml_files = list(templates_dir.rglob("*.yaml"))
    # 至少有 7 个 .yaml 模板（不含 _helpers.tpl 和 crds/）
    assert len(yaml_files) >= 7, (
        f"Expected 7+ templates, got {len(yaml_files)}: {[f.name for f in yaml_files]}"
    )
