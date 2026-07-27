# superteam-a2a 项目宪法

> **版本**：v0.5.0
> **生效日期**：v0.1.0 于 2026-07-23；**v0.2.0 于 2026-07-23 同日**升级（新增第二条 9 款 2.9"记忆可追溯"，依据 ADR-0004）；**v0.3.0 于 2026-07-23 同日**升级（新增第十六条"会话与上下文管理"）；**v0.4.0 于 2026-07-24**升级（第十六条 §16.1 修订：明确模型上下文窗口 = 1M tokens、50% 红线 = 500K tokens、新增"按实际水位判断"执行细则）；**v0.5.0 于 2026-07-24**升级（依据 ADR-0005：平台自有实现改为 Python-first，测试/文档/类型检查门禁同步 Python 化）
> **最高纲领**：本文件是 `superteam-a2a` 项目的最高纲领，所有架构决策、代码实现、流程规范都应与本文件保持一致。如有冲突，**以第十五条（质量第一性）为准**；如需修改本文件，须经维护者团队审批并记录变更原因。

---

## 序言

`superteam-a2a` 是一个基于 Google A2A 协议的、Kubernetes 原生的、多 Agent 框架互通的编排平台。我们致力于让 LangChain、AutoGen、CrewAI、Semantic Kernel、Strands、Smolagents 等任何主流 Agent 框架构建的 Agent，都能作为一等公民在 Kubernetes 上运行、彼此发现、协作完成复杂任务。

本宪法确立项目不可动摇的根本原则，确保系统始终朝着**可控、可信、可演进、社区友好**的方向发展。

> **风格说明**：本项目是 Apache 2.0 开源项目，由单人维护者投入 ~2h/day 运营。宪法条款主要面向**长期约束**，而非短期 KPI；执行强度按"**影响质量 / 安全 / 兼容性**"分级——核心条款用 MUST，非核心条款用 SHOULD，社区规则用 MAY。

---

## 第一条 使命宣言

`superteam-a2a` 的使命是：**基于 Google A2A 协议，构建一个 Kubernetes 原生的、多 Agent 框架互通的编排平台，让任何主流 Agent 框架构建的 Agent 都能作为一等公民在集群上运行、彼此发现、协同完成复杂任务**。

我们追求的不是 demo，而是一个**生产级**、**社区友好**、**长期演进**的开源系统。

**对外承诺**：
- 对**用户**：任何符合 A2A 协议的 Agent 都能接入；任何集群规模都能水平扩展
- 对**贡献者**：清晰的贡献路径、低门槛的提案通道、透明的决策记录
- 对**上游**：与 A2A 协议、Kubernetes Operator 生态、Python Agent 框架社区保持紧密兼容

---

## 第二条 核心价值观（不可妥协）

### 2.1 协议优先（Protocol First）
所有 Agent 间的通信必须遵循 A2A 协议规范。即便性能更优，也不允许绕过 A2A 进行私有通信。
- ✅ 正确：通过 A2A 调用其他 Agent
- ❌ 错误：Agent 之间直接共享内存 / 私有 RPC / in-process call

### 2.2 多框架多元主义（Multi-Framework Pluralism）
**不与任何 Agent 框架绑定**。LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents 等都是一等公民。
- Adapter 是薄薄一层（5 行 YAML 原则）
- 不得为某一框架优化而牺牲其他框架的体验
- 跨框架调用必须走 A2A，禁止 adapter 私有直通

### 2.3 可观测性即基础设施（Observability as Infrastructure）
没有可观测性的 Agent / Operator 不允许上线。所有任务必须可追踪、可回放、可调试。
- 每个任务必须有唯一 `trace_id`，贯穿所有 Agent
- Prometheus 指标、OpenTelemetry trace、结构化日志必须开箱即用
- 失败可归因（例：哪个 A2A RPC、哪个 Pod、哪个 Span）

### 2.4 失败是常态（Failure is the Default）
所有跨 Agent 调用 / K8s 操作必须考虑失败：超时、重试、降级、补偿链路必须显式设计。
- 每次 A2A RPC 必须有超时与重试策略
- 每个长任务必须有断点续跑能力（基于 K8s Job / Workflow CRD 状态）
- Operator 必须是**幂等**的（reconciliation loop 多次触发不破坏状态）

### 2.5 显式优于隐式（Explicit > Implicit）
Agent / Workflow / Adapter 的输入输出契约、能力描述、依赖关系必须**显式声明**，禁止"黑魔法"。
- Agent Card 必须可读、可验证、可版本化
- CRD 字段必须显式（禁止 `any`、禁止动态 schema）
- 拒绝"运行时探测"式的隐式适配

### 2.6 Backward Compatibility is a Promise（向后兼容是承诺）
公共 API（A2A 消息、CRD schema、CLI、Helm chart values）对用户是**承诺**。
- 任何破坏性变更必须走 ADR + 至少一个 minor 版本弃用期
- API 稳定性 v1.0.0 之前可放宽，但 v1.0.0 之后必须遵守 Semver
- CRD 必须有 conversion webhook（v1alpha1 ↔ v1beta1 ↔ v1）

### 2.7 人类拥有最终否决权（Human in the Loop）
Operator / Agent 默认是辅助工具，对外不可逆动作必须有人类审批节点。
- 涉及删除生产 namespace、强制 cordon、跨集群联邦等动作必须二次确认
- 默认走"低风险 → 高风险"渐进授权
- 维护者保留对 main 分支的最终否决权

### 2.8 资源可控（Resource is a First-Class Concern）
K8s 资源（CPU / 内存 / 存储 / 网络 / API server QPS）都是设计约束，不是事后优化。
- 每个 Agent / Workflow 必须有 ResourceQuota / LimitRange
- Operator 自身必须有 leader election + 自身资源限制
- 资源超限 = 熔断 + 告警，不静默失败

### 2.9 记忆可追溯（Memory Traceability）

Agent 的持久化记忆（Persistent Memory）是 `superteam-a2a` 的核心差异化能力之一。Memory 与显性知识（KnowledgeItem）共享 4 级作用域（industry / organization / team / project），并附加正交的 agent-private 可见性维度。

**承诺**：

- ✅ 每条 Memory 必须**可追溯**——能定位到创建它的 Agent、触发它的 Task、引用的 KnowledgeItem
- ✅ 每条 Memory 必须有**显式生命周期**——`confidence` 评估、衰减（decay）、强化（reinforce）机制（具体算法由 ADR-0003 定义）
- ✅ 每条 Memory 必须**挂载在 KnowledgeScope 上**——不允许存在 scope-less 的"游离记忆"
- ✅ Memory 的可见性遵循 KnowledgeScope 继承规则 + agent-private 正交维度（5 维矩阵）

**反模式**：

- ❌ 不得为简化实现省略 `confidence` / `decay` / `scope` 字段
- ❌ 不得让 Memory 绕过 A2A 协议在 adapter 间直接传递
- ❌ 不得静默聚合跨级 Memory（如 project → industry）而无显式 ADR 授权
- ❌ 不得把 Memory 当作"会话上下文"使用（会话上下文不属于持久化记忆范畴）

**实施**：具体 CRD schema、A2A method 字段、生命周期算法由 ADR-0003（Memory 设计，待写）定义；ADR-0004 已授权 v0.1 范围包含 Memory。

---

## 第三条 架构红线

### 3.1 分层严格

系统必须严格分为以下五层，**禁止跨层调用，禁止反向依赖**：

```
① 接入层 (kubectl / Helm / UI / CLI)
② 编排层 (Operator / Controllers / Workflow Engine)
③ 资源模型层 (CRDs: Agent / AgentSet / Workflow / Conversation)
④ 通信层 (A2A Protocol Adapter + Discovery)
⑤ 运行时层 (Agent Pods / Sidecar / External Agents)
```

每一层只能依赖下一层，不得跨越。

### 3.2 Operator 模式约束
- 控制器逻辑必须是**幂等**的（reconcile 多次 = 一次结果）
- 必须支持 leader election（`--leader-elect`）
- 必须使用 workqueue（不直接调 API server）
- 状态更新走 `Status` 子资源（不与 `Spec` 混用）
- 必须为关键资源注册 Finalizer（避免删除泄漏）

### 3.3 CRD 生命周期
- **CRD 必须有版本演进路径**（v1alpha1 → v1beta1 → v1）
- 跨版本必须提供 conversion webhook
- 删除 CRD 字段必须先 deprecated，再下一个 major 移除
- 字段命名遵循 Kubernetes API Conventions（`camelCase` + `kebab-case` 资源）

### 3.4 Agent 隔离
- 每个 Agent 必须在**独立 Pod** 中执行（多容器 Sidecar 模式允许）
- **禁止 Agent 共享可变状态**（除非通过 A2A 显式通信）
- Agent 之间的通信只允许通过 A2A 协议
- 生产环境必须配置 NetworkPolicy / PodSecurityStandards

### 3.5 协议兼容
- 必须支持 A2A 协议最新稳定版
- 不得破坏向后兼容性
- 破坏性变更必须走 ADR 流程（第十二条）

### 3.6 MCP 与 A2A 的边界
- **MCP** 用于 Agent ↔ Tool / Data Source 的连接
- **A2A** 用于 Agent ↔ Agent 的连接
- 两者职责清晰，**禁止混用**
- Operator 不引入 MCP 依赖（保持协议精简）

### 3.7 反依赖规则
- Operator 不得直接 import 任何 Agent 框架（LangChain / AutoGen / CrewAI 等）
- 框架交互通过 Adapter 子模块（语言无关的协议边界）
- 第三方 HTTP 调用必须通过 A2A 客户端，不直连

### 3.8 Python-first 实现边界
- 平台自有代码（Operator / A2A Core / Adapter SDK / Knowledge / Memory / Hello Agent）使用 **Python 3.12+**
- 标准 A2A 类型与传输优先复用官方 Python SDK；不得无理由 fork 或重复实现上游协议
- 平台公共边界必须有严格类型：Pydantic model / `typing.Protocol` / 显式 JSON Schema；禁止未约束 `Any` 穿过公共 API
- 网络与 K8s I/O 采用 async-first；禁止在 event loop 中直接执行阻塞 K8s/HTTP/CPU 密集操作
- 第三方 Agent Runtime 保持语言无关，可为 Python / JavaScript / .NET / Java / Rust；跨语言只通过 A2A 或 Adapter localhost 边界
- 任何平台核心模块偏离 Python、引入原生扩展或新增第二核心语言，必须先经 ADR 批准

---

## 第四条 Agent & Adapter 标准

### 4.1 Agent Card 规范
每个 Agent 必须发布标准 A2A Agent Card（Serve 在 `.well-known/agent.json`），包含：
- `name`：唯一标识，遵循 kebab-case
- `description`：使用**程序员语言**描述能力，禁用营销话术
- `skills`：可测试、可验证的技能列表
- `input_modes` / `output_modes`：支持的输入输出格式
- `version`：语义化版本
- `protocol_version`：A2A 协议版本
- 禁止出现"擅长"、"优秀"、"强大"等模糊词

**反例**：
```json
{"description": "一个强大的代码编写助手，能力优秀"}
```

**正例**：
```json
{
  "name": "python-codegen",
  "description": "基于 Claude 的 Python 代码生成与重构 Agent，输入为自然语言需求或函数签名，输出为符合 PEP8 + type hints 的代码 diff",
  "skills": ["code-generation", "code-refactor", "pytest-scaffold"],
  "input_modes": ["text"],
  "output_modes": ["text", "file-diff"],
  "version": "0.1.0",
  "protocol_version": "0.3"
}
```

### 4.2 Adapter Contract（适配器契约）
每个 Agent 框架必须有一个 Adapter 子模块，承诺：
- ✅ **5 行 YAML 接入**：用户只需写 5 行 YAML 即可将框架 Agent 暴露为 A2A 服务
- ✅ **零业务侵入**：Adapter 不修改框架源码
- ✅ Sidecar 模式：Adapter 与 Agent 框架同 Pod 部署，通过 localhost 通信
- ✅ **协议透明**：调用方只看到 A2A 接口，不感知底层框架

### 4.3 单一职责
- 一个 Agent 只做一件事
- 复合能力必须拆分为多个 Agent + Workflow 编排

### 4.4 资源约束
- 每个 Agent Pod 必须有 `resources.requests` 与 `resources.limits`
- 禁止缺失资源限制的 Agent 进入生产
- 资源超限 OOMKilled 必须有清晰的告警与 ConfigMap 记录

### 4.5 工具使用约束
- 所有外部能力通过 **MCP Server** 提供（Agent 框架侧）
- Adapter 不替 Agent 框架实现工具
- 工具调用必须有审计日志（OpenTelemetry Span）

### 4.6 上下文管理
- 每个 Agent 必须有**最大上下文上限**
- Adapter 必须实现 summarization 或 truncation 策略
- 超出上限必须显式报错，而非静默截断

### 4.7 评测驱动
- 每个官方 Adapter 必须有 **Golden Adapter**（参考实现）
- 关键 Agent 的评测结果纳入 CI 流水线
- 社区贡献 Adapter 提交时必须附 Golden Example

---

## 第五条 编排标准

### 5.1 任务拆解
- 任务拆解结果必须是**结构化 DAG**（`Workflow` CRD 的 `spec.tasks` 字段）
- 每个节点必须有明确的输入/输出契约（JSON Schema）
- 拆解结果必须经过校验（CRD validation webhook）后才执行

### 5.2 团队组建（AgentSet）
- AgentSet 用于定义同质 Agent 集群（scale by HPA / KEDA）
- Agent 匹配必须基于 **Agent Card 能力匹配**
- 不允许硬编码 Agent 列表
- 匹配失败必须有明确的降级策略（v0.1: 错误状态 + 事件）

### 5.3 流程选择优先级
```
Sequential / Parallel  >  Hierarchical  >  Dynamic / Debate
```
- 优先使用 sequential / parallel（map / reduce 子任务）
- hierarchical 仅在必要时使用，且必须有 ADR 说明必要性
- dynamic / debate 等高级模式仅用于实验，不进入生产

### 5.4 Workflow 边界
- 一个 Workflow 一次只完成一个"业务任务"
- 不允许 Workflow 嵌套 Workflow（避免递归和资源爆炸）
- Workflow 必须有 `ttlSecondsAfterFinished`（默认 86400）

### 5.5 集群边界
- 跨集群 Agent 调用走 A2A over federation（v2 范畴）
- v1 范围内只承诺单集群语义

---

## 第六条 安全规范

### 6.1 身份认证
- Agent 间通信使用 **mTLS**（cert-manager + SPIFFE/SPIRE 推荐）
- Operator ↔ API server 走 K8s ServiceAccount + RBAC
- 禁止匿名调用

### 6.2 权限最小化
- 每个 Agent Pod 运行时使用独立 ServiceAccount
- 禁止使用 `default` ServiceAccount
- 凭据通过 External Secrets Operator / Vault 注入，**禁止硬编码**
- Pod 不允许以 `privileged` / `hostNetwork` / `hostPID` 运行

### 6.3 镜像供应链
- 所有官方镜像必须签名（cosign / sigstore）
- 镜像必须基于 distroless 或最小化 base
- 依赖必须定期扫描（trivy / grype）
- CI 集成 SBOM 生成

### 6.4 Pod Security Standards
- 默认 `restricted` profile
- v0.1 阶段允许 `baseline`（限制性），但必须标注 ADR
- 任何 root 容器必须评审

### 6.5 Network Policy
- 默认拒绝所有 ingress/egress
- 仅显式声明 allow 规则
- Agent 间通信强制通过 A2A 端口（默认 8080）

### 6.6 审计日志
- K8s audit log 不可关闭
- A2A 消息必须留痕（OpenTelemetry Span + 结构化日志）
- 审计日志**不可篡改**（append-only）
- 保留期不少于 90 天

### 6.7 危险操作拦截
涉及以下操作必须有人类审批（通过 GitOps / ArgoCD / kubectl confirmation）：
- 删除 CRD / 整个 namespace
- 强制 cordon / drain 节点
- 跨集群联邦操作
- 升级 Operator 本身
- 公开镜像 / 公开 Helm chart

---

## 第七条 可观测性标准

### 7.1 Metrics（指标）
**Prometheus 强制指标**（命名遵循 `superteam_*` 前缀）：
- 任务成功率（按 Workflow / Agent 分维度）
- A2A RPC 延迟分布（p50 / p95 / p99）
- A2A RPC 错误码分布
- Token 消耗（输入 / 输出 / 缓存）
- Operator Reconcile 延迟 / 重试次数
- Agent Pod 资源使用率
- Adapter 框架特定指标（每个 Adapter 必须暴露）

### 7.2 Trace（链路追踪）
- 每次任务必须有唯一 `trace_id`，贯穿所有 Agent
- 使用 **OpenTelemetry** 标准
- 必须支持跨 Pod、跨 Service、跨 Cluster 的 trace 关联

### 7.3 Logs（日志）
- 结构化日志（JSON 格式）
- 必须包含：`trace_id`、`agent_id`、`task_id`、`workflow_name`、`namespace`、`timestamp`
- **禁止**打印敏感信息（API Key、Token、个人数据）
- Operator 与 Agent 日志统一打到 stdout，由 K8s / Loki 收集

### 7.4 K8s Events
- 所有 Operator 状态变更必须 emit K8s Event
- 关键失败（reconcile error / Webhook reject）必须 emit Warning 级 Event
- Event 命名遵循 `<Component><Action><Result>` 风格

### 7.5 Evals（评测）
- 每个官方 Adapter 至少有 **5 个** Golden Cases
- 核心 Agent 至少有 **10 个** Golden Cases
- 评测集纳入 CI，每次发版前必须通过
- 关键 Adapter 的回归测试覆盖率 ≥ 80%

### 7.6 仪表盘
- 必须提供 Grafana 仪表盘 JSON（位于 `dashboards/`）
- 仪表盘覆盖：Operator 健康 / Agent 性能 / A2A RPC / 资源使用

---

## 第八条 资源与成本控制

### 8.1 设计原则
- 资源是设计约束，不是事后优化
- **所有资源上限必须可配置**（避免硬编码束缚未来演进）
- 随 LLM token 单价下降、推理效率提升，相关上限应**同步下调**而非废弃
- 配置是契约的一部分，变更需走 PR 评审

### 8.2 默认上限（v0.1 阶段参考值）

| 项目 | 默认值 | 配置项 |
|------|--------|--------|
| 单 Agent Pod CPU request | 100m | `resources.agent.cpu.request` |
| 单 Agent Pod CPU limit | 1000m | `resources.agent.cpu.limit` |
| 单 Agent Pod memory request | 256Mi | `resources.agent.memory.request` |
| 单 Agent Pod memory limit | 1Gi | `resources.agent.memory.limit` |
| 单 Agent 任务 max_tokens | 50,000 | `cost.agent.max_tokens` |
| 单 Agent 任务最大执行时间 | 10 分钟 | `cost.agent.max_duration_sec` |
| 单 Agent 任务最大重试次数 | 3 | `cost.agent.max_retries` |
| 单 Workflow max_tokens | 200,000 | `cost.workflow.max_tokens` |
| 单 Workflow 最大成本（美元） | $5 | `cost.workflow.max_cost_usd` |
| 单 Workflow 最大执行时间 | 30 分钟 | `cost.workflow.max_duration_sec` |
| Operator 资源 request | 100m / 256Mi | `resources.operator.requests` |
| Operator 资源 limit | 1000m / 1Gi | `resources.operator.limits` |

> **演进说明**：上述默认值为 v0.1 阶段的保守估算。随着 token 单价下降与模型能力提升，预计每季度评审一次，逐步放宽 `max_tokens` 限制。**预期方向**：1 年内单 Workflow `max_tokens` 上限放宽至 500,000+。

### 8.3 配置管理
- 所有资源相关配置集中在 Helm `values.yaml`
- 遵循 schema 校验（`values.schema.json`）
- 不同环境（dev / staging / prod）通过 Helm values 覆盖
- 配置变更记录在 `charts/CHANGELOG.md`

### 8.4 超限行为
- 超限自动熔断 + K8s Event 告警（不静默失败）
- Workflow 级别超限通知发起者（v0.1: K8s Event；v0.5: 通知 API）
- 超限事件必须落审计日志，便于后续优化配置

### 8.5 优化策略
- 优先使用小模型（Haiku）做规划与轻量任务
- 仅在关键节点使用大模型（Opus / Sonnet）
- 启用 prompt caching 降低成本
- 配置化的模型路由：不同类型任务可配置不同模型（v0.5 规划）

---

## 第九条 测试策略

### 9.1 单元测试
- 核心模块覆盖率 **≥ 80%**；协议类型、错误模型、状态机和生命周期算法目标 **≥ 90%**
- Operator 的可测试业务逻辑必须从 Kopf handler 中分离，使用 fake/mock Kubernetes client 编写单元测试
- 测试框架：`pytest` + `pytest-asyncio` / AnyIO；属性与模糊测试使用 Hypothesis
- async 测试必须真实 `await` 目标协程；禁止用同步 wrapper 掩盖 event-loop 问题

### 9.2 集成测试
- 每个 Controller 路径必须有集成测试
- API 升级（CRD conversion）必须有 E2E 测试
- Python 没有 `envtest` 的完全等价替代：mock/fake 只能作为单元测试，关键 reconcile / watch / webhook / leader failover 必须在 `kind` / `k3d` 真实集群验证
- HTTP/A2A 集成测试使用 ASGI test client / `httpx` / `respx`，并覆盖 timeout、取消、重试与 mTLS 失败路径

### 9.3 E2E 测试
- 使用 `kind` / `k3d` 启动真实 K8s 集群
- Workflow 完整流程必须有 E2E 测试
- E2E 测试必须使用 mock LLM（避免成本）

### 9.4 Conformance 测试
- A2A 协议必须有 conformance 套件（参考 `google-a2a/conformance`）
- 每个 Adapter 必须通过 conformance 套件
- 防止协议升级时 silent break

### 9.5 评测驱动
- 每个 Adapter 必须有 **Golden Adapter**（参考实现 + 测试）
- 评测指标必须包含：成功率、延迟、token 效率、安全性
- 评测结果纳入发版门槛（不通过不允许发版）

### 9.6 契约测试
- CRD schema 变更必须有 schema 兼容性测试
- CLI 命令必须有契约测试（防止 silent break）
- Pydantic model → JSON Schema → CRD OpenAPI 生成必须 deterministic，CI 必须验证生成结果无漂移

### 9.7 Python 静态质量与供应链
- `uv.lock` 必须提交；CI 使用 `uv sync --frozen`
- Ruff format/lint、Pyright strict、Bandit、pip-audit 是合并门禁
- 禁止浮动生产依赖；依赖升级必须通过完整测试和漏洞扫描
- 禁止未解释的公共 `Any`、全局 `# type: ignore`、全局 Ruff ignore
- Python 镜像仍必须执行 SBOM、Trivy/Grype 扫描与 Cosign/Sigstore 签名

---

## 第十条 文档标准

### 10.1 必须文档化的内容
- **ADR**（架构决策记录）：所有重大架构决策（第十二条）
- **Agent Card**：每个 Agent 的能力描述（自动生成）
- **CRD API 文档**：每个 CRD 的字段说明（自动生成 + 示例）
- **Helm chart 文档**：values 字段说明
- **Runbook**：常见故障的处理流程（`docs/runbooks/`）
- **README**：每个子项目的使用说明
- **CHANGELOG**：每次发版必须更新

### 10.2 文档位置
```
docs/
├── adr/                  # 架构决策记录
├── api/                  # CRD API 文档
├── runbooks/             # 故障处理手册
├── adapters/             # Adapter 指南
├── examples/             # YAML 示例
└── tutorials/            # 端到端教程
```

### 10.3 代码注释
- 所有 public module / class / function / method 必须有 Python docstring，并满足 Pyright 可解析的类型签名
- docstring 遵循统一格式（项目在 L3 锁定 Google 或 NumPy 风格后不得混用）
- 关键算法必须解释 "Why" 而非 "What"
- 测试注释必须是"为什么写这个测试"而非"测试做了什么"
- `# type: ignore` / Ruff `noqa` 只能最小范围使用，必须附错误码与原因

### 10.4 文档站
- v0.5 规划使用 MkDocs 或 Docusaurus
- 文档与代码同仓库（`docs/`）
- 自动部署到 GitHub Pages

---

## 第十一条 API 与版本管理

### 11.1 破坏性变更
以下变更必须走 **ADR 流程**（第十二条）：
- 修改本宪法
- 改变 A2A 协议兼容性
- 修改 CRD Schema（字段删除 / 类型变更 / 必填化）
- 改变 CLI 命令 / Helm chart values
- 改变安全相关行为

### 11.2 版本管理
- **二进制版本**：遵循 **Semver**（MAJOR.MINOR.PATCH）
- **CRD 版本**：独立演进（每个 CRD 自己的 API 版本路线）
- **A2A 协议版本**：与上游 `google-a2a/A2A` 同步
- 每次发版必须有 `CHANGELOG.md` 条目
- Git Tag 必须与版本号一致

### 11.3 弃用策略
- 弃用必须提前 **一个 minor 版本**通知
- 字段标记 `// Deprecated: ...` 或 `+optional` + `deprecated: true`
- 提供迁移指南（`docs/migrations/`）
- 弃用期内同时支持新旧两套接口
- 至少保持 **2 个 minor 版本** 的兼容性

### 11.4 CRD 演进
- 新字段添加：直接加，可选
- 字段类型变更：必须 deprecate 旧字段，引入新字段
- 字段删除：必须先废弃 1 个 minor 版本，下次 major 移除
- 重大重命名：必须走 ADR

---

## 第十二条 决策机制

### 12.1 ADR 流程
1. **提出 Issue**：描述背景与动机
2. **撰写 ADR 草案**：`docs/adr/NNNN-title.md`
3. **评审讨论**：维护者评审（lazy consensus + binding vote）
4. **通过后实施**：未通过则关闭 Issue

ADR 模板必须包含：
- 标题（Title）
- 状态（Status：Proposed / Accepted / Deprecated / Superseded）
- 背景（Context）
- 决策（Decision）
- 后果（Consequences，正面与负面）
- 备选方案（Alternatives）

### 12.2 决策模型
- **Minor 决策**：维护者 lazy consensus（72h 内无反对即通过）
- **Major 决策**：维护者 binding vote（明确同意/反对，多数通过）
- **宪法修改**：见 12.3

### 12.3 宪法修改
- 宪法修改必须经**维护者全员同意**
- 修改记录在 `CONSTITUTION-CHANGELOG.md`
- 重大修改需要回滚方案

### 12.4 公开性
- 所有 ADR 在 GitHub 公开
- 评审讨论在 GitHub Issues / Discussions
- 决策记录永久可追溯

---

## 第十三条 社区治理

### 13.1 角色
- **维护者（Maintainer）**：拥有 main 分支合并权
- **评审者（Reviewer）**：可 Approve PR，可被维护者提升
- **贡献者（Contributor）**：提交过 PR / Issue 的人
- **用户（User）**：使用 superteam-a2a 的开发者

### 13.2 贡献流程
1. Fork → Feature Branch → Pull Request
2. PR 必须通过 CI（测试 + lint + conformance）
3. PR 必须有 ≥ 1 个维护者 Approval
4. main 分支受保护，必须走 PR 合并
5. 不允许 force-push main

### 13.3 行为准则
- 所有参与者必须遵守 `CODE_OF_CONDUCT.md`
- 维护者保留移除违规者的权利
- 决策偏见必须公开讨论

### 13.4 发布流程
1. 维护者创建 Release PR（更新版本号 + CHANGELOG）
2. 跑完整测试 + Conformance 套件
3. 创建 Git Tag（`vX.Y.Z`）
4. GitHub Actions 自动构建镜像 + 发布 Helm chart
5. 发布公告（GitHub Discussions + Discord）

### 13.5 维护者轮换
- 维护者连续 90 天无活动 → 自动 inactive
- 连续 180 天 inactive → 退出 maintainer 角色
- 退出者欢迎随时回归

### 13.6 维护者责任
- 72h 内响应 Priority Bug
- 每周至少 4h 投入（与"2h/day"维护者本人并存）
- 维护 A2A Python SDK、Kopf、Kubernetes Python/async client 与 Python 运行时版本兼容性

### 13.7 资金与赞助
- 接受 GitHub Sponsors / Open Collective
- 资金使用公开记录（`FUNDING.md`）
- 资金不得用于个人，只能用于项目运营（基础设施 / 文档 / 设计）

---

## 第十四条 设计流程规范（Design-First Process）

> **本条是项目执行的根本流程，违反本条等同于违反宪法。**

### 14.1 基本原则
本项目采用**自顶向下的分层设计（Top-Down Layered Design）**：
1. **设计先于实现（Design Before Code）** —— 任何代码提交前必须有对应的设计文档
2. **从总体到模块，再到文件粒度，依次分层**
3. **每一层设计完成后必须经过评审**
4. **上层设计评审未通过，禁止开始下一层设计**（强门禁）
5. **每一层必须有对应的设计文档 + Spec 文档**（两个产物，不可省略其一）

### 14.2 设计分层

| 层级 | 名称 | 设计文档 | Spec 文档 | 颗粒度 |
|------|------|----------|-----------|--------|
| **L1** | 总体架构设计 | `docs/design/L1-architecture.md` | `docs/spec/L1-system-spec.md` | 系统、子系统、核心组件 |
| **L2** | 模块设计 | `docs/design/L2-modules/*.md`（按模块） | `docs/spec/L2-module-specs/*.md`（按模块） | 模块 API、依赖、状态 |
| **L3** | 文件级 Spec | — | `docs/spec/L3-file-specs/*.md`（按模块） | 函数签名、类型、接口契约 |

> L3 阶段设计文档与 Spec 文档合并为一份（文件粒度的"设计"本身就是 Spec）。

### 14.3 评审流程
1. **提交**：设计者提交 PR（含设计文档 + Spec 文档）
2. **评审**：维护者评审（≥ 1 人 Approval）
3. **通过**：进入下一层设计
4. **驳回**：修改后重新提交评审，不可绕过

### 14.4 强制门禁（Hard Gates）
- ❌ **未完成 L1 设计** → 禁止开始 L2 设计
- ❌ **L1 评审未通过** → 禁止开始 L2 设计
- ❌ **未完成 L2 设计** → 禁止开始 L3 Spec
- ❌ **L2 评审未通过** → 禁止开始 L3 Spec
- ❌ **未完成 L3 Spec** → 禁止提交该模块的实现代码
- ❌ **跳过评审环节** → 视为流程违规，PR 必须驳回

### 14.5 MVP 例外（Critical）
**v0.1 MVP 阶段**（Phase 1-2），允许以下例外：
- L1 设计与 L2 设计可合并为一份（若模块数 ≤ 3）
- L3 Spec 可由完整类型签名 + docstring + `# Why:` 代码注释替代
- 评审可由维护者本人单点批准（但必须在 PR 描述中明确"单点评审"理由）

**例外撤销触发**：v1.0.0 发布后，所有例外自动失效。

### 14.6 评审记录
- 每次评审必须在 PR 中留下评审意见
- 通过的评审以 PR Approval 形式留痕
- 重大分歧以 ADR 形式归档（见第十二条）

---

## 第十五条 质量第一性原则（Quality as First Principle）

> **本条是项目所有行为的最高原则，凌驾于其他一切考量之上。任何条款、决策、行为与本条冲突时，以本条为准。**

### 15.1 绝对性声明

**质量是 superteam-a2a 项目的第一性原则（First Principle），在任何时候都不可妥协。**

不得为任何理由牺牲质量，包括但不限于：

- ❌ **不得**为赶进度牺牲质量
- ❌ **不得**为简化实现牺牲质量
- ❌ **不得**为节省资源成本牺牲质量
- ❌ **不得**为"先上线再修复"牺牲质量
- ❌ **不得**为减少工作量牺牲质量
- ❌ **不得**为迎合外部压力（含社区要求）牺牲质量
- ❌ **不得**为"看起来差不多"牺牲质量
- ❌ **不得**为快速达到 stars 目标牺牲质量

### 15.2 质量的内涵

"质量"在本项目中是一个多维度概念，必须同时满足：

| 维度 | 含义 | 对应条款 |
|------|------|----------|
| **正确性** | 代码与设计一致，逻辑无误，行为可预测 | 第 3、9 条 |
| **安全性** | 无已知漏洞，符合安全规范 | 第 6 条 |
| **可观测性** | 行为可追踪、可调试、可回溯 | 第 7 条 |
| **可维护性** | 代码清晰、可读、可演进 | 第 4、5 条 |
| **可测试性** | 关键逻辑有测试覆盖 | 第 9 条 |
| **一致性** | 与宪法、设计、Spec 保持一致 | 第 14 条 |
| **兼容性** | A2A 协议 / K8s API / CRD 兼容 | 第 3、11 条 |
| **文档完备** | 文档与代码同步更新 | 第 10 条 |
| **社区友好** | 清晰的贡献路径、透明的决策 | 第 12、13 条 |

任何一维度的妥协都是质量妥协。

### 15.3 决策排序

当面临权衡时，按以下顺序决策：

```
1. 先评估是否影响质量
2. 如影响质量 → 拒绝该方案
3. 在所有"不影响质量"的方案中，按其他维度（性能、成本、进度）择优
```

**示例**：

- "跳过 CRD conversion webhook 可以加快 v0.1 进度" → ❌ 拒绝（违反向后兼容承诺）
- "降低镜像签名要求可以简化 CI" → ❌ 拒绝（违反安全规范）
- "用更简单的 Agent 状态机可以减少代码量" → ✅ 如果在性能、可维护性、可测试性上等价或更优
- "用更贵的托管服务可以提升可靠性" → ✅ 如果可靠性是关键质量属性

### 15.4 技术债务

**任何形式的技术债务都不可"悄悄累积"**：

- ✅ **可以接受的技术债务** — 必须满足：
  - 通过 ADR 明确记录（第十二条）
  - 有明确的偿还计划与时间表
  - 在 PR 中显式标注（不隐藏在提交信息中）
- ❌ **不可接受的技术债务**：
  - "先这样，回头再改"（无 ADR、无计划）
  - "测试不重要"（违反第九条）
  - "安全可以先放一放"（违反第六条）
  - "向后兼容可以以后再说"（违反第二条 2.6）

### 15.5 质量红线（绝对禁止）

以下行为**任何时候**都禁止，违者必须驳回：

- 🚫 提交未经测试的关键路径代码
- 🚫 关闭或跳过失败的测试以让 CI 通过
- 🚫 提交后门、调试代码、特权绕过代码到主分支
- 🚫 注释掉关键安全检查
- 🚫 关闭或降低 Python 类型/静态检查（Pyright strict / Ruff）以"快速通过"
- 🚫 删除失败的可观测性埋点
- 🚫 在 PR 中绕过 Code Review
- 🚫 提交与 ADR 决策不一致的实现
- 🚫 提交未经签名 / 扫描的镜像
- 🚫 跳过 Conformance 测试以"加速发版"

### 15.6 质量与效率的权衡

**质量与效率并非对立**：

- 长期看，高质量带来高效率（少 bug、少返工、少技术债）
- 短期看似"低质量更快"，实际是借用未来的时间
- "快"不等于"省时间"，而是用未来的时间填补现在的窟窿

**当被要求牺牲质量时**，开发者有义务：

1. 明确指出该妥协将影响的具体质量维度
2. 量化长期成本（未来的 bug 修复、技术债利息）
3. 提出不影响质量的替代方案
4. 如对方仍坚持，必须通过 ADR 留痕，不可"私下妥协"

### 15.7 质量评审

任何 PR / 设计 / Spec 评审，**质量是首要评审标准**：

- 通过评审 ≠ 跑通测试 ≠ 功能正确
- 必须评估：是否符合宪法？是否引入技术债？是否降低可维护性？
- 评审者否决一项 PR 时，必须引用具体质量条款

### 15.8 与其他条款的关系

本条与第二条（核心价值观）、第三条（架构红线）、第六条（安全规范）、第七条（可观测性）、第九条（测试策略）、第十一条（API 兼容性）形成**质量保障体系**：

```
第十五条（质量第一性）← 最高原则
       ↓
第二条（核心价值观）← 8 条不可妥协原则
       ↓
第三、六、七、九、十一条 ← 具体质量维度
       ↓
第十四条（设计流程）← 保障质量的流程
       ↓
第十二、十三条（决策与治理）← 保障质量的制度
```

任何条款与本条冲突时，**以本条为准**。

---

## 第十六条 会话与上下文管理（Session & Context Continuity）

> **背景**：本项目由单人维护者以 ~2h/day、跨多次会话（session）方式推进，强依赖持久化记忆（Memory）在会话间传递上下文。上下文一旦在单次会话内耗尽而未保存，将导致进度断裂、决策丢失、返工——这直接违反第十五条（质量第一性）中的**一致性**与**可维护性**维度。本条确立会话级别的状态保全纪律。

### 16.1 上下文水位红线（Hard Gate）

> **v0.4.0 修订（2026-07-24）**：明确模型上下文窗口基线 + "按实际水位判断"执行细则。原 50% 阈值保持不变，但执行方法从"按启发式自估"改为"按窗口基线量化"。

#### 16.1.1 上下文窗口基线与红线换算

| 项 | 取值 | 说明 |
|----|------|------|
| **模型上下文窗口** | **1,000,000 tokens**（1M） | 项目默认使用的模型上下文窗口基线 |
| **§16.1 红线（50%）** | **500,000 tokens** | 触及此阈值即触发 §16.2 流程 |
| **预留余量** | 至少 100,000 tokens | 用于 §16.2 保存动作本身 + 临时推理 |
| **§16.1 红线等效表述** | "距窗口基线 50%" | 避免每次判断时手算绝对值 |

> **窗口变更说明**：若模型上下文窗口发生变化（如升级到 2M），应同步更新本表 + 变更日志 + ADR。**红线百分比（50%）保持不变**，仅基线绝对值调整。

#### 16.1.2 触发条件

- ❌ 当单次会话的上下文占用**预计或实际超过 50%**（≥ 500K tokens）时，**禁止**继续开展新的实质性工作（新增设计、编码、大范围重构）。
- ✅ 触及 50% 水位时，必须立即进入 **16.2 保存-暂停-交接** 流程。
- 50% 是**保守下限**，其目的是为"保存状态"这一动作本身预留充足的上下文余量。宁可早停，不可晚停。

#### 16.1.3 按实际水位判断（v0.4.0 新增）

- **不得**仅依据"上一会话越权记录"或"经验惯性"判定本会话应停。
- **必须**依据本会话实际产出的可观察证据：
  1. **Read 累计**：本会话已 Read 的文件总字符数 ÷ ~3.5 ≈ tokens（粗估）
  2. **Write 累计**：本会话已 Write 的文件总字符数 ÷ ~3.5 ≈ tokens（粗估）
  3. **工具调用结果**：每个工具结果 ≈ 500-5000 tokens（视结果大小）
  4. **对话轮次**：每轮用户消息 + 助手回复 ≈ 1000-10000 tokens
- **估算方法**：将上述 4 项累加 → 除以 1M → 得水位百分比；≥ 50% 即触发 §16.2。
- **当不确定水位时**：优先按 §16.1 触发（即宁可保守）；但不应将"上一会话触及红线"作为本会话的预设前提。

#### 16.1.4 典型水位参照表（v0.4.0 新增）

| 已 Read | 已 Write | 工具调用 | 对话轮次 | 估算水位 | 是否触发 §16.2 |
|---------|----------|----------|----------|----------|----------------|
| 0 | 0 | 0 | 1 | ~1% | ❌ |
| 50KB | 30KB | 5 | 3 | ~5% | ❌ |
| 200KB | 100KB | 10 | 5 | ~10% | ❌ |
| 500KB | 300KB | 15 | 8 | ~25% | ❌ |
| 1MB | 500KB | 20 | 10 | ~50% | ✅ **触发红线** |
| 2MB+ | 1MB+ | 30+ | 15+ | >80% | ❌ 已超红线（事后） |

### 16.2 保存-暂停-交接三步动作

触及水位红线时，必须**按序**完成以下三步，缺一不可：

1. **保存项目状态（Save）**
   - 将本次会话的关键进展、决策、未决事项写入持久化记忆（`memory/` 下的 session 档案 + 更新主项目档案与 `MEMORY.md` 索引）。
   - 保存内容必须包含：已完成事项、当前所处任务节点、**下次会话的明确起手动作**、任何未落盘的临时结论。
   - 相关设计/文档产物必须已落盘（不得停留在"待写"状态而无记录）。

2. **暂停（Pause）**
   - 停止一切新的实质性工作，不得为"再多做一点"而突破水位。

3. **交接提示（Handoff Prompt）**
   - 向用户明确输出一段提示，内容至少包含：
     - 已触及上下文水位、状态已保存的声明；
     - 状态保存到了哪个文件（可追溯）；
     - **下次会话应如何起手**（复制即可用的一句话入口）；
     - 建议用户**开启新会话**继续。

### 16.3 与其他条款的关系

- 本条是第十五条（质量第一性）中"一致性 / 可维护性"维度在**会话层面**的具体保障机制。
- 本条服务于持久化记忆纪律，与 2.9（记忆可追溯）互为补充：2.9 约束 Agent 的记忆，本条约束**维护者工作会话**的状态连续性。
- 本条不适用于纯咨询、查询类的轻量会话（无实质性产物产出者）。

---

## 附录 A：术语表

| 术语 | 定义 |
|------|------|
| **A2A** | Agent-to-Agent Protocol，Google 主推的 Agent 通信协议 |
| **MCP** | Model Context Protocol，Anthropic 主推的 Agent-Tool 连接协议 |
| **Adapter** | superteam-a2a 与各 Agent 框架之间的薄薄一层 |
| **Agent Card** | A2A 协议规定的 Agent 能力描述 JSON |
| **AgentSet** | 同质 Agent 集群 CRD（类似 Deployment for Agents） |
| **Workflow** | 多 Agent 协作的 DAG 编排 CRD |
| **Operator** | Kubernetes Operator 模式实现的控制器 |
| **Python-first** | 平台自有代码默认使用 Python 3.12+；第三方 Agent Runtime 仍语言无关 |
| **Kopf** | 本项目 Python Operator 的事件处理框架，可靠性行为必须经 kind 验证 |
| **Pydantic** | 项目自有 DTO、配置与 CRD Schema 的严格类型/校验基础 |
| **CRD** | Custom Resource Definition，自定义资源 |
| **Sidecar** | 与 Agent 同 Pod 部署的 Adapter 容器 |
| **Conformance** | 协议兼容性测试 |
| **Golden Adapter** | 参考实现 + 测试用例，作为 Adapter 正确性的基线 |
| **Helm Chart** | superteam-a2a 的 K8s 安装包 |
| **Trace ID** | 贯穿整个任务链路的唯一标识 |
| **ADR** | Architecture Decision Record，架构决策记录 |
| **L1 设计** | 总体架构设计文档（系统、子系统、核心交互） |
| **L2 设计** | 模块设计文档（按模块拆分，含 API、依赖、状态） |
| **L3 Spec** | 文件级 Spec（函数签名、类型、接口契约） |
| **Reconcile** | Operator 一次完整的"观察-差异-行动"循环 |
| **Finalizer** | K8s 资源删除前的清理钩子 |
| **MVP** | Minimum Viable Product，最小可行产品 |
| **维护者** | Maintainer，拥有 main 分支合并权 |

---

## 附录 B：参考标准

- [ADR-0005: Python-first 全栈技术栈迁移](docs/adr/0005-python-first-technology-stack.md)
- [A2A Protocol Specification](https://github.com/google-a2a/A2A)
- [A2A Python SDK](https://github.com/google-a2a/a2a-python)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Kubernetes API Conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md)
- [Kubernetes Operator Pattern](https://kubernetes.io/docs/concepts/extendkubernetes/operator/)
- [Kopf — Python Operator Framework](https://kopf.readthedocs.io/en/latest/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [kubernetes_asyncio](https://github.com/tomplus/kubernetes_asyncio)
- [Pydantic](https://docs.pydantic.dev/latest/)
- [uv](https://docs.astral.sh/uv/)
- [OpenTelemetry Specification](https://opentelemetry.io/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [Semantic Versioning](https://semver.org/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Network Policy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [kagent (设计参考)](https://github.com/kagent-dev/kagent)
- [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)
- [CNCF Code of Conduct](https://github.com/cncf/foundation/blob/main/code-of-conduct.md)

---

## 附录 C：版本历史

| 版本 | 日期 | 变更 | 决策人 | ADR |
|------|------|------|--------|-----|
| v0.1.0-draft | 2026-07-23 | 初稿：参考 AgentCompany 宪法 v0.1.3-draft 适配，开源/K8s-native/多框架场景；新增维护者治理 / API 版本管理 / 镜像供应链 / Pod Security；保留 15 articles + 3 appendices 结构 | 项目发起人 | — |
| v0.1.0 | 2026-07-23 | **正式采纳**：v0.1.0-draft 经项目发起人批准升级为正式版本；移除 `-draft` 后缀；保留全部条款；生效日期为本日 | 项目发起人 | — |
| v0.2.0 | 2026-07-23 | **新增条款**：第二条新增 2.9 款"记忆可追溯"（Memory Traceability）—— 4 级作用域 + agent-private 正交维度 + confidence / decay / scope 三项强制字段；同日生效，依据 ADR-0004 | 项目发起人 | ADR-0004 |
| v0.3.0 | 2026-07-23 | **新增条款**：新增第十六条"会话与上下文管理"（Session & Context Continuity）—— 50% 上下文水位红线 + 保存-暂停-交接三步动作 + 与第十五条 / 2.9 的关系；同日生效 | 项目发起人 | — |
| v0.4.0 | 2026-07-24 | **条款修订**：第十六条 §16.1 修订——明确模型上下文窗口基线 = 1M tokens、50% 红线 = 500K tokens、新增 §16.1.3"按实际水位判断"执行细则、§16.1.4 典型水位参照表；同日生效 | 项目发起人 | — |
| v0.5.0 | 2026-07-24 | **架构条款修订**：依据 ADR-0005 将平台自有实现改为 Python 3.12+ Python-first；新增 §3.8；§9 测试/静态质量、§10 docstring、§13 维护职责、§14 L3 注释例外、§15 类型检查红线同步 Python 化 | 项目发起人 | ADR-0005 |

> **背景说明**：本宪法以 AgentCompany 内部宪法 v0.1.3-draft 为蓝本，重新设计以适配公开开源、Kubernetes-native、多 Agent 框架互通的 `superteam-a2a` 项目。**保留**了质量第一性（第十五条）、设计优先（第十四条）、ADR 流程（第十二条）、协议优先（2.1）、可观测性即基础设施（2.3）、失败是常态（2.4）、单一职责（4.3）等核心条款；**重写**了架构红线（Operator / CRD / Adapter）、Agent 标准（Adapter Contract）、安全（K8s RBAC / Pod Security / NetworkPolicy）、可观测（Prometheus 强制）、成本控制（K8s 资源语义）、社区治理（13 条新增）；**新增**了多框架多元主义（2.2）、向后兼容是承诺（2.6）、API 与版本管理（11 条）、MVP 例外（14.5）。

---

---

> **签署**：
> 本宪法 **v0.1.0** 版由 `superteam-a2a` 项目发起人于 2026-07-23 正式批准生效。
> 本宪法 **v0.2.0** 版由项目发起人于 **2026-07-23 同日**升级批准生效，新增第二条 2.9 款"记忆可追溯"（依据 ADR-0004）。
> 本宪法 **v0.3.0** 版由项目发起人于 **2026-07-23 同日**升级批准生效，新增第十六条"会话与上下文管理"（Session & Context Continuity），确立 50% 上下文水位的保存-暂停-交接纪律。**v0.4.0 版**于 **2026-07-24**修订第十六条 §16.1，明确模型上下文窗口基线 = 1M tokens、50% 红线 = 500K tokens，并新增"按实际水位判断"执行细则 + 典型水位参照表，纠正此前因未明确窗口基线导致的误判。**v0.5.0 版**于 **2026-07-24**依据 ADR-0005 将平台自有实现确立为 Python 3.12+ Python-first，并同步测试、文档、类型检查与供应链质量门禁。
> 所有贡献者应被视为已阅读并同意遵守本宪法。
> 贡献者通过提交 PR 即视为接受本宪法的约束。
> 本宪法的任何修改须经维护者团队审批，并记录在 `CONSTITUTION-CHANGELOG.md` 与本文件附录 C。
