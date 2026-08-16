# Show HN: superteam-a2a — Multi-framework agent orchestration on Kubernetes

Hi HN,

I'm [@CoderZhangfujiang](https://github.com/CoderZhangfujiang) and I've been building **superteam-a2a** for the last 6 weeks: a Kubernetes-native runtime for AI agent frameworks (LangChain, AutoGen, CrewAI, Semantic Kernel, Strands, Smolagents) that lets them discover and call each other over the [Google A2A protocol](https://github.com/google/A2A).

I started it because every agent framework I've tried in production has the same problem: it's great at running one agent, but the moment you want a fleet of agents that hand off tasks to each other (a planner agent delegating to a researcher agent, a code-review agent checking a coder agent's output), you're on your own. No standard protocol, no Kubernetes story, no observability, no admission control, no shared memory.

## What it does

`superteam-a2a` gives you:

- **6 CRDs** (`Agent`, `AgentSet`, `Workflow`, `KnowledgeScope`, `KnowledgeItem`, `Memory`) — agents are first-class K8s resources with rolling updates, RBAC, ServiceMonitor, NetworkPolicy.
- **A2A protocol runtime** — `Agent Card` (`.well-known/agent.json`), `Message`, `Task`, `Artifact`, `Streaming`, all per the A2A v0.3+ spec. JSON-RPC 2.0 over HTTP/SSE.
- **In-cluster discovery** — DNS-style resolution across namespaces and clusters, just like Services.
- **Hierarchical knowledge** — 4-level scope (industry / org / team / project) with a BM25 inverted index for retrieval.
- **Persistent memory** — agents record/query experience with confidence + decay + reinforce lifecycle, 5-dimensional visibility matrix (4 scopes + agent-private).
- **Admission webhook with 50ms fail-closed** — every record/query validates scope + admission mutex + visibility before hitting storage. Predictable latency under load.
- **Production-grade security** — restricted Pod Security Standards, non-root UID 1000, NetworkPolicy default-deny + explicit allow, opt-in cert-manager mTLS, dual-Role RBAC.

## What it looks like to use it

```bash
helm install hello-agent oci://ghcr.io/superteam-cn/charts/hello-agent

kubectl apply -f examples/lc-code-review-agent.yaml

kubectl get agentsets
# NAME           FRAMEWORK   STATUS    DISCOVERED
# lc-review      langchain   Running   3
# at-test        autogen     Running   1

# Hit the agent card
curl http://hello-agent/.well-known/agent.json

# Send an A2A message
curl -X POST http://hello-agent/jsonrpc \
  -d '{"jsonrpc":"2.0","id":1,"method":"message/send","params":{"message":{"role":"user","parts":[{"type":"text","text":"Review my PR"}]}}}'
```

## Architectural choice: single-process (D 方案)

The biggest decision we made was to run **Knowledge + Memory as a single Python process** (ADR-0006 v1.0). Most "agent platform" projects use 2-3 separate microservices (API + memory + knowledge), each with their own state, each needing leader election, each fighting to keep their caches consistent. We considered and rejected:

- **HTTP loopback** — adds 50ms per call for no architectural benefit
- **Shared memory IPC** — fragile, hard to debug
- **Two pods with separate Redis** — extra moving parts, eventual consistency

Instead, Knowledge Service + Memory Service share one `kopf` operator + one Starlette ASGI app + one process. Single Deployment, single RBAC, single health check, single leader election (when needed). The trade-off: slightly larger container (~150 MB vs 80 MB). We think that's the right call.

## Numbers

- **466/466 tests PASS** (0 regressions) in 2 seconds
- **62 PRs merged** since launch (2026-07-08)
- **5 design dimensions** with full ADR coverage (L1 / L2 / L3 / L4)
- **8/8 Phase 4 PRs shipped** in v0.1.0 (2026-08-16)

## What's NOT done yet

I'll be honest about what's missing:

- **Framework adapters** are not all wired up — only the Hello Agent (reference) and Knowledge Service ship in v0.1.0. LangChain/AutoGen/CrewAI adapters are in progress. The adapter SDK is documented and the architecture is adapter-first, but you'll need to write a small wrapper (5-10 lines per framework).
- **Workflow CRD** is specced but not implemented (Phase 6 / v1.0).
- **Multi-cluster federation** is on the roadmap but not started.
- **Visual editor** for workflows is v1.0+.

## Try it

- **Repo**: https://github.com/superteam-cn/superteam-a2a
- **466 tests, 100% local, no cloud needed**: `uv sync --all-packages --all-extras && uv run pytest`
- **5-minute kind demo**: see `CONTRIBUTING.md`
- **Show me what breaks**: file at https://github.com/superteam-cn/superteam-a2a/issues

## Why I'm posting this

I'm not looking for a launch announcement, I'm looking for **early users who want to influence the API before v0.5**. Specifically:

- **Agent framework authors**: if you maintain LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents, the adapter SDK is designed to make your integration trivial. Tell me what you'd want.
- **K8s operators**: tell me which admission webhook latency budget actually works in your cluster.
- **Anyone running agent fleets**: what's the workflow primitive you'd want first?

I'd rather get feedback now than ship a v1.0 that misses the mark.

— CoderZhangfujiang (Zach Zhang)
