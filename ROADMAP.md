# superteam-a2a — Roadmap

> 📅 Last updated: **2026-08-16**（**Phase 4 PR-5 Knowledge Service Step 3 完整实装 #61 squash merged @ `eb4a7be` · 466/466 PASS · 1 主 Agent 起草（Phase A · 4 files）+ 1 主 Agent 测试实装（Phase B · 16 测试 ID）· 4 CI SUCCESS · **Phase 4 8/8 PR merged 全部收口** · v0.1.0 准备就绪**）（同步至 ADR-0001 / 0004 / 0005 / **0006 v1.0 Accepted (D 方案 · 同进程 · 合并 L3-5 + L3-6)** + **宪法 v0.6.0**（§17 SOLID + 合成复用 6 项 · 2026-08-13 #112）+ L1 v0.2.0 + L2-1/L2-2/L2-3/L2-4 v0.2.0 Python 通过 + **L3-1 Operator Core v0.2.0 #56** + **L3-2 A2A Core v0.2.0 #54** + **L3-3 Adapter SDK v0.2.0 #58** + **L3-4 Hello Agent v0.2.0 #61** + **L3-5 Knowledge Service v0.2.0 + v0.2.1 #63.5/#71** + **L3-6 Memory backend v0.2.0 + v0.2.1 #67/#71**；**L3 阶段 6/6 全部完成** · **Phase 4 8/8 PR merged**（PR-1 + PR-2 + PR-3 + PR-4a + PR-4a Phase B + PR-4b + PR-4c + PR-5））
> 👤 Maintainer: [@CoderZhangfujiang](https://github.com/CoderZhangfujiang)
> 🎯 Goal: ≥3,000 GitHub stars within 18 months (by **2027-09**)

This roadmap is a living document, kept in sync with the authoritative [ADR-0001 scope statement](./docs/adr/0001-v1-scope-statement.md) and [ADR-0004 timeline extension](./docs/adr/0004-v01-scope-extension-knowledge-and-memory.md). Tasks and timelines reflect the maintainer's ~2 hours/day capacity.

---

## 版本演进路径

| 版本 | 预计交付 | 关键承诺 | 状态 |
|---|---|---|---|
| **v0.1.0** | **2027-01-20**（20 周） | 5 能力 + 6 CRD + Hello Agent + Knowledge + Memory | 🚧 进行中 |
| **v0.5.0** | TBD | + LangChain + AutoGen + SSE + Conversation CRD | ⏳ 待启动 |
| **v1.0.0** | 预计 2027-Q3 | + 6 framework adapters + Dashboard + 完整 conformance | ⏳ 待启动 |

权威范围定义：[ADR-0001](./docs/adr/0001-v1-scope-statement.md) · 范围重定依据：[ADR-0004](./docs/adr/0004-v01-scope-extension-knowledge-and-memory.md)

---

## Phase 0 — Foundation（Week 0）✅ 已完成

- [x] 项目名锁定：`superteam-a2a`（无 GitHub / PyPI / npm 冲突）
- [x] GitHub 用户名锁定：`CoderZhangfujiang`
- [x] 仓库骨架（README / LICENSE / CONTRIBUTING / CODE_OF_CONDUCT / SECURITY / .gitignore）
- [x] Issue 模板（api-design / bug_report / feature_request）
- [x] **宪法 v0.1.0 → v0.2.0**（15 articles + 3 appendices + **2.9 记忆可追溯**）
- [x] L1 Architecture / L1 Spec / L1 Review 评审通过
- [x] ADR-0004（v0.1 范围重定：12 周 → 20 周）
- [x] ADR-0001（v1 版本范围声明：v0.1 / v0.5 / v1.0 + 永久 out-of-scope + 5 类 28 项验收门禁）

---

## Phase 1 — MVP Core（第 1-10 周）🚧 进行中

> 对应发版 tag：**`v0.1.0-alpha`**

### 设计层（先于实施）

- [x] ADR-0002（知识管理能力设计）✅ 2026-07-23
- [x] ADR-0003（Memory 持久化记忆设计）✅ 2026-07-23
- [x] L1 Architecture 更新（+3 CRD + 4 method + MemoryReconciler）✅ 2026-07-23 → v0.2.0 ✅ 2026-07-24（Python-first 迁移）
- [x] L1 Spec 更新（CRD 字段 + 错误码 + 状态机）✅ 2026-07-23 → v0.2.0 ✅ 2026-07-24（Python-first 迁移）
- [x] L2 模块设计（Operator / A2A Core / Adapter SDK / Knowledge Service 4 个 L2 文档）：
  - L2-1 A2A Protocol ✅ v0.1.0 Go baseline（2026-07-23）→ ✅ v0.2.0 Python（2026-07-24）
  - L2-2 Operator Core ✅ v0.1.0 Go baseline（2026-07-24，已归档）→ ✅ v0.2.0 Python（2026-07-25 #33 评审通过）
  - L2-3 Adapter ✅ v0.1.0 Go baseline（2026-07-24）→ ✅ v0.2.0 Python（2026-07-26 #37 评审通过 · Design + Spec 双产物）
  - L2-4 Knowledge / Memory ✅ v0.1.0 Go baseline（2026-07-24）→ ✅ **v0.2.0 Python**（2026-07-27 #43 评审通过 · Design 1920 行 / 97KB + Spec 4152 行 / 194.6KB · §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项 · 60 测试 ID + 30 验收点 + 22 开放问题）
  - **L2 阶段 4/4 完成**（Python 化 100% · L2-1 + L2-2 + L2-3 + L2-4 全部 v0.2.0 评审通过）

### 实施层

- [ ] Agent CRD（v1alpha1）+ Agent Controller
- [ ] AgentSet CRD（v1alpha1）+ AgentSet Controller
- [ ] Workflow CRD（v1alpha1）+ Workflow Controller（含 DAG 校验）
- [ ] A2A core lib（Message / Task / AgentCard 实现）
- [ ] Hello Agent 镜像（Go，无框架，10 行代码 ping/pong）
- [ ] `kubectl apply -f examples/hello-agent.yaml` 端到端跑通
- [ ] Helm chart 基础（Operator Deployment + RBAC + NetworkPolicy + ServiceAccount）
- [ ] E2E 测试（kind + hello-world 通信）
- [ ] GitHub Actions CI（lint + unit + e2e）
- [ ] Prometheus 强制指标（`superteam_*` 前缀）
- [ ] 结构化 JSON 日志（K8s stdout）

**Done when**：`kubectl get agents` 显示 hello-world agent 运行，并通过 A2A `Message` 与另一 in-cluster agent 通信；E2E + CI 全绿。

### Phase 1.5 — Python-first 全栈迁移（2026-07-24 · ADR-0005）🚧 进行中

> **触发事件**：用户锁定平台全栈 Python（2026-07-24）；ADR-0005 批准；宪法 v0.5.0 同步升级
> **状态**：✅ L1 v0.2.0 已通过；✅ L2-1 Python v0.2.0 已通过；✅ L2-2 Python v0.2.0 已通过；✅ L2-3 Adapter Python v0.2.0 已通过；✅ **L2-4 Knowledge/Memory Python v0.2.0 已通过**（2026-07-27 #43 评审通过 · 60 测试 ID + 30 验收点 + 22 开放问题）；**L2 阶段 4/4 全部完成**（Python 化 100%）

- [x] **ADR-0005**（Python-first 技术栈）✅ 2026-07-24
- [x] **宪法 v0.5.0**（§3.8 Python-first + §9 pytest + §10 docstring + §13 SDK 维护 + §15 类型检查红线）✅ 2026-07-24
- [x] **L3-1 Operator Core v0.2.0**（[Spec](docs/spec/L3-file-specs/L3-operator-core.md) · 245KB / 3925 行 / 16 节 + 2 附录 / 70 Python + 9 Helm + 25 工程 + 50 顶层测试 = 162 文件 + 277 测试 ID + 25 OPEN-OP / [评审](docs/reviews/l3-1-operator-core-spec-review.md) 700 行 / 55KB / §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项）✅ 2026-07-28 #56
- [x] **L1 v0.2.0**（Architecture + Spec + 评审）✅ 2026-07-24
- [x] **L2-1 A2A Protocol v0.2.0 Python**（设计 + Spec + 评审）✅ 2026-07-24
- [x] **L2-2 Go baseline 归档** → `docs/archive/pre-python-2026-07-24/` ✅ 2026-07-24
- [x] **L2-2 Python 设计 v0.2-draft-skeleton** ✅ 2026-07-24
- [x] **L2-2 Python 设计 v0.2-draft-full** ✅ 2026-07-24（§0-§14 + 附录 A/B 全部完整）
- [x] **L2-2 Python 设计 v0.2.0 评审通过** ✅ 2026-07-24（[评审](docs/reviews/l2-2-operator-core-python-review.md) · 10 维度全 PASS · 0 阻塞项）
- [ ] **L2-2 Python Spec v0.2-draft**（独立任务，下次会话启动；建议拆 Spec 起草 + 评审两会话避免 §16.1 红线）
- [ ] **L3-1 Operator Core 文件级 Spec**（Spec 评审通过后启动；建议拆主 Spec 50-60KB + 辅助 Spec 30-40KB）
- [x] **L2-3 Adapter Python v0.2-draft 设计** ✅ 2026-07-26（[设计](docs/design/L2-modules/L2-adapter.md) · 1267 行 / 66KB / 14 节 + 2 附录；待评审 + Spec 起草）
- [x] **L2-3 Adapter Python v0.2 评审**（[评审](docs/reviews/l2-3-adapter-python-review.md) · §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项 · 49.7KB / 657 行 · 升级 v0.2.0）✅ 2026-07-26
- [x] **L2-3 Adapter Python v0.2 Spec**（[Spec](docs/spec/L2-module-specs/L2-adapter.md) · 114KB / 2705 行 / 14 节 + 2 附录）✅ 2026-07-26
- [x] **L2-4 Knowledge/Memory Python v0.2**（[Design](docs/design/L2-modules/L2-knowledge-memory.md) 1920 行 / 97KB + [Spec](docs/spec/L2-module-specs/L2-knowledge-memory.md) 4152 行 / 194.6KB + [评审](docs/reviews/l2-4-knowledge-memory-spec-python-review.md) 697 行 / 59.7KB · §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项 · 60 测试 ID + 30 验收点 + 22 开放问题）✅ 2026-07-27
- [x] **L3-1 Operator Core v0.2.0**（[Spec](docs/spec/L3-file-specs/L3-operator-core.md) · 245KB / 3925 行 / 70 Python + 9 Helm + 25 工程 + 50 顶层测试 = 162 文件 + 277 测试 ID + 25 OPEN-OP / [评审](docs/reviews/l3-1-operator-core-spec-review.md) 700 行 / 55KB · §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项；L3 阶段 1/4 完成）✅ 2026-07-28 #56
- [x] **L3-2 A2A Core v0.2.0**（[Spec](docs/spec/L3-file-specs/L3-a2a-core.md) · 2852 行 / 160KB / 16 节 + 2 附录 / 30 文件 + 9 Helm + 30 测试 / 276 测试 ID / 24 错误码 / 15 指标 / [评审](docs/reviews/l3-2-a2a-core-spec-review.md) 217 行 / 20KB · §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项）✅ 2026-07-28 #54
- [x] **L3-3 Adapter SDK v0.2.0**（[Spec](docs/spec/L3-file-specs/L3-adapter-sdk.md) · ~2400 行 / 148KB / 16 节 + 2 附录 / 12 SDK + 22 framework + 11 文件级契约 + 200 测试 ID + 45 文件镜像清单 / [评审](docs/reviews/l3-3-adapter-sdk-spec-review.md) 657 行 / 40KB · §A-§P 10 维度全 PASS · 0 阻塞项 · 9 关注项 · 4 建议项；L3 阶段 3/4 完成）✅ 2026-07-29 #58
- [x] **L3-4 Hello Agent v0.2.0**（[Spec](docs/spec/L3-file-specs/L3-hello-agent.md) · 1576 行 / 75KB / 11 主章节 §0-§10 + 2 附录 / 5 文件级契约 + 7 Helm 模板 + 1 Dockerfile + 2 CRD / 25 测试 ID + 30/37 验收点 / [评审](docs/reviews/l3-4-hello-agent-spec-review.md) 700+ 行 / 48.8KB · §A-§J 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项；L3 阶段 4/4 完成 · 3 关注项 L3-4-followup-1~3 移交 L4 实施第一周 / v0.2.1）✅ 2026-07-29 #61
- [x] **L3-5 Knowledge Service v0.2.0**（[Spec](docs/spec/L3-file-specs/L3-knowledge-service.md) · 2467 行 / 154KB / 16 节 + 2 附录 / 30 文件级契约 + 7 Helm 模板 + 1 Dockerfile + 2 CRD / 60 测试 ID + 30/30 验收点 / [评审](docs/reviews/l3-5-knowledge-service-spec-review.md) 552 行 / 57KB · §A-§Q 17 节 / 10 维度全 PASS · 0 阻塞项 · 4 关注项 · 4 建议项；L3 阶段 5/5 完成 · 5 关注项 L3-5-followup-1~5 移交 v0.2.1 / L3-6 / L4 实施第一周）✅ 2026-07-29 #63.5
- [x] **L3-6 Memory backend v0.2.0**（[Spec](docs/spec/L3-file-specs/L3-memory-backend.md) · ~1850 行 / 122KB / §0-§13 + 附录 A/B + M.1-M.6 / 28 文件级契约 + 60 测试 ID + 30/30 验收点 + 5 关键不变量 / 12 MEMORY_* 错误码零漂移 + MemoryBackend 抽象层 / [评审](docs/reviews/l3-6-memory-backend-spec-review.md) 525 行 / 67.9KB · §A-§Q 17 节 / 10 维度全 PASS · 0 阻塞项 · 5 关注项 · 4 建议项；L3 阶段 6/6 完成 · 5 关注项 L3-6-followup-1~5 全部关闭（TEST-MEM-051 集合相等静态断言 + §9.7 PrometheusRule 完整 YAML + HELM-DEPLOY-002 IPC/env/Recreate 描述 + role_write admissionregistration+authn+authz + Clock.monotonic() 暴露到 handler 边界）· 4 建议项 L3-6-followup-M-2.1~2.4 移交 v0.2.1 微同步）✅ 2026-07-30 #67
- [ ] **L4 Python 实现启动**（✅ **已解锁 · ADR-0006 v1.0 Accepted (D 方案 · 2026-07-30 #71)** · uv workspace + packages/operator + packages/a2a-core + packages/adapter-sdk + **packages/knowledge-memory（D 方案合并 packages/knowledge + packages/memory）** + packages/hello-agent + services/knowledge-memory-service）

**Done when**：L2 Python 设计 + Spec + 评审全 4 模块通过；L3 Python 文件级 Spec 全模块通过；uv workspace 初始化；L4 至少 1 个 Python 包可 `uv sync` 安装并 `pytest` 通过

---

## Phase 2 — 知识管理（第 11-14 周）⏳ 待启动

> 对应发版 tag：**`v0.1.0-beta`**

- [ ] KnowledgeScope CRD（v1alpha1）+ Scope Controller
- [ ] KnowledgeItem CRD（v1alpha1）+ Item Controller
- [ ] Knowledge Service（特殊 Agent，CRD-driven，自身走 A2A 协议）
- [ ] A2A method：`a2a.queryKnowledge` / `a2a.getKnowledgeItem`
- [ ] 4 级作用域继承规则实现（industry / organization / team / project）
- [ ] 知识管理 E2E 测试
- [ ] 知识版本与可见性控制（`visibility: public | org-only | team-only | private`）

**Done when**：在 project scope 下创建 KnowledgeItem，能被同 scope 的 Agent 通过 `a2a.queryKnowledge` 检索到；上层 scope 的 KnowledgeItem 自动可见（继承规则验证）。

---

## Phase 3 — Memory（第 15-18 周）✅ 4/4 PR merged（#96）· 文档同步待 #97

> 对应发版 tag：**`v0.1.0-rc`**
>
> **实施状态**（截至 2026-08-10 #97）：
> - ✅ **L4-Phase1 MVP Core 5/5 Step merged**（PR #17/#18/#19/#20/#21 · 138/138 PASS · 2026-08-07）
> - ✅ **L4-Phase2 Memory spike 4/4 PR merged**（PR #22 RBAC + #23 K8sLeaseLeaderElector + #24 H-RM/H-QM stubs + #25 kind E2E spike 基础设施 · 2026-08-09 · #88）
> - ✅ **chart 完整化**（PR-4.1 #89 + #90 · deployment.yaml + service.yaml + CRD + Dockerfile · #91）
> - ✅ **Phase 3 4/4 PR merged**（PR-1 #30 A2A HTTP JSON-RPC server + PR-2 #34 K8sBackend 完整实装 + PR-3 #35 25 指标 ServiceMonitor + PR-4 #36 H-RM/H-QM-E2E 真实实装 · 241/241 PASS · #92-#96）
> - 🚧 **Phase 3 PR-5 文档同步**（PR #37 待启动 · §F.1-§F.4 跨文档同步）

- [x] Memory CRD（v1alpha1）+ Memory Controller · ✅ L4-Phase1 Step 1（uv workspace + Pydantic schema · 2026-08-03 #76）
- [x] MemoryReconciler（周期 reconcile + decay/reinforce） · ✅ L4-Phase1 Step 3（60s kopf.timer · 2026-08-05 #79 · 15 测试 TEST-MEM-016~030 PASS）
- [x] A2A method：`a2a.recordMemory` / `a2a.queryMemory` · ✅ L4-Phase1 Step 4（in-process handlers · 2026-08-05 #80 · 8 测试 TEST-MEM-053~060 PASS）
- [x] MemoryBackend 抽象层（InMemoryBackend） · ✅ L4-Phase1 Step 2（Protocol + 4 纯函数 · 2026-08-04 #77 · 11 测试 PASS）
- [x] K8sLeaseLeaderElector 完整实装 · ✅ L4-Phase2 PR-2（PR #23 · 2026-08-07 · 192 PASS · 覆盖率 93.26%）
- [x] H-RM/H-QM IT/CF 4 ID stub 升级 · ✅ L4-Phase2 PR-3（PR #24 · 2026-08-07）
- [x] kind E2E spike 基础设施 · ✅ L4-Phase2 PR-4（PR #25 · 2026-08-09 · LEADER-E2E-001 PASS · 5 skipped · chart 缺口 P0）
- [x] chart 完整化（CRD + deployment + service + Dockerfile） · ✅ L4-Phase2 PR-4.1 + #4.1.1（PR #27 + #89 + #90 · 2026-08-09 · #91）
- [x] A2A HTTP JSON-RPC server（starlette + uvicorn · 单进程 D 方案） · ✅ Phase 3 PR-1（PR #30 · 2026-08-10 · #92 · 12 测试 PASS）
- [x] K8sBackend 完整实装（CustomObjectsApi · helm `backend.type=k8s`） · ✅ Phase 3 PR-2（PR #34 · 2026-08-10 · #94 · 8 测试 PASS）
- [x] 25 指标 ServiceMonitor 全量验证（Operator 真实输出） · ✅ Phase 3 PR-3（PR #35 · 2026-08-10 · #95 · observability 完整）
- [x] H-RM/H-QM-E2E-001 真实实装（unskip + port-forward + JSON-RPC round-trip） · ✅ Phase 3 PR-4（PR #36 · 2026-08-10 · #96 · 5 E2E 全部 unskip）
- [x] 5 维矩阵实现（industry / org / team / project + agent-private 正交） · ✅ L2-4 §3.4 Spec 完整版 + L3-6 §3 Pydantic schema
- [x] Memory 生命周期算法（confidence 评估 + decay 半衰期 + reinforcedCount 强化） · ✅ L4-Phase1 Step 5（_build_memo + admission + BM25 index · 2026-08-07 #82 · 138/138 PASS）
- [x] Memory E2E 测试（5 E2E 全部 PASS · H-RM/H-QM unskip 后 4/6 partial · 持续改进） · ✅ Phase 3 PR-4 完成 H-RM/H-QM unskip
- [ ] Memory 跨级 scope-up 机制（v0.1 简化为手动触发）

**Done when**：Agent 记录 Memory 后，30 天后看到 confidence 自然衰减到阈值以下被归档；reinforce 后回升；agent-private 隔离生效。

---

## Phase 4 — 打磨 + Launch（第 19-20 周）✅ **8/8 PR merged · Phase 4 全部收口**（PR-1 + PR-2 + PR-3 + PR-4a plan + PR-4a 实装 + PR-4b 实装 + PR-4c 实装 + **PR-5 实装**）

> 对应发版 tag：**`v0.1.0`**

**Phase 4 实施 PR 推进**：
- [x] **PR-1 Hello Agent Step 1**（5 文件级契约 + 22 测试 ID） · ✅ #38 · 2026-08-10 · 191/191 PASS
- [x] **PR-2 Hello Agent Step 2**（Dockerfile + 8 Helm + kind E2E） · ✅ #45 squash merged @ `76c08f2` · 2026-08-11 · 36/36 PASS
- [x] **PR-3 Knowledge Service Step 1**（8 CRD + 4 shared + 30 测试 ID） · ✅ #49 squash merged @ `74af527` · 2026-08-12 · 284/284 PASS · 6 commits feat 分支
- [x] **PR-4a plan v0.1-draft**（23 错误码 + admission webhook + 入参校验） · ✅ #51 squash merged @ `9f2be9a` · 2026-08-12
- [x] **PR-4b plan v0.1-draft**（4 A2A handler + 12 service） · ✅ #53 squash merged @ `f5d9220` · 2026-08-12
- [x] **PR-4c plan v0.1-draft**（ASGI + Card-driven + BM25 + scope resolver） · ✅ #55 squash merged @ `2f0202d` · 2026-08-12
- [x] **PR-5 plan v0.1-draft**（7 Helm + RBAC + cert-manager + kind E2E） · ✅ #57 squash merged @ `406aa5c` · 2026-08-12
- [x] **PR-4a Phase B 实装**（11 KNOWLEDGE_* enum + admission webhook 50ms fail-closed + KnowledgeMemoryMutexValidator 5 步算法 + 3 Pydantic v2 validators） · ✅ #58 squash merged @ `834ced8` · 2026-08-13 · **347/347 PASS** · 8 commits feat 分支 + 2 Subagent 接力
- [x] **PR-4b Phase A+B 实装**（4 A2A handler + 12 service + 18 测试 ID + WireSyncService 23 错误码静态断言） · ✅ #59 squash merged @ `f9b733f` · 2026-08-14 · **437/437 PASS** · 4 commits feat 分支 + 2 Subagent 接力 + 1 PR-4b 启动前置修复（修复 6 PR-4a 遗留 admission 失败 · 382 → 388 PASS）· 90 测试 ID · 宪法 §17 SOLID 6 原则应用验证
- [x] **PR-4c 实装**（ASGI server + Card-driven + BM25 业务邏輯 + scope resolver + visibility resolver · 依赖 PR-4b handlers） · ✅ #60 squash merged @ `00b3457` · 2026-08-16 · **456/456 PASS** · 5 commits feat 分支 + 2 Subagent 接力 + 1 pytest 根因修复（typo path 影子目录合并 + git index 恢复）
- [x] **PR-5 实装**（7 Helm templates 完整化 + Dockerfile multi-stage + cert-manager mTLS templates + 16 测试 ID） · ✅ #61 squash merged @ `eb4a7be` · 2026-08-16 · **466/466 PASS** · 1 主 Agent 起草（Phase A · 4 files）+ 1 主 Agent 测试实装（Phase B · 16 测试 ID）· 4 CI SUCCESS

> 对应发版 tag：**`v0.1.0`**

- [ ] 60-90s Demo 视频（含 Knowledge + Memory 演示）
- [ ] README 重写（替换"planned"为"works" + 5 能力 + 6 CRD 介绍）
- [ ] HN Show HN 草稿（提前 2 周打磨）
- [ ] Reddit / dev.to / 掘金 cross-post 草稿
- [ ] CONTRIBUTING.md 实际本地开发步骤
- [ ] GitHub Release note + Tag + 镜像推送
- [ ] ROADMAP 同步更新（标 v0.1.0 完成）

**Done when**：`v0.1.0` GitHub Release 发布 + HN 提交 + 至少 50 个 star（首周目标）。

---

## Phase 5 — v0.5.0（v1.0.0 前最后一个 minor）⏳

> 预计 2027-Q2 启动

- [ ] 6 个 CRD `v1alpha1 → v1beta1` 字段冻结 + conversion webhook
- [ ] LangChain adapter（第一个 framework adapter）+ Golden Adapter 测试（≥ 5 cases）
- [ ] AutoGen adapter + Golden Adapter 测试
- [ ] SSE Streaming（`a2a.subscribeTask` / `a2a.cancelTask`）
- [ ] `Conversation` CRD（A2A 长会话状态）
- [ ] 完整 Conformance 套件（参考 `google-a2a/conformance`）

---

## Phase 6 — v1.0.0（第一个 stable release）⏳

> 预计 2027-Q3

- [ ] 6 framework adapters 全覆盖（LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents）
- [ ] 6 个 CRD `v1beta1 → v1` + conversion webhook（字段冻结）
- [ ] Web Dashboard（React 19 + Vite + TanStack Query）
- [ ] 完整 Conformance 套件 100% 通过
- [ ] 5 类 28 项验收门禁全部通过（功能 / 质量 / 安全 / 可观测 / 文档）
- [ ] 社区贡献通道完善（good-first-issue 清单 + 自动 CHANGELOG）

---

## Phase 7 — Growth（v1.0.0 之后）⏳

- [ ] 1,000 stars 里程碑
- [ ] 招募 2-3 名 framework 维护者（每个 adapter 1 人）
- [ ] 多集群联邦（v2 范畴）
- [ ] 3,000 stars 里程碑（项目 North Star Metric）

---

## 🎯 North Star Metric

**3,000 GitHub stars by 2027-09**（项目启动后 18 个月）

---

## 🚦 Risk Register

| 风险 | 等级 | 缓解措施 |
|---|---|---|
| **范围爆炸** | 高 | ADR-0001 / 0004 / 0002 / 0003 严格限制范围；本 ROADMAP 引用权威 |
| **A2A 协议变更** | 中 | 锁定 minor 版本范围，跟踪上游 `google-a2a/A2A` |
| **K8s API 弃用** | 中 | 跟 kubebuilder 版本升级 |
| **单人 2h/天 不够** | 高 | 严格 MVP 范围 + Phase 5 招募 framework 维护者 |
| **冷启动失败** | 高 | Phase 4 提前 2 周准备 HN / Reddit 草稿 + Demo 视频 |
| **Memory 复杂度未知** | 中 | 首个版本最简算法（30 天固定 decay + 手动 reinforce），v0.5 再迭代 |
| **MVP 例外 14.5 长期适用** | 中 | 14.5 例外窗口已在 2026-07-23 明确（v0.1.0 含 → v1.0.0 不含） |

---

## Out of Scope（永久不做）

完整定义见 [ADR-0001 §决策 4](./docs/adr/0001-v1-scope-statement.md#决策-4永久-out-of-scope永远不做)。摘要：

- ❌ **闭源 / 企业版**（Apache 2.0 always）
- ❌ **多集群联邦**（v1 范围内；推 v2）
- ❌ **Vector DB 抽象**（每个 Agent 自带）
- ❌ **非 SDLC 模板**（社区可自由贡献）
- ❌ **对任何 Agent 框架的偏好**（宪法 2.2 强制）
- ❌ **不替代上游 A2A / MCP**（项目是 runtime，非协议实现者）
- ❌ **协议绕过通信**（宪法 2.1 协议优先）
- ❌ **跳过可观测性**（宪法 7.x 无例外）
- ❌ **跳过测试的"快速发版"**（宪法 9.x + 15.5 质量红线）

---

<sub>📬 任何范围变更须走 [ADR 流程](./docs/adr/)。诚实悲观估算优先于乐观估算。</sub>