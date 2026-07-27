# L2 模块设计：Operator Core（编排层）

> 📦 **ARCHIVED · 2026-07-24 · GO BASELINE · DO NOT USE FOR PYTHON IMPLEMENTATION**
> 本文件是 L2-2 Operator Core 的 Go baseline v0.1.0 归档（2026-07-24 评审通过；ADR-0005 supersede 指针同期追加）。**仅作历史参考**，所有 Python 实现依据请参考：
> - **Python 设计 v0.2-draft**：`docs/design/L2-modules/L2-operator-core.md`（待 #23 会话起草）
> - **ADR-0005 Python-first**：`docs/adr/0005-python-first-technology-stack.md` §3.1 Operator Core 模块映射
> - **L1 v0.2.0 Architecture**：`docs/design/L1-architecture.md` §3.2 编排层 + §4 核心组件

> **⚠️ ADR-0005 supersede 指针（2026-07-24）**：本 v0.1.0 设计文档**仅 supersede Go / kubebuilder / controller-runtime / client-go 实现条款**；wire contract（CRD YAML / Controller reconcile 语义 / Leader Election / Finalizer / RBAC）与 v0.1 业务语义**完全继续有效**。L1 v0.2.0 已于 2026-07-24 评审通过（[`docs/reviews/l1-python-stack-migration-review.md`](../../reviews/l1-python-stack-migration-review.md)），依据 ADR-0005 Python-first 全栈迁移。本文档作为**迁移输入**保留，待 L2-2 Python v0.2 重写并评审通过后归档至 `docs/archive/pre-python-2026-07-24/`。v0.1 不得作为 Python 实现依据。
>
> **层级**：L2 — 模块设计
> **模块 ID**：C-1（Operator Core，见 L1 第 6 节模块清单）
> **代码位置**：`src/operator/`（**v0.1 Go 路径，已废弃**）
> **版本**: v0.1.0（2026-07-24）+ ADR-0005 supersede 指针（2026-07-24）
> **状态**: ✅ v0.1.0 已评审通过 + ⚠️ 待 L2-2 Python v0.2 重写（2026-07-24 计划）
> **配套 Spec**: [`docs/spec/L2-module-specs/L2-operator-core.md`](../../spec/L2-module-specs/L2-operator-core.md) v0.1.0（顶部同样追加 supersede 指针）
> **Python 重写入口**：依据 L1 v0.2.0 Architecture §3.2 + ADR-0005 §3.1 + §7，4 个 Controller（Agent / AgentSet / Workflow / MemoryReconciler）由 **Kopf async handlers + 独立 async reconciler services** 实现；Leader Election 用 `coordination.k8s.io/v1 Lease`；K8s I/O 用 `kubernetes_asyncio`；handler 30-50 行 + service 业务逻辑分离
> **上游约束**：L1 Architecture §3.2 / §5（CRD 列表）/ §6（Adapter 契约）；宪法 §3.1（K8s-native）/ §3.5（协议兼容）/ §7（可观测性）/ §9（测试）
> **本模块目的**：定义 `superteam-a2a` Operator 的 4 个 Controller (Agent / AgentSet / Workflow / MemoryReconciler) 的 reconcile 契约、状态机、错误处理、依赖关系。它是 L1 §3.2 编排层的唯一实现，**所有 CRD 生命周期管理均通过本模块**。

---

## 1 模块边界（Scope & Non-Goals）

### 1.1 职责（In-Scope）

- **4 个 Controller** 的 reconcile 循环实现：
  - AgentController（CRD: Agent）
  - AgentSetController（CRD: AgentSet）
  - WorkflowController（CRD: Workflow）
  - MemoryReconciler（CRD: Memory）—— 代理由 ADR-0003 引入
- **Leader election**（同一 namespace 同类 Controller 单实例运行）
- **Workqueue + 指数退避重试**（基于 controller-runtime）
- **Finalizer**（防止 CR 删除时资源泄漏）
- **Status 字段更新**（observedGeneration / conditions / endpoints）
- **指标 + Events**（按宪法 §7）
- **Watch 关系**（Agent → AgentSet → Deployment → Service → Agent 闭环）

### 1.2 非职责（Out-of-Scope）

- ❌ 不实现 Agent 业务逻辑（属 Adapter / Agent 框架）
- ❌ 不直接实现 A2A 协议（属 A2A Protocol 模块，调用其 Client SDK）
- ❌ 不实现 Knowledge / Memory 业务（属 Knowledge / Memory 模块）
- ❌ 不实现 Adapter 镜像（属 Adapter 模块）
- ❌ 不实现 Workflow 表达式引擎（v0.5+，宪法 §3.10）
- ❌ 不实现 CRD schema 定义（属 L1 Spec，仅生成 deepcopy）

---

## 2 在 L1 中的位置

L1 第 3.1 节确立的 5 层架构中，本模块独占 **第 ② 层编排层**：

```
① 接入层 (kubectl / Helm / UI / CLI)
② 编排层 ←—— 本模块（4 Controllers + Leader election + Workqueue）———————
③ 资源模型层 (CRDs: Agent / AgentSet / Workflow / KnowledgeScope / KnowledgeItem / Memory)
④ 通信层 (A2A Protocol Adapter + Discovery)
⑤ 运行时层 (Agent Pods / Sidecar / External Agents)
```

**与其他模块的依赖方向**（仅向下依赖，禁止反向）：

| 上游模块（依赖本模块） | 调用形态 |
|------------------------|----------|
| 用户 / kubectl | 通过 K8s API 创建 / 修改 CR |
| Workflow Controller | 通过本模块 reconcile 结果触发 A2A 调用（直接调 Client SDK） |
| Adapter | 通过本模块 status 字段响应（endpoints / AgentCard） |
| MemoryReconciler | 通过本模块 reconcile 触发 Memory 衰减 / 强化（写 Memory CR） |

| 下游依赖（本模块使用） | 用途 |
|------------------------|------|
| k8s.io/apimachinery | CRD schema 生成 |
| sigs.k8s.io/controller-runtime | Manager / Controller / Reconciler / Client / Workqueue |
| go.opentelemetry.io/otel | trace / metric |
| `src/a2a/client` | 调度 Agent / 触发 A2A 调用（Workflow Controller） |
| `src/knowledge` / `src/memory` | Knowledge / Memory CR reconcile（仅 import 类型） |

---

## 3 子模块拆分

```
src/operator/
├── main.go                       # Operator 启动入口
├── controllers/
│   ├── agent_controller.go       # AgentController
│   ├── agentset_controller.go    # AgentSetController
│   ├── workflow_controller.go    # WorkflowController
│   └── memory_reconciler.go      # MemoryReconciler
├── common/
│   ├── reconciler.go             # Reconciler 通用接口 + 通用工具
│   ├── finalizer.go              # Finalizer 通用实现
│   ├── leader_election.go        # Leader election 配置
│   ├── status.go                 # Status 字段更新工具
│   └── conditions.go             # 4 类 Condition 工厂
├── watches/
│   └── watches.go                # Watch 关系注册（Agent → Deployment 等）
├── apis/                         # CRD 类型定义（generated from L1 Spec）
│   ├── agent/v1alpha1/
│   ├── agentset/v1alpha1/
│   ├── workflow/v1alpha1/
│   └── memory/v1alpha1/
└── observability/
    ├── metrics.go                # Prometheus 指标
    └── events.go                 # K8s Event 发射器
```

---

## 4 公共 API 表面

### 4.1 Reconciler 接口

```go
// Reconciler 是所有 4 个 Controller 共用的通用接口
type Reconciler interface {
    // Reconcile 是单次 reconcile 入口
    Reconcile(ctx context.Context, req Request) (Result, error)
    
    // SetupWithManager 注册 Controller 到 Manager
    SetupWithManager(mgr ctrl.Manager) error
}

type Request struct {
    NamespacedName types.NamespacedName
}

// Result 决定 reconcile 行为
type Result struct {
    Requeue      bool          // 立即重新入队
    RequeueAfter time.Duration // 延迟重新入队
}
```

### 4.2 Controller 启动配置

```go
type OperatorConfig struct {
    MetricsAddr          string        // default ":8080"
    HealthAddr           string        // default ":8081"
    LeaderElection       bool          // default true
    LeaderElectionID     string        // "superteam-a2a-operator"
    LeaderElectionNS     string        // default "superteam-a2a-system"
    WatchNamespace       string        // "" → all namespaces
    MaxConcurrentReconciles int        // default 1
}

func Main(cfg OperatorConfig) error
```

### 4.3 4 个 Controller 入口

| Controller | Watch 资源 | Owned 资源 | Owns 关系 |
|------------|------------|------------|----------|
| AgentController | Agent | Deployment, Service, ServiceAccount, Role, RoleBinding | 5 类 |
| AgentSetController | AgentSet | Agent (如果 replicas > 0) | 1 类 |
| WorkflowController | Workflow | (Task CRD 移除，任务直接通过 A2A Client 触发) | 0 类 |
| MemoryReconciler | Memory | (无 owned，单独 reconcile 衰减) | 0 类 |

---

## 5 关键数据结构

### 5.1 CRD 资源类型（generated from L1 Spec）

```go
// 4 个 CRD 的 Go 类型（全部从 L1 Spec §2-§4 + ADR-0003 §6 生成）
package agentv1alpha1

type Agent struct {
    metav1.TypeMeta   `json:",inline"`
    metav1.ObjectMeta `json:"metadata,omitempty"`
    Spec   AgentSpec   `json:"spec"`
    Status AgentStatus `json:"status,omitempty"`
}
type AgentSpec struct { /* 10 个字段，详见 L1 Spec §2.1 */ }
type AgentStatus struct { /* 8 个字段，详见 L1 Spec §2.5 */ }

// AgentSet / Workflow / Memory 类似，省略
```

### 5.2 Reconciler 通用辅助

```go
// Finalizer 名称规范
const (
    FinalizerAgent    = "superteam-a2a.io/agent-protection"
    FinalizerAgentSet = "superteam-a2a.io/agentset-protection"
    FinalizerWorkflow = "superteam-a2a.io/workflow-protection"
    FinalizerMemory   = "superteam-a2a.io/memory-protection"
)

// 4 类 Condition 工厂
func NewReadyCondition(reason, message string) metav1.Condition
func NewProgressingCondition(reason, message string) metav1.Condition
func NewDegradedCondition(reason, message string) metav1.Condition
func NewReconciledCondition(reason, message string) metav1.Condition
```

### 5.3 状态机流转通用

```go
// StatusHelper 自动化 status 字段更新
type StatusHelper struct {
    Client client.Client
}

func (h *StatusHelper) UpdateStatus(ctx context.Context, obj client.Object, phase string, conditions []metav1.Condition) error

func (h *StatusHelper) AddFinalizer(ctx context.Context, obj client.Object, finalizer string) error
func (h *StatusHelper) RemoveFinalizer(ctx context.Context, obj client.Object, finalizer string) error

func (h *StatusHelper) IsBeingDeleted(obj client.Object) bool
func (h *StatusHelper) HasFinalizer(obj client.Object, finalizer string) bool
```

---

## 6 状态机

### 6.1 Agent 状态机（L1 Spec §2.5）

```
Pending ──(reconcile 成功)──▶ Available
   │                            │
   │                            │(reconcile 失败)
   │                            ▼
   └──────────────────────────▶ Failed
                                │
                                │(rebalance / 重新 reconcile)
                                ▼
                             Available
```

| 状态 | 进入条件 | 退出条件 |
|------|----------|----------|
| Pending | CR 创建 / spec 变化 | Deployment / Service 创建完成 |
| Available | Pod ready + Service endpoints 填充 + AgentCard 暴露 | 上述任意失败 |
| Failed | reconcile 错误 / 资源创建失败 | spec 变化触发重新 reconcile |

### 6.2 AgentSet 状态机

```
Pending ──(计算 replicas)──▶ ScalingUp ──(ready)──▶ Available
   │                            │                     │
   │                            └─(减少)──▶ ScalingDown
   │                                                  │
   └──────────────────────────────────────────────────▶ Failed
```

| 状态 | 进入条件 | 退出条件 |
|------|----------|----------|
| Pending | CR 创建 | replicas > 0 |
| ScalingUp | 增加 replicas | 所有 Pod ready |
| ScalingDown | 减少 replicas | 旧 Pod 终止 |
| Available | replicas == readyReplicas | 数量变化或失败 |
| Failed | reconcile 错误 | spec 变化 |

### 6.3 Workflow 状态机（L1 Spec §4.2）

```
Pending ──(DAG 校验通过)──▶ Running ──(全部 task 完成)──▶ Succeeded
   │                          │                            │
   │                          │(超时)                      │
   │                          ▼                            │
   │                       Timeout ──(重试)──▶ Running    │
   │                                                      │
   └──────────────────(失败)──────────────────────────────▶ Failed
```

| 状态 | 进入条件 | 退出条件 |
|------|----------|----------|
| Pending | CR 创建 | DAG 校验通过 + 首个任务调度 |
| Running | 任务调度启动 | 全部任务完成 / 失败 / 超时 |
| Succeeded | 全部任务成功 | 终态 |
| Failed | 任务失败 / DAG 校验失败 | 终态（可人工重建） |
| Timeout | 超过 workflow.timeout | 终态（可重试） |

### 6.4 Memory 状态机（ADR-0003 §6.5）

```
Active ──(decay 时间到)──▶ Decaying ──(reinforced)──▶ Active
   │                          │
   │                          │(过期)
   │                          ▼
   │                       Expired (终态，可清理)
   │
   └──(scope 提升)──▶ Active (新 scope)
```

| 状态 | 进入条件 | 退出条件 |
|------|----------|----------|
| Active | CR 创建 / 强化 | 时间到 |
| Decaying | decayDays 到期 | 强化 / 过期 |
| Expired | 超出 grace period | 终态（GC） |

---

## 7 关键算法

### 7.1 Reconcile 通用流程（伪代码）

```go
func (r *AgentReconciler) Reconcile(ctx context.Context, req Request) (Result, error) {
    // 1. 获取 CR
    agent := &Agent{}
    if err := r.Get(ctx, req.NamespacedName, agent); err != nil {
        return Result{}, client.IgnoreNotFound(err)
    }
    
    // 2. 处理删除
    if agent.DeletionTimestamp != nil {
        return r.reconcileDelete(ctx, agent)
    }
    
    // 3. 确保 Finalizer
    if !r.HasFinalizer(agent, FinalizerAgent) {
        r.AddFinalizer(ctx, agent, FinalizerAgent)
        return Result{Requeue: true}, nil
    }
    
    // 4. Spec 差异检测
    if !r.specChanged(agent) {
        return Result{}, nil
    }
    
    // 5. 主体 reconcile
    if err := r.reconcileDeployment(ctx, agent); err != nil {
        return r.updateStatus(ctx, agent, "Failed", err)
    }
    if err := r.reconcileService(ctx, agent); err != nil {
        return r.updateStatus(ctx, agent, "Failed", err)
    }
    if err := r.reconcileAgentCard(ctx, agent); err != nil {
        return r.updateStatus(ctx, agent, "Failed", err)
    }
    
    // 6. 更新 Status
    return r.updateStatus(ctx, agent, "Available", nil)
}
```

### 7.2 Watches 关系

| Watcher | Watches | 用途 |
|---------|---------|------|
| AgentController | Deployment | 检测 Pod 状态变化 |
| AgentController | Service | 检测 endpoints 变化 |
| AgentSetController | Agent | 检测 Agent CR 变化（生成） |
| WorkflowController | Agent / Task | 任务调度触发 |

### 7.3 Leader Election

- 同一 namespace 同类 Controller **单实例**运行（避免并发 reconcile）
- 使用 `Lease` CRD（kube-system 或 superteam-a2a-system）
- 续期间隔 15s，租约 30s（controller-runtime 默认）
- 切换时 Workqueue 重新入队

### 7.4 Finalizer 机制

```go
// reconcileDelete 流程
1. 获取所有 owned resource
2. 执行清理（删除 Deployment / Service / RBAC）
3. 等待 owned resource 真正删除（poll 5s）
4. RemoveFinalizer
5. CR 进入正常删除流程
```

### 7.5 重试与退避

| 场景 | 行为 |
|------|------|
| K8s API 临时错误（5xx） | 指数退避（1s → 2s → 4s → 8s → 30s 上限） |
| K8s API 冲突（409） | 立即重试（资源版本过期） |
| K8s API 4xx | 标记 Failed，不重试 |
| Agent reconcile 失败 | 同 controller-runtime 默认 |

### 7.6 Memory 衰减算法（ADR-0003 §4.3）

```
每 1 小时 reconcile 一次 Memory CR：
  if now - lastReinforcedAt > decayDays:
    state = "Decaying"
    confidence *= 0.95  // 每天衰减 5%
  if confidence < 0.1:
    state = "Expired"
    // 30 天后 GC
```

---

## 8 身份认证

- **Operator 自身**：通过 ServiceAccount 调 K8s API（RBAC 由 Helm 创建）
- **调用 A2A**：使用 `src/a2a/client` 的 SPIFFE 身份（Operator SPIFFE ID 特权，可调所有 method）
- **跨 namespace 隔离**：见 L2-1 Spec §2.7 `Authorize` 函数

---

## 9 可观测性

### 9.1 Prometheus 指标

| 指标 | 类型 | 标签 | 用途 |
|------|------|------|------|
| `supteam_operator_reconcile_total` | Counter | controller, result | reconcile 总数 |
| `supteam_operator_reconcile_duration_seconds` | Histogram | controller | reconcile 延迟 |
| `supteam_operator_reconcile_errors_total` | Counter | controller, reason | 错误分类 |
| `supteam_operator_workqueue_depth` | Gauge | controller | 队列深度 |
| `supteam_operator_leader_election_state` | Gauge | controller | 0=follower, 1=leader |
| `supteam_operator_owned_resources` | Gauge | controller, kind | owned 资源数 |
| `supteam_operator_memory_decay_total` | Counter | scope | Memory 衰减次数 |

### 9.2 K8s Events

| Type | Reason | 触发 |
|------|--------|------|
| Normal | Created | owned resource 创建 |
| Normal | Updated | owned resource 更新 |
| Normal | StatusUpdated | status 字段更新 |
| Warning | ReconcileError | reconcile 错误 |
| Warning | FinalizerTimeout | Finalizer 清理超时 |

### 9.3 OTel Span

- 每个 reconcile 调 Span `operator.reconcile.{controller}`
- 属性包含 controller / namespace / name / generation / result
- 与 A2A Span 链接（通过 traceparent）

---

## 10 错误模型

### 10.1 自定义错误码（与 L2-1 §10 区分）

| Code | 名称 | 触发 | 客户端行为 |
|------|------|------|-----------|
| 1001 | ReconcileError | reconcile 任意错误 | 重试（指数退避） |
| 1002 | FinalizerTimeout | Finalizer 清理 30s 未完成 | 报警 |
| 1003 | OwnedResourceLeak | Finalizer 移除后 owned 资源残留 | 报警 |
| 1004 | DAGValidation | Workflow DAG 校验失败 | 不可重试 |
| 1005 | MemoryDecayError | Memory 衰减失败 | 重试 |

### 10.2 错误处理优先级

```go
// 错误优先级
1. K8s API 认证错误 → 立即失败，标记 Operator 自身不可用
2. Schema 校验错误 → 标记为 Failed，requeue=false
3. owned resource 冲突 → 重新获取资源版本，重试
4. owned resource 临时错误 → 指数退避重试
5. 业务错误（如 DAG 校验失败）→ 标记 Failed + Event
```

---

## 11 版本管理与兼容性

- **本模块锁定**：K8s 1.28+ / controller-runtime v0.18+
- **CRD 版本演进**：`v1alpha1` → `v1beta1` → `v1`（与 L1 Spec §1.1 一致）
- **升级路径**：通过 admission webhook 实现 v1alpha1 → v1beta1 conversion
- **Finalizer 列表**：所有 v0.1 Finalizer 永久保留（不删除已注册 Finalizer）

---

## 12 依赖矩阵

| 依赖 | 方向 | 用途 | 备注 |
|------|------|------|------|
| k8s.io/api | 下游 | K8s API 类型 | 必选 |
| k8s.io/apimachinery | 下游 | CRD schema 生成 | 必选 |
| sigs.k8s.io/controller-runtime | 下游 | Manager / Controller | 必选 |
| `src/a2a/client` | 内部 | Reconciler 调 A2A | 接口稳定 |
| `src/knowledge` / `src/memory` | 内部 | 类型 import | 后续模块 |
| go.opentelemetry.io/otel | 下游 | trace | 必选 |
| github.com/prometheus/client_golang | 下游 | 指标 | 必选 |

---

## 13 测试策略

### 13.1 单元测试（覆盖率 ≥ 80%）

- `common/reconciler.go`：通用工具方法
- `common/finalizer.go`：Finalizer 添加 / 移除
- `common/status.go`：status 字段更新
- `controllers/agent_controller.go`：reconcile 路径（mock client）
- `controllers/agentset_controller.go`：replicas 数学
- `controllers/workflow_controller.go`：DAG 校验
- `controllers/memory_reconciler.go`：衰减算法

### 13.2 集成测试（envtest）

- Controller 完整 reconcile 循环
- Finalizer 完整流程
- Watch 触发（创建 Deployment → Controller 响应）
- 错误路径（K8s API 失败）

### 13.3 E2E（kind + hello-agent）

- `kubectl apply -f hello-agent.yaml` → Controller 创建 Deployment → Pod ready → Agent Card 拉取成功
- AgentSet 扩缩容（3 → 5 → 1）
- Workflow 任务调度（Hello Agent 为例）
- Memory 衰减 → 强化 → 衰减 全链路

---

## 14 开放问题（移交 L2 Spec / L3）

1. **reconcile 性能**：当 Agent 数量 > 1000 时，单 Controller reconcile 性能如何？是否需要 informer 分片？
2. **Workflow 表达式引擎**：v0.1 静态 inputs，v0.5 引入表达式引擎（CEL？）—— L2-2 Spec 需明确 stub 接口
3. **Memory 衰减频率**：1 小时是否合理？高频（1 分钟）可提高精度但增加 Controller 负载
4. **Owned resource 引用**：AgentSet owns Agent 时，Agent 删除如何处理？是否需要 Orphan 模式？
5. **Operator 升级策略**：CRD 字段新增时如何避免 reconcile 抖动？webhook conversion 流程

---

## 15 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| L2-2-draft | 2026-07-23 | 初稿：Operator Core 模块设计；4 Controllers + Leader election + Workflow + Memory reconcile 完整定义 |
| v0.1.0 | 2026-07-24 | 评审通过；版本号从 L2-2-draft 升级为 v0.1.0；与配套 Spec 同步 |

> **评审门禁（宪法 §14.4）**：本 L2 文档评审通过后，才能开始 `docs/spec/L2-module-specs/L2-operator-core.md` 的 Spec 起草，再之后才能进入 L3 文件级 Spec。
