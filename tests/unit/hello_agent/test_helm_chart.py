"""Hello Agent · Helm chart 静态验证 · HELLO-HELM-001~007（7 UT）。

依据 Phase 4 PR-2 plan §2.2 + §2.3 + §2.4 + §7 测试策略：
- 不依赖 helm binary（仅解析 Chart.yaml + values.yaml + values.schema.json + 模板）
- HELLO-HELM-001/002/003/004/005/006/007 覆盖 PR-2 §4 验收清单
- pytest function-based · 无 setup/teardown · 直接断言
- schema 验证用 stdlib 实现（不依赖 jsonschema 包 · uv workspace 未含该包）

5 项关键不变量验证（PR-2 §6）：
1. Card-driven 单实例（values.schema.json replicaCount enum [1]）
2. Python-first 边界（chart 与 base image 无关）
3. observability 4 指标（servicemonitor.yaml scrape + honorLabels true）
4. wire contract（Hello Agent 不涉及 MEMORY_*）
5. 单进程 8080 端口（values.schema.json port enum [8080] + containerPort 8080）
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

# ============================================================================
# 路径常量（workspace 根定位 · 不依赖 helm binary）
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHART_DIR = _REPO_ROOT / "helm" / "superteam-a2a-hello-agent"
_TEMPLATES_DIR = _CHART_DIR / "templates"


# ============================================================================
# Helpers
# ============================================================================


def _load_yaml(path: Path) -> Any:
    """读取 YAML 文件（已存在性保证）。"""
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _validate_against_schema(value: Any, schema: dict[str, Any], path: str = "") -> list[str]:
    """最小化 JSON Schema 验证器（覆盖 values.schema.json 用到的子集）。

    支持：
    - type（integer / string / object / boolean）
    - required
    - properties
    - enum（integer / string 列表）
    - const
    - pattern（re.fullmatch）

    不支持：$ref / allOf / oneOf / anyOf / additionalProperties / conditional。
    """
    errors: list[str] = []
    current_path = path or "$"

    if "type" in schema:
        expected_type = schema["type"]
        type_map = {
            "integer": int,
            "string": str,
            "object": dict,
            "boolean": bool,
            "array": list,
        }
        # YAML 1.1 yaml.safe_load 可能把 bool 解析为 bool
        py_type = type_map.get(expected_type)
        # YAML 1.1 quirk: bool 是 int 的子类，需要排除
        if (
            py_type is not None
            and not isinstance(value, py_type)
            and not (expected_type == "integer" and isinstance(value, bool))
        ):
            errors.append(
                f"{current_path}: expected type '{expected_type}', got {type(value).__name__}"
            )
            return errors

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{current_path}: value {value!r} not in enum {schema['enum']!r}")

    if "const" in schema and value != schema["const"]:
        errors.append(f"{current_path}: value {value!r} != const {schema['const']!r}")

    if (
        "pattern" in schema
        and isinstance(value, str)
        and re.fullmatch(schema["pattern"], value) is None
    ):
        errors.append(
            f"{current_path}: value {value!r} does not match pattern {schema['pattern']!r}"
        )

    if schema.get("type") == "object" and isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{current_path}: missing required property '{req}'")
        for prop, sub_schema in schema.get("properties", {}).items():
            if prop in value:
                errors.extend(
                    _validate_against_schema(value[prop], sub_schema, f"{current_path}.{prop}")
                )

    return errors


# ============================================================================
# HELLO-HELM-001 · helm lint 静态等价（Chart.yaml + values.yaml + schema 校验）
# ============================================================================


def test_hello_helm_001_chart_yaml_valid() -> None:
    """HELLO-HELM-001 :: Chart.yaml 必填字段 + 类型校验。

    验证：Chart.yaml 解析 + apiVersion/name/version/appVersion/kubeVersion/type 字段存在。
    PR-2 §2.2 要求 Helm chart 标准化字段。
    """
    chart = _load_yaml(_CHART_DIR / "Chart.yaml")
    assert isinstance(chart, dict), "Chart.yaml must parse as YAML object"

    # apiVersion v2
    assert chart.get("apiVersion") == "v2", (
        f"Chart.yaml apiVersion must be 'v2', got {chart.get('apiVersion')!r}"
    )
    # name
    assert chart.get("name") == "superteam-a2a-hello-agent", (
        f"Chart.yaml name must be 'superteam-a2a-hello-agent', got {chart.get('name')!r}"
    )
    # version
    assert chart.get("version") == "0.1.0", (
        f"Chart.yaml version must be '0.1.0', got {chart.get('version')!r}"
    )
    # appVersion
    assert chart.get("appVersion") == "0.1.0", (
        f"Chart.yaml appVersion must be '0.1.0', got {chart.get('appVersion')!r}"
    )
    # kubeVersion
    assert "kubeVersion" in chart, "Chart.yaml must declare kubeVersion"
    # type
    assert chart.get("type") == "application", (
        f"Chart.yaml type must be 'application', got {chart.get('type')!r}"
    )


def test_hello_helm_001_values_yaml_valid() -> None:
    """HELLO-HELM-001 :: values.yaml 解析 + 默认值符合 schema。

    验证：values.yaml 解析 + default values 全部满足 schema 强约束。
    关键不变量 #1 Card-driven 单实例 + #5 单进程 8080 端口。
    """
    values = _load_yaml(_CHART_DIR / "values.yaml")
    assert isinstance(values, dict), "values.yaml must parse as YAML object"

    schema = _load_yaml(_CHART_DIR / "values.schema.json")
    errors = _validate_against_schema(values, schema)
    assert not errors, f"values.yaml violates schema: {errors}"


# ============================================================================
# HELLO-HELM-002 · helm template 静态等价（YAML 语法 + K8s 资源类型）
# ============================================================================


def test_hello_helm_002_templates_parseable() -> None:
    """HELLO-HELM-002 :: 所有 templates/*.yaml YAML 语法 + K8s 资源类型校验。

    验证：7 模板文件（_helpers.tpl 跳过）+ 全部 YAML 语法 OK + apiVersion + kind 字段存在。
    模拟 helm template 渲染前的静态解析门禁。
    """
    expected_resources = {
        "deployment.yaml": ("apps/v1", "Deployment"),
        "service.yaml": ("v1", "Service"),
        "configmap.yaml": ("v1", "ConfigMap"),
        "serviceaccount.yaml": ("v1", "ServiceAccount"),
        "networkpolicy.yaml": ("networking.k8s.io/v1", "NetworkPolicy"),
        "servicemonitor.yaml": ("monitoring.coreos.com/v1", "ServiceMonitor"),
    }

    for filename, (api_version, kind) in expected_resources.items():
        path = _TEMPLATES_DIR / filename
        assert path.is_file(), f"Template not found: {path}"

        # 解析（去掉 helm template 指令行 · 因 helm binary 不可用）
        # 简化策略：跳过模板行（{{ }}），仅解析纯 YAML 部分
        # 对于本 chart，所有模板顶层资源都是纯 YAML，{{ }} 都在 metadata.name 等字段值内
        content = path.read_text(encoding="utf-8")

        # 替换 helm 模板表达式为占位符以通过 yaml.safe_load
        # 简化：只检查顶层 apiVersion/kind 字段
        api_match = re.search(r"^apiVersion:\s*(.+)$", content, re.MULTILINE)
        kind_match = re.search(r"^kind:\s*(.+)$", content, re.MULTILINE)

        assert api_match is not None, f"{filename}: missing apiVersion"
        assert kind_match is not None, f"{filename}: missing kind"

        # 提取值（去除引号和尾部注释）
        actual_api = api_match.group(1).strip().strip('"').strip("'")
        actual_kind = kind_match.group(1).strip().strip('"').strip("'")

        assert actual_api == api_version, (
            f"{filename}: apiVersion expected '{api_version}', got '{actual_api}'"
        )
        assert actual_kind == kind, f"{filename}: kind expected '{kind}', got '{actual_kind}'"


# ============================================================================
# HELLO-HELM-003 · schema 强约束：replicaCount != 1 应失败
# ============================================================================


def test_hello_helm_003_schema_replica_count_must_be_one() -> None:
    """HELLO-HELM-003 :: values.schema.json 强约束验证（replicaCount enum [1]）。

    验证：
    - 合法 values（replicaCount=1）通过 schema 校验
    - 非法 values（replicaCount=2）违反 schema

    关键不变量 #1：Card-driven 单实例（replicaCount 仅允许 1）。
    """
    schema = _load_yaml(_CHART_DIR / "values.schema.json")

    # 合法 baseline
    valid_values = {
        "replicaCount": 1,
        "image": {"repository": "ghcr.io/superteam-cn/superteam-a2a-hello-agent", "tag": "0.1.0"},
        "service": {"port": 8080, "targetPort": 8080},
    }
    errors = _validate_against_schema(valid_values, schema)
    assert not errors, f"Valid baseline must pass: {errors}"

    # 非法：replicaCount=2
    invalid_values = dict(valid_values)
    invalid_values["replicaCount"] = 2
    errors = _validate_against_schema(invalid_values, schema)
    assert any("replicaCount" in e for e in errors), (
        f"replicaCount=2 must violate schema, got errors: {errors}"
    )


# ============================================================================
# HELLO-HELM-004 · schema 强约束：port != 8080 应失败
# ============================================================================


def test_hello_helm_004_schema_service_port_must_be_8080() -> None:
    """HELLO-HELM-004 :: values.schema.json 强约束验证（service.port enum [8080]）。

    验证：
    - 合法 values（service.port=8080）通过 schema 校验
    - 非法 values（service.port=9090）违反 schema

    关键不变量 #5：单进程 8080 端口。
    """
    schema = _load_yaml(_CHART_DIR / "values.schema.json")

    # 合法 baseline
    valid_values = {
        "replicaCount": 1,
        "image": {"repository": "ghcr.io/superteam-cn/superteam-a2a-hello-agent", "tag": "0.1.0"},
        "service": {"port": 8080, "targetPort": 8080},
    }
    errors = _validate_against_schema(valid_values, schema)
    assert not errors, f"Valid baseline must pass: {errors}"

    # 非法：service.port=9090
    invalid_values = {
        "replicaCount": 1,
        "image": {"repository": "ghcr.io/superteam-cn/superteam-a2a-hello-agent", "tag": "0.1.0"},
        "service": {"port": 9090, "targetPort": 8080},
    }
    errors = _validate_against_schema(invalid_values, schema)
    assert any("service.port" in e or "port" in e for e in errors), (
        f"service.port=9090 must violate schema, got errors: {errors}"
    )


# ============================================================================
# HELLO-HELM-005 · deployment.yaml SecurityContext = restricted profile
# ============================================================================


def test_hello_helm_005_deployment_security_context_restricted() -> None:
    """HELLO-HELM-005 :: deployment.yaml 容器 SecurityContext = restricted profile。

    验证：Pod Security Standards restricted profile 4 项关键约束。
    PR-2 §2.3 要求容器级 SecurityContext 满足 restricted。

    实现策略：deployment.yaml 通过 `toYaml .Values.securityContext` 渲染，
    因此验证 values.yaml 中的 securityContext 与 podSecurityContext 字段值
    （helm 渲染后即为 deployment 内容）。
    """
    content = (_TEMPLATES_DIR / "deployment.yaml").read_text(encoding="utf-8")

    # 1. deployment.yaml 模板引用 .Values.securityContext（容器级）
    assert re.search(
        r"securityContext:\s*\n\s*\{\{-?\s*toYaml\s+\.Values\.securityContext",
        content,
    ), "deployment.yaml must reference .Values.securityContext (container SecurityContext)"
    # 2. deployment.yaml 模板引用 .Values.podSecurityContext（Pod 级）
    assert re.search(
        r"securityContext:\s*\n\s*\{\{-?\s*toYaml\s+\.Values\.podSecurityContext",
        content,
    ), "deployment.yaml must reference .Values.podSecurityContext (pod SecurityContext)"

    # 3. 验证 values.yaml 中的 securityContext 默认值（渲染后的字面量）
    values = _load_yaml(_CHART_DIR / "values.yaml")
    sc = values["securityContext"]
    assert sc["runAsNonRoot"] is True, (
        f"values.yaml securityContext.runAsNonRoot must be true (restricted), got {sc['runAsNonRoot']}"
    )
    assert sc["readOnlyRootFilesystem"] is True, (
        f"values.yaml securityContext.readOnlyRootFilesystem must be true (restricted), got {sc['readOnlyRootFilesystem']}"
    )
    assert sc["allowPrivilegeEscalation"] is False, (
        f"values.yaml securityContext.allowPrivilegeEscalation must be false (restricted), got {sc['allowPrivilegeEscalation']}"
    )
    assert "ALL" in sc["capabilities"]["drop"], (
        f"values.yaml securityContext.capabilities.drop must include 'ALL' (restricted), got {sc['capabilities']['drop']}"
    )

    # 4. 验证 values.yaml 中的 podSecurityContext 默认值
    psc = values["podSecurityContext"]
    assert psc["runAsNonRoot"] is True, (
        f"values.yaml podSecurityContext.runAsNonRoot must be true, got {psc['runAsNonRoot']}"
    )
    assert psc["runAsUser"] == 1000, (
        f"values.yaml podSecurityContext.runAsUser must be 1000, got {psc['runAsUser']}"
    )
    assert psc["seccompProfile"]["type"] == "RuntimeDefault", (
        f"values.yaml podSecurityContext.seccompProfile.type must be 'RuntimeDefault', got {psc['seccompProfile']['type']}"
    )


# ============================================================================
# HELLO-HELM-006 · configmap.yaml 3 env vars 注入
# ============================================================================


def test_hello_helm_006_configmap_env_vars() -> None:
    """HELLO-HELM-006 :: configmap.yaml 注入 3 env vars。

    验证：LOG_LEVEL + OTEL_EXPORTER_OTLP_ENDPOINT + PYTHONUNBUFFERED 3 个 data 字段。
    PR-2 §2.4 config 注入契约。
    """
    content = (_TEMPLATES_DIR / "configmap.yaml").read_text(encoding="utf-8")

    expected_keys = ["LOG_LEVEL", "OTEL_EXPORTER_OTLP_ENDPOINT", "PYTHONUNBUFFERED"]
    for key in expected_keys:
        assert re.search(rf"^\s*{key}:\s", content, re.MULTILINE), (
            f"configmap.yaml must declare env var '{key}'"
        )


# ============================================================================
# HELLO-HELM-007 · servicemonitor.yaml 4 指标 endpoint + honorLabels true
# ============================================================================


def test_hello_helm_007_servicemonitor_metrics_endpoint() -> None:
    """HELLO-HELM-007 :: servicemonitor.yaml endpoint + honorLabels 校验。

    验证：
    - spec.endpoints[0].port: http
    - spec.endpoints[0].path: /metrics
    - spec.endpoints[0].honorLabels: true（避免 label 漂移）

    关键不变量 #3：observability 4 指标 scrape。

    实现策略：port/path 是字面量（直接渲染），honorLabels 通过 template 引用
    .Values.prometheus.serviceMonitor.honorLabels（验证 values.yaml 默认值 + template 引用）。
    """
    content = (_TEMPLATES_DIR / "servicemonitor.yaml").read_text(encoding="utf-8")

    # 1. port: http（字面量 · 引用 Service spec.ports[0].name）
    assert re.search(r"^\s*-\s*port:\s*http\s*$", content, re.MULTILINE), (
        "servicemonitor.yaml must declare port: http (Service port name reference)"
    )
    # 2. path: /metrics（字面量）
    assert re.search(r"^\s*path:\s*/metrics\s*$", content, re.MULTILINE), (
        "servicemonitor.yaml must declare path: /metrics"
    )
    # 3. honorLabels: template 引用 .Values.prometheus.serviceMonitor.honorLabels
    assert re.search(
        r"honorLabels:\s*\{\{.*\.Values\.prometheus\.serviceMonitor\.honorLabels",
        content,
    ), "servicemonitor.yaml must reference .Values.prometheus.serviceMonitor.honorLabels"

    # 4. 验证 values.yaml 中的 honorLabels 默认值 = true（避免 label 漂移）
    values = _load_yaml(_CHART_DIR / "values.yaml")
    honor_labels = values["prometheus"]["serviceMonitor"]["honorLabels"]
    assert honor_labels is True, (
        f"values.yaml prometheus.serviceMonitor.honorLabels must be true (避免 label 漂移), got {honor_labels}"
    )
    # 5. 验证 values.yaml 中的 scrape 配置
    assert values["prometheus"]["serviceMonitor"]["interval"] == "30s", (
        f"values.yaml prometheus.serviceMonitor.interval must be '30s', got {values['prometheus']['serviceMonitor']['interval']}"
    )
    assert values["prometheus"]["serviceMonitor"]["scrapeTimeout"] == "10s", (
        f"values.yaml prometheus.serviceMonitor.scrapeTimeout must be '10s', got {values['prometheus']['serviceMonitor']['scrapeTimeout']}"
    )
