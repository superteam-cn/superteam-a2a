# ADR-0001: v1 版本范围声明（v0.1.0 / v0.5.0 / v1.0.0 / 永久 out-of-scope）

> **本 ADR 授权 v0.1.0 / v0.5.0 / v1.0.0 的范围边界**。详细 CRD 字段 / API method / 算法由 L1 Architecture / L1 Spec / ADR-0002 / ADR-0003 定义。本 ADR 不重复"如何实现"，只界定"何时包含什么"。
>
> **2026-07-24 实现栈说明**：本 ADR 的版本范围与功能边界继续有效；其中 Go / kubebuilder 等实现语言假设已由 [ADR-0005](0005-python-first-technology-stack.md) supersede。现行平台自有实现采用 Python-first。

---

## 状态

| 字段 | 值 |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-07-23 |
| **Deciders** | 项目发起人（CoderZhangfujiang） |
| **Reviewers** | 项目发起人（依据宪法 14.5 MVP 例外，单点评审） |
| **Supersedes** | 无 |
| **Superseded by** | [ADR-0005](0005-python-first-technology-stack.md)（仅 Go/实现栈条款；版本范围继续有效） |
| **Related** | [ADR-0004](0004-v01-scope-extension-knowledge-and-memory.md)（v0.1 范围重定，已写）、ADR-0002（知识管理设计，待写）、ADR-0003（Memory 设计，待写） |

---

## 背景（Context）

### 版本管理依据

[CONSTITUTION.md](../../CONSTITUTION.md) 第十一条 2：

> 二进制版本遵循 **Semver**（MAJOR.MINOR.PATCH）。
> CRD 版本独立演进（每个 CRD 自己的 API 版本路线）。
> A2A 协议版本与上游 `google-a2a/A2A` 同步。

### 版本演进路径

```
v0.1.0  →  v0.5.0  →  v1.0.0  →  v1.1.0  →  v2.0.0
   │          │          │          │          │
   │          │          │          │          └─ 协议 / 架构重大变更
   │          │          │          └─ 增量功能（向后兼容）
   │          │          └─ 第一个 stable release（API 锁定）
   │          └─ 最后一个 minor（API 接近稳定）
   └─ 第一个公开 alpha
```

### 各版本定位

| 版本 | 定位 | 关键承诺 | 依赖 |
|---|---|---|---|
| **v0.1.0** | 第一个公开 alpha | 5 大能力 + 6 CRD + Hello Agent 可跑 | ADR-0004 |
| **v0.5.0** | 最后一个 minor（API 接近稳定） | 第一个 framework adapter + SSE streaming | v0.1.0 反馈 |
| **v1.0.0** | 第一个 stable | API 锁定 + 6 框架 adapters + Dashboard | v0.5.0 反馈 |

### 决策必要性

版本范围若不显式声明，会出现两类问题：

1. **范围爆炸**：每个版本都"再加一点"，最终 v1.0.0 永远不到（违反宪法 15.4 技术债务不可悄悄累积）
2. **方向漂移**：用户/社区期望与维护者实际交付不一致，丧失信任

本 ADR 用"版本 = 时间盒 + 范围集"的语义，提前固化 3 个版本的承诺边界。

---

## 决策（Decision）

### 决策 1：v0.1.0 范围（2026-07-08 → 2027-01-20，20 周）

#### 1.1 包含（In-Scope）

**5 大基础能力**：发现 / 通信 / 监控 / 编排 / **知识管理（含 Memory）**

**6 个 CRD**：
- `Agent`（v1alpha1）—— 单个 Agent 实例 + Adapter Sidecar
- `AgentSet`（v1alpha1）—— 同质 Agent 集群（Deployment 风格）
- `Workflow`（v1alpha1）—— 多 Agent DAG 编排
- `KnowledgeScope`（v1alpha1）—— 4 级作用域（industry / organization / team / project）
- `KnowledgeItem`（v1alpha1）—— 显性知识（人工撰写）
- `Memory`（v1alpha1）—— 持久化记忆（Agent 生成，含 lifecycle）

**6 个 A2A method**：
- `a2a.sendMessage`（sync）
- `a2a.getTask`
- `a2a.queryKnowledge`
- `a2a.getKnowledgeItem`
- `a2a.recordMemory`
- `a2a.queryMemory`

**4 个 Controller**：Agent / AgentSet / Workflow / **MemoryReconciler**

**2 个特殊 Agent**：Hello Agent（参考实现，无框架）/ Knowledge Service（CRD-driven）

**运维配套**：
- Helm chart 基础（Operator Deployment + RBAC + NetworkPolicy + ServiceAccount）
- E2E 测试（kind + hello-world 跑通）
- GitHub Actions CI（lint + unit + e2e）
- Prometheus 指标（`superteam_*` 前缀，强制指标）
- 结构化 JSON 日志（K8s stdout）
- K8s Events（所有 Operator 状态变更）

**交付方式**：4 Phase 阶段发版
- Phase 1（第 1-10 周）：`v0.1.0-alpha`
- Phase 2（第 11-14 周）：`v0.1.0-beta`
- Phase 3（第 15-18 周）：`v0.1.0-rc`
- Phase 4（第 19-20 周）：`v0.1.0`

#### 1.2 不包含（Out-of-Scope，推迟到 v0.5.0+）

- ❌ Framework Adapter（LangChain / AutoGen / CrewAI / SK / Strands / Smolagents）—— Hello Agent 是唯一内置
- ❌ SSE Streaming（`a2a.subscribeTask` / `a2a.cancelTask`）
- ❌ `Conversation` CRD
- ❌ Web UI / Dashboard
- ❌ KEDA / HPA 自动扩缩
- ❌ 多集群联邦
- ❌ CRD conversion webhook（v1alpha1 单版本足够）
- ❌ 完整 Conformance 套件（仅基础 A2A 协议测试）

### 决策 2：v0.5.0 范围（v1.0.0 前最后一个 minor）

#### 2.1 包含（In-Scope）

新增项：

- **第一个 framework adapter**：**LangChain**（按宪法 4.7 Golden Adapter 强制）
- **SSE Streaming**：新增 `a2a.subscribeTask` / `a2a.cancelTask`（v0.1 推到 v0.5）
- **CRD 版本升级**：所有 CRD `v1alpha1` → `v1beta1`，**字段集冻结**
- **Conversion Webhook**：v1alpha1 ↔ v1beta1 兼容
- **`Conversation` CRD**：A2A 长会话状态
- **第二个 framework adapter**：AutoGen

升级项：

- E2E 测试覆盖 2 个 framework adapters 完整路径
- 完整 Conformance 套件（参考 `google-a2a/conformance`）
- 评测驱动（每个 adapter ≥ 5 个 Golden Cases）

#### 2.2 不包含（Out-of-Scope，推迟到 v1.0.0）

- ❌ CrewAI / Semantic Kernel / Strands / Smolagents adapters
- ❌ Web UI / Dashboard
- ❌ 多集群联邦

### 决策 3：v1.0.0 范围（第一个 stable）

#### 3.1 包含（In-Scope）

**6 个 framework adapters 全覆盖**：
- LangChain · AutoGen · CrewAI · Semantic Kernel · Strands · Smolagents
- 每个 adapter 有 Golden Adapter + ≥ 10 个 Golden Cases（宪法 7.5）

**完整 A2A 协议**：所有 method + Stream + Artifact

**CRD 升级到 `v1`**：
- 6 个 CRD 全部 `v1beta1` → `v1`
- 字段集**冻结**（破坏性变更需走 ADR + 1 个 minor 弃用期）

**Web Dashboard**：
- React 19 + Vite + TanStack Query（按宪法 3.1 / L1 Architecture §3.1）
- 功能：CRD 列表 / Workflow 状态可视化 / Memory 浏览

**社区贡献通道**：
- `CONTRIBUTING.md` 实际开发步骤
- Issue 模板（已建，需打磨）
- "Good First Issue" 清单
- 自动 CHANGELOG 生成

**Helm chart 1.0**：
- OCI registry 发布（ghcr.io 或 harbor）
- `values.schema.json` 完整（已存在 v0.1 草案）
- 多环境覆盖（dev / staging / prod values）

#### 3.2 不包含（Out-of-Scope）

- ❌ 多集群联邦（推 v2）
- ❌ Vector DB 抽象（每个 Agent 自带）
- ❌ 闭源特性（Apache 2.0 always）

### 决策 4：永久 out-of-scope（永远不做）

| 项 | 不做的理由 |
|---|---|
| **闭源 / 企业版** | Apache 2.0 always；违反用户硬约束 |
| **多云联邦**（v1 范围） | 复杂度极高；v2 范畴；v1 只承诺单集群 |
| **Vector DB 抽象** | 每个 Agent 框架自带选择（Chroma / Pinecone / Weaviate），强行抽象会破坏宪法 2.2 多框架多元主义 |
| **非 SDLC 模板**（如法律 / 营销） | 社区可自由贡献；项目本身只维护 SDLC 模板 |
| **对任何 Agent 框架的偏好** | 宪法 2.2 明确禁止；Operator **不得 import** 任何框架代码 |
| **不替代上游 A2A / MCP** | 项目是 A2A 的 **runtime**，不是 A2A 协议的 **实现者**；A2A 协议变更需跟上游 |
| **协议绕过通信**（agent-to-agent 直连） | 违反宪法 2.1 协议优先 |
| **跳过可观测性** | 违反宪法 7.x（无 observability 不允许上线） |
| **跳过测试的"快速发版"** | 违反宪法 9.x + 15.5 质量红线 |

### 决策 5：验收标准（v1.0.0 必须满足才发版）

#### 5.1 功能完整性

- [ ] 6 个 framework adapters 全部通过 Golden Adapter 测试
- [ ] 6 个 CRD 全部支持 v1alpha1 → v1beta1 → v1 三阶段转换
- [ ] A2A 协议全 method 实现且通过 conformance 套件
- [ ] Memory 5 维矩阵完整（industry/org/team/project + agent-private）
- [ ] Knowledge 4 级作用域继承规则完整实现
- [ ] Demo 视频（60-90s）录制完成

#### 5.2 质量门禁（宪法 9.x）

- [ ] 单元测试覆盖率 ≥ **80%**（核心模块）
- [ ] Operator 逻辑 100% 单元测试覆盖
- [ ] 每个 Controller 路径有集成测试（基于 envtest）
- [ ] Workflow 完整流程有 E2E 测试（kind 集群）
- [ ] A2A Conformance 套件 100% 通过
- [ ] 每个官方 Adapter ≥ 10 个 Golden Cases，纳入 CI
- [ ] CRD schema 兼容性测试（schema 变更不破坏旧 manifest）
- [ ] CLI 命令契约测试

#### 5.3 安全门禁（宪法 6.x）

- [ ] Agent ↔ Agent 通信强制 mTLS（cert-manager 颁发）
- [ ] 每个 Agent Pod 独立 ServiceAccount（无 default SA）
- [ ] Pod Security Standards 默认 `restricted`
- [ ] Network Policy 默认 deny-all，显式 allow
- [ ] 所有官方镜像签名（cosign keyless）
- [ ] 所有官方镜像 trivy 扫描无 High/Critical 漏洞
- [ ] 审计日志保留 ≥ 90 天（append-only）

#### 5.4 可观测性门禁（宪法 7.x）

- [ ] Prometheus 强制指标全覆盖（reconcile / RPC / agent / workflow）
- [ ] OpenTelemetry Trace 贯穿（Workflow → Task → A2A → Agent）
- [ ] 结构化 JSON 日志（必含 trace_id / agent_id / task_id / workflow / namespace）
- [ ] Grafana Dashboard JSON 提交（Operator Health / A2A RPC / Agent Resources / Workflow）
- [ ] K8s Events：Normal + Warning 级正确 emit

#### 5.5 文档门禁（宪法 10.x）

- [ ] 所有 CRD 字段有 API 文档（自动生成 + 示例）
- [ ] 所有 Adapter 有用户指南 + Golden Adapter 参考
- [ ] 每个官方 Agent 有 Agent Card 描述
- [ ] Runbook（常见故障处理）覆盖 Operator / Adapter / Workflow
- [ ] README：5 分钟快速上手 + 60 秒 Demo 视频
- [ ] CHANGELOG.md 每个发版版本有记录

### 决策 6：发布与弃用策略

#### 6.1 发版策略

- **Semver 严格遵守**（MAJOR.MINOR.PATCH）
- **每次发版必须**：更新 CHANGELOG.md + 创建 Git Tag + GitHub Actions 自动构建镜像 + 发布 Helm chart
- **Git Tag 与版本号一致**：`v0.1.0` / `v0.5.0` / `v1.0.0`
- **Pre-release tag**：alpha / beta / rc 在 v0.x 阶段正常使用

#### 6.2 弃用策略（宪法 11.3）

- 弃用必须提前 **1 个 minor 版本**通知
- 字段标记 `// Deprecated: ...` 或 `+optional` + `deprecated: true`
- 提供迁移指南（`docs/migrations/`）
- 弃用期内同时支持新旧两套接口
- 至少保持 **2 个 minor 版本**的兼容性
- 字段删除必须先废弃 1 个 minor 版本，下次 major 移除

#### 6.3 CRD 演进路径

- **v0.1.x**：`v1alpha1`（字段可自由变更）
- **v0.5.x**：`v1alpha1` + `v1beta1` 双版本（v1beta1 字段集稳定）
- **v1.0.x+**：`v1beta1` + `v1` 双版本（v1 字段冻结）
- 每次升级提供 conversion webhook

#### 6.4 破坏性变更判定

以下变更视为破坏性，必须走 ADR + 弃用期：

- 修改本宪法任何条款
- 改变 A2A 协议兼容性
- 修改 CRD Schema（字段删除 / 类型变更 / 必填化）
- 改变 CLI 命令 / Helm chart values
- 改变安全相关行为

---

## 后果（Consequences）

### 正面

- ✅ **范围显式**：3 个版本的承诺边界清晰，社区可预期
- ✅ **宪法一致**：本 ADR 与 ADR-0004 + CONSTITUTION v0.2.0 + L1 Architecture 全部一致
- ✅ **验收客观**：v1.0.0 的 5 类门禁（功能 / 质量 / 安全 / 可观测 / 文档）清晰可量化
- ✅ **永久 out-of-scope 明确**：避免"未来可能再加"的隐性范围爆炸
- ✅ **发布策略可执行**：Semver + 弃用期 + CRD 演进路径形成闭环

### 负面

- ⚠️ **v1.0.0 时间不确定**：依赖 v0.5.0 反馈，**预计 2027-Q3**（保守估算 v1.0.0）
- ⚠️ **永久 out-of-scope 可能过严**：未来若社区强烈需求某项 out-of-scope 功能，需重新走 ADR 推翻本 ADR（流程成本）
- ⚠️ **v0.5.0 CRD 升级风险**：`v1alpha1 → v1beta1` 的字段冻结后，v1.0.0 之前若发现字段遗漏需走 ADR
- ⚠️ **6 framework adapters 全覆盖工作量巨大**：v1.0.0 是 6 个框架 + 完整测试的工作量，单人 2h/天 可能需要 30-40 周

### 缓解措施

| 风险 | 缓解 |
|---|---|
| v1.0.0 时间不确定 | v0.5.0 发版时同步更新本 ADR 的"预计交付时间" |
| out-of-scope 过严 | ADR 流程本就是推翻本 ADR 的合法路径；新增永久 out-of-scope 项需 ADR |
| v0.5.0 CRD 冻结风险 | 14.5 MVP 例外窗口（v0.1.0 含 → v1.0.0 不含）允许小字段调整 |
| v1.0.0 工作量大 | 招募 2-3 名 framework 维护者（每个 adapter 1 人）；或拆出社区版 |

---

## 备选方案（Alternatives）

### A. 宽范围 v1（**采纳**）

如本决策所述：6 framework adapters + 完整 A2A + Dashboard + 社区通道。

**采纳理由：**
- 与宪法 2.2（多框架多元主义）一致 —— 所有框架必须支持
- 与宪法 7.5（每个 adapter ≥ 10 个 Golden Cases）一致 —— 评测驱动是质量保障
- 用户硬约束 1（Apache 2.0 开源 / 目标 3,000 stars）需要完整产品力

### B. 窄范围 v1（**未采纳**）

v1.0.0 = 2 个 framework adapters（LangChain + AutoGen）+ 核心 A2A + 无 Dashboard。

**未采纳理由：**
- 违反宪法 2.2（多框架多元主义）
- 与项目定位"任何主流 Agent 框架都能接入"不符
- 3,000 stars 目标难以达成（社区会问"为什么只支持 2 个框架"）

### C. 时间盒版本（**未采纳**）

取消 v1.0.0 概念，改为"滚动更新 + 持续集成"。

**未采纳理由：**
- 违反宪法 2.6（向后兼容是承诺）—— 无版本锁定意味着无兼容性承诺
- 违反宪法 11.2（Semver 严格遵守）
- 用户和社区无法判断"何时达到 stable"

### D. v1.0.0 仅交付 Operator（**未采纳**）

v1.0.0 = Operator + 6 CRD + 1 个 Hello Agent（不包含 framework adapters）。

**未采纳理由：**
- 违反宪法 2.2（多框架多元主义）
- 用户实际可用性低（只有 Hello Agent 不能解决真实问题）
- 与 ADR-0004 的 v0.1 范围重叠（v0.1 已有 6 CRD）

---

## 决策依据（Rationale）

本决策选择 A（宽范围 v1），依据如下：

1. **用户决策**：用户硬约束 1 明确"基于 Google A2A 实现 + 兼容主流框架"，框架覆盖必须完整
2. **宪法一致性**：A 方案与宪法 2.2 / 7.5 / 11.x 完全对齐
3. **社区信任**：6 framework adapters 全覆盖是 GitHub 3,000 stars 目标的必要条件
4. **质量优先**：v1.0.0 必须通过 5 类门禁（功能 / 质量 / 安全 / 可观测 / 文档），确保发布即可用

---

## 实施（Implementation）

### 立即（本会话内）

- [x] 本 ADR 落地（`docs/adr/0001-v1-scope-statement.md`）
- [ ] ADR-0002 知识管理能力设计（依赖 v0.1 范围明确）
- [ ] ADR-0003 Memory 持久化记忆设计（依赖 v0.1 范围明确）

### v0.1.0 周期（第 1-20 周）

按 [ROADMAP.md](../../ROADMAP.md)（已更新至 20 周）+ ADR-0004 实施：
- 第 1-10 周：Phase 1 → `v0.1.0-alpha`
- 第 11-14 周：Phase 2 → `v0.1.0-beta`
- 第 15-18 周：Phase 3 → `v0.1.0-rc`
- 第 19-20 周：Phase 4 → `v0.1.0`

### v0.5.0 周期（v1.0.0 发布前 1 个 minor）

- 6 个 CRD `v1alpha1 → v1beta1` + conversion webhook
- LangChain adapter + AutoGen adapter + Golden Adapter 测试
- SSE Streaming 实现（`a2a.subscribeTask` / `a2a.cancelTask`）
- `Conversation` CRD

### v1.0.0 周期

- 6 framework adapters 全覆盖 + Golden Cases
- 6 个 CRD `v1beta1 → v1` + conversion webhook
- Web Dashboard
- 完整 Conformance 套件
- 5 类门禁全部通过

---

## 参考（References）

- [CONSTITUTION.md](../../CONSTITUTION.md) v0.2.0 第十一条 2（版本管理）
- [CONSTITUTION.md](../../CONSTITUTION.md) 第十一条 3（弃用策略）
- [CONSTITUTION.md](../../CONSTITUTION.md) 第二条 2（多框架多元主义）
- [CONSTITUTION.md](../../CONSTITUTION.md) 第二条 6（向后兼容是承诺）
- [CONSTITUTION.md](../../CONSTITUTION.md) 第九条（测试策略）+ 第七条（可观测性）+ 第六条（安全规范）
- [ADR-0004](0004-v01-scope-extension-knowledge-and-memory.md)（v0.1 范围重定）
- [ROADMAP.md](../../ROADMAP.md)（已更新至 20 周）
- [L1-architecture.md](../design/L1-architecture.md)（v0.1 / v1.0 范围基线）
- [L1-system-spec.md](../spec/L1-system-spec.md)（CRD / API 详细规格）

---

## 签署

本 ADR 由项目发起人于 **2026-07-23** 批准生效（依据宪法 14.5 MVP 例外，单点评审）。