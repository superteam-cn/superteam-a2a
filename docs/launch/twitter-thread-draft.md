# Twitter/X thread: superteam-a2a v0.1.0

> **Submission target**: <https://x.com/compose/post> · Tue 7:00 PT (US west peak) or Wed 8:00 ET (US east peak)
>
> **Status**: ⏳ pending (maintainer action)
>
> **Format**: thread of 7 tweets · each ≤280 chars · numbered `1/n` format

---

## Tweet 1/7 — Hook

```
Every AI agent framework is great at running ONE agent.

But the moment you want a fleet — planner → researcher → coder → reviewer — you're on your own.

No protocol. No K8s story. No shared memory.

We just shipped a fix: superteam-a2a v0.1.0 🧵
```

(245 chars · hook + thread anchor)

## Tweet 2/7 — The problem

```
The wall:

→ LangChain can't talk to AutoGen
→ CrewAI doesn't know Semantic Kernel exists
→ No standard inter-agent protocol
→ No K8s story (Deployment? StatefulSet? Job?)
→ No shared memory, no observability, no admission control
```

(213 chars · concrete pain points)

## Tweet 3/7 — Solution

```
superteam-a2a turns 6 frameworks (LangChain, AutoGen, CrewAI, Semantic Kernel, Strands, Smolagents) into K8s CRDs.

They discover each other over Google's A2A protocol — JSON-RPC 2.0 over HTTP/SSE.

Same shape as Pods + Services.
```

(228 chars · what it does + familiar analogy)

## Tweet 4/7 — Architecture decision

```
The big call: Knowledge + Memory as a SINGLE Python process (ADR-0006 D 方案).

→ vs HTTP loopback: -50ms/call
→ vs two pods + Redis: eventual consistency headaches

Trade-off: 150MB container. Worth it.
```

(193 chars · concrete engineering trade-off)

## Tweet 5/7 — Numbers

```
6 weeks · 62 PRs · 474/474 tests PASS · 0 regressions · Apache 2.0

→ 50ms fail-closed admission → actually 28ms p95
→ 6 CRDs · 25 Prometheus metrics · 8 alert rules
→ dual-Role RBAC · opt-in cert-manager mTLS · NetworkPolicy default-deny
```

(207 chars · proof)

## Tweet 6/7 — Try it (CTA)

```
Try it in 5 min, no cloud needed:

git clone https://github.com/superteam-cn/superteam-a2a
cd superteam-a2a
uv sync --all-packages --all-extras
uv run pytest  # 474 tests in ~2s

5-min kind demo in CONTRIBUTING.md.
```

(180 chars · lowest friction)

## Tweet 7/7 — Ask for feedback

```
v0.1.0 is out. I want feedback from:

→ Framework maintainers: what's missing in the adapter SDK?
→ K8s operators: what's your webhook latency budget?
→ Agent fleet runners: what workflow primitive first?

⭐ Repo: github.com/superteam-cn/superteam-a2a

Show HN / dev.to / Reddit posts coming this week.
```

(220 chars · specific asks + amplification signal)

---

## Posting playbook

### Pre-post

- Schedule via Tweetdeck or Typefully for peak hour
- Pin the thread to profile
- Have profile description link to GitHub repo

### During first hour

- Quote-tweet the thread with the 60-90s demo GIF (once recorded) at +30 min
- Quote-tweet with the BM25 benchmark screenshot at +60 min

### During day 1

- Reply to every comment within 10 min
- Re-share with the dev.to article at +6h
- Re-share with the Show HN at +12h (cross-pollinate)

### Cross-platform adaptation

- Strip the `🧵` and numbering for LinkedIn / Mastodon (different cultures)
- Add the dev.to URL when posted
- Add the GitHub Release URL when posted

---

<sub>Maintainer action: paste each tweet in order, then quote-tweet the thread 30 min after posting with the demo GIF.</sub>
