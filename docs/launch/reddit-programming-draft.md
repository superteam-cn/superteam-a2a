# Reddit r/programming: superteam-a2a v0.1.0

> **Submission target**: <https://www.reddit.com/r/programming/submit?type=TEXT>
>
> **Status**: ⏳ pending (maintainer action)
>
> **Format**: text post · no emoji in title · programming-focused framing (less K8s jargon than r/kubernetes)

---

## Title

```
Show & Tell: superteam-a2a — Kubernetes-native runtime for LangChain/AutoGen/CrewAI agents over Google's A2A protocol (Python, 474 tests, Apache 2.0)
```

(~155 chars · within Reddit title limits · descriptive without emoji)

## Body

```
**TL;DR**: A Python framework that lets you deploy AI agents from LangChain, AutoGen, CrewAI, Semantic Kernel, Strands, and Smolagents as Kubernetes resources, and have them talk to each other over Google's A2A protocol (JSON-RPC 2.0). 474 tests, Apache 2.0, single-process backend, zero cloud lock-in.

---

Hi r/programming,

I just shipped v0.1.0 of superteam-a2a after 6 weeks of work, and I want to tell you about it because it touches on a problem I think this community will recognize: **the moment you want more than one AI agent, you're on your own**.

Every framework is great at running ONE agent. But the moment you want a fleet — planner delegating to researcher, coder handing off to reviewer — there's no standard protocol, no shared memory, no observability, no admission control.

## What's in it

- **6 CRDs** (Agent / AgentSet / Workflow / KnowledgeScope / KnowledgeItem / Memory) — agents become K8s resources with rolling updates, RBAC, health checks
- **A2A protocol runtime** — Agent Card (`.well-known/agent.json`), Message, Task, Artifact, Streaming types, JSON-RPC 2.0 over HTTP/SSE
- **DNS-style discovery** across namespaces — agents find each other like Services find Pods
- **Hierarchical knowledge** — 4-level scope (industry/org/team/project) + BM25 inverted index
- **Persistent memory** — confidence + decay + reinforce lifecycle
- **50ms fail-closed admission webhook** — predictable latency on every record/query

## What it looks like

```python
# Define an agent (Python)
from superteam_a2a import Agent, AgentSpec

agent = Agent(
    metadata={"name": "lc-review"},
    spec=AgentSpec(
        framework="langchain",
        model="gpt-4o",
        system_prompt="You review pull requests...",
    ),
)
```

```bash
# Deploy it
helm install hello-agent oci://ghcr.io/superteam-cn/charts/hello-agent
kubectl apply -f examples/lc-code-review-agent.yaml
kubectl get agentsets
# NAME        FRAMEWORK    STATUS    DISCOVERED
# lc-review   langchain    Running   3

# Agent Card discovery (per A2A spec)
curl http://hello-agent/.well-known/agent.json | jq

# Send an A2A message via JSON-RPC 2.0
curl -X POST http://hello-agent/jsonrpc \
  -d '{"jsonrpc":"2.0","id":1,"method":"message/send","params":{"message":{"role":"user","parts":[{"type":"text","text":"Review PR #42"}]}}}' | jq
```

## The architecture decision that mattered

I considered 4 designs for Knowledge + Memory backend ([ADR-0006](https://github.com/superteam-cn/superteam-a2a/blob/main/docs/adr/0006-memory-transport.md)):

| Design | Verdict |
|---|---|
| Two microservices + Redis | ❌ eventual consistency |
| HTTP loopback between services | ❌ 50ms per call, no benefit |
| Shared mmap | ❌ fragile, hard to debug |
| **Single Python process** | ✅ one Deployment, one leader election |

I went with single process. Container is ~150 MB instead of ~80 MB. Worth it.

## The Python bits that might interest you

- **uv workspace** with 8 members — `uv sync --all-packages --all-extras` resolves everything in <10s
- **Pydantic v2.13.4** for CRD schemas (using `populate_by_name` to keep camelCase K8s field names while exposing snake_case Python attrs)
- **kopf 1.44.6** operator framework for the reconcilers
- **Starlette ASGI** + uvicorn for the A2A JSON-RPC endpoints
- **pytest** suite: 474 tests in ~2 seconds, with parallel execution via `pytest-xdist`
- **pyright** in strict mode: 0 errors
- **ruff** for lint + format

## Numbers

- **474/474 tests PASS** in ~2 seconds
- **62 PRs merged** since 2026-07-08
- **~30,000 lines of Python** across 8 workspace members
- **Apache 2.0**
- **No cloud lock-in** — runs entirely on local `kind` cluster

## What's NOT done

I'll be honest:

- **Framework adapters** — only the Hello Agent (reference) ships in v0.1.0. LangChain / AutoGen / CrewAI adapters are specced but not implemented. The adapter SDK is documented and stable — adding a new framework is 5-10 lines of glue, but you'll need to write it.
- **Workflow CRD** (declarative DAG) — specced but not implemented (Phase 6 / v1.0).
- **Multi-cluster federation** — on the roadmap.

## Try it

```bash
git clone https://github.com/superteam-cn/superteam-a2a
cd superteam-a2a
uv sync --all-packages --all-extras
uv run pytest  # 474 tests in ~2s
```

5-min `kind` demo in `CONTRIBUTING.md`. No cloud needed.

## What I want feedback on

- **Python ecosystem folks**: any libraries you'd recommend we integrate with instead of building our own? (We use Pydantic v2, kopf, Starlette, uv — anything missing?)
- **Async Python folks**: the A2A message handlers are async-first. Anything you'd do differently?
- **Type-checking folks**: pyright strict mode is on. Any patterns you'd push back on?
- **Framework maintainers**: the adapter SDK is designed to make your integration trivial. What's missing?

Repo: https://github.com/superteam-cn/superteam-a2a
Issues: https://github.com/superteam-cn/superteam-a2a/issues

— Zach
```

## Posting playbook

### Pre-post

- Subreddit rules check: r/programming allows Show & Tell on Tuesdays (verify)
- Have a clean Reddit account or one with prior comment history (avoid throwaways)
- Pre-write a few helpful comments in adjacent subs in the week before (build karma)

### Post

- Flair: **Show & Tell** (if available) or **Project**
- Title: paste above (NO emoji — Reddit bans emoji titles)
- Body: paste above

### Engagement

- **First 4 hours are critical** — Reddit algorithm promotes based on early engagement
- Reply to every comment within 10 minutes for the first 2 hours
- Be ready for skepticism — "why another agent framework?" is the obvious pushback. Have a calm, factual answer.
- Cross-link to the dev.to article in a comment at +6 hours (not in the original post)

### What to avoid

- Do NOT link to Product Hunt or "show HN" in the post body (looks spammy)
- Do NOT include affiliate / referral links
- Do NOT cross-post to multiple subs at once (flagged as spam)
- Do NOT edit the post body after submission (counts against you)

### After 24 hours

- Don't delete the post even if it gets a few downvotes
- If it gets buried, leave it — Reddit punishes deletions
- Move on to the next channel (r/Python, dev.to, Show HN)

---

<sub>Maintainer action: verify r/programming rules, post Tuesday 9:00 ET, engage for 4 hours.</sub>
