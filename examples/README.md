# Examples

Sample `AgentSet` and other CRD manifests for **superteam-a2a**. These are runnable in any Kubernetes cluster (or `kind`) that has the superteam-a2a operator installed.

## What's here

| Folder | Framework | What it does |
|---|---|---|
| [`hello/`](./hello/) | Hello (reference) | Minimal agent. Echoes back user messages. Used for testing A2A protocol. |
| [`langchain/`](./langchain/) | LangChain | PR review agent using LangChain ReAct pattern. |
| [`autogen/`](./autogen/) | AutoGen | Multi-agent group chat (user_proxy + coder + reviewer). |
| [`crewai/`](./crewai/) | CrewAI | Sequential research crew (researcher + writer + editor). |

## Prerequisites

1. A Kubernetes cluster (use `kind create cluster` for local dev).
2. The superteam-a2a operator installed (see [helm/](../../helm/)).
3. The framework image built and loaded (`docker buildx build` + `kind load docker-image`).
4. For frameworks that need API keys, create the corresponding Secret.

## Quick start

```bash
# Hello Agent — no API keys needed
kubectl apply -f examples/hello/agentset.yaml

# LangChain — needs OPENAI_API_KEY
kubectl create secret generic langchain-code-review-secret \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=GITHUB_TOKEN=ghp_...
kubectl apply -f examples/langchain/agentset.yaml

# AutoGen — needs OPENAI_API_KEY
kubectl create secret generic autogen-chat-secret \
  --from-literal=OPENAI_API_KEY=sk-...
kubectl apply -f examples/autogen/agentset.yaml

# CrewAI — needs OPENAI_API_KEY + SERPER_API_KEY
kubectl create secret generic crewai-research-secret \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=SERPER_API_KEY=...
kubectl apply -f examples/crewai/agentset.yaml

# Verify
kubectl get agentsets
kubectl port-forward svc/hello-agent 8080:8080 &
curl http://localhost:8080/.well-known/agent.json | jq
```

## Verification: send an A2A message

```bash
# Hello Agent
curl -X POST http://localhost:8080/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "Hello!"}]
      }
    }
  }'

# Expected response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "role": "agent",
    "parts": [{"type": "text", "text": "Hello from superteam-a2a · received: Hello!"}]
  }
}
```

## Conventions

- All examples use the default namespace.
- Image tags use `:0.1.0` matching the v0.1.0 release.
- All examples enable Knowledge integration with the same 4-level scope.
- All examples use restricted Pod Security Standards (non-root, read-only root filesystem).

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full development workflow.