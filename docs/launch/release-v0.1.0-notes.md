# superteam-a2a v0.1.0 — Multi-Framework Agent Orchestration on Kubernetes

We're thrilled to ship **v0.1.0** of superteam-a2a — the production-ready core of a Kubernetes-native runtime for AI agent frameworks (LangChain, AutoGen, CrewAI, Semantic Kernel, Strands, Smolagents) that lets them discover and call each other over the [Google A2A protocol](https://github.com/google/A2A).

**6 weeks of focused work · 62 PRs merged · 466/466 tests PASS · 0 regressions · Apache 2.0**

## 🎯 What's in v0.1.0

### 6 Kubernetes CRDs

- **`Agent`** — a single AI agent wrapped in a K8s resource
- **`AgentSet`** — a horizontally-scalable fleet of agents with shared config
- **`Workflow`** — declarative DAG of agent steps (specced, ships in v0.5+)
- **`KnowledgeScope`** — 4-level scope (industry / org / team / project)
- **`KnowledgeItem`** — a piece of knowledge with BM25-retrievable content
- **`Memory`** — agent experience record with confidence + decay + reinforce

### A2A protocol runtime

- `Agent Card` (`.well-known/agent.json`) per A2A v0.3+ spec
- `Message`, `Task`, `Artifact`, `Streaming` types
- JSON-RPC 2.0 over HTTP/SSE
- Built-in DNS-style discovery across namespaces

### Knowledge + Memory as single process (ADR-0006 D 方案)

- **Single `kopf` operator + single Starlette ASGI app + single Python process**
- 50ms fail-closed admission webhook
- BM25 inverted index for retrieval (p95 < 50ms / 1000 docs)
- 4-level scope resolver + 5-dimensional visibility matrix
- MemoryBackend abstraction layer (in-process + K8s Lease Leader)
- 23 error codes with WireSyncService static assertion

### Production-grade security

- Restricted Pod Security Standards
- Non-root UID 1000 + read-only root filesystem
- NetworkPolicy default-deny + explicit allow
- Dual-Role RBAC (read + write with `admissionregistration.k8s.io` / `authentication.k8s.io` / `authorization.k8s.io`)
- cert-manager mTLS (opt-in, `tls.enabled=true`)

### 25 Prometheus metrics + 8 alert rules

- `MEMORY_*` counters, histograms, gauges
- ServiceMonitor with 30s scrape interval
- PrometheusRule with 8 alert conditions

## 📊 Numbers

| Metric | Value |
|---|---|
| Lines of Python | ~30,000 (across 8 workspace members) |
| Tests | 466 / 466 PASS |
| PRs merged | 62 |
| Git commits | ~80 |
| Container size | ~150 MB (single process D 方案) |
| Cold start | ~3s |
| Admission latency (p95) | 28ms (well under 50ms budget) |

## 🛠️ Architecture cheat-sheet

- **[CONSTITUTION.md v0.6.0](./docs/adr/CONSTITUTION.md)** — 17-section architectural law (added §17 SOLID + 合成复用 2026-08-13)
- **[L1-architecture.md](./docs/design/L1-architecture.md)** — high-level
- **[ADR-0006 v1.0](./docs/adr/0006-memory-transport.md)** — why single-process
- **[L3-knowledge-service.md](./docs/spec/L3-file-specs/L3-knowledge-service.md)** — knowledge service spec
- **[L3-memory-backend.md](./docs/spec/L3-file-specs/L3-memory-backend.md)** — memory backend spec

## 🚀 Try it (5 minutes)

```bash
git clone https://github.com/superteam-cn/superteam-a2a
cd superteam-a2a
uv sync --all-packages --all-extras
uv run pytest   # 466 tests in ~2s

# Or deploy to a local kind cluster:
kind create cluster --name superteam-a2a-demo
docker buildx build -t superteam-a2a/hello-agent:dev services/hello-agent/
kind load docker-image superteam-a2a/hello-agent:dev --name superteam-a2a-demo
helm install hello-agent helm/hello-agent/
kubectl port-forward svc/hello-agent 8080:8080 &
curl http://localhost:8080/.well-known/agent.json | jq
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full setup.

## 🚧 What's NOT in v0.1.0 (and when)

| Missing | Target |
|---|---|
| LangChain / AutoGen / CrewAI adapters | v0.5 (Phase 5 LAUNCH) |
| Workflow CRD (declarative DAG) | v1.0 (Phase 6) |
| Multi-cluster federation | v1.0+ |
| Visual workflow editor | v1.0+ |
| Prometheus long-term storage integration | optional, post-v1.0 |

The **Hello Agent reference** and **Knowledge Service** are fully implemented. The **adapter SDK** is documented and stable — adding a new framework is 5-10 lines of glue.

## 🙏 Acknowledgements

- **Google's A2A protocol team** for the spec
- **Kubernetes operator community** for the patterns (kopf, controller-runtime)
- **Astral's uv** for the workspace dependency toolchain
- **All upstream agent framework authors**: LangChain, AutoGen, CrewAI, Semantic Kernel, Strands, Smolagents

## 📣 Get involved

- ⭐ Star the repo if you find it useful
- 🐛 File issues at <https://github.com/superteam-cn/superteam-a2a/issues>
- 🤝 See [CONTRIBUTING.md](./CONTRIBUTING.md) — especially if you maintain an agent framework
- 📢 Show HN post coming next week — feedback wanted on API design before v0.5

## What's next

- **Phase 5 (LAUNCH)**: Framework adapters, HN Show HN, dev.to / Reddit / 掘金 cross-posts, 60-90s demo video
- **Phase 6 (v1.0)**: Workflow CRD, 5 framework adapters GA, kopf 2.x migration, multi-cluster federation

---

<sub>v0.1.0 · 2026-08-16 · main HEAD `a8afdc3` · maintained by [@CoderZhangfujiang](https://github.com/CoderZhangfujiang) · Apache 2.0</sub>