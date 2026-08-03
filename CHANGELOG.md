# Changelog

本项目的所有重要变更都会记录于此文件。

格式基于 [Keep a Changelog 1.1.0](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [Semantic Versioning 2.0.0](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 计划

- L4 Phase 1 MVP Core 实施层启动（uv workspace + 6 CRD Pydantic v2 schema）
- L4 Step 1：uv workspace 脚手架 + `packages/operator` / `packages/a2a-core` / `packages/adapter-sdk` / `packages/knowledge-memory` / `packages/hello-agent` / `services/knowledge-memory-service`
- kind spike 验证 webhook 50ms 端到端时延（OPEN-L1-002）
- L3-5 / L3-6 v0.2.1 关注项台账落实（5 项 L3-5-followup-1~5 + 4 项 L3-6-followup-1~4）

## [v0.3.0] - 计划中（L4 Phase 1 MVP Core 启动）

> **状态**：Unreleased · L4 实施层已解锁 · 等待 PR #1 落地

### Added

- L4 Phase 1 MVP Core 实施层脚手架（ADR-0006 D 方案单进程架构落地）
- uv workspace 顶层结构（`packages/*` + `services/*` + `agents/*`）
- 6 个 L3 CRD Pydantic v2 schema（Operator / A2A / Adapter / Knowledge / Memory / Hello Agent）
- Hello Agent 单进程 ASGI 冒烟
- mTLS cert-manager 接入（Operator ↔ KS 单进程，跨进程无 mTLS）
- 第一版 Adapter SDK + 第一个 framework adapter（LangChain）

### Changed

- 从 Go baseline 切换到 Python-first 实施栈（ADR-0005 Accepted）
- 文档结构从 Go 命名（`cmd/`）切换到 Python uv workspace（`packages/`）

## [v0.2.1] - 2026-07-30

### Added

- ADR-0006 v1.0 Accepted（D 方案 · 同进程单进程 · 合并 L3-5 + L3-6）
- ADR-0006 5 候选方案决策矩阵（5×7 维度）

### Changed

- L3-5 v0.2.1 微同步：`§6.2` 共享 Deployment 协调点 → 单进程架构（关联测试 ID `MTLS-IT-001` 废弃）
- L3-6 v0.2.1 微同步：`§6.1+§6.2+§6.3+§6.5+§9.2+§9.10` 单进程部署
  - 删除 `IPC_SOCKET` / `emptyDir` volumeMount / `MEMORY_RECONCILER_INTERVAL` / `LEASE_NAME`
- L1 v0.2.0 `§4.1` C-6 + C-7 合并为 Knowledge-Memory Service
  - 顶层目录：`uv workspace packages/knowledge-memory` + `services/knowledge-memory-service`
- 开放问题关闭：`OPEN-MEMORY-001` / `OPEN-L1-003` / `OPEN-ADR-0006-001`

### Removed

- 跨进程 IPC transport（UDS / shared runtime / mmap / HTTP loopback）所有配置
- 双进程架构下 mTLS 跨进程 cert-manager 链路（单进程不需要）

## [v0.2.0] - 2026-07-29

### Added

- L3 阶段 6/6 v0.2.0 文件级 Spec 100% 落地：
  - L3-1 Operator Core（46 → 71 测试 ID · 139 测试 ID）
  - L3-2 A2A Core（276 测试 ID · 4 时序图）
  - L3-3 Adapter SDK（91 测试 ID）
  - L3-4 Hello Agent（48KB 评审 + 10 维度）
  - L3-5 Knowledge Service（60 测试 ID + 23 错误码）
  - L3-6 Memory Backend（60 TEST-MEM-001~060 + 12 MEMORY_* 错误码）
- L1 v0.2.0 Python 重写（86KB Design + 75KB Spec · 27KB 评审）
- L2 阶段 4/4 v0.2.0 Python：
  - L2-1 A2A Protocol（44KB Design + 72KB Spec · 31KB 评审）
  - L2-2 Operator Core（28KB Spec + 28KB 评审 · 10 维度全 PASS）
  - L2-3 Adapter（66KB Design + 114KB Spec · 49.7KB + 53.5KB 评审）
  - L2-4 Knowledge & Memory（97KB Design + 194.6KB Spec · 59.7KB 评审）
- 8 个 L3 评审通过（`docs/reviews/l3-*-spec-review.md`）
- ADR-0005 v1.0 Accepted（Python-first 技术栈）
- 宪法 v0.5.0（含 §3.4 ADR / §3.8 uv workspace / §9.7 uv.lock 必须提交 / §14.5 MVP 例外窗口 / §16.1 上下文红线）

### Changed

- 技术栈从 Go baseline 全部切换到 Python-first
- Spec 评审从 Go 视角重写为 Python 视角（含 Pydantic v2 schema / kopf / structlog / OTel）
- 错误码体系：L2-4 v0.2.0 §9.1 12 MEMORY_* 权威名（`-32101` ~ `-32112`）确立

### Fixed

- L3-5 v0.2.0 升级：23 处错误码漂移修正（与 L2-4 v0.2.0 §9.1 权威名 100% wire contract 一致）

## [v0.1.0] - 2026-07-24

### Added

- L1 v0.1.0 架构初稿（Go baseline · 三层 Spec 体系）
- L2 阶段 4/4 v0.1.0 Go：
  - L2-1 A2A Protocol Design Go（21KB）
  - L2-1 A2A Protocol Spec Go（31KB）
  - L2-2 Operator Core Design Go（50KB）
  - L2-2 Operator Core Spec Go（50KB · 139 测试 ID）
  - L2-3 Adapter Design Go（32KB）
  - L2-3 Adapter Spec Go（43KB）
  - L2-4 Knowledge & Memory Design Go（41KB）
  - L2-4 Knowledge & Memory Spec Go（99KB）
- L3-1 Operator Core v0.2-draft 骨架稿（46 测试 ID · 71 测试 ID）
- 宪法 v0.3.0（`§16` 水位红线 · 50% 窗口）+ 宪法 v0.4.0
- 9 个 L2/L3 评审通过（`docs/reviews/l2-*-*-review.md` / `docs/reviews/l3-1-*-review.md`）
- ADR-0001 v1 scope 声明
- ADR-0002 知识管理设计
- ADR-0003 Memory 设计
- ADR-0004 v0.1 scope 扩展（Knowledge & Memory）
- git init 本地化（commit `64b6147` · 45 sessions 首次 commit）

### Changed

- 从"无版本"过渡到 v0.1.0 Go baseline
- L2 阶段从设计到 Spec 到评审三步走流程确立

## [v0.0.0] - 2026-07-08

### Added

- 项目启动：superteam-a2a 命名锁定
- A2A + K8s spine 项目档案建立（`user-profile.md` / `a2a-k8s-agent-platform.md`）
- Apache 2.0 LICENSE
- README / ROADMAP 草稿
- Pre-ADR 阶段（无正式版本号 · 无 ADR 文件）

[Unreleased]: https://github.com/superteam-cn/superteam-a2a/compare/v0.2.1...HEAD
[v0.3.0]: https://github.com/superteam-cn/superteam-a2a/compare/v0.2.1...v0.3.0
[v0.2.1]: https://github.com/superteam-cn/superteam-a2a/compare/v0.2.0...v0.2.1
[v0.2.0]: https://github.com/superteam-cn/superteam-a2a/compare/v0.1.0...v0.2.0
[v0.1.0]: https://github.com/superteam-cn/superteam-a2a/compare/v0.0.0...v0.1.0
[v0.0.0]: https://github.com/superteam-cn/superteam-a2a/releases/tag/v0.0.0

## 版本号约定

遵循 Semantic Versioning 2.0.0：

- **MAJOR** (x.0.0): 不兼容 API/CRD schema 变更
- **MINOR** (0.x.0): 向后兼容功能新增（新增 CRD / 新 endpoint）
- **PATCH** (0.0.x): 向后兼容 bug 修复（错误码映射 / 文档 / 测试）
- **Pre-alpha 版本**（< 1.0.0）：任何变更都允许升级 MINOR

## 类型约定（Keep a Changelog 1.1.0）

- **Added** — 新功能
- **Changed** — 已有功能的变更
- **Deprecated** — 即将移除（建议但不强制的过渡期）
- **Removed** — 已移除功能
- **Fixed** — Bug 修复
- **Security** — 安全漏洞修复（不暴露细节，仅引向 `SECURITY.md`）

## 历史 commit 参考

本节仅列出关键版本节点。具体 commit SHA 与 PR 号请查阅：

- `git log --oneline | grep -E "v0\.[0-9]+\.[0-9]+"` — 版本相关 commit
- `git log --oneline | grep -E "ADR-000[1-6]"` — ADR 相关 commit
- `docs/constitution/CONSTITUTION-CHANGELOG.md` — 宪法版本历史
- `docs/adr/0001~0006-*.md` — 6 个 ADR 的演进历史
- `docs/reviews/` — 17 个 spec 评审

## 历史节点

- 2026-07-08 — 项目启动（v0.0.0 Pre-ADR 阶段）
- 2026-07-23 — L1 v0.1.0 + ADR-0001~0004 + 宪法 v0.3.0
- 2026-07-24 — L2 4/4 v0.1.0 Go baseline + 宪法 v0.4.0 + 9 个 L2 评审
- 2026-07-25 — L2-2 Spec Python 完整版（88KB · 10 维度全 PASS）
- 2026-07-26 — L2-3/L2-4 Python 完整版（114KB + 194.6KB）
- 2026-07-27 — L2-4 收口 + L3 启动 + git init 本地化
- 2026-07-28 — L3-1/3 收口
- 2026-07-29 — L3-3/4/5 推进（v0.2-draft → v0.2-draft-full 评审）
- 2026-07-29 — L3 阶段 5/5 v0.2.0 全部收口（ADR-0005 Python-first Accepted）
- 2026-07-30 — L3-6 v0.2-draft 骨架稿 + 完整 + 评审 + 升级 v0.2.0
- 2026-07-30 — ADR-0006 v0.1-draft → v1.0 推荐 → **Accepted**（D 方案 · 同进程单进程）
- 2026-07-30 — L3-5 + L3-6 v0.2.1 微同步（IPC/emptyDir/RECONCILER_INTERVAL 删除）
- 2026-07-30 — 完整交接文档 #72（14KB · 11 节）
- 2026-08-01 — MEMORY 维护 + 完整交接 #73（19.9KB · 12 节）
- 2026-08-02 — GitHub Private 发布到 superteam-cn org（v0.2.1 · commit `2c0fbe1`）

---

本 changelog 由项目维护者手工维护，与 [`CONSTITUTION-CHANGELOG.md`](./CONSTITUTION-CHANGELOG.md) 配套（后者记录宪法本身的演进）。
