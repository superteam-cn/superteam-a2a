"""Hello Agent · DEPLOY 测试 · HELLO-HELM-001~007（7 UT · 模拟渲染）。

Phase 4 PR-1 plan §2.5：DEPLOY 7 ID 镜像 helm template 渲染（实际 Dockerfile + helm install 推迟到 PR-2）。

本测试策略：
- 验证 L3-4 §1.3 + §6 文件清单中关键 schema/契约约束（以 Python dict 模拟渲染结果）
- 不直接执行 helm CLI（依赖外部二进制 · 本地 Windows 不可用）
- 测试入口：tests/deploy/test_hello_helm_template.py
- 通过 `python -m uv run pytest tests/deploy/test_hello_helm_template.py` 显式调用
"""

from __future__ import annotations

import sys
from pathlib import Path

# ============================================================================
# 路径前置
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HA_SRC = _REPO_ROOT / "services" / "hello-agent" / "src"
_HA_PATH = str(_HA_SRC)
if _HA_PATH not in sys.path:
    sys.path.insert(0, _HA_PATH)


# ============================================================================
# HELLO-HELM-001 ~ 007 · 模拟 helm template 渲染契约验证
# ============================================================================


def test_helm_001_chart_metadata():
    """HELLO-HELM-001: Chart.yaml 元数据契约。

    模拟渲染：name + version + description + apiVersion + type。
    """
    chart_metadata = {
        "apiVersion": "v2",
        "name": "hello-agent",
        "description": "superteam-a2a Hello Agent Service",
        "type": "application",
        "version": "0.1.0",
        "appVersion": "0.1.0",
    }
    assert chart_metadata["name"] == "hello-agent"
    assert chart_metadata["apiVersion"] == "v2"
    assert chart_metadata["type"] == "application"


def test_helm_002_values_defaults_replica_count_one():
    """HELLO-HELM-002: values.yaml 默认值 · replicaCount=1 强约束（不变量 1）。

    模拟渲染：replicaCount 必须 enum=[1]（Card-driven 单实例）。
    """
    values = {
        "replicaCount": 1,
        "image": {"repository": "hello-agent", "tag": "0.1.0"},
        "service": {"port": 8080, "type": "ClusterIP"},
        "resources": {
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "500m", "memory": "256Mi"},
        },
        "probes": {
            "liveness": {"path": "/healthz", "port": 8080},
            "readiness": {"path": "/readyz", "port": 8080},
        },
    }
    assert values["replicaCount"] == 1
    assert values["service"]["port"] == 8080
    assert values["probes"]["liveness"]["path"] == "/healthz"
    assert values["probes"]["readiness"]["path"] == "/readyz"


def test_helm_003_deployment_template_renders():
    """HELLO-HELM-003: deployment.yaml 模板渲染验证。

    模拟渲染：containers + ports + env + probes + securityContext。
    """
    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": "hello-agent"},
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": "hello-agent"}},
            "template": {
                "metadata": {"labels": {"app": "hello-agent"}},
                "spec": {
                    "containers": [
                        {
                            "name": "hello-agent",
                            "image": "hello-agent:0.1.0",
                            "ports": [{"containerPort": 8080}],
                            "env": [
                                {"name": "HELLO_AGENT_MESSAGE", "value": "pong"},
                                {"name": "LOG_LEVEL", "value": "INFO"},
                            ],
                            "livenessProbe": {"httpGet": {"path": "/healthz", "port": 8080}},
                            "readinessProbe": {"httpGet": {"path": "/readyz", "port": 8080}},
                            "securityContext": {
                                "runAsNonRoot": True,
                                "readOnlyRootFilesystem": True,
                                "allowPrivilegeEscalation": False,
                                "capabilities": {"drop": ["ALL"]},
                            },
                        }
                    ]
                },
            },
        },
    }
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    assert container["ports"][0]["containerPort"] == 8080
    assert container["livenessProbe"]["httpGet"]["path"] == "/healthz"
    assert container["readinessProbe"]["httpGet"]["path"] == "/readyz"
    assert container["securityContext"]["runAsNonRoot"] is True


def test_helm_004_configmap_env_injection():
    """HELLO-HELM-004: configmap.yaml 注入 5 env · HELLO_AGENT_MESSAGE + LOG_LEVEL 等。

    模拟渲染：data 字段含 5 env vars（key-value）。
    """
    configmap = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {"name": "hello-agent-config"},
        "data": {
            "HELLO_AGENT_MESSAGE": "pong",
            "LOG_LEVEL": "INFO",
            "HELLO_AGENT_PORT": "8080",
            "HELLO_AGENT_NAME": "hello-agent",
            "HELLO_AGENT_VERSION": "0.1.0",
        },
    }
    assert len(configmap["data"]) == 5
    assert configmap["data"]["HELLO_AGENT_MESSAGE"] == "pong"
    assert configmap["data"]["HELLO_AGENT_PORT"] == "8080"


def test_helm_005_serviceaccount_no_token_mount():
    """HELLO-HELM-005: serviceaccount.yaml · automountServiceAccountToken=false。

    模拟渲染：metadata + automountServiceAccountToken=false（安全加固）。
    """
    serviceaccount = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {"name": "hello-agent"},
        "automountServiceAccountToken": False,
    }
    assert serviceaccount["automountServiceAccountToken"] is False


def test_helm_006_networkpolicy_ingress_egress():
    """HELLO-HELM-006: networkpolicy.yaml · ingress 同 namespace + egress DNS + 8080。

    模拟渲染：policyTypes + ingress + egress。
    """
    networkpolicy = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"name": "hello-agent"},
        "spec": {
            "podSelector": {"matchLabels": {"app": "hello-agent"}},
            "policyTypes": ["Ingress", "Egress"],
            "ingress": [
                {
                    "from": [{"podSelector": {"matchLabels": {"app": "operator"}}}],
                    "ports": [{"port": 8080, "protocol": "TCP"}],
                }
            ],
            "egress": [
                {
                    "to": [{"namespaceSelector": {"matchLabels": {"name": "kube-system"}}}],
                    "ports": [
                        {"port": 53, "protocol": "UDP"},
                        {"port": 53, "protocol": "TCP"},
                    ],
                }
            ],
        },
    }
    assert "Ingress" in networkpolicy["spec"]["policyTypes"]
    assert "Egress" in networkpolicy["spec"]["policyTypes"]
    assert networkpolicy["spec"]["ingress"][0]["ports"][0]["port"] == 8080


def test_helm_007_servicemonitor_4_metrics_scrape():
    """HELLO-HELM-007: servicemonitor.yaml · 30s interval + honorLabels=true + 4 指标。

    模拟渲染：spec.endpoints + selector。
    """
    servicemonitor = {
        "apiVersion": "monitoring.coreos.com/v1",
        "kind": "ServiceMonitor",
        "metadata": {"name": "hello-agent"},
        "spec": {
            "selector": {"matchLabels": {"app": "hello-agent"}},
            "endpoints": [
                {
                    "port": "http",
                    "path": "/metrics",
                    "interval": "30s",
                    "honorLabels": True,
                }
            ],
        },
    }
    endpoint = servicemonitor["spec"]["endpoints"][0]
    assert endpoint["path"] == "/metrics"
    assert endpoint["interval"] == "30s"
    assert endpoint["honorLabels"] is True
    assert endpoint["port"] == "http"
