# Reddit r/Python: superteam-a2a v0.1.0

> **Submission target**: <https://www.reddit.com/r/Python/submit?type=TEXT>
>
> **Status**: ⏳ pending (maintainer action)
>
> **Format**: text post · no emoji in title · Python-ecosystem framing (uv, kopf, Pydantic, Starlette, asyncio)

---

## Title

```
Show & Tell: superteam-a2a — async-first Python runtime for orchestrating LangChain/AutoGen/CrewAI agents via K8s + Google's A2A protocol
```

(~160 chars · Python-first keywords · A2A protocol anchor)

## Body

```
**TL;DR**: A Python 3.12 project that runs LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents as Kubernetes resources, with an async A2A JSON-RPC 2.0 protocol between them. 474 tests, Pydantic v2, kopf, Starlette ASGI, uv workspace, Apache 2.0.

---

Hi r/Python,

I shipped v0.1.0 of superteam-a2a this week — a runtime for orchestrating AI agents from multiple frameworks inside a Kubernetes cluster. It's mostly an excuse to use a few Python libraries I'm excited about together:

- **uv** workspaces (8 members, `uv sync --all-packages --all-extras` in <10s)
- **Pydantic v2.13.4** for CRD schemas (with `populate_by_name` to keep camelCase K8s field names + snake_case Python attrs)
- **kopf 1.44.6** for the operator reconcilers
- **Starlette ASGI + uvicorn** for the A2A JSON-RPC endpoints
- **pytest + pytest-xdist** (474 tests in ~2 seconds)
- **pyright** strict mode (0 errors)
- **ruff** for lint + format

## The async story

The A2A message handlers are async-first throughout. A `message/send` request goes through:

```python
async def handle_message_send(request: MessageSendRequest) -> Task:
    async with admission_validator.fail_closed_50ms():  # Pydantic + kopf + mutex
        task = await task_service.create_task(
            message=request.message,
            agent_card=await agent_card_resolver.resolve(request.target_agent),
        )
        await task_service.dispatch(task)  # SSE streaming
        return task
```

The admission validator is the part I'm proudest of: it's a 50ms fail-closed guard that runs Pydantic validation + kopf admission handler + mutex check + visibility matrix check on every record/query. Predictable latency under load.

## The CRD model

You define an agent with Pydantic:

```python
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

Then deploy it via Helm, and it shows up in `kubectl get agentsets`.

## The single-process decision

The Knowledge Service and Memory Service run in a single Python process ([ADR-0006](https://github.com/superteam-cn/superteam-a2a/blob/main/docs/adr/0006-memory-transport.md)) — one kopf operator + one Starlette ASGI app + one process. I considered and rejected:

- HTTP loopback (50ms per call)
- Shared mmap (fragile)
- Two pods + Redis (eventual consistency)

Single process = single Deployment, single RBAC, single health check. Trade-off: ~150 MB container. Worth it.

## The numbers

- **474/474 tests PASS** in ~2 seconds
- **62 PRs merged** since 2026-07-08
- **~30,000 lines of Python** across 8 workspace members
- **Apache 2.0**
- Runs entirely on local `kind` cluster

## What's NOT done

Honest list:

- **Framework adapters** — only the Hello Agent (reference) ships in v0.1.0. LangChain / AutoGen / CrewAI adapters are specced but not implemented.
- **Workflow CRD** (declarative DAG) — specced but not implemented (v1.0).
- **Multi-cluster federation** — on the roadmap.

## Try it

```bash
git clone https://github.com/superteam-cn/superteam-a2a
cd superteam-a2a
uv sync --all-packages --all-extras
uv run pytest  # 474 tests in ~2s
```

## What I want feedback on

- **Pydantic v2 users**: any patterns you'd push back on? I'm using `populate_by_name` + `extra=forbid` + `@model_validator(mode="after")` heavily.
- **Async Python folks**: any libraries I'm missing? (asyncio, anyio, httpx, structlog, pydantic-settings — all in use)
- **Type-checking folks**: pyright strict mode is on, 0 errors. Any patterns that should be reconsidered?
- **uv workspace users**: 8 members, working well. Any gotchas?
- **Operator framework folks**: kopf vs operator-sdk vs kubebuilder — opinions on the Python operator ecosystem?

Repo: https://github.com/superteam-cn/superteam-a2a

— Zach
```

## Posting playbook

### Pre-post

- r/Python allows Show & Tell — verify current rules
- Avoid Tuesday peak (competes with r/programming Show & Tell) — try Wednesday or Thursday 10:00 ET
- Pre-write helpful Python comments in adjacent subs (build karma)

### Post

- Title: paste above (no emoji)
- Body: paste above
- Flair: **Show & Tell** if available, else **Project**

### Engagement

- r/Python audience is technical and skeptical in a good way
- "Why not just use LangChain's built-in agent orchestration?" is the obvious pushback — have a concrete answer ready
- Async + Pydantic + kopf questions will come up — be ready
- Reply within 10 min for first 2 hours

### What to avoid

- Don't post the same day as r/programming (looks like karma farming)
- Don't link to Show HN or Product Hunt in the post
- Don't edit the post body after submission

---

<sub>Maintainer action: post Thursday 10:00 ET, engage for 4 hours, follow up on Pydantic / async / kopf questions concretely.</sub>
