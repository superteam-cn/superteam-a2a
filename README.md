# superteam-a2a

> **Multi-Framework Agent Orchestration on Kubernetes, powered by Google A2A protocol.**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/status-v0.1.0--ready-success)](#project-status)
[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://www.python.org/)
[![A2A](https://img.shields.io/badge/A2A-v0.3+-green)](https://github.com/google/A2A)
[![Tests](https://img.shields.io/badge/tests-466%2F466-success)](./docs/admin/l4-package-layout.md)
[![Constitution](https://img.shields.io/badge/constitution-v0.6.0-blueviolet)](./docs/adr/CONSTITUTION.md)

**superteam-a2a** turns your LangChain, AutoGen, CrewAI, Semantic Kernel, Strands, and Smolagents agents into first-class Kubernetes workloads. Define an `Agent` CRD once, run a fleet of agents that discover and call each other via the [A2A protocol](https://google-a2a.github.io/A2A/), monitor them in Prometheus, and ship an SDLC workflow on day one.

## ✨ What works today

- 🧩 **Hello Agent reference implementation** — a working LangChain-style agent that talks A2A over JSON-RPC, registers as `Agent`/`AgentSet` CRDs, and survives `helm install` + `kubectl rollout`. Use it as the template for your framework adapter.
- 🚀 **K8s-native runtime** — `Agent`, `AgentSet`, `Workflow`, `KnowledgeScope`, `KnowledgeItem`, `Memory` CRDs (6 total). Same scaling, rolling update, RBAC, and ServiceMonitor as Deployments.
- 🔌 **A2A protocol-first** — first-class `Agent Card` (`.well-known/agent.json`), `Message`, `Task`, `Artifact`, `Streaming` per the [A2A spec](https://google-a2a.github.io/A2A/specification/).
- 🔍 **Discovery** — agents publish a `.well-known/agent.json` per the A2A spec; built-in DNS-style resolver for the cluster.
- 📡 **Communication** — A2A `JSON-RPC 2.0` over HTTP/SSE; works across namespaces and clusters.
- 📊 **Monitoring** — Prometheus metrics out of the box (token usage, latency, success rate, A2A RPC error codes) + 8 alert rules in `PrometheusRule`.
- 🧠 **Hierarchical knowledge management** — 4-level scope (industry / organization / team / project) + `KnowledgeItem` + Knowledge Service (a special A2A-driven Agent) **with BM25 inverted index and 5-dimensional visibility matrix**.
- 💾 **Persistent memory** — agents record/query persistent experience with `confidence` + `decay` + `reinforce` lifecycle; 5-dimensional visibility (4 scopes + `agent-private`). **MemoryBackend abstraction layer + in-process + K8s Lease Leader** production-ready.
- 🛡️ **Admission webhook 50ms fail-closed** — every record/query validates scope + admission mutex + visibility matrix before hitting storage. Latency-bounded for predictable cluster behaviour.
- 🔐 **Production-grade security** — restricted Pod Security Standards, non-root UID 1000, NetworkPolicy default-deny + explicit allow, cert-manager mTLS (opt-in), dual-Role RBAC (read + write with `admissionregistration.k8s.io`/`authentication.k8s.io`/`authorization.k8s.io`).
- 📦 **Single-process D 方案** — Knowledge + Memory share one Deployment (ADR-0006 Accepted), backed by `kopf` operator + Starlette ASGI in a single Python process. No leader-election complexity, no shared IPC.

## 📦 Project status

**✅ v0.1.0 ready — production-ready core, framework adapters on the way.**

This repository was created on 2026-07-08. Scope is locked per [ADR-0001](./docs/adr/0001-v1-scope-statement.md) and [ADR-0004](./docs/adr/0004-v01-scope-extension-knowledge-and-memory.md): **5 base capabilities** (discovery / communication / observability / orchestration / knowledge management), **6 CRDs**, single-process **ADR-0006 v1.0 D 方案** accepted. **Phase 4 全部 8 PR merged · 474/474 tests PASS · 0 回归**.

**v0.1.0 ships with** (all shipped 2026-08-16, main HEAD `6c4f9ce`):

| Component | Status | Squash | Tests |
|---|---|---|---|
| Hello Agent (reference) | ✅ | `76c08f2` | 36 PASS |
| Knowledge Service Step 1 (CRDs) | ✅ | `74af527` | 284 PASS |
| Knowledge Service Step 2a (admission + 11 KNOWLEDGE_*) | ✅ | `834ced8` | 347 PASS |
| Knowledge Service Step 2b (4 handlers + 12 services) | ✅ | `f9b733f` | 437 PASS |
| Knowledge Service Step 2c (ASGI + BM25 + scope + visibility) | ✅ | `00b3457` | 456 PASS |
| Knowledge Service Step 3 (Helm + Dockerfile + cert-manager + RBAC) | ✅ | `eb4a7be` | 466 PASS |

**Roadmap to v1.0** (see [ROADMAP.md](./ROADMAP.md)):
- ✅ **Phase 1-4** (MVP Core → Knowledge Service full stack → 8/8 PR merged)
- 🚧 **Phase 5** (Launch + Polish): README rewrite, HN Show HN draft, framework adapters (LangChain / AutoGen / CrewAI), more CRDs (Workflow declarative DAG).
- 📋 **Phase 6** (v1.0 GA): 5 framework adapters production-ready, 1000+ GitHub stars, kopf 2.x migration, multi-cluster federation.

### Constitution & design quality

The codebase operates under [CONSTITUTION.md v0.6.0](./docs/adr/CONSTITUTION.md) — 17 sections covering architecture, security, testing, observability, and the new **§17 SOLID + 合成复用** design principles (added 2026-08-13). Every PR passes 4 static gates (`ruff check`, `ruff format`, `pyright`, `pytest`) and 2 dynamic gates (`CodeQL python`, `CodeQL actions`).

## 🚀 Quickstart

```bash
# 1. Clone + install
git clone https://github.com/superteam-cn/superteam-a2a.git
cd superteam-a2a
uv sync --all-packages --all-extras

# 2. Run the full test suite (466 tests, ~2s)
uv run pytest --tb=short -q

# 3. Deploy the Hello Agent + Knowledge Service to a local kind cluster
kind create cluster --name superteam-a2a-demo
docker buildx build -t superteam-a2a/hello-agent:dev services/hello-agent/
kind load docker-image superteam-a2a/hello-agent:dev --name superteam-a2a-demo
helm install hello-agent helm/hello-agent/

# 4. Verify the agent is registered
kubectl get agentsets
# NAME           FRAMEWORK   STATUS    DISCOVERED
# hello-agent    hello       Running   0

# 5. Hit the A2A card
kubectl port-forward svc/hello-agent 8080:8080 &
curl http://localhost:8080/.well-known/agent.json | jq

# 6. Send an A2A message
curl -X POST http://localhost:8080/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"message/send","params":{"message":{"role":"user","parts":[{"type":"text","text":"Hello"}]}}}'
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full development setup, the kind E2E workflow, and the 4-gate CI checklist.

## 🤝 Contributing

We're early — now is the best time to influence the API. See [CONTRIBUTING.md](./CONTRIBUTING.md) and our [ROADMAP.md](./ROADMAP.md).

**Looking for framework adapter authors?** We're building adapters for LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents. See [docs/design/L2-modules/L2-adapter.md](./docs/design/L2-modules/L2-adapter.md) for the adapter SDK spec and [docs/reviews/l3-3-adapter-sdk-spec-review.md](./docs/reviews/l3-3-adapter-sdk-spec-review.md) for the 22-framework coverage plan.

## 📜 License

[Apache 2.0](./LICENSE) — friendly for both commercial and open use.

## 🙏 Acknowledgements

- Google's [A2A protocol](https://github.com/google/A2A) team for the spec
- The [Kubernetes](https://github.com/kubernetes-sigs) operator community for the patterns
- All upstream agent framework authors (LangChain, AutoGen, CrewAI, Semantic Kernel, Strands, Smolagents)
- [uv](https://github.com/astral-sh/uv) for the workspace dependency toolchain
- [kopf](https://github.com/nkdAgility/kopf) for the Kubernetes operator framework

---

<sub>👋 Maintainer: [@CoderZhangfujiang](https://github.com/CoderZhangfujiang) · built in the open · powered by A2A · ⭐ if you like it</sub>