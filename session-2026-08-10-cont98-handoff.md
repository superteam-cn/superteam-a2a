# #98 完整交接文档（14KB · 11 节 · 2026-08-10）

> **交接说明**：本会话 #98 完整收口 Phase 4 PR-1 Hello Agent Step 1 + 启动 A 选项 P0 全部。下一会话 #99 接力：Phase 4 PR-2 Hello Agent Step 2（Dockerfile + 7 Helm + kind E2E）。本交接文档 self-contained，详细列出会话序列 + 关键决策 + 下一会话入口。

---

## §1 当前完成状态（2026-08-10）

### 1.1 项目里程碑

| 阶段 | 状态 |
|---|---|
| L1 Architecture + Spec | ✅ v0.2.0 |
| L2 Knowledge/Memory Spec | ✅ v0.2.0（4/4） |
| L3 文件级 Spec | ✅ v0.2.0 + v0.2.1（6/6） |
| **ADR-0006 v1.0 Accepted** | ✅ **D 方案 · 单进程 · kopf + starlette 同 event loop** |
| L4 实施层 Phase 1 | ✅ MVP Core 5/5 Step（PR #17-#21）|
| L4 实施层 Phase 2 | ✅ spike 4/4 PR（#22-#25）+ chart 完整化（#27/#89/#90）|
| L4 实施层 Phase 3 | ✅ 4/4 PR（#30 server + #34 K8sBackend + #35 metrics + #36 H-RM/H-QM-E2E）+ #37 文档同步 |
| **L4 实施层 Phase 4** | 🚧 **#98 PR-1 Hello Agent Step 1 open (#38)** · 4 PR 待启动（#99-#102）|

### 1.2 git 状态

| 项 | 值 |
|---|---|
| 本地 main HEAD | `8d94464`（PR #37 merged at 2026-08-10T22:44:xx） |
| **本地 PR-1 分支** | `feat/phase4-pr1-hello-agent-step1` HEAD `77e0218`（session-98 记录） |
| **远程 PR-1 分支** | `b92d1a8` + `77e0218`（pushed · 等项目发起人合并） |
| PR #38 | **OPEN** · CI 5 SUCCESS + 1 SKIPPED · 等 merge |
| 未推送 commit | 无（working tree clean） |
| 5 个 untracked session 文件 | 已 commit 至 feature 分支 |

### 1.3 最近 11 个 commits（按时间倒序）

```
77e0218 docs(session): #98 PR-1 Hello Agent Step 1 完整收口 session 记录
b92d1a8 feat(phase4): PR-1 Hello Agent Step 1 完整实装（5 文件级契约 + 22 测试 ID）
bd2a5ae chore(admin): #98 branch-protection-fix guide + #96 session record
8d94464 feat(phase3): PR-5 Phase 3 文档同步（§F.1-§F.4 跨文档收口） (#37)
5259c14 feat(phase3): PR-4 H-RM/H-QM-E2E-001 真实实装（unskip + port-forward + JSON-RPC round-trip） (#36)
25b857c feat(phase3): PR-3 25 指标 ServiceMonitor 实装 (#35)
8cab684 feat(phase3): PR-2 K8sBackend 完整实装（CustomObjectsApi wrapper） (#34)
870c9f1 chore(deps): bump starlette from 0.52.1 to 1.4.1 (#33)
da4dd5e chore(deps): bump pytest in the dev-dependencies group (#32)
a821085 fix(ci): resolve pre-existing CI failures (5 类根因 · #92 关注项 #13 完整收口) (#31)
... (省略更早 commits · git log --oneline -20)
```

---

## §2 L4 Phase 4 · 5 PR 序列（A 选项 P0 全部）

| PR | 标题 | 工作量 | 起点 | 状态 |
|---|---|---|---|---|
| **#98 PR-1** | **Hello Agent Step 1**（5 Python 文件 + 22 测试 ID） | 2 周 | ✅ 完成 | **🟡 open (#38) 等合并** |
| #99 PR-2 | Hello Agent Step 2（Dockerfile + 7 Helm + kind E2E） | 1 周 | #98 merged | ⏳ |
| #100 PR-3 | Knowledge Service Step 1（8 CRD types + 4 shared） | 1.5 周 | #99 merged | ⏳ |
| #101 PR-4 | Knowledge Service Step 2（12 service + 4 A2A handler + 23 错误码） | 2 周 | #100 merged | ⏳ |
| #102 PR-5 | Knowledge Service Step 3（7 Helm + RBAC） | 1 周 | #101 merged | ⏳ |

**Phase 4 总工作量**：~3700 行 / 5 PR / 6-8 周集中（2h/day）

---

## §3 关键决策历史（#95-#98 · Phase 3 + 4 启动）

### #95 · Phase 3 PR-3 25 指标 ServiceMonitor
- commit `38e05f6` · 15 files / +1434 / -2
- 25 指标命名空间（10 Memory + 15 shared）· ServiceMonitor 全量验证
- 5 项不变量 100% 保持

### #96 · Phase 3 PR-4 H-RM/H-QM-E2E 真实实装
- commit `4d9b923` · 3 files / +1161 / -34 · merged `5259c14`
- 2 E2E unskip + port-forward helper + JSON-RPC round-trip
- **关键发现**：QueryMemoryRequest.scope 是 MemoryScope enum（不是 string）· mem_records.agent_ref 三方各异

### #97 · Phase 3 PR-5 文档同步
- commit `08d3abb` · 4 docs / +171 / -16 · merged `8d94464`
- §F.1-§F.4 跨文档同步（ROADMAP + CONSTITUTION-CHANGELOG + ADR-0006 §M.8 + MEMORY）

### #98 · Phase 4 PR-1 Hello Agent Step 1
- commit `b92d1a8` · 17 files / +1723 / -1 · session `77e0218`
- **关键发现 3 项**：
  1. ⚠️ **a2a-sdk 未安装 + a2a-core stub**：调整 PR-1 不依赖 google-a2a-sdk · 最小化 starlette + Pydantic
  2. 🪟 **Windows fallback `_PsutilProcessCollector`**：prometheus_client 默认 ProcessCollector 仅 Linux · psutil-based fallback 实现
  3. ⏰ **Branch Protection ⑭ mismatch**：4 required_status_checks 不匹配 ci.yml 实际 job name

---

## §4 6 项关键不变量 100% 保持（Phase 4 PR-1 验证）

| # | 不变量 | PR-1 验证 |
|---|---|---|
| 1 | Card-driven 单实例 | `replicaCount: 1` schema enum 强约束推迟到 PR-2（Helm schema.json）|
| 2 | Python-first 边界 | 不依赖 google-a2a-sdk · 仅 starlette + Pydantic + uvicorn + prometheus-client + structlog |
| 3 | observability 4 指标 | 严格 4 项 + Windows fallback · 不混入 L3-5 25 Memory 指标命名空间 |
| 4 | wire contract | Hello Agent 不涉及 12 MEMORY_* · 0 错误码定义 |
| 5 | 单进程 8080 端口 | uvicorn 端口 8080 · 端口独占（无 kopf · 纯 A2A server）|
| 6 | pytest + ruff + pyright 5 重门禁 | ruff check All passed · 173 files formatted · pyright 0 errors |

---

## §5 宪法 v0.5.0 + ADR-0006 D 兼容性

### 5.1 宪法 v0.5.0 兼容项（PR-1 通过）

- **§3.4 Card-driven 单实例**（PR-2 schema enum 强约束）
- **§3.7 Python-first 边界**（不依赖 framework · Hello Agent 独立 service）
- **§3.8 Python-first 边界**（5 文件 Pydantic v2 BaseModel + Protocol + starlette ASGI）
- **§6 SecurityContext**（PR-2 Helm restricted profile）
- **§7 可观测性**（4 Python runtime 指标 + structlog 8 字段 + /healthz /readyz /metrics）
- **§9.7 静态质量**（5 重门禁 ruff + pyright strict + bandit + pip-audit + interrogate）
- **§13.6 上游追踪**（a2a-sdk pin 推迟到 PR-2 之后实装 a2a-core）
- **§14.5 MVP 例外时间窗口**（Phase 4 是 v0.1.0-beta 起步 · 不触发宪法 v0.6.0 升级）
- **§15.5 质量红线**（observability 模块 ≥ 95% 覆盖率 · Hello Agent observability.py 100% 测试覆盖）
- **§16.1 水位纪律**（PR-1 Subagent 接力 143 tool uses / 10 分钟 + 主 Agent 收口 模式）

### 5.2 ADR-0006 v1.0 Accepted D 方案兼容

- ✅ 单进程 · kopf + starlette 同 event loop（Hello Agent **无 kopf** · 纯 A2A server）
- ✅ 60s MemoryReconciler timer 不变（Hello Agent 不涉及）
- ✅ 共享 Deployment（Hello Agent 独立 service · 不与 knowledge-memory-service 共享）
- ✅ 4 纯函数数学不变（Hello Agent 0 业务逻辑）
- ✅ wire contract（12 MEMORY_* 错误码 100% 保持 · Hello Agent 0 错误码定义）

---

## §6 项目结构（PR-1 后）

```
D:/Agents/AgentTeam/superteam-a2a/
├── .github/
│   └── workflows/         # 6 workflows · ci + codeql + dependabot-auto-merge + e2e-envtest + release-drafter + stale
├── docs/
│   ├── admin/
│   │   └── branch-protection-fix.md  # ⑭ 关注项 + web 端 admin 操作步骤
│   ├── adr/               # 6 ADR (0001-0006)
│   ├── phase3/            # Phase 3 PR-1/2/3/4/5 plan 文档
│   │   ├── pr4-h-rm-h-qm-e2e-plan.md
│   │   ├── pr5-doc-sync-plan.md
│   │   └── ...
│   ├── phase4/
│   │   └── pr1-hello-agent-impl-plan.md  # PR-1 plan 8 节
│   ├── reviews/           # 7 L3 评审文件
│   ├── spec/
│   │   ├── L1/ ...
│   │   ├── L2/ ...
│   │   └── L3-file-specs/  # 6 L3 Spec 文件
│   └── design/ ...
├── helm/
│   └── knowledge-memory-service/  # 7 templates + CRD + values.yaml
├── packages/
│   ├── a2a-core/          # L3-2 stub (8 行 __init__.py)
│   ├── adapter-sdk/       # L3-3
│   └── operator/          # L3-1
├── services/
│   ├── knowledge-memory-service/  # Phase 3 4/4 PR 完整实装
│   └── hello-agent/       # 🆕 Phase 4 PR-1 完整实装
│       ├── pyproject.toml
│       ├── README.md
│       └── src/superteam_a2a/hello_agent/
│           ├── __init__.py
│           ├── agent.py
│           ├── card.py
│           ├── observability.py  # 含 _PsutilProcessCollector Windows fallback
│           └── _internals.py
├── tests/
│   ├── unit/
│   │   ├── hello_agent/   # 🆕 11 UT + 4 UT = 15 测试
│   │   ├── knowledge_memory/  # 73 测试
│   │   ├── operator/      # 12 测试
│   │   └── ...
│   ├── conformance/       # 60 RBAC 测试
│   ├── deploy/            # 🆕 test_hello_helm_template.py 7 UT
│   └── e2e/              # 5 E2E (LEADER + LIFECYCLE + H-RM + H-QM)
├── pyproject.toml         # workspace members + sources + dev deps
├── uv.lock
├── README.md
├── ROADMAP.md
├── CONSTITUTION.md
└── CONSTITUTION-CHANGELOG.md
```

---

## §7 下一会话入口（#99 PR-2 Hello Agent Step 2）

### 7.1 #99 PR-2 工作范围

- **工作量**：1 周集中（2h/day）
- **起点**：PR #38 merged（项目发起人合并）
- **内容**：
  1. **Dockerfile**（多阶段 builder + psutil runtime dep + python:3.12-slim + uv workspace install + uvicorn entrypoint）
  2. **7 Helm 模板**：
     - `Chart.yaml`（appVersion: 0.2.0 + kubeVersion: ">=1.29.0-0"）
     - `values.yaml`（replicaCount: 1 + 5 env + mtls.enabled: false）
     - `values.schema.json`（replicaCount.enum: [1] 强约束 + image.tag.pattern: "^v0\\.2\\.0$"）
     - `templates/deployment.yaml`（单实例 + 双探针 + restricted SecurityContext + terminationGracePeriodSeconds: 30 + prometheus.io/scrape: "true"）
     - `templates/configmap.yaml`（5 env 注入）
     - `templates/serviceaccount.yaml`（automountServiceAccountToken: false）
     - `templates/networkpolicy.yaml`（ingress 同 namespace + egress DNS 53 + 同 namespace 8080）
     - `templates/servicemonitor.yaml`（interval: 30s + scrapeTimeout: 10s + honorLabels: true）
  3. **kind cluster E2E**（HELLO-E2E-001~003 · A2A sendMessage → pong 端到端）
     - 复用 Phase 2 e2e-envtest.yml workflow（不动）
     - 测试在 kind cluster 内 `kubectl port-forward svc/...` + POST `/a2a/sendMessage`

### 7.2 #99 PR-2 实施顺序

| 阶段 | 内容 | 时间 |
|---|---|---|
| A · 主 Agent 分支 + plan | `git checkout -b feat/phase4-pr2-hello-agent-step2` · 写 `docs/phase4/pr2-hello-agent-helm-plan.md` | 30 min |
| B · Subagent 接力实装 | Dockerfile + 7 Helm 模板 + kind E2E + 12 DEPLOY 测试 ID | 60-90 min |
| C · 主 Agent 收口 | lint + pytest + pyright + push + PR #39 + CI 验证 + MEMORY 维护 | 30 min |

### 7.3 #99 PR-2 关键约束

1. **replicaCount: 1 强约束**（values.schema.json `enum: [1]`）
2. **psutil runtime dep**（Dockerfile `pip install` 阶段必须显式添加）
3. **5 env 注入**（HELLO_AGENT_NAME + VERSION + DESCRIPTION + URL + LOG_LEVEL）
4. **port 8080 共享**（livenessProbe `/healthz` + readinessProbe `/readyz` + scrape `/metrics`）
5. **SecurityContext restricted profile**（runAsNonRoot + readOnlyRootFilesystem + allowPrivilegeEscalation: false + seccompProfile: RuntimeDefault）

### 7.4 #99 PR-2 验收清单

- ✅ Dockerfile + 7 Helm 模板实装（15 文件级契约 · ~280 行）
- ✅ HELLO-DOCKER-001 + HELLO-HELM-001~007 + HELLO-DEPLOY-001~003 = 12 测试 ID PASS
- ✅ kind cluster E2E（HELLO-E2E-001~003）PASS（label trigger e2e-envtest workflow）
- ✅ 263 + 12 = 275 PASS
- ✅ ruff + pyright 全绿
- ✅ 5 项不变量 100% 保持

---

## §8 紧急联系 / 注意事项

### 8.1 ⚠️ ⑭ Branch Protection 关注项 · 必做

**状态**：main-protection Ruleset required_status_checks 4 项（`ci/lint ci/test/test ci`）与 ci.yml 实际 job name `Lint / Type-check / Test (Python 3.12)` **不匹配** · CI 失败未阻断 merge · 当前 PR 都由项目发起人手动合并。

**操作**：项目发起人访问 https://github.com/superteam-cn/superteam-a2a/rules/20232954 修改 required status checks：
- 删除：ci / lint ci / test / test ci
- 新增：**`Lint / Type-check / Test (Python 3.12)`**

**GitHub REST API 限制**：不允许 CLI 修改 required_status_checks contexts · 唯一可行路径是 web 端 admin UI。

**完整操作指南**：`docs/admin/branch-protection-fix.md`

### 8.2 ⚠️ a2a-core stub · 后续 PR 范围

**状态**：`packages/a2a-core/src/superteam_a2a/a2a/__init__.py` 仅 8 行 + `__version__` · a2a-sdk 完全未安装 · L3-2 Spec 实装推迟到 v0.1.0 GA 之后。

**PR-1 调整**：不依赖 google-a2a-sdk · 最小化 starlette + Pydantic + uvicorn 实现 · 与 `services/knowledge-memory-service/` 同架构。

**后续 PR 范围**：v0.1.0 GA 后单独 PR 实装 a2a-core（AgentExecutor Protocol + AgentCard Pydantic + 4 A2A methods + sendMessage handler）。

### 8.3 ⚠️ Windows 测试环境

**状态**：prometheus_client 默认 ProcessCollector 仅 Linux /proc 可用 · Windows 测试需要 psutil fallback（`_PsutilProcessCollector`）。

**PR-1 实装**：psutil 加为 dev dep（不污染 runtime）· Windows 上自动 unregister 默认 + 注册 psutil 版。

**生产环境**：Linux 镜像走默认 ProcessCollector 路径 · psutil **不是** runtime 依赖 · 但 PR-2 Dockerfile 需要在 runtime 阶段显式 `pip install psutil`（如果需要 Windows 兼容）。

### 8.4 ⚠️ psutil 依赖决策

**PR-1 现状**：psutil 仅 dev dep（`[dependency-groups] dev`）· 测试环境可用 · 生产 Linux 镜像不需要。

**PR-2 Dockerfile 实装建议**：
- 多阶段 builder：builder 阶段 `pip install .[dev]`（含 psutil）
- runtime 阶段：仅 `pip install .`（不含 psutil，减小镜像体积）
- Linux 生产环境走默认 ProcessCollector 路径
- Windows 测试 / 容器环境需要 psutil fallback

---

## §9 关键引用

### 9.1 Spec 文档

- **L3-4 Hello Agent Spec v0.2.0**：`docs/spec/L3-file-specs/L3-hello-agent.md`（1579 行 · 5 文件级契约 + 7 Helm + 25 ID 测试 + 30 验收点）
- **L3-4 评审**：`docs/reviews/l3-4-hello-agent-spec-review.md`（464 行 · 10 维度全 PASS · 3 关注项 + 4 建议项）
- **L3-5 Knowledge Service Spec v0.2.0**：`docs/spec/L3-file-specs/L3-knowledge-service.md`（2613 行 · 30 文件级契约 + 23 错误码 + 60 ID 测试）
- **L3-5 评审**：`docs/reviews/l3-5-knowledge-service-spec-review.md`（552 行 · 10 维度全 PASS · 4 关注项 + 4 建议项）
- **L2-4 Knowledge/Memory Spec v0.2.0**：`docs/spec/L2-module-specs/L2-knowledge-memory.md`（4152 行 · 12 MEMORY_* 错误码权威名）

### 9.2 ADR + Constitution

- **ADR-0006 v1.0 Accepted**：`docs/adr/0006-memory-transport.md`（D 方案 · 单进程 · kopf + starlette 同 event loop）
- **Constitution v0.5.0**：`CONSTITUTION.md`（§3.4/§6/§7/§9.7/§13.1/§14.5/§15.5/§16.1）
- **ROADMAP v0.2.0**：`ROADMAP.md`（Phase 3 4/4 merged + Phase 4 启动就绪）

### 9.3 Phase 3-4 Plan + Session

- **Phase 3 plan v1.0 推荐**：`docs/phase3/l4-phase3-plan.md`（4 PR 候选 + 5 关注项）
- **Phase 4 PR-1 plan v0.1-draft**：`docs/phase4/pr1-hello-agent-impl-plan.md`（8 节 + M.1-M.6）
- **本次会话 session**：`session-2026-08-10-cont98-pr1-hello-agent.md`
- **本次交接**：`session-2026-08-10-cont98-handoff.md`（本文件）

---

## §10 宪法纪律（§16.1 实际水位判断）

### 10.1 本次会话 #98 应用 §16.1

- **会话 #98 总工作量**：~3 小时（用户选择 A 选项 P0 全部）
- **水位判断**：
  - 主 Agent 直接执行：labels 创建 + branch-protection-fix 文档 + Subagent 调研/实装调度 + commit + push + PR
  - Subagent 接力：L3-4 + L3-5 Spec 调研 + Hello Agent 完整实装（143 tool uses / 10 min）
- **主 Agent 水位**：5-8%（实测安全）
- **Subagent 接力必要性**：Hello Agent 17 文件 / +1723 行属中等工作量 · Subagent 隔离降低主 Agent token 风险

### 10.2 后续会话建议

- **#99 PR-2（1 周集中）**：Subagent 接力实装 Dockerfile + 7 Helm + 12 DEPLOY 测试（预计 80-120 tool uses / 15-20 min）
- **#100-#102（5 周集中）**：Knowledge Service 30 文件级契约 + 60 测试 ID · 建议分 2-3 个 Subagent 接力
- **宪法纪律**：每次会话主 Agent 水位严格 ≤ 15% · 超过立即 Subagent 接力

---

## §11 ⚠️ 11 项注意事项

### 严格禁止 ❌

1. ❌ 修改 `services/knowledge-memory-service/`（Phase 3 4/4 PR 已完整收口 · 不再触动）
2. ❌ 修改 `packages/a2a-core/`（stub 状态 · 推迟到 v1.0 GA 后）
3. ❌ 修改 `helm/knowledge-memory-service/`（Phase 3 4/4 PR 已完整收口）
4. ❌ 修改 `.github/workflows/ci.yml`（PR #31 #32 #33 修复后 · 已稳定）
5. ❌ 直接使用 `python` 而非 `python -m uv run`（uv workspace 必需 · direct python 找不到模块路径）
6. ❌ 跳过 ruff check / format / pyright 任一项（5 重门禁）

### 强制要求 ✅

7. ✅ 所有 Python 代码用 `from __future__ import annotations` 开头
8. ✅ 所有 service 顶层导出 `create_app` 或类似 factory function（starlette ASGI 模式）
9. ✅ 所有测试用 `starlette.testclient.TestClient` 而非 uvicorn 启动（节省时间 · 避免端口冲突）
10. ✅ 所有 metrics 命名空间独立（Hello Agent 4 指标 ≠ Memory 25 指标）
11. ✅ 所有 PR commit message 含 `feat(phase4):` / `feat(phase3):` 等 conventional commits 前缀

### MEMORY.md 维护

- 头部状态行 ≤ 2 行（KB 上限 · 已临界 252-260 lines / 39.6KB）
- session 文件 ≤ 200 行 · 详情放 session 文件
- 每次 commit 后立即更新 MEMORY.md 头部状态行（PR 编号 + main HEAD + 测试数 + 关键不变量）

---

> **交接完成** · 2026-08-10 · Phase 4 PR-1 完整收口 · 等项目发起人合并 PR #38 · #99 PR-2 Hello Agent Step 2 入口已就绪