# ADR-0004: v0.1 范围扩展与时间线延长 — 引入知识管理 + 持久化记忆

> **元决策 ADR（meta-ADR）**：本 ADR 在 ADR-0001 / 0002 / 0003 之前落地，授权后续 ADR 的范围与边界。**在本 ADR 通过前，不得开始上述任何 ADR 的实施。**
>
> **编号说明**：本 ADR 采用"主题优先"编号（meta-ADR 用 0004），而非"时间优先"编号。0001-0003 为后续设计 ADR，0004 为本元决策。编号仅用于标识，不暗示顺序。
>
> **2026-07-24 实现栈说明**：本 ADR 的 v0.1 功能范围与 20 周预算决策继续有效；其中 Go 相关实现假设已由 [ADR-0005](0005-python-first-technology-stack.md) supersede。Python 迁移引入的新增设计工作量将在 L1 v0.2 评审时重新估算。

---

## 状态

| 字段 | 值 |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-07-23 |
| **Deciders** | 项目发起人（CoderZhangfujiang） |
| **Reviewers** | 项目发起人（依据宪法 14.5 MVP 例外，单点评审） |
| **Supersedes** | 无 |
| **Superseded by** | [ADR-0005](0005-python-first-technology-stack.md)（仅 Go/实现栈条款；范围与时间线决策继续有效） |
| **Related** | ADR-0001（待写）、ADR-0002（待写）、ADR-0003（待写） |

---

## 背景（Context）

### 原 v0.1 范围（2026-07-08 锁定）

依据 [ROADMAP.md](../../ROADMAP.md) Phase 0-1，v0.1 原计划为：

- **4 大基础能力**：Agent 发现 / Agent 通信 / Agent 监控 / Agent 编排
- **3 个 CRD**：Agent / AgentSet / Workflow
- **2 个 A2A method**：`a2a.sendMessage` / `a2a.getTask`
- **3 个 Controller**
- **1 个参考 Agent**：Hello Agent
- **交付期：12 周**（约 2026-07-08 → 2026-09-30）@ 2h/天

工作量估算：~120h，**贴预算**（12 周 × 2h × 5 天 = 120h）。

### 范围扩展（2026-07-23 用户决策）

本会话期间，用户基于"agent 实际可用性需要"做出两个新决策：

1. **新增第 5 大基础能力**：在原 4 项（发现 / 通信 / 监控 / 编排）之外，增加 **"知识管理（Knowledge Management）"** —— Agent 需要按 4 级作用域（industry / organization / team / project）+ agent-private 维度管理显性知识与经验沉淀。
2. **持久化记忆（Persistent Memory）**作为知识管理的子能力进入 v0.1：Agent 团队需共享一部分经验记忆（**不是全部**会话上下文，仅**持久化部分**），含 decay / reinforce 生命周期。

### 工作量影响

| 维度 | 原 v0.1 | 新 v0.1 | 增加 |
|---|---|---|---|
| 基础能力 | 4 项 | **5 项** | +1 |
| CRD | 3 个 | **6 个** | +3（KnowledgeScope / KnowledgeItem / Memory） |
| A2A method | 2 个 | **6 个** | +4（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory） |
| Controller | 3 个 | **4 个** | +1（MemoryReconciler） |
| 特殊 Agent | 1 个（Hello） | **2 个**（+Knowledge Service） | +1 |
| 工作量 | ~120h | **~200h** | **+80h（≈ 8 周）** |

### 关键约束

**用户硬约束**（来自项目 memory）：

- 单人维护
- ~2h/天 时间投入
- Apache 2.0 开源 / 目标 3,000 stars / 18 个月
- 无外部资金、无社区贡献者

**宪法硬约束**（[CONSTITUTION.md](../../CONSTITUTION.md)）：

- **第十五条**（质量第一性）：不得为任何理由牺牲质量
- **第十五条 4**（技术债务）：可接受的技术债务须经 ADR + 偿还计划 + 显式标注；**不可接受的"先这样回头再改"违反本条**
- **第三条 1**（分层严格）：禁止跨层调用，禁止反向依赖
- **第十一条 1**（破坏性变更）：范围扩展属重大变更，必须走 ADR

### 决策必要性

80h 的工作量缺口若不显式记账，将违反宪法 15.4（技术债务不可悄悄累积）。本 ADR 的目的是**显式承认缺口、显式选择填补路径、显式记录后果**。

---

## 决策（Decision）

v0.1 的交付范围与时间线按以下方式调整：

### 决策 1：v0.1 范围扩展为 5 项基础能力 + 6 个 CRD + 6 个 A2A method

完整范围（最终）：

- **5 大基础能力**：发现 / 通信 / 监控 / 编排 / **知识管理（含 Memory）**
- **6 个 CRD**：Agent / AgentSet / Workflow / **KnowledgeScope / KnowledgeItem / Memory**
- **6 个 A2A method**：`a2a.sendMessage` / `a2a.getTask` / **`a2a.queryKnowledge` / `a2a.getKnowledgeItem` / `a2a.recordMemory` / `a2a.queryMemory`**
- **4 个 Controller**：Agent / AgentSet / Workflow / **MemoryReconciler**
- **2 个特殊 Agent**：Hello Agent / **Knowledge Service**

### 决策 2：交付期从 12 周延长到 20 周

- **新交付期：20 周**（≈ 5 个月 @ 2h/天）
- 起止：**2026-07-08 → 2027-01-20**（含 buffer）
- **工作量预算：200h**（缺口 80h 由延长时间线吸收）

### 决策 3：不削减范围、不降低质量

明确**不接受**的妥协：

- ❌ 不删除 Memory 子能力（用户已决策"全部进 v0.1"）
- ❌ 不降低 CRD 字段严格度（违反 2.5 显式优于隐式）
- ❌ 不跳过 conformance / e2e 测试（违反 9.x）
- ❌ 不关闭可观测性埋点（违反 7.x）
- ❌ 不跳过 CRD conversion webhook（违反 2.6 / 3.3）
- ❌ 不"先这样回头再改"（违反 15.4）

### 决策 4：4 个新文档先于实施落地

按宪法 14.4 强门禁，以下文档必须在任何代码提交前完成并通过评审：

1. **ADR-0001** v1 范围声明（依赖本 ADR）
2. **ADR-0002** 知识管理能力设计（依赖 ADR-0001）
3. **ADR-0003** Memory 持久化记忆设计（依赖 ADR-0001）
4. **[CONSTITUTION.md](../../CONSTITUTION.md) v0.1.0 → v0.2.0**：第二条新增 2.9 条款"记忆可追溯"

随后是：

5. **L1 Architecture** 更新（+3 CRD + 4 method + MemoryReconciler）
6. **L1 Spec** 更新（CRD 字段 + 错误码 + 状态机）
7. **L2 模块设计**（4 个 L2 文档）

### 决策 5：阶段性交付，不等待全部完工

为降低"5 个月无任何公开产出"的风险，v0.1 内部拆分为 4 个**可独立发版**的 Phase：

| Phase | 周次 | 交付物 | 独立发版 tag |
|---|---|---|---|
| **Phase 1** | 第 1-10 周 | MVP 内核 + 集成（3 CRD + Hello Agent + Helm + E2E + CI） | `v0.1.0-alpha` |
| **Phase 2** | 第 11-14 周 | 知识管理（+2 CRD + Knowledge Service + 2 method） | `v0.1.0-beta` |
| **Phase 3** | 第 15-18 周 | Memory（+1 CRD + MemoryReconciler + 2 method） | `v0.1.0-rc` |
| **Phase 4** | 第 19-20 周 | 打磨 + Demo 视频 + launch 准备 | `v0.1.0` |

每个 Phase 结束即打 tag、推镜像、写 release note，不等 v0.1.0 完整。

---

## 后果（Consequences）

### 正面

- ✅ **范围完整**：知识管理与 Memory 是项目的差异化核心，进 v0.1 防止"未来再补"的二次返工
- ✅ **质量有保障**：不削减范围、不降低测试覆盖、不接受隐性技术债（符合宪法 15.1 / 15.4）
- ✅ **文档驱动**：4 个新 ADR 强制设计先于实施（符合宪法 14.4 强门禁）
- ✅ **阶段可见**：4 个 Phase 各自可发版，避免"5 个月零公开产出"风险
- ✅ **宪法一致**：ADR 形式显式记账（15.4 要求）
- ✅ **真实工作量匹配用户能力**：2h/天 × 20 周 ≈ 200h ≈ 实际工作量

### 负面

- ⚠️ **进度延迟 8 周**：v0.1.0 完整版交付从 2026-09-30 → 2027-01-20
- ⚠️ **首公开产出延后**：Phase 1 v0.1.0-alpha 需 ~10 周后才能发布
- ⚠️ **冷启动窗口变窄**：原计划 12 周可发版抢 star，现延至 20 周
- ⚠️ **范围爆炸风险增加**：5 项能力 + 6 CRD 是大项目，单人维护出错率上升
- ⚠️ **宪法 2.6 锁定风险**：6 个 CRD 在 v0.1 阶段锁定字段集后，v1.0.0 之前的字段调整会更频繁（违反 2.6 精神），需要 MVP 例外 14.5 长期适用
- ⚠️ **Memory 复杂度未知**：decay / reinforce / scope-up 算法需要实践验证，**首个版本可能需要 1-2 次重写**

### 缓解措施

| 风险 | 缓解 |
|---|---|
| 进度延迟 | 阶段发版 + 提前准备 launch 草稿（第 10 周起即写 HN draft） |
| 冷启动窗口窄 | Phase 1 alpha 即可对外发"prerelease"，抢早期试用 |
| 范围爆炸 | ADR-0001 / 0002 / 0003 严格限制每个 CRD 字段数 ≤ 15（防过度设计） |
| MVP 例外长期适用 | 14.5 例外窗口已在 2026-07-23 明确（v0.1.0 含 → v1.0.0 不含），不可延后 |
| Memory 复杂度 | 首个版本用最简算法（固定 decay 30 天 + 手动 reinforce），v0.5 再迭代 |

---

## 备选方案（Alternatives）

### A. 延长时间线到 20 周（**采纳**）

如本决策所述。

**采纳理由：** 唯一满足"不削减范围 + 不降低质量 + 用户 2h/天 限制"三约束的方案。

### B. 拆分 v0.1-core / v0.1-full（**未采纳**）

v0.1-core（12 周）：Agent/AgentSet/Workflow + Hello + KnowledgeScope/KnowledgeItem + queryKnowledge/getKnowledgeItem  
v0.1-full（+8 周）：追加 Memory + MemoryReconciler + recordMemory/queryMemory

**未采纳理由：**

- 用户已明确决策"Memory 全部进 v0.1"，违反用户决策
- 拆分会让 v0.1 概念变模糊（社区难以理解"v0.1 是哪一个"）
- 实际上节省的只是"Phase 3 延后"，并未减少工作量

### C. 招募 1 名贡献者（**未采纳**）

招募 1 名贡献者承担 40-50h 工作量，主攻 Adapter / Hello Agent / 测试。

**未采纳理由：**

- 招募本身需要 2-3 周投入（写招募帖 / 准备 onboarding / 沟通）
- 招募失败的风险存在，等于延长时间线 + 浪费招募投入
- 用户当前偏好"先做出来再开放"（无社区贡献者时更可控）
- 项目早期不适合分配关键模块给陌生人（违反 6.2 权限最小化精神）

### D. 不变，公开声明超预算（**未采纳**）

12 周不变，README/ROADMAP 顶部明示"v0.1 范围超出预算，滚动交付"。

**未采纳理由：**

- 违反宪法 15.4（技术债务不可悄悄累积）—— 即使公开，scope 仍悄悄超出
- 用户已决策"全部进 v0.1"，12 周不可能完成该范围
- "滚动交付"会导致版本号语义混乱（社区无法判断"当前可用版本"）

---

## 决策依据（Rationale）

本决策选择 A（延长时间线）而非其他备选，依据如下：

1. **用户决策优先**：用户已明确"全部进 v0.1"，任何削减 Memory 的方案都违反用户决策
2. **宪法一致性**：A 方案是唯一不触发 15.4（技术债务）的方案
3. **风险可控**：20 周时间线对单人 2h/天 是可执行的（无认知/体力风险）
4. **公开透明**：ADR 形式显式记录决策与后果（社区可追溯）
5. **阶段可见**：4 Phase 拆分让进度可视化，**降低"5 个月黑暗期"风险**

---

## 实施（Implementation）

按以下顺序执行（依据宪法 14.4 强门禁）：

1. ✅ 本 ADR 落地（`docs/adr/0004-v01-scope-extension-knowledge-and-memory.md`）
2. ⏳ ADR-0001 v1 范围声明
3. ⏳ ADR-0002 知识管理能力设计
4. ⏳ ADR-0003 Memory 持久化记忆设计
5. ⏳ [CONSTITUTION.md](../../CONSTITUTION.md) v0.1.0 → v0.2.0
6. ⏳ L1 Architecture 更新
7. ⏳ L1 Spec 更新
8. ⏳ L2 模块设计（4 个 L2 文档）
9. ⏳ Phase 1 实施（第 1-10 周）— `v0.1.0-alpha`
10. ⏳ Phase 2 实施（第 11-14 周）— `v0.1.0-beta`
11. ⏳ Phase 3 实施（第 15-18 周）— `v0.1.0-rc`
12. ⏳ Phase 4 打磨（第 19-20 周）— `v0.1.0`

---

## 参考（References）

- [CONSTITUTION.md](../../CONSTITUTION.md) v0.1.0 第十五条（质量第一性）
- [CONSTITUTION.md](../../CONSTITUTION.md) 第十一条 1（破坏性变更需走 ADR）
- [CONSTITUTION.md](../../CONSTITUTION.md) 第十四条（设计流程规范）+ 14.4 强门禁 + 14.5 MVP 例外
- [ROADMAP.md](../../ROADMAP.md)（待同步更新至 20 周）
- [L1-architecture.md](../design/L1-architecture.md)（待更新至 6 CRD / 6 method）
- [L1-system-spec.md](../spec/L1-system-spec.md)（待更新）
- [README.md](../../README.md)（待更新至"5 大基础能力"）

---

## 签署

本 ADR 由项目发起人于 **2026-07-23** 批准生效（依据宪法 14.5 MVP 例外，单点评审）。