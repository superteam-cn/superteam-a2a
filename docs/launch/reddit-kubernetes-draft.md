Title: Show & Tell: superteam-a2a — multi-framework agent orchestration on K8s via Google A2A protocol

Body:

**TL;DR**: Kubernetes-native runtime for AI agent frameworks (LangChain, AutoGen, CrewAI, etc.) that lets them discover and call each other over the Google A2A protocol. 6 CRDs, 466 tests, single-process knowledge+memory backend, 50ms fail-closed admission. Apache 2.0.

Hey r/kubernetes,

I've been building **superteam-a2a** for 6 weeks — it's a Kubernetes operator + CRDs that turns LangChain/AutoGen/CrewAI agents into first-class K8s resources, with A2A protocol-based discovery and communication between agents.

## The problem I was solving

Every agent framework is great at running **one** agent, but if you want a fleet of agents that hand off tasks to each other (planner → researcher, coder → reviewer), you hit:

- No standard protocol between frameworks (LangChain can't talk to AutoGen)
- No Kubernetes story (deploy agents as what? Deployments? StatefulSets?)
- No discovery (how does agent A know agent B exists?)
- No observability (which agent is slow? which is failing?)
- No admission control (what if a malicious agent tries to read scope "production"?)
- No shared memory (every agent keeps its own context)

## What it does

6 CRDs (`Agent`, `AgentSet`, `Workflow`, `KnowledgeScope`, `KnowledgeItem`, `Memory`) backed by a `kopf` operator. Agents publish `.well-known/agent.json` per the A2A spec, and a built-in DNS-style resolver maps logical names → cluster IPs.

Cross-cutting concerns are real K8s primitives:
- **RBAC**: dual Role (read + write with admissionregistration.k8s.io/authentication.k8s.io/authorization.k8s.io)
- **NetworkPolicy**: default-deny + explicit allow
- **ServiceMonitor**: 25 Prometheus metrics + 8 alert rules
- **PodSecurity**: restricted profile, non-root UID 1000, read-only root filesystem
- **cert-manager**: opt-in mTLS for the webhook

The admission webhook enforces **50ms fail-closed** on every record/query — predictable latency under load.

## Architectural choice: single-process

The biggest decision was running **Knowledge Service + Memory Service as a single Python process** (ADR-0006 v1.0 D 方案). I considered:

- HTTP loopback between services — adds latency
- Shared mmap — fragile
- Two pods with Redis — eventual consistency headaches

Single process = single Deployment, single RBAC, single health check, single leader election (when needed). Trade-off: ~150 MB container vs 80 MB. Worth it.

## What it looks like

```bash
helm install hello-agent oci://ghcr.io/superteam-cn/charts/hello-agent
kubectl apply -f examples/lc-code-review-agent.yaml
kubectl get agentsets
# NAME           FRAMEWORK   STATUS    DISCOVERED
# lc-review      langchain   Running   3

# Send an A2A message via JSON-RPC 2.0
curl -X POST http://hello-agent/jsonrpc -d '{"jsonrpc":"2.0","id":1,"method":"message/send","params":{"message":{"role":"user","parts":[{"type":"text","text":"Review PR #42"}]}}}'
```

## Numbers

- **466/466 tests PASS** (2 seconds locally)
- **62 PRs merged** since 2026-07-08
- **8/8 Phase 4 PRs shipped** in v0.1.0 (2026-08-16)
- All under Apache 2.0
- Single binary, no external dependencies (besides Prometheus/cert-manager if you opt in)

## What's NOT done

- Framework adapters (only Hello Agent reference ships in v0.1.0; LangChain/AutoGen/CrewAI in progress)
- Workflow CRD (Phase 6 / v1.0)
- Multi-cluster federation (roadmap)

## Try it

- **Repo**: https://github.com/superteam-cn/superteam-a2a
- **466 tests, 100% local, no cloud**: `uv sync && uv run pytest`
- **5-min kind demo**: see CONTRIBUTING.md
- **Issues welcome**: https://github.com/superteam-cn/superteam-a2a/issues

Looking for feedback from anyone running K8s + AI agents in production. What's your admission webhook latency budget? Which framework adapters matter most?