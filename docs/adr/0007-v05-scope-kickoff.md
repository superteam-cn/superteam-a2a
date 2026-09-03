# ADR-0007: v0.5.0 scope 启动 · 进度同步 + CrewAI 范围决策

> **本 ADR 不重新定义 v0.5.0 范围**（已在 ADR-0001 §决策 2 锁定）。本 ADR 的目的是：
> 1. 标记 v0.5.0 实施阶段启动（v0.1.0 → v0.5.0 transition）
> 2. 同步 v0.1.0 launch 后的实际进度（#118 PR 超额实装 4 framework examples）
> 3. 提出 1 个新决策点（CrewAI 是否从 v1.0.0 提前到 v0.5.0）
> 4. 列出剩余 v0.5.0 工作项与粗略 effort 估算
> 5. 明确 v0.5.0 推进依赖（launch 反馈 · 用户决策）
>
> **宪法合规**：本 ADR 走 §14.5 MVP 例外单点评审（v0.1.0 → v1.0.0 期间）；v1.0.0 发布后必须改走 §14 完整评审流程。

---

## 状态

| 字段 | 值 |
|---|---|
| **Status** | v0.1-draft (推荐升级 → Accepted 等项目发起人决策) |
| **Date** | 2026-09-03 |
| **Deciders** | 项目发起人（CoderZhangfujiang） |
| **Reviewers** | 项目发起人（依据宪法 14.5 MVP 例外，单点评审） |
| **Supersedes** | 无 |
| **Superseded by** | TBD |
| **Related** | [ADR-0001](0001-v1-scope-statement.md) §决策 2（v0.5.0 范围 · 权威定义）、[ADR-0004](0004-v01-scope-extension-knowledge-and-memory.md)（v0.1 范围扩展先例）、[ROADMAP.md](../../ROADMAP.md) Phase 5、PR #62（#118 Phase 5 LAUNCH · Adapter SDK Protocol + 4 framework examples） |

---

## 背景（Context）

### v0.5.0 定位（ADR-0001 §决策 2）

| 维度 | 内容 |
|---|---|
| **版本定位** | v1.0.0 前最后一个 minor（API 接近稳定） |
| **关键承诺** | 第一个 framework adapter + SSE streaming |
| **依赖** | v0.1.0 反馈 |
| **预计发版** | 2027-Q2（ADR-0001 §决策 2 + ROADMAP Phase 5） |

### v0.5.0 范围授权（ADR-0001 §2.1 原文）

**新增项**：

- 第一个 framework adapter：**LangChain**（按宪法 4.7 Golden Adapter 强制）
- SSE Streaming：新增 `a2a.subscribeTask` / `a2a.cancelTask`（v0.1 推到 v0.5）
- CRD 版本升级：所有 CRD `v1alpha1` → `v1beta1`，**字段集冻结**
- Conversion Webhook：v1alpha1 ↔ v1beta1 兼容
- `Conversation` CRD：A2A 长会话状态
- 第二个 framework adapter：**AutoGen**

**升级项**：

- E2E 测试覆盖 2 个 framework adapters 完整路径
- 完整 Conformance 套件（参考 `google-a2a/conformance`）
- 评测驱动（每个 adapter ≥ 5 个 Golden Cases）

### v0.5.0 范围不包含（ADR-0001 §2.2 推迟到 v1.0.0）

- ❌ CrewAI / Semantic Kernel / Strands / Smolagents adapters
- ❌ Web UI / Dashboard
- ❌ 多集群联邦

### 实际进度（2026-09-03 · #118 PR squash merged @ `6c4f9ce`）

PR #62（[Phase 5 LAUNCH](https://github.com/superteam-cn/superteam-a2a/pull/62)）实施内容：

- ✅ **Adapter SDK Protocol** 实装（`packages/adapter-sdk` · `Adapter` 抽象基类 + `AdapterCard` + `to_a2a_card()` 转换层）
- ✅ **4 framework examples**（`examples/{hello,langchain,crewai,autogen}/agentset.yaml` + `examples/README.md` 索引）
- ✅ **8 ADAPTER-UT 测试**（`tests/unit/adapter_sdk/test_adapter_sdk.py`）
- ✅ **mkdocs docs site**（`docs/admin/mkdocs.yml` + `.github/workflows/docs.yml`）

**进度对比**：

| v0.5.0 范围项 | ADR-0001 状态 | #118 实际进度 | 差异 |
|---|---|---|---|
| LangChain adapter | 新增项 | ✅ `examples/langchain/agentset.yaml` + 集成测试 | **已超额** |
| AutoGen adapter | 新增项 | ✅ `examples/autogen/agentset.yaml` + 集成测试 | **已超额** |
| CrewAI adapter | 推迟到 v1.0.0 | ✅ `examples/crewai/agentset.yaml`（未预期） | **提前** |
| SSE Streaming | 新增项 | ❌ 未开始 | **待启动** |
| CRD v1alpha1 → v1beta1 | 新增项 | ❌ 未开始 | **待启动** |
| Conversion Webhook | 新增项 | ❌ 未开始 | **待启动** |
| Conversation CRD | 新增项 | ❌ 未开始 | **待启动** |
| 完整 Conformance 套件 | 升级项 | 🟡 33 conformance tests（v0.1 baseline） | **待扩展** |
| E2E 覆盖 2 adapters | 升级项 | 🟡 kind E2E 基础设施已建（Phase 3 PR-4） | **待补 case** |
| Golden Cases ≥ 5/adapter | 升级项 | 🟡 8 ADAPTER-UT 测试（粗略覆盖） | **待形式化** |

### 进度总结

- **已完成（3/9）**：LangChain + AutoGen + CrewAI adapter（**CrewAI 是超出 ADR-0001 授权的提前交付**）
- **待启动（4/9）**：SSE Streaming + CRD 升级 + Conversion Webhook + Conversation CRD
- **待扩展（2/9）**：完整 Conformance 套件 + Golden Cases 形式化

---

## 决策（Decision）

### 决策 1：v0.5.0 范围保持 ADR-0001 §2.1 不变

**理由**：

- ADR-0001 §2.1 已通过项目发起人单点评审（2026-07-23），本 ADR 不推翻既有授权
- v0.5.0 范围经过 6 周 v0.1.0 实装验证，工作量估算准确（3 framework adapters + 4 平台核心 = 7 项）
- 任何范围变更需走 ADR（宪法 §11.1 破坏性变更规则）

**不包含**：

- ❌ 任何 v1.0.0 范围的项（Web Dashboard / 完整 conformance 100% / 多集群联邦 / 6 framework adapters 全覆盖）

### 决策 2：CrewAI adapter 从 v1.0.0 升级到 v0.5.0

**观察**：#118 PR #62 实装了 `examples/crewai/agentset.yaml` 与 CrewAI adapter 集成路径。**CrewAI 不在 ADR-0001 §2.1 授权范围内**（原文 §2.2 明确推迟到 v1.0.0）。

**问题**：是否将 CrewAI 形式化为 v0.5.0 范围内？

**选项**：

- **A. 维持 ADR-0001 §2.2 推迟到 v1.0.0**（推荐）理由：保持 v0.5.0 scope 节制（§1 范围不爆炸原则）；CrewAI example 保留作为"社区贡献预览"，但不算 v0.5.0 完成度
- **B. 将 CrewAI 升级到 v0.5.0 In-Scope**（备选）理由：example 已 ship，社区可立即使用；形式化升级只增加文档工作量
- **C. 推迟决策到 v0.5.0 kickoff 会话再决定**（保守）理由：避免本次 ADR 锁死决定，等 v0.1.0 launch 反馈后再权衡

**推荐 A**：保持范围节制。ADR-0001 §决策必要性 §1 明确"范围爆炸"是 v1.0.0 永远不到的核心风险。**CrewAI example 作为社区贡献预览存在，但不计入 v0.5.0 完成度门禁**。

### 决策 3：v0.5.0 实施顺序（粗略 · 等 v0.1.0 launch 反馈再细化）

按依赖关系排序（**纯推断 · 未启动**）：

1. **CRD v1alpha1 → v1beta1** + **Conversation CRD**（基础设施 · 必先）
   - 字段冻结前需跑通 v0.1.0 launch 至少 4 周（收集字段遗漏）
   - 工期估算：**6-8 周**（6 CRD × 1 周 + conversion webhook 2 周）
2. **Conversion Webhook**（与 CRD 升级同期）
   - 工期估算：**2 周**（含 conformance 测试）
3. **SSE Streaming**（`a2a.subscribeTask` / `a2a.cancelTask`）
   - 依赖：Adapter SDK Protocol（已就绪 #118）+ L3-2 A2A Core Spec
   - 工期估算：**3-4 周**（含 K8s Ingress SSE config + 客户端 SDK）
4. **完整 Conformance 套件 + Golden Cases 形式化**
   - 依赖：前 3 项就绪
   - 工期估算：**2-3 周**（LangChain + AutoGen 各 ≥ 5 cases + conformance harness）
5. **v0.5.0 打磨 + 文档同步**（PR-1 + PR-2 + §F 同步）
   - 工期估算：**2 周**

**总计**：15-19 周 · 120-150h · **贴 2h/day × 5 天 × 20 周 = 200h 预算**（v0.1.0 同模式）

### 决策 4：v0.5.0 启动依赖（**关键路径阻塞点**）

**依赖 1：v0.1.0 launch 反馈**

- 14 渠道 7 天 rollout（按 `docs/launch/submission-checklist.md` 时间表）
- Day 7 复盘 + Week 1 stats（按 `docs/launch/engagement-playbook.md`）
- **触发条件**：至少 50 stars + 5 个 issues/PRs 反馈（首次校准 v0.5.0 范围）

**依赖 2：A2A 协议上游变更**

- 跟踪 [google-a2a/A2A](https://github.com/google-a2a/A2A) 上游
- 若 v0.5.0 启动前 A2A 协议发布 minor 升级，需评估影响
- 当前 `a2a.subscribeTask` 在上游是否已稳定？（**OPEN-ADR-0007-001**）

**依赖 3：framework 维护者招募**

- v0.1.0 launch 后通过 good-first-issue 标签招募 framework 维护者
- 每个 framework 1 人（ADR-0001 §4 永久 out-of-scope "对任何 Agent 框架的偏好"）
- **关键路径**：招募失败则 v0.5.0 推迟（OPEN-ADR-0007-002）

**依赖 4（新增）：单人 2h/day 容量**

- v0.5.0 工期估算 120-150h（按决策 3）
- 假设单人 2h/day × 5 天 × 20 周 = 200h **贴预算**
- 若 v0.1.0 launch 后维护负担加重（issues / PR review / community），可能需缩减 v0.5.0 scope

### 决策 5：v0.5.0 scope 不变原则（避免 §11 1 破坏性变更）

- v0.5.0 范围变更须新 ADR 推翻 ADR-0001 §决策 2 + 本 ADR §决策 1
- 流程成本：单点评审（§14.5 MVP 例外 · v0.1.0 → v1.0.0 期间）
- 提交窗口：v0.5.0 启动会话之前（不可在实施中途变更）
- 任何 v0.5.0 实施 PR 必须显式引用 ADR-0001 §2.1 + 本 ADR §决策 1（合规检查）

---

## 实施计划（粗略）

### Phase 5.0 · v0.5.0 scope kickoff（**当前会话 · 2026-09-03**）

- [x] ADR-0007 v0.1-draft 起草（本文件）
- [ ] ADR-0007 v1.0 推荐（项目发起人单点评审）
- [ ] ADR-0007 Accepted + 后续 §F 同步（更新 ROADMAP Phase 5 状态）

### Phase 5.1 · v0.1.0 launch 反馈窗口（**4-6 周 · 2026-09 → 2026-10**）

- [ ] 14 渠道 7 天 rollout 执行（maintainer web 端）
- [ ] Day 7 / Day 14 / Day 30 复盘（按 `engagement-playbook.md`）
- [ ] 字段遗漏收集（v0.1.0 → v0.5.0 CRD 升级的 6-8 周工作前置）
- [ ] framework 维护者招募启动（good-first-issue）

### Phase 5.2 · v0.5.0 实施（**15-19 周 · 2026-11 → 2027-Q1**）

- [ ] PR-1: CRD v1alpha1 → v1beta1 字段冻结（6 CRD · 6-8 周）
- [ ] PR-2: Conversion Webhook（v1alpha1 ↔ v1beta1 · 2 周 · 依赖 PR-1）
- [ ] PR-3: Conversation CRD（与 PR-1 同期 · 1-2 周）
- [ ] PR-4: SSE Streaming（`a2a.subscribeTask` / `a2a.cancelTask` · 3-4 周）
- [ ] PR-5: 完整 Conformance 套件 + Golden Cases（LangChain + AutoGen 各 ≥ 5 · 2-3 周）
- [ ] PR-6: v0.5.0 打磨 + §F 同步（2 周）
- [ ] GitHub Release `v0.5.0` tag 发布

### Phase 5.3 · v0.5.0 launch（**1 周 · 2027-Q1 末**）

- [ ] CHANGELOG 自动生成
- [ ] v0.5.0 Release notes 撰写
- [ ] Re-launch 14 渠道（突出 v0.5.0 升级点 · 精简版）

---

## 影响分析（Consequences）

### 正面

- ✅ v0.5.0 范围清晰，避免范围爆炸（ADR-0001 §决策必要性 §1）
- ✅ 进度可见（3/9 已完成 · 4/9 待启动 · 2/9 待扩展）
- ✅ 启动依赖显式记录（避免开工后才发现阻塞）
- ✅ 单人 2h/day 容量贴合（120-150h / 200h 预算）

### 负面 / 风险

- ⚠️ **A2A 协议上游风险**：`a2a.subscribeTask` 在 v0.5.0 启动前若上游 API 变更，需重构
- ⚠️ **framework 维护者招募失败**：v0.5.0 推迟或缩减 scope
- ⚠️ **CRD 字段冻结过早**：v0.5.0 后若发现遗漏需走 ADR + 弃用期
- ⚠️ **15-19 周工期可能过度乐观**：v0.1.0 实装中 PR-4b/4c 出现意外根因（typo path / pytest config），v0.5.0 类似风险存在

### 缓解措施

| 风险 | 缓解 |
|---|---|
| A2A 协议上游变更 | OPEN-ADR-0007-001 · 锁定 minor 版本范围（追踪上游 release notes） |
| framework 维护者招募 | 主动接触 LangChain/AutoGen 社区 + good-first-issue 标签 + "Help wanted" 帖子 |
| CRD 字段冻结过早 | v0.1.0 launch 后 4-6 周窗口收集字段遗漏 |
| 工期过度乐观 | 每个 PR 后 §M.5 关注项台账 + 实际工期 vs 估算对比 |

---

## 开放问题（OPEN-ADR-0007-）

| 编号 | 问题 | 状态 |
|---|---|---|
| OPEN-ADR-0007-001 | `a2a.subscribeTask` 在 A2A 上游当前稳定状态？ | 🟡 待调研 |
| OPEN-ADR-0007-002 | framework 维护者招募渠道与时间表？ | 🟡 v0.1.0 launch 后启动 |
| OPEN-ADR-0007-003 | Conversation CRD 字段定义（L2-4 之前未规划） | 🟡 v0.5.0 PR-3 启动时起草 |
| OPEN-ADR-0007-004 | v0.5.0 → v1.0.0 期间如何处理 CRD `v1beta1 → v1` 升级风险？ | 🟡 等 v0.5.0 launch 反馈 |

---

## 关键引用（Related）

- [ADR-0001](0001-v1-scope-statement.md) §决策 2（v0.5.0 范围 · 权威）
- [ADR-0004](0004-v01-scope-extension-knowledge-and-memory.md)（v0.1 范围扩展先例 · meta-ADR 模式）
- [ROADMAP.md](../../ROADMAP.md) Phase 5（v0.5.0 阶段定义 · 本 ADR §F 同步更新）
- [CONSTITUTION.md](../../CONSTITUTION.md) §14.5（v0.1.0 → v1.0.0 MVP 例外单点评审窗口）
- [CONSTITUTION.md](../../CONSTITUTION.md) §11.1（破坏性变更走 ADR）
- [CONSTITUTION.md](../../CONSTITUTION.md) §4.7（Golden Adapter 强制）
- PR #62 / #118 Phase 5 LAUNCH（`6c4f9ce` · 4 framework examples + Adapter SDK Protocol + mkdocs docs site）
- `examples/{hello,langchain,crewai,autogen}/agentset.yaml`（4 framework examples · #118 ship）

---

## 决策清单摘要

| 决策 | 内容 | 状态 |
|---|---|---|
| §决策 1 | v0.5.0 范围保持 ADR-0001 §2.1 不变 | ✅ |
| §决策 2 | CrewAI 维持 v1.0.0 推迟（不升级到 v0.5.0） | 🟡 推荐 A · 等发起人确认 |
| §决策 3 | v0.5.0 实施顺序（CRD → Conversion → Conversation → SSE → Conformance → 打磨） | ✅ |
| §决策 4 | v0.5.0 启动依赖（launch 反馈 + A2A 上游 + framework 招募 + 2h/day 容量） | ✅ |
| §决策 5 | v0.5.0 scope 不变原则（避免破坏性变更） | ✅ |

---

## 文档元数据

| 字段 | 值 |
|---|---|
| **M.1 文件路径** | `docs/adr/0007-v05-scope-kickoff.md` |
| **M.2 创建日期** | 2026-09-03 |
| **M.3 最后更新** | 2026-09-03 |
| **M.4 版本** | v0.1-draft |
| **M.5 关注项台账** | 4 OPEN-ADR-0007-001~004（见上） |
| **M.6 关联 PR** | PR #71（视觉资产 #124）+ PR #62（Phase 5 LAUNCH #118） |

---

<sub> v0.5.0 scope 启动 · 进度 3/9 已完成 · 4/9 待启动 · 2/9 待扩展 · 启动依赖 launch 反馈 · 1 个新决策点（CrewAI 维持 v1.0.0 推迟 · 推荐） · 工期估算 15-19 周 · 贴单人 2h/day 预算 · 走 §14.5 MVP 例外单点评审</sub>