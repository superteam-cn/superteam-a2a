# superteam-a2a — L1 总体架构设计

> **层级**: L1（总体架构）
> **版本**: **v0.2.0**（Python 重写，ADR-0005 触发；2026-07-24 评审通过）
> **状态**: ✅ **已评审通过**（依据 [`docs/reviews/l1-python-stack-migration-review.md`](../reviews/l1-python-stack-migration-review.md) 2026-07-24；10 维度全 PASS）
> **配套 Spec**: [`docs/spec/L1-system-spec.md`](../spec/L1-system-spec.md)（**v0.2.0** 同日同步评审通过）
> **配套评审**: [`docs/reviews/l1-python-stack-migration-review.md`](../reviews/l1-python-stack-migration-review.md)（✅ 2026-07-24）
> **依据**: [`CONSTITUTION.md`](../../CONSTITUTION.md) **v0.5.0**（§3.8 Python-first 实现边界 + §9.7 Python 静态质量 + §10.3 docstring + §13.6 维护 A2A Python SDK/Kopf）
> **设计输入**：[ADR-0001](../adr/0001-v1-scope-statement.md)（v1 范围）/ [ADR-0002](../adr/0002-knowledge-management-design.md)（知识管理）/ [ADR-0003](../adr/0003-memory-design.md)（Memory）/ [ADR-0004](../adr/0004-v01-scope-extension-knowledge-and-memory.md)（v0.1 范围）/ [ADR-0005](../adr/0005-python-first-technology-stack.md)（**Python-first 实现栈**）
> **supersedes**: v0.1.0 Go baseline（[`docs/reviews/l1-review-architecture.md`](../reviews/l1-review-architecture.md) 2026-07-23 通过；**仅 supersede Go / kubebuilder / controller-runtime / client-go 实现条款；wire contract 与业务语义完全继续有效**）
> **MVP 例外**: §14.5 适用（v0.1.0 → v1.0.0；本版本仍属 MVP 阶段，单点评审）

---

## 0. 阅读指南

本文档定义 `superteam-a2a` 的 **L1 总体架构**：使命、边界、子系统、核心组件、数据流。**不**涉及具体模块 API、函数签名、CRD 字段（这些在 L2 / L3 层级定义）。**wire contract（A2A JSON-RPC + CRD YAML + K8s Service/DNS）保持 v0.1.0 不变**，仅替换实现栈为 Python。

**读者**：L2 模块设计者、贡献者、评审者、架构委员会。

**配套文档**：
- **L1 契约**：[`L1-system-spec.md`](../spec/L1-system-spec.md) — CRD Schema / API / 错误模型 / 状态机
- **宪法**：[`CONSTITUTION.md`](../../CONSTITUTION.md) — 最高纲领（v0.5.0 = Python-first）
- **ADR-0005**：[`docs/adr/0005-python-first-technology-stack.md`](../adr/0005-python-first-technology-stack.md) — Python-first 元决策
- **路线图**：[`ROADMAP.md`](../../ROADMAP.md) — 阶段交付物

---

## 1. 使命与边界

### 1.1 使命

让任何主流 Agent 框架（LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents 等）构建的 Agent 都能作为**一等公民**在 Kubernetes 上运行、彼此通过 A2A 协议发现与协作，最终完成复杂任务。**平台自有代码以 Python 3.12+ 编写**（依据 ADR-0005），与第三方 Agent Runtime 通过 A2A/localhost 边界解耦。

### 1.2 系统边界

**系统内**（v0.1 Python-first 实现）：
- **Operator 控制器**：Kopf handlers + 独立 async reconciler service（替代 Go controller-runtime）
- **CRD 定义**（6 个 v1alpha1）：Agent / AgentSet / Workflow / KnowledgeScope / KnowledgeItem / Memory
- **Adapter 框架**：Sidecar 默认 / 同进程可选；`typing.Protocol` 契约；Python-native framework 同进程 plugin
- **协议层**：官方 `a2a-sdk`（Agent Card / Message / Task / Artifact / JSON-RPC）；项目自有的 4 个扩展 method（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）通过 compatibility adapter 注册
- **4 个 Controller**（Kopf handlers + Python services）：Agent / AgentSet / Workflow / MemoryReconciler
- **2 个特殊 Agent**：Hello Agent（Python 参考实现）/ Knowledge Service（Card-driven，Python，与 MemoryReconciler 共享 Deployment）
- **可观测性埋点**：`prometheus-client` + OpenTelemetry Python SDK + `structlog`
- **Helm Chart + 文档 + 仪表盘**

**系统外**（明确不实现）：
- Agent 框架内部实现（LangChain / AutoGen / CrewAI 等）→ 由各框架提供；Operator 不得依赖任何 framework（宪法 §3.7）
- LLM Provider 细节（OpenAI / Anthropic / Google）→ Agent 框架处理
- MCP Server 实现（Tool 连接）→ Agent 框架处理
- Vector DB → 由 Agent 框架选用；Memory/Knowledge 存储走 etcd（v0.1 不引入 Vector DB）
- 多集群联邦（v2 范畴）
- 业务 UI（K8s 生态用 k9s / kubectl；v1.0 引入 Dashboard）
- 知识图谱 / Knowledge Graph（v0.5+ 范畴）
- 自动化 scope-up（v0.1 手动 `kubectl patch`，v0.5+ KnowledgePromotionRequest）
- Memory 跨 cluster 联邦 / 静态加密 / 内容审核（v0.5+ 范畴）
- 平台原生扩展（Rust / Cython）→ 走 ADR（ADR-0005 §6.3）

### 1.3 价值主张

| 维度 | 承诺 |
|------|------|
| **对用户** | 5 行 YAML 把任意 Agent 暴露为 A2A 服务 |
| **对 Agent 框架作者** | 一份 Python Adapter 模板，社区零门槛支持 |
| **对 K8s 运维者** | 标准 CRD + Helm，跟 Deployment 一样运维 |
| **对社区** | Apache 2.0 + 透明 ADR + 公开演进 |
| **对贡献者** | Python-first 单语言栈，2h/day 维护可持续 |

---

## 2. 系统总览

### 2.1 一句话定义

> `superteam-a2a` 是一个 **Python 编写的 Kubernetes Operator + 一组 CRD + 一组 Adapter + 一份基于官方 a2a-sdk 的 A2A 协议实现 + 一个 Pydantic 类型层**，把多 Agent 编排语义映射到 K8s 原语。

### 2.2 架构鸟瞰

```
┌─────────────────────────────────────────────────────────────────┐
│  ① 接入层                                                        │
│  kubectl / Helm / (future) Dashboard / CLI                       │
└────────────────────────────────────────┬────────────────────────┘
                                         │ (CRD apply)
                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  ② 编排层（Operator · Python 3.12+ · Kopf + kubernetes_asyncio）│
│  Agent · AgentSet · Workflow · MemoryReconciler (Kopf handlers) │
│  (leader-elected via coordination.k8s.io/v1 Lease,              │
│   idempotent reconcile loops, single Python process)            │
│  ── handlers 仅做事件适配；业务逻辑放 async service ──           │
└────────────────────────┬────────────────────────────────────────┘
                         │ (creates / watches)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  ③ 资源模型层（CRDs · 6 个 v1alpha1 · Pydantic v2 → OpenAPI v3）│
│  Agent · AgentSet · Workflow                                    │
│  KnowledgeScope · KnowledgeItem · Memory                         │
└────────────────────────┬────────────────────────────────────────┘
                         │ (translates to)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  ④ 通信层（A2A Protocol · 6 method · 官方 a2a-sdk + adapter）   │
│  sendMessage · getTask  ←→  官方 a2a-sdk (Card / Message / Task)│
│  queryKnowledge · getKnowledgeItem  ←→  项目 extension router   │
│  recordMemory · queryMemory         ←→  项目 extension router   │
│  + K8s Service/EndpointSlice Discovery (single Python process)  │
└────────────────────────┬────────────────────────────────────────┘
                         │ (drives / observes)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  ⑤ 运行时层（Agent Pods · 2 个特殊 Agent）                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  Hello Agent     │  │  LangChain Agent │  │  AutoGen Agent │ │
│  │  ┌────┐  ┌────┐  │  │  ┌────┐  ┌────┐  │  │  ┌────┐  ┌────┐│ │
│  │  │Adpt│  │Agt │  │  │  │Adpt│  │Agt │  │  │  │Adpt│  │Agt ││ │
│  │  └────┘  └────┘  │  │  └────┘  └────┘  │  │  └────┘  └────┘│ │
│  │  uvicorn 8080    │  │  uvicorn 8080     │  │  uvicorn 8080  │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────┐                │
│  │  Knowledge Service（Card-driven · 单实例）  │                │
│  │  ┌─────────────────────────────────────┐    │                │
│  │  │  暴露 skills: query_knowledge +    │    │                │
│  │  │           get_knowledge_item +      │    │                │
│  │  │           record_memory + query_mem │    │                │
│  │  │  uvicorn 8080 (mTLS, single proc)   │    │                │
│  │  └─────────────────────────────────────┘    │                │
│  └─────────────────────────────────────────────┘                │
│                                                                  │
│  MemoryReconciler（Controller-only，不暴露 A2A）                 │
│   └─ reconcile loop: decay / reinforce / GC / eligibleForPromotion│
└─────────────────────────────────────────────────────────────────┘
                         │ (metrics / traces / logs)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  横切关注点（Cross-Cutting · Python 全栈）                       │
│  prometheus-client · OpenTelemetry Python · structlog           │
│  K8s Events · NetworkPolicy · RBAC                              │
│  admission webhook（Knowledge ↔ Memory 双向互斥）               │
│  Pydantic v2 strict types · Pyright strict · Ruff               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 关键架构原则

1. **CRD-first**：所有编排语义以 CRD 表达，kubectl / GitOps 是自然操作界面
2. **协议-immutable**：A2A 协议版本独立演进；Operator 优先复用官方 a2a-sdk，禁止 fork（ADR-0005 §3.2）
3. **Adapter 薄**：Adapter 是 200-500 行的 `typing.Protocol` 实现，非业务逻辑
4. **Sidecar 优先**：Adapter 与 Agent 同 Pod 部署（localhost 通信）；Python-native framework 可同进程 plugin
5. **幂等 reconcile**：所有 Controller 必须幂等（Kopf `kopf.index`/`kopf.resume`/`kopf.timer` 派生事件均幂等）
6. **async-first**：所有跨网络/K8s I/O 使用 async；阻塞 CPU 工作通过 `anyio.to_thread.run_sync` offload（ADR-0005 §6.1）
7. **typed-first**：公共边界 Pydantic v2 strict / `typing.Protocol`；禁止未约束 `Any` 穿过公共 API
8. **单进程原则**：含本地 TaskStore / Discovery cache / BM25 index / limiter state 的 Pod 默认单 Python worker / 单 event loop；水平扩展靠多 Pod（ADR-0005 §6.2）
9. **Observability-default**：指标 / Trace / 日志 / Events 必须开箱即用；新增 event-loop lag / thread-offload 指标
10. **社区友好**：所有 CRD 有详细字段说明，所有 Adapter 有 Golden Adapter 范例

---

## 3. 五层架构详解（Python 实现栈映射）

### 3.1 ① 接入层（Access Layer）

**职责**：用户与系统交互的入口。

**组件**：
- `kubectl apply -f agent.yaml` — 标准 K8s 工具
- `helm install` — 标准化部署
- `k9s` / `Lens` / `Octant` — 第三方 UI（系统不提供）
- **未来 v0.5+**：自研 Dashboard（React 19 + Vite + TanStack Query）

**输入**：YAML / Helm values
**输出**：CRD 对象（apply 至 API Server）

**反依赖规则**：接入层**不得**直接调用 A2A 协议客户端（必须通过 CRD 操作）。

### 3.2 ② 编排层（Orchestration Layer · Python + Kopf）

> **对应 L2 模块**：✅ **L2-2 Operator Core v0.2.0**（Python 重写 · 2026-07-24 评审通过；详见 [设计](../design/L2-modules/L2-operator-core.md) + [评审](../reviews/l2-2-operator-core-python-review.md)；模块 ID C-1 不变；4 Controllers + admission webhook + Leader Election + Finalizer + async-first + 错误模型 + 可观测性 + Helm values + RBAC + 测试策略 11 个主题）

**职责**：观察 CRD 变化，调度资源，使系统状态收敛到期望状态。

**核心组件**：

#### 3.2.1 Agent Controller
- **观察**：`Agent` CRD
- **Kopf 实现**：
  ```python
  # operator/handlers/agent.py（示意，详见 L2-2 / L3-1 Spec）
  @kopf.on.create('superteam-a2a.io', 'v1alpha1', 'agents')
  async def on_agent_create(spec, name, namespace, **kwargs): ...
  
  @kopf.on.update('superteam-a2a.io', 'v1alpha1', 'agents')
  async def on_agent_update(spec, status, name, namespace, **kwargs): ...
  
  @kopf.on.delete('superteam-a2a.io', 'v1alpha1', 'agents')
  async def on_agent_delete(name, namespace, **kwargs): ...
  ```
- **动作**：
  - 创建 / 更新 / 删除 Agent Pod（`kubernetes_asyncio`）
  - 配置 ServiceAccount / NetworkPolicy / ConfigMap
  - 注入 Adapter Sidecar 容器（PodSpec 合并）
  - 注册 / 反注册 Agent Card 至 Discovery（in-memory + EndpointSlice）
- **状态**：写入 `Agent.status`（`kopf.adopt` 状态子资源 patch）
- **业务逻辑分离**：handler 仅做事件适配 + 依赖解析；reconcile 逻辑放 `agent_reconciler.py` async service，便于单元测试（ADR-0005 §3.1）

#### 3.2.2 AgentSet Controller
- **观察**：`AgentSet` CRD
- **Kopf 实现**：同 Agent，使用 `kopf.on.update` + `kopf.timer` 周期 reconcile
- **动作**：类 Deployment 管理同质 Agent 副本
- **副本控制**：v0.1 仅 `replicas` 字段；KEDA/HPA 扩展推 v0.5+
- **状态**：`readyReplicas` / `availableReplicas`

#### 3.2.3 Workflow Controller
- **观察**：`Workflow` CRD
- **动作**：
  - 校验 DAG 结构（无环、依赖有效）— 在 `kopf.on.create` handler 内调用 `WorkflowValidator` 纯 Python 函数
  - 调度任务节点（创建 Kubernetes Job / 触发 A2A 调用）
  - 维护执行状态（task_state / dependencies met）
  - TTL 清理（`kopf.timer` 周期检查）
- **状态**：`Workflow.status.phase`（Pending / Running / Succeeded / Failed / Timeout）

#### 3.2.4 MemoryReconciler（v0.1 必需 · ADR-0003）
- **观察**：`Memory` CRD（cluster-wide watch）
- **Kopf 实现**：`kopf.timer(interval=60.0)` 周期 reconcile 全部 Memory
- **动作**：
  - **decay 算法**：`effectiveConfidence = confidence × exp(-elapsed_days / decayDays)`，< 0.1 → phase=Expired
  - **reinforce 算法**：命中 `memoryKey` 三元组时 `confidence += 0.05`（上限 1.0）、`reinforcedCount += 1`、衰减时钟重启
  - **GC**：`phase=Expired` 持续 7 天 → 删除（finalizer 保护）
  - **eligibleForPromotion 计算**：`confidence >= 0.85 && reinforcedCount >= 5` → 填 status 字段（**v0.1 仅计算**，不触发 KnowledgePromotionRequest）
- **状态**：`Memory.status`（`effectiveConfidence` / `phase` / `lastDecayedAt` / `lastReinforcedAt` / `eligibleForPromotion`）
- **不暴露为 A2A Agent**：仅 Controller 后台触发；`a2a.recordMemory` / `a2a.queryMemory` 由 Knowledge Service 同 Deployment 暴露

#### 3.2.5 （v2）Conversation Controller
- **观察**：`Conversation` CRD
- **作用域**：A2A 长会话状态（v2 范畴）
- **状态**：v0.1 不实现

#### 3.2.6 通用机制
- **Leader Election**：`coordination.k8s.io/v1 Lease`（K8s 标准）；不依赖 Kopf peering，避免引入额外 CRD 成本（ADR-0005 §7）
- **Workqueue**：Kopf 内部 workqueue（自动处理 retry / backoff / rate-limiting）
- **Finalizer**：Kopf `@kopf.on.delete` + `@kopf.on.finalize` 双钩子；删除前清理子资源
- **Requeue**：Kopf `kopf.HandlersError` 触发指数退避；自定义 classifier（`KopfError`/`PermanentError`）区分可重试/不可重试

**反依赖规则（Knowledge ↔ Memory）**：Knowledge Service 与 MemoryReconciler **不得**直接通信 —— 两者均通过 etcd CRD 状态 + admission webhook 互斥规则解耦（详见 §3.7）。

### 3.3 ③ 资源模型层（Resource Model Layer · Pydantic v2 → OpenAPI v3）

**职责**：用 K8s CRD 描述系统的所有"实体"。

| CRD | 用途 | 状态 | 字段数约束 |
|-----|------|------|------|
| **Agent** | 单个 Agent 实例（1 套 Sidecar + 1 套 Agent 容器） | v0.1 | — |
| **AgentSet** | 同质 Agent 集群（Deployment 风格） | v0.1 | — |
| **Workflow** | 多 Agent DAG 编排 | v0.1 | — |
| **KnowledgeScope**（ADR-0002） | 4 级作用域 + 继承链 | v0.1 | ≤ 6 spec 字段 |
| **KnowledgeItem**（ADR-0002） | 显性知识（人工撰写，Markdown body ≤ 64KB） | v0.1 | 12 spec 字段 |
| **Memory**（ADR-0003） | 持久化记忆（Agent 生成，结构化 KV + lifecycle） | v0.1 | 12 spec 字段 |
| **Conversation** | A2A 长会话 | v2 | — |

**Python 实现关键路径**：

```
Pydantic v2 BaseModel (业务层)
   │
   │  Pydantic model_json_schema() → JSON Schema 2020-12
   ▼
确定性生成器（build/gen_crds.py）
   │
   │  → Kubernetes OpenAPI v3 with x-kubernetes-* extensions
   ▼
helm/templates/crds/*.yaml（checked-in，由 CI 验证无 diff）
```

- **CRD 字段语义稳定**：v1.0.0 后字段变更必须走 ADR（宪法 §3.3）
- **状态独立 Spec**：`status` 通过 `kopf.adopt(status=...)` 子资源更新
- **字段命名**遵循 [K8s API Conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md)（业务层 snake_case，wire 字段 camelCase 由 Pydantic alias 控制，ADR-0005 §5.1）
- **字段数硬约束**（ADR-0004 防过度设计）：每个 CRD spec 字段 ≤ 15
- **Knowledge ↔ Memory 边界**（ADR-0002 §6.3 + ADR-0003 §2.4）：admission webhook 强制 —— `KnowledgeItem.ownerRef.kind ∈ {User, Group}`；`Memory.agentRef` schema 硬编码 `ServiceAccount`

### 3.4 ④ 通信层（Communication Layer · 官方 a2a-sdk + 4 个扩展 method）

**职责**：实现 A2A 协议，提供 Agent 发现与调用。

**A2A method 清单（v0.1 共 6 个 · 4 个为项目扩展）**：

| Method | 来源 | 用途 | 调用方 | 服务方 | 依据 |
|--------|------|------|--------|--------|------|
| `a2a.sendMessage` | 官方 a2a-sdk | 同步发送消息 | 任意 Agent | 任意 Agent | — |
| `a2a.getTask` | 官方 a2a-sdk | 查询任务状态 | 任意 Agent | 任意 Agent | — |
| `a2a.queryKnowledge` | **项目扩展** | 知识检索（自由文本 + scope 继承 + type/tag 过滤） | 任意 Agent | **Knowledge Service** | ADR-0002 §5.1 |
| `a2a.getKnowledgeItem` | **项目扩展** | 知识详情拉取（按 name + version） | 任意 Agent | **Knowledge Service** | ADR-0002 §5.2 |
| `a2a.recordMemory` | **项目扩展** | 记忆写入（Agent 生成经验 + memoryKey 去重） | 任意 Agent | **MemoryReconciler 间接** | ADR-0003 §5.1 |
| `a2a.queryMemory` | **项目扩展** | 记忆检索（5 维可见性矩阵过滤） | 任意 Agent | **MemoryReconciler 间接** | ADR-0003 §5.2 |

**核心组件**：

#### 3.4.1 A2A Server（基于官方 a2a-sdk ASGI）
- **协议**：A2A JSON-RPC 2.0 over HTTP（SSE v0.5+）
- **端点**：
  - `GET /.well-known/agent.json` — Agent Card
  - `POST /a2a/jsonrpc` — A2A 消息处理（含 6 个 method）
  - `GET /a2a/events` — SSE 流（v0.5+）
- **端口**：8080（默认）
- **Python 实现**：
  ```python
  # 示意，详见 L2-1 / L3-2 Spec
  from a2a.server import A2AServer          # 官方 a2a-sdk
  from superteam_a2a.a2a.extension import (
      QueryKnowledgeRouter, GetKnowledgeItemRouter,
      RecordMemoryRouter, QueryMemoryRouter,
  )
  
  app = A2AServer(card=agent_card, handlers=[
      QueryKnowledgeRouter(...),  # 项目 extension
      GetKnowledgeItemRouter(...),
      RecordMemoryRouter(...),
      QueryMemoryRouter(...),
  ])  # 标准 method 由 SDK 提供
  ```
- **compatibility adapter**：所有 4 个扩展 method 注册在 `superteam_a2a.a2a.upstream` 边界外（ADR-0005 §3.2），防止 SDK 升级扩散到业务模块

#### 3.4.2 A2A Client（基于官方 a2a-sdk）
- **协议**：A2A JSON-RPC 2.0 client
- **能力**：
  - Discovery：DNS / Agent Card 拉取（`httpx.AsyncClient` + DNS resolve）
  - 调用：sync（v0.1）/ SSE 流（v0.5+）
  - 重试 + 退避（`tenacity` 包，受 method idempotency gate 约束）
  - mTLS 验证对端证书（`ssl.SSLContext` + URI SAN SPIFFE 解析）
- **每个 method 的请求/响应字段**：详见 [`L1-system-spec.md`](../spec/L1-system-spec.md)

#### 3.4.3 Identity（mTLS / SPIFFE）
- **mTLS**：通过 cert-manager 颁发 SPIFFE 兼容证书
  - Python `ssl.SSLContext` 加载 server cert/key/client CA
  - 最低 TLS 1.3
  - 证书热更新通过原子替换 SSL context/transport（ADR-0005 §9.1）
- **ServiceAccount**：每个 Agent 独立 SA；Memory `agentRef` schema 硬编码 SA
- **SPIFFE**：从 URI SAN 解析 SPIFFE ID；`py-spiffe` / Workload API 在 L3 前做兼容性验证；不满足时回退 cert-manager mounted cert + URI SAN（ADR-0005 §9.1）
- **Token**：可选 (v0.5+)，用于跨集群联邦

#### 3.4.4 Discovery
- **In-Cluster**：标准 K8s Service + DNS（`socket.getaddrinfo`）
- **Agent Card**：`/.well-known/agent.json` 路径（httpx fetch）
- **Resolver**：`superteam-a2a.io/v1.agents` 格式的集群内 DNS
- **EndpointSlice watch**：in-memory cache；watch invalidation 由 `kubernetes_asyncio` 异步 watch 触发
- **Knowledge Service Card**：单实例 v0.1，详见 ADR-0002 §4.2

### 3.5 ⑤ 运行时层（Runtime Layer）

**职责**：实际的 Agent 容器执行 + 2 个特殊 Agent + 1 个 Controller-only 后台。

**Agent Pod 模式**：

**模式 A — Sidecar 模式**（v0.1 推荐，Python-native + 跨语言均适用）：
```
Pod:
  - Container 1: Agent (user-provided image)
  - Container 2: Adapter (Python-based, framework-specific)
  Communication: localhost:8080
  Pro: 框架无侵入 / 进程隔离 / 资源边界清晰
  Con: 资源开销略高
```

**模式 B — 同进程 plugin**（v0.1，Python-native framework）：
```
Pod:
  - Container 1: Agent + Adapter (single Python process, framework 在同进程)
  Communication: in-process
  Pro: 资源占用低 / 启动快
  Con: 仅 Python framework / 共享进程生命周期
```

**模式 C — 直连模式**（v0.5+）：
```
Pod:
  - Container 1: Agent (内置 Adapter)
  Pro: 资源占用低
  Con: 框架需修改
```

**模式 D — 外部 Agent**（v0.5+）：
- 不在 K8s 内运行，仅通过 A2A 接入
- 用 Service + ExternalName 引用

**2 个特殊 Agent**：

#### 3.5.1 Hello Agent（v0.1 · Python 无框架参考实现）
- 单一 Pod，**单 Python 进程 / 单 Uvicorn worker**（ADR-0005 §6.2）
- 直接实现 A2A 协议端点（基于官方 a2a-sdk）
- 仅暴露 `a2a.sendMessage` / `a2a.getTask`
- 用作 E2E Demo + Operator 冒烟测试
- 镜像基线：`python:3.12-slim` + 多阶段构建

#### 3.5.2 Knowledge Service（v0.1 · Python · Card-driven）

> **L2-4 状态**：✅ v0.2.0 Python（2026-07-27 #43 评审通过，详见 [设计](../design/L2-modules/L2-knowledge-memory.md) + [Spec](../spec/L2-module-specs/L2-knowledge-memory.md) + [评审](../reviews/l2-4-knowledge-memory-spec-python-review.md) §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项 · 194.6KB / 4152 行 / 60 测试 ID + 30 验收点 + 22 开放问题）
> **A2A Protocol 依赖**：✅ L2-1 v0.2.0（Python 重写，详见 [Spec](../../spec/L2-module-specs/L2-a2a-protocol.md) + [评审](../../reviews/l2-1-a2a-protocol-review.md)；2026-07-24 通过）

- **不是** Sidecar 模式 —— 是独立 Deployment，单实例 v0.1，单 Python 进程 / 单 worker
- **Card**：`superteam-a2a.knowledge-service` v0.1.0
- **Skills**：`query_knowledge` / `get_knowledge_item` / `record_memory` / `query_memory`（详见 L2-4 Spec §4.5 完整 JSON — **4 个 method 与 MemoryReconciler 共享同 Deployment**）
- **Capabilities**：streaming=false / pushNotifications=false（v0.1 简化）
- **认证**：mTLS（cert-manager 颁发，Python `ssl.SSLContext`）
- **依赖 CRD**：KnowledgeScope / KnowledgeItem / Memory（通过 `kubernetes_asyncio` 读取）
- **承担职责**：暴露 4 个 A2A method（Knowledge 2 + Memory 2）；Memory 不另部署独立 Agent（v0.1 单 Deployment 共享简化）

**Controller-only 后台**：

#### 3.5.3 MemoryReconciler（v0.1 · Python · 非 Agent）

> **L2-4 状态**：✅ v0.2.0 Python（2026-07-27 #43 评审通过 · 与 Knowledge Service 共享同 Deployment）；**MemoryReconciler 4 状态机 + decay 公式 + Leader Election Lease + 60s 周期 kopf.timer + BM25 InvertedIndex 完整落地**
> **A2A Protocol 依赖**：✅ L2-1 v0.2.0（Python 重写，详见 [Spec](../../spec/L2-module-specs/L2-a2a-protocol.md)；2026-07-24 通过）

- **不是** Agent —— 是 Operator 内部 Controller（与 Knowledge Service 共享同 Deployment）
- **职责**：每 60s reconcile 所有 Memory，应用 decay/reinforce/GC/promotion（`kopf.timer` 驱动）
- **触发**：`a2a.recordMemory` 命中 / `a2a.queryMemory` 读取（通过 K8s watch 间接触发）
- **不暴露 A2A 端点**：Memory 2 个 A2A method（recordMemory / queryMemory）由 Knowledge Service 同 Deployment 暴露
- **Leader Election**：单 leader（`coordination.k8s.io/v1 Lease`）避免多副本 reconcile 冲突
- **decay 公式**：`effectiveConfidence = confidence × exp(-elapsed_days / decayDays)`（详见 L2-4 Spec §7.4 + ADR-0003 §4.1）
- **CPU 工作**：batch decay / BM25 rebuild 通过 `anyio.to_thread.run_sync` offload，不阻塞 event loop（ADR-0005 §6.3）

### 3.6 横切关注点（Cross-Cutting · Python 全栈）

| 关注点 | Python 实现位置 |
|--------|----------------|
| **认证 / 鉴权** | RBAC（ServiceAccount）+ cert-manager（mTLS，Python `ssl.SSLContext`） + NetworkPolicy |
| **资源配额** | ResourceQuota / LimitRange（per namespace） |
| **可观测** | `prometheus-client` + OpenTelemetry Python SDK + `structlog` + K8s Events |
| **审计** | K8s audit log + Operator emit Event |
| **镜像安全** | cosign 签名 + trivy 扫描 + `python:3.12-slim` 多阶段构建 |
| **配置** | Helm values + ConfigMap + Secret（External Secrets Operator） |
| **类型/Schema** | Pydantic v2 strict + `pydantic-settings`（配置）+ JSON Schema 2020-12 生成 |
| **静态质量门禁** | Ruff format/lint + Pyright strict + Bandit + pip-audit |
| **运行时门禁** | 单进程 + single Uvicorn worker + event-loop lag 监控 + thread-offload 队列监控 |

### 3.7 Knowledge ↔ Memory 边界（双向互斥）

> 与 v0.1 Go baseline 完全相同；Python 重写**不修改业务规则**，仅替换实现栈。

| 维度 | Knowledge（ADR-0002） | Memory（ADR-0003） |
|------|---------------------|--------------------|
| **ownerRef / agentRef kind** | `User` / `Group`（**禁 ServiceAccount**） | `ServiceAccount`（**硬编码 schema**） |
| **visibility 取值** | 4 枚举（含 `public-readable`，仅 industry scope） | 3 枚举（**不包含 public-readable**） |
| **可追溯链** | `relatedItems`（可选） | `sourceKnowledgeRef`（必填同 scope，admission 强制） |
| **数量上限** | cluster ≤ 10K | cluster ≤ 50K |

**admission webhook 双向互斥规则**（Kopf `@kopf.on.validate` 或独立 webhook server，二选一在 L2-2 Spec 锁定）：
- ❌ KnowledgeItem `visibility == agent-private` 且 `ownerRef.kind == ServiceAccount` —— **禁止**
- ❌ KnowledgeItem `visibility == public-readable` 且 `spec.scopeRef.level != industry` —— **禁止**
- ❌ Memory `agentRef` schema 硬编码 SA（双重校验：K8s type validation + admission）
- ❌ Memory `visibility == public-readable` —— **禁止**

---

## 4. 核心组件（Python 实现清单）

### 4.1 组件清单

| ID | 组件名 | 层级 | 语言 | Python 包路径 |
|----|--------|------|------|----------------|
| C-1 | superteam-a2a Operator | ② | **Python 3.12+** | `packages/operator/src/superteam_a2a/operator/` |
| C-2 | A2A Core Library | ④ | **Python 3.12+** | `packages/a2a-core/src/superteam_a2a/a2a/` |
| C-3 | Adapter SDK | ④ | **Python 3.12+** | `packages/adapter-sdk/src/superteam_a2a/adapter/` |
| C-4 | Framework Adapters | ④ | **Python 3.12+** | `adapters/{langchain,autogen,crewai,sk,strands,smolagents}/` |
| C-5 | Hello Agent | ⑤ | **Python 3.12+** | `agents/hello/src/superteam_a2a/hello/` |
| C-6 | Knowledge Service | ⑤ | **Python 3.12+** | `services/knowledge-service/src/superteam_a2a/knowledge/` |
| C-7 | Memory backend (共享 Deployment) | ⑤ | **Python 3.12+** | `services/memory-backend/src/superteam_a2a/memory/` |
| C-8 | Helm Chart | 横切 | YAML | `helm/` |
| C-9 | Grafana Dashboards | 横切 | JSON | `dashboards/` |
| C-10 | Examples | ① | YAML | `examples/` |

**uv workspace 布局**（ADR-0005 §13）：

```
pyproject.toml          # 根工作区配置（统一工具链版本）
uv.lock                  # 必须提交；CI 使用 uv sync --frozen
packages/
  a2a-core/src/superteam_a2a/a2a/
  operator/src/superteam_a2a/operator/
  adapter-sdk/src/superteam_a2a/adapter/
services/
  knowledge-service/src/superteam_a2a/knowledge/
  memory-backend/src/superteam_a2a/memory/
agents/
  hello/src/superteam_a2a/hello/
adapters/
  langchain/
  autogen/
  crewai/
  semantic-kernel/
  strands/
  smolagents/
tests/
  integration/    # kind + 真实 K8s reconcile / webhook / mTLS
  conformance/    # 上游 A2A suite
  e2e/            # kind + Helm 端到端
```

**关键约束**：
- Operator / A2A Core / Adapter SDK **不得依赖任何 Agent framework**（宪法 §3.7 + ADR-0005 §13）
- framework Adapter 独立 workspace package + 独立镜像 + 独立 ServiceAccount
- 根 `pyproject.toml` 统一 Ruff / Pyright / pytest / Bandit / pip-audit 配置
- 各 package 自声明最小运行依赖
- lockfile（`uv.lock`）是构建契约的一部分

### 4.2 组件依赖图

```
┌──────────────┐
│  CRD Apply   │
└──────┬───────┘
       │
       ▼
┌──────────────────┐    ┌──────────────────┐
│   Operator       │───▶│  K8s API Server  │
│   (Kopf +        │    │  (kubernetes_    │
│    kubernetes_   │    │   asyncio)       │
│    asyncio)      │    └──────────────────┘
└──────┬───────────┘
       │ rebuilds
       ▼
┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐
│   Pod Spec       │───▶│  Adapter Sidecar │───▶│  Agent Container│
└──────────────────┘    │  (Python uvicorn)│    │ (Py/JS/Java/..)│
                        └────────┬─────────┘    └────────────────┘
                                 │ localhost
                                 ▼
                        ┌──────────────────┐
                        │  A2A Core Library│
                        │  (官方 a2a-sdk + │
                        │   extension      │
                        │   compatibility  │
                        │   adapter)       │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  A2A Other Agents│
                        └──────────────────┘
```

### 4.3 Python 技术栈选型

| 维度 | 选型 | 备注 |
|------|------|------|
| **语言** | **Python 3.12+** | ADR-0005 锁定；Operator 生态事实标准 |
| **Operator 框架** | **[Kopf](https://kopf.readthedocs.io/)** | async handlers + retry/resume/finalizer；可靠性门禁见 ADR-0005 §7 |
| **K8s 客户端** | **[`kubernetes_asyncio`](https://github.com/tomplus/kubernetes_asyncio)** + `kubernetes-client/python`（同步工具） | 禁止在 event loop 内调用阻塞式 K8s client |
| **A2A 协议** | **官方 [`a2a-sdk`](https://github.com/google-a2a/a2a-python)** | v0.1 必须复用；禁止 fork（ADR-0005 §3.2） |
| **RPC** | JSON-RPC 2.0 | A2A 协议原生 |
| **HTTP 服务器** | **Uvicorn + Starlette/FastAPI（ASGI）** | 单 worker / 单 event loop（ADR-0005 §6.2） |
| **HTTP 客户端** | **[`httpx.AsyncClient`](https://www.python-httpx.org/)** | 进程级复用连接池；所有请求必须 timeout |
| **类型/Schema** | **[Pydantic v2](https://docs.pydantic.dev/latest/) strict** | 配置：`pydantic-settings`；CRD Schema 单一来源 |
| **重试** | **[Tenacity](https://tenacity.readthedocs.io/)** | 受 method idempotency gate 约束 |
| **mTLS** | cert-manager + stdlib `ssl.SSLContext`（TLS 1.3+）+ `py-spiffe`（v0.1 验证，必要时回退） | 证书热更新通过原子替换 |
| **指标** | [`prometheus-client`](https://github.com/prometheus/client_python) | 单进程模式（避免 multiprocess） |
| **Trace** | **[OpenTelemetry Python SDK](https://opentelemetry.io/docs/languages/python/)** | W3C Trace Context + 显式 provider 注入 |
| **日志** | **[`structlog`](https://www.structlog.org/)** + stdlib logging | JSON；敏感内容禁记 |
| **异步/线程 offload** | `asyncio` + `anyio.to_thread.run_sync`（CPU 工作） | ADR-0005 §6.1/§6.3 |
| **Workspace / lock** | **[`uv`](https://docs.astral.sh/uv/)** workspace + `pyproject.toml` + `uv.lock` | CI 必须 `uv sync --frozen` |
| **单元/集成测试** | `pytest` + `pytest-asyncio` / `AnyIO` + `respx` | async 路径必须真实 await |
| **属性/模糊测试** | `Hypothesis` + `hypothesis-jsonschema` | envelope / schema / FSM / 算法 |
| **类型门禁** | **`Pyright strict`** | 公共 API 禁止未解释 `Any` |
| **Lint/format** | **[Ruff](https://docs.astral.sh/ruff/)** | 单一 formatter/linter |
| **安全扫描** | **`Bandit` + `pip-audit` + Trivy + Cosign** | Python 依赖 + 镜像双层扫描 |
| **E2E** | `kind` + `pytest` | 真实 K8s reconcile / webhook / mTLS |
| **Chart** | Helm 3 + values schema | v0.1 |
| **CI** | GitHub Actions | OSS 友好 |
| **基础镜像** | `python:3.12-slim` 多阶段构建 | 非 root / read-only rootfs / 最小依赖 |

---

## 5. CRD 模型（Pydantic v2 → CRD OpenAPI）

### 5.1 资源关系图

```
┌─────────────┐    ┌─────────────┐
│   AgentSet  │───▶│  Agent 1..N │
└─────────────┘    └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  A2A Server │
                   │  (uvicorn)  │
                   └─────────────┘
                          ▲
                          │ A2A calls
┌─────────────┐    ┌──────┴──────┐
│  Workflow   │───▶│  Agent Pool │
└─────────────┘    └──────┴──────┘
                          │
                          │ reads / writes
                          ▼
              ┌────────────────────────────┐
              │  KnowledgeScope ←──┐        │
              │     └──KnowledgeItem│        │
              │                     │ 引用  │
              │  Memory ────────────┘        │
              │     ▲     │                  │
              │     │     └── reconcile      │
              │     │        (MemoryReconciler)
              │     │                         │
              │  Knowledge Service ──▶ queryKnowledge/getKnowledgeItem
              └────────────────────────────┘
```

### 5.2 核心 CRD 概览（wire YAML 不变；Python 内部用 Pydantic 表达）

#### 5.2.1 Agent（v0.1 · wire YAML 不变）

```yaml
apiVersion: superteam-a2a.io/v1alpha1
kind: Agent
metadata:
  name: hello-agent
  namespace: default
spec:
  framework: langchain        # langchain / autogen / crewai / sk / strands / smolagents / custom
  version: "0.1.0"
  image: "ghcr.io/me/my-langchain-agent:0.1.0"
  resources:
    requests: { cpu: 100m, memory: 256Mi }
    limits:   { cpu: 1000m, memory: 1Gi }
  card:
    name: "hello-agent"
    description: "Echoes any input message"
    skills: ["echo"]
    inputModes: ["text"]
    outputModes: ["text"]
  adapter:
    image: "ghcr.io/superteam-a2a/adapter-langchain:0.1.0"
    port: 8080
  serviceAccountName: "hello-agent-sa"
  timeout: 600
  maxRetries: 3
  replicas: 1
```

**Python 内部表达**（Pydantic v2）：

```python
# packages/operator/src/superteam_a2a/operator/models.py
# 示意，详见 L2-2 / L3-1 Spec
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class ResourceRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requests: dict[str, str]  # {"cpu": "100m", "memory": "256Mi"}
    limits: dict[str, str]

class AgentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    
    framework: Literal["langchain", "autogen", "crewai", "sk",
                       "strands", "smolagents", "custom"]
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    image: str
    image_pull_policy: str | None = Field(None, alias="imagePullPolicy")
    resources: ResourceRequirements
    card: AgentCard
    adapter: AdapterConfig
    timeout: int = Field(600, ge=1, le=3600)
    max_retries: int = Field(3, ge=0, le=10)
    replicas: int = Field(1, ge=1, le=100)
```

> wire YAML 字段名（`imagePullPolicy` 等）通过 Pydantic `alias` 保留，业务层使用 Pythonic snake_case（ADR-0005 §5.1）。

#### 5.2.2 AgentSet（v0.1 · wire YAML 不变）

```yaml
apiVersion: superteam-a2a.io/v1alpha1
kind: AgentSet
metadata:
  name: echo-fleet
spec:
  template:
    spec: { ... }   # 完整 AgentSpec
  replicas: 3
```

#### 5.2.3 Workflow（v0.1 · wire YAML 不变）

```yaml
apiVersion: superteam-a2a.io/v1alpha1
kind: Workflow
metadata:
  name: code-review-workflow
spec:
  tasks:
    - id: "fetch"
      agent: "github-reader"
      inputs: { repo: "superteam-a2a/superteam-a2a", ref: "main" }
      outputs: ["files"]
    - id: "lint"
      agent: "python-linter"
      dependsOn: ["fetch"]
      inputs:
        files: "{{ fetch.files }}"
      outputs: ["lint_report"]
    - id: "review"
      agent: "code-reviewer"
      dependsOn: ["lint"]
      inputs:
        files: "{{ fetch.files }}"
        lint: "{{ lint.lint_report }}"
      outputs: ["review"]
  timeout: 1800
  ttlSecondsAfterFinished: 86400
  maxRetries: 1
```

### 5.3 CRD 演进路径

| 版本 | 内容 | 计划 |
|------|------|------|
| **v1alpha1** | 初始定义，字段可自由变更 | v0.1.0（6 CRD 全部） |
| **v1beta1** | 字段稳定，破坏性变更走 ADR | v0.5.0（6 CRD 全部 v1alpha1 → v1beta1 + conversion webhook） |
| **v1** | API 锁定，强烈向后兼容 | v1.0.0（6 CRD 全部 v1beta1 → v1） |

**Python 实现要点**：
- Pydantic v2 model → JSON Schema 2020-12 → 确定性生成 Kubernetes OpenAPI v3
- 生成器（`build/gen_crds.py`）必须满足（ADR-0005 §5.2）：
  - 稳定排序，重复生成无 diff
  - 保留 `x-kubernetes-*` 扩展（`int-or-string`, `validations`, `list-type` 等）
  - 拒绝 Kubernetes 不支持的 schema 特性
  - CI 验证工作区无未提交生成差异
- CRD YAML checked-in 到 `helm/templates/crds/`

### 5.4 v0.1 新增 CRD（ADR-0002 + ADR-0003 · wire YAML 不变）

#### 5.4.1 KnowledgeScope（v0.1 · ADR-0002 §2 · wire 不变）

```yaml
apiVersion: superteam-a2a.io/v1alpha1
kind: KnowledgeScope
metadata:
  name: team-payments-platform
spec:
  level: team
  displayName: "Payments Platform Team"
  description: "Knowledge owned by the Payments Platform team"
  parentRef:
    name: org-payments
  ownerRef:
    kind: Group
    name: payments-platform-leads
  inheritRules:
    includeTypes: ["runbook", "faq", "best-practice"]
  labels:
    domain: payments
    cost-center: cc-123
```

#### 5.4.2 KnowledgeItem（v0.1 · ADR-0002 §3 · wire 不变）

```yaml
apiVersion: superteam-a2a.io/v1alpha1
kind: KnowledgeItem
metadata:
  name: refund-failure-handling
spec:
  scopeRef:
    name: team-payments-platform
  type: runbook
  title: "信用卡退款失败处理流程"
  body: |
    ## 场景 1: ...
  summary: "针对 3 种常见退款失败场景的处理步骤"
  tags: ["payments", "refund"]
  visibility: scope-and-children
  ownerRef:
    kind: User
    name: alice
  sourceURI: "https://wiki.example.com/refund-failure-handling"
  version: 3
  relatedItems:
    - name: refund-api-spec
```

#### 5.4.3 Memory（v0.1 · ADR-0003 §2 · wire 不变）

```yaml
apiVersion: superteam-a2a.io/v1alpha1
kind: Memory
metadata:
  name: team-payments-platform/credit-card-refund-retry-strategy
spec:
  scopeRef:
    name: team-payments-platform
  agentRef:
    name: refund-analyzer           # schema 硬编码 ServiceAccount
  content:
    pattern: "credit-card-refund-fail-retry-3x"
    outcome: "success-after-2nd-retry"
    duration: "8.5s"
  summary: "信用卡退款失败时，重试 3 次成功率最高"
  confidence: 0.55
  decayDays: 30
  reinforcedCount: 2
  visibility: scope-and-children    # 3 枚举（无 public-readable）
  memoryKey: "credit-card-refund-retry-strategy"
  sourceKnowledgeRef:
    name: refund-failure-handling
  tags: ["payments", "refund"]
```

### 5.5 CRD 关系总图（含知识 / 记忆）

```
┌─────────────┐    ┌─────────────┐
│   AgentSet  │───▶│  Agent 1..N │
└─────────────┘    └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  A2A Server │
                   └─────────────┘
                          ▲
                          │ A2A calls
┌─────────────┐    ┌──────┴──────┐
│  Workflow   │───▶│  Agent Pool │
└─────────────┘    └──────┴──────┘
                          │
                          │ reads / writes
                          ▼
              ┌────────────────────────────┐
              │  KnowledgeScope ←──┐        │
              │     └──KnowledgeItem│        │
              │                     │ 引用  │
              │  Memory ────────────┘        │
              │     ▲     │                  │
              │     │     └── reconcile      │
              │     │        (MemoryReconciler)
              │     │                         │
              │  Knowledge Service ──▶ queryKnowledge/getKnowledgeItem
              └────────────────────────────┘
```

**关系说明**（与 v0.1 Go baseline 一致）：
- `Memory.sourceKnowledgeRef` → `KnowledgeItem`（建立可追溯链，ADR-0003 §2.4 admission 强制同 scope）
- `KnowledgeItem.relatedItems[]` 可包含 `Memory` 引用（**可选**，v0.1 仅展示）
- Agent ↔ Knowledge Service 通过 A2A（不直接读 CRD）
- Agent ↔ Memory 通过 A2A（经 MemoryReconciler 落 CRD）

---

## 6. Adapter 架构（Python 协议契约）

### 6.1 Adapter 角色

Adapter 是 **Agent 框架** 与 **A2A 协议** 之间的薄翻译层。它**不**实现 Agent 逻辑，只做：
1. 接收 A2A 请求
2. 转换成框架原生调用
3. 把 Agent 输出转回 A2A 响应
4. 暴露 `/.well-known/agent.json`

### 6.2 Adapter 契约（5 行 YAML 原则）

对用户而言，每个 Adapter 只需 5 行 YAML 即可启用：

```yaml
adapter:
  framework: langchain          # 1. 框架名
  image: my-agent:latest        # 2. Agent 镜像
  card: ./agent-card.yaml       # 3. Agent Card
  resources: { limits: {...} }  # 4. 资源
  healthCheck: /healthz         # 5. 健康检查
```

### 6.3 Adapter 接口（Python `typing.Protocol`）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/protocol.py
# 示意，详见 L2-3 Spec
from typing import Protocol, runtime_checkable
from a2a import AgentCard, Message, Task, Part

@runtime_checkable
class Adapter(Protocol):
    """Adapter 与 A2A Server 之间的协议边界（ADR-0005 §3.3）。"""
    
    async def on_message(
        self, message: Message, context_id: str | None,
    ) -> Task:
        """处理 A2A sendMessage；返回 Task + 状态。"""
        ...
    
    def agent_card(self) -> AgentCard:
        """返回 Agent Card。"""
        ...
    
    async def health_check(self) -> bool:
        """健康检查。"""
        ...


class FrameworkAdapter(Protocol):
    """框架特定扩展钩子（v0.1 Hello Agent 必实现）。"""
    
    async def on_framework_event(self, event: dict) -> None:
        """框架事件回调（如 LangChain chain run）。"""
        ...
```

**关键约束**：
- Adapter **不得** import 任何 Agent framework（与 Operator 规则一致，宪法 §3.7）
- Adapter 必须复用 A2A Core 的 Server / Schema / TLS / 限流 / Trace，不复制协议实现（ADR-0005 §3.3）
- Adapter 镜像基线 `python:3.12-slim` 多阶段构建

### 6.4 Adapter 拓扑

**Sidecar 模式（v0.1 推荐）**：
```
┌──────────────────────────────────────────┐
│ Agent Pod                                │
│                                          │
│  ┌──────────────────┐                    │
│  │  Adapter Container (Python)          │
│  │  ┌──────────────┐│     A2A JSON-RPC  │
│  │  │ A2A Server   ││───▶:8080 (uvicorn) │
│  │  │  ↕ translate  ││                   │
│  │  │ Framework    ││                   │
│  │  │ Client       ││                   │
│  │  └──────┬───────┘│                   │
│  └─────────┼────────┘                   │
│            │ localhost:7080              │
│  ┌─────────▼────────────────────────┐  │
│  │ Agent Container (任意语言)        │  │
│  │  - LangChain / AutoGen / etc.    │  │
│  │  - MCP client for tools           │  │
│  └──────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

**同进程 plugin 模式（v0.1 Python-native）**：
```
┌──────────────────────────────────────────┐
│ Agent Pod                                │
│  ┌────────────────────────────────┐      │
│  │  Single Python Process         │      │
│  │  ┌──────────┐  ┌──────────┐    │      │
│  │  │ Adapter  │◄─│ Agent    │    │      │
│  │  │  (uvicorn) │ (framework)│    │      │
│  │  └──────────┘  └──────────┘    │      │
│  │  in-process / asyncio          │      │
│  └────────────────────────────────┘      │
└──────────────────────────────────────────┘
```

### 6.5 官方 Adapter 路线图

| 版本 | 框架 | 优先级 | Python 实现要点 |
|------|------|--------|------------------|
| v0.1.0 | **Hello Agent**（无框架） | P0 | 单进程，标准 SDK |
| v0.2.0 | **LangChain** | P0 | 同进程 plugin（Python-native） |
| v0.2.0 | **AutoGen** | P1 | 同进程 plugin |
| v0.5.0 | **CrewAI** | P1 | Sidecar 模式 |
| v0.5.0 | **Semantic Kernel** | P2 | Sidecar 模式 |
| v1.0.0 | **Strands** | P2 | Sidecar 模式 |
| v1.0.0 | **Smolagents** | P2 | Sidecar 模式 |
| v1.5.0 | 社区贡献 | by contribution | — |

---

## 7. A2A 协议集成（官方 a2a-sdk + 4 个扩展 method）

### 7.1 协议版本

- **目标**：A2A v0.3+（参考 google-a2a/A2A）
- **本地实现**：Python `a2a-sdk`（**复用官方**，不 fork）
- **v0.1 优先级**：
  - 复用：Agent Card / Message / Task (sync) / 标准 JSON-RPC envelope / ASGI server
  - 扩展：4 个 method（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）通过 compatibility adapter 注册
- **v0.5 扩展**：SSE Streaming / Artifact
- **v1.0 完整**：参考 google-a2a/A2A 完整规范

### 7.2 标准类型（Pydantic from official a2a-sdk）

```python
# 示意，全部来自官方 a2a-sdk；项目不重新定义
from a2a.types import AgentCard, Message, Part, Task, TaskStatus, Artifact

# 标准 wire shape（Python 内部直接复用 SDK 类型）
```

### 7.3 RPC 端点

| 方法 | 路径 | 用途 |
|------|------|------|
| `GET` | `/.well-known/agent.json` | 获取 Agent Card |
| `POST` | `/a2a/jsonrpc` | JSON-RPC 2.0 端点 |
| `GET` | `/a2a/events` | SSE 流（v0.5+） |
| `GET` | `/healthz` | 健康检查 |
| `GET` | `/readyz` | 就绪检查 |

### 7.4 JSON-RPC Method（v0.1 共 6 个 · 2 个 v0.5+）

| Method | 来源 | 用途 | 服务方 | 引入版本 |
|--------|------|------|--------|----------|
| `a2a.sendMessage` | 官方 SDK | 同步发送消息 | 任意 Agent | v0.1 |
| `a2a.getTask` | 官方 SDK | 查询任务状态 | 任意 Agent | v0.1 |
| `a2a.queryKnowledge` | 项目扩展 | 知识检索（scope 继承 + type/tag 过滤） | Knowledge Service | **v0.1（ADR-0002）** |
| `a2a.getKnowledgeItem` | 项目扩展 | 知识详情拉取 | Knowledge Service | **v0.1（ADR-0002）** |
| `a2a.recordMemory` | 项目扩展 | 记忆写入（memoryKey 去重 + reinforce） | MemoryReconciler 间接 | **v0.1（ADR-0003）** |
| `a2a.queryMemory` | 项目扩展 | 记忆检索（5 维可见性矩阵） | MemoryReconciler 间接 | **v0.1（ADR-0003）** |
| `a2a.cancelTask` | 官方 SDK | 取消任务 | 任意 Agent | v0.5+ |
| `a2a.subscribeTask` | 官方 SDK | 订阅任务事件（SSE） | 任意 Agent | v0.5+ |

**错误码**：每个 method 的错误码详见 [`L1-system-spec.md`](../spec/L1-system-spec.md)。Knowledge 类错误码以 `KNOWLEDGE_*` 前缀；Memory 类以 `MEMORY_*` 前缀。

### 7.5 官方 a2a-sdk compatibility adapter（ADR-0005 §3.2 + §8）

```python
# packages/a2a-core/src/superteam_a2a/a2a/upstream.py
# 边界：所有官方 a2a-sdk import 必须仅经此模块，业务模块禁止直接 import
from a2a.server import A2AServer as _OfficialServer
from a2a.client import A2AClient as _OfficialClient
from a2a.types import AgentCard, Message, Task, Part, Artifact

# 业务层只通过 superteam_a2a.a2a.upstream 导入
__all__ = ["AgentCard", "Message", "Task", "Part", "Artifact"]
```

**compatibility adapter 原则**（ADR-0005 §8）：
- 标准 method 直接交 SDK
- 4 个扩展 method 注册在 `superteam_a2a.a2a.upstream` 边界**外**（router 层），不修改/不 fork SDK
- SDK 不支持的扩展 method：通过自定义 router 路由到项目业务 handler
- contract test 保证同一 JSON wire shape

---

## 8. 数据流

### 8.1 创建 Agent 流程

```
User: kubectl apply -f agent.yaml
   ↓
API Server: 写入 etcd
   ↓
Kopf watch 触发 @kopf.on.create('Agent')
   ↓
AgentReconciler (Python async service):
   1. Pydantic 校验 CRD (schema validation)
   2. 创建 / 更新 ServiceAccount
   3. 创建 / 更新 NetworkPolicy
   4. 创建 / 更新 Pod (Agent + Adapter Sidecar)
   5. 等待 Pod Ready (kubernetes_asyncio watch)
   6. 抓取 Agent Card (httpx fetch /.well-known/agent.json)
   7. 注册至 Discovery (in-memory cache + EndpointSlice 注释)
   8. 更新 Status 子资源 (kopf.adopt status patch)
   ↓
User: kubectl get agent hello-agent
   ↓
Status: Available
```

### 8.2 A2A 调用流程

```
Agent A → Adapter A → JSON-RPC over HTTPS (httpx + mTLS) → Adapter B → Agent B
   ↑                                                       ↓
   └──────────────── A2A Response ←───────────────────────┘
```

**详细步骤**：
1. Agent A 调用 Adapter A（`A2AClient` from `superteam_a2a.a2a.upstream`）
2. Adapter A 解析目标 Agent（K8s Service DNS + Agent Card Discovery）
3. Adapter A 发起 JSON-RPC 请求（`httpx.AsyncClient` + `ssl.SSLContext` mTLS）
4. NetworkPolicy 校验（同一 namespace / 允许的源）
5. Adapter B 接收请求，校验 Agent Card
6. Adapter B 调用 Agent B（localhost 或 in-process）
7. Agent B 处理（可能调用 LLM / MCP Tools）
8. Adapter B 把响应转回 A2A 格式
9. Adapter B 返回 JSON-RPC 响应
10. Adapter A 把响应返回给 Agent A
11. 全程有 OTel Trace / Prometheus 指标 / `structlog` JSON 日志

### 8.3 Workflow 执行流程

```
User: kubectl apply -f workflow.yaml
   ↓
WorkflowReconciler (Python):
   1. @kopf.on.create handler 接收 CRD
   2. DAG 校验（无环、依赖有效、ID 唯一）— WorkflowValidator 纯 Python 函数
   ↓
Status: Pending → Running
   ↓
按 tasks 拓扑执行（asyncio.TaskGroup）：
   1. 无依赖任务 → 启动
   2. 任务完成 → 检查下游
   3. 下游依赖满足 → 启动
   4. 全部完成 → Status: Succeeded
   ↓
TTL 到期 → GC 资源（kopf.timer 周期检查）
```

### 8.4 Knowledge 查询流程（v0.1 · ADR-0002 · Python 实现）

```
Agent A → A2A Client → a2a.queryKnowledge → Knowledge Service (Python)
                                                      │
                                                      ├─ 1. resolve_effective_scopes(scope)  # 异步查 etcd
                                                      │     ↓
                                                      │   继承链 [industry, org, team, project]
                                                      │
                                                      ├─ 2. 遍历链上每个 scope → list_knowledge_items
                                                      │
                                                      ├─ 3. 应用 InheritRules (includeTypes / excludeTypes)
                                                      │
                                                      ├─ 4. 应用 visibility 过滤
                                                      │     (scope-only / scope-and-children / public-readable)
                                                      │
                                                      ├─ 5. 内存 BM25 评分 + 排序
                                                      │     (Pydantic result schema 校验)
                                                      │
                                                      └─ 6. 去重（保留最新 version）
                                                            ↓
                                            返回 [{name, scope, type, title, summary, relevanceScore}, ...]
```

**约束**：queryKnowledge 在 industry scope 时 **必须** 携带 typeFilter 或 tagFilter（避免全集群扫描）。

**CPU 工作 offload**：BM25 评分 > 1K items 时通过 `anyio.to_thread.run_sync` offload，避免阻塞 event loop（ADR-0005 §6.3）。

### 8.5 Memory 写入流程（v0.1 · ADR-0003 · Python 实现）

```
Agent A → A2A Client → a2a.recordMemory → Knowledge Service (Python, 共享 Deployment)
                                              │
                                              ├─ 1. admission webhook 校验 (Kopf @kopf.on.validate 或独立 webhook)
                                              │     ✓ agentRef SA 存在 (kubernetes_asyncio get)
                                              │     ✓ scopeRef KnowledgeScope 存在
                                              │     ✓ sourceKnowledgeRef (若填写) 同 scope
                                              │
                                              ├─ 2. 若 memoryKey 已存在（同三元组）
                                              │     └─ 命中 reinforce：
                                              │        - confidence += 0.05 (≤1.0)
                                              │        - reinforcedCount += 1
                                              │        - lastReinforcedAt = now (UTC)
                                              │        - lastDecayedAt = now (衰减重启)
                                              │
                                              └─ 3. 若不存在 → 创建新 Memory
                                                    - confidence 初始值（默认 0.5）
                                                    - reinforcedCount = 0
                                                    - decayDays 默认 30
                                                    - phase: Active
                                                    ↓
                                            60s 后 MemoryReconciler (kopf.timer) 计算 effectiveConfidence
```

### 8.6 失败处理

| 失败类型 | Python 实现行为 |
|----------|----------------|
| Agent Pod 崩溃 | K8s 自动重启；Kopf handler 检测到 Ready 失败 → emit Event |
| A2A RPC 超时 | `httpx` + `tenacity` 重试（指数退避），超过 maxRetries → 任务失败 |
| Workflow 任务失败 | 标记下游任务为 Skipped；总体状态 Failed |
| Operator 崩溃 | Leader Election 切换（Lease）；其他 Pod 接管 |
| Adapter 崩溃 | Sidecar 重启；Agent 处于 NotReady 状态 |
| **Knowledge Service 不可用** | queryKnowledge 返回 `KNOWLEDGE_INTERNAL_ERROR`；Agent 可降级为本地缓存查询 |
| **Memory admission 拒绝** | 写入失败，返回 4xx 错误码；Agent 可回退到本地会话上下文（非持久化） |
| **MemoryReconciler 崩溃** | Leader Election 切换；Memory 状态在重启后从 etcd 重建（无状态丢失） |
| **event loop 阻塞** | `event_loop_lag` 指标告警 + 线程 offload 队列监控（ADR-0005 §6.3） |

---

## 9. 可观测性（Python 全栈 · 沿用 v0.1 命名）

### 9.1 指标（Prometheus · `prometheus-client` 单进程模式）

**命名规范**：`superteam_<component>_<metric>_<unit>_<suffix>`（**与 v0.1 Go 版完全相同**）

**Operator 指标**：
- `superteam_operator_reconcile_total{crd, result}` — Counter
- `superteam_operator_reconcile_duration_seconds{crd}` — Histogram
- `superteam_operator_leader_election` — Gauge

**A2A 指标**：
- `superteam_a2a_rpc_total{agent, method, status}` — Counter
- `superteam_a2a_rpc_duration_seconds{agent, method}` — Histogram
- `superteam_a2a_active_streams` — Gauge

**Agent 指标**：
- `superteam_agent_pod_resource_usage{agent, resource}` — Gauge
- `superteam_agent_token_total{agent, model, type}` — Counter
- `superteam_agent_invocations_total{agent, result}` — Counter

**Workflow 指标**：
- `superteam_workflow_active{namespace}` — Gauge
- `superteam_workflow_duration_seconds{workflow}` — Histogram
- `superteam_workflow_tasks_total{workflow, status}` — Counter

**Knowledge 指标**（ADR-0002 §9.4）：
- `superteam_knowledge_query_total{scope, type, result}` — Counter
- `superteam_knowledge_query_duration_seconds` — Histogram
- `superteam_knowledge_items_total{scope, type, phase}` — Gauge
- `superteam_knowledge_search_index_size` — Gauge

**Memory 指标**（ADR-0003 §9.4）：
- `superteam_memory_record_total{scope, agent, result}` — Counter
- `superteam_memory_query_total{scope, visibility, result}` — Counter
- `superteam_memory_decay_total{phase_from, phase_to}` — Counter
- `superteam_memory_reconcile_duration_seconds` — Histogram
- `superteam_memory_eligible_for_promotion_total` — Counter
- `superteam_memory_total{scope, phase}` — Gauge

**Python runtime 新增指标**（ADR-0005 §10 · **不重定义既有指标**）：
- `superteam_python_event_loop_lag_seconds` — Histogram（event loop 阻塞检测）
- `superteam_python_thread_offload_queue_depth` — Gauge（anyio 线程池队列深度）
- `superteam_python_active_asyncio_tasks` — Gauge（活跃 task 数）
- `superteam_python_gc_collections_total{generation}` — Counter（GC 触发计数）

### 9.2 Trace（OpenTelemetry Python SDK · W3C Trace Context）

**Span 结构**：
```
Workflow Run
  └── Task Run
        └── A2A RPC
              ├── Adapter.Translate
              ├── Agent.Run
              │     ├── LLM Call
              │     └── MCP Tool Call
              └── Adapter.TranslateBack
```

**Trace ID 透传**：
- 通过 A2A Message metadata 注入 `traceparent`
- 通过 K8s Downward API 注入 Pod EnvVar
- Workflow → Task → A2A 全程关联

**Python 特定要求**（ADR-0005 §10）：
- 显式 provider 注入；测试不能污染全局 provider
- OTel exporter 必须使用 async export pipeline

**A2A RPC Span 字段契约**（与 L2-1 Spec v0.2.0 §16.1 一致）：
- `rpc.system="a2a"`、`rpc.service=<Agent name>`、`a2a.method=<6 个 method 名>`
- span attribute 完整列表 + W3C Trace Context 注入位置详见 [L2-1 Spec v0.2.0](../../spec/L2-module-specs/L2-a2a-protocol.md) §16.1 + [L1 Spec v0.2.0 §15](../spec/L1-system-spec.md)

### 9.3 日志（`structlog` + stdlib logging · JSON）

```json
{
  "ts": "2026-07-24T10:00:00.000Z",
  "level": "info",
  "msg": "Task completed",
  "trace_id": "abc123",
  "agent": "hello-agent",
  "task_id": "task-456",
  "duration_ms": 1234,
  "namespace": "default"
}
```

**必含字段**：`trace_id` / `agent` / `task_id` / `workflow` / `namespace` / `ts`

**禁忌**：
- 禁止打印 API Key / Token / 用户数据 / Memory content / Knowledge body
- Python `Message/Memory/Knowledge content` 永不进入普通日志（ADR-0005 §10）

### 9.4 K8s Events

**所有 Controller 状态变更必须 emit Event**：
- `Normal`：Pod 启动、任务完成
- `Warning`：reconcile 错误、Webhook 拒绝、超时
- 命名：`<Component><Action><Result>`（如 `AgentCreated`、`ReconcileFailed`）

**Python 实现**：Kopf `kopf.event` API 或 `kubernetes_asyncio.CoreV1EventInterface.create`。

### 9.5 Grafana 仪表盘

v0.1 提供（与 Go 版同名 JSON）：
- **Operator Health**：reconcile 速率、错误率、leader 状态
- **A2A RPC**：QPS、延迟分布、错误码
- **Agent Resources**：CPU / Memory / Token 使用
- **Workflow**：活跃数、平均时长、成功率
- **Knowledge**：query QPS、index size、items by phase
- **Memory**：record/query QPS、decay events、eligibleForPromotion

---

## 10. 安全（Python 实现路径）

### 10.1 信任模型

```
┌──────────────────────────────────────────────────────────┐
│ Trust Domain 1: Platform                                 │
│   - Cluster Admin（操作 Operator）                        │
│   - Operator ServiceAccount（K8s API · kubernetes_asyncio）│
│   - cert-manager（证书颁发）                              │
└──────────────────────────────────────────────────────────┘
                          │ ↓
┌──────────────────────────────────────────────────────────┐
│ Trust Domain 2: Tenant Namespace                         │
│   - Namespace Admin（操作 CRD）                          │
│   - Agent ServiceAccount（同 namespace）                  │
│   - NetworkPolicy 边界（同 namespace）                    │
└──────────────────────────────────────────────────────────┘
                          │ ↓
┌──────────────────────────────────────────────────────────┐
│ Trust Domain 3: Agent ↔ Agent                            │
│   - mTLS 互信（Python ssl.SSLContext + URI SAN SPIFFE）  │
│   - Agent Card 验证                                       │
└──────────────────────────────────────────────────────────┘
```

### 10.2 身份与认证

| 路径 | 认证方式（Python 实现） |
|------|------------------------|
| User → kubectl | K8s RBAC（ClusterRole / Role） |
| User → Helm | K8s ServiceAccount |
| Operator → API Server | K8s ServiceAccount + `kubernetes_asyncio`（最小权限 RBAC） |
| Agent ↔ Agent | mTLS（cert-manager + Python `ssl.SSLContext` + SPIFFE URI SAN） |
| Agent → LLM | LLM API Key（External Secrets Operator 注入） |

### 10.3 RBAC（与 v0.1 Go 版一致）

**Operator 需要的最小权限**（CRD-level）：
- `agents`, `agentsets`, `workflows` — full access
- `knowledgescopes`, `knowledgeitems`, `memories` — full access
- `pods`, `services`, `configmaps`, `secrets` — own namespace
- `events` — create
- `serviceaccounts` — own namespace
- `leases` — get, list, watch, create, update, patch（**Leader Election**）
- `admissionregistration.k8s.io/validatingwebhookconfigurations` — manage（如启用 admission webhook）

**Agent 需要的最小权限**：
- `configmaps` (get) — 读配置
- `secrets` (get) — 读 LLM API Key（External Secrets 注入）
- `events` (create) — emit 业务事件
- `memory (create, get, list, update)` — 仅 Agent 自己的 SA；**禁止 delete**
- `knowledgeitems (get, list)` — 仅 scope 内；agent-private 校验在 Knowledge Service 层

**Knowledge Service 需要的最小权限**：
- `knowledgescopes`, `knowledgeitems` (get, list, watch)
- `memories` (get, list, watch, create, update)
- `serviceaccounts` (get) — 校验 agentRef
- `events` (create)

**MemoryReconciler 需要的最小权限**（与 Knowledge Service 共享 Deployment）：
- `memories` (get, list, watch, update, delete)
- `serviceaccounts` (get) — 校验 agentRef
- `events` (create)
- `leases` — Leader Election

### 10.4 Pod Security

- **默认**：Pod Security Standard `restricted`
- **例外**：v0.1 允许 `baseline`（标 ADR 记录）
- **禁止**：`privileged` / `hostNetwork` / `hostPID` / `hostIPC`
- **Python 镜像**：非 root、read-only rootfs、drop all capabilities、`allowPrivilegeEscalation=false`（ADR-0005 §9.3）

### 10.5 Network Policy

**默认行为**：deny all ingress/egress

**必须显式 allow**：
- Agent Container ↔ Adapter Sidecar（localhost，仅 loopback）
- Ingress：API Server → Adapter（端口 8080）
- Egress：Adapter → DNS / LLM API / 其他 Agent（按需）

### 10.6 镜像供应链（Python 双层扫描）

- **基础镜像**：`python:3.12-slim`（多阶段构建；非 root；最小依赖）
- **签名**：cosign keyless（GitHub OIDC）
- **扫描**：
  - **Python wheel 层**：Bandit + `pip-audit`（CI 强制）+ Dependabot/Renovate
  - **镜像层**：Trivy / Grype
- **SBOM**：syft（Python wheel + 系统包，CI 强制）

### 10.7 审计

- K8s audit log 不可关闭
- A2A RPC 留 OTel Span
- 结构化日志保留 90 天
- 关键操作（CRD 删除 / namespace 删除）emit Warning Event

---

## 11. 资源模型

### 11.1 默认资源限制

| 资源 | request | limit | 配置项 | Python 镜像基线 |
|------|---------|-------|--------|----------------|
| **Operator** | 100m / 256Mi | 1000m / 1Gi | `resources.operator` | `python:3.12-slim` |
| **Adapter** | 50m / 64Mi | 500m / 256Mi | `resources.adapter` | `python:3.12-slim` + framework 层 |
| **Agent** | 100m / 256Mi | 1000m / 1Gi | `resources.agent` | user-provided |
| **AgentSet 单副本** | = Agent | = Agent | 继承自 Agent | — |
| **Knowledge Service + MemoryReconciler**（共享 Deployment） | 200m / 512Mi | 1500m / 2Gi | `resources.knowledge_service` | `python:3.12-slim` |

### 11.2 限流（API · Python 实现）

- **Operator SharedInformer**：默认 QPS 5 / Burst 10（`kubernetes_asyncio` 配置）
- **A2A RPC**：单 Agent 默认 100 RPS（`httpx` semaphore + 限流中间件）
- **Memory batch reconcile**：单次 ≤ 1,000 items（`asyncio.Semaphore`）
- **K8s API Server**：依赖其限流

### 11.3 命名空间配额

**默认**（Helm 安装时创建）：
- `pods: 100`
- `services: 100`
- `secrets: 50`
- `configmaps: 50`
- `requests.cpu: 10`
- `requests.memory: 20Gi`
- `limits.cpu: 20`
- `limits.memory: 40Gi`

**可被 Helm values 覆盖**

### 11.4 成本控制

- 单 Agent 任务 `max_tokens: 50000`
- 单 Workflow `max_tokens: 200000` / `max_cost: $5`
- 超限熔断 + K8s Event 告警
- 所有上限可在 Helm values 调整

### 11.5 Python 性能预算（ADR-0005 §12 · 基准测试目标）

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 1 KiB A2A loopback p50/p95/p99 | < 5ms / < 20ms / < 50ms | `pytest-benchmark` |
| Pydantic validation overhead | < 1ms | `pytest-benchmark` |
| Agent Card cache hit | < 0.5ms | `pytest-benchmark` |
| EndpointSlice watch invalidation | < 100ms | kind E2E |
| 10K KnowledgeItem BM25 query p95 | < 200ms | `pytest-benchmark` |
| 50K Memory batch decay | < 60s | kind E2E |
| reconcile throughput | ≥ 100 reconcile/min | Locust |
| event-loop lag p95 | < 50ms | `prometheus-client` Gauge |
| RSS per Pod | < 1Gi | `prometheus-client` Gauge |

**触发升级决策**（ADR-0005 §12.2）：
1. 先 profile；
2. 减少不必要分配/重复校验；
3. 使用连接池、cache、batch 和受控 thread offload；
4. 通过 Pod 水平扩容验证；
5. 仍不满足时提交 ADR。

> 禁止未经 ADR 静默加入 Go sidecar，避免重新产生双语言核心。

---

## 12. 部署架构

### 12.1 Helm Chart 结构

```
helm/
├── Chart.yaml
├── values.yaml              # 默认值
├── values.schema.json       # schema 校验（含 Python 镜像/Pyright/Ruff 配置块）
├── README.md
├── CHANGELOG.md
├── templates/
│   ├── _helpers.tpl
│   ├── operator/
│   │   ├── deployment.yaml       # Python Operator Pod
│   │   ├── serviceaccount.yaml
│   │   ├── rbac.yaml
│   │   └── service.yaml
│   ├── knowledge-service/        # v0.1 共享 Deployment（Knowledge + MemoryReconciler）
│   │   ├── deployment.yaml
│   │   ├── serviceaccount.yaml
│   │   ├── rbac.yaml
│   │   └── service.yaml
│   ├── crds/                     # 由 build/gen_crds.py 从 Pydantic 生成
│   │   ├── agent.yaml
│   │   ├── agentset.yaml
│   │   ├── workflow.yaml
│   │   ├── knowledgescope.yaml
│   │   ├── knowledgeitem.yaml
│   │   └── memory.yaml
│   ├── rbac/
│   │   └── clusterrole.yaml
│   ├── networkpolicies/
│   │   └── default-deny.yaml
│   ├── serviceaccount.yaml
│   └── tests/
│       └── connection_test.yaml
```

### 12.2 安装命令

```bash
helm repo add superteam-a2a https://coderzhangfujiang.github.io/superteam-a2a
helm install superteam-a2a superteam-a2a/superteam-a2a \
  --namespace superteam-a2a-system \
  --create-namespace
```

### 12.3 升级策略

- **Patch 升级**：Helm upgrade（无中断）
- **Minor 升级**：Helm upgrade + 手动迁移（如必要）
- **Major 升级**：Helm upgrade + CRD conversion + ConfigMap 迁移

### 12.4 多环境

- **dev**：单副本 Operator、调试日志、Mock Adapter
- **staging**：高可用、Full 监控
- **prod**：高可用、所有安全特性、备份

---

## 13. 约束与非目标

### 13.1 v0.1 范围

**包含**（依据 [ADR-0001](../../adr/0001-v1-scope-statement.md) + [ADR-0004](../../adr/0004-v01-scope-extension-knowledge-and-memory.md) + [ADR-0005](../../adr/0005-python-first-technology-stack.md)）：

- **5 大基础能力**：发现 / 通信 / 监控 / 编排 / **知识管理（含 Memory）**
- **6 个 CRD**（v1alpha1）：Agent / AgentSet / Workflow / KnowledgeScope / KnowledgeItem / Memory
- **6 个 A2A method**：`sendMessage` / `getTask` / `queryKnowledge` / `getKnowledgeItem` / `recordMemory` / `queryMemory`
- **4 个 Controller**（Kopf handlers + Python services）：Agent / AgentSet / Workflow / MemoryReconciler
- **2 个特殊 Agent**（Python）：Hello Agent / Knowledge Service（Card-driven，共享 Deployment 与 MemoryReconciler）
- **1 个参考 Adapter**：Hello Agent（无框架）
- **1 套 E2E Demo**（2 Agent + 1 Workflow + 知识 + 记忆演示）
- **基本 Helm Chart**（Operator + Knowledge Service Deployment + RBAC + NetworkPolicy + cert-manager）
- **基本监控 / 日志 / Events**（含 Knowledge / Memory 10 个新指标 + Python runtime 4 个新指标）
- **admission webhook**：双向互斥规则（Knowledge ↔ Memory）
- **Python 工具链**：uv workspace / Ruff / Pyright strict / Bandit / pip-audit / kind
- **交付期**：20 周（2026-07-08 → 2027-01-20）；**ADR-0005 不改变功能范围，但设计重写延迟 L4 开始，新截止日期在 L1 v0.2 review 时重新估算**

**不包含**（明确推迟）：
- 其他框架 Adapter（LangChain / AutoGen / CrewAI / SK / Strands / Smolagents）—— v0.5+
- SSE Streaming（`a2a.subscribeTask` / `a2a.cancelTask`）—— v0.5+
- UI / Dashboard —— v1.0+
- CRD Conversion webhook（v0.1 单 v1alpha1 版本足够）—— v0.5+
- KEDA / HPA 自动扩缩容 —— v0.5+
- 多集群联邦 —— v2+
- Vector DB 集成 —— v0.5+（v0.1 用 etcd + 内存 BM25）
- Knowledge Graph / 实体关系 —— v0.5+
- 自动化 scope-up（KnowledgePromotionRequest）—— v0.5+
- Memory 跨 cluster 联邦 / 静态加密 —— v0.5+
- Memory 内容审核 / 敏感词过滤 —— v0.5+
- Platform native extension（Cython/Rust）—— 走 ADR（ADR-0005 §6.3）

### 13.2 v1.0 范围

**包含**：
- 6 个框架 Adapter（LangChain / AutoGen / CrewAI / SK / Strands / Smolagents）
- 完整 A2A 协议（Stream / Artifact）
- 4 个 CRD（+ Conversation）
- Helm Chart 1.0
- 完整 Dashboard
- 社区贡献通道（CI / 模板）

### 13.3 永远不做

- **闭源**：Apache 2.0 always
- **多云联邦**：v2 范畴
- **Vector DB 抽象**：每个 Agent 自带
- **非 SDLC 模板**：社区添加
- **对任何 Agent 框架的偏好**：所有框架平等
- **未经 ADR 静默引入第二核心语言**（Go sidecar / 原生扩展）：ADR-0005 §6.3 + §17

### 13.4 风险与未决

| 风险 | 影响 | 缓解 |
|------|------|------|
| A2A 协议变更 | 破坏兼容 | 复用官方 SDK + 锁定 minor 版本范围，跟踪上游 |
| K8s API 弃用 | 需重构 | 跟 Kopf / kubernetes_asyncio 版本 |
| Kopf 与 controller-runtime 成熟度差距 | 部分 reconcile 行为不一致 | ADR-0005 §7 列 12 项 kind 验证清单 |
| Python GIL/单进程状态约束 | 多 worker 不可用 | ADR-0005 §6.2 单进程 + 多 Pod 水平扩展 |
| mTLS/SPIFFE 热更新复杂度 | 证书失效风险 | cert-manager mounted cert + URI SAN；`py-spiffe` v0.1 验证 |
| 缺少 envtest 等价物 | 集成测试更依赖 kind | ADR-0005 §11.2 / §9.2 mock+fake 仅单元测试 |
| Python dependency/supply-chain 面更大 | 供应链风险 | uv.lock + pip-audit + Bandit + Dependabot |
| Hello Agent 过于简单 | 难以 demo | v0.2 增加 LangChain Adapter |
| 维护者 2h/day 不够 | 进度不可控 | 严格 MVP 范围 + 招募贡献者 |
| 社区冷启动 | 不达 stars 目标 | 早期 Demo + Show HN |

---

## 14. 路线图对齐

**L1 v0.2 设计对应 ROADMAP 阶段**：

| ROADMAP 阶段 | L1 组件 | 状态 |
|--------------|---------|------|
| Phase 0 Foundation | 仓库 + 宪法 v0.5.0 + ROADMAP | ✅ |
| Phase 1 MVP Core (Go) | Operator + 3 CRD + Hello Agent + A2A Core | ✅ L1 v0.1.0 通过（已 supersede） |
| Phase 1.5 L1 Python 重写 | L1 Architecture/Spec v0.2.0 + ADR-0005 | 🚧 进行中 |
| Phase 2 L2 Python 重写 | L2-1~L2-4 v0.2 | 待 L1 v0.2 通过 |
| Phase 3 L3 Python 重写 | L3-1~L3-6 + 归档 L3 Go draft | 待 L2 v0.2 通过 |
| Phase 4 L4 初始化 | uv workspace + 实现 | 待 L3 通过 |
| Phase 5 多框架 Adapter | LangChain / AutoGen / CrewAI / SK / Strands / Smolagents | 待 v0.5 |
| Phase 6 公开 launch | Helm chart published | 待 v0.5+ |

---

## 15. 术语表

详见 [`L1-system-spec.md` § 附录 A](../spec/L1-system-spec.md#附录-a术语表)

**新增 Python 术语**：

| 术语 | 定义 |
|------|------|
| **Kopf** | Python Kubernetes Operator 框架（handlers + retry + resume + finalizer） |
| **`kubernetes_asyncio`** | K8s 官方 Python 客户端的 asyncio 适配 |
| **官方 a2a-sdk** | google-a2a/a2a-python 仓库提供的 A2A Python SDK |
| **compatibility adapter** | 项目自有层与官方 SDK 之间的边界（`superteam_a2a.a2a.upstream`） |
| **Pydantic v2** | Python 类型 + 校验基础；CRD/JSON Schema 单一来源 |
| **uv** | Astral 提供的 Python workspace + lock 工具 |
| **ASGI / Uvicorn** | Python 异步 HTTP 服务器；单 worker / 单 event loop 部署 |
| **Tenacity** | Python 重试库，受 method idempotency gate 约束 |
| **`anyio.to_thread.run_sync`** | 阻塞 CPU 工作 offload 到线程池 |
| **`structlog`** | Python 结构化日志库（JSON） |
| **Leader Election（Lease）** | `coordination.k8s.io/v1 Lease` 单活；不依赖 Kopf peering |

---

## 16. 开放问题（Python-first 重写后的新风险）

> 需要在 L2 / L3 设计时定夺

1. **A2A 协议**：官方 `a2a-sdk` 成熟度 vs 项目 4 个扩展 method 注册路径？ → **倾向**：compatibility adapter router，contract test 验证 wire 一致（ADR-0005 §3.2 + §8）
2. **Adapter 部署**：Sidecar 强制 vs 同进程 plugin 可选？ → **倾向**：v0.1 Sidecar + Python 同进程 plugin 双模式
3. **Agent Card 持久化**：CRD 字段 vs 单独 ConfigMap？ → **倾向**：CRD 字段
4. **Trace 采样**：默认 100% vs 10%？ → **倾向**：100%（易调试）
5. **CRD 数量**：3 vs 6（+ KnowledgeScope / KnowledgeItem / Memory）？ → **决议**：v0.1 六个（依据 ADR-0001 + ADR-0004）
6. **Adapter vs Operator 边界**：Adapter 能否调用 K8s API？ → **倾向**：不能（仅协议 + `kubernetes_asyncio` 受限读 CRD）
7. **Knowledge Service 部署形态**：单实例 vs 多实例？ → **决议**：v0.1 单实例（依据 ADR-0002 §4.3）
8. **MemoryReconciler reconcile 频率**：60s 固定 vs 自适应？ → **倾向**：v0.1 固定 60s；v0.5+ 评估自适应
9. **Knowledge 搜索性能上限**：10K items P95 ≤ 200ms 是否可达？ → **待 L2 / Phase 2 Python benchmark 验证**
10. **Memory GC 时机**：phase=Expired 后 7 天 vs 立即删除？ → **决议**：7 天宽限期（依据 ADR-0003 §4.5，finalizer 保护）
11. **eligibleForPromotion 触发 v0.5+**：自动化生成 KnowledgePromotionRequest 是否需人工审批？ → **倾向**：需 Owner 审批（v0.5 ADR 评估）
12. **CRD 生成器稳定性**：`build/gen_crds.py` 的 deterministic + CI 验证？ → **倾向**：v0.1 引入；CI 验证无未提交 diff
13. **`py-spiffe` vs cert-manager mounted cert**：`py-spiffe` Workload API 在 L3 验证；不满足时回退 URI SAN（ADR-0005 §9.1）
14. **Leader Election**：K8s Lease vs Kopf peering？ → **倾向**：K8s Lease（避免额外 CRD 成本）
15. **Python image 多阶段构建**：`python:3.12-slim` builder + distroless/slim runtime？ → **倾向**：v0.1 builder + runtime 都 `python:3.12-slim`；distroless 评估推 v0.5+
16. **Event-loop lag 阈值告警**：> 50ms 触发 Warning Event？ → **倾向**：v0.1 实现 + Helm values 可配置
17. **Kopf handler 与业务 service 的拆分比例**：handler 仅 30-50 行 + service 业务逻辑？ → **倾向**：v0.1 强制；code review 检查

---

## 17. 验收清单（v0.2 · Python-first）

> L1 v0.2 设计被认定为"通过"必须满足

- [x] 所有 5 层职责清晰，无跨层调用
- [x] **6 个 CRD 模型覆盖 5 大能力**（Agent / AgentSet / Workflow / KnowledgeScope / KnowledgeItem / Memory）
- [x] **6 个 A2A method 字段定义清晰**（含 4 个项目扩展：queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）
- [x] **wire contract 与 v0.1 完全一致**（YAML 字段名、JSON 字段、错误码、Task FSM、Agent Card 路径）
- [x] **Python 实现栈锁定**：Python 3.12+ / uv / Kopf / kubernetes_asyncio / 官方 a2a-sdk / Pydantic v2 / Uvicorn / httpx / structlog
- [x] **Kopf vs controller-runtime 语义映射完整**（handler / resume / timer / finalize / leader election）
- [x] **async-first 边界明确**（K8s I/O / A2A HTTP / webhook / OTel exporter；阻塞 CPU offload 到 anyio thread）
- [x] **Pydantic v2 strict + JSON Schema 2020-12 单源 + CRD YAML 确定性生成**
- [x] **官方 a2a-sdk compatibility adapter 边界**（`superteam_a2a.a2a.upstream`）
- [x] **Knowledge ↔ Memory 边界清晰**（admission webhook 双向互斥规则 + Python 实现路径）
- [x] **5 维可见性矩阵实现路径明确**（4 scope × agent-private 正交）
- [x] Adapter 契约明确（5 行 YAML 原则 + `typing.Protocol`）
- [x] A2A 协议集成有版本对齐（v0.3 core + 4 扩展 method）
- [x] **可观测指标覆盖全栈**（含 Knowledge / Memory 10 个指标 + Python runtime 4 个新指标）
- [x] **Python 供应链门禁**（uv.lock + pip-audit + Bandit + Dependabot）
- [x] 安全信任模型有边界（含 Python `ssl.SSLContext` + SPIFFE URI SAN）
- [x] **Pod Security：Python 镜像非 root + read-only rootfs + drop all capabilities**
- [x] 资源默认值 + 可配置 + Python 性能预算表
- [x] 部署路径完整（Helm + uv workspace + kind）
- [x] v0.1 / v1.0 范围清晰
- [x] 风险与未决有缓解方案（含 17 项新风险）
- [x] 与宪法 v0.5.0 无冲突（§3.8 Python-first + §9.7 Python 静态质量 + §10.3 docstring + §13.6 维护 + §14 L3 注释例外）
- [x] **与 5 个 ADR 一致**（ADR-0001 / 0002 / 0003 / 0004 / 0005）
- [x] **与 Go v0.1 业务语义完全一致**（wire 不变，仅替换实现栈）
- [x] **与官方 A2A SDK 上游追踪责任明确**（§13.6 维护 SDK 兼容）
- [x] **MVP 例外 §14.5 显式声明**（v0.1 阶段适用）

---

> **状态**：✅ **v0.2.0 已评审通过**（2026-07-24，依据 [`docs/reviews/l1-python-stack-migration-review.md`](../reviews/l1-python-stack-migration-review.md) §A-§F + ADR-0005 + 宪法 v0.5.0；10 维度全 PASS + 27 项验收清单全部勾选）
> **supersedes**：v0.1.0 Go baseline（仅 supersede Go / kubebuilder / controller-runtime / client-go / envtest 实现条款；wire contract 与业务语义继续有效）
> **下一步**：L2-1 A2A Protocol Python 重写（必做 ADR-0005 §8 a2a-python spike）→ L2-1 v0.2.0 → L2-2~L2-4 Python v0.2 → 归档 L3 Go draft → 重写 Python L3 → 初始化 uv workspace → L4 实现
> **评审者**：项目发起人（基于单人维护者 + MVP 例外 14.5 单点评审）
> **变更摘要**（2026-07-24 · v0.1 → v0.2 增量）：
> - **+1 ADR**（ADR-0005 Python-first）→ 替换 5.3 / 4.3 / 4.1 / 2.2 全部 Go 字眼
> - **实现栈**：Go 1.22+ → **Python 3.12+ / uv workspace**
> - **Operator**：controller-runtime → **Kopf + kubernetes_asyncio**
> - **A2A Core**：自研 Go → **官方 a2a-sdk + compatibility adapter**
> - **类型层**：Go struct + kubebuilder annotation → **Pydantic v2 strict + JSON Schema 2020-12 + CRD OpenAPI 确定性生成**
> - **HTTP**：net/http + gorilla/mux → **Uvicorn + Starlette/FastAPI（ASGI）单 worker**
> - **HTTP client**：→ **httpx.AsyncClient（连接池复用）**
> - **重试**：→ **Tenacity**
> - **指标**：prometheus/client_golang → **prometheus-client 单进程**
> - **Trace**：OTel Go → **OTel Python（显式 provider 注入）**
> - **日志**：log/slog + zap → **structlog + stdlib logging**
> - **新增** §3.6 async-first / 单进程原则 / GIL / 线程 offload / event-loop lag 监控
> - **新增** Python runtime 4 个指标 + 性能预算表（§9.1 + §11.5）
> - **新增** uv workspace 布局 + Helm Chart Python 镜像配置块（§4.1 + §12.1）
> - **新增** 17 项开放问题（含 Python-first 重写后的新风险 §16）