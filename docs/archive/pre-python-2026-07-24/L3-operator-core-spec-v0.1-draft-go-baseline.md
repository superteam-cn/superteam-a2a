# L3 文件级 Spec：Operator Core（编排层文件级）

> **⚠️ ADR-0005 supersede + 归档标记（2026-07-24）**：本 v0.1-draft Spec 文档**仅 supersede Go struct / Go package / kubebuilder / controller-runtime / client-go 实现条款**；wire contract（4 Controller / CRD 状态机 / Leader Election / Finalizer / RBAC）与 v0.1 业务语义**完全继续有效**。**本 Go draft 未评审**，依据 ADR-0005 §14.2 + Phase D 实施清单，**重写前必须先归档到 `docs/archive/pre-python-2026-07-24/`**（项目当前无 `.git` 历史，禁止直接覆盖丢失）。归档后原文作历史记录；Python L3-1 在 L2-2 Python v0.2 评审通过后重写。L1 v0.2.0 已于 2026-07-24 评审通过（[`docs/reviews/l1-python-stack-migration-review.md`](../../reviews/l1-python-stack-migration-review.md)），依据 ADR-0005 Python-first 全栈迁移。
>
> **Python 重写入口**：依据 L1 v0.2.0 Architecture §3.2 + ADR-0005 §3.1 + §7，70 文件清单 → Python 包结构（`superteam_a2a.operator.handlers.*` + `superteam_a2a.operator.services.*` + `superteam_a2a.operator.models.*`）；4 Controller 完整 Go 代码契约 → Kopf handlers + 独立 async reconciler services；MemoryReconciler 60s 周期 → `@kopf.timer(interval=60.0)`
>
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-1（Operator Core，见 L1 Architecture §6 模块清单）
> **代码位置**：`src/operator/`（**v0.1-draft Go 路径，未评审 + 已废弃**）
> **版本**：v0.1-draft（2026-07-24 起草）+ ADR-0005 supersede 指针（2026-07-24）
> **状态**：⏳ v0.1-draft 起草中（**未评审**）+ ⚠️ 待归档 + 待 Python 重写
> **上游约束**：[`docs/spec/L2-module-specs/L2-operator-core.md`](../L2-module-specs/L2-operator-core.md) v0.1.0（顶部已加 ADR-0005 supersede 指针）
> **本 Spec 目的**：将 L2-2 Operator Core Spec 中的 **6 子包** + **4 Controller** + **Memory 衰减算法** + **Finalizer/Condition/Error 契约** 落地为 **文件级 Go 代码契约**——每个文件列明路径、职责、import 列表、exported 符号签名、内部 helper 列表、关联测试文件。是 L4 实施阶段（开发者打开 IDE 即可对照写代码）的直接输入。
> **配套 Spec**：[L3-5 Knowledge Service 文件级 Spec](./L3-knowledge-service.md)（待起草）/ [L3-6 Memory backend 文件级 Spec](./L3-memory-backend.md)（待起草）

---

## 0. 阅读指南

- **读者**：Operator 实施工程师（L4 编码）、Code Reviewer（PR 审查）、架构 Reviewer（设计一致性）
- **必读章节**：§1（完整文件树）/ §2（main.go 入口）/ §3-§6（4 Controller 文件清单）/ §9（common/ 共享 helper）/ §12（observability/）
- **可选章节**：§4（agentset Rolling update 细节）/ §5（workflow DAG 调度）/ §6（Memory 衰减算法实现）/ §11（admission webhook server）/ §13（测试文件映射）
- **配套阅读**：[L2-2 Operator Core Spec v0.1.0](../L2-module-specs/L2-operator-core.md) · [L1 Architecture §3.2 编排层](../../design/L1-architecture.md) · [ADR-0003 §4 Memory 衰减算法](../adr/0003-memory-design.md) · [K8s controller-runtime 文档](https://book.kubebuilder.io/) · [memory CRD types](./L3-knowledge-service.md)（仅 Operator 消费类型，定义见 L3-5）

---

## 1. 完整文件树

```
src/operator/
├── main.go                              # cmd 入口（~80 行）
├── config/                              # 配置加载（新增）
│   ├── loader.go                        # 4 层优先级加载（flag > env > configmap > default）
│   ├── loader_test.go                   # UT-CFG-01~04
│   └── defaults.go                      # 默认值常量
├── controllers/                         # 4 Controller 子包
│   ├── agent/                           # AgentReconciler
│   │   ├── reconciler.go                # Reconcile + SetupWithManager + finalizer 逻辑
│   │   ├── reconciler_test.go           # UT-A-01~07
│   │   ├── deployment.go                # reconcileDeployment: 创建/更新/删除 Deployment
│   │   ├── deployment_test.go           # UT-A-08~10
│   │   ├── service.go                   # reconcileService: 创建 Service + Endpoints
│   │   ├── service_test.go              # UT-A-11~13
│   │   ├── rbac.go                      # reconcileServiceAccount + reconcileRoleAndBinding
│   │   ├── rbac_test.go                 # UT-A-14~16
│   │   ├── agent_card.go                # reconcileAgentCard: 从 Pod 抓取 /.well-known/agent.json
│   │   ├── agent_card_test.go           # UT-A-17~19
│   │   ├── predicates.go                # specChanged + label predicate helpers
│   │   └── predicates_test.go           # UT-A-20~22
│   ├── agentset/                        # AgentSetReconciler
│   │   ├── reconciler.go                # Reconcile + SetupWithManager
│   │   ├── reconciler_test.go           # UT-AS-01~05
│   │   ├── replicas.go                  # computeDesiredReplicas + selector
│   │   ├── replicas_test.go             # UT-AS-06~08
│   │   ├── rolling.go                   # applyRollingUpdate + partition
│   │   ├── rolling_test.go              # UT-AS-09~12
│   │   └── adoption.go                  # Orphan Adoption 模式（AgentSet owns Agent）
│   ├── workflow/                        # WorkflowReconciler
│   │   ├── reconciler.go                # Reconcile + SetupWithManager
│   │   ├── reconciler_test.go           # UT-W-01~08
│   │   ├── dag.go                       # validateDAG（5 条规则）
│   │   ├── dag_test.go                  # UT-W-09~14
│   │   ├── scheduler.go                 # scheduleReadyTasks（依赖检查 + A2A SendMessage）
│   │   ├── scheduler_test.go            # UT-W-15~18
│   │   └── status.go                    # recordTaskResult + isTerminal
│   └── memory/                          # MemoryReconciler（注意：与 L3-6 memory/lifecycle/ 共享算法）
│       ├── reconciler.go                # Reconcile + SetupWithManager + finalizer
│       ├── reconciler_test.go           # UT-M-01~10
│       ├── decay.go                     # decayOne（指数衰减公式）
│       ├── decay_test.go                # UT-M-11~14
│       ├── reinforce.go                 # reinforceOne + 频次节流
│       ├── reinforce_test.go            # UT-M-15~18
│       ├── gc.go                        # gcExpired（gracePeriod GC）
│       ├── gc_test.go                   # UT-M-19~21
│       ├── promotion.go                 # isEligibleForPromotion（v0.1 仅计算）
│       ├── promotion_test.go            # UT-M-22~24
│       ├── clock.go                     # Clock 接口 + RealClock + FakeClock
│       └── periodic_worker.go           # 全集群 list + 周期 reconcile（与 L3-6 同步）
├── common/                              # 通用基础设施（6 文件）
│   ├── reconciler.go                    # Reconciler interface + Request/Result + ReconcileError
│   ├── reconciler_test.go               # UT-C-01~04
│   ├── finalizer.go                     # 4 个 Finalizer 常量 + AddFinalizer/RemoveFinalizer/HasFinalizer
│   ├── finalizer_test.go                # UT-C-05~09
│   ├── status.go                        # StatusHelper（UpdateStatus/UpdateEndpoints/IncrementObservedGeneration）
│   ├── status_test.go                   # UT-C-10~13
│   ├── conditions.go                    # 4 类 Condition 工厂函数 + 4 个 Condition Type 常量
│   ├── conditions_test.go               # UT-C-14~17
│   ├── errors.go                        # OperatorError 类型 + 5 个 sentinel + IsRetryable/IsPermanent/ClassifyError
│   ├── errors_test.go                   # UT-C-18~21
│   └── leader_election.go               # Leader election 配置 + Enable 选项
├── watches/                             # Watch 关系注册
│   ├── watches.go                       # RegisterForController + 4 类 WatchTarget
│   └── watches_test.go                  # UT-WT-01~04
├── admission/                           # admission webhook（Operator 同 Pod 部署）
│   ├── server.go                        # Webhook Server（端口 9443 + TLS cert 加载）
│   ├── server_test.go                   # UT-ADM-01~03
│   ├── memory_validator.go              # Memory admission 校验（与 L3-5 knowledge/admission 协同）
│   ├── memory_validator_test.go         # UT-ADM-04~08
│   └── tls.go                           # TLS cert 自动加载（cert-manager 颁发）
├── observability/                       # 可观测性
│   ├── metrics.go                       # 7 个 Prometheus 指标 + 6 个 Record/Set helper
│   ├── metrics_test.go                  # UT-O-01~05
│   ├── events.go                        # EventHelper + 5 类 reason 常量
│   └── events_test.go                   # UT-O-06~10
├── apis/                                # CRD Go types（**不**手写；由 controller-gen 生成）
│   ├── agent/v1alpha1/
│   │   ├── doc.go                       # +k8s:deepcopy-gen=package
│   │   ├── agent_types.go               # AgentSpec + AgentStatus + AgentCard + ...
│   │   ├── groupversion_info.go         # SchemeGroupVersion + SchemeBuilder
│   │   └── zz_generated.deepcopy.go     # controller-gen 产物
│   ├── agentset/v1alpha1/
│   │   ├── agentset_types.go            # AgentSetSpec + AgentSetStatus + RollingUpdate
│   │   └── zz_generated.deepcopy.go
│   ├── workflow/v1alpha1/
│   │   ├── workflow_types.go            # WorkflowSpec + WorkflowStatus + WorkflowTask + TaskStatus
│   │   └── zz_generated.deepcopy.go
│   └── memory/v1alpha1/                 # Memory 类型（与 L3-6 共享）
│       ├── memory_types.go              # MemorySpec + MemoryStatus + MemoryState + MemoryVisibility
│       └── zz_generated.deepcopy.go
└── deploy/                              # Helm chart（独立子目录）
    └── helm/
        ├── Chart.yaml
        ├── values.yaml                  # 与 L2-2 Spec §3 默认值一致
        ├── templates/
        │   ├── operator-deployment.yaml
        │   ├── operator-service.yaml
        │   ├── operator-serviceaccount.yaml
        │   ├── operator-role.yaml       # ClusterRole（4 CRD + 5 owned resources）
        │   ├── operator-rolebinding.yaml
        │   ├── operator-leader-election.yaml
        │   ├── operator-configmap.yaml  # 默认配置
        │   ├── operator-networkpolicy.yaml
        │   └── operator-servicemonitor.yaml
        └── tests/
            ├── operator-helm-unittest.yaml
            └── operator-helm-lint.yaml
```

**总文件数**：~70 个 Go 文件 + 5 个 YAML 模板 + 2 个 Helm 测试。

**包级别约束**：
- `apis/` **仅消费**类型，**不**生成（kubebuilder/controller-gen 从 L1 Spec 自动生成 deepcopy）
- `controllers/memory/decay.go` 等算法文件与 `src/memory/lifecycle/`（L3-6）共享代码（通过 `internal/` 共享包或 submodule 引用），避免重复实现
- `admission/` Operator 同 Pod 内嵌 webhook server（端口 9443 + cert-manager TLS）
- 测试文件命名严格 `*_test.go`，无 helpers 独立文件

---

## 2. `main.go` + `config/` 子包

### 2.1 `src/operator/main.go`

**职责**：Operator 进程入口；解析 flags + 启动 controller-runtime Manager + 注册 4 Controller + 优雅停机。

**关键结构**：

```go
// src/operator/main.go
package main

import (
    "context"
    "flag"
    "log/slog"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/spf13/pflag"
    "sigs.k8s.io/controller-runtime/pkg/manager"
    "sigs.k8s.io/controller-runtime/pkg/manager/signals"

    "superteam-a2a.io/operator/config"
    "superteam-a2a.io/operator/controllers/agent"
    "superteam-a2a.io/operator/controllers/agentset"
    "superteam-a2a.io/operator/controllers/workflow"
    "superteam-a2a.io/operator/controllers/memory"
    "superteam-a2a.io/operator/common"
    "superteam-a2a.io/operator/admission"
    "superteam-a2a.io/operator/observability"
)

func main() {
    // 1. 加载配置（flag > env > configmap > 默认值）
    cfg, err := config.Load()
    if err != nil {
        slog.Error("config load failed", "err", err)
        os.Exit(1)
    }

    // 2. 初始化日志（JSON 结构化）
    logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
    slog.SetDefault(logger)

    // 3. 初始化 Prometheus 指标
    metrics := observability.NewMetrics(prometheus.DefaultRegisterer)

    // 4. 创建 controller-runtime Manager
    mgr, err := manager.New(cfg.ManagerOptions, manager.Options{
        Scheme:                 common.Scheme,            // 注册 4 CRD scheme
        MetricsBindAddress:     cfg.MetricsAddr,          // 默认 :8080
        HealthProbeBindAddress: cfg.HealthAddr,           // 默认 :8081
        LeaderElection:         cfg.EnableLeaderElection, // 默认 true
        LeaderElectionID:       cfg.LeaderElectionID,     // 默认 "superteam-a2a-operator"
        LeaderElectionNamespace: cfg.LeaderElectionNamespace,
        WatchNamespace:         cfg.WatchNamespace,       // 默认 "" = 全 namespace
    })
    if err != nil {
        slog.Error("manager creation failed", "err", err)
        os.Exit(1)
    }

    // 5. 注册 4 Controller（按 L2-2 §2.2-§2.5）
    if err := (&agent.AgentReconciler{
        Client: mgr.GetClient(),
        Scheme: mgr.GetScheme(),
        // ... 依赖注入（Status / Finalizer / Recorder / Metrics）
    }).SetupWithManager(mgr); err != nil {
        slog.Error("agent controller setup failed", "err", err)
        os.Exit(1)
    }
    // agentset / workflow / memory 同上

    // 6. 启动 admission webhook server（同 Pod 内嵌）
    if cfg.Admission.Enabled {
        webhookServer := admission.NewServer(cfg.Admission, logger)
        if err := mgr.Add(webhookServer); err != nil {
            slog.Error("admission webhook server failed", "err", err)
            os.Exit(1)
        }
    }

    // 7. 启动 Manager（阻塞直到 ctx 取消）
    ctx := signals.SetupSignalHandler()  // 监听 SIGTERM/SIGINT
    if err := mgr.Start(ctx); err != nil {
        slog.Error("manager start failed", "err", err)
        os.Exit(1)
    }
}
```

**关键依赖**：
- `controller-runtime` v0.17+
- `pflag`（替代 stdlib flag；支持 env binding）
- `slog`（Go 1.21+ 结构化日志）
- `prometheus/client_golang`

### 2.2 `src/operator/config/loader.go`

**职责**：从 flag / env / ConfigMap / 默认值加载 OperatorConfig。

```go
// src/operator/config/loader.go
package config

import (
    "time"
    "github.com/spf13/pflag"
    "github.com/spf13/viper"
)

type OperatorConfig struct {
    // Manager 配置
    MetricsAddr             string        // 默认 ":8080"
    HealthAddr              string        // 默认 ":8081"
    EnableLeaderElection    bool          // 默认 true
    LeaderElectionID        string        // 默认 "superteam-a2a-operator"
    LeaderElectionNamespace string        // 默认 "superteam-a2a-system"
    WatchNamespace          string        // 默认 ""
    MaxConcurrentReconciles int           // 默认 1

    // Reconcile 重试
    RetryMaxRetries  int
    RetryBackoffBase time.Duration  // 默认 1s
    RetryBackoffMax  time.Duration  // 默认 30s
    RetryBackoffFactor float64      // 默认 2.0
    RetryBackoffJitter float64      // 默认 0.2

    // Memory Reconciler
    DecayInterval      time.Duration  // 默认 1h
    DecayRatePerDay    float64        // 默认 0.05
    ExpiringConfidence float64        // 默认 0.1
    GracePeriodDays    int            // 默认 7
    ReinforceAmount    float64        // 默认 0.05
    PromoteCount       int            // 默认 5

    // Admission webhook
    Admission AdmissionConfig

    // Controller enable flags
    EnableAgent    bool
    EnableAgentSet bool
    EnableWorkflow bool
    EnableMemory   bool
}

type AdmissionConfig struct {
    Enabled        bool          // 默认 true
    Port           int           // 默认 9443
    CertDir        string        // 默认 /tmp/k8s-webhook-server/serving-certs
    TimeoutSeconds int           // 默认 5
}

// Load 加载配置（4 层优先级）
func Load() (*OperatorConfig, error) {
    cfg := &OperatorConfig{}

    // 1. 应用硬编码默认值
    applyDefaults(cfg)

    // 2. flag 解析（命令行最高优先级）
    pflag.StringVar(&cfg.MetricsAddr, "metrics-addr", cfg.MetricsAddr, "Prometheus metrics bind address")
    pflag.StringVar(&cfg.HealthAddr, "health-addr", cfg.HealthAddr, "Health probe bind address")
    // ... 其余 17 个 flag（详见 L2-2 Spec §3 env 映射表）
    pflag.Parse()

    // 3. env 变量绑定（自动 viper.BindEnv）
    bindEnv(cfg)

    // 4. ConfigMap 加载（可选；如不存在则跳过）
    if cm, err := loadConfigMap(cfg.WatchNamespace, "superteam-a2a-operator-config"); err == nil {
        mergeFromConfigMap(cfg, cm)
    }

    return cfg, nil
}
```

### 2.3 `src/operator/config/defaults.go`

**职责**：集中所有默认值常量。

```go
// src/operator/config/defaults.go
package config

import "time"

const (
    DefaultMetricsAddr             = ":8080"
    DefaultHealthAddr              = ":8081"
    DefaultLeaderElectionID        = "superteam-a2a-operator"
    DefaultLeaderElectionNamespace = "superteam-a2a-system"
    DefaultWatchNamespace          = ""
    DefaultMaxConcurrentReconciles = 1

    DefaultRetryMaxRetries   = 3
    DefaultRetryBackoffBase  = 1 * time.Second
    DefaultRetryBackoffMax   = 30 * time.Second
    DefaultRetryBackoffFactor = 2.0
    DefaultRetryBackoffJitter = 0.2

    DefaultDecayInterval       = 1 * time.Hour
    DefaultDecayRatePerDay     = 0.05
    DefaultExpiringConfidence  = 0.1
    DefaultGracePeriodDays     = 7
    DefaultReinforceAmount     = 0.05
    DefaultPromoteCount        = 5

    DefaultAdmissionEnabled = true
    DefaultAdmissionPort    = 9443
    DefaultAdmissionCertDir = "/tmp/k8s-webhook-server/serving-certs"
    DefaultAdmissionTimeout = 5
)

func applyDefaults(cfg *OperatorConfig) {
    cfg.MetricsAddr = DefaultMetricsAddr
    cfg.HealthAddr = DefaultHealthAddr
    cfg.EnableLeaderElection = true
    cfg.LeaderElectionID = DefaultLeaderElectionID
    // ... 其余 17 项
}
```

### 2.4 `config/loader_test.go`

| ID | 用例 | 期望 |
|----|------|------|
| UT-CFG-01 | 无 flag 无 env 无 ConfigMap → 全为默认值 | 18 项默认值均符合 L2-2 Spec §3 |
| UT-CFG-02 | flag `--metrics-addr=:9999` 覆盖 | cfg.MetricsAddr == ":9999" |
| UT-CFG-03 | env `OPERATOR_METRICS_ADDR=:7777` 覆盖 | cfg.MetricsAddr == ":7777"（flag > env） |
| UT-CFG-04 | ConfigMap 覆盖 retry 配置 | cfg.RetryMaxRetries == 5（来自 CM） |

---

## 3. `controllers/agent/` 子包

### 3.1 `controllers/agent/reconciler.go`

**职责**：AgentReconciler 主 reconcile 循环 + SetupWithManager。

**结构**：

```go
// src/operator/controllers/agent/reconciler.go
package agent

import (
    "context"
    "time"

    "k8s.io/apimachinery/pkg/runtime"
    "k8s.io/client-go/tools/record"
    "sigs.k8s.io/controller-runtime/pkg/client"
    "sigs.k8s.io/controller-runtime/pkg/manager"
    "sigs.k8s.io/controller-runtime/pkg/reconcile"

    agentv1alpha1 "superteam-a2a.io/operator/apis/agent/v1alpha1"
    "superteam-a2a.io/operator/common"
    "superteam-a2a.io/operator/observability"
)

type AgentReconciler struct {
    client.Client
    Scheme      *runtime.Scheme
    Status      *common.StatusHelper
    Finalizer   *common.FinalizerHelper
    Recorder    record.EventRecorder
    Metrics     *observability.Metrics
    EventHelper *observability.EventHelper
    Config      *AgentConfig  // 见 §3.10
}

type AgentConfig struct {
    DefaultImageRegistry string        // 默认 "ghcr.io/superteam-a2a"
    DefaultAgentPort     int           // 默认 8080
    AgentCardCacheTTL    time.Duration // 默认 5 * time.Minute
    ReconcileTimeout     time.Duration // 默认 30s
}

func (r *AgentReconciler) Reconcile(ctx context.Context, req reconcile.Request) (reconcile.Result, error) {
    // 详见 L2-2 Spec §5.1：8 步流程（Get → Delete 检查 → Finalizer → Spec 差异 → 5 owned reconcile → Status）
}

func (r *AgentReconciler) SetupWithManager(mgr manager.Manager) error {
    // 详见 L2-2 Spec §5.7：For(Agent) + Owns 5 类 + Watches Secret
}
```

**内部 helper（私有）**：
- `specChanged(agent)`：对比 hash annotation
- `reconcileDelete(ctx, agent)`：详见 L2-2 Spec §5.3（5 owned 顺序删除 + 30s poll + FinalizerTimeout Event）
- `updateStatus(ctx, agent, phase, causeErr)`：详见 L2-2 Spec §5.2（4 类 Condition 全量 set）

### 3.2 `controllers/agent/deployment.go`

**职责**：reconcileDeployment — 创建/更新/删除 Agent 主容器 Deployment。

```go
// src/operator/controllers/agent/deployment.go
package agent

import (
    "context"
    agentv1alpha1 "superteam-a2a.io/operator/apis/agent/v1alpha1"
)

// reconcileDeployment 确保 Agent CR 对应的 Deployment 存在且 spec 一致
func (r *AgentReconciler) reconcileDeployment(ctx context.Context, agent *agentv1alpha1.Agent) error

// 内部 helper
func (r *AgentReconciler) buildDeployment(agent *agentv1alpha1.Agent) *appsv1.Deployment
func (r *AgentReconciler) listOwnedDeployments(ctx context.Context, agent *agentv1alpha1.Agent) ([]appsv1.Deployment, error)
func (r *AgentReconciler) setDeploymentOwnerRef(deploy *appsv1.Deployment, agent *agentv1alpha1.Agent) error
```

**关键实现细节**：
- 镜像：`{DefaultImageRegistry}/{spec.image}`（spec.image 为必填）
- 容器端口：8080（A2A HTTP，可配置）
- mTLS cert 挂载：`/etc/mtls/tls.crt` + `/etc/mtls/tls.key`（来自 Secret，由 cert-manager 颁发）
- resources：spec.resources 必填（requests + limits）
- securityContext：Pod Security Standard `restricted`（runAsNonRoot + readOnlyRootFilesystem + drop ALL）

### 3.3 `controllers/agent/service.go`

**职责**：reconcileService — 创建 Service（ClusterIP 暴露 A2A HTTP）+ Endpoints 同步。

```go
// src/operator/controllers/agent/service.go
package agent

func (r *AgentReconciler) reconcileService(ctx context.Context, agent *agentv1alpha1.Agent) error

// buildService ClusterIP Service（port 8080 → targetPort 8080）
func (r *AgentReconciler) buildService(agent *agentv1alpha1.Agent) *corev1.Service

// listOwnedServices
func (r *AgentReconciler) listOwnedServices(ctx context.Context, agent *agentv1alpha1.Agent) ([]corev1.Service, error)
```

**关键实现细节**：
- Service type: `ClusterIP`（不暴露 NodePort / LoadBalancer；Agent 仅 namespace 内可达）
- Ports: 8080 (A2A HTTP) + 8081 (health probe, if enabled)
- Selector: `app.kubernetes.io/name={agent-name}`（匹配 Pod template labels）
- Endpoint URL 格式：`https://{agent-name}.{namespace}.svc:8080`（Operator 写入 status.endpoints[]）

### 3.4 `controllers/agent/rbac.go`

**职责**：reconcileServiceAccount + reconcileRoleAndBinding — 创建 SA + Role + RoleBinding。

```go
// src/operator/controllers/agent/rbac.go
package agent

// reconcileServiceAccount 创建独立 SA（命名：{agent-name}-sa）
func (r *AgentReconciler) reconcileServiceAccount(ctx context.Context, agent *agentv1alpha1.Agent) error

// reconcileRoleAndBinding 创建 Role（最小权限：CRD get/list/watch）+ RoleBinding
func (r *AgentReconciler) reconcileRoleAndBinding(ctx context.Context, agent *agentv1alpha1.Agent) error

// buildServiceAccount
func (r *AgentReconciler) buildServiceAccount(agent *agentv1alpha1.Agent) *corev1.ServiceAccount

// buildRole（verbs: get/list/watch on knowledgescopes/knowledgeitems/memories）
func (r *AgentReconciler) buildRole(agent *agentv1alpha1.Agent) *rbacv1.Role

// buildRoleBinding
func (r *AgentReconciler) buildRoleBinding(agent *agentv1alpha1.Agent, sa *corev1.ServiceAccount, role *rbacv1.Role) *rbacv1.RoleBinding
```

**关键实现细节**：
- SA 命名：`{agent-name}-sa`（避免与 default SA 冲突）
- Role 权限（最小化）：
  - `knowledge.superteam-a2a.io/knowledgescopes`: get, list, watch
  - `knowledge.superteam-a2a.io/knowledgeitems`: get
  - `memory.superteam-a2a.io/memories`: get, list, watch, create, update, patch
  - `core/serviceaccounts`: get（验证 Memory.agentRef.Name）
- automountServiceAccountToken: true（Agent 需要调用 K8s API 验证 scope + SA）

### 3.5 `controllers/agent/agent_card.go`

**职责**：reconcileAgentCard — 从 Pod IP 抓取 `/.well-known/agent.json` 并缓存到 status.agentCard。

```go
// src/operator/controllers/agent/agent_card.go
package agent

import "time"

// agentCardCacheTTL 5 分钟（避免每次 reconcile 都抓取）
const agentCardCacheTTL = 5 * time.Minute

func (r *AgentReconciler) reconcileAgentCard(ctx context.Context, agent *agentv1alpha1.Agent) error

// fetchAgentCard 从 Pod IP 抓取 + 缓存校验
func (r *AgentReconciler) fetchAgentCard(ctx context.Context, agent *agentv1alpha1.Agent) (*a2a.AgentCard, error)

// cachedCardIsFresh 检查 lastQueriedAt 是否在 TTL 内
func (r *AgentReconciler) cachedCardIsFresh(agent *agentv1alpha1.Agent) bool
```

**关键实现细节**：
- 抓取路径：`http://{pod-ip}:8080/.well-known/agent.json`
- 超时：5s（agent_card.go 内 const）
- 重试：3 次（指数退避 100ms-1s）
- 缓存校验：status.agentCard.lastQueriedAt > now() - 5min → 跳过抓取
- 失败处理：抓取失败 → 标记 Agent status.phase=Failed（不阻塞 reconcile；下次 reconcile 重试）

### 3.6 `controllers/agent/predicates.go`

**职责**：specChanged + label predicate helpers。

```go
// src/operator/controllers/agent/predicates.go
package agent

import "sigs.k8s.io/controller-runtime/pkg/predicate"

// specChanged 检查 spec hash annotation 是否变化（避免无变化 reconcile）
func specChanged(obj client.Object) bool

// SpecHash 计算 spec 序列化 hash（SHA-256，hex 编码前 16 chars）
func SpecHash(obj runtime.Object) string

// LabelSelectorPredicate 匹配 labels[app.kubernetes.io/instance] == agent.Name
func LabelSelectorPredicate(agentName string) predicate.Predicate
```

**关键实现细节**：
- specChanged 通过比较 `metadata.annotations["superteam-a2a.io/spec-hash"]` 与当前 SpecHash
- SpecHash 在 Reconcile 末尾更新（写入 annotation）
- LabelSelectorPredicate 用于 AgentSet 监听 Agent CR 变化

### 3.7-3.9 控制器测试文件

| 文件 | 测试 ID | 覆盖场景 |
|------|---------|----------|
| `reconciler_test.go` | UT-A-01 ~ UT-A-07 | L2-2 Spec §6.1 agent 包测试 |
| `deployment_test.go` | UT-A-08 ~ UT-A-10 | Deployment 创建/更新/删除；image / port / resources / securityContext 字段 |
| `service_test.go` | UT-A-11 ~ UT-A-13 | Service ClusterIP / selector / port 字段 |
| `rbac_test.go` | UT-A-14 ~ UT-A-16 | SA 命名 / Role verbs / RoleBinding subject |
| `agent_card_test.go` | UT-A-17 ~ UT-A-19 | 抓取成功 / 失败重试 / 缓存命中跳过 |
| `predicates_test.go` | UT-A-20 ~ UT-A-22 | specChanged / LabelSelectorPredicate 行为 |

**总计**：Agent 子包 22 个 UT ID。

---

## 4. `controllers/agentset/` 子包

### 4.1 `controllers/agentset/reconciler.go`

**职责**：AgentSetReconciler 主 reconcile 循环 + SetupWithManager。

**结构**：

```go
// src/operator/controllers/agentset/reconciler.go
package agentset

import (
    "context"
    "sigs.k8s.io/controller-runtime/pkg/client"
    "sigs.k8s.io/controller-runtime/pkg/manager"
    "sigs.k8s.io/controller-runtime/pkg/reconcile"

    agentsetv1alpha1 "superteam-a2a.io/operator/apis/agentset/v1alpha1"
    "superteam-a2a.io/operator/common"
    "superteam-a2a.io/operator/observability"
)

type AgentSetReconciler struct {
    client.Client
    Scheme      *runtime.Scheme
    Status      *common.StatusHelper
    Metrics     *observability.Metrics
    EventHelper *observability.EventHelper
}

func (r *AgentSetReconciler) Reconcile(ctx context.Context, req reconcile.Request) (reconcile.Result, error) {
    // 1. Get AgentSet
    // 2. handle delete（Finalizer + GC owned Agent CRs）
    // 3. ensure Finalizer
    // 4. computeDesiredReplicas + selector
    // 5. list existing Agent CRs（selector 匹配）
    // 6. applyRollingUpdate（diff current vs desired）
    // 7. update status（replicas / readyReplicas / availableReplicas）
}

func (r *AgentSetReconciler) SetupWithManager(mgr manager.Manager) error {
    // For(AgentSet) + Owns(Agent) + LabelSelectorPredicate
}
```

### 4.2 `controllers/agentset/replicas.go`

**职责**：computeDesiredReplicas + selector 计算。

```go
// src/operator/controllers/agentset/replicas.go
package agentset

// computeDesiredReplicas 返回目标副本数（spec.replicas 或默认 1）
func (r *AgentSetReconciler) computeDesiredReplicas(set *agentsetv1alpha1.AgentSet) int32

// selector 计算 label selector（匹配 spec.selector + spec.template.labels）
func (r *AgentSetReconciler) selector(set *agentsetv1alpha1.AgentSet) labels.Selector

// listOwnedAgents 列出 selector 匹配的 Agent CR
func (r *AgentSetReconciler) listOwnedAgents(ctx context.Context, set *agentsetv1alpha1.AgentSet) ([]agentv1alpha1.Agent, error)
```

**关键实现细节**：
- 默认 replicas：`int32(1)`（spec.replicas 为 nil 时）
- selector 合并：`spec.selector.MatchLabels + spec.template.Labels`（两者必须一致；不一致 → 拒绝 reconcile）
- list 时使用 `client.MatchingLabels(selector.MatchLabels)` + `client.InNamespace(set.Namespace)`

### 4.3 `controllers/agentset/rolling.go`

**职责**：Rolling update 应用（K8s Deployment 同款算法）。

```go
// src/operator/controllers/agentset/rolling.go
package agentset

// applyRollingUpdate 应用 K8s 标准滚动更新算法
//   - RollingUpdate（默认）：MaxSurge 25% + MaxUnavailable 25%
//   - OnDelete：等待手动删除（可指定 partition）
func (r *AgentSetReconciler) applyRollingUpdate(ctx context.Context, set *agentsetv1alpha1.AgentSet, ready int32) error

// applyRollingUpdateWithParams 实际计算 scale up/down 步长
func (r *AgentSetReconciler) applyRollingUpdateWithParams(ctx context.Context, set *agentsetv1alpha1.AgentSet, ready int32, maxSurge, maxUnavailable intstr.IntOrString) error

// partitionUpdate 仅更新 ≥partition 的 Agent（OnDelete 策略）
func (r *AgentSetReconciler) partitionUpdate(ctx context.Context, set *agentsetv1alpha1.AgentSet, partition int32) error
```

**关键实现细节**：
- 默认 maxSurge/maxUnavailable：`intstr.FromString("25%")`
- 滚动步长公式（K8s 标准）：
  - scale up：`maxSurge` 数 → 新 Agent CR 进入 Pending
  - scale down：旧 Agent CR 标记 Terminating → `maxUnavailable` 数
- OnDelete 策略：仅当 spec.strategy.type == "OnDelete" 时启用；partition 支持

### 4.4 `controllers/agentset/adoption.go`

**职责**：Orphan Adoption 模式（AgentSet owns Agent）。

```go
// src/operator/controllers/agentset/adoption.go
package agentset

// adoptAgent 将孤立 Agent CR 加入 AgentSet ownerReferences（orphanDeletion=false）
func (r *AgentSetReconciler) adoptAgent(ctx context.Context, agent *agentv1alpha1.Agent, set *agentsetv1alpha1.AgentSet) error

// releaseAgent 从 AgentSet ownerReferences 移除（保留 Agent CR）
func (r *AgentSetReconciler) releaseAgent(ctx context.Context, agent *agentv1alpha1.Agent, set *agentsetv1alpha1.AgentSet) error
```

**关键实现细节**：
- Adopt 触发：selector 匹配但 ownerReferences 不含 AgentSet UID
- Release 触发：AgentSet.spec.selector 变化导致 Agent 不再匹配
- **不**删除 Agent（仅修改 ownerReferences）；Agent 删除由用户手动 kubectl delete

### 4.5 `controllers/agentset/reconciler_test.go` 等

| 文件 | 测试 ID | 覆盖场景 |
|------|---------|----------|
| `reconciler_test.go` | UT-AS-01 ~ UT-AS-05 | L2-2 Spec §6.1 agentset 包测试 |
| `replicas_test.go` | UT-AS-06 ~ UT-AS-08 | computeDesiredReplicas / selector / listOwnedAgents |
| `rolling_test.go` | UT-AS-09 ~ UT-AS-12 | RollingUpdate step / OnDelete / partition |

**总计**：AgentSet 子包 12 个 UT ID。

---

## 5. `controllers/workflow/` 子包

### 5.1 `controllers/workflow/reconciler.go`

**职责**：WorkflowReconciler 主 reconcile 循环 + SetupWithManager。

```go
// src/operator/controllers/workflow/reconciler.go
package workflow

import (
    "context"
    a2aclient "superteam-a2a.io/a2a/client"  // L2-1
    workflowv1alpha1 "superteam-a2a.io/operator/apis/workflow/v1alpha1"
)

type WorkflowReconciler struct {
    client.Client
    Scheme      *runtime.Scheme
    Status      *common.StatusHelper
    A2AClient   *a2aclient.Client
    Metrics     *observability.Metrics
    EventHelper *observability.EventHelper
}

func (r *WorkflowReconciler) Reconcile(ctx context.Context, req reconcile.Request) (reconcile.Result, error) {
    // 1. Get Workflow
    // 2. handle delete（无 owned resources）
    // 3. validateDAG（5 条规则；失败 → status=Failed + Event）
    // 4. scheduleReadyTasks（依赖完成 → A2A SendMessage）
    // 5. recordTaskResult + isTerminal 检查
    // 6. update status（taskStatuses / phase）
}

func (r *WorkflowReconciler) SetupWithManager(mgr manager.Manager) error {
    // For(Workflow) + Watches(Agent) + Watches(Memory)
}
```

### 5.2 `controllers/workflow/dag.go`

**职责**：validateDAG（5 条规则）。

```go
// src/operator/controllers/workflow/dag.go
package workflow

// validateDAG 5 条规则（详见 L2-2 Spec §2.4）
func (r *WorkflowReconciler) validateDAG(spec *workflowv1alpha1.WorkflowSpec) error

// hasCycle DFS + 灰色节点检测
func hasCycle(tasks []workflowv1alpha1.WorkflowTask) bool

// allDepsExist 检查所有 dependsOn 引用存在
func allDepsExist(tasks []workflowv1alpha1.WorkflowTask) bool

// hasSelfDep 检查 task.dependsOn 包含 task.id
func hasSelfDep(tasks []workflowv1alpha1.WorkflowTask) bool

// hasDuplicateID 检查 task.id 在 workflow 内唯一
func hasDuplicateID(tasks []workflowv1alpha1.WorkflowTask) bool

// allInputsValid 检查 (taskId, output) 存在 + type 一致
func allInputsValid(tasks []workflowv1alpha1.WorkflowTask) bool
```

**关键实现细节**：
- DFS 实现：邻接表（task.id → dependsOn ids）+ 颜色标记（white/gray/black）
- inputsFrom 校验：v0.1 仅静态字符串值；v0.5+ 引入 CEL 表达式
- validateDAG 失败 → 不调度任何 task + status.phase=Failed + Event emit

### 5.3 `controllers/workflow/scheduler.go`

**职责**：scheduleReadyTasks（依赖检查 + A2A SendMessage）。

```go
// src/operator/controllers/workflow/scheduler.go
package workflow

// scheduleReadyTasks 遍历所有 task；已调度或依赖未完成 → 跳过；否则触发 A2A SendMessage
func (r *WorkflowReconciler) scheduleReadyTasks(ctx context.Context, wf *workflowv1alpha1.Workflow) error

// allDepsCompleted 检查 task.DependsOn 中所有 task 的 status.phase == "Succeeded"
func (r *WorkflowReconciler) allDepsCompleted(deps []string, wf *workflowv1alpha1.Workflow) bool

// resolveAgent 解析 task.agent 或 task.agentSet → *agentv1alpha1.Agent
func (r *WorkflowReconciler) resolveAgent(ctx context.Context, ref *AgentRef, setRef *AgentSetRef) (*agentv1alpha1.Agent, error)

// renderInputs 渲染 task.Inputs 为 message parts（v0.1 静态字符串）
func renderInputs(inputs map[string]string) string
```

**关键实现细节**：
- taskID 生成：uuid.New().String()（传给 A2A SendOptions.TaskID 用于追踪）
- A2A 消息格式：`{Role: "user", Parts: [{Type: "text", Text: renderInputs(task.Inputs)}]}`
- resolveAgent：优先 task.agent（直接引用）；否则 task.agentSet（选 replicas[0]）
- renderInputs：v0.1 仅支持字符串模板；v0.5+ 引入 CEL

### 5.4 `controllers/workflow/status.go`

**职责**：recordTaskResult + isTerminal。

```go
// src/operator/controllers/workflow/status.go
package workflow

// recordTaskResult 记录单个 task 状态变化到 wf.Status.TaskStatuses
func (r *WorkflowReconciler) recordTaskResult(taskID string, status workflowv1alpha1.TaskStatus) error

// isTerminal 检查 Workflow 是否完成（全部 Succeeded 或任意 Failed 不可重试）
func (r *WorkflowReconciler) isTerminal(wf *workflowv1alpha1.Workflow) (done bool, phase string)

// checkTimeout 检查 Workflow 是否超时（spec.timeout > 0 且已超时）
func (r *WorkflowReconciler) checkTimeout(wf *workflowv1alpha1.Workflow) bool
```

**关键实现细节**：
- terminal phases：Succeeded / Failed / Timeout
- 不可重试 Failed：task.retryable=false 时立即 Failed
- 可重试 Failed：retryable=true 时 retry count +1；达到 maxRetries → Failed
- Timeout：spec.timeout 秒数（1-7200）+ status.startedAt + now() > timeout → Timeout

### 5.5 `controllers/workflow/*_test.go`

| 文件 | 测试 ID | 覆盖场景 |
|------|---------|----------|
| `reconciler_test.go` | UT-W-01 ~ UT-W-08 | L2-2 Spec §6.1 workflow 包测试 |
| `dag_test.go` | UT-W-09 ~ UT-W-14 | 5 条 DAG 校验规则（含循环 / 自依赖 / 重复 ID） |
| `scheduler_test.go` | UT-W-15 ~ UT-W-18 | 依赖检查 + A2A SendMessage 调用 |
| `status.go` 无独立测试（集成在 reconciler_test.go） | — | — |

**总计**：Workflow 子包 18 个 UT ID。

---

## 6. `controllers/memory/` 子包

### 6.1 `controllers/memory/reconciler.go`

**职责**：MemoryReconciler 主 reconcile 循环 + SetupWithManager。

```go
// src/operator/controllers/memory/reconciler.go
package memory

import (
    "context"
    "time"

    "superteam-a2a.io/operator/apis/memory/v1alpha1"
    "superteam-a2a.io/operator/common"
    "superteam-a2a.io/operator/observability"
)

type MemoryReconciler struct {
    client.Client
    Scheme       *runtime.Scheme
    Status       *common.StatusHelper
    Clock        Clock                            // 接口（RealClock / FakeClock）
    DecayEngine  DecayEngine                      // 详见 §6.2
    Reinforcer   ReinforceEngine                  // 详见 §6.3
    GCRunner     GarbageCollector                 // 详见 §6.4
    Promoter     PromotionChecker                 // 详见 §6.5
    EventHelper  *observability.EventHelper
    Metrics      *observability.Metrics
    DecayInterval time.Duration                   // 默认 1h
}

func (r *MemoryReconciler) Reconcile(ctx context.Context, req reconcile.Request) (reconcile.Result, error) {
    // 详见 L2-4 Spec §7.1：10 步流程（Get → Delete → Finalizer → decay → computePhase → GC → Status → Event → RequeueAfter 1h）
}

func (r *MemoryReconciler) SetupWithManager(mgr manager.Manager) error {
    // For(Memory) + 单 leader（MaxConcurrentReconciles=1）
}
```

**关键实现细节**：
- **不**使用 informer 分片（v0.1 内存倒排索引足够；后续 v0.5+ 评估）
- 周期触发：RequeueAfter 1h（Helm 可配 30s-300s）
- 注入 Clock 接口：测试用 FakeClock，生产用 RealClock
- Leader Election：通过 K8s Lease（详见 common/leader_election.go）

### 6.2 `controllers/memory/decay.go`

**职责**：decayOne（指数衰减公式）。

```go
// src/operator/controllers/memory/decay.go
package memory

// DecayEngine 接口
type DecayEngine interface {
    // Apply 输入 Memory CR，返回 effectiveConfidence + newState
    Apply(m *memoryv1alpha1.Memory, clock Clock) (effConf float64, state string, err error)

    // IsExpired 判断是否进入 Expired（effectiveConfidence < 阈值 + age > 上限）
    IsExpired(m *memoryv1alpha1.Memory, clock Clock, threshold float64) bool
}

// ExponentialDecayEngine 默认实现
type ExponentialDecayEngine struct {
    DecayRatePerDay float64  // 默认 0.05
}

func (e *ExponentialDecayEngine) Apply(m *memoryv1alpha1.Memory, clock Clock) (float64, string, error) {
    // 公式：effectiveConfidence = confidence × exp(-elapsed_days × decayRate)
    // 注：与 L2-4 §7.4 exp(-elapsed/decayDays) 数学等价（λ = decayRate）
}

// 内部 helper
func (e *ExponentialDecayEngine) computeDays(lastDecay time.Time, now time.Time) float64

// 状态判定
//   effectiveConfidence >= 0.5 → "Active"
//   effectiveConfidence >= ExpiringConfidence（0.1）→ "Decaying"
//   else → "Expired"
```

**关键实现细节**：
- 公式：`effConf = conf × exp(-days × rate)`（与 L2-4 Spec §7.4 数学等价）
- 状态阈值：Active ≥ 0.5 / Decaying ≥ 0.1 / Expired < 0.1
- Clock 注入：`Clock.Now()` + `Clock.Since(t)`
- 错误处理：`math.IsNaN` 或 `math.IsInf` → 返回 ErrMemoryDecay

### 6.3 `controllers/memory/reinforce.go`

**职责**：reinforceOne（confidence 累加 + 频次节流）。

```go
// src/operator/controllers/memory/reinforce.go
package memory

// ReinforceEngine 接口
type ReinforceEngine interface {
    // Apply 强化一次 Memory（confidence += amount，上限 1.0）
    Apply(m *memoryv1alpha1.Memory, amount float64) error

    // ShouldThrottle 判断是否触发节流（同 agent 24h 内最多 N 次）
    ShouldThrottle(m *memoryv1alpha1.Memory, agentName string, clock Clock) (bool, error)
}

// DefaultReinforceEngine 默认实现
type DefaultReinforceEngine struct {
    Amount             float64        // 默认 0.05
    ThrottleWindow     time.Duration  // 默认 24h
    MaxPerWindow       int            // 默认 3
    LastReinforcedAt   time.Time      // 注入最近一次时间
    ReinforcedByAgent  map[string]int // SA → 窗口内次数
}

func (r *DefaultReinforceEngine) Apply(m *memoryv1alpha1.Memory, amount float64) error {
    // 1. ShouldThrottle 检查
    // 2. newConfidence = min(m.Status.EffectiveConfidence + amount, 1.0)
    // 3. reinforcedCount++
    // 4. lastReinforcedAt = clock.Now()
}

func (r *DefaultReinforceEngine) ShouldThrottle(m *memoryv1alpha1.Memory, agentName string, clock Clock) (bool, error) {
    // 计算窗口内强化次数；超过 MaxPerWindow → true（拒绝）
}
```

### 6.4 `controllers/memory/gc.go`

**职责**：gcExpired（gracePeriod GC）。

```go
// src/operator/controllers/memory/gc.go
package memory

// GarbageCollector 接口
type GarbageCollector interface {
    // ShouldDelete 判断 Memory CR 是否应硬删（state == Expired && now - lastTransition > gracePeriod）
    ShouldDelete(m *memoryv1alpha1.Memory, clock Clock, gracePeriodDays int) bool

    // Collect 执行硬删（call client.Delete）
    Collect(ctx context.Context, m *memoryv1alpha1.Memory) error
}

// DefaultGarbageCollector 默认实现
type DefaultGarbageCollector struct {
    Client client.Client
}

func (g *DefaultGarbageCollector) ShouldDelete(m *memoryv1alpha1.Memory, clock Clock, gracePeriodDays int) bool {
    // 公式：state == "Expired" && now.Sub(m.Status.LastTransitionTime) > 7*24h
}

func (g *DefaultGarbageCollector) Collect(ctx context.Context, m *memoryv1alpha1.Memory) error {
    // client.Delete(m) + 触发 K8s Event MemoryGarbageCollected
}
```

### 6.5 `controllers/memory/promotion.go`

**职责**：isEligibleForPromotion（v0.1 仅计算不触发）。

```go
// src/operator/controllers/memory/promotion.go
package memory

// PromotionChecker 接口
type PromotionChecker interface {
    // IsEligible 判断 Memory 是否满足 promote 条件（v0.1 仅标记 status.eligibleForPromotion）
    IsEligible(m *memoryv1alpha1.Memory) bool
}

// DefaultPromotionChecker 默认实现
type DefaultPromotionChecker struct {
    MinReinforcedCount   int     // 默认 5
    MinEffectiveConf     float64 // 默认 0.85
    RequiredVisibility   MemoryVisibility  // 默认 scope-and-children
}

func (p *DefaultPromotionChecker) IsEligible(m *memoryv1alpha1.Memory) bool {
    return m.Status.EffectiveConfidence >= p.MinEffectiveConf &&
           m.Status.ReinforcedCount >= p.MinReinforcedCount &&
           m.Spec.Visibility == p.RequiredVisibility
}
```

### 6.6 `controllers/memory/clock.go`

**职责**：Clock 接口 + RealClock + FakeClock。

```go
// src/operator/controllers/memory/clock.go
package memory

// Clock 接口允许注入 fake clock 实现时间穿越单测
type Clock interface {
    Now() time.Time
    Since(t time.Time) time.Duration
}

// RealClock 真实时钟（生产环境）
type RealClock struct{}

func (RealClock) Now() time.Time                       { return time.Now() }
func (RealClock) Since(t time.Time) time.Duration      { return time.Since(t) }

// FakeClock 测试用
type FakeClock struct {
    mu  sync.RWMutex
    now time.Time
}

func NewFakeClock(t time.Time) *FakeClock              { ... }
func (f *FakeClock) Now() time.Time                    { ... }
func (f *FakeClock) Since(t time.Time) time.Duration   { ... }
func (f *FakeClock) Advance(d time.Duration)           { ... }  // 时间穿越核心
```

### 6.7 `controllers/memory/periodic_worker.go`

**职责**：全集群 list + 周期 reconcile。

```go
// src/operator/controllers/memory/periodic_worker.go
package memory

// PeriodicWorker 每 DecayInterval 触发全集群 list Memory + 加入 queue
type PeriodicWorker struct {
    client.Client
    Clock      Clock
    Interval   time.Duration  // 默认 1h（与 Reconcile.RequeueAfter 同步）
    BatchSize  int            // 默认 1000
    Logger     *slog.Logger
}

func (w *PeriodicWorker) Start(ctx context.Context) error {
    ticker := time.NewTicker(w.Interval)
    defer ticker.Stop()
    for {
        select {
        case <-ctx.Done():
            return nil
        case <-ticker.C:
            if err := w.reconcileAll(ctx); err != nil {
                w.Logger.Error("periodic reconcile failed", "err", err)
            }
        }
    }
}

func (w *PeriodicWorker) reconcileAll(ctx context.Context) error {
    // 1. listAllNamespaces
    // 2. list Memory per namespace
    // 3. 分批 batchSize
    // 4. 加入 workqueue
}
```

**关键实现细节**：
- 双触发机制：单 CR reconcile（per-CR watch）+ 全集群周期 reconcile（PeriodicWorker）
- 两者**不**冲突（PeriodicWorker 触发后所有 Memory CR 重新入队）
- Leader Election：仅 leader 执行 PeriodicWorker（避免多副本重复触发）

### 6.8 `controllers/memory/*_test.go`

| 文件 | 测试 ID | 覆盖场景 |
|------|---------|----------|
| `reconciler_test.go` | UT-M-01 ~ UT-M-10 | L2-2 Spec §6.1 memory 包测试（含 fake clock 时间穿越） |
| `decay_test.go` | UT-M-11 ~ UT-M-14 | exp(-1) ≈ 0.368 / 状态阈值 / NaN 处理 |
| `reinforce_test.go` | UT-M-15 ~ UT-M-18 | 累加 / 上限截断 / 节流 / 多 agent 独立计数 |
| `gc_test.go` | UT-M-19 ~ UT-M-21 | gracePeriod 判定 / delete 调用 / Event 触发 |
| `promotion_test.go` | UT-M-22 ~ UT-M-24 | 三条件（confidence + reinforcedCount + visibility） |
| `clock_test.go` | UT-M-25 ~ UT-M-27 | FakeClock Advance 30 天 = exp(-1) |
| `periodic_worker_test.go` | UT-M-28 ~ UT-M-30 | ticker 触发 / listAllNamespaces / batchSize |

**总计**：Memory 子包 30 个 UT ID。

---

## 7. `common/` 子包

### 7.1 `common/reconciler.go`

**职责**：Reconciler 接口 + Request/Result + ReconcileError。

```go
// src/operator/common/reconciler.go
package common

import (
    "context"
    "time"
    "k8s.io/apimachinery/pkg/types"
)

// Request 同 ctrl.Request（避免循环 import）
type Request = ctrl.Request

// Result 同 ctrl.Result
type Result = ctrl.Result

// Reconciler 接口（标准化 reconcile 入口）
type Reconciler interface {
    Reconcile(ctx context.Context, req Request) (Result, error)
    SetupWithManager(mgr ctrl.Manager) error
}

// ReconcileError 包装错误（携带 controller 标识 + retryable 标记）
type ReconcileError struct {
    Controller string
    Reason     string
    Err        error
    Retryable  bool
}

func (e *ReconcileError) Error() string  { return fmt.Sprintf("[%s] %s: %v", e.Controller, e.Reason, e.Err) }
func (e *ReconcileError) Unwrap() error  { return e.Err }
func (e *ReconcileError) Is(target error) bool {
    if t, ok := target.(*ReconcileError); ok {
        return e.Reason == t.Reason
    }
    return false
}
```

### 7.2 `common/finalizer.go`

**职责**：4 个 Finalizer 常量 + Add/Remove/Has helper。

```go
// src/operator/common/finalizer.go
package common

const (
    FinalizerAgent    = "superteam-a2a.io/agent-protection"
    FinalizerAgentSet = "superteam-a2a.io/agentset-protection"
    FinalizerWorkflow = "superteam-a2a.io/workflow-protection"
    FinalizerMemory   = "superteam-a2a.io/memory-protection"
)

// FinalizerHelper 封装 finalizer 操作
type FinalizerHelper struct {
    Client client.Client
}

// AddFinalizer 幂等添加
func (h *FinalizerHelper) AddFinalizer(ctx context.Context, obj client.Object, finalizer string) error {
    if HasFinalizer(obj, finalizer) {
        return nil
    }
    controllerutil.AddFinalizer(obj, finalizer)
    return h.Client.Update(ctx, obj)
}

// RemoveFinalizer 幂等移除
func (h *FinalizerHelper) RemoveFinalizer(ctx context.Context, obj client.Object, finalizer string) error {
    if !HasFinalizer(obj, finalizer) {
        return nil
    }
    controllerutil.RemoveFinalizer(obj, finalizer)
    return h.Client.Update(ctx, obj)
}

// HasFinalizer 检查
func HasFinalizer(obj client.Object, finalizer string) bool {
    return controllerutil.ContainsFinalizer(obj, finalizer)
}

// IsBeingDeleted 检查 DeletionTimestamp
func IsBeingDeleted(obj client.Object) bool {
    return !obj.GetDeletionTimestamp().IsZero()
}
```

### 7.3 `common/status.go`

**职责**：StatusHelper（UpdateStatus / UpdateEndpoints / IncrementObservedGeneration）。

```go
// src/operator/common/status.go
package common

type StatusHelper struct {
    Client client.Client
}

// UpdateStatus 原子更新 Status 子资源（不触发 reconcile 风暴）
func (h *StatusHelper) UpdateStatus(ctx context.Context, obj client.Object, phase string, conditions []metav1.Condition, opts ...StatusOpt) error {
    // 1. 应用 opts（WithRetry / WithBackoff）
    // 2. obj.Status.Phase = phase
    // 3. obj.Status.Conditions = conditions（全量 set）
    // 4. obj.Status.ObservedGeneration = obj.GetGeneration()
    // 5. retryWithBackoff: client.Status().Update()
}

// UpdateEndpoints 仅更新 Endpoints（Agent CR 特有）
func (h *StatusHelper) UpdateEndpoints(ctx context.Context, agent *agentv1alpha1.Agent, endpoints []Endpoint) error {
    // 1. agent.Status.Endpoints = endpoints
    // 2. client.Status().Update()
}

// IncrementObservedGeneration 同步 observedGeneration = metadata.generation
func (h *StatusHelper) IncrementObservedGeneration(ctx context.Context, obj client.Object) error

type StatusOpt func(*statusOpts)
func WithRetry(r int) StatusOpt              // 默认 3
func WithBackoff(d time.Duration) StatusOpt  // 默认 100ms
```

### 7.4 `common/conditions.go`

**职责**：4 类 Condition 工厂函数 + 4 个 Condition Type 常量。

```go
// src/operator/common/conditions.go
package common

import metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

type Condition = metav1.Condition

const (
    ConditionReady       = "Ready"
    ConditionProgressing = "Progressing"
    ConditionDegraded    = "Degraded"
    ConditionReconciled  = "Reconciled"
)

// NewReadyCondition 工厂
func NewReadyCondition(status metav1.ConditionStatus, reason, message string) Condition {
    return Condition{
        Type: ConditionReady,
        Status: status,
        Reason: reason,
        Message: message,
        LastTransitionTime: metav1.Now(),
    }
}

// NewProgressingCondition / NewDegradedCondition / NewReconciledCondition 类似
```

### 7.5 `common/errors.go`

**职责**：OperatorError 类型 + 5 个 sentinel + IsRetryable / IsPermanent / ClassifyError。

```go
// src/operator/common/errors.go
package common

import stderr "errors"

type OperatorError struct {
    Code      int
    Reason    string
    Message   string
    Component string
    Cause     error
}

func (e *OperatorError) Error() string  { ... }
func (e *OperatorError) Unwrap() error  { return e.Cause }
func (e *OperatorError) Is(target error) bool {
    if t, ok := target.(*OperatorError); ok {
        return e.Code == t.Code
    }
    return false
}

// 5 个 sentinel
var (
    ErrReconcile         = &OperatorError{Code: 1001, Reason: "ReconcileError"}
    ErrFinalizerTimeout  = &OperatorError{Code: 1002, Reason: "FinalizerTimeout"}
    ErrOwnedResourceLeak = &OperatorError{Code: 1003, Reason: "OwnedResourceLeak"}
    ErrDAGValidation     = &OperatorError{Code: 1004, Reason: "DAGValidationError"}
    ErrMemoryDecay       = &OperatorError{Code: 1005, Reason: "MemoryDecayError"}
)

// IsRetryable Code ∈ {1001, 1005}
func IsRetryable(err error) bool

// IsPermanent Code ∈ {1004}
func IsPermanent(err error) bool

// ClassifyError 包装任意 error 为 OperatorError
func ClassifyError(component string, err error) *OperatorError

// handleReconcileError 错误处理优先级（详见 L2-2 Spec §2.1.5）
func handleReconcileError(err error) (ctrl.Result, error)
```

### 7.6 `common/leader_election.go`

**职责**：Leader election 配置 + Enable 选项。

```go
// src/operator/common/leader_election.go
package common

// LeaderElectionConfig K8s Lease 资源配置
type LeaderElectionConfig struct {
    Enabled      bool          // 默认 true
    ID           string        // 默认 "superteam-a2a-operator"
    Namespace    string        // 默认 "superteam-a2a-system"
    LeaseDuration time.Duration // 默认 15s
    RenewDeadline time.Duration // 默认 10s
    RetryPeriod   time.Duration // 默认 2s
}

// ApplyToManager 应用 Leader Election 到 controller-runtime Manager
func (c *LeaderElectionConfig) ApplyToManager(mgr manager.Manager, componentName string) error {
    // 使用 mgr.Options.LeaderElection + LeaderElectionResourceLock (Lease)
}
```

### 7.7 `common/*_test.go`

| 文件 | 测试 ID | 覆盖场景 |
|------|---------|----------|
| `reconciler_test.go` | UT-C-01 ~ UT-C-04 | Reconciler interface / Request / Result / ReconcileError.Is |
| `finalizer_test.go` | UT-C-05 ~ UT-C-09 | AddFinalizer / RemoveFinalizer / HasFinalizer / IsBeingDeleted |
| `status_test.go` | UT-C-10 ~ UT-C-13 | UpdateStatus / UpdateEndpoints / WithRetry / WithBackoff |
| `conditions_test.go` | UT-C-14 ~ UT-C-17 | 4 类 Condition 工厂输出 |
| `errors_test.go` | UT-C-18 ~ UT-C-21 | OperatorError / 5 sentinel / IsRetryable / IsPermanent |

**总计**：common 子包 21 个 UT ID。

---

## 8. `watches/` 子包

### 8.1 `watches/watches.go`

**职责**：RegisterForController + 4 类 WatchTarget。

```go
// src/operator/watches/watches.go
package watches

import "sigs.k8s.io/controller-runtime/pkg/builder"

type WatchTarget string
const (
    WatchAgent     WatchTarget = "agent"
    WatchAgentSet  WatchTarget = "agentset"
    WatchWorkflow  WatchTarget = "workflow"
    WatchMemory    WatchTarget = "memory"
)

// RegisterForController 注册 Controller 的 Watch 关系
// 详见 L2-2 Spec §2.6 + §5.7
func RegisterForController(b *builder.Builder, target WatchTarget) error {
    switch target {
    case WatchAgent:
        // Owns(Deployment / Service / ServiceAccount / Role / RoleBinding)
        // Watches(Secret with predicate.GenerationChangedPredicate)
    case WatchAgentSet:
        // Owns(Agent with predicate.LabelMatchPredicate)
    case WatchWorkflow:
        // Watches(Agent + Memory with predicate.GenerationChangedPredicate)
    case WatchMemory:
        // 仅 For(Memory)；无外部 watches
    }
}

// Predicate helpers
type Predicate func(client.Object) bool

func PredicateForGenerationChange(obj client.Object) bool {
    return obj.GetGeneration() != getOldGeneration(obj)
}

func PredicateForLabelChange(labelKey string) Predicate {
    return func(obj client.Object) bool {
        return getOldLabels(obj)[labelKey] != obj.GetLabels()[labelKey]
    }
}
```

### 8.2 `watches/watches_test.go`

| ID | 覆盖场景 |
|----|----------|
| UT-WT-01 | RegisterForController(WatchAgent) 包含 5 类 Owns + 1 类 Watches |
| UT-WT-02 | RegisterForController(WatchAgentSet) 仅 Owns(Agent) |
| UT-WT-03 | PredicateForGenerationChange |
| UT-WT-04 | PredicateForLabelChange |

---

## 9. `admission/` 子包

### 9.1 `admission/server.go`

**职责**：Webhook Server（端口 9443 + TLS cert 加载）。

```go
// src/operator/admission/server.go
package admission

import (
    "context"
    "net/http"

    "sigs.k8s.io/controller-runtime/pkg/manager"
    "sigs.k8s.io/controller-runtime/pkg/webhook"
)

const (
    DefaultPort       = 9443
    DefaultCertDir    = "/tmp/k8s-webhook-server/serving-certs"
    DefaultTimeoutSec = 5
)

// Server admission webhook server（嵌入 Operator 同 Pod）
type Server struct {
    Port         int
    CertDir      string
    TimeoutSec   int
    Validator    *MemoryValidator  // 详见 §9.2
    TLS          *TLSLoader       // 详见 §9.4
    Logger       *slog.Logger
}

func NewServer(cfg config.AdmissionConfig, logger *slog.Logger) *Server

// Start 实现 manager.Runnable 接口（mgr.Add(server) 时调用）
func (s *Server) Start(ctx context.Context) error {
    // 1. 加载 TLS cert（s.TLS.Load()）
    // 2. 创建 http.Server（端口 s.Port + TLS）
    // 3. 注册 /validate-memory handler（s.Validator.Handle）
    // 4. 启动 HTTP server
    // 5. <-ctx.Done() → Shutdown
}

func (s *Server) NeedLeaderElection() bool { return false }  // 所有副本都运行 webhook
```

**关键实现细节**：
- TLS cert 由 cert-manager 颁发（MountPath: `/tmp/k8s-webhook-server/serving-certs/tls.crt` + `tls.key`）
- 所有 Operator 副本都运行 webhook server（不参与 Leader Election）
- 超时：5s（Helm 可配 1-30s）

### 9.2 `admission/memory_validator.go`

**职责**：Memory admission 校验（与 L3-5 knowledge/admission 协同部署一份）。

```go
// src/operator/admission/memory_validator.go
package admission

import (
    "context"
    "net/http"

    admissionv1 "k8s.io/api/admission/v1"
    memoryv1alpha1 "superteam-a2a.io/operator/apis/memory/v1alpha1"
)

// MemoryValidator Memory admission 校验（详见 L2-4 Spec §5.2）
type MemoryValidator struct {
    KubeClient    kubernetes.Interface
    ScopeResolver scope.InheritanceResolver
    Logger        *slog.Logger
}

// Handle HTTP handler（路由 /validate-memory）
func (v *MemoryValidator) Handle(w http.ResponseWriter, r *http.Request) {
    // 1. 解析 AdmissionReview
    // 2. 提取 Memory CR（admission.Request.Object）
    // 3. ValidateCreate / ValidateUpdate
    // 4. 返回 AdmissionResponse（Allowed / Denied + Status）
}

// ValidateCreate 7 条规则（详见 L2-4 Spec §5.2）
func (v *MemoryValidator) ValidateCreate(ctx context.Context, m *memoryv1alpha1.Memory) error {
    // 1. agentRef.Kind == ServiceAccount（拒绝 User/Group）
    // 2. agentRef.Name 对应 SA 存在
    // 3. scopeRef 对应 KS 存在
    // 4. sourceKnowledgeRef 若存在 → KI 存在 + scope 一致
    // 5. visibility == agent-private 必须 agentRef.Name != ""
    // 6. decayDays ∈ [0, 3650]
    // 7. content KV 数 ∈ [1, 20]
}

// ValidateUpdate 增量校验（spec 变化触发）
func (v *MemoryValidator) ValidateUpdate(ctx context.Context, old, new *memoryv1alpha1.Memory) error
```

### 9.3 `admission/server_test.go` + `admission/memory_validator_test.go`

| 文件 | 测试 ID | 覆盖场景 |
|------|---------|----------|
| `server_test.go` | UT-ADM-01 ~ UT-ADM-03 | TLS 加载 / HTTP handler 注册 / Shutdown 优雅 |
| `memory_validator_test.go` | UT-ADM-04 ~ UT-ADM-08 | 7 条 ValidateCreate 规则 |

---

## 10. `observability/` 子包

### 10.1 `observability/metrics.go`

**职责**：7 个 Prometheus 指标 + 6 个 Record/Set helper。

```go
// src/operator/observability/metrics.go
package observability

import "github.com/prometheus/client_golang/prometheus"

type Metrics struct {
    ReconcileTotal      *prometheus.CounterVec
    ReconcileDuration   *prometheus.HistogramVec
    ReconcileErrors     *prometheus.CounterVec
    WorkQueueDepth      *prometheus.GaugeVec
    LeaderElectionState *prometheus.GaugeVec
    OwnedResources      *prometheus.GaugeVec
    MemoryDecayTotal    *prometheus.CounterVec
}

// NewMetrics 注册 7 个指标到 Registerer
func NewMetrics(reg prometheus.Registerer) *Metrics

// RecordReconcile counter+1 + histogram observe
func (m *Metrics) RecordReconcile(controller string, result string, duration time.Duration)

// RecordReconcileError counter+1
func (m *Metrics) RecordReconcileError(controller string, reason string)

// SetLeaderState gauge=0/1
func (m *Metrics) SetLeaderState(controller string, isLeader bool)

// SetOwnedResources gauge
func (m *Metrics) SetOwnedResources(controller string, kind string, count int)

// RecordMemoryDecay counter+1（scope + transition）
func (m *Metrics) RecordMemoryDecay(scope string, transition string)

// RecordWorkQueueDepth gauge（定期 poll workqueue）
func (m *Metrics) RecordWorkQueueDepth(controller string, depth int)
```

**指标命名规范**（宪法 §7.1 `superteam_*` 前缀）：

| 指标名 | 类型 | 标签 | 单位 |
|--------|------|------|------|
| `supteam_operator_reconcile_total` | Counter | `controller, result` | 个 |
| `supteam_operator_reconcile_duration_seconds` | Histogram | `controller` | 秒 |
| `supteam_operator_reconcile_errors_total` | Counter | `controller, reason` | 个 |
| `supteam_operator_workqueue_depth` | Gauge | `controller` | 个 |
| `supteam_operator_leader_election_state` | Gauge | `controller` | 0/1 |
| `supteam_operator_owned_resources` | Gauge | `controller, kind` | 个 |
| `supteam_operator_memory_decay_total` | Counter | `scope, transition` | 个 |

### 10.2 `observability/events.go`

**职责**：EventHelper + 5 类 reason 常量。

```go
// src/operator/observability/events.go
package observability

import "k8s.io/client-go/tools/record"

type EventHelper struct {
    Recorder record.EventRecorder
}

const (
    EventReasonCreated          = "Created"
    EventReasonUpdated          = "Updated"
    EventReasonStatusUpdated    = "StatusUpdated"
    EventReasonReconcileError   = "ReconcileError"
    EventReasonFinalizerTimeout = "FinalizerTimeout"
)

// EmitEvent 统一发射接口
func (h *EventHelper) EmitEvent(obj client.Object, eventType, reason, message string) {
    h.Recorder.Event(obj, eventType, reason, message)
}
```

### 10.3 `observability/*_test.go`

| 文件 | 测试 ID | 覆盖场景 |
|------|---------|----------|
| `metrics_test.go` | UT-O-01 ~ UT-O-05 | 7 个指标注册 + Record/Set 调用 |
| `events_test.go` | UT-O-06 ~ UT-O-10 | 5 类 reason 常量 + EmitEvent 调用 |

---

## 11. `apis/` 子包（**不**手写）

### 11.1 文件清单

```
src/operator/apis/
├── agent/v1alpha1/
│   ├── doc.go                              # +k8s:deepcopy-gen=package
│   ├── agent_types.go                      # AgentSpec + AgentStatus + AgentCard + ...
│   ├── groupversion_info.go                # SchemeGroupVersion + SchemeBuilder
│   └── zz_generated.deepcopy.go            # controller-gen 产物
├── agentset/v1alpha1/
│   ├── agentset_types.go                   # AgentSetSpec + AgentSetStatus + RollingUpdate
│   ├── groupversion_info.go
│   └── zz_generated.deepcopy.go
├── workflow/v1alpha1/
│   ├── workflow_types.go                   # WorkflowSpec + WorkflowStatus + WorkflowTask + TaskStatus
│   ├── groupversion_info.go
│   └── zz_generated.deepcopy.go
└── memory/v1alpha1/
    ├── memory_types.go                     # MemorySpec + MemoryStatus + MemoryState + MemoryVisibility
    ├── groupversion_info.go
    └── zz_generated.deepcopy.go
```

**关键约束**：
- `apis/` 全部**由 controller-gen 自动生成**（`make generate`）
- Operator 代码**仅消费类型**（`import`），**不修改**类型定义
- 类型定义源头：[L1 Spec §2-§4](../L1-system-spec.md) + [ADR-0003 §6](../adr/0003-memory-design.md)

### 11.2 类型快速参考（仅消费侧）

```go
// 仅展示 Operator 消费的关键字段（非完整定义）

// Agent CR
type AgentSpec struct {
    Image       string                  // 必填
    Framework   string                  // 必填
    Card        AgentCard               // 必填
    Resources   ResourceRequirements    // 必填
    Replicas    *int32                  // 默认 1
    // ... 详见 L1 Spec §2.6
}

// AgentSet CR
type AgentSetSpec struct {
    Replicas       *int32
    Selector       LabelSelector
    Template       AgentTemplate
    UpdateStrategy AgentSetUpdateStrategy
    // ... 详见 L1 Spec §3.3
}

// Workflow CR
type WorkflowSpec struct {
    Tasks  []WorkflowTask
    Timeout int32  // 1-7200 秒
    // ... 详见 L1 Spec §4.3
}

// Memory CR
type MemorySpec struct {
    ScopeRef  ScopeReference
    AgentRef  AgentReference
    Content   map[string]string
    Summary   string
    Confidence float64
    DecayDays  int32
    Visibility MemoryVisibility
    // ... 详见 L2-4 Spec §3.3
}
```

---

## 12. 测试文件映射总表

| 测试文件 | 测试 ID 范围 | 测试数量 |
|---------|-------------|---------|
| `config/loader_test.go` | UT-CFG-01 ~ UT-CFG-04 | 4 |
| `controllers/agent/reconciler_test.go` | UT-A-01 ~ UT-A-07 | 7 |
| `controllers/agent/deployment_test.go` | UT-A-08 ~ UT-A-10 | 3 |
| `controllers/agent/service_test.go` | UT-A-11 ~ UT-A-13 | 3 |
| `controllers/agent/rbac_test.go` | UT-A-14 ~ UT-A-16 | 3 |
| `controllers/agent/agent_card_test.go` | UT-A-17 ~ UT-A-19 | 3 |
| `controllers/agent/predicates_test.go` | UT-A-20 ~ UT-A-22 | 3 |
| `controllers/agentset/reconciler_test.go` | UT-AS-01 ~ UT-AS-05 | 5 |
| `controllers/agentset/replicas_test.go` | UT-AS-06 ~ UT-AS-08 | 3 |
| `controllers/agentset/rolling_test.go` | UT-AS-09 ~ UT-AS-12 | 4 |
| `controllers/workflow/reconciler_test.go` | UT-W-01 ~ UT-W-08 | 8 |
| `controllers/workflow/dag_test.go` | UT-W-09 ~ UT-W-14 | 6 |
| `controllers/workflow/scheduler_test.go` | UT-W-15 ~ UT-W-18 | 4 |
| `controllers/memory/reconciler_test.go` | UT-M-01 ~ UT-M-10 | 10 |
| `controllers/memory/decay_test.go` | UT-M-11 ~ UT-M-14 | 4 |
| `controllers/memory/reinforce_test.go` | UT-M-15 ~ UT-M-18 | 4 |
| `controllers/memory/gc_test.go` | UT-M-19 ~ UT-M-21 | 3 |
| `controllers/memory/promotion_test.go` | UT-M-22 ~ UT-M-24 | 3 |
| `controllers/memory/clock_test.go` | UT-M-25 ~ UT-M-27 | 3 |
| `controllers/memory/periodic_worker_test.go` | UT-M-28 ~ UT-M-30 | 3 |
| `common/reconciler_test.go` | UT-C-01 ~ UT-C-04 | 4 |
| `common/finalizer_test.go` | UT-C-05 ~ UT-C-09 | 5 |
| `common/status_test.go` | UT-C-10 ~ UT-C-13 | 4 |
| `common/conditions_test.go` | UT-C-14 ~ UT-C-17 | 4 |
| `common/errors_test.go` | UT-C-18 ~ UT-C-21 | 4 |
| `watches/watches_test.go` | UT-WT-01 ~ UT-WT-04 | 4 |
| `admission/server_test.go` | UT-ADM-01 ~ UT-ADM-03 | 3 |
| `admission/memory_validator_test.go` | UT-ADM-04 ~ UT-ADM-08 | 5 |
| `observability/metrics_test.go` | UT-O-01 ~ UT-O-05 | 5 |
| `observability/events_test.go` | UT-O-06 ~ UT-O-10 | 5 |
| **合计** | — | **122** |

**集成测试（envtest）**（L2-2 Spec §6.2 IT-01 ~ IT-11）：11 个
**E2E 测试（kind）**（L2-2 Spec §6.3 E2E-01 ~ E2E-06）：6 个

**总计**：122 UT + 11 IT + 6 E2E = **139 测试 ID**

---

## 13. 关联部署文件

### 13.1 `deploy/helm/values.yaml` Operator 段

完整 values 见 L2-2 Spec §3；本节列出**仅 Operator 部署相关**的字段。

### 13.2 `deploy/helm/templates/` 模板

| 模板 | 职责 |
|------|------|
| `operator-deployment.yaml` | Deployment（replicas 默认 1）+ container image + env + liveness / readiness probe |
| `operator-service.yaml` | Service（ClusterIP 暴露 metrics 8080 + health 8081）|
| `operator-serviceaccount.yaml` | SA 命名 `superteam-a2a-operator` |
| `operator-role.yaml` | ClusterRole（4 CRD + 5 owned resources + ServiceAccount + Secret + Role + RoleBinding + Lease + Event + Pod）|
| `operator-rolebinding.yaml` | ClusterRoleBinding → SA |
| `operator-leader-election.yaml` | Lease 资源（leader-election-id） |
| `operator-configmap.yaml` | 默认配置（OperatorConfig） |
| `operator-networkpolicy.yaml` | NetworkPolicy（ingress 允许 K8s API + 8443 webhook；egress 允许 K8s API + OTel）|
| `operator-servicemonitor.yaml` | ServiceMonitor（Prometheus scrape metrics）|

### 13.3 RBAC 最小权限（ClusterRole）

```yaml
# deploy/helm/templates/operator-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: superteam-a2a-operator
rules:
# 4 CRD
- apiGroups: ["agents.superteam-a2a.io"]
  resources: ["agents", "agentsets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["workflows.superteam-a2a.io"]
  resources: ["workflows"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["memory.superteam-a2a.io"]
  resources: ["memories"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["knowledge.superteam-a2a.io"]
  resources: ["knowledgescopes", "knowledgeitems"]
  verbs: ["get", "list", "watch"]
# 5 owned resources
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["services", "serviceaccounts", "secrets", "pods"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["roles", "rolebindings"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
# Lease (leader election)
- apiGroups: ["coordination.k8s.io"]
  resources: ["leases"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
# Events
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create", "patch", "update"]
# Webhook (admission)
- apiGroups: ["admissionregistration.k8s.io"]
  resources: ["mutatingwebhookconfigurations", "validatingwebhookconfigurations"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

---

## 14. 变更记录

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| v0.1-draft | 2026-07-24 | 初稿：~70 文件清单 + 4 Controller reconcile 完整 Go 代码契约 + 4 common helper 接口签名 + Memory 衰减算法实现 + admission webhook 部署 + 7 指标 + 5 类 Event + 122 UT + 11 IT + 6 E2E = 139 测试 ID + 9 Helm 模板 + RBAC ClusterRole 完整 | Claude Code（会话 cont14） |

---

## 附录 A：跨模块引用

| 引用对象 | 位置 | 用途 |
|----------|------|------|
| L2-2 Operator Core Spec v0.1.0 | [docs/spec/L2-module-specs/L2-operator-core.md](../L2-module-specs/L2-operator-core.md) | 上游 Spec（本文件级 Spec 是其落地） |
| L2-2 Operator Core 设计 v0.1.0 | [docs/design/L2-modules/L2-operator-core.md](../../design/L2-modules/L2-operator-core.md) | 设计意图参考 |
| L2-2 Operator Core 评审 | [docs/reviews/l2-2-operator-core-review.md](../../reviews/l2-2-operator-core-review.md) | 评审结论 |
| L1 Architecture §3.2 编排层 | [docs/design/L1-architecture.md](../../design/L1-architecture.md) | Operator 在 5 层架构中位置 |
| L1 Spec §2-§4 | [docs/spec/L1-system-spec.md](../L1-system-spec.md) | 4 CRD 字段定义 |
| ADR-0003 Memory §4.3 | [docs/adr/0003-memory-design.md](../../adr/0003-memory-design.md) | Memory 衰减算法数学公式 |
| L2-1 A2A Protocol Spec §2.5 | [docs/spec/L2-module-specs/L2-a2a-protocol.md](../L2-module-specs/L2-a2a-protocol.md) | a2aclient.SendMessage（Workflow 调用） |
| L2-3 Adapter Spec | [docs/spec/L2-module-specs/L2-adapter.md](../L2-module-specs/L2-adapter.md) | Agent CR spec.adapter 字段（Operator 创建 Deployment 时引用） |
| L2-4 Knowledge / Memory Spec §7 | [docs/spec/L2-module-specs/L2-knowledge-memory.md](../L2-module-specs/L2-knowledge-memory.md) | Memory 衰减/强化/GC 算法详细规格（与本文件 decay.go 共享） |
| L3-5 Knowledge Service 文件级 Spec | [docs/spec/L3-file-specs/L3-knowledge-service.md](./L3-knowledge-service.md) | Knowledge admission webhook 协同部署 |
| 宪法 §3.1 分层 / §3.2 Operator 模式 | [CONSTITUTION.md](../../../CONSTITUTION.md) | 架构红线 |
| 宪法 §7 可观测性 | 同上 | Prometheus / OTel / Event 强制 |
| 宪法 §9 测试策略 | 同上 | ≥80% 覆盖率 + envtest + E2E |
| 宪法 §11 API 兼容性 | 同上 | CRD 字段永久承诺 |

---

## 附录 B：开放问题（移交 L4 实施）

| # | 问题 | 默认决策 | 待确认 |
|---|------|----------|--------|
| **B.1** | Operator 是否需要包含 KnowledgeScope/Item controllers（与 L2-4 Knowledge Service 拆分）？ | v0.1 不包含（Operator 仅 4 controllers；Knowledge admission + controllers 由 L2-4 Knowledge Service 提供）；L3-5 详细定义 | 用户 |
| **B.2** | MemoryReconciler 周期 1h 是否过短/过长？ | 1h 默认 + Helm 可配（30s-300s）；参考 L2-2 Spec §3 | 用户 |
| **B.3** | PeriodicWorker 与单 CR reconcile 是否双触发？ | 双触发（PeriodicWorker 全集群 + 单 CR watch），两者不冲突（PeriodicWorker 触发后所有 Memory CR 重新入队）；仅 leader 执行 | 用户 |
| **B.4** | admission webhook server 是否参与 Leader Election？ | 不参与（所有 Operator 副本都运行 webhook server，确保 webhook 高可用） | 用户 |
| **B.5** | Operator 是否需要 HPA（水平扩展）？ | v0.1 不需要（单副本足够 100 个 Agent CR）；v0.5+ 评估（informer 分片 + 多副本） | 用户 |
| **B.6** | status.endpoints 频繁更新是否触发 reconcile 风暴？ | 优化：仅在 Service / Endpoint 变化时更新；UpdateEndpoints 使用 client.Status().Update() 避免 spec hash 变化 | 用户 |
| **B.7** | specChanged 通过 hash annotation 还是 generation？ | hash annotation（SHA-256 前 16 chars）；更精确（generation 1 步变化但 spec 可能不变） | 用户 |

---

## 签署

本 L3 文件级 Spec 由起草人根据 [L2-2 Operator Core Spec v0.1.0](../L2-module-specs/L2-operator-core.md) + [L2-2 设计 v0.1.0](../../design/L2-modules/L2-operator-core.md) 编写，依据宪法 §14.4 待评审。**评审通过后**进入 L4 实施阶段（开发者对照本文件逐文件实现）。