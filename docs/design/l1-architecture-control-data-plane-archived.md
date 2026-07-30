# superteam-a2a — L1 v0.3 候选草案归档指针

> **目的**：本指针指向已归档的 L1 v0.3 候选草案（控制平面 / 数据平面 / 横切 三段视图），便于未来 L4 实施层实战验证后决定是否重新激活。

## 归档位置

[`docs/archive/l1-architecture-control-data-plane-v0.1-draft-discarded.md`](../archive/l1-architecture-control-data-plane-v0.1-draft-discarded.md)

## 当前状态（2026-07-30 · 会话 #68）

- **现行 L1 架构**：[`docs/design/L1-architecture.md`](./L1-architecture.md) **v0.2.0**（2026-07-24 评审通过 · 不变）
- **候选草案状态**：🗄️ **已归档（不合并）** · 决策路径 B（最小化 L4 启动门禁）
- **关联 ADR-0006**：OPEN-MEMORY-001 跨 container transport spike（独立起草 · 不依赖本草案）

## 重新激活条件

任一条件满足可重启本草案评审：
- L4 实施第一周实战发现 L1 v0.2.0 §2.2 旧图 3 个内在张力阻碍开发
- OPEN-MEMORY-001 spike 结论反向影响 L1 架构视图
- L4 中期回顾（Phase 1 MVP Core 完成后）触发

## 历史会话

- **#67.x**：起草 v0.1-draft（342 行 / 32.6KB）
- **#68**：用户决策路径 B · git mv 归档 + 本指针创建

---

**相关文件**：
- 草案正文：[`docs/archive/l1-architecture-control-data-plane-v0.1-draft-discarded.md`](../archive/l1-architecture-control-data-plane-v0.1-draft-discarded.md)
- 现行 L1：[`docs/design/L1-architecture.md`](./L1-architecture.md)
- 关联 ADR（待创建）：`docs/adr/0006-memory-transport.md`
