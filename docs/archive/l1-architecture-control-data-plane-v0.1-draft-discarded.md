# superteam-a2a — L1 架构候选：控制平面 / 数据平面 / 横切 三段视角（v0.1-draft · **已归档**）

> ## ⚠️ 归档标记（2026-07-30 · 会话 #68）
>
> **状态变更**：🟡 v0.1-draft 候选草案 → 🗄️ **已归档（不合并）**
>
> **决策路径**：用户选择 **路径 B：最小化 L4 启动门禁**（2026-07-30 #68 AskUserQuestion）
>
> **决策理由**：
> 1. L4 实施层启动时间紧迫，本草案升级 L1 v0.3 需 4-6 session（§F 6 步 + 独立评审 + ADR 流程），延迟过大
> 2. L3-5 + L3-6 共享 Deployment 的唯一架构门禁是 OPEN-MEMORY-001（跨 container transport spike），与本草案的"三段视图"无强依赖
> 3. T1/T2/T3 三个内在张力虽显式标注但未关闭，合并 L1 v0.3 风险高于收益
> 4. 沿用 L1 v0.2.0 §2.2 旧图启动 L4 实施层；待 L4 实战验证后再决定是否重新激活本草案（OPEN-L1-004 / OPEN-L1-005）
>
> **未来重新激活条件**（任一满足可重启评审）：
> - L4 实施第一周实战发现 L1 v0.2.0 §2.2 旧图 3 个内在张力阻碍开发
> - OPEN-MEMORY-001 spike 结论反向影响 L1 架构视图
> - L4 中期（Phase 1 MVP Core 完成后）回顾触发
>
> **配套现行 L1 不变**：[`docs/design/L1-architecture.md`](../../docs/design/L1-architecture.md) v0.2.0（2026-07-24 评审通过）
>
> **关联 ADR-0006**：OPEN-MEMORY-001 跨 container transport spike（UDS / 共享 runtime / 共享 mmap / 同进程 / HTTP loopback 五选一）独立起草，不依赖本草案
>
> **关联归档 pointer**：[`docs/design/l1-architecture-control-data-plane-archived.md`](../../docs/design/l1-architecture-control-data-plane-archived.md)
>
> ---

> **状态**：🟡 **v0.1-draft 候选草案**（**非现行 L1**；现行 L1 仍为 [`L1-architecture.md`](../../docs/design/L1-architecture.md) v0.2.0 / 2026-07-24 评审通过；本草案为 v0.3 候选讨论稿）
> **目的**：把现行 L1 §2.2 的「5 层请求流」视图（① 接入 / ② 编排 / ③ 资源模型 / ④ 通信 / ⑤ 运行时）改写为「控制平面 / 数据平面 / 横切」三段视图，**解决原视图的 3 个内在张力**（CRD 跨 ②/③、MemoryReconciler 错位、A2A ④ 主体不清），并为 L4 实施层提供更清晰的入口。
> **变更来源**：2026-07-30 #67.x 会话讨论（与项目发起人当面）；L1 阶段 6/6 全部 v0.2.0 文件级 Spec 通过后的下一阶段规划
> **决策窗口**：L4 实施层启动前必须决定是否合并到 L1 v0.3；不合并则 L4 沿用 L1 v0.2.0 §2.2 旧图
> **配套规范**：现行 L1 v0.2.0 [`L1-architecture.md`](./L1-architecture.md) §0-§15 + [L1 Spec v0.2.0](../spec/L1-system-spec.md) + L2-1/L2-2/L2-3/L2-4 v0.2.0 + L3-1/2/3/4/5/6 v0.2.0
> **不做的事**（本草案未触及，需另案）：CRD wire contract 变更 / 不变量 5 项 Python 化决策修订 / 宪法 §3.4/§6/§7/§9.7/§13.1 修订 / 任何新增 ADR

---

## 0. 阅读指南

**读者**：架构委员会、L4 实施层入口决策者、企业接入方

**何时使用本草案**：
- L4 实施层启动前决定入口顺序时（按本草案的"控制平面 → 数据平面"逐层进入）
- 评估企业网关嵌入点时（控制平面 vs 数据平面 vs 横切的归位判断）
- 评审 MEMORY_* / KNOWLEDGE_* 错误码跨平面传播时

**何时回退到 L1 v0.2.0 §2.2**：
- PR 描述引用 L1 鸟瞰图时（旧图依然是 baseline）
- 跨文档同步引用 `L1-architecture.md §2.2` 时

---

## 1. 为什么重画

### 1.1 L1 v0.2.0 §2.2 旧视图的 3 个张力

| # | 张力 | 旧视图处理 | 后果 |
|---|---|---|---|
| **T1** | **CRD 跨 ② 和 ③** | ② 写"`(creates / watches)` CRD"，③ 写"`(translates to)` CRD" | CRD 既是被操作对象（控制）又是状态 schema（数据），两层耦合但被分到两段 |
| **T2** | **MemoryReconciler 错位** | 画在 ⑤「运行时层」，但本质是 60s `@kopf.timer` 控制循环 | 让人误以为它是 Agent；忽略它"逻辑归属 ② 编排 / 物理驻留 ⑤ 数据平面"的双重身份 |
| **T3** | **A2A ④ 主体不清** | ④ 描述为"通信层"，但发起方和接收方都是 ⑤ Agent Pod | ④ 实际是"通信能力（SDK + method 集合）"，不是"通信双方"——把它独立画成一层制造了独立段位的错觉 |

### 1.2 三段视图的替换目标

| 段 | 主轴 | 回答"什么角色" | 候选是否解决张力 |
|---|---|---|---|
| **控制平面** | 谁调度 / 谁持有状态 schema | 编排者 + 状态词汇 | T1 ✅（CRD 整段归控制平面）/ T2 ✅（MemoryReconciler 标注为"逻辑归属控制平面 / 物理在数据平面"） |
| **数据平面** | 谁执行 / 谁通信 | 业务 Pod + 通信能力 | T3 ✅（A2A 嵌入每个 Agent 进程，不是独立段） |
| **横切** | 跨段正交关注点 | observability / 安全 / 静态质量 / 部署 / 类型 | — |

---

## 2. 三段架构图

```
═══════════════════════════════════════════════════════════════════════════════
  superteam-a2a v0.2.0 · 控制平面 / 数据平面 / 横切 三段架构
  (L1 v0.2.0 + L2 4/4 + L3 6/6 全部文件级 Spec 评审通过)
═══════════════════════════════════════════════════════════════════════════════


╔═════════════════════════════════════════════════════════════════════════════╗
║                       控制平面  Control Plane                              ║
║  (单 Operator Python 进程 · replicaCount=1 · L3-1 模块 162 文件 / 277 ID)   ║
║  部署在: superteam-a2a-system namespace                                     ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌────────────────────┐                                                     ║
║  │  ① 接入  Access    │                                                     ║
║  │  ┌──────────────┐  │       ┌──────────────────────────────────────────┐  ║
║  │  │ kubectl      │  │       │  ② 编排  Orchestration  (L3-1)          │  ║
║  │  │ Helm         │──┼──────▶│  Python 3.12 + Kopf + kubernetes_asyncio│  ║
║  │  │ Dashboard    │  │       │                                          │  ║
║  │  │ CLI          │  │       │  ┌────────────────────────────────────┐ │  ║
║  │  └──────────────┘  │       │  │  3 个 CRD Controller (C-1)        │ │  ║
║  │  ─────             │       │  │  · Agent      @kopf.on.create/update│ │  ║
║  │  反依赖规则:        │       │  │  · AgentSet   @kopf.on.create/update│ │  ║
║  │  不得直接调 A2A    │       │  │  · Workflow   @kopf.on.create/update│ │  ║
║  │  客户端, 只能 apply │       │  └────────────────────────────────────┘ │  ║
║  │  CRD              │       │                                          │  ║
║  └────────┬───────────┘       │  ┌────────────────────────────────────┐ │  ║
║           │                   │  │  MemoryReconciler (C-1.4)          │ │  ║
║           │ CRD apply         │  │  @kopf.timer(interval=60.0,         │ │  ║
║           ▼                   │  │              id="memory-reconciler")│ │  ║
║  ┌────────────────────┐       │  │  4 纯函数: decay / reinforce /      │ │  ║
║  │  K8s API Server   │◀──────┼──┤  GC / eligibleForPromotion          │ │  ║
║  │  (集群控制枢纽)    │       │  │  ⚠ 物理在数据平面 (L3-6)            │ │  ║
║  │  · etcd 存储       │       │  │  逻辑归属控制平面 (L3-1 §3.4)       │ │  ║
║  │  · schema 校验     │       │  └────────────────────────────────────┘ │  ║
║  └────────┬───────────┘       │                                          │  ║
║           │                   │  ┌────────────────────────────────────┐ │  ║
║           │ 同步 / 监视        │  │  横向 control flow (全 Operator 域)│ │  ║
║           │                   │  │  · admission webhook  ←→ 业务 Pod   │ │  ║
║           │                   │  │    Knowledge ↔ Memory 双向互斥      │ │  ║
║           │                   │  │    50ms fail-closed                 │ │  ║
║           │                   │  │  · Leader Election (Lease)          │ │  ║
║           │                   │  │    renew 失败 3 次让位 + 30s grace   │ │  ║
║           │                   │  │  · Finalizer handling               │ │  ║
║           │                   │  │  · Helm 9 模板 (Deployment/RBAC/    │ │  ║
║           │                   │  │    NetworkPolicy/PrometheusRule/...) │ │  ║
║           │                   │  └────────────────────────────────────┘ │  ║
║           │                   └────────────────┬─────────────────────────┘  ║
║           │                                    │ creates / patches /       ║
║           │                                    │ watches 业务 CRD          ║
║           │                                    ▼                           ║
║           │       ┌────────────────────────────────────────────────────┐  ║
║           │       │  ③ 状态词汇  Resource Model                          │  ║
║           │       │  6 CRD v1alpha1 · Pydantic v2 → OpenAPI v3           │  ║
║           │       │                                                     │  ║
║           │       │  ┌─────────┐ ┌─────────┐ ┌─────────┐               │  ║
║           │       │  │ Agent   │ │AgentSet │ │Workflow │ ← ② 管理       │  ║
║           └──────▶│  │ (C-2)   │ │ (C-3)   │ │ (C-4)   │               │  ║
║                   │  └─────────┘ └─────────┘ └─────────┘               │  ║
║                   │                                                     │  ║
║                   │  ┌────────────────┐ ┌────────────────┐ ┌────────┐ │  ║
║                   │  │KnowledgeScope  │ │KnowledgeItem   │ │ Memory │ │  ║
║                   │  │ (C-6 part)     │ │ (C-6 part)     │ │ (C-7)  │ │  ║
║                   │  └────────────────┘ └────────────────┘ └────────┘ │  ║
║                   │  ← 业务 Agent Pod (⑤) 写入 + 读取                  │  ║
║                   │                                                     │  ║
║                   │  wire 永久不变: 12 spec 字段 + 12 MEMORY_* 错误码    │  ║
║                   │  + 4 级 scope + 5 维 visibility (任何修改走 ADR)     │  ║
║                   └────────────────────────────────────────────────────┘  ║
║                                                                            ║
╚═════════════════════════════════════════════════════════════════════════════╝
                                       ║
                                       ║ K8s API (CRD apply/watches)
                                       ║ + admission webhook callbacks
                                       ║
                                       ▼
╔═════════════════════════════════════════════════════════════════════════════╗
║                       数据平面  Data Plane                                 ║
║  (多 Pod · 每 Pod 单 Python 进程 · uvicorn 1 worker · 共享 IPC)            ║
║  部署在: superteam-a2a namespace (业务 CRD 应用所在)                       ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │  ④ 通信能力  A2A Protocol  (L3-2 库, 嵌入每个 Agent 进程)           │  ║
║  │  ★ 这是"协议栈", 不是"通信双方" — 通信双方都是 ⑤ Agent Pod           │  ║
║  │                                                                      │  ║
║  │  ┌────────────────────────┐    ┌─────────────────────────────────┐  │  ║
║  │  │ 官方 a2a-sdk  (upstream)│ +  │  4 extension method (project)    │  │  ║
║  │  │ · sendMessage            │    │  · queryKnowledge                │  │  ║
║  │  │ · getTask                │    │  · getKnowledgeItem              │  │  ║
║  │  │ · Agent Card / Message   │    │  · recordMemory ─┐ 委托 ⑤b      │  │  ║
║  │  │ · Task / Artifact        │    │  · queryMemory  ─┘ 共享 Deployment│  │  ║
║  │  └────────────────────────┘    └─────────────────────────────────┘  │  ║
║  │                                                                      │  ║
║  │  wire: JSON-RPC 2.0 over HTTP · mTLS TLS 1.3 (cert-manager / PKI)   │  ║
║  │  discovery: K8s Service / EndpointSlice / .well-known/agent.json     │  ║
║  │  observability: 15 shared + 20 KS+MEM + 10 Memory = 45 metrics        │  ║
║  │  error codes: 24 L3-2 + 23 L3-5 (11 KNOWLEDGE_ + 12 MEMORY_)         │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║         ▲                              ▲                          ▲        ║
║         │ 嵌入(import)                 │ 嵌入(import)             │ 嵌入    ║
║         │                              │                          │        ║
║  ┌──────┴────────────────────┐ ┌────────┴─────────────────┐ ┌────┴───────┐ ║
║  │  ⑤a 业务 Agent Pod        │ │  ⑤b Knowledge Service     │ │ ⑤c Hello   │ ║
║  │  (用户/Agent 框架作者)     │ │     + Memory backend      │ │   Agent    │ ║
║  │                           │ │     共享 Deployment 双进程 │ │  (C-5)     │ ║
║  │  ┌──────────┐  ┌────────┐ │ │                           │ │            │ ║
║  │  │ Adapter  │  │ Agent  │ │ │  ┌──────────┐ ┌─────────┐ │ │  ┌──────┐  │ ║
║  │  │ 侧车     │  │ 业务   │ │ │  │ KS Pod   │ │  MEM    │ │ │  │单    │  │ ║
║  │  │ (L3-3)   │  │ 框架   │ │ │  │:8080     │ │  Pod   │ │ │  │Pod   │  │ ║
║  │  │:15001    │  │:8080   │ │ │  │:8443 mTLS│ │:8081   │ │ │  │:8080 │  │ ║
║  │  │localhost │  │        │ │ │  │1 uvicorn │ │(probe) │ │ │  │uvi-  │  │ ║
║  │  └──────────┘  └────────┘ │ │  │worker    │ │60s     │ │ │  │corn  │  │ ║
║  │                           │ │  │          │ │timer   │ │ │  │1 wkr │  │ ║
║  │  Adapter 模式:             │ │  │ 4 A2A    │ │        │ │ │  │      │  │ ║
║  │  · Sidecar (默认)          │ │  │ method   │ │4 纯函数│ │ │  │ 参考 │  │ ║
║  │  · 同进程 (Python plugin)  │ │  │ handler  │ │+ LE    │ │ │  │ 实现 │  │ ║
║  │  · 6 framework adapters    │ │  │+ admission│ │+ clock │ │ │  │      │  │ ║
║  │    LangChain/AutoGen/      │ │  │(独占)    │ │+ BM25  │ │ │  │L3-4  │  │ ║
║  │    CrewAI/SK/Strands/      │ │  └──────────┘ └─────────┘ │ │  └──────┘  │ ║
║  │    Smolagents              │ │                           │ │            │ ║
║  │                           │ │  ⚠ 共享 Deployment:        │ │            │ ║
║  │  → L3-3 Adapter SDK       │ │  共享 SA / TLS Secret /    │ │  → L3-4    │ ║
║  │  (162 文件 / 200 ID)      │ │  ConfigMap / IPC volume    │ │  (1576 行) │ ║
║  └───────────────────────────┘ │  进程隔离 + 共享网络         │ └────────────┘ ║
║                               │  详见 L3-5 §6.2 line 1488) │                  ║
║                               │  → L3-5 + L3-6             │                  ║
║                               │  (2467+1850 行 / 120 ID)    │                  ║
║                               └────────────┬───────────────┘                  ║
║                                            │                                  ║
║                                            │ A2A envelope (mTLS)              ║
║                                            │ KS pod 内的 4 method              ║
║                                            │ record/query → 委托 MEM 进程     ║
║                                            ▼                                  ║
║                  ⑤b 内部 IPC (L4 spike 待定 OPEN-MEMORY-001)                ║
║                  ┌──────────────────────────────────────┐                    ║
║                  │ 候选:                                │                    ║
║                  │ (a) Unix Domain Socket (UDS)         │                    ║
║                  │     emptyDir 挂载 /var/run/superteam │                    ║
║                  │     mode 0660 + UID/GID 隔离          │                    ║
║                  │ (b) 共享 Python runtime (同进程)     │                    ║
║                  │     不推荐: 破坏 "每 Pod 单 Python 进程" │                 ║
║                  │ (c) 共享 memory-mapped region         │                    ║
║                  │     v0.5+ 候选, 性能更好              │                    ║
║                  │ 禁止: HTTP loopback (违反宪法 §3.4)   │                    ║
║                  └──────────────────────────────────────┘                    ║
║                                                                            ║
║         ▲ JSON-RPC over mTLS  ▲ A2A envelope     ▲ A2A envelope           ║
║         │ (5a ↔ 5b/5c)        │ (5b ↔ 5c 或其他)  │ (5b ↔ 5a)             ║
║         └─────────────────────┴────────────────────┴──────────────────────  ║
║                                  (Agent 间互发现 + 互调)                    ║
║                                                                            ║
╚═════════════════════════════════════════════════════════════════════════════╝
                                  ║
                                  ║ metrics / traces / logs / events
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                横切关注点  Cross-Cutting Aspects                              │
│                (与控制平面/数据平面正交, 通过依赖注入贯穿所有层)               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─ observability (as code 注入到所有 Pod + Operator)                       │
│  │   · prometheus-client: 45 metrics (15+20+10)                             │
│  │   · OpenTelemetry Python SDK: W3C traceparent + OTLP                     │
│  │   · structlog: 8 必含字段 (timestamp/level/service/trace_id/span_id/     │
│  │                  request_id/agent_id/event) + recursive redaction          │
│  │   · K8s Events: 8 EventReason (Operator + KS + MEM)                      │
│  └──────────────────────────────────────────────────────────────────────────│
│  ┌─ 安全 (Security)                                                          │
│  │   · mTLS TLS 1.3: cert-manager (默认) / HotReloader 原子替换 /             │
│  │                  2160h duration + 720h renewBefore                        │
│  │   · RBAC: read-only Role (L3-5) / write Role (L3-6) / + admissionreg     │
│  │          + tokenreviews + subjectaccessreviews (L3-6 followup-4)         │
│  │   · NetworkPolicy: default-deny + 显式 allow (8443/8080/443/4317)        │
│  │   · Pod Security: restricted (runAsNonRoot + seccomp + readOnlyRootFS)   │
│  │   · 9 项敏感字段脱敏: api_key/token/password/secret/                     │
│  │                       memory_content/content/knowledge_body/             │
│  │                       tls_key/private_key                                │
│  └──────────────────────────────────────────────────────────────────────────│
│  ┌─ 静态质量 (Quality Gates · 5+1 门禁)                                     │
│  │   · uv sync --frozen                                                     │
│  │   · ruff format --check && ruff check                                     │
│  │   · pyright --level error (strict)                                       │
│  │   · bandit -r && pip-audit                                               │
│  │   · interrogate -f 100 (docstring 100% 覆盖)                            │
│  │   · lint-imports (ST-MEMORY-BOUNDARY / ST-KNOWLEDGE-BOUNDARY 强制)       │
│  └──────────────────────────────────────────────────────────────────────────│
│  ┌─ 部署与发布 (Deploy)                                                     │
│  │   · Helm Chart: 7 模板 (L3-5/6 共享) / 9 模板 (L3-1 Operator)            │
│  │   · Dockerfile: python:3.12-slim + uv build + SBOM/Trivy/Cosign           │
│  │   · Argo CD Application + syncPolicy (automated prune/selfHeal)          │
│  │   · uv workspace (ADR-0005 §13.1)                                       │
│  └──────────────────────────────────────────────────────────────────────────│
│  ┌─ 类型与契约 (Type System)                                                 │
│  │   · Pydantic v2 strict (extra="forbid" + frozen + AwareDatetime UTC)     │
│  │   · typing.Protocol (MemoryBackend / Clock / InProcessService)           │
│  │   · wire contract 永久不变: 12 spec 字段 + 12 MEMORY_* name/code         │
│  └──────────────────────────────────────────────────────────────────────────│
│                                                                             │
│  注入路径:                                                                  │
│  ┌─ 控制平面: ② 编排层全部 (Kopf handlers + async services)                 │
│  ├─ 数据平面: ④ 嵌入每个 ⑤ Pod 进程                                        │
│  ├─ 数据平面: ⑤b 双 container 共享 IPC volume + TLS Secret                 │
│  └─ CRD: ③ 通过 admission webhook 校验 (L3-5 §5 互斥算法)                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 三段视图与现行 L1 v0.2.0 §2.2 旧图的逐项对应

| 旧视图 (L1 v0.2.0 §2.2) | 新视图 (本草案) | 差异 |
|---|---|---|
| ① 接入 | 控制平面 · ① 接入 | 不变 |
| ② 编排 | 控制平面 · ② 编排 | 不变（但 MemoryReconciler 标注"逻辑归属此处 / 物理在 ⑤b"） |
| ③ 资源模型 | 控制平面 · ③ 状态词汇 | **整个 CRD 集（6 个）合并为控制平面的一段**，旧图分到 ②/③ 两段 |
| ④ 通信 | 数据平面 · ④ 通信能力 | **明确标注为"协议栈嵌入每个 ⑤ Pod 进程，不是独立段"** |
| ⑤ 运行时 | 数据平面 · ⑤a / ⑤b / ⑤c 三种 Pod 形态 | 旧图把所有 Agent 混在一段；新图按"Adapter 侧车" / "KS+MEM 共享 Deployment" / "单进程参考" 三种 Pod 形态分列 |
| 横切关注点 | 横切关注点（不变） | observability / 安全 / 静态质量 / 部署 / 类型 — 完全对应 |

---

## 4. 3 个内在张力（重画后仍未自动解决，但已显式标注）

| # | 张力 | 当前处理 | 待决策 |
|---|---|---|---|
| **T1** | **MemoryReconciler 跨平面** | 物理在数据平面（`memory-backend` container，60s timer），逻辑归属控制平面（Operator 编排） | 是否要为这种"控制循环驻留在数据平面"现象定义新角色名（如"in-pod controller"），而不是简单画"桥"？ |
| **T2** | **admission webhook 双向互斥归谁** | L3-5 §5 独占 `@kopf.validation`（业务知识），但 webhook 注册在 Operator（L3-1 §7.3） | v0.2 维持现状；L4 实施时验证 webhook 50ms 端到端时延（Operator → KS admission → K8s API callback） |
| **T3** | **共享 Deployment 心智模型冲突** | ⑤b 同 Pod 双 Python 进程（L3-5 §6.2 line 1488）；ADR-0005 §6.2 单进程原则被"共享网络 + 进程隔离"调和 | 后续 L4 transport spike 选 UDS（不打破单进程）/ 共享 runtime（打破单进程）/ 共享 mmap（v0.5+）三选一 |

---

## 5. L4 实施入口（按本草案三段分层）

| 顺序 | 起点 | 终点 | 对应段 | L4 第一周任务 |
|---|---|---|---|---|
| 1 | ② | ③ | 控制平面 | uv workspace 初始化 + 6 CRD Pydantic v2 schema 落地 |
| 2 | ② | ③ | 控制平面 | 3 个 Controller + admission webhook + Finalizer + Lease |
| 3 | ⑤c | ④ | 数据平面 | Hello Agent 单进程 ASGI 起来（最小冒烟） |
| 4 | ④ | ⑤c | 数据平面 | mTLS cert-manager + a2a-sdk 接入 |
| 5 | ⑤a | ④ | 数据平面 | Adapter SDK 模板 + 第一个 framework adapter |
| 6 | ⑤b | ④ | 数据平面 | KS + MEM 共享 Deployment（**OPEN-MEMORY-001 spike 必做**） |
| 7 | 横切 | 全部 | 全部段 | observability / RBAC / NetworkPolicy 集成 |

**最关键**的是 **#6 OPEN-MEMORY-001** —— 这是 L4 开工前唯一架构门禁：跨 container transport 选 UDS / 共享 runtime / 共享 mmap 哪个，**决定 ⑤b 双进程是否真的能落地**。

---

## 6. 合并到 L1 v0.3 的待办（草案不构成正式提案）

本草案如要升格为 L1 v0.3 正式版，需先解决以下前置：

| 前置 | 现状 | 行动 |
|---|---|---|
| 宪法 v0.5.0 兼容性 | L1 §2.2 旧图无宪法定向 | 本草案 §2 三段图与宪法 §3.4/§3.7/§3.8/§6/§7/§9.7/§13.1/§15.5/§16.1 全部兼容；如有不一致需 ADR |
| 跨文档同步 | 现行 L2/L3 v0.2.0 全部引用旧图 | 合并前需 L1 v0.3 → L1 Spec v0.3 → L2 附录 → L3 §0 阅读指南 同步（§F 6 步） |
| 评审 10 维度 | 旧图无独立评审 | 合并前需独立评审（沿用 L1 v0.2.0 评审模板 §A-§P） |
| T1/T2/T3 张力决策 | 本草案显式标注但未关闭 | 合并前需 T1（in-pod controller 命名） / T2（webhook 时延） / T3（transport 选型）三项至少 2 项有结论 |
| 与 L1 Spec v0.2.0 §15 视图一致性 | L1 Spec v0.2.0 可能引用旧图 | 需对齐 L1 Spec §15 鸟瞰图 |

**不构成正式提案的依据**：未走 §16.1 宪法纪律的单点评审 + §14.5 MVP 例外窗口内评审 + ADR 流程。

---

## 7. 开放问题

| ID | 问题 | 状态 | 决策窗口 |
|---|---|---|---|
| OPEN-L1-001 | T1 in-pod controller 是否要起新名字？ | 🟡 | L4 启动前 |
| OPEN-L1-002 | T2 admission webhook 端到端 50ms 时延验证 | 🟡 | L4 实施第一周 |
| OPEN-L1-003 | T3 ⑤b 跨 container transport 选 UDS / 共享 runtime / 共享 mmap | 🟡 | L4 启动前（OPEN-MEMORY-001 spike） |
| OPEN-L1-004 | 本草案是否合并到 L1 v0.3？ | 🟡 | L4 启动前 |
| OPEN-L1-005 | L1 Spec v0.3 鸟瞰图是否同步改为三段视图？ | 🟡 | 同 OPEN-L1-004 |

---

## 文档元数据

| 字段 | 值 |
|---|---|
| 草案版本 | v0.1-draft |
| 创建日期 | 2026-07-30 |
| 创建会话 | #67.x 后段（与项目发起人当面讨论） |
| 配套现行 L1 | [`L1-architecture.md`](./L1-architecture.md) **v0.2.0**（2026-07-24 评审通过；不变） |
| 配套 L2 | L2-1 / L2-2 / L2-3 / L2-4 v0.2.0（不变） |
| 配套 L3 | L3-1 / L3-2 / L3-3 / L3-4 / L3-5 / L3-6 v0.2.0（不变） |
| 配套 ADR | ADR-0001 / ADR-0002 / ADR-0003 / ADR-0004 / ADR-0005（不变） |
| 配套宪法 | v0.5.0（不变） |
| 状态 | 🟡 草案，不构成正式提案 |
| 决策窗口 | L4 实施层启动前（OPEN-L1-004） |
| 下次更新 | 决定合并 → 启动 L1 v0.3 起草 + §F 6 步同步；不合并 → 本文档归档至 `docs/archive/l1-architecture-control-data-plane-v0.1-draft-discarded.md` |

---

<sub>📬 本草案仅作 L4 实施层入口决策参考；任何引用应同时引用现行 L1 v0.2.0 §2.2 以避免歧义。诚实悲观估算：本草案合并 L1 v0.3 的工作量约 5-8% 单会话水位（独立评审 + §F 6 步同步）；不合并则 0% 工作量。</sub>
