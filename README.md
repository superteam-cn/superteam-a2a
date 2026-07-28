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

Constitution is at v0.5.0; L1 architecture has been reviewed and accepted. **The current focus is Python-first full-stack migration (ADR-0005)** — L1 v0.2.0 + L2-1 v0.2.0 + L2-2 v0.2.0 + L2-3 v0.2.0 + **L2-4 v0.2.0** Python all passed review (2026-07-24 → 2026-07-27). **L2 阶段 4/4 全部完成**（Python 化 100%）。**L3 阶段 1/4 ~ 2/4 进行中**：L3-1 Operator Core v0.2.0（2026-07-28 #56）+ L3-2 A2A Core v0.2.0（2026-07-28 #54）文件级 Spec 均通过评审。No production code yet — check [ROADMAP.md](./ROADMAP.md) for the full timeline.

### L2 模块矩阵（2026-07-27 · L2 阶段 4/4 完成）

| 模块 | 名称 | 状态 | Python v0.2 进度 |
|------|------|------|------------------|
| **L2-1** | A2A Protocol | ✅ v0.2.0 Python | ✅ 已通过（2026-07-24 · [评审](docs/reviews/l2-1-a2a-protocol-review.md) · §A-§G 10 维度全 PASS） |
| **L2-2** | Operator Core | ✅ v0.2.0 Python | ✅ 已通过（2026-07-25 · [评审](docs/reviews/l2-2-operator-core-python-review.md) · §A-§G 10 维度全 PASS · 103KB / 1890 行） |
| **L2-3** | Adapter | ✅ v0.2.0 Python | ✅ 已通过（2026-07-26 · [评审](docs/reviews/l2-3-adapter-spec-python-review.md) · §A-§P 16 节 · 114KB / 2705 行） |
| **L2-4** | Knowledge / Memory | ✅ **v0.2.0 Python** | ✅ **已通过**（2026-07-27 #43 · [评审](docs/reviews/l2-4-knowledge-memory-spec-python-review.md) · §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项 · 194.6KB / 4152 行 / 60 测试 ID + 30 验收点 + 22 开放问题） |

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
