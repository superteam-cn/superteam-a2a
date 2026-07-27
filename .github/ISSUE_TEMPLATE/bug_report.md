---
name: 🐞 Bug report
about: Something is broken in superteam-a2a
title: "[bug] "
labels: ["bug", "needs-triage"]
assignees: []
---

## Describe the bug

A clear and concise description of what the bug is.

## To reproduce

Steps to reproduce the behavior:

```yaml
# paste your Agent / AgentSet YAML here
apiVersion: agents.superteam-a2a.dev/v1alpha1
kind: Agent
metadata:
  name: example
spec:
  ...
```

```bash
# exact commands you ran
```

## Expected behavior

What did you expect to happen?

## Actual behavior

What actually happens? (paste logs, errors, screenshots)

```text
[paste here]
```

## Environment

- superteam-a2a version: (run `superteam-a2a version`)
- Kubernetes version: (`kubectl version`)
- Agent framework + version (LangChain / AutoGen / CrewAI / etc.):
- A2A protocol version observed:
- OS:

## Anything else?

Screenshots, related issues, etc.
