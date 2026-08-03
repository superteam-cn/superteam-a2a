---
name: Bug Report
about: Report incorrect behavior, crashes, or unexpected output
title: '[bug] '
labels: bug
assignees: ''
---

## Bug 描述

<!-- 清楚描述 bug：现象 + 触发条件 + 影响范围。 -->

## 复现步骤

1.
2.
3.

## 期望 vs 实际

**期望**：

**实际**：

## 环境

<!-- 请运行以下命令并粘贴输出。 -->

| 项        | 值           |
|-----------|--------------|
| OS        |              |
| Python    | `python --version` → |
| uv        | `uv --version` → |
| commit SHA| `git rev-parse HEAD` → |
| branch    | `git branch --show-current` → |

## 关联 Spec 段落

<!-- 本 bug 涉及哪个 L1 / L2 / L3 spec 段落？引用具体行号。 -->
- L1-system-spec.md §X.Y
- L2-module-specs/L2-*.md §X.Y
- L3-file-specs/L3-*.md §X.Y

## L4 Component

<!-- 涉及哪个 L4 实施层包？多选用 `,` 分隔。 -->
- [ ] `packages/operator`
- [ ] `packages/a2a-core`
- [ ] `packages/adapter-sdk`
- [ ] `packages/knowledge-memory`
- [ ] `agents/hello`
- [ ] `services/knowledge-memory-service`
- [ ] `helm/`
- [ ] `docs/`
- [ ] CI / GitHub workflows

## 错误码（若适用）

<!-- 若报错包含 MEMORY_* / KNOWLEDGE_* / OPERATOR_* 错误码，请贴出。 -->
```
错误码: -32XXX
message:
```

## 日志 / 截图

```
<paste logs here>
```

## 备注

<!-- 任何额外上下文：是否可重现（always / sometimes / once）/ 临时绕过方案 / 相关 issue 链接。 -->
