"""Hello Agent · Helm 部署资源验证 · HELLO-DEPLOY-001~003（3 UT）。

依据 Phase 4 PR-2 plan §2.4 + §7 测试策略：
- 验证 deployment.yaml + service.yaml + serviceaccount.yaml 3 个核心 K8s 资源
- 不依赖 helm binary（直接解析 template 文件）
- pytest function-based · 无 setup/teardown · 直接断言

5 项关键不变量验证（PR-2 §6）：
1. Card-driven 单实例（HELLO-DEPLOY-001）
2. Python-first 边界（chart 与 base image 无关）
3. observability 4 指标（servicemonitor 在 test_helm_chart.py 覆盖）
4. wire contract（Hello Agent 不涉及 MEMORY_*）
5. 单进程 8080 端口（HELLO-DEPLOY-002）
"""

from __future__ import annotations

import re
from pathlib import Path

# ============================================================================
# 路径常量（workspace 根定位 · 不依赖 helm binary）
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TEMPLATES_DIR = _REPO_ROOT / "helm" / "superteam-a2a-hello-agent" / "templates"


# ============================================================================
# Helpers
# ============================================================================


def _read(path: Path) -> str:
    """读取模板文件内容（已存在性保证）。"""
    return path.read_text(encoding="utf-8")


# ============================================================================
# HELLO-DEPLOY-001 · 单实例 deployment 创建成功
# ============================================================================


def test_hello_deploy_001_single_replica() -> None:
    """HELLO-DEPLOY-001 :: deployment.yaml 单实例（replicas: 1）。

    验证：spec.replicas 字段 = 1（Card-driven 单实例）。
    关键不变量 #1：Card-driven 单实例。
    """
    content = _read(_TEMPLATES_DIR / "deployment.yaml")

    # spec.replicas: {{ .Values.replicaCount }}（template 渲染为字面量 1）
    # 由于不能直接渲染，验证 template 表达式正确引用 .Values.replicaCount
    assert re.search(r"replicas:\s*\{\{.*\.Values\.replicaCount", content), (
        "deployment.yaml must reference .Values.replicaCount (template 渲染为 1)"
    )

    # 进一步验证 values.yaml default replicaCount=1
    import yaml

    values = yaml.safe_load(
        (_REPO_ROOT / "helm" / "superteam-a2a-hello-agent" / "values.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert values["replicaCount"] == 1, (
        f"values.yaml replicaCount must be 1, got {values['replicaCount']}"
    )


# ============================================================================
# HELLO-DEPLOY-002 · service ClusterIP + port 8080 暴露
# ============================================================================


def test_hello_deploy_002_service_clusterip_port_8080() -> None:
    """HELLO-DEPLOY-002 :: service.yaml ClusterIP + port 8080 暴露。

    验证：
    - spec.type: ClusterIP
    - spec.ports[0].port: 8080
    - spec.ports[0].targetPort: http（引用 deployment containerPort name）

    关键不变量 #5：单进程 8080 端口。
    """
    content = _read(_TEMPLATES_DIR / "service.yaml")

    # spec.type: ClusterIP（template 渲染引用 .Values.service.type）
    assert re.search(r"type:\s*\{\{.*\.Values\.service\.type", content), (
        "service.yaml must reference .Values.service.type (template 渲染为 ClusterIP)"
    )

    # spec.ports[0].port: 8080
    assert re.search(r"port:\s*\{\{.*\.Values\.service\.port", content), (
        "service.yaml must reference .Values.service.port (template 渲染为 8080)"
    )

    # targetPort: http（name reference · 与 deployment containerPort name="http" 对齐）
    assert re.search(r"targetPort:\s*http", content), (
        "service.yaml must declare targetPort: http (name reference)"
    )

    # 进一步验证 values.yaml default service.port=8080
    import yaml

    values = yaml.safe_load(
        (_REPO_ROOT / "helm" / "superteam-a2a-hello-agent" / "values.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert values["service"]["port"] == 8080, (
        f"values.yaml service.port must be 8080, got {values['service']['port']}"
    )
    assert values["service"]["targetPort"] == 8080, (
        f"values.yaml service.targetPort must be 8080, got {values['service']['targetPort']}"
    )
    assert values["service"]["type"] == "ClusterIP", (
        f"values.yaml service.type must be ClusterIP, got {values['service']['type']}"
    )


# ============================================================================
# HELLO-DEPLOY-003 · serviceaccount automountServiceAccountToken=false
# ============================================================================


def test_hello_deploy_003_serviceaccount_token_disabled() -> None:
    """HELLO-DEPLOY-003 :: serviceaccount.yaml automountServiceAccountToken=false。

    验证：serviceaccount.yaml 字段 automountServiceAccountToken 渲染为 false（最小权限）。
    """
    content = _read(_TEMPLATES_DIR / "serviceaccount.yaml")

    # automountServiceAccountToken: {{ .Values.serviceAccount.automountServiceAccountToken }}
    # （template 渲染引用 values · values.yaml 默认 false）
    assert re.search(
        r"automountServiceAccountToken:\s*\{\{.*\.Values\.serviceAccount\.automountServiceAccountToken",
        content,
    ), (
        "serviceaccount.yaml must reference .Values.serviceAccount.automountServiceAccountToken "
        "(template 渲染为 false · 最小权限)"
    )

    # 进一步验证 values.yaml default automountServiceAccountToken=false
    import yaml

    values = yaml.safe_load(
        (_REPO_ROOT / "helm" / "superteam-a2a-hello-agent" / "values.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert values["serviceAccount"]["automountServiceAccountToken"] is False, (
        f"values.yaml serviceAccount.automountServiceAccountToken must be false, "
        f"got {values['serviceAccount']['automountServiceAccountToken']}"
    )
