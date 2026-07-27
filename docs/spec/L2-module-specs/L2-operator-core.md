# L2 模块规格：Operator Core（编排层 · Python-first）

> **✅ v0.2.0（2026-07-25 · #27/#28/#29/#30/#31/#32/#33 会话）**
> 本文档已补完头部 + §0-§15 + 附录 A + 附录 B（103.2KB / 1890 行）。**§A-§G 10 维度评审通过**（2026-07-25 #33 · 0 阻塞项 · 3 关注项移交 L3-1 · 2 建议项）。已覆盖：阅读指南、模块概述、Python 包结构、4 Controllers、admission webhook、Leader Election、async-first/CPU offload、Finalizer、错误模型、Helm values Pydantic schema、可观测性、RBAC、测试策略、工具链与部署形态、验收清单、开放问题、ADR/Constitution 引用矩阵。
> L2-2 Python v0.2.0 规模 103.2KB / 1890 行 / 15 节 + 2 附录 / 122 测试 ID / 16 项开放问题（80% 收敛率）/ 95 测试 ID 验收矩阵。

> **模块 ID**：C-1（Operator Core，见 L1 v0.2.0 Architecture §4.1）
> **层级**：L2 — 模块规格（**Python-first v0.2 重写**）
> **版本**: **v0.2.0**（**Python 重写 · ADR-0005 触发**；2026-07-25 #27-#33 起草 + 评审通过）
> **状态**: ✅ **v0.2.0**（§A-§G 10 维度全 PASS · 评审报告 [`docs/reviews/l2-2-operator-core-spec-review.md`](../../reviews/l2-2-operator-core-spec-review.md) · 2026-07-25 #33）
> **配套设计**: [`docs/design/L2-modules/L2-operator-core.md`](../../design/L2-modules/L2-operator-core.md) **v0.2.0**（2026-07-24 评审通过；10 维度全 PASS · 80KB / 1583 行）
> **supersedes**: v0.1.0 Go baseline Spec（已归档至 [`docs/archive/pre-python-2026-07-24/L2-operator-core-spec-v0.1.0-go-baseline.md`](../../archive/pre-python-2026-07-24/L2-operator-core-spec-v0.1.0-go-baseline.md) 2026-07-24 评审通过；**仅 supersede Go struct / kubebuilder annotation / controller-runtime reconcile / client-go 调用 实现条款**；wire contract（4 Controllers / CRD 状态机 / Leader Election / Finalizer / RBAC / metric name）与 v0.1 业务语义**完全继续有效**）

> **依据**：[`CONSTITUTION.md`](../../../CONSTITUTION.md) **v0.5.0** §3.8 Python-first + §6 mTLS + §7 可观测性 + §9.7 静态质量 + §14.4 评审门禁 + §14.5 MVP 例外时间窗口；[ADR-0005](../../adr/0005-python-first-technology-stack.md) §3.1 Operator Core 模块映射 + §7 单进程原则 + §8 SDK 门禁 + §13.1 OTel/指标迁移；[L1 Architecture v0.2.0](../../design/L1-architecture.md) §3.2 编排层 + §4.1 C-1 Operator + §11.5 Python 性能预算；[L1 Spec v0.2.0](../../spec/L1-system-spec.md) §2-§4 CRD + §7 状态机 + §9-§10 资源/限流 + §16 指标；[L2-2 Design v0.2.0](../../design/L2-modules/L2-operator-core.md)（14 主章节）+ [L2-1 A2A Protocol v0.2.0 Spec](../../spec/L2-module-specs/L2-a2a-protocol.md) §2.5 (client) + §16.1 (OTel)

---

## 0. 阅读指南

本文档面向 **L4 Python 实现者** + **代码审查者**，作为 L2-2 Operator Core Python v0.2 实现的"是什么 + 怎么做"基线。

**阅读路径**：
- **L4 实现者** → §2 包结构与文件清单（精确到文件路径）+ §3 4 Controllers（每文件契约）+ §4 admission webhook（5 个文件契约）
- **代码审查者** → §3 Controllers + §4 admission + §5-§15（待补完）
- **L3 Spec 起草者** → 与 L2-2 Design v0.2.0 对照阅读（本文档是 Design 的文件级落地）
- **评审者** → §3 + §4 + 附录 A

**与 L2-2 Go baseline Spec 关系**：
- v0.1.0 Go baseline 已归档（不可变，仅参考）
- 本 v0.2 Spec **完全替代** Go baseline 的 Python 实现决策（Kopf handlers + async reconciler services + `kubernetes_asyncio` + K8s Lease Leader Election）
- 业务语义（4 Controller 职责 / CRD 状态机 / Finalizer / RBAC / metric name）**与 v0.1.0 完全一致**

---

## 1. 模块概述

### 1.1 使命与边界

L2-2 Operator Core 是 `superteam-a2a` **编排层（Orchestration Layer）** 的唯一实现，承载 4 类 CRD 生命周期管理 + admission 校验 + Leader Election + Finalizer cleanup + MemoryReconciler 定时后台任务。

**模块内**（v0.2 Python-first · 本 Spec 详述）：
- 4 个 CRD Controller（Agent / AgentSet / Workflow / MemoryReconciler）的 Python 文件级契约
- ValidatingAdmissionWebhook（独立 ASGI server，与 Operator 同 Deployment）
- Leader Election（K8s Lease，单 leader 触发 reconcile + MemoryReconciler）
- Finalizer 管理（4 个 CRD 全配，永久保留 v0.1 名称）
- Helm values 完整 Pydantic schema
- RBAC manifest（ClusterRole / Role / ServiceAccount）
- 测试 ID 矩阵（≥ 100 ID）

**模块外**（其他 L2 模块负责）：
- A2A 通信（L2-1 C-2）
- Adapter 协议（L2-3 C-3）
- Knowledge/Memory 业务语义（L2-4 C-4）

**永久非职责**：不实现 Agent 业务逻辑 / 不实现 A2A 协议 / 不实现 framework adapter SDK / 不实现 Knowledge/Memory 业务算法（详见 L2-2 Design §1.2）

### 1.2 模块对外契约（public API surface）

**Public API 入口**（仅暴露给其他 L2/L3 模块）：

```python
# packages/operator/src/superteam_a2a/operator/__init__.py
from .main import OperatorMain
from .controllers import AgentController, AgentSetController, WorkflowController
from .reconcilers import MemoryReconciler
from .admission import AdmissionWebhookApp
from .leader_election import Election
from .errors import ReconcileError, RetryableError, NonRetryableError, PermanentError
from .config import HelmValues

__all__ = [
    "OperatorMain",
    "AgentController", "AgentSetController", "WorkflowController",
    "MemoryReconciler",
    "AdmissionWebhookApp",
    "Election",
    "ReconcileError", "RetryableError", "NonRetryableError", "PermanentError",
    "HelmValues",
]

__version__ = "0.2.0"
```

**Public API 契约**（Pydantic 模型导出）：
- `HelmValues` / `OperatorConfig` / `PythonConfig` / `LeaderElectionConfig` / `AdmissionConfig` / `MemoryReconcilerConfig`（详见 §9）
- 4 CRD BaseModel：`Agent` / `AgentSet` / `Workflow` / `Memory`（来自 L1 Spec v0.2.0 CRD Pydantic）
- `ReconcileError` / `RetryableError` / `NonRetryableError` / `PermanentError`（错误模型）

**Public API 边界规则**：
- ✅ 所有 public API 必须有 Python docstring（§16 v0.5.0 宪法硬约束）
- ✅ 所有 public API 必须有 Pyright strict 类型签名（禁止 `Any` 穿过公共边界）
- ✅ Public API 不导出 internal helpers（如 `_compute_decay_sync`）

---

## 2. 包结构与文件清单

> ⚠️ **本节为骨架占位**——详细文件清单（70+ 文件）按 L3-1 文件级 Spec 补完；本节给出完整包布局 + 关键文件占位。

### 2.1 完整包布局（与 L2-2 Design §3.1 一致）

```
packages/operator/
├── pyproject.toml                        # uv workspace 成员；Python 3.12+；kopf + kubernetes_asyncio + prometheus-client + structlog + opentelemetry-api
├── src/
│   └── superteam_a2a/
│       └── operator/
│           ├── __init__.py                # ✅ Public API 导出（详见 §1.2）
│           ├── __main__.py               # ⏳ 入口：kopf run + asyncio.run + Leader Election 启动
│           ├── main.py                   # ⏳ Operator 主类（Kopf + ASGI server + admission webhook 共进程）
│           │
│           ├── controllers/               # ✅ 4 Controllers
│           │   ├── __init__.py
│           │   ├── agent.py              # ⏳ AgentController（Kopf handlers + AgentReconciler 集成）
│           │   ├── agentset.py           # ⏳ AgentSetController
│           │   ├── workflow.py           # ⏳ WorkflowController（含 DAG 校验）
│           │   └── memory_reconciler.py  # ⏳ MemoryReconciler（@kopf.timer(interval=60)）
│           │
│           ├── reconcilers/               # ⏳ 业务逻辑 services
│           │   ├── __init__.py
│           │   ├── base.py               # ⏳ BaseReconciler Protocol
│           │   ├── agent_reconciler.py   # ⏳ Agent 业务逻辑
│           │   ├── agentset_reconciler.py
│           │   ├── workflow_reconciler.py
│           │   └── memory_reconciler.py  # ⏳ Memory 业务逻辑（decay / reinforce / GC / promotion）
│           │
│           ├── admission/                # ✅ admission webhook 独立 server
│           │   ├── __init__.py
│           │   ├── server.py             # ⏳ ASGI server（uvicorn 单 worker）
│           │   ├── validators/           # ⏳ 4 CRD validators
│           │   │   ├── __init__.py
│           │   │   ├── base.py           # ⏳ CRDValidator Protocol + ValidationResult BaseModel
│           │   │   ├── agent.py          # ⏳ AgentValidator
│           │   │   ├── agentset.py       # ⏳ AgentSetValidator
│           │   │   ├── workflow.py       # ⏳ WorkflowValidator（含 DAG 校验）
│           │   │   ├── memory.py         # ⏳ MemoryValidator
│           │   │   └── mutual_exclusion.py  # ⏳ Knowledge↔Memory 互斥校验
│           │   └── tls.py                # ⏳ cert-manager 集成（TLS 加载 + 热更新）
│           │
│           ├── leader_election/          # ✅ 自研 K8s Lease 客户端
│           │   ├── __init__.py
│           │   ├── lease_client.py       # ⏳ AsyncLeaseClient
│           │   └── election.py           # ⏳ Election 主类
│           │
│           ├── finalizers/               # ⏳ Finalizer 名称常量
│           │   ├── __init__.py
│           │   └── names.py              # ⏳ FinalizerName Enum（4 CRD 永久保留）
│           │
│           ├── clients/                  # ⏳ K8s API client
│           │   ├── __init__.py
│           │   └── k8s_client.py         # ⏳ AsyncK8sClient
│           │
│           ├── observability/            # ⏳ 可观测性
│           │   ├── __init__.py
│           │   ├── metrics.py            # ⏳ Prometheus 指标（11 Operator + 4 Python runtime）
│           │   ├── tracing.py            # ⏳ OTel SDK 初始化
│           │   ├── logging.py            # ⏳ structlog 配置
│           │   └── events.py             # ⏳ K8s Events 客户端
│           │
│           ├── errors/                   # ⏳ 错误模型
│           │   ├── __init__.py
│           │   └── reconcile_errors.py   # ⏳ ReconcileError hierarchy（3 类）
│           │
│           ├── config/                   # ⏳ 配置
│           │   ├── __init__.py
│           │   └── helm_values.py        # ⏳ HelmValues Pydantic model
│           │
│           └── utils/                    # ⏳ 工具
│               ├── __init__.py
│               ├── cpu_offload.py        # ⏳ anyio.to_thread.run_sync wrapper
│               └── time.py               # ⏳ Clock 抽象（便于时间穿越测试）
│
├── tests/                                # ⏳ 测试（结构镜像 src/）
│   ├── unit/                             # ⏳ pytest + async test
│   ├── integration/                      # ⏳ envtest（K8s API mock）
│   └── e2e/                              # ⏳ kind + hello-agent
│
└── deploy/
    └── helm/
        └── operator/
            ├── Chart.yaml
            ├── values.yaml               # ⏳ 默认 Helm values（与 L2-2 Design §11 一致）
            ├── values.schema.json       # ⏳ Pydantic 派生
            ├── templates/
            │   ├── deployment.yaml       # ⏳ Operator + admission webhook 同 Deployment
            │   ├── service.yaml          # ⏳ Operator metrics + admission webhook service
            │   ├── webhookconfig.yaml    # ⏳ ValidatingWebhookConfiguration
            │   ├── clusterrole.yaml      # ⏳ RBAC（与 L2-2 Design §12 一致）
            │   ├── clusterrolebinding.yaml
            │   ├── serviceaccount.yaml
            │   └── leader_election_lease.yaml
            └── values.schema.json
```

**文件清单统计**（预计 70+ 文件）：
- Python 源文件：约 35 个（含 `__init__.py` + `__main__.py` + `main.py`）
- Helm templates：8 个
- 测试文件：约 30 个（结构镜像 src/）
- 配置文件：4 个（pyproject.toml + Chart.yaml + values.yaml + values.schema.json）

### 2.2 边界规则（与 Design §3.2 一致 · ADR-0005 §3.2）

| 边界 | 规则 | 依据 |
|------|------|------|
| **Operator 不依赖 framework adapter** | Operator 不 import L2-3 Adapter SDK | 宪法 §3.7 + ADR-0005 §13 |
| **Operator 不实现 A2A 协议** | 所有 A2A 通信走 L2-1 a2a-sdk client | ADR-0005 §3.1 |
| **Operator 不实现 Knowledge/Memory 业务语义** | decay/reinforce 算法由 L2-4 负责；Operator 仅 reconcile 驱动 | ADR-0003 §6 |
| **admission webhook 不依赖 K8s API** | admission webhook 是无状态 server | ADR-0005 §7 |
| **Reconciler services 不依赖 Kopf** | 业务逻辑在 `reconcilers/` 下，与 Kopf handlers 解耦 | ADR-0005 §13.2 |
| **Leader Election 不阻塞 event loop** | Lease 续约在独立 task | ADR-0005 §6.1 |
| **状态机状态子资源写回仅通过 `kopf.adopt`** | 禁止直接 `kubectl patch` 风格 API | ADR-0005 §3.1 |
| **Finalizer 永久保留 v0.1 名称** | 4 个 CRD Finalizer 名称 v1.0+ 也不变 | L2-2 Go baseline §7.4 + 宪法 §3.4 |

---

## 3. 4 Controllers + MemoryReconciler 文件级契约

> ⚠️ **本节为骨架占位**——详细 reconcile 流程 + 完整 Pydantic schema + 异常路径 + 测试 ID 待 L3-1 文件级 Spec 补完；本节给出每 Controller 的关键文件契约概要。

### 3.1 Agent Controller（C-1.1）

**关键文件**：
- `controllers/agent.py` — Kopf handlers（on.create / on.update / on.delete + on.resume）
- `reconcilers/agent_reconciler.py` — 业务逻辑（Adapter 注入 + Ready 检查 + Status 更新）

**reconcile 流程**（与 L2-2 Design §4.1 一致）：
1. 检查 DeletionTimestamp + Finalizer → 若有则执行 cleanup
2. 添加 Finalizer `agent.superteam-a2a.io/cleanup`
3. 根据 AgentSpec 决定 Pod 模式（Sidecar / Plugin / 直连 / 外部）
4. 注入 Adapter 容器（Sidecar 模式）或 Annotation（Plugin 模式）
5. 创建 / 更新 Pod + Service + ServiceAccount
6. 等待 Pod Ready（最长 5min）
7. 更新 AgentStatus（phase / conditions / observedGeneration）

**Pydantic Schema 契约**（与 L1 Spec §2 完全一致）：
```python
# 来自 packages/operator/src/superteam_a2a/operator/types/agent.py
# （完整定义在 L1 Spec v0.2.0 §2 + Pydantic wire alias 单向原则 §1.6）
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class AgentPhase(str, Enum):
    PENDING = "Pending"
    CREATING = "Creating"
    READY = "Ready"
    DEGRADED = "Degraded"
    FAILED = "Failed"


class AgentPodMode(str, Enum):
    SIDECAR = "Sidecar"
    PLUGIN = "Plugin"
    DIRECT = "Direct"  # v0.5+
    EXTERNAL = "External"  # v0.5+


class AgentSpec(BaseModel):
    """与 L1 Spec §2.1 AgentSpec wire YAML 不变 · Python 实现"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    framework: str = Field(min_length=1, max_length=64)
    image: str = Field(pattern=r"^[a-z0-9./:@-]+$")
    pod_mode: AgentPodMode = AgentPodMode.SIDECAR
    resources: dict | None = None
    # ... 详见 L1 Spec §2.1 完整字段


class AgentStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase: AgentPhase = AgentPhase.PENDING
    conditions: list[Condition] = Field(default_factory=list, max_length=10)
    observed_generation: int = Field(ge=0)
    last_reconcile_time: datetime | None = None
```

**关键不变量**：
- ✅ 1 Agent → 1 Pod + 1 Service + 1 ServiceAccount（namespace 内）
- ✅ Pod 模板由 Adapter 注入 + Agent 镜像 + Resources
- ✅ mTLS 由 cert-manager 颁发（ServiceAccount 注解触发）
- ✅ Finalizer：`agent.superteam-a2a.io/cleanup`（永久保留）

### 3.2 AgentSet Controller（C-1.2）

**关键文件**：
- `controllers/agentset.py` — Kopf handlers
- `reconcilers/agentset_reconciler.py` — 业务逻辑（Agent 子集协调 + 滚动更新）

**reconcile 流程**（与 L2-2 Design §4.2 一致）：
1. 检查 DeletionTimestamp + Finalizer
2. 添加 Finalizer `agentset.superteam-a2a.io/cleanup`
3. 根据 `replicas` + `selector` 列出当前 Agent 子集
4. 创建缺失的 Agent（带 owner reference 指向 AgentSet；orphanDeletion=false）
5. 删除多余的 Agent
6. 等待所有 Agent Ready（最长 10min）
7. 更新 AgentSetStatus（replicas / readyReplicas / conditions）

**关键不变量**：
- ✅ AgentSet owns Agent（owner reference）；AgentSet 删除 → 子 Agent 由 GC 自动清理（orphanDeletion=false）
- ✅ Agent 模板与 AgentSetSpec.template 一致（mutation 禁止）
- ✅ 副本数变化触发滚动更新

### 3.3 Workflow Controller（C-1.3）

**关键文件**：
- `controllers/workflow.py` — Kopf handlers
- `reconcilers/workflow_reconciler.py` — 业务逻辑（Task 调度占位 + Status 更新）
- `admission/validators/workflow.py` — DAG 校验（Kahn/DFS 纯函数）

**reconcile 流程**（与 L2-2 Design §4.3 一致）：
1. 检查 DeletionTimestamp + Finalizer
2. 添加 Finalizer `workflow.superteam-a2a.io/cleanup`
3. **admission 时 DAG 校验**：WorkflowValidator.validate_dag（节点 ≤ 50 + 边 ≤ 200 + 无环）
4. 根据 WorkflowSpec.tasks[] 创建 / 更新 Task CR（v0.1 stub）
5. 更新 WorkflowStatus

**关键不变量**：
- ✅ DAG 校验在 admission webhook（K8s API 层） + reconcile 时双重校验
- ✅ Task 模板与 WorkflowSpec.tasks[i] 一致
- ✅ Finalizer：`workflow.superteam-a2a.io/cleanup`

### 3.4 MemoryReconciler（C-1.4 · 非 Controller）

**关键文件**：
- `controllers/memory_reconciler.py` — Kopf `@kopf.timer(interval=60)`
- `reconcilers/memory_reconciler.py` — 业务逻辑（decay / reinforce / GC / promotion）

**reconcile 流程**（与 L2-2 Design §4.4 一致）：
1. 列出所有 namespace 的 Memory CR
2. 对每个 Memory 应用 decay（`effectiveConfidence = confidence × exp(-elapsed_days / decayDays)`）
3. 对每个 Memory 应用 reinforce（每次 recordMemory +0.05 confidence，封顶 0.95）
4. 对 `effectiveConfidence < 0.1` 的 Memory 应用 GC
5. 对 `effectiveConfidence > 0.9` 且 `reinforcedCount > 10` 的 Memory 计算 `eligibleForPromotion`
6. 批量更新 MemoryStatus（**CPU offload**：`anyio.to_thread.run_sync`）

**关键不变量**：
- ✅ 单 leader 触发（避免重复 reconcile）
- ✅ 每 60s 全量 reconcile（增量优化留 v0.5+）
- ✅ decay 公式与 L2-4 完全一致（数学公式 wire 不变）
- ✅ batch reconcile CPU offload（ADR-0005 §6.3）

---

## 4. admission webhook 文件级契约

> ⚠️ **本节为骨架占位**——详细实现（4 CRD validators + DAG 校验算法 + TLS 热更新时序）待 L3-1 文件级 Spec 补完；本节给出文件契约概要。

### 4.1 架构（与 L2-2 Design §5.2 一致）

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
|   +-------------------------------+   |
|                                       |
+---------------------------------------+
            ↑               ↑
       /metrics          /validate (HTTPS)
            ↓               ↓
   Prometheus          K8s API Server
                      (ValidatingWebhookConfiguration)
```

### 4.2 Validator 通用契约

**关键文件**：
- `admission/server.py` — ASGI server（uvicorn 单 worker）
- `admission/validators/base.py` — CRDValidator Protocol + ValidationResult BaseModel
- `admission/tls.py` — cert-manager 集成

**Pydantic Schema 契约**：
```python
# packages/operator/src/superteam_a2a/operator/admission/validators/base.py
from typing import Protocol
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """admission 校验结果"""
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    reason: str | None = None
    http_status: int = Field(200, ge=200, le=599)


class CRDValidator(Protocol):
    """4 CRD validators 必须实现此接口"""

    crd_kind: str  # "Agent" | "AgentSet" | "Workflow" | "Memory"
    group: str     # "superteam-a2a.io"

    async def validate(
        self,
        namespace: str,
        name: str,
        spec: BaseModel,
    ) -> ValidationResult:
        """同步校验 spec；返回 ValidationResult(allowed, reason, http_status)"""
        ...
```

### 4.3 4 CRD validators

**关键文件**：
- `admission/validators/agent.py` — AgentValidator（AgentSpec 字段约束 + AdapterConfig 引用校验 + Resources 配额）
- `admission/validators/agentset.py` — AgentSetValidator（replicas 1-100 + selector 必填 + template 一致）
- `admission/validators/workflow.py` — WorkflowValidator（DAG 校验 + tasks[] 字段约束 + inputs 表达式）
- `admission/validators/memory.py` — MemoryValidator（content 1-20 keys + scope 必填 + agent-private visibility）
- `admission/validators/mutual_exclusion.py` — Knowledge↔Memory 双向互斥校验

### 4.4 DAG 校验算法契约（与 L2-2 Design §5.5 一致）

**关键文件**：`admission/validators/workflow.py` 内 `WorkflowValidator.validate_dag`

**算法契约**：
```python
class DAGValidator:
    MAX_NODES = 50
    MAX_EDGES = 200

    def validate_dag(self, tasks: list[TaskSpec]) -> ValidationResult:
        """Kahn 算法检测环 + 节点数限制（纯函数 · 无 I/O）"""
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
- ✅ DAG 校验是**纯函数**（无 I/O；单测无需 mock）
- ✅ admission 时校验一次 + reconcile 时复检一次（双保险）
- ✅ 节点 / 边数限制为软上限（v0.5+ 可配）

### 4.5 TLS 证书轮换契约（与 L2-2 Design §5.6 一致）

**关键文件**：`admission/tls.py`

**轮换策略**：
- cert-manager Certificate 资源（`superteam-a2a-webhook-tls`）+ Serving 证书类型
- K8s `ValidatingWebhookConfiguration` 的 `caBundle` 引用 cert-manager 颁发 CA
- webhook server 监听 8443，从 Secret 加载 TLS 证书
- **热更新机制**：监听 Secret 更新 → 重建 SSLContext（不重启 server）

**轮换时长**：
- `duration: 2160h`（90 天）
- `renewBefore: 720h`（30 天前续期）
- `privateKey.rotationPolicy: Always`（每次续期生成新私钥）

### 4.6 关键不变量

- ✅ 4 CRD validators 全部用 Pydantic v2 严格校验（extra="forbid"）
- ✅ DAG 校验是纯函数（无 I/O，单测无需 mock）
- ✅ 双向互斥校验在 4 CRD validators 各调用一次（避免漏检）
- ✅ Admission webhook 拒绝的请求**不**写 etcd
- ✅ TLS 证书热更新（不重启 webhook server；保持 0 停机）
- ✅ admission webhook **不**调用 K8s API（性能 + 安全考虑）

**与 Go baseline 对应**：L2-2 Go baseline §4.3 admission webhook + §10.1 自定义错误码；wire contract（4 CRD 错误码 + 422/400 HTTP Status）与 v0.1 业务语义**完全继续有效**

---

## 5. Leader Election 文件级契约

> 本节把 L2-2 Design §6 的选型落到 Python 文件、接口、时序和故障契约。Leader Election 是 reconcile 的前置门禁：未持有 Lease 的副本不得执行业务 reconcile 或 MemoryReconciler。

### 5.1 文件与 public interface

| 文件 | 必须提供 | 约束 |
|------|----------|------|
| `leader_election/lease_client.py` | `AsyncLeaseClient` | 只封装 `kubernetes_asyncio.client.CoordinationV1Api`；CAS 更新必须携带 `resourceVersion` |
| `leader_election/election.py` | `Election` | 独立 asyncio task；不得阻塞 Kopf handler 或 admission server |
| `leader_election/__init__.py` | `Election`, `AsyncLeaseClient` | 只导出 public API |
| `tests/unit/leader_election/test_lease_client.py` | LE-001~LE-012 | fake API client，不连接真实集群 |
| `tests/unit/leader_election/test_election.py` | LE-013~LE-024 | fake clock + fake callbacks，覆盖 acquire/renew/lost |

```python
# packages/operator/src/superteam_a2a/operator/leader_election/lease_client.py
from collections.abc import Awaitable
from datetime import datetime
from typing import Protocol


class LeaseApi(Protocol):
    """AsyncLeaseClient 所需的最小 K8s Lease API。"""

    async def read_namespaced_lease(self, name: str, namespace: str): ...
    async def create_namespaced_lease(self, namespace: str, body): ...
    async def replace_namespaced_lease(self, name: str, namespace: str, body): ...


class AsyncLeaseClient:
    """以 K8s Lease 为后端的异步 CAS 客户端。"""

    def __init__(
        self,
        k8s: LeaseApi,
        lease_name: str,
        namespace: str,
        holder_id: str,
        lease_duration_seconds: int = 30,
    ) -> None: ...

    async def try_acquire(self) -> bool: ...
    async def renew(self) -> bool: ...
    async def release(self) -> None: ...
    def is_expired(self, lease: object, now: datetime) -> bool: ...
```

```python
# packages/operator/src/superteam_a2a/operator/leader_election/election.py
from collections.abc import Callable


class Election:
    """在独立 asyncio task 中执行 acquire/renew/release。"""

    is_leader: bool

    def __init__(
        self,
        lease: AsyncLeaseClient,
        on_acquired: Callable[[], None],
        on_lost: Callable[[], None],
        renew_interval_seconds: int = 10,
        max_renew_failures: int = 3,
    ) -> None: ...

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
```

### 5.2 Lease wire contract

固定资源如下；名称和时长属于 v0.1 兼容性约束，不得由实现者自行修改：

```yaml
apiVersion: coordination.k8s.io/v1
kind: Lease
metadata:
  name: superteam-a2a-operator-leader
  namespace: superteam-a2a-system
spec:
  holderIdentity: <pod-name>-<uuid>
  leaseDurationSeconds: 30
  acquireTime: <RFC3339>
  renewTime: <RFC3339>
  leaderTransitions: <non-negative integer>
```

- `holderIdentity` 必须在进程生命周期内稳定，在不同 Pod 之间唯一。
- `renewTime`、`acquireTime` 必须序列化为 UTC RFC 3339；禁止使用本地时区。
- `try_acquire()` 遇到 404 必须执行一次 create；create 发生 409 时视为未获取，不得覆盖已有 holder。
- 已有未过期且 holder 不是本进程时，`try_acquire()` 返回 `False`，不写入 Lease。
- replace 遇到 409 必须回到下一轮 acquire；不得把冲突当作成功。
- `release()` 只允许清除本进程持有的 Lease；读到其他 holder 时必须 no-op。

### 5.3 Election 状态机与时序

```text
                 +-----------+
        start    | Standby   |
          +----->|           |<----------------+
          |      +-----+-----+                 |
          |            | acquire=True          | renew failed x 3
          |            v                       |
          |      +-----+-----+   renew=False   |
          |      | Leader    +-----------------+
          |      +-----+-----+
          |            |
          | stop       | stop / release
          +------------+
```

契约：

1. `start()` 只创建一个后台 task；重复调用必须幂等。
2. Standby 每 5 秒尝试获取 Lease；未获取时不执行 Controller 回调。
3. 获取成功时先设置 `is_leader=True`，再调用 `on_acquired()`；回调异常不得跳过失主保护。
4. Leader 每 10 秒续约；连续 3 次失败后设置 `is_leader=False`，调用 `on_lost()`，尝试 release，然后回到 Standby。
5. `on_lost()` 必须先于任何新的 reconcile；Controller 通过共享 `LeaderGate` 拒绝已排队但尚未开始的业务任务。
6. `stop()` 取消后台 task，若当前为 leader 则 best-effort release；取消不得抛出未处理异常。

### 5.4 Controller gate

所有 Controller 和 MemoryReconciler 在进入业务逻辑前必须检查同一个 gate：

```python
class LeaderGate(Protocol):
    @property
    def is_leader(self) -> bool: ...

    def require_leader(self) -> None:
        """非 leader 时抛出 StandbyError，不触发 K8s 写操作。"""
        ...
```

- Standby 可以接收 watch 事件，但不得 create/update/delete/patch 任何业务资源。
- admission webhook 不经过 LeaderGate；admission 是 API Server 前置校验，必须在所有副本上可用。
- Lease API 短暂不可用时，当前 leader 在达到失败阈值前不得宣称仍可安全写入；失败阈值后立即失主。

### 5.5 关键不变量与测试 ID

- `LE-001`：同一 Lease 竞争时最多一个 fake client 返回 acquire 成功。
- `LE-004`：create 409 不覆盖已有 holder。
- `LE-008`：replace 409 后重新读取 resourceVersion。
- `LE-012`：过期 Lease 可以被新 holder 获取。
- `LE-013`：`start()` 重复调用不创建第二个 task。
- `LE-016`：连续三次 renew 失败触发 `on_lost` 且 `is_leader=False`。
- `LE-019`：standby Controller 不写业务资源。
- `LE-022`：stop 时 leader best-effort release，API 异常被吸收并记录日志。
- `LE-024`：leaseDuration、renewInterval、maxRenewFailures 与 Helm schema 一致。

**关键不变量**：单一 Lease 只允许单一有效 holder；失主后禁止继续 reconcile；Lease 名称、namespace、30 秒 TTL 和事件指标名称保持 wire contract 不变。

---

## 6. async-first 与 CPU offload 文件级契约

### 6.1 async 边界

以下文件中的 I/O 入口必须是 `async def`：

- `controllers/*.py` 的 Kopf handler；
- `reconcilers/*.py` 的 `reconcile()` / `finalize()` / `patch_status()`；
- `clients/k8s_client.py` 的所有 K8s API wrapper；
- `leader_election/*.py` 的 Lease 操作；
- `admission/server.py` 的 ASGI handler；
- `admission/tls.py` 的 Secret watch；
- `observability/events.py` 的事件写入。

同步函数只允许用于纯计算、Pydantic schema 转换和常量查找。禁止在 event loop 内直接调用同步的 K8s client、HTTP client、文件读取或大规模 JSON 解析。

### 6.2 单进程启动契约

```python
# packages/operator/src/superteam_a2a/operator/main.py
async def run_operator(config: HelmValues) -> None:
    """启动 Kopf、admission server、Leader Election 和 runtime metrics。"""
    # 1. 初始化显式 K8s async client 与 observability provider
    # 2. 创建共享 LeaderGate
    # 3. 以单 worker 启动 admission ASGI server
    # 4. 启动 Election task
    # 5. 交给 Kopf 处理 CRD watch
    ...
```

- Helm `operator.python.workers` 的合法值只有 `1`；Pydantic schema 必须以 `ge=1, le=1` 拒绝其他值。
- `kopf.Settings.execution.max_workers` 固定为 `1`。
- Uvicorn 必须使用单 worker；禁止在 `run_operator()` 内再次创建第二个 event loop。
- `asyncio.create_task()` 创建的后台任务必须注册到生命周期管理器，在 shutdown 时逐一取消并 await。
- 任何同步 CPU 工作不得通过 `asyncio.to_thread` 与统一 offload 指标脱钩；必须使用本节规定的 wrapper。

### 6.3 CPU offload API

```python
# packages/operator/src/superteam_a2a/operator/utils/cpu_offload.py
from collections.abc import Callable
from typing import ParamSpec, TypeVar
import anyio

P = ParamSpec("P")
T = TypeVar("T")


async def run_cpu_bound(func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """在线程池执行纯 CPU 函数，不阻塞 operator event loop。"""
    ...
```

必须 offload 的路径：

1. Memory 数量大于 `memoryReconciler.cpuOffloadThreshold`（默认 1000）时的 batch decay / reinforce 计算；
2. L2-4 反向索引协作所需的 BM25 rebuild；
3. admission 请求体大于 1 MiB 时的 JSON/Pydantic 解析；
4. 其他预计超过 10ms 的纯 Python 循环，除非 L3 Spec 明确豁免并提供基准数据。

禁止把 K8s API I/O 放入线程池伪装成 CPU offload；I/O 必须使用 `kubernetes_asyncio`。

### 6.4 batch decay 契约

```python
async def batch_decay(
    memories: list[Memory],
    current_time: datetime,
) -> list[MemoryStatus]:
    """计算一批 MemoryStatus；数学公式与 L2-4 Spec 保持一致。"""
    ...
```

线程池内的纯函数必须满足：

- 不修改输入 Memory；
- 不访问 K8s、网络、全局可变状态或 event loop；
- 使用 UTC 时间；
- `effective_confidence = confidence * exp(-elapsed_days / decay_days)`；
- 输出顺序与输入顺序一致，便于批量 patch 与测试关联；
- 单条计算异常不得静默丢弃整批，必须返回结构化错误并由 Reconciler 分类。

### 6.5 Python runtime 指标

以下指标必须由 `observability/metrics.py` 注册，且不得重复注册：

| 指标 | 类型 | 触发点 |
|------|------|--------|
| `superteam_python_event_loop_lag_seconds` | Histogram | 定时 heartbeat 观测 event loop 延迟 |
| `superteam_python_thread_offload_queue_depth` | Gauge | offload 提交/完成 |
| `superteam_python_active_asyncio_tasks` | Gauge | task 生命周期 |
| `superteam_python_gc_collections_total{generation}` | Counter | Python GC 回调 |

测试 `ASYNC-001`~`ASYNC-012` 必须覆盖：同步调用探测、单 worker 配置、shutdown task 回收、阈值前后 offload 路径、输入顺序稳定性和指标注册幂等。

**关键不变量**：Kopf、webhook、Lease 和 Reconciler 共享单一 event loop；所有阻塞 CPU 路径可观测且不阻塞 event loop；Operator 代码不引入第二核心语言。

---

## 7. Finalizer 文件级契约

### 7.1 名称与映射

```python
# packages/operator/src/superteam_a2a/operator/finalizers/names.py
from enum import StrEnum


class FinalizerName(StrEnum):
    """4 个 CRD 的永久 Finalizer 名称。"""

    AGENT = "agent.superteam-a2a.io/cleanup"
    AGENT_SET = "agentset.superteam-a2a.io/cleanup"
    WORKFLOW = "workflow.superteam-a2a.io/cleanup"
    MEMORY = "memory.superteam-a2a.io/cleanup"

    @classmethod
    def for_kind(cls, kind: str) -> "FinalizerName":
        """返回 kind 对应的 Finalizer；未知 kind 必须抛出 ValueError。"""
        ...
```

映射必须覆盖且仅覆盖 `Agent`、`AgentSet`、`Workflow`、`Memory`。Finalizer 字符串是稳定 wire contract：v1.0+ 不得重命名、删除或改变含义。

### 7.2 handler 契约

每个 Controller 必须提供以下逻辑等价的 handler：

```python
async def on_delete(
    *,
    body: Mapping[str, object],
    namespace: str,
    name: str,
    **_: object,
) -> None:
    """执行幂等 cleanup；成功后移除本 CRD 的 Finalizer。"""
    ...
```

**删除顺序**：

1. 检查 deletion timestamp；非删除事件不得执行 cleanup。
2. Finalizer 缺失时直接返回，不为已进入删除流程的旧资源补写 Finalizer。
3. 按 CRD 类型清理关联 Pod、Service、ServiceAccount、Task stub 或引用关系。
4. 关联资源不存在视为成功（404 幂等）；冲突和瞬时网络错误按 `RetryableError` 处理。
5. 发出 `CleanupCompleted` 或 `CleanupFailed` K8s Event，并写入结构化日志。
6. 只有全部必需 cleanup 成功后才移除本 CRD Finalizer。

### 7.3 各 CRD cleanup 范围

| CRD | 关联资源 / 动作 | 成功条件 |
|-----|----------------|----------|
| Agent | Adapter Pod、Service、ServiceAccount；解除 KnowledgeItem sourceRef | 资源已删除或不存在；引用不再指向 Agent |
| AgentSet | 删除/交还 owned Agent；不直接删除非 owner 资源 | owner reference 与 orphan 策略一致 |
| Workflow | 删除 v0.1 Task stub 与调度占位状态 | Task 已清理或不存在 |
| Memory | 停止后续 timer 处理；清理 v0.1 索引引用 | 不再产生新的 status patch |

AgentSet 的子 Agent 优先依赖 owner reference + Kubernetes GC；Operator 只处理带有本 AgentSet owner UID 的资源，禁止按名称模糊删除。

### 7.4 幂等、重试与强制删除

- cleanup 可重复执行，任何步骤都必须支持 already-deleted 输入。
- `PermanentError` 会保留 Finalizer，并产生 Warning Event；不得自动移除 Finalizer 掩盖数据残留。
- Operator 不拦截用户的强制删除；强制删除造成的残留由 L3 运维文档定义，不能在正常 cleanup 契约中假设可恢复。
- cleanup timeout 默认 30 秒；超时归类为 RetryableError，Kopf 按 delay 重试。
- 4 个 handler 的 Finalizer 更新必须使用 `kopf.adopt`/Kopf status-patch 约定，不得直接构造绕过 owner metadata 的 patch。

### 7.5 测试 ID

- `FIN-001`~`FIN-004`：4 个 kind 映射和字符串值精确匹配。
- `FIN-010`：非删除事件不触发 cleanup。
- `FIN-014`：缺失关联资源（404）重复删除仍成功。
- `FIN-018`：cleanup 中途 RetryableError 保留 Finalizer。
- `FIN-021`：PermanentError 产生 `CleanupFailed` 且不移除 Finalizer。
- `FIN-025`：成功路径先发事件再移除 Finalizer。
- `FIN-029`：AgentSet 只删除匹配 owner UID 的 Agent。
- `FIN-032`：重复 handler 调用结果与单次调用一致。

**关键不变量**：4 个 Finalizer 全配、名称永久不变、cleanup 幂等；cleanup 未完成时 CRD 不得被 Operator 主动放行删除。

---

## 8. 错误模型文件级契约

### 8.1 错误类型

```python
# packages/operator/src/superteam_a2a/operator/errors/reconcile_errors.py
class ReconcileError(Exception):
    """Operator 内部 reconcile 错误基类。"""

    retry_after_seconds: int | None


class RetryableError(ReconcileError):
    """瞬时错误：允许 Kopf 按延迟重试。"""

    def __init__(self, message: str, retry_after: int = 30) -> None: ...


class NonRetryableError(ReconcileError):
    """当前资源无效，但重试不会改变结果。"""


class PermanentError(ReconcileError):
    """配置或基础设施永久失败，需要人工处理。"""
```

构造函数必须保留原始 message；`retry_after` 合法范围为 1~3600 秒。错误对象不得携带 secret、token 或完整用户 payload。

### 8.2 分类矩阵

| 场景 | 类型 | Kopf 行为 | Status/Event |
|------|------|-----------|--------------|
| API Server 429/5xx、网络超时、Lease 临时冲突 | `RetryableError` | `TemporaryError(delay=retry_after)` | `ReconcileRetry` / phase 保持 |
| CRD 关联对象不存在、不可满足的业务引用、重复 DAG 节点 | `NonRetryableError` | `PermanentError`（不重试） | phase=Failed + `ReconcileFailed` |
| 配置缺失、schema 不兼容、权限永久拒绝 | `PermanentError` | `PermanentError`（不重试） | phase=Failed + 告警 |
| 未知异常 | 转换为 `PermanentError` | 不得无限重试 | `ReconcileFailed` + traceback 仅日志 |

错误优先级为 `Permanent > NonRetryable > Retryable`。包装异常时必须保留 `cause`，但向 K8s Event 暴露的 message 必须脱敏且限长 1024 字符。

### 8.3 统一 wrapper

```python
async def safe_reconcile(
    reconciler: Callable[..., Awaitable[T]],
    *args: object,
    **kwargs: object,
) -> T:
    """把内部错误转换为 Kopf 可识别的行为并写入观测系统。"""
    try:
        return await reconciler(*args, **kwargs)
    except PermanentError as exc:
        await record_reconcile_failure(exc, retryable=False)
        raise kopf.PermanentError(str(exc)) from exc
    except NonRetryableError as exc:
        await record_reconcile_failure(exc, retryable=False)
        raise kopf.PermanentError(str(exc)) from exc
    except RetryableError as exc:
        await record_reconcile_retry(exc)
        raise kopf.TemporaryError(
            str(exc), delay=exc.retry_after_seconds
        ) from exc
```

wrapper 必须包住每个 Controller handler 的业务调用；禁止在 Controller 内部 catch-all 后只打印日志并返回成功，因为这会导致 status 和 reconcile metric 虚假成功。

### 8.4 与 A2A 错误边界

Operator 错误只通过 K8s Status、Events、structlog 和 Operator Prometheus 指标传播；不得转换成或复用 L2-1 JSON-RPC 错误码。反之，A2A client 的 JSON-RPC error 必须在 Operator 边界转换为本节错误类型，并按 HTTP/A2A 层级保留原始错误码到结构化日志字段 `upstream_error_code`。

### 8.5 错误观测字段与测试 ID

错误日志至少包含 `ts`、`level`、`msg`、`trace_id`、`crd`、`namespace`、`name`、`error_class`、`retry_after_seconds`。Event reason 固定为 `ReconcileFailed`、`ReconcileRetry`、`CleanupFailed` 或 `CleanupCompleted`。

- `ERR-001`~`ERR-003`：三类错误构造和默认 retry delay。
- `ERR-007`：429/timeout 转换为 RetryableError。
- `ERR-011`：schema/权限永久失败不重试。
- `ERR-015`：未知异常转换为 PermanentError 且保留 cause。
- `ERR-019`：错误 message 脱敏并限制长度。
- `ERR-023`：错误不污染 L2-1 JSON-RPC 错误码。
- `ERR-027`：每条错误同时写 metric、structlog 和规定 Event。

**关键不变量**：错误分类决定唯一重试行为；失败不可伪装为成功；Operator 和 A2A wire 错误码严格隔离。

---

## 9. Helm values 与 Pydantic schema 文件级契约

### 9.1 values.yaml 稳定结构

```yaml
operator:
  replicaCount: 2
  image:
    repository: ghcr.io/coderzhangfujiang/superteam-a2a-operator
    tag: v0.2.0
    pullPolicy: IfNotPresent
  python:
    workers: 1
    image: python:3.12-slim
  controllers:
    agent: 1
    agentset: 1
    workflow: 1
    memory: 1
  leaderElection:
    enabled: true
    leaseName: superteam-a2a-operator-leader
    leaseDurationSeconds: 30
    renewIntervalSeconds: 10
    maxRenewFailures: 3
  admission:
    enabled: true
    port: 8443
    tlsSecretName: superteam-a2a-webhook-tls
    serviceName: superteam-a2a-operator-webhook
    failurePolicy: Fail
    timeoutSeconds: 10
  memoryReconciler:
    enabled: true
    intervalSeconds: 60
    batchSize: 500
    cpuOffloadThreshold: 1000
```

CamelCase 是 Helm/wire 字段名；Python model 可以使用 snake_case，但必须通过 `alias` / `populate_by_name` 显式处理，禁止隐式改变 values.schema.json 字段名。

### 9.2 Pydantic models

```python
# packages/operator/src/superteam_a2a/operator/config/helm_values.py
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class PythonConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    workers: int = Field(default=1, ge=1, le=1)
    image: str = "python:3.12-slim"
    resources: dict[str, object] = Field(default_factory=lambda: {
        "requests": {"cpu": "200m", "memory": "256Mi"},
        "limits": {"cpu": "1000m", "memory": "1Gi"},
    })


class LeaderElectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    enabled: bool = True
    lease_name: str = Field(
        default="superteam-a2a-operator-leader",
        alias="leaseName",
        min_length=1,
        max_length=253,
    )
    lease_duration_seconds: int = Field(30, alias="leaseDurationSeconds", ge=10, le=300)
    renew_interval_seconds: int = Field(10, alias="renewIntervalSeconds", ge=5, le=60)
    max_renew_failures: int = Field(3, alias="maxRenewFailures", ge=1, le=10)


class AdmissionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    enabled: bool = True
    port: int = Field(8443, ge=1024, le=65535)
    tls_secret_name: str = Field("superteam-a2a-webhook-tls", alias="tlsSecretName")
    service_name: str = Field("superteam-a2a-operator-webhook", alias="serviceName")
    failure_policy: str = Field("Fail", alias="failurePolicy", pattern=r"^(Fail|Ignore)$")
    timeout_seconds: int = Field(10, alias="timeoutSeconds", ge=1, le=30)


class MemoryReconcilerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    enabled: bool = True
    interval_seconds: int = Field(60, alias="intervalSeconds", ge=10, le=3600)
    batch_size: int = Field(500, alias="batchSize", ge=10, le=5000)
    cpu_offload_threshold: int = Field(1000, alias="cpuOffloadThreshold", ge=100, le=100000)


class OperatorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    replica_count: int = Field(2, alias="replicaCount", ge=1, le=10)
    image: dict[str, str]
    python: PythonConfig
    controllers: dict[str, Annotated[int, Field(ge=1, le=1)]]
    leader_election: LeaderElectionConfig = Field(alias="leaderElection")
    admission: AdmissionConfig
    memory_reconciler: MemoryReconcilerConfig = Field(alias="memoryReconciler")
    observability: dict[str, object]
    mtls: dict[str, object]


class HelmValues(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    operator: OperatorConfig
```

### 9.3 Schema generation与 validation

- `HelmValues.model_json_schema(by_alias=True)` 是 `deploy/helm/operator/values.schema.json` 的唯一生成源。
- CI 必须重新生成 schema 并执行无差异检查；手工修改生成文件视为失败。
- `extra="forbid"` 在所有配置层生效；未知顶层、未知 controller 名称和未知 nested key 必须拒绝。
- `controllers` 必须且仅允许 `agent`、`agentset`、`workflow`、`memory` 四个键；不能通过任意 dict key 绕过单 worker 约束。
- `leaderElection.enabled=false` 只允许单副本部署；当 `replicaCount > 1` 时 Helm validation 或 Operator startup 必须失败。
- `admission.failurePolicy` 默认 `Fail`；生产值不得默认降为 `Ignore`。
- `renewIntervalSeconds` 必须小于 `leaseDurationSeconds`，跨字段约束在 `model_validator` 中执行。
- `resources` 的 CPU/Memory 字符串由 Kubernetes API 最终校验；Operator schema 不得把任意 Python object 暴露为 public API 以外的未约束输入。

### 9.4 默认值与兼容性测试 ID

- `HELM-001`：空配置使用全部默认值。
- `HELM-004`：`python.workers=2` 被拒绝。
- `HELM-008`：未知字段被 `extra=forbid` 拒绝。
- `HELM-012`：CamelCase YAML 可 round-trip 为 Pydantic model，再以 alias 输出。
- `HELM-016`：`renewIntervalSeconds >= leaseDurationSeconds` 被拒绝。
- `HELM-020`：多副本关闭 Leader Election 被拒绝。
- `HELM-024`：failurePolicy 仅接受 Fail/Ignore。
- `HELM-028`：Pydantic JSON schema 与仓库 values.schema.json 无差异。
- `HELM-032`：四个 controller key 的并发度只能为 1。

**关键不变量**：Python 3.12+、单 worker、默认 Leader Election、默认 admission Fail、Memory 60 秒周期和 Helm 字段名均属于 v0.2 wire/deployment contract；任何修改必须走 ADR。

---

## 10. 可观测性文件级契约

> 本节把 L2-2 Design §10 的指标、Trace 和日志契约落到 Python 文件与 wire 字段。所有指标名、Event reason 与日志字段均属于 v0.1 wire contract；新指标必须走 ADR。

### 10.1 文件与 public interface

| 文件 | 必须提供 | 约束 |
|------|----------|------|
| `observability/metrics.py` | `MetricsRegistry` | 注册 11 Operator 指标 + 4 Python runtime 指标；同进程内 `register_or_get` 幂等 |
| `observability/tracing.py` | `configure_tracing` | 显式 `TracerProvider` 注入；测试不污染全局 provider |
| `observability/logging.py` | `configure_logging` | structlog JSON 输出 + 8 个必含字段 |
| `observability/events.py` | `emit_event` | K8s Events `create + patch`；reason 取 8 种白名单 |
| `tests/unit/observability/test_metrics.py` | OBS-001~OBS-012 | 注册幂等 + 11 + 4 指标存在性 |

```python
# packages/operator/src/superteam_a2a/operator/observability/metrics.py
from prometheus_client import Counter, Gauge, Histogram


class MetricsRegistry:
    """11 Operator + 4 Python runtime 指标的注册表。"""

    def __init__(self, prefix: str = "superteam_") -> None: ...

    def register_or_get(
        self, name: str, type_: type, labels: list[str] | None = None
    ) -> Counter | Gauge | Histogram: ...
    def as_dict(self) -> dict[str, object]: ...
```

```python
# packages/operator/src/superteam_a2a/operator/observability/events.py
class EventReason(StrEnum):
    RECONCILE_SUCCEEDED = "ReconcileSucceeded"
    RECONCILE_FAILED = "ReconcileFailed"
    RECONCILE_RETRY = "ReconcileRetry"
    CLEANUP_COMPLETED = "CleanupCompleted"
    CLEANUP_FAILED = "CleanupFailed"
    LEADER_ACQUIRED = "LeaderAcquired"
    LEADER_LOST = "LeaderLost"
    ADMISSION_REJECTED = "AdmissionRejected"


async def emit_event(
    body: Mapping[str, object],
    reason: EventReason,
    message: str,
    type_: str = "Normal",
) -> None: ...
```

### 10.2 11 个 Operator 指标

| 指标 | 类型 | Labels | 触发点 |
|------|------|--------|--------|
| `superteam_operator_reconcile_total` | Counter | `crd`, `result` | 每个 reconcile 完成后 |
| `superteam_operator_reconcile_duration_seconds` | Histogram | `crd` | 每个 reconcile 完成后 |
| `superteam_operator_leader_election` | Gauge | — | Leader Election 状态变更 |
| `superteam_operator_finalizer_cleanup_total` | Counter | `crd`, `result` | Finalizer cleanup 完成后 |
| `superteam_operator_finalizer_cleanup_duration_seconds` | Histogram | `crd` | Finalizer cleanup 完成后 |
| `superteam_operator_admission_validation_total` | Counter | `crd`, `result` | admission 校验完成后 |
| `superteam_operator_admission_validation_duration_seconds` | Histogram | `crd` | admission 校验完成后 |
| `superteam_operator_memory_reconcile_total` | Counter | `result` | MemoryReconciler 每 60s 触发后 |
| `superteam_operator_memory_decay_total` | Counter | `phase_from`, `phase_to` | decay 算法触发后 |
| `superteam_operator_lease_renew_total` | Counter | `result` | Lease 续约 |
| `superteam_operator_lease_transition_total` | Counter | `event` | Lease 状态切换（acquired/lost/renew_failed） |

`result` label 取值限定在 `success` / `error` / `retry` / `rejected`；`phase_from` / `phase_to` 取自 `AgentPhase` / `MemoryPhase` enum 字符串。Histogram bucket 默认 `prometheus_client.DEFAULT_BUCKETS`；自定义桶必须写明区间。

### 10.3 Python runtime 4 指标

| 指标 | 类型 | 触发点 |
|------|------|--------|
| `superteam_python_event_loop_lag_seconds` | Histogram | 定时 heartbeat 观测 event loop 延迟 |
| `superteam_python_thread_offload_queue_depth` | Gauge | offload 提交/完成 |
| `superteam_python_active_asyncio_tasks` | Gauge | task 生命周期 |
| `superteam_python_gc_collections_total{generation}` | Counter | Python GC 回调 |

指标名与 L1 Spec §16.7 完全一致；运行时通过 `RuntimeMonitor` 后台任务每 30s 采集一次。

### 10.4 Trace 契约

- `TracerProvider` 在 `configure_tracing()` 中显式构造并注册到全局；测试场景使用独立 `InMemorySpanExporter`，不得污染生产 provider。
- OTLP exporter 必须使用 async transport（`opentelemetry-exporter-otlp-proto-grpc` async transport）。
- W3C `traceparent` 必须注入到：K8s Events annotation `trace.superteam-a2a.io/parent`、structlog JSON 的 `trace_id` / `span_id` 字段、admission audit log 行。
- Span 层级见 L2-2 Design §10.2；不允许为同一个 reconcile 创建多个并行 root span。
- 失败/超时分支必须包含 `error.type` + `error.message` attribute，且 message 同样限长 1024 字符。

### 10.5 structlog 8 个必含字段

每条 JSON 日志必须包含：

1. `ts` — RFC3339 UTC timestamp；
2. `level` — debug / info / warning / error / critical；
3. `msg` — 事件名（snake_case）；
4. `trace_id` — W3C Trace Context（无时为 `null`）；
5. `crd` — Agent / AgentSet / Workflow / Memory 或 `null`；
6. `namespace` — K8s namespace 或 `null`；
7. `name` — CRD instance name 或 `null`；
8. `phase` — 当前状态或 `null`。

附加字段应避免与以上 8 个冲突；自定义字段必须以业务前缀（如 `decay.`，`lease.`）开头。

### 10.6 K8s Events 8 种 reason

| reason | type | 触发时机 | message 模板 |
|--------|------|----------|--------------|
| `ReconcileSucceeded` | Normal | reconcile 成功 | `Reconcile succeeded for {crd}/{namespace}/{name}` |
| `ReconcileFailed` | Warning | Permanent / NonRetryable 错误 | `Reconcile failed for {crd}/{namespace}/{name}: {reason}` |
| `ReconcileRetry` | Normal | Retryable 错误（含 retry_after） | `Reconcile retry after {retry_after}s for {crd}/{namespace}/{name}` |
| `CleanupCompleted` | Normal | Finalizer cleanup 成功 | `Cleanup completed for {crd}/{namespace}/{name}` |
| `CleanupFailed` | Warning | Finalizer cleanup 失败 | `Cleanup failed for {crd}/{namespace}/{name}: {reason}` |
| `LeaderAcquired` | Normal | Leader Election 获取成功 | `Operator {pod_name} acquired lease` |
| `LeaderLost` | Warning | Leader Election 失主 | `Operator {pod_name} lost lease` |
| `AdmissionRejected` | Warning | admission 拒绝请求 | `Admission rejected for {crd}/{namespace}/{name}: {reason}` |

`type` 必须是 `Normal` 或 `Warning`；自定义 reason 必须新增白名单成员并加测试，禁止运行时拼字符串。

### 10.7 关键不变量与测试 ID

- `OBS-001`：11 Operator + 4 Python runtime 指标在 `MetricsRegistry` 中唯一存在。
- `OBS-004`：同进程重复注册同名指标返回已有对象。
- `OBS-007`：`EventReason` 枚举禁止接受未列举字符串。
- `OBS-010`：structlog 8 字段在 sample 日志中全部存在。
- `OBS-013`：Histogram bucket 配置可被测试验证。
- `OBS-016`：OTel `TracerProvider` 在测试中替换为 `InMemorySpanExporter`，生产代码不持有全局。
- `OBS-019`：reconcile 失败时 span 包含 `error.type` + 限长 `error.message`。
- `OBS-022`：Event message 限长 1024 字符并被截断。
- `OBS-025`：reason 不在白名单时 `emit_event` 抛出 `ValueError`。

**关键不变量**：11 Operator 指标名 + 4 Python runtime 指标名 + 8 Event reason + 8 structlog 字段都是 wire contract，修改必须走 ADR；Operator 错误**不**通过 A2A 错误码传播。

---

## 11. RBAC 文件级契约

> 本节把 L2-2 Design §12 的 RBAC 矩阵落到 Helm 模板、ServiceAccount annotation 和 CI 校验；任何 ClusterRole/Role 规则调整必须同步更新此节与 L3-1 验证脚本。

### 11.1 文件与发布资产

| 文件 | 必须提供 | 约束 |
|------|----------|------|
| `deploy/helm/operator/templates/clusterrole.yaml` | `ClusterRole` `superteam-a2a-operator` | cluster-scoped；规则集合见 §11.2 |
| `deploy/helm/operator/templates/clusterrolebinding.yaml` | `ClusterRoleBinding` | 唯一绑定 Operator ServiceAccount |
| `deploy/helm/operator/templates/serviceaccount.yaml` | `ServiceAccount` + cert-manager annotation | 命名空间 `superteam-a2a-system` |
| `deploy/helm/operator/templates/admission_role.yaml` | `Role` `superteam-a2a-admission` | namespace-scoped TLS Secret 读取 |
| `deploy/helm/operator/templates/admission_rolebinding.yaml` | `RoleBinding` | 绑定 admission ServiceAccount（同 namespace） |
| `tests/integration/rbac/test_manifests.py` | RBAC-001~RBAC-010 | 解析 YAML + 规则差异检查 |

### 11.2 ClusterRole 规则

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: superteam-a2a-operator
rules:
  - apiGroups: ["superteam-a2a.io"]
    resources: ["agents", "agentsets", "workflows", "memories", "knowledgescopes", "knowledgeitems"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["superteam-a2a.io"]
    resources: ["agents/status", "agentsets/status", "workflows/status", "memories/status", "knowledgescopes/status", "knowledgeitems/status"]
    verbs: ["get", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods", "services", "serviceaccounts", "configmaps", "secrets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["coordination.k8s.io"]
    resources: ["leases"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["events.k8s.io"]
    resources: ["events"]
    verbs: ["create", "patch"]
  - apiGroups: ["admissionregistration.k8s.io"]
    resources: ["validatingwebhookconfigurations"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["admissionregistration.k8s.io"]
    resources: ["validatingwebhookconfigurations"]
    resourceNames: ["superteam-a2a-admission"]
    verbs: ["update", "patch"]
  - apiGroups: ["cert-manager.io"]
    resources: ["certificates"]
    verbs: ["get", "list", "watch"]
```

`resourceNames` 限定在 `superteam-a2a-admission` 一个；`namespaces` 字段不得新增非 `superteam-a2a-system` 的值。

### 11.3 ServiceAccount 与证书注入

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: superteam-a2a-operator
  namespace: superteam-a2a-system
  annotations:
    cert-manager.io/inject-ca-from: superteam-a2a-ca/superteam-a2a-ca-cert
automountServiceAccountToken: true
```

- 命名空间 `superteam-a2a-system` 必须在 Helm chart `Namespace` 模板中存在；不允许跨 chart 共享 namespace。
- `cert-manager.io/inject-ca-from` 必须指向 cluster-scoped `ClusterIssuer`（与 §9 Helm mTLS 配置保持一致）。
- `automountServiceAccountToken: true` 由 chart 默认覆盖；任何子 chart 不得关闭。
- admission webhook 复用同一 ServiceAccount；如未来拆分独立身份，§11.2 规则集合必须同步调整并加 RBAC-XXX 测试。

### 11.4 admission webhook 的 Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: superteam-a2a-admission
  namespace: superteam-a2a-system
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["admissionregistration.k8s.io"]
    resources: ["validatingwebhookconfigurations"]
    verbs: ["get", "list", "watch"]
```

Role 不允许扩展到 `pods` / `services`；admission 不直接执行 K8s 写操作。如果 v0.5+ admission 引入 K8s 调用，必须改用 ClusterRole 并加测试。

### 11.5 CI 校验与跨文档同步

- `tests/integration/rbac/test_manifests.py` 必须执行：
  1. 解析所有模板，对比 §11.2 规则集合的精确等价；
  2. 校验 `ServiceAccount` annotation 与 §9 mTLS 配置一致；
  3. 校验 `Role` 不出现 `pods` / `services` 等越权 verbs。
- `helm template` 输出在 `helm-lint` CI 任务中失败时必须停止后续构建。
- L1 Spec §10 / L2-2 Design §12 的权限矩阵更新时，本节必须同步；任一端不同步会触发 `RBAC-DRIFT` 失败。

### 11.6 关键不变量与测试 ID

- `RBAC-001`：ClusterRole 规则集合与 §11.2 精确等价。
- `RBAC-004`：`ServiceAccount` 命名空间为 `superteam-a2a-system`，annotation 引用 `ClusterIssuer`。
- `RBAC-007`：admission `Role` 不出现写权限。
- `RBAC-010`：`helm template` 在 CI 中无警告。

**关键不变量**：ClusterRole 名称 `superteam-a2a-operator`、ServiceAccount 名称 `superteam-a2a-operator`、命名空间 `superteam-a2a-system` 均为 wire contract；权限集合修改必须走 ADR；cert-manager 集成仅通过 ServiceAccount annotation 触发。

---

## 12. 测试策略文件级契约

> 本节把 L2-2 Design §13 的测试层级固化到 pytest 目录结构、夹具（fixture）和 ID 矩阵；ID 编号与既有 §5-§9 保持衔接（`TEST-` 为独立前缀），便于跨 spec 串联。

### 12.1 测试目录与夹具

```
packages/operator/tests/
├── conftest.py                       # 共享 fixture：fake k8s client、fake clock、fake election
├── unit/
│   ├── controllers/                  # 4 Controller handler 测试
│   ├── reconcilers/                  # 业务服务测试
│   ├── admission/                    # 4 validators + mutual_exclusion + DAG
│   ├── leader_election/              # AsyncLeaseClient + Election
│   ├── finalizers/                   # 4 CRD cleanup 流程
│   ├── errors/                       # 错误模型分类
│   ├── observability/                # metrics / events / logging / tracing
│   ├── config/                       # Helm values Pydantic
│   ├── rbac/                         # 模板解析与规则差异
│   └── observability_runtime/        # Python runtime 指标
├── integration/
│   ├── envtest/                      # Kopf testing harness
│   ├── admission/                    # ValidatingWebhookConfiguration 全流程
│   └── memory/                       # MemoryReconciler timer mock
├── e2e/
│   ├── kind/
│   │   ├── agent_lifecycle.py        # E2E-001~E2E-010
│   │   ├── workflow_dag.py
│   │   └── memory_reconcile.py
│   └── conformance/
│       └── a2a_wire_contract.py      # 4 个项目扩展 A2A method + 11 错误码
└── perf/
    └── reconcile_throughput.py       # v0.5+ 启动；v0.1 仅占位
```

共享夹具：

- `fake_k8s_client`：模拟 `kubernetes_asyncio`，拒绝真实网络。
- `fake_clock`：UTC 时钟注入；用于 `batch_decay`、`Lease.renew_time` 等时间敏感逻辑。
- `fake_election`：替代 `Election`，始终返回 `is_leader=True`；通过 fixture 参数控制。
- `fake_metrics`：使用 `CollectorRegistry` 替代默认注册，避免跨测试状态污染。

### 12.2 单元测试

**目标**（与 L2-2 Go baseline §13.1 一致）：

- 行覆盖 ≥ 80%，分支覆盖 ≥ 75%，关键路径（reconcile / cleanup / admission）覆盖 ≥ 95%。

**强制工具链**（ADR-0005 §9 + 宪法 §9.7）：

- `pytest`、`pytest-asyncio`、`pytest-cov`、`pytest-mock`、`hypothesis`；
- `respx`（httpx mock）、`kubernetes_asyncio` fake client、`prometheus_client.CollectorRegistry`；
- `ruff`、`pyright --strict`、`bandit`、`pip-audit` 在 CI 中以 gate 形式运行。

每个 `*.py` 文件必须有同名的 `test_*.py`；新增文件必须附带 ≥ 80% 行覆盖，否则 CI 失败。

### 12.3 集成测试

**envtest**（Kopf testing harness）覆盖：

- 4 CRD 完整生命周期：create / update / delete + Finalizer cleanup；
- admission webhook 完整流程：`ValidatingWebhookConfiguration` 注册 + 422/400 错误响应 + 拒绝请求未写 etcd；
- Leader Election 多副本场景：envtest 不支持多实例 → 用 fake `AsyncLeaseClient` 模拟；
- MemoryReconciler 定时任务：`@kopf.timer` 触发用 mock time；
- mTLS 集成：cert-manager fake issuer 生成 Secret 供 webhook 加载。

envtest 已知限制必须在文档中明示：

- 不支持 Helm → 测试直接 apply manifest；
- 不支持 cert-manager → 使用 fake Secret；
- 不支持多 Operator 副本 → Leader Election 用单副本 + fake 并发场景验证。

### 12.4 E2E 测试

**测试场景**（≥ 10 个 E2E case）：

- `E2E-001`：Agent CRD 创建 → Pod Ready + `AgentStatus.phase=Ready`。
- `E2E-002`：AgentSet CRD（replicas=3）→ 3 个 Agent 全部 Ready。
- `E2E-003`：合法 DAG Workflow → `WorkflowStatus.phase=Running`。
- `E2E-004`：非法 DAG Workflow → admission 拒绝 + `AdmissionRejected` Event。
- `E2E-005`：Memory CRD 创建 → `MemoryStatus` 初始化 + MemoryReconciler 触发 decay。
- `E2E-006`：KnowledgeItem + Memory 同时引用 → admission 互斥拒绝。
- `E2E-007`：Agent 删除 → Finalizer cleanup → Pod 优雅停止 + `CleanupCompleted`。
- `E2E-008`：Operator 重启 → Lease 自动让位 + 重新选举 + `LeaderAcquired`/`LeaderLost` Event。
- `E2E-009`：mTLS 证书轮换 → admission webhook 不停机 + 0 个 4xx/5xx 漏接。
- `E2E-010`：11 Operator 指标全量暴露，labels 全部填充合法值。

E2E 跑在 kind（K8s in Docker）集群中；每次运行必须使用独立 cluster 名称避免残留；CI 中使用 ephemeral runner。

### 12.5 Conformance 测试

与 L2-1 Python v0.2.0 Spec §11.5 一致：

- 4 个项目扩展 A2A method（`queryKnowledge` / `getKnowledgeItem` / `recordMemory` / `queryMemory`）的 JSON wire shape 一致性；
- Operator 通过 a2a-sdk client 调用 L2-4 Knowledge Service 4 method；
- 11 个 A2A JSON-RPC 错误码与 L2-1 Spec §8.4 字节级一致；
- contract test 失败时禁止合并（CI gate）。

### 12.6 覆盖率与 CI 门禁

- `pytest --cov=superteam_a2a.operator --cov-fail-under=80` 强制通过。
- `pyright --strict` 与 `ruff check` 失败等同测试失败。
- `bandit -r packages/operator/src` 与 `pip-audit` 高危漏洞数必须为 0。
- 性能测试 `reconcile_throughput.py` 在 v0.1 仅占位（标记 `@pytest.mark.skip` + 引用 L3-1 移交问题），CI 不得因此失败。

### 12.7 关键不变量与测试 ID

- `TEST-001`：新增 `*.py` 必须有同名 `test_*.py`。
- `TEST-005`：关键路径覆盖 ≥ 95% 由 CI 阈值保证。
- `TEST-009`：`ruff` + `pyright` + `bandit` + `pip-audit` 全部通过。
- `TEST-012`：`pytest --cov-fail-under=80` 通过。
- `TEST-016`：envtest fixture 在 60 秒内完成启动。
- `TEST-019`：E2E 必须从干净 kind 集群开始，禁止复用。
- `TEST-022`：conformance 失败 = 合并阻断。
- `TEST-025`：所有错误日志 message 长度 ≤ 1024。

**关键不变量**：测试 ID 在 §5-§9 已使用的 LE/ASYNC/FIN/ERR/HELM/OBS/RBAC 之外，新增前缀 `TEST-` 与 `E2E-`；覆盖率与门禁是合并前提；Operator 与 A2A 错误码的 wire contract 由 conformance 套件锁定。

---

## 13. 工具链与部署形态文件级契约

> 本节把 L2-2 Design §3（包结构）+ §11（Helm values 已落地在 §9）+ §14（部署形态）压缩成可执行的工程契约；覆盖 pyproject、uv workspace、Dockerfile、Helm chart 顶层和部署时序。所有产物路径、依赖版本约束和镜像 tag 属于 v0.2 部署 contract；变更必须走 ADR。

### 13.1 文件与产物

| 文件 | 必须提供 | 约束 |
|------|----------|------|
| `packages/operator/pyproject.toml` | PEP 621 metadata + 依赖列表 | Python 3.12+；`[project.scripts]` 含 `superteam-a2a-operator` |
| `packages/operator/uv.lock` | uv lockfile | CI 与本地 lock 必须一致（`uv lock --check`） |
| `packages/operator/Dockerfile` | 多阶段构建 | builder + runtime 两层；runtime 仅 `python:3.12-slim` + 非 root 用户 |
| `packages/operator/src/superteam_a2a/operator/__main__.py` | `python -m superteam_a2a.operator` 入口 | 调用 `OperatorMain.run()` |
| `deploy/helm/operator/Chart.yaml` | Helm chart 元信息 | `apiVersion: v2`；`name: superteam-a2a-operator`；`appVersion` 与 `pyproject.__version__` 同步 |
| `deploy/helm/operator/values.yaml` | 默认 values | 必须可被 §9 Pydantic schema 严格校验 |
| `deploy/helm/operator/values.schema.json` | 自动生成 | 与 `HelmValues.model_json_schema(by_alias=True)` 无差异（CI 校验） |
| `deploy/helm/operator/templates/deployment.yaml` | Operator + admission webhook Deployment | 端口 8080 / 8443；探针 /healthz / /readyz |
| `deploy/helm/operator/templates/service.yaml` | metrics + admission webhook Service | 双端口 Service；端口名固定 `http` / `https` |
| `deploy/helm/operator/templates/webhookconfig.yaml` | `ValidatingWebhookConfiguration` | `failurePolicy: Fail`；`admissionReviewVersions: [v1]` |
| `deploy/helm/operator/templates/leader_election_lease.yaml` | Lease 资源占位 | 仅当 `leaderElection.enabled=true` 时渲染 |
| `tests/integration/helm/test_chart.py` | HL-001~HL-010 | `helm template` + `helm lint` + `values.schema.json` 校验 |

### 13.2 pyproject.toml 关键字段

```toml
[project]
name = "superteam-a2a-operator"
version = "0.2.0"
description = "superteam-a2a Operator Core — 4 CRD lifecycle + admission + Leader Election"
requires-python = ">=3.12,<3.13"
license = { text = "Apache-2.0" }
authors = [{ name = "CoderZhangfujiang" }]
dependencies = [
    "kopf>=1.37",
    "kubernetes-asyncio>=30.0",
    "pydantic>=2.6",
    "prometheus-client>=0.20",
    "structlog>=24.1",
    "opentelemetry-api>=1.24",
    "opentelemetry-sdk>=1.24",
    "opentelemetry-exporter-otlp-proto-grpc>=1.24",
    "anyio>=4.3",
    "httpx>=0.27",
    "tenacity>=8.2",
]

[project.scripts]
superteam-a2a-operator = "superteam_a2a.operator.__main__:main"
```

约束：

- `requires-python` 锁定 `>=3.12,<3.13`；ADR-0005 §2.2 允许的 Python 3.12+ 视为最低版本。
- 运行时依赖只能新增 Python 生态库；引入第二核心语言（Go / Rust / C++ 扩展）必须走 ADR。
- `[project.optional-dependencies.dev]` 仅用于本地开发（pytest / ruff / pyright / bandit / pip-audit）；**禁止**进入运行时镜像。
- `dependencies` 中所有库必须有 SPDX 兼容 license（与 §3.8 一致）。
- `version` 字段必须与 `Chart.yaml` 的 `appVersion` 同步；CI 中使用脚本验证 `pyproject.__version__ == chart.appVersion`。

### 13.3 uv workspace 集成

`superteam-a2a` 在仓库根使用 uv workspace 统一管理多包：

```toml
# pyproject.toml（仓库根）
[tool.uv.workspace]
members = [
    "packages/operator",
    "packages/a2a-core",
    "packages/adapter-sdk",
    "packages/knowledge-service",
    "packages/memory-backend",
    "packages/hello-agent",
]
```

- 仓库根 `pyproject.toml` 必须包含 `[tool.uv.workspace]`；`packages/operator` 必须在 `members` 列表中。
- `uv lock` 在仓库根执行；Operator 包的 `uv.lock` 不再单独存在。
- 跨包导入遵循 §2.2 边界规则；CI 通过自定义 Ruff 规则 `ST-A2A-BOUNDARY` 强制。
- 单包构建：`uv build --package superteam-a2a-operator`，产物 `dist/superteam_a2a_operator-0.2.0-*.whl`。

### 13.4 Dockerfile（多阶段 · 非 root）

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS builder
WORKDIR /build
RUN pip install --no-cache-dir uv==0.4.18
COPY pyproject.toml uv.lock ./
COPY packages/operator ./packages/operator
RUN uv export --frozen --no-hashes --package superteam-a2a-operator \
    --format requirements-txt > /tmp/requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt

FROM python:3.12-slim AS runtime
RUN groupadd --system --gid 65532 superteam && \
    useradd --system --uid 65532 --gid superteam --no-create-home superteam
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels superteam-a2a-operator && \
    rm -rf /wheels
USER 65532:65532
EXPOSE 8080 8443
ENTRYPOINT ["superteam-a2a-operator"]
```

契约：

- runtime 阶段**禁止**包含 `gcc` / `git` / `pip` / `uv`；只能保留 `python` 可执行文件和 stdlib + 安装的 wheels。
- 非 root 用户固定 `uid=65532` / `gid=65532`；Linux capabilities 必须 `drop=["ALL"]` + 仅 `add=["NET_BIND_SERVICE"]`（8443 < 1024 时需要）。
- 镜像 base 固定 `python:3.12-slim`；不得使用 `latest` 或非 slim tag。
- 镜像必须包含 `HEALTHCHECK`（与 §13.5 探针一致）；CI 使用 `docker inspect` 校验存在。
- 镜像 tag 与 `pyproject.version` + `Chart.appVersion` 三方一致；CI 校验三处相等。
- 多架构（`linux/amd64` + `linux/arm64`）在 v0.1 不强制；v0.5+ 启动；CI 必须记录基线架构。

### 13.5 Deployment 探针与生命周期

- `livenessProbe`：`httpGet /healthz` 端口 8080；`initialDelaySeconds=30`，`periodSeconds=10`，`timeoutSeconds=3`，`failureThreshold=3`。
- `readinessProbe`：`httpGet /readyz` 端口 8080；`initialDelaySeconds=5`，`periodSeconds=5`，`timeoutSeconds=2`，`failureThreshold=2`。
- `/healthz`：liveness 端点，必须在 Leader Election 初始化**前**就绪；返回 200 当且仅当进程未僵死。
- `/readyz`：readiness 端点，必须在 Lease 初始化 + admission webhook 启动**之后**才返回 200；非 leader 副本 `/readyz` 也必须 200（因为 admission webhook 在所有副本上可用）。
- `/metrics`：端口 8080，路径 `/metrics`；不得启用 basic auth（由 ServiceMonitor 自行控制）。
- 资源 requests / limits 由 §9 Helm values 控制；`requests.cpu=200m`、`requests.memory=256Mi`、`limits.cpu=1000m`、`limits.memory=1Gi` 是 v0.2 默认。
- `replicaCount` 默认 2；Operator 副本**必须**部署在不同的 K8s 节点（`topologySpreadConstraints` 或 `podAntiAffinity` 推荐软约束；v0.1 不强制）。

### 13.6 Helm chart 关键字段

- `apiVersion: v2` + `name: superteam-a2a-operator`；`type: application`；`version: 0.2.0`（chart 自身版本，独立于 appVersion）。
- `appVersion` 必须等于 `pyproject.__version__`；CI 失败时阻塞 release。
- `kubeVersion` 约束 `>=1.27, <1.32`（envtest 验证范围；v0.2 锁定）。
- 依赖 chart：暂不依赖外部 chart（cert-manager 由用户集群预装）。
- `values.yaml` 必须可被 §9 `HelmValues` Pydantic 模型严格校验；CI `helm lint` + `helm template` 双重验证。
- `templates/` 渲染必须满足：`Deployment` + `Service` + `ServiceAccount` + `ClusterRole` + `ClusterRoleBinding` + `Role` + `RoleBinding` + `ValidatingWebhookConfiguration` + 可选 `Lease` + 可选 `Namespace`。
- `NOTES.txt` 必须说明获取 Operator pod 名 + 验证 admission webhook 已注册的 `kubectl get validatingwebhookconfigurations` 命令。

### 13.7 部署时序

```text
helm install → 创建 Namespace
             → 创建 ServiceAccount + ClusterRoleBinding
             → 创建 Deployment (replicaCount=2)
             → 创建 ValidatingWebhookConfiguration
             → 创建 admission Role + RoleBinding
             → 创建 Service（双端口）
             → 创建可选 Lease

Pod 启动:
  pre-hook     → 镜像 pull + 探针端口暴露
  entrypoint   → superteam-a2a-operator
                 ├─ 解析 Helm values（Pydantic）
                 ├─ 初始化 K8s async client + OTel
                 ├─ 启动 admission webhook（8443 / TLS）
                 ├─ 启动 metrics server（8080）
                 ├─ /healthz 立即返回 200
                 ├─ 启动 Leader Election task
                 ├─ /readyz 在 Lease acquire + webhook 就绪后返回 200
                 └─ Kopf 处理 CRD watch
```

关键不变量：

- admission webhook 必须在 `/readyz` 返回 200**之前**完成 TLS 加载 + ValidatingWebhookConfiguration 注册；否则 API Server 无法调用 webhook → CRD 写入失败。
- 副本之间无强启动顺序；非 leader 副本会重复尝试 acquire Lease，全部就绪后由 Lease 决定唯一 leader。
- 删除 chart 顺序：先 `kubectl delete validatingwebhookconfigurations`（避免 webhook 阻止 Finalizer cleanup）→ `helm uninstall` → 残留资源（CRD / CR）由用户决策。
- 升级期间：Helm `pre-upgrade` hook 仅打印「确认所有副本已就绪」日志；v0.1 不执行 webhooks conversion（L3-1 移交）。

### 13.8 镜像分发与版本

- 镜像仓库：默认 `ghcr.io/coderzhangfujiang/superteam-a2a-operator`。
- Tag 规则：`<version>`、`latest`（仅 main 分支）、`<version>-dev.<short-sha>`（PR build）。
- 多架构：v0.1 仅 `linux/amd64`；v0.5+ 启动 `linux/arm64`。
- 签名：v0.5+ 引入 `cosign` keyless 签名（sigstore）；v0.1 记录为开放问题（移交 L3-1）。
- SBOM：v0.5+ 使用 `syft` 生成 CycloneDX SBOM；v0.1 移交 L3-1。

### 13.9 关键不变量与测试 ID

- `TOOL-001`：`pyproject.requires-python` 锁定 `>=3.12,<3.13`。
- `TOOL-004`：runtime 镜像不含 `pip` / `uv` / `git` / `gcc`。
- `TOOL-007`：镜像 user 固定 `uid=65532`。
- `TOOL-010`：`pyproject.version` == `Chart.appVersion`（CI 校验）。
- `TOOL-013`：`uv lock --check` 在 CI 中无差异。
- `TOOL-016`：`helm template` 无 warning，`helm lint` 通过。
- `TOOL-019`：`values.schema.json` 与 `HelmValues.model_json_schema(by_alias=True)` 无差异。
- `TOOL-022`：`/healthz` 在 Leader Election 初始化前返回 200。
- `TOOL-025`：`/readyz` 在 admission webhook + Lease 初始化**之后**才返回 200。
- `TOOL-028`：删除 chart 时 ValidatingWebhookConfiguration 优先清理（hooks 顺序）。
- `TOOL-031`：镜像 manifest 仅包含 `linux/amd64`（v0.1 基线）。
- `TOOL-034`：cross-package boundary Ruff 规则 `ST-A2A-BOUNDARY` 在 CI 中通过。

**关键不变量**：Operator 镜像 + Helm chart 与 `pyproject.version` 三方一致；非 root + 最小 runtime base；admission webhook 与 Leader Election 启动顺序由 readiness 探针强制；`/readyz` 不因为非 leader 而返回 5xx（admission 必须始终可用）。

---

## 14. 验收清单

> 本节是 L2-2 Spec v0.2.0 升级前的可勾选验收基线；每条验收点对应一处具体设计/Spec 位置或测试 ID。L2-2 Spec 评审（§A-§G 10 维度）必须以本清单为唯一凭证，**任何未勾选项必须解释**或推迟到 v0.2.1 / v0.5 路线图中。

### 14.1 评审维度验收（§A-§G 10 项）

| 维度 | 验收点 | 对应位置 | 勾选 |
|------|--------|----------|------|
| **A. 文档完整性** | §0-§15 + 附录 A 全部存在，0 个 TODO/待补完标记 | 本 Spec 全文 | ☐ |
| | 头部包含版本/状态/supersede/依据 4 段 | 头部 | ☐ |
| | supersede 指针指向 Go baseline 归档 | 头部 | ☐ |
| **B. 设计深度** | 4 Controllers + admission + Leader Election + Finalizer + async-first + 错误模型 + 可观测性 + Helm values + RBAC + 测试策略 + 工具链 11 子模块全覆盖 | §3-§13 | ☐ |
| | Pydantic schema 在 §3 + §9 + §10 + §13.2 全部展开 | §3.1 / §9.2 / §10.1 / §13.2 | ☐ |
| **C. 宪法一致性** | §3.8 Python-first 强制通过所有 `import` 边界 | §2.2 + §13.2 | ☐ |
| | §6 mTLS 通过 cert-manager 集成 | §11.3 + §13.4 | ☐ |
| | §7 可观测性 11 指标 + 4 Python runtime 指标全覆盖 | §10.2 + §10.3 | ☐ |
| | §9.7 静态质量门禁（ruff + pyright + bandit + pip-audit） | §12.6 | ☐ |
| | §14.4 评审门禁：10 维度 + 验收清单 | §14.1 | ☐ |
| | §16 会话纪律：本 Spec 由 5 个独立会话（#27-#31）补完 | MEMORY 索引 | ☐ |
| **D. 依赖方向** | Operator 不依赖 L2-3 Adapter SDK | §2.2 | ☐ |
| | Operator 不实现 A2A 协议 | §2.2 | ☐ |
| | Operator 不实现 Knowledge/Memory 业务语义 | §2.2 | ☐ |
| | admission webhook 不调用 K8s API | §2.2 | ☐ |
| | Reconciler services 不依赖 Kopf | §2.2 | ☐ |
| **E. 性能约束** | Helm `python.workers: 1` 强制 | §9.2 + §9.3 | ☐ |
| | K8s Lease 30s TTL + 10s 续约 + 3 次失败让位 | §5.2 | ☐ |
| | MemoryReconciler 60s + CPU offload 阈值 1000 | §6.3 + §9.2 | ☐ |
| | 11 Operator 指标 + 4 Python runtime 指标 | §10.2 + §10.3 | ☐ |
| **F. 跨文档一致性** | 与 L1 v0.2.0 + L2-1 v0.2.0 + L2-3 v0.1.0 + L2-4 v0.1.0 同步 | §F 同步记录 | ☐ |
| | L1 Architecture §3.5.2/§3.5.3 模块映射正确 | §1.1 + 附录 A | ☐ |
| | L1 Spec §16 指标 + §7 状态机 + §9-§10 资源/限流 一致 | §10.2 + §3.1 | ☐ |
| | L2-1 A2A Spec §2.5 (client) + §16.1 (OTel) 一致 | §13.3 | ☐ |
| | ADR-0002/0003/0005 字段约束一致 | 全文 | ☐ |
| | 宪法 v0.5.0 + ADR-0005 supersede 指针 | 头部 + 附录 A | ☐ |
| **G. Python-first** | Kopf + kubernetes_asyncio + Pydantic v2 + structlog + OTel + cert-manager | §13.2 | ☐ |
| | 11 个运行时依赖无第二核心语言 | §13.2 | ☐ |
| | Dockerfile runtime 仅 `python:3.12-slim` | §13.4 | ☐ |
| | cross-package boundary Ruff 规则 | §13.3 + §13.9 | ☐ |

### 14.2 测试 ID 验收（95 个 ID 全覆盖）

- **LE-001~LE-024（24）** — Leader Election：`AsyncLeaseClient` 8 + `Election` 12 + Controller gate 4；详见 §5.5。
- **ASYNC-001~ASYNC-012（12）** — async 边界 + CPU offload；详见 §6.5。
- **FIN-001~FIN-032（32）** — Finalizer 4 名称映射 + 4 CRD cleanup 流程 + 错误路径；详见 §7.5。
- **ERR-001~ERR-027（27）** — 错误模型 + 分类矩阵 + wrapper + 边界；详见 §8.5。

  > ⚠️ 本 Spec §8.5 描述的 ERR ID 编号最大到 ERR-027；§10-§13 增补时未复用 ERR- 前缀，避免与 §8 测试 ID 冲突。
- **HELM-001~HELM-032（9 个有效 ID）** — Helm values + Pydantic schema + 跨字段约束；详见 §9.4。
- **OBS-001~OBS-025（9 个有效 ID）** — 可观测性：metrics + tracing + logging + events；详见 §10.7。
- **RBAC-001~RBAC-010（4 个有效 ID）** — RBAC 模板 + ServiceAccount + admission Role + CI 校验；详见 §11.6。
- **TEST-001~TEST-025（8 个有效 ID）** + **E2E-001~E2E-010（10 个 E2E case）** — 单元 + 集成 + E2E + conformance；详见 §12.7 + §12.4。
- **TOOL-001~TOOL-034（12 个有效 ID）** — 工具链与部署；详见 §13.9。

合计 95 个 ID（部分区间 ID 为 §内部分配编号；CI 实际注册 ID 数量与 §内 ID 矩阵一致即可）。

### 14.3 部署与文档交付验收

- ☐ 11 个 Operator 指标 + 4 Python runtime 指标全量暴露（`/metrics` 路径）
- ☐ 8 个 Event reason 在代码与文档严格匹配
- ☐ structlog 8 必含字段在 sample 日志中全部存在
- ☐ 4 个 Finalizer 名称与 K8s CRD 注解一致
- ☐ `pyproject.version` == `Chart.appVersion`（CI 校验）
- ☐ `values.schema.json` 与 `HelmValues.model_json_schema(by_alias=True)` 无差异
- ☐ `helm template` + `helm lint` CI 通过
- ☐ 镜像 manifest 仅 `linux/amd64`（v0.1 基线）
- ☐ `ruff` + `pyright --strict` + `bandit` + `pip-audit` 在 CI 通过
- ☐ `pytest --cov-fail-under=80` 通过
- ☐ E2E 10 个 case 全部从干净 kind 集群开始
- ☐ conformance 与 L2-1 Spec §8.4 11 JSON-RPC 错误码字节级一致
- ☐ 附录 A 跨模块引用 12 条全勾选
- ☐ MEMORY 索引条目 #27-#31 全部存在
- ☐ 宪法 v0.5.0 + ADR-0005 supersede 指针在头部 + 附录 A 完整

### 14.4 评审与归档验收

- ☐ L2-2 Spec 评审报告 `docs/reviews/l2-2-operator-core-spec-review.md` 存在
- ☐ 评审报告采用 §A-§G 10 维度模板
- ☐ Design + Spec 双文档升级 v0.2.0
- ☐ Go baseline v0.1.0 归档完整（Design + Spec 两份）
- ☐ L1 Architecture + L1 Spec 跨文档同步标记（`l2-2-supersede` 指针）
- ☐ L2-1 A2A Spec + L2-3 Adapter Spec + L2-4 Knowledge Spec 跨文档同步
- ☐ ROADMAP + README + CHANGELOG 同步标记 v0.2.0 L2-2 通过
- ☐ 宪法 v0.5.0 §16 纪律：会话 #27-#31 累计水位 < 80% 临界

### 14.5 关键不变量与测试 ID

- `ACCEPT-001`：§14.1 10 维度全部勾选或显式解释。
- `ACCEPT-004`：§14.2 95 个测试 ID 全部映射到具体测试函数或 IT/E2E 用例。
- `ACCEPT-007`：§14.3 部署与文档交付 15 条全部勾选。
- `ACCEPT-010`：§14.4 评审与归档 8 条全部勾选。
- `ACCEPT-013`：未勾选项必须在评审报告 `L2-2 Operator Core Spec Review` 附录列出推迟版本（v0.2.1 / v0.5 / v1.0）。

**关键不变量**：验收清单是 L2-2 Spec 升级 v0.2.0 的唯一凭证；任何未勾选项必须附推迟版本与原因；评审报告必须引用本节行号。

---

## 15. 开放问题（v0.2-draft-full 收敛清单）

> ✅ **本节为 v0.2-draft-full 完整版**——在 L2-2 Design v0.2.0 §14 基础上，叠加 **本 Spec §5-§14 起草期间新发现的 2 项收敛 + 4 项细化**，最终收敛为 **20 项**（其中 16 项在 §5-§14 已有最终决策 / 4 项移交 L3-1 / 1 项移交 v0.5+）。
> **完整讨论待 L3-1 文件级 Spec 起草时再细化实现细节**；本 Spec 给出"问题描述 + 默认决策 + 收敛位置 + 移交版本"四元组。

### 15.1 开放问题收敛状态总览

| 类别 | 数量 | 收敛位置 | 移交位置 |
|------|------|----------|----------|
| L2-2 Go baseline 继承 | 5 | 5/5 已在 §5-§14 给出最终决策 | 0（v0.1 已固化） |
| kopf-python spike 已知未决 | 5 | 4/5 已在 §5-§14 给出最终决策 | 1 项移交 L3-1 |
| 本 Design 新发现 | 8 | 7/8 已在 §5-§14 给出最终决策 | 1 项移交 L3-1 |
| **本 Spec 起草期间新发现** | **2** | **1/2 在 §5-§14 给出最终决策** | **1 项移交 L3-1** |
| **合计** | **20** | **16** | **3 移交 L3-1 + 1 移交 v0.5+** |

### 15.2 继承自 L2-2 Go baseline（5 项 · 全部已在 §5-§14 收敛）

| # | 开放问题 | 默认决策（v0.2 Spec） | 收敛位置 |
|---|----------|---------------------|----------|
| Q-01 | reconcile 性能：Agent > 1000 是否需要 informer 分片 | v0.2 不分片；`superteam_operator_reconcile_queue_depth` 指标暴露 + 监控告警；v0.5+ 触发分片决策 | §10.2 + §14.3 |
| Q-02 | Workflow 表达式引擎（v0.1 静态 inputs） | v0.1 仅静态 inputs；v0.5 引入 CEL；Operator Spec 留 `WorkflowExpression` stub 接口（不允许 v0.1 误用） | §3.4 + §15.4 OPEN-Q2 |
| Q-03 | Memory 衰减频率（1h 是否合理） | v0.2 默认 60s；可配置 `memoryReconciler.intervalSeconds` Helm values（30-300s） | §6.3 + §9.2 |
| Q-04 | AgentSet owns Agent 删除处理 | Adoption 模式（`orphanDeletion=false`）+ Finalizer `superteam.a2a.io/agentset-adoption` | §7.3 + §7.5 |
| Q-05 | Operator 升级时避免 reconcile 抖动 | webhooks conversion + Helm pre-upgrade hook + grace period 30s | §13.7 + §13.9 |

### 15.3 继承自 kopf-python spike D-1~D-5（5 项 · 4 收敛 + 1 移交 L3-1）

| # | 开放问题 | 默认决策（v0.2 Spec） | 收敛位置 |
|---|----------|---------------------|----------|
| Q-06 | Kopf `@kopf.Singleton` event loop 绑定 | Uvicorn 单 worker = 单 event loop；Singleton 无冲突；Kopf handlers 中禁止 `@kopf.Singleton` 与 `@kopf.timer` 共存 | §5.5 + §6.2 |
| Q-07 | K8s Lease 续约失败处理 | 自动让位（renew 失败 3 次 × 10s 触发让位）；让位前触发 K8s Event `LeaseLost` + structlog INFO | §5.2 + §5.5 |
| Q-08 | admission webhook TLS 证书轮换 | cert-manager 集成（`cert-manager.io/inject-ca-from` 注解）+ 30 天自动轮换；**L3-1 验证**实际轮换是否触发 pod 热加载证书 | §11.3 + §11.6 |
| Q-09 | MemoryReconciler CPU offload 阈值 | Memory CR 数量 > 1000 时启用 `anyio.to_thread.run_sync`；阈值 Helm values `memoryReconciler.cpuOffloadThreshold` | §6.3 + §9.2 |
| Q-10 | Operator 升级期间 reconcile 抖动抑制 | webhooks conversion（CRD schema 升级前先 freeze）+ Helm pre-upgrade hook（pre-upgrade pod 启动前 drain leader）；Kopf 自带 resync period 60s 平滑 | §13.7 + §13.9 |

### 15.4 继承自 L2-2 Design v0.2.0 §14.3 新发现（8 项 · 7 收敛 + 1 移交 L3-1）

| # | 开放问题 | 默认决策（v0.2 Spec） | 收敛位置 |
|---|----------|---------------------|----------|
| Q-11 | 4 CRD validators 错误响应格式 | `reason` 字段 snake_case（如 `invalid_workflow_dag`）+ `http_status` 数字（400/422）；AdmissionResponse Pydantic 模型定义 | §4.2 + §8.4 |
| Q-12 | Kopf handlers 异常是否触发 Status 更新 | 触发：`status.phase=Failed` + `conditions[]` 记录（type=`ReconcileFailed` / reason=`ExceptionClass` / message 含 trace_id） | §8.3 + §10.5 |
| Q-13 | MemoryReconciler Leader Election 关系 | 复用同一 K8s Lease（单一 leader）；非 leader 副本仅 reconcile CR，**不执行** MemoryReconciler timer | §5.4 + §6.3 |
| Q-14 | admission webhook 拒绝审计日志格式 | structlog（level=WARN，字段=trace_id/reason/crd/namespace/name）+ K8s Event `AdmissionDenied` 双写；**L3-1 验证** OTLP 转发链路 | §10.6 + §11.3 |
| Q-15 | Operator CrashLoopBackOff 时的 Leader Lease 释放 | grace period 30s（Kopf 自身）+ K8s Lease TTL 30s 自动过期；其他副本 10s 后重新获取 lease | §5.2 + §5.5 |
| Q-16 | structlog JSON 日志 trace_id 注入位置 | 注入到 K8s Events（annotation）+ structlog processor + admission audit log；统一使用 OTel `trace_id` | §10.4 + §10.6 |
| Q-17 | Helm values 验证失败错误信息可读性 | Pydantic ValidationError 翻译为 YAML 路径 + 字段名（如 `values.python.workers: must be 1 (got 4)`） | §9.4 + §13.6 |
| Q-18 | Operator + admission 共进程崩溃隔离 | subprocess 隔离：admission webhook **独立 process**（同 Deployment 不同 container）；Operator 崩溃不影响 admission；通过 shared emptyDir 卷共享 PID 1 信号 | §4.1 + §13.4 |

### 15.5 本 Spec 起草期间新发现（2 项）

| # | 开放问题 | 默认决策 | 收敛 / 移交位置 |
|---|----------|----------|-----------------|
| OPEN-Q-01 | **Pydantic v2 `model_json_schema(by_alias=True)` 与 Helm `values.schema.json` 的隐式字段重命名** | `values.schema.json` 由 `HelmValues.model_json_schema(by_alias=True)` 在 CI 中生成；任何手工修改被校验脚本拦截；版本号增量 | §9.4 + §13.9（已收敛） |
| OPEN-Q-02 | **`@kopf.on.resume` 与 admission webhook 启动顺序**：Kopf handlers 在 webhook 未就绪时已开始 reconcile CR，可能绕过 admission | Helm pre-install hook（Job）必须等待 admission webhook `/readyz` 返回 200 才放行；**L3-1 验证** Operator 启动顺序契约 | §13.7（移交 L3-1） |

### 15.6 开放问题汇总与移交

- **本 Spec 已收敛**：**16 项**（Q-01 / Q-02 / Q-03 / Q-04 / Q-05 / Q-06 / Q-07 / Q-09 / Q-10 / Q-11 / Q-12 / Q-13 / Q-15 / Q-16 / Q-17 / Q-18 / OPEN-Q-01）—— 默认决策已写入 §3-§13，评审者可直接通过 §15.2-§15.5 表格中的"收敛位置"列跳转
- **移交 L3-1**：**3 项**（Q-08 证书轮换实测 / Q-14 审计日志 OTLP 转发 / OPEN-Q-02 启动顺序契约）
- **未来版本**：**1 项**（Q-02 Workflow 表达式引擎 v0.5+ CEL）—— §3.4 留 stub 接口
- **收敛率**：**16 / 20 = 80%**（远高于 L1 v0.2.0 收敛率 70%；原因是 L2-2 Design v0.2.0 已先收敛大部分决策）

### 15.7 与 L2-2 Design v0.2.0 §14 的差异

| 差异点 | Design §14 状态 | Spec §15 状态 | 原因 |
|--------|----------------|---------------|------|
| 开放问题总数 | 18 项 | **20 项** | 本 Spec 起草期间新增 2 项（OPEN-Q-01 Pydantic schema CI 生成 / OPEN-Q-02 Kopf resume 与 admission 启动顺序） |
| 已收敛数 | 5 项（Design 已给默认决策） | **16 项** | Spec §5-§14 把 Design 的"默认决策"细化为"具体实现契约 + Pydantic 字段 + Helm values 默认值" |
| 移交 L3-1 数 | 11 项 | **3 项** | 大部分 Design 移交项已在 Spec §5-§14 收敛；仅 Q-08 / Q-14 / OPEN-Q-02 仍需 L3-1 实测 |
| 未来版本数 | 1 项（Q-2） | **1 项** | 完全对齐 |

### 15.8 开放问题测试 ID（OPEN- 前缀）

- `OPEN-Q-01`~`OPEN-Q-20`：20 项 ID；§15.2-§15.5 表格中每个 Q-XX 即对应一个 ID
- `OPEN-Q-21`~`OPEN-Q-025`：预留 5 项（v0.5+ 引入 Workflow CEL 后追加）
- **OPEN- 测试 ID 不计入 §14.2 验收矩阵**（验收矩阵仅算实际测试函数或 E2E case；开放问题 ID 仅作为"决策追踪器"）

---

## 附录 B: ADR / Constitution 引用矩阵（v0.2-draft-full）

> ✅ **本附录为 v0.2-draft-full 新增**——L2-2 Design v0.2.0 无对应附录（Design 通过 §0"依据"段直接引用 ADR/Constitution）；Spec 作为 L4 实施基线，需要**字段级**精确映射 ADR/Constitution 约束到本 Spec 章节，确保评审者与 L4 实现者能逐条追溯。

### B.1 ADR 引用矩阵

| ADR | 标题 | 关键约束章节 | 本 Spec 引用位置 | 状态 |
|-----|------|--------------|------------------|------|
| **ADR-0001** | v1 Scope Statement | §1 范围 + §2 排除 | §1.1 使命边界 + §1.2 模块外 | ✅ 2026-07-23 |
| **ADR-0002** | 知识管理设计 | §2 KnowledgeScope + §3 KnowledgeItem + §5 生命周期 | §2.2 模块外（L2-4 负责）+ §6.4 MemoryReconciler 集成点 | ✅ 2026-07-23 |
| **ADR-0003** | Memory 设计 | §4.3 decay 频率 + §6 Memory CRD + §6.5 MemoryReconciler | §6.3 MemoryReconciler timer + §9.2 `memoryReconciler.intervalSeconds` + §15.2 Q-03 | ✅ 2026-07-23 |
| **ADR-0004** | v0.1 Scope Extension（Knowledge + Memory） | §1 扩展范围 + §3 排除 | §1.1 使命边界（Knowledge/Memory 业务语义归 L2-4） | ✅ 2026-07-23 |
| **ADR-0005** | Python-first 技术栈 | §3.1 Operator Core 模块映射 + §7 单进程原则 + §8 SDK 门禁 + §13.1 OTel/指标迁移 | §13.2 pyproject.toml 依赖 + §13.3 uv workspace + §2.2 依赖方向（D 维度）+ §10 可观测性 | ✅ 2026-07-24 |

### B.2 Constitution 引用矩阵（v0.5.0）

| 宪法条款 | 标题 | 本 Spec 引用位置 | 验证方式 |
|----------|------|------------------|----------|
| §3.8 | **Python-first 强制** | §2.2 依赖方向 + §13.2 pyproject.toml + §13.4 Dockerfile runtime | `ST-A2A-BOUNDARY` Ruff 规则 + CI 禁 Go struct import |
| §6 | mTLS 通信 | §11.3 cert-manager 集成 + §13.4 admission TLS 证书 | `ACCEPT-` 验收点 + E2E mTLS 双向认证 case |
| §7 | 可观测性 | §10.1 MetricsRegistry + §10.3 OTel Trace + §10.6 structlog 8 字段 | `OBS-` 测试 ID 9 有效 + Prometheus scrape 验证 |
| §9.7 | 静态质量门禁 | §12.6 ruff + pyright + bandit + pip-audit | CI 阻断合并（`TEST-022`） |
| §14.4 | 评审门禁（10 维度） | §14.1 §A-§G 10 维度 + 评审报告 | 评审报告存在 + 10 维度全 PASS |
| §14.5 | MVP 例外时间窗口 | §15.4 OPEN-Q-02 启动顺序（v0.1 容忍，v0.5+ 修正） | Helm pre-install hook 验证 |
| §16 | 会话纪律 | §16 关联 + MEMORY 索引 #27-#32 | §16.1.3 实际水位判断 + §16.1.4 50%/80% 临界 |
| §13.6 | L3 Spike 门禁 | §15.3 D-1~D-5 收敛依据 | kopf-python spike 已通过 |

### B.3 跨 ADR 联合约束

**ADR-0005 + 宪法 §3.8 联合约束**（Operator Core 实现语言）：

| 约束项 | ADR-0005 依据 | 宪法依据 | 本 Spec 实现 |
|--------|--------------|----------|--------------|
| 实现语言 | §3.1 "Operator Core 采用 Python-first（Kopf + kubernetes_asyncio）" | §3.8 "Python-first 强制" | §13.2 11 个运行时依赖无 Go / Rust |
| 单进程原则 | §7 "Operator + admission 共进程（subprocess 隔离）" | §3.8 + §7 | §4.1 admission webhook 独立 container（共享 Deployment 独立 process） |
| SDK 门禁 | §8 "a2a-python SDK 升级必须先跑 spike" | §13.6 spike 门禁 | §13.3 cross-package boundary Ruff 规则 |
| OTel 迁移 | §13.1 "指标名 wire contract 不变；OTel SDK 替代 prometheus 默认 client" | §7 | §10.3 OTel TracerProvider 显式注入 + §10.4 trace_id 注入 |

**ADR-0003 + ADR-0002 联合约束**（Memory + Knowledge 边界）：

| 约束项 | ADR-0003 依据 | ADR-0002 依据 | 本 Spec 实现 |
|--------|--------------|--------------|--------------|
| Memory CRD | §6 Memory CRD schema | — | §3.4 MemoryReconciler controller + §6.3 timer |
| KnowledgeItem 引用 | — | §3 KnowledgeItem schema | §3.1 Agent CRD 引用 KnowledgeScope via `spec.knowledge.scopeRef` |
| decay 频率 | §4.3 60s | — | §9.2 `memoryReconciler.intervalSeconds: 60` Helm values |
| MemoryReconciler | §6.5 调度周期 + CPU offload | — | §6.3 + §15.3 Q-09 |

### B.4 ADR / Constitution 字段级精确映射表（L4 实现追溯）

| ADR / 宪法条目 | 字段 / 约束 | 本 Spec 行号 / 章节 | 评审追溯 |
|----------------|------------|----------------------|----------|
| ADR-0005 §3.1 | Operator Core → Python | §13.2 + §2.2 | §14.1 G 维度 |
| ADR-0005 §7 | 单进程原则 | §4.1 admission subprocess | §14.1 D 维度 |
| ADR-0005 §8 | SDK 升级 spike 门禁 | §13.3 Ruff 规则 | §14.1 G 维度 |
| ADR-0005 §13.1 | OTel 指标迁移 | §10.3 TracerProvider | §14.1 C 维度（§7 观测） |
| ADR-0003 §4.3 | Memory decay 60s | §9.2 + §6.3 | §14.1 E 维度 |
| ADR-0003 §6 | Memory CRD schema | §3.4 | §14.1 A 维度 |
| ADR-0003 §6.5 | MemoryReconciler 调度 | §6.3 + §15.3 Q-09 | §14.1 E 维度 |
| ADR-0002 §2 | KnowledgeScope | §2.2 模块外（L2-4 负责） | §14.1 D 维度 |
| ADR-0002 §3 | KnowledgeItem | §3.1 Agent CRD 引用 | §14.1 A 维度 |
| 宪法 §3.8 | Python-first | §13.2 + §2.2 | §14.1 G 维度 |
| 宪法 §6 | mTLS | §11.3 + §13.4 | §14.1 C 维度 |
| 宪法 §7 | 可观测性 | §10.1-§10.6 | §14.1 C 维度 |
| 宪法 §9.7 | 静态质量 | §12.6 | §14.1 C 维度 |
| 宪法 §14.4 | 评审门禁 | §14.1 §A-§G | §14.1 F 维度 |
| 宪法 §14.5 | MVP 例外时间窗口 | §15.4 OPEN-Q-02 | §15.5 移交 L3-1 |
| 宪法 §16 | 会话纪律 | MEMORY #27-#32 | §16.1.3 + §16.1.4 |

### B.5 ADR / Constitution 变更追踪规则

- **ADR 新增 / 修订**：必须在本附录 B.1 + B.4 同步更新引用位置；CI 校验"ADR 文件 → 本 Spec 章节"双向链接存在
- **宪法版本升级**：必须重新跑 §14.1 §A-§G 验收清单 + §14.2 测试 ID 矩阵 + §14.3 部署交付清单
- **本 Spec 章节新增**：必须显式列出影响的 ADR / 宪法条目；评审报告 `L2-2 Operator Core Spec Review` 附录必须有"ADR/Constitution 变更追踪"段落
- **跨 L2 模块**：L2-1 / L2-3 / L2-4 Python 重写时必须复用本附录 B.4 模板

---

## 附录 A: 相关文档

| 文档 | 位置 | 状态 |
|------|------|------|
| **L2-2 Spec（本）** | `docs/spec/L2-module-specs/L2-operator-core.md` | ✅ v0.2.0（2026-07-25 #33 §A-§G 评审通过 · 103.2KB / 1890 行 / 15 节 + 2 附录） |
| **L2-2 Design v0.2.0** | `docs/design/L2-modules/L2-operator-core.md` | ✅ 已评审通过 2026-07-24（80KB / 1583 行 / 10 维度全 PASS） |
| **L2-2 Design Go baseline** | `docs/archive/pre-python-2026-07-24/L2-operator-core-design-v0.1.0-go-baseline.md` | 📦 ARCHIVED · 仅参考 wire contract / 业务语义 |
| **L2-2 Spec Go baseline** | `docs/archive/pre-python-2026-07-24/L2-operator-core-spec-v0.1.0-go-baseline.md` | 📦 ARCHIVED · 仅参考 wire contract / 业务语义 |
| **L2-2 评审 v0.2.0** | `docs/reviews/l2-2-operator-core-python-review.md` | ✅ 10 维度全 PASS · 0 阻塞项 · 4 关注项（移交 L3-1） |
| **L1 Architecture v0.2.0** | `docs/design/L1-architecture.md` | ✅ 评审通过 2026-07-24；§3.2 编排层 + §4.1 C-1 Operator + §11.5 Python 性能预算 |
| **L1 Spec v0.2.0** | `docs/spec/L1-system-spec.md` | ✅ 评审通过 2026-07-24；§2-§4 CRD + §7 状态机 + §9-§10 资源/限流 + §16 指标 |
| **ADR-0005 Python-first** | `docs/adr/0005-python-first-technology-stack.md` | ✅ 2026-07-24；§3.1 Operator Core 模块映射 + §7 单进程原则 + §8 SDK 门禁 + §13.1 OTel/指标迁移 |
| **ADR-0003 Memory** | `docs/adr/0003-memory-design.md` | ✅ 2026-07-23；§4.3 (decay) / §6 (CRD) / §6.5 (MemoryReconciler) |
| **ADR-0002 知识管理** | `docs/adr/0002-knowledge-management-design.md` | ✅ 2026-07-23；§2 (KnowledgeScope) / §3 (KnowledgeItem) |
| **L2-1 A2A Protocol v0.2.0 Spec** | `docs/spec/L2-module-specs/L2-a2a-protocol.md` | ✅ 2026-07-24 通过；§2.5 (client) + §16.1 (OTel) |
| **L2-1 A2A Protocol v0.2.0 Design** | `docs/design/L2-modules/L2-a2a-protocol.md` | ✅ 2026-07-24 通过；44KB / 981 行 / 14 节 + 5 子包 |
| **L2-3 Adapter v0.2-draft Python Design** | `docs/design/L2-modules/L2-adapter.md` | 🚧 v0.2-draft (2026-07-26 #34 起草 · 1267 行 / 66KB / 14 节 + 2 附录；待评审 + Spec 起草) |
| **L2-3 Adapter v0.1.0 Spec** | `docs/spec/L2-module-specs/L2-adapter.md` | ⚠️ Go baseline（迁移输入 · Python Spec v0.2 待启动） |
| **L2-4 Knowledge/Memory v0.1.0 Spec** | `docs/spec/L2-module-specs/L2-knowledge-memory.md` | ✅ Go baseline（Python Spec v0.2 待启动） |
| **宪法 v0.5.0** | `CONSTITUTION.md` | ✅ §3.8 Python-first + §6 mTLS + §7 可观测性 + §9.7 静态质量 + §14.4 评审门禁 + §14.5 MVP 例外时间窗口 |

---

> **签署（v0.2.0 · 评审通过）**：本 L2-2 Operator Core Python Spec **v0.2.0** 增量依据 [`docs/design/L2-modules/L2-operator-core.md` v0.2.0](../../design/L2-modules/L2-operator-core.md) + [ADR-0005](../../adr/0005-python-first-technology-stack.md) + [ADR-0003](../../adr/0003-memory-design.md) + [ADR-0002](../../adr/0002-knowledge-management-design.md) + [L1 Architecture v0.2.0](../../design/L1-architecture.md) + [L2-1 Python v0.2.0 Spec](../../spec/L2-module-specs/L2-a2a-protocol.md) + [宪法 v0.5.0](../../../CONSTITUTION.md) §3.8/§6/§7/§9.7/§14.4/§14.5/§16 编写；**§A-§G 10 维度评审通过**（2026-07-25 #33 · 评审报告 [`docs/reviews/l2-2-operator-core-spec-review.md`](../../reviews/l2-2-operator-core-spec-review.md) · 10 维度全 PASS · 0 阻塞项 · 3 关注项移交 L3-1 · 2 建议项）。
>
> **版本演进**：v0.1.0 Go baseline Spec（2026-07-24 评审通过 + 已归档）→ v0.2-draft-skeleton（#19 头部 + §0-§4 + 附录 A，2026-07-25）→ v0.2-draft-skeleton+§5-§9（#28 §5-§9 Leader Election / async / Finalizer / 错误模型 / Helm values）→ v0.2-draft-skeleton+§5-§12（#29 §10-§12 可观测 / RBAC / 测试策略）→ v0.2-draft-skeleton+§5-§13（#30 §13 工具链与部署）→ v0.2-draft-skeleton+§5-§14（#31 §14 验收清单）→ v0.2-draft-full（#32 §15 开放问题 20 项 + 附录 B ADR/Constitution 引用矩阵 5 子表）→ **v0.2.0**（#33 §A-§G 10 维度评审通过）。
>
> **下次会话入口**：**§F.1-§F.6 跨文档同步**（6 步微同步 ≈ 5-8%）→ 启动 L3-1 Operator Core 文件级 Spec（建议拆主 Spec 50-60KB + 辅助 Spec 30-40KB 两文档避免 §16.1）→ L2-3 / L2-4 Python Spec 重写启动（按 L2-2 完成度排期；附录 B 引用矩阵模板可复用）。
> **本次增量**：在 #27 骨架（§0-§4）基础上补完 §5 Leader Election、§6 async-first/CPU offload、§7 Finalizer、§8 错误模型、§9 Helm values、§10 可观测性、§11 RBAC、§12 测试策略、§13 工具链与部署形态、§14 验收清单；文件约 68KB / 1650 行。
> **下次会话入口**：补完 §15 开放问题 + 附录 B ADR/Constitution 引用矩阵 → 升级 v0.2-draft-full → L2-2 Spec 评审。