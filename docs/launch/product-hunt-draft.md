# Product Hunt: superteam-a2a

> **Submission target**: <https://www.producthunt.com/posts/new> · Tue 8:00 PT (PH peak)
>
> **Status**: ⏳ pending (maintainer action)

## Tagline (≤60 chars)

```
Multi-framework AI agents on K8s via Google A2A
```

(52 chars · uses the word "K8s" once · positions against the dominant protocol reference)

## Short description (≤260 chars)

```
K8s-native runtime for AI agent frameworks via Google A2A. 6 CRDs · DNS
discovery · hierarchical knowledge + persistent memory · 50ms fail-closed
admission · 474 tests · Apache 2.0.
```

(~175 chars · bullet-style scannable · emphasizes numbers + license)

## Topics (pick from PH taxonomy)

- Open Source
- Kubernetes
- Developer Tools
- AI
- Tech

## Cover image / gallery

- Cover: <https://github.com/superteam-cn/superteam-a2a/raw/head/docs/launch/cover-ph.png> (TODO: create at 240×240)
- Gallery (3 images):
  1. Architecture diagram: AgentSet → ASGI → A2A JSON-RPC
  2. `kubectl get agentsets` terminal screenshot
  3. BM25 admission latency benchmark (p95 28ms)

## Maker comment (post immediately after submission)

```markdown
Hey Product Hunt 👋

I'm Zach (@CoderZhangfujiang), the maintainer of superteam-a2a. We just shipped **v0.1.0** — a Kubernetes-native runtime for orchestrating AI agent frameworks (LangChain, AutoGen, CrewAI, Semantic Kernel, Strands, Smolagents) via the [Google A2A protocol](https://github.com/google/A2A).

## The problem

If you've tried to run more than one AI agent in production, you've hit the same wall: frameworks are great at running **one** agent, but the moment you want a **fleet** that hands off tasks to each other (planner → researcher → coder → reviewer), you end up writing bespoke glue.

There's no standard protocol between LangChain and AutoGen. No Kubernetes story. No discovery. No observability. No admission control. No shared memory.

## What superteam-a2a gives you

- **6 Kubernetes CRDs** — `Agent`, `AgentSet`, `Workflow`, `KnowledgeScope`, `KnowledgeItem`, `Memory`
- **A2A protocol runtime** — `Agent Card` (`.well-known/agent.json`), `Message`, `Task`, `Artifact`, `Streaming`, JSON-RPC 2.0 over HTTP/SSE
- **DNS-style discovery** across namespaces and clusters
- **Hierarchical knowledge** — 4-level scope (industry / org / team / project) + BM25 inverted index
- **Persistent memory** — confidence + decay + reinforce lifecycle, 5-dimensional visibility matrix
- **50ms fail-closed admission webhook** on every record/query
- **Production-grade security** — restricted PodSecurity, non-root UID 1000, NetworkPolicy default-deny, dual-Role RBAC, opt-in cert-manager mTLS

## Numbers

- **474/474 tests PASS** (0 regressions)
- **62 PRs merged** since 2026-07-08
- **~30,000 lines of Python** across 8 workspace members
- **Admission latency p95 = 28ms** (well under 50ms budget)

## What I'd love feedback on

- **Framework maintainers** (LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents): the [adapter SDK](https://superteam-cn.github.io/superteam-a2a/sdk/) is designed to make integration trivial (5-10 lines per framework). What's missing?
- **K8s operators**: which admission webhook latency budget actually works in your cluster?
- **Anyone running agent fleets**: what's the workflow primitive you'd want first?

I'd rather get feedback now than ship a v1.0 that misses the mark.

- **Repo**: <https://github.com/superteam-cn/superteam-a2a>
- **Release notes**: <https://github.com/superteam-cn/superteam-a2a/releases/tag/v0.1.0>
- **Docs site**: <https://superteam-cn.github.io/superteam-a2a/>
- **Try it locally**: 5-minute `kind` demo in `CONTRIBUTING.md` — no cloud needed
```

## First 24h engagement plan

- **Hour 0**: post + comment
- **Hour 1**: respond to every comment within 10 min
- **Hour 2**: post a follow-up comment with the demo GIF (once recorded)
- **Hour 4**: post a follow-up comment with the BM25 benchmark output
- **Hour 8**: pin the "Try it locally" instructions as a second comment
- **Hour 24**: post a "Day 1 stats" comment (test count, install success rate, issues filed)

## What to do if ranked poorly

- Don't delete and re-post (PH punishes)
- Don't ask for upvotes in comments (against TOS)
- Do thank every commenter by name
- Do post follow-up technical comments as new discoveries happen
- If flagged: stay calm, link to facts, never argue

## Tracking

Append to submission-checklist.md → Day 0 row for Product Hunt.

---

<sub>Maintainer action: copy the tagline + description into PH submit form, paste the maker comment as the first comment immediately after submission. Cover image is the only blocking gap — schedule a 30-min screenshot session.</sub>
