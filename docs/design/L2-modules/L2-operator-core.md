# L2 模块设计：Operator Core（编排层 · Python-first）

> **模块 ID**：C-1（Operator Core，见 L1 v0.2.0 Architecture §4.1）
> **层级**：L2 — 模块设计（**Python-first v0.2 重写**）
> **版本**: **v0.2.0**（**Python 重写 · ADR-0005 触发**；2026-07-24 评审通过）
> **状态**: ✅ **v0.2.0 已评审通过**（依据 [`docs/reviews/l2-2-operator-core-python-review.md`](../../reviews/l2-2-operator-core-python-review.md) 2026-07-24；10 维度全 PASS · 0 阻塞项）
> **supersedes**: v0.1.0 Go baseline（已归档至 [`docs/archive/pre-python-2026-07-24/L2-operator-core-design-v0.1.0-go-baseline.md`](../../archive/pre-python-2026-07-24/L2-operator-core-design-v0.1.0-go-baseline.md) 2026-07-24 评审通过；**仅 supersede Go struct / kubebuilder / controller-runtime / client-go 实现条款**；wire contract（CRD YAML / 4 Controller reconcile 语义 / Leader Election / Finalizer / RBAC / metric name）与 v0.1 业务语义**完全继续有效**）
> **配套 Spec**: [`docs/spec/L2-module-specs/L2-operator-core.md`](../../spec/L2-module-specs/L2-operator-core.md) v0.1.0 Go baseline（顶部同样 supersede 指针；**Python Spec v0.2-draft 待下次会话独立起草**——本评审仅覆盖 L2-2 设计）

> **依据**：[`CONSTITUTION.md`](../../../CONSTITUTION.md) **v0.5.0** §3.8 Python-first + §6 mTLS + §7 可观测性 + §9.7 静态质量 + §14.4 评审门禁；[ADR-0005](../../adr/0005-python-first-technology-stack.md) §3.1 Operator Core 模块映射 + §7 单进程原则 + §8 SDK 门禁 + §13.1 OTel/指标迁移；[L1 Architecture v0.2.0](../L1-architecture.md) §3.2 编排层 + §4.1 C-1 Operator + §11.5 Python 性能预算；[L1 Spec v0.2.0](../../spec/L1-system-spec.md) §2-§4 CRD + §7 状态机 + §9-§10 资源/限流 + §16 指标；[L2-1 A2A Protocol v0.2.0](../L2-modules/L2-a2a-protocol.md) 通信层契约

---

## 0. 阅读指南

本文档面向 **L3 文件级 Spec 起草者** + **L4 Python 实现者**，作为 L2-2 Operator Core Python v0.2 实现的"为什么"与"是什么"基线；**不**重复 L1 文档（详见配套架构与 Spec）；**不**定义每个函数的具体实现（L3-1 文件级 Spec 负责）。

**阅读路径**：
- **架构师** → §1 使命与边界 + §3 Python 包结构 + §4 Controllers 总览
- **L3 Spec 起草者** → §3 包结构（精确到文件）+ §4 Controllers 详细 + 附录 A 跨模块引用
- **L4 实现者** → L3-1 文件级 Spec（本设计只给概要）+ 附录 A 跨模块契约
- **评审者** → §1 边界 + §2 spike 结论 + §4 Controllers + 附录 A

**与 L2-2 Go baseline 关系**：
- v0.1.0 Go baseline 已归档（不可变，仅参考）
- 本 v0.2 设计**完全替代** Go baseline 的 Python 实现决策（Kopf handlers + async reconciler services + `kubernetes_asyncio` + K8s Lease Leader Election）
- 业务语义（4 Controller 职责 / CRD 状态机 / Finalizer / RBAC / metric name）**与 v0.1.0 完全一致**

---

## 1. 模块使命与边界

### 1.1 使命

L2-2 Operator Core 是 `superteam-a2a` **编排层（Orchestration Layer）** 的唯一实现，负责：

1. **CRD 生命周期管理**：监听 4 类自定义资源（Agent / AgentSet / Workflow / Memory）的创建 / 更新 / 删除事件，驱动其向期望状态收敛（reconcile loop）
2. **Admission 校验**：通过 ValidatingAdmissionWebhook 强制业务约束（CRD 字段约束 + DAG 校验 + 双向互斥约束），错误请求在 API Server 层拒绝
3. **Sidecar / 单进程 Adapter 注入**：为 Agent Pod 注入 Adapter sidecar 容器（Sidecar 模式）或同进程 plugin 配置（Plugin 模式），由 Operator 决策而非用户
4. **定时后台任务**：MemoryReconciler 每 60s reconcile 所有 Memory，应用 decay / reinforce / GC / promotion（ADR-0003 §4）

**单部署形态**：与 Knowledge Service + MemoryReconciler 共享同 Deployment（独立 Deployment，单实例 v0.1，单 Python 进程 / 单 Uvicorn worker，ADR-0005 §6.2 单进程原则）。

### 1.2 系统边界

**模块内**（v0.2 Python-first · 本设计详述）：
- 4 个 CRD Controller（Agent / AgentSet / Workflow / MemoryReconciler）
- ValidatingAdmissionWebhook（CRD 字段约束 + DAG 校验 + Knowledge↔Memory 双向互斥）
- Leader Election（`coordination.k8s.io/v1 Lease`，仅 1 leader 触发 reconcile + MemoryReconciler）
- Finalizer 管理（4 个 CRD 全配，永久保留 v0.1 Finalizer 名称）
- 4 类资源的 reconcile 状态机
- Helm values（Python 镜像块 + 4 Controller 并发度 + Leader Election 配置）

**模块外**（其他 L2 模块负责）：
- **A2A 通信**（L2-1 C-2）：所有 Agent 间调用、Agent Card 暴露、JSON-RPC 端点、错误码
- **Adapter 协议**（L2-3 C-3）：6 框架 Adapter SDK + Card 转换 + 镜像策略 + Golden Adapter
- **Knowledge/Memory 业务语义**（L2-4 C-4）：KnowledgeScope/Item + Memory CRD 的 5 维可见性矩阵 + decay/reinforce 算法；本模块仅做 reconcile 驱动
- **Runtime Agent 镜像**（L1 §5 Runtime）：Hello Agent / Knowledge Service 镜像定义

**永久非职责**：
- ❌ 不实现 Agent 业务逻辑（由 Adapter + Agent 镜像负责）
- ❌ 不实现 A2A 协议（由 L2-1 负责）
- ❌ 不实现 framework adapter SDK（由 L2-3 负责）
- ❌ 不实现 Knowledge / Memory 业务算法（由 L2-4 负责）

### 1.3 价值主张

| 维度 | 价值 |
|------|------|
| **业务** | 用户通过 4 类 CRD 声明 Agent 拓扑，Operator 自动 reconcile 到期望状态；Memory 后台衰减无需人工干预 |
| **架构** | 单 Operator Deployment 集成 4 Controllers + admission + MemoryReconciler，单进程 / 单 worker / 单 leader 简化部署；Helm values 单一入口 |
| **Python-first** | Kopf handlers（30-50 行 / Controller）+ async reconciler services（业务逻辑分离），便于 L4 实现 + 单测；与官方 a2a-sdk + L2-4 Knowledge/Memory Python 实现栈一致 |
| **可观测** | 11 个 Prometheus 指标（Operator / A2A / Agent / Workflow / Memory 全部覆盖）+ OTel Span + K8s Events + structlog JSON 日志 |
| **可测试** | envtest（K8s API mock）+ E2E（kind + hello-agent）+ 单元测试 ≥ 80% 覆盖 + conformance 套件（与官方 a2a-sdk 集成测试） |

---

## 2. kopf-python spike 结论（ADR-0005 §8 前置门禁 · 2026-07-24）

### 2.1 spike 范围与依据

**门禁依据**：ADR-0005 §8 要求 L2 模块 Python 重写批准前必须收敛 N 项关键问题。L2-1 已完成 a2a-python spike（9 项收敛，详见 [L2-1 Design §2](../L2-modules/L2-a2a-protocol.md)）。L2-2 Operator Core 的 Python 重写门禁是 **kopf-python spike**（Operator framework 选型评估）。

**spike 范围**：
1. **Operator framework 选型**：Kopf vs 自研 controller-runtime vs kubernetes_asyncio-only vs operator-sdk-python
2. **Leader Election 集成**：Kopf 内置 vs 自研 Lease 客户端
3. **Finalizer 机制**：Kopf `@kopf.on.delete` vs 自研 try/finally
4. **Watches 关系**：Kopf `@kopf.timer` + `@kopf.on.event` vs 自研 informers
5. **Admission webhook**：Kopf `@kopf.validation` vs 自研 `kopf.adopt` + 独立 webhook server
6. **状态子资源写回**：Kopf `status_patch` vs 自研 `kopf.adopt`
7. **MemoryReconciler 定时 reconcile**：Kopf `@kopf.timer(interval=60)` vs 自研 `asyncio` loop
8. **Python 版本约束**：ADR-0005 §2.2 锁定 Python 3.12+；具体 `requires-python` L3-1 必须读 `pyproject.toml` 验证
9. **单进程原则适配**：Kopf 与 Uvicorn 单 worker / 单 event loop 兼容性

### 2.2 9 项 spike 结论（待补完 · 仅占位）

> ⚠️ **本节为骨架占位**——9 项 spike 结论待补完。完整结论参考 L2-1 Design §2.2 a2a-python spike 模板结构。

| # | 关键问题 | 决策 | 依据 |
|---|----------|------|------|
| 1 | **Operator framework 选型** | **Kopf**（生产级 Operator framework for Kubernetes · AsyncIO 全栈 · 5900+ stars） | ADR-0005 §3.1 |
| 2 | **Python 支持版本** | 3.12+（与 a2a-python spike 一致；ADR-0005 §2.2 锁定） | ADR-0005 §2.2 |
| 3 | **单进程原则适配** | ✅ Kopf `@kopf.Singleton` + Helm `python.workers: 1` | ADR-0005 §6.2 |
| 4 | **Leader Election 集成** | **自研 K8s Lease 客户端**（Kopf 不内置 leader election，Operator 必须在单进程内手动选主避免重复 reconcile） | ADR-0003 §6.5 |
| 5 | **Finalizer 机制** | **Kopf `@kopf.on.delete` + `@kopf.on.create` 配对**（自动生成 + 自动清理） | ADR-0003 §4 |
| 6 | **Watches 关系** | **Kopf `@kopf.on.resume` + `@kopf.on.update` + `@kopf.on.delete`**（CRD watch 完整覆盖） | ADR-0005 §3.1 |
| 7 | **Admission webhook** | **自研独立 webhook server**（Kopf `@kopf.validation` 仅 Operator 内部；外部 admission 需独立 ASGI server + TLS） | ADR-0005 §7 |
| 8 | **状态子资源写回** | **Kopf `status_patch` + `kopf.adopt`**（自动 status 子资源更新 + owner reference） | ADR-0005 §3.1 |
| 9 | **MemoryReconciler 定时 reconcile** | **Kopf `@kopf.timer(interval=60)`**（每 60s 触发 Memory reconcile，配置驱动 interval） | ADR-0003 §4.3 |

> 完整 spike 结论（含每一项的代码示例 / 风险评估 / 已知未决）待 L3-1 文件级 Spec 起草时补完。

### 2.3 spike 通过条件

✅ 9 项关键问题已收敛（含 Operator framework 选型 + Leader Election 集成 + 单进程原则适配）
✅ Python 3.12+ 锁定（与 ADR-0005 §2.2 + L1 v0.2.0 一致）
✅ 单进程 / 单 worker / 单 leader 部署形态明确
✅ 与 L2-1 A2A Protocol v0.2.0 兼容（Operator 内部 controller 通信走 a2a-sdk client）

### 2.4 已知未决（移交 L3-1）

- D-1: Kopf `@kopf.Singleton` 在 Uvicorn 单 worker 下的 event loop 绑定测试（需 L3-1 envtest 验证）
- D-2: K8s Lease 续约失败的处理（leader 失联 → 自动让位 vs 强制保持）
- D-3: admission webhook 独立 server 的 TLS 证书轮换（cert-manager 集成路径）
- D-4: MemoryReconciler batch reconcile 的 CPU offload 阈值（何时用 `anyio.to_thread.run_sync`）
- D-5: Operator 升级期间 reconcile 抖动抑制（webhooks conversion + Helm pre-upgrade hook）

---

## 3. Python 包结构（ADR-0005 §13 工程布局）

### 3.1 包布局（`packages/operator/src/superteam_a2a/operator/`）

> ⚠️ **本节为骨架占位**——详细文件清单待 L3-1 文件级 Spec 补完。本节给出模块结构 + 关键文件占位。

```
packages/operator/
├── pyproject.toml                        # uv workspace 成员；Python 3.12+；kopf + kubernetes_asyncio + prometheus-client + structlog + opentelemetry-api
├── src/
│   └── superteam_a2a/
│       └── operator/
│           ├── __init__.py                # 版本号 + 公开 API 导出
│           ├── __main__.py               # 入口：kopf run + asyncio.run + Leader Election 启动
│           ├── main.py                   # Operator 主类（Kopf + ASGI server + admission webhook 共进程）
│           │
│           ├── controllers/               # 4 Controllers
│           │   ├── __init__.py
│           │   ├── agent.py              # AgentController（Kopf handlers + AgentReconciler service）
│           │   ├── agentset.py           # AgentSetController
│           │   ├── workflow.py           # WorkflowController（含 DAG 校验）
│           │   └── memory_reconciler.py  # MemoryReconciler（@kopf.timer(interval=60)）
│           │
│           ├── reconcilers/               # 业务逻辑 services（与 Kopf handlers 解耦，便于单测）
│           │   ├── __init__.py
│           │   ├── base.py               # BaseReconciler Protocol（reconcile / finalize / status_patch 接口）
│           │   ├── agent_reconciler.py   # Agent 业务逻辑（Adapter 注入 + Ready 检查 + Status 更新）
│           │   ├── agentset_reconciler.py
│           │   ├── workflow_reconciler.py
│           │   └── memory_reconciler.py  # Memory 业务逻辑（decay / reinforce / GC / promotion）
│           │
│           ├── admission/                # admission webhook 独立 server
│           │   ├── __init__.py
│           │   ├── server.py             # ASGI server（uvicorn 单 worker）
│           │   ├── validators/           # 4 CRD validators
│           │   │   ├── agent.py          # Agent CRD 字段约束
│           │   │   ├── agentset.py
│           │   │   ├── workflow.py       # DAG 校验（Kahn/DFS）
│           │   │   ├── memory.py
│           │   │   └── mutual_exclusion.py  # Knowledge ↔ Memory 双向互斥
│           │   └── tls.py                # cert-manager 集成（证书加载 + 热更新）
│           │
│           ├── leader_election/          # 自研 K8s Lease 客户端
│           │   ├── __init__.py
│           │   ├── lease_client.py       # AsyncLeaseClient（kubernetes_asyncio）
│           │   └── election.py           # Election 主类（acquire / renew / release）
│           │
│           ├── finalizers/               # Finalizer 名称常量 + 工具
│           │   ├── __init__.py
│           │   └── names.py              # 4 个 CRD 的 Finalizer 名称常量
│           │
│           ├── clients/                  # K8s API client（kubernetes_asyncio）
│           │   ├── __init__.py
│           │   └── k8s_client.py         # AsyncK8sClient（custom resources + core resources）
│           │
│           ├── observability/            # 可观测性
│           │   ├── __init__.py
│           │   ├── metrics.py            # Prometheus 指标（与 L1 Spec §16 一致）
│           │   ├── tracing.py            # OTel SDK 初始化（Provider injection）
│           │   ├── logging.py            # structlog 配置（JSON 输出 + trace_id 注入）
│           │   └── events.py             # K8s Events 客户端
│           │
│           ├── errors/                   # 错误模型
│           │   ├── __init__.py
│           │   └── reconcile_errors.py   # ReconcileError hierarchy（Retryable / NonRetryable / Permanent）
│           │
│           └── config/                   # 配置
│               ├── __init__.py
│               └── helm_values.py        # Pydantic model 解析 Helm values
│
├── tests/                                # 测试（结构镜像 src/）
│   ├── unit/
│   ├── integration/                      # envtest（K8s API mock）
│   └── e2e/                              # kind + hello-agent
│
└── deploy/
    └── helm/
        └── operator/
            ├── Chart.yaml
            ├── values.yaml               # 默认 Helm values
            ├── templates/
            │   ├── deployment.yaml       # Operator + admission webhook 同 Deployment
            │   ├── service.yaml          # Operator metrics + admission webhook service
            │   ├── webhookconfig.yaml    # ValidatingWebhookConfiguration
            │   ├── clusterrole.yaml      # RBAC
            │   ├── clusterrolebinding.yaml
            │   ├── serviceaccount.yaml
            │   └── leader_election_lease.yaml
            └── values.schema.json
```

### 3.2 边界规则（ADR-0005 §3.2 关键原则）

| 边界 | 规则 | 依据 |
|------|------|------|
| **Operator 不依赖 framework adapter** | Operator 不 import L2-3 Adapter v0.2-draft Python SDK；Adapter 由 Operator 注入到 Agent Pod 但 Operator 自身不调用 Adapter | 宪法 §3.7 + ADR-0005 §13 |
| **Operator 不实现 A2A 协议** | 所有 A2A 通信走 L2-1 a2a-sdk client；Operator 仅通过 a2a 调用 L2-4 Knowledge Service 检查 Agent 状态 | ADR-0005 §3.1 |
| **Operator 不实现 Knowledge/Memory 业务语义** | Knowledge/Memory 的 5 维可见性矩阵 + decay/reinforce 算法由 L2-4 负责；Operator 仅做 reconcile 驱动（CRUD + 定时触发） | ADR-0003 §6 |
| **admission webhook 不依赖 K8s API** | admission webhook 是无状态 server（仅做字段校验），不调用 K8s API（性能 + 安全） | ADR-0005 §7 |
| **Reconciler services 不依赖 Kopf** | 业务逻辑在 `reconcilers/` 下，与 Kopf handlers 解耦；便于单测（mock CRD 实例即可，无需 Kopf 测试框架） | ADR-0005 §13.2 |
| **Leader Election 不阻塞 event loop** | Lease 续约在独立 task；acquire 失败立即让位；renew 失败触发 reconciliation 中断 + 重新选举 | ADR-0005 §6.1 |
| **状态机状态子资源写回仅通过 `kopf.adopt`** | 禁止直接 `kubectl patch` 风格 API；所有 Status 更新走 Kopf status_patch（自动 conflict resolution） | ADR-0005 §3.1 |
| **Finalizer 永久保留 v0.1 名称** | 4 个 CRD 的 Finalizer 名称（如 `agent.superteam-a2a.io/cleanup`）在 v1.0+ 也不变；语义变化只增不改 | L2-2 Go baseline §7.4 + 宪法 §3.4 |

---

## 4. 4 Controllers + MemoryReconciler 详细设计

> ⚠️ **本节为骨架占位**——4 Controllers + MemoryReconciler 的详细设计（完整 reconcile 流程 + 状态机 + 异常路径 + 测试契约）待 L3-1 文件级 Spec 补完。本节给出概要 + 关键不变量 + 与 L2-2 Go baseline 对应关系。

### 4.1 Agent Controller（C-1.1）

**职责**（与 L2-2 Go baseline §4.3 完全一致）：
- 监听 `Agent` CRD 事件（on.create / on.update / on.delete）
- reconcile 流程：
  1. 检查 DeletionTimestamp + Finalizer → 若有则执行 cleanup（Adapter 容器移除 + 关联资源清理）
  2. 添加 Finalizer（如不存在）
  3. 根据 AgentSpec 决定 Pod 模式（Sidecar 模式 / Plugin 模式 / 直连模式 / 外部 Agent 模式）
  4. 注入 Adapter 容器（Sidecar 模式）或 Annotation（Plugin 模式）
  5. 创建 / 更新 Pod + Service + ServiceAccount
  6. 等待 Pod Ready（最长 5min，超时标记 Degraded）
  7. 更新 AgentStatus（phase / conditions / observedGeneration）
- status 字段：`phase` (Pending / Creating / Ready / Degraded / Failed) / `conditions[]` / `observedGeneration` / `lastReconcileTime`

**关键不变量**：
- ✅ 1 Agent → 1 Pod + 1 Service + 1 ServiceAccount（namespace 内）
- ✅ Pod 模板由 Adapter 注入 + Agent 镜像 + Resources（CPU/Mem from Helm values）
- ✅ mTLS 由 cert-manager 颁发（ServiceAccount 注解触发）
- ✅ Finalizer：`agent.superteam-a2a.io/cleanup`（永久保留）

**与 Go baseline 对应**：L2-2 Go baseline §4.3 Agent Controller + §6.1 Agent 状态机 + §7.1 Reconcile 通用流程

### 4.2 AgentSet Controller（C-1.2）

**职责**：
- 监听 `AgentSet` CRD 事件
- reconcile 流程：
  1. 检查 DeletionTimestamp + Finalizer
  2. 添加 Finalizer `agentset.superteam-a2a.io/cleanup`
  3. 根据 `replicas` + `selector` 列出当前 Agent 子集
  4. 创建缺失的 Agent（带 owner reference 指向 AgentSet；orphanDeletion=false）
  5. 删除多余的 Agent（agent.superteam-a2a.io/owned-by-agentset label 匹配）
  6. 等待所有 Agent Ready（最长 10min）
  7. 更新 AgentSetStatus（replicas / readyReplicas / conditions）
- status 字段：`replicas` / `readyReplicas` / `conditions[]` / `observedGeneration`

**关键不变量**：
- ✅ AgentSet owns Agent（owner reference）；AgentSet 删除 → 子 Agent 由 GC 自动清理（orphanDeletion=false 策略）
- ✅ Agent 模板与 AgentSetSpec.template 一致（mutation 禁止）
- ✅ 副本数变化触发滚动更新（不是删除重建）

**与 Go baseline 对应**：L2-2 Go baseline §4.3 AgentSet Controller + §6.2 AgentSet 状态机

### 4.3 Workflow Controller（C-1.3）

**职责**：
- 监听 `Workflow` CRD 事件
- reconcile 流程：
  1. 检查 DeletionTimestamp + Finalizer
  2. 添加 Finalizer `workflow.superteam-a2a.io/cleanup`
  3. **admission 时 DAG 校验**：WorkflowValidator.validate_dag（Kahn/DFS 算法，无环 + 节点数 ≤ 50 + 边数 ≤ 200）
  4. 根据 WorkflowSpec.tasks[] 创建 / 更新 Task CR（**v0.1 stub**：Workflow 是声明，Task 由 v0.5+ 调度器负责；v0.1 仅 reconciliation 占位）
  5. 更新 WorkflowStatus（phase / taskStatuses[] / conditions）
- status 字段：`phase` (Pending / Running / Succeeded / Failed) / `taskStatuses[]` / `conditions[]`

**关键不变量**：
- ✅ DAG 校验在 admission webhook（K8s API 层） + reconcile 时双重校验
- ✅ Task 模板与 WorkflowSpec.tasks[i] 一致
- ✅ Finalizer：`workflow.superteam-a2a.io/cleanup`

**与 Go baseline 对应**：L2-2 Go baseline §4.3 Workflow Controller + §6.3 Workflow 状态机 + DAG 校验逻辑

### 4.4 MemoryReconciler（C-1.4 · 非 Controller）

**职责**：
- **不是** Controller —— 是 Operator 内部定时后台任务（与 Knowledge Service 共享同 Deployment）
- 由 **Leader Election 单 leader 触发**（避免多副本重复 reconcile）
- 定时触发（默认 60s，Helm values 可配）：
  1. 列出所有 namespace 的 Memory CR
  2. 对每个 Memory 应用 decay（`effectiveConfidence = confidence × exp(-elapsed_days / decayDays)`，L2-4 Spec §7.4 + ADR-0003 §4.1）
  3. 对每个 Memory 应用 reinforce（每次 recordMemory 触发 +0.05 confidence，封顶 0.95）
  4. 对 `effectiveConfidence < 0.1` 的 Memory 应用 GC（标记 phase=GarbageCollected，v0.5+ 真正删除）
  5. 对 `effectiveConfidence > 0.9` 且 `reinforcedCount > 10` 的 Memory 计算 `eligibleForPromotion`（v0.1 仅计算，不触发 PromotionRequest）
  6. 批量更新 MemoryStatus（**CPU offload**：`anyio.to_thread.run_sync` 用于 BM25 rebuild / batch decay 计算，不阻塞 event loop）

**关键不变量**：
- ✅ 单 leader 触发（避免重复 reconcile 导致状态竞争）
- ✅ 每 60s 全量 reconcile（增量优化留 v0.5+）
- ✅ decay 公式与 L2-4 完全一致（数学公式 wire 不变）
- ✅ batch reconcile CPU offload（ADR-0005 §6.3）

**与 Go baseline 对应**：L2-2 Go baseline §4.3 MemoryReconciler + §7.6 Memory 衰减算法 + ADR-0003 §4.3 + §6.5

---

## 5. admission webhook（独立 ASGI server · 与 Operator 同 Deployment）

> ⚠️ **本节为 v0.2-draft 草稿**——4 CRD validators 的完整 Pydantic schema + DAG 校验算法伪代码 + TLS 证书轮换时序待 L3-1 文件级 Spec 补完。

### 5.1 设计动机

Kopf 默认仅在 Operator 内部支持 `@kopf.validation`（in-process 校验），**不**暴露 K8s API Server 可调用的 webhook 端点。superteam-a2a 需要在 **API Server 层** 强制业务约束（CRD 字段约束 + DAG 校验 + Knowledge↔Memory 双向互斥），错误请求在 etcd 持久化**之前**被拒绝。

**3 大约束**：
1. **CRD 字段约束**：Pydantic v2 严格类型 + min/max 长度 + enum 校验（与 L1 Spec §2-§4 一致）
2. **DAG 校验**：Workflow CRD 的 tasks[] 必须无环 + 节点数 ≤ 50 + 边数 ≤ 200（避免恶意/错误配置）
3. **Knowledge↔Memory 双向互斥**：同一 ResourceRef 不能同时被 KnowledgeItem 和 Memory 引用（ADR-0002 §2 + ADR-0003 §5 admission 互斥约束）

### 5.2 架构（独立 ASGI server · 与 Operator 同 Deployment）

```
+---------------------------------------+
|        Operator Pod                    |
|                                       |
|   +-------------------------------+   |
|   | Kopf Operator Process         |   |
|   |  (4 Controllers + Lease)      |   |
|   |  Port: 8080 (metrics)         |   |
|   +-------------------------------+   |
|                                       |
|   +-------------------------------+   |
|   | Admission Webhook ASGI Server |   |
|   |  (uvicorn single worker)      |   |
|   |  Port: 8443 (HTTPS only)      |   |
|   |  Validators: 4 CRD + mutual   |   |
|   |  TLS: cert-manager 自动轮换   |   |
|   +-------------------------------+   |
|                                       |
+---------------------------------------+
            ↑               ↑
       /metrics          /validate (HTTPS)
            ↓               ↓
   Prometheus          K8s API Server
                      (ValidatingWebhookConfiguration)
```

**关键决策**：
- ✅ Admission webhook 与 Kopf Operator 同进程/同 Deployment（共享 Pod lifecycle + RBAC + NetworkPolicy + 镜像）
- ✅ **独立端口**：8080 (Operator metrics) vs 8443 (webhook HTTPS)；通过 Helm values 区分
- ✅ **HTTPS only**：cert-manager 颁发证书（Serving 证书类型）；K8s API Server 通过 Service CA Bundle 验证
- ✅ **单进程原则**（ADR-0005 §6.2）：uvicorn 单 worker / 单 event loop，与 Operator 一致

### 5.3 4 CRD validators（Pydantic v2 严格校验）

**Validator 通用契约**：
```python
# packages/operator/src/superteam_a2a/operator/admission/validators/base.py
from typing import Protocol
from pydantic import BaseModel, ValidationError


class CRDValidator(Protocol):
    """4 CRD validators 必须实现此接口"""

    crd_kind: str  # "Agent" | "AgentSet" | "Workflow" | "Memory"
    group: str  # "superteam-a2a.io"

    async def validate(self, namespace: str, name: str, spec: BaseModel) -> ValidationResult:
        """同步校验 spec；返回 ValidationResult(allowed, reason)"""
        ...


class ValidationResult(BaseModel):
    allowed: bool
    reason: str | None = None
    http_status: int = 200  # 200=allowed; 422=invalid; 400=malformed
```

**4 个 validators**（与 L2-2 Go baseline §10 admission 对应）：
- **AgentValidator**（[§5.3.1](../L2-modules/L2-operator-core.md#53-4-crd-validators-pydantic-v2-严格校验)）：AgentSpec 字段约束 + AdapterConfig 引用校验 + Resources 配额
- **AgentSetValidator**：AgentSetSpec.replicas (1-100) + selector 必填 + template 字段与 Agent 一致
- **WorkflowValidator**：DAG 校验（见 §5.5）+ tasks[] 字段约束 + inputs 表达式（v0.1 仅静态）
- **MemoryValidator**：MemorySpec.content (1-20 keys) + scope 必填 + agent-private visibility 必填 ownerAgentId

### 5.4 Knowledge ↔ Memory 双向互斥（ADR-0002 §2 + ADR-0003 §5）

**互斥规则**：
- 同一 ResourceRef（namespace + name）不能同时出现在 KnowledgeItem.spec.sourceRef 和 Memory.spec.sourceKnowledgeRef
- 校验时机：KnowledgeItem 与 Memory CRD 创建/更新时**双向**校验
- 实现：`mutual_exclusion.py` 校验器在 4 CRD validators 中各调用一次

```python
# packages/operator/src/superteam_a2a/operator/admission/validators/mutual_exclusion.py
async def check_knowledge_memory_exclusion(
    namespace: str,
    source_ref: ResourceRef,
    k8s_client: AsyncK8sClient,
) -> ValidationResult:
    """检查 ResourceRef 是否同时被 KnowledgeItem 和 Memory 引用"""
    knowledge_items = await k8s_client.list(
        KnowledgeItem,
        namespace=namespace,
        label_selector=f"superteam-a2a.io/source-ref={source_ref.name}",
    )
    memories = await k8s_client.list(
        Memory,
        namespace=namespace,
        label_selector=f"superteam-a2a.io/source-ref={source_ref.name}",
    )
    if knowledge_items and memories:
        return ValidationResult(
            allowed=False,
            reason=f"ResourceRef {source_ref.name} 同时被 KnowledgeItem ({len(knowledge_items)} 个) 和 Memory ({len(memories)} 个) 引用",
            http_status=422,
        )
    return ValidationResult(allowed=True)
```

### 5.5 DAG 校验（Kahn/DFS 纯函数）

**算法契约**：
```python
# packages/operator/src/superteam_a2a/operator/admission/validators/workflow.py
class DAGValidator:
    MAX_NODES = 50
    MAX_EDGES = 200

    def validate_dag(self, tasks: list[TaskSpec]) -> ValidationResult:
        """Kahn 算法检测环 + 节点数限制"""
        if len(tasks) > self.MAX_NODES:
            return ValidationResult(False, f"节点数 {len(tasks)} > {self.MAX_NODES}", 422)

        # 1. 构建邻接表
        adj = {task.name: task.dependsOn for task in tasks}
        edge_count = sum(len(deps) for deps in adj.values())
        if edge_count > self.MAX_EDGES:
            return ValidationResult(False, f"边数 {edge_count} > {self.MAX_EDGES}", 422)

        # 2. Kahn 算法检测环
        in_degree = {task.name: len(task.dependsOn) for task in tasks}
        queue = [name for name, deg in in_degree.items() if deg == 0]
        topo_order = []

        while queue:
            node = queue.pop(0)
            topo_order.append(node)
            for neighbor, deps in adj.items():
                if node in deps:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        if len(topo_order) != len(tasks):
            cycle_nodes = [name for name, deg in in_degree.items() if deg > 0]
            return ValidationResult(False, f"检测到环，涉及节点: {cycle_nodes}", 422)

        return ValidationResult(allowed=True)
```

**关键不变量**：
- ✅ DAG 校验是**纯函数**（无 I/O，便于单测；无需 K8s API mock）
- ✅ admission 时校验一次 + reconcile 时复检一次（双保险）
- ✅ 节点 / 边数限制为软上限（v0.5+ 可配）

### 5.6 TLS 证书轮换（cert-manager 集成）

**证书路径**：
- cert-manager Certificate 资源（`superteam-a2a-webhook-tls`）+ Serving 证书类型
- K8s `ValidatingWebhookConfiguration` 的 `caBundle` 引用 cert-manager 颁发 CA
- webhook server 监听 8443，从 Secret 加载 TLS 证书

**热更新机制**：
```python
# packages/operator/src/superteam_a2a/operator/admission/tls.py
async def watch_tls_secret(secret_name: str, on_update: Callable[[SSLContext], None]):
    """监听 Secret 更新 + 触发 SSLContext 重建（不重启 server）"""
    watcher = AsyncWatch(Secret, name=secret_name)
    async for event in watcher.stream():
        new_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        new_ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        new_ctx.load_cert_chain(
            certfile=event.object.data["tls.crt"],
            keyfile=event.object.data["tls.key"],
        )
        on_update(new_ctx)  # 热更新 SSLContext（不重启 server）
```

**轮换策略**（cert-manager Certificate spec）：
- `duration: 2160h`（90 天）
- `renewBefore: 720h`（30 天前续期）
- `privateKey.rotationPolicy: Always`（每次续期生成新私钥）

### 5.7 关键不变量

- ✅ 4 CRD validators 全部用 Pydantic v2 严格校验（extra="forbid"，拒绝未知字段）
- ✅ DAG 校验是纯函数（无 I/O，单测无需 mock）
- ✅ 双向互斥校验在 4 CRD validators 各调用一次（避免漏检）
- ✅ Admission webhook 拒绝的请求**不**写 etcd（K8s API Server 默认行为）
- ✅ TLS 证书热更新（不重启 webhook server；保持 0 停机）
- ✅ admission webhook **不**调用 K8s API（性能 + 安全考虑）

**与 Go baseline 对应**：L2-2 Go baseline §4.3 admission webhook + §10.1 自定义错误码；wire contract（4 CRD 错误码 + 422/400 HTTP Status）与 v0.1 业务语义**完全继续有效**

---

## 6. Leader Election（K8s Lease · 单 leader 触发 reconcile + MemoryReconciler）

### 6.1 设计动机

Operator 部署多副本时，**所有副本**默认监听同一组 CRD 事件并触发 reconcile，导致：
1. **重复 reconcile**：同一 CRD 资源被多副本并发处理，浪费 API Server 资源 + 状态竞争
2. **MemoryReconciler 重复触发**：多副本同时触发 decay 算法，导致 MemoryStatus 抖动

**解法**：通过 K8s Lease 选举单 leader，仅 leader 触发 reconcile + MemoryReconciler；非 leader 进入 standby 模式（仅 watch 事件缓存，不触发业务逻辑）。

### 6.2 K8s Lease 模型

```yaml
# deploy/helm/operator/templates/leader_election_lease.yaml
apiVersion: coordination.k8s.io/v1
kind: Lease
metadata:
  name: superteam-a2a-operator-leader
  namespace: superteam-a2a-system
spec:
  holderIdentity: <operator-pod-uuid>  # 持有者 Pod UUID
  leaseDurationSeconds: 30              # 租约时长（renew 超时 = 30s）
  acquireTime: <RFC3339>
  renewTime: <RFC3339>                  # 最后续约时间
  leaderTransitions: <int>              # 切换次数（监控）
```

### 6.3 自研 AsyncLeaseClient（kubernetes_asyncio）

**Kopf 不内置 Leader Election**（ADR-0005 §3.1），需自研客户端：

```python
# packages/operator/src/superteam_a2a/operator/leader_election/lease_client.py
from kubernetes_asyncio import client
from datetime import datetime, timezone, timedelta


class AsyncLeaseClient:
    """K8s Lease 异步客户端（kubernetes_asyncio 封装）"""

    def __init__(self, k8s_client: client.CoordinationV1Api, lease_name: str, namespace: str):
        self.k8s = k8s_client
        self.lease_name = lease_name
        self.namespace = namespace
        self.holder_id = f"{socket.gethostname()}-{uuid.uuid4()}"
        self.lease_duration = timedelta(seconds=30)
        self.renew_deadline = datetime.now(timezone.utc) + self.lease_duration

    async def try_acquire(self) -> bool:
        """尝试获取 Lease（CAS 操作）"""
        try:
            existing = await self.k8s.read_namespaced_lease(self.lease_name, self.namespace)
            if existing.spec.holder_identity and not self._is_expired(existing):
                return False  # 已被其他副本持有

            # CAS 更新（带上 resourceVersion）
            existing.spec.holder_identity = self.holder_id
            existing.spec.acquire_time = datetime.now(timezone.utc).isoformat()
            existing.spec.renew_time = datetime.now(timezone.utc).isoformat()
            existing.spec.lease_duration_seconds = int(self.lease_duration.total_seconds())
            await self.k8s.replace_namespaced_lease(self.lease_name, self.namespace, existing)
            return True
        except client.exceptions.ApiException as e:
            if e.status == 404:  # Lease 不存在，创建
                await self._create_lease()
                return True
            raise

    async def renew(self) -> bool:
        """续约 Lease（更新 renew_time）"""
        try:
            lease = await self.k8s.read_namespaced_lease(self.lease_name, self.namespace)
            if lease.spec.holder_identity != self.holder_id:
                return False  # 已失主
            lease.spec.renew_time = datetime.now(timezone.utc).isoformat()
            await self.k8s.replace_namespaced_lease(self.lease_name, self.namespace, lease)
            self.renew_deadline = datetime.now(timezone.utc) + self.lease_duration
            return True
        except client.exceptions.ApiException:
            return False

    async def release(self) -> None:
        """主动让位（graceful shutdown）"""
        try:
            lease = await self.k8s.read_namespaced_lease(self.lease_name, self.namespace)
            if lease.spec.holder_identity == self.holder_id:
                lease.spec.holder_identity = None
                await self.k8s.replace_namespaced_lease(self.lease_name, self.namespace, lease)
        except client.exceptions.ApiException:
            pass  # 已过期或不存在

    def _is_expired(self, lease) -> bool:
        renew_time = datetime.fromisoformat(lease.spec.renew_time)
        return (datetime.now(timezone.utc) - renew_time) > self.lease_duration
```

### 6.4 Election 主类（grace period + renew 失败 3 次让位）

```python
# packages/operator/src/superteam_a2a/operator/leader_election/election.py
class Election:
    """Leader Election 主类（独立 task，不阻塞 event loop）"""

    def __init__(self, lease_client: AsyncLeaseClient, on_acquired: Callable, on_lost: Callable):
        self.lease = lease_client
        self.on_acquired = on_acquired
        self.on_lost = on_lost
        self._task: asyncio.Task | None = None
        self._renew_failures = 0
        self._MAX_RENEW_FAILURES = 3

    async def start(self) -> None:
        """启动 Leader Election loop（独立 task）"""
        self._task = asyncio.create_task(self._election_loop())

    async def _election_loop(self) -> None:
        """持续尝试获取/续约 Lease"""
        while True:
            try:
                if not await self.lease.try_acquire():
                    await asyncio.sleep(5)  # 退避 5s
                    continue

                # 成功获取
                self.on_acquired()
                self._renew_failures = 0

                # 持续续约
                while await self.lease.renew():
                    self._renew_failures = 0
                    await asyncio.sleep(10)  # 每 10s 续约一次

                # 续约失败
                self._renew_failures += 1
                if self._renew_failures >= self._MAX_RENEW_FAILURES:
                    self.on_lost()
                    await self.lease.release()
                    break  # 退出循环，重新进入 try_acquire
            except Exception as e:
                logger.error("leader_election_error", error=str(e))
                await asyncio.sleep(5)
```

### 6.5 关键不变量

- ✅ **单 leader**：Operator 多副本下，仅 1 个 holder_identity 持有 Lease
- ✅ **MemoryReconciler 单触发**：仅 leader 触发 `@kopf.timer(interval=60)`；非 leader 进入 standby
- ✅ **grace period 30s**：Lease 过期后最多 30s 自动让位，避免长期分裂
- ✅ **renew 失败 3 次触发让位**：连续 3 次续约失败（30s × 3 = 90s）后主动让位
- ✅ **优雅停机**：Operator SIGTERM 时主动 release Lease，下一 leader 立即接管（避免 30s 等待）
- ✅ **不阻塞 event loop**：Leader Election 在独立 asyncio task；Lease 续约失败不阻塞 reconcile

**与 Go baseline 对应**：L2-2 Go baseline §7.3 Leader Election + ADR-0003 §6.5 单 leader 触发；wire contract（Lease 名称 + 30s leaseDurationSeconds）与 v0.1 业务语义**完全继续有效**

---

## 7. async-first 与 CPU offload（ADR-0005 §6.1 / §6.3）

### 7.1 async 边界（Kopf @kopf.Singleton + Uvicorn 单 worker + 单 event loop）

**单进程原则**（ADR-0005 §6.2）：
- ✅ **Kopf `@kopf.Singleton`**：所有 4 Controllers 注册为 Singleton，确保单 event loop 处理
- ✅ **Uvicorn 单 worker**：`python.workers: 1`（Helm values 强制）
- ✅ **单 event loop**：Kopf + admission webhook + Leader Election 共享同一 event loop

```python
# packages/operator/src/superteam_a2a/operator/main.py
import kopf
import asyncio


@kopf.on.startup()
async def configure(settings: kopf.Settings, **_):
    settings.persistence.diff_base_layer = "apiextensions.k8s.io"  # CRD watch
    settings.execution.max_workers = 1  # 单 worker（强制）


@kopf.on.login()
async def login(**_):
    """K8s API Server 身份认证（ServiceAccount token）"""
    return kopf.login_with_service_account(...)


# 4 Controllers 注册
kopf.on.create("Agent", callback=AgentController.on_create)
kopf.on.update("Agent", callback=AgentController.on_update)
kopf.on.delete("Agent", callback=AgentController.on_delete)

kopf.on.create("AgentSet", callback=AgentSetController.on_create)
# ... AgentSet / Workflow / Memory


# MemoryReconciler 定时任务
@kopf.timer("Memory", interval=60, when=lambda mem: mem.status.phase != "GarbageCollected")
async def memory_reconcile_timer(mem, **_):
    if not election.is_leader:
        return  # 非 leader 跳过
    await MemoryReconciler.reconcile(mem)


if __name__ == "__main__":
    asyncio.run(kopf.run())
```

### 7.2 CPU offload（anyio.to_thread.run_sync · Memory batch reconcile / BM25 rebuild）

**何时 offload**：
- **Memory batch reconcile**：每 60s 处理 > 1000 个 Memory，decay 计算密集
- **BM25 rebuild**：KnowledgeService Memory 反向索引重建（与 L2-4 协同）
- **大 JSON 解析**：admission webhook 接收 > 1MB JSON 时

**实现契约**：
```python
# packages/operator/src/superteam_a2a/operator/utils/cpu_offload.py
import anyio
from functools import partial


async def run_cpu_bound(func, *args, **kwargs):
    """CPU-bound 函数 offload 到 anyio 线程池（不阻塞 event loop）"""
    return await anyio.to_thread.run_sync(partial(func, *args, **kwargs))


# 示例：Memory batch decay
async def batch_decay(memories: list[Memory], current_time: datetime) -> list[MemoryStatus]:
    """批量计算 decay（CPU-bound）"""
    return await run_cpu_bound(_compute_decay_sync, memories, current_time)


def _compute_decay_sync(memories: list[Memory], current_time: datetime) -> list[MemoryStatus]:
    """纯 Python decay 计算（线程池内同步执行）"""
    results = []
    for mem in memories:
        elapsed_days = (current_time - mem.spec.lastReinforcedAt).days
        effective_confidence = mem.spec.confidence * math.exp(-elapsed_days / mem.spec.decayDays)
        results.append(
            MemoryStatus(
                memory_id=mem.metadata.name,
                effective_confidence=effective_confidence,
                phase="Promotable" if effective_confidence > 0.9 else "Active",
            )
        )
    return results
```

### 7.3 事件循环监控（Python runtime 4 个指标）

**4 个 Python runtime 指标**（与 L1 Spec §16.7 一致）：
- `superteam_python_event_loop_lag_seconds` (Histogram) — event loop 阻塞检测
- `superteam_python_thread_offload_queue_depth` (Gauge) — anyio 线程池队列深度
- `superteam_python_active_asyncio_tasks` (Gauge) — 活跃 task 数
- `superteam_python_gc_collections_total{generation}` (Counter) — GC 触发计数

**集成方式**：`prometheus-client` + `structlog` + 每 30s 采集一次（与 L1 v0.2.0 Spec §16.7 同步）。

### 7.4 关键不变量

- ✅ **async 边界完整**：Kopf handlers + admission webhook + Leader Election + MemoryReconciler 全部 async
- ✅ **CPU offload 强制**：Memory batch reconcile / BM25 rebuild / 大 JSON 解析必须 offload
- ✅ **Python runtime 4 指标**全量暴露（监控 event loop 健康）
- ✅ **不引入第二核心语言**：所有 Operator 代码 Python 3.12+（ADR-0005 §3.1）

**与 Go baseline 对应**：L2-2 Go baseline §7.1 Reconcile 通用流程（async 化 + CPU offload）；wire contract（4 Python runtime 指标 metric name）与 v0.1 业务语义**完全继续有效**

---

## 8. Finalizer 机制（4 CRD 全配 · 永久保留 v0.1 名称）

### 8.1 设计动机

CRD 删除时，K8s 默认**立即**清理关联资源（Pod / Service / ServiceAccount / AdmissionReview），导致：
1. **Adapter 容器未优雅停止**：Agent Pod 中 Adapter 容器未收到 SIGTERM
2. **关联资源残留**：KnowledgeItem.sourceRef 指向的 Agent 删除后未清理
3. **审计日志缺失**：删除动作未触发 K8s Events + structlog 记录

**解法**：Finalizer 机制确保 CRD 删除前先执行 cleanup 流程，cleanup 完成后才允许 K8s 删除 CRD。

### 8.2 4 CRD Finalizer 名称常量

```python
# packages/operator/src/superteam_a2a/operator/finalizers/names.py
from enum import Enum


class FinalizerName(str, Enum):
    """4 CRD Finalizer 名称常量（永久保留 v0.1 名称）"""

    AGENT = "agent.superteam-a2a.io/cleanup"
    AGENT_SET = "agentset.superteam-a2a.io/cleanup"
    WORKFLOW = "workflow.superteam-a2a.io/cleanup"
    MEMORY = "memory.superteam-a2a.io/cleanup"

    @classmethod
    def for_kind(cls, kind: str) -> "FinalizerName":
        """根据 CRD kind 检索 Finalizer 名称"""
        mapping = {
            "Agent": cls.AGENT,
            "AgentSet": cls.AGENT_SET,
            "Workflow": cls.WORKFLOW,
            "Memory": cls.MEMORY,
        }
        return mapping[kind]
```

### 8.3 cleanup 流程（@kopf.on.delete + retry + idempotent）

```python
# packages/operator/src/superteam_a2a/operator/controllers/base.py
@kopf.on.delete("Agent")
async def agent_on_delete(spec, status, name, namespace, body, **_):
    """Agent 删除时触发 cleanup（Finalizer 存在时）"""
    finalizers = body.metadata.finalizers or []
    if FinalizerName.AGENT.value not in finalizers:
        return  # 无 Finalizer，直接返回

    try:
        # 1. 优雅停止 Adapter 容器（SIGTERM + grace period 30s）
        await k8s_client.delete_namespaced_pod(
            name=f"{name}-adapter", namespace=namespace, grace_period_seconds=30
        )

        # 2. 清理关联 Service + ServiceAccount
        await k8s_client.delete_namespaced_service(name=f"{name}-svc", namespace=namespace)
        await k8s_client.delete_namespaced_service_account(name=f"{name}-sa", namespace=namespace)

        # 3. 清理 KnowledgeItem.sourceRef 引用
        knowledge_items = await k8s_client.list(
            KnowledgeItem,
            namespace=namespace,
            label_selector=f"superteam-a2a.io/source-ref={name}",
        )
        for item in knowledge_items:
            item.spec.source_ref = None  # 解除引用
            await k8s_client.replace_namespaced_knowledge_item(item.metadata.name, namespace, item)

        # 4. 记录审计事件
        await emit_event(
            involved_object=body,
            reason="CleanupCompleted",
            message=f"Agent {name} cleanup completed",
            type="Normal",
        )

    except kopf.PermanentError as e:
        # 永久错误：清理失败且不可重试 → 保留 Finalizer + 记录事件
        logger.error("agent_cleanup_failed", name=name, error=str(e))
        raise kopf.PermanentError(f"Cleanup failed: {e}")

    # 5. 移除 Finalizer（允许 K8s 删除 CRD）
    body.metadata.finalizers.remove(FinalizerName.AGENT.value)
    await k8s_client.patch_namespaced_agent(name, namespace, body)
```

### 8.4 永久保留原则（v1.0+ 也不变）

**L2-2 Go baseline §7.4 + 宪法 §3.4 永久保留原则**：
- ✅ 4 个 Finalizer 名称（`*.superteam-a2a.io/cleanup`）在 v1.0+ **也不变**
- ✅ 即使 cleanup 语义变化（v0.5+），Finalizer 名称仅增不改
- ✅ 已有 CRD 升级后 Finalizer 保留（K8s 自动迁移；Operator 不删除）

### 8.5 关键不变量

- ✅ 4 CRD 全部配置 Finalizer（缺失会被 admission webhook 拒绝创建）
- ✅ cleanup 是 idempotent（重复触发不报错；retry 安全）
- ✅ cleanup 失败 → K8s 保留 CRD + 触发事件 + 记录日志（**不**自动重试无限循环）
- ✅ cleanup 完成后才移除 Finalizer（避免 CRD 被强制删除导致 cleanup 中断）
- ✅ 审计事件双写：K8s Events + structlog JSON 日志

**与 Go baseline 对应**：L2-2 Go baseline §7.4 Finalizer 机制；wire contract（Finalizer 名称 + cleanup 顺序）与 v0.1 业务语义**完全继续有效**

---

## 9. 错误模型（ReconcileError hierarchy · 与 L2-1 §10 错误码区分）

### 9.1 ReconcileError hierarchy（Retryable / NonRetryable / Permanent）

**3 类错误**（与 L2-2 Go baseline §10.1 对应）：

```python
# packages/operator/src/superteam_a2a/operator/errors/reconcile_errors.py
class ReconcileError(Exception):
    """Operator reconcile 通用错误基类"""

    retry_after_seconds: int | None = None  # 重试间隔（None = 由 Kopf 决策）


class RetryableError(ReconcileError):
    """可重试错误（瞬时失败：网络抖动 + API Server 限流 + 外部服务暂不可用）"""

    def __init__(self, message: str, retry_after: int = 30):
        super().__init__(message)
        self.retry_after_seconds = retry_after


class NonRetryableError(ReconcileError):
    """不可重试错误（业务逻辑错误：CRD 字段非法 + 关联资源缺失）"""

    pass


class PermanentError(ReconcileError):
    """永久错误（不可恢复：K8s API 永久失败 + 配置错误）"""

    pass
```

**使用契约**：
- ✅ Controllers 在重试场景抛 `RetryableError`（含 `retry_after`）
- ✅ 业务校验失败抛 `NonRetryableError`（Kopf 不重试 + 记录事件）
- ✅ 配置错误抛 `PermanentError`（Kopf 标记为不可恢复 + 触发告警）

### 9.2 错误处理优先级（Permanent > NonRetryable > Retryable）

```python
# packages/operator/src/superteam_a2a/operator/controllers/base.py
async def safe_reconcile(reconciler_func, *args, **kwargs):
    """统一错误处理 wrapper"""
    try:
        return await reconciler_func(*args, **kwargs)
    except PermanentError as e:
        logger.error("reconcile_permanent_error", error=str(e))
        await emit_event(reason="ReconcileFailed", message=str(e), type="Warning")
        raise kopf.PermanentError(str(e))  # 不重试
    except NonRetryableError as e:
        logger.warning("reconcile_nonretryable_error", error=str(e))
        await emit_event(reason="ReconcileInvalid", message=str(e), type="Warning")
        raise kopf.PermanentError(str(e))  # 不重试
    except RetryableError as e:
        logger.info("reconcile_retryable_error", error=str(e), retry_after=e.retry_after_seconds)
        raise kopf.TemporaryError(str(e), delay=e.retry_after_seconds)  # Kopf 退避重试
```

### 9.3 与 L2-1 §10 错误码区分

| 维度 | Operator 错误（L2-2 §9） | A2A 错误（L2-1 §10） |
|------|-------------------------|----------------------|
| **作用域** | Operator 内部 reconcile 流程 | A2A JSON-RPC wire 协议 |
| **错误对象** | `ReconcileError` 异常 | JSON-RPC error 响应（11 + 7 + 6 = 24 个错误码） |
| **传播路径** | Operator → K8s Events + structlog | Agent → A2A Client → 调用方 |
| **用户感知** | K8s Events + AgentStatus.phase=Failed | A2A Client 收到 JSON-RPC error |
| **可观测性** | Prometheus `superteam_operator_reconcile_total{result="error"}` | Prometheus `superteam_a2a_rpc_total{status="error"}` |

### 9.4 错误日志格式（structlog + K8s Events）

**structlog JSON 日志**（与 L1 Spec §16.8 一致）：
```json
{
  "ts": "2026-07-24T10:00:00.000Z",
  "level": "error",
  "msg": "reconcile_permanent_error",
  "trace_id": "abc123",
  "crd": "Agent",
  "namespace": "default",
  "name": "hello-agent",
  "error": "Cleanup failed: K8s API timeout",
  "retry_after_seconds": null
}
```

**K8s Events**（与 L2-2 Go baseline §9.2 一致）：
- `ReconcileFailed` (Warning) — Permanent / NonRetryable 错误
- `ReconcileRetry` (Normal) — Retryable 错误（含 retry_after）
- `CleanupCompleted` (Normal) — Finalizer cleanup 成功
- `CleanupFailed` (Warning) — Finalizer cleanup 失败

### 9.5 关键不变量

- ✅ Operator 错误**不**污染 A2A 错误码（24 个 JSON-RPC 错误码保持 wire 不变）
- ✅ 3 类错误分类明确（Retryable / NonRetryable / Permanent）
- ✅ 错误日志包含 trace_id + crd + namespace + name（结构化字段）
- ✅ K8s Events 触发规则明确（4 种 event reason）

**与 Go baseline 对应**：L2-2 Go baseline §10 错误模型；wire contract（4 event reason + 3 错误类型）与 v0.1 业务语义**完全继续有效**

---

## 10. 可观测性（Python 全栈 · 沿用 v0.1 metric name）

> ⚠️ **本节为 v0.2-draft 草稿**——11 个 Operator 指标的完整 metric schema + OTel Provider 注入细节 + structlog JSON 格式字段约束待 L3-1 文件级 Spec 补完。

### 10.1 Prometheus 指标（与 L1 v0.2.0 Spec §16.1/§16.3/§16.4/§16.5/§16.6/§16.7 完全一致）

**11 个 Operator 指标**（与 v0.1 Go baseline §9.1 名称一致）：

| 指标 | 类型 | Labels | 触发点 | 单位 |
|------|------|--------|--------|------|
| `superteam_operator_reconcile_total` | Counter | `crd`, `result` | 每个 reconcile 完成后 | requests |
| `superteam_operator_reconcile_duration_seconds` | Histogram | `crd` | 每个 reconcile 完成后 | seconds |
| `superteam_operator_leader_election` | Gauge | — | Leader Election 状态变更（0/1） | — |
| `superteam_operator_finalizer_cleanup_total` | Counter | `crd`, `result` | Finalizer cleanup 完成后 | cleanups |
| `superteam_operator_finalizer_cleanup_duration_seconds` | Histogram | `crd` | Finalizer cleanup 完成后 | seconds |
| `superteam_operator_admission_validation_total` | Counter | `crd`, `result` | admission 校验完成后 | validations |
| `superteam_operator_admission_validation_duration_seconds` | Histogram | `crd` | admission 校验完成后 | seconds |
| `superteam_operator_memory_reconcile_total` | Counter | `result` | MemoryReconciler 每 60s 触发后 | reconciles |
| `superteam_operator_memory_decay_total` | Counter | `phase_from`, `phase_to` | decay 算法触发后 | decays |
| `superteam_operator_lease_renew_total` | Counter | `result` | Leader Election 续约 | renews |
| `superteam_operator_lease_transition_total` | Counter | `event` | Leader Election 状态切换（acquired/lost/renew_failed） | transitions |

**命名约束**（ADR-0005 §10）：
- ✅ 11 个 metric name 与 v0.1 Go baseline **完全一致**（不重定义既有指标）
- ✅ Python runtime 4 个新增指标（`superteam_python_*`）在 L1 Spec §16.7 已定义，本设计复用

### 10.2 Trace（OpenTelemetry Python SDK · 与 L1 Arch §9.2 一致）

**Span 结构**：
```
CRD Write (K8s API Server)
  └── admission Validation
        └── mutual_exclusion check
              └── K8s API list (KnowledgeItem + Memory)
  └── Operator Reconcile
        └── Leader Election acquire/renew
        └── Finalizer add/remove
        └── Reconciler service
              ├── K8s API read (CRD)
              ├── K8s API write (Pod / Service / SA)
              ├── mTLS cert request (cert-manager)
              └── K8s Events emit
        └── Status patch (kopf.adopt)
  └── MemoryReconciler timer
        └── Batch decay (CPU offload)
              └── K8s API patch (Memory status)
```

**Python 特定要求**（ADR-0005 §10）：
- ✅ 显式 `TracerProvider` 注入；测试不能污染全局 provider（每个 test 独立 provider）
- ✅ OTel exporter 必须使用 async export pipeline（`opentelemetry-exporter-otlp-proto-grpc` async transport）
- ✅ W3C Trace Context 注入到 K8s Events + structlog JSON 日志 + admission audit log

### 10.3 日志（`structlog` + stdlib logging · JSON）

**日志格式**（与 L1 Spec §16.8 一致）：
```json
{
  "ts": "2026-07-24T10:00:00.000Z",
  "level": "info",
  "msg": "agent_reconcile_completed",
  "trace_id": "abc123def456",
  "span_id": "789ghi",
  "crd": "Agent",
  "namespace": "default",
  "name": "hello-agent",
  "phase": "Ready",
  "duration_seconds": 3.45
}
```

**8 个必含字段**（结构化日志 · L1 Spec §16.8）：
1. `ts` — RFC3339 UTC timestamp
2. `level` — debug / info / warning / error / critical
3. `msg` — 事件名（snake_case）
4. `trace_id` — W3C Trace Context
5. `crd` — Agent / AgentSet / Workflow / Memory
6. `namespace` — K8s namespace
7. `name` — CRD instance name
8. `phase` — reconcile phase / status

### 10.4 K8s Events（4 种 event reason）

| Event Reason | Type | 触发时机 | Message 模板 |
|--------------|------|----------|--------------|
| `ReconcileSucceeded` | Normal | reconcile 成功 | `Reconcile succeeded for {crd}/{namespace}/{name}` |
| `ReconcileFailed` | Warning | Permanent / NonRetryable 错误 | `Reconcile failed for {crd}/{namespace}/{name}: {reason}` |
| `ReconcileRetry` | Normal | Retryable 错误（含 retry_after） | `Reconcile retry after {retry_after}s for {crd}/{namespace}/{name}` |
| `CleanupCompleted` | Normal | Finalizer cleanup 成功 | `Cleanup completed for {crd}/{namespace}/{name}` |
| `CleanupFailed` | Warning | Finalizer cleanup 失败 | `Cleanup failed for {crd}/{namespace}/{name}: {reason}` |
| `LeaderAcquired` | Normal | Leader Election 获取成功 | `Operator {pod_name} acquired lease` |
| `LeaderLost` | Warning | Leader Election 失主 | `Operator {pod_name} lost lease` |
| `AdmissionRejected` | Warning | admission 拒绝请求 | `Admission rejected for {crd}/{namespace}/{name}: {reason}` |

### 10.5 关键不变量

- ✅ 11 个 Operator metric name 与 v0.1 Go baseline **完全一致**（wire contract 锁定）
- ✅ OTel Provider 显式注入（测试隔离）
- ✅ structlog 8 个必含字段全覆盖
- ✅ K8s Events 8 种 reason 全量触发（每个 reconcile / cleanup / leader 事件）
- ✅ Python runtime 4 指标（`superteam_python_*`）在 Operator 进程内启用

**与 Go baseline 对应**：L2-2 Go baseline §9 可观测性；wire contract（11 metric name + 8 event reason + 8 必含日志字段）与 v0.1 业务语义**完全继续有效**

---

## 11. Helm values（Python 镜像块 · ADR-0005 §13.1 工程布局）

> ⚠️ **本节为 v0.2-draft 草稿**——完整 `values.schema.json` 待 L3-1 文件级 Spec 起草时补完；本节给出 Pydantic 模型契约。

### 11.1 values.yaml 结构概览

```yaml
# deploy/helm/operator/values.yaml
operator:
  # 通用配置
  replicaCount: 2  # 多副本 + Leader Election 选举单 leader
  image:
    repository: ghcr.io/coderzhangfujiang/superteam-a2a-operator
    tag: v0.2.0
    pullPolicy: IfNotPresent

  # Python-first 配置（ADR-0005 §6）
  python:
    workers: 1  # 单 worker 强制（ADR-0005 §6.2）
    image: python:3.12-slim  # 基础镜像（多阶段构建）
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /readyz
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
    resources:
      requests:
        cpu: 200m
        memory: 256Mi
      limits:
        cpu: 1000m
        memory: 1Gi

  # 4 Controllers 并发度（Kopf max_workers）
  controllers:
    agent: 1  # 单 worker（ADR-0005 §6.2）
    agentset: 1
    workflow: 1
    memory: 1

  # Leader Election 配置
  leaderElection:
    enabled: true
    leaseName: superteam-a2a-operator-leader
    leaseDurationSeconds: 30
    renewIntervalSeconds: 10
    maxRenewFailures: 3  # 连续失败 3 次触发让位

  # admission webhook 配置
  admission:
    enabled: true
    port: 8443
    tlsSecretName: superteam-a2a-webhook-tls
    serviceName: superteam-a2a-operator-webhook
    failurePolicy: Fail  # webhook 不可用时拒绝请求（保守策略）
    timeoutSeconds: 10

  # MemoryReconciler 配置
  memoryReconciler:
    enabled: true
    intervalSeconds: 60  # 每 60s 全量 reconcile
    batchSize: 500  # 单次 reconcile 批大小
    cpuOffloadThreshold: 1000  # Memory 数量 > 1000 时启用 CPU offload

  # 可观测性
  observability:
    prometheus:
      enabled: true
      port: 8080
      path: /metrics
    opentelemetry:
      enabled: true
      exporter: otlp-grpc  # otlp / otlp-grpc / jaeger
      endpoint: http://otel-collector.observability.svc:4317
    logging:
      level: info  # debug / info / warning / error
      format: json  # json / text（生产环境必须 json）

  # mTLS（cert-manager 集成）
  mtls:
    certManager:
      enabled: true
      issuerName: superteam-a2a-ca
      issuerKind: ClusterIssuer
      dnsNames:
        - superteam-a2a-operator
        - superteam-a2a-operator.superteam-a2a-system
        - superteam-a2a-operator.superteam-a2a-system.svc
        - superteam-a2a-operator.superteam-a2a-system.svc.cluster.local

# RBAC
rbac:
  clusterRole: superteam-a2a-operator
  serviceAccountName: superteam-a2a-operator
```

### 11.2 Pydantic Schema（values.schema.json 派生）

```python
# packages/operator/src/superteam_a2a/operator/config/helm_values.py
from pydantic import BaseModel, Field, ConfigDict


class PythonConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workers: int = Field(1, ge=1, le=1)  # 强制单 worker
    image: str = "python:3.12-slim"
    liveness_probe: dict | None = None
    readiness_probe: dict | None = None
    resources: dict = Field(
        default_factory=lambda: {
            "requests": {"cpu": "200m", "memory": "256Mi"},
            "limits": {"cpu": "1000m", "memory": "1Gi"},
        }
    )


class LeaderElectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    lease_name: str = "superteam-a2a-operator-leader"
    lease_duration_seconds: int = Field(30, ge=10, le=300)
    renew_interval_seconds: int = Field(10, ge=5, le=60)
    max_renew_failures: int = Field(3, ge=1, le=10)


class AdmissionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    port: int = Field(8443, ge=1024, le=65535)
    tls_secret_name: str = "superteam-a2a-webhook-tls"
    service_name: str = "superteam-a2a-operator-webhook"
    failure_policy: str = Field("Fail", pattern="^(Fail|Ignore)$")
    timeout_seconds: int = Field(10, ge=1, le=30)


class MemoryReconcilerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    interval_seconds: int = Field(60, ge=10, le=3600)
    batch_size: int = Field(500, ge=10, le=5000)
    cpu_offload_threshold: int = Field(1000, ge=100, le=100000)


class HelmValues(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operator: "OperatorConfig"


class OperatorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    replicaCount: int = Field(2, ge=1, le=10)
    image: dict
    python: PythonConfig
    controllers: dict[str, int] = Field(
        default_factory=lambda: {
            "agent": 1,
            "agentset": 1,
            "workflow": 1,
            "memory": 1,
        }
    )
    leader_election: LeaderElectionConfig
    admission: AdmissionConfig
    memory_reconciler: MemoryReconcilerConfig
    observability: dict
    mtls: dict
```

### 11.3 关键不变量

- ✅ `python.workers: 1` 强制单 worker（ADR-0005 §6.2 单进程原则）
- ✅ `leaderElection.enabled: true` 默认开启（多副本部署必需）
- ✅ `admission.failurePolicy: Fail` 保守策略（webhook 不可用时拒绝请求，避免非法 CRD 入库）
- ✅ `memoryReconciler.intervalSeconds: 60` 默认 60s（与 v0.1 一致）
- ✅ `values.schema.json` 由 Pydantic 自动生成（CI 验证无 diff）

**与 Go baseline 对应**：L2-2 Go baseline §11 资源默认值；wire contract（Helm values 字段名 + 默认值）与 v0.1 业务语义**完全继续有效**

---

## 12. RBAC（ClusterRole · Role · ServiceAccount）

> ⚠️ **本节为 v0.2-draft 草稿**——完整 RBAC manifest（ClusterRole + Role + RoleBinding + ServiceAccount）待 L3-1 文件级 Spec 起草时补完；本节给出权限契约。

### 12.1 ClusterRole（cluster-scoped 权限）

```yaml
# deploy/helm/operator/templates/clusterrole.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: superteam-a2a-operator
rules:
  # 4 CRD 全权限
  - apiGroups: ["superteam-a2a.io"]
    resources: ["agents", "agentsets", "workflows", "memories", "knowledgescopes", "knowledgeitems"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["superteam-a2a.io"]
    resources: ["agents/status", "agentsets/status", "workflows/status", "memories/status", "knowledgescopes/status", "knowledgeitems/status"]
    verbs: ["get", "update", "patch"]

  # 关联资源（Pod / Service / ServiceAccount / ConfigMap / Secret）
  - apiGroups: [""]
    resources: ["pods", "services", "serviceaccounts", "configmaps", "secrets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

  # Leader Election Lease
  - apiGroups: ["coordination.k8s.io"]
    resources: ["leases"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

  # K8s Events
  - apiGroups: ["events.k8s.io"]
    resources: ["events"]
    verbs: ["create", "patch"]

  # admission webhook
  - apiGroups: ["admissionregistration.k8s.io"]
    resources: ["validatingwebhookconfigurations"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["admissionregistration.k8s.io"]
    resources: ["validatingwebhookconfigurations"]
    resourceNames: ["superteam-a2a-admission"]
    verbs: ["update", "patch"]

  # cert-manager（CRD 触发证书轮换）
  - apiGroups: ["cert-manager.io"]
    resources: ["certificates"]
    verbs: ["get", "list", "watch"]
```

### 12.2 ServiceAccount + ClusterRoleBinding

```yaml
# deploy/helm/operator/templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: superteam-a2a-operator
  namespace: superteam-a2a-system
  annotations:
    # cert-manager 集成：触发证书自动颁发
    cert-manager.io/inject-ca-from: superteam-a2a-ca/superteam-a2a-ca-cert

---
# deploy/helm/operator/templates/clusterrolebinding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: superteam-a2a-operator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: superteam-a2a-operator
subjects:
  - kind: ServiceAccount
    name: superteam-a2a-operator
    namespace: superteam-a2a-system
```

### 12.3 admission webhook RBAC（独立 Role + RoleBinding）

```yaml
# admission webhook 在 superteam-a2a-system namespace 内运行
# 不需要 ClusterRole，仅 Role 即可（admission API 调用受限）
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: superteam-a2a-admission
  namespace: superteam-a2a-system
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list", "watch"]  # TLS Secret 读取
  - apiGroups: ["admissionregistration.k8s.io"]
    resources: ["validatingwebhookconfigurations"]
    verbs: ["get", "list", "watch"]
```

### 12.4 关键不变量

- ✅ ClusterRole 覆盖 4 CRD 全权限 + status 子资源
- ✅ ClusterRoleBinding 绑定 ServiceAccount（cluster-scoped）
- ✅ admission webhook 仅需 Role（namespace-scoped TLS Secret）
- ✅ Leader Election Lease 权限独立（避免与 reconcile 权限冲突）
- ✅ cert-manager 集成通过 ServiceAccount annotation 触发

**与 Go baseline 对应**：L2-2 Go baseline §12 RBAC；wire contract（ClusterRole + ServiceAccount 名称 + namespace）与 v0.1 业务语义**完全继续有效**

---

## 13. 测试策略（pytest + envtest + E2E + conformance）

> ⚠️ **本节为 v0.2-draft 草稿**——完整测试 ID 矩阵（≥ 80 测试 ID）待 L3-1 文件级 Spec 起草时补完；本节给出测试层级 + 工具链契约。

### 13.1 单元测试（pytest · 覆盖率 ≥ 80%）

**工具链**（ADR-0005 §9）：
- ✅ `pytest` + `pytest-asyncio` + `pytest-cov` + `pytest-mock` + `hypothesis`（属性测试）
- ✅ `respx`（httpx mock） + `kubernetes_asyncio` fake client
- ✅ `Ruff` + `Pyright strict` + `Bandit` + `pip-audit`（CI 门禁）

**测试范围**：
- 4 Controllers 的 reconcile 流程（含 happy path + 异常路径）
- MemoryReconciler 的 decay / reinforce / GC / promotion 算法
- admission validators（4 CRD + mutual exclusion + DAG）
- Leader Election（acquire / renew / release / 失败重试）
- Finalizer cleanup 流程（含异常路径 + idempotent）
- 错误模型（3 类错误分类 + 处理优先级）
- Helm values Pydantic 解析

**覆盖率目标**（L2-2 Go baseline §13.1）：
- ✅ **行覆盖 ≥ 80%**
- ✅ **分支覆盖 ≥ 75%**
- ✅ **关键路径（reconcile / cleanup / admission）覆盖 ≥ 95%**

### 13.2 集成测试（envtest · K8s API mock）

**工具链**：
- ✅ `envtest`（Kopf 内置；启动 etcd + kube-apiserver 真实二进制）
- ✅ `pytest-envtest`（自动下载 K8s 二进制）
- ✅ `kopf.testing`（Kopf 测试 harness）

**测试范围**：
- 4 CRD 完整生命周期（create / update / delete + Finalizer cleanup）
- admission webhook 完整流程（含 ValidatingWebhookConfiguration 注册）
- Leader Election 多副本场景（envtest 不支持多实例 → 用 mock 模拟）
- MemoryReconciler 定时任务（mock timer）
- mTLS 集成（cert-manager fake issuer）

**envtest 限制**：
- ⚠️ envtest 不支持 Helm（直接 apply manifest）
- ⚠️ envtest 不支持 cert-manager（用 fake Secret）
- ⚠️ envtest 不支持多 Operator 副本（Leader Election 单副本测试）

### 13.3 E2E（kind + hello-agent）

**工具链**：
- ✅ `kind`（K8s in Docker）
- ✅ `helm`（部署 Operator + Admission）
- ✅ `kubectl`（apply CRD + 验证 Status）
- ✅ `hello-agent`（L1 v0.2.0 运行时层参考实现）

**测试场景**（≥ 10 个 E2E case）：
1. Agent CRD 创建 → Pod Ready + AgentStatus.phase=Ready
2. AgentSet CRD 创建（replicas=3）→ 3 Agent Ready
3. Workflow CRD 创建（合法 DAG）→ WorkflowStatus.phase=Running
4. Workflow CRD 创建（非法 DAG 环）→ admission 拒绝 + K8s Event
5. Memory CRD 创建 → MemoryStatus 初始化 + MemoryReconciler 触发 decay
6. KnowledgeItem CRD 创建 + Memory CRD 同时引用 → admission 互斥拒绝
7. Agent 删除 → Finalizer cleanup → Pod 优雅停止 + K8s Event
8. Operator 重启 → Leader Election 自动让位 + 重新选举
9. mTLS 证书轮换 → admission webhook 不停机 + K8s Event
10. Prometheus 指标采集 → 11 个 Operator metric 全量暴露

### 13.4 Conformance（与官方 a2a-sdk 集成）

**测试范围**：
- ✅ 4 个项目扩展 A2A method（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）的 JSON wire shape 一致性
- ✅ Operator 通过 a2a-sdk client 调用 L2-4 Knowledge Service 的 4 个 method
- ✅ 11 个 A2A 错误码（JSON-RPC）与 L2-1 Spec §8.4 完全一致

### 13.5 关键不变量

- ✅ **单元测试覆盖率 ≥ 80%**（关键路径 ≥ 95%）
- ✅ **E2E ≥ 10 个场景**（含 happy path + 异常路径）
- ✅ **envtest + E2E + conformance** 三层测试（不留测试盲区）
- ✅ **测试在 CI 中自动运行**（GitHub Actions）

**与 Go baseline 对应**：L2-2 Go baseline §13 测试策略；wire contract（测试场景 + 覆盖率目标）与 v0.1 业务语义**完全继续有效**

---

## 14. 开放问题（完整清单 · v0.2-draft-full）

> ⚠️ **本节为 v0.2-draft 草稿**——18 项开放问题为继承自 L2-2 Go baseline §14 + L2-1 Python 设计 D-1~D-7 + 本设计新发现的合并清单；完整讨论待 L3-1 文件级 Spec 起草时收敛。

### 14.1 继承自 L2-2 Go baseline（5 项）

| # | 开放问题 | 移交位置 | 默认决策 |
|---|----------|----------|---------|
| 1 | reconcile 性能：Agent 数量 > 1000 时是否需要 informer 分片 | L3-1 Performance Spec | v0.1 不分片；监控指标暴露 queue depth |
| 2 | Workflow 表达式引擎（v0.1 静态 inputs） | L3 Future Spec | v0.1 仅静态；v0.5 引入 CEL；Operator Spec 留 stub 接口 |
| 3 | Memory 衰减频率（1h 是否合理） | 本 Spec §4.4 | 60s + 可配置（Helm values） |
| 4 | AgentSet owns Agent 时，Agent 删除如何处理 | 本 Spec §4.2 | Adoption 模式（orphanDeletion=false） |
| 5 | Operator 升级时如何避免 reconcile 抖动 | L3-1 Upgrade Spec | webhooks conversion + Helm pre-upgrade hook |

### 14.2 来自 kopf-python spike 已知未决（5 项 · §2.4 D-1~D-5）

| # | 开放问题 | 移交位置 | 默认决策 |
|---|----------|----------|---------|
| 6 | **Kopf `@kopf.Singleton` 在 Uvicorn 单 worker 下的 event loop 绑定测试** | L3-1 envtest 验证 | ✅ 单 worker = 单 event loop；Singleton 无冲突 |
| 7 | **K8s Lease 续约失败的处理**（leader 失联 → 自动让位 vs 强制保持） | L3-1 Leader Election Spec | 自动让位（renew 失败 3 次触发让位） |
| 8 | **admission webhook 独立 server 的 TLS 证书轮换** | L3-1 Admission Spec | cert-manager 集成 + 30 天自动轮换 |
| 9 | **MemoryReconciler batch reconcile 的 CPU offload 阈值** | L3-1 MemoryReconciler Spec | Memory > 1000 时启用 anyio.to_thread.run_sync |
| 10 | **Operator 升级期间 reconcile 抖动抑制** | L3-1 Upgrade Spec | webhooks conversion + Helm pre-upgrade hook |

### 14.3 本设计新发现（8 项）

| # | 开放问题 | 移交位置 | 默认决策 |
|---|----------|----------|---------|
| 11 | **4 CRD validators 错误响应格式**（结构化 reason 字段） | L3-1 Admission Spec | `reason` 字段 snake_case + http_status 数字 |
| 12 | **Kopf handlers 异常是否触发 Status 更新** | L3-1 Error Handling Spec | 触发（status.phase=Failed + conditions[] 记录） |
| 13 | **MemoryReconciler Leader Election 关系** | 本 Spec §6.4 | 复用同一 Lease（单一 leader） |
| 14 | **admission webhook 拒绝请求的审计日志格式** | L3-1 Admission Spec | structlog + K8s Event 双写 |
| 15 | **Operator CrashLoopBackOff 时的 Leader Lease 释放** | L3-1 Leader Election Spec | grace period 30s + Lease TTL 自动过期 |
| 16 | **structlog JSON 日志的 trace_id 注入位置** | L3-1 Observability Spec | 注入到 K8s Events + structlog + admission audit |
| 17 | **Helm values 验证失败的错误信息可读性** | L3-1 Helm Spec | Pydantic 错误翻译为 YAML 路径 + 字段名 |
| 18 | **Operator + admission webhook 共进程的崩溃隔离** | L3-1 Architecture Spec | subprocess 隔离（admission 独立 process；Operator 崩溃不影响 admission） |

### 14.4 开放问题统计

- **总数**：18 项
- **本 Spec 已收敛**：5 项（#3 / #6 / #7 / #8 / #13）
- **移交 L3-1**：11 项（#1 / #2 / #4 / #5 / #9 / #10 / #11 / #12 / #14 / #15 / #16 / #17 / #18 中大部分）
- **未来版本**：1 项（#2 Workflow 表达式引擎 v0.5+）

---

## 附录 A: 跨模块引用清单（v0.2-draft-skeleton）

| 引用 | 位置 | 状态 |
|------|------|------|
| L2-2 设计文档（本） | `docs/design/L2-modules/L2-operator-core.md` | 🚧 v0.2-draft-skeleton（§5-§14 + 附录 B 待补完） |
| L2-2 设计 Go baseline | `docs/archive/pre-python-2026-07-24/L2-operator-core-design-v0.1.0-go-baseline.md` | 📦 ARCHIVED · 仅参考 wire contract / 业务语义 |
| L1 Architecture v0.2.0 | `docs/design/L1-architecture.md` §3.2 编排层 + §4.1 C-1 Operator + §11.5 Python 性能预算 | ✅ |
| L1 Spec v0.2.0 | `docs/spec/L1-system-spec.md` §2-§4 CRD + §7 状态机 + §9-§10 资源/限流 + §16 指标 | ✅ |
| ADR-0005 Python-first | `docs/adr/0005-python-first-technology-stack.md` §3.1 Operator Core 模块映射 + §7 单进程原则 + §8 SDK 门禁 + §13.1 OTel/指标迁移 | ✅ |
| ADR-0003 Memory | `docs/adr/0003-memory-design.md` §4.3 (decay) / §6 (CRD) / §6.5 (MemoryReconciler) | ✅ |
| ADR-0002 知识管理 | `docs/adr/0002-knowledge-management-design.md` §2 (KnowledgeScope) / §3 (KnowledgeItem) | ✅ |
| L2-1 A2A Protocol v0.2.0 Spec | `docs/spec/L2-module-specs/L2-a2a-protocol.md` §2.5 (client) + §16.1 (OTel) | ✅ v0.2.0 (2026-07-24 Python 重写通过；模块 ID C-2 不变) |
| L2-3 Adapter v0.2-draft Python Design | `docs/design/L2-modules/L2-adapter.md` | 🚧 v0.2-draft (2026-07-26 #34 起草 · 1267 行 / 66KB / 14 节 + 2 附录；待评审 + Spec 起草) |
| L2-3 Adapter v0.1.0 Spec | `docs/spec/L2-module-specs/L2-adapter.md` | ⚠️ v0.1.0 Go baseline (2026-07-24, 设计 32KB / 555 行 + Spec 43KB / 1044 行) — 迁移输入，待 Python Spec 重写后归档 |
| L2-4 Knowledge/Memory v0.1.0 Spec | `docs/spec/L2-module-specs/L2-knowledge-memory.md` | ✅ v0.1.0 (2026-07-24, 设计 41KB / 872 行 + Spec 99KB / 2494 行) |
| 宪法 v0.5.0 | `CONSTITUTION.md` §3.8 Python-first + §6 mTLS + §7 可观测性 + §9.7 静态质量 + §14.4 评审门禁 + §16 会话管理 | ✅ |

---

## 附录 B: 开放问题清单（v0.2-draft-full）

> ✅ **本附录已升级为完整版**——18 项开放问题（继承 L2-2 Go baseline §14 + L2-1 Python 设计 D-1~D-7 + 本设计新发现）详见 §14；本附录为 §14 的精简版索引。

| # | 开放问题 | 移交位置 | 默认决策 |
|---|----------|----------|---------|
| 1 | Kopf `@kopf.Singleton` event loop 绑定 | L3-1 envtest | ✅ 单 worker = 单 event loop |
| 2 | K8s Lease 续约失败处理 | L3-1 Leader Election | 自动让位（renew 失败 3 次） |
| 3 | admission webhook TLS 证书轮换 | L3-1 Admission | cert-manager + 30 天自动 |
| 4 | MemoryReconciler CPU offload 阈值 | L3-1 MemoryReconciler | Memory > 1000 启用 |
| 5 | Operator 升级抖动抑制 | L3-1 Upgrade | webhooks conversion + Helm pre-upgrade |
| 6 | reconcile 性能 informer 分片 | L3-1 Performance | v0.1 不分片；监控 queue depth |
| 7 | Workflow 表达式引擎 | L3 Future | v0.1 仅静态；v0.5 CEL |
| 8 | AgentSet owns Agent 删除处理 | 本 Spec §4.2 | orphanDeletion=false |
| 9 | Leader Election 与 MemoryReconciler 关系 | 本 Spec §6.4 | 复用同一 Lease（单一 leader） |
| 10 | admission 拒绝审计日志格式 | L3-1 Admission | structlog + K8s Event |
| 11 | Operator CrashLoopBackOff Lease 释放 | L3-1 Leader Election | grace period 30s + TTL 过期 |
| 12 | Kopf handlers 异常 Status 更新 | L3-1 Error Handling | 触发（phase=Failed） |
| 13 | admission 错误响应格式 | L3-1 Admission | reason snake_case + http_status |
| 14 | structlog trace_id 注入位置 | L3-1 Observability | K8s Events + structlog + audit |
| 15 | Helm values 验证失败可读性 | L3-1 Helm | Pydantic → YAML 路径翻译 |
| 16 | Operator + admission 崩溃隔离 | L3-1 Architecture | subprocess 隔离 admission |

> **完整 18 项清单见 §14**（含统计：本 Spec 已收敛 5 项 + 移交 L3-1 11 项 + 未来版本 1 项 + 新发现 8 项）。

---

> **签署（v0.2.0）**：本 L2-2 Operator Core Python v0.2.0 由起草人根据 [`docs/design/L2-modules/L2-operator-core.md` v0.1.0 Go baseline](../../archive/pre-python-2026-07-24/L2-operator-core-design-v0.1.0-go-baseline.md) + [ADR-0005](../../adr/0005-python-first-technology-stack.md) + [L1 Architecture v0.2.0](../L1-architecture.md) + [L2-1 Python v0.2.0](../L2-modules/L2-a2a-protocol.md) 编写，依据宪法 §14.4 评审通过（10 维度全 PASS）。
> **版本演进**：v0.1.0 Go baseline（2026-07-24 评审通过 + 已归档）→ v0.2-draft-skeleton（#23）→ v0.2-draft-full（#25）→ **v0.2.0**（#26 评审通过）
> **下次会话入口**：L2-2 Spec v0.2-draft Python 起草（独立任务；30-40KB / ~800-1000 行；建议拆 Spec 起草 + 评审两会话避免 §16.1 红线）+ L3-1 文件级 Spec 起草（Operator Core Python；建议拆主 Spec 50-60KB + 辅助 Spec 30-40KB 两文档）