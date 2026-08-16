Title: Building a Kubernetes-native agent platform: lessons from shipping v0.1.0 in 6 weeks

Body:

How we built **superteam-a2a** — a Kubernetes operator + 6 CRDs for orchestrating AI agent frameworks (LangChain, AutoGen, CrewAI, etc.) via the Google A2A protocol.

## Why this project exists

If you've tried to run more than one AI agent in production, you've hit the same wall: frameworks are great at running **one** agent, but the moment you want a fleet that hands off tasks to each other (planner → coder → reviewer), you end up writing bespoke glue.

There's no standard protocol between frameworks. No Kubernetes story. No discovery. No observability. No admission control. No shared memory.

**superteam-a2a** is our attempt to fill that gap.

## What it is

A Kubernetes-native runtime that:

- Turns agents into CRDs (`Agent`, `AgentSet`, `Workflow`, `KnowledgeScope`, `KnowledgeItem`, `Memory`)
- Uses Google's A2A protocol (`Agent Card`, `Message`, `Task`, `Artifact`, `Streaming`) for inter-agent communication
- Provides built-in discovery (DNS-style resolution across namespaces)
- Adds hierarchical knowledge (4-level scope + BM25 inverted index)
- Adds persistent memory (confidence + decay + reinforce lifecycle)
- Enforces 50ms fail-closed admission webhook on every record/query
- Ships with Prometheus metrics (25 indicators) + ServiceMonitor + 8 alert rules

## The architectural choice that mattered most: single-process

The biggest decision was **running Knowledge Service + Memory Service as a single Python process** (ADR-0006 v1.0 D 方案).

I considered and rejected:

- **HTTP loopback** — adds 50ms per call for no architectural benefit
- **Shared mmap** — fragile, hard to debug
- **Two pods with separate Redis** — extra moving parts, eventual consistency

Single-process means: one Deployment, one RBAC, one health check, one leader election (when needed), one Prometheus job. The trade-off: ~150 MB container vs 80 MB. We think that's the right call.

## What surprised me

### 1. The admission webhook latency budget

I assumed 50ms fail-closed was generous. It is actually tight in production:

- Pydantic v2 validation: ~5ms
- kopf admission handler invocation: ~10ms
- Network round-trip to k8s API: ~5-15ms
- Mutex check + visibility matrix: ~3ms
- Total: ~25-35ms in the happy path

50ms gives us ~15ms headroom for spikes. We measure this in E2E tests with artificial latency injection.

### 2. The Windows filesystem gotchas

If you develop on Windows + WSL2 + a kind cluster, you will lose hours to NTFS path normalization. `C:\path\to\repo` and `/mnt/c/path/to/repo` are NOT the same path to Python's import system. Use `os.path.realpath()` religiously, and add a `pre-commit` hook that fails on backslash paths.

### 3. The "typo path shadow directory" problem

We had a Subagent write 60 files to `services/foo/supteam_a2a/...` (missing the "er") instead of `services/foo/superteam_a2a/...`. Windows bash happily created both directories. The typo paths made it into git index (60 entries). It took a full day to diagnose because everything "looked fine" — `git status` showed the correct paths, but `pytest` couldn't find any of them.

Lesson: **never use a Subagent to write files via relative paths. Always pass absolute paths, and verify with `git ls-files` before committing.**

## What is NOT done (v0.1.0 → v1.0)

- **Framework adapters**: only the Hello Agent reference ships in v0.1.0. LangChain/AutoGen/CrewAI adapters are specced but not implemented. The adapter SDK makes it 5-10 lines per framework.
- **Workflow CRD**: declarative DAG is specced but not built.
- **Multi-cluster federation**: roadmap.

## Try it

```bash
git clone https://github.com/superteam-cn/superteam-a2a
cd superteam-a2a
uv sync --all-packages --all-extras
uv run pytest   # 466 tests in ~2s
```

## Get involved

- **Issues**: https://github.com/superteam-cn/superteam-a2a/issues
- **CONTRIBUTING.md**: full setup, kind demo, 4-gate CI checklist
- **Discord**: (coming soon — for now, use issues)

If you are running agent fleets in production, I want to hear about your admission webhook latency budget. And if you maintain LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents, the adapter SDK is designed to make integration trivial — tell me what you would want.