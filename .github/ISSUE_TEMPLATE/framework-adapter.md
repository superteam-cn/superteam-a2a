---
name: New framework adapter
about: Propose support for a new agent framework (LangChain, AutoGen, CrewAI, etc.)
title: "[adapter] "
labels: ["enhancement", "framework-adapter", "help wanted"]
assignees: []
---

## Framework

**Name** (e.g. LangChain, AutoGen, CrewAI, Semantic Kernel, Strands, Smolagents):

**Website / docs**:

**License** (MIT / Apache 2.0 / etc.):

**Python SDK package** (e.g. `langchain`, `pyautogen`, `crewai`):

## Adapter SDK coverage

Phase 5 LAUNCH (PR #62) ships `packages/adapter-sdk/` with `Adapter`, `AgentCard`, and `FrameworkAdapter` Protocols. New frameworks only need to implement these protocols.

- [ ] I've read [`packages/adapter-sdk/README.md`](../../packages/adapter-sdk/README.md)
- [ ] I'm willing to write ~50-100 lines of glue code
- [ ] I'm willing to write 5+ Golden Cases (constitutional requirement §4.7)

## Use case

Describe the agent you'd build with this framework. What problem does it solve?

## Implementation plan

```python
# Pseudo-code outline (will live in adapters/<framework>/src/supteam_a2a/adapters/<framework>/__init__.py)
from superteam_a2a.adapter import Adapter, AgentCard, FrameworkAdapter

class MyFrameworkAdapter(Adapter):
    framework_name = "myframework"
    async def invoke(self, message): ...

class MyFrameworkAgentCard(AgentCard):
    framework_name = "myframework"
    name = "..."
    description = "..."
    def to_a2a_card(self): ...
```

## Alternatives considered

What other frameworks could you have used? Why this one?

## References

- Related docs: [`docs/design/L2-modules/L2-adapter.md`](../../docs/design/L2-modules/L2-adapter.md)
- Adapter SDK: [`packages/adapter-sdk/`](../../packages/adapter-sdk/)
- Example: `examples/langchain/agentset.yaml`

---

<sub>📌 Issue tracker is the right place to scope before writing code. Once we agree on the approach, open a PR linking this issue.</sub>