---
name: Feature Request
about: Propose a new CRD, A2A method, framework adapter, or operator capability
title: '[feature] '
labels: feature
assignees: ''
---

## 功能描述

<!-- 一段话讲清楚要加什么、解决什么问题。 -->

## 动机 / 用户故事

**As a** `<role>`
**I want** `<capability>`
**so that** `<value>`

## 提议方案

<!-- 详细描述你建议的实现：CRD 字段 / A2A method / Controller 行为 / 配置项 / 指标。 -->

### 接口契约（如适用）

```yaml
# CRD 草案 / API 草案 / wire contract 草案
apiVersion: a2a.superteam.cn/v1alpha1
kind: <Kind>
spec:
  <fields>
```

### 行为流

1. 用户/Operator 触发条件
2. 系统响应
3. 期望结果

## 受影响 Spec 段落

<!-- 本 feature 涉及哪些 spec / ADR / 宪法 段落？ -->
- 宪法 §X.Y — 涉及理由
- ADR-XXXX — 涉及理由
- L1-system-spec.md §X.Y — 涉及理由
- L2-module-specs/L2-*.md §X.Y — 涉及理由
- L3-file-specs/L3-*.md §X.Y — 涉及理由

## 替代方案考虑

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| A    |      |      | 选 / 弃 |
| B    |      |      | 选 / 弃 |
| C    |      |      | 选 / 弃 |

## 向后兼容影响

<!-- API / Kubernetes API / wire contract / 错误码 / RBAC / 配置项。 -->
- [ ] 现有 CRD schema 不变（仅 additive）
- [ ] 现有 A2A method 行为不变
- [ ] 错误码不变（无新码 / 无映射变更）
- [ ] RBAC 不变
- [ ] Helm values 向后兼容
- [ ] **BREAKING**: 说明 break 范围 + 迁移路径

## 测试计划

- [ ] unit（pytest 覆盖新逻辑）
- [ ] integration（kind cluster 端到端）
- [ ] spike（探索性验证 / 性能门禁 / 兼容性验证）
- [ ] 评审（10 维度 / §A-§P / spec-review.md 模板）

## L4 步骤映射

<!-- 落到 L4 Phase 1/2/3 哪一步？ -->
- [ ] L4 Step 1（uv workspace + 6 CRD schema）
- [ ] L4 Step 2（3 Controller + admission + Finalizer + Lease）
- [ ] L4 Step 3（Hello Agent ASGI 冒烟）
- [ ] L4 Step 4（mTLS cert-manager + a2a-sdk）
- [ ] L4 Step 5（Adapter SDK 模板 + 第一个 framework adapter）
- [ ] L4 Step 6（KS + MEM 单进程）
- [ ] L4 Step 7（observability / RBAC / NetworkPolicy 集成）

## 备注

<!-- 相关 issue / 外部参考 / 灵感来源。 -->
