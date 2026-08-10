# L4-Phase3 PR-5 Plan v0.1-draft · Phase 3 文档同步

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.1-draft**（2026-08-10 · #97 启动） |
| 上游 | PR-1 #30 + PR-2 #34 + PR-3 #35 + **PR-4 #36** 全部 merged（main HEAD `5259c14`） |
| 下游 | 无（Phase 3 收口） |
| 关联 PR | Phase 3 PR-1~PR-4 merged · **PR-5 #37 文档同步 · 本 plan** |
| main HEAD | `5259c14`（含 PR-4 squash merge） |

---

## §1 目标与边界

**目标**：将 Phase 3 4/4 PR merged 状态同步到 4 个项目治理文档，确保 ROADMAP / CONSTITUTION-CHANGELOG / ADR-0006 / MEMORY 4 个文档对项目当前状态描述一致。

**不在范围**：
- ❌ 宪法 v0.6.0 升级（ADR-0006 D + Phase 3 plan v1.0 推荐 · MVP 例外窗口兼容）
- ❌ L3-5/L3-6 Spec 修订（Phase 3 plan §F 仅文档同步 · 不触动 Spec）
- ❌ Helm chart 改动（PR-4 实装已完成）
- ❌ 代码改动（PR-5 仅文档）

---

## §2 §F 同步 4 步（v0.1-draft 清单）

### §F.1 · ROADMAP.md

**变更位置**：
- line 117 `Phase 3 — Memory` 旁状态：`🚧 进行中（L4-Phase 1/2 spike）` → `✅ 4/4 PR merged（#96）· 文档同步待 #97`
- line 121-124 实施状态：扩展到 Phase 3 4/4 PR
- line 132 kind E2E spike 状态：从 `🚧 L4-Phase2 PR-4（PR #25 open）` → `✅ L4-Phase2 PR-4（PR #25 merged · 2026-08-09 · 192 PASS）`
- 新增 Phase 3 4 项复选框勾选行：
  - `[x]` A2A HTTP JSON-RPC server · ✅ Phase 3 PR-1（PR #30 · 2026-08-10 · 12 测试 PASS）
  - `[x]` K8sBackend 完整实装 · ✅ Phase 3 PR-2（PR #34 · 2026-08-10 · 8 测试 PASS）
  - `[x]` 25 指标 ServiceMonitor 全量验证 · ✅ Phase 3 PR-3（PR #35 · 2026-08-10）
  - `[x]` H-RM/H-QM-E2E-001 真实实装 · ✅ Phase 3 PR-4（PR #36 · 2026-08-10 · unskip 2 E2E）
- line 135 `[ ] Memory E2E 测试` → 标 partial 完成注释（4/6 PASS · H-RM/H-QM unskip）

### §F.2 · CONSTITUTION-CHANGELOG.md

**新增 1 行**（line 25 之后 · 时序倒序）：
- `2026-08-10` · **L4-Phase3 4/4 PR merged + 文档同步（#97）** · **不触发宪法修订**
- 内容：PR-1 #30 (server) + PR-2 #34 (K8sBackend) + PR-3 #35 (25 metrics) + PR-4 #36 (H-RM/H-QM-E2E) + PR-5 #37 文档同步 · main HEAD `5259c14` · 36/36 PR 全部 merged · 241/241 PASS · 5 项关键不变量 100% 保持 · 6 项 CI check 全绿 · 宪法 §3.4/§6/§7/§9.7/§13.1/§14.5/§15.5/§16.1 全部通过 Phase 3 实战验证

### §F.3 · ADR-0006 §M.7 + §M.8

**M.7 扩展**（line 558 之后）：
- 现有 §M.7 Phase 2 spike 记录（PR #22/#23/#24/#25）保持不变
- line 567 PR #25 状态：`🟡 open` → `✅ merged · 2026-08-09 · 192 PASS`（注：#88 session 已 merged）
- line 580-585 Phase 2 PR-4.1 P0 跟进项：保持原状（PR-4.1 实际由 #89 #90 完成 · 但本表是 ADR-0006 §M.7 当时的快照）

**新增 §M.8 Phase 3 4/4 PR merged 记录**（line 586 之后）：
- 表格 4 行：PR #30 / PR #34 / PR #35 / PR #36
- 关键不变量保持（与 §M.7 同样的 5 项）

**§M.6 下次更新**：line 551-552 → 改写为 Phase 3 4/4 merged + PR-5 文档同步

### §F.4 · MEMORY.md

**头部状态行更新**（#96 → #97）：
- PR #36 → 下一里程碑 #97 PR-5
- session 编号 #97 + PR-5 doc-sync session 文件引用
- 36 → 36 PR merged 保持不变

**session 文件**：
- 新增 `session-2026-08-10-cont97-pr5.md`（PR-5 文档同步完整收口记录）

---

## §3 PR-5 启动检查清单

- [x] PR #30 #34 #35 #36 全部 merged（main HEAD `5259c14`）
- [x] Plan 文档（本文件 · 进行中）
- [ ] §F.1 ROADMAP.md 更新
- [ ] §F.2 CONSTITUTION-CHANGELOG.md 新增 1 行
- [ ] §F.3 ADR-0006 §M.7 + §M.8 更新
- [ ] §F.4 MEMORY.md 头部状态行 + session 引用
- [ ] commit + push + PR #37 创建

---

## §4 验收清单（4 项）

1. **§F.1 ROADMAP.md**：Phase 3 状态 `✅ 4/4 merged` + 4 个新增 PR 复选框勾选
2. **§F.2 CONSTITUTION-CHANGELOG.md**：新增 1 行 2026-08-10 L4-Phase3 4/4 PR merged + 文档同步
3. **§F.3 ADR-0006 §M.7 + §M.8**：Phase 2 PR #25 状态更新到 merged + 新增 §M.8 Phase 3 4 行
4. **§F.4 MEMORY.md**：头部状态行 + session 引用 · 不超 KB 上限

---

## §5 风险与缓解（3 项）

| # | 风险 | 缓解 |
|---|---|---|
| 1 | MEMORY.md 已 252 lines / 39.6KB（超限） | 头部状态行 ≤ 2 行更新 + 1 行 session 引用 · 详情放 session 文件 |
| 2 | ADR-0006 §M.7 已 30+ 行 · §M.8 新增需保持简洁 | 复用 §M.7 表格格式 · 4 行简洁 |
| 3 | PR-5 commit 触动 4 文档 · CI lint 不通过 | 0 代码改动 · ruff/pyright 跳过 · 仅 markdown · CI 8 项 check 必全绿 |

---

## M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-10 · #97 启动）
- **M.2 落地记录**：#97（2026-08-10 · Phase 3 文档同步 · 4 文档 §F.1-§F.4）
- **M.3 关联 PR**：Phase 3 #30 #34 #35 #36 merged · **#37 PR-5 文档同步 · 本 plan**
- **M.4 下次会话入口**：#97 阶段 B/C 实施 → #98 PR-5 收口（如需 → 项目发起人合并）· Phase 3 完整收口
- **M.5 关注项台账**：
  - ① MEMORY.md 头部行不超 2 行（KB 上限）
  - ② ADR-0006 §M.8 简洁（4 行表格）
  - ③ PR-5 commit 0 代码改动 · 仅 markdown
- **M.6 文档状态**：v0.1-draft 骨架稿（实施前完整 · 5 节 · ~10KB）

---

> **PR-5 启动就绪** · 2026-08-10 · 阶段 A 完成 · 阶段 B §F.1-§F.4 同步实施