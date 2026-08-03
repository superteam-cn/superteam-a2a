---
name: Spec Deviation
about: Report a gap between an L1/L2/L3 spec and actual implementation behavior (spec-driven project)
title: '[spec-deviation] '
labels: spec, bug
assignees: ''
---

> **本项目为 spec-driven**：所有实现必须遵循 L1-system-spec / L2-module-specs / L3-file-specs 三层 Spec。
> 如发现实现行为与 Spec 描述不符，请用本模板而非普通 bug 模板。
> 严重偏差将先于新功能处理（**不变量优先级**）。

## Spec 引用（必填）

<!-- 精确到段落 / 行号。 -->
- **Spec 文档**：`docs/spec/<L1|L2|L3>/<file>.md` §X.Y（line ZZ-ZZ）
- **关联 ADR**：`docs/adr/000X-<name>.md §X.Y`（如有）
- **关联宪法**：`docs/constitution/CONSTITUTION.md §X.Y`（如有）

## 当前实现行为

<!-- 实际观察到的实现行为（与 Spec 不一致）。 -->

```
<paste observed behavior — log / kubectl output / pytest output>
```

## Spec 要求行为

<!-- 从 Spec 原文中摘录相关段落。 -->

```markdown
> [paste spec quote here]
> — docs/spec/LX-*/<file>.md §X.Y
```

## 证据

### 复现命令

```bash
# 最小复现命令序列
```

### 测试 / 日志

```
<paste pytest output or kubectl logs>
```

### 错误码 / 事件（若适用）

```
错误码: -32XXX
EventReason: <reason>
```

## 提议 fix

<!-- 至少勾选一个方向。 -->
- [ ] 修改实现以符合 Spec
- [ ] 修改 Spec 以反映实现（需提交 ADR 或 Spec revision + 评审）
- [ ] 双修：实现 + Spec 同步（需评审 10 维度 + §A-§P）

### fix 涉及面

- [ ] 1 个文件（局部）
- [ ] 1 个 L3 段落
- [ ] 跨多个 L3 Spec
- [ ] 需新增 ADR
- [ ] 需新增 OPEN-XXX-XXX

## 不变量影响

- [ ] wire contract（API/CRD schema）
- [ ] 12 MEMORY_* 错误码（与 L2-4 v0.2.0 §9.1 权威名）
- [ ] 单进程架构（ADR-0006 D 方案）
- [ ] uv workspace 结构
- [ ] 其它：____________

## 备注

<!-- 相关 issue / spec 评审 / 历史 commit。 -->
