# Phase 4 PR-2 Plan v0.1-draft · Hello Agent Step 2（Dockerfile + 7 Helm 模板 + kind E2E）

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.1-draft**（2026-08-11 · #101 启动）|
| 上游 | #98 PR-1 Hello Agent Step 1 完整收口（PR #38 merged `c97330bb` · 263/263 PASS · 5 SUCCESS + 1 SKIPPED CI）+ #99 ⑭ BP fix（Issue #42 closed）+ #100 Dependabot PR 修复（PR #39 #40 #41 merged）+ #101 ⑯ bypass actor fix（Issue #43 closed）|
| 下游 | Phase 4 PR-3~PR-5（Knowledge Service Step 1/2/3）+ v0.5+ 演进 |
| 关联 PR | Phase 4 PR-2 Hello Agent Step 2 · 本 plan |
| main HEAD | `5e6d79b`（含 commit `052681d` workflow + commit `5e6d79b` bypass-actor-fix.md）|
| 启动条件 | ✅ 全部满足（BP 严格生效 + Dependabot 自动化 + Issue #43 closed + ⑯ 解决）|

---

## §1 目标与边界

**目标**：将 Hello Agent（Phase 4 PR-1 已实装的 5 Python 文件）打包为 **容器镜像 + Helm chart**，并在 **kind 集群 E2E 验证**。这是 Hello Agent **"可部署性"** 的关键里程碑。

**PR-2 实装清单**（L3-4 v0.2.0 §5 + §9 + PR-1 plan §1）：

| 项 | 文件数 | 关键依赖 |
|---|---|---|
| **Dockerfile** | 1 | multi-stage · python:3.12-slim · uv · non-root · HEALTHCHECK · EXPOSE 8080 |
| **Chart.yaml** | 1 | apiVersion v2 + version 0.1.0 + appVersion 0.1.0 + kubeVersion >=1.25 |
| **values.yaml** | 1 | replicaCount=1 + image + service + resources + serviceAccount + prometheus |
| **values.schema.json** | 1 | JSON Schema 强约束（replicaCount enum [1] + image.repository pattern + port enum [8080]）|
| **templates/deployment.yaml** | 1 | 单容器 + 8080 + 双探针 + volumeMounts + serviceAccountName + restricted SecurityContext |
| **templates/configmap.yaml** | 1 | LOG_LEVEL=INFO + OTEL_EXPORTER_OTLP_ENDPOINT 留空 + PYTHONUNBUFFERED=1 |
| **templates/serviceaccount.yaml** | 1 | 最小权限 + automountServiceAccountToken=false |
| **templates/networkpolicy.yaml** | 1 | ingress: Prometheus + namespace selectors · egress: DNS + OTLP |
| **templates/servicemonitor.yaml** | 1 | 4 指标 scrape + interval 30s + honorLabels true |
| **kind E2E**（HELLO-E2E-001~003）| 3 测试 ID | kind create cluster + helm install + kubectl port-forward + JSON-RPC round-trip |

**PR-2 增量测试 ID**（L3-4 §10）：

- UT 增量：**0**（PR-1 已有 22 ID）
- DEPLOY 增量：**+12**（HELLO-DOCKER-001 + HELLO-HELM-001~007 + HELLO-DEPLOY-001~003）
- E2E 增量：**+3**（HELLO-E2E-001~003）

**PR-2 测试增量合计**：~15 ID（**DEPLOY 12 + E2E 3**）· 6 层级金字塔镜像规则 + 4 重静态门禁（ruff check + ruff format + pyright + helm lint）。

**不在范围**（明确剔除 · 推迟到 PR-3+）：

- ❌ 修改 `services/hello-agent/` 业务代码（PR-1 已实装 · 5 项关键不变量 100% 保持）
- ❌ 修改 `packages/a2a-core`（stub 保持 · 实装推迟到 PR-3+）
- ❌ Knowledge Service Step 1/2/3 实装（PR-3~PR-5 范围）
- ❌ 修改 `services/knowledge-memory-service/`（Phase 2 PR-1~PR-5 已实装）
- ❌ Framework adapter 接入（v0.5+ 范围）
- ❌ 修改 L3-4 Spec（v0.2.0 已评审通过）

---

## §2 设计决策（5 项关键）

### §2.1 Dockerfile multi-stage

**架构**：2-stage build

| Stage | Base | 关键命令 |
|---|---|---|
| builder | `python:3.12-slim` | `uv sync --frozen --no-dev` 安装依赖到 `.venv` |
| runtime | `python:3.12-slim` | 复制 `.venv` + 源码 + non-root user + ENTRYPOINT |

**理由**：
- builder stage 隔离编译工具（uv 等）
- runtime stage 仅含 `.venv` + 源码 + 必要 system libs
- 镜像体积最小化（目标 < 200MB）
- multi-stage pattern 是 k8s 容器化最佳实践

### §2.2 Helm chart `replicaCount: 1` schema enum 强约束

**values.yaml**:

```yaml
replicaCount: 1

image:
  repository: ghcr.io/superteam-cn/superteam-a2a-hello-agent
  tag: "0.1.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8080

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi

serviceAccount:
  create: true
  name: hello-agent
  automountServiceAccountToken: false

prometheus:
  enabled: true
  serviceMonitor:
    interval: 30s
```

**values.schema.json 强约束**（PR-1 plan §2.3 + L3-4 §5 锁定）：

```json
{
  "properties": {
    "replicaCount": { "enum": [1] },
    "image": {
      "properties": {
        "repository": { "pattern": "^ghcr\\.io/superteam-cn/superteam-a2a-hello-agent$" },
        "tag": { "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" }
      }
    },
    "service": {
      "properties": {
        "port": { "enum": [8080] }
      }
    }
  }
}
```

**理由**：
- `replicaCount enum [1]` 强约束 = Card-driven 单实例（5 项关键不变量 #1）
- 防止误部署多副本导致 `_task_store` race（PR-1 plan §5 风险 #2）
- `port enum [8080]` 强约束 = 单进程 8080 端口（5 项关键不变量 #5）

### §2.3 restricted SecurityContext

`deployment.yaml` SecurityContext：

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
```

**理由**：
- Pod Security Standards `restricted` profile（k8s 官方推荐基线）
- 防止容器逃逸 + 提权攻击
- 与 networkpolicy + serviceaccount 最小权限组合形成 defense-in-depth

### §2.4 双探针 + ServiceMonitor

**deployment.yaml** 双探针：

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /readyz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

**servicemonitor.yaml** 4 指标 scrape：

```yaml
spec:
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
      honorLabels: true
  selector:
    matchLabels:
      app.kubernetes.io/name: hello-agent
```

**理由**：
- 双探针 = K8s 标准 lifecycle（liveness 重启 + readiness 流量）
- ServiceMonitor = Prometheus Operator scrape 4 Python runtime 指标
- `honorLabels: true` = 保留 prometheus_client 默认 label，不被 ServiceMonitor 覆盖（避免命名漂移）

### §2.5 kind cluster E2E

**测试流程**（HELLO-E2E-001~003）：

```
1. kind create cluster --name hello-agent-e2e
2. helm install hello-agent ./helm/superteam-a2a-hello-agent
3. kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=hello-agent --timeout=60s
4. kubectl port-forward svc/hello-agent 8080:8080 &
5. curl http://localhost:8080/.well-known/agent.json  → 200 + AgentCard
6. curl -X POST http://localhost:8080/a2a/sendMessage -d '{"message": {...}}'  → 200 + Task(artifacts: "pong")
7. curl http://localhost:8080/healthz  → 200
8. curl http://localhost:8080/readyz  → 200
9. curl http://localhost:8080/metrics  → 200 + 4 metrics
10. kind delete cluster --name hello-agent-e2e
```

**理由**：
- kind = k8s-in-docker（无需真实集群）
- 验证完整链路（构建 → 推送 → 部署 → 服务暴露 → JSON-RPC round-trip）
- 3 ID 测试对应 3 关键步骤（install / port-forward / round-trip）

---

## §3 实施步骤（4 阶段 · 接力模式 · 宪法 §16.1）

### 阶段 A · 主 Agent 起草 plan（本会话 · 进行中）

- ✅ 本 plan 文档（`docs/phase4/pr2-hello-agent-helm-plan.md` · ~10-12KB · v0.1-draft）
- ✅ Issue #44 创建跟踪
- ✅ commit + push plan 文档
- 🚧 本阶段进行中

### 阶段 B · Subagent 隔离实装（估算 200K-400K tokens · ~30-60 分钟）

**Subagent 任务清单**：

| Subagent | 任务 | 估算 tokens | 隔离方式 |
|---|---|---|---|
| Subagent 1 | Dockerfile 实装 + HELLO-DOCKER-001 测试 | 30K-50K | worktree 隔离 |
| Subagent 2 | 7 Helm 模板实装 + HELLO-HELM-001~007 + HELLO-DEPLOY-001~003 测试 | 80K-120K | worktree 隔离 |
| Subagent 3 | kind E2E 实装 + HELLO-E2E-001~003 测试 | 50K-80K | worktree 隔离 |
| Subagent 4（可选）| 文档同步（§F.1-§F.6） | 30K-50K | worktree 隔离 |

**Subagent 接力原则**（§16.1 + #79 经验）：
- 主 Agent 仅调度 + 验证 + 收口
- 每个 Subagent 在 **独立 worktree** 中实装
- Subagent 完成后回到主分支 → 主 Agent 合并 + 验证

### 阶段 C · 主 Agent 收口（10-20 分钟）

1. fast-forward main（所有 Subagent commit 合并）
2. 验证：ruff check + ruff format + pyright + helm lint + yamllint
3. 验证：pytest 全套（unit + conformance + deploy = ~275 PASS）
4. 验证：kind cluster E2E（HELLO-E2E-001~003）
5. `git push` + `gh pr create` → PR #44
6. 等 CI 5 SUCCESS（BP 严格生效 · 项目发起人手动合并或 Dependabot bypass）
7. MEMORY.md 头部更新 + session 文件创建

### 阶段 D · MEMORY 维护（5-8% 水位 · 10 分钟）

1. 创建 `session-2026-08-XX-cont102-pr2-helm.md`
2. MEMORY.md 头部状态行更新（PR #44 merged · main HEAD 推进）
3. 跨文档同步（§F.1-§F.6）：
   - `ROADMAP.md` · 5/5 PR 完成 → 6/6 PR（新增 PR-2）
   - `README.md` · Hello Agent 部分更新（容器化 + Helm 部署）
   - `CONSTITUTION-CHANGELOG.md` · v0.5.0 → v0.5.1（如有微同步）
   - `L4-Phase4 plan` · 更新 PR-2 完成状态
   - `services/hello-agent/README.md` · 新增 Docker + Helm 部署章节
   - `docs/admin/helm-values-schema-guide.md` · 新增指南（JSON Schema 强约束最佳实践）
4. Issue #44 close + 项目发起人合并确认

---

## §4 PR-2 验收清单（10 项）

| # | 项 | 验证方法 |
|---|---|---|
| 1 | Dockerfile 创建（multi-stage + python:3.12-slim + uv + non-root + HEALTHCHECK + EXPOSE 8080）| `docker build` + `docker run` 验证 + HELLO-DOCKER-001 测试 |
| 2 | Chart.yaml + values.yaml + values.schema.json 创建（API v2 + replicaCount enum [1] + port enum [8080]）| `helm lint` + `helm template` 验证 + HELLO-HELM-001~002 测试 |
| 3 | 5 Helm 模板创建（deployment + configmap + serviceaccount + networkpolicy + servicemonitor）| `helm template` 验证 + HELLO-HELM-003~007 + HELLO-DEPLOY-001~003 测试 |
| 4 | kind cluster E2E 完整通过（HELLO-E2E-001~003）| kind create + helm install + port-forward + JSON-RPC round-trip |
| 5 | 镜像大小 < 200MB | `docker images` |
| 6 | uv sync `--frozen --no-dev` 成功 | Dockerfile build log |
| 7 | ruff check All passed + ruff format OK + pyright 0 errors | GitHub Actions CI |
| 8 | pytest ~275 PASS（基线 263 + PR-2 新增 ~12 DEPLOY） | GitHub Actions CI |
| 9 | helm lint + yamllint 0 errors | GitHub Actions CI |
| 10 | 5 项关键不变量 100% 保持（Card-driven + Python-first + observability + wire contract + 8080 端口）| 验证脚本 + PR description |

---

## §5 风险与缓解（7 项）

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| 1 | Dockerfile build 时间过长（uv sync + python install） | CI 5-10 min 延迟 | multi-stage 缓存 .venv + uv `--frozen` + dependabot 镜像 base 更新 |
| 2 | kind cluster 启动慢（~30s） | E2E 总时长 2-3 min | kind `--retain` 复用 + 并行测试 + GH Actions cache kind image |
| 3 | Helm values.schema.json 误拒绝合法值 | 部署失败 | schema 严格但有穷举（enum 限定）+ 测试覆盖 |
| 4 | networkpolicy 误阻断 ServiceMonitor scrape | Prometheus 无法 scrape 指标 | egress: Prometheus namespace selector 留空（允许所有 egress）+ 测试验证 |
| 5 | ServiceMonitor `honorLabels: true` 与 prometheus_client label 冲突 | 指标丢失 | 验证 prometheus_client 默认 label 无冲突 + 测试 scrape 4 指标 |
| 6 | kind cluster 内存不足（GH Actions runner 7GB）| E2E OOM killed | `kind create --config kind-config.yaml` 限制 resources + 复用 single node |
| 7 | uv workspace 跨包依赖（superteam-a2a-a2a-core）build 失败 | Dockerfile 构建失败 | `uv sync --all-packages --all-extras` 在 builder stage 显式执行 |

---

## §6 5 项关键不变量保持（PR-2 验证）

| # | 不变量 | PR-2 验证方法 |
|---|---|---|
| 1 | Card-driven 单实例 | `values.schema.json: replicaCount.enum: [1]` 强约束 · helm template 验证 |
| 2 | Python-first 边界 | Dockerfile base image = `python:3.12-slim` · 0 系统级依赖（除 psutil）|
| 3 | observability 4 指标 | servicemonitor.yaml scrape 4 项（`python_gc_objects_collected_total` / `process_cpu_seconds_total` / `process_resident_memory_bytes` / `process_open_fds`）+ 不混入 25 Memory 指标 |
| 4 | wire contract（12 MEMORY_*）| Hello Agent 不涉及 MEMORY_* · 0 错误码定义 · L3-4 v0.2.0 §9 锁定 |
| 5 | 单进程 8080 端口 | Dockerfile EXPOSE 8080 + deployment.yaml containerPort 8080 + service port 8080 + values.schema.json port enum [8080] 强约束 |

**额外 PR-2 不变量**（Helm chart 层级）：

- ✅ `restricted` SecurityContext（runAsNonRoot + readOnlyRootFilesystem + drop ALL capabilities）
- ✅ `automountServiceAccountToken: false`（最小权限）
- ✅ NetworkPolicy 最小化（ingress Prometheus + egress DNS）
- ✅ ServiceMonitor `honorLabels: true`（避免命名漂移）

---

## §7 测试策略增量（PR-2）

| 层级 | PR-1 终态 | PR-2 增量 | PR-2 累计 |
|---|---|---|---|
| UT | 22 | **0** | 22 |
| CF | 18 | 0 | 18 |
| IT | 24 | 0 | 24 |
| E2E | 3（LEADER/LIFECYCLE/H-RM/H-QM/HELLO）| **+3**（HELLO-E2E-001~003）| 6 |
| DEPLOY | 5 | **+12**（HELLO-DOCKER-001 + HELLO-HELM-001~007 + HELLO-DEPLOY-001~003）| 17 |
| PERF | 0 | 0 | 0 |

**PR-2 测试增量**：~15 ID（DEPLOY 12 + E2E 3）· 6 层级金字塔镜像规则 / 4 重静态门禁（ruff + ruff format + pyright + helm lint）· 覆盖率 ≥ 90%

**HELLO-DOCKER-001** · Dockerfile lint + build 验证
**HELLO-HELM-001** · `helm lint` 通过
**HELLO-HELM-002** · `helm template` 渲染所有 7 模板成功
**HELLO-HELM-003** · `values.schema.json` 强约束验证（replicaCount=2 应失败）
**HELLO-HELM-004** · `values.schema.json` 强约束验证（port=9090 应失败）
**HELLO-HELM-005** · deployment.yaml SecurityContext = `restricted` profile
**HELLO-HELM-006** · configmap.yaml 3 env vars 注入（LOG_LEVEL + OTEL + PYTHONUNBUFFERED）
**HELLO-HELM-007** · servicemonitor.yaml 4 指标 endpoint + honorLabels true
**HELLO-DEPLOY-001** · 单实例 deployment 创建成功
**HELLO-DEPLOY-002** · service ClusterIP + port 8080 暴露
**HELLO-DEPLOY-003** · serviceaccount automountServiceAccountToken=false
**HELLO-E2E-001** · kind cluster create + helm install 成功 + pod ready
**HELLO-E2E-002** · kubectl port-forward + curl AgentCard + curl sendMessage 200
**HELLO-E2E-003** · 5 端点全部 200（agent.json + sendMessage + healthz + readyz + metrics）

---

## §8 Phase 4 PR 序列更新（PR-1 已 merged · PR-2 启动中）

| PR | 标题 | 状态 | main HEAD | 工作量 |
|---|---|---|---|---|
| **#98 PR-1** | **Hello Agent Step 1**（5 Python + 22 测试） | ✅ merged `c97330bb` | `5e6d79b`（含 bypass-actor-fix） | 2 周（已完成）|
| **#99 PR-2** | **Hello Agent Step 2**（Dockerfile + 7 Helm + kind E2E） | 🚧 **本 plan 启动** | （待 PR-2 完成后） | 1 周 |
| #102 PR-3 | Knowledge Service Step 1（8 CRD types + 4 shared + 测试） | 📋 待启动 | — | 1.5 周 |
| #103 PR-4 | Knowledge Service Step 2（12 service + 4 A2A handler + 23 错误码） | 📋 待启动 | — | 2 周 |
| #104 PR-5 | Knowledge Service Step 3（7 Helm + RBAC + kind E2E） | 📋 待启动 | — | 1 周 |

**Phase 4 进度**：1/5 PR 已 merged · **2/5 PR 启动中**（本 plan）
**Phase 4 剩余工作量**：~4-5 周集中（2h/day）

---

## §9 宪法 v0.5.0 兼容性

| 条款 | 兼容性 | 验证 |
|---|---|---|
| §3.4 文档同步 | ✅ | plan 文档 + Issue #44 + MEMORY 同步 + §F.1-§F.6 跨文档 |
| §6 测试纪律 | ✅ | 4 重静态门禁（ruff + ruff format + pyright + helm lint）+ pytest ~275 PASS |
| §7 关键决策记录 | ✅ | 5 项设计决策（multi-stage + schema enum + restricted + 双探针 + kind E2E）|
| §9.7 文档先行 | ✅ | 本 plan 文档先于实装（v0.1-draft · 启动条件明确）|
| §13.1 测试 ID 命名 | ✅ | HELLO-DOCKER/HELM/DEPLOY/E2E 系列连贯 · 不与 L3-5/L3-6 TEST-MEM-* 重名 |
| §13.6 依赖锁定 | ✅ | Dockerfile `uv sync --frozen` + uv.lock 提交 |
| §14.5 MVP 例外 | ✅ | 0 例外 · 5 项关键不变量 100% 保持 |
| §15 安全基线 | ✅ | restricted SecurityContext + automountServiceAccountToken=false + NetworkPolicy |
| §16.1 水位纪律 | ✅ | Subagent 接力模式（Phase B 4 个 Subagent 隔离 worktree）+ 主 Agent 5-8% 水位调度 |

---

## §10 M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-11 · #101 启动）
- **M.2 落地记录**：#101（2026-08-11 · Issue #44 创建 + 本 plan 文档完成 · 准备进入 Phase B Subagent 实装）
- **M.3 关联 PR**：Phase 4 PR-2 Hello Agent Step 2 · 本 plan（PR #44 待创建）
- **M.4 下次会话入口**：
  - Phase A：本会话完成（plan + Issue #44 + commit + push）
  - Phase B：#102 启动 Subagent 接力实装（4 Subagent worktree 隔离）
  - Phase C：主 Agent 收口（lint + test + PR 创建）
  - Phase D：MEMORY 维护（#102 session + 跨文档 §F.1-§F.6）
- **M.5 关注项台账**：
  - ① Dockerfile build 时间（multi-stage + uv `--frozen` 缓解）
  - ② kind cluster 内存（限制 resources + 复用 single node）
  - ③ uv workspace 跨包依赖（`--all-packages --all-extras` 显式执行）
  - ④ ⑯ bypass actor fix（#101 已解决 · Dependabot PR 自动化）
  - ⑤ ⑭ BP mismatch（#99 已解决 · BP 严格生效）
- **M.6 文档状态**：v0.1-draft 完整（10 节 · 估算 ~10-12KB · 启动前完整）
