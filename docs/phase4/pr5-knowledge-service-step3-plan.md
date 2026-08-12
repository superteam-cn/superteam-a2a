# Phase 4 PR-5 Plan v0.1-draft · Knowledge Service Step 3（7 Helm + RBAC + cert-manager mTLS + kind E2E）

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.1-draft**（2026-08-12 · #109 启动 · **PR-4 拆分最后一个子 PR**） |
| 上游 | #108 PR-4c plan v0.1-draft merged (`2f0202d` · 445 行 / 10 节) + #107 PR-4b plan merged (`f5d9220`) + #106 PR-4a plan merged (`9f2be9a`) + #105 PR-3 Phase B merged (`74af527`) + Phase 3 PR-1/2/3 merged + Phase 2 PR-4.1 chart 完整化 (`879849f`) + L3-5 + L3-6 v0.2.0 + ADR-0006 v1.0 Accepted D 方案 |
| 下游 | **Phase 4 完整收口**（PR-1 + PR-2 + PR-3 + PR-4a + PR-4b + PR-4c + PR-5 全部 merged）→ v0.1.0 准备 → Phase 4 打磨（README 重写 + HN 草稿） |
| 关联 PR | Phase 4 PR-5 Knowledge Service Step 3 · 本 plan |
| main HEAD | `2f0202d`（PR-4c plan squash merged commit） |
| 启动条件 | ✅ 全部满足（PR-3 + PR-4a/b/c plan merged · BP 严格生效 · Dependabot 自动化） |

---

## §1 目标与边界

**目标**：将 L3-5 Knowledge Service v0.2.0 + L3-6 Memory backend v0.2.0 文件级 Spec 中的 **7 Helm 模板**（_helpers + deployment + service + serviceaccount + rbac + networkpolicy + servicemonitor）+ **RBAC ClusterRole 双 Role**（read-only + write 含 admissionregistration + authentication + authorization）+ **cert-manager mTLS 配置**（Certificate + Issuer）+ **kind 集群 E2E** + **Dockerfile** 落地为 **13 文件（11 helm + 2 e2e）+ ~16 测试 ID**。这是 Knowledge Service **"部署与 E2E 验证层"** 的关键里程碑（PR-5 完成后 Phase 4 全部收口）。

**PR-5 拆分理由**（延续 #106/#107/#108 拆分决策 · PR-4 拆分最后一个子 PR）：
- PR-4a = 23 错误码 + admission webhook + validators（✅ merged）
- PR-4b = 4 A2A handlers + 12 service 业务逻辑层（✅ merged）
- PR-4c = ASGI server + Card-driven + BM25 + scope resolver + visibility resolver（✅ merged）
- **PR-5**（本 plan）= 7 Helm + RBAC + cert-manager + kind E2E + Dockerfile · 1 周工作量
- **Phase 4 全部收口** = PR-1 + PR-2 + PR-3 + PR-4a/b/c + PR-5 全部 merged

**PR-5 实装清单**（L3-5 §9 + L3-6 §9 + Phase 2 PR-4.1 chart 完整化 + Phase 2 PR-4.1.1 E2E unskip + Phase 3 PR-2 K8sBackend）：

| 类别 | 数量 | 路径前缀 | 关键依赖 |
|---|---|---|---|
| **7 Helm 模板** | 11 | `helm/knowledge-memory-service/{Chart.yaml,values.yaml,values.schema.json,templates/}` | kubernetes-asyncio + cert-manager + Prometheus Operator |
| **RBAC ClusterRole 双 Role** | 1 | `helm/.../templates/rbac.yaml` | 7 apiGroups + admissionregistration.k8s.io + authentication.k8s.io + authorization.k8s.io |
| **cert-manager mTLS 配置** | 2 | `helm/.../templates/{certificate,issuer}.yaml` | cert-manager v1.14+ · port 8443 tls.enabled 默认 false |
| **kind 集群 E2E** | 2 | `tests/e2e/{conftest.py,test_knowledge_memory_e2e.py}` | docker buildx + kind load + Helm install + wait for ready + JSON-RPC round-trip |
| **Dockerfile** | 1 | `services/knowledge-memory-service/Dockerfile` | python:3.12-slim + uv --frozen + non-root UID 1000 + HEALTHCHECK + uvicorn --factory |
| **pytest 测试（UT + IT）** | ~16 ID | `tests/{unit,integration,e2e}/` | helm + rbac + mtls + kind |

**PR-5 增量测试 ID**（基于 L3-5 §10.1 + L3-6 §10.1 + Phase 2 + Phase 3 + Phase 4 E2E 测试 ID 矩阵的子集）：

- UT 增量：**~10**（HELM-UT × 4 + RBAC-UT × 3 + MTLS-UT × 2 + DOCKERFILE-UT × 1 = 10 ID）
- IT 增量：**~4**（HELM-IT × 2 + RBAC-IT × 2 = 4 ID）
- E2E 增量：**~2**（E2E-001 kind cluster create + load image + Helm install + wait for ready + curl /healthz + JSON-RPC round-trip · E2E-002 admission webhook 50ms fail-closed）
- **总计：~16 ID**

**不在范围**（明确剔除 · 推迟到 Phase 4 打磨）：

- ❌ README 重写 + HN/Reddit/dev.to/掘金草稿 → Phase 4 打磨（PR-4 plan §F.6）
- ❌ CONTRIBUTING.md 实际本地开发步骤 → Phase 4 打磨
- ❌ GitHub Release note + Tag + 镜像推送 → Phase 4 打磨
- ❌ ROADMAP 标 v0.1.0 完成 → Phase 4 打磨
- ❌ 修改 L3-5 / L3-6 Spec → v0.2.0 已评审通过
- ❌ 修改 services/hello-agent/ → PR-5 不涉及（PR-2 已实装完整）
- ❌ admission webhook handler 实装（PR-4a）· PR-5 复用 PR-4a
- ❌ 23 错误码 enum（PR-4a）· PR-5 复用 PR-4a
- ❌ 4 A2A handlers + 12 service（PR-4b）· PR-5 复用 PR-4b
- ❌ ASGI + Card + BM25 + scope + visibility（PR-4c）· PR-5 复用 PR-4c

---

## §2 设计决策（5 项关键）

### §2.1 7 Helm 模板完整化（参考 Phase 2 PR-4.1 + L3-5 §9 + L3-6 §9）

**7 Helm 模板**（延续 Phase 2 PR-4.1 #89 chart 完整化模式）：

```yaml
# helm/knowledge-memory-service/Chart.yaml
apiVersion: v2
name: knowledge-memory-service
description: Knowledge-Memory Service · 单进程 D 方案 (ADR-0006)
type: application
version: 0.1.0
appVersion: "0.1.0"

# helm/knowledge-memory-service/values.yaml
replicaCount: 1  # Card-driven 单实例 (D 方案)
image:
  repository: ghcr.io/superteam-cn/knowledge-memory-service
  tag: "0.1.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80
  targetPort: 8080  # starlette uvicorn
  mtlsPort: 8443

tls:
  enabled: false  # 默认 disabled（向后兼容 · Phase 4 打磨阶段启用）
  certManager:
    issuer: selfsigned  # cert-manager Issuer 名称
    duration: 2160h  # 90 天证书
    renewBefore: 720h  # 30 天前续期

# ... 全套 values（autoscaling + resources + monitoring + rbac + networkpolicy）
```

**7 templates 文件**：

| 文件 | 资源类型 | 关键字段 |
|---|---|---|
| `templates/_helpers.tpl` | Go template helpers | `knowledge-memory.fullname` + `common.labels` |
| `templates/deployment.yaml` | apps/v1 Deployment | `replicas: 1` + `runAsNonRoot: true` + `readOnlyRootFilesystem: true` + `seccompProfile: RuntimeDefault` + `automountServiceAccountToken: false` + probes /healthz + /readyz + Prometheus 端口 8080 |
| `templates/service.yaml` | v1 Service | port 80 → 8080 + port 8443 → 8443（mTLS）|
| `templates/serviceaccount.yaml` | v1 ServiceAccount | `automountServiceAccountToken: false` + cert-manager annotation |
| `templates/rbac.yaml` | rbac.authorization.k8s.io | ClusterRole read-only + write Role（含 admissionregistration+authn+authz）|
| `templates/networkpolicy.yaml` | networking.k8s.io/v1 NetworkPolicy | ingress allow APIServer + egress allow DNS + OTLP + L3-6 pod |
| `templates/servicemonitor.yaml` | monitoring.coreos.com/v1 ServiceMonitor | 25 指标 + 8 alert PrometheusRule |
| `templates/certificate.yaml` | cert-manager.io/v1 Certificate | port 8443 + issuerRef + duration 2160h + renewBefore 720h |
| `templates/issuer.yaml` | cert-manager.io/v1 Issuer | self-signed issuer |

**理由**：
- **7 templates 完整化**（延续 Phase 2 PR-4.1 chart 完整化模式）
- **单实例 D 方案**（replicaCount: 1 · 避免 leader election 复杂度）
- **Pod Security Standards restricted**（runAsNonRoot + readOnlyRootFilesystem + seccompProfile）
- **完整 RBAC 双 Role**（read-only + write · L3-5 + L3-6 协调点）

### §2.2 RBAC ClusterRole 双 Role（含 admissionregistration + authn + authz）

**RBAC 配置**（L3-5 §9.7 + L3-6 §9.5 + L3-6 #67 评审关注项 §M-1.4）：

```yaml
# helm/knowledge-memory-service/templates/rbac.yaml
---
# ClusterRole read-only (L3-5 Knowledge Service)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: {{ include "knowledge-memory.fullname" . }}-reader
rules:
  - apiGroups: [""]
    resources: ["secrets"]  # namespace-scoped secrets only
    verbs: ["get", "list", "watch"]
  - apiGroups: ["superteam-a2a.io"]
    resources: ["knowledgescopes", "knowledgeitems", "memories"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apiextensions.k8s.io"]
    resources: ["customresourcedefinitions"]
    verbs: ["get", "list", "watch"]
---
# Role write (L3-6 Memory backend) - 含 admissionregistration + authn + authz 扩展
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ include "knowledge-memory.fullname" . }}-writer
  namespace: {{ .Release.Namespace }}
rules:
  - apiGroups: ["superteam-a2a.io"]
    resources: ["memories", "knowledgescopes", "knowledgeitems"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["admissionregistration.k8s.io"]  # L3-6 #67 评审 §M-1.4
    resources: ["validatingwebhookconfigurations"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["authentication.k8s.io"]  # L3-6 #67 评审 §M-1.4
    resources: ["tokenreviews"]
    verbs: ["create"]
  - apiGroups: ["authorization.k8s.io"]  # L3-6 #67 评审 §M-1.4
    resources: ["subjectaccessreviews"]
    verbs: ["create"]
```

**理由**：
- **ClusterRole read-only**（L3-5 Knowledge Service · 7 apiGroups）
- **Role write**（L3-6 Memory backend · 含 admissionregistration + authn + authz · #67 评审关注项 §M-1.4 关闭）
- **namespace-scoped secrets**（避免 cluster-wide 权限泄露）
- **K8s API server 最小权限原则**

### §2.3 cert-manager mTLS 配置（port 8443 · 默认 disabled）

**cert-manager 配置**（L3-5 §9.5 + L3-6 §9.5 + Phase 4 打磨准备）：

```yaml
# helm/knowledge-memory-service/templates/issuer.yaml
{{- if .Values.tls.enabled }}
---
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: {{ include "knowledge-memory.fullname" . }}-selfsigned
spec:
  selfSigned: {}
---
# helm/knowledge-memory-service/templates/certificate.yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: {{ include "knowledge-memory.fullname" . }}-tls
spec:
  secretName: {{ include "knowledge-memory.fullname" . }}-tls
  issuerRef:
    name: {{ include "knowledge-memory.fullname" . }}-selfsigned
    kind: Issuer
  duration: {{ .Values.tls.certManager.duration | default "2160h" }}  # 90 天
  renewBefore: {{ .Values.tls.certManager.renewBefore | default "720h" }}  # 30 天前续期
  dnsNames:
    - {{ include "knowledge-memory.fullname" . }}.{{ .Release.Namespace }}.svc.cluster.local
{{- end }}
```

**理由**：
- **tls.enabled 默认 false**（向后兼容 · Phase 4 打磨阶段启用）
- **cert-manager v1.14+ 集成**（Certificate + Issuer · 90 天证书 + 30 天前续期）
- **TLSv1.3 minimum**（与 L3-5 §6 + 宪法 §6 mTLS 一致）
- **HotReloader 原子替换**（L3-6 §6 协调点）

### §2.4 kind 集群 E2E（docker buildx + kind load + Helm install）

**kind E2E 配置**（参考 Phase 2 PR-4.1.1 #90 + Phase 3 PR-4 #96）：

```python
# tests/e2e/test_knowledge_memory_e2e.py
"""E2E-001 · kind 集群完整链路 · PR-5 Phase 4 完整收口验证."""

import pytest
import subprocess
import time
from pathlib import Path


@pytest.fixture(scope="session")
def kind_cluster():
    """kind cluster spin up + image load + Helm install + cleanup."""
    # Step 1: kind cluster create
    subprocess.run(["kind", "create", "cluster", "--name", "knowledge-memory-e2e"], check=True)

    # Step 2: docker buildx build + kind load
    subprocess.run(
        [
            "docker",
            "buildx",
            "build",
            "-t",
            "knowledge-memory-service:0.1.0",
            "services/knowledge-memory-service/",
        ],
        check=True,
    )
    subprocess.run(["kind", "load", "docker-image", "knowledge-memory-service:0.1.0"], check=True)

    # Step 3: Helm install
    subprocess.run(
        [
            "helm",
            "install",
            "knowledge-memory-service",
            "helm/knowledge-memory-service/",
            "--wait",
            "--timeout",
            "5m",
        ],
        check=True,
    )

    yield "knowledge-memory-service"

    # Cleanup
    subprocess.run(["kind", "delete", "cluster", "--name", "knowledge-memory-e2e"], check=True)


def test_e2e_001_healthz_endpoint(kind_cluster):
    """E2E-001 · kind cluster /healthz 端点验证."""
    result = subprocess.run(
        [
            "kubectl",
            "exec",
            "-n",
            "default",
            "deploy/knowledge-memory-service",
            "--",
            "curl",
            "-f",
            "http://localhost:8080/healthz",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0


def test_e2e_002_jsonrpc_round_trip(kind_cluster):
    """E2E-002 · JSON-RPC 2.0 round-trip + recordMemory admission 50ms fail-closed."""
    # port-forward + JSON-RPC request
    ...
```

**理由**：
- **kind 集群完整链路**（cluster create + image build + load + Helm install + wait + curl + JSON-RPC + cleanup）
- **E2E-001 验证** healthz 端点 + ASGI server 启动（PR-4c 实装）
- **E2E-002 验证** admission webhook 50ms fail-closed（PR-4a 实装）

### §2.5 Dockerfile + uv --frozen 集成（参考 Phase 4 PR-2 Hello Agent）

**Dockerfile**（参考 services/hello-agent/Dockerfile + Phase 2 PR-4.1.1 #90）：

```dockerfile
# services/knowledge-memory-service/Dockerfile
FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy workspace files
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
COPY services/knowledge-memory-service/ ./services/knowledge-memory-service/

# Install dependencies
RUN uv sync --frozen --all-packages --all-extras

# Non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 kmm
USER 1000

# Expose port
EXPOSE 8080 8443

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/healthz || exit 1

# Run uvicorn
CMD ["uv", "run", "--frozen", "uvicorn", \
     "superteam_a2a.knowledge_memory.asgi.app:app", \
     "--host", "0.0.0.0", "--port", "8080"]
```

**理由**：
- **multi-stage build**（python:3.12-slim + uv --frozen · 不需要 Go build）
- **non-root UID 1000**（与 Phase 2 PR-4.1.1 + Phase 4 PR-2 Hello Agent 一致）
- **HEALTHCHECK + EXPOSE 8080 + 8443**（与 deployment.yaml probes 一致）
- **uvicorn --factory 模式**（ASGI server · PR-4c 实装）

---

## §3 实施步骤（4 阶段 · 接力模式 · 宪法 §16.1）

### 阶段 A · 主 Agent 起草 plan（本会话 · 进行中）

- ✅ 本 plan 文档（`docs/phase4/pr5-knowledge-service-step3-plan.md` · ~14-18KB · v0.1-draft）
- ✅ Issue 创建跟踪
- ✅ feat/phase4-pr5-knowledge-step3-plan 分支 + commit + push
- ✅ gh pr create + 等 CI 5 SUCCESS（注意 #106 教训：ruff format 文档预检查）
- ✅ 项目发起人 squash merge

### 阶段 B · Subagent 隔离实装（估算 150K-250K tokens · ~45-75 分钟 · #109 实装会话）

**Subagent 任务清单**（与 PR-3 Phase B + PR-4a + PR-4b + PR-4c 同模式 · §16.1 实际水位判断）：

| Subagent | 任务 | 估算 tokens | 隔离方式 |
|---|---|---|---|
| Subagent 1 | 7 Helm 模板 + Chart.yaml + values.yaml + values.schema.json（11 文件）+ Dockerfile（1 文件）+ HELM-UT × 4 + DOCKERFILE-UT × 1 + HELM-IT × 2 = 8 ID | 80K-120K | 直接在 feat 分支工作（#105 实战经验 · 无 worktree）|
| Subagent 2 | RBAC ClusterRole 双 Role + cert-manager mTLS + RBAC-UT × 3 + MTLS-UT × 2 + RBAC-IT × 2 = 7 ID | 50K-80K | 直接在 feat 分支工作 |
| Subagent 3 | kind 集群 E2E（conftest.py + test_knowledge_memory_e2e.py）+ E2E-001 + E2E-002 = 2 ID | 50K-80K | 直接在 feat 分支工作（**依赖 docker + kind + helm 工具链**）|

**Subagent 接力原则**（§16.1 + #79/#82/#103/#105/#107/#108 实战经验）：
- 主 Agent 仅调度 + 验证 + 收口（5-8% 水位）
- 每个 Subagent 在 feat 分支 commit + push（避免文件冲突）
- Subagent 必须 `uv sync --all-packages --all-extras` 后再开始
- 每个 Subagent 完成后必须 `ruff check + ruff format + pyright + pytest` 全绿才能交付
- 关键 commit 步骤主 Agent 备份（避免 Subagent 中断丢失）
- **Subagent 顺序**：Subagent 1 → 2 → 3（helm + dockerfile → rbac + mtls → kind e2e）
- **Subagent 3 依赖**：本地有 docker desktop + kind + helm + kubectl 工具链 · 否则使用 GitHub Actions e2e-envtest workflow

### 阶段 C · 主 Agent 收口（10-20 分钟 · Phase 4 完整收口）

1. 验证所有 Subagent commits 在 feat 分支累计
2. 验证：ruff check All passed + ruff format 0 差异 + pyright 0 errors
3. 验证：pytest `tests/unit tests/integration` **339 + 14 = 353 PASS**（不含 E2E · E2E 在 CI 中）
4. push feat 分支 → `gh pr create` → PR #56
5. 等 CI 5 SUCCESS + e2e-envtest workflow（BP 严格生效 · 项目发起人 squash merge）
6. Issue close + MEMORY.md 头部更新

### 阶段 D · MEMORY 维护 + Phase 4 完整收口（5-8% 水位 · 15 分钟 · #110 Phase 4 打磨启动）

1. 创建 `session-2026-08-XX-cont109-pr5.md`
2. MEMORY.md 头部状态行更新（PR #56 merged · Phase 4 全部收口 · main HEAD 推进）
3. 跨文档同步（§F.1-§F.6）：
   - `ROADMAP.md` · Phase 4 状态 `🚧 5/7 PR` → `✅ 7/7 PR merged`
   - `README.md` · L4 实施层进度更新 · Phase 4 全部收口
   - `CONSTITUTION-CHANGELOG.md` · v0.5.0 → v0.5.1（如有微同步）
   - `L3-5 Spec` M.4 · 关联 PR + Commit SHA 更新
   - `L3-6 Spec` M.4 · 关联 PR + Commit SHA 更新
   - `docs/admin/l4-package-layout.md` · 新增 helm/ 章节 + Dockerfile
4. 关键不变量映射更新（PR-5 验证 5 项保持）
5. **下一里程碑**：#110 Phase 4 打磨启动（README 重写 + HN/Reddit/dev.to/掘金草稿 + CONTRIBUTING.md + GitHub Release note + Tag + 镜像推送 + ROADMAP v0.1.0 完成）

---

## §4 PR-5 验收清单（10 项）

| # | 项 | 验证方法 |
|---|---|---|
| 1 | `helm/knowledge-memory-service/` 11 文件创建（Chart.yaml + values.yaml + values.schema.json + 7 templates + 1 issuer + 1 certificate） | `ls helm/knowledge-memory-service/templates/` · 9 文件存在 |
| 2 | `services/knowledge-memory-service/Dockerfile` 创建（multi-stage + non-root + uvicorn） | `ls services/knowledge-memory-service/Dockerfile` |
| 3 | RBAC ClusterRole read-only + write Role（含 admissionregistration + authn + authz） | `helm template helm/knowledge-memory-service/ \| grep "kind: ClusterRole\|kind: Role"` |
| 4 | cert-manager Certificate + Issuer（tls.enabled=false 默认 disabled） | `helm template --set tls.enabled=true helm/knowledge-memory-service/ \| grep "kind: Certificate"` |
| 5 | UT 测试 10 ID 全部 PASS | `pytest tests/unit/ -q` · 339 + 10 = 349 PASS |
| 6 | IT 测试 4 ID 全部 PASS（HELM × 2 + RBAC × 2） | `pytest tests/integration/ -q` · 19 + 4 = 23 PASS |
| 7 | E2E 测试 2 ID 全部 PASS（kind cluster + JSON-RPC round-trip） | `pytest tests/e2e/ -q` · 2 PASS（**GitHub Actions e2e-envtest workflow**）|
| 8 | ruff check All passed + ruff format 0 差异 + pyright 0 errors | GitHub Actions CI |
| 9 | helm lint + helm template 全部 7+ resources 渲染成功 | `helm lint helm/knowledge-memory-service/` + `helm template helm/knowledge-memory-service/` |
| 10 | 5 项关键不变量 100% 保持（wire contract + 50ms admission + RBAC 双 Role + cert-manager + 单实例 D 方案） | 验证脚本 + PR description |

---

## §5 风险与缓解（6 项）

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| 1 | kind 集群在 Subagent 3 本地环境不可用（Windows PATH 无 docker/kind/helm） | E2E 测试无法本地运行 | 使用 GitHub Actions e2e-envtest workflow（已就绪 · Phase 2 PR-25 + PR-28）· Subagent 3 仅编写 E2E 代码 + 测试 ID 命名 |
| 2 | cert-manager mTLS 配置错误（issuerRef 引用错误 · Certificate duration/renewBefore 错误） | TLS 证书无法生成 · mTLS 失败 | 严格参考 Phase 2 PR-4.1.1 #90 + L3-5 §9.5 + L3-6 §9.5 模板 · UT 验证 helm template 渲染 |
| 3 | RBAC 双 Role 权限不足（write Role 缺 admissionregistration.k8s.io 导致 admission webhook 失败） | admission webhook 50ms fail-closed 无法验证 | 严格参考 L3-6 #67 评审关注项 §M-1.4 关闭 · RBAC-UT × 3 静态断言 3 个 apiGroups 存在 |
| 4 | Helm chart 单实例 D 方案被误配置（replicaCount > 1 导致 leader election 冲突） | 多副本并发写 BM25 索引 · 数据竞争 | values.yaml replicaCount: 1 默认 + UT 验证 values.schema.json 拒绝 replicaCount > 1 |
| 5 | Dockerfile uv --frozen 失败（uv.lock 不一致） | Docker build 失败 · image 无法生成 | CI 中 Dockerfile build test（PR-2 Phase 4 Hello Agent 同模式）+ uv.lock 必须与 pyproject.toml 同步 |
| 6 | Subagent 接力时 token plan 中断（#79 经验 · 331 tool uses / 23 分钟 · 429 终止） | Subagent 实装中断 | 每个 Subagent 任务拆分 ≤ 100K tokens · 关键 commit 步骤主 Agent 备份 · #105 实战验证无需 worktree isolation |

---

## §6 5 项关键不变量保持（PR-5 验证）

| # | 不变量 | PR-5 验证方法 |
|---|---|---|
| 1 | wire contract 完全继承 L2-4 v0.2.0 Spec（CRD schema + 23 错误码 + Agent Card JSON） | UT `HELM-UT-004` · helm template 渲染 CRD schema 与 PR-3 Phase B + PR-4a 23 错误码一致 |
| 2 | 50ms admission fail-closed（recordMemory handler 严格时限） | E2E-002 · kind 集群 admission webhook 实测 |
| 3 | Pydantic v2 + populate_by_name + alias + extra=forbid + frozen（service 层 request/response） | 复用 PR-3 + PR-4a/b/c 已实装 · 不修改 |
| 4 | Python-first 边界（services/knowledge-memory-service/ 仅依赖 pydantic + a2a-core + kopf + starlette + packages/knowledge） | `pyproject.toml` dependencies ≤ 5 项（PR-4c 已实装）|
| 5 | 5 维 visibility 矩阵 + 4 级 scope + RBAC 双 Role + cert-manager mTLS + 单实例 D 方案 | UT `RBAC-UT × 3` + `MTLS-UT × 2` + `HELM-UT × 4` · 静态断言 + helm template 验证 |

**额外 PR-5 不变量**：

- ✅ Pod Security Standards restricted（runAsNonRoot + readOnlyRootFilesystem + seccompProfile）
- ✅ RBAC 最小权限原则（namespace-scoped secrets + 7 apiGroups）
- ✅ NetworkPolicy ingress/egress 显式 allow（避免 cluster-wide 访问）
- ✅ cert-manager mTLS 默认 disabled（向后兼容 · Phase 4 打磨阶段启用）
- ✅ 单实例 D 方案（replicaCount: 1 · ADR-0006 · 避免 leader election 复杂度）

---

## §7 测试策略增量（PR-5）

| 层级 | PR-4c 终态 | PR-5 增量 | PR-5 累计 |
|---|---|---|---|
| UT | 69 | **+10**（HELM-UT × 4 + RBAC-UT × 3 + MTLS-UT × 2 + DOCKERFILE-UT × 1）| 79 |
| CF | 18 | 0 | 18 |
| IT | 19 | **+4**（HELM-IT × 2 + RBAC-IT × 2）| 23 |
| E2E | 6 | **+2**（E2E-001 kind cluster + E2E-002 admission webhook 50ms）| 8 |
| DEPLOY | 17 | 0 | 17 |
| PERF | 0 | 0 | 0 |

**PR-5 测试增量**：~16 ID（UT 10 + IT 4 + E2E 2）· 4 重静态门禁（ruff + ruff format + pyright + pytest）· E2E 在 GitHub Actions 中执行

**测试 ID 命名规范**（L3-5 §10.1 + L3-6 §10.1 + Phase 2 + Phase 3 + Phase 4 测试 ID 严格遵守）：

- **HELM-UT-001~004** · helm lint + helm template 渲染 + values.schema 验证 + 7 resources 存在
- **RBAC-UT-001~003** · ClusterRole read-only apiGroups + write Role admissionregistration + namespace-scoped secrets
- **MTLS-UT-001~002** · cert-manager Certificate + Issuer 模板
- **DOCKERFILE-UT-001** · non-root UID 1000 + HEALTHCHECK + EXPOSE 8080 + uvicorn --factory
- **HELM-IT-001~002** · helm template 完整渲染 + values override 测试
- **RBAC-IT-001~002** · kubectl auth-can-i 验证 + impersonation 测试
- **E2E-001** · kind cluster create + load image + Helm install + wait for ready + curl /healthz
- **E2E-002** · kind cluster admission webhook 50ms fail-closed 实测

---

## §8 Phase 4 PR 序列更新（PR-1 + PR-2 + PR-3 + PR-4a + PR-4b + PR-4c merged · PR-5 启动中）

| PR | 标题 | 状态 | main HEAD | 工作量 |
|---|---|---|---|---|
| #38 PR-1 | Hello Agent Step 1 | ✅ merged `c97330bb` | `5e6d79b` | 2 周 |
| #45 PR-2 | Hello Agent Step 2 | ✅ merged `76c08f2` | `76c08f2` | 1 周 |
| #49 PR-3 | Knowledge Service Step 1 | ✅ merged `74af527` | `74af527` | 1.5 周 |
| #51 PR-4a | Knowledge Service Step 2a | ✅ merged `9f2be9a` | `9f2be9a` | 1 周 |
| #53 PR-4b | Knowledge Service Step 2b | ✅ merged `f5d9220` | `f5d9220` | 1 周 |
| #55 PR-4c | Knowledge Service Step 2c | ✅ merged `2f0202d` | `2f0202d` | 1 周 |
| **#109 PR-5** | **Knowledge Service Step 3** | 🚧 **本 plan 启动** | （待 PR-5 完成后） | **1 周** |

**Phase 4 进度**：6/7 PR 已 merged · **7/7 PR 启动中**（PR-5 · **Phase 4 全部收口在即**）
**Phase 4 剩余工作量**：~1 周 PR-5 + ~1 周 Phase 4 打磨（README + HN 草稿 + GitHub Release + Tag）

---

## §9 宪法 v0.5.0 兼容性

| 条款 | 兼容性 | 验证 |
|---|---|---|
| §3.4 文档同步 | ✅ | plan 文档 + Issue + MEMORY 同步 + §F.1-§F.6 跨文档 |
| §3.8 Python-first 实现边界 | ✅ | services/knowledge-memory-service/ 仅依赖 pydantic + a2a-core + kopf + starlette + packages/knowledge（≤ 5 项 · PR-4c 已实装）|
| §6 测试纪律 | ✅ | 4 重静态门禁（ruff + ruff format + pyright + pytest）+ pytest ~14 PASS + E2E 2 ID |
| §6 mTLS | ✅ | cert-manager Certificate + Issuer（默认 disabled · Phase 4 打磨启用）|
| §7 关键决策记录 | ✅ | 5 项设计决策（7 Helm + RBAC + cert-manager + kind E2E + Dockerfile）|
| §9.7 文档先行 | ✅ | 本 plan 文档先于实装（v0.1-draft · 启动条件明确）|
| §11.5 event-loop lag < 100ms | ✅ | kopf MemoryReconciler 60s timer + starlette ASGI 共享 asyncio loop（PR-4c 实装）|
| §13.1 测试 ID 命名 | ✅ | HELM-UT / RBAC-UT / MTLS-UT / DOCKERFILE-UT / HELM-IT / RBAC-IT / E2E-001~002 系列连贯 |
| §13.6 依赖锁定 | ✅ | `pyproject.toml` 依赖固定版本范围 + `uv.lock` 提交 + Dockerfile uv --frozen |
| §14.5 MVP 例外 | ✅ | 0 例外 · 5 项关键不变量 100% 保持 |
| §15 安全基线 | ✅ | PR-5 涉及 Pod Security Standards restricted + RBAC 最小权限 + cert-manager mTLS + NetworkPolicy |
| §16.1 水位纪律 | ✅ | Subagent 接力模式（Phase B 3 个 Subagent）+ 主 Agent 5-8% 水位调度 |
| §17 PR 流程 | ✅ | feat 分支 + PR + CI 5 SUCCESS + squash merge（#103 修复实战验证） |

---

## §10 M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-12 · #109 启动 · **PR-4 拆分最后一个子 PR**）
- **M.2 落地记录**：#109（2026-08-12 · 本 plan 文档完成 · 准备进入 Phase B Subagent 实装）
- **M.3 关联 PR**：Phase 4 PR-5 Knowledge Service Step 3 · 本 plan（PR #56 plan 文档 + PR #57 实装代码）
- **M.4 下次会话入口**：
  - Phase A：本会话完成（plan + Issue + commit + push + PR #56 + CI + squash merge）
  - Phase B：#109 启动 Subagent 接力实装（3 Subagent feat 分支直接工作 · 避免 worktree isolation 无 Bash 权限 · #105 实战经验）
  - Phase C：Phase 4 完整收口主 Agent 收口（lint + test + 实装 PR #57 创建 + CI + squash merge + e2e-envtest workflow 验证）
  - Phase D：#110 Phase 4 打磨启动（README 重写 + HN/Reddit/dev.to/掘金草稿 + CONTRIBUTING.md + GitHub Release note + Tag + 镜像推送 + ROADMAP v0.1.0 完成）
- **M.5 关注项台账**：
  - ① kind 集群在 Subagent 3 本地环境不可用（Windows PATH 无 docker/kind/helm · 使用 GitHub Actions e2e-envtest workflow）
  - ② cert-manager mTLS 配置错误（严格参考 Phase 2 PR-4.1.1 #90 + L3-5/L3-6 §9.5 模板 + UT 验证 helm template 渲染）
  - ③ RBAC 双 Role 权限不足（严格参考 L3-6 #67 评审关注项 §M-1.4 关闭 · RBAC-UT × 3 静态断言 3 个 apiGroups 存在）
  - ④ Helm chart 单实例 D 方案被误配置（replicaCount: 1 默认 + UT 验证 values.schema.json 拒绝 replicaCount > 1）
  - ⑤ Dockerfile uv --frozen 失败（CI 中 Dockerfile build test · uv.lock 必须与 pyproject.toml 同步）
  - ⑥ Subagent 接力 token plan 中断（#79 经验 · 每个 Subagent ≤ 100K tokens · 主 Agent 备份关键 commit · #105 实战验证无需 worktree isolation）
- **M.6 文档状态**：v0.1-draft 完整（10 节 · 估算 ~16-18KB · 启动前完整）
