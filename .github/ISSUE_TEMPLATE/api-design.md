---
name: 🧬 API design proposal
about: Influence CRD, A2A message shape, or workflow DSL before v1 lock
title: "[api] "
labels: ["api-design", "needs-discussion"]
assignees: []
---

> 📣 **This is the most valuable issue type right now.** We are pre-v0.1; the next 8 weeks decide the public API surface. Voice your preference on CRD field names, A2A message shapes, workflow DSL ergonomics, etc.

## What part of the API?

- [ ] `Agent` CRD fields
- [ ] `AgentSet` CRD fields
- [ ] A2A message envelope
- [ ] A2A agent card shape
- [ ] Workflow DSL (YAML key names)
- [ ] CLI command surface (`st-a2a …`)
- [ ] Other: `_____________________`

## Current proposal

Sketch the design you'd prefer. Sample YAML, JSON, or CLI:

```yaml
apiVersion: agents.superteam-a2a.dev/v1alpha1
kind: Agent
metadata:
  name: …
spec:
  …
```

## Alternatives considered

Sketch 1-2 alternatives.

## Tradeoffs you see

Which axis do you gain on, which do you lose on?
- Backward-compat risk:
- Cognitive load:
- Implementation cost:
- Coverage of multi-framework cases:

## Reference

Links to existing projects (LangChain, CrewAI, AutoGen, K8s idioms) that informed this.
