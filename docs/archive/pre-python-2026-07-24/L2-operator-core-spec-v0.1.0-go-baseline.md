# L2 模块规格：Operator Core（编排层）

> 📦 **ARCHIVED · 2026-07-24 · GO BASELINE · DO NOT USE FOR PYTHON IMPLEMENTATION**
> 本文件是 L2-2 Operator Core 的 Go baseline Spec v0.1.0 归档（2026-07-24 评审通过；ADR-0005 supersede 指针同期追加）。**仅作历史参考**，所有 Python 实现依据请参考：
> - **Python Spec v0.2-draft**：`docs/spec/L2-module-specs/L2-operator-core.md`（待 #23+ 会话起草）
> - **ADR-0005 Python-first**：`docs/adr/0005-python-first-technology-stack.md` §3.1 + §7 单进程原则 + §13.1 OTel/指标迁移
> - **L1 v0.2.0 Spec**：`docs/spec/L1-system-spec.md` §2-§4 CRD + §7 状态机 + §9-§10 资源/限流

> **⚠️ ADR-0005 supersede 指针（2026-07-24）**：本 v0.1.0 Spec 文档**仅 supersede Go struct / kubebuilder annotation / controller-runtime reconcile / client-go 调用 实现条款**；wire contract（4 Controller / CRD 状态机 / Leader Election / Finalizer / RBAC / metric name）与 v0.1 业务语义**完全继续有效**。L1 v0.2.0 已于 2026-07-24 评审通过，依据 ADR-0005 Python-first 全栈迁移。本文档作为**迁移输入**保留，待 L2-2 Python v0.2 Spec 重写并评审通过后归档至 `docs/archive/pre-python-2026-07-24/`。v0.1 不得作为 Python 实现依据。
>
> **Python 重写入口**：依据 L1 v0.2.0 Spec §0 + ADR-0005 §3.1 + §7，Go struct → Pydantic v2 BaseModel；kubebuilder annotation → `Field(...)`；controller-runtime reconcile → Kopf handlers + 独立 async reconciler services；client-go → `kubernetes_asyncio`；状态子资源写回用 `kopf.adopt(status_patch=...)`；Leader Election 用 K8s Lease
>
> **层级**: L2 — 模块 Spec
> **模块 ID**: C-1（Operator Core，见 L1 Architecture §6 模块清单）
> **代码位置**: `src/operator/`（**v0.1 Go 路径，已废弃**）
> **版本**: v0.1.0（2026-07-24）+ ADR-0005 supersede 指针（2026-07-24）
> **状态**: ✅ v0.1.0 已评审通过 + ⚠️ 待 L2-2 Python v0.2 Spec 重写
> **配套设计**: [`docs/design/L2-modules/L2-operator-core.md`](../../design/L2-modules/L2-operator-core.md) v0.1.0（顶部同样追加 supersede 指针）
> **依据**: 宪法 v0.3.0 §3.1（分层）/ §3.2（Operator 模式）/ §3.7（反依赖）/ §6.1（认证）/ §7（可观测性）/ §9（测试）/ §14（设计流程）/ §16（会话纪律）；L1 Architecture §3.2 / §5 / §6；L1 Spec §1-§4 + §7.6 + §9-§10；ADR-0003 §4（Memory 衰减算法）
> **评审门禁**: 宪法 §14.4（L2 Spec 起草通过后才能开始 L3 文件级 Spec）

---

## 0. 阅读指南

本文档定义 `src/operator/` 6 个子包的 **exported API 契约**、**4 个 Controller 的 reconcile 流程伪代码**、**Helm values 默认值**、**Finalizer / Condition / Error / Watch 契约**、**Memory 衰减算法实现细节**、**测试用例骨架**。**不**解释"为什么"（设计意图见配套设计文档）。

**读者**: L3 文件级 Spec 起草者、Controller 实现者、Helm chart 维护者、评审者。

**与 L2 设计的边界**:

| L2 设计文档 | L2 Spec 文档（本） |
|-------------|---------------------|
| 概念 / 架构图 / 选型理由 | 函数签名 / 默认值 / 伪代码 / 契约表 |
| 状态机图 + 守卫规则 | 状态机实现 API（FSM）+ State Transition Test 矩阵 |
| 错误码名单 | 错误码 → Go 错误类型 + Retryable + 处理优先级伪代码 |
| 关键算法文字描述 | 算法签名 + 输入/输出契约 + 频率/间隔具体值 |
| 子模块目录树概念图 | 完整 export 列表 + 每个子包导出符号契约 |

**不包含在本 Spec**（移交其他模块）:
- 4 个 CRD 详细字段定义 → L1 Spec §2-§4 + ADR-0003 §6（Operator 仅消费类型）
- Adapter 镜像细节 → L2-3 Adapter Spec（Operator 仅创建 Deployment / Service 模板）
- Workflow 表达式引擎（v0.5+） → L3 Future Spec（v0.1 仅 stub 接口）
- Knowledge 业务逻辑 → L2-4 Knowledge Spec（Operator 仅 listens）

---

## 1. Go Package 布局

```
src/operator/
├── main.go                       # cmd 入口：解析 flags + 启动 Manager
├── controllers/
│   ├── agent_controller.go       # AgentController (CRD: Agent)
│   ├── agentset_controller.go    # AgentSetController (CRD: AgentSet)
│   ├── workflow_controller.go    # WorkflowController (CRD: Workflow)
│   └── memory_reconciler.go      # MemoryReconciler (CRD: Memory)
├── common/
│   ├── reconciler.go             # Reconciler 通用接口 + Result / Request 类型
│   ├── finalizer.go              # 4 个 Finalizer 常量 + 添加/移除 helper
│   ├── leader_election.go        # Leader election 配置 + Enable 选项
│   ├── status.go                 # StatusHelper：条件/状态/e metadata 更新
│   ├── conditions.go             # 4 类 Condition 工厂函数
│   └── errors.go                 # 5 个自定义错误 + 错误处理优先级
├── watches/
│   └── watches.go                # Watch 关系注册函数（4 Controller 共用）
├── apis/                         # CRD Go 类型（generated from L1 Spec，**不**手工修改）
│   ├── agent/v1alpha1/           # AgentSpec / AgentStatus / AgentCard / ...
│   ├── agentset/v1alpha1/        # AgentSetSpec / AgentSetStatus / ...
│   ├── workflow/v1alpha1/        # WorkflowSpec / WorkflowStatus / WorkflowTask
│   └── memory/v1alpha1/          # MemorySpec / MemoryStatus / MemoryState
└── observability/
    ├── metrics.go                # 7 个 Prometheus 指标注册 + helper 函数
    └── events.go                 # K8s Event 发射器（Normal/Warning + 5 类 reason）
```

**包级别约束**:
- `apis/` 子包**仅消费**（`import` 类型），**不**生成（由 `kubebuilder`/`controller-gen` 从 L1 Spec 自动生成 deepcopy）
- 所有 exported 符号必须有 godoc 注释（最小粒度：函数意图 + 参数约束 + 返回 + 错误语义）
- 自定义错误必须实现 `errors.Is`/`errors.As` 兼容（统一 `OperatorError` 类型）
- **不**创建 `_test.go` 之外的测试辅助符号；测试符号放 `*_test.go`
- **不**直接 import A2A 协议业务类型（仅 import `src/a2a/client` 包用于调度，见 L2-1 Spec §2.5）

---

## 2. 子包 exported API

### 2.1 `common/` — 通用基础设施

#### 2.1.1 Reconciler 接口

```go
package common

import (
    "context"
    "time"
    "sigs.k8s.io/controller-runtime/pkg/client"
)

type Reconciler interface {
    // Reconcile 单次 reconcile 入口；返回 Result 决定是否重入队
    Reconcile(ctx context.Context, req Request) (Result, error)
    
    // SetupWithManager 注册 Controller 到 Manager + Watch 关系
    SetupWithManager(mgr ctrl.Manager) error
}

type Request struct {
    NamespacedName types.NamespacedName  // CR 的 namespace + name
}

type Result struct {
    Requeue      bool          // true → 立即入队（不写回 Status）
    RequeueAfter time.Duration // > 0 → 延迟入队（用于 Memory 1 小时周期）
}

// ReconcileError 是 reconcile 错误的包装（携带 controller 标识）
type ReconcileError struct {
    Controller string  // "agent" | "agentset" | "workflow" | "memory"
    Reason     string  // 错误简码
    Err        error   // 底层错误
    Retryable  bool    // 客户端据此决定是否重试
}

func (e *ReconcileError) Error() string
func (e *ReconcileError) Unwrap() error
func (e *ReconcileError) Is(target error) bool  // 按 Reason 匹配
```

#### 2.1.2 Finalizer 常量 + Helper

```go
package common

const (
    FinalizerAgent    = "superteam-a2a.io/agent-protection"
    FinalizerAgentSet = "superteam-a2a.io/agentset-protection"
    FinalizerWorkflow = "superteam-a2a.io/workflow-protection"
    FinalizerMemory   = "superteam-a2a.io/memory-protection"
)

// AddFinalizer 幂等添加（已存在则 no-op）
func AddFinalizer(ctx context.Context, c client.Client, obj client.Object, finalizer string) error

// RemoveFinalizer 幂等移除
func RemoveFinalizer(ctx context.Context, c client.Client, obj client.Object, finalizer string) error

// HasFinalizer 检查 finalizer 是否存在
func HasFinalizer(obj client.Object, finalizer string) bool

// IsBeingDeleted 检查 DeletionTimestamp 是否非空
func IsBeingDeleted(obj client.Object) bool
```

**Finalizer 命名规则（永久承诺，宪法 §11.3）**:
- 所有 v0.1 Finalizer 名称**永久保留**到 v1.0+（即便语义变化也只增不改）
- 新增 Finalizer 必须以 `superteam-a2a.io/{kind}-protection` 结尾

#### 2.1.3 Condition 工厂（4 类）

```go
package common

import metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

type Condition = metav1.Condition  // type alias

// NewReadyCondition：Ready=True 表示资源可用
func NewReadyCondition(status metav1.ConditionStatus, reason, message string) Condition

// NewProgressingCondition：Progressing=True 表示 reconcile 进行中
func NewProgressingCondition(reason, message string) Condition

// NewDegradedCondition：Degraded=True 表示降级运行（reconcile 出错但未失败）
func NewDegradedCondition(reason, message string) Condition

// NewReconciledCondition：Reconciled=True 表示最近一次 reconcile 成功
func NewReconciledCondition(status metav1.ConditionStatus, reason, message string) Condition

// 4 类 Condition Type 常量
const (
    ConditionReady       = "Ready"
    ConditionProgressing = "Progressing"
    ConditionDegraded    = "Degraded"
    ConditionReconciled  = "Reconciled"
)
```

**使用约束**:
- 每个 Controller **每次** reconcile 必须 set **全部 4 类** Condition（即便状态未变也要重设以更新 `LastTransitionTime`）
- 4 类 Condition Type 与 L1 Spec §1.5 严格一致

#### 2.1.4 StatusHelper

```go
package common

type StatusHelper struct {
    Client client.Client
}

// UpdateStatus 原子更新 Status 子资源（不触发 reconcile 风暴）
func (h *StatusHelper) UpdateStatus(
    ctx context.Context,
    obj client.Object,
    phase string,                  // "Pending" | "Available" | ...
    conditions []metav1.Condition,
    opts ...StatusOpt,
) error

// UpdateEndpoints 只更新 Endpoints（用于 Agent CR endpoints 频繁变化）
func (h *StatusHelper) UpdateEndpoints(
    ctx context.Context,
    agent *agentv1alpha1.Agent,
    endpoints []Endpoint,
) error

// IncrementObservedGeneration 同步 observedGeneration = metadata.generation
func (h *StatusHelper) IncrementObservedGeneration(ctx context.Context, obj client.Object) error

type StatusOpt func(*statusOpts)
func WithRetry(r int) StatusOpt                 // 重试次数（默认 3）
func WithBackoff(d time.Duration) StatusOpt       // 重试间隔（默认 100ms）
```

#### 2.1.5 错误模型（5 类自定义错误码）

```go
package common

import stderr "errors"

// OperatorError 是 Operator 域错误（统一格式）
type OperatorError struct {
    Code      int            // 见下表
    Reason    string         // 短码，对齐 K8s Event.reason
    Message   string         // 人类可读
    Component string         // "agent-controller" | ...
    Cause     error          // 底层错误（可选）
}

func (e *OperatorError) Error() string
func (e *OperatorError) Unwrap() error
func (e *OperatorError) Is(target error) bool  // 按 Code 匹配

// 5 个自定义错误（与 A2A 域错误区分，范围 1001-1099）
var (
    ErrReconcile         = &OperatorError{Code: 1001, Reason: "ReconcileError", Message: "reconcile failed"}
    ErrFinalizerTimeout  = &OperatorError{Code: 1002, Reason: "FinalizerTimeout", Message: "finalizer cleanup timed out"}
    ErrOwnedResourceLeak = &OperatorError{Code: 1003, Reason: "OwnedResourceLeak", Message: "finalizer removed but owned resource remains"}
    ErrDAGValidation     = &OperatorError{Code: 1004, Reason: "DAGValidationError", Message: "workflow DAG validation failed"}
    ErrMemoryDecay       = &OperatorError{Code: 1005, Reason: "MemoryDecayError", Message: "memory decay calculation failed"}
)

// SentinelErrorIs 判断是否为可重试错误
func IsRetryable(err error) bool  // Code 在 {1001, 1005}
func IsPermanent(err error) bool  // Code 在 {1004}

// ClassifyError 将任意 error 分类为 OperatorError（如非 Operator 域则返回 ErrReconcile 包装）
func ClassifyError(component string, err error) *OperatorError
```

**错误处理优先级**（见设计 §10.2）:

```go
func handleReconcileError(err error) (ctrl.Result, error) {
    switch {
    case errors.Is(err, ErrDAGValidation):
        // 业务校验失败：标记 Failed，**不**重试
        return ctrl.Result{}, err
    case isK8sAuthError(err):
        // 认证失败：Operator 自身不可用，Fail fast
        return ctrl.Result{}, err
    case errors.Is(err, ErrReconcile) || errors.Is(err, ErrMemoryDecay):
        // 重试：指数退避（1s → 2s → 4s → 8s → 30s 上限）
        return ctrl.Result{RequeueAfter: backoff()}, nil
    default:
        // 默认：重试 1 次后放弃
        return ctrl.Result{RequeueAfter: 30 * time.Second}, nil
    }
}
```

### 2.2 `controllers/agent` — AgentController

```go
package agent

import (
    "context"
    "sigs.k8s.io/controller-runtime/pkg/client"
    agentv1alpha1 "superteam-a2a.io/operator/apis/agent/v1alpha1"
)

type AgentReconciler struct {
    client.Client
    Status     *common.StatusHelper
    Finalizer  *common.FinalizerHelper   // 见 §2.1.2
    Recorder   record.EventRecorder
    Metrics    *observability.Metrics
}

func (r *AgentReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error)

func (r *AgentReconciler) SetupWithManager(mgr ctrl.Manager) error

// 内部步骤（私有方法，由 Reconcile 按序调用）
func (r *AgentReconciler) reconcileDeployment(ctx context.Context, agent *agentv1alpha1.Agent) error
func (r *AgentReconciler) reconcileService(ctx context.Context, agent *agentv1alpha1.Agent) error
func (r *AgentReconciler) reconcileServiceAccount(ctx context.Context, agent *agentv1alpha1.Agent) error
func (r *AgentReconciler) reconcileRoleAndBinding(ctx context.Context, agent *agentv1alpha1.Agent) error
func (r *AgentReconciler) reconcileAgentCard(ctx context.Context, agent *agentv1alpha1.Agent) error
```

**Owned 资源**（5 类，setOwnerReference + controller）:
- `apps/v1.Deployment`（Agent 主容器）
- `core/v1.Service`（暴露 A2A HTTP）
- `core/v1.ServiceAccount`（mTLS 身份）
- `rbac.authorization.k8s.io/v1.Role`
- `rbac.authorization.k8s.io/v1.RoleBinding`

**reconcileDelete 流程**（详见 §5.3）

### 2.3 `controllers/agentset` — AgentSetController

```go
package agentset

type AgentSetReconciler struct {
    client.Client
    Status *common.StatusHelper
}

func (r *AgentSetReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error)

// 计算 desiredReplicas（含 Rolling update 语义）
func (r *AgentSetReconciler) computeDesiredReplicas(set *agentsetv1alpha1.AgentSet) int32

// 计算 Label selector（匹配 Agent CR）
func (r *AgentSetReconciler) selector(set *agentsetv1alpha1.AgentSet) labels.Selector

// Apply Rolling update 策略（MaxSurge / MaxUnavailable）
func (r *AgentSetReconciler) applyRollingUpdate(ctx context.Context, set *agentsetv1alpha1.AgentSet, ready int32) error
```

**Owned 资源**（1 类）:
- `superteam-a2a.io/v1alpha1.Agent`（replicas > 0 时创建）

**关键算法**: 见 §5.4（replicas 数学 + Rolling update）

### 2.4 `controllers/workflow` — WorkflowController

```go
package workflow

type WorkflowReconciler struct {
    client.Client
    Status    *common.StatusHelper
    A2AClient *a2aclient.Client  // 调用 L2-1 client 触发 task
}

func (r *WorkflowReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error)

// DAG 校验（5 条规则）
func (r *WorkflowReconciler) validateDAG(spec *workflowv1alpha1.WorkflowSpec) error

// 调度就绪任务（DependsOn 全部 Succeeded）
func (r *WorkflowReconciler) scheduleReadyTasks(ctx context.Context, wf *workflowv1alpha1.Workflow) error

// 记录 Task 输出到 Status.TaskStatuses
func (r *WorkflowReconciler) recordTaskResult(taskID string, status workflowv1alpha1.TaskStatus) error

// 检查 Workflow 是否完成（全部 Succeeded 或 任意 Failed 不可重试）
func (r *WorkflowReconciler) isTerminal(wf *workflowv1alpha1.Workflow) (done bool, phase string)
```

**DAG 校验 5 条规则**（对 L1 Spec §4.4 的实现契约）:

```go
func validateDAG(spec *WorkflowSpec) error {
    // 1. 无环：DFS + 灰色节点检测
    if hasCycle(spec.Tasks) { return ErrDAGValidation }
    // 2. 依赖存在：所有 dependsOn 引用 task.id
    if !allDepsExist(spec.Tasks) { return ErrDAGValidation }
    // 3. 无自依赖：task.dependsOn 不能包含 task.id
    if hasSelfDep(spec.Tasks) { return ErrDAGValidation }
    // 4. 无重复 ID：task.id 在 workflow 内唯一
    if hasDuplicateID(spec.Tasks) { return ErrDAGValidation }
    // 5. inputsFrom 合法：所有 (taskId, output) 存在且 type 一致
    if !allInputsValid(spec.Tasks) { return ErrDAGValidation }
    return nil
}
```

**Owned 资源**: 无（任务执行通过 A2A RPC，不创建 K8s 资源）

### 2.5 `controllers/memory` — MemoryReconciler

```go
package memory

type MemoryReconciler struct {
    client.Client
    Status *common.StatusHelper
    // 周期触发器（RequeueAfter=1h）
    Clock clock.Clock  // 接口，可注入 fake clock 用于测试
}

func (r *MemoryReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error)

// 衰减一次 Memory CR（核心算法）
// inputs: *Memory
// outputs: (newConfidence, newState, error)
func (r *MemoryReconciler) decayOne(ctx context.Context, mem *memoryv1alpha1.Memory) (float64, string, error)

// 强化一次 Memory CR（confidence += 0.05，上限 1.0）
func (r *MemoryReconciler) reinforceOne(ctx context.Context, mem *memoryv1alpha1.Memory, amount float64) error

// GC：删除 Expired 状态超过 gracePeriod 的 Memory
func (r *MemoryReconciler) gcExpired(ctx context.Context, mem *memoryv1alpha1.Memory) (deleteIt bool, err error)
```

**Owned 资源**: 无

**周期触发契约**:
- 默认 `RequeueAfter = 1h`（在 Reconcile 返回 `ctrl.Result{RequeueAfter: time.Hour}`）
- 同 `Clock` 接口注入以支持测试（`clock.RealClock{}` / `clock.NewFakeClock(t0)`）
- 每次 reconcile 处理**单个** Memory CR（rate-limited per-CR）
- **不**对全部 Memory 做 list+foreach（避免 list-watch 抖动）

**衰减算法实现**（详见 §5.6）

### 2.6 `watches/` — Watch 关系注册

```go
package watches

import "sigs.k8s.io/controller-runtime/pkg/builder"

// RegisterForController 注册 Controller 的 Watch 关系
func RegisterForController(b *ctrl.Builder, ctrlType WatchTarget) error

type WatchTarget string
const (
    WatchAgent              WatchTarget = "agent"           // watches Deployment + Service + Secret
    WatchAgentSet           WatchTarget = "agentset"        // watches Agent CR
    WatchWorkflow           WatchTarget = "workflow"        // watches Agent + Memory (为 task 输入)
    WatchMemory             WatchTarget = "memory"          // 无外部 watches（仅自身 CR）
)

type Predicate func(client.Object) bool
// used: PredicateForGenerationChange / PredicateForLabelChange / AlwaysTrue
```

**Watch 关系表**（完整版）:

| Controller | Watches | 谓词 | 用途 |
|------------|---------|------|------|
| AgentController | `apps/v1.Deployment` | GenerationChange | 检测 Pod 状态变化 |
| AgentController | `core/v1.Service` | GenerationChange | 检测 endpoints 变化 |
| AgentController | `core/v1.Secret`（mTLS） | GenerationChange | 证书轮换触发 reconcile |
| AgentSetController | `agent.v1alpha1.Agent` | LabelMatchPredicate | 检测 Agent CR 变化（生成 / 删除） |
| WorkflowController | `agent.v1alpha1.Agent` | LabelMatchPredicate | 监听 Agent 可用性（卡 task 调度） |
| WorkflowController | `memory.v1alpha1.Memory` | GenerationChange | 监听 task 输出到 memory 后的变化 |
| MemoryReconciler | — | — | 无外部 watches（自触发 1h reconcile） |

### 2.7 `apis/` — CRD 类型（仅指针引用）

本目录**仅**由 `controller-gen` 从 L1 Spec §2-§4 + ADR-0003 §6 自动生成。本 Operator 代码**消费**类型，**不修改**类型定义。

```go
// 编译期约束：apis/ 子包必须有 v1alpha1 版本
import (
    agentv1alpha1    "superteam-a2a.io/operator/apis/agent/v1alpha1"
    agentsetv1alpha1 "superteam-a2a.io/operator/apis/agentset/v1alpha1"
    workflowv1alpha1 "superteam-a2a.io/operator/apis/workflow/v1alpha1"
    memoryv1alpha1   "superteam-a2a.io/operator/apis/memory/v1alpha1"
)
```

**字段完整定义 → 见 L1 Spec §2.1 / §3.1 / §4.1 + ADR-0003 §6（Memory）**

### 2.8 `observability/` — 指标与事件

#### 2.8.1 Prometheus 指标（7 项）

```go
package observability

import "github.com/prometheus/client_golang/prometheus"

type Metrics struct {
    ReconcileTotal      *prometheus.CounterVec   // "supteam_operator_reconcile_total"
    ReconcileDuration   *prometheus.HistogramVec // "supteam_operator_reconcile_duration_seconds"
    ReconcileErrors     *prometheus.CounterVec   // "supteam_operator_reconcile_errors_total"
    WorkQueueDepth      *prometheus.GaugeVec     // "supteam_operator_workqueue_depth"
    LeaderElectionState *prometheus.GaugeVec    // "supteam_operator_leader_election_state"
    OwnedResources      *prometheus.GaugeVec     // "supteam_operator_owned_resources"
    MemoryDecayTotal    *prometheus.CounterVec   // "supteam_operator_memory_decay_total"
}

func NewMetrics(reg prometheus.Registerer) *Metrics

// Helper：每个指标都有 RecordXxx 方法
func (m *Metrics) RecordReconcile(controller string, result string, duration time.Duration)
func (m *Metrics) RecordReconcileError(controller string, reason string)
func (m *Metrics) RecordWorkQueueDepth(controller string, depth int)
func (m *Metrics) SetLeaderState(controller string, isLeader bool)
func (m *Metrics) SetOwnedResources(controller string, kind string, count int)
func (m *Metrics) RecordMemoryDecay(scope string, transition string)  // transition: active→decaying | decaying→active | ...
```

**指标命名规范**（宪法 §7.1 `superteam_*` 前缀）:

| 指标名 | 类型 | 标签 | 单位 |
|--------|------|------|------|
| `supteam_operator_reconcile_total` | Counter | `controller, result` | 个 |
| `supteam_operator_reconcile_duration_seconds` | Histogram | `controller` | 秒 |
| `supteam_operator_reconcile_errors_total` | Counter | `controller, reason` | 个 |
| `supteam_operator_workqueue_depth` | Gauge | `controller` | 个 |
| `supteam_operator_leader_election_state` | Gauge | `controller` | 0/1 |
| `supteam_operator_owned_resources` | Gauge | `controller, kind` | 个 |
| `supteam_operator_memory_decay_total` | Counter | `scope, transition` | 个 |

#### 2.8.2 K8s Events

```go
package observability

type EventHelper struct {
    Recorder record.EventRecorder
}

// 5 类 reason 常量（用于 EmitEvent 的 reason 字段）
const (
    EventReasonCreated         = "Created"            // Normal
    EventReasonUpdated         = "Updated"            // Normal
    EventReasonStatusUpdated   = "StatusUpdated"      // Normal
    EventReasonReconcileError  = "ReconcileError"     // Warning
    EventReasonFinalizerTimeout = "FinalizerTimeout"  // Warning
)

func (h *EventHelper) EmitEvent(obj client.Object, eventType, reason, message string)

// 5 类事件触发契约（与设计 §9.2 一致）
```

**5 类事件触发场景**:

| Type | Reason | 触发条件 | 关联指标 |
|------|--------|---------|---------|
| Normal | Created | owned resource 创建成功 | ReconcileTotal{result="success"} |
| Normal | Updated | owned resource spec 变化 | ReconcileTotal{result="success"} |
| Normal | StatusUpdated | Status 字段更新 | — |
| Warning | ReconcileError | reconcile 返回 error（除 DAGValidation） | ReconcileErrors |
| Warning | FinalizerTimeout | Finalizer 清理超过 30s | ReconcileErrors{reason="FinalizerTimeout"} |

### 2.9 `main/` — Operator 启动入口

```go
package main

type OperatorConfig struct {
    MetricsAddr             string        // default ":8080"
    HealthAddr              string        // default ":8081"
    EnableLeaderElection    bool          // default true
    LeaderElectionID        string        // default "superteam-a2a-operator"
    LeaderElectionNamespace string        // default "superteam-a2a-system"
    WatchNamespace          string        // default "" (all namespaces)
    MaxConcurrentReconciles int           // default 1（每 Controller）
    MemoryDecayInterval     time.Duration // default 1h
}

func Main(cfg OperatorConfig) error  // 阻塞直到 ctx 取消

// Flags 解析（自动注册 pflag）
func RegisterFlags(fs *pflag.FlagSet) *OperatorConfig
```

**启动顺序**:
1. `LoadConfig()` 加载配置（flag > env > configmap > 默认值）
2. `observability.NewMetrics()` 注册 Prometheus
3. `mgr, _ := ctrl.NewManager(...)` 启动 controller-runtime Manager
4. 注册 4 Controller（agent / agentset / workflow / memory）
5. 注册 Watch 关系（`watches.RegisterForController`）
6. `mgr.Start(ctx)` 阻塞

---

## 3. 默认配置值（Helm `values.yaml`）

所有配置项支持三源加载（优先级：flag > env > configmap > 默认值）。

```yaml
# helm/values.yaml（Operator Core 子段）
operator:
  metricsAddr: ":8080"
  healthAddr: ":8081"
  enableLeaderElection: true
  leaderElectionID: "superteam-a2a-operator"
  leaderElectionNamespace: "superteam-a2a-system"
  watchNamespace: ""           # 空 → 全 namespace
  maxConcurrentReconciles: 1   # 每 Controller

reconcile:
  retryMaxRetries: 3
  retryBackoffBase: "1s"
  retryBackoffFactor: 2.0
  retryBackoffMax: "30s"
  retryBackoffJitter: 0.2

memoryReconciler:
  decayInterval: "1h"          # 周期触发间隔
  decayRatePerDay: 0.05        # confidence 每日衰减率（5%）
  expiringConfidenceThreshold: 0.1
  gracePeriodDays: 7           # Expired 后 GC 宽限
  reinforceAmount: 0.05        # 单次强化量
  reinforcementCountForPromote: 5  # 触发 Promotable 标记的最少强化次数

controller:
  agent:
    enable: true
  agentset:
    enable: true
  workflow:
    enable: true
  memory:
    enable: true
```

**env 映射 + 默认值表**:

| 配置 Key | 默认值 | 范围 | env 变量 | 备注 |
|----------|--------|------|---------|------|
| `operator.metricsAddr` | `:8080` | — | `OPERATOR_METRICS_ADDR` | Prometheus 暴露 |
| `operator.healthAddr` | `:8081` | — | `OPERATOR_HEALTH_ADDR` | Health/Ready probe |
| `operator.enableLeaderElection` | `true` | bool | `OPERATOR_LEADER_ELECT` | K8s 生产必须 |
| `operator.leaderElectionID` | `superteam-a2a-operator` | — | `OPERATOR_LEADER_ID` | — |
| `operator.leaderElectionNamespace` | `superteam-a2a-system` | — | `OPERATOR_LEADER_NS` | — |
| `operator.watchNamespace` | `""` | — | `OPERATOR_WATCH_NS` | 空 → all |
| `operator.maxConcurrentReconciles` | `1` | 1-10 | `OPERATOR_MAX_RECONCILES` | — |
| `reconcile.retryMaxRetries` | `3` | 0-10 | `RECONCILE_RETRIES` | — |
| `reconcile.retryBackoffBase` | `1s` | duration | `RECONCILE_BACKOFF_BASE` | 指数基数 |
| `reconcile.retryBackoffFactor` | `2.0` | float | `RECONCILE_BACKOFF_FACTOR` | — |
| `reconcile.retryBackoffMax` | `30s` | duration | `RECONCILE_BACKOFF_MAX` | 单次回退上限 |
| `reconcile.retryBackoffJitter` | `0.2` | 0-1 | `RECONCILE_BACKOFF_JITTER` | ± 百分比 |
| `memoryReconciler.decayInterval` | `1h` | 1m-24h | `MEMORY_DECAY_INTERVAL` | 周期触发 |
| `memoryReconciler.decayRatePerDay` | `0.05` | 0-1 | `MEMORY_DECAY_RATE` | 每天 5% |
| `memoryReconciler.expiringConfidenceThreshold` | `0.1` | 0-1 | `MEMORY_EXPIRE_THRESHOLD` | < 该值 → Expired |
| `memoryReconciler.gracePeriodDays` | `7` | 1-90 | `MEMORY_GRACE_DAYS` | Expired 后 GC 宽限 |
| `memoryReconciler.reinforceAmount` | `0.05` | 0-1 | `MEMORY_REINFORCE_AMT` | — |
| `memoryReconciler.reinforcementCountForPromote` | `5` | 0-100 | `MEMORY_PROMOTE_COUNT` | — |

**加载入口**:

```go
func LoadOperatorConfig() (OperatorConfig, error)
// 实现：flag → env → configmap(superteam-a2a-system/operator-config) → hardcoded default
```

---

## 4. CRD Schema 概要（Operator 注入字段）

> **本节概要描述 Operator 在 reconcile 时**主动注入**的 Status 字段；CRD Spec 字段定义 → 见 L1 Spec §2-§4 + ADR-0003 §6。

### 4.1 Status 字段（Operator 写入）

```yaml
status:
  # 通用字段（所有 CR 共享，L1 Spec §1.4）
  phase: "Pending"               # Operator 写入
  observedGeneration: 1         # Operator 同步 = metadata.generation
  conditions: [...]             # 4 类 Condition 工厂输出
  endpoints: []                  # Agent CR 特有：Operator 抓取后填入
  lastUpdated: "2026-07-23T..."
  
  # CR 特有字段（详见 L1 Spec）
  replicas: 1                   # AgentSet / Agent
  readyReplicas: 1              # AgentSet / Agent
  availableReplicas: 1          # AgentSet
  agentCard: {...}              # Agent CR：Operator 从 Pod 抓取
  taskStatuses: {...}           # Workflow CR：每个 task 的 Status
  effectiveConfidence: 0.85     # Memory CR
  reinforcedCount: 5            # Memory CR
  decayAt: "..."                # Memory CR：下次衰减时间
```

### 4.2 Operator 校验规则（CRD schema 由 controller-gen 生成）

| CR 字段 | 规则 | 来源 |
|---------|------|------|
| `Agent.spec.framework` | enum: `langchain` / `autogen` / `crewai` / `sk` / `strands` / `smolagents` / `custom` | L1 Spec §2.6 |
| `Agent.spec.card.name` | kebab-case，正则 `^[a-z][a-z0-9-]*[a-z0-9]$` | L1 Spec §2.6 |
| `Agent.spec.resources` | 必须包含 `requests` 与 `limits` | L1 Spec §2.6 |
| `AgentSet.spec.replicas` | 0-100 | L1 Spec §3.3 |
| `Workflow.spec.tasks` | ≥ 1，DAG 无环 | L1 Spec §4.3 + §4.4 |
| `Workflow.spec.tasks[].id` | kebab-case + 唯一 | L1 Spec §4.3 |
| `Workflow.spec.timeout` | 1-7200（秒） | L1 Spec §4.3 |
| `Memory.spec.content` | keys ≤ 20（ADR-0003 §5） | ADR-0003 |

**Operator 注入的特殊字段**:
- `status.endpoints[].url`: 形如 `https://<cr-name>.<namespace>.svc:<port>`
- `status.agentCard`: 从 `/.well-known/agent.json` 抓取并缓存 5 分钟

---

## 5. 控制器契约（Reconcile / Finalizer / Memory 衰减）

### 5.1 Reconcile 通用流程

```go
func (r *AgentReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    startTime := time.Now()
    defer func() {
        r.Metrics.RecordReconcile("agent", "success", time.Since(startTime))
    }()
    
    // 1. 获取 CR（不存在 → IgnoreNotFound）
    agent := &agentv1alpha1.Agent{}
    if err := r.Get(ctx, req.NamespacedName, agent); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }
    
    // 2. 处理删除
    if common.IsBeingDeleted(agent) {
        return r.reconcileDelete(ctx, agent)
    }
    
    // 3. 确保 Finalizer
    if !common.HasFinalizer(agent, common.FinalizerAgent) {
        if err := common.AddFinalizer(ctx, r.Client, agent, common.FinalizerAgent); err != nil {
            return ctrl.Result{RequeueAfter: 5 * time.Second}, err
        }
        return ctrl.Result{Requeue: true}, nil  // 添加后立即 reconcile 一次
    }
    
    // 4. Spec 差异检测（避免无变化 reconcile）
    if !r.specChanged(agent) {
        return ctrl.Result{}, nil
    }
    
    // 5. 主体 reconcile（按顺序执行 owned resource 创建）
    if err := r.reconcileDeployment(ctx, agent); err != nil {
        r.EventHelper.EmitEvent(agent, corev1.EventTypeWarning, "ReconcileError", err.Error())
        r.Metrics.RecordReconcileError("agent", "DeploymentFailed")
        return r.updateStatus(ctx, agent, "Failed", err)
    }
    if err := r.reconcileService(ctx, agent); err != nil {
        return r.updateStatus(ctx, agent, "Failed", err)
    }
    if err := r.reconcileServiceAccount(ctx, agent); err != nil {
        return r.updateStatus(ctx, agent, "Failed", err)
    }
    if err := r.reconcileRoleAndBinding(ctx, agent); err != nil {
        return r.updateStatus(ctx, agent, "Failed", err)
    }
    if err := r.reconcileAgentCard(ctx, agent); err != nil {
        return r.updateStatus(ctx, agent, "Failed", err)
    }
    
    // 6. 更新 Status（4 类 Condition 全量 set）
    return r.updateStatus(ctx, agent, "Available", nil)
}
```

### 5.2 Status 字段更新契约

每次 reconcile **必须**全量 set 4 类 Condition：

```go
func (r *AgentReconciler) updateStatus(ctx context.Context, agent *agentv1alpha1.Agent, phase string, causeErr error) (ctrl.Result, error) {
    conditions := []metav1.Condition{
        common.NewReadyCondition(metav1.ConditionTrue, "AllChecksPass", "Agent is ready"),
        common.NewProgressingCondition("ReconcileComplete", "Last reconcile completed"),
        common.NewDegradedCondition("None", "No degradation"),
        common.NewReconciledCondition(metav1.ConditionTrue, "ReconcileOK", "Reconcile succeeded"),
    }
    if causeErr != nil {
        conditions = []metav1.Condition{
            common.NewReadyCondition(metav1.ConditionFalse, "ReconcileError", causeErr.Error()),
            common.NewProgressingCondition("RetryPending", "Will retry with backoff"),
            common.NewDegradedCondition("Yes", "Agent is degraded"),
            common.NewReconciledCondition(metav1.ConditionFalse, "ReconcileError", causeErr.Error()),
        }
    }
    
    if err := r.Status.UpdateStatus(ctx, agent, phase, conditions); err != nil {
        return ctrl.Result{RequeueAfter: 1 * time.Second}, err
    }
    return ctrl.Result{}, nil
}
```

### 5.3 Finalizer 清理流程

```go
func (r *AgentReconciler) reconcileDelete(ctx context.Context, agent *agentv1alpha1.Agent) (ctrl.Result, error) {
    // 1. 列出所有 owned resource（5 类）
    deployments, _ := r.listOwnedDeployments(ctx, agent)
    services, _ := r.listOwnedServices(ctx, agent)
    serviceAccounts, _ := r.listOwnedServiceAccounts(ctx, agent)
    roles, _ := r.listOwnedRoles(ctx, agent)
    roleBindings, _ := r.listOwnedRoleBindings(ctx, agent)
    
    // 2. 并发删除
    for _, deploy := range deployments {
        if err := r.Delete(ctx, deploy); err != nil && !apierrors.IsNotFound(err) {
            return ctrl.Result{RequeueAfter: 5 * time.Second}, err
        }
    }
    // （其他 4 类类似，省略）
    
    // 3. poll 等 owned resource 真正删除（≤ 30s）
    deadline := time.Now().Add(30 * time.Second)
    for time.Now().Before(deadline) {
        if allGone() {
            break
        }
        time.Sleep(2 * time.Second)
    }
    if !allGone() {
        // 触发 FinalizerTimeout Event + 报警
        r.EventHelper.EmitEvent(agent, corev1.EventTypeWarning, "FinalizerTimeout",
            "owned resources not deleted within 30s")
        return ctrl.Result{RequeueAfter: 10 * time.Second}, common.ErrFinalizerTimeout
    }
    
    // 4. 移除 Finalizer
    if err := common.RemoveFinalizer(ctx, r.Client, agent, common.FinalizerAgent); err != nil {
        return ctrl.Result{RequeueAfter: 5 * time.Second}, err
    }
    
    // 5. K8s 自动执行原 delete
    return ctrl.Result{}, nil
}
```

**Finalizer 顺序约束**:
- 删除顺序：Deployment → Service → ServiceAccount → Role → RoleBinding（**反**创建顺序，避免短暂 Service 流量打到不存在 Pod）
- poll 间隔 2s，超时 30s（30s 后 emit `FinalizerTimeout`）

### 5.4 AgentSet replicas 数学 + Rolling update

```go
func (r *AgentSetReconciler) computeDesiredReplicas(set *AgentSet) int32 {
    if set.Spec.Replicas != nil {
        return *set.Spec.Replicas
    }
    return 1  // 默认值
}

func (r *AgentSetReconciler) applyRollingUpdate(ctx context.Context, set *AgentSet, ready int32) error {
    strategy := set.Spec.UpdateStrategy
    
    // 类型 1: RollingUpdate（默认）
    if strategy.Type == "" || strategy.Type == "RollingUpdate" {
        maxSurge := intstr.FromString("25%")          // 默认
        maxUnavailable := intstr.FromString("25%")    // 默认
        if strategy.RollingUpdate != nil {
            if strategy.RollingUpdate.MaxSurge != nil {
                maxSurge = *strategy.RollingUpdate.MaxSurge
            }
            if strategy.RollingUpdate.MaxUnavailable != nil {
                maxUnavailable = *strategy.RollingUpdate.MaxUnavailable
            }
        }
        // 应用 K8s 标准滚动更新算法
        return r.applyRollingUpdateWithParams(ctx, set, ready, maxSurge, maxUnavailable)
    }
    
    // 类型 2: OnDelete（手动）
    if strategy.Type == "OnDelete" {
        if strategy.Partition != nil {
            return r.partitionUpdate(ctx, set, *strategy.Partition)
        }
        return nil  // 等待手动删除
    }
    
    return fmt.Errorf("unknown strategy type: %s", strategy.Type)
}
```

### 5.5 Workflow 调度契约

```go
func (r *WorkflowReconciler) scheduleReadyTasks(ctx context.Context, wf *workflowv1alpha1.Workflow) error {
    for _, task := range wf.Spec.Tasks {
        // 1. 跳过已调度的
        if existingStatus := wf.Status.TaskStatuses[task.ID]; existingStatus != nil {
            if existingStatus.Phase != "" && existingStatus.Phase != "Pending" {
                continue
            }
        }
        
        // 2. 检查依赖完成
        if !r.allDepsCompleted(task.DependsOn, wf) {
            continue
        }
        
        // 3. 解析 Agent 引用
        agent, err := r.resolveAgent(ctx, task.Agent, task.AgentSet)
        if err != nil {
            return err
        }
        
        // 4. 通过 A2A Client 触发
        taskID := uuid.New().String()
        if err := r.A2AClient.SendMessage(ctx, &a2aclient.AgentRef{
            Name: agent.Name, Namespace: agent.Namespace,
        }, &a2atypes.Message{
            Role: "user",
            Parts: []a2atypes.Part{{Type: "text", Text: renderInputs(task.Inputs)}},
        }, &a2aclient.SendOptions{TaskID: taskID}); err != nil {
            return err
        }
        
        // 5. 记录状态
        wf.Status.TaskStatuses[task.ID] = &workflowv1alpha1.TaskStatus{
            Phase: "Running",
            StartedAt: metav1.Now(),
            Attempts: 1,
        }
    }
    return nil
}
```

### 5.6 Memory 衰减算法（具体实现）

> 衰减算法概要见 ADR-0003 §4.3 + L1 Spec §7.6。本节定义 **Operator 端** 周期触发实现。

```go
func (r *MemoryReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    mem := &memoryv1alpha1.Memory{}
    if err := r.Get(ctx, req.NamespacedName, mem); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }
    
    // 删除中：Finalizer 处理（不衰减）
    if common.IsBeingDeleted(mem) {
        return r.reconcileDelete(ctx, mem)
    }
    
    // 计算衰减
    newConfidence, newState, err := r.decayOne(ctx, mem)
    if err != nil {
        r.Metrics.RecordReconcileError("memory", "DecayError")
        return ctrl.Result{RequeueAfter: 1 * time.Minute}, common.ErrMemoryDecay
    }
    
    // GC Expired（过 gracePeriod）
    shouldDelete, err := r.gcExpired(ctx, mem)
    if err != nil {
        return ctrl.Result{RequeueAfter: 5 * time.Minute}, err
    }
    if shouldDelete {
        if err := r.Delete(ctx, mem); err != nil {
            return ctrl.Result{RequeueAfter: 1 * time.Minute}, err
        }
        return ctrl.Result{}, nil
    }
    
    // 更新 Status
    mem.Status.EffectiveConfidence = newConfidence
    mem.Status.DecayAt = metav1.NewTime(r.Clock.Now().Add(decayInterval))
    if err := r.Status.UpdateStatus(ctx, mem, newState, nil); err != nil {
        return ctrl.Result{RequeueAfter: 30 * time.Second}, err
    }
    
    // 指标
    r.Metrics.RecordMemoryDecay(string(mem.Spec.Scope.ScopeLevel), 
        mem.Status.Phase + "->" + newState)
    
    // 周期触发（1h 后再次 reconcile）
    return ctrl.Result{RequeueAfter: r.DecayInterval}, nil
}

// 衰减公式（每天 5% 衰减）
func (r *MemoryReconciler) decayOne(ctx context.Context, mem *Memory) (float64, string, error) {
    lastDecay := mem.Status.DecayAt
    if lastDecay.IsZero() {
        lastDecay = metav1.NewTime(mem.CreationTimestamp.Time)
    }
    
    elapsed := r.Clock.Now().Sub(lastDecay.Time)
    days := elapsed.Hours() / 24
    
    // confidence *= (1 - rate)^days
    rate := r.DecayRate  // 0.05
    newConf := mem.Status.EffectiveConfidence * math.Pow(1-rate, days)
    
    var newState string
    switch {
    case newConf >= 0.5:
        newState = "Active"
    case newConf >= r.ExpiringThreshold:  // 0.1
        newState = "Decaying"
    default:
        newState = "Expired"
    }
    
    return newConf, newState, nil
}
```

**衰减/强化/GC 公式表**:

| 操作 | 输入 | 输出 | 公式 |
|------|------|------|------|
| **decay** | lastDecay, confidence, rate=0.05 | newConfidence | `confidence × (1 - rate)^days` |
| **reinforce** | currentConfidence, amount=0.05 | newConfidence | `min(current + amount, 1.0)` |
| **expire** | newConfidence | state | `confidence < 0.1 ? "Expired" : "Active"/"Decaying"` |
| **gc** | state, lastTransition, gracePeriod=7d | shouldDelete | `state == "Expired" && now - lastTransition > gracePeriod` |
| **promote** | state, confidence, reinforcedCount, visibility | promotable flag | `confidence >= 0.85 && reinforcedCount >= 5 && visibility == scope-and-children` |

**周期触发契约**:
- 每次 Reconcile 结束**必须**返回 `Result{RequeueAfter: 1h}`（除非 CR 已被删除）
- 使用 `Clock` 接口（`clock.RealClock{}` / `clock.NewFakeClock(t0)`）以支持测试注入
- Memory **不**主动 list 全表（避免 list-watch 抖动），仅 reconcile 被 Watch 触发的单 CR
- `Promotable` 状态为 v0.1 字段值标记，**不**触发 PromotionRequest（见 L1 Spec §7.6 注释）

### 5.7 Watch 关系实现模板

```go
// 在 SetupWithManager 中注册 Watch
func (r *AgentReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        For(&agentv1alpha1.Agent{}).
        Owns(&appsv1.Deployment{}).                              // owned
        Owns(&corev1.Service{}).                                 // owned
        Owns(&corev1.ServiceAccount{}).                          // owned
        Owns(&rbacv1.Role{}).                                    // owned
        Owns(&rbacv1.RoleBinding{}).                             // owned
        Watches(
            &corev1.Secret{},
            handler.EnqueueRequestsFromMapFunc(r.findAgentsForSecret),
            builder.WithPredicates(predicate.GenerationChangedPredicate{}),
        ).
        Complete(r)
}

func (r *AgentReconciler) findAgentsForSecret(ctx context.Context, obj client.Object) []reconcile.Request {
    secret, ok := obj.(*corev1.Secret)
    if !ok { return nil }
    agents := &agentv1alpha1.AgentList{}
    if err := r.List(ctx, agents, 
        client.InNamespace(secret.Namespace),
        client.MatchingLabels{secretLabelKey: secret.Name}); err != nil {
        return nil
    }
    var reqs []reconcile.Request
    for _, a := range agents.Items {
        reqs = append(reqs, reconcile.Request{NamespacedName: types.NamespacedName{
            Name: a.Name, Namespace: a.Namespace,
        }})
    }
    return reqs
}
```

---

## 6. 测试用例骨架

> 测试目标: 单元覆盖率 ≥ 80%（宪法 §9.1）；集成测试覆盖所有 Controller 路径（§9.2）；E2E 在 kind 集群跑 hello-agent（§9.3）。

### 6.1 单元测试（按子包）

#### `common/` 包

| ID | 用例 | 期望 |
|----|------|------|
| UT-C-01 | `ReconcileError.Is` 同 Code | true |
| UT-C-02 | `AddFinalizer` 重复添加 | no-op（不重复） |
| UT-C-03 | `RemoveFinalizer` 已移除 | no-op |
| UT-C-04 | `HasFinalizer` 存在 | true |
| UT-C-05 | `NewReadyCondition` 输出格式 | type="Ready", status="True" |
| UT-C-06 | `IsRetryable(ErrReconcile)` | true |
| UT-C-07 | `IsPermanent(ErrDAGValidation)` | true |
| UT-C-08 | `ClassifyError(non-Operator)` | 包装为 ErrReconcile |
| UT-C-09 | `IsBeingDeleted` DeletionTimestamp 非空 | true |

#### `controllers/agent` 包

| ID | 用例 | 期望 |
|----|------|------|
| UT-A-01 | 创建 Agent → reconcile 创建 5 类 owned | Deploy/Service/SA/Role/RoleBinding 全部存在 |
| UT-A-02 | 删除 Agent → reconcileDelete 清理 5 类 | poll 30s 内全部 gone |
| UT-A-03 | spec 无变化 → specChanged=false | 不执行 reconcile |
| UT-A-04 | Deployment 创建失败 → status=Failed | ReconcileErrors++ + Event emit |
| UT-A-05 | Agent Card 抓取失败 → status=Failed | 同上 |
| UT-A-06 | 重试：ErrReconcile → 指数退避 | 1s/2s/4s/8s/30s |
| UT-A-07 | DAGValidation 类型：立即失败（不重试） | requeue=false |

#### `controllers/agentset` 包

| ID | 用例 | 期望 |
|----|------|------|
| UT-AS-01 | replicas=3 → 创建 3 个 Agent CR | AgentList 长度=3 |
| UT-AS-02 | replicas=0 → 保留已有，不删除 | 滚动到 0 由用户手动 |
| UT-AS-03 | replicas 减少 → RollingUpdate（MaxUnavailable=25%） | 旧 Pod 逐个 Terminate |
| UT-AS-04 | replicas 增大 → RollingUpdate（MaxSurge=25%） | 新 Pod 逐个 Pending→Running |
| UT-AS-05 | strategy=OnDelete, partition=2 → 只更新 ≥3 的 Pod | 0/1 保留旧版 |

#### `controllers/workflow` 包

| ID | 用例 | 期望 |
|----|------|------|
| UT-W-01 | DAG 含环 → ErrDAGValidation | 不调度 |
| UT-W-02 | dependsOn 引用不存在 → ErrDAGValidation | 不调度 |
| UT-W-03 | self-dependency → ErrDAGValidation | 不调度 |
| UT-W-04 | 重复 task.id → ErrDAGValidation | 不调度 |
| UT-W-05 | inputsFrom 引用不存在 → ErrDAGValidation | 不调度 |
| UT-W-06 | 全部依赖 Succeeded → 调度当前 task | A2A Client.SendMessage 调用 1 次 |
| UT-W-07 | 任意 task Failed 不可重试 → workflow=Failed | 终态 |
| UT-W-08 | 超时 → workflow=Timeout | 终态 |

#### `controllers/memory` 包

| ID | 用例 | 期望 |
|----|------|------|
| UT-M-01 | decay 0.85 × (1-0.05)^1 ≈ 0.8075 | 落在区间 |
| UT-M-02 | decay 到 0.05 → state=Expired | gracePeriod 触发后 GC |
| UT-M-03 | reinforce 0.5 + 0.05 = 0.55 | confidence 累加 |
| UT-M-04 | reinforce 1.0 + 0.05 = 1.0 | 上限截断 |
| UT-M-05 | confidence >= 0.5 → state=Active | — |
| UT-M-06 | 0.1 <= confidence < 0.5 → state=Decaying | — |
| UT-M-07 | gracePeriod 未到 → 不 GC | 保留 |
| UT-M-08 | gracePeriod 已过 → delete | CR 删除 |
| UT-M-09 | 周期触发：返回 RequeueAfter=1h | 1 小时后再次入队 |
| UT-M-10 | fakeClock 注入：1 天跳进 → decay 计算正确 | 测试时间解耦 |

#### `observability/` 包

| ID | 用例 | 期望 |
|----|------|------|
| UT-O-01 | `RecordReconcile` 累计指标 | counter+1 |
| UT-O-02 | `RecordReconcileError` 累计指标 | counter+1 |
| UT-O-03 | `SetLeaderState(true)` | gauge=1 |
| UT-O-04 | `RecordMemoryDecay("team", "Active->Decaying")` | counter+1 |
| UT-O-05 | `EmitEvent` Warning 类型 → EventRecorder 接收 | Recorder.Event 调用 1 次 |

### 6.2 集成测试（envtest）

> 使用 `sigs.k8s.io/controller-runtime/pkg/envtest` 在真实 API server + etcd 上跑完整 reconcile。

| ID | 用例 | 前置 | 期望 |
|----|------|------|------|
| IT-01 | Agent 完整生命周期 | CR apply | CR status.phase=Available，5 类 owned 创建 |
| IT-02 | Agent 删除清理 | Agent run 一次 + delete | Finalizer 清理 5 类 owned，30s 内完成 |
| IT-03 | AgentSet scale 1 → 3 | AS=1 → 改 3 | 3 个 Agent CR 创建，Pod ready |
| IT-04 | AgentSet scale 3 → 1 | AS=3 → 改 1 | 2 个 Agent CR 删除 |
| IT-05 | Workflow DAG 校验 | CR apply with cycle | reconcile 返回 ErrDAGValidation，Event emit |
| IT-06 | Workflow 调度 2 task | apply wf with 2 deps | 按依赖顺序触发 A2A SendMessage |
| IT-07 | Memory decay 周期触发 | apply mem, fake clock | 1h 后回到 reconcile，confidence 下降 |
| IT-08 | Memory gracePeriod GC | apply mem, 跳过 gracePeriod | CR 被 Delete |
| IT-09 | Leader election | 启 2 个 Operator pod | 仅 1 个为 leader，另一个 follower |
| IT-10 | Watch Secret rotation | 更新 mTLS secret | Agent 重新 reconcile |
| IT-11 | Finalizer Timeout | delete 时阻塞 owned | emit FinalizerTimeout Event，Requeue |

### 6.3 E2E（kind + hello-agent）

> 使用 `kind` 启动真实 K8s 集群 + mock LLM。

| ID | 用例 | 步骤 | 期望 |
|----|------|------|------|
| E2E-01 | hello-agent 端到端 | `kubectl apply -f hello-agent.yaml` → port-forward → curl `/.well-known/agent.json` | 200 + Agent Card JSON |
| E2E-02 | AgentSet scale 1 → 3 → 1 | `kubectl scale` | Pod 数跟随，请求分摊到 3 个 IP |
| E2E-03 | Workflow DAG 执行 | apply refund-workflow.yaml | 3 个 task 按依赖顺序完成 |
| E2E-04 | Memory 衰减全链路 | recordMemory → 跳 1 天 → queryMemory | confidence 下降，状态变化 |
| E2E-05 | Operator 升级无中断 | 滚动 Operator 镜像 | reconcile 不中断，新 leader 接管 |
| E2E-06 | Agent 删除清理完整 | kubectl delete agent | 30s 内 5 类 owned 全清 |

### 6.4 Conformance（待上游 `google-a2a/conformance` 发布后接入）

- 4 个 CRD schema 通过 `controller-gen` 校验 + kubeval 校验
- 4 个 Controller 全部通过 envtest 集成（无 skip）
- Leader election 切换时间 < 30s

---

## 7. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| L2-2-spec-draft | 2026-07-24 | 初稿：`src/operator/` 6 子包 exported API / Helm values 配置（17 项）/ 4 Controller reconcile 流程 / Finalizer-Condition-Error 契约 / Memory 衰减算法（含 5 个公式）/ 测试用例骨架（单元 39 项 + 集成 11 项 + E2E 6 项） |
| v0.1.0 | 2026-07-24 | 评审通过；版本号从 L2-2-spec-draft 升级为 v0.1.0 |

> **评审门禁（宪法 §14.4）**：本 L2 Spec 文档评审通过后，才能开始 `src/operator/` 下任一文件的具体实现，再之后才能进入 L3 文件级 Spec。

---

## 附录 A: 跨模块引用清单

| 引用 | 位置 | 状态 |
|------|------|------|
| L2-2 设计文档 | `docs/design/L2-modules/L2-operator-core.md` | ⏳ 待评审 |
| L1 Architecture | `docs/design/L1-architecture.md` §3.2 | ✅ |
| L1 Spec | `docs/spec/L1-system-spec.md` §2-§4 / §7.6 / §9-§10 | ✅ |
| ADR-0003 Memory | `docs/adr/0003-memory-design.md` §4.3 (decay) / §6 (CRD) | ✅ |
| L2-1 A2A Protocol Spec | `docs/spec/L2-module-specs/L2-a2a-protocol.md` §2.5 (client) | ✅ **v0.2.0** (2026-07-24 Python 重写 · 评审通过；模块 ID C-2 不变) |
| L2-3 Adapter Spec | `docs/spec/L2-module-specs/L2-adapter.md` | ✅ v0.1.0 (2026-07-24, 设计 32KB / 555 行 + Spec 43KB / 1044 行) |
| L2-4 Knowledge / Memory Spec | `docs/spec/L2-module-specs/L2-knowledge-memory.md` | ✅ v0.1.0 (2026-07-24, 设计 41KB / 872 行 + Spec 99KB / 2494 行) |

## 附录 B: 来自 L2 设计的 5 项开放问题 + 移交 L3

| # | 开放问题 | 移交位置 | 默认决策 |
|---|----------|----------|---------|
| 1 | reconcile 性能：Agent 数量 > 1000 时是否需要 informer 分片 | L3 Performance Spec | v0.1 不分片；监控指标暴露 queue depth |
| 2 | Workflow 表达式引擎（v0.1 静态 inputs） | L3 Future Spec | v0.1 仅静态；v0.5 引入 CEL；Operator Spec 留 stub 接口 |
| 3 | Memory 衰减频率（1h 是否合理） | 本 Spec §5.6 | 1h + 可配置（Helm values） |
| 4 | AgentSet owns Agent 时，Agent 删除如何处理 | 本 Spec §2.3 | Adoption 模式（orphanDeletion=false） |
| 5 | Operator 升级时如何避免 reconcile 抖动 | L3 Upgrade Spec | webhooks conversion + Helm pre-upgrade hook |

---

**签署**：本 L2 模块规格由起草人根据 [`docs/design/L2-modules/L2-operator-core.md` v0.1-draft](../../design/L2-modules/L2-operator-core.md) 编写，依据宪法 §14.4 待评审。
