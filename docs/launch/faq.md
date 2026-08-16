# FAQ — superteam-a2a v0.1.0

> **Audience**: early users, evaluators, framework maintainers
>
> **Status**: ✅ ready for launch · linked from GitHub Discussions, Reddit, HN comments, Discord
>
> **Last updated**: 2026-08-16

This FAQ answers the top 10 questions we expect from the v0.1.0 launch audience. If your question isn't here, please file an issue at <https://github.com/superteam-cn/superteam-a2a/issues>.

---

## Q1: How do I install superteam-a2a?

**A**: Five minutes, no cloud needed. See [Quickstart in README](https://github.com/superteam-cn/superteam-a2a#-quickstart):

```bash
git clone https://github.com/superteam-cn/superteam-a2a.git
cd superteam-a2a
uv sync --all-packages --all-extras
uv run pytest        # 474 tests in ~2s

kind create cluster --name superteam-a2a-demo
docker buildx build -t superteam-a2a/hello-agent:dev services/hello-agent/
kind load docker-image superteam-a2a/hello-agent:dev --name superteam-a2a-demo
helm install hello-agent helm/hello-agent/
kubectl get agentsets
```

Production install with Prometheus + cert-manager is in [`CONTRIBUTING.md`](https://github.com/superteam-cn/superteam-a2a/blob/main/CONTRIBUTING.md).

---

## Q2: What frameworks are supported in v0.1.0?

**A**: Only the **Hello Agent** (reference implementation) is wired up. The adapter SDK is documented and stable, but the LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents adapters are specced, not implemented. Each adapter is **5-10 lines of glue** using the SDK.

To write a custom adapter:

```python
from superteam_a2a import AgentAdapter, AgentSpec

class MyFrameworkAdapter(AgentAdapter):
    def build_agent(self, spec: AgentSpec) -> Any:
        return my_framework.build(spec)
    
    async def handle_message(self, message: A2AMessage) -> A2AResponse:
        return await my_framework.invoke(message)
```

See [`docs/sdk/`](https://superteam-cn.github.io/superteam-a2a/) for the full SDK reference. v0.5 will ship all 6 framework adapters GA.

---

## Q3: How does the admission webhook work? Why 50ms?

**A**: Every write to Memory or Knowledge goes through an admission webhook that validates scope + mutex + visibility matrix before storage. The 50ms is a **hard timeout** — if validation takes longer, the write is **denied** (fail-closed).

Components in the happy path:

| Component | Latency |
|---|---|
| Pydantic v2 schema check | ~5ms |
| kopf admission handler | ~10ms |
| K8s API network round-trip | ~5-15ms |
| Mutex + visibility matrix | ~3ms |
| **Total** | **~25-35ms** |

Actual p95 measured at **28ms** in our E2E benchmark. 50ms leaves ~15ms headroom for spikes.

Why fail-closed (not fail-open)? Under load, an admission that's "slow but allows" can cause cascading consistency violations. Fail-closed makes the SLO predictable: at the cost of rejecting a small fraction of writes, we get bounded latency for all.

---

## Q4: Is it production-ready?

**A**: Yes for the **core protocol runtime**, no for everything else.

What we believe is production-ready:
- ✅ A2A protocol runtime (JSON-RPC 2.0 over HTTP/SSE)
- ✅ 6 CRDs with RBAC, NetworkPolicy, ServiceMonitor
- ✅ Admission webhook with predictable latency
- ✅ Knowledge + Memory with BM25 + 4-level scope + 5-dim visibility
- ✅ 474 tests with 4 static + 2 dynamic CI gates
- ✅ Restricted PodSecurity, non-root, read-only rootfs

What is NOT production-ready in v0.1.0:
- ⚠️ Framework adapters (only Hello Agent ships)
- ⚠️ Workflow CRD (specced, not built)
- ⚠️ Multi-cluster federation (roadmap)
- ⚠️ Visual workflow editor (v1.0+)

Use v0.1.0 as a **runtime platform** for your agents. Build your own adapters for now. Wait for v0.5+ for production fleet management.

---

## Q5: Why single-process backend (not microservices)?

**A**: It's the explicit architectural decision we made and documented in [ADR-0006 v1.0](https://github.com/superteam-cn/superteam-a2a/blob/main/docs/adr/0006-memory-transport.md). We considered 5 designs and chose **D: single Python process** (kopf operator + Starlette ASGI + Knowledge Service + Memory Service all in one process).

| Option | Verdict |
|---|---|
| A. UDS | Backup option, more complex deployment |
| B. Shared runtime | ❌ process state explosion |
| C. Shared mmap | ❌ fragile, OS-specific |
| **D. Single process** | ✅ **Accepted** |
| E. HTTP loopback | ❌ +50ms per call, no benefit |

Trade-offs accepted:
- ~150 MB container vs ~80 MB (acceptable)
- Memory leak in one service affects both (single restart cycle is fine)
- Can't scale Knowledge independently of Memory (not needed in v0.1.0)

When to revisit: if memory footprint grows beyond ~500 MB, or Knowledge needs independent scaling. See [`docs/architecture/single-process-backend.md`](https://superteam-cn.github.io/superteam-a2a/architecture/single-process-backend/) for the full visual.

---

## Q6: How is data persisted?

**A**: All data lives in **Kubernetes etcd** as CRD objects. There is no external database.

- **`KnowledgeItem`**, **`Memory`**, **`KnowledgeScope`**: stored as K8s CRDs → etcd
- **Agent state**: in-memory, rebuilt from CRDs on restart
- **Hot-path indexes** (BM25 inverted index): in-memory, rebuilt from CRDs on restart

This means:
- ✅ No external dependencies (besides K8s)
- ✅ Standard K8s backup/restore applies
- ✅ Multi-replica = K8s Deployment replicas
- ⚠️ Not designed for 10M+ items per scope (use external DB for that)

For v0.5+ we're considering a pluggable `MemoryBackend` (in-memory + K8s Lease Leader is the current default; Redis / PostgreSQL adapters are on the roadmap).

---

## Q7: How does it compare to LangGraph / AutoGen Studio?

**A**: Different layer of the stack.

| | LangGraph / AutoGen Studio | superteam-a2a |
|---|---|---|
| **Layer** | Application (single agent logic) | Infrastructure (cluster runtime) |
| **State** | In-memory, per-agent | Distributed, via K8s CRDs |
| **Discovery** | Code-level imports | A2A protocol over network |
| **Deployment** | Python script | K8s Deployment + Helm chart |
| **Multi-tenancy** | Single process | Namespaces + RBAC |
| **Observability** | Framework logs | Prometheus + ServiceMonitor |
| **Admission control** | None | 50ms fail-closed webhook |

**They compose, not compete.** Run LangGraph inside a superteam-a2a `Agent` Pod. superteam-a2a handles fleet management, A2A communication, and observability — LangGraph handles the agent logic.

---

## Q8: How do I write a framework adapter?

**A**: 5-10 lines of glue. The full SDK reference is at [`docs/sdk/`](https://superteam-cn.github.io/superteam-a2a/).

Minimal LangChain adapter example:

```python
from superteam_a2a import AgentAdapter, AgentSpec, A2AMessage, A2AResponse
from langchain.agents import create_react_agent

class LangChainAdapter(AgentAdapter):
    async def handle_message(self, message: A2AMessage) -> A2AResponse:
        prompt = message.text
        result = await self.agent.ainvoke({"input": prompt})
        return A2AResponse(text=result["output"])
```

That's it. The SDK handles:
- A2A protocol parsing
- Admission webhook validation
- Scope + visibility enforcement
- Metrics emission
- DNS-style discovery

The framework-specific code is just `await self.agent.ainvoke(...)`.

---

## Q9: What's the difference between Agent and AgentSet?

**A**:

- **`Agent`** = a single AI agent wrapped in a K8s resource. Use when you need one specific agent.
- **`AgentSet`** = a horizontally-scalable fleet of agents with shared config. Use when you need multiple replicas behind one logical name.

```yaml
# Agent — single instance
apiVersion: superteam.io/v1alpha1
kind: Agent
metadata:
  name: lc-review
spec:
  framework: langchain
  model: gpt-4o
---
# AgentSet — 3 replicas, autoscale 1-10
apiVersion: superteam.io/v1alpha1
kind: AgentSet
metadata:
  name: at-test-fleet
spec:
  replicas: 3
  scaleTarget: { minReplicas: 1, maxReplicas: 10, targetCPUUtilization: 70 }
  template:
    spec:
      framework: autogen
      model: claude-3-opus
```

Same `kubectl get agentsets` shows both.

---

## Q10: What's the roadmap?

**A**: 

- **v0.1.0** (✅ 2026-08-16) — core protocol runtime, Hello Agent, 6 CRDs, Knowledge + Memory single-process
- **v0.5** (Phase 5 LAUNCH, ~Q4 2026) — LangChain / AutoGen / CrewAI adapters GA
- **v1.0** (Phase 6, ~Q1-Q2 2027) — Workflow CRD, 5 framework adapters production-ready, 1000+ GitHub stars, kopf 2.x migration, multi-cluster federation
- **v1.0+** — Visual workflow editor, MCP tool integration, RBAC scope-up automation

The biggest missing piece right now is **framework adapters**. If you maintain LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents and want to influence the adapter SDK before v0.5, **now is the best time**.

---

## Still have questions?

- **Bug or feature request**: <https://github.com/superteam-cn/superteam-a2a/issues>
- **Show HN / Reddit / Discord discussions**: see [submission-checklist.md](./submission-checklist.md)
- **Maintainer**: [@CoderZhangfujiang](https://github.com/CoderZhangfujiang) (Zach Zhang)

<sub>FAQ is updated each release. Suggest additions via PR to `docs/launch/faq.md`.</sub>
