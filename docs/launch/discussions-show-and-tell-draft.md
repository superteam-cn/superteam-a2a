# GitHub Discussions: Show and tell — superteam-a2a v0.1.0

> **Submission target**: <https://github.com/superteam-cn/superteam-a2a/discussions/new?category=show-and-tell>
>
> **Status**: ⏳ pending (maintainer action)
>
> **Format**: Discussions markdown body · distinct from HN (less terse, more welcoming)

---

## Discussion title

```
Show and tell: superteam-a2a v0.1.0 — LangChain + AutoGen + CrewAI on K8s via Google A2A
```

## Discussion body

```markdown
👋 Hi all — Zach here. If you're mentally composing *"Yet another agent framework?"* — fair, this newsletter is non-empty. But here's the twist: **28ms admission webhook, Apache 2.0, zero funding rounds, and 65 PRs of pure sweat.**

Today we shipped **v0.1.0** of superteam-a2a, and I wanted to walk you through what it is, what we decided, and what I genuinely need your feedback on.

If you're not familiar: superteam-a2a is a **Kubernetes-native runtime for AI agent frameworks**. v0.1.0 ships with **LangChain, AutoGen, CrewAI** adapters — additional frameworks (Semantic Kernel / Strands / Smolagents) are spec'd in ADR-0001 and welcome via PR. Frameworks discover and call each other over the [Google A2A protocol](https://github.com/google/A2A).

It turns agents into first-class K8s resources with proper rolling updates, RBAC, observability, and admission control — the same operational story you have for stateless services today.

---

## What you get in v0.1.0

### 6 CRDs

| CRD | Purpose |
|---|---|
| `Agent` | a single AI agent wrapped in a K8s resource |
| `AgentSet` | horizontally-scalable fleet of agents with shared config |
| `Workflow` | declarative DAG of agent steps (specced, ships in v1.0 / Phase 6) |
| `KnowledgeScope` | 4-level scope (industry / org / team / project) |
| `KnowledgeItem` | a piece of knowledge with BM25-retrievable content |
| `Memory` | agent experience record with confidence + decay + reinforce |

### A2A protocol runtime

- `Agent Card` (`.well-known/agent.json`) per A2A v0.3+ spec
- `Message`, `Task`, `Artifact`, `Streaming` types
- JSON-RPC 2.0 over HTTP/SSE
- Built-in DNS-style discovery across namespaces

### Single-process knowledge + memory backend

The biggest architectural call was running Knowledge Service + Memory Service as **a single Python process** ([ADR-0006](./../adr/0006-memory-transport.md), Accepted). We considered:

- ❌ HTTP loopback between services (50ms per call, no benefit)
- ❌ Shared mmap (fragile, hard to debug)
- ❌ Two pods + Redis (eventual consistency headaches)
- ✅ **Single process** — one Deployment, one RBAC, one health check

Trade-off: ~150 MB container vs 80 MB. We think that's the right call.

### Production-grade security

- Restricted Pod Security Standards
- Non-root UID 1000, read-only root filesystem
- NetworkPolicy default-deny + explicit allow
- Dual-Role RBAC (read + write with `admissionregistration.k8s.io`)
- cert-manager mTLS (opt-in via `tls.enabled=true`)

### 25 Prometheus metrics + 8 alert rules

`MEMORY_*` counters / histograms / gauges, ServiceMonitor (30s scrape interval), PrometheusRule (8 alert conditions).

---

## How it looks to use it

```bash
helm install hello-agent oci://ghcr.io/superteam-cn/charts/hello-agent

kubectl apply -f examples/lc-code-review-agent.yaml

kubectl get agentsets
# NAME           FRAMEWORK   STATUS    DISCOVERED
# lc-review      langchain   Running   3

# Agent Card discovery (per A2A spec)
curl http://hello-agent/.well-known/agent.json | jq

# Send an A2A message via JSON-RPC 2.0
curl -X POST http://hello-agent/jsonrpc \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"message/send","params":{"message":{"role":"user","parts":[{"type":"text","text":"Review PR #42"}]}}}' | jq
```

---

## Numbers

- **474/474 tests PASS** in ~2 seconds, 0 regressions
- **65 PRs merged** since 2026-07-08 (project start · through 2026-09-03 v0.5.0 scope kickoff)
- **~30,000 lines of Python** across 8 workspace members
- **Admission latency p95 = 28ms** (well under 50ms budget)
- **Apache 2.0** — no CLA, no copyright assignment

---

## What's honest NOT in v0.1.0

I want to be upfront:

- **Framework adapters shipped in v0.1.0**: LangChain, AutoGen, CrewAI (all three wired end-to-end with reference implementations, 8 ADAPTER-UT tests, and 4 framework examples). The [adapter SDK](./../sdk/) is documented and stable — adding a new framework is 5-10 lines of glue. Adapters for **Semantic Kernel / Strands / Smolagents** are spec'd in ADR-0001 and welcome via PR.
- **Workflow CRD** is spec'd but not implemented (Phase 6 / v1.0).
- **Multi-cluster federation** is on the roadmap but not started.
- **Visual editor** for workflows is v1.0+.

The reference Hello Agent is enough to demonstrate the protocol end-to-end and to validate the architecture. But this is **not** yet "drop-in replace your agent platform."

---

## What I need your help with

I'd love feedback on these specific questions:

1. **For framework maintainers** (LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents): the adapter SDK is designed to make your integration trivial. What would you want in it that isn't there?

2. **For K8s operators**: what admission webhook latency budget actually works in your cluster? 50ms is tight — is there room for a generous default like 200ms? Or is fail-closed at <50ms actually fine?

3. **For agent fleet runners**: what's the workflow primitive you'd want first? Plain DAG? State machines? Conditional branching? Long-running suspension? Tell me what you'd reach for.

4. **For everyone**: what did we get wrong? What's missing?

---

## Get involved

- ⭐ [Star the repo](https://github.com/superteam-cn/superteam-a2a) if any of this is useful to you
- 🐛 [File an issue](https://github.com/superteam-cn/superteam-a2a/issues) — bug or feature request, both welcome
- 🤝 See [CONTRIBUTING.md](https://github.com/superteam-cn/superteam-a2a/blob/main/CONTRIBUTING.md) — especially if you maintain an agent framework
- 💬 Discuss in this thread below

A real demo.mp4 is queued — see [Issue #73](https://github.com/superteam-cn/superteam-a2a/issues/73) (waiting on a maintainer weekend block to set up kind/helm/asciinema). For now a 6-frame storyboard GIF ships in `docs/launch/demo.gif`. A Show HN post will follow on rollout Day 3 (9/10 Thu). Cross-posts to dev.to, Reddit, and 掘金 are queued across the 7-day rollout (9/8–9/14).

— Zach ([@CoderZhangfujiang](https://github.com/CoderZhangfujiang))
```

---

## Posting playbook

### Pre-post

- Enable Discussions: repo Settings → Features → Discussions ✓
- Create categories: Show and tell, Help wanted, Q&A, Announcements, General
- Pin a "Welcome" thread pointing to CONTRIBUTING.md + good-first-issue label

### Post

- Category: **Show and tell**
- Title: `Show and tell: superteam-a2a v0.1.0 — multi-framework agent orchestration on K8s`
- Body: paste the markdown above

### Engagement

- Pin the discussion in the Discussions sidebar for the first 7 days
- Reply to every comment within 30 min for the first 4 hours (Discussions algorithm punishes unattended threads)
- Mark good feedback as "Resolved" when addressed in code

### After 7 days

- Convert actionable feedback into issues
- Link to issues from the discussion
- Keep the discussion open for ongoing conversation — don't lock it

---

<sub>Maintainer action: enable Discussions, create categories, then paste the markdown body into a new thread pinned to "Show and tell".</sub>
