# superteam-a2a

> **Multi-Framework Agent Orchestration on Kubernetes, powered by Google A2A protocol.**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/status-pre--alpha-yellow)](#project-status)
[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://www.python.org/)
[![A2A](https://img.shields.io/badge/A2A-v0.3+-green)](https://github.com/google/A2A)
[![L1 v0.2.0](https://img.shields.io/badge/L1-v0.2.0-blueviolet)](./docs/design/L1-architecture.md)
[![L2-1 v0.2.0](https://img.shields.io/badge/L2--1-v0.2.0-success)](./docs/design/L2-modules/L2-a2a-protocol.md)
[![L2-2 v0.2.0](https://img.shields.io/badge/L2--2-v0.2.0-success)](./docs/design/L2-modules/L2-operator-core.md)

**superteam-a2a** turns your LangChain, AutoGen, CrewAI, Semantic Kernel, Strands, and Smolagents agents into first-class Kubernetes workloads. Define an `Agent` CRD once, run a fleet of agents that discover and call each other via the [A2A protocol](https://google-a2a.github.io/A2A/), monitor them in Prometheus, and ship an SDLC workflow on day one.

## ✨ What this gives you

- 🧩 **Multi-framework adapters** — bring your existing LangChain/AutoGen/CrewAI agent; wrap it as an A2A card in 5 lines of YAML. (Hello Agent ships in v0.1; framework adapters in v0.5+)
- 🚀 **K8s-native runtime** — agents are CRDs (`Agent`, `AgentSet`, `Workflow`); same scaling, rolling update, RBAC as Deployments.
- 🔌 **A2A protocol-first** — first-class support for `Agent Card`, `Message`, `Task`, `Artifact`, `Streaming` (per the [A2A spec](https://google-a2a.github.io/A2A/specification/)).
- 🔍 **Discovery** — agents publish a `.well-known/agent.json` per the A2A spec; built-in DNS-style resolver for the cluster.
- 📡 **Communication** — A2A `JSON-RPC 2.0` over HTTP/SSE; works across namespaces, clusters, even cloud boundaries.
- 📊 **Monitoring** — Prometheus metrics out of the box (token usage, latency, success rate, A2A RPC error codes).
- 🧠 **Hierarchical knowledge management** — 4-level scope (industry / organization / team / project) + `KnowledgeItem` + `Knowledge Service` (a special A2A-driven Agent). Ships in v0.1.0-beta.
- 💾 **Persistent memory** — agents record/query persistent experience with `confidence` + `decay` + `reinforce` lifecycle; 5-dimensional visibility (4 scopes + `agent-private`). Ships in v0.1.0-rc.
- 🛠️ **Custom workflows** — declarative YAML manifests with DAG validation; visual editor planned for v1.0.
- 📦 **SDLC workflow template** — requirements → design → code → review → test → CI/CD → deploy → monitor, ship-ready.

## 📦 Project status

**🚧 Pre-alpha. v0.1.0 under construction — delivery 2027-01-20.**

This repository was created on 2026-07-08. Scope is locked per [ADR-0001](./docs/adr/0001-v1-scope-statement.md) and [ADR-0004](./docs/adr/0004-v01-scope-extension-knowledge-and-memory.md): **5 base capabilities** (discovery / communication / observability / orchestration / **knowledge management**), **6 CRDs** (Agent / AgentSet / Workflow / KnowledgeScope / KnowledgeItem / Memory), 4-phase delivery (`v0.1.0-alpha` → `beta` → `rc` → `v0.1.0`).

Constitution is at v0.5.0; L1 architecture has been reviewed and accepted. **The current focus is Python-first full-stack migration (ADR-0005) + L4 实施层启动（ADR-0006 v1.0 Accepted · D 方案 · 2026-07-30 #71）** — L1 v0.2.0 + L2-1 v0.2.0 + L2-2 v0.2.0 + L2-3 v0.2.0 + **L2-4 v0.2.0** Python all passed review (2026-07-24 → 2026-07-27). **L2 阶段 4/4 全部完成**（Python 化 100%）。**L3 阶段 6/6 全部完成**（文件级 Spec 100% 通过评审）：L3-1 Operator Core v0.2.0（#56）+ L3-2 A2A Core v0.2.0（#54）+ L3-3 Adapter SDK v0.2.0（#58）+ L3-4 Hello Agent v0.2.0（#61）+ **L3-5 Knowledge Service v0.2.0（#63.5）** + **L3-6 Memory backend v0.2.0（#67）** + **L3-5 v0.2.1 + L3-6 v0.2.1（ADR-0006 D 方案单进程合并 #71）** + **L1 v0.2.0 §4.1 C-6 + C-7 合并为 Knowledge-Memory Service（#71）** + **ADR-0006 v1.0 Accepted（OPEN-MEMORY-001 + OPEN-L1-003 + OPEN-ADR-0006-001 全部关闭 · D 方案 · 2026-07-30 #71）** 文件级 Spec 均通过评审。

**L4 实施层进度**（2026-08-16 #115）：
- ✅ **Phase 1 MVP Core 5/5 Step merged**（PR #17/#18/#19/#20/#21 · 138/138 PASS · uv workspace + Memory CRD + MemoryBackend 抽象层 + MemoryReconciler 60s kopf.timer + in-process handlers + admission + BM25 Index + handle_query_memory）
- ✅ **Phase 2 Memory spike 4/5 PR merged**（PR #22 RBAC + #23 K8sLeaseLeaderElector 完整实装 192 PASS + #24 H-RM/H-QM IT/CF stub 4 ID + #25 kind E2E spike 基础设施）
- ✅ **Phase 3 4/4 PR merged**（PR-1 #30 A2A HTTP JSON-RPC server + PR-2 #34 K8sBackend 完整实装 + PR-3 #35 25 指标 ServiceMonitor + PR-4 #36 H-RM/H-QM-E2E 真实实装 + PR-5 #37 文档同步 · 241/241 PASS）
- ✅ **Phase 4 PR-1 + PR-2 merged**（PR-1 #38 Hello Agent Step 1 + PR-2 #45 Hello Agent Step 2 · Dockerfile + 8 Helm）
- ✅ **Phase 4 PR-3 Knowledge Service Step 1 完整实装**（PR #49 squash merged @ `74af527` · 2026-08-12 · 6 commits feat 分支 + 3 Subagent + 2 hotfix + 1 ruff fix · 8 CRD types + 4 shared modules + 30 测试 ID · **284/284 PASS**）
- ✅ **Phase 4 PR-4a Knowledge Service Step 2a 完整实装**（PR #58 squash merged @ `834ced8` · 2026-08-13 · 11 KNOWLEDGE_* enum + admission webhook 50ms fail-closed + KnowledgeMemoryMutexValidator 5 步算法 + 3 Pydantic v2 validators · **347/347 PASS** · 63 测试 ID）
- ✅ **Phase 4 PR-4b Knowledge Service Step 2b 完整实装**（PR #59 squash merged @ `f9b733f` · 2026-08-14 · 4 A2A handler + 12 service + 18 测试 ID + WireSyncService 23 错误码静态断言 · **437/437 PASS** · 4 commits feat 分支 + 2 Subagent 接力 + 1 PR-4b 启动前置修复（修复 6 PR-4a 遗留 admission 失败 · 382 → 388 PASS）· 90 测试 ID · 宪法 §17 SOLID 6 原则应用验证）
- ✅ **Phase 4 PR-4c Knowledge Service Step 2c 完整实装**（PR #60 squash merged @ `00b3457` · 2026-08-16 · 4 ASGI handler (app + card + routes + main) + 2 BM25 (index + scorer) + 4 级 scope resolver + 5 维 visibility resolver + 20 测试 ID · **456/456 PASS** · 5 commits feat 分支 + 2 Subagent 接力 + 1 pytest 根因修复（typo path 影子目录合并 + git index 恢复）· baseline 437 → 456 PASS · 0 回归）
- 📋 **Phase 4 PR-5 Knowledge Service Step 3 待启动**（7 Helm + RBAC + cert-manager + kind E2E + Dockerfile · 1 周工作量 · #116）

No production code yet — check [ROADMAP.md](./ROADMAP.md) for the full timeline.

### L2 模块矩阵（2026-07-27 · L2 阶段 4/4 完成）

| 模块 | 名称 | 状态 | Python v0.2 进度 |
|------|------|------|------------------|
| **L2-1** | A2A Protocol | ✅ v0.2.0 Python | ✅ 已通过（2026-07-24 · [评审](docs/reviews/l2-1-a2a-protocol-review.md) · §A-§G 10 维度全 PASS） |
| **L2-2** | Operator Core | ✅ v0.2.0 Python | ✅ 已通过（2026-07-25 · [评审](docs/reviews/l2-2-operator-core-python-review.md) · §A-§G 10 维度全 PASS · 103KB / 1890 行） |
| **L2-3** | Adapter | ✅ v0.2.0 Python | ✅ 已通过（2026-07-26 · [评审](docs/reviews/l2-3-adapter-spec-python-review.md) · §A-§P 16 节 · 114KB / 2705 行） |
| **L2-4** | Knowledge / Memory | ✅ **v0.2.0 Python** | ✅ **已通过**（2026-07-27 #43 · [评审](docs/reviews/l2-4-knowledge-memory-spec-python-review.md) · §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项 · 194.6KB / 4152 行 / 60 测试 ID + 30 验收点 + 22 开放问题） |

### L3 文件级 Spec 矩阵（2026-07-30 · L3 阶段 6/6 完成）

| 模块 | 名称 | 状态 | Python v0.2 进度 |
|------|------|------|------------------|
| **L3-1** | Operator Core（文件级） | ✅ v0.2.0 Python | ✅ 已通过（2026-07-28 #56 · [评审](docs/reviews/l3-1-operator-core-spec-review.md) · §A-§P 10 维度全 PASS · 245KB / 3925 行 / 162 文件 + 277 测试 ID） |
| **L3-2** | A2A Core Library（文件级） | ✅ v0.2.0 Python | ✅ 已通过（2026-07-28 #54 · [评审](docs/reviews/l3-2-a2a-core-spec-review.md) · §A-§P 10 维度全 PASS · 160KB / 2852 行 / 30 文件 + 9 Helm + 30 测试 / 276 测试 ID / 24 错误码 / 15 指标） |
| **L3-3** | Adapter SDK（文件级） | ✅ v0.2.0 Python | ✅ 已通过（2026-07-29 #58 · [评审](docs/reviews/l3-3-adapter-sdk-spec-review.md) · §A-§P 10 维度全 PASS · 148KB / ~2400 行 / 12 SDK + 22 framework + 200 测试 ID + 45 文件镜像清单） |
| **L3-4** | Hello Agent（参考实现 · 文件级） | ✅ v0.2.0 Python | ✅ 已通过（2026-07-29 #61 · [评审](docs/reviews/l3-4-hello-agent-spec-review.md) · §A-§J 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项 · 75KB / 1576 行 / 5 文件级契约 + 7 Helm 模板 + 1 Dockerfile + 25 测试 ID） |
| **L3-5** | Knowledge Service（文件级） | ✅ v0.2.0 Python | ✅ 已通过（2026-07-29 #63.5 · [评审](docs/reviews/l3-5-knowledge-service-spec-review.md) · §A-§Q 17 节 / 10 维度全 PASS · 0 阻塞项 · 4 关注项 · 4 建议项 · 154KB / 2467 行 / 30 文件级契约 + 7 Helm + 1 Dockerfile + 60 测试 ID + 30/30 验收点） |
| **L3-6** | Memory backend（**D 方案 · 单进程合并** · 文件级） | ✅ **v0.2.0 + v0.2.1 Python** | ✅ **已通过**（2026-07-30 #67 · [评审](docs/reviews/l3-6-memory-backend-spec-review.md) · §A-§Q 17 节 / 10 维度全 PASS · 0 阻塞项 · 5 关注项全关闭 · 4 建议项 · 122KB / ~1850 行 / 28 文件级契约 + 60 测试 ID + 30/30 验收点 + 12 MEMORY_* 错误码零漂移 + MemoryBackend 抽象层） + **v0.2.1 微同步（ADR-0006 v1.0 Accepted · D 方案 · 2026-07-30 #71）· §6.1+§6.2+§6.3+§6.5+§9.2+§9.10 单进程架构 + OPEN-MEMORY-001 关闭** |


## 🚀 Quickstart (planned)

After v0.1 ships, the goal is:

```bash
# 1. install the operator
helm install superteam-a2a oci://ghcr.io/coderzhangfujiang/charts/superteam-a2a

# 2. apply an AgentSet (LangChain)
kubectl apply -f examples/lc-code-review-agent.yaml

# 3. agents discover each other automatically
kubectl get agents
# NAME        FRAMEWORK      STATUS    DISCOVERED
# lc-review   langchain      Running   3
# at-test     autogen        Running   1

# 4. watch metrics
kubectl port-forward svc/prometheus 9090:9090
```

## 🤝 Contributing

We're early — now is the best time to influence the API. See [CONTRIBUTING.md](./CONTRIBUTING.md) and our [ROADMAP.md](./ROADMAP.md).

## 📜 License

[Apache 2.0](./LICENSE) — friendly for both commercial and open use.

## 🙏 Acknowledgements

- Google's [A2A protocol](https://github.com/google/A2A) team for the spec
- The [Kubernetes](https://github.com/kubernetes-sigs) operator community for the patterns
- All upstream agent framework authors (LangChain, AutoGen, CrewAI, Semantic Kernel, Strands, Smolagents)

---

<sub>👋 Maintainer: [@CoderZhangfujiang](https://github.com/CoderZhangfujiang) · built in the open · powered by A2A</sub>
