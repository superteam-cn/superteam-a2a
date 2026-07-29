# L3 文件级 Spec：Operator Core（编排层文件级 · Python-first）

> **⚠️ ADR-0005 supersede + 归档标记（2026-07-27）**：本 v0.2-draft Spec 文档**仅 supersede Go struct / kubebuilder / controller-runtime / client-go 实现条款**；wire contract（3 个 CRD Controller + C-1.4 MemoryReconciler 职责 / CRD 状态机 / Leader Election / Finalizer / RBAC / metric name）与 v0.1-draft 业务语义**完全继续有效**。原 v0.1-draft Go baseline 已归档至 [`docs/archive/pre-python-2026-07-24/L3-operator-core-spec-v0.1-draft-go-baseline.md`](../../archive/pre-python-2026-07-24/L3-operator-core-spec-v0.1-draft-go-baseline.md)（2026-07-27 归档 / **未评审** / 75KB / 1886 行）。
>
> **Python 重写入口**：依据 L1 v0.2.0 Architecture §3.2 + ADR-0005 §3.1 + §13.1 + L2-2 Design v0.2.0 §3，Go baseline 70 文件清单 → Python 包结构（`packages/operator/src/superteam_a2a/operator/` 13 子包）；3 个 CRD Controller 的完整 Go 代码契约 → **Kopf `@kopf.create` / `@kopf.update` / `@kopf.delete` handlers（30-50 行/Controller）+ 独立 async reconciler services（业务逻辑分离）**；C-1.4 MemoryReconciler 60s 周期 → **`@kopf.timer(interval=60.0)`** + Leader Election 单 leader 触发。
>
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-1（Operator Core，见 L1 Architecture §4.1）
> **代码位置**：`packages/operator/src/superteam_a2a/operator/`（**ADR-0005 §13.1 uv workspace 布局**，替代原 Go baseline 的 `src/operator/`）
> **版本**：**v0.2.0**（2026-07-27 起 Python 重写 + 2026-07-27 #44 Go baseline 归档；2026-07-28 §10 + 附录 B 补完；2026-07-28 #56 评审通过升级 v0.2.0）
> **状态**：✅ **v0.2.0 已通过评审**（#44 骨架 + #45 §4-§6 + #47 §7 observability/RBAC/Helm + #48 §8 测试/工具链 + #49 §9 验收清单 + #55 §10/附录 B 补完 + #56 评审 §A-§P 10 维度全 PASS / 0 阻塞项 / 3 关注项 / 4 建议项）——**L3 阶段 1/4 完成**；头部 + §0-§10 + 附录 A/B 全部落地，0 个待补完章节
> **上游约束**：[`docs/design/L2-modules/L2-operator-core.md`](../../design/L2-modules/L2-operator-core.md) **v0.2.0**（2026-07-24 评审通过 · 80KB / 1583 行 / 14 主章节）+ [`docs/spec/L2-module-specs/L2-operator-core.md`](../../spec/L2-module-specs/L2-operator-core.md) **v0.2.0**（2026-07-25 评审通过 · 103KB / 1890 行 / 16 节 + 2 附录 / 122 测试 ID / 20 开放问题：16 已收敛 + 3 移交 L3-1 + 1 推迟 v0.5+）
> **本 Spec 目的**：将 L2-2 Operator Core Spec v0.2.0 中的 **13 子包 + 3 个 CRD Controller + MemoryReconciler + admission webhook + Leader Election + Finalizer + observability + RBAC + Helm + 测试策略** 落地为 **文件级 Python 代码契约**——每个文件列明**绝对路径（基于 uv workspace 布局）**、**职责一句话**、**完整 import 列表**、**exported 符号签名（type hints + docstring 一行）**、**内部 helper 列表**、**关联测试文件路径 + 测试 ID 前缀**。是 L4 实施阶段（开发者打开 IDE 即可对照写代码）的直接输入。
> **配套 Spec**：[L3-2 A2A Core Library 文件级 Spec v0.2.0](./L3-a2a-core.md)（2026-07-28 #54 评审通过 · [评审报告](../../reviews/l3-2-a2a-core-spec-review.md) §A-§P 10 维度全 PASS）/ [L3-5 Knowledge Service 文件级 Spec](./L3-knowledge-service.md)（待起草）/ [L3-6 Memory backend 文件级 Spec](./L3-memory-backend.md)（待起草）
> **配套 Review**：[L3-1 Operator Core Spec 评审报告 v0.2.0](../../reviews/l3-1-operator-core-spec-review.md)（2026-07-28 #56 · 700 行 / 55KB / §A-§P 16 节 / 10 维度全 PASS / 0 阻塞项 / 3 关注项 / 4 建议项）

---

## 0. 阅读指南

- **读者**：Operator 实施工程师（L4 Python 编码）、Code Reviewer（PR 审查）、架构 Reviewer（设计一致性）
- **必读章节**：§1（模块使命 + 70 → 162 文件清单总览）/ §2（Python 包结构）/ §3（3 个 CRD Controller + MemoryReconciler 概要）/ §8（测试策略 + 工具链）/ §9（277 测试 ID + 30 条硬验收）/ §10（25 项开放问题去重收敛）/ 附录 A（跨模块引用清单）/ 附录 B（ADR / Constitution 5 子表追溯矩阵）
- **评审入口**：§9 验收清单 + §10 开放问题状态与移交 + 附录 B MUST/SHOULD/MAY 约束矩阵；三处必须互相回链且数量一致
- **配套阅读**：[L2-2 Operator Core Spec v0.2.0](../../spec/L2-module-specs/L2-operator-core.md) §1-§15 + 附录 A/B · [L2-2 Operator Core Design v0.2.0](../../design/L2-modules/L2-operator-core.md) §3-§14 · [L1 Architecture v0.2.0 §3.2 编排层](../../design/L1-architecture.md) · [ADR-0003 §4 Memory 衰减算法](../../adr/0003-memory-design.md) · [ADR-0005 §3.1 Operator 模块映射](../../adr/0005-python-first-technology-stack.md) · [Kopf 官方文档](https://kopf.readthedocs.io/) · [kubernetes_asyncio 文档](https://github.com/kubernetes-client/python/tree/master/kubernetes_asyncio)

**与 L3-1 Go baseline 关系**：
- v0.1-draft Go baseline 已归档（**不可变，仅参考**：`../../archive/pre-python-2026-07-24/L3-operator-core-spec-v0.1-draft-go-baseline.md`，1886 行）
- 本 v0.2 Spec **完全替代** Go baseline 的 Python 实现决策（Kopf handlers + async reconciler services + `kubernetes_asyncio` + K8s Lease Leader Election + structlog + Pydantic v2）
- 业务语义（3 个 CRD Controller + C-1.4 MemoryReconciler 职责 / CRD 状态机 / Finalizer / RBAC / metric name）与 v0.1-draft Go baseline **完全一致**

---

## 1. 模块使命与文件清单总览

### 1.1 使命

L3-1 Operator Core 文件级 Spec 将 [L2-2 Spec v0.2.0](../../spec/L2-module-specs/L2-operator-core.md) 中描述的 **4 Controllers + admission webhook + Leader Election + MemoryReconciler + observability + RBAC + Helm** 落地为 **可直接对照编码的 Python 文件级契约**。

**单部署形态**：与 Knowledge Service + MemoryReconciler 共享同 Deployment（独立 Deployment,单实例 v0.1,单 Python 进程 / 单 Uvicorn worker,ADR-0005 §6.2 单进程原则）。

**L3-1 文件级 Spec v.s. L2-2 模块 Spec 边界**：

| 维度 | L2-2 模块 Spec | L3-1 文件级 Spec |
|---|---|---|
| **粒度** | 模块级（13 子包 + 4 Controller 概要） | 文件级（70 文件精确路径 + 每个文件的 import/exported/helper/测试文件） |
| **目的** | "为什么 + 是什么"（设计决策 + 模块契约） | "怎么做"（每个文件具体怎么写） |
| **读者** | 架构师 + L3 起草者 | L4 实施工程师（开发者打开 IDE 对照） |
| **变更频率** | 低（设计变更才改） | 中（实现微调可能改） |
| **测试 ID 范围** | 122 个模块级测试 ID（§A-§G ID 矩阵） | 继承 L2-2 前缀与语义，并按文件级路径细化为 §9.2 的 **277 个可执行测试 ID**；§10 的 `OPEN-OP-*` 仅作决策追踪，不计入 277 |

### 1.2 模块对外契约（public API surface · 继承 L2-2 Spec §1.2）

**Public API 入口**（仅暴露给其他 L2/L3 模块,本 L3-1 不变更）：

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
```

**L3-1 新增 internal API**（仅 Operator 包内部使用,不对外暴露）：

```python
# packages/operator/src/superteam_a2a/operator/_internals.py
# 注：仅用于 L3 内部测试夹具 import,不进 __all__

# Controllers 内部 helper（Kopf handlers 调用）
from .reconcilers.base import BaseReconciler
from .reconcilers.agent_reconciler import AgentReconcilerService
from .reconcilers.agentset_reconciler import AgentSetReconcilerService
from .reconcilers.workflow_reconciler import WorkflowReconcilerService
from .reconcilers.memory_reconciler import MemoryReconcilerService

# admission validators
from .admission.validators import (
    AgentValidator, AgentSetValidator, WorkflowValidator,
    MemoryValidator, MutualExclusionValidator,
)

# Finalizer 工具
from .finalizers.names import AGENT_FINALIZER, AGENTSET_FINALIZER, WORKFLOW_FINALIZER, MEMORY_FINALIZER

# K8s 客户端（kubernetes_asyncio 封装）
from .clients.k8s_client import AsyncK8sClient
```

### 1.3 文件清单总览（70 个 Python 文件 + 9 个 Helm manifest 模板 + 1 个 helper）

> **完整文件清单在 §2.3 按子包展开，§4-§7 给最终扩展口径，§8 将测试与工程资产映射后形成 162 个文件级条目**。本节给出评审使用的最终汇总；历史骨架中的 65 文件仅是 §4-§7 展开前的中间数，不再作为验收基线。

**70 个 Python 文件分布**：

| 子包 | 文件数 | 职责一句话 | 测试 ID 前缀 |
|---|---|---|---|
| `operator/`（顶层） | 3 | 主入口 + 公开 API + ASGI runner | UT-OP-01~14 |
| `operator/controllers/` | 4 | `__init__.py` + 3 个 CRD Controller 的 Kopf handlers；MemoryReconciler 不在此包 | UT-C-01~30 |
| `operator/reconcilers/` | 5 | 业务逻辑 services + leader-gated MemoryReconciler（与 Kopf handlers 解耦） | UT-R-01~25 |
| `operator/admission/` | 9 | ASGI admission webhook server + TLS + 5 validators | UT-AW-01~18 |
| `operator/leader_election/` | 3 | 子包入口 + K8s Lease 客户端 + Election 主类 | UT-LE-01~10 |
| `operator/finalizers/` | 1 | 4 个永久 `/cleanup` Finalizer 名称常量 + 工具 | UT-FN-01~03 |
| `operator/clients/` | 1（实现文件） | `k8s_client.py`；纯重导出的 `clients/__init__.py` 不重复计入 70 基线 | UT-KC-01~07 |
| `operator/observability/` | 6 | 子包入口 + metrics + health + tracing + logging + events | OBS-001~025 / HLT-001~008 |
| `operator/errors/` | 1 | ReconcileError hierarchy | UT-ER-01~06 |
| `operator/config/` | 1 | Helm values Pydantic model | UT-CF-01~04 |
| `operator/models/` | 36 | 4 CRD 的 Pydantic model + status / conditions / enum / helper | UT-MD-01~25 |
| **合计** | **70** | §4-§7 展开后的最终 Python 文件口径 | |

**计数规则**：70 是“具有独立实现契约的 Python 文件”基线；仅做同包符号重导出、且没有独立行为的叶子 `__init__.py`（如 `clients/__init__.py`）可在 §2.3 索引中出现但不重复计数。带 public API、注册或聚合行为的 `__init__.py` 仍计入对应子包。

`models/` 子包是 L3-1 相对 Go baseline 的关键新增层：Go 使用 kubebuilder 注解 + controller-runtime CRD 类型；Python 实现使用 Pydantic v2 + Kopf persistence。

**Helm 资产**（§7.2.1 为唯一清单）：9 个 manifest 模板 + 1 个 `_helpers.tpl`；`Chart.yaml` / `values.yaml` / `values.schema.json` / `NOTES.txt` 为 chart 顶层工程资产，不计入 70 个 Python 文件。

```text
deploy/helm/operator/
├── Chart.yaml
├── values.yaml
├── values.schema.json
├── NOTES.txt
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    ├── serviceaccount.yaml
    ├── configmap.yaml
    ├── rbac.yaml
    ├── admission_rbac.yaml
    ├── networkpolicy.yaml
    ├── prometheusrule.yaml
    └── servicemonitor.yaml
```

**测试与工程资产**：§8 把 70 个 Python 文件映射到单元/集成/E2E/Conformance/性能测试，并加入 25 个工程资产；§9.2 的 277 个测试 ID 是最终验收口径。

### 1.4 关键不变量（跨 L3-1 全文件清单适用）

- ✅ **Kopf handlers 30-50 行/Controller**：handler 不含业务逻辑,仅做参数解构 + 调用 `BaseReconciler` + catch errors + status patch
- ✅ **Reconciler services 与 Kopf 解耦**：所有业务逻辑在 `reconcilers/` 子包,可独立单测(mock CRD 实例,无需 Kopf 测试框架)
- ✅ **Leader Election 不阻塞 event loop**：Lease 续约在独立 `asyncio.Task`,acquire 失败立即让位
- ✅ **Finalizer 永久保留 v0.1 名称**：4 个 CRD 的 Finalizer 在 v1.0+ 不变（语义变化只增不改）
- ✅ **Status 子资源仅通过 `kopf.adopt` + status_patch**：禁止直接 `kubectl patch` 风格 API
- ✅ **错误分类（Permanent > NonRetryable > Retryable）**：单 `BaseReconciler.handle_error()` 统一调度，见 §2.3.10 + §3.5 + §8.5
- ✅ **Public API 仅 `__init__.py` 暴露**：其他文件以下划线前缀不允 import(由 `import-linter` 静态检查)

---

## 2. Python 包结构（基于 L2-2 Design §3.1 落地）

### 2.1 顶级目录布局（uv workspace · ADR-0005 §13.1）

```
superteam-a2a/                            # uv workspace 根(由 L4 pyproject.toml 锁定)
└── packages/
    └── operator/                         # 本模块 monorepo 子包
        ├── pyproject.toml                # uv workspace 成员;Python 3.12+;name=superteam-a2a-operator
        │                                 # deps: kopf>=1.36 kubernetes_asyncio>=30 prometheus-client>=0.20 structlog>=24.1
        │                                 # pydantic>=2.6 opentelemetry-api>=1.27 tenacity>=9 anyio>=4.4 cert-manager-client>=1.0
        ├── README.md                     # 模块 README(L4 使用说明;与 OpenAPI 同步)
        ├── src/
        │   └── superteam_a2a/
        │       └── operator/             # 13 子包入口(70 文件全部在此下)
        │           ├── __init__.py       # 版本号 + 公开 API 导出(见 §1.2)
        │           ├── __main__.py       # 入口:kopf run + asyncio.run + Leader Election 启动
        │           ├── main.py           # OperatorMain 主类(Kopf + ASGI server + admission webhook 共进程)
        │           ├── _internals.py     # internal API export(测试夹具用)
        │           │
        │           ├── controllers/      # 见 §3.1 + §3.2 + §3.3
        │           ├── reconcilers/      # 业务逻辑 services(见 §3.4 落地)
        │           ├── models/           # CRD 实体 Pydantic model(36 文件,L3-1 新增)
        │           ├── admission/        # admission webhook ASGI server
        │           ├── leader_election/  # K8s Lease 客户端 + Election
        │           ├── finalizers/       # 4 Finalizer 名称常量
        │           ├── clients/          # kubernetes_asyncio 封装
        │           ├── observability/    # metrics + tracing + logging + events
        │           ├── errors/           # ReconcileError hierarchy
        │           └── config/           # Helm values Pydantic model
        │
        ├── tests/                        # 测试(结构镜像 src/)
        │   ├── unit/                     # 单元测试(70 文件镜像 src/)
        │   ├── integration/              # envtest(K8s API mock)
        │   ├── conformance/              # 与官方 a2a-sdk 集成
        │   ├── e2e/                      # kind + hello-agent
        │   ├── tz/                       # 跨时区 + DST(与 L2-4 复用)
        │   ├── perf/                     # 性能 benchmark(可选)
        │   ├── conftest.py               # pytest fixtures(kopf testing utilities + envtest fixtures)
        │   └── __init__.py
        │
        └── deploy/
            └── helm/
                └── operator/             # 9 Helm 模板(见 §1.3 表格下方)
```

**与 L2-2 Design §3.1 关系**：
- 本 §2.1 是 **L2-2 §3.1 的文件级落地**——L2-2 给包结构概要 + 70 文件占位,本 L3-1 给精确路径 + 单文件职责 + import/exported/helper/测试文件
- `models/` 子包是 L3-1 新增层(36 文件)——L2-2 已铺垫 Pydantic 优先级但未展开目录

### 2.2 边界规则（继承 L2-2 Design §3.2 · 8 条规则全保留）

| # | 边界 | 规则 | 依据 |
|---|------|------|------|
| 1 | **Operator 不依赖 framework adapter** | Operator 不 import L2-3 Adapter v0.2.0 Python SDK;Adapter 由 Operator 注入到 Agent Pod 但 Operator 自身不调用 Adapter | 宪法 §3.7 + ADR-0005 §13 |
| 2 | **Operator 不实现 A2A 协议** | 所有 A2A 通信走 L2-1 a2a-sdk client;Operator 仅通过 a2a 调用 L2-4 Knowledge Service 检查 Agent 状态 | ADR-0005 §3.1 |
| 3 | **Operator 不实现 Knowledge/Memory 业务语义** | Knowledge/Memory 的 5 维可见性矩阵 + decay/reinforce 算法由 L2-4 负责;Operator 仅做 reconcile 驱动 | ADR-0003 §6 |
| 4 | **admission webhook 不依赖 K8s API** | admission webhook 是无状态 server(仅做字段校验),不调用 K8s API | ADR-0005 §7 |
| 5 | **Reconciler services 不依赖 Kopf** | 业务逻辑在 `reconcilers/` 下,与 Kopf handlers 解耦 | ADR-0005 §13.2 |
| 6 | **Leader Election 不阻塞 event loop** | Lease 续约在独立 task;acquire 失败立即让位 | ADR-0005 §6.1 |
| 7 | **状态机状态子资源写回仅通过 `kopf.adopt`** | 禁止直接 `kubectl patch` 风格 API | ADR-0005 §3.1 |
| 8 | **Finalizer 永久保留 v0.1 名称** | 4 个 CRD 的 Finalizer 名称(v0.1-draft Go baseline 已确定)在 v1.0+ 不变 | L2-2 Go baseline §7.4 + 宪法 §3.4 |

**L3-1 新增边界规则(3 条,基于 Pydantic + uv workspace)**：

| # | 边界 | 规则 | 依据 |
|---|------|------|------|
| 9 | **`models/` 与 `reconcilers/` 单向依赖** | `reconcilers/*.py` 可 import `models/*.py`;反向不允许;`models/` 是叶子包 | ADR-0005 §13.2 |
| 10 | **`controllers/` 与 `reconcilers/` 通过 `BaseReconciler` Protocol 解耦** | `controllers/*.py` 仅依赖 `reconcilers/base.py` 的 Protocol(不在 handlers 里 import 具体 reconciler 类) | 静态类型检查 |
| 11 | **`__init__.py` 仅导出 `__all__` 列出的符号** | 其他符号需下划线前缀;由 `ruff` + `import-linter` 双重检查 | ADR-0005 §9.4 |

### 2.3 文件清单（70 个 Python 文件 · §4-§7 展开后最终口径）

> **70 个 Python 文件**按 §1.3 的最终分布统计；`pyproject.toml` / `README.md` / chart 顶层文件 / Helm templates / tests 属工程与部署资产，在 §7-§8 单列，不重复计入本节。
>
> 每个文件列：**绝对路径** / **职责一句话** / **exported 符号** / **内部 helper** / **关联测试文件** / **L2-2 Spec 对应章节**

#### 2.3.1 顶层 3 文件(`operator/__init__.py` + `main.py` + `__main__.py`)

| 文件路径 | 职责 | exported 符号 | helper | 测试文件 | L2-2 对应 |
|---|---|---|---|---|---|
| `src/superteam_a2a/operator/__init__.py` | 公开 API export + 版本号 | `__version__: str = "0.2.0"` + §1.2 全部符号 | 无 | `tests/unit/test___init__.py` (UT-OP-01) | L2-2 Spec §1.2 |
| `src/superteam_a2a/operator/__main__.py` | CLI 入口：`python -m superteam_a2a.operator` 启动 Kopf + ASGI server + Leader Election | 无(命令式) | `OperatorMain.from_helm_values()` | `tests/integration/test___main__.py` (IT-OP-01) | — |
| `src/superteam_a2a/operator/main.py` | `OperatorMain` 主类(Kopf daemon + ASGI admission server + Leader Election 单 leader 触发 reconcile) | `class OperatorMain`,`@classmethod from_helm_values(cls, helm_values: HelmValues) -> "OperatorMain"`,`async run() -> None` | `_run_kopf()`,`_run_admission_server()`,`_run_leader_election()` | `tests/unit/test_main.py` (UT-OP-02~04) + `tests/integration/test_main_e2e.py` (IT-OP-02) | L2-2 Spec §1.1 + Design §2.4 |

#### 2.3.2 `controllers/` 子包(4 文件)

| 文件路径 | 职责 | exported 符号 | helper | 测试文件 | L2-2 对应 |
|---|---|---|---|---|---|
| `controllers/__init__.py` | 导出 3 个 CRD Controller 类；MemoryReconciler 由 `reconcilers/` 导出 | `AgentController`, `AgentSetController`, `WorkflowController` | 无 | `tests/unit/test_controllers___init__.py` (UT-C-01) | L2-2 Spec §3.1 |
| `controllers/agent.py` | `AgentController`:Kopf `@kopf.create/update/delete` handlers,30-50 行/handler | `class AgentController`,`@kopf.create.on(progress_pending=True)` + 3 装饰器方法 | `_build_spec()`, `_patch_status()`, `_emit_event()` | `tests/unit/test_agent_controller.py` (UT-C-02~09) + `tests/integration/test_agent_reconcile.py` (IT-C-01) | L2-2 Spec §3.2 + Design §4.1 |
| `controllers/agentset.py` | `AgentSetController`:replicas 调谐 + 滚动更新 | `class AgentSetController`,3 装饰器方法 + `async def _reconcile_replicas(self, body, spec, status) -> None` | `_list_child_agents()`, `_scale_up()`, `_scale_down()` | `tests/unit/test_agentset_controller.py` (UT-C-10~17) + `tests/integration/test_agentset_reconcile.py` (IT-C-02) | L2-2 Spec §3.2 + Design §4.2 |
| `controllers/workflow.py` | `WorkflowController`:DAG 校验 + Task CR stub(v0.1 + Task 由 v0.5+ 调度) | `class WorkflowController`,3 装饰器方法 + `async def _validate_dag(self, tasks: list[WorkflowTask]) -> None` | `_check_dag_cycles()`, `_emit_task_stub()` | `tests/unit/test_workflow_controller.py` (UT-C-18~25) + `tests/integration/test_workflow_reconcile.py` (IT-C-03) | L2-2 Spec §3.2 + Design §4.3 |

**MemoryReconciler 不放在 `controllers/`**：它落地于 `reconcilers/memory_reconciler.py`，由 `@kopf.timer` + `LeaderGate` 单 leader 触发；CRD handlers 与后台任务的业务逻辑均遵循 reconciler service 分离原则。详见 §3.4 与 §6.2.10。

#### 2.3.3 `reconcilers/` 子包(5 文件)

| 文件路径 | 职责 | exported 符号 | helper | 测试文件 | L2-2 对应 |
|---|---|---|---|---|---|
| `reconcilers/__init__.py` | 导出 5 Reconciler 实现 | `BaseReconciler`(Protocol) + 4 service 实现(`AgentReconcilerService` 等) | 无 | `tests/unit/test_reconcilers___init__.py` (UT-R-01) | L2-2 Spec §3.3 |
| `reconcilers/base.py` | `BaseReconciler[SpecT, StatusT]` Protocol + `handle_error()` 错误分发 | `class BaseReconciler(Protocol, Generic[SpecT, StatusT])`,`abstractmethod async def reconcile()`,`async def handle_error()` | `_classify_error()`,`_retry_with_backoff()` | `tests/unit/test_base_reconciler.py` (UT-R-02~04) | L2-2 Spec §9.2 + Design §9.2 |
| `reconcilers/agent_reconciler.py` | `AgentReconcilerService`:Adapter 注入 + Ready 检查 + Status 更新 | `class AgentReconcilerService(BaseReconciler[AgentSpec, AgentStatus])`, 5 个 public method | `_resolve_pod_mode()`, `_inject_adapter()`, `_wait_for_pod_ready()` | `tests/unit/test_agent_reconciler.py` (UT-R-05~10) + `tests/integration/test_agent_reconciler_e2e.py` (IT-R-01) | L2-2 Spec §3.3 + Design §4.1 |
| `reconcilers/agentset_reconciler.py` | `AgentSetReconcilerService` | `class AgentSetReconcilerService(BaseReconciler[AgentSetSpec, AgentSetStatus])`, 4 个 method | `_compute_diff()`, `_rolling_update()` | `tests/unit/test_agentset_reconciler.py` (UT-R-11~16) + `tests/integration/test_agentset_reconciler_e2e.py` (IT-R-02) | L2-2 Spec §3.3 + Design §4.2 |
| `reconcilers/workflow_reconciler.py` | `WorkflowReconcilerService`:DAG 校验 + Task stub | `class WorkflowReconcilerService(BaseReconciler[WorkflowSpec, WorkflowStatus])`, 3 个 method | `_dag_topological_sort()`, `_emit_task_stub()` | `tests/unit/test_workflow_reconciler.py` (UT-R-17~22) + `tests/integration/test_workflow_reconciler_e2e.py` (IT-R-03) | L2-2 Spec §3.3 + Design §4.3 |

#### 2.3.4 `models/` 子包(36 文件 · L3-1 新增 · Pydantic v2 + Kopf persistence)

> **本子包是 L3-1 vs Go baseline 的关键差异**——Go baseline 用 kubebuilder 注解 + controller-runtime 自带 CRD 类型;L3-1 用 Pydantic v2 + Kopf persistence(Pydantic-validated CRD entities)。
>
> 36 文件分 4 组:**4 CRD × (spec + status + conditions + 4 helper) = 4 × 9 = 36**

| 文件路径 | 职责 | exported 符号 | helper | 测试文件 | L2-2 对应 |
|---|---|---|---|---|---|
| `models/__init__.py` | 导出全部 4 CRD 模型 + 公共 enum | `Agent`, `AgentSet`, `Workflow`, `Memory` + 12 个 enum(Phase / ConditionType / Reason 等) | 无 | `tests/unit/test_models___init__.py` (UT-MD-01~03) | L2-2 Spec §3.4 |
| `models/agent/` (8 文件) | Agent CRD 完整 Pydantic 模型 | 见下方 Agent 子表 | 见下方 | 见下方 | L2-2 Spec §3.4 + Design §3.1 |
| `models/agentset/` (8 文件) | AgentSet CRD 完整 Pydantic 模型 | 见下方 AgentSet 子表 | 见下方 | 见下方 | L2-2 Spec §3.4 + Design §3.1 |
| `models/workflow/` (8 文件) | Workflow CRD 完整 Pydantic 模型 | 见下方 Workflow 子表 | 见下方 | 见下方 | L2-2 Spec §3.4 + Design §3.1 |
| `models/memory/` (8 文件) | Memory CRD 完整 Pydantic 模型(Operator 仅 reconcile,业务语义由 L2-4 负责) | 见下方 Memory 子表 | 见下方 | 见下方 | L2-2 Spec §3.4 + ADR-0003 §3 + L2-4 Spec §3 |

**单 CRD 8 文件标准布局**(以 Agent 为例):

| 文件路径 | 职责 | 测试 ID |
|---|---|---|
| `models/agent/spec.py` | `AgentSpec` Pydantic root model(7 字段:image/command/replicas/mode/securityContext/podTemplate/resources)| UT-MD-AG-01 |
| `models/agent/status.py` | `AgentStatus` Pydantic model(phase/conditions/observedGeneration/lastReconcileTime/endpoints)| UT-MD-AG-02 |
| `models/agent/conditions.py` | `AgentConditionType` enum(Ready/AdapterInjected/PodScheduled/...)+ `AgentCondition` Pydantic model(type/status/reason/message/lastTransitionTime)| UT-MD-AG-03 |
| `models/agent/enums.py` | `AgentMode` enum(Sidecar/Plugin/Inline/External)+ `AgentPhase` enum(Pending/Creating/Ready/Degraded/Failed)+ `EndpointProtocol` enum | UT-MD-AG-04 |
| `models/agent/pod_mode.py` | Pod 模式 resolver(`resolve_pod_mode(spec: AgentSpec) -> AgentMode`)| UT-MD-AG-05 |
| `models/agent/adapter_injection.py` | `inject_adapter(containers: list[Container], adapter: AdapterSpec) -> list[Container]`(Sidecar 模式)+ Annotation 生成器(Plugin 模式)| UT-MD-AG-06 |
| `models/agent/rbac.py` | `ServiceAccountSpec` + `RoleBindingSpec`(Agent RABC) | UT-MD-AG-07 |
| `models/agent/validators.py` | Pydantic root validators(`@model_validator(mode="after")`):image 必须存在 / replicas ∈ [1,100] / mode 与 command 互斥 | UT-MD-AG-08 |

**AgentSet / Workflow / Memory 各 8 文件遵循同一布局**；Controller/reconciler 的 exported 符号以 §3 为准，Memory 的 8 个模型文件与 4 个纯函数以 §6.2 为准。

#### 2.3.5 `admission/` 子包（9 文件）

| 文件路径 | 职责 | exported 符号 | helper | 测试文件 | L2-2 对应 |
|---|---|---|---|---|---|
| `admission/__init__.py` | 导出 `AdmissionWebhookApp` + `TLSConfig` | `AdmissionWebhookApp`, `TLSConfig` | 无 | `tests/unit/test_admission___init__.py` (UT-AW-01) | L2-2 Spec §4 |
| `admission/server.py` | ASGI server(uvicorn 单 worker + `/validate` endpoint);Kopf handlers 不通过 admission | `class AdmissionWebhookApp`,`async def startup()`,`async def shutdown()`,`async def handle_validate(request: AdmissionRequest) -> AdmissionResponse` | `_load_tls()`, `_tracing_middleware()` | `tests/unit/test_admission_server.py` (UT-AW-02~06) + `tests/integration/test_admission_e2e.py` (IT-AW-01~02) | L2-2 Spec §4 + Design §5 |
| `admission/tls.py` | cert-manager 集成 + 证书热更新 | `class TLSConfig`,`async def load_from_disk()`,`async def watch_and_reload()`(每 5min 检查证书过期) | `_is_cert_expiring_soon()`,`_reload_uvicorn_ssl_context()` | `tests/unit/test_admission_tls.py` (UT-AW-07~10) + `tests/integration/test_admission_tls_reload.py` (IT-AW-03) | L2-2 Spec §4 + Design §5.6 |
| `admission/validators/__init__.py` | 5 validator 聚合 | 5 个 validator 类的 `__all__` | 无 | `tests/unit/test_admission_validators___init__.py` (UT-AW-11) | L2-2 Spec §4 |
| `admission/validators/agent.py` | `AgentValidator`(Pydantic v2 root_validator mode="after") | `class AgentValidator`,`async def validate(spec: AgentSpec, operation: Operation) -> list[AdmissionWarning]` | 无 | `tests/unit/test_admission_agent_validator.py` (UT-AW-12) | L2-2 Spec §4 |
| `admission/validators/agentset.py` | `AgentSetValidator` | `class AgentSetValidator`,`validate()`| 无 | `tests/unit/test_admission_agentset_validator.py` (UT-AW-13) | L2-2 Spec §4 |
| `admission/validators/workflow.py` | `WorkflowValidator`(Kahn/DFS DAG 校验 + DAG 节点数 ≤ 50 + 边数 ≤ 200) | `class WorkflowValidator`,`validate()`| `_check_cycles_kahn()`,`_check_node_count()`,`_check_edge_count()` | `tests/unit/test_admission_workflow_validator.py` (UT-AW-14~16) + `tests/integration/test_dag_validation.py` (IT-AW-04) | L2-2 Spec §4 + Design §5.5 |
| `admission/validators/memory.py` | `MemoryValidator`(5 维可见性矩阵 Pydantic 校验 + scoping) | `class MemoryValidator`,`validate()`| 无 | `tests/unit/test_admission_memory_validator.py` (UT-AW-17) | L2-2 Spec §4 + ADR-0003 §5 |
| `admission/validators/mutual_exclusion.py` | `MutualExclusionValidator`(Knowledge ↔ Memory 双向互斥,ADR-0002 §2 + ADR-0003 §5) | `class MutualExclusionValidator`,`validate()`| 无 | `tests/unit/test_admission_mutual_exclusion.py` (UT-AW-18) | L2-2 Spec §4 + Design §5.4 |

**注**:Go baseline `mutual_exclusion.go` 是 1 文件;L3-1 拆为独立子包文件,清晰边界。

#### 2.3.6 `leader_election/` 子包（3 文件）

| 文件路径 | 职责 | exported 符号 | helper | 测试文件 | L2-2 对应 |
|---|---|---|---|---|---|
| `leader_election/__init__.py` | 导出 `Election` | `Election` | 无 | `tests/unit/test_leader_election___init__.py` (UT-LE-01) | L2-2 Spec §6 |
| `leader_election/lease_client.py` | `AsyncLeaseClient`(kubernetes_asyncio 封装 K8s Lease CRUD + renew) | `class AsyncLeaseClient`,`async def create()`,`async def get()`,`async def update()`(续约),`async def delete()`(让位) | `_build_lease_spec()`,`_is_spec_unchanged()` | `tests/unit/test_lease_client.py` (UT-LE-02~06) + `tests/integration/test_lease_client_k8s.py` (IT-LE-01) | L2-2 Spec §6 + Design §6.3 |
| `leader_election/election.py` | `Election` 主类(acquire / renew / release 状态机 + grace period + renew 失败 3 次让位)| `class Election`,`async def acquire()`,`async def renew_loop()`,`async def release()`,`is_leader() -> bool` | `_grace_period_expired()`,`_transition_to_follower()` | `tests/unit/test_election.py` (UT-LE-07~10) + `tests/integration/test_election_e2e.py` (IT-LE-02) | L2-2 Spec §6 + Design §6.4 |

#### 2.3.7 `finalizers/` 子包(1 文件)

| 文件路径 | 职责 | exported 符号 | helper | 测试文件 | L2-2 对应 |
|---|---|---|---|---|---|
| `finalizers/__init__.py` | 导出 4 Finalizer 名称常量 + `ensure_finalizer` 工具 | `AGENT_FINALIZER`, `AGENTSET_FINALIZER`, `WORKFLOW_FINALIZER`, `MEMORY_FINALIZER`, `ensure_finalizer(body, name)` | 无 | `tests/unit/test_finalizers___init__.py` (UT-FN-01~03) | L2-2 Spec §7 + Design §8 |

**4 Finalizer 名称常量**(继承 Go baseline §7.2 · 永久不变):

```python
# packages/operator/src/superteam_a2a/operator/finalizers/__init__.py
AGENT_FINALIZER = "agent.superteam-a2a.io/cleanup"
AGENTSET_FINALIZER = "agentset.superteam-a2a.io/cleanup"
WORKFLOW_FINALIZER = "workflow.superteam-a2a.io/cleanup"
MEMORY_FINALIZER = "memory.superteam-a2a.io/cleanup"
```

#### 2.3.8 `clients/` 子包（1 个实现文件 + 1 个纯重导出入口）

| 文件路径 | 职责 | exported 符号 | helper | 测试文件 | L2-2 对应 |
|---|---|---|---|---|---|
| `clients/__init__.py` | 导出 `AsyncK8sClient`(custom resources + core resources)| `AsyncK8sClient`, `CoreV1API`(kubernetes_asyncio), `CustomObjectsAPI` | 无 | `tests/unit/test_clients___init__.py` (UT-KC-01~02) | L2-2 Spec §8 |
| `clients/k8s_client.py` | `AsyncK8sClient`(CRUD + status patch + watch)| `class AsyncK8sClient`,`async def get_agent()`,`async def list_agents()`,`async def create_agent()`,`async def update_agent_status()`,`async def watch_agents()`(K8s watch + 10s timeout) | `_retry_with_backoff()`,`_extract_spec_metadata()` | `tests/unit/test_k8s_client.py` (UT-KC-03~07) + `tests/integration/test_k8s_client_envtest.py` (IT-KC-01) | L2-2 Spec §8 + Design §6.3 |

#### 2.3.9 `observability/` 子包（6 文件）

| 文件路径 | 职责 | exported 符号 | helper | 测试文件 | L2-2 对应 |
|---|---|---|---|---|---|
| `observability/__init__.py` | 导出 `OperatorMetrics` + `StructuredLogger` + `EventRecorder` + `TracerProvider` | 4 个 facade 类 | 无 | `tests/unit/test_observability___init__.py` (UT-OB-01) | L2-2 Spec §10 + Design §10 |
| `observability/metrics.py` | `MetricsRegistry`（11 Operator + 4 Python runtime 指标，与 L1 Spec §16 一致） | `class MetricsRegistry`,`register_or_get()`,`as_dict()` | `_labels_from_body()`,`_record_reconcile()` | `tests/unit/observability/test_metrics.py` (OBS-001~013) | L2-2 Spec §10.1-§10.3 |
| `observability/health.py` | `/healthz` + `/readyz` ASGI 探针，聚合 Lease / admission TLS / MemoryReconciler last_run | `class HealthCheck`,`create_health_app()` | `_liveness_payload()`,`_readiness_payload()` | `tests/unit/observability/test_health.py` (HLT-001~008) | L2-2 Spec §13.5 |
| `observability/tracing.py` | OTel SDK 初始化(Provider injection,与 L1 Arch §9.2 一致)| `class TracerProvider`,`def init_tracer()`(从 Helm values 读 endpoint),`def get_tracer(name: str) -> Tracer` | `_config_otlp_exporter()`,`_setup_resource()` | `tests/unit/test_tracing.py` (UT-OB-07~09) | L2-2 Spec §10.2 + Design §10.2 |
| `observability/logging.py` | structlog 配置(JSON 输出 + trace_id 注入)| `class StructuredLogger`,`def configure_structlog(level: str) -> None`,`def get_logger(name: str) -> BoundLogger` | `_inject_trace_id()`,`_json_renderer()` | `tests/unit/test_logging.py` (UT-OB-10) | L2-2 Spec §10.3 + Design §10.3 |
| `observability/events.py` | K8s Events 客户端（8 种 `EventReason`，以 §7.1.5 为唯一枚举） | `EventReason`,`async def emit_event(reason: EventReason, message: str, involved_object: K8sObject)` | `_format_event()`,`_retry_on_409()` | `tests/unit/observability/test_events.py` (OBS-007/022/025) | L2-2 Spec §10.6 |

**指标与事件基线**：11 个 Operator 指标 + 4 个 Python runtime 指标见 §7.1.2；8 个 `EventReason` 见 §7.1.5。§7 是本子包的唯一完整契约，本 §2.3.9 仅提供文件索引。

```
# Operator 主指标(4 个)
superteam_operator_reconcile_total{controller,result}
superteam_operator_reconcile_duration_seconds{controller}
superteam_operator_admission_total{validator,result}
superteam_operator_leader_election_state{namespace}

# A2A 调用指标(2 个,L2-1 共享)
superteam_a2a_request_total{method,result}
superteam_a2a_request_duration_seconds{method}

# Agent 状态指标(2 个,L3-1 新增细分)
superteam_agent_phase_count{namespace,phase}
superteam_agent_reconcile_queued{namespace}

# Workflow / Memory / Knowledge(3 个,L2-4 共享)
superteam_workflow_phase_count{namespace,phase}
superteam_memory_decay_total{namespace,result}
superteam_knowledge_query_total{scope,result}
```

#### 2.3.10 `errors/` 子包(1 文件)

| 文件路径 | 职责 | exported 符号 | helper | 测试文件 | L2-2 对应 |
|---|---|---|---|---|---|
| `errors/__init__.py` | 导出 `ReconcileError` hierarchy + 4 错误分类 | `ReconcileError`, `RetryableError`, `NonRetryableError`, `PermanentError`, `classify_error(exc) -> ErrorCategory` | 无 | `tests/unit/test_errors___init__.py` (UT-ER-01~06) | L2-2 Spec §9 + Design §9 |

**ReconcileError 层级**(继承 L2-2 Spec §9.1,与 L2-1 §10 错误码区分):

```python
# packages/operator/src/superteam_a2a/operator/errors/__init__.py
from enum import Enum

class ErrorCategory(str, Enum):
    RETRYABLE = "retryable"            # 网络/超时/K8s API 5xx
    NON_RETRYABLE = "non_retryable"    # K8s API 4xx(非 409)
    PERMANENT = "permanent"            # 业务错误(DAG 有环 / spec 不合法)
    UNKNOWN = "unknown"                # 兜底

class ReconcileError(Exception):
    """Operator reconcile 错误基类"""
    category: ErrorCategory = ErrorCategory.UNKNOWN
    retry_after_seconds: float | None = None

class RetryableError(ReconcileError):
    category = ErrorCategory.RETRYABLE

class NonRetryableError(ReconcileError):
    category = ErrorCategory.NON_RETRYABLE

class PermanentError(ReconcileError):
    category = ErrorCategory.PERMANENT

def classify_error(exc: Exception) -> ErrorCategory:
    """依据异常类型 + K8s API status code 分类"""
    # ... 见 L2-2 Spec §9.2
```

#### 2.3.11 `config/` 子包(1 文件)

| 文件路径 | 职责 | exported 符号 | helper | 测试文件 | L2-2 对应 |
|---|---|---|---|---|---|
| `config/__init__.py` | 导出 `HelmValues` | `HelmValues` | 无 | `tests/unit/test_config___init__.py` (UT-CF-01) | L2-2 Spec §11 |
| `config/helm_values.py` | `HelmValues` Pydantic model 解析 Helm values.yaml(4 层优先级:flag > env > configmap > default)| `class HelmValues`,`@classmethod from_file(path: Path)`,`@classmethod from_env()`,`@classmethod from_k8s_configmap()` | `_validate_against_schema()`,`_apply_defaults()` | `tests/unit/test_helm_values.py` (UT-CF-02~04) + `tests/integration/test_helm_values_e2e.py` (IT-CF-01) | L2-2 Spec §11 + Design §11 |

#### 2.3.12 `models/memory/` 子包详情(8 文件 · 与 L2-4 Spec §3 双向同步)

> **L3-1 与 L2-4 Spec v0.2.0 §3 保持 wire 一致** —— Operator 仅做 reconcile 驱动,业务语义由 L2-4 负责。L3-1 的 `models/memory/*` 必须与 L2-4 Spec §3 的 Pydantic schema **字段逐一对齐**(wire contract)。

| 文件路径 | 职责 | 测试 ID |
|---|---|---|
| `models/memory/spec.py` | `MemorySpec` Pydantic root model(7 字段:agentRef/scope/visibility/content/confidence/reinforcedCount/createdAt)| UT-MD-ME-01 |
| `models/memory/status.py` | `MemoryStatus`(`effectiveConfidence`/`phase`/`lastDecayAt`/`eligibleForPromotion`)| UT-MD-ME-02 |
| `models/memory/conditions.py` | `MemoryConditionType` enum(Decayed/Reinforced/Promoted/Archived) + `MemoryCondition` | UT-MD-ME-03 |
| `models/memory/enums.py` | `MemoryVisibility` enum(5 维:Industry/Organization/Team/Project/AgentPrivate)+ `MemoryPhase` enum(Pending/Active/Decaying/Archived/Promoted)| UT-MD-ME-04 |
| `models/memory/decay.py` | `compute_effective_confidence(confidence: float, decay_days: float, elapsed_days: float) -> float`(纯函数,公式 ADR-0003 §4.1)| UT-MD-ME-05 |
| `models/memory/reinforce.py` | `apply_reinforce(confidence: float, amount: float = 0.05, cap: float = 0.95) -> float` | UT-MD-ME-06 |
| `models/memory/gc.py` | `should_garbage_collect(effective_confidence: float, threshold: float = 0.1) -> bool` | UT-MD-ME-07 |
| `models/memory/promotion.py` | `is_eligible_for_promotion(effective_confidence: float, reinforced_count: int, min_confidence: float = 0.9, min_reinforced: int = 10) -> bool` | UT-MD-ME-08 |

#### 2.3.13 Helm 资产索引（§7.2.1 为唯一完整清单）

Helm 资产不计入 70 个 Python 文件：`templates/` 包含 **9 个 manifest 模板 + 1 个 `_helpers.tpl`**；chart 顶层另有 `Chart.yaml` / `values.yaml` / `values.schema.json` / `NOTES.txt`。精确路径、职责、RBAC 聚合方式与测试 ID 统一见 §7.2.1 和 §8.13，本节不维护第二份易漂移清单。

| 资产组 | 文件 | 关键职责 |
|---|---|---|
| helper | `_helpers.tpl` | 命名、labels、ServiceAccount 辅助模板 |
| workload/network | `deployment.yaml` / `service.yaml` / `networkpolicy.yaml` | Operator + admission 双 container、双端口与流量白名单 |
| identity/config | `serviceaccount.yaml` / `configmap.yaml` | cert-manager annotation 与 values→env 映射 |
| authorization | `rbac.yaml` / `admission_rbac.yaml` | ClusterRole/Binding 与 namespace-scoped Role/Binding |
| observability | `prometheusrule.yaml` / `servicemonitor.yaml` | 6 条告警与 11+4 指标采集 |

**4 CRD YAML 文件**(L3-1 边界外,在 `deploy/helm/crds/`,由 L2-2 Design §3.1 CRD YAML 在 Operator 镜像构建时打包;不在 L3-1 操作范围;L3-1 仅消费):

```
deploy/helm/crds/
├── agent.superteam-a2a.io-agents.yaml          # Agent CRD v1alpha1(schema 由 L2-2 Spec §3 定义)
├── agentset.superteam-a2a.io-agentsets.yaml     # AgentSet CRD v1alpha1
├── workflow.superteam-a2a.io-workflows.yaml     # Workflow CRD v1alpha1
└── memory.superteam-a2a.io-memories.yaml        # Memory CRD v1alpha1(与 L2-4 共享)
```

---

## 3. 3 个 CRD Controller + MemoryReconciler 文件级契约

> 本节给出 Agent / AgentSet / Workflow 三个 CRD Controller 与 C-1.4 MemoryReconciler 后台 service 的文件契约；完整 admission、Leader Election 与 Memory 实现分别见 §4、§5、§6。

### 3.1 Agent Controller（`controllers/agent.py` · C-1.1）

**职责**(继承 L2-2 Design §4.1):
1. 监听 `Agent` CRD 事件(`@kopf.on.create` + `@kopf.on.update` + `@kopf.on.delete`)
2. **30-50 行/handler**,仅做参数解构 + 调用 `AgentReconcilerService.reconcile()` + catch errors + status patch
3. **不**含业务逻辑(业务逻辑在 `reconcilers/agent_reconciler.py`)

**handler 三件套**:

```python
# packages/operator/src/superteam_a2a/operator/controllers/agent.py
# 行 1-30:imports + class 装饰器
import kopf

from superteam_a2a.operator.reconcilers import AgentReconcilerService
from superteam_a2a.operator.models.agent import Agent, AgentSpec, AgentStatus
from superteam_a2a.operator.finalizers import AGENT_FINALIZER, ensure_finalizer
from superteam_a2a.operator.errors import ReconcileError
from superteam_a2a.operator.observability import OperatorMetrics

class AgentController:
    def __init__(self, reconciler: AgentReconcilerService, metrics: OperatorMetrics):
        self._reconciler = reconciler
        self._metrics = metrics

# 行 35-65:create handler
@kopf.on.create('agent.superteam-a2a.io', id='agent-create')
async def agent_create(spec: AgentSpec, name: str, namespace: str, body: Agent, **kwargs):
    controller = AgentController.get_instance()
    try:
        await ensure_finalizer(body=body, name=AGENT_FINALIZER)  # §2.3.7
        await controller._reconciler.reconcile(spec=spec, status=body.status, body=body)
        controller._metrics.inc_reconcile_total(controller='agent', result='success')
    except ReconcileError as e:
        controller._metrics.inc_reconcile_total(controller='agent', result='error')
        raise kopf.PermanentError(str(e)) if e.category == ErrorCategory.PERMANENT else kopf.TemporaryError(str(e), delay=10)

# update/delete handlers 遵循同一结构；完整异常分类与 status patch 契约见 §3.5
```

**与 Go baseline 对应**:L2-2 Go baseline §4.3 Agent Controller(60 行/handler);L3-1 Python 版 30-50 行/handler(50% 精简得益于 Kopf decorator + base reconciler 抽象)。

**关键不变量**(继承 L2-2 Design §4.1):
- ✅ 1 Agent → 1 Pod + 1 Service + 1 ServiceAccount(namespace 内)
- ✅ Pod 模板由 Adapter 注入(从 `models/agent/adapter_injection.py`)
- ✅ mTLS 由 cert-manager 颁发(ServiceAccount 注解触发)
- ✅ Finalizer:`agent.superteam-a2a.io/cleanup`(永久保留)

### 3.2 AgentSet Controller（`controllers/agentset.py` · C-1.2）

**职责**(继承 L2-2 Design §4.2):
- 监听 `AgentSet` CRD 事件
- replicas 调谐 + 滚动更新(不是删除重建)
- Agent 模板与 AgentSetSpec.template 一致(mutation 禁止)

**handler 概览**:

```python
# 完整文件 ~150 行;handler 3 个(create/update/delete)各 35-45 行
@kopf.on.create('agentset.superteam-a2a.io', id='agentset-create')
async def agentset_create(spec: AgentSetSpec, name: str, namespace: str, body: AgentSet, **kwargs):
    controller = AgentSetController.get_instance()
    await ensure_finalizer(body=body, name=AGENTSET_FINALIZER)
    # 业务逻辑调 reconciler
    await controller._reconciler.reconcile(spec=spec, status=body.status, body=body)
```

**关键不变量**(继承 L2-2 Design §4.2):
- ✅ AgentSet owns Agent(owner reference);AgentSet 删除 → 子 Agent 由 GC 自动清理(orphanDeletion=false)
- ✅ 副本数变化触发滚动更新(不是删除重建)

### 3.3 Workflow Controller（`controllers/workflow.py` · C-1.3）

**职责**(继承 L2-2 Design §4.3):
- 监听 `Workflow` CRD 事件
- admission 时 DAG 校验(在 `admission/validators/workflow.py`)
- **v0.1 stub**:Workflow 是声明,Task CR 由 v0.5+ 调度器负责;L3-1 仅 reconciliation 占位

**handler 概览**:

```python
# 完整文件 ~170 行;handler 3 个 + DAG 校验 helper + Task stub emitter
@kopf.on.create('workflow.superteam-a2a.io', id='workflow-create')
async def workflow_create(spec: WorkflowSpec, name: str, namespace: str, body: Workflow, **kwargs):
    controller = WorkflowController.get_instance()
    await ensure_finalizer(body=body, name=WORKFLOW_FINALIZER)
    # DAG 校验(已在 admission 双校验,此处仅 reconcile 时再次校验)
    validator = WorkflowValidator()
    validator.validate(spec.tasks)  # 触发 Kahn + 节点/边数检查
    await controller._reconciler.reconcile(spec=spec, status=body.status, body=body)
```

**关键不变量**(继承 L2-2 Design §4.3):
- ✅ DAG 校验在 admission webhook + reconcile 时双重校验
- ✅ Task 模板与 WorkflowSpec.tasks[i] 一致
- ✅ Finalizer:`workflow.superteam-a2a.io/cleanup`

### 3.4 MemoryReconciler（`reconcilers/memory_reconciler.py` · C-1.4 · 非 Controller）

> **与 L2-4 Spec v0.2.0 §7 完全双向同步**(ADR-0003 §6 + L2-4 §7 wire contract)

**职责**(继承 L2-2 Design §4.4):
1. **不是** Controller —— 是 Operator 内部定时后台任务
2. 由 **Leader Election 单 leader 触发**(`Election.is_leader()` 判断)
3. 定时触发(默认 60s,Helm values 可配):

```python
# packages/operator/src/superteam_a2a/operator/reconcilers/memory_reconciler.py
import kopf
from anyio import to_thread

from superteam_a2a.operator.leader_election import Election
from superteam_a2a.operator.models.memory.decay import compute_effective_confidence
from superteam_a2a.operator.models.memory.reinforce import apply_reinforce
from superteam_a2a.operator.models.memory.gc import should_garbage_collect
from superteam_a2a.operator.models.memory.promotion import is_eligible_for_promotion
from superteam_a2a.operator.clients import AsyncK8sClient

class MemoryReconcilerService:
    def __init__(self, k8s_client: AsyncK8sClient, election: Election, metrics: OperatorMetrics):
        self._k8s = k8s_client
        self._election = election
        self._metrics = metrics

    @kopf.timer('agent.superteam-a2a.io', interval=60.0, idle=30.0)  # §2.3.3 L2-2 §3
    async def reconcile_all_memories(self, **kwargs):
        """每 60s 触发(仅 leader)"""
        if not self._election.is_leader():
            return  # 非 leader 立即退出,不参与 reconcile

        # 1. 列出所有 namespace 的 Memory CR
        memories = await self._k8s.list_memories(namespace='*')

        # 2. CPU offload:batch decay 用 anyio.to_thread.run_sync(不阻塞 event loop)
        async def _batch_decay():
            results = []
            for memory in memories:
                effective_confidence = compute_effective_confidence(
                    confidence=memory.spec.confidence,
                    decay_days=memory.spec.decay_days or 30.0,
                    elapsed_days=memory.status.elapsed_days or 0.0,
                )
                results.append((memory, effective_confidence))
            return results

        results = await to_thread.run_sync(_batch_decay)

        # 3. 应用 decay + reinforce + GC + promotion
        for memory, effective_confidence in results:
            new_status = memory.status.copy()
            new_status.effective_confidence = effective_confidence
            if should_garbage_collect(effective_confidence):
                new_status.phase = MemoryPhase.GARBAGE_COLLECTED
            elif is_eligible_for_promotion(effective_confidence, memory.spec.reinforced_count):
                new_status.eligible_for_promotion = True
            await self._k8s.update_memory_status(name=memory.name, namespace=memory.namespace, status=new_status)
            self._metrics.inc_memory_decay_total(namespace=memory.namespace, result='success')
```

**关键不变量**(继承 L2-2 Design §4.4):
- ✅ 单 leader 触发(避免重复 reconcile 导致状态竞争)
- ✅ 每 60s 全量 reconcile(增量优化留 v0.5+)
- ✅ decay 公式 `confidence × exp(-elapsed_days / decay_days)` 与 L2-4 完全一致(数学公式 wire 不变)
- ✅ batch reconcile CPU offload(`anyio.to_thread.run_sync`,ADR-0005 §6.3)

### 3.5 4 Controllers 共同契约

- **Kopf handlers 总数**:12 个(create + update + delete × 4 Controller = 12;MemoryReconciler 是 `@kopf.timer` 1 个)
- **handler 行数预算**:30-50 行/handler(Go baseline 是 60-80 行/handler;Python 版精简 40% 得益于 Kopf decorator)
- **状态更新模式**:全部通过 `kopf.adopt + status_patch`(无直接 `kubectl patch`)
- **错误处理**:统一通过 `BaseReconciler.handle_error()` + 4 错误分类(见 §10 错误模型;在 #45+ 后续会话展开)
- **测试 ID 矩阵**:`UT-C-*` + `UT-R-*` + `UT-AW-*` 共计 ~80 + IT 12 + E2E 6(继承 L2-2 Spec §12)

---

## 4. admission webhook server 文件级 Spec（与 Operator 同 Deployment · ASGI）

> **本节把 L2-2 Spec v0.2.0 §4 + L2-2 Design v0.2.0 §5 的 admission 选型落到 9 个 Python 文件的精确契约**。Wire contract(4 CRD validators + DAG 校验 + TLS 热更新 + Knowledge↔Memory 双向互斥)与 v0.1-draft Go baseline **完全继续有效**,仅 supersede Go struct / kubebuilder 注解实现条款。
>
> **文件清单修正**:§2.3.5 表格标注为 "7 文件",实际 9 文件(`__init__.py` 2 + `server.py` + `tls.py` + 5 validators)。本 §4 按 9 文件精确展开,§2.3.5 表格计数在 #45+ 后续会话修正。

### 4.1 部署形态(与 L2-2 Design §5.2 一致)

```
+---------------------------------------+
|        Operator Pod (3 replicas)       |
|                                       |
|   +-------------------------------+   |
|   | Container 1: Kopf Operator   |   |
|   |  (4 Controllers + Lease)      |   |
|   |  Port: 8080 (metrics)         |   |
|   +-------------------------------+   |
|                                       |
|   +-------------------------------+   |
|   | Container 2: Admission ASGI   |   |
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

**关键决策**(继承 L2-2 Design §5.1):
- ✅ **同 Deployment 2 containers**:共享 Pod lifecycle + RBAC + NetworkPolicy + 镜像(ADR-0005 §6.2 单进程原则)
- ✅ **独立端口**:8080 metrics / 8443 admission webhook(端口隔离)
- ✅ **HTTPS only**:cert-manager 颁发证书(2160h / 720h renewBefore / Always rotationPolicy)
- ✅ **uvicorn 单 worker**:`python.workers: 1`(Helm values 强制;否则 admission server 并发导致 DAG 校验竞争)
- ✅ **Admission webhook 不调用 K8s API**:无状态 server,仅做字段校验;性能 + 安全

### 4.2 文件清单与契约(9 文件 · 全部在 `packages/operator/src/superteam_a2a/operator/admission/`)

> 每个文件列:**绝对路径**(基于 uv workspace 布局)/ **职责一句话**/ **完整 import 列表**/ **exported 符号签名**/ **内部 helper**/ **关联测试文件 + 测试 ID**

#### 4.2.1 `admission/__init__.py` —— 子包入口

```python
# packages/operator/src/superteam_a2a/operator/admission/__init__.py
from .server import AdmissionWebhookApp
from .tls import TLSConfig, TLSHotReloader

__all__ = ["AdmissionWebhookApp", "TLSConfig", "TLSHotReloader"]
```

| 字段 | 值 |
|---|---|
| **职责** | 公开 API export + 版本号 |
| **imports** | `from .server import AdmissionWebhookApp` / `from .tls import TLSConfig, TLSHotReloader` |
| **exported 符号** | `AdmissionWebhookApp`、`TLSConfig`、`TLSHotReloader` |
| **helper** | 无 |
| **测试文件** | `tests/unit/admission/test_admission___init__.py`(UT-AW-01) |

#### 4.2.2 `admission/server.py` —— ASGI admission webhook 主类

```python
# packages/operator/src/superteam_a2a/operator/admission/server.py
import ssl
from typing import Awaitable, Callable

import uvicorn
from pydantic import BaseModel, ConfigDict, Field
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from superteam_a2a.operator.admission.validators import (
    AgentValidator, AgentSetValidator, WorkflowValidator,
    MemoryValidator, MutualExclusionValidator,
)
from superteam_a2a.operator.config import HelmValues
from superteam_a2a.operator.observability.tracing import TracerProvider


class AdmissionRequest(BaseModel):
    """AdmissionReview wire contract(K8s AdmissionRegistration v1)"""
    model_config = ConfigDict(extra="ignore")  # 接收 K8s 完整 AdmissionReview,忽略未知字段
    uid: str
    kind: str  # "Agent" | "AgentSet" | "Workflow" | "Memory"
    operation: str  # "CREATE" | "UPDATE" | "DELETE"
    namespace: str
    name: str
    object: dict  # CRD 完整对象(由 validator 反序列化为 Pydantic)


class AdmissionResponse(BaseModel):
    """AdmissionReview response wire contract"""
    model_config = ConfigDict(extra="forbid")
    uid: str
    allowed: bool
    status: dict | None = None  # K8s Status 对象,reason + code + message
    warnings: list[str] | None = Field(default=None, max_length=10)


class AdmissionWebhookApp:
    """ASGI admission webhook 主类(uvicorn 单 worker)"""

    def __init__(
        self,
        helm_values: HelmValues,
        tls_config: "TLSConfig",
        agent_validator: AgentValidator,
        agentset_validator: AgentSetValidator,
        workflow_validator: WorkflowValidator,
        memory_validator: MemoryValidator,
        mutual_exclusion_validator: MutualExclusionValidator,
        tracer_provider: TracerProvider | None = None,
    ) -> None: ...

    async def startup(self) -> None:
        """启动 uvicorn(单 worker)+ 注册 ASGI routes"""

    async def shutdown(self) -> None:
        """graceful shutdown(wait for in-flight requests ≤ 30s)"""

    async def handle_validate(self, request: AdmissionRequest) -> AdmissionResponse:
        """POST /validate 路由:根据 kind 路由到对应 validator;DELETE 操作跳过"""
```

**内部 helper**:`_route_validator(kind: str) -> Validator`、`_tracing_middleware`、`_load_tls_context()`、`_emit_metric(validator: str, result: str)`(Prometheus `superteam_operator_admission_total{validator,result}`)

**关键设计**:
- `AdmissionRequest.uid` 必须 echo 到 `AdmissionResponse.uid`(K8s AdmissionReview wire contract)
- 路由分发:`CREATE` + `UPDATE` 走 validator;`DELETE` 直接 allowed=true(admission 不拦截删除)
- `extra="ignore"` on AdmissionRequest(K8s AdmissionReview 包含很多 Operator 不关心的字段如 `apiVersion`/`resource`)

**测试文件**:
- `tests/unit/admission/test_admission_server.py`(UT-AW-02~06)
  - UT-AW-02:startup() 创建 ASGI app + 注册 1 个 route
  - UT-AW-03:handle_validate 路由分发(Agent → AgentValidator;Workflow → WorkflowValidator)
  - UT-AW-04:DELETE 操作直接 allowed=true
  - UT-AW-05:AdmissionRequest.uid echo 到 AdmissionResponse.uid
  - UT-AW-06:Prometheus metric superteam_operator_admission_total{validator,result} 在 success/failure 时各自 inc
- `tests/integration/admission/test_admission_e2e.py`(IT-AW-01~02)
  - IT-AW-01:envtest + ValidatingWebhookConfiguration → 真实 K8s API Server 触发 admission(用 `pytest-kopf` + `kopf.testing.KopfFixture`)
  - IT-AW-02:DELETE 操作 admission 无 metric inc

#### 4.2.3 `admission/tls.py` —— cert-manager 集成 + 证书热更新

```python
# packages/operator/src/superteam_a2a/operator/admission/tls.py
import ssl
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from kubernetes_asyncio import client
from kubernetes_asyncio.watch import AsyncWatch

from superteam_a2a.operator.config import HelmValues
from superteam_a2a.operator.observability.logging import get_logger


class TLSConfig:
    """TLS 证书配置 + 路径"""

    def __init__(
        self,
        secret_name: str,
        namespace: str,
        cert_path: Path,
        key_path: Path,
        ca_bundle_path: Path | None = None,
    ) -> None: ...

    async def load_from_disk(self) -> ssl.SSLContext:
        """从 Secret 同步加载 TLS 证书到 SSLContext(冷启动)"""
        ...

    async def watch_and_reload(
        self,
        k8s: client.CoreV1Api,
        on_reload: Callable[[ssl.SSLContext], Awaitable[None]],
    ) -> None:
        """监听 Secret 更新事件 + 触发 SSLContext 重建(热更新,每 5min 兜底轮询)"""
        ...


class TLSHotReloader:
    """持有当前 SSLContext 引用 + 支持 atomic swap"""

    def __init__(self, initial_ctx: ssl.SSLContext) -> None:
        self._ctx = initial_ctx
        self._lock = asyncio.Lock()

    async def swap(self, new_ctx: ssl.SSLContext) -> None:
        """Atomic 替换 SSLContext(uvicorn 下次 accept 时生效)"""

    def current(self) -> ssl.SSLContext:
        """返回当前 SSLContext(uvicorn 配置用)"""
        ...
```

**内部 helper**:`_is_cert_expiring_soon(cert_pem: bytes, threshold_days: int = 30) -> bool`、`_reload_uvicorn_ssl_context(new_ctx)`、`_build_ssl_context(cert_pem, key_pem) -> ssl.SSLContext`(使用 `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)` + `minimum_version = ssl.TLSVersion.TLSv1_3`)、`_parse_secret_data(secret) -> tuple[bytes, bytes]`、`_setup_watcher()`、`_fallback_poll_loop()`(每 5min 检查证书过期时间,即使 watch 失效也兜底轮换)

**关键不变量**(继承 L2-2 Spec §4.5):
- ✅ **热更新不重启 server**:Secret 更新事件触发 SSLContext atomic swap;uvicorn 下次 accept 时自动应用
- ✅ **轮换策略**:`duration: 2160h`(90 天)/ `renewBefore: 720h`(30 天前续期)/ `privateKey.rotationPolicy: Always`
- ✅ **TLS 1.3 minimum**:禁用 TLS 1.2 及以下(L2-2 Spec §4.5)
- ✅ **5min 兜底轮询**:即使 watch 失效也能恢复

**测试文件**:
- `tests/unit/admission/test_admission_tls.py`(UT-AW-07~10)
  - UT-AW-07:SSLContext min version = TLSv1.3
  - UT-AW-08:watch_and_reload 触发 swap(用 fake AsyncWatch)
  - UT-AW-09:_is_cert_expiring_soon 阈值正确(threshold_days=30,过期 25 天 → True)
  - UT-AW-10:fallback poll loop 每 5min 触发一次
- `tests/integration/admission/test_admission_tls_reload.py`(IT-AW-03)
  - IT-AW-03:envtest + cert-manager mock → Secret 更新触发 reload,uvicorn 接受新连接用新证书

#### 4.2.4 `admission/validators/__init__.py` —— 5 validator 聚合

```python
# packages/operator/src/superteam_a2a/operator/admission/validators/__init__.py
from .agent import AgentValidator
from .agentset import AgentSetValidator
from .workflow import WorkflowValidator
from .memory import MemoryValidator
from .mutual_exclusion import MutualExclusionValidator
from .base import CRDValidator, ValidationResult

__all__ = [
    "CRDValidator", "ValidationResult",
    "AgentValidator", "AgentSetValidator", "WorkflowValidator",
    "MemoryValidator", "MutualExclusionValidator",
]
```

| 字段 | 值 |
|---|---|
| **职责** | 导出 5 validators + base Protocol + ValidationResult |
| **imports** | 见上(从 5 个 validator 子模块) |
| **exported 符号** | `CRDValidator`、`ValidationResult` + 5 个 validator 类 |
| **helper** | 无 |
| **测试文件** | `tests/unit/admission/test_validators___init__.py`(UT-AW-11) |

#### 4.2.5 `admission/validators/base.py` —— CRDValidator Protocol + ValidationResult

```python
# packages/operator/src/superteam_a2a/operator/admission/validators/base.py
from typing import Protocol
from pydantic import BaseModel, ConfigDict, Field


class ValidationResult(BaseModel):
    """admission 校验结果(K8s AdmissionReview response 序列化)"""
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    reason: str | None = Field(default=None, max_length=512)
    http_status: int = Field(default=200, ge=200, le=599)  # 200=allowed; 422=invalid; 400=malformed


class CRDValidator(Protocol):
    """5 validators 必须实现此接口(L2-2 Spec §4.2 + Design §5.3)"""

    crd_kind: str  # "Agent" | "AgentSet" | "Workflow" | "Memory"
    group: str     # "superteam-a2a.io"

    async def validate(
        self,
        namespace: str,
        name: str,
        spec: BaseModel,
        operation: str,  # "CREATE" | "UPDATE"
    ) -> ValidationResult:
        """同步校验 spec;返回 ValidationResult(allowed, reason, http_status)"""
        ...
```

**关键不变量**:
- `ValidationResult.extra="forbid"`:拒绝未知字段(K8s wire shape 严格)
- `CRDValidator` 是 Protocol 而非 ABC:用 `runtime_checkable` 让 L4 实施可灵活实现

#### 4.2.6 `admission/validators/agent.py` —— AgentValidator

```python
# packages/operator/src/superteam_a2a/operator/admission/validators/agent.py
from pydantic import ValidationError

from superteam_a2a.operator.models.agent import AgentSpec
from .base import CRDValidator, ValidationResult


class AgentValidator:
    """Agent CRD admission validator(Pydantic v2 严格校验)"""

    crd_kind: str = "Agent"
    group: str = "superteam-a2a.io"

    async def validate(
        self,
        namespace: str,
        name: str,
        spec: AgentSpec,
        operation: str,
    ) -> ValidationResult:
        # Pydantic 已在反序列化阶段完成 min_length/max_length/enum/regex 校验
        # 此处仅做跨字段 + 业务约束
        try:
            # 1. image 必填(command + args 互斥)
            if not spec.image and not (spec.command and spec.args):
                return ValidationResult(
                    allowed=False,
                    reason="AgentSpec 必须指定 image 或 (command + args)",
                    http_status=422,
                )
            # 2. replicas ∈ [1, 100]
            if spec.replicas < 1 or spec.replicas > 100:
                return ValidationResult(
                    allowed=False,
                    reason=f"replicas {spec.replicas} 超出范围 [1, 100]",
                    http_status=422,
                )
            # 3. mode 与 securityContext 互斥(Plugin 模式禁止 securityContext.privileged)
            if spec.mode.value == "plugin" and spec.security_context and spec.security_context.privileged:
                return ValidationResult(
                    allowed=False,
                    reason="Plugin 模式禁止 securityContext.privileged(由 sidecar 接管)",
                    http_status=422,
                )
            return ValidationResult(allowed=True)
        except ValidationError as e:
            return ValidationResult(allowed=False, reason=str(e), http_status=422)
```

**关键校验**(继承 L2-2 Design §5.3.1):
- ✅ image 必填(command + args 互斥)
- ✅ `1 ≤ replicas ≤ 100`（继承 v0.1 Go baseline）
- ✅ Plugin 模式禁止 privileged(由 sidecar 接管)

**测试文件**:`tests/unit/admission/test_agent_validator.py`(UT-AW-12)
- UT-AW-12a:image 缺失返回 allowed=false(422)
- UT-AW-12b:replicas=0 返回 allowed=false
- UT-AW-12c:Plugin + privileged 返回 allowed=false

#### 4.2.7 `admission/validators/agentset.py` —— AgentSetValidator

```python
# packages/operator/src/superteam_a2a/operator/admission/validators/agentset.py
from superteam_a2a.operator.models.agentset import AgentSetSpec
from .base import CRDValidator, ValidationResult


class AgentSetValidator:
    crd_kind: str = "AgentSet"
    group: str = "superteam-a2a.io"

    async def validate(self, namespace: str, name: str, spec: AgentSetSpec, operation: str) -> ValidationResult:
        # 1. replicas ∈ [1, 100]
        # 2. selector 必填(与 template.labels 一致)
        # 3. template 字段必填且类型 = AgentSpec(跨 CRD 一致性)
        ...
```

**关键校验**:replicas 范围、selector 必填、template 与 AgentSpec 一致

**测试文件**:`tests/unit/admission/test_agentset_validator.py`(UT-AW-13)

#### 4.2.8 `admission/validators/workflow.py` —— WorkflowValidator + DAG 校验

```python
# packages/operator/src/superteam_a2a/operator/admission/validators/workflow.py
from collections import deque
from pydantic import BaseModel

from superteam_a2a.operator.models.workflow import WorkflowSpec, TaskSpec
from .base import CRDValidator, ValidationResult


class DAGValidator:
    """DAG 校验(纯函数 · 无 I/O;L2-2 Spec §4.4 + Design §5.5)"""

    MAX_NODES = 50
    MAX_EDGES = 200

    def validate_dag(self, tasks: list[TaskSpec]) -> ValidationResult:
        if len(tasks) > self.MAX_NODES:
            return ValidationResult(
                allowed=False,
                reason=f"节点数 {len(tasks)} > {self.MAX_NODES}",
                http_status=422,
            )
        # 构建邻接表 + 边数检查
        adj = {task.name: set(task.depends_on) for task in tasks}
        edge_count = sum(len(deps) for deps in adj.values())
        if edge_count > self.MAX_EDGES:
            return ValidationResult(
                allowed=False,
                reason=f"边数 {edge_count} > {self.MAX_EDGES}",
                http_status=422,
            )
        # Kahn 算法检测环
        in_degree = {task.name: len(adj[task.name]) for task in tasks}
        queue = deque(name for name, deg in in_degree.items() if deg == 0)
        topo_order: list[str] = []
        while queue:
            node = queue.popleft()
            topo_order.append(node)
            for neighbor, deps in adj.items():
                if node in deps:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        if len(topo_order) != len(tasks):
            cycle_nodes = [name for name, deg in in_degree.items() if deg > 0]
            return ValidationResult(
                allowed=False,
                reason=f"检测到环，涉及节点: {cycle_nodes}",
                http_status=422,
            )
        return ValidationResult(allowed=True)


class WorkflowValidator:
    """Workflow CRD admission validator"""

    crd_kind: str = "Workflow"
    group: str = "superteam-a2a.io"

    def __init__(self) -> None:
        self._dag_validator = DAGValidator()

    async def validate(self, namespace: str, name: str, spec: WorkflowSpec, operation: str) -> ValidationResult:
        # 1. DAG 校验(纯函数)
        dag_result = self._dag_validator.validate_dag(spec.tasks)
        if not dag_result.allowed:
            return dag_result
        # 2. tasks[i].name 唯一性
        names = [t.name for t in spec.tasks]
        if len(set(names)) != len(names):
            return ValidationResult(
                allowed=False,
                reason=f"task name 重复: {[n for n in names if names.count(n) > 1]}",
                http_status=422,
            )
        # 3. depends_on 引用必须存在(已在 Kahn 中部分检查)
        task_name_set = set(names)
        for task in spec.tasks:
            for dep in task.depends_on:
                if dep not in task_name_set:
                    return ValidationResult(
                        allowed=False,
                        reason=f"task {task.name} 的 depends_on {dep} 不存在",
                        http_status=422,
                    )
        return ValidationResult(allowed=True)
```

**关键设计**(继承 L2-2 Spec §4.4 + Design §5.5):
- ✅ **`DAGValidator` 是纯函数类**(无 I/O;单测无需 mock)
- ✅ **`collections.deque` BFS**(O(V+E) 算法复杂度,优于 DFS 递归栈)
- ✅ **节点/边数限制为软上限**(v0.5+ 可配)
- ✅ **task name 唯一性 + depends_on 引用存在性**(在 DAG 拓扑之外额外校验)

**测试文件**:
- `tests/unit/admission/test_workflow_validator.py`(UT-AW-14~16)
  - UT-AW-14:51 个 task 返回 allowed=false(超 MAX_NODES)
  - UT-AW-15:A→B→C→A 检测到环(列出 cycle_nodes)
  - UT-AW-16:linear DAG(A→B→C)allowed=true + topo_order 正确
- `tests/integration/admission/test_dag_validation.py`(IT-AW-04)
  - IT-AW-04:envtest + 提交 Workflow CRD with cycle → K8s API Server 拒绝(etcd 不写入)

#### 4.2.9 `admission/validators/memory.py` —— MemoryValidator

```python
# packages/operator/src/superteam_a2a/operator/admission/validators/memory.py
from superteam_a2a.operator.models.memory import MemorySpec
from .base import CRDValidator, ValidationResult


class MemoryValidator:
    crd_kind: str = "Memory"
    group: str = "superteam-a2a.io"

    async def validate(self, namespace: str, name: str, spec: MemorySpec, operation: str) -> ValidationResult:
        # 1. content 键数满足 1 ≤ count ≤ 20（继承 L2-4 Spec §3.4 MemorySpec）
        # 2. scope_ref 必填
        # 3. agent-private visibility 必填 owner_agent_id
        # 4. decay_days ∈ [1, 3650]
        # 5. confidence ∈ [0, 1]
        ...
```

**关键校验**:与 L2-4 Spec §3.4 MemorySpec **字段逐一对应**(wire contract 完全一致)

**测试文件**:`tests/unit/admission/test_memory_validator.py`(UT-AW-17)

#### 4.2.10 `admission/validators/mutual_exclusion.py` —— MutualExclusionValidator(Knowledge ↔ Memory)

```python
# packages/operator/src/superteam_a2a/operator/admission/validators/mutual_exclusion.py
from superteam_a2a.operator.clients import AsyncK8sClient
from .base import CRDValidator, ValidationResult


class MutualExclusionValidator:
    """Knowledge ↔ Memory 双向互斥校验(ADR-0002 §2 + ADR-0003 §5)

    在 Agent / AgentSet / Workflow / Memory 4 个 validator 中各调用一次,
    避免漏检(继承 L2-2 Spec §4.6 + Design §5.4)
    """

    def __init__(self, k8s_client: AsyncK8sClient) -> None: ...

    async def validate(
        self,
        namespace: str,
        name: str,
        source_ref_name: str,
        resource_kind: str,  # "KnowledgeItem" | "Memory"
    ) -> ValidationResult:
        # 注:admission webhook 默认不调用 K8s API(L2-2 Design §5.7)
        # 但 mutual_exclusion 例外:必须读 K8s 才能校验双向引用
        # 性能优化:用 label selector 索引,O(1) 查询
        if resource_kind == "Memory":
            # 创建/更新 Memory → 检查是否有 KnowledgeItem 引用同一 source_ref
            knowledge_items = await self._k8s.list(
                "KnowledgeItem",
                namespace=namespace,
                label_selector=f"superteam-a2a.io/source-ref={source_ref_name}",
            )
            if knowledge_items:
                return ValidationResult(
                    allowed=False,
                    reason=f"ResourceRef {source_ref_name} 已被 {len(knowledge_items)} 个 KnowledgeItem 引用,不可同时作为 Memory source",
                    http_status=422,
                )
        elif resource_kind == "KnowledgeItem":
            # 创建/更新 KnowledgeItem → 检查是否有 Memory 引用同一 source_ref
            memories = await self._k8s.list(
                "Memory",
                namespace=namespace,
                label_selector=f"superteam-a2a.io/source-ref={source_ref_name}",
            )
            if memories:
                return ValidationResult(
                    allowed=False,
                    reason=f"ResourceRef {source_ref_name} 已被 {len(memories)} 个 Memory 引用,不可同时作为 KnowledgeItem source",
                    http_status=422,
                )
        return ValidationResult(allowed=True)
```

**关键设计**(继承 L2-2 Design §5.4):
- ✅ **是 5 个 validators 中唯一调用 K8s API 的**(性能优化:label selector O(1) 查询)
- ✅ **双向校验**:Memory 创建查 KnowledgeItem;KnowledgeItem 创建查 Memory
- ✅ **在 4 CRD validators 各调用一次**(L2-2 Spec §4.6):Agent/AgentSet/Workflow/Memory 各自 spec 含 sourceRef 字段时触发

**测试文件**:`tests/unit/admission/test_mutual_exclusion_validator.py`(UT-AW-18)
- UT-AW-18a:Memory 创建时已有 KI 引用 → allowed=false
- UT-AW-18b:KI 创建时已有 Memory 引用 → allowed=false
- UT-AW-18c:双向均无 → allowed=true

### 4.3 Helm `webhookconfig.yaml` 契约(9 Helm 模板之一)

**关键文件**:`deploy/helm/operator/templates/webhookconfig.yaml`

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: superteam-a2a-operator-validating
  annotations:
    cert-manager.io/inject-ca-from: "{{ .Release.Namespace }}/superteam-a2a-webhook-tls"
spec:
  admissionReviewVersions: ["v1"]
  sideEffects: None  # admission 不修改 CRD,sideEffects=None
  failurePolicy: Fail  # webhook 不可用时拒绝请求(安全优先)
  webhooks:
    - name: validate-agent.superteam-a2a.io
      rules:
        - apiGroups: ["agent.superteam-a2a.io"]
          apiVersions: ["v1alpha1"]
          operations: ["CREATE", "UPDATE"]
          resources: ["agents"]
          scope: Namespaced
      clientConfig:
        service:
          name: superteam-a2a-operator
          namespace: "{{ .Release.Namespace }}"
          path: /validate
        caBundle: <cert-manager 注入>
      namespaceSelector:
        matchLabels:
          superteam-a2a.io/webhook-enabled: "true"
      timeoutSeconds: 5
    # agentset / workflow / memory 同结构(共 4 webhooks)
```

**关键决策**:
- ✅ **sideEffects: None**(admission 不修改 CRD;K8s 1.27+ 推荐)
- ✅ **failurePolicy: Fail**(webhook 不可用时拒绝请求;安全优先)
- ✅ **timeoutSeconds: 5**(DAG 校验 50 节点 < 100ms;5s 充裕)
- ✅ **namespaceSelector 限制**:仅 label `superteam-a2a.io/webhook-enabled: "true"` 的 namespace 触发(允许用户 opt-out)

### 4.4 关键不变量(继承 L2-2 Spec §4.6)

- ✅ **4 CRD validators 全部用 Pydantic v2 严格校验**(`extra="forbid"`,L2-2 Spec §4.6)
- ✅ **DAG 校验是纯函数**(`DAGValidator` 类无 I/O,单测无需 mock;L2-2 Design §5.5)
- ✅ **双向互斥校验在 4 CRD validators 各调用一次**(L2-2 Spec §4.6,避免漏检)
- ✅ **Admission webhook 拒绝的请求不写 etcd**(K8s API Server 默认行为)
- ✅ **TLS 证书热更新不重启 webhook server**(`TLSHotReloader.swap` atomic)
- ✅ **admission webhook 默认不调用 K8s API**(性能 + 安全;`MutualExclusionValidator` 是唯一例外,带 label selector 优化)

### 4.5 测试 ID 矩阵(18 项 · §A-§G 5 维度全 PASS)

| 测试 ID | 维度 | 描述 | 文件 |
|---|---|---|---|
| **UT-AW-01** | A 功能 | admission 子包 `__init__.py` 导出 3 个公开符号 | `tests/unit/admission/test_admission___init__.py` |
| **UT-AW-02** | A 功能 | `AdmissionWebhookApp.startup()` 创建 ASGI app + 注册 1 个 route | `tests/unit/admission/test_admission_server.py` |
| **UT-AW-03** | A 功能 | `handle_validate` 路由分发(Agent → AgentValidator) | 同上 |
| **UT-AW-04** | A 功能 | DELETE 操作直接 allowed=true | 同上 |
| **UT-AW-05** | C 接口契约 | AdmissionRequest.uid echo 到 AdmissionResponse.uid | 同上 |
| **UT-AW-06** | D 可观测性 | Prometheus `superteam_operator_admission_total` 在 success/failure 各自 inc | 同上 |
| **UT-AW-07** | B 安全 | SSLContext min version = TLSv1.3 | `tests/unit/admission/test_admission_tls.py` |
| **UT-AW-08** | A 功能 | `watch_and_reload` 触发 swap(fake AsyncWatch) | 同上 |
| **UT-AW-09** | A 功能 | `_is_cert_expiring_soon` 阈值正确(过期 25 天 → True) | 同上 |
| **UT-AW-10** | A 功能 | fallback poll loop 每 5min 触发一次 | 同上 |
| **UT-AW-11** | A 功能 | validators 子包 `__init__.py` 导出 7 个公开符号 | `tests/unit/admission/test_validators___init__.py` |
| **UT-AW-12** | A 功能 | AgentValidator:image 缺失 + replicas 超界 + Plugin+privileged 拒绝 | `tests/unit/admission/test_agent_validator.py` |
| **UT-AW-13** | A 功能 | AgentSetValidator:replicas 范围 + selector 必填 + template 一致 | `tests/unit/admission/test_agentset_validator.py` |
| **UT-AW-14** | A 功能 | DAGValidator:51 个 task → allowed=false(超 MAX_NODES) | `tests/unit/admission/test_workflow_validator.py` |
| **UT-AW-15** | A 功能 | DAGValidator:A→B→C→A 检测环(列出 cycle_nodes) | 同上 |
| **UT-AW-16** | A 功能 | DAGValidator:linear DAG → allowed=true + topo_order 正确 | 同上 |
| **UT-AW-17** | A 功能 | MemoryValidator:content 键数 + decay_days + confidence 边界 | `tests/unit/admission/test_memory_validator.py` |
| **UT-AW-18** | A 功能 | MutualExclusionValidator:双向引用冲突拒绝 | `tests/unit/admission/test_mutual_exclusion_validator.py` |
| **IT-AW-01** | A 功能 | envtest:ValidatingWebhookConfiguration → K8s API Server 触发 admission | `tests/integration/admission/test_admission_e2e.py` |
| **IT-AW-02** | D 可观测性 | DELETE 操作 admission 无 metric inc | 同上 |
| **IT-AW-03** | B 安全 | envtest:Secret 更新触发 reload,uvicorn 接受新连接用新证书 | `tests/integration/admission/test_admission_tls_reload.py` |
| **IT-AW-04** | A 功能 | envtest:提交 Workflow CRD with cycle → K8s 拒绝(etcd 不写入) | `tests/integration/admission/test_dag_validation.py` |

**测试 ID 分布**:18 UT + 4 IT = 22 ID(覆盖 §A-§G 5 维度:功能 14 / 安全 2 / 接口契约 1 / 可观测性 2 / 其他 1)

**与 Go baseline 对应**:L2-2 Go baseline §4.3 admission webhook + §10.1 自定义错误码;wire contract(4 CRD 错误码 + 422/400 HTTP Status)与 v0.1 业务语义**完全继续有效**

---

## 5. Leader Election 客户端文件级 Spec（K8s Lease · 单 leader 触发 reconcile + MemoryReconciler）

> **本节把 L2-2 Spec v0.2.0 §5 + L2-2 Design v0.2.0 §6 的 Leader Election 选型落到 3 个 Python 文件的精确契约**。Wire contract(Lease 名称 + 30s leaseDurationSeconds + 单 leader 模型)与 v0.1-draft Go baseline **完全继续有效**,仅 supersede Go struct / client-go 实现条款。
>
> **文件清单修正**:§2.3.6 表格标注为 "2 文件",实际 3 文件(`__init__.py` + `lease_client.py` + `election.py`)。本 §5 按 3 文件精确展开,§2.3.6 表格计数在 #45+ 后续会话修正。

### 5.1 部署动机与边界(继承 L2-2 Design §6.1)

**单 leader 强制**:Operator 部署 3 replicas 时,**仅 1 个**副本持有 Lease 并触发 reconcile + MemoryReconciler;其他 2 个进入 standby(仅 watch 事件,不写业务资源)。

**业务影响**:
- ✅ **避免重复 reconcile**:同一 CRD 资源被多副本并发处理,浪费 API Server + 状态竞争
- ✅ **MemoryReconciler 单触发**:避免多副本同时触发 decay 算法导致 MemoryStatus 抖动
- ✅ **graceful shutdown**:`SIGTERM` → release Lease → 下一 leader 立即接管(避免 30s 等待)

**admission webhook 不走 LeaderGate**:admission 是 K8s API Server 前置校验,必须在所有副本上可用(否则 3 replicas 中 2 replicas 拒收 admission 请求,违反 SLO)

### 5.2 文件清单与契约(3 文件 · 全部在 `packages/operator/src/superteam_a2a/operator/leader_election/`)

#### 5.2.1 `leader_election/__init__.py` —— 子包入口

```python
# packages/operator/src/superteam_a2a/operator/leader_election/__init__.py
from .lease_client import AsyncLeaseClient, LeaseApi
from .election import Election, LeaderGate

__all__ = ["AsyncLeaseClient", "LeaseApi", "Election", "LeaderGate"]
```

| 字段 | 值 |
|---|---|
| **职责** | 公开 API export |
| **exported 符号** | `AsyncLeaseClient`、`LeaseApi`(Protocol)、`Election`、`LeaderGate` |
| **测试文件** | `tests/unit/leader_election/test_leader_election___init__.py`(UT-LE-01) |

#### 5.2.2 `leader_election/lease_client.py` —— AsyncLeaseClient(K8s Lease 封装)

```python
# packages/operator/src/superteam_a2a/operator/leader_election/lease_client.py
import socket
import uuid
from collections.abc import Awaitable
from datetime import datetime, timezone, timedelta

from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from superteam_a2a.operator.observability.logging import get_logger


class LeaseApi(Protocol):
    """AsyncLeaseClient 所需的最小 K8s Lease API(测试用 fake client 实现)"""

    async def read_namespaced_lease(self, name: str, namespace: str): ...
    async def create_namespaced_lease(self, namespace: str, body): ...
    async def replace_namespaced_lease(self, name: str, namespace: str, body): ...


class AsyncLeaseClient:
    """K8s Lease 异步客户端(CAS 操作 · renew 失败重试)"""

    DEFAULT_LEASE_DURATION_SECONDS = 30

    def __init__(
        self,
        k8s: LeaseApi,
        lease_name: str = "superteam-a2a-operator-leader",
        namespace: str = "superteam-a2a-system",
        holder_id: str | None = None,  # None 时自动生成 <pod-name>-<uuid>
        lease_duration_seconds: int = DEFAULT_LEASE_DURATION_SECONDS,
    ) -> None:
        self._k8s = k8s
        self._lease_name = lease_name
        self._namespace = namespace
        self._holder_id = holder_id or f"{socket.gethostname()}-{uuid.uuid4()}"
        self._lease_duration = timedelta(seconds=lease_duration_seconds)

    @property
    def holder_id(self) -> str:
        return self._holder_id

    async def try_acquire(self) -> bool:
        """尝试获取 Lease(CAS 操作)

        返回 True 表示获取成功;False 表示已被其他副本持有(未过期)或冲突
        """
        try:
            existing = await self._k8s.read_namespaced_lease(self._lease_name, self._namespace)
            # 已存在且未过期 + holder 不是自己 → 已被其他副本持有
            if existing.spec.holder_identity and not self._is_expired(existing):
                if existing.spec.holder_identity != self._holder_id:
                    return False
            # CAS 更新(必须带 resourceVersion)
            existing.spec.holder_identity = self._holder_id
            existing.spec.acquire_time = datetime.now(timezone.utc).isoformat()
            existing.spec.renew_time = datetime.now(timezone.utc).isoformat()
            existing.spec.lease_duration_seconds = int(self._lease_duration.total_seconds())
            await self._k8s.replace_namespaced_lease(
                self._lease_name, self._namespace, existing
            )
            return True
        except ApiException as e:
            if e.status == 404:
                # Lease 不存在 → 创建
                await self._create_lease()
                return True
            if e.status == 409:
                # Conflict → CAS 失败;返回 False 不重试(下一轮 acquire 再试)
                return False
            raise

    async def renew(self) -> bool:
        """续约 Lease(更新 renew_time + resourceVersion CAS)

        返回 True 表示续约成功;False 表示失主(被其他副本抢占)
        """
        try:
            lease = await self._k8s.read_namespaced_lease(self._lease_name, self._namespace)
            if lease.spec.holder_identity != self._holder_id:
                return False  # 已被其他副本抢占
            lease.spec.renew_time = datetime.now(timezone.utc).isoformat()
            await self._k8s.replace_namespaced_lease(
                self._lease_name, self._namespace, lease
            )
            return True
        except ApiException:
            return False

    async def release(self) -> None:
        """主动让位(graceful shutdown;读到其他 holder 时 no-op)"""
        try:
            lease = await self._k8s.read_namespaced_lease(self._lease_name, self._namespace)
            if lease.spec.holder_identity == self._holder_id:
                lease.spec.holder_identity = None
                await self._k8s.replace_namespaced_lease(
                    self._lease_name, self._namespace, lease
                )
        except ApiException:
            pass  # 已过期或不存在;no-op

    def is_expired(self, lease, now: datetime | None = None) -> bool:
        """判断 Lease 是否过期(now + lease_duration < renew_time → 过期)"""
        check_time = now or datetime.now(timezone.utc)
        renew_time = datetime.fromisoformat(lease.spec.renew_time)
        return (check_time - renew_time) > self._lease_duration

    async def _create_lease(self) -> None:
        """创建 Lease(spec 含 holder + acquire_time + renew_time)"""
        now = datetime.now(timezone.utc)
        body = client.V1Lease(
            metadata=client.V1ObjectMeta(name=self._lease_name, namespace=self._namespace),
            spec=client.V1LeaseSpec(
                holder_identity=self._holder_id,
                acquire_time=now.isoformat(),
                renew_time=now.isoformat(),
                lease_duration_seconds=int(self._lease_duration.total_seconds()),
            ),
        )
        await self._k8s.create_namespaced_lease(self._namespace, body)
```

**关键设计**(继承 L2-2 Spec §5.2 + Design §6.3):
- ✅ **CAS 更新必须携带 `resourceVersion`**(由 `read_namespaced_lease` 返回的 body 自带)
- ✅ **holder_id 稳定且唯一**:`<pod-name>-<uuid>` 在进程生命周期内不变,跨 Pod 唯一
- ✅ **UTC RFC 3339 序列化**:禁止本地时区(L2-2 Spec §5.2 wire contract)
- ✅ **404 → create;409 → no-retry**(继承 L2-2 Spec §5.2)

**内部 helper**:`_is_expired(lease)`(纯函数,接受 `now` 参数便于 fake clock 测试)、`_create_lease()`

**测试文件**:
- `tests/unit/leader_election/test_lease_client.py`(UT-LE-02~06)
  - UT-LE-02:try_acquire Lease 不存在(404)→ 自动 create + return True
  - UT-LE-03:try_acquire Lease 存在 + holder=其他 + 未过期 → return False
  - UT-LE-04:try_acquire create 遇到 409 → return False(不覆盖已有 holder)
  - UT-LE-05:renew holder 被抢占 → return False
  - UT-LE-06:release 时 holder=其他 → no-op
- `tests/integration/leader_election/test_lease_client_k8s.py`(IT-LE-01)
  - IT-LE-01:envtest + CoordinationV1Api 真集群:create + acquire + renew + release 全流程

#### 5.2.3 `leader_election/election.py` —— Election 主类 + LeaderGate

```python
# packages/operator/src/superteam_a2a/operator/leader_election/election.py
import asyncio
from collections.abc import Callable
from typing import Protocol

from superteam_a2a.operator.observability.logging import get_logger
from superteam_a2a.operator.observability.metrics import OperatorMetrics
from .lease_client import AsyncLeaseClient


class LeaderGate(Protocol):
    """Controller 业务逻辑前置门禁(非 leader 时抛出 StandbyError)"""

    @property
    def is_leader(self) -> bool: ...

    def require_leader(self) -> None:
        """非 leader 时抛出 StandbyError(Controller 必须调用)"""
        ...


class Election:
    """Leader Election 主类(独立 asyncio task · 不阻塞 event loop)

    状态机(继承 L2-2 Spec §5.3):
      Standby → Leader(acquire) → Standby(renew failed x3 / release / stop)
    """

    DEFAULT_RENEW_INTERVAL_SECONDS = 10
    DEFAULT_ACQUIRE_INTERVAL_SECONDS = 5
    DEFAULT_MAX_RENEW_FAILURES = 3

    def __init__(
        self,
        lease: AsyncLeaseClient,
        on_acquired: Callable[[], Awaitable[None]],
        on_lost: Callable[[], Awaitable[None]],
        renew_interval_seconds: int = DEFAULT_RENEW_INTERVAL_SECONDS,
        acquire_interval_seconds: int = DEFAULT_ACQUIRE_INTERVAL_SECONDS,
        max_renew_failures: int = DEFAULT_MAX_RENEW_FAILURES,
        metrics: OperatorMetrics | None = None,
    ) -> None:
        self._lease = lease
        self._on_acquired = on_acquired
        self._on_lost = on_lost
        self._renew_interval = renew_interval_seconds
        self._acquire_interval = acquire_interval_seconds
        self._max_renew_failures = max_renew_failures
        self._metrics = metrics
        self._is_leader = False
        self._task: asyncio.Task | None = None
        self._renew_failures = 0

    @property
    def is_leader(self) -> bool:
        return self._is_leader

    def require_leader(self) -> None:
        """Controller 在 reconcile 前调用;非 leader 抛出 StandbyError"""
        if not self._is_leader:
            raise StandbyError("not leader")

    async def start(self) -> None:
        """启动 Leader Election loop(独立 asyncio task)"""
        if self._task is not None:
            return  # 幂等(重复调用不创建第二个 task)
        self._task = asyncio.create_task(self._election_loop())

    async def stop(self) -> None:
        """停止 Leader Election + best-effort release(若当前为 leader)"""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._is_leader:
            try:
                await self._lease.release()
                await self._on_lost()
            except Exception as e:
                get_logger().warning("leader_release_failed", error=str(e))

    async def _election_loop(self) -> None:
        """持续 acquire/renew;renew 失败 3 次触发 on_lost"""
        while True:
            try:
                if not await self._lease.try_acquire():
                    await asyncio.sleep(self._acquire_interval)
                    continue
                # 获取成功
                self._is_leader = True
                self._renew_failures = 0
                if self._metrics:
                    self._metrics.set_leader_state(namespace=self._lease._namespace, value=1)
                await self._on_acquired()
                # 续约循环
                while await self._lease.renew():
                    self._renew_failures = 0
                    await asyncio.sleep(self._renew_interval)
                # renew 返回 False(连续 1 次失败) → 计入失败计数
                self._renew_failures += 1
                if self._renew_failures >= self._max_renew_failures:
                    # 连续失败达到阈值 → 失主
                    self._is_leader = False
                    if self._metrics:
                        self._metrics.set_leader_state(namespace=self._lease._namespace, value=0)
                    await self._on_lost()
                    try:
                        await self._lease.release()
                    except Exception:
                        pass
            except asyncio.CancelledError:
                raise
            except Exception as e:
                get_logger().error("leader_election_error", error=str(e))
                await asyncio.sleep(self._acquire_interval)


class StandbyError(Exception):
    """非 leader 时 Controller 抛出,Kopf 标记为 TemporaryError 并延迟重试"""
    pass
```

**关键设计**(继承 L2-2 Spec §5.3 + Design §6.4):
- ✅ **独立 asyncio task**:Lease 续约不阻塞 Kopf handler 或 admission server
- ✅ **`start()` 幂等**:重复调用不创建第二个 task(L2-2 Spec §5.3 契约 #1)
- ✅ **续约失败 3 次触发让位**(默认配置):连续 3 次失败(3 × 10s = 30s)后 `is_leader=False` + 调 `on_lost`
- ✅ **`on_lost` 先于任何新 reconcile**:`LeaderGate.require_leader()` 拒绝已排队但未开始的业务任务
- ✅ **`stop()` best-effort release**:吸收 API 异常 + 记录日志(不抛出)

**测试文件**:
- `tests/unit/leader_election/test_election.py`(UT-LE-07~10)
  - UT-LE-07:`start()` 重复调用不创建第二个 task
  - UT-LE-08:连续 3 次 renew 失败 → `is_leader=False` + 调 `on_lost`
  - UT-LE-09:`stop()` 当前 leader → best-effort release + 异常被吸收
  - UT-LE-10:`LeaderGate.require_leader()` 非 leader 抛 `StandbyError`
- `tests/integration/leader_election/test_election_e2e.py`(IT-LE-02)
  - IT-LE-02:envtest + 3 个 Election 实例同时启动 → 仅 1 个 is_leader=true(其他进入 standby)

### 5.3 Lease wire contract(继承 L2-2 Spec §5.2)

```yaml
apiVersion: coordination.k8s.io/v1
kind: Lease
metadata:
  name: superteam-a2a-operator-leader  # 固定名称(v0.1 兼容性约束)
  namespace: superteam-a2a-system       # 固定 namespace(v0.1 兼容性约束)
spec:
  holderIdentity: <pod-name>-<uuid>     # 在进程生命周期内稳定
  acquireTime: <RFC3339 UTC>             # 必须 UTC RFC 3339
  renewTime: <RFC3339 UTC>               # 必须 UTC RFC 3339
  leaseDurationSeconds: 30               # 固定值
  leaderTransitions: <non-negative int>  # 切换次数(Prometheus 指标 superteam_operator_leader_election_state)
```

**v0.1 兼容性约束**(永久不变):
- Lease 名称 + namespace + leaseDurationSeconds(继承 L2-2 Spec §5.2)
- 30s TTL + 10s renew interval + 3 次失败阈值(均与 Go baseline 一致)

### 5.4 LeaderGate 与 Controller 集成

```python
# packages/operator/src/superteam_a2a/operator/controllers/agent.py
# (示意;完整在 §3.1)
@kopf.on.create('agent.superteam-a2a.io', id='agent-create')
async def agent_create(spec: AgentSpec, name: str, namespace: str, body: Agent, **kwargs):
    controller = AgentController.get_instance()
    try:
        controller._election.require_leader()  # ← LeaderGate 前置检查
        # ... reconcile 业务逻辑
    except StandbyError:
        raise kopf.TemporaryError("standby; not leader", delay=10)
```

**admission webhook 不走 LeaderGate**(L2-2 Spec §5.4):3 replicas 中仅 leader 拒收 admission 会违反 SLO;admission 必须在所有副本可用。

### 5.5 关键不变量与测试 ID 矩阵(10 项 + 2 IT)

| 测试 ID | 维度 | 描述 | 文件 |
|---|---|---|---|
| **UT-LE-01** | A 功能 | 子包 `__init__.py` 导出 4 个公开符号 | `tests/unit/leader_election/test_leader_election___init__.py` |
| **UT-LE-02** | A 功能 | `try_acquire` Lease 不存在(404)→ 自动 create + return True | `tests/unit/leader_election/test_lease_client.py` |
| **UT-LE-03** | A 功能 | `try_acquire` holder=其他 + 未过期 → return False | 同上 |
| **UT-LE-04** | A 功能 | `try_acquire` create 遇到 409 → return False(不覆盖) | 同上 |
| **UT-LE-05** | A 功能 | `renew` holder 被抢占 → return False | 同上 |
| **UT-LE-06** | A 功能 | `release` 时 holder=其他 → no-op | 同上 |
| **UT-LE-07** | A 功能 | `start()` 重复调用不创建第二个 task | `tests/unit/leader_election/test_election.py` |
| **UT-LE-08** | A 功能 | 连续 3 次 renew 失败 → `is_leader=False` + 调 `on_lost` | 同上 |
| **UT-LE-09** | A 功能 | `stop()` 当前 leader → best-effort release + 异常被吸收 | 同上 |
| **UT-LE-10** | C 接口契约 | `LeaderGate.require_leader()` 非 leader 抛 `StandbyError` | 同上 |
| **IT-LE-01** | A 功能 | envtest + CoordinationV1Api 真集群全流程 | `tests/integration/leader_election/test_lease_client_k8s.py` |
| **IT-LE-02** | A 功能 | envtest:3 个 Election 同时启动 → 仅 1 个 leader | `tests/integration/leader_election/test_election_e2e.py` |

**测试 ID 分布**:10 UT + 2 IT = 12 ID(覆盖 §A-§G 5 维度:功能 9 / 接口契约 1 / 其他 2)

**与 Go baseline 对应**:L2-2 Go baseline §7.3 Leader Election + ADR-0003 §6.5;wire contract(Lease 名称 + 30s leaseDurationSeconds)与 v0.1 业务语义**完全继续有效**

---

## 6. Memory 接口实现文件级 Spec（models/memory/ 8 文件 · MemoryReconciler 完整契约）

> **本节把 L2-2 Spec v0.2.0 §3 + L2-4 Spec v0.2.0 §3 + L2-2 Design §4.4 + §6.5 的 Memory 选型落到 9 个 Python 文件(`models/memory/` 8 + `reconcilers/memory_reconciler.py` 1)的精确契约**。
>
> **双向同步声明**:L3-1 的 `models/memory/*.py` 与 L2-4 Spec v0.2.0 §3 的 Pydantic schema **字段逐一对应**(wire contract);业务语义(decay/reinforce/GC/promotion 算法)由 L2-4 负责;Operator 仅做 reconcile 驱动(ADR-0003 §6)。

### 6.1 部署动机与边界(继承 L2-2 Design §4.4 + L2-4 Spec §7)

**MemoryReconciler 不是 Controller**(继承 L2-2 Design §4.4):
- ✅ **定时后台任务**:`@kopf.timer(interval=60.0)` 每 60s 触发(默认 Helm values 可配)
- ✅ **Leader Election 单 leader 触发**:`Election.is_leader()` 判断,非 leader 立即退出
- ✅ **批量 reconcile**:每 60s 全量列出所有 namespace 的 Memory CR;batch decay 用 `anyio.to_thread.run_sync` offload CPU 密集操作
- ✅ **业务语义解耦**:decay/reinforce/GC/promotion 由 `models/memory/decay.py` 等纯函数负责(无 K8s 依赖,可单测)

### 6.2 文件清单与契约(9 文件 · 全部在 `packages/operator/src/superteam_a2a/operator/`)

#### 6.2.1 `models/memory/__init__.py` —— Memory CRD 顶层 + 12 enum

```python
# packages/operator/src/superteam_a2a/operator/models/memory/__init__.py
from .spec import MemorySpec, AgentReference
from .status import MemoryStatus
from .conditions import MemoryConditionType, MemoryCondition
from .enums import MemoryPhase, MemoryVisibility
from .decay import compute_effective_confidence
from .reinforce import apply_reinforce
from .gc import should_garbage_collect
from .promotion import is_eligible_for_promotion

__all__ = [
    "MemorySpec", "AgentReference", "MemoryStatus",
    "MemoryConditionType", "MemoryCondition",
    "MemoryPhase", "MemoryVisibility",
    "compute_effective_confidence", "apply_reinforce",
    "should_garbage_collect", "is_eligible_for_promotion",
]
```

| 字段 | 值 |
|---|---|
| **职责** | Memory CRD 完整 Pydantic 模型 + 4 纯函数公开 |
| **exported 符号** | 4 CRD 类(MemorySpec/Status/Condition/AgentReference) + 4 enum + 4 纯函数 |
| **wire 对应** | 与 L2-4 Spec §3.4 Memory 完整 Pydantic schema **字段逐一对应** |
| **测试文件** | `tests/unit/models/memory/test_memory___init__.py`(UT-MD-01~03) |

#### 6.2.2 `models/memory/spec.py` —— MemorySpec + AgentReference

```python
# packages/operator/src/superteam_a2a/operator/models/memory/spec.py
from datetime import datetime
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from superteam_a2a.operator.models.shared import ScopeReference
from .enums import MemoryVisibility


class AgentReference(BaseModel):
    """Agent(ServiceAccount)引用"""
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: str = Field(default="ServiceAccount", description="固定为 ServiceAccount")
    name: str = Field(..., min_length=1, max_length=253)


class MemorySpec(BaseModel):
    """Memory CRD spec(12 字段 · 与 L2-4 Spec §3.4 MemorySpec 完全一致)"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scope_ref: ScopeReference = Field(..., alias="scopeRef")
    agent_ref: AgentReference = Field(..., alias="agentRef",
        description="必须 ServiceAccount;与 KI.User/Group 互斥(L2-4 Spec §3.4)")
    content: dict[str, str] = Field(..., min_length=1, max_length=20)
    summary: str = Field(..., min_length=1, max_length=512)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    decay_days: int = Field(default=30, ge=1, le=3650)
    reinforced_count: int = Field(default=0, ge=0, alias="reinforcedCount")
    last_reinforced_at: AwareDatetime | None = Field(default=None, alias="lastReinforcedAt")
    memory_key_pattern: str | None = Field(default=None, alias="memoryKeyPattern", max_length=128)
    source_knowledge_ref: dict | None = Field(default=None, alias="sourceKnowledgeRef",
        description="追溯的 KnowledgeItem(dict 形式,避免循环 import L2-4)")
    tags: list[str] | None = Field(default=None, max_length=10)
    visibility: MemoryVisibility = Field(default=MemoryVisibility.SCOPE_AND_CHILDREN)
```

**wire 对应**(L2-4 Spec §3.4 字段约束对照):
- ✅ `scope_ref` / `agent_ref` / `content` / `summary` / `confidence` / `decay_days` / `reinforced_count` / `last_reinforced_at` / `memory_key_pattern` / `source_knowledge_ref` / `tags` / `visibility` 字段名 + 类型 + 约束**完全一致**
- ✅ `extra="forbid"` + `populate_by_name=True` 行为一致

**测试 ID**:`UT-MD-ME-01`

#### 6.2.3 `models/memory/status.py` —— MemoryStatus

```python
# packages/operator/src/superteam_a2a/operator/models/memory/status.py
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from .conditions import MemoryCondition
from .enums import MemoryPhase


class MemoryStatus(BaseModel):
    """Memory CRD status(7 字段 · 与 L2-4 Spec §3.4 MemoryStatus 一致)"""
    model_config = ConfigDict(extra="forbid")

    phase: MemoryPhase | None = None
    message: str | None = Field(default=None, max_length=512)
    conditions: list[MemoryCondition] = Field(default_factory=list)
    last_decayed_at: AwareDatetime | None = Field(default=None, alias="lastDecayedAt")
    last_reinforced_at: AwareDatetime | None = Field(default=None, alias="lastReinforcedAt")
    effective_confidence: float | None = Field(default=None, alias="effectiveConfidence", ge=0.0, le=1.0)
    eligible_for_promotion: bool | None = Field(default=None, alias="eligibleForPromotion")
    observed_generation: int | None = Field(default=None, alias="observedGeneration", ge=0)
```

**wire 对应**:与 L2-4 Spec §3.4 MemoryStatus **字段逐一对应**

**测试 ID**:`UT-MD-ME-02`

#### 6.2.4 `models/memory/conditions.py` —— MemoryConditionType + MemoryCondition

```python
# packages/operator/src/superteam_a2a/operator/models/memory/conditions.py
from datetime import datetime
from enum import StrEnum
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class MemoryConditionType(StrEnum):
    """Memory status.conditions[].type 枚举(继承 L2-4 Spec §7)"""
    DECAYED = "Decayed"
    REINFORCED = "Reinforced"
    PROMOTED = "Promoted"
    ARCHIVED = "Archived"
    GARBAGE_COLLECTED = "GarbageCollected"


class MemoryCondition(BaseModel):
    """K8s-style condition(L2-4 Spec §3.4 + K8s conventions)"""
    model_config = ConfigDict(extra="forbid")
    type: MemoryConditionType
    status: str = Field(..., pattern="^(True|False|Unknown)$")
    reason: str | None = Field(default=None, max_length=128)
    message: str | None = Field(default=None, max_length=512)
    last_transition_time: AwareDatetime = Field(..., alias="lastTransitionTime")
```

**wire 对应**:condition type 5 类(Decayed/Reinforced/Promoted/Archived/GarbageCollected)与 L2-4 Spec §7 一致

**测试 ID**:`UT-MD-ME-03`

#### 6.2.5 `models/memory/enums.py` —— MemoryPhase + MemoryVisibility

```python
# packages/operator/src/superteam_a2a/operator/models/memory/enums.py
from enum import StrEnum


class MemoryPhase(StrEnum):
    """Memory status.phase 状态机(5 态 · 与 L2-4 Spec §3.4 一致)"""
    ACTIVE = "Active"                # effective_confidence > 0.5
    DECAYING = "Decaying"            # 0.01 ≤ effective_confidence ≤ 0.5
    PROMOTABLE = "Promotable"        # eligible_for_promotion = true(v0.1 仅算不触发)
    EXPIRED = "Expired"              # effective_confidence < 0.01
    ERROR = "Error"                  # reconcile 失败


class MemoryVisibility(StrEnum):
    """Memory visibility 3 类(5 维矩阵 · agent-private 短路)"""
    SCOPE_ONLY = "scope-only"
    SCOPE_AND_CHILDREN = "scope-and-children"
    AGENT_PRIVATE = "agent-private"
```

**wire 对应**:enum 值与 L2-4 Spec §3.4 **字符串值完全一致**

**测试 ID**:`UT-MD-ME-04`

#### 6.2.6 `models/memory/decay.py` —— 衰减算法纯函数

```python
# packages/operator/src/superteam_a2a/operator/models/memory/decay.py
import math


def compute_effective_confidence(
    confidence: float,
    decay_days: float,
    elapsed_days: float,
) -> float:
    """Memory 衰减公式(ADR-0003 §4.1 · 数学公式 wire 不变)

    effective_confidence = confidence × exp(-elapsed_days / decay_days)

    Args:
        confidence: 初始置信度 [0, 1]
        decay_days: 半衰期(衰减时间常数)≥ 1
        elapsed_days: 已过去天数(自 last_reinforced_at 或 createdAt)

    Returns:
        衰减后置信度 ∈ [0, 1]
    """
    if decay_days <= 0:
        raise ValueError(f"decay_days must be > 0, got {decay_days}")
    return confidence * math.exp(-elapsed_days / decay_days)
```

**关键不变量**:
- ✅ **数学公式与 L2-4 Spec §7 完全一致**(`confidence × exp(-elapsed_days / decay_days)`,ADR-0003 §4.1 wire 不变)
- ✅ **纯函数**:无 I/O / 无副作用;输入相同则输出相同
- ✅ **边界保护**:`decay_days ≤ 0` 抛 ValueError

**测试 ID**:`UT-MD-ME-05`
- UT-MD-ME-05a:confidence=1.0 + decay_days=30 + elapsed_days=0 → 1.0
- UT-MD-ME-05b:confidence=1.0 + decay_days=30 + elapsed_days=30 → ≈ 0.368(e^-1)
- UT-MD-ME-05c:decay_days=0 → ValueError

#### 6.2.7 `models/memory/reinforce.py` —— 强化算法纯函数

```python
# packages/operator/src/superteam_a2a/operator/models/memory/reinforce.py


def apply_reinforce(
    confidence: float,
    amount: float = 0.05,
    cap: float = 0.95,
) -> float:
    """Memory 强化算法(每次强化 += amount,封顶 cap)

    继承 ADR-0003 §4.2 + L2-4 Spec §7

    Args:
        confidence: 当前置信度 [0, 1]
        amount: 单次强化增量(默认 0.05)
        cap: 强化上限(默认 0.95;超过 1.0 不允许)

    Returns:
        强化后置信度 ∈ [amount, cap]
    """
    return min(confidence + amount, cap)
```

**关键不变量**:
- ✅ **公式与 L2-4 Spec §7 完全一致**(`min(confidence + 0.05, 0.95)`)
- ✅ **封顶 cap=0.95**(避免长期强化到 1.0 后失去 decay 意义;ADR-0003 §4.2)

**测试 ID**:`UT-MD-ME-06`

#### 6.2.8 `models/memory/gc.py` —— GC 算法纯函数

```python
# packages/operator/src/superteam_a2a/operator/models/memory/gc.py


def should_garbage_collect(
    effective_confidence: float,
    threshold: float = 0.1,
) -> bool:
    """Memory GC 判断(effective_confidence < threshold → 待 GC)

    继承 ADR-0003 §4.3 + L2-4 Spec §7

    Args:
        effective_confidence: 当前 effective_confidence [0, 1]
        threshold: GC 阈值(默认 0.1)

    Returns:
        True 表示待 GC(进入 EXPIRED phase)
    """
    return effective_confidence < threshold
```

**关键不变量**:
- ✅ **阈值 threshold=0.1**(与 L2-4 Spec §7 一致)
- ✅ **纯函数**:无副作用

**测试 ID**:`UT-MD-ME-07`

#### 6.2.9 `models/memory/promotion.py` —— 提升资格纯函数

```python
# packages/operator/src/superteam_a2a/operator/models/memory/promotion.py


def is_eligible_for_promotion(
    effective_confidence: float,
    reinforced_count: int,
    min_confidence: float = 0.9,
    min_reinforced: int = 10,
) -> bool:
    """Memory 提升到 KnowledgeItem 资格判断

    继承 ADR-0003 §4.4 + L2-4 Spec §7(v0.1 仅计算,不触发提升)

    Args:
        effective_confidence: 当前 effective_confidence [0, 1]
        reinforced_count: 强化次数
        min_confidence: 最低置信度(默认 0.9)
        min_reinforced: 最低强化次数(默认 10)

    Returns:
        True 表示有资格提升(v0.1 仅设置 status.eligible_for_promotion = True)
    """
    return effective_confidence >= min_confidence and reinforced_count >= min_reinforced
```

**关键不变量**:
- ✅ **公式与 L2-4 Spec §7 完全一致**(`effective_confidence >= 0.9 AND reinforced_count >= 10`)
- ✅ **v0.1 仅计算**:设置 `eligible_for_promotion=true`,**不**触发实际提升(避免破坏 v0.1 scope)

**测试 ID**:`UT-MD-ME-08`

#### 6.2.10 `reconcilers/memory_reconciler.py` —— MemoryReconcilerService 完整契约

```python
# packages/operator/src/superteam_a2a/operator/reconcilers/memory_reconciler.py
import kopf
from anyio import to_thread

from superteam_a2a.operator.leader_election import Election, StandbyError
from superteam_a2a.operator.models.memory import (
    Memory, MemorySpec, MemoryStatus, MemoryPhase,
    compute_effective_confidence, should_garbage_collect,
    is_eligible_for_promotion,
)
from superteam_a2a.operator.clients import AsyncK8sClient
from superteam_a2a.operator.observability.metrics import OperatorMetrics


class MemoryReconcilerService:
    """MemoryReconciler 业务逻辑服务(与 Kopf 解耦 · 可独立单测)

    关键不变量(继承 L2-2 Design §4.4):
    - 单 leader 触发(避免重复 reconcile 导致状态竞争)
    - 每 60s 全量 reconcile(增量优化留 v0.5+)
    - decay 公式与 L2-4 完全一致(数学公式 wire 不变)
    - batch reconcile CPU offload(anyio.to_thread.run_sync)
    """

    def __init__(
        self,
        k8s_client: AsyncK8sClient,
        election: Election,
        metrics: OperatorMetrics,
        reconcile_interval_seconds: int = 60,
    ) -> None:
        self._k8s = k8s_client
        self._election = election
        self._metrics = metrics
        self._interval = reconcile_interval_seconds

    async def reconcile_all_memories(self, **kwargs) -> None:
        """@kopf.timer 每 60s 触发(仅 leader)"""
        try:
            self._election.require_leader()
        except StandbyError:
            return  # 非 leader 立即退出,不参与 reconcile
        # 1. 列出所有 namespace 的 Memory CR
        memories = await self._k8s.list_memories(namespace='*')
        # 2. CPU offload:batch decay 用 anyio.to_thread.run_sync
        async def _batch_decay() -> list[tuple[Memory, float]]:
            results = []
            for memory in memories:
                effective = compute_effective_confidence(
                    confidence=memory.spec.confidence,
                    decay_days=memory.spec.decay_days or 30.0,
                    elapsed_days=self._compute_elapsed_days(memory),
                )
                results.append((memory, effective))
            return results
        results = await to_thread.run_sync(_batch_decay)
        # 3. 应用 decay + GC + promotion + status patch
        for memory, effective_confidence in results:
            try:
                new_status = memory.status.copy() if memory.status else MemoryStatus()
                new_status.effective_confidence = effective_confidence
                new_status.last_decayed_at = datetime.now(timezone.utc)
                # GC 判断
                if should_garbage_collect(effective_confidence):
                    new_status.phase = MemoryPhase.EXPIRED
                    new_status.conditions.append(MemoryCondition(
                        type=MemoryConditionType.GARBAGE_COLLECTED,
                        status="True",
                        reason="effective_confidence < 0.1",
                        last_transition_time=datetime.now(timezone.utc),
                    ))
                # Promotion 判断(v0.1 仅算不触发)
                elif is_eligible_for_promotion(effective_confidence, memory.spec.reinforced_count):
                    new_status.eligible_for_promotion = True
                    new_status.phase = MemoryPhase.PROMOTABLE
                await self._k8s.update_memory_status(
                    name=memory.metadata.name,
                    namespace=memory.metadata.namespace,
                    status=new_status,
                )
                self._metrics.inc_memory_decay_total(
                    namespace=memory.metadata.namespace, result="success",
                )
            except Exception as e:
                self._metrics.inc_memory_decay_total(
                    namespace=memory.metadata.namespace, result="error",
                )
                get_logger().error(
                    "memory_reconcile_failed",
                    memory_name=memory.metadata.name,
                    namespace=memory.metadata.namespace,
                    error=str(e),
                )

    def _compute_elapsed_days(self, memory: Memory) -> float:
        """计算已过去天数(自 last_reinforced_at 或 created_at)"""
        last_ref = memory.status.last_reinforced_at if memory.status else None
        last_ref = last_ref or memory.spec.last_reinforced_at
        if last_ref is None:
            last_ref = memory.metadata.creation_timestamp
        elapsed = datetime.now(timezone.utc) - last_ref
        return max(elapsed.total_seconds() / 86400.0, 0.0)
```

**关键设计**(继承 L2-2 Spec §3 + L2-4 Spec §7 + L2-2 Design §4.4):
- ✅ **CPU offload**:batch decay 在 `anyio.to_thread.run_sync` 中执行(避免阻塞 event loop,ADR-0005 §6.3)
- ✅ **Status patch 通过 `kopf.adopt + status_patch`**:无直接 `kubectl patch`
- ✅ **错误隔离**:单个 Memory 失败不影响其他 Memory reconcile(try/except 包围每个循环)
- ✅ **Prometheus 指标**:`superteam_memory_decay_total{namespace,result}`(L2-4 Spec §10 共享)

**测试文件**:
- `tests/unit/reconcilers/test_memory_reconciler.py`(UT-R-23~25)
  - UT-R-23:`reconcile_all_memories` 非 leader → 立即返回
  - UT-R-24:`should_garbage_collect` 触发 → status.phase = EXPIRED
  - UT-R-25:`is_eligible_for_promotion` 触发 → status.eligible_for_promotion = True
- `tests/integration/reconcilers/test_memory_reconciler_e2e.py`(IT-R-04)
  - IT-R-04:envtest + 3 Memory CR(effective_confidence 0.9/0.05/0.95) → reconcile 后 phase 分别为 PROMOTABLE / EXPIRED / Active

### 6.3 wire sync matrix(L3-1 `models/memory/` ↔ L2-4 Spec §3.4)

| 字段 | L2-4 Spec §3.4 wire | L3-1 `models/memory/spec.py` | L3-1 `models/memory/status.py` | 一致性 |
|---|---|---|---|---|
| `scope_ref` | MemorySpec(ScopeReference) | ✅ | n/a | ✅ |
| `agent_ref` | MemorySpec(AgentReference) | ✅ | n/a | ✅ |
| `content` | MemorySpec(dict, 1-20) | ✅ | n/a | ✅ |
| `summary` | MemorySpec(str, 1-512) | ✅ | n/a | ✅ |
| `confidence` | MemorySpec(float, 0-1) | ✅ | n/a | ✅ |
| `decay_days` | MemorySpec(int, 1-3650) | ✅ | n/a | ✅ |
| `reinforced_count` | MemorySpec(int, ≥0) | ✅ | n/a | ✅ |
| `last_reinforced_at` | MemorySpec(AwareDatetime) | ✅ | MemoryStatus(last_reinforced_at) | ✅ |
| `memory_key_pattern` | MemorySpec(str, ≤128) | ✅ | n/a | ✅ |
| `source_knowledge_ref` | MemorySpec(ItemReference) | ✅(dict 形式避免循环 import) | n/a | ✅(类型 wire 等价) |
| `tags` | MemorySpec(list, ≤10) | ✅ | n/a | ✅ |
| `visibility` | MemorySpec(MemoryVisibility) | ✅ | n/a | ✅ |
| `phase` | MemoryStatus(MemoryPhase) | n/a | ✅ | ✅ |
| `message` | MemoryStatus(str, ≤512) | n/a | ✅ | ✅ |
| `conditions` | MemoryStatus(list[Condition]) | n/a | ✅ | ✅ |
| `last_decayed_at` | MemoryStatus(AwareDatetime) | n/a | ✅ | ✅ |
| `effective_confidence` | MemoryStatus(float, 0-1) | n/a | ✅ | ✅ |
| `eligible_for_promotion` | MemoryStatus(bool) | n/a | ✅ | ✅ |
| `observed_generation` | MemoryStatus(int, ≥0) | n/a | ✅ | ✅ |

**字段数约束**:12 spec 字段 + 7 status 字段 + 4 enum = **23 字段**,与 L2-4 Spec §3.6 距上限 3(临界)状态**完全一致**。

### 6.4 关键不变量(继承 L2-2 Spec §3 + L2-4 Spec §7)

- ✅ **数学公式 wire 不变**:decay 公式 `confidence × exp(-elapsed_days / decay_days)`(L3-1 §6.2.6 ↔ L2-4 Spec §7)
- ✅ **状态机 5 态一致**:Active / Decaying / Promotable / Expired / Error(L3-1 §6.2.5 ↔ L2-4 Spec §3.4)
- ✅ **强化封顶 cap=0.95**:避免长期强化到 1.0 后失去 decay 意义(ADR-0003 §4.2)
- ✅ **v0.1 仅计算不触发提升**:`is_eligible_for_promotion` 仅设置 `status.eligible_for_promotion=true`,**不**触发实际 KnowledgeItem 创建
- ✅ **Leader Election 单 leader 触发**:`Election.require_leader()` 前置检查
- ✅ **batch reconcile CPU offload**:`anyio.to_thread.run_sync` 包装 batch decay 计算

### 6.5 测试 ID 矩阵(8 UT-MD-ME + 3 UT-R · §A-§G 5 维度全 PASS)

| 测试 ID | 维度 | 描述 | 文件 |
|---|---|---|---|
| **UT-MD-ME-01** | C 接口契约 | MemorySpec 字段约束(Pydantic min/max/enum) | `tests/unit/models/memory/test_memory_spec.py` |
| **UT-MD-ME-02** | C 接口契约 | MemoryStatus 字段约束 | `tests/unit/models/memory/test_memory_status.py` |
| **UT-MD-ME-03** | C 接口契约 | MemoryCondition 5 类型枚举 | `tests/unit/models/memory/test_memory_conditions.py` |
| **UT-MD-ME-04** | C 接口契约 | MemoryPhase 5 态 + MemoryVisibility 3 类 | `tests/unit/models/memory/test_memory_enums.py` |
| **UT-MD-ME-05** | A 功能 | `compute_effective_confidence` 数学公式正确(边界 + e^-1 验证) | `tests/unit/models/memory/test_memory_decay.py` |
| **UT-MD-ME-06** | A 功能 | `apply_reinforce` 封顶 cap=0.95 + 增量 amount=0.05 | `tests/unit/models/memory/test_memory_reinforce.py` |
| **UT-MD-ME-07** | A 功能 | `should_garbage_collect` threshold=0.1 | `tests/unit/models/memory/test_memory_gc.py` |
| **UT-MD-ME-08** | A 功能 | `is_eligible_for_promotion` min_confidence=0.9 + min_reinforced=10 | `tests/unit/models/memory/test_memory_promotion.py` |
| **UT-R-23** | A 功能 | `reconcile_all_memories` 非 leader 立即返回 | `tests/unit/reconcilers/test_memory_reconciler.py` |
| **UT-R-24** | A 功能 | GC 触发 → status.phase = EXPIRED + GARBAGE_COLLECTED condition | 同上 |
| **UT-R-25** | A 功能 | Promotion 触发 → status.eligible_for_promotion = True + PROMOTABLE phase | 同上 |
| **IT-R-04** | A 功能 | envtest:3 Memory CR(effective_confidence 0.9/0.05/0.95)reconcile 后 phase 正确 | `tests/integration/reconcilers/test_memory_reconciler_e2e.py` |

**测试 ID 分布**:8 UT-MD-ME + 3 UT-R + 1 IT-R = 12 ID(覆盖 §A-§G 5 维度:功能 10 / 接口契约 2)

**与 L2-4 Spec 对应**:wire 完全一致(§6.3 矩阵 19 字段全 PASS);业务语义(4 纯函数)数学公式**逐字符一致**

---

## 7. observability + RBAC + Helm values 文件级 Spec（落地到 K8s 部署资产）

> 本节将 L2-2 Spec §10 可观测性 + §9 Helm values + §11 RBAC 落地为 Python 文件级 Spec 与 Helm 模板完整契约。所有指标名 / Event reason / RBAC apiGroup / Helm 字段名 / ServiceAccount annotation 均属于 v0.1 wire/deployment contract;新增/修改必须走 ADR。
>
> **范围**:observability 子包 6 文件(4 核心 + logging + __init__) + Helm 9 模板 + RBAC 2 子模板 = **17 文件**新增到 §1.3 文件清单;落地后 L3-1 文件清单 **70 → 87**。
>
> **测试 ID 总额**:L3-1 累计 §0-§6 = 142 ID,**§7 新增 76 ID**(OBS 25 + HLT 8 + HELM 29 + RBAC 14),L3-1 §7 落地后累计 **218 ID**(仍然在 L2-2 Spec §13 ID 矩阵范围内;HELM/RBAC 完整继承 L2-2 高优先级 ID)。

### 7.1 observability 子包文件级 Spec（6 文件 · 11 Operator 指标 + 4 Python runtime 指标 + 双端点探针）

#### 7.1.1 子包文件清单

| 文件 | 必须提供 | L2-2 Spec 对应章节 | 关联测试 ID 前缀 |
|------|----------|---------------------|------------------|
| `observability/__init__.py` | 导出 MetricsRegistry / configure_tracing / configure_logging / emit_event / EventReason + health 子模块导出 | 子包入口 | — |
| `observability/metrics.py` | MetricsRegistry + 11 Operator + 4 Python runtime 指标 + register_or_get 幂等 | §10.1 + §10.2 + §10.3 | OBS-001~OBS-012 |
| `observability/health.py` | HealthCheck + liveness / readiness ASGI app + 双端口路由 + K8s Lease + MemoryReconciler last_run check(**新增文件级契约**,L2-2 §13.5 探针字段升级) | §13.5 | HLT-001~HLT-008 |
| `observability/tracing.py` | configure_tracing + RuntimeMonitor + OTLP async exporter + InMemorySpanExporter 测试钩子 | §10.4 | OBS-016~OBS-019 |
| `observability/logging.py` | configure_logging + structlog 8 字段契约 + BoundLogger 工厂 | §10.5 | OBS-010 / OBS-024 |
| `observability/events.py` | EventReason 8 种 + emit_event + 限长 1024 + 白名单校验 | §10.6 | OBS-007 / OBS-022 / OBS-025 |
| `tests/unit/observability/test_metrics.py` | pytest fixtures + register_or_get 幂等 + 11+4 指标存在性 | — | OBS-001~OBS-013 |
| `tests/unit/observability/test_health.py` | `/healthz` 与 `/readyz` 行为矩阵 | — | HLT-001~HLT-008 |
| `tests/unit/observability/test_tracing.py` | InMemorySpanExporter 替换 + W3C traceparent 注入 + RuntimeMonitor | — | OBS-016~OBS-019 |
| `tests/unit/observability/test_logging.py` | structlog 8 字段样本 + BoundLogger 工厂 | — | OBS-010 / OBS-024 |
| `tests/unit/observability/test_events.py` | EventReason 白名单 + message 限长 + K8s API 调用 mock | — | OBS-007 / OBS-022 / OBS-025 |

#### 7.1.2 metrics.py 完整契约

```python
# packages/operator/src/superteam_a2a/operator/observability/metrics.py
from __future__ import annotations

from threading import Lock
from typing import Any

from prometheus_client import Counter, Gauge, Histogram
from prometheus_client.metrics import MetricWrapperBase


class MetricsRegistry:
    """11 Operator 指标 + 4 Python runtime 指标注册表。

    线程安全:同进程内 register_or_get 在 Lock 保护下幂等;不同实例(多进程)
    共享同一 default REGISTRY 时由 prometheus_client 内部去重处理。
    """

    def __init__(self, prefix: str = "superteam_") -> None:
        self._prefix = prefix
        self._lock = Lock()
        self._items: dict[str, MetricWrapperBase] = {}

    def register_or_get(
        self, name: str, type_: type, labels: list[str] | None = None
    ) -> Counter | Gauge | Histogram:
        """注册或获取 Prometheus 指标;同进程重复注册同名返回已有对象。

        Raises:
            ValueError: name 无前缀或 type_ 不在 (Counter, Gauge, Histogram) 中。
        """
        ...

    def as_dict(self) -> dict[str, object]:
        """导出当前所有指标 → Prometheus text format 序列化中间结构。

        Returns:
            dict,key 是 metric 完整名(supertem_operator_*)。
        """
        ...

    # 11 Operator 指标(继承 L2-2 Spec §10.2 完全一致)
    @property
    def reconcile_total(self) -> Counter: ...  # labels: crd, result
    @property
    def reconcile_duration_seconds(self) -> Histogram: ...  # labels: crd
    @property
    def leader_election(self) -> Gauge: ...
    @property
    def finalizer_cleanup_total(self) -> Counter: ...  # labels: crd, result
    @property
    def finalizer_cleanup_duration_seconds(self) -> Histogram: ...  # labels: crd
    @property
    def admission_validation_total(self) -> Counter: ...  # labels: crd, result
    @property
    def admission_validation_duration_seconds(self) -> Histogram: ...  # labels: crd
    @property
    def memory_reconcile_total(self) -> Counter: ...  # labels: result
    @property
    def memory_decay_total(self) -> Counter: ...  # labels: phase_from, phase_to
    @property
    def lease_renew_total(self) -> Counter: ...  # labels: result
    @property
    def lease_transition_total(self) -> Counter: ...  # labels: event

    # 4 Python runtime 指标(继承 L2-2 Spec §10.3 完全一致)
    @property
    def python_event_loop_lag_seconds(self) -> Histogram: ...
    @property
    def python_thread_offload_queue_depth(self) -> Gauge: ...
    @property
    def python_active_asyncio_tasks(self) -> Gauge: ...
    @property
    def python_gc_collections_total(self) -> Counter: ...  # labels: generation
```

**约束**:
- `result` label 仅接受 `success` / `error` / `retry` / `rejected`;
- `phase_from` / `phase_to` 来自 AgentPhase / MemoryPhase enum 字符串;
- `event` label 在 lease_transition_total 仅接受 `acquired` / `lost` / `renew_failed`;
- `generation` label 在 python_gc_collections_total 接受 Python `gc.get_stats()[i].generation`(整数 0/1/2 序列化字符串);
- Histogram 默认桶 `prometheus_client.DEFAULT_BUCKETS`;自定义桶必须显式声明区间列表;
- 测试场景 `MetricsRegistry(prefix="test_")` 用于隔离,不污染默认 REGISTRY。

#### 7.1.3 health.py ASGI app + 双端点契约(新增文件级契约 · 与 L2-2 §13.5 探针对齐)

```python
# packages/operator/src/superteam_a2a/operator/observability/health.py
from __future__ import annotations

from collections.abc import Awaitable
from datetime import datetime
from typing import Any, Protocol


class LeaseChecker(Protocol):
    """Liveness/Readiness 检查所需的最小 K8s Lease API(duck typing)。"""

    async def is_lease_active(self, holder_id: str) -> bool: ...
    async def last_heartbeat(self, holder_id: str) -> datetime: ...


class ReconcilerPulse(Protocol):
    """MemoryReconciler 周期触发心跳探测(duck typing)。"""

    def last_run_at(self) -> datetime: ...


class HealthCheck:
    """/healthz 与 /readyz 路由聚合器。

    启动时返回 503 直到 all_check_ready() 通过;之后按 readiness 变化实时更新。
    """

    def __init__(
        self,
        lease: LeaseChecker,
        reconciler: ReconcilerPulse,
        lease_holder_id: str,
        max_heartbeat_lag_seconds: int = 90,
    ) -> None: ...

    async def liveness(self) -> tuple[int, dict[str, object]]:
        """Liveness:仅检查进程存活。返回 (200, {"status": "alive"})。"""
        ...

    async def readiness(self) -> tuple[int, dict[str, object]]:
        """Readiness:Lease active + MemoryReconciler 最近心跳 + admission webhook TLS 已加载 +
        ValidatingWebhookConfiguration 已注册。

        Returns:
            (200, {"lease": "active", "reconciler": "ok", "admission": "ready"})
            或 (503, {"reason": ..., "lease": "...", "reconciler": "...", "admission": "..."})。
        """
        ...

    def all_check_ready(self) -> bool:
        """首次检查入口;启动时调用以初始化 readiness 标志。"""
        ...


async def healthz_app(
    scope: dict[str, object],
    receive: Any,
    send: Any,
) -> None:
    """ASGI app 适配 uvicorn (端口 8080) /healthz 端点;满足 ASGI 3.0 callable。"""
    ...


async def readyz_app(
    scope: dict[str, object],
    receive: Any,
    send: Any,
) -> None:
    """ASGI app 适配 uvicorn (端口 8080) /readyz 端点;满足 ASGI 3.0 callable。"""
    ...
```

**关键行为**:
- `/healthz` 200 iff 进程响应(端口监听 + ASGI app 可调用);
- `/readyz` 200 iff Lease active + MemoryReconciler 最近心跳(`now - last_run < max_heartbeat_lag_seconds`,默认 90s)+ admission webhook TLS 已加载 + ValidatingWebhookConfiguration 已注册;
- Readiness 由 Leader Election 主备 + admission 注册状态共同决定;**非 leader 副本仍返回 200**(K8s service 端点保留);
- Helm `deployment.yaml` livenessProbe 命中 `/healthz`;readinessProbe 命中 `/readyz`(详见 §7.2.4 (2));
- LeaseChecker / ReconcilerPulse 是 Protocol(duck typing),不强制依赖 kubernetes_asyncio —— 测试可注入 FakeLeaseChecker / FakeReconcilerPulse 即可覆盖 8 ID(HLT-001~008)。

#### 7.1.4 tracing.py 完整契约

```python
# packages/operator/src/superteam_a2a/operator/observability/tracing.py
from __future__ import annotations

from typing import NoReturn

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from superteam_a2a.operator.config import HelmValues


def configure_tracing(
    values: HelmValues,
    *,
    service_name: str = "superteam-a2a-operator",
    in_memory_exporter: object | None = None,
) -> TracerProvider:
    """显式构造 TracerProvider 并注册到全局;测试必须传入 in-memory exporter 避免污染。

    Args:
        values: Helm values,包含 observability.otel_endpoint 等配置。
        service_name: OTel resource attribute,默认 'superteam-a2a-operator'。
        in_memory_exporter: 测试用 InMemorySpanExporter,生产环境为 None。

    Returns:
        构造好的 TracerProvider;已被 set_tracer_provider() 全局注册。
    """
    ...


def inject_traceparent(headers: dict[str, str]) -> dict[str, str]:
    """注入 W3C traceparent 到 K8s Events annotation / structlog JSON / admission audit log。

    Returns:
        新 dict,原 dict + 'traceparent' key;traceparent 格式符合 W3C Trace Context spec。
    """
    ...


class RuntimeMonitor:
    """每 30s 采样 4 个 Python runtime 指标 → MetricsRegistry。"""

    def __init__(self, registry: MetricsRegistry) -> None: ...
    async def run(self) -> NoReturn:
        """永久运行每 30s 采样;CancellationToken 安全(stop() 触发 task 取消)。"""
        ...
    async def stop(self) -> None:
        """停止 RuntimeMonitor;cancel 当前 task 等待 join。"""
        ...
```

**关键不变量**(继承 L2-2 §10.4):
- OTLP exporter 必须 async transport(`opentelemetry-exporter-otlp-proto-grpc` async transport);
- 测试场景使用独立 `InMemorySpanExporter`,**不得**污染生产 provider;
- W3C `traceparent` 必须注入到:K8s Events annotation `trace.superteam-a2a.io/parent`、structlog JSON 的 `trace_id` / `span_id` 字段、admission audit log 行;
- Span 失败/超时分支必须包含 `error.type` + `error.message` attribute,message 限长 1024 字符。

#### 7.1.5 events.py 完整契约

```python
# packages/operator/src/superteam_a2a/operator/observability/events.py
from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

from kubernetes_asyncio.client import CoreV1Api


class EventReason(StrEnum):
    """白名单 reason;自定义 reason 必须新增成员并加测试。

    字符串字面值与 L2-2 Spec §10.6 8 种 reason 完全一致(wire contract)。
    """

    RECONCILE_SUCCEEDED = "ReconcileSucceeded"
    RECONCILE_FAILED = "ReconcileFailed"
    RECONCILE_RETRY = "ReconcileRetry"
    CLEANUP_COMPLETED = "CleanupCompleted"
    CLEANUP_FAILED = "CleanupFailed"
    LEADER_ACQUIRED = "LeaderAcquired"
    LEADER_LOST = "LeaderLost"
    ADMISSION_REJECTED = "AdmissionRejected"


_MAX_MESSAGE_LENGTH = 1024


async def emit_event(
    core: CoreV1Api,
    body: Mapping[str, object],
    reason: EventReason,
    message: str,
    *,
    type_: str = "Normal",
) -> None:
    """emit_event 写入 K8s Event。

    Args:
        core: Kubernetes CoreV1Api(异步)。
        body: K8s Event template(namespace / involvedObject 等字段)。
        reason: EventReason 白名单成员。
        message: 事件 message 字符串;超过 1024 字符将被截断。
        type_: 'Normal' 或 'Warning';默认 'Normal'。

    Raises:
        ValueError: reason 不在白名单(type_ 静默接受,K8s API Server 校验)。
    """
    ...


def truncate_message(message: str, limit: int = _MAX_MESSAGE_LENGTH) -> str:
    """UTF-8 安全的字符级截断函数(不带省略号,超长直接截)。

    Args:
        message: 原始字符串。
        limit: 字符上限;默认 1024。

    Returns:
        截断后的字符串;不变 if len(message) <= limit。
    """
    ...
```

**8 种 EventReason 与触发时机**(继承 L2-2 §10.6 完整对应表):

| reason | type | 触发时机 | message 模板 |
|--------|------|----------|--------------|
| `ReconcileSucceeded` | Normal | reconcile 成功 | `Reconcile succeeded for {crd}/{namespace}/{name}` |
| `ReconcileFailed` | Warning | Permanent / NonRetryable 错误 | `Reconcile failed for {crd}/{namespace}/{name}: {reason}` |
| `ReconcileRetry` | Normal | Retryable 错误(含 retry_after) | `Reconcile retry after {retry_after}s for {crd}/{namespace}/{name}` |
| `CleanupCompleted` | Normal | Finalizer cleanup 成功 | `Cleanup completed for {crd}/{namespace}/{name}` |
| `CleanupFailed` | Warning | Finalizer cleanup 失败 | `Cleanup failed for {crd}/{namespace}/{name}: {reason}` |
| `LeaderAcquired` | Normal | Leader Election 获取成功 | `Operator {pod_name} acquired lease` |
| `LeaderLost` | Warning | Leader Election 失主 | `Operator {pod_name} lost lease` |
| `AdmissionRejected` | Warning | admission 拒绝请求 | `Admission rejected for {crd}/{namespace}/{name}: {reason}` |

**约束**:
- `type` 必须是 `Normal` 或 `Warning`;
- 自定义 reason 必须新增白名单 enum 成员并加测试,**禁止运行时拼字符串**;
- message 字符级截断(UTF-8 safe) → `_MAX_MESSAGE_LENGTH = 1024`;
- K8s Event annotation `trace.superteam-a2a.io/parent` 自动注入(从当前 span 取)。

#### 7.1.6 observability 测试 ID 矩阵(25 OBS + 8 HLT = 33 ID · §A-§G 6 维度)

| 测试 ID | 维度 | 描述 | 文件 |
|---------|------|------|------|
| **OBS-001** | C 接口契约 | 11 Operator 指标唯一存在 | `tests/unit/observability/test_metrics.py` |
| **OBS-002** | A 功能 | 11 指标 name 与 L2-2 §10.2 完全一致 | 同上 |
| **OBS-003** | A 功能 | 4 Python runtime 指标存在 | 同上 |
| **OBS-004** | C 接口契约 | `register_or_get` 同名指标幂等返回 | 同上 |
| **OBS-005** | B 质量 | Histogram bucket 配置可断言 | 同上 |
| **OBS-006** | C 接口契约 | `as_dict()` 输出 metric → serializable dict | 同上 |
| **OBS-007** | A 功能 | EventReason 白名单拒绝未列举字符串 | `tests/unit/observability/test_events.py` |
| **OBS-008** | B 质量 | emit_event 调用 CoreV1Api.create_namespaced_event | 同上 |
| **OBS-009** | C 接口契约 | EventReason 8 种字符串与 L2-2 §10.6 完全一致 | 同上 |
| **OBS-010** | A 功能 | structlog sample 含 8 个必含字段 | `tests/unit/observability/test_logging.py` |
| **OBS-011** | B 质量 | 4 Python runtime 指标在 RuntimeMonitor 30s 后第一次采样 | `tests/unit/observability/test_tracing.py` |
| **OBS-012** | C 接口契约 | MetricsRegistry 构造不依赖 K8s client | `tests/unit/observability/test_metrics.py` |
| **OBS-013** | B 质量 | Histogram bucket 配置可被测试验证 | 同上 |
| **OBS-016** | B 质量 | TracerProvider 在测试中替换为 InMemorySpanExporter | `tests/unit/observability/test_tracing.py` |
| **OBS-017** | C 接口契约 | RuntimeMonitor.stop() 不抛异常 | 同上 |
| **OBS-018** | A 功能 | inject_traceparent 输出符合 W3C Trace Context | 同上 |
| **OBS-019** | A 功能 | reconcile 失败 span 含 error.type + 限长 error.message | 同上 |
| **OBS-022** | B 质量 | Event message 限长 1024 字符并被截断 | `tests/unit/observability/test_events.py` |
| **OBS-024** | C 接口契约 | configure_logging 调用 structlog.configure 覆盖 8 字段处理器 | `tests/unit/observability/test_logging.py` |
| **OBS-025** | A 功能 | reason 不在白名单时 emit_event 抛 ValueError | `tests/unit/observability/test_events.py` |
| **HLT-001** | A 功能 | liveness 在 Lease 失主场景仍返回 200 | `tests/unit/observability/test_health.py` |
| **HLT-002** | A 功能 | readiness 在 Lease 未 acquire 返回 503 | 同上 |
| **HLT-003** | A 功能 | readiness 在 MemoryReconciler 心跳超时返回 503 | 同上 |
| **HLT-004** | A 功能 | readiness 在 admission webhook TLS 未加载返回 503 | 同上 |
| **HLT-005** | C 接口契约 | HealthCheck 构造不依赖 K8s client(仅 Protocol) | 同上 |
| **HLT-006** | A 功能 | Readiness 200 后所有探针条件仍需持续满足 | 同上 |
| **HLT-007** | B 质量 | healthz_app / readyz_app 满足 ASGI 3.0 callable | 同上 |
| **HLT-008** | C 接口契约 | LeaseChecker Protocol 不强制 kubernetes_asyncio 类型 | 同上 |

**测试 ID 分布**:20 OBS + 8 HLT = 28 ID(覆盖 §A-§G 6 维度:功能 13 / 接口契约 10 / 质量 5)。

**与 L2-2 Spec 对应**:
- OBS-001~OBS-025 完全继承 L2-2 §10.7(25 ID);
- HLT-001~HLT-008 是本 L3-1 新增(health.py 在 L2-2 §13.5 仅有字段级,新增文件级契约触发 8 测试 ID)。

### 7.2 Helm values + 9 Helm 模板文件级契约

#### 7.2.1 Helm 模板文件清单(9 模板)

```
deploy/helm/operator/
├── Chart.yaml
├── values.yaml                      # 稳定结构见 §7.2.2
├── values.schema.json               # 自动生成自 Pydantic,见 §7.2.3
├── NOTES.txt
└── templates/
    ├── _helpers.tpl                 # 命名/标签/ServiceAccount 命名辅助
    ├── deployment.yaml              # Operator + admission webhook 双容器
    ├── service.yaml                 # 双端口 Service(80→8080 + 443→8443)
    ├── serviceaccount.yaml          # cert-manager.io/inject-ca-from annotation
    ├── configmap.yaml               # Helm values → env vars(可选)
    ├── rbac.yaml                    # clusterrole + clusterrolebinding
    ├── admission_rbac.yaml          # admission role + rolebinding
    ├── networkpolicy.yaml           # ingress + egress 限制
    ├── prometheusrule.yaml          # 6 个告警规则
    └── servicemonitor.yaml          # 11+4 指标 scrape 配置
```

#### 7.2.2 values.yaml 稳定结构(继承 L2-2 §9.1 完全一致)

```yaml
operator:
  replicaCount: 2
  image:
    repository: ghcr.io/coderzhangfujiang/superteam-a2a-operator
    tag: v0.2.0
    pullPolicy: IfNotPresent
  serviceAccount:
    create: true
    name: superteam-a2a-operator
    annotations:
      cert-manager.io/inject-ca-from: superteam-a2a-ca/superteam-a2a-ca-cert
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
  observability:
    otelEndpoint: http://otel-collector.observability:4317
    logLevel: info
  mtls:
    caBundleSecretRef: superteam-a2a-ca
```

**字段命名规则**:CamelCase 是 Helm/wire 字段名;Python `HelmValues` model 使用 snake_case 但通过 `alias` + `populate_by_name` 显式映射,**禁止隐式改变 values.schema.json 字段名**。

#### 7.2.3 Pydantic models(继承 L2-2 §9.2 完整契约)

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


class ServiceAccountConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    create: bool = True
    name: str = "superteam-a2a-operator"
    annotations: dict[str, str] = Field(default_factory=lambda: {
        "cert-manager.io/inject-ca-from": "superteam-a2a-ca/superteam-a2a-ca-cert",
    })


class OperatorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    replica_count: int = Field(2, alias="replicaCount", ge=1, le=10)
    image: dict[str, str]
    service_account: ServiceAccountConfig = Field(alias="serviceAccount")
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

**Schema 生成**:Helm `values.schema.json` 由 `HelmValues.model_json_schema(by_alias=True)` 唯一生成;**CI 重新生成并做无差异检查,手工修改生成文件视为失败**。

#### 7.2.4 9 Helm 模板逐个契约

**(1) `_helpers.tpl`**:
- `superteam-a2a.operatorName` — `{{ include "common.names.fullname" . }}-operator`
- `superteam-a2a.labels` — `app.kubernetes.io/name=superteam-a2a-operator`、`app.kubernetes.io/component=operator`、`app.kubernetes.io/part-of=superteam-a2a`、`app.kubernetes.io/managed-by=Helm`、`helm.sh/chart={{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}`、`app.kubernetes.io/version={{ .Chart.AppVersion }}`
- `superteam-a2a.selectorLabels` — 仅 `app.kubernetes.io/name=superteam-a2a-operator`(避免 label 冲突)
- `superteam-a2a.serviceAccountName` — 默认 `superteam-a2a-operator`,可通过 `operator.serviceAccount.name` 覆盖

**(2) `deployment.yaml`**(关键字段):
- **双容器**:
  - `operator` 容器:`image` from `values.operator.image.*`、`ports.containerPort=8080`(metrics + healthz/readyz)、`args=["run"]` 或从 `argv[0]` 取;
  - `admission-webhook` 容器:与 operator 容器共享 `image`,`ports.containerPort=8443`、`args=["admission"]`(独立子命令允许 pipeline 化);
- **探针**:
  - `livenessProbe.httpGet.path=/healthz` + `port=8080`,`initialDelaySeconds=10`,`periodSeconds=10`、`timeoutSeconds=3`、`failureThreshold=3`;
  - `readinessProbe.httpGet.path=/readyz` + `port=8080`,`initialDelaySeconds=15`,`periodSeconds=5`、`timeoutSeconds=3`、`failureThreshold=3`;
  - `startupProbe.httpGet.path=/healthz` + `port=8080`,`failureThreshold=30`、`periodSeconds=10`(启动慢保障);
- **resources** from `operator.python.resources`(requests + limits);
- **envFrom.configMapRef=superteam-a2a-operator-config** + 可选 secretRef;
- **volumeMounts**:`/tmp`(emptyDir)、`/workspace`(emptyDir)、可选 mTLS Secret;
- **securityContext**:`runAsNonRoot=true`、`runAsUser=1000`、`readOnlyRootFilesystem=true`、`allowPrivilegeEscalation=false`、`capabilities.drop=[ALL]`;
- **terminationGracePeriodSeconds=30**;
- **`spec.topologySpreadConstraints`** 跨节点分布(可选,默认关闭)。

**(3) `service.yaml`**:
- 端口 1:`port=80`、`targetPort=8080`、`name=http`(Operator metrics + healthz/readyz);
- 端口 2:`port=443`、`targetPort=8443`、`name=admission`(admission webhook);
- `type=ClusterIP`;
- `selectorLabels` 来自 `_helpers.tpl.selectorLabels`(`app.kubernetes.io/name=superteam-a2a-operator`);
- `publishNotReadyAddresses=true`(允许非 ready 副本保留端点,FRD-1 HLT-001 设计要求)。

**(4) `serviceaccount.yaml`**:
- 命名 `{{ include "superteam-a2a.serviceAccountName" . }}`,命名空间 `superteam-a2a-system`;
- annotation 来自 `values.operator.serviceAccount.annotations`(默认 `cert-manager.io/inject-ca-from: superteam-a2a-ca/superteam-a2a-ca-cert`);
- `automountServiceAccountToken: true`(chart 默认覆盖;子 chart 不得关闭)。

**(5) `configmap.yaml`**(可选,默认开启):
- `data.HELM_VALUES_JSON` = `{{ toJson .Values }}`(Python 启动时解析);
- `data.OTEL_EXPORTER_OTLP_ENDPOINT` = `{{ .Values.operator.observability.otelEndpoint }}`;
- `data.LOG_LEVEL` = `{{ .Values.operator.observability.logLevel }}`。

**(6) `rbac.yaml`**(见 §7.3.2 ClusterRole 完整规则):
- `ClusterRole` `superteam-a2a-operator` + `ClusterRoleBinding`;
- 引用 helper 输出的 ServiceAccount name + namespace。

**(7) `admission_rbac.yaml`**(见 §7.3.3 admission Role):
- namespace-scoped `Role` + `RoleBinding` `superteam-a2a-admission`;
- 仅 secrets 读权限 + admissionregistration.k8s.io read。

**(8) `networkpolicy.yaml`**:
- **ingress**:仅允许 API Server(port 443)从 `kubernetes` namespace + Prometheus(port 8080 from cluster CIDR)+ cert-manager webhook control plane(port 443 from `cert-manager` namespace);
- **egress**:仅 K8s API server(port 443 排除 service CIDR)+ OTLP collector(port 4317 from `observability` namespace)+ DNS(port 53 to kube-system);
- `policyTypes: [Ingress, Egress]`、`podSelector.matchLabels` from helper。

**(9) `prometheusrule.yaml`**(6 个告警规则):
- `OperatorReconcileFailureRate` — `rate(superteam_operator_reconcile_total{result="error"}[5m]) > 0.1 for 2m` (severity: warning);
- `OperatorAdmissionRejectSpike` — `rate(superteam_operator_admission_validation_total{result="rejected"}[5m]) > 0.5 for 2m` (severity: warning);
- `OperatorLeaderNotElected` — `absent(superteam_operator_leader_election == 1) for 2m` (severity: critical);
- `OperatorLeaseRenewFailure` — `rate(superteam_operator_lease_renew_total{result="error"}[5m]) > 0.05 for 2m` (severity: warning);
- `OperatorMemoryReconcileLagging` — `histogram_quantile(0.95, rate(superteam_operator_memory_reconcile_duration_seconds_bucket[5m])) > 5 for 2m` (severity: warning);
- `OperatorEventLoopLagHigh` — `histogram_quantile(0.95, rate(superteam_python_event_loop_lag_seconds_bucket[5m])) > 0.5 for 2m` (severity: critical);
- **全局 `for: 2m` 在 alertmanager 层覆盖,rule 文件可省略**。

**(10) `servicemonitor.yaml`**:
- `selector.matchLabels` from helpers;
- `endpoints`:
  - `port=http`、`path=/metrics`、`interval=15s`、`scrapeTimeout=10s`;
  - `relabelings`:drop replica label(`__replica__`)+ drop `prometheus_replica` label;
  - `metricRelabelings`:保留 prefix=`superteam_` 或 prefix=`superteam_python_`(避免跨服务 metric 污染);
  - `honorLabels: true`(尊重 Operator 自带标签)。

#### 7.2.5 Helm values 测试 ID 矩阵(19 HELM + 10 HELM-DEPLOY = 29 ID · §A-§G 5 维度)

| 测试 ID | 维度 | 描述 | 文件 |
|---------|------|------|------|
| **HELM-001** | A 功能 | 空配置使用全部默认值 | `tests/unit/config/test_helm_values.py` |
| **HELM-002** | A 功能 | `replicaCount=1` 接受 + Leader Election 启用 | 同上 |
| **HELM-003** | B 质量 | `replicaCount=11` 被拒绝(ge=1, le=10) | 同上 |
| **HELM-004** | A 功能 | `python.workers=2` 被拒绝 | 同上 |
| **HELM-005** | B 质量 | `controllers.agent=2` 被拒绝(ge=1, le=1) | 同上 |
| **HELM-008** | A 功能 | 未知字段被 `extra=forbid` 拒绝 | 同上 |
| **HELM-009** | B 质量 | `admission.port < 1024` 被拒绝 | 同上 |
| **HELM-010** | C 接口契约 | AdmissionConfig.failurePolicy 仅接受 Fail/Ignore | 同上 |
| **HELM-011** | C 接口契约 | `leaderElection.enabled=False + replicaCount > 1` 启动失败 | `tests/integration/operator/test_startup.py` |
| **HELM-012** | A 功能 | CamelCase YAML 可 round-trip 为 Pydantic model | `test_helm_values.py` |
| **HELM-013** | B 质量 | `memoryReconciler.intervalSeconds=5` 被拒绝(ge=10) | 同上 |
| **HELM-014** | B 质量 | `memoryReconciler.batchSize=5` 被拒绝(ge=10) | 同上 |
| **HELM-015** | B 质量 | `memoryReconciler.cpuOffloadThreshold=99` 被拒绝(ge=100) | 同上 |
| **HELM-016** | A 功能 | `renewIntervalSeconds >= leaseDurationSeconds` 被拒绝 | 同上 |
| **HELM-020** | A 功能 | 多副本关闭 Leader Election 被拒绝 | `test_startup.py` |
| **HELM-024** | A 功能 | failurePolicy 仅接受 Fail/Ignore | `test_helm_values.py` |
| **HELM-028** | B 质量 | Pydantic JSON schema 与仓库 values.schema.json 无差异 | `tests/integration/helm/test_schema_diff.py` |
| **HELM-029** | C 接口契约 | `controllers` dict 仅接受 4 个白名单 key | `test_helm_values.py` |
| **HELM-032** | A 功能 | 4 个 controller key 并发度只能为 1 | 同上 |
| **HELM-DEPLOY-001** | A 功能 | deployment 渲染 2 containers(operator + admission-webhook) | `tests/integration/helm/test_rendering.py` |
| **HELM-DEPLOY-002** | A 功能 | deployment liveness + readiness + startup 三探针 | 同上 |
| **HELM-DEPLOY-003** | A 功能 | service 渲染双端口(80→8080 + 443→8443) | 同上 |
| **HELM-DEPLOY-004** | A 功能 | serviceaccount annotation 引用 ClusterIssuer | 同上 |
| **HELM-DEPLOY-005** | A 功能 | configmap HELM_VALUES_JSON = values.yaml 序列化 | 同上 |
| **HELM-DEPLOY-006** | A 功能 | prometheusrule 6 告警规则渲染(rule count=6) | 同上 |
| **HELM-DEPLOY-007** | A 功能 | servicemonitor endpoints 命中 /metrics + interval=15s | 同上 |
| **HELM-DEPLOY-008** | A 功能 | networkpolicy ingress 仅允许 API Server + Prometheus + cert-manager | 同上 |
| **HELM-DEPLOY-009** | A 功能 | networkpolicy egress 仅 K8s API + OTLP + DNS | 同上 |
| **HELM-DEPLOY-010** | B 质量 | helm lint 在 CI 中无警告 | 同上 |

**测试 ID 分布**:19 HELM + 10 HELM-DEPLOY = 29 ID(覆盖 §A-§G 5 维度:功能 17 / 质量 9 / 接口契约 3)。

### 7.3 RBAC 文件级契约(2 Helm 子模板 · 继承 L2-2 §11 完全一致)

#### 7.3.1 RBAC 模板文件清单

| 文件 | 输出资源 | 命名空间 |
|------|----------|----------|
| `rbac.yaml` | `ClusterRole` + `ClusterRoleBinding` `superteam-a2a-operator` | cluster-scoped |
| `admission_rbac.yaml` | `Role` + `RoleBinding` `superteam-a2a-admission` | `superteam-a2a-system` |

#### 7.3.2 ClusterRole 完整规则(继承 L2-2 §11.2 7 apiGroups)

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
    resources:
      ["agents/status", "agentsets/status", "workflows/status",
       "memories/status", "knowledgescopes/status", "knowledgeitems/status"]
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

**约束**:
- `resourceNames` 限定在 `superteam-a2a-admission` 一个;
- `namespaces` 字段不得新增非 `superteam-a2a-system` 的值;
- admission webhook 复用同一 ServiceAccount;如未来拆分独立身份,本节必须同步调整并加 RBAC-XXX 测试。

#### 7.3.3 admission Role 完整规则(继承 L2-2 §11.4 namespace-scoped secrets only)

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

**约束**:Role 不允许扩展到 `pods` / `services`;admission 不直接执行 K8s 写操作。如果 v0.5+ admission 引入 K8s 调用,必须改用 ClusterRole 并加测试。

#### 7.3.4 RBAC 测试 ID 矩阵(10 RBAC + 4 RBAC-IT = 14 ID · §A-§G 4 维度)

| 测试 ID | 维度 | 描述 | 文件 |
|---------|------|------|------|
| **RBAC-001** | A 功能 | ClusterRole 规则集合与 §7.3.2 精确等价 | `tests/integration/rbac/test_manifests.py` |
| **RBAC-002** | A 功能 | ClusterRoleBinding 引用 ServiceAccount `superteam-a2a-operator` | 同上 |
| **RBAC-003** | B 质量 | ClusterRole 无 namespaces 限定 | 同上 |
| **RBAC-004** | A 功能 | ServiceAccount 命名空间为 `superteam-a2a-system` | 同上 |
| **RBAC-005** | B 质量 | ServiceAccount annotation 引用 ClusterIssuer | 同上 |
| **RBAC-006** | C 接口契约 | admission Role 仅含 secrets read + validatingwebhookconfigurations read | 同上 |
| **RBAC-007** | A 功能 | admission Role 不出现写权限 | 同上 |
| **RBAC-008** | C 接口契约 | ServiceAccount automountServiceAccountToken=true | 同上 |
| **RBAC-009** | B 质量 | ClusterRole `resourceNames` 限定在 `superteam-a2a-admission` 一个 | 同上 |
| **RBAC-010** | B 质量 | `helm template` 在 CI 中无警告 | `tests/integration/helm/test_rendering.py` |
| **RBAC-IT-001** | A 功能 | envtest:ClusterRole 在 Operator Pod 内可读 6 类 CRD | `tests/integration/rbac/test_runtime_access.py` |
| **RBAC-IT-002** | A 功能 | envtest:admission Role 实际读取 webhook TLS Secret 成功 | 同上 |
| **RBAC-IT-003** | A 功能 | envtest:Operator 创建 K8s Event 成功(events.create) | 同上 |
| **RBAC-IT-004** | A 功能 | envtest:Operator 创建/更新 Lease 成功(leases.create/update/patch) | 同上 |

**测试 ID 分布**:10 RBAC + 4 RBAC-IT = 14 ID(覆盖 §A-§G 4 维度:功能 8 / 质量 4 / 接口契约 2)。

### 7.4 observability + RBAC + Helm values 关键不变量

#### 7.4.1 observability 不变量(继承 L2-2 §10 + 宪法 §7)

- ✅ **指标 wire 不变**:11 Operator 指标名 + 4 Python runtime 指标名 = `superteam_operator_*` + `superteam_python_*`,修改必须走 ADR;
- ✅ **Event reason 白名单**:8 种,新增 reason 必须新增 enum 成员 + 测试;
- ✅ **structlog 8 字段必含**:`ts` / `level` / `msg` / `trace_id` / `crd` / `namespace` / `name` / `phase`;附加字段以业务前缀开头(如 `decay.*`、`lease.*`);
- ✅ **Health endpoints**:`/healthz` 进程存活 + `/readyz` Lease + Memory + admission 三件套;
- ✅ **OTel TracerProvider 测试替换**:`InMemorySpanExporter` 必须不污染生产 provider;
- ✅ **message 限长 1024**:UTF-8 字符级截断;过长直接截;不附加省略号;
- ✅ **Operator 错误不通过 A2A 错误码传播**:Operator / admission 错误只写 K8s Events + structlog,**不走** A2A protocol channel(L2-2 §10.7 末尾明确)。

#### 7.4.2 Helm values 不变量(继承 L2-2 §9 + 宪法 §6 mTLS)

- ✅ **CamelCase wire 一致**:values.yaml 字段名 = Pydantic alias = values.schema.json 字段名;snake_case 仅在 Python 代码内;
- ✅ **`extra="forbid"` 顶层 + 嵌套层全生效**:未知字段拒绝;
- ✅ **`controllers` dict 仅 4 个白名单 key**:`agent` / `agentset` / `workflow` / `memory`;并发度只能为 1;
- ✅ **`replicaCount > 1` 必须 `leaderElection.enabled=true`**:启动期 / 部署期校验;
- ✅ **`admission.failurePolicy` 默认 `Fail`**:生产值不得默认降为 `Ignore`;
- ✅ **`renewInterval < leaseDuration`**:跨字段 model_validator 校验;
- ✅ **schema 一致性**:CI 重新生成 `values.schema.json` 与仓库无差异;
- ✅ **Python 3.12+ + 单 worker**:v0.2 wire/deployment contract;修改必须走 ADR;
- ✅ **cert-manager 集成**:ServiceAccount annotation + ClusterIssuer(L2-2 §9 / §11);
- ✅ **NetworkPolicy + mTLS**:Operator Pod 仅与 API Server / OTLP collector / cert-manager 通信(宪法 §6);

#### 7.4.3 RBAC 不变量(继承 L2-2 §11 + 宪法 §6)

- ✅ **ClusterRole 名称 wire 不变**:`superteam-a2a-operator`;ServiceAccount 名称 wire 不变;
- ✅ **命名空间 wire 不变**:`superteam-a2a-system`;Helm chart Namespace 模板必须存在;不允许跨 chart 共享;
- ✅ **权限集合修改走 ADR**:ClusterRole / Role apiGroups/verbs/resourceNames 调整必须 §F 同步 + RBAC-XXX 测试;
- ✅ **cert-manager 仅通过 ServiceAccount annotation 触发**:不允许手动注入 CA bundle;
- ✅ **admission Role 不写**:`pods` / `services` 等越权 verbs 不允许;
- ✅ **CI `helm template` 无警告**:RBAC-DRIFT 失败必须停止后续构建;
- ✅ **CI `tests/integration/rbac/test_manifests.py` 校验**:`§7.3.2` 规则集合精确等价 + ServiceAccount annotation 与 §7.4.2 mTLS 一致 + `Role` 不出现写 verbs;

#### 7.4.4 observability + RBAC + Helm values wire contract 总览

| 类别 | wire 字段数 | 修改门禁 |
|------|-------------|----------|
| Operator 指标名 | 11 | ADR |
| Python runtime 指标名 | 4 | ADR |
| EventReason 白名单 | 8 | enum 成员 + 测试 |
| structlog 字段名 | 8 | 命名空间以业务前缀开头 |
| Helm values 字段名 | ~28(含 controllers dict 4 key) | alias 映射 + schema 重新生成 |
| ClusterRole apiGroups | 7(含 subresource) | ADR |
| admission Role apiGroups | 2 | ADR |
| ServiceAccount annotation | 1(cert-manager) | 强制一致 |
| Namespace | 1(`superteam-a2a-system`) | 强制 wire |

**总计**:**~52 wire contract 字段**;任何修改必须走 ADR。

### 7.5 与既有 L2 Spec 测试 ID 对应

- **L2-2 Spec §10.7** 提供 OBS-001~OBS-025 = 25 ID → L3-1 完整继承无修改;
- **L2-2 Spec §9.4** 提供 HELM-001~HELM-032 = 32 ID → L3-1 落地为 19 HELM + 10 HELM-DEPLOY = 29 ID(保留所有 L2-2 高优先级 ID + 新增部署相关 6 ID);
- **L2-2 Spec §11.6** 提供 RBAC-001~RBAC-010 = 10 ID → L3-1 完整继承 + 新增 RBAC-IT-001~004 = 14 ID;
- 本 §7 新增 HLT-001~HLT-008 = 8 ID;
- **本节新增/继承测试 ID 总计** = **29 (HELM) + 14 (RBAC) + 28 (OBS+HLT) = 71 ID**,覆盖 §A-§G 6 维度。

### 7.6 与 L3-1 §0-§6 衔接

- **§1.3 文件清单**:observability/ 子包 6 文件 + helm/operator/templates/ 9 模板 + RBAC 2 子模板 = **17 文件**新增到 §1.3 主清单;落地后 L3-1 文件清单 **70 → 87**;
- **§2.3 Python 包结构**:§7.2.3 Pydantic models 落实 §2.3.7 config/helm_values.py 完整契约;
- **§3 3 个 CRD Controller + MemoryReconciler 概要**:MemoryReconciler 调用 `observability.events` + `observability.metrics` 的接口在 §6.3 MemoryReconcilerService 伪代码中已声明;本 §7 是其落地的文件级契约;
- **§4 admission webhook**:调用 `observability.metrics.admission_validation_total` / `observability.events.ADMISSION_REJECTED`;此处 §7.1 提供契约;
- **§5 Leader Election**:调用 `observability.metrics.leader_election` / `.lease_renew_total` / `.lease_transition_total`;`observability.events.LEADER_ACQUIRED` / `LEADER_LOST`;此处 §7.1 提供契约;
- **§6 Memory**:调用 `observability.metrics.memory_reconcile_total` / `.memory_decay_total`;此处 §7.1 提供契约;
- **§7.3 RBAC**:ClusterRole / Role 引用 `certificates.cert-manager.io`、`events.k8s.io` 是 §7.1 events.py 调用 K8s Events 的权限依据;

**结论**:**§7 是 §3-§6 运行时可观测性 + K8s 部署资产的物理落地**,所有引用点的契约均集中在本节给出。

---

## 8. 测试策略 + 工具链文件级 Spec（落地到 pytest 测试镜像 + pyproject + uv workspace + Dockerfile + Helm chart 顶层）

> 本节将 L2-2 Spec §12 测试策略 + §13 工具链与部署形态落地为 **pytest 测试镜像布局 + 4 工程配置文件 + Helm chart 顶层结构** 的文件级契约。所有测试 ID（`TEST-` / `TOOL-` / `E2E-` 前缀）+ pyproject 字段名 + Dockerfile 阶段 + Helm chart 元信息 + 镜像 tag 规则 属于 v0.1 工程 contract；新增/修改必须走 ADR。
>
> **范围**:测试镜像 87 `test_*.py` 文件 + conftest.py + 4 工程配置文件（`pyproject.toml` / `Dockerfile` / `Chart.yaml` / `values.schema.json`）+ uv workspace 根 `pyproject.toml` = **新增 92 个工程资产**到 L3-1 文件清单（70 → 87 Python + 25 工程 = 162 资产；测试镜像与 src 1:1 镜像）。落地后 L3-1 累计文件清单 **70 → 162**（87 src + 25 工程 + 50 顶层测试夹具 = 162）。
>
> **测试 ID 总额**:L3-1 累计 §0-§7 = 218 ID,**§8 新增/继承 59 ID**(TEST-001~025 = 25 ID 完整继承 L2-2 §12.7 + TOOL-001~034 = 34 ID 完整继承 L2-2 §13.9;L3-1 §8 不创造新 ID,仅落地到具体测试文件路径),L3-1 §8 落地后累计 **277 ID**(仍然在 L2-2 Spec §A-§G 6 维度范围内;TEST/TOOL 完整继承 L2-2 ID 矩阵)。
>
> **与 L2-2 Spec §12/§13 关系**:L3-1 **完整继承** L2-2 §12 测试策略 + §13 工具链的所有契约(测试目录、覆盖率、pyproject 字段、Dockerfile 阶段、Helm chart 顶层、镜像 tag),落地为 **每个文件的具体路径 + 测试文件 ID 映射**;L3-1 不创造新测试策略或工具链概念。

### 8.1 测试目录镜像布局（87 src → 87 test_*.py + 50 顶层测试夹具 = 137 测试文件）

> **镜像规则**(继承 L2-2 Spec §12.1 + 宪法 §15.5):`src/superteam_a2a/operator/<sub>/<file>.py` → `tests/unit/<sub>/test_<file>.py` 1:1 镜像;新增 `*.py` 必须有同名 `test_*.py`,否则 CI 失败。

**L3-1 测试目录完整结构**（基于 L2-2 §12.1 + §7 observability/RBAC/Helm 17 文件新增后的 87 src 文件 1:1 镜像）:

```
packages/operator/tests/
├── conftest.py                                  # 共享 fixture：fake_k8s_client / fake_clock / fake_election / fake_metrics
├── pytest.ini                                   # pytest 配置（asyncio_mode=auto + 严格覆盖率门禁）
├── unit/                                        # 87 个 test_*.py（src 1:1 镜像）
│   ├── conftest.py                              # 单元测试层 fixture（fake_clock 等）
│   ├── operator/                                # 顶层 operator/ 3 文件
│   │   ├── test___init__.py                     # UT-OP-01~04 public API 导出
│   │   ├── test___internals.py                  # UT-OP-05~08 internal API 重导出
│   │   ├── test_main.py                         # UT-OP-09~12 OperatorMain.run() 启动序列
│   │   └── test___main__.py                     # UT-OP-13~14 CLI 入口（python -m superteam_a2a.operator）
│   ├── controllers/                             # 4 Controller handler 测试
│   │   ├── test_agent.py                        # UT-C-A-01~07 AgentController handlers + error dispatch
│   │   ├── test_agentset.py                     # UT-C-AS-01~07 AgentSetController
│   │   ├── test_workflow.py                     # UT-C-W-01~07 WorkflowController + DAG 校验触发
│   │   └── test_memory_reconciler_controller.py # UT-C-M-01~09 MemoryReconciler Kopf timer + handlers
│   ├── reconcilers/                             # 业务服务测试（5 文件）
│   │   ├── test_base.py                         # UT-R-B-01~04 BaseReconciler 错误分类
│   │   ├── test_agent_reconciler.py             # UT-R-A-01~05 AgentReconcilerService
│   │   ├── test_agentset_reconciler.py          # UT-R-AS-01~05 AgentSetReconcilerService
│   │   ├── test_workflow_reconciler.py          # UT-R-W-01~06 WorkflowReconcilerService
│   │   └── test_memory_reconciler_service.py    # UT-R-M-01~05 MemoryReconcilerService
│   ├── admission/                               # admission webhook server + 5 validators
│   │   ├── test_server.py                       # UT-AW-S-01~05 ASGI server + 双路由
│   │   ├── test_tls.py                          # UT-AW-T-01~04 TLS 热更新
│   │   ├── test_base_validator.py               # UT-AW-BV-01~03 CRDValidator Protocol
│   │   ├── test_agent_validator.py              # UT-AW-AV-01~03 AgentValidator
│   │   ├── test_agentset_validator.py           # UT-AW-ASV-01~03 AgentSetValidator
│   │   ├── test_workflow_validator.py           # UT-AW-WV-01~03 WorkflowValidator + DAG
│   │   ├── test_memory_validator.py             # UT-AW-MV-01~03 MemoryValidator
│   │   └── test_mutual_exclusion.py             # UT-AW-ME-01~03 Knowledge↔Memory 互斥
│   ├── leader_election/                         # K8s Lease 客户端 + Election 主类
│   │   ├── test_lease_client.py                 # UT-LE-LC-01~05 AsyncLeaseClient 状态机
│   │   └── test_election.py                     # UT-LE-EL-01~05 Election 完整生命周期
│   ├── finalizers/                              # 4 Finalizer 名称 + 工具
│   │   └── test_names.py                        # UT-FN-01~03 4 Finalizer 名称常量
│   ├── clients/                                 # kubernetes_asyncio 封装
│   │   └── test_k8s_client.py                   # UT-KC-01~07 AsyncK8sClient
│   ├── observability/                           # observability 子包 6 文件（§7.1 新增）
│   │   ├── test_metrics.py                      # OBS-001~013 MetricsRegistry + 11+4 指标
│   │   ├── test_health.py                       # HLT-001~008 双探针 + Lease + MemoryReconciler
│   │   ├── test_tracing.py                      # OBS-016~019 OTLP + RuntimeMonitor
│   │   ├── test_logging.py                      # OBS-010/024 structlog 8 字段 + BoundLogger
│   │   ├── test_events.py                       # OBS-007/022/025 EventReason + 1024 截断
│   │   └── test___init__.py                     # observability 子包导出
│   ├── errors/                                  # ReconcileError hierarchy
│   │   └── test_errors.py                       # UT-ER-01~06 错误分类 + handle_error
│   ├── config/                                  # Helm values Pydantic
│   │   └── test_helm_values.py                  # UT-CF-01~04 HelmValues + alias 映射
│   └── models/                                  # CRD 实体 Pydantic（36 文件 → 36 test_*.py）
│       ├── agent/
│       │   ├── test_spec.py                     # UT-MD-A-S 1~5 AgentSpec
│       │   ├── test_status.py                   # UT-MD-A-St 1~5 AgentStatus
│       │   ├── test_conditions.py               # UT-MD-A-C 1~4 AgentCondition
│       │   └── test_enums.py                    # UT-MD-A-E 1~3 Phase/ReconcileState
│       ├── agentset/                            # AgentSetSpec/Status/Conditions/Enums (4)
│       ├── workflow/                            # WorkflowSpec/Status/Conditions/Enums/DagValidator (5)
│       └── memory/                              # MemorySpec/Status/Conditions/Enums/Decay/Reinforce/GC/Promotion (8)
├── integration/                                 # envtest + Kopf testing harness
│   ├── conftest.py                              # envtest fixture（Kopf 启动 + CRD apply）
│   ├── envtest/                                 # envtest 集成
│   │   ├── test_agent_lifecycle.py              # IT-ENV-A-01~05 4 CRD 完整生命周期
│   │   ├── test_finalizer_cleanup.py            # IT-ENV-FC-01~04 Finalizer 清理
│   │   ├── test_memory_timer.py                 # IT-ENV-MT-01~04 MemoryReconciler 定时
│   │   └── test_concurrent_election.py          # IT-ENV-CE-01~03 多副本并发（fake）
│   ├── admission/                               # admission 集成
│   │   ├── test_webhook_registration.py         # IT-AW-WR-01~04 ValidatingWebhookConfiguration
│   │   ├── test_mtls_rotation.py                # IT-AW-MT-01~03 cert-manager fake issuer
│   │   └── test_mutual_exclusion_e2e.py         # IT-AW-ME-01~03 Knowledge↔Memory 拒绝
│   └── helm/                                    # Helm chart 集成测试（§13.6 + §9.4）
│       ├── test_chart_lint.py                   # HELM-021~024 helm lint + template
│       ├── test_values_schema.py                # HELM-025~028 values.schema.json 与 Pydantic 对齐
│       └── test_rbac_apply.py                   # RBAC-IT-001~004 envtest 中 apply ClusterRole/Role
├── e2e/                                         # kind 集群 E2E
│   ├── conftest.py                              # kind 集群 fixture（独立 cluster name）
│   ├── kind/
│   │   ├── test_agent_lifecycle.py              # E2E-001~010 Agent CRD + Pod Ready + 通信
│   │   ├── test_workflow_dag.py                 # E2E-011~015 合法/非法 DAG Workflow
│   │   └── test_memory_reconcile.py             # E2E-016~020 MemoryReconciler decay/reinforce
│   └── conformance/
│       └── test_a2a_wire_contract.py            # CONFORMANCE-001~010 4 项目扩展 A2A method + 11 错误码
├── perf/                                        # 性能测试（v0.1 占位 · v0.5+ 启动）
│   └── test_reconcile_throughput.py             # PERF-001~005 v0.1 @pytest.mark.skip
└── tools/                                       # 工具脚本测试（独立 pytest collect）
    ├── test_chart_version_sync.py               # TOOL-010/013 pyproject.version == Chart.appVersion
    └── test_lock_check.py                       # TOOL-013 uv lock --check
```

**总计**:87 个 src 文件 → 87 个 `test_*.py` 单元测试 + 8 envtest + 7 admission 集成 + 3 helm 集成 + 3 kind E2E + 1 conformance + 1 perf + 2 tools = **111 test_*.py** + 6 conftest.py + pytest.ini + Chart.yaml + values.yaml + values.schema.json + Dockerfile + pyproject.toml + uv.lock = **137 文件**(L3-1 §8 文件清单 70 + 17 §7 + 50 §8 镜像 = 137;含 50 个独立顶层资产如 conftest/pytest.ini/Dockerfile 等)。

**conftest.py 分层**(继承 L2-2 Spec §12.1 + 强化分层 fixture):

- `tests/conftest.py`:全局 fixture,导入所有子层 conftest 的 fixture 并提供 `fake_k8s_client` / `fake_clock` / `fake_election` / `fake_metrics` 4 个核心 mock。
- `tests/unit/conftest.py`:单元测试层,定义 `event_loop_policy` (Windows 默认 ProactorEventLoop;Linux 默认 uvloop)、`auto_mock_clock` autouse fixture。
- `tests/integration/conftest.py`:envtest fixture,启动 Kopf testing harness (60 秒内完成,IT-ENV-INIT-001);使用 fake AsyncLeaseClient 模拟多副本。
- `tests/integration/helm/conftest.py`:Helm fixture,执行 `helm template` + `helm lint` + 比对 `values.schema.json`。
- `tests/e2e/conftest.py`:kind fixture,创建独立 cluster name `e2e-<short-sha>-<pid>`(TEST-019 E2E 必须从干净 kind 集群开始)。

### 8.2 单元测试（继承 L2-2 Spec §12.2 · 强制 1:1 镜像）

**目标**(与 L2-2 Spec §12.2 + 宪法 §15.5 一致):

- 行覆盖 **≥ 80%**,分支覆盖 **≥ 75%**,关键路径(reconcile / cleanup / admission / Leader Election)覆盖 **≥ 95%**。
- 每个 `*.py` 文件**必须**有同名 `test_*.py`(TEST-001);新增文件必须附带 ≥ 80% 行覆盖,否则 CI 失败(TEST-005)。
- pyright strict + ruff + bandit + pip-audit + interrogate 5 重 gate(TEST-009)。

**强制工具链**(继承 L2-2 §12.2 + ADR-0005 §9 + 宪法 §9.4/§9.7):

| 工具 | 版本约束 | 用途 | 测试 ID |
|------|----------|------|---------|
| `pytest` | ≥ 8.0 | 测试运行器 | TEST-002 |
| `pytest-asyncio` | ≥ 0.23 | 异步测试 (asyncio_mode=auto) | TEST-003 |
| `pytest-cov` | ≥ 4.1 | 行/分支覆盖率 | TEST-004 / TEST-012 |
| `pytest-mock` | ≥ 3.12 | mock fixture | TEST-006 |
| `hypothesis` | ≥ 6.100 | 属性测试（Memory decay/reinforce 数学公式） | TEST-007 |
| `respx` | ≥ 0.21 | httpx mock（OTLP exporter / K8s API mock） | TEST-008 |
| `prometheus_client.CollectorRegistry` | ≥ 0.20 | fake metrics registry 隔离 | TEST-010 |
| `ruff` | ≥ 0.4 | lint + import-linter 静态检查 | TEST-009 |
| `pyright --strict` | ≥ 1.1.350 | 类型检查 | TEST-009 |
| `bandit` | ≥ 1.7 | 安全 lint | TEST-009 |
| `pip-audit` | ≥ 2.7 | 依赖漏洞扫描 | TEST-009 |
| `interrogate` | ≥ 1.7 | docstring 100% 覆盖 | TEST-011 |

**关键不变量**:

- ✅ TEST-001:每个新增 `*.py` 必须有同名 `test_*.py`(由 CI 中自定义 pytest plugin `pytest_supertem.py` 检查,失败等同 build break)。
- ✅ TEST-005:关键路径(reconcile / cleanup / admission / Leader Election)行覆盖 ≥ 95% 由 `pytest --cov-fail-under=95 --cov-context=test` 双阈值保证。
- ✅ TEST-012:`pytest --cov=superteam_a2a.operator --cov-fail-under=80` 强制通过。
- ✅ TEST-025:所有错误日志 message 长度 ≤ 1024(由 `observability/logging.py` BoundLogger + pytest caplog 双重断言)。

### 8.3 集成测试（envtest + Kopf harness）

**envtest 范围**(继承 L2-2 Spec §12.3):

- **4 CRD 完整生命周期**:create / update / delete + Finalizer cleanup(IT-ENV-A-01~05);
- **admission webhook 完整流程**:`ValidatingWebhookConfiguration` 注册 + 422/400 错误响应 + 拒绝请求未写 etcd(IT-AW-WR-01~04);
- **Leader Election 多副本场景**:envtest 不支持多实例 → 用 fake `AsyncLeaseClient` 模拟(IT-ENV-CE-01~03);
- **MemoryReconciler 定时任务**:`@kopf.timer` 触发用 mock time(IT-ENV-MT-01~04);
- **mTLS 集成**:cert-manager fake issuer 生成 Secret 供 webhook 加载(IT-AW-MT-01~03);
- **Helm chart apply**:envtest 中 apply ClusterRole/Role/ServiceAccount/RBAC-IT-001~004;
- **Knowledge↔Memory 互斥拒绝** admission 端到端 IT-AW-ME-01~03。

**envtest 已知限制**(继承 L2-2 Spec §12.3,必须在 README 显式标注):

- 不支持 Helm → 测试直接 apply manifest(`tests/integration/helm/` 单独路径 + `helm template` 校验);
- 不支持 cert-manager → 使用 fake Secret(`tests/integration/admission/test_mtls_rotation.py`);
- 不支持多 Operator 副本 → Leader Election 用单副本 + fake 并发场景(`tests/integration/envtest/test_concurrent_election.py`)。
- TEST-016:envtest fixture 在 60 秒内完成启动(IT-ENV-INIT-001 监控)。

### 8.4 E2E 测试（kind 集群 · ≥ 10 场景）

**测试场景**(继承 L2-2 Spec §12.4 的 10 个 + L3-1 §7 落地后新增 10 个 = 20 个 E2E case):

**L2-2 §12.4 继承(完整继承 10 个)**:

- `E2E-001`:Agent CRD 创建 → Pod Ready + `AgentStatus.phase=Ready`。
- `E2E-002`:AgentSet CRD(replicas=3)→ 3 个 Agent 全部 Ready。
- `E2E-003`:合法 DAG Workflow → `WorkflowStatus.phase=Running`。
- `E2E-004`:非法 DAG Workflow → admission 拒绝 + `AdmissionRejected` Event。
- `E2E-005`:Memory CRD 创建 → `MemoryStatus` 初始化 + MemoryReconciler 触发 decay。
- `E2E-006`:KnowledgeItem + Memory 同时引用 → admission 互斥拒绝。
- `E2E-007`:Agent 删除 → Finalizer cleanup → Pod 优雅停止 + `CleanupCompleted`。
- `E2E-008`:Operator 重启 → Lease 自动让位 + 重新选举 + `LeaderAcquired`/`LeaderLost` Event。
- `E2E-009`:mTLS 证书轮换 → admission webhook 不停机 + 0 个 4xx/5xx 漏接。
- `E2E-010`:11 Operator 指标全量暴露,labels 全部填充合法值。

**L3-1 §8 新增(基于 §7 observability + RBAC + Helm 17 文件)**:

- `E2E-011`:6 Prometheus 告警规则触发 → Alertmanager 接收 + 路由正确(`tests/e2e/kind/test_prometheus_alerts.py`)。
- `E2E-012`:NetworkPolicy 阻断 → Operator 无法访问未授权 DNS → 探针失败 + Pod NotReady。
- `E2E-013`:ServiceAccount annotation `cert-manager.io/issuer` 缺失 → admission webhook 启动失败 + `CertificateNotReady` Event。
- `E2E-014`:Helm `replicaCount=3` → 3 Operator 副本 + 唯一 leader + 2 standby `/readyz` 返回 200。
- `E2E-015`:OTLP exporter 不可达 → structlog 错误日志 + tracing span 标记 `error=true` + 不阻塞 reconcile。
- `E2E-016`:`/healthz` 在 Lease 初始化前立即返回 200 + 探针延迟 < 50ms。
- `E2E-017`:`/readyz` 在 admission webhook + Lease 初始化**之后**才返回 200 + 切换顺序由 IT-AW-MT-002 验证。
- `E2E-018`:EventReason 8 种全部覆盖 → K8s Events API 可查询 + `involvedObject.uid` 与 CRD 实例对齐。
- `E2E-019`:ConfigMap `HELM_VALUES_JSON` 修改 → Operator 不重启 + 60s 内 reconcile 读取新配置(可选 reload,IT-CONF-001)。
- `E2E-020`:scrape interval 30s + 11+4 指标全部在 ServiceMonitor 中注册 + `honorLabels=true`。

**E2E 跑在 kind(K8s in Docker)集群中**(继承 L2-2 Spec §12.4):

- 每次运行必须使用独立 cluster 名称 `e2e-<short-sha>-<pid>`(TEST-019 E2E 必须从干净 kind 集群开始);
- CI 中使用 ephemeral runner,失败时 dump `kind export logs` 到 artifacts;
- E2E 总时长预算 10 分钟(TEST-019 timeout),超时则 fail-fast。

### 8.5 Conformance 测试（4 项目扩展 A2A method + 11 错误码）

与 L2-1 Python v0.2.0 Spec §11.5 一致(继承 L2-2 Spec §12.5):

- **4 个项目扩展 A2A method**(`queryKnowledge` / `getKnowledgeItem` / `recordMemory` / `queryMemory`)的 JSON wire shape 一致性(CONFORMANCE-001~004);
- Operator 通过 a2a-sdk client 调用 L2-4 Knowledge Service 4 method(CONFORMANCE-005~008);
- **11 个 A2A JSON-RPC 错误码**与 L2-1 Spec §8.4 字节级一致(CONFORMANCE-009);
- contract test 失败时禁止合并(CI gate,TEST-022)。

**L3-1 §8 新增 Conformance 维度**:

- `CONFORMANCE-011`:Operator 在 Leader Election 切换时,正在处理的 A2A message 不丢失(由 fake `AsyncLeaseClient` 模拟 + L2-1 client retry 验证)。
- `CONFORMANCE-012`:admission webhook 拒绝的 CRD,apiServer 返回的 AdmissionReview JSON 与 L2-1 Spec §4 wire 字节一致。
- `CONFORMANCE-013`:MemoryReconciler decay/reinforce 输出与 L2-4 Spec §3.4 wire 字段 19 项 100% 对齐(`tests/e2e/conformance/test_memory_wire.py`)。

### 8.6 覆盖率与 CI 门禁

继承 L2-2 Spec §12.6:

- `pytest --cov=superteam_a2a.operator --cov-fail-under=80` 强制通过(TEST-012);
- `pyright --strict` 与 `ruff check` 失败等同测试失败(TEST-009);
- `bandit -r packages/operator/src` 与 `pip-audit` 高危漏洞数必须为 0(TEST-009);
- 性能测试 `reconcile_throughput.py` 在 v0.1 仅占位(标记 `@pytest.mark.skip` + 引用 L3-1 移交问题),CI 不得因此失败(PERF-001~005 全部 skip)。

**新增 CI gate**(L3-1 §8 落地):

- **TEST-026**:新增文件必须包含 ≥ 1 个 `test_*.py`(由 pytest plugin `pytest_supertem.py` 静态扫描 `src/` 目录并在收集阶段对比);
- **TEST-027**:`pytest --cov-context=test` 关键模块(reconcilers/admission/leader_election)覆盖率 ≥ 95%;
- **TEST-028**:conftest.py 分层 fixture 无循环导入(由 import-linter 规则 `ST-A2A-CONFTEST` 检测);
- **TOOL-034**:cross-package boundary Ruff 规则 `ST-A2A-BOUNDARY` 在 CI 中通过(L3-1 与 packages/a2a-core / adapter-sdk / knowledge-service 边界)。

### 8.7 关键不变量与测试 ID 矩阵（TEST- 前缀 · 继承 L2-2 §12.7）

继承 L2-2 Spec §12.7 所有 TEST- ID(完整继承 25 个,无修改无新增;L3-1 落地为具体测试文件路径):

| 测试 ID | 描述 | L3-1 落地位置 |
|---------|------|---------------|
| `TEST-001` | 新增 `*.py` 必须有同名 `test_*.py` | CI plugin `pytest_supertem.py` + 87 个 test_*.py 1:1 镜像 |
| `TEST-002` | pytest ≥ 8.0 | `pyproject.toml [project.optional-dependencies.dev]` 锁定 |
| `TEST-003` | pytest-asyncio ≥ 0.23,asyncio_mode=auto | `pytest.ini` 配置 |
| `TEST-004` | pytest-cov ≥ 4.1,行/分支覆盖 | `pyproject.toml [tool.coverage.*]` 配置 |
| `TEST-005` | 关键路径覆盖 ≥ 95% | `--cov-fail-under=95 --cov-context=test` |
| `TEST-006` | pytest-mock ≥ 3.12 | dev 依赖 |
| `TEST-007` | hypothesis ≥ 6.100 | `tests/unit/models/memory/test_decay.py` 属性测试 |
| `TEST-008` | respx ≥ 0.21 | `tests/unit/observability/test_tracing.py` |
| `TEST-009` | ruff + pyright + bandit + pip-audit 全部通过 | CI workflow `lint.yml` 4 步 gate |
| `TEST-010` | prometheus_client.CollectorRegistry 隔离 | `tests/unit/observability/test_metrics.py` |
| `TEST-011` | interrogate ≥ 1.7,docstring 100% | `pyproject.toml [tool.interrogate]` fail-under=100 |
| `TEST-012` | `--cov-fail-under=80` 通过 | CI workflow `test.yml` |
| `TEST-016` | envtest fixture 在 60 秒内完成启动 | `tests/integration/envtest/conftest.py` IT-ENV-INIT-001 |
| `TEST-019` | E2E 必须从干净 kind 集群开始,禁止复用 | `tests/e2e/conftest.py` 独立 cluster name |
| `TEST-022` | conformance 失败 = 合并阻断 | CI workflow `conformance.yml` required check |
| `TEST-025` | 所有错误日志 message 长度 ≤ 1024 | `tests/unit/observability/test_logging.py` caplog 断言 |
| **TEST-026**(新增) | 新增文件必须包含 ≥ 1 个 `test_*.py` | CI plugin `pytest_supertem.py` |
| **TEST-027**(新增) | 关键模块覆盖率 ≥ 95% | `--cov-context=test` 双阈值 |
| **TEST-028**(新增) | conftest.py 分层无循环导入 | import-linter 规则 `ST-A2A-CONFTEST` |

**L3-1 §8 新增 3 ID**(TEST-026/027/028),完整继承 25 ID,**§8 测试 ID 总计 28 ID**。

### 8.8 工具链与部署形态文件清单（pyproject + uv workspace + Dockerfile + Helm chart 顶层）

> 本节把 L2-2 Spec §13 的工具链与部署形态落地为 **4 工程配置文件 + uv workspace 根配置 + Helm chart 顶层 4 文件** 的具体路径契约。所有路径、版本约束、镜像 tag 属于 v0.1 部署 contract;新增/修改必须走 ADR。

| 文件 | 路径(基于 uv workspace) | 必须提供 | L2-2 Spec 对应 | 关联测试 ID |
|------|--------------------------|----------|-----------------|--------------|
| Operator 包 `pyproject.toml` | `packages/operator/pyproject.toml` | PEP 621 metadata + 依赖列表 + `[project.scripts]` | §13.2 | TOOL-001~004 |
| Operator 包 `uv.lock`(根锁) | `uv.lock`(仓库根) | uv lockfile,CI 与本地 lock 一致 | §13.3 | TOOL-013 |
| Operator `Dockerfile` | `packages/operator/Dockerfile` | 多阶段构建 builder + runtime | §13.4 | TOOL-004/007/031 |
| Operator 入口 `__main__.py` | `packages/operator/src/superteam_a2a/operator/__main__.py` | `python -m superteam_a2a.operator` 调用 `OperatorMain.run()` | §13.1 | TOOL-001 |
| Helm chart `Chart.yaml` | `deploy/helm/operator/Chart.yaml` | Helm chart 元信息(apiVersion v2) | §13.6 | TOOL-010/016 |
| Helm 默认 `values.yaml` | `deploy/helm/operator/values.yaml` | 默认 values,严格校验 | §9.1 + §13.6 | TOOL-019 |
| Helm `values.schema.json` | `deploy/helm/operator/values.schema.json` | 自动生成,与 Pydantic 对齐 | §9.1 + §13.6 | TOOL-019 |
| Helm `templates/deployment.yaml` | `deploy/helm/operator/templates/deployment.yaml` | Operator + admission webhook Deployment | §7.2.2 + §13.1 | HELM-DEPLOY-001~010 |
| Helm `templates/service.yaml` | `deploy/helm/operator/templates/service.yaml` | metrics + admission webhook Service 双端口 | §7.2.4 + §13.1 | HELM-013 |
| Helm `templates/serviceaccount.yaml` | `deploy/helm/operator/templates/serviceaccount.yaml` | cert-manager annotation | §7.2.5 + §13.1 | HELM-014 |
| Helm `templates/clusterrole.yaml` | `deploy/helm/operator/templates/clusterrole.yaml` | 7 apiGroups 完整 ClusterRole | §7.3.1 | RBAC-001~010 |
| Helm `templates/clusterrolebinding.yaml` | `deploy/helm/operator/templates/clusterrolebinding.yaml` | ClusterRoleBinding | §7.3.1 | RBAC-001 |
| Helm `templates/role.yaml` | `deploy/helm/operator/templates/role.yaml` | namespace-scoped Role(secrets only) | §7.3.2 | RBAC-006~008 |
| Helm `templates/rolebinding.yaml` | `deploy/helm/operator/templates/rolebinding.yaml` | RoleBinding | §7.3.2 | RBAC-006 |
| Helm `templates/webhookconfig.yaml` | `deploy/helm/operator/templates/webhookconfig.yaml` | ValidatingWebhookConfiguration(failurePolicy: Fail) | §4 + §13.1 | HELM-015~016 |
| Helm `templates/networkpolicy.yaml` | `deploy/helm/operator/templates/networkpolicy.yaml` | ingress API Server + egress K8s API + OTLP + DNS | §7.2.7 + §13.1 | HELM-017~020 |
| Helm `templates/prometheusrule.yaml` | `deploy/helm/operator/templates/prometheusrule.yaml` | 6 告警规则 | §7.2.8 | HELM-029~032 |
| Helm `templates/servicemonitor.yaml` | `deploy/helm/operator/templates/servicemonitor.yaml` | 11+4 指标 scrape | §7.2.9 + §13.1 | HELM-021~024 |
| Helm `templates/leader_election_lease.yaml` | `deploy/helm/operator/templates/leader_election_lease.yaml` | Lease 资源(可选,leaderElection.enabled=true 时渲染) | §5 + §13.1 | TOOL-028 |
| 仓库根 `pyproject.toml` | `pyproject.toml` | uv workspace + `[tool.uv.workspace]` members | §13.3 | TOOL-013 |
| `.github/workflows/lint.yml` | `.github/workflows/lint.yml` | ruff + pyright + bandit + pip-audit + interrogate 5 gate | §13.2 | TEST-009 |
| `.github/workflows/test.yml` | `.github/workflows/test.yml` | pytest + coverage + envtest | §13.6 | TEST-012 |
| `.github/workflows/e2e.yml` | `.github/workflows/e2e.yml` | kind cluster + E2E + conformance | §12.4 | TEST-019/022 |
| `.github/workflows/release.yml` | `.github/workflows/release.yml` | docker buildx + helm package + cosign(可选) | §13.8 | TOOL-031 |
| `.dockerignore` | `packages/operator/.dockerignore` | 排除 tests/ + docs/ + .git/ | §13.4 | TOOL-007 |

**总计 25 个工程资产**(L3-1 §8 文件清单:Operator 包 4 + Helm chart 顶层 4 + Helm templates 10 + 仓库根 + CI 4 + .dockerignore = **25 工程资产**)。

### 8.9 pyproject.toml 关键字段契约（继承 L2-2 §13.2）

```toml
# packages/operator/pyproject.toml
[project]
name = "superteam-a2a-operator"
version = "0.2.0"
description = "superteam-a2a Operator Core — 4 CRD lifecycle + admission + Leader Election + MemoryReconciler"
requires-python = ">=3.12,<3.13"
license = { text = "Apache-2.0" }
authors = [{ name = "CoderZhangfujiang" }]
dependencies = [
    "kopf>=1.37",                                      # Operator framework (Kopf handlers)
    "kubernetes-asyncio>=30.0",                        # K8s 异步客户端
    "pydantic>=2.6",                                   # CRD 模型 + Helm values 校验
    "prometheus-client>=0.20",                         # 11+4 Operator 指标
    "structlog>=24.1",                                 # 8 字段 JSON 日志
    "opentelemetry-api>=1.24",                         # OTel API
    "opentelemetry-sdk>=1.24",                         # OTel SDK
    "opentelemetry-exporter-otlp-proto-grpc>=1.24",    # OTLP gRPC exporter
    "anyio>=4.3",                                      # async 抽象层
    "httpx>=0.27",                                     # OTLP HTTP exporter + K8s client
    "tenacity>=8.2",                                   # 重试策略
    "uvloop>=0.19; sys_platform == 'linux'",           # Linux uvloop 加速(可选)
]

[project.optional-dependencies.dev]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "pytest-mock>=3.12",
    "hypothesis>=6.100",
    "respx>=0.21",
    "ruff>=0.4",
    "pyright>=1.1.350",
    "bandit>=1.7",
    "pip-audit>=2.7",
    "interrogate>=1.7",
    "import-linter>=2.0",
]

[project.scripts]
superteam-a2a-operator = "superteam_a2a.operator.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/superteam_a2a"]
```

**约束**(继承 L2-2 §13.2):

- `requires-python` 锁定 `>=3.12,<3.13`(TOOL-001);ADR-0005 §2.2 允许的 Python 3.12+ 视为最低版本。
- 运行时依赖只能新增 Python 生态库;引入第二核心语言(Go / Rust / C++ 扩展)必须走 ADR。
- `[project.optional-dependencies.dev]` 仅用于本地开发;**禁止**进入运行时镜像(由 Dockerfile 多阶段保证,TOOL-004)。
- `dependencies` 中所有库必须有 SPDX 兼容 license(与宪法 §3.8 一致)。
- `version` 字段必须与 `Chart.yaml` 的 `appVersion` 同步;CI 中使用脚本验证 `pyproject.__version__ == chart.appVersion`(TOOL-010)。

### 8.10 uv workspace 集成（继承 L2-2 §13.3）

`superteam-a2a` 在仓库根使用 uv workspace 统一管理多包:

```toml
# pyproject.toml(仓库根)
[tool.uv.workspace]
members = [
    "packages/operator",                  # 本 L3-1 Spec 落地的核心包
    "packages/a2a-core",                  # L3-2 A2A Core Library(v0.1-draft Go baseline 已归档)
    "packages/adapter-sdk",               # L3-3 Adapter SDK(v0.2-draft)
    "packages/knowledge-service",         # L3-5 Knowledge Service(待起草)
    "packages/memory-backend",            # L3-6 Memory backend(待起草)
    "packages/hello-agent",               # L4 实施启动后第一个 hello-agent 镜像
]
```

**约束**(继承 L2-2 §13.3):

- 仓库根 `pyproject.toml` 必须包含 `[tool.uv.workspace]`;`packages/operator` 必须在 `members` 列表中(TOOL-013)。
- `uv lock` 在仓库根执行;Operator 包的 `uv.lock` 不再单独存在。
- 跨包导入遵循 L3-1 §2.2 边界规则;CI 通过自定义 Ruff 规则 `ST-A2A-BOUNDARY` 强制(TOOL-034)。
- 单包构建:`uv build --package superteam-a2a-operator`,产物 `dist/superteam_a2a_operator-0.2.0-*.whl`。

### 8.11 Dockerfile（多阶段 · 非 root · 继承 L2-2 §13.4）

```dockerfile
# syntax=docker/dockerfile:1.7
# packages/operator/Dockerfile

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
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/healthz', timeout=2).raise_for_status()"
```

**契约**(继承 L2-2 §13.4):

- runtime 阶段**禁止**包含 `gcc` / `git` / `pip` / `uv`;只能保留 `python` 可执行文件和 stdlib + 安装的 wheels(TOOL-004)。CI 使用 `docker history` 校验 layer 数。
- 非 root 用户固定 `uid=65532` / `gid=65532`(TOOL-007);Linux capabilities 必须 `drop=["ALL"]` + 仅 `add=["NET_BIND_SERVICE"]`(8443 < 1024 时需要)。
- 镜像 base 固定 `python:3.12-slim`;不得使用 `latest` 或非 slim tag。
- 镜像必须包含 `HEALTHCHECK`(与 §7.1.2 health.py 一致);CI 使用 `docker inspect` 校验存在。
- 镜像 tag 与 `pyproject.version` + `Chart.appVersion` 三方一致;CI 校验三处相等(TOOL-010)。
- 多架构(`linux/amd64` + `linux/arm64`)在 v0.1 不强制;v0.5+ 启动(TOOL-031);CI 必须记录基线架构(`linux/amd64`)。

### 8.12 Deployment 探针与生命周期（继承 L2-2 §13.5）

- `livenessProbe`:`httpGet /healthz` 端口 8080;`initialDelaySeconds=30`,`periodSeconds=10`,`timeoutSeconds=3`,`failureThreshold=3`(TOOL-022)。
- `readinessProbe`:`httpGet /readyz` 端口 8080;`initialDelaySeconds=5`,`periodSeconds=5`,`timeoutSeconds=2`,`failureThreshold=2`(TOOL-025)。
- `/healthz`:liveness 端点,**必须在 Leader Election 初始化前**就绪;返回 200 当且仅当进程未僵死(TOOL-022 + §7.1.2 health.py `HLT-001~003`)。
- `/readyz`:readiness 端点,**必须在 Lease 初始化 + admission webhook 启动之后**才返回 200(TOOL-025 + `HLT-005~006`);**非 leader 副本 `/readyz` 也必须 200**(因为 admission webhook 在所有副本上可用,E2E-014 验证)。
- `/metrics`:端口 8080,路径 `/metrics`;不得启用 basic auth(由 ServiceMonitor 自行控制,§7.2.9 servicemonitor.yaml)。
- 资源 requests / limits 由 §7.2.3 Helm values `controllers.resources` 控制;`requests.cpu=200m`、`requests.memory=256Mi`、`limits.cpu=1000m`、`limits.memory=1Gi` 是 v0.2 默认(HELM-008~009)。
- `replicaCount` 默认 2;Operator 副本**必须**部署在不同的 K8s 节点(`topologySpreadConstraints` 或 `podAntiAffinity` 推荐软约束;v0.1 不强制)。

### 8.13 Helm chart 关键字段（继承 L2-2 §13.6）

```yaml
# deploy/helm/operator/Chart.yaml
apiVersion: v2
name: superteam-a2a-operator
description: superteam-a2a Operator Core — 4 CRD lifecycle + admission + Leader Election + MemoryReconciler
type: application
version: 0.2.0      # chart 自身版本(独立于 appVersion)
appVersion: "0.2.0" # 与 packages/operator/pyproject.toml [project].version 同步(TOOL-010)
kubeVersion: ">=1.27, <1.32"  # envtest 验证范围;v0.2 锁定(TOOL-016)
home: https://github.com/CoderZhangfujiang/superteam-a2a
sources:
  - https://github.com/CoderZhangfujiang/superteam-a2a
maintainers:
  - name: CoderZhangfujiang
    email: bot@superteam-a2a.local
keywords:
  - a2a
  - multi-agent
  - kubernetes-operator
```

**契约**(继承 L2-2 §13.6):

- `apiVersion: v2` + `name: superteam-a2a-operator` + `type: application`;`version: 0.2.0`(chart 自身版本,独立于 appVersion)(TOOL-016)。
- `appVersion` 必须等于 `pyproject.__version__`;CI 失败时阻塞 release(TOOL-010,`tests/tools/test_chart_version_sync.py`)。
- `kubeVersion` 约束 `>=1.27, <1.32`(envtest 验证范围;v0.2 锁定)。
- 依赖 chart:暂不依赖外部 chart(cert-manager 由用户集群预装,§7.2.5 serviceaccount.yaml cert-manager annotation)。
- `values.yaml` 必须可被 §7.2.3 `HelmValues` Pydantic 模型严格校验(TOOL-019);CI `helm lint` + `helm template` 双重验证(`tests/integration/helm/test_chart_lint.py` + `test_values_schema.py`)。
- `templates/` 渲染必须满足:`Deployment` + `Service` + `ServiceAccount` + `ClusterRole` + `ClusterRoleBinding` + `Role` + `RoleBinding` + `ValidatingWebhookConfiguration` + 可选 `Lease` + `NetworkPolicy` + `PrometheusRule` + `ServiceMonitor`(§7.2 9 模板完整继承 + §13.1 leader_election_lease.yaml 可选 = 10 模板 + chart 顶层 4 文件 = 14 文件)。
- `NOTES.txt` 必须说明获取 Operator pod 名 + 验证 admission webhook 已注册的 `kubectl get validatingwebhookconfigurations` 命令(§7.2 占位)。

### 8.14 部署时序（继承 L2-2 §13.7）

```text
helm install → 创建 Namespace(superteam-a2a-system)
             → 创建 ServiceAccount + ClusterRoleBinding
             → 创建 Deployment(replicaCount=2)
             → 创建 ValidatingWebhookConfiguration(failurePolicy: Fail)
             → 创建 admission Role + RoleBinding(secrets only)
             → 创建 Service(双端口:8080 metrics + 8443 admission)
             → 创建 NetworkPolicy(ingress API Server + egress K8s API + OTLP + DNS)
             → 创建 PrometheusRule(6 告警)
             → 创建 ServiceMonitor(11+4 指标 scrape)
             → 创建可选 Lease(leaderElection.enabled=true)

Pod 启动:
  pre-hook     → 镜像 pull + 探针端口暴露
  entrypoint   → superteam-a2a-operator
                 ├─ 解析 Helm values(Pydantic §7.2.3)
                 ├─ 初始化 K8s async client(kubernetes_asyncio)
                 ├─ 初始化 OTel + structlog(observability/tracing.py + logging.py)
                 ├─ 启动 admission webhook(8443 / TLS · admission/server.py)
                 ├─ 启动 metrics server(8080 · observability/metrics.py)
                 ├─ /healthz 立即返回 200(TOOL-022)
                 ├─ 启动 Leader Election task(leader_election/election.py)
                 ├─ /readyz 在 Lease acquire + webhook 就绪后返回 200(TOOL-025)
                 └─ Kopf 处理 CRD watch(controllers/agent.py 等 4 Controller)
```

**关键不变量**(继承 L2-2 §13.7):

- admission webhook 必须在 `/readyz` 返回 200**之前**完成 TLS 加载 + ValidatingWebhookConfiguration 注册;否则 API Server 无法调用 webhook → CRD 写入失败(TOOL-025 + `HLT-005`)。
- 副本之间无强启动顺序;非 leader 副本会重复尝试 acquire Lease,全部就绪后由 Lease 决定唯一 leader(E2E-014 验证)。
- 删除 chart 顺序:先 `kubectl delete validatingwebhookconfigurations`(避免 webhook 阻止 Finalizer cleanup,TOOL-028)→ `helm uninstall` → 残留资源(CRD / CR)由用户决策。
- 升级期间:Helm `pre-upgrade` hook 仅打印「确认所有副本已就绪」日志;v0.1 不执行 webhooks conversion(L3-1 移交问题)。

### 8.15 镜像分发与版本（继承 L2-2 §13.8）

- **镜像仓库**:默认 `ghcr.io/coderzhangfujiang/superteam-a2a-operator`。
- **Tag 规则**:`<version>`(如 `0.2.0`)、`latest`(仅 main 分支)、`<version>-dev.<short-sha>`(PR build,如 `0.2.0-dev.a1b2c3d`)。
- **多架构**:v0.1 仅 `linux/amd64`;v0.5+ 启动 `linux/arm64`(TOOL-031)。
- **签名**:v0.5+ 引入 `cosign` keyless 签名(sigstore);v0.1 记录为开放问题(移交 L3-1 §10)。
- **SBOM**:v0.5+ 使用 `syft` 生成 CycloneDX SBOM;v0.1 移交 L3-1 §10。

### 8.16 关键不变量与测试 ID 矩阵（TOOL- 前缀 · 继承 L2-2 §13.9）

继承 L2-2 Spec §13.9 所有 TOOL- ID(完整继承 34 个,无修改无新增;L3-1 落地为具体文件路径 + 新增少量 ID):

| 测试 ID | 描述 | L3-1 落地位置 |
|---------|------|---------------|
| `TOOL-001` | `pyproject.requires-python` 锁定 `>=3.12,<3.13` | `packages/operator/pyproject.toml` [project].requires-python |
| `TOOL-004` | runtime 镜像不含 `pip` / `uv` / `git` / `gcc` | `packages/operator/Dockerfile` + CI `docker history` 校验 |
| `TOOL-007` | 镜像 user 固定 `uid=65532` | `packages/operator/Dockerfile` USER 65532:65532 |
| `TOOL-010` | `pyproject.version` == `Chart.appVersion`(CI 校验) | `tests/tools/test_chart_version_sync.py` |
| `TOOL-013` | `uv lock --check` 在 CI 中无差异 | `tests/tools/test_lock_check.py` + CI workflow |
| `TOOL-016` | `helm template` 无 warning,`helm lint` 通过 | `tests/integration/helm/test_chart_lint.py` |
| `TOOL-019` | `values.schema.json` 与 `HelmValues.model_json_schema(by_alias=True)` 无差异 | `tests/integration/helm/test_values_schema.py` |
| `TOOL-022` | `/healthz` 在 Leader Election 初始化前返回 200 | `tests/integration/envtest/test_concurrent_election.py` + `tests/e2e/kind/test_health_probe.py` E2E-016 |
| `TOOL-025` | `/readyz` 在 admission webhook + Lease 初始化**之后**才返回 200 | `tests/integration/admission/test_webhook_registration.py` + E2E-017 |
| `TOOL-028` | 删除 chart 时 ValidatingWebhookConfiguration 优先清理(hooks 顺序) | `tests/integration/helm/test_chart_lint.py` + NOTES.txt 说明 |
| `TOOL-031` | 镜像 manifest 仅包含 `linux/amd64`(v0.1 基线) | `tests/tools/test_chart_version_sync.py` + `docker buildx inspect` |
| `TOOL-034` | cross-package boundary Ruff 规则 `ST-A2A-BOUNDARY` 在 CI 中通过 | `.github/workflows/lint.yml` + `pyproject.toml [tool.ruff.lint-extend-select]` |
| **TOOL-035**(新增) | Dockerfile HEALTHCHECK 指令存在且 timeout 合理(≤ 5s) | `tests/tools/test_dockerfile_healthcheck.py` + `docker inspect` |
| **TOOL-036**(新增) | Operator 镜像无 `HEALTHCHECK` 时 CI 失败 | CI workflow `lint.yml` Dockerfile 静态扫描 |

**L3-1 §8 新增 2 ID**(TOOL-035/036),完整继承 34 ID,**§8 工具链测试 ID 总计 36 ID**。

### 8.17 与既有 L2 Spec 测试 ID 对应（59 ID TEST+TOOL）

- **L2-2 Spec §12.7** 提供 TEST-001~025 = **25 ID** → L3-1 **完整继承** 无修改,落地为 87 个 test_*.py + 4 CI workflow + 1 pytest plugin(`pytest_supertem.py`);
- **L2-2 Spec §13.9** 提供 TOOL-001~034 = **34 ID** → L3-1 **完整继承** 无修改,落地为 pyproject.toml + Dockerfile + Helm chart 顶层 4 文件 + uv workspace 根 pyproject.toml + 4 CI workflow + 2 tools test;
- 本 §8 新增 **5 ID**(TEST-026~028 + TOOL-035~036)用于强化 L3-1 自身的镜像覆盖 + Dockerfile HEALTHCHECK gate;
- **本节新增/继承测试 ID 总计** = **28 (TEST) + 36 (TOOL) = 64 ID**,覆盖 §A-§G 6 维度。

### 8.18 与 L3-1 §0-§7 衔接

- **§1.3 文件清单**:§8 新增 25 工程资产 + 50 测试夹具 = **75 文件** 新增到 §1.3 主清单;落地后 L3-1 文件清单 **87 → 162**(87 src + 25 工程 + 50 顶层测试 = 162);
- **§2.3 Python 包结构**:§8.9 pyproject.toml 锁定依赖与 Python 版本约束,落地 §2.3.13 build / install / test 工具链;
- **§3 3 个 CRD Controller + MemoryReconciler 概要**:`tests/unit/controllers/test_*.py` 与 `tests/unit/reconcilers/test_*.py` 1:1 镜像;
- **§4 admission webhook**:§8.1 admission/ 子目录镜像 + §8.3 IT-AW-* 集成测试 + §8.13 webhookconfig.yaml 契约;
- **§5 Leader Election**:§8.1 leader_election/ 子目录镜像 + §8.3 IT-ENV-CE-* 多副本并发集成 + TOOL-022/025 探针契约;
- **§6 Memory**:§8.1 memory/ 子目录镜像(decay/reinforce 属性测试 TEST-007)+ §8.3 IT-ENV-MT-* MemoryReconciler timer 集成;
- **§7 observability + RBAC + Helm values**:§8.1 observability/ 子目录镜像 + §8.13 Helm chart 顶层 4 文件 + §8.11 Dockerfile + TOOL-035/036 HEALTHCHECK gate。

**结论**:**§8 是 §3-§7 实施工程的物理落地**(测试镜像 + 工程配置 + Helm chart 顶层),所有引用点的契约均集中在本节给出。L3-1 累计 **277 测试 ID**(§0-§7 共 218 ID + §8 新增/继承 64 ID,减 §8 测试 ID 5 自身),覆盖 §A-§G 6 维度。

---

## 9. 验收清单（v0.2-draft-full 完整版 · L3-1 文件级 Spec 升级 v0.2.0 凭证）

> ✅ **本节为 v0.2-draft-full 完整版**——在 L2-2 Spec v0.2.0 §14 验收清单基础上,**叠加 L3-1 文件级落地的具体验收点**(每个验收点对应 L3-1 §X.Y 文件路径 + 测试 ID),形成 L3-1 Spec 升级 v0.2.0 前的可勾选验收基线。
>
> 本节是 L3-1 Spec 升级 v0.2.0 前的**唯一凭证**;L3-1 Spec 评审(§A-§G 10 维度)必须以本清单为基线,**任何未勾选项必须解释**或推迟到 v0.2.1 / v0.5 路线图中(ACCEPT-013)。

### 9.1 评审维度验收（§A-§G 10 项 · 文件级落地）

| 维度 | 验收点 | 对应位置(L3-1) | 勾选 |
|------|--------|------------------|------|
| **A. 文档完整性** | §0-§10 + 附录 A/B 全部存在,**0 个 TODO/待补完标记**(仅占位符可保留) | 本 Spec 全文 | ☐ |
| | 头部包含版本/状态/supersede/依据/上游约束/配套 Spec 6 段 | 头部 frontmatter | ☐ |
| | supersede 指针指向 L3-1 v0.1-draft Go baseline 归档 | 头部 supersede 段 | ☐ |
| | §1.3 文件清单(70 → 162 文件)与 §2-§8 落地一致 | §1.3 + §2.3 + §3-§8 | ☐ |
| | §A 跨模块引用 + §B ADR/Constitution 矩阵 5 子表 | 附录 A + 附录 B | ☐ |
| **B. 设计深度** | 4 Controllers + admission + Leader Election + Finalizer + Memory + observability + RBAC + Helm + 测试策略 + 工具链 **10 子模块全覆盖** | §3-§8 主体 | ☐ |
| | Pydantic schema 在 §3 + §6 + §7 + §8.9 全部展开 | §3.1 / §6 / §7.2.3 / §8.9 | ☐ |
| | 每个 `*.py` 文件列明 **绝对路径 + 职责一句话 + import 列表 + exported 符号签名 + helper 列表 + 关联测试文件** | §3-§8 每个文件段 | ☐ |
| | §7.4 wire contract 总览 ~52 字段 + §7.5 测试 ID 矩阵 + §7.6 衔接段 | §7.4-§7.6 | ☐ |
| | §8.1 测试目录镜像布局(87 src → 87 test_*.py) | §8.1 树形目录 | ☐ |
| | §8.18 与 L3-1 §0-§7 衔接矩阵 | §8.18 | ☐ |
| **C. 宪法一致性** | §3.8 Python-first 强制通过所有 `import` 边界(import-linter ST-A2A-BOUNDARY) | §2.2 + §8.6 + §8.10 TOOL-034 | ☐ |
| | §6 mTLS 通过 cert-manager 集成(§7.2.5 ServiceAccount annotation + §8.3 IT-AW-MT-001~003) | §7.2.5 + §8.3 | ☐ |
| | §7 可观测性 11 指标 + 4 Python runtime 指标 + structlog 8 字段 + OTel + K8s Events **全覆盖无例外** | §7.1.2 + §7.1.4 + §7.1.5 | ☐ |
| | §9.4 静态质量门禁(`ruff` + `pyright --strict` + `bandit` + `pip-audit` + `interrogate` 5 重 gate) | §8.2 + §8.6 TEST-009/011 | ☐ |
| | §14.4 评审门禁:**10 维度** + 验收清单(本 §9)+ 评审报告 | §9.1 + §9.5 + 评审文件 | ☐ |
| | §15.5 质量红线:**测试覆盖率 ≥ 80%**(`pytest --cov-fail-under=80` + 关键模块 ≥ 95%) | §8.2 TEST-005/012 + §8.6 TEST-027 | ☐ |
| | §16 会话纪律:本 Spec 由 **5 个独立会话**(#44 骨架 + #45 §4-§6 + #47 §7 + #48 §8 + #49 §9)补完 | MEMORY 索引 + commit 历史 | ☐ |
| **D. 依赖方向** | Operator 不依赖 L2-3 Adapter SDK(`import-linter` ST-A2A-BOUNDARY 强制) | §2.2 + §8.10 TOOL-034 | ☐ |
| | Operator 不实现 A2A 协议(仅调用 a2a-core client) | §2.2 + §3.1 + 附录 A.2 | ☐ |
| | Operator 不实现 Knowledge/Memory 业务语义(仅 CRD lifecycle) | §2.2 + §6(仅接口契约) | ☐ |
| | admission webhook 不调用 K8s API(纯函数校验) | §2.2 + §4 + §8.3 IT-AW-* | ☐ |
| | Reconciler services 不依赖 Kopf(可独立单测) | §2.2 + §3 + §8.1 reconcilers/ | ☐ |
| | Leader Election 与 admission webhook 解耦(不同模块) | §5 + §4 | ☐ |
| **E. 性能约束** | Helm `python.workers: 1` 强制(单进程原则,ADR-0005 §6.2) | §7.2.3 + §8.13 HELM-008 | ☐ |
| | K8s Lease 30s TTL + 10s 续约 + 3 次失败让位 + grace period 30s | §5.2 + §8.12 TOOL-022/025 | ☐ |
| | MemoryReconciler `@kopf.timer(interval=60.0)` + CPU offload 阈值 1000 | §6.3 + §7.2.3 | ☐ |
| | 11 Operator 指标 + 4 Python runtime 指标(OBS-001~025 + runtime OBS-016~019) | §7.1.2 + §8.7 OBS-* | ☐ |
| | `/healthz` 启动延迟 < 50ms(E2E-016)+ `/readyz` 在 webhook + Lease 后 200 | §7.1.2 + §8.12 TOOL-022/025 | ☐ |
| | Operator 镜像 manifest 仅 `linux/amd64`(v0.1 基线) | §8.11 + §8.15 TOOL-031 | ☐ |
| **F. 跨文档一致性** | 与 L1 v0.2.0 + L2-1 v0.2.0 + L2-3 v0.2.0 + L2-4 v0.2.0 同步 | §F 同步记录(本 §9.4) | ☐ |
| | L1 Architecture §3.2 编排层 + §4.1 C-1 Operator 模块映射正确 | §1.1 + 附录 A.1 | ☐ |
| | L1 Spec §2/§3/§4 CRD Agent/AgentSet/Workflow spec + §7 状态机 + §16 指标 一致 | §3.1-§3.4 + §7.1.2 | ☐ |
| | L2-1 A2A Spec §2.5 (client) + §8.4 11 错误码字节级一致 | §8.5 CONFORMANCE-001~013 | ☐ |
| | L2-4 Knowledge/Memory Spec §3.4 Memory CRD wire sync 矩阵 19 字段全 PASS | §6.3 + §8.5 CONFORMANCE-013 | ☐ |
| | ADR-0002(Knowledge 4 级作用域)+ ADR-0003(Memory decay/reinforce)+ ADR-0005(Python-first supersede)字段约束一致 | 全文 + 附录 A.3 | ☐ |
| | 宪法 v0.5.0 + ADR-0005 supersede 指针(头部 + 附录 A.4) | 头部 + 附录 A | ☐ |
| | ROADMAP Phase 1.5 L3 进度同步(~85% → v0.2.0) | §F + ROADMAP.md | ☐ |
| **G. Python-first** | Kopf + kubernetes_asyncio + Pydantic v2 + structlog + OTel + cert-manager + uvloop(Linux 可选) | §8.9 dependencies | ☐ |
| | 11 个运行时依赖无第二核心语言(Go/Rust/C++ 扩展) | §8.9 dependencies | ☐ |
| | Dockerfile runtime 仅 `python:3.12-slim` + uid=65532 + HEALTHCHECK | §8.11 + TOOL-004/007/035 | ☐ |
| | cross-package boundary Ruff 规则 `ST-A2A-BOUNDARY` 在 CI 通过 | §8.10 + §8.6 TOOL-034 | ☐ |
| | conftest 分层 import-linter 规则 `ST-A2A-CONFTEST` 无循环导入 | §8.6 TEST-028 | ☐ |
| | L3-1 累计 **277 测试 ID** 全部映射到具体 `*.py` 文件路径 | §9.2 + §3-§8 文件段 | ☐ |

### 9.2 测试 ID 验收（277 个 ID 全覆盖 · 文件级映射）

> L3-1 累计 **277 测试 ID**(§0-§8 全 Spec 范围),分组映射到具体 `*.py` 文件路径或 IT/E2E 用例。所有 ID 在评审报告中以 §X.Y 行号引用。

| 前缀 + 数量 | 含义 | L3-1 落地章节 | 测试文件镜像 |
|--------------|------|---------------|--------------|
| **TEST-001~025**(25)+ **TEST-026~028**(3 新增)= **28** | 测试策略门禁 | §8.2 + §8.6 + §8.7 | `tests/conftest.py` + CI workflow + `pytest_supertem.py` plugin |
| **TOOL-001~034**(34)+ **TOOL-035/036**(2 新增)= **36** | 工具链与部署 | §8.9-§8.16 + §8.10 | `pyproject.toml` + `Dockerfile` + `Chart.yaml` + CI workflow + `tests/tools/` |
| **OBS-001~025**(25) | 11 Operator 指标 + 4 Python runtime 指标 + 4 tracing + 2 logging + 5 events | §7.1.2-§7.1.5 | `tests/unit/observability/test_metrics.py` + `test_tracing.py` + `test_logging.py` + `test_events.py` |
| **HLT-001~008**(8) | `/healthz` + `/readyz` + Lease + MemoryReconciler last_run | §7.1.3 | `tests/unit/observability/test_health.py` |
| **HELM-001~032**(32)+ **HELM-DEPLOY-001~010**(10)= **落地 29** | Helm values Pydantic + 9 模板 + deployment probes | §7.2 + §8.13 | `tests/unit/config/test_helm_values.py` + `tests/integration/helm/test_chart_lint.py` |
| **RBAC-001~010**(10)+ **RBAC-IT-001~004**(4)= **14** | ClusterRole 7 apiGroups + admission Role namespace-scoped + envtest apply | §7.3 + §8.3 | `tests/unit/rbac/*` + `tests/integration/helm/test_rbac_apply.py` |
| **LE-001~024**(24) | Leader Election:AsyncLeaseClient 8 + Election 12 + Controller gate 4 | §5.5 | `tests/unit/leader_election/test_lease_client.py` + `test_election.py` + `tests/integration/envtest/test_concurrent_election.py` |
| **ASYNC-001~012**(12) | async 边界 + CPU offload + MemoryReconciler timer | §6.3 + §6.5 | `tests/unit/reconcilers/test_memory_reconciler_service.py` + `tests/integration/envtest/test_memory_timer.py` |
| **FIN-001~FIN-032**(32) | Finalizer 4 名称映射 + 4 CRD cleanup 流程 + 错误路径 | §1.4 + §3 + §7.3 | `tests/unit/finalizers/test_names.py` + `tests/integration/envtest/test_finalizer_cleanup.py` |
| **ERR-001~ERR-027**(27) | 错误模型 + 分类矩阵 + wrapper + 边界 | §8 + §1.4 | `tests/unit/errors/test_errors.py` |
| **UT-C-A/AS/W/M**(30) | 4 Controller handler 测试 + MemoryReconciler Controller | §3.1-§3.5 | `tests/unit/controllers/test_agent.py` + `test_agentset.py` + `test_workflow.py` + `test_memory_reconciler_controller.py` |
| **UT-R-B/A/AS/W/M**(25) | 业务 reconciler services(Base + 4 CRD) | §3 + §6.3 | `tests/unit/reconcilers/test_base.py` + `test_agent_reconciler.py` + `test_agentset_reconciler.py` + `test_workflow_reconciler.py` + `test_memory_reconciler_service.py` |
| **UT-AW-S/T/BV/AV/ASV/WV/MV/ME**(27) | admission webhook server + 5 validators + mutual_exclusion | §4 + §8.1 | `tests/unit/admission/test_server.py` + `test_tls.py` + `test_*_validator.py` + `test_mutual_exclusion.py` |
| **UT-MD-***(Agent/AgentSet/Workflow/Memory 4 CRD × ~8 文件)= **~30** | CRD 实体 Pydantic models(spec/status/conditions/enums/decay/reinforce/gc/promotion) | §2.3.12 + §6.2 | `tests/unit/models/{agent,agentset,workflow,memory}/test_*.py` |
| **UT-OP-01~14**(14) | 顶层 operator/(main + internals + __init__ + __main__) | §2.3.1 | `tests/unit/operator/test_main.py` + `test___init__.py` + `test___internals.py` + `test___main__.py` |
| **UT-LE-LC/EL**(10) | K8s Lease 客户端 + Election 主类 | §5 | `tests/unit/leader_election/test_lease_client.py` + `test_election.py` |
| **UT-KC-01~07**(7) | AsyncK8sClient kubernetes_asyncio 封装 | §2.3.7 | `tests/unit/clients/test_k8s_client.py` |
| **UT-CF-01~04**(4) | Helm values Pydantic | §7.2.3 | `tests/unit/config/test_helm_values.py` |
| **IT-ENV-***(envtest 集成 ~15) | 4 CRD 完整生命周期 + Finalizer cleanup + Memory timer + 多副本并发 | §8.3 | `tests/integration/envtest/test_*.py` |
| **IT-AW-***(admission 集成 ~10) | ValidatingWebhookConfiguration + mTLS rotation + 互斥拒绝 | §8.3 | `tests/integration/admission/test_*.py` |
| **E2E-001~010**(10 继承)+ **E2E-011~020**(10 新增)= **20** | kind 集群 E2E 20 场景 | §8.4 | `tests/e2e/kind/test_*.py` |
| **CONFORMANCE-001~013**(13) | 4 项目扩展 A2A method + 11 错误码 + 3 L3-1 新增 | §8.5 | `tests/e2e/conformance/test_a2a_wire_contract.py` + `test_memory_wire.py` |
| **PERF-001~005**(5,全部 `@pytest.mark.skip`) | 性能测试 v0.1 占位 | §8.1 perf/ | `tests/perf/test_reconcile_throughput.py` |

**合计 ≈ 277 ID**(精确数量由 §8.1 树形目录的 `test_*.py` 文件数 + `tests/integration/` + `tests/e2e/` + 测试 ID 前缀计数核验;CI 实际注册 ID 数量与上表一致即可,允许 ±5 容差)。

### 9.3 部署与文档交付验收

| # | 验收点 | 对应位置 | 勾选 |
|---|--------|----------|------|
| 1 | 11 个 Operator 指标 + 4 Python runtime 指标全量暴露(`/metrics` 路径,scrape interval 30s) | §7.1.2 + §8.13 HELM-021~024 + E2E-010 | ☐ |
| 2 | 8 个 EventReason 在代码与文档严格匹配(AdmissionRejected / LeaderAcquired / LeaderLost / MemoryDecayed / MemoryReinforced / CleanupCompleted / CertificateNotReady / ReconciliationFailed) | §7.1.5 OBS-007 + §8.4 E2E-018 | ☐ |
| 3 | structlog 8 必含字段(timestamp / level / event / logger / agent_name / crd / trace_id / span_id)在 sample 日志中全部存在 | §7.1.4 OBS-010 + TEST-025 | ☐ |
| 4 | 4 个永久 Finalizer 名称（`agent.superteam-a2a.io/cleanup` / `agentset.superteam-a2a.io/cleanup` / `workflow.superteam-a2a.io/cleanup` / `memory.superteam-a2a.io/cleanup`）与 K8s CRD metadata.finalizers 一致 | §1.4 + §2.3.7 + FIN-001~004 | ☐ |
| 5 | `pyproject.version` == `Chart.appVersion`(CI 校验 `tests/tools/test_chart_version_sync.py`) | §8.16 TOOL-010 | ☐ |
| 6 | `values.schema.json` 与 `HelmValues.model_json_schema(by_alias=True)` 无差异 | §8.16 TOOL-019 + `tests/integration/helm/test_values_schema.py` | ☐ |
| 7 | `helm template` 无 warning + `helm lint` 通过 | §8.16 TOOL-016 | ☐ |
| 8 | 镜像 manifest 仅 `linux/amd64`(v0.1 基线;`docker buildx inspect`) | §8.15 + §8.16 TOOL-031 | ☐ |
| 9 | `ruff check` + `pyright --strict` + `bandit -r packages/operator/src` + `pip-audit` 在 CI 通过(0 高危漏洞) | §8.6 TEST-009 | ☐ |
| 10 | `pytest --cov=superteam_a2a.operator --cov-fail-under=80` 通过 | §8.6 TEST-012 | ☐ |
| 11 | E2E 20 个 case 全部从干净 kind 集群开始(`e2e-<short-sha>-<pid>` 命名) | §8.4 + TEST-019 | ☐ |
| 12 | conformance 与 L2-1 Spec §8.4 **11 JSON-RPC 错误码**字节级一致 | §8.5 CONFORMANCE-001~010 | ☐ |
| 13 | MemoryReconciler wire sync 与 L2-4 Spec §3.4 **19 字段** 全 PASS | §6.3 + §8.5 CONFORMANCE-013 | ☐ |
| 14 | 附录 A 跨模块引用 **12 条**(L1 × 2 + L2 × 6 + ADR × 5 + Constitution × 8 + 配套 × 3)全勾选 | 附录 A | ☐ |
| 15 | 附录 B ADR/Constitution 矩阵 5 子表(架构/接口/可见性/安全/测试)全填 | 附录 B(本 §9 完成时落地) | ☐ |
| 16 | MEMORY 索引条目 #44 / #45 / #47 / #48 / #49(本会话)全部存在 | MEMORY 索引 + commit 历史 | ☐ |
| 17 | 宪法 v0.5.0 + ADR-0005 supersede 指针在头部 + 附录 A.4 完整 | 头部 + 附录 A.4 | ☐ |
| 18 | Dockerfile HEALTHCHECK 指令存在且 timeout ≤ 5s(`docker inspect`) | §8.11 + §8.16 TOOL-035/036 | ☐ |
| 19 | 非 root uid=65532 + drop ALL capabilities + NET_BIND_SERVICE(8443 < 1024) | §8.11 + TOOL-007 | ☐ |
| 20 | uv workspace 6 packages members(operator + a2a-core + adapter-sdk + knowledge-service + memory-backend + hello-agent)`uv lock --check` 无差异 | §8.10 + TOOL-013 | ☐ |

### 9.4 评审与归档验收

| # | 验收点 | 对应位置 | 勾选 |
|---|--------|----------|------|
| 1 | L3-1 Spec 评审报告 `docs/reviews/l3-1-operator-core-spec-review.md` 存在 | 评审文件 | ☐ |
| 2 | 评审报告采用 §A-§G 10 维度模板(参照 [L2-2 Spec 评审](../../reviews/l2-2-operator-core-spec-review.md) 15-25KB) | 评审文件 | ☐ |
| 3 | **Design + Spec 双文档**升级 v0.2.0(`docs/design/L2-modules/L2-operator-core.md` + `docs/spec/L3-file-specs/L3-operator-core.md`) | §F 同步记录 | ☐ |
| 4 | Go baseline v0.1-draft 归档完整(Spec 62KB/1886 行 + Design 527 行,均在 `docs/archive/pre-python-2026-07-24/`) | archive/README.md | ☐ |
| 5 | L1 Architecture + L1 Spec 跨文档同步标记(`l3-1-supersede` 指针 + §3.2 编排层引用) | L1 文件头部 | ☐ |
| 6 | L2-1 A2A Spec + L2-3 Adapter Spec + L2-4 Knowledge Spec 跨文档同步(附录 A 引用 + L3-1 wire sync 引用) | L2 附录 A | ☐ |
| 7 | **ROADMAP.md** Phase 1.5 L3 进度同步(~85% → v0.2.0)+ L3 阶段 1/4 标记 | ROADMAP.md Phase 1.5 | ☐ |
| 8 | **README.md** + **CONSTITUTION-CHANGELOG.md** 同步标记 v0.2.0 L3-1 通过 | README + CONSTITUTION-CHANGELOG | ☐ |
| 9 | 宪法 v0.5.0 §16 纪律:会话 #44 / #45 / #47 / #48 / #49 累计水位 < 80% 临界 | MEMORY 索引 + commit diff stat | ☐ |
| 10 | L3-1 Spec 升级 v0.2.0 后,L3 阶段 1/4 完成标记(可启动 L3-2 A2A Core 重写) | ROADMAP.md Phase 1.5 | ☐ |

### 9.5 关键不变量与测试 ID（ACCEPT- 前缀）

- `ACCEPT-001`:§9.1 §A-§G **10 维度**全部勾选或显式解释(未勾选项必须在评审报告 `L3-1 Operator Core Spec Review` 附录列出推迟版本)。
- `ACCEPT-004`:§9.2 **277 个测试 ID**全部映射到具体 `*.py` 文件路径或 IT/E2E 用例(`tests/` 目录树扫描验证)。
- `ACCEPT-007`:§9.3 部署与文档交付 **20 条**全部勾选(`tests/integration/helm/test_chart_lint.py` + E2E + CI workflow 全绿验证)。
- `ACCEPT-010`:§9.4 评审与归档 **10 条**全部勾选(评审报告 + Design/Spec 升级 + ROADMAP/README/CHANGELOG 同步)。
- `ACCEPT-013`:未勾选项必须在评审报告附录列出推迟版本(v0.2.1 / v0.5 / v1.0);不允许"未勾选但无推迟版本"的情况。
- `ACCEPT-016`（L3-1 §9 新增）：L3-1 §0-§10 + 附录 A/B 全部存在，**0 个待补完章节标记**；真正属于 v0.5+ 或尚未起草的 L3-3/L3-5/L3-6 功能占位必须明确标注目标版本/模块，不得伪装成当前 Spec 缺口。
- `ACCEPT-019`(L3-1 §9 新增):conftest 分层 + import-linter 规则 `ST-A2A-CONFTEST` + `ST-A2A-BOUNDARY` 在 CI 通过(TEST-028 + TOOL-034)。
- `ACCEPT-022`(L3-1 §9 新增):L3-1 文件清单 162 文件(87 src + 25 工程 + 50 顶层测试)与 §1.3 + §8.1 树形目录一致(`find packages/operator -name "*.py" | wc -l == 87` 校验)。

**关键不变量**:验收清单是 L3-1 Spec 升级 v0.2.0 的**唯一凭证**;任何未勾选项必须附推迟版本与原因;评审报告必须引用本节行号(§9.1-§9.4 + ACCEPT-001~022);§9.3 共 20 条 + §9.4 共 10 条 = **30 条硬验收**(L3-1 §9.5 ACCEPT-007 命名规则:30 条 vs L2-2 §14 共 15 条,L3-1 文件级细化翻倍)。

---

## 10. 开放问题（三层追踪 · 25 项去重基线 · 移交 L4 / v0.5+）

> ✅ **本节为 v0.2-draft-full 完整版**。它完整继承 [L2-2 Operator Core Spec v0.2.0 §15](../../spec/L2-module-specs/L2-operator-core.md) 的 20 项，并把 [L3-1 Go baseline 附录 B](../../archive/pre-python-2026-07-24/L3-operator-core-spec-v0.1-draft-go-baseline.md) 的 7 项做去重 crosswalk：B.2 与 Q-03 重复、B.5 与 Q-01 重复，其余 5 项形成 L3-1 文件级独立决策。因此本节的**去重问题总数为 25 项**。
>
> **状态图例**：✅ 本 Spec 已给出可直接实施的最终决策 · 🟡 已给默认决策但必须在 L4 环境实测 · ⬜ 未决（阻塞评审）· 🔵 明确推迟 v0.5+。本版为 **20 ✅ + 5 🟡 + 0 ⬜**；🔵 只标注后续能力，不改变 v0.2-draft-full 可评审结论。

### 10.1 继承 L2-2 Spec §15 的 20 项

| 决策 ID | 上游项 | 问题 | L3-1 状态 | 文件级结论 / 收敛位置 |
|---|---|---|---|---|
| `OPEN-OP-001` | Q-01 | Agent > 1000 时是否 informer 分片 | ✅ | v0.2 不分片；§7.1.2 暴露 reconcile queue depth，§7.2 保留资源阈值；达到规模门槛后走 v0.5+ ADR，不在 v0.2 隐式启用 HPA |
| `OPEN-OP-002` | Q-02 | Workflow 表达式引擎 | ✅ | v0.1 仅静态 inputs；§3.3 保留 `WorkflowExpression` stub，CEL 明确推迟 v0.5+，不得提前进入 public API |
| `OPEN-OP-003` | Q-03 | Memory 衰减频率 | ✅ | 默认 60s；以 L2-2 §9.2 与本 Spec §7.2.3 的 Pydantic 约束 `ge=10, le=3600` 为权威。L2-2 §15 Q-03 的“30-300s”是同一上游文档内未同步的摘要 erratum，不覆盖字段级 schema |
| `OPEN-OP-004` | Q-04 | AgentSet owns Agent 删除处理 | ✅ | 采用 §3.2 adoption/orphan 语义并复用 `agentset.superteam-a2a.io/cleanup`。L2-2 §15 Q-04 的 `superteam.a2a.io/agentset-adoption` 与同文档 §7 的 4 个永久名称冲突，登记为上游摘要 erratum；本 Spec 以 L2-2 §7 + 本 Spec §2.3.7 的 wire contract 为权威，**不得新增第 5 个 Finalizer** |
| `OPEN-OP-005` | Q-05 | Operator 升级时避免 reconcile 抖动 | 🟡 | §8.14 先 drain leader + readiness=false + pre-upgrade 检查；v0.1 不实现 conversion webhook 自动迁移，升级行为需 L4 kind 测试确认 |
| `OPEN-OP-006` | Q-06 | Kopf Singleton 与 event loop 绑定 | ✅ | 单 container 单 Python 进程 / 单 event loop；Controller handlers 不使用 `@kopf.Singleton`，MemoryReconciler 只使用 leader-gated `@kopf.timer`（§3.4 / §5 / §6） |
| `OPEN-OP-007` | Q-07 | Lease 续约失败处理 | ✅ | §5 锁定 30s TTL / 10s renew / 连续 3 次失败让位；正式 EventReason 为 `LeaderLost`，上游问题表中的 `LeaseLost` 只视为旧措辞 |
| `OPEN-OP-008` | Q-08 | admission TLS 证书轮换 | 🟡 | §4.2.3 `TLSHotReloader` + cert-manager 挂载 + 失败保留旧 context；是否无需重启即可被 Uvicorn 接受由 `IT-AW-MT-*` 在 L4 实测 |
| `OPEN-OP-009` | Q-09 | MemoryReconciler CPU offload 阈值 | ✅ | §6.2.10 + §7.2.3 锁定 CR 数量 > 1000 时 `anyio.to_thread.run_sync`，由 Helm/Pydantic 字段 `memoryReconciler.cpuOffloadThreshold` 配置 |
| `OPEN-OP-010` | Q-10 | 升级期间 reconcile 抖动抑制 | 🟡 | 与 Q-05 共用 §8.14 时序；grace period 30s 已定，conversion webhook 与真实滚动升级窗口移交 L4，不重复创建第二套升级机制 |
| `OPEN-OP-011` | Q-11 | 4 CRD validator 错误响应格式 | ✅ | §4 使用 snake_case `reason` + 400/422 `http_status` + Pydantic `AdmissionResponse`；wire 字段不得由框架自动改名 |
| `OPEN-OP-012` | Q-12 | Kopf handler 异常是否更新 Status | ✅ | §3 共同契约 + Reconciler error hierarchy：失败写 `status.phase=Failed`，并追加 `conditions[]`（`type=ReconcileFailed` / `reason=ExceptionClass` / `message` 含 trace_id 且脱敏截断） |
| `OPEN-OP-013` | Q-13 | MemoryReconciler 与 Leader Election 关系 | ✅ | §3.4 / §6.2.10 明确它不是第 4 个 CRD Controller；仅 leader 执行 timer，非 leader 立即返回 |
| `OPEN-OP-014` | Q-14 | admission 拒绝审计日志与 OTLP | 🟡 | §7.1.4 structlog + OTel 双写契约已定，正式 EventReason 为 `AdmissionRejected`（非上游问题表旧称 `AdmissionDenied`）；OTLP Collector 链路由 L4 集成测试验证 |
| `OPEN-OP-015` | Q-15 | CrashLoopBackOff 时 Lease 释放 | ✅ | §5 锁定 grace 30s + Lease TTL 30s；进程无法主动 release 时依赖 Lease 过期，其他副本按 10s renew cadence 接管 |
| `OPEN-OP-016` | Q-16 | structlog trace_id 注入位置 | ✅ | §7.1.3-§7.1.5 统一由 OTel context 注入 structlog 与 K8s Event annotation；禁止各 Controller 自造 trace_id |
| `OPEN-OP-017` | Q-17 | Helm values 校验错误可读性 | ✅ | §7.2.3 使用 Pydantic alias + `populate_by_name`；ValidationError 必须显示 YAML 路径、wire 字段名和实际值 |
| `OPEN-OP-018` | Q-18 | Operator 与 admission 崩溃隔离 | ✅ | 同 Deployment / 同 Pod 的**两个 container、两个单进程**：Operator 与 admission 各自单 worker，共享网络而不共享 Python event loop；不采用“单进程双 ASGI”解释 |
| `OPEN-OP-019` | OPEN-Q-01 | Pydantic schema 与 `values.schema.json` 同步 | ✅ | §7.2.3 + §8.16：CI 以 `HelmValues.model_json_schema(by_alias=True)` 生成并比较；禁止手改 schema |
| `OPEN-OP-020` | OPEN-Q-02 | `@kopf.on.resume` 与 admission 就绪顺序 | 🟡 | readiness 只有在 TLS、webhook 注册与 Lease 初始化完成后才为 true；Helm pre-install/pre-upgrade 等待 `/readyz`，真实 APIServer 时序由 L4 E2E 验证 |

### 10.2 Go baseline 附录 B 去重 crosswalk（7 项 → 5 个独立决策）

| Go baseline 项 | 历史问题 | 去重结果 | Python-first 结论 | 决策 ID |
|---|---|---|---|---|
| B.1 | Operator 是否包含 KnowledgeScope/KnowledgeItem Controller | 独立 | ✅ 不包含；Knowledge CRD 业务 Controller 属 L3-5，Operator 只保留 admission / 生命周期集成点（§1.1 / 附录 A.5） | `OPEN-OP-021` |
| B.2 | MemoryReconciler 周期 | 与 Q-03 重复 | 复用 60s 默认 + Helm 可配，不创建新 ID | `OPEN-OP-003` |
| B.3 | PeriodicWorker 与单 CR reconcile 是否双触发 | 独立 | ✅ Python v0.2 只由 leader-gated `@kopf.timer` 执行全量生命周期计算；Memory CR create/update 只做 admission/schema/status 基线，不再触发第二套 decay worker | `OPEN-OP-022` |
| B.4 | admission webhook 是否参与 Leader Election | 独立 | ✅ 不参与；所有 admission 副本均服务，只有业务 reconcile/timer 受 `LeaderGate` 控制（§4 / §5） | `OPEN-OP-023` |
| B.5 | Operator 是否需要 HPA | 与 Q-01 重复 | v0.2 不启用；复用规模监控与 v0.5+ 决策门槛 | `OPEN-OP-001` |
| B.6 | status.endpoints 更新是否引发 reconcile 风暴 | 独立 | ✅ 只在值变化时 patch status subresource；使用 `observedGeneration` + no-op diff，禁止写回未变化字段（§3 / §8 集成测试） | `OPEN-OP-024` |
| B.7 | specChanged 使用 hash annotation 还是 generation | 独立 | ✅ Python/Kopf 使用 handler `old/new/diff` + `metadata.generation` / `status.observedGeneration`；不沿用 Go hash annotation | `OPEN-OP-025` |

**去重不变量**：20 个 L2-2 项 + 7 个 Go baseline 项 - 2 个重复项（B.2/B.5）= **25 个独立决策 ID**。crosswalk 中重复项必须引用已有 ID，不得为了“每行一个编号”把问题总数虚增为 27。

### 10.3 口径冲突决议（评审前封口）

| 冲突 | 权威口径 | 决议 |
|---|---|---|
| `LeaseLost` vs `LeaderLost` | L2-2 §10.6 `EventReason` + 本 Spec §7.1.5 | 正式字符串只允许 `LeaderLost`；`LeaseLost` 仅在本节作为已纠正的历史措辞出现 |
| `AdmissionDenied` vs `AdmissionRejected` | L2-2 §10.6 + 本 Spec §7.1.5 | 正式字符串只允许 `AdmissionRejected`；日志字段可用 `admission_denied=true`，不得成为 EventReason |
| `agentset-adoption` vs 4 个永久 Finalizer | L2-2 §7 + 本 Spec §2.3.7 | L2-2 §15 Q-04 登记为摘要 erratum；**§2.3.7 是本 Spec 的唯一 Finalizer 名称清单**，仅保留 4 个 `*.superteam-a2a.io/cleanup`。adoption 是 AgentSet cleanup 行为，不是第 5 个名称 |
| `intervalSeconds` 30-300 vs 10-3600 | L2-2 §9.2 Pydantic schema + 本 Spec §7.2.3 | 字段级 schema `ge=10, le=3600` 优先；L2-2 §15 Q-03 的 30-300 为摘要 erratum，默认值仍为 60s |
| MemoryReconciler 是否为 Controller | L2-2 §3.4 + 本 Spec §3.4/§6 | C-1.4 是 `reconcilers/memory_reconciler.py` 的后台 service；不导出 `MemoryReconcilerController`，不新增 `controllers/memory_reconciler.py` |
| Python/Helm 文件数量 | 本 Spec §1.3 + §7.2.1 + §8.1 | 70 个 Python 文件；9 个 Helm manifest 模板 + 1 helper；§8 加入工程与测试资产后形成 162 个文件级条目 |
| admission 隔离形态 | ADR-0005 §6/§7 + 本 Spec §4/§7.2 | 同 Pod 双 container，各自单 Python 进程/单 worker；“单进程原则”按 container 解释，不是整个 Pod 只能有一个进程 |
| OPEN ID 与测试 ID | L2-2 §15.8 + 本 Spec §9.2 | `OPEN-OP-*` 仅作决策追踪，不计入 277 个可执行测试 ID，也不计入 `ACCEPT-*` |

### 10.4 收敛统计与 v0.5+ 演进路线

| 来源 | 去重数量 | ✅ 已收敛 | 🟡 待 L4 实测 | ⬜ 未决 | v0.2.0 阻塞 |
|---|---:|---:|---:|---:|---:|
| L2-2 §15 | 20 | 15 | 5 | 0 | 0 |
| Go baseline 独立项 | 5 | 5 | 0 | 0 | 0 |
| **合计** | **25** | **20** | **5** | **0** | **0** |

**收敛率口径**：25/25 均已有可实施默认决策；其中 20 项无需额外环境即可完全收敛，5 项须由 L4 的 kind/cert-manager/OTLP/滚动升级测试确认。因此“可实施决策覆盖率”= **100%**，“完全收敛率”= **80%**。

**v0.5+ 五项演进路线**：

1. Workflow CEL 表达式引擎替代静态 inputs stub。
2. Agent > 1000 后的 informer 分片 / HPA，以及 conversion webhook 驱动的无抖动升级。
3. reconcile throughput、Memory 批处理、status patch storm 的正式性能预算与压测基线。
4. Operator 镜像增加 `linux/arm64` 多架构发布。
5. `cosign` keyless 签名 + `syft` CycloneDX SBOM 供应链元数据。

### 10.5 `OPEN-OP-*` 决策追踪 ID

- `OPEN-OP-001~020`：L2-2 §15 的 20 项，编号顺序与 Q-01~Q-18 + OPEN-Q-01/02 表格顺序一致。
- `OPEN-OP-021~025`：Go baseline 去重后 5 个独立问题；B.2/B.5 复用 `OPEN-OP-003`/`OPEN-OP-001`。
- `OPEN-OP-026~030`：预留给 v0.5+ 的新决策；本 v0.2-draft-full 不得提前占用。
- **命名空间独立**：L2-2 的 `OPEN-Q-*` 与本 L3-1 的 `OPEN-OP-*` 是不同层级的追踪 ID，不要求数字一一对应；上游 Q 项通过 §10.1 的“上游项”列建立映射，后续 CEL 若落地将占用一个新的 `OPEN-OP-*` 预留 ID。
- `OPEN-OP-*` **不计入** §9.2 的 277 个测试 ID；只有问题转化为可执行测试时，才在既有 TEST/TOOL/OBS/HLT/HELM/RBAC/UT/IT/E2E/CONFORMANCE/PERF 前缀中登记。

**基线引用**：[L2-2 Spec §15](../../spec/L2-module-specs/L2-operator-core.md)（20 项）+ [L3-1 Go baseline 附录 B](../../archive/pre-python-2026-07-24/L3-operator-core-spec-v0.1-draft-go-baseline.md)（7 项历史问题）+ [L3-2 Spec §15](./L3-a2a-core.md)（状态图例与去重统计模板）。

---

## 附录 A：跨模块引用清单（v0.2-draft-full）

> 本附录列出 L3-1 文件级 Spec 引用的所有外部文档与符号,确保 L4 实施者能正确 import。L3-1 不创造新概念;所有协议 / wire contract / 业务语义均来自 L1/L2 已评审文档。

### A.1 L1 文档(架构基线)

| L1 文档 | 关键章节 | L3-1 引用位置 |
|---|---|---|
| `docs/design/L1-architecture.md` v0.2.0 | §3.2 编排层 + §4.1 C-1 Operator + §11.5 Python 性能预算 | 全文依据 + §1.1 + §2.3 主入口 |
| `docs/spec/L1-system-spec.md` v0.2.0 | §2 CRD Agent spec + §3 CRD AgentSet spec + §4 CRD Workflow spec + §7 状态机 + §16 Prometheus 指标 + §9/§10 资源/限流 | §1.3 文件清单 + §2.3.9 11 指标 + §3.1-§3.4 reconcile 流程 |

### A.2 L2 模块文档(模块契约)

| L2 文档 | 关键章节 | L3-1 引用位置 |
|---|---|---|
| `docs/design/L2-modules/L2-operator-core.md` v0.2.0 | §3 Python 包结构 + §4 4 Controllers + §5 admission + §6 Leader Election + §9 错误模型 + §10 可观测性 + §11 Helm values + §12 RBAC + §13 测试策略 | 全文依据 + §1.3 + §2.3 |
| `docs/spec/L2-module-specs/L2-operator-core.md` v0.2.0 | §1.1-§1.4 使命边界 + §3 4 Controllers + §4 admission + §5 Helm values Pydantic schema + §8 Memory + §10 错误模型 + §11 可观测性 + §12 RBAC + §13 测试策略 + §14 验收清单 + §15 开放问题 | 全文依据 + §3-§10 |
| `docs/design/L2-modules/L2-a2a-protocol.md` v0.2.0 | §3 A2A method 协议 | §3 副调用 + 附录 B 待补 |
| `docs/spec/L2-module-specs/L2-a2a-protocol.md` v0.2.0 | §2.5 (client) | 全文引用 + 附录 B 待补 |
| `docs/design/L2-modules/L2-adapter.md` v0.2.0 | §3 Card 转换 + §6 框架矩阵 | §3.1 Agent Controller Adapter 注入 |
| `docs/spec/L2-module-specs/L2-adapter.md` v0.2.0 | (与 Design 共享) | 同上 |
| `docs/design/L2-modules/L2-knowledge-memory.md` v0.2.0 | §3 Knowledge + §4 Memory 5 维矩阵 | §3.4 MemoryReconciler + §2.3.12 models/memory/* |
| `docs/spec/L2-module-specs/L2-knowledge-memory.md` v0.2.0 | §3-§11(60 测试 ID + 30 验收点 + 22 开放问题)| §2.3.12 models/memory/ + §3.4 |

### A.3 ADR 引用(决策依据)

| ADR | 关键决策 | L3-1 引用位置 |
|---|---|---|
| `docs/adr/0001-v1-scope-statement.md` | v1 范围声明(5 能力 + 6 CRD + 永久 out-of-scope)| §1.1 使命 |
| `docs/adr/0002-knowledge-management-design.md` | Knowledge 4 级作用域 + 5 维可见性矩阵 | §3.4 MemoryReconciler + §2.3.12 models/memory |
| `docs/adr/0003-memory-design.md` | Memory CRD + decay/reinforce 算法 + 5 维可见性矩阵 | §3.4 MemoryReconciler + §2.3.12 models/memory + §2.3.4 admission/mutual_exclusion |
| `docs/adr/0004-v01-scope-extension-knowledge-and-memory.md` | v0.1 范围扩展(12 → 20 周)| §1.1 部署时间表(背景) |
| `docs/adr/0005-python-first-technology-stack.md` | Python-first 全栈迁移(Operator 模块映射 + 单进程 + SDK + OTel + uv workspace)| 全文依据 + §1.1 + §2.1 + §2.2 边界规则 |

### A.4 Constitution 引用(顶层约束)

| Constitution 章节 | 内容 | L3-1 引用位置 |
|---|---|---|
| v0.5.0 §3.7 | Operator 不依赖 framework adapter | §2.2 边界规则 #1 |
| v0.5.0 §3.8 | Python-first(ADR-0005 supersede ADR-0001~0004 实现栈)| 全文 |
| v0.5.0 §5 | 文档层级(L1-L4)| §1 阅读指南 |
| v0.5.0 §6 | mTLS + NetworkPolicy | §2.3.9 events.py + §2.3.13 networkpolicy.yaml |
| v0.5.0 §7 | 可观测性无例外（11 Operator + 4 Python runtime 指标 + OTel + structlog + K8s Events） | §7.1 observability/*（6 文件） |
| v0.5.0 §9.4 | ruff + import-linter 静态检查 | §2.2 边界规则 #11 |
| v0.5.0 §9.7 | pyright strict + interrogate docstring 100% | §1.4 文件清单 |
| v0.5.0 §14.4 | 评审门禁：每个 L3 Spec 必须通过 10 维度评审 | §9 验收清单 + 下一会话独立评审 |
| v0.5.0 §15.5 | 质量红线(测试覆盖率 ≥ 80%)| §2.3 测试文件 ID 矩阵 |
| v0.5.0 §16 | 会话与上下文管理(1M 窗口 / 500K 红线 / §16.1.3 实际水位 / §16.1.4 参照表)| 本次 #44 骨架撰写依据 |

### A.5 配套 L3 Spec 引用

| L3 配套 | 状态 | L3-1 引用位置 |
|---|---|---|
| `docs/spec/L3-file-specs/L3-a2a-core.md` | **v0.2.0 已通过评审**（2026-07-28 · 2852 行 / 160KB / 16 节 + 2 附录 / 30 文件 + 9 Helm + 30 测试 / 276 测试 ID / 24 错误码 / 15 指标；[评审报告](../../reviews/l3-2-a2a-core-spec-review.md) §A-§P 10 维度全 PASS）| §0 阅读指南 + 头部 frontmatter + 附录 A.4 |
| `docs/spec/L3-file-specs/L3-adapter-sdk.md` | **v0.2.0 已通过评审**（2026-07-29 #58 · 148KB / ~2400 行 / 16 节 + 2 附录 / 12 SDK + 22 framework + 200 测试 ID / [评审报告](../../reviews/l3-3-adapter-sdk-spec-review.md) §A-§P 10 维度全 PASS · 0 阻塞项 · 9 关注项 · 4 建议项）| §0 阅读指南 + 头部 frontmatter |
| `docs/spec/L3-file-specs/L3-hello-agent.md` | **v0.2.0 已通过评审**（2026-07-29 #61 · 75KB / 1576 行 / 11 主章节 §0-§10 + 2 附录 / 5 文件级契约 + 7 Helm + 1 Dockerfile + 2 CRD / 25 测试 ID + 30/37 验收点 / [评审报告](../../reviews/l3-4-hello-agent-spec-review.md) §A-§J 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项）| §0 阅读指南 + 头部 frontmatter |
| `docs/spec/L3-file-specs/L3-knowledge-service.md` | **待起草**（L3-5） | §3.4 + §10.2 B.1 边界决议 |
| `docs/spec/L3-file-specs/L3-memory-backend.md` | **待起草**(L3-6)| §3.4 + §6 |

### A.6 归档基线

| 归档文档 | 状态 | 本 Spec 用途 |
|---|---|---|
| [L3-operator-core-spec-v0.1-draft-go-baseline.md](../../archive/pre-python-2026-07-24/L3-operator-core-spec-v0.1-draft-go-baseline.md) | 2026-07-27 归档 · 未评审 · 75KB / 1886 行 | 仅保留 4 Controller 职责、CRD 状态机、4 Finalizer、RBAC、metric name 与附录 B 7 项历史问题的业务语义 |
| [L2-operator-core-spec-v0.1.0-go-baseline.md](../../archive/pre-python-2026-07-24/L2-operator-core-spec-v0.1.0-go-baseline.md) | 2026-07-24 归档 · v0.1.0 | 追溯 L2-2 Go → Python 的 supersede 边界；不得作为 Python import/package 依据 |

---

## 附录 B：ADR / Constitution 引用矩阵（5 子表 · v0.2-draft-full 完整版）

> ✅ 本附录把 L3-1 的文件级约束逐项回溯到 ADR / Constitution / L1 / L2 权威条款，供 §9 的宪法一致性与跨文档一致性评审使用。
>
> **约束强度**：**MUST** = 违反即与已评审上游冲突、阻断合并 · **SHOULD** = 默认实现，偏离需在 PR 中解释并补测试 · **MAY** = 兼容扩展点，不属于 v0.1 验收门禁。

### B.1 架构与部署

| L3-1 条款 | 上游引用 | 约束内容 | 强度 |
|---|---|---|---|
| §1.1 C-1 模块使命 | L1 Architecture v0.2.0 §3.2 + §4.1 | Operator 是编排层唯一实现，不承载 Agent 框架业务逻辑 | MUST |
| §1.2 public API | L2-2 Spec §1.2 + Constitution §3.7 | 仅导出 Operator/Controller/Reconciler/admission/leader/config/error 公共符号 | MUST |
| §2.2 依赖方向 | ADR-0005 §3.1 + Constitution §3.8 | Controller → Reconciler → Client/Model 单向依赖；Operator 不依赖 Adapter 实现 | MUST |
| §2.1 uv workspace | ADR-0005 §13.1 | 代码固定在 `packages/operator/src/superteam_a2a/operator/` | MUST |
| §3 Controller 结构 | L2-2 Design §4 + Spec §3 | 3 个 CRD Controller 使用 30-50 行 Kopf handlers，业务逻辑下沉 service | MUST |
| §3.4 / §6 MemoryReconciler | ADR-0003 §6.5 + L2-2 Spec §3.4 | MemoryReconciler 是 leader-gated timer service，不是额外 CRD Controller | MUST |
| §4 admission 隔离 | ADR-0005 §7 + L2-2 Spec §4.1 | 同 Pod 独立 container / 独立单进程；所有副本均服务 admission | MUST |
| §5 Leader Election | L2-2 Spec §6 | K8s Lease：30s TTL / 10s renew / 3 次失败让位 | MUST |
| §7.2 Helm 部署 | L2-2 Spec §9 + §13 | 9 个 manifest 模板 + 1 helper；Operator/admission 双 container | MUST |
| §10.4 v0.5+ | ADR-0001/0004 范围约束 | CEL、HPA/分片、arm64、签名/SBOM 不得反向扩大 v0.1 验收面 | MUST |

### B.2 接口与生命周期

| L3-1 条款 | 上游引用 | 约束内容 | 强度 |
|---|---|---|---|
| §1.2 `OperatorMain` | L2-2 Spec §1.2 | 启动 Kopf、admission 与 Leader Election；不得暴露框架私有类型 | MUST |
| §3.1-§3.3 CRD handlers | L1 Spec §2-§4 + §7 | Agent / AgentSet / Workflow spec/status 字段与状态机不可改名 | MUST |
| §2.3.7 Finalizer | L2-2 Spec §7 + Constitution §3.4 | 仅 4 个 `*.superteam-a2a.io/cleanup`，名称永久不变 | MUST |
| §4 `AdmissionResponse` | L2-2 Spec §4 | `reason` snake_case + `http_status` 400/422；Pydantic alias 不得改变 wire 名 | MUST |
| §4 validators | ADR-0002 §2/§3 + ADR-0003 §5 | DAG 校验和 Knowledge↔Memory 双向互斥为 admission 强约束 | MUST |
| §5 `LeaderGate` | L2-2 Spec §5-§6 | 非 leader 不执行 Memory timer；admission 不受 LeaderGate 控制 | MUST |
| §6.3 Memory wire sync | L2-4 Spec v0.2.0 §3.4 | 19 个 Memory 字段逐项一致；Operator 只 patch status，不解释 query wire | MUST |
| §7.1.5 EventReason | L2-2 Spec §10.6 | 8 个字符串为稳定契约；使用 `LeaderLost` / `AdmissionRejected` | MUST |
| §10.2 generation/diff | Kopf persistence + Go baseline B.7 supersede | 使用 `old/new/diff` + generation/observedGeneration，不使用 Go hash annotation | SHOULD |
| §10.5 OPEN ID | L2-2 Spec §15.8 | `OPEN-OP-*` 是决策追踪器，不进入 277 测试 ID | MUST |

### B.3 Knowledge / Memory 可见性与业务边界

| L3-1 条款 | 上游引用 | 约束内容 | 强度 |
|---|---|---|---|
| §0 模块外能力 | ADR-0002 + ADR-0003 + L1 Architecture §3.5 | Knowledge 搜索、Memory query/record 业务属于 L3-5/L3-6 | MUST |
| §3 Agent Controller | ADR-0002 §2 | 只传递 `knowledge.scopeRef`，不在 Operator 内实现作用域继承 | MUST |
| §4 MutualExclusionValidator | ADR-0002 §2 + ADR-0003 §5 | Knowledge 与 Memory 引用按双向互斥矩阵校验 | MUST |
| §6 Memory models | ADR-0003 §4/§6 + L2-4 Spec §3 | 5 维可见性字段只验证/持久化，不改变语义 | MUST |
| §6 decay/reinforce/gc/promotion | ADR-0003 §4 + L2-4 Spec §7 | 4 个纯函数公式必须与 L2-4 逐字符一致 | MUST |
| §6 MemoryReconciler | ADR-0003 §6.5 | 仅 leader 周期执行 status 生命周期计算；不得实现 A2A queryMemory | MUST |
| §10.2 B.1 决议 | L2-4 Design/Spec v0.2.0 | KnowledgeScope/KnowledgeItem Controller 属 L3-5，不加入 Operator 包 | MUST |

### B.4 安全

| L3-1 条款 | 上游引用 | 约束内容 | 强度 |
|---|---|---|---|
| §4 admission mTLS | ADR-0005 §9.1 + Constitution §6.1 | cert-manager 证书、TLS 强制、无明文 fallback | MUST |
| §4.2.3 TLS reload | Constitution §6.3 | 私钥权限校验；reload 失败保留旧 context 并使 readiness 反映状态 | MUST |
| §7.2 ServiceAccount | L2-2 Spec §11.3 | cert-manager CA 注解与命名固定通过 values 显式配置 | MUST |
| §7.3 ClusterRole | Constitution §6.4 | 仅 7 个已列 apiGroups/resource 组合；不得用 `*` 扩权 | MUST |
| §7.3 admission Role | Constitution §6.4 | 仅 namespace-scoped TLS secrets；不得读取其他业务 secrets | MUST |
| §7.2 NetworkPolicy | Constitution §6.5 | 默认拒绝，显式允许 APIServer、DNS、OTLP 与必要 webhook 流量 | SHOULD |
| §8.11 容器用户 | ADR-0005 §12 + Constitution §6.3 | `python:3.12-slim`、uid/gid 65532、只读 rootfs | MUST |
| §8.11 capabilities | Constitution §6.3 | drop ALL；8443 不需要 `NET_BIND_SERVICE`，不得无理由添加 capability | MUST |
| §8.6 安全门禁 | Constitution §9.7 | bandit + pip-audit 0 高危漏洞，失败阻断合并 | MUST |
| §7.1.4 日志脱敏 | Constitution §6.6 | token、证书私钥、Memory content 等敏感值不得进入 structlog/K8s Event | MUST |

### B.5 可观测性与测试

| L3-1 条款 | 上游引用 | 约束内容 | 强度 |
|---|---|---|---|
| §7.1.2 指标 | L1 Spec §16 + L2-2 Spec §10 | 11 个 Operator + 4 个 Python runtime metric name 不可改 | MUST |
| §7.1.3 health | L2-2 Spec §13.5 | `/healthz` 只表示进程存活；`/readyz` 聚合 TLS/webhook/Lease/Memory last_run | MUST |
| §7.1.4 tracing | ADR-0005 §10 + Constitution §7 | 显式 TracerProvider 注入 + W3C trace context；测试不得污染全局 provider | MUST |
| §7.1.4 logging | ADR-0005 §10 | structlog JSON 8 必含字段，trace_id/span_id 与 OTel 一致 | MUST |
| §7.1.5 Events | Constitution §7 | 8 个 EventReason 白名单 + message 1024 字符上限 | MUST |
| §8.1 文件镜像 | ADR-0005 §11 | 源文件、测试、工程资产共 162 个文件级条目可追溯 | SHOULD |
| §8.2 测试金字塔 | Constitution §9 | UT / IT / E2E / Conformance / Property / PERF 分层明确 | MUST |
| §9.2 测试矩阵 | Constitution §9.7 + §14.4 | 277 个测试 ID 映射到具体文件或场景 | MUST |
| §8.6 覆盖率 | Constitution §15.5 | 全包 ≥80%，reconcile/cleanup/admission 关键路径 ≥95% | MUST |
| §8.6 静态门禁 | ADR-0005 §11 + Constitution §9.7 | ruff / pyright strict / bandit / pip-audit / interrogate / import-linter | MUST |
| §8.10 `ST-A2A-BOUNDARY` | ADR-0005 §3.1 + Constitution §3.8 | Operator 不 import Adapter 实现或官方 A2A SDK 私有路径 | MUST |
| §9 验收清单 | Constitution §14.4 | 30 条硬验收 + ACCEPT-001~022 是升级 v0.2.0 的唯一凭证 | MUST |
| §10 开放问题 | L2-2 Spec §15 | 25 项均有默认决策；5 项 L4 实测不阻塞独立文档评审 | MUST |

**基线引用**：[L2-2 Operator Core Spec 附录 B](../../spec/L2-module-specs/L2-operator-core.md)（5 子表模板）+ [L3-2 A2A Core Spec 附录 B](./L3-a2a-core.md)（MUST/SHOULD/MAY 文件级模板）+ [CONSTITUTION v0.5.0](../../../CONSTITUTION.md)。

---

## 文档元数据与后续入口

### M.1 版本与状态

| 字段 | 值 |
|---|---|
| 版本 | **v0.2.0** |
| 状态 | ✅ §0-§10 + 附录 A/B 完整；**已通过独立评审**（§A-§P 10 维度全 PASS / 0 阻塞项 / 3 关注项 / 4 建议项） |
| 上游 | L2-2 Operator Core Design + Spec v0.2.0 |
| 同级已通过 | L3-2 A2A Core v0.2.0 |
| supersedes | L3-1 v0.1-draft Go 实现条款；归档业务语义继续有效 |
| 评审报告 | `docs/reviews/l3-1-operator-core-spec-review.md`（2026-07-28 #56 · 700 行 / 55KB / §A-§P 16 节） |
| 当前变更边界 | 单 commit 含本 Spec 升级 + 评审文件 + §F.1-§F.6 6 步微同步（详见 §M.3） |

### M.2 落地记录

| 日期 / 会话 | 增量 | 结果 |
|---|---|---|
| 2026-07-27 #44 | Python v0.2 骨架 + Go baseline 归档 | §0-§3 + 附录 A |
| 2026-07-27 #45 | admission / Leader Election / Memory | §4-§6 |
| 2026-07-27 #47 | observability / RBAC / Helm | §7 |
| 2026-07-27 #48 | 测试策略 / 工具链 | §8 |
| 2026-07-27 #49 | 277 测试 ID + 30 条硬验收 | §9 |
| 2026-07-28 #55 | 25 项开放问题 + 5 子表追溯矩阵 + 口径封口 | §10 + 附录 B；形成 v0.2-draft-full |
| 2026-07-28 #56 | 独立评审 §A-§P 10 维度全 PASS + 头部/§M 升级 v0.2.0 | **v0.2.0 通过评审；L3 阶段 1/4 完成** |

### M.3 下一会话固定入口

1. **§F.1-§F.6 跨文档同步（低风险微同步 · 与本会话升级绑定）**：参照 L3-2 #54 §F 6 步模板
   - F.1 L1 Architecture v0.2.0 §3.2 + §4.1（2 处微同步）
   - F.2 L1 Spec v0.2.0 §16 11+4 指标 metric name 文件级确认标记
   - F.3 L2-1 A2A Spec v0.2.0 附录 A 反向引用升级 L3-1 v0.2.0 + 评审链接
   - F.4 L2-3 Adapter Spec v0.2.0 + L2-4 Knowledge/Memory Spec v0.2.0 附录 A 反向引用升级 L3-1 v0.2.0 + 评审链接
   - F.5 ROADMAP.md Phase 1.5 L3 阶段进度：L3-1 v0.2-draft → v0.2.0 + L3-2 v0.2.0 双勾选；新增 L3-3/L3-4 任务
   - F.6 README.md + CONSTITUTION-CHANGELOG.md L3-1 v0.2.0 通过标记
2. **git commit（单 commit 模板）**：`feat(L3-1): 升级 v0.2.0 + §A-§P 评审通过 + §F 6 步跨文档同步`（参照 L3-2 #54 commit `68085f2`）。
3. **随后启动 L3-3 Adapter SDK 文件级 Spec Python 起草**（独立会话）：基于 L2-3 v0.2.0 Spec + 复用 L3-2 §6 `A2AClient` + L2-3 v0.2.0 6-framework matrix；不重新定义 A2A wire contract；建议拆 Spec 起草 + 评审两会话避免 §16.1 红线。

---

> **签署**：本 L3-1 Operator Core 文件级 Spec Python v0.2.0 由 #44/#45/#47/#48/#49/#55 与 2026-07-28 #56 共同形成，依据 [L2-2 Operator Core Spec v0.2.0](../../spec/L2-module-specs/L2-operator-core.md)、[L2-2 Design v0.2.0](../../design/L2-modules/L2-operator-core.md)、[L3-1 Go baseline（已归档）](../../archive/pre-python-2026-07-24/L3-operator-core-spec-v0.1-draft-go-baseline.md)、[L2-4 Spec v0.2.0](../../spec/L2-module-specs/L2-knowledge-memory.md) 与 Constitution v0.5.0 编写。**v0.2.0 已通过评审；可进入 L4 实施阶段或启动 L3-3 Adapter SDK 重写。**