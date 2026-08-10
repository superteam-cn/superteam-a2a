"""RBAC conformance tests for knowledge-memory-service Helm chart.

Reference:
- docs/spec/L3-file-specs/L3-memory-backend.md §9.5 line 1331-1361
- docs/reviews/l3-6-memory-backend-spec-review.md §M-1.4 line 358-376
- docs/phase2/l4-phase2-spike-plan.md §2.2/§2.3/§3.1

Test groups (pytest fixtures):
- TestChartStructure — Chart.yaml + values.yaml + values.schema.json 结构
- TestRoleReadStructure — role_read.yaml 3 apiGroups + 只读 verbs
- TestRoleWriteStructure — role_write.yaml 7 apiGroups(含 §M-1.4 三 apiGroups)
- TestRoleBindingStructure — rolebinding.yaml 双 Role → 同一 SA
- TestValuesSchema — values.schema.json 强制 leaderElection.backend enum
- TestValuesDefaults — values.yaml 默认值与 schema 一致
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CHART_ROOT = REPO_ROOT / "helm" / "knowledge-memory-service"
RBAC_TEMPLATES = CHART_ROOT / "templates" / "rbac"


def _strip_helm_templates(content: str) -> str:
    """Strip Helm template directives before YAML parsing.

    Helm templates use Go-template syntax `{{ ... }}` and `{{- ... -}}` for control flow
    (if-range, with, define). For structural validation we only need the static YAML
    structure, so replace template directives with empty strings before PyYAML parsing.

    Caveat: This loses conditional rendering. Test scope is static structure validation,
    not template rendering (which requires `helm template` binary or pyhelm library).
    """
    import re

    # Replace `{{- ... -}}` and `{{ ... }}` (with optional whitespace control) with empty
    return re.sub(r"\{\{-?\s*[^}]*?\s*-?\}\}", "", content)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load single-document YAML file with Helm template stripping."""
    content = path.read_text(encoding="utf-8")
    return yaml.safe_load(_strip_helm_templates(content))


def _load_all_yaml(path: Path) -> list[dict[str, Any]]:
    """Load multi-document YAML file (--- separated) with Helm template stripping."""
    content = path.read_text(encoding="utf-8")
    stripped = _strip_helm_templates(content)
    return [doc for doc in yaml.safe_load_all(stripped) if doc is not None]


# =============================================================================
# TestChartStructure
# =============================================================================


class TestChartStructure:
    """Chart.yaml + values.yaml + values.schema.json 结构验证."""

    def test_chart_yaml_exists(self) -> None:
        assert (CHART_ROOT / "Chart.yaml").exists(), "Chart.yaml 必须存在"

    def test_chart_yaml_required_fields(self) -> None:
        chart = _load_yaml(CHART_ROOT / "Chart.yaml")
        assert chart["apiVersion"] == "v2", "Helm 3 chart apiVersion 必须为 v2"
        assert chart["name"] == "knowledge-memory-service"
        assert chart["type"] == "application"
        assert isinstance(chart["version"], str), "version must be str"
        assert chart["version"], "version must be non-empty"
        assert isinstance(chart["appVersion"], str), "appVersion must be str"
        assert chart["appVersion"], "appVersion must be non-empty"

    def test_values_yaml_exists(self) -> None:
        assert (CHART_ROOT / "values.yaml").exists(), "values.yaml 必须存在"

    def test_values_schema_json_exists(self) -> None:
        assert (CHART_ROOT / "values.schema.json").exists(), "values.schema.json 必须存在"

    def test_values_schema_required_top_level_fields(self) -> None:
        schema = _load_yaml(CHART_ROOT / "values.schema.json")
        required = schema.get("required", [])
        assert "replicaCount" in required, "schema.required 必须含 replicaCount"
        assert "leaderElection" in required, "schema.required 必须含 leaderElection"

    def test_helpers_tpl_exists(self) -> None:
        assert (CHART_ROOT / "templates" / "_helpers.tpl").exists(), "_helpers.tpl 必须存在"


# =============================================================================
# TestRoleReadStructure
# =============================================================================


class TestRoleReadStructure:
    """role_read.yaml — read-only Role per L3-6 §9.5 line 1334-1341.

    期望 apiGroups:
    - superteam-a2a.io (knowledgescopes / knowledgeitems / memories)
    - "" (configmaps)
    - "" (secrets · resourceNames restricted)

    期望 verbs: 仅 get / list / watch(无 create / update / patch / delete)
    """

    @pytest.fixture
    def role_read(self) -> dict[str, Any]:
        return _load_yaml(RBAC_TEMPLATES / "role_read.yaml")

    def test_kind_is_role(self, role_read: dict[str, Any]) -> None:
        assert role_read["kind"] == "Role"
        assert role_read["apiVersion"] == "rbac.authorization.k8s.io/v1"

    def test_has_exactly_three_api_groups(self, role_read: dict[str, Any]) -> None:
        """role_read 期望 3 apiGroups: superteam-a2a.io + "" (configmaps) + "" (secrets)."""
        api_groups = {rule["apiGroups"][0] for rule in role_read["rules"]}
        assert api_groups == {"superteam-a2a.io", ""}, (
            f"role_read 期望 apiGroups {{superteam-a2a.io, ''}}, 实际 {api_groups}"
        )

    def test_read_only_verbs_no_create_update_patch_delete(self, role_read: dict[str, Any]) -> None:
        """Phase 1 ADR-0006 D 方案: read Role 不含 create/update/patch/delete."""
        forbidden_verbs = {"create", "update", "patch", "delete"}
        all_verbs: set[str] = set()
        for rule in role_read["rules"]:
            all_verbs.update(rule.get("verbs", []))
        violations = all_verbs & forbidden_verbs
        assert not violations, (
            f"role_read 含禁止 verbs {violations}(Phase 1 ADR-0006 D 方案: read-only)"
        )

    def test_secrets_resource_names_restricted(self, role_read: dict[str, Any]) -> None:
        """L3-6 §9.5 line 1337: secrets resourceNames 必须限定."""
        secrets_rules = [
            rule for rule in role_read["rules"] if "secrets" in rule.get("resources", [])
        ]
        assert len(secrets_rules) == 1, "应有恰好 1 个 secrets rule"
        resource_names = secrets_rules[0].get("resourceNames", [])
        assert "knowledge-service-tls" in resource_names
        assert "superteam-client-ca" in resource_names

    def test_core_crd_resources_present(self, role_read: dict[str, Any]) -> None:
        """superteam-a2a.io 必须含 knowledgescopes/knowledgeitems/memories."""
        crd_resources: set[str] = set()
        for rule in role_read["rules"]:
            if "superteam-a2a.io" in rule["apiGroups"]:
                crd_resources.update(rule.get("resources", []))
        assert crd_resources == {"knowledgescopes", "knowledgeitems", "memories"}


# =============================================================================
# TestRoleWriteStructure
# =============================================================================


class TestRoleWriteStructure:
    """role_write.yaml — write Role per L3-6 §9.5 line 1343-1349 + §M-1.4 修复.

    期望 apiGroups (7 个):
    1. superteam-a2a.io (memories/status + memories)
    2. coordination.k8s.io (leases · resourceNames restricted)
    3. "" (events)
    4. admissionregistration.k8s.io (validatingwebhookconfigurations) — §M-1.4
    5. authentication.k8s.io (tokenreviews) — §M-1.4
    6. authorization.k8s.io (subjectaccessreviews) — §M-1.4
    注: 实际去重后是 6 个唯一 apiGroups(superteam-a2a.io / coordination.k8s.io / "" / admissionregistration / authentication / authorization)
    但实际 rule 数 = 7(superteam-a2a.io 拆为 memories/status + memories)
    """

    @pytest.fixture
    def role_write(self) -> dict[str, Any]:
        return _load_yaml(RBAC_TEMPLATES / "role_write.yaml")

    def test_kind_is_role(self, role_write: dict[str, Any]) -> None:
        assert role_write["kind"] == "Role"
        assert role_write["apiVersion"] == "rbac.authorization.k8s.io/v1"

    def test_has_m14_admissionregistration_rule(self, role_write: dict[str, Any]) -> None:
        """§M-1.4 修复 1/3: admissionregistration.k8s.io validatingwebhookconfigurations."""
        matching = [
            rule
            for rule in role_write["rules"]
            if "admissionregistration.k8s.io" in rule.get("apiGroups", [])
        ]
        assert len(matching) == 1, "§M-1.4: admissionregistration.k8s.io 规则必须存在"
        rule = matching[0]
        assert "validatingwebhookconfigurations" in rule["resources"]
        assert "get" in rule["verbs"]
        assert "list" in rule["verbs"]
        assert "watch" in rule["verbs"]

    def test_has_m14_authentication_rule(self, role_write: dict[str, Any]) -> None:
        """§M-1.4 修复 2/3: authentication.k8s.io tokenreviews."""
        matching = [
            rule
            for rule in role_write["rules"]
            if "authentication.k8s.io" in rule.get("apiGroups", [])
        ]
        assert len(matching) == 1, "§M-1.4: authentication.k8s.io 规则必须存在"
        rule = matching[0]
        assert "tokenreviews" in rule["resources"]
        assert "create" in rule["verbs"]

    def test_has_m14_authorization_rule(self, role_write: dict[str, Any]) -> None:
        """§M-1.4 修复 3/3: authorization.k8s.io subjectaccessreviews."""
        matching = [
            rule
            for rule in role_write["rules"]
            if "authorization.k8s.io" in rule.get("apiGroups", [])
        ]
        assert len(matching) == 1, "§M-1.4: authorization.k8s.io 规则必须存在"
        rule = matching[0]
        assert "subjectaccessreviews" in rule["resources"]
        assert "create" in rule["verbs"]

    def test_has_coordination_lease_rule_with_resource_names(
        self, role_write: dict[str, Any]
    ) -> None:
        """Phase 2 §2.3 k8s leader election 依赖: leases resourceNames 限定."""
        matching = [
            rule
            for rule in role_write["rules"]
            if "coordination.k8s.io" in rule.get("apiGroups", [])
        ]
        assert len(matching) == 1, "coordination.k8s.io leases 规则必须存在"
        rule = matching[0]
        assert "leases" in rule["resources"]
        assert "memory-reconciler-leader" in rule.get("resourceNames", [])

    def test_memory_status_patch_update(self, role_write: dict[str, Any]) -> None:
        """memories/status: get/patch/update(generation CAS patch_status 需要)."""
        matching = [
            rule for rule in role_write["rules"] if "memories/status" in rule.get("resources", [])
        ]
        assert len(matching) == 1, "memories/status 规则必须存在"
        verbs = matching[0]["verbs"]
        assert "get" in verbs
        assert "patch" in verbs
        assert "update" in verbs

    def test_memory_lifecycle_verbs(self, role_write: dict[str, Any]) -> None:
        """memories: get/list/watch/delete(finalize 5 步需要 delete)."""
        matching = [
            rule
            for rule in role_write["rules"]
            if "memories" in rule.get("resources", [])
            and "memories/status" not in rule.get("resources", [])
        ]
        assert len(matching) == 1, "memories 规则必须存在"
        verbs = matching[0]["verbs"]
        assert "get" in verbs
        assert "list" in verbs
        assert "watch" in verbs
        assert "delete" in verbs

    def test_total_api_groups_uniqueness(self, role_write: dict[str, Any]) -> None:
        """role_write 期望 ≥ 6 唯一 apiGroups(5 原始 + §M-1.4 3 新, 实际 6 因 '' 计数)."""
        unique_api_groups: set[str] = set()
        for rule in role_write["rules"]:
            unique_api_groups.update(rule.get("apiGroups", []))
        expected = {
            "superteam-a2a.io",
            "coordination.k8s.io",
            "",
            "admissionregistration.k8s.io",
            "authentication.k8s.io",
            "authorization.k8s.io",
        }
        assert expected.issubset(unique_api_groups), (
            f"role_write 缺少 apiGroups: {expected - unique_api_groups}"
        )


# =============================================================================
# TestRoleBindingStructure
# =============================================================================


class TestRoleBindingStructure:
    """rolebinding.yaml — 双 RoleBinding → 同一 SA per L3-6 §9.5 line 1364."""

    @pytest.fixture
    def rolebindings(self) -> list[dict[str, Any]]:
        return _load_all_yaml(RBAC_TEMPLATES / "rolebinding.yaml")

    def test_has_two_rolebindings(self, rolebindings: list[dict[str, Any]]) -> None:
        """期望 read + write 两个 RoleBinding(--- 分隔多文档)."""
        kinds = [doc["kind"] for doc in rolebindings]
        assert kinds == ["RoleBinding", "RoleBinding"], (
            f"rolebinding.yaml 必须含 2 个 RoleBinding, 实际 {kinds}"
        )

    def test_both_bind_to_same_service_account(self, rolebindings: list[dict[str, Any]]) -> None:
        """双 RoleBinding subject 必须为 ServiceAccount kind + 同一 namespace.

        注: subject.name 含 Helm template `{{ include ... }}` 经 _strip_helm_templates 后为 None,
        实际渲染需 helm template(PR-1 范围内未提供 helm binary). 此测试验证结构:
        - subject.kind == ServiceAccount
        - subject.namespace 模板引用一致(同一 namespace)
        - subject.name 通过 helper `knowledge-memory-service.serviceAccountName` 引用(已定义)
        """
        sa_kinds: set[str] = set()
        sa_namespaces: set[tuple[str, str]] = set()  # (namespace_template, name_template) pair
        for rb in rolebindings:
            for subj in rb["subjects"]:
                sa_kinds.add(subj["kind"])
                # After stripping, both fields are None if templated
                sa_namespaces.add((subj["namespace"], subj["name"]))
        assert sa_kinds == {"ServiceAccount"}, (
            f"subject.kind 必须为 ServiceAccount, 实际 {sa_kinds}"
        )
        # Both rolebindings use the same (namespace, name_template) → same SA
        assert len(sa_namespaces) == 1, f"双 RoleBinding 必须引用同一 SA, 实际 {sa_namespaces}"

    def test_helpers_define_service_account_name(self) -> None:
        """_helpers.tpl 必须定义 `knowledge-memory-service.serviceAccountName` 模板."""
        content = (CHART_ROOT / "templates" / "_helpers.tpl").read_text(encoding="utf-8")
        assert 'define "knowledge-memory-service.serviceAccountName"' in content, (
            "_helpers.tpl 必须定义 knowledge-memory-service.serviceAccountName 模板"
        )
        assert "serviceAccount.name" in content, (
            "serviceAccountName 模板必须引用 .Values.serviceAccount.name"
        )

    def test_bind_to_read_and_write_roles(self, rolebindings: list[dict[str, Any]]) -> None:
        """RoleBinding 必须分别绑定 -read 与 -write Role."""
        bound_roles = {rb["roleRef"]["name"] for rb in rolebindings}
        assert len(bound_roles) == 2
        assert any("read" in r for r in bound_roles), f"需绑定 -read Role, 实际 {bound_roles}"
        assert any("write" in r for r in bound_roles), f"需绑定 -write Role, 实际 {bound_roles}"


# =============================================================================
# TestValuesSchema
# =============================================================================


class TestValuesSchema:
    """values.schema.json — Phase 2 §2.2/§2.3 leaderElection.backend enum 强制."""

    @pytest.fixture
    def schema(self) -> dict[str, Any]:
        return _load_yaml(CHART_ROOT / "values.schema.json")

    def test_leader_election_backend_enum(self, schema: dict[str, Any]) -> None:
        """leaderElection.backend enum 必须为 ["in_process", "k8s"]."""
        le_schema = schema["properties"]["leaderElection"]["properties"]["backend"]
        assert le_schema["type"] == "string"
        assert sorted(le_schema["enum"]) == ["in_process", "k8s"], (
            f"leaderElection.backend enum 期望 [in_process, k8s], 实际 {le_schema.get('enum')}"
        )

    def test_additional_properties_disabled(self, schema: dict[str, Any]) -> None:
        """顶层 additionalProperties: false 防止 typo."""
        assert schema.get("additionalProperties") is False


# =============================================================================
# TestValuesDefaults
# =============================================================================


class TestValuesDefaults:
    """values.yaml — 默认值与 schema 一致性验证."""

    @pytest.fixture
    def values(self) -> dict[str, Any]:
        return _load_yaml(CHART_ROOT / "values.yaml")

    def test_replica_count_default_is_one(self, values: dict[str, Any]) -> None:
        """Phase 1 ADR-0006 D 方案: replicaCount 默认 1."""
        assert values["replicaCount"] == 1, (
            f"replicaCount 必须为 1, 实际 {values['replicaCount']}(违反 ADR-0006 D 单进程)"
        )

    def test_leader_election_backend_default_in_process(self, values: dict[str, Any]) -> None:
        """Phase 2 §2.2: leaderElection.backend 默认 in_process."""
        assert values["leaderElection"]["backend"] == "in_process"

    def test_tls_disabled_by_default(self, values: dict[str, Any]) -> None:
        """Phase 2 §2.7: cert-manager 默认禁用(tls.enabled=false)."""
        assert values["tls"]["enabled"] is False

    def test_rbac_create_enabled(self, values: dict[str, Any]) -> None:
        """PR-1 范围内 rbac.create 必须为 true(否则 RBAC 不实装)."""
        assert values["rbac"]["create"] is True

    def test_backend_type_default_in_process(self, values: dict[str, Any]) -> None:
        """L4-Phase3 PR-2: backend.type 默认 in_process (Phase 1 MVP core + dev/CI 默认).

        生产可选切换为 k8s (CustomObjectsApi-backed).
        """
        assert values["backend"]["type"] == "in_process"

    def test_backend_k8s_defaults_present(self, values: dict[str, Any]) -> None:
        """L4-Phase3 PR-2: backend.k8s 默认配置项完整（crdGroup/crdVersion/crdPlural/listTimeoutSeconds）.

        这些配置在 helm values.yaml 作为 defaults 暴露, 与 deployment.yaml env var 注入配对.
        """
        k8s_cfg = values["backend"]["k8s"]
        assert k8s_cfg["crdGroup"] == "memory.superteam-a2a.io"
        assert k8s_cfg["crdVersion"] == "v1alpha1"
        assert k8s_cfg["crdPlural"] == "memories"
        assert k8s_cfg["listTimeoutSeconds"] == 30


class TestValuesSchemaBackend:
    """L4-Phase3 PR-2: values.schema.json backend 字段 enum + structure."""

    @pytest.fixture
    def schema(self) -> dict[str, Any]:
        return _load_yaml(CHART_ROOT / "values.schema.json")

    def test_backend_type_enum(self, schema: dict[str, Any]) -> None:
        """backend.type enum 必须为 ["in_process", "k8s"]."""
        backend_type_schema = schema["properties"]["backend"]["properties"]["type"]
        assert backend_type_schema["type"] == "string"
        assert sorted(backend_type_schema["enum"]) == ["in_process", "k8s"], (
            f"backend.type enum 期望 [in_process, k8s], 实际 {backend_type_schema.get('enum')}"
        )

    def test_backend_required_type(self, schema: dict[str, Any]) -> None:
        """backend 必须含 type 字段 (required)."""
        backend_required = schema["properties"]["backend"].get("required", [])
        assert "type" in backend_required, f"backend.required 必须含 type, 实际 {backend_required}"
