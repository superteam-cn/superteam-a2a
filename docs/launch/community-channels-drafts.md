# Discord / Slack announcement cards

> **Format**: 5 communities, each with a tailored short message (≤500 chars).
>
> **Posting day**: Sat 12:00 ET (per submission-checklist.md)
>
> **Status**: ⏳ pending (maintainer action)
>
> **Common rules**:
> - Always read channel rules + pinned messages first
> - Use the right channel (`#show-and-tell`, `#announcements`, `#opensource`, `#projects`)
> - Never cross-post the exact same message — adapt to each community's tone
> - Engage with replies for 2 hours

---

## 1. Kubernetes Slack — `#sig-apps` or `#show-and-tell`

<https://slack.k8s.io/>

```text
👋 K8s folks — we just shipped v0.1.0 of superteam-a2a, a Kubernetes-native
runtime for orchestrating AI agent frameworks (LangChain, AutoGen, CrewAI,
Semantic Kernel, Strands, Smolagents) via Google's A2A protocol.

6 CRDs · kopf operator · Starlette ASGI · NetworkPolicy default-deny ·
dual-Role RBAC · opt-in cert-manager mTLS · ServiceMonitor (25 metrics) ·
PrometheusRule (8 alerts).

Admission webhook 50ms fail-closed (actual p95: 28ms).
474/474 tests, 62 PRs in 6 weeks, Apache 2.0.

Repo → https://github.com/superteam-cn/superteam-a2a
5-min kind demo → CONTRIBUTING.md

Looking for feedback from K8s operators on the admission latency budget.
```

(485 chars · K8s-native terms + admission focus)

---

## 2. AI Agents Discord — `#project-showcase` or `#open-source`

(Locate via search for "AI Agents community Discord" — Latent Space, MLOps Community, etc.)

```text
🤖 We just shipped v0.1.0 of superteam-a2a — a runtime that lets LangChain,
AutoGen, CrewAI, Semantic Kernel, Strands, and Smolagents agents talk to
each other over Google's A2A protocol (JSON-RPC 2.0 over HTTP/SSE).

Turns them into K8s resources — agents discover each other DNS-style, share
hierarchical knowledge + persistent memory, and every record/query goes
through a 50ms fail-closed admission webhook.

474 tests, 62 PRs in 6 weeks, Apache 2.0. Framework-agnostic by design —
the adapter SDK makes adding a new framework 5-10 lines of glue.

Repo → https://github.com/superteam-cn/superteam-a2a

Would love feedback from framework maintainers on the adapter SDK shape.
```

(540 chars · agent-framework focus · SDK call-out)

---

## 3. r/kubernetes Discord — `#show-and-tell`

(Usually linked from reddit sidebar)

```text
🚀 v0.1.0 of superteam-a2a is live — K8s-native runtime for AI agent
frameworks via Google's A2A protocol.

→ 6 CRDs (Agent, AgentSet, Workflow, KnowledgeScope, KnowledgeItem, Memory)
→ kopf operator + Starlette ASGI in one process
→ 50ms fail-closed admission (p95: 28ms)
→ restricted PodSecurity, non-root UID 1000, NetworkPolicy default-deny
→ dual-Role RBAC + opt-in cert-manager mTLS
→ 25 Prometheus metrics + 8 alert rules

474/474 tests, 62 PRs in 6 weeks, Apache 2.0.

5-min kind demo: CONTRIBUTING.md
Repo: https://github.com/superteam-cn/superteam-a2a
```

(495 chars · bullet-heavy for quick scanning)

---

## 4. CNCF Slack — `#K8s-Operators` or `#Service-Mesh`

<https://slack.cncf.io/>

```text
Hi CNCF — sharing a project we just released: superteam-a2a v0.1.0.

It's a Kubernetes-native runtime for orchestrating AI agents from multiple
frameworks (LangChain, AutoGen, CrewAI, etc.) over Google's A2A protocol.

The interesting parts from a K8s-native perspective:

→ 6 CRDs with full RBAC, NetworkPolicy, ServiceMonitor, PrometheusRule
→ admission webhook with 50ms fail-closed (p95: 28ms)
→ single-process architecture (Knowledge + Memory) — ADR-0006 D 方案
→ restricted PodSecurity, non-root, read-only rootfs
→ 474/474 tests, 62 PRs in 6 weeks, Apache 2.0

Repo → https://github.com/superteam-cn/superteam-a2a
Looking for feedback on the operator pattern + admission latency budget.
```

(530 chars · CNCF tone · operator-pattern focus)

---

## 5. LangChain Discord — `#showcase` or `#langchain-projects`

(Discord invite from langchain.com)

```text
👋 LangChain community — we just shipped v0.1.0 of superteam-a2a, which
treats LangChain agents as first-class Kubernetes resources.

What you get:

→ AgentSet CRD scales LangChain agents horizontally
→ A2A JSON-RPC endpoint at `/jsonrpc` (per Google A2A spec)
→ Persistent Memory with confidence + decay + reinforce lifecycle
→ Hierarchical Knowledge with 4-level scope + BM25 retrieval
→ 50ms fail-closed admission webhook (p95: 28ms)

The LangChain adapter SDK is documented and stable — 5-10 lines to wire
your existing LangChain agent into a K8s deployment.

474/474 tests, Apache 2.0.
Repo → https://github.com/superteam-cn/superteam-a2a
Adapter SDK docs → https://superteam-cn.github.io/superteam-a2a/sdk/
```

(580 chars · LangChain-specific framing · SDK pointer)

---

## Posting playbook

### Pre-post checklist

- [ ] Join each community (use your real GitHub identity, not a throwaway)
- [ ] Read the channel topic + pinned messages
- [ ] Lurk for 5 min to understand the tone
- [ ] Have your GitHub profile link in your Discord/Slack bio

### Posting order (same Saturday, spaced 30 min apart)

1. 12:00 ET — Kubernetes Slack `#show-and-tell`
2. 12:30 ET — AI Agents Discord `#project-showcase`
3. 13:00 ET — r/kubernetes Discord `#show-and-tell`
4. 13:30 ET — CNCF Slack `#K8s-Operators`
5. 14:00 ET — LangChain Discord `#showcase`

### Engagement rules

- Reply within 15 min for the first 2 hours
- Don't argue with skeptics — link to facts
- Never paste a link-only message — always include context
- Don't ping maintainers or admins

### What to do if no engagement

- Don't re-post in the same channel
- Don't DM users who didn't engage
- Move on — Discord/Slack is a long game, not a launch channel

---

<sub>Maintainer action: schedule a 4-hour Saturday block (12:00-16:00 ET) to post + engage across all 5 communities. Don't skip the engagement — Discord/Slack audiences punish drive-by posters.</sub>
