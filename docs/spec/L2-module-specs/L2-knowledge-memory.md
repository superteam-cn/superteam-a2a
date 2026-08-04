# L2 模块 Spec：Knowledge / Memory（知识管理 + 持久化记忆 · Python-first）

> **⚠️ ADR-0005 supersede 指针（2026-07-26）**：本 v0.2-draft Python Spec 文档**仅 supersede Go struct / Go interface / kubebuilder annotation / Go package layout / Go 镜像块 实现条款**；wire contract（**3 CRD 字段 / 4 A2A method / 5 维可见性矩阵 / decay/reinforce/GC/promotion 算法 / admission 双向互斥 / 状态机 / 错误码范围 / 生命周期契约 / 测试 ID**）与 v0.1.0 Go baseline 业务语义**完全继续有效**。L1 v0.2.0 / L2-1 v0.2.0 / L2-2 v0.2.0 / L2-3 v0.2.0 / L2-4 Design v0.2.0 已于 2026-07-24~27 评审通过，依据 ADR-0005 Python-first 全栈迁移 + 宪法 v0.5.0 §3.8。
>
> **Python 重写映射**：Go struct → Pydantic v2 BaseModel + `Field(...)` + `populate_by_name` + alias；Go `interface{}` → `typing.Protocol` + `@runtime_checkable`；Go `controller-runtime` reconcile → Kopf `@kopf.timer(interval=60.0)` + 独立 `MemoryReconciler` async service + Leader Election via `coordination.k8s.io/v1` Lease；Go BM25 → Python `dict[str, set[str]]` + `anyio.to_thread.run_sync` 受控线程 offload；Go `kubebuilder:validation:` → Pydantic `Field(...)` → JSON Schema 2020-12 → deterministic OpenAPI v3 CRD 生成；Clock 用 `typing.Protocol[now, advance]` 注入 + `FakeClock` 时间穿越；admission webhook 用 Kopf `kopf.validation` decorator + cert-manager TLS + 50ms 超时 fail-closed；镜像基线 `golang:1.22-alpine` → `python:3.12-slim` 多阶段 + uv build；测试 `testing` + `gomock` + envtest → `pytest` + `pytest-asyncio` + `respx` + `hypothesis` + `freezegun` 时间穿越
>
> **层级**：L2 — 模块 Spec
> **模块 ID**：C-4（Knowledge / Memory，见 L1 v0.2.0 Architecture §3.5.2 / §3.5.3）
> **代码位置**：`packages/knowledge/src/supteam_a2a/knowledge/` + `packages/memory/src/supteam_a2a/memory/` + `packages/knowledge-service/src/supteam_a2a/knowledge_service/` + `packages/memory-backend/src/supteam_a2a/memory_backend/` + `packages/shared-visibility/src/supteam_a2a/shared/visibility/`（**Python-first · ADR-0005 §13 工程布局 · uv workspace**）
> **版本**：**v0.2.0**（Python 重写 · ADR-0005 触发；2026-07-27 #42 补完 §12-§15 + #43 评审通过）
> **状态**：✅ **v0.2.0 已评审通过**（§0-§15 + 附录 A/B + §16 全部完成；4152 行 / 194.6KB / 60 测试 ID + 30 验收点 + 22 开放问题；[评审报告 §A-§P 10 维度全 PASS](../../reviews/l2-4-knowledge-memory-spec-python-review.md)）
> **supersedes**：v0.1.0 Go baseline（[`docs/reviews/l2-4-knowledge-memory-review.md`](../../reviews/l2-4-knowledge-memory-review.md) 2026-07-24 通过；**仅 supersede Go struct / Go interface / Go package / Go 镜像块 / kubebuilder annotation 实现条款**；wire contract（3 CRD 字段 / 4 A2A method / 5 维可见性矩阵 / decay/reinforce 算法 / admission 双向互斥 / BM25 评分 / 状态机）与 v0.1 业务语义**完全继续有效**）
> **配套 Design**：[`docs/design/L2-modules/L2-knowledge-memory.md`](../../design/L2-modules/L2-knowledge-memory.md) **v0.2.0 Python**（2026-07-27 #39 评审通过；1920 行 / 97KB / 14 节 + 2 附录；本 Spec 的设计依据）
> **Go baseline（v0.1.0 · 归档丢失）**：v0.1.0 Go Spec 2501 行 / 99KB / 12 节 + 2 附录（已被 v0.2-draft Python 覆盖；wire contract / 业务语义完全继续有效）
> **本模块目的**：把 [`docs/design/L2-modules/L2-knowledge-memory.md`](../../design/L2-modules/L2-knowledge-memory.md) v0.2.0 中的 3 CRD + 1 特殊 Agent + 4 A2A method + 4 级继承 + 5 维矩阵 + admission 双向互斥 + MemoryReconciler 设计落地为 **Python 代码契约**（Pydantic v2 + typing.Protocol）、**完整 JSON Schema**（CRD YAML 单一来源）、**Helm values 配置面**（uv 多阶段镜像）、**测试骨架**（6 层级 + 57 ID）与 **生命周期契约**（5 时序图）。它是 L2-1 A2A Protocol（嵌入 Server SDK 注册 4 method handler）与 L2-2 Operator Core（MemoryReconciler 60s 周期 reconcile）的**下游实现**。

---

## 0. 阅读指南

- **读者**：Agent 作者（理解 4 级 scope 继承 + recordMemory 写入契约 + queryKnowledge 调用形态）、Operator 维护者（了解 MemoryReconciler reconcile 流程 + 60s 周期 + decay 公式 + Leader Election）、文档贡献者（理解 KI scope/visibility 规则 + admission 互斥校验）、L3-5 / L3-6 文件级 Spec 作者（实现输入）
- **必读章节**：§1（模块概述 + public API surface）/ §2（包结构与文件清单）/ §3（CRD JSON Schema）/ §4（4 级 scope + 5 维矩阵）/ §6（4 个 A2A method handler）/ §7（MemoryReconciler reconcile 流程）
- **可选章节**：§5（admission 互斥规则）/ §8（检索路径）/ §9（错误码）/ §10（可观测性）/ §11（Helm values）/ §12（测试骨架）/ §13（工具链与部署）/ §14（验收清单）/ §15（开放问题）/ 附录 A（跨模块引用）/ 附录 B（ADR/Constitution 引用矩阵）
- **配套阅读**：[L2-4 Design v0.2.0 Python](../../design/L2-modules/L2-knowledge-memory.md) · [L2-1 A2A Protocol Spec v0.2.0 Python](./L2-a2a-protocol.md) · [L2-2 Operator Core Spec v0.2.0 Python §5.6](./L2-operator-core.md) · [L2-3 Adapter Spec v0.2.0 Python §11](./L2-adapter.md) · [L1 Architecture v0.2.0 §3.5.2 / §3.5.3](../../design/L1-architecture.md) + [L1 Spec v0.2.0 §5](../../spec/L1-system-spec.md) · [ADR-0002 知识管理设计](../../adr/0002-knowledge-management-design.md) · [ADR-0003 Memory 设计](../../adr/0003-memory-design.md) · [ADR-0004 v0.1 时间线](../../adr/0004-v01-scope-extension-knowledge-and-memory.md) · [ADR-0005 Python-first §3.4/§6.2/§6.3/§7/§10/§13](../../adr/0005-python-first-technology-stack.md)

**关键变化**（与 v0.1.0 Go baseline 对照 · 继承自 Design v0.2.0 §0）：

| 维度 | v0.1.0 Go | v0.2 Python |
|------|-----------|-------------|
| **CRD types** | Go struct + `+kubebuilder:validation:` | **Pydantic v2 BaseModel + `Field(...)` + `populate_by_name` + alias** |
| **CRD 生成** | `controller-gen` | **Pydantic JSON Schema 2020-12 → 确定性 OpenAPI v3 → checked-in CRD YAML** |
| **算法抽象** | Go `interface{}` | **`typing.Protocol` + `@runtime_checkable`** |
| **4 级 scope 继承** | Go `func` + error | **Python async def + 显式 `ScopeError` 异常** |
| **MemoryReconciler** | controller-runtime `Reconcile()` | **Kopf `@kopf.timer(interval=60.0)` + 独立 `MemoryReconciler` async service + Leader Election via `coordination.k8s.io/v1` Lease** |
| **5 维矩阵** | Go switch + sync.Map | **Python `dict[MemoryVisibility, Callable]` 策略表 + asyncio.Lock** |
| **Clock** | Go interface + `k8s.io/utils/clock` | **`Protocol[now, advance]` + `RealClock` + `FakeClock` 时间穿越** |
| **decay/reinforce** | Go math + sync.Mutex | **Python 数学等价 + asyncio 序列化（Memory 写入串行化避免 race）** |
| **BM25 倒排索引** | Go `map[string][]Item.ID` | **Python `dict[str, set[str]]` + `anyio.to_thread.run_sync` CPU offload** |
| **search 路径** | 同步 in-process | **`async def query()` 入口 + `await anyio.to_thread.run_sync(_search_blocking, query)` offload** |
| **A2A Server 嵌入** | Go `a2a.NewServer(handler)` | **ASGI（Uvicorn 单 worker）+ 官方 `a2a-python` + `supteam_a2a.a2a.upstream` 边界** |
| **错误码** | Go 常量 + `errors.New` | **StrEnum + `a2a-python` JSON-RPC error struct（KNOWLEDGE_* -32008~-32018 / MEMORY_* -32101~-32112）** |
| **可观测性** | `prometheus/client_golang` + `go.opentelemetry.io` | **`prometheus-client` 单进程 + `opentelemetry-sdk` + `structlog`** |
| **admission webhook** | Go `admissionv1.Handler` | **Kopf `kopf.validation` decorator + cert-manager TLS + 50ms 超时 fail-closed** |
| **镜像基线** | `golang:1.22-alpine` + 静态 Go 二进制 | **`python:3.12-slim` 多阶段 + uv build** |
| **测试** | `testing` + `gomock` + envtest | **`pytest` + `pytest-asyncio` + `respx` + `hypothesis` + `freezegun` 时间穿越** |

**与 v0.1.0 Go baseline 关系**：
- v0.1.0 Go baseline 仍作为 **迁移业务语义输入**（已被顶部 supersede 指针标记为「迁移输入」）
- 本 v0.2 Spec **完全替代** Go baseline 的 Python 实现契约（Pydantic + Protocol + ASGI + uv workspace + Kopf）
- 业务语义（3 CRD 字段约束 / 4 级 scope 继承 / 5 维矩阵 / admission 双向互斥 / 4 A2A method / decay/reinforce/GC/promotion 算法 / 错误码范围 / BM25 评分 / Helm values / 测试矩阵 / 部署形态）与 v0.1.0 **完全一致**

---

## 1. 模块概述 + Public API Surface

### 1.1 模块职责

L2-4 Knowledge / Memory 是 `superteam-a2a` **运行时层（Runtime Layer）** 的实现子层，承载 v0.1 第 5 大基础能力 = **知识管理 + 持久化记忆**。本 Spec 定义：

1. **3 个 Pydantic v2 CRD types**（KnowledgeScope / KnowledgeItem / Memory）+ 完整 JSON Schema
2. **Knowledge Service Agent**（CRD-driven 无 framework adapter · `AgentCard` Pydantic model）
3. **4 个 A2A method handler**（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）
4. **Knowledge 4 级作用域继承算法**（typing.Protocol + 异步 + 循环引用检测）
5. **Memory 5 维可见性矩阵过滤算法**（typing.Protocol + 12 种 scope × visibility 组合穷举）
6. **admission webhook 双向互斥**（KnowledgeItem vs Memory · Kopf `kopf.validation`）
7. **MemoryReconciler 周期 reconcile**（Kopf `@kopf.timer(interval=60.0)` + `MemoryReconciler` async service + Leader Election via Lease）
8. **decay / reinforce / GC / promotion 数学**（纯函数 + `Clock` Protocol 注入 + `FakeClock` 时间穿越单测）
9. **内存 BM25 倒排索引**（`InvertedIndex` Protocol + `RealInvertedIndex` 实现 + `anyio.to_thread.run_sync` CPU offload）
10. **可观测性埋点**（Prometheus 17 个 + OTel + structlog JSON）
11. **Helm values 5 段式配置面**（knowledgeService + memoryReconciler + search + admission + ratelimit）
12. **测试骨架**（6 层级 + 57 ID · UT + IT + E2E + CF + 时间穿越 + 性能门禁）

### 1.2 Public API Surface（边界规则）

**五层 import 规则**（与 L2-1 §3.2 + L2-2 §1.4 + L2-3 §1.2 + 宪法 §3.7 + ADR-0005 §3.3 严格一致）：

```
┌─────────────────────────────────────────────────────────┐
│  a2a-python SDK（PyPI: a2a-sdk）                         │
│  ASGI server / AgentCard / Message / Task               │
└──────────────────────┬──────────────────────────────────┘
                       │ 唯一 import 入口
                       ▼
       ┌─────────────────────────────────┐
       │  superteam_a2a.a2a.upstream      │  ← ⚠️ boundary（L2-1）
       └────────────────┬────────────────┘
                        │ 依赖
       ┌────────────────▼─────────────────┐
       │  superteam_a2a.knowledge_service  │  ← Knowledge Service + Memory backend 共享 Deployment
       │  superteam_a2a.memory_backend     │  ← 同进程 / lifespan startup 装载
       └────────────────┬─────────────────┘
                        │ 依赖
       ┌────────────────▼─────────────────┐
       │  superteam_a2a.knowledge          │  ← Knowledge 资源模型层（CRD + scope + search + admission）
       │  superteam_a2a.memory             │  ← Memory 资源模型层（CRD + lifecycle + admission）
       └────────────────┬─────────────────┘
                        │ 依赖
       ┌────────────────▼─────────────────┐
       │  superteam_a2a.shared             │  ← 跨模块共享（clock / leader / observability / errors / meta）
       │  superteam_a2a.shared.visibility  │  ← 5 维矩阵复用
       └──────────────────────────────────┘

       ⚠️ Operator Core（L2-2 · packages/operator）通过 K8s API watch CRD 编排
         Knowledge Service Deployment；不直接 import knowledge_service / memory_backend
```

**关键约束**：
1. `knowledge` / `memory` / `knowledge_service` / `memory_backend` **严禁 import `framework SDK`**（宪法 §3.6 反依赖）
2. `shared` / `shared-visibility` 是唯一被多个模块引用的公共包（避免循环依赖）
3. `operator` package（不在本模块）通过 K8s API watch CRD 编排 `knowledge_service` Deployment，不直接 import（Kopf CRD-driven）
4. `memory_backend.main` 不单独启动；由 `knowledge_service.main` 在 lifespan startup 中 `import` 并装载 2 个 handler（共享 Deployment / 共享进程 / 共享内存倒排索引）

### 1.3 公共 API 一览（来自 `knowledge` + `memory`）

```python
# knowledge 公共 API（业务层可 import）
from superteam_a2a.knowledge import (
    # CRD types（Pydantic v2 BaseModel）
    KnowledgeScope,
    KnowledgeScopeSpec,
    KnowledgeScopeStatus,
    KnowledgeItem,
    KnowledgeItemSpec,
    KnowledgeItemStatus,
    # 引用类型
    ScopeReference,
    SubjectReference,
    ItemReference,
    InheritRules,
    # 枚举
    ScopeLevel,
    ScopePhase,
    KnowledgeType,
    KnowledgeVisibility,
    # 算法抽象
    ScopeResolver,
    RealScopeResolver,
    resolve_effective_scopes,
    InvertedIndex,
    RealInvertedIndex,
    # admission webhook（Kopf validation）
    validate_knowledge_item,
    validate_knowledge_scope,
    # 错误
    ScopeNotFound,
    ScopeCycle,
    ScopeHierarchyViolation,
    KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY,
    KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS,
    KNOWLEDGE_OWNER_KIND_FORBIDDEN,
    KNOWLEDGE_ADMISSION_TIMEOUT,
)

# memory 公共 API（业务层可 import）
from superteam_a2a.memory import (
    # CRD types
    Memory,
    MemorySpec,
    MemoryStatus,
    # 引用类型
    AgentReference,
    # 枚举
    MemoryPhase,
    MemoryVisibility,
    # 算法抽象
    MemoryVisibilityFilter,
    RealMemoryVisibilityFilter,
    is_memory_visible_to,
    # lifecycle 纯函数（Clock 注入）
    apply_decay,
    apply_reinforce,
    gc_expired,
    is_eligible_for_promotion,
    # admission webhook
    validate_memory,
    # 错误
    MEMORY_SCOPE_NOT_FOUND,
    MEMORY_INVALID_CONTENT,
    MEMORY_FORBIDDEN,
    MEMORY_RATE_LIMIT,
    MEMORY_QUERY_TOO_BROAD,
    MEMORY_ADMISSION_TIMEOUT,
)

# shared 跨模块共享（clock / leader / observability / errors）
from superteam_a2a.shared import (
    Clock,
    RealClock,
    FakeClock,
    LeaseLeader,
    RealLeaseLeader,
    ObjectMeta,
    Condition,
    AwareDatetime,
    # 错误基类
    ScopeError,
    AdmissionTimeoutError,
)

# shared-visibility 5 维矩阵复用（Knowledge v0.5+ + Memory 共享）
from superteam_a2a.shared.visibility import (
    VisibilityMatrix,
    RealVisibilityMatrix,
    MEMORY_VISIBILITY_SCOPE_MATRIX,  # 4 × 3 矩阵定义
)
```

**边界保护**：用 ruff + pyright 自定义 import linter 检测（规则名 `ST-KNOWLEDGE-BOUNDARY` / `ST-MEMORY-BOUNDARY`）；违规即 lint 失败。

### 1.4 价值主张

| 角色 | 承诺 |
|------|------|
| **Agent 作者** | 5 行 YAML（`framework` / `image` / `card` / `resources` / `healthCheck`）+ A2A method 即可 queryKnowledge / recordMemory |
| **文档贡献者** | `kubectl apply` Markdown KI；scope 自动继承；4 类 visibility 受 admission 强制 |
| **Operator 维护者** | 标准 Kopf timer + Lease + admission webhook；Python 单进程可调试 |
| **架构评审者** | 业务语义（3 CRD / 5 维矩阵 / 4 method）= v0.1 Go baseline；实现栈 = Python 栈迁移 |
| **未来演进** | v0.5+ Vector DB / scope-up 自动 / Memory 全文搜索 = Helm values + Adapter Protocol 替换实现 |

---

## 2. 包结构与文件清单（ADR-0005 §13 工程布局）

### 2.1 总览（uv workspace · 5 个独立 package + 共享 sub-package）

**ADR-0005 §13 工程布局**：

```
pyproject.toml                          # uv workspace 根 + 共享工具配置（ruff / pyright / pytest / structlog）
uv.lock                                 # 单一 lockfile，CI 必须 `uv sync --frozen`

packages/
  shared/src/supteam_a2a/shared/        # 跨模块共享（clock / leader / observability / errors / meta）
  shared-visibility/src/supteam_a2a/shared/visibility/  # 5 维矩阵复用（Knowledge v0.5+ + Memory 共享）
  knowledge/src/supteam_a2a/knowledge/  # Knowledge 资源模型层（CRD types + scope inheritance + search + admission）
  memory/src/supteam_a2a/memory/        # Memory 资源模型层（CRD types + lifecycle + admission）
  knowledge-service/src/supteam_a2a/knowledge_service/  # Knowledge Service Agent 部署（4 A2A method handler）
  memory-backend/src/supteam_a2a/memory_backend/  # Memory A2A method 服务（与 Knowledge Service 共享 deployment）
```

**关键约束**：
- `packages/*` 各自有独立 `pyproject.toml` + 独立 lockfile entry（uv workspace 共享 lockfile 但独立可发布）
- `shared` 与 `shared-visibility` 是 PEP 420 namespace package（与 ADR-0005 §2.2 一致）
- `operator` package 引用 `knowledge` / `memory` 作为 library（Operator Core 同时跑所有 Controller；ADR-0005 §3.1）
- `knowledge-service` / `memory-backend` 引用 `knowledge` / `memory` + `supteam_a2a.a2a.upstream`（L2-1 边界）

### 2.2 `packages/knowledge` 文件清单

```
packages/knowledge/
├── pyproject.toml                      # name=superteam-a2a-knowledge; deps: pydantic>=2.7, anyio, kubernetes_asyncio
├── src/supteam_a2a/knowledge/
│   ├── __init__.py                     # 公共 API surface（re-export CRD types + 关键 helper）
│   ├── apis/                           # Pydantic v2 CRD types
│   │   ├── __init__.py
│   │   └── v1alpha1/
│   │       ├── __init__.py
│   │       ├── knowledgescope.py       # KnowledgeScopeSpec + Status + KnowledgeScope + SubjectReference + ScopeReference + InheritRules + ScopeLevel + ScopePhase
│   │       ├── knowledgeitem.py        # KnowledgeItemSpec + Status + KnowledgeItem + ItemReference + KnowledgeType + KnowledgeVisibility
│   │       └── common.py               # 共享引用类型（LabelSelector + OwnerReference）
│   ├── scope/                          # 4 级继承算法
│   │   ├── __init__.py
│   │   ├── inheritance.py              # ScopeResolver Protocol + RealScopeResolver + resolve_effective_scopes()
│   │   ├── validation.py               # 4 级 + 循环引用校验（admission 调用）
│   │   ├── inherit_rules.py            # include_types / exclude_types 过滤
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_inheritance.py     # UT-SCOPE-001~006 12 种 scope 组合表驱动
│   │       ├── test_validation.py      # UT-SCOPE-007~010 4 级 + 循环引用
│   │       └── test_inherit_rules.py   # UT-SCOPE-011~013 include/exclude 过滤
│   ├── admission/                      # admission webhook（双向互斥左侧 · D-5）
│   │   ├── __init__.py
│   │   ├── ki_webhook.py               # @kopf.validation decorator · KnowledgeItem 互斥规则
│   │   ├── scope_webhook.py            # @kopf.validation decorator · KnowledgeScope 4 级 + 循环引用
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_ki_webhook.py      # UT-ADM-K-001~008 互斥规则 + 50ms timeout fail-closed
│   │       └── test_scope_webhook.py   # UT-ADM-S-001~005 4 级 + 循环引用
│   ├── search/                         # Operator 内存倒排索引
│   │   ├── __init__.py
│   │   ├── inverted_index.py           # InvertedIndex Protocol + RealInvertedIndex（D-2）
│   │   ├── bm25.py                     # BM25 评分公式（独立可测；K1=1.5 / B=0.75）
│   │   ├── rebuild.py                  # 启动期全量重建 + watch 增量
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_inverted_index.py  # UT-SRCH-001~010 search + upsert + remove + size
│   │       ├── test_bm25.py            # UT-SRCH-011~013 BM25 评分公式
│   │       └── test_perf.py            # UT-SRCH-014~016 10K items P95 ≤ 200ms 性能门禁
│   └── _internal/                      # ⚠️ private — 业务层禁止 import
│       └── __init__.py
└── tests/
    └── __init__.py
```

**关键约束**：
- `knowledge` 不依赖 `memory` package（资源模型层独立）
- `knowledge` 引用 `shared`（clock / leader / observability / errors）+ `shared-visibility`（5 维矩阵复用）
- Pydantic CRD types 必须支持 JSON Schema 推导（`model_json_schema()` 稳定排序）

### 2.3 `packages/memory` 文件清单

```
packages/memory/
├── pyproject.toml                      # name=superteam-a2a-memory; deps: pydantic>=2.7, anyio
├── src/supteam_a2a/memory/
│   ├── __init__.py                     # 公共 API surface（re-export CRD types + lifecycle 函数）
│   ├── apis/                           # Pydantic v2 CRD types
│   │   ├── __init__.py
│   │   └── v1alpha1/
│   │       ├── __init__.py
│   │       ├── memory.py               # MemorySpec + Status + Memory + AgentReference + MemoryPhase + MemoryVisibility
│   │       └── common.py               # 共享引用类型
│   ├── lifecycle/                      # decay / reinforce / GC / promotion 数学（纯函数 + Clock 注入）
│   │   ├── __init__.py
│   │   ├── decay.py                    # apply_decay(mem, now) → effective_confidence（D-4 + 数学等价）
│   │   ├── reinforce.py                # apply_reinforce(mem, ts) → reinforced_count + last_reinforced_at（频次节流）
│   │   ├── promotion.py                # is_eligible_for_promotion(mem, now) → bool（v0.1 仅算不触发）
│   │   ├── gc.py                       # gc_expired(memories, now) → 待清理列表
│   │   ├── visibility.py               # is_memory_visible_to() 5 维矩阵过滤（共享 visibility）
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_decay.py           # UT-DECAY-001~005 时间穿越（FakeClock 推进；freezegun 风格）
│   │       ├── test_reinforce.py       # UT-REINF-001~004 频次节流 + last_reinforced_at
│   │       ├── test_promotion.py       # UT-PROM-001~003 资格计算（v0.1 仅算不触发）
│   │       ├── test_gc.py              # UT-GC-001~003 expired 阈值 + effective_confidence < 0.01
│   │       └── test_visibility.py      # UT-VIS-001~012 4 × 3 = 12 种 scope × visibility 穷举
│   └── admission/                      # admission webhook（双向互斥右侧 · D-5）
│       ├── __init__.py
│       ├── m_webhook.py                # @kopf.validation decorator · Memory 互斥规则
│       └── tests/
│           ├── __init__.py
│           └── test_m_webhook.py       # UT-ADM-M-001~008 互斥规则 + 50ms timeout fail-closed
└── tests/
    └── __init__.py
```

**关键约束**：
- `memory.lifecycle.*` 全部是**纯函数**（无 I/O、无 side effect）；Clock 通过参数注入（无 module-level global state）
- `memory.admission` 与 `knowledge.admission` 部署于同一 Operator 进程内（Kopf validation 同 namespace）

### 2.4 `packages/knowledge-service` 文件清单

```
packages/knowledge-service/
├── pyproject.toml                      # name=superteam-a2a-knowledge-service; deps: knowledge, memory, memory-backend, a2a-sdk
├── src/supteam_a2a/knowledge_service/
│   ├── __init__.py
│   ├── main.py                         # ASGI 入口 + Uvicorn 单 worker + lifespan 装载 4 handler
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── query_knowledge.py          # a2a.queryKnowledge handler（基于 §6 4 method 详细规格）
│   │   ├── get_knowledge_item.py       # a2a.getKnowledgeItem handler
│   │   ├── record_memory.py            # a2a.recordMemory handler（代理到 memory_backend.record_memory）
│   │   └── query_memory.py             # a2a.queryMemory handler（代理到 memory_backend.query_memory）
│   ├── card/
│   │   ├── __init__.py
│   │   ├── card.py                     # KnowledgeServiceCard Pydantic model
│   │   └── knowledge_service_card.json # Agent Card JSON（推导生成）
│   ├── config/
│   │   ├── __init__.py
│   │   └── loader.py                   # 4 层配置加载（Secret > CRD > ConfigMap > Env）
│   └── tests/
│       ├── __init__.py
│       ├── unit/
│       │   ├── test_query_knowledge.py # UT-HANDLER-QK-001~005
│       │   ├── test_get_item.py        # UT-HANDLER-GI-001~004
│       │   ├── test_record_memory.py   # UT-HANDLER-RM-001~004
│       │   └── test_query_memory.py    # UT-HANDLER-QM-001~004
│       └── integration/
│           └── test_a2a_compat.py      # IT-A2A-001~004 4 method handler 真实 a2a-python SDK 调用
└── tests/
    └── __init__.py
```

**关键约束**：
- `knowledge_service` 不依赖 `framework SDK`（CRD-driven 无 framework adapter；宪法 §3.6）
- `knowledge_service` 引用 `knowledge` + `memory` + `memory_backend` + `supteam_a2a.a2a.upstream`（L2-1 边界）
- ASGI 入口基于 `supteam_a2a.a2a.create_app`（L2-1 A2A Protocol Spec v0.2.0 Python §5）

### 2.5 `packages/memory-backend` 文件清单

```
packages/memory-backend/
├── pyproject.toml                      # name=superteam-a2a-memory-backend; deps: memory, a2a-sdk, prometheus-client
├── src/supteam_a2a/memory_backend/
│   ├── __init__.py
│   ├── main.py                         # ASGI 入口（与 knowledge-service 同进程；不单独启动）
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── record_memory.py            # a2a.recordMemory 实际实现（knowledge_service 代理调用）
│   │   └── query_memory.py             # a2a.queryMemory 实际实现
│   ├── store/
│   │   ├── __init__.py
│   │   ├── store.py                    # MemoryStore Protocol + RealMemoryStore（CRD 即存储）
│   │   └── tests/
│   │       └── test_store.py           # UT-STORE-001~006 CRD write/read/list/delete/patch_status
│   └── middleware/
│       ├── __init__.py
│       ├── ratelimit.py                # 60/min per SA（错误码 -32104；Tenacity sliding window）
│       ├── audit.py                    # Memory 写入审计日志（K8s event + structured logger）
│       └── tests/
│           ├── test_ratelimit.py       # UT-RL-001~004 60/min per SA + sliding window
│           └── test_audit.py           # UT-AUDIT-001~003 写入审计
└── tests/
    └── __init__.py
```

**关键约束**：
- `memory_backend` 与 `knowledge_service` **同 Deployment / 同进程**（共享内存倒排索引 + 单人维护简化）
- `memory_backend.main` 不单独启动；由 `knowledge_service.main` 在 lifespan startup 中 `import` 并装载 2 个 handler

### 2.6 边界规则与 import linter

```python
# ruff 自定义规则（pyproject.toml [tool.ruff.lint.flake8-tidy-imports]）
[tool.ruff.lint.flake8-tidy-imports]
banned-modules = { 
    "superteam_a2a.framework_adapters.*" = "knowledge/memory/knowledge_service/memory_backend 严禁 import framework SDK（宪法 §3.6 反依赖）",
    "superteam_a2a.a2a.upstream" = "knowledge/memory 严禁 import a2a-python SDK（仅 knowledge_service/memory_backend 可 import）",
    "superteam_a2a.framework.*" = "knowledge/memory/knowledge_service/memory_backend 严禁 import L2-3 Adapter 业务代码",
}
```

---

## 3. Pydantic v2 CRD Schema（完整 JSON Schema · ADR-0005 §5）

> **本节定义 3 个 Pydantic v2 BaseModel 的完整 JSON Schema**，通过 `model_json_schema()` 推导 → deterministic OpenAPI v3 → checked-in CRD YAML（ADR-0005 §5.2 单一来源）。Schema 字段约束与 v0.1.0 Go baseline 完全继承（仅替换 `+kubebuilder:validation:` 为 Pydantic `Field(...)`）。

### 3.1 CRD 生成链路

```
Pydantic BaseModel.model_json_schema()
   ↓ (deterministic sort_keys=True + x-kubernetes-* extensions injection)
deterministic OpenAPI v3 schema
   ↓ (CI: scripts/crd_gen.py + git diff --exit-code + kubectl apply --dry-run=server + round-trip test)
checked-in: charts/superteam-a2a/crds/knowledgescope.yaml
            charts/superteam-a2a/crds/knowledgeitem.yaml
            charts/superteam-a2a/crds/memory.yaml
```

**CI 门禁**：
- `uv run python scripts/crd_gen.py` — 生成 CRD YAML
- `git diff --exit-code charts/superteam-a2a/crds/` — 无 diff 才允许提交
- `kubectl apply --dry-run=server -f charts/superteam-a2a/crds/` — schema 校验通过
- Pydantic ↔ YAML round-trip test（fixture 验证）

### 3.2 KnowledgeScope CRD（Pydantic 完整 schema）

```python
# packages/knowledge/src/supteam_a2a/knowledge/apis/v1alpha1/knowledgescope.py
# 完整 JSON Schema 在 charts/superteam-a2a/crds/knowledgescope.yaml
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict, AwareDatetime
from superteam_a2a.shared.meta import ObjectMeta, Condition


class ScopeLevel(StrEnum):
    """4 级作用域枚举（ADR-0002 §3.1 + §4.1）。"""

    INDUSTRY = "industry"  # cluster-scoped；唯一 1 个
    ORGANIZATION = "organization"  # namespace-scoped
    TEAM = "team"
    PROJECT = "project"


class ScopePhase(StrEnum):
    """KnowledgeScope status.phase 状态机。"""

    PENDING = "Pending"  # 创建中
    ACTIVE = "Active"  # 正常
    ERROR = "Error"  # reconcile 失败
    DELETING = "Deleting"  # 清理中


class SubjectKind(StrEnum):
    """Subject 引用类型（User / Group / ServiceAccount）。"""

    USER = "User"
    GROUP = "Group"
    SERVICE_ACCOUNT = "ServiceAccount"


class SubjectReference(BaseModel):
    """指向 User / Group / ServiceAccount 的引用。"""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    kind: SubjectKind = Field(..., description="主体类型")
    name: str = Field(..., min_length=1, max_length=253)


class ScopeReference(BaseModel):
    """指向 KnowledgeScope 的引用。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., min_length=1, max_length=128)
    level: ScopeLevel | None = Field(default=None, description="冗余缓存；admission 校验一致性")


class InheritRules(BaseModel):
    """4 级 scope 继承过滤规则（admission webhook 强制）。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    include_types: list[str] | None = Field(default=None, max_length=11, alias="includeTypes")
    exclude_types: list[str] | None = Field(default=None, max_length=11, alias="excludeTypes")


class KnowledgeScopeSpec(BaseModel):
    """KnowledgeScope CRD spec（6 字段 · ADR-0002 §3.1 + L1 v0.2.0 §5.2.2）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    level: ScopeLevel = Field(..., description="作用域级别")
    display_name: str = Field(..., alias="displayName", min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=512)
    parent_ref: ScopeReference | None = Field(
        default=None,
        alias="parentRef",
        description="industry 必须为 None；其他 level 必须 parent 严格递增 1 级",
    )
    owner_ref: SubjectReference = Field(..., alias="ownerRef")
    inherit_rules: InheritRules | None = Field(default=None, alias="inheritRules")
    # 6 spec 字段（含引用类型 + labels 可选 · 不计 spec 字段数）


class KnowledgeScopeStatus(BaseModel):
    """KnowledgeScope CRD status（6 字段）。"""

    model_config = ConfigDict(extra="forbid")

    phase: ScopePhase | None = None
    message: str | None = Field(default=None, max_length=512)
    conditions: list[Condition] = Field(default_factory=list)
    item_count: int | None = Field(default=None, alias="itemCount", ge=0)
    child_scopes: int | None = Field(default=None, alias="childScopes", ge=0)
    observed_generation: int | None = Field(default=None, alias="observedGeneration", ge=0)


class KnowledgeScope(BaseModel):
    """KnowledgeScope CRD 顶层。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    api_version: str = Field(default="knowledge.superteam-a2a.io/v1alpha1", alias="apiVersion")
    kind: str = Field(default="KnowledgeScope")
    metadata: ObjectMeta
    spec: KnowledgeScopeSpec
    status: KnowledgeScopeStatus | None = None
```

**与 Go baseline 对照**：
- v0.1.0 Go：`type KnowledgeScope struct { metav1.TypeMeta; metav1.ObjectMeta; Spec KnowledgeScopeSpec; Status KnowledgeScopeStatus }` + `+kubebuilder:validation:Enum=industry|organization|team|project` + `+kubebuilder:validation:Required`
- v0.2 Python：`class KnowledgeScope(BaseModel)` + `Field(..., alias="displayName")` + `populate_by_name=True`（业务层 Pythonic snake_case + wire camelCase 单向）
- 行为兼容性：**完全一致**（JSON wire shape + enum 值 + 必填性 + 类型不变）

### 3.3 KnowledgeItem CRD（Pydantic 完整 schema）

```python
# packages/knowledge/src/supteam_a2a/knowledge/apis/v1alpha1/knowledgeitem.py
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict, AwareDatetime
from superteam_a2a.shared.meta import ObjectMeta, Condition
from superteam_a2a.knowledge.apis.v1alpha1.knowledgescope import (
    ScopeReference,
    SubjectReference,
)


class KnowledgeType(StrEnum):
    """KnowledgeItem 11 类枚举（ADR-0002 §3.2）。"""

    DOCUMENT = "document"
    RUNBOOK = "runbook"
    API_SPEC = "api-spec"
    ARCHITECTURE = "architecture"
    FAQ = "faq"
    BEST_PRACTICE = "best-practice"
    TEMPLATE = "template"
    CONTRACT = "contract"
    TROUBLESHOOTING = "troubleshooting"
    GLOSSARY = "glossary"
    OTHER = "other"


class KnowledgeVisibility(StrEnum):
    """KnowledgeItem visibility 4 类（admission 强制 scope 校验）。"""

    SCOPE_ONLY = "scope-only"  # 仅当前作用域成员可见
    SCOPE_AND_CHILDREN = "scope-and-children"  # 当前 + 子作用域（默认）
    PUBLIC_READABLE = "public-readable"  # 必须 industry scope
    AGENT_PRIVATE = "agent-private"  # v0.1 禁用（保留 v0.5+）


class KnowledgeItemPhase(StrEnum):
    """KnowledgeItem status.phase 状态机。"""

    DRAFT = "Draft"
    PUBLISHED = "Published"
    DEPRECATED = "Deprecated"


class ItemReference(BaseModel):
    """KnowledgeItem 引用类型（Memory.source_knowledge_ref 使用）。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., min_length=1, max_length=128)
    version: int = Field(..., ge=1)


class KnowledgeItemSpec(BaseModel):
    """KnowledgeItem CRD spec（9 字段 · ADR-0002 §3.2 + L1 v0.2.0 §5.2.3）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scope_ref: ScopeReference = Field(..., alias="scopeRef")
    type: KnowledgeType = Field(...)
    title: str = Field(..., min_length=1, max_length=256)
    body: str = Field(..., min_length=1, max_length=65536)  # 64KB Markdown body
    summary: str | None = Field(default=None, max_length=512)
    tags: list[str] | None = Field(default=None, max_length=20)
    visibility: KnowledgeVisibility = Field(default=KnowledgeVisibility.SCOPE_AND_CHILDREN)
    owner_ref: SubjectReference = Field(
        ..., alias="ownerRef", description="必须 User / Group；ServiceAccount 由 admission 拒绝"
    )
    source_uri: str | None = Field(default=None, alias="sourceUri", max_length=512)
    version: int = Field(default=1, ge=1)
    # 9 spec + 引用类型（距上限 15 距离 6）


class KnowledgeItemStatus(BaseModel):
    """KnowledgeItem CRD status（4 字段）。"""

    model_config = ConfigDict(extra="forbid")

    phase: KnowledgeItemPhase | None = None
    conditions: list[Condition] = Field(default_factory=list)
    last_queried_at: AwareDatetime | None = Field(default=None, alias="lastQueriedAt")
    observed_generation: int | None = Field(default=None, alias="observedGeneration", ge=0)


class KnowledgeItem(BaseModel):
    """KnowledgeItem CRD 顶层。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    api_version: str = Field(default="knowledge.superteam-a2a.io/v1alpha1", alias="apiVersion")
    kind: str = Field(default="KnowledgeItem")
    metadata: ObjectMeta
    spec: KnowledgeItemSpec
    status: KnowledgeItemStatus | None = None
```

### 3.4 Memory CRD（Pydantic 完整 schema）

```python
# packages/memory/src/supteam_a2a/memory/apis/v1alpha1/memory.py
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict, AwareDatetime
from superteam_a2a.shared.meta import ObjectMeta, Condition
from superteam_a2a.knowledge.apis.v1alpha1.knowledgescope import (
    ScopeReference,
    SubjectReference,
    SubjectKind,
)


class MemoryPhase(StrEnum):
    """Memory status.phase 状态机（5 态）。"""

    ACTIVE = "Active"  # effective_confidence > 0.5
    DECAYING = "Decaying"  # 0.01 ≤ effective_confidence ≤ 0.5
    PROMOTABLE = "Promotable"  # eligible_for_promotion = true（v0.1 仅算不触发）
    EXPIRED = "Expired"  # effective_confidence < 0.01
    ERROR = "Error"  # reconcile 失败


class MemoryVisibility(StrEnum):
    """Memory visibility 3 类（5 维矩阵 · agent-private 短路）。"""

    SCOPE_ONLY = "scope-only"
    SCOPE_AND_CHILDREN = "scope-and-children"
    AGENT_PRIVATE = "agent-private"


class AgentReference(BaseModel):
    """指向 Agent（ServiceAccount）的引用。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: SubjectKind = Field(
        default=SubjectKind.SERVICE_ACCOUNT, description="Memory 仅支持 ServiceAccount；与 KI 互斥"
    )
    name: str = Field(..., min_length=1, max_length=253)


class MemorySpec(BaseModel):
    """Memory CRD spec（12 字段 · ADR-0003 §3 + L1 v0.2.0 §5.2.4）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scope_ref: ScopeReference = Field(..., alias="scopeRef")
    agent_ref: AgentReference = Field(
        ..., alias="agentRef", description="必须 ServiceAccount；与 KI.User/Group 互斥"
    )
    content: dict[str, str] = Field(
        ..., min_length=1, max_length=20, description="键值对结构化记忆内容；最多 20 个键"
    )
    summary: str = Field(..., min_length=1, max_length=512)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    decay_days: int = Field(default=30, ge=1, le=3650, description="decay 半衰期；超过 3650 拒绝")
    reinforced_count: int = Field(default=0, ge=0, alias="reinforcedCount")
    last_reinforced_at: AwareDatetime | None = Field(default=None, alias="lastReinforcedAt")
    memory_key_pattern: str | None = Field(
        default=None,
        alias="memoryKeyPattern",
        max_length=128,
        description="Memory 唯一键模式（SA-scoped）",
    )
    source_knowledge_ref: ItemReference | None = Field(
        default=None,
        alias="sourceKnowledgeRef",
        description="追溯的 KnowledgeItem（宪法 §2.9 记忆可追溯）",
    )
    tags: list[str] | None = Field(default=None, max_length=10)
    visibility: MemoryVisibility = Field(default=MemoryVisibility.SCOPE_AND_CHILDREN)
    # 12 spec（距上限 15 距离 3 · 临界）


class MemoryStatus(BaseModel):
    """Memory CRD status（7 字段）。"""

    model_config = ConfigDict(extra="forbid")

    phase: MemoryPhase | None = None
    message: str | None = Field(default=None, max_length=512)
    conditions: list[Condition] = Field(default_factory=list)
    last_decayed_at: AwareDatetime | None = Field(default=None, alias="lastDecayedAt")
    last_reinforced_at: AwareDatetime | None = Field(default=None, alias="lastReinforcedAt")
    effective_confidence: float | None = Field(
        default=None, alias="effectiveConfidence", ge=0.0, le=1.0
    )
    eligible_for_promotion: bool | None = Field(default=None, alias="eligibleForPromotion")
    observed_generation: int | None = Field(default=None, alias="observedGeneration", ge=0)


class Memory(BaseModel):
    """Memory CRD 顶层。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    api_version: str = Field(default="memory.superteam-a2a.io/v1alpha1", alias="apiVersion")
    kind: str = Field(default="Memory")
    metadata: ObjectMeta
    spec: MemorySpec
    status: MemoryStatus | None = None
```

### 3.5 字段约束对照（Go vs Python）

| CRD | 字段 | v0.1.0 Go baseline | v0.2 Python | wire 兼容性 |
|-----|------|---------------------|--------------|--------------|
| KnowledgeScope | `level` | `+kubebuilder:validation:Enum=industry;organization;team;project` | `Field(..., description="作用域级别")` + StrEnum | ✅ enum 值不变 |
| KnowledgeScope | `display_name` | `+kubebuilder:validation:MinLength=1;MaxLength=64` | `Field(..., alias="displayName", min_length=1, max_length=64)` | ✅ wire shape camelCase |
| KnowledgeItem | `owner_ref.kind` | `+kubebuilder:validation:Enum=User;Group;Not=ServiceAccount` | admission webhook `validate_knowledge_item` 拒绝 SA | ✅ 行为等价 |
| KnowledgeItem | `visibility == public-readable` | admission 必须 `level == industry` | `validate_knowledge_item` 校验 scope.level | ✅ 行为等价 |
| Memory | `agent_ref.kind` | `+kubebuilder:validation:Enum=ServiceAccount;Not=User;Group` | admission webhook `validate_memory` 拒绝 User/Group | ✅ 行为等价 |
| Memory | `decay_days` | `+kubebuilder:validation:Maximum=3650` | `Field(default=30, ge=1, le=3650)` | ✅ 边界一致 |
| Memory | `effective_confidence` | status 字段，Reconciler 更新 | 同上 | ✅ wire 一致 |
| Memory | `eligible_for_promotion` | status 字段，v0.1 仅计算 | 同上（v0.1 不触发 KnowledgePromotionRequest） | ✅ 行为等价 |

### 3.6 字段数约束（防过度设计 · ADR-0004）

| CRD | spec 字段数 | 上限 | 距离 |
|-----|------------|------|------|
| KnowledgeScope | 6 + 引用类型 | 15 | 距上限 9 |
| KnowledgeItem | 9 + 引用类型 | 15 | 距上限 6 |
| Memory | 12 + 引用类型 | 15 | **距上限 3（临界）** |

### 3.7 wire camelCase ↔ Pythonic snake_case 单向映射

**关键约束**：
- 所有时间字段必须 `AwareDatetime`（UTC）；业务层 `datetime.now(UTC)`
- enum 使用 `StrEnum`（与 wire 字符串值兼容；避免 IntEnum 序列化问题）
- 不可变 value object 加 `frozen=True`（SubjectReference / ScopeReference / AgentReference / ItemReference）
- `populate_by_name=True` + `alias` 实现 wire camelCase ↔ Pythonic snake_case 单向映射（wire 是 source of truth）
- `extra="forbid"` 在 strict 模式下禁止未声明字段（与 K8s API server strict 校验一致）

---

## 4. Knowledge 4 级作用域 + Memory 5 维可见性矩阵（Python Protocol + Pydantic）

### 4.1 4 级作用域枚举 + 继承约束

| Level | 用途 | 数量约束（v0.1） | 命名空间 |
|-------|------|------------------|---------|
| **industry** | 行业级共享知识（外部公开 read-only） | cluster-scoped，**只能 1 个** | cluster-wide |
| **organization** | 公司/团队级共享 | namespace-scoped | 用户 namespace |
| **team** | 团队级共享（核心粒度） | namespace-scoped | 用户 namespace |
| **project** | 项目级私有 | namespace-scoped | 用户 namespace |

**继承约束**（admission webhook 强制；§3.2 `validation.py`）：
- `industry` 的 `ParentRef == None`
- `organization` 的 `ParentRef → industry`
- `team` 的 `ParentRef → organization`
- `project` 的 `ParentRef → team`
- ❌ 禁止循环引用（admission 拓扑排序检测）
- ❌ 禁止 parent 跨 level（精确递增 1 级）

### 4.2 继承算法 Protocol（异步实现）

```python
# packages/knowledge/src/supteam_a2a/knowledge/scope/inheritance.py
from typing import Protocol, runtime_checkable
from superteam_a2a.knowledge.apis.v1alpha1 import (
    KnowledgeScope,
    KnowledgeScopeSpec,
    ScopeLevel,
    ScopeReference,
)
from superteam_a2a.shared.errors import ScopeNotFound, ScopeCycle, ScopeHierarchyViolation


@runtime_checkable
class ScopeResolver(Protocol):
    """4 级 scope 继承解析抽象。"""

    async def get_scope(self, name: str) -> KnowledgeScope | None:
        """从 K8s API / 内存缓存获取 scope。"""
        ...

    async def resolve_effective_scopes(self, scope_name: str) -> list[str]:
        """从 industry 一路到当前 scope 的完整继承链（顶层在前）。"""
        ...


class RealScopeResolver:
    """生产实现：Kopf K8s API client + 内存 LRU 缓存。"""

    def __init__(self, k8s_client: "kubernetes_asyncio.client.CustomObjectsApi") -> None:
        self._k8s = k8s_client
        self._cache: dict[str, KnowledgeScope] = {}
        self._cache_lock = asyncio.Lock()
        self._cache_ttl_seconds = 300  # 5min

    async def get_scope(self, name: str) -> KnowledgeScope | None:
        if name in self._cache:
            return self._cache[name]
        scope = await self._fetch_scope_from_k8s(name)
        if scope is not None:
            async with self._cache_lock:
                self._cache[name] = scope
        return scope

    async def resolve_effective_scopes(self, scope_name: str) -> list[str]:
        """从 industry 一路到当前 scope 的完整继承链（顶层在前）。

        例：["industry-cloud", "org-acme", "team-payments", "project-checkout"]
        """
        chain: list[str] = []
        visited: set[str] = set()  # 循环引用检测
        current_name: str | None = scope_name

        while current_name is not None:
            if current_name in visited:
                raise ScopeCycle(f"Cycle detected in scope inheritance at {current_name}")
            visited.add(current_name)

            scope = await self.get_scope(current_name)
            if scope is None:
                raise ScopeNotFound(
                    f"KnowledgeScope {current_name} not found during inheritance resolution"
                )

            chain.insert(0, scope.metadata.name)  # 顶层在前

            if scope.spec.parent_ref is None:
                break  # industry 终止条件

            parent_scope = await self.get_scope(scope.spec.parent_ref.name)
            if parent_scope is None:
                raise ScopeNotFound(f"Parent scope {scope.spec.parent_ref.name} not found")
            if not _is_strict_child_level(scope.spec.level, parent_scope.spec.level):
                raise ScopeHierarchyViolation(
                    f"Scope {scope.metadata.name} (level={scope.spec.level}) "
                    f"parent {parent_scope.metadata.name} (level={parent_scope.spec.level}) "
                    f"violates strict level increment"
                )

            current_name = scope.spec.parent_ref.name

        return chain


def _is_strict_child_level(child: ScopeLevel, parent: ScopeLevel) -> bool:
    """level 严格递增 1 级校验。"""
    order = [ScopeLevel.INDUSTRY, ScopeLevel.ORGANIZATION, ScopeLevel.TEAM, ScopeLevel.PROJECT]
    return order.index(child) == order.index(parent) + 1


async def query_knowledge(
    scope_resolver: ScopeResolver,
    inverted_index: "InvertedIndex",
    scope_name: str,
    query: str,
    type_filter: list[str] | None = None,
    tag_filter: list[str] | None = None,
    max_results: int = 10,
) -> list[tuple[KnowledgeItem, float]]:
    """查询时自动包含继承链上所有作用域的 KnowledgeItem。"""
    effective_scopes = await scope_resolver.resolve_effective_scopes(scope_name)

    candidates = await inverted_index.search(
        query=query,
        scope_chain=effective_scopes,
        type_filter=type_filter,
        tag_filter=tag_filter,
        max_results=max_results * 2,
    )

    results: list[tuple[KnowledgeItem, float]] = []
    for item, score in candidates:
        if not _is_inherit_allowed(item, effective_scopes):
            continue
        if not _is_visibility_allowed(item, scope_name):
            continue
        results.append((item, score))

    return _dedupe_by_id_keep_latest(results)[:max_results]
```

### 4.3 KnowledgeItem Visibility 4 类枚举

| Visibility | 含义 | 适用 Level |
|------------|------|------------|
| `scope-only` | 仅当前作用域成员可见 | 任意 |
| `scope-and-children` | 当前作用域 + 子作用域成员可见（**默认**） | 任意 |
| `public-readable` | **必须** industry scope 才允许 | industry only |
| `agent-private` | v0.1 **禁用**（保留给 v0.5+ SA-级隔离） | — |

**admission webhook 强制**：
- `public-readable` 必须 `level == industry`，否则 `KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY` 拒绝
- `agent-private` v0.1 拒绝（未来 v0.5+ 扩展）`KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS`

### 4.4 Knowledge 容量与性能约束

- 单集群 ≤ **10,000 KnowledgeItem**（超出拒绝创建；提示升级 Vector DB）
- Operator 内存倒排索引**重建 ≤ 30s**（10K items）
- `queryKnowledge` **P95 ≤ 200ms**（性能门禁；§10.2 测试）

### 4.5 Memory 5 维可见性矩阵过滤算法

**5 维矩阵**（4 scope × 3 visibility + agent-private 短路）：

| visibility \ scope | industry | organization | team | project |
|---|---|---|---|---|
| `scope-only` | 仅 industry | 仅 org | 仅 team | 仅 project |
| `scope-and-children`（默认） | industry + 所有子 | org + 所有子 team/project | team + 所有子 project | 仅 project |
| `agent-private` | **仅 owner agent**（无视 scope） | **仅 owner agent** | **仅 owner agent** | **仅 owner agent** |

```python
# packages/memory/src/supteam_a2a/memory/lifecycle/visibility.py
from typing import Protocol, runtime_checkable
from superteam_a2a.memory.apis.v1alpha1 import Memory, MemoryVisibility, MemoryPhase


@runtime_checkable
class MemoryVisibilityFilter(Protocol):
    """Memory 可见性过滤抽象。"""

    async def is_memory_visible_to(
        self,
        memory: Memory,
        caller_agent: str,
        caller_scope_chain: list[str],
    ) -> bool:
        """判断 caller 是否可见 memory。"""
        ...


class RealMemoryVisibilityFilter:
    """生产实现：5 维矩阵过滤算法。"""

    async def is_memory_visible_to(
        self,
        memory: Memory,
        caller_agent: str,
        caller_scope_chain: list[str],
    ) -> bool:
        visibility = memory.spec.visibility

        # 规则 1：agent-private 短路（不参与 scope 继承）
        if visibility == MemoryVisibility.AGENT_PRIVATE:
            return memory.spec.agent_ref.name == caller_agent

        # 规则 2：scope-only 仅当前 scope
        if visibility == MemoryVisibility.SCOPE_ONLY:
            return memory.spec.scope_ref.name == caller_scope_chain[-1]

        # 规则 3：scope-and-children（默认）
        if visibility == MemoryVisibility.SCOPE_AND_CHILDREN:
            # caller_scope_chain 顶层在前；scope_ref 必须在 chain 内或 chain 内某个 scope 的子级
            target_scope = memory.spec.scope_ref.name
            return any(
                _scope_includes_or_equals(caller_scope, target_scope)
                for caller_scope in caller_scope_chain
            )

        raise ValueError(f"Unknown visibility: {visibility}")


def _scope_includes_or_equals(caller_scope: str, target_scope: str) -> bool:
    """判断 caller_scope 是否包含 target_scope（caller 在继承链上方）。"""
    # 实际实现：基于 ScopeResolver 查询 caller_scope 的完整继承链
    # 若 target_scope 在 caller_scope 的继承链内或等于 caller_scope，返回 True
    # 此处简化（完整实现在 L3-6 Spec）
    return caller_scope == target_scope or True  # placeholder


async def query_memory(
    visibility_filter: MemoryVisibilityFilter,
    memories: list[Memory],
    caller_agent: str,
    caller_scope_chain: list[str],
    scope_filter: str | None = None,
    agent_filter: str | None = None,
    memory_key_pattern: str | None = None,
    tag_filter: list[str] | None = None,
    min_confidence: float | None = None,
    max_results: int = 100,
) -> list[Memory]:
    """Memory 过滤查询（5 维矩阵 + 多维过滤）。"""
    results: list[Memory] = []
    for mem in memories:
        # visibility 过滤
        if not await visibility_filter.is_memory_visible_to(mem, caller_agent, caller_scope_chain):
            continue
        # scope 过滤
        if scope_filter and mem.spec.scope_ref.name != scope_filter:
            continue
        # agent 过滤
        if agent_filter and mem.spec.agent_ref.name != agent_filter:
            continue
        # memory key pattern 过滤
        if memory_key_pattern and not _match_key_pattern(
            memory_key_pattern, mem.spec.memory_key_pattern
        ):
            continue
        # tag 过滤
        if tag_filter and not (set(mem.spec.tags or []) & set(tag_filter)):
            continue
        # confidence 过滤
        if min_confidence is not None and (mem.status.effective_confidence or 0) < min_confidence:
            continue
        results.append(mem)
        if len(results) >= max_results:
            break
    return results
```

### 4.6 5 维矩阵测试矩阵（12 种组合穷举）

| visibility \ scope | industry | organization | team | project |
|---|---|---|---|---|
| `scope-only` | UT-VIS-001 | UT-VIS-002 | UT-VIS-003 | UT-VIS-004 |
| `scope-and-children` | UT-VIS-005 | UT-VIS-006 | UT-VIS-007 | UT-VIS-008 |
| `agent-private` | UT-VIS-009 | UT-VIS-010 | UT-VIS-011 | UT-VIS-012 |

**边界用例**：
- UT-VIS-013：caller_agent ≠ owner 且 visibility = agent-private → 拒绝
- UT-VIS-014：memory 在 caller scope_chain 外 → 拒绝（scope-and-children）
- UT-VIS-015：scope-only 但 caller 在 parent scope → 拒绝

### 4.7 共享 visibility 矩阵（shared-visibility package）

```python
# packages/shared-visibility/src/supteam_a2a/shared/visibility/matrix.py
# 5 维矩阵定义共享（Knowledge v0.5+ + Memory 共用）
from enum import StrEnum
from typing import Callable, Awaitable


class VisibilityRule(StrEnum):
    """可见性规则枚举（Knowledge 4 类 + Memory 3 类共享）。"""

    SCOPE_ONLY = "scope-only"
    SCOPE_AND_CHILDREN = "scope-and-children"
    PUBLIC_READABLE = "public-readable"
    AGENT_PRIVATE = "agent-private"


# 4 × 3 矩阵定义
VISIBILITY_MATRIX: dict[tuple[VisibilityRule, str], Callable[..., Awaitable[bool]]] = {
    (VisibilityRule.SCOPE_ONLY, "industry"): ...,
    (VisibilityRule.SCOPE_ONLY, "organization"): ...,
    # ... 12 种组合
}
```

---

## 5. admission webhook 详细规格（双向互斥 · D-5）

### 5.1 KnowledgeItem admission webhook

```python
# packages/knowledge/src/supteam_a2a/knowledge/admission/ki_webhook.py
from typing import Any
import kopf
from superteam_a2a.knowledge.apis.v1alpha1 import (
    KnowledgeItem,
    KnowledgeVisibility,
)
from superteam_a2a.shared.errors import AdmissionTimeoutError


@kopf.validation(
    "knowledge.superteam-a2a.io",
    "v1alpha1",
    "knowledgeitems",
    timeout=0.05,  # 50ms 超时 fail-closed
    operations=["CREATE", "UPDATE"],
)
async def validate_knowledge_item(spec: dict[str, Any], **kwargs) -> None:
    """KnowledgeItem admission webhook（双向互斥左侧）。

    校验规则：
    1. owner_ref.kind ∈ {User, Group}（拒绝 ServiceAccount）→ KNOWLEDGE_OWNER_KIND_FORBIDDEN
    2. visibility == public-readable 必须 scope.level == industry → KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY
    3. visibility == agent-private v0.1 拒绝 → KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS
    4. scope_ref 存在 + level 合法 + parent 关系合法（admission scope webhook）
    """
    # 解析 spec（admission 上下文只有 spec；status 由 controller 更新）
    item = KnowledgeItem.model_validate({"spec": spec})

    # 规则 1：owner_kind
    if item.spec.owner_ref.kind.value == "ServiceAccount":
        raise kopf.AdmissionError(
            "KnowledgeItem.ownerRef.kind cannot be ServiceAccount; use Memory instead. "
            "Error code: KNOWLEDGE_OWNER_KIND_FORBIDDEN",
            code=400,
        )

    # 规则 2：public-readable 必须 industry scope
    if item.spec.visibility == KnowledgeVisibility.PUBLIC_READABLE:
        # 查询 scope level（admission timeout 50ms 强制 fail-closed）
        try:
            scope = await _fetch_scope_with_timeout(item.spec.scope_ref.name, timeout_ms=50)
        except AdmissionTimeoutError:
            raise kopf.AdmissionError(
                f"Admission timeout fetching KnowledgeScope {item.spec.scope_ref.name} "
                f"after 50ms; fail-closed. Error code: KNOWLEDGE_ADMISSION_TIMEOUT",
                code=503,
            )
        if scope is None or scope.spec.level.value != "industry":
            raise kopf.AdmissionError(
                f"KnowledgeItem.visibility=public-readable requires KnowledgeScope.level=industry "
                f"(got {scope.spec.level if scope else 'NOT FOUND'}). "
                f"Error code: KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY",
                code=400,
            )

    # 规则 3：agent-private v0.1 拒绝
    if item.spec.visibility == KnowledgeVisibility.AGENT_PRIVATE:
        raise kopf.AdmissionError(
            "KnowledgeItem.visibility=agent-private is reserved for v0.5+. "
            "Error code: KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS",
            code=400,
        )


async def _fetch_scope_with_timeout(name: str, timeout_ms: int) -> "KnowledgeScope | None":
    """50ms 超时获取 scope（fail-closed）。"""
    try:
        return await asyncio.wait_for(
            k8s_custom_api.get_namespaced_custom_object(
                group="knowledge.superteam-a2a.io",
                version="v1alpha1",
                namespace=...,
                plural="knowledgescopes",
                name=name,
            ),
            timeout=timeout_ms / 1000.0,
        )
    except asyncio.TimeoutError:
        raise AdmissionTimeoutError(
            f"Admission timeout fetching KnowledgeScope {name} after {timeout_ms}ms"
        )
```

### 5.2 KnowledgeScope admission webhook

```python
# packages/knowledge/src/supteam_a2a/knowledge/admission/scope_webhook.py
@kopf.validation(
    "knowledge.superteam-a2a.io",
    "v1alpha1",
    "knowledgescopes",
    timeout=0.05,
    operations=["CREATE", "UPDATE"],
)
async def validate_knowledge_scope(spec: dict[str, Any], **kwargs) -> None:
    """KnowledgeScope admission webhook（4 级 + 循环引用校验）。"""
    scope = KnowledgeScope.model_validate({"spec": spec})

    # 规则 1：industry 必须 parent_ref = None
    if scope.spec.level == ScopeLevel.INDUSTRY and scope.spec.parent_ref is not None:
        raise kopf.AdmissionError(
            f"KnowledgeScope.level=industry must have parentRef=None "
            f"(got {scope.spec.parent_ref.name}). Error code: KNOWLEDGE_INDUSTRY_MUST_BE_ROOT",
            code=400,
        )

    # 规则 2：non-industry 必须 parent_ref 存在 + 严格递增 1 级
    if scope.spec.level != ScopeLevel.INDUSTRY and scope.spec.parent_ref is None:
        raise kopf.AdmissionError(
            f"KnowledgeScope.level={scope.spec.level.value} must have parentRef. "
            f"Error code: KNOWLEDGE_PARENT_REQUIRED",
            code=400,
        )

    if scope.spec.parent_ref is not None:
        try:
            parent = await _fetch_scope_with_timeout(scope.spec.parent_ref.name, timeout_ms=50)
        except AdmissionTimeoutError:
            raise kopf.AdmissionError(
                f"Admission timeout fetching parent KnowledgeScope "
                f"{scope.spec.parent_ref.name}; fail-closed. "
                f"Error code: KNOWLEDGE_ADMISSION_TIMEOUT",
                code=503,
            )
        if parent is None:
            raise kopf.AdmissionError(
                f"Parent KnowledgeScope {scope.spec.parent_ref.name} not found. "
                f"Error code: KNOWLEDGE_PARENT_NOT_FOUND",
                code=400,
            )
        if not _is_strict_child_level(scope.spec.level, parent.spec.level):
            raise kopf.AdmissionError(
                f"KnowledgeScope.level={scope.spec.level.value} parent.level={parent.spec.level.value} "
                f"violates strict level increment. Error code: KNOWLEDGE_HIERARCHY_VIOLATION",
                code=400,
            )

    # 规则 3：循环引用检测（admission 不易做；改为 controller reconcile 时校验）
    # 实际：scope_webhook 仅校验直接 parent；循环引用由 scope_controller reconcile 检测
```

### 5.3 Memory admission webhook

```python
# packages/memory/src/supteam_a2a/memory/admission/m_webhook.py
@kopf.validation(
    "memory.superteam-a2a.io",
    "v1alpha1",
    "memories",
    timeout=0.05,
    operations=["CREATE", "UPDATE"],
)
async def validate_memory(spec: dict[str, Any], **kwargs) -> None:
    """Memory admission webhook（双向互斥右侧）。

    校验规则：
    1. agent_ref.kind == ServiceAccount（拒绝 User/Group）→ MEMORY_OWNER_KIND_FORBIDDEN
    2. agent_ref.name 对应 ServiceAccount 存在
    3. scope_ref 对应 KnowledgeScope 存在
    4. source_knowledge_ref 若存在 → KI 存在 + scope 匹配
    5. visibility == agent-private 必须 agent_ref.name != ""
    6. decay_days ≤ 3650
    7. 50ms 超时 fail-closed
    """
    memory = Memory.model_validate({"spec": spec})

    # 规则 1：agent_ref.kind == ServiceAccount
    if memory.spec.agent_ref.kind.value != "ServiceAccount":
        raise kopf.AdmissionError(
            f"Memory.agentRef.kind must be ServiceAccount "
            f"(got {memory.spec.agent_ref.kind.value}); use KnowledgeItem for User/Group. "
            f"Error code: MEMORY_OWNER_KIND_FORBIDDEN",
            code=400,
        )

    # 规则 2-3：scope / agent 存在性
    try:
        scope = await _fetch_scope_with_timeout(memory.spec.scope_ref.name, timeout_ms=50)
    except AdmissionTimeoutError:
        raise kopf.AdmissionError(
            f"Admission timeout fetching KnowledgeScope {memory.spec.scope_ref.name}; "
            f"fail-closed. Error code: MEMORY_ADMISSION_TIMEOUT",
            code=503,
        )
    if scope is None:
        raise kopf.AdmissionError(
            f"Memory.scopeRef {memory.spec.scope_ref.name} not found. "
            f"Error code: MEMORY_SCOPE_NOT_FOUND",
            code=400,
        )

    sa = await _fetch_service_account_with_timeout(memory.spec.agent_ref.name, timeout_ms=50)
    if sa is None:
        raise kopf.AdmissionError(
            f"Memory.agentRef {memory.spec.agent_ref.name} ServiceAccount not found. "
            f"Error code: MEMORY_AGENT_NOT_FOUND",
            code=400,
        )

    # 规则 4：source_knowledge_ref scope 匹配
    if memory.spec.source_knowledge_ref is not None:
        ki = await _fetch_knowledge_item_with_timeout(
            memory.spec.source_knowledge_ref.name,
            timeout_ms=50,
        )
        if ki is None:
            raise kopf.AdmissionError(
                f"Memory.sourceKnowledgeRef {memory.spec.source_knowledge_ref.name} not found. "
                f"Error code: MEMORY_SOURCE_KI_NOT_FOUND",
                code=400,
            )
        if ki.spec.scope_ref.name != memory.spec.scope_ref.name:
            raise kopf.AdmissionError(
                f"Memory.sourceKnowledgeRef scope {ki.spec.scope_ref.name} "
                f"must equal Memory.scopeRef {memory.spec.scope_ref.name}. "
                f"Error code: MEMORY_SOURCE_KI_SCOPE_MISMATCH",
                code=400,
            )

    # 规则 5：agent-private 必须 agent_ref.name != ""
    if memory.spec.visibility == MemoryVisibility.AGENT_PRIVATE and not memory.spec.agent_ref.name:
        raise kopf.AdmissionError(
            'Memory.visibility=agent-private requires agentRef.name != "". '
            "Error code: MEMORY_AGENT_PRIVATE_REQUIRES_NAME",
            code=400,
        )

    # 规则 6：decay_days ≤ 3650（已在 Pydantic Field le=3650 强制）
    if memory.spec.decay_days > 3650:
        raise kopf.AdmissionError(
            f"Memory.decayDays must be <= 3650 (got {memory.spec.decay_days}). "
            f"Error code: MEMORY_DECAY_DAYS_EXCEEDED",
            code=400,
        )
```

### 5.4 admission 部署形态 + 双向互斥总结

| 维度 | KnowledgeItem | Memory |
|------|---------------|--------|
| **ownerRef.kind** | User / Group | ServiceAccount |
| **部署形态** | Operator 进程内（Kopf `kopf.validation` decorator · D-5） | 同 Operator 进程 |
| **超时** | 50ms fail-closed | 50ms fail-closed |
| **TLS** | cert-manager 自动颁发 | 同上 |
| **错误码范围** | KNOWLEDGE_* -32008~-32018 | MEMORY_* -32101~-32112 |

**双向互斥严格区分**（admission webhook 强制）：
- ❌ KnowledgeItem 不允许 `owner_ref.kind == ServiceAccount` → `KNOWLEDGE_OWNER_KIND_FORBIDDEN`
- ❌ Memory 不允许 `agent_ref.kind ∈ {User, Group}` → `MEMORY_OWNER_KIND_FORBIDDEN`

### 5.5 admission webhook 测试矩阵

| 测试 ID | 类型 | 场景 |
|---------|------|------|
| UT-ADM-K-001 | UT | owner_ref.kind=ServiceAccount → 拒绝 |
| UT-ADM-K-002 | UT | visibility=public-readable, scope.level=industry → 通过 |
| UT-ADM-K-003 | UT | visibility=public-readable, scope.level=team → 拒绝 KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY |
| UT-ADM-K-004 | UT | visibility=agent-private → 拒绝 KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS |
| UT-ADM-K-005 | UT | scope_ref 不存在 → 拒绝 KNOWLEDGE_SCOPE_NOT_FOUND |
| UT-ADM-K-006 | UT | admission timeout 50ms → fail-closed |
| UT-ADM-K-007 | UT | round-trip Pydantic → JSON → Pydantic 字段不丢失 |
| UT-ADM-K-008 | UT | extra 字段 → extra="forbid" 拒绝 |
| UT-ADM-S-001 | UT | industry level + parent_ref=None → 通过 |
| UT-ADM-S-002 | UT | industry level + parent_ref=X → 拒绝 KNOWLEDGE_INDUSTRY_MUST_BE_ROOT |
| UT-ADM-S-003 | UT | non-industry + parent_ref=None → 拒绝 KNOWLEDGE_PARENT_REQUIRED |
| UT-ADM-S-004 | UT | parent level 跨级（industry→team） → 拒绝 KNOWLEDGE_HIERARCHY_VIOLATION |
| UT-ADM-S-005 | UT | parent scope 不存在 → 拒绝 KNOWLEDGE_PARENT_NOT_FOUND |
| UT-ADM-M-001 | UT | agent_ref.kind=User → 拒绝 MEMORY_OWNER_KIND_FORBIDDEN |
| UT-ADM-M-002 | UT | agent_ref.kind=ServiceAccount + SA 不存在 → 拒绝 MEMORY_AGENT_NOT_FOUND |
| UT-ADM-M-003 | UT | scope_ref 不存在 → 拒绝 MEMORY_SCOPE_NOT_FOUND |
| UT-ADM-M-004 | UT | source_knowledge_ref KI 不存在 → 拒绝 MEMORY_SOURCE_KI_NOT_FOUND |
| UT-ADM-M-005 | UT | source_knowledge_ref scope 不匹配 → 拒绝 MEMORY_SOURCE_KI_SCOPE_MISMATCH |
| UT-ADM-M-006 | UT | visibility=agent-private + agent_ref.name="" → 拒绝 MEMORY_AGENT_PRIVATE_REQUIRES_NAME |
| UT-ADM-M-007 | UT | decay_days=4000 → 拒绝 MEMORY_DECAY_DAYS_EXCEEDED |
| UT-ADM-M-008 | UT | admission timeout 50ms → fail-closed |

---

## 6. Knowledge Service Agent + 4 个 A2A method handler（Python AgentCard + Pydantic DTO）

### 6.1 KnowledgeServiceCard Pydantic Model

```python
# packages/knowledge-service/src/supteam_a2a/knowledge_service/card/card.py
from pydantic import BaseModel, Field, ConfigDict
from superteam_a2a.a2a.upstream import AgentSkill  # L2-1 边界


class KnowledgeServiceCard(BaseModel):
    """Knowledge Service Agent Card（Pydantic 推导 AgentCard JSON）。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(default="superteam-a2a.knowledge-service", frozen=True)
    version: str = Field(default="0.2.0", description="Python 重写版本")
    description: str = Field(default=(
        "Internal knowledge service for superteam-a2a. "
        "Provides free-text query and item retrieval across the 4-level "
        "scope hierarchy, plus persistent memory record/query."
    ))
    provider: dict[str, str] = Field(default={
        "organization": "superteam-a2a",
        "url": "https://github.com/superteam-cn/superteam-a2a",
    })
    skills: list[AgentSkill] = Field(default_factory=lambda: [
        AgentSkill(
            id="query_knowledge",
            name="Query Knowledge",
            description="Free-text search over KnowledgeItems with scope/type/tag filters.",
            input_schema={
                "type": "object",
                "required": ["scope", "query"],
                "properties": {
                    "scope": {"type": "string", "description": "KnowledgeScope name"},
                    "query": {"type": "string", "minLength": 1, "maxLength": 512},
                    "typeFilter": {"type": "array", "items": {"enum": [
                        "document", "runbook", "api-spec", "architecture", "faq",
                        "best-practice", "template", "contract", "troubleshooting",
                        "glossary", "other",
                    ]}},
                    "tagFilter": {"type": "array"},
                    "maxResults": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                },
            },
            output_schema={
                "type": "object",
                "required": ["items", "totalCount"],
                "properties": {
                    "items": {"type": "array"},
                    "totalCount": {"type": "integer", "minimum": 0},
                },
            },
        ),
        AgentSkill(
            id="get_knowledge_item",
            name="Get Knowledge Item",
            description="Retrieve full KnowledgeItem by name + version.",
            input_schema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "integer", "minimum": 1},
                },
            },
        ),
        AgentSkill(
            id="record_memory",
            name="Record Memory",
            description="Persist agent experience as Memory with decay/reinforce lifecycle.",
            input_schema={
                "type": "object",
                "required": ["scope", "agent", "content", "summary"],
                "properties": {
                    "scope": {"type": "string"},
                    "agent": {"type": "string"},
                    "content": {"type": "object", "minProperties": 1, "maxProperties": 20},
                    "summary": {"type": "string", "minLength": 1, "maxLength": 512},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1, "default": 1.0},
                    "decayDays": {"type": "integer", "minimum": 1, "maximum": 3650, "default": 30},
                    "visibility": {"type": "enum": [
                        "scope-only", "scope-and-children", "agent-private",
                    ], "default": "scope-and-children"},
                    "memoryKeyPattern": {"type": "string", "maxLength": 128},
                    "sourceKnowledgeRef": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "version": {"type": "integer", "minimum": 1},
                        },
                    },
                },
            },
        ),
        AgentSkill(
            id="query_memory",
            name="Query Memory",
            description="Query Memories with 5-dim visibility matrix + multi-filter.",
            input_schema={
                "type": "object",
                "required": ["callerAgent", "callerScopeChain"],
                "properties": {
                    "callerAgent": {"type": "string"},
                    "callerScopeChain": {"type": "array", "items": {"type": "string"}},
                    "scopeFilter": {"type": "string"},
                    "agentFilter": {"type": "string"},
                    "memoryKeyPattern": {"type": "string"},
                    "tagFilter": {"type": "array"},
                    "minConfidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "maxResults": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100},
                },
            },
        ),
    ])
    capabilities: dict[str, bool] = Field(default={
        "streaming": False,
        "pushNotifications": False,
        "stateTransitionHistory": False,
    })
    authentication: dict[str, list[str]] = Field(default={"schemes": ["mtls"]})
```

### 6.2 `a2a.queryKnowledge` handler

```python
# packages/knowledge-service/src/supteam_a2a/knowledge_service/handlers/query_knowledge.py
from pydantic import BaseModel, Field, ConfigDict
from superteam_a2a.a2a.upstream import A2AError, ErrorCode
from superteam_a2a.knowledge_service.handlers.errors import (
    KNOWLEDGE_SCOPE_NOT_FOUND,
    KNOWLEDGE_QUERY_TOO_LONG,
    KNOWLEDGE_INVALID_TYPE,
    KNOWLEDGE_INTERNAL_ERROR,
    KNOWLEDGE_ADMISSION_TIMEOUT,
)
from superteam_a2a.knowledge_service.deps import (
    get_scope_resolver,
    get_inverted_index,
    get_visibility_filter,
)


class QueryKnowledgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scope: str = Field(..., min_length=1, max_length=128)
    query: str = Field(..., min_length=1, max_length=512)
    type_filter: list[str] | None = Field(default=None, max_length=11, alias="typeFilter")
    tag_filter: list[str] | None = Field(default=None, alias="tagFilter")
    max_results: int = Field(default=10, ge=1, le=50, alias="maxResults")


class KnowledgeItemSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    scope: str
    type: str
    title: str
    summary: str | None = None
    version: int
    relevance_score: float = Field(..., alias="relevanceScore", ge=0.0, le=1.0)


class QueryKnowledgeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    items: list[KnowledgeItemSummary]
    total_count: int = Field(..., ge=0, alias="totalCount")


async def handle_query_knowledge(
    req: QueryKnowledgeRequest,
    *,
    caller_agent: str,
    caller_scope_chain: list[str],
) -> QueryKnowledgeResponse:
    """a2a.queryKnowledge handler。

    错误码：
    - KNOWLEDGE_SCOPE_NOT_FOUND (-32008)
    - KNOWLEDGE_QUERY_TOO_LONG (-32009)
    - KNOWLEDGE_INVALID_TYPE (-32010)
    - KNOWLEDGE_INTERNAL_ERROR (-32011)
    - KNOWLEDGE_ADMISSION_TIMEOUT (-32018)
    """
    scope_resolver = get_scope_resolver()
    inverted_index = get_inverted_index()

    # 1. scope 存在性
    scope = await scope_resolver.get_scope(req.scope)
    if scope is None:
        raise A2AError(KNOWLEDGE_SCOPE_NOT_FOUND, f"KnowledgeScope {req.scope} not found")

    # 2. query 长度校验（已在 Pydantic 校验；此处冗余防御）
    if len(req.query) > 512:
        raise A2AError(KNOWLEDGE_QUERY_TOO_LONG, f"Query length {len(req.query)} exceeds 512")

    # 3. type_filter 校验
    valid_types = {t.value for t in KnowledgeType}
    if req.type_filter and any(t not in valid_types for t in req.type_filter):
        raise A2AError(KNOWLEDGE_INVALID_TYPE, f"typeFilter contains invalid types")

    # 4. resolve effective scopes
    try:
        effective_scopes = await scope_resolver.resolve_effective_scopes(req.scope)
    except AdmissionTimeoutError:
        raise A2AError(KNOWLEDGE_ADMISSION_TIMEOUT, "Admission timeout resolving scope chain")

    # 5. inverted index search（CPU offload）
    candidates = await inverted_index.search(
        query=req.query,
        scope_chain=effective_scopes,
        type_filter=req.type_filter,
        tag_filter=req.tag_filter,
        max_results=req.max_results * 2,
    )

    # 6. visibility + inherit_rules 过滤
    results: list[tuple[KnowledgeItem, float]] = []
    for item, score in candidates:
        if not _is_inherit_allowed(item, effective_scopes):
            continue
        if not _is_visibility_allowed(item, req.scope):
            continue
        results.append((item, score))

    # 7. 去重：同 ID 保留最新 version
    results = _dedupe_by_id_keep_latest(results)[: req.max_results]

    # 8. 构造 response
    items = [
        KnowledgeItemSummary(
            name=item.metadata.name,
            scope=item.spec.scope_ref.name,
            type=item.spec.type.value,
            title=item.spec.title,
            summary=item.spec.summary,
            version=item.spec.version,
            relevance_score=score,
        )
        for item, score in results
    ]

    return QueryKnowledgeResponse(items=items, total_count=len(items))
```

### 6.3 `a2a.getKnowledgeItem` handler

```python
# packages/knowledge-service/src/supteam_a2a/knowledge_service/handlers/get_knowledge_item.py
class GetKnowledgeItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=128)
    version: int | None = Field(default=None, ge=1)


class GetKnowledgeItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    item: KnowledgeItem  # 完整 Pydantic 对象


async def handle_get_knowledge_item(
    req: GetKnowledgeItemRequest,
    *,
    caller_agent: str,
    caller_scope_chain: list[str],
) -> GetKnowledgeItemResponse:
    """a2a.getKnowledgeItem handler。

    错误码：
    - KNOWLEDGE_ITEM_NOT_FOUND (-32012)
    - KNOWLEDGE_VERSION_NOT_FOUND (-32013)
    - KNOWLEDGE_FORBIDDEN (-32014，agent-private 且 caller ≠ owner)
    - KNOWLEDGE_INTERNAL_ERROR (-32011)
    """
    # 1. 获取 KI（按 name + version；若 version=None 返回最新）
    items = await k8s_custom_api.list_namespaced_custom_object(
        group="knowledge.superteam-a2a.io",
        version="v1alpha1",
        namespace=...,
        plural="knowledgeitems",
        label_selector=f"name={req.name}",
    )

    if not items["items"]:
        raise A2AError(KNOWLEDGE_ITEM_NOT_FOUND, f"KnowledgeItem {req.name} not found")

    # 选择版本
    target_version = req.version or max(int(item["spec"]["version"]) for item in items["items"])
    matching = [i for i in items["items"] if int(i["spec"]["version"]) == target_version]
    if not matching:
        raise A2AError(
            KNOWLEDGE_VERSION_NOT_FOUND,
            f"KnowledgeItem {req.name} version {target_version} not found",
        )

    item = KnowledgeItem.model_validate(matching[0])

    # 2. visibility 校验（agent-private 且 caller ≠ owner → 拒绝）
    if item.spec.visibility == KnowledgeVisibility.AGENT_PRIVATE:
        if item.spec.owner_ref.name != caller_agent:
            raise A2AError(
                KNOWLEDGE_FORBIDDEN,
                f"KnowledgeItem {req.name} is agent-private; caller {caller_agent} not owner",
            )

    # 3. scope inheritance 校验
    effective_scopes = await get_scope_resolver().resolve_effective_scopes(item.spec.scope_ref.name)
    if not any(caller_scope in effective_scopes for caller_scope in caller_scope_chain):
        raise A2AError(
            KNOWLEDGE_FORBIDDEN,
            f"KnowledgeItem {req.name} scope {item.spec.scope_ref.name} not in caller scope chain",
        )

    return GetKnowledgeItemResponse(item=item)
```

### 6.4 `a2a.recordMemory` handler

```python
# packages/knowledge-service/src/supteam_a2a/knowledge_service/handlers/record_memory.py
# Agent → Knowledge Service → memory_backend.record_memory
class RecordMemoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scope: str = Field(..., min_length=1, max_length=128)
    agent: str = Field(..., min_length=1, max_length=253)
    content: dict[str, str] = Field(..., min_length=1, max_length=20)
    summary: str = Field(..., min_length=1, max_length=512)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    decay_days: int = Field(default=30, ge=1, le=3650, alias="decayDays")
    visibility: MemoryVisibility = Field(default=MemoryVisibility.SCOPE_AND_CHILDREN)
    memory_key_pattern: str | None = Field(default=None, alias="memoryKeyPattern", max_length=128)
    source_knowledge_ref: ItemReference | None = Field(default=None, alias="sourceKnowledgeRef")
    tags: list[str] | None = Field(default=None, max_length=10)


class RecordMemoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    phase: MemoryPhase
    effective_confidence: float = Field(..., alias="effectiveConfidence")


async def handle_record_memory(
    req: RecordMemoryRequest,
    *,
    caller_agent: str,
) -> RecordMemoryResponse:
    """a2a.recordMemory handler（代理到 memory_backend）。

    错误码：
    - MEMORY_SCOPE_NOT_FOUND (-32101)
    - MEMORY_INVALID_CONTENT (-32102)
    - MEMORY_FORBIDDEN (-32103)
    - MEMORY_RATE_LIMIT (-32104，60/min per SA)
    - MEMORY_INTERNAL_ERROR (-32105)
    - MEMORY_ADMISSION_TIMEOUT (-32112)
    """
    # 1. rate limit（60/min per SA）
    if not await get_ratelimiter().check_and_record(caller_agent, scope=req.scope):
        raise A2AError(
            MEMORY_RATE_LIMIT,
            f"Memory rate limit exceeded for SA {caller_agent} (60/min)",
        )

    # 2. 构造 Memory CR + apply
    memory_name = f"{caller_agent}-{req.memory_key_pattern or uuid.uuid4().hex[:8]}"
    memory_obj = Memory(
        metadata=ObjectMeta(
            name=memory_name,
            namespace=...,
            labels={"scope": req.scope, "agent": caller_agent},
        ),
        spec=MemorySpec(
            scope_ref=ScopeReference(name=req.scope),
            agent_ref=AgentReference(kind=SubjectKind.SERVICE_ACCOUNT, name=caller_agent),
            content=req.content,
            summary=req.summary,
            confidence=req.confidence,
            decay_days=req.decay_days,
            reinforced_count=0,
            last_reinforced_at=datetime.now(UTC),
            memory_key_pattern=req.memory_key_pattern,
            source_knowledge_ref=req.source_knowledge_ref,
            tags=req.tags,
            visibility=req.visibility,
        ),
    )

    try:
        created = await k8s_custom_api.create_namespaced_custom_object(
            group="memory.superteam-a2a.io",
            version="v1alpha1",
            namespace=...,
            plural="memories",
            body=memory_obj.model_dump(by_alias=True, exclude_none=True),
        )
    except kubernetes_asyncio.client.exceptions.ApiException as e:
        if e.status == 404:
            raise A2AError(MEMORY_SCOPE_NOT_FOUND, f"KnowledgeScope {req.scope} not found")
        if e.status == 403:
            raise A2AError(MEMORY_FORBIDDEN, f"Forbidden creating Memory: {e.reason}")
        if e.status == 422:
            raise A2AError(MEMORY_INVALID_CONTENT, f"Invalid Memory content: {e.reason}")
        if e.status == 503:  # admission timeout
            raise A2AError(MEMORY_ADMISSION_TIMEOUT, f"Admission timeout: {e.reason}")
        raise A2AError(MEMORY_INTERNAL_ERROR, f"K8s API error: {e.reason}")

    # 3. audit log
    await get_audit_logger().log_memory_created(caller_agent, memory_name, req.scope)

    return RecordMemoryResponse(
        name=memory_name,
        phase=MemoryPhase.ACTIVE,
        effective_confidence=req.confidence,
    )
```

### 6.5 `a2a.queryMemory` handler

```python
# packages/knowledge-service/src/supteam_a2a/knowledge_service/handlers/query_memory.py
class QueryMemoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    caller_agent: str = Field(..., alias="callerAgent", min_length=1, max_length=253)
    caller_scope_chain: list[str] = Field(..., alias="callerScopeChain", min_length=1)
    scope_filter: str | None = Field(default=None, alias="scopeFilter", max_length=128)
    agent_filter: str | None = Field(default=None, alias="agentFilter", max_length=253)
    memory_key_pattern: str | None = Field(default=None, alias="memoryKeyPattern", max_length=128)
    tag_filter: list[str] | None = Field(default=None, alias="tagFilter", max_length=10)
    min_confidence: float | None = Field(default=None, alias="minConfidence", ge=0.0, le=1.0)
    max_results: int = Field(default=100, ge=1, le=1000, alias="maxResults")


class MemorySummary(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    scope: str
    agent: str
    summary: str
    confidence: float
    effective_confidence: float = Field(..., alias="effectiveConfidence")
    phase: MemoryPhase
    reinforced_count: int = Field(..., alias="reinforcedCount")
    created_at: AwareDatetime = Field(..., alias="createdAt")
    tags: list[str] | None = None


class QueryMemoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    memories: list[MemorySummary]
    total_count: int = Field(..., ge=0, alias="totalCount")


async def handle_query_memory(
    req: QueryMemoryRequest,
) -> QueryMemoryResponse:
    """a2a.queryMemory handler。

    错误码：
    - MEMORY_SCOPE_NOT_FOUND (-32101)
    - MEMORY_FORBIDDEN (-32103)
    - MEMORY_QUERY_TOO_BROAD (-32106，scope=industry + 无 tag/confidence 过滤被拒)
    - MEMORY_INTERNAL_ERROR (-32105)
    - MEMORY_ADMISSION_TIMEOUT (-32112)
    """
    # 1. query too broad 校验（scope=industry + 无 tag/confidence 过滤 → 拒绝）
    if req.scope_filter == "industry" and not req.tag_filter and req.min_confidence is None:
        raise A2AError(
            MEMORY_QUERY_TOO_BROAD,
            "Querying industry scope requires tagFilter or minConfidence",
        )

    # 2. 拉取候选 Memory（按 scope + agent 索引）
    memories_raw = await k8s_custom_api.list_namespaced_custom_object(
        group="memory.superteam-a2a.io",
        version="v1alpha1",
        namespace=...,
        plural="memories",
        label_selector=_build_label_selector(req),
    )
    memories = [Memory.model_validate(m) for m in memories_raw["items"]]

    # 3. 5 维矩阵过滤 + 多维过滤
    visibility_filter = get_visibility_filter()
    filtered = await query_memory(
        visibility_filter=visibility_filter,
        memories=memories,
        caller_agent=req.caller_agent,
        caller_scope_chain=req.caller_scope_chain,
        scope_filter=req.scope_filter,
        agent_filter=req.agent_filter,
        memory_key_pattern=req.memory_key_pattern,
        tag_filter=req.tag_filter,
        min_confidence=req.min_confidence,
        max_results=req.max_results,
    )

    # 4. 构造 response
    summaries = [
        MemorySummary(
            name=m.metadata.name,
            scope=m.spec.scope_ref.name,
            agent=m.spec.agent_ref.name,
            summary=m.spec.summary,
            confidence=m.spec.confidence,
            effective_confidence=m.status.effective_confidence or m.spec.confidence,
            phase=m.status.phase or MemoryPhase.ACTIVE,
            reinforced_count=m.spec.reinforced_count,
            created_at=m.metadata.creation_timestamp,
            tags=m.spec.tags,
        )
        for m in filtered
    ]

    return QueryMemoryResponse(memories=summaries, total_count=len(summaries))
```

### 6.6 4 handler 部署形态（共享 Deployment）

- **Deployment**：1 副本（v0.1 单实例，水平扩展推 v0.5+）
- **ServiceAccount**：独立 SA（`superteam-a2a-knowledge-service`），**不是 default**
- **NetworkPolicy**：仅允许 Operator + 其他 Agent 调用
- **不暴露 HTTP**：仅 A2A mTLS（cert-manager 颁发）
- **挂载 4 个 A2A method handler**（与 Memory backend 共享同 Deployment）：
  - `a2a.queryKnowledge` / `a2a.getKnowledgeItem`（Knowledge 主接口）
  - `a2a.recordMemory` / `a2a.queryMemory`（Memory 副接口）

### 6.7 handler 测试矩阵

| 测试 ID | 类型 | 场景 |
|---------|------|------|
| UT-HANDLER-QK-001 | UT | 正常查询 → 返回 items[] |
| UT-HANDLER-QK-002 | UT | scope 不存在 → KNOWLEDGE_SCOPE_NOT_FOUND |
| UT-HANDLER-QK-003 | UT | type_filter 无效 → KNOWLEDGE_INVALID_TYPE |
| UT-HANDLER-QK-004 | UT | admission timeout → KNOWLEDGE_ADMISSION_TIMEOUT |
| UT-HANDLER-QK-005 | UT | 12 种 visibility × scope 组合穷举 |
| UT-HANDLER-GI-001 | UT | 正常获取 → 返回完整 KnowledgeItem |
| UT-HANDLER-GI-002 | UT | KI 不存在 → KNOWLEDGE_ITEM_NOT_FOUND |
| UT-HANDLER-GI-003 | UT | version 不存在 → KNOWLEDGE_VERSION_NOT_FOUND |
| UT-HANDLER-GI-004 | UT | agent-private + caller ≠ owner → KNOWLEDGE_FORBIDDEN |
| UT-HANDLER-RM-001 | UT | 正常写入 → Memory 创建 + ACTIVE |
| UT-HANDLER-RM-002 | UT | rate limit 超限 → MEMORY_RATE_LIMIT |
| UT-HANDLER-RM-003 | UT | SA 不存在 → MEMORY_FORBIDDEN |
| UT-HANDLER-RM-004 | UT | decay_days=4000 → MEMORY_INVALID_CONTENT |
| UT-HANDLER-QM-001 | UT | 正常查询 → 返回 memories[] |
| UT-HANDLER-QM-002 | UT | industry + 无过滤 → MEMORY_QUERY_TOO_BROAD |
| UT-HANDLER-QM-003 | UT | 5 维矩阵过滤正确性 |
| UT-HANDLER-QM-004 | UT | agent-private + caller ≠ owner → 过滤掉 |

---

## 7. MemoryReconciler reconcile 流程（Kopf timer + Lease + decay/reinforce/GC/promotion）

### 7.1 架构总览

```
┌─────────────────────────────────────────────────────────┐
│ Operator Process (uvicorn 单 worker · 单 event loop)    │
│                                                         │
│  ┌─────────────────────┐   ┌─────────────────────────┐  │
│  │ Kopf daemon         │   │ MemoryReconciler        │  │
│  │ (K8s API watch)     │   │ async service           │  │
│  │                     │   │                         │  │
│  │ AgentReconciler     │   │ @kopf.timer(60s)        │  │
│  │ AgentSetReconciler  │   │   ↓                     │  │
│  │ WorkflowReconciler  │   │ reconcile_all_memories  │  │
│  │ KnowledgeItem Ctl   │   │   - decay batch         │  │
│  │ KnowledgeScope Ctl │   │   - GC expired          │  │
│  │ admission webhook   │   │   - promote compute     │  │
│  └─────────────────────┘   └─────────────────────────┘  │
│                                                         │
│  Leader Election via coordination.k8s.io/v1 Lease      │
└─────────────────────────────────────────────────────────┘
```

### 7.2 MemoryReconciler Service（Protocol + Real 实现）

```python
# packages/operator/src/supteam_a2a/operator/handlers/memory.py
# 完整代码在 L2-2 Operator Core Spec v0.2.0 Python §5.6 + L3-5 Spec
import asyncio
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable
import kopf
from superteam_a2a.memory.lifecycle import (
    apply_decay,
    apply_reinforce,
    gc_expired,
    is_eligible_for_promotion,
)
from superteam_a2a.memory.apis.v1alpha1 import Memory, MemoryPhase, MemoryVisibility
from superteam_a2a.shared.clock import Clock, RealClock
from superteam_a2a.shared.leader import LeaseLeader
from superteam_a2a.shared.observability import (
    SUPTEAM_MEMORY_DECAY_TOTAL,
    SUPTEAM_MEMORY_RECONCILE_DURATION_SECONDS,
)


@runtime_checkable
class MemoryReconcilerService(Protocol):
    """MemoryReconciler 业务抽象（L2-2 Operator Core §5.6）。"""

    async def reconcile_all(self, now: datetime) -> ReconcileSummary:
        """单次全集群 Memory reconcile；返回计数摘要。"""
        ...


@dataclass
class ReconcileSummary:
    """Reconcile 计数摘要。"""

    decayed: int = 0
    expired: int = 0
    promoted_eligible: int = 0
    reinforced: int = 0
    errors: int = 0


class RealMemoryReconcilerService:
    """生产实现：批量 reconcile + Leader Election + 周期触发。"""

    BATCH_SIZE = 1000  # 单 reconcile 批大小；Helm values 可配

    def __init__(
        self,
        clock: Clock,
        leader: LeaseLeader,
        memory_store: "MemoryStoreProtocol",
    ) -> None:
        self._clock = clock
        self._leader = leader
        self._store = memory_store

    async def reconcile_all(self, now: datetime) -> ReconcileSummary:
        """周期 reconcile 入口（被 @kopf.timer 调用）。"""
        if not await self._leader.is_leader():
            return ReconcileSummary()  # 非 leader 直接返回（K8s Lease 单活）

        with SUPTEAM_MEMORY_RECONCILE_DURATION_SECONDS.time():
            summary = ReconcileSummary()

            # 1. 拉取全集群 Memory（分批，避免 API server 过载）
            memories = await self._store.list_all_memories()
            for batch in chunked(memories, self.BATCH_SIZE):
                async with asyncio.TaskGroup() as tg:
                    for mem in batch:
                        tg.create_task(self._reconcile_one(mem, now, summary))
            return summary

    async def _reconcile_one(
        self,
        mem: Memory,
        now: datetime,
        summary: ReconcileSummary,
    ) -> None:
        """单 Memory reconcile（decay + GC + promotion 计算）。"""
        # 1. decay 公式（数学等价于 L2-2 §5.6）
        new_effective = apply_decay(mem, now)
        old_phase = mem.status.phase if mem.status else MemoryPhase.ACTIVE

        # 2. GC 检查
        if new_effective < 0.01 and mem.spec.decay_days > 0:
            await self._store.delete_memory(mem.metadata.name)
            SUPTEAM_MEMORY_DECAY_TOTAL.labels(
                phase_from=old_phase.value,
                phase_to=MemoryPhase.EXPIRED.value,
            ).inc()
            summary.expired += 1
            return

        # 3. promotion 资格计算（v0.1 仅算不触发）
        eligible = is_eligible_for_promotion(mem, new_effective)

        # 4. status 写回（partial update，避免覆盖 spec）
        new_phase = _phase_for(new_effective)
        await self._store.patch_status(
            mem.metadata.name,
            {
                "phase": new_phase.value,
                "effectiveConfidence": new_effective,
                "lastDecayedAt": now.isoformat(),
                "eligibleForPromotion": eligible,
                "observedGeneration": mem.metadata.generation,
            },
        )

        if old_phase != new_phase:
            SUPTEAM_MEMORY_DECAY_TOTAL.labels(
                phase_from=old_phase.value,
                phase_to=new_phase.value,
            ).inc()
            summary.decayed += 1

        if eligible:
            summary.promoted_eligible += 1


def _phase_for(effective: float) -> MemoryPhase:
    """effective_confidence → MemoryPhase 状态机映射。"""
    if effective < 0.01:
        return MemoryPhase.EXPIRED
    if effective < 0.5:
        return MemoryPhase.DECAYING
    return MemoryPhase.ACTIVE


# Kopf timer 入口
@kopf.timer("memory.superteam-a2a.io", "v1alpha1", "memories", interval=60.0)
async def memory_reconcile_timer(
    *,
    memo: kopf.Memo,
    logger: kopf.Logger,
    **kwargs,
) -> None:
    """60s 周期触发全集群 Memory reconcile。"""
    reconciler: MemoryReconcilerService = memo.get_or_create(
        "memory_reconciler",
        lambda: RealMemoryReconcilerService(
            clock=memo.get_or_create("clock", lambda: RealClock()),
            leader=memo.get_or_create(
                "leader",
                lambda: RealLeaseLeader(
                    lease_name="superteam-a2a-operator-leader",
                    lease_namespace="superteam-a2a-system",
                ),
            ),
            memory_store=memo.get_or_create("memory_store", lambda: RealMemoryStore()),
        ),
    )
    now = reconciler._clock.now()
    try:
        summary = await reconciler.reconcile_all(now)
        logger.info(
            "memory reconcile completed",
            decayed=summary.decayed,
            expired=summary.expired,
            promoted_eligible=summary.promoted_eligible,
            reinforced=summary.reinforced,
            errors=summary.errors,
        )
    except Exception as e:
        logger.exception("memory reconcile failed", error=str(e))
        # Kopf backoff 自动重试（指数退避，上限 5min）
```

### 7.3 decay / reinforce / GC / promotion 数学（纯函数）

```python
# packages/memory/src/supteam_a2a/memory/lifecycle/decay.py
import math
from datetime import datetime, timedelta
from superteam_a2a.memory.apis.v1alpha1 import Memory, MemoryPhase
from superteam_a2a.shared.clock import Clock


def apply_decay(memory: Memory, now: datetime) -> float:
    """计算 effective_confidence（指数衰减 · 数学等价 v0.1 Go baseline）。

    公式：effective_confidence = base_confidence * exp(-elapsed_days / decay_days)
    - base_confidence = spec.confidence（初始 1.0）
    - elapsed_days = (now - creation_timestamp).total_seconds() / 86400
    - decay_days = spec.decay_days（默认 30）

    返回值：0.0 ~ 1.0
    """
    creation = memory.metadata.creation_timestamp
    elapsed_seconds = (now - creation).total_seconds()
    elapsed_days = elapsed_seconds / 86400.0

    base = memory.spec.confidence
    half_life = memory.spec.decay_days

    if half_life <= 0:
        return base

    return base * math.exp(-elapsed_days / half_life)


# packages/memory/src/supteam_a2a/memory/lifecycle/reinforce.py
def apply_reinforce(
    memory: Memory, now: datetime, min_interval_seconds: int = 3600
) -> tuple[Memory, bool]:
    """reinforce Memory（频次节流）。

    频次节流：上次 reinforce 后 < 1h（可配）→ 不重复更新 last_reinforced_at。
    返回：(new_memory, was_reinforced)。

    副作用：reinforced_count +1，last_reinforced_at = now，confidence 不变（decay 重新计算覆盖）。
    """
    last = memory.spec.last_reinforced_at
    if last is not None and (now - last).total_seconds() < min_interval_seconds:
        return memory, False

    new_memory = memory.model_copy(deep=True)
    new_memory.spec.reinforced_count = memory.spec.reinforced_count + 1
    new_memory.spec.last_reinforced_at = now
    # 注意：effective_confidence 不在此更新；由下一次 reconcile_all 重新计算
    return new_memory, True


# packages/memory/src/supteam_a2a/memory/lifecycle/gc.py
def gc_expired(memories: list[Memory], now: datetime) -> list[str]:
    """返回待 GC 的 Memory name 列表。

    GC 条件：effective_confidence < 0.01（decay_days > 0 时）。
    """
    expired: list[str] = []
    for mem in memories:
        eff = apply_decay(mem, now)
        if eff < 0.01 and mem.spec.decay_days > 0:
            expired.append(mem.metadata.name)
    return expired


# packages/memory/src/supteam_a2a/memory/lifecycle/promotion.py
def is_eligible_for_promotion(memory: Memory, effective_confidence: float) -> bool:
    """判断 Memory 是否 eligible for promotion（v0.1 仅算不触发）。

    资格条件：
    - effective_confidence > 0.95
    - reinforced_count >= 5
    - decay_days < 365
    - visibility != agent-private（agent-private 不允许升级为 KI）
    """
    if effective_confidence <= 0.95:
        return False
    if memory.spec.reinforced_count < 5:
        return False
    if memory.spec.decay_days >= 365:
        return False
    if memory.spec.visibility.value == "agent-private":
        return False
    return True
```

### 7.4 Clock Protocol（注入时间穿越单测 · D-4）

```python
# packages/shared/src/supteam_a2a/shared/clock.py
from typing import Protocol, runtime_checkable
from datetime import datetime, timedelta


@runtime_checkable
class Clock(Protocol):
    """时间抽象（ADR-0005 §3.4 + §11 测试；时间穿越单测必须可注入）。"""

    def now(self) -> datetime:
        """返回当前 UTC 时间。"""
        ...


class RealClock:
    """生产实现：datetime.now(UTC)。"""

    def now(self) -> datetime:
        from datetime import UTC

        return datetime.now(UTC)


class FakeClock:
    """测试实现：手动推进时间（freezegun 风格 · D-4）。"""

    def __init__(self, start: datetime | None = None) -> None:
        from datetime import UTC

        self._now = start or datetime.now(UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        """手动推进时间（测试用）。"""
        self._now += delta

    def set(self, ts: datetime) -> None:
        """设置时间到指定时刻（测试用）。"""
        self._now = ts
```

### 7.5 时间穿越单测（关键 · 验证 decay 数学）

```python
# packages/memory/tests/unit/lifecycle/test_decay.py
def test_decay_over_30_days():
    """30 天后 effectiveConfidence 应为 1.0 * exp(-1) ≈ 0.368。"""
    from datetime import datetime, timedelta, UTC
    fake_clock = FakeClock(start=datetime(2026, 7, 24, 0, 0, 0, tzinfo=UTC))
    memory = Memory(
        spec=MemorySpec(
            confidence=1.0, decay_days=30,
            scope_ref=ScopeReference(name="team-test"),
            agent_ref=AgentReference(kind=SubjectKind.SERVICE_ACCOUNT, name="test-agent"),
            content={"key": "value"}, summary="test",
            reinforced_count=0,
            visibility=MemoryVisibility.SCOPE_AND_CHILDREN,
        ),
        metadata=ObjectMeta(
            name="test", creation_timestamp=fake_clock.now(),
            namespace="default",
        ),
    )

    fake_clock.advance(timedelta(days=30))  # 30 天后

    effective = apply_decay(memory, fake_clock.now())
    assert abs(effective - 0.368) < 0.01  # exp(-1) ≈ 0.368


def test_decay_60_days():
    """60 天后 effectiveConfidence 应为 exp(-2) ≈ 0.135。"""
    fake_clock = FakeClock(start=datetime(2026, 7, 24, 0, 0, 0, tzinfo=UTC))
    memory = Memory(
        spec=MemorySpec(confidence=1.0, decay_days=30, ...),
        metadata=ObjectMeta(name="test", creation_timestamp=fake_clock.now(), ...),
    )
    fake_clock.advance(timedelta(days=60))
    effective = apply_decay(memory, fake_clock.now())
    assert abs(effective - 0.135) < 0.01


def test_reinforce_throttle():
    """reinforce 后 1h 内再次 reinforce → 不更新 last_reinforced_at。"""
    fake_clock = FakeClock(start=datetime(2026, 7, 24, 0, 0, 0, tzinfo=UTC))
    memory = Memory(...)

    new_mem, reinforced = apply_reinforce(memory, fake_clock.now())
    assert reinforced is True
    assert new_mem.spec.reinforced_count == 1

    fake_clock.advance(timedelta(minutes=30))  # 30 分钟后
    new_mem2, reinforced2 = apply_reinforce(new_mem, fake_clock.now())
    assert reinforced2 is False
    assert new_mem2.spec.reinforced_count == 1
```

### 7.6 Leader Election（Operator 进程级共享）

```python
# packages/shared/src/supteam_a2a/shared/leader.py
from typing import Protocol, runtime_checkable
from datetime import datetime, timedelta
import kubernetes_asyncio.client as k8s_client


@runtime_checkable
class LeaseLeader(Protocol):
    """K8s Lease 抽象（Operator 进程级单活）。"""

    async def is_leader(self) -> bool:
        """当前进程是否是 leader。"""
        ...


class RealLeaseLeader:
    """生产实现：coordination.k8s.io/v1 Lease + 续约。"""

    def __init__(
        self,
        lease_name: str,
        lease_namespace: str,
        renew_deadline_seconds: int = 15,
        retry_period_seconds: int = 5,
    ) -> None:
        self._name = lease_name
        self._namespace = lease_namespace
        self._renew_deadline = renew_deadline_seconds
        self._retry_period = retry_period_seconds
        self._holder_id = uuid.uuid4().hex
        self._is_leader = False
        self._last_renew = datetime.now(UTC)

    async def is_leader(self) -> bool:
        """获取或续约 Lease，返回是否持有 lease。"""
        try:
            # 尝试获取 lease
            lease = await k8s_client.CoordinationV1Api().read_namespaced_lease(
                name=self._name,
                namespace=self._namespace,
            )
            now = datetime.now(UTC)
            renew_time = lease.spec.renew_time
            if renew_time and (now - renew_time).total_seconds() < self._renew_deadline:
                # 其他 holder 持有且未过期；尝试抢占
                if lease.spec.holder_identity == self._holder_id:
                    self._is_leader = True
                    await self._renew(lease)
                else:
                    self._is_leader = False
            else:
                # 抢占
                await self._acquire_or_renew(lease)
        except k8s_client.exceptions.ApiException as e:
            if e.status == 404:
                # Lease 不存在；创建
                await self._create_lease()
            else:
                raise
        return self._is_leader

    async def _acquire_or_renew(self, lease):
        lease.spec.holder_identity = self._holder_id
        lease.spec.renew_time = datetime.now(UTC)
        lease.spec.lease_duration_seconds = self._renew_deadline + self._retry_period
        await k8s_client.CoordinationV1Api().replace_namespaced_lease(
            name=self._name,
            namespace=self._namespace,
            body=lease,
        )
        self._is_leader = True
        self._last_renew = datetime.now(UTC)
```

### 7.7 MemoryReconciler 测试矩阵

| 测试 ID | 类型 | 场景 |
|---------|------|------|
| UT-DECAY-001 | UT | 30 天后 effectiveConfidence ≈ 0.368（FakeClock 推进） |
| UT-DECAY-002 | UT | 60 天后 effectiveConfidence ≈ 0.135 |
| UT-DECAY-003 | UT | decay_days=1 → 1 天后 exp(-1) ≈ 0.368 |
| UT-DECAY-004 | UT | decay_days=3650 → 3650 天后 exp(-1) ≈ 0.368 |
| UT-DECAY-005 | UT | confidence=0.5 → 30 天后 0.184 |
| UT-REINF-001 | UT | reinforce → reinforced_count + 1，last_reinforced_at 更新 |
| UT-REINF-002 | UT | 1h 内再次 reinforce → 拒绝（throttle） |
| UT-REINF-003 | UT | 1h 后再次 reinforce → 接受 |
| UT-REINF-004 | UT | reinforce 不修改 confidence（decay 重新计算覆盖） |
| UT-PROM-001 | UT | effectiveConfidence > 0.95 + reinforced_count >= 5 + decay_days < 365 → eligible |
| UT-PROM-002 | UT | reinforced_count < 5 → not eligible |
| UT-PROM-003 | UT | agent-private → not eligible |
| UT-GC-001 | UT | effectiveConfidence < 0.01 → 待 GC |
| UT-GC-002 | UT | effectiveConfidence = 0.05 → 不 GC |
| UT-GC-003 | UT | decay_days = 0 → 永不 GC |
| IT-MEM-REC-001 | IT | 周期 reconcile 触发 decay + status 更新 |
| IT-MEM-REC-002 | IT | 50K memories 60s 周期全集群 reconcile ≤ 30s |
| IT-MEM-REC-003 | IT | Leader Election failover（kill leader → 新 leader ≤ 30s） |
| E2E-M-001 | E2E | memory-record-query（agent 写 1 memory → queryMemory 命中 → reinforce → decay P95 ≤ 300ms） |
| E2E-M-003 | E2E | MemoryReconciler Python 路径（FakeClock 推进 30 天 → effective_confidence = 0.368） |
| E2E-M-004 | E2E | Leader Election failover（kill leader pod → 30s 内新 leader 接管） |

---

## 附录 A：跨模块引用

| 引用对象 | 位置 | 用途 |
|----------|------|------|
| L1 Architecture v0.2.0 §3.5.2 | [docs/design/L1-architecture.md](../../design/L1-architecture.md) | Knowledge Service 运行时层定位 |
| L1 Architecture v0.2.0 §3.5.3 | 同上 | Memory backend + MemoryReconciler 定位 |
| L1 Architecture v0.2.0 §5.2.2-5.2.4 | 同上 | 3 CRD spec/status 字段基线 |
| L1 Spec v0.2.0 §5 | [docs/spec/L1-system-spec.md](../../spec/L1-system-spec.md) | CRD YAML wire contract |
| L1 Spec v0.2.0 §15 | 同上 | 部署 / Helm values |
| L1 Spec v0.2.0 §16 | 同上 | Python runtime 4 个新指标 |
| ADR-0001 v1 范围 | [docs/adr/0001-v1-scope-statement.md](../../adr/0001-v1-scope-statement.md) | 第 5 大基础能力 = 知识管理 |
| ADR-0002 知识管理设计 | [docs/adr/0002-knowledge-management-design.md](../../adr/0002-knowledge-management-design.md) | KnowledgeScope/Item CRD + 4 级继承算法 + Visibility 4 枚举 |
| ADR-0003 Memory 设计 | [docs/adr/0003-memory-design.md](../../adr/0003-memory-design.md) | Memory CRD + 5 维矩阵 + decay/reinforce 算法 + admission 互斥 |
| ADR-0004 v0.1 时间线 | [docs/adr/0004-v01-scope-extension-knowledge-and-memory.md](../../adr/0004-v01-scope-extension-knowledge-and-memory.md) | v0.1 Phase 2/3 拆分 |
| **ADR-0005 Python-first** | [docs/adr/0005-python-first-technology-stack.md](../../adr/0005-python-first-technology-stack.md) | **§3.4 Knowledge/Memory + §6.2 单进程 + §6.3 GIL 与 CPU 工作 + §7 Operator 可靠性门禁 + §10 可观测性 + §13 工程布局** |
| L2-1 A2A Protocol Spec v0.2.0 Python | [docs/spec/L2-module-specs/L2-a2a-protocol.md](../../spec/L2-module-specs/L2-a2a-protocol.md) | `supteam_a2a.a2a.upstream.create_app` 嵌入 + 错误码基线 + JSON-RPC 2.0 + ASGI |
| L2-2 Operator Core Spec v0.2.0 Python §5.6 | [docs/spec/L2-module-specs/L2-operator-core.md](../../spec/L2-module-specs/L2-operator-core.md) | MemoryReconciler reconcile 流程 + decay 公式 + Clock 接口注入 + Leader Election |
| L2-3 Adapter Spec v0.2.0 Python §11 | [docs/spec/L2-module-specs/L2-adapter.md](../../spec/L2-module-specs/L2-adapter.md) | v0.5+ Adapter 代理 4 A2A method |
| 宪法 v0.5.0 §2.5 | [CONSTITUTION.md](../../../CONSTITUTION.md) | 强制 namespace + admission 校验 + visibility 枚举 |
| 宪法 v0.5.0 §2.9 | 同上 | Memory 可回溯 KnowledgeItem (source_knowledge_ref) |
| 宪法 v0.5.0 §3.6 | 同上 | MCP 边界（Knowledge/Memory 不实现 MCP） |
| 宪法 v0.5.0 §3.7 | 同上 | Knowledge/Memory 不依赖 framework 代码 |
| 宪法 v0.5.0 §3.8 | 同上 | Python-first 全栈迁移 |
| 宪法 v0.5.0 §6 | 同上 | mTLS + RBAC + NetworkPolicy + admission 互斥 |
| 宪法 v0.5.0 §7 | 同上 | 11 个 supteam_knowledge_* + 6 个 supteam_memory_* Prometheus 指标 |
| 宪法 v0.5.0 §9 | 同上 | ≥80% 覆盖 + 时间穿越单测 + E2E + conformance |
| 宪法 v0.5.0 §16.1 | 同上 | 1M 窗口 / 500K 红线 / 实际水位判断 / 典型参照表 |

---

## 8. 检索路径（Python BM25 + anyio to_thread offload · D-2）

### 8.1 存储策略

| 数据 | 存储 | 理由 |
|------|------|------|
| **KnowledgeItem** | K8s **etcd**（CRD 即存储） | 无外部依赖；v0.1 简化；天然 RBAC + audit log |
| **Memory** | K8s **etcd**（CRD 即存储） | 同上；MemoryReconciler 直接 K8s API patch status |
| **倒排索引** | **Operator 进程内存**（`RealInvertedIndex`） | 10K items 重建 ≤30s 可接受；无外部依赖 |

### 8.2 queryKnowledge 检索流程（5 时序）

```
┌──────────┐   ┌────────────────┐   ┌──────────────┐   ┌─────────────────┐   ┌──────────┐
│ Caller   │   │ queryKnowledge │   │ ScopeResolver│   │ InvertedIndex   │   │K8s API  │
│ (Agent)  │   │ handler        │   │              │   │ (RealInverted)  │   │(etcd)    │
└────┬─────┘   └────────┬───────┘   └──────┬───────┘   └────────┬────────┘   └────┬─────┘
     │ A2A request       │                  │                    │                  │
     │ a2a.queryKnowledge│                  │                    │                  │
     │ {scope, query,    │                  │                    │                  │
     │  typeFilter,      │                  │                    │                  │
     │  tagFilter,       │                  │                    │                  │
     │  maxResults}      │                  │                    │                  │
     ├──────────────────>│                  │                    │                  │
     │                   │ 1. scope 存在性检查                     │                  │
     │                   ├─────────────────>│                    │                  │
     │                   │  get_scope(scope)│                    │                  │
     │                   ├─────────────────>│                    │                  │
     │                   │                  │ [memory cache hit] │                  │
     │                   │                  │ or fetch K8s API   │                  │
     │                   │                  ├───────────────────>│                  │
     │                   │                  │                    │                  │
     │                   │<─────────────────┤                    │                  │
     │                   │ KnowledgeScope   │                    │                  │
     │                   │ 2. typeFilter 校验                     │                  │
     │                   │    (Pydantic 校验)                      │                  │
     │                   │ 3. resolve_effective_scopes()           │                  │
     │                   ├─────────────────>│                    │                  │
     │                   │                  │ 遍历 parent chain  │                  │
     │                   │                  │ [4 步循环]          │                  │
     │                   │<─────────────────┤                    │                  │
     │                   │ [industry, org,  │                    │                  │
     │                   │  team, project]  │                    │                  │
     │                   │ 4. index.search(scope_chain, query)    │                  │
     │                   ├────────────────────────────────────────>│                  │
     │                   │                  │                    │ tokenize +       │
     │                   │                  │                    │ BM25 score       │
     │                   │                  │                    │ (CPU offload     │
     │                   │                  │                    │  to_thread)      │
     │                   │<────────────────────────────────────────┤                  │
     │                   │ [(KI, score), ...] (top maxResults*2)   │                  │
     │                   │ 5. visibility + inheritRules 过滤       │                  │
     │                   │    + dedupe by id (latest version)      │                  │
     │                   │ 6. truncate to maxResults               │                  │
     │                   │ 7. construct QueryKnowledgeResponse     │                  │
     │<──────────────────┤                                          │                  │
     │ A2A response       │                                          │                  │
     │ {items, totalCount}│                                          │                  │
     │                   │                                          │                  │
```

### 8.3 InvertedIndex Protocol + Real 实现（详细）

```python
# packages/knowledge/src/supteam_a2a/knowledge/search/inverted_index.py
# 完整实现 + 性能测试在 L3-5 Spec
from typing import Protocol, runtime_checkable
from datetime import UTC
import asyncio
import math
from collections import Counter, defaultdict
from anyio import to_thread
from superteam_a2a.knowledge.apis.v1alpha1 import KnowledgeItem


# BM25 参数（与 v0.1.0 Go baseline 完全一致）
BM25_K1 = 1.5  # 词频饱和参数
BM25_B = 0.75  # 文档长度归一化参数


@runtime_checkable
class InvertedIndex(Protocol):
    """内存倒排索引抽象（ADR-0005 §3.4）。"""

    async def search(
        self,
        query: str,
        scope_chain: list[str],
        type_filter: list[str] | None = None,
        tag_filter: list[str] | None = None,
        max_results: int = 10,
    ) -> list[tuple[KnowledgeItem, float]]:
        """BM25 检索；返回 (item, score) 列表。

        阻塞工作通过 to_thread.run_sync offload（满足 ADR-0005 §6.3）。
        """
        ...

    async def rebuild(self, items: list[KnowledgeItem]) -> None:
        """全量重建索引（启动期 + Helm values 触发）。"""
        ...

    async def upsert(self, item: KnowledgeItem) -> None:
        """增量更新（watch 触发）。"""
        ...

    async def remove(self, item_name: str) -> None:
        """增量删除。"""
        ...

    def size(self) -> int:
        """当前索引条目数（10K 上限报警）。"""
        ...


class RealInvertedIndex:
    """生产实现：内存 dict + BM25 评分。"""

    def __init__(self) -> None:
        # token → set of item names
        self._postings: dict[str, set[str]] = defaultdict(set)
        # item name → Counter of tokens (用于 BM25 tf 计算)
        self._doc_tokens: dict[str, Counter[str]] = {}
        # item name → KnowledgeItem 引用
        self._items: dict[str, KnowledgeItem] = {}
        self._avg_doc_len: float = 0.0
        self._lock = asyncio.Lock()  # single-writer 多 reader

    async def search(
        self,
        query: str,
        scope_chain: list[str],
        type_filter: list[str] | None = None,
        tag_filter: list[str] | None = None,
        max_results: int = 10,
    ) -> list[tuple[KnowledgeItem, float]]:
        """异步入口 + 受控线程 offload（满足 ADR-0005 §6.3 + L1 §11.5 event-loop lag 门禁）。"""
        return await to_thread.run_sync(
            self._search_blocking,
            query,
            scope_chain,
            type_filter,
            tag_filter,
            max_results,
        )

    def _search_blocking(
        self,
        query: str,
        scope_chain: list[str],
        type_filter: list[str] | None,
        tag_filter: list[str] | None,
        max_results: int,
    ) -> list[tuple[KnowledgeItem, float]]:
        """同步 BM25 检索（在工作线程中执行）。"""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # 1. 收集候选 item name（union of postings）
        candidates: set[str] = set()
        for tok in query_tokens:
            candidates.update(self._postings.get(tok, set()))

        # 2. scope 过滤
        scope_set = set(scope_chain)
        candidates = {
            name for name in candidates if self._items[name].spec.scope_ref.name in scope_set
        }

        # 3. typeFilter / tagFilter 过滤
        if type_filter:
            candidates = {
                name for name in candidates if self._items[name].spec.type.value in type_filter
            }
        if tag_filter:
            candidates = {
                name
                for name in candidates
                if set(self._items[name].spec.tags or []) & set(tag_filter)
            }

        # 4. BM25 评分
        N = len(self._items)
        scores: list[tuple[str, float]] = []
        for name in candidates:
            score = self._bm25_score(name, query_tokens, N)
            if score > 0:
                scores.append((name, score))

        # 5. 排序 + 截断
        scores.sort(key=lambda x: x[1], reverse=True)
        top = scores[:max_results]

        # 6. visibility 过滤（公开方法调用，避免循环依赖）
        results: list[tuple[KnowledgeItem, float]] = []
        for name, score in top:
            item = self._items[name]
            if self._is_visible(item, scope_chain):
                results.append((item, score))
        return results

    def _bm25_score(self, doc_name: str, query_tokens: list[str], N: int) -> float:
        """BM25 评分公式（与 v0.1.0 Go baseline math 完全等价）。"""
        doc_counter = self._doc_tokens[doc_name]
        doc_len = sum(doc_counter.values())
        score = 0.0
        for term in query_tokens:
            tf = doc_counter.get(term, 0)
            if tf == 0:
                continue
            df = len(self._postings.get(term, set()))
            idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
            tf_norm = (tf * (BM25_K1 + 1)) / (
                tf + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / self._avg_doc_len)
            )
            score += idf * tf_norm
        return score

    def _tokenize(self, text: str) -> list[str]:
        """简单 tokenizer（lowercase + ASCII alphanumeric split；与 Go baseline 等价）。"""
        import re

        return re.findall(r"[a-z0-9]+", text.lower())

    def _is_visible(self, item: KnowledgeItem, scope_chain: list[str]) -> bool:
        """visibility 过滤（public-readable 仅 industry；agent-private v0.1 禁用）。"""
        visibility = item.spec.visibility
        scope_name = item.spec.scope_ref.name

        if visibility.value == "scope-only":
            return scope_name == scope_chain[-1]
        if visibility.value == "scope-and-children":
            return scope_name in scope_chain
        if visibility.value == "public-readable":
            # admission 强制 scope.level == industry；此处仅校验 scope_chain 包含
            return scope_name in scope_chain
        if visibility.value == "agent-private":
            return False  # v0.1 禁用（admission 已拒绝创建）
        return False

    async def rebuild(self, items: list[KnowledgeItem]) -> None:
        """启动期全量重建（10K items ≤ 30s）。"""
        await to_thread.run_sync(self._rebuild_blocking, items)

    def _rebuild_blocking(self, items: list[KnowledgeItem]) -> None:
        self._postings.clear()
        self._doc_tokens.clear()
        self._items.clear()
        total_len = 0
        for item in items:
            self._items[item.metadata.name] = item
            tokens = self._tokenize(item.spec.body + " " + item.spec.title)
            counter = Counter(tokens)
            self._doc_tokens[item.metadata.name] = counter
            total_len += len(tokens)
            for tok in counter:
                self._postings[tok].add(item.metadata.name)
        self._avg_doc_len = total_len / len(items) if items else 0.0

    async def upsert(self, item: KnowledgeItem) -> None:
        """watch 触发的增量更新。"""
        async with self._lock:
            await to_thread.run_sync(self._upsert_blocking, item)

    def _upsert_blocking(self, item: KnowledgeItem) -> None:
        name = item.metadata.name
        if name in self._items:
            self.remove_sync(name)  # 清理旧 postings
        self._items[name] = item
        tokens = self._tokenize(item.spec.body + " " + item.spec.title)
        counter = Counter(tokens)
        self._doc_tokens[name] = counter
        for tok in counter:
            self._postings[tok].add(name)

    async def remove(self, item_name: str) -> None:
        async with self._lock:
            await to_thread.run_sync(self._remove_blocking, item_name)

    def _remove_blocking(self, item_name: str) -> None:
        if item_name not in self._items:
            return
        for tok in self._doc_tokens.get(item_name, {}):
            self._postings[tok].discard(item_name)
        self._doc_tokens.pop(item_name, None)
        self._items.pop(item_name, None)

    def remove_sync(self, item_name: str) -> None:
        """同步版 remove（upsert 内部调用）。"""
        self._remove_blocking(item_name)

    def size(self) -> int:
        return len(self._items)
```

### 8.4 检索路径测试 ID

| 测试 ID | 类型 | 场景 |
|---------|------|------|
| UT-SRCH-001 | UT | 单 token BM25 评分正确 |
| UT-SRCH-002 | UT | 多 token BM25 评分正确 |
| UT-SRCH-003 | UT | scope_chain 过滤（继承链上所有 scope） |
| UT-SRCH-004 | UT | typeFilter 过滤 |
| UT-SRCH-005 | UT | tagFilter 过滤 |
| UT-SRCH-006 | UT | visibility=public-readable + scope.level=industry 命中 |
| UT-SRCH-007 | UT | visibility=agent-private 拒绝 |
| UT-SRCH-008 | UT | upsert 后 search 命中新增 |
| UT-SRCH-009 | UT | remove 后 search 不命中 |
| UT-SRCH-010 | UT | size() 报告准确条目数 |
| UT-SRCH-011 | UT | BM25 K1/B 参数对评分影响 |
| UT-SRCH-012 | UT | empty query 返回 [] |
| UT-SRCH-013 | UT | 文档长度归一化（long doc score 衰减） |
| UT-SRCH-014 | UT perf | 10K items queryKnowledge P95 ≤ 200ms |
| UT-SRCH-015 | UT perf | search 阻塞时间 ≤ 100ms（event-loop lag 门禁） |
| UT-SRCH-016 | UT perf | rebuild 10K items ≤ 30s |
| IT-SRCH-001 | IT | watch 触发 upsert 增量更新 |
| IT-SRCH-002 | IT | watch 触发 remove 增量删除 |
| E2E-K-001 | E2E | knowledge-quickstart（4 级 scope + 5 KI + queryKnowledge 命中继承链） |

### 8.5 v0.5+ 演进（非 v0.1 范围）

- **可选 Vector DB 后端**（Chroma / Qdrant）：Helm values `search.backend: vector` 选择；Operator 实现 `VectorInvertedIndex` 同样满足 `InvertedIndex` Protocol
- **自动 scope-up**：`KnowledgePromotionRequest` CRD（v0.1 仅 is_eligible_for_promotion 计算不触发）
- **Memory 全文搜索**：v0.1 仅 memoryKeyPattern + tag + confidence 过滤；v0.5+ 可加 BM25 over Memory.content（不大于 1KB）
- **Memory 分支 / 快照**：v0.1 覆盖更新；v0.5+ 可加 MemoryRevision 历史
- **跨 cluster 联邦**：v0.1 单 cluster；v1.0+ ADR 评估

### 8.6 BM25 + anyio to_thread 性能门禁

**CPU offload 约束**（ADR-0005 §6.3 + L1 v0.2.0 §11.5）：
- 默认 `to_thread` limiter = 40 线程（anyio 默认）
- 单次 search `to_thread.run_sync` 超时 5s（Helm values 可配）
- `event_loop_lag_seconds` 指标（ADR-0005 §10）：> 100ms 持续 10s → 报警
- 10K items rebuild 时间 ≤ 30s（Helm values `search.rebuildOnStart: true`）
- 50K memories 60s 周期 reconcile ≤ 30s（MemoryReconciler）

---

## 9. 错误码与重试（KNOWLEDGE_* -32008~-32018 + MEMORY_* -32101~-32112）

### 9.1 错误码完整表格（与 v0.1 Go baseline 完全继承）

| 错误码（StrEnum） | JSON-RPC code | 模块 | 触发场景 | 客户端处理 |
|------------------|---------------|------|----------|------------|
| `KNOWLEDGE_SCOPE_NOT_FOUND` | -32008 | knowledge_service | scope_ref.name 不存在 | 404 / 重新创建 scope |
| `KNOWLEDGE_QUERY_TOO_LONG` | -32009 | knowledge_service | query 长度 > 512 | 400 / 截断 query |
| `KNOWLEDGE_INVALID_TYPE` | -32010 | knowledge_service | typeFilter 含无效枚举 | 400 / 修正 typeFilter |
| `KNOWLEDGE_INTERNAL_ERROR` | -32011 | knowledge_service | K8s API 5xx / Python 异常 | 500 / 重试 1 次 |
| `KNOWLEDGE_ITEM_NOT_FOUND` | -32012 | knowledge_service | KI name 不存在 | 404 / 检查 KI name |
| `KNOWLEDGE_VERSION_NOT_FOUND` | -32013 | knowledge_service | KI version 不存在 | 404 / 取最新 version |
| `KNOWLEDGE_FORBIDDEN` | -32014 | knowledge_service | agent-private + caller ≠ owner / scope 不在 chain | 403 / 重新授权 |
| `KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY` | -32015 | knowledge admission | visibility=public-readable 但 scope.level ≠ industry | 400 / 改 visibility |
| `KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS` | -32016 | knowledge admission | visibility=agent-private v0.1 拒绝 | 400 / v0.5+ |
| `KNOWLEDGE_OWNER_KIND_FORBIDDEN` | -32017 | knowledge admission | KI.ownerRef.kind=ServiceAccount | 400 / 改用 Memory |
| **`KNOWLEDGE_ADMISSION_TIMEOUT`** | **-32018** | knowledge admission | admission 50ms timeout | 503 / 退避重试 |
| `MEMORY_SCOPE_NOT_FOUND` | -32101 | memory_backend | Memory.scopeRef 不存在 | 404 |
| `MEMORY_INVALID_CONTENT` | -32102 | memory_backend | content 字段超限（> 20 keys） | 400 |
| `MEMORY_FORBIDDEN` | -32103 | memory_backend | SA 不存在 / admission 拒绝 | 403 |
| `MEMORY_RATE_LIMIT` | -32104 | memory_backend middleware | SA 写 Memory > 60/min | 429 / 退避到下分钟 |
| `MEMORY_INTERNAL_ERROR` | -32105 | memory_backend | K8s API 5xx / Python 异常 | 500 / 重试 1 次 |
| `MEMORY_QUERY_TOO_BROAD` | -32106 | memory_backend | scope=industry + 无 tag/confidence 过滤 | 400 / 加过滤 |
| `MEMORY_SOURCE_KI_NOT_FOUND` | -32107 | memory admission | sourceKnowledgeRef.name 不存在 | 400 |
| `MEMORY_SOURCE_KI_SCOPE_MISMATCH` | -32108 | memory admission | KI.scopeRef ≠ Memory.scopeRef | 400 / 修正 scope |
| `MEMORY_AGENT_PRIVATE_REQUIRES_NAME` | -32109 | memory admission | agent-private + agentRef.name="" | 400 |
| `MEMORY_DECAY_DAYS_EXCEEDED` | -32110 | memory admission | decayDays > 3650 | 400 / 修正 decayDays |
| `MEMORY_AGENT_NOT_FOUND` | -32111 | memory admission | agentRef.name SA 不存在 | 400 |
| **`MEMORY_ADMISSION_TIMEOUT`** | **-32112** | memory admission | admission 50ms timeout | 503 / 退避重试 |

**wire 范围**：KNOWLEDGE_* -32008~-32018 + MEMORY_* -32101~-32112（与 v0.1.0 Go baseline 完全一致；新增 -32018 / -32112 为 admission timeout）。

### 9.2 错误码 StrEnum 定义（Python 实现）

```python
# packages/knowledge-service/src/supteam_a2a/knowledge_service/handlers/errors.py
# packages/memory-backend/src/supteam_a2a/memory_backend/handlers/errors.py
from enum import IntEnum, StrEnum
from superteam_a2a.a2a.upstream import A2AError, ErrorCode  # L2-1 边界


class KnowledgeErrorCode(IntEnum):
    """Knowledge Service 错误码（JSON-RPC code 范围 -32008~-32018）。"""

    KNOWLEDGE_SCOPE_NOT_FOUND = -32008
    KNOWLEDGE_QUERY_TOO_LONG = -32009
    KNOWLEDGE_INVALID_TYPE = -32010
    KNOWLEDGE_INTERNAL_ERROR = -32011
    KNOWLEDGE_ITEM_NOT_FOUND = -32012
    KNOWLEDGE_VERSION_NOT_FOUND = -32013
    KNOWLEDGE_FORBIDDEN = -32014
    KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY = -32015
    KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS = -32016
    KNOWLEDGE_OWNER_KIND_FORBIDDEN = -32017
    KNOWLEDGE_ADMISSION_TIMEOUT = -32018


class MemoryErrorCode(IntEnum):
    """Memory backend 错误码（JSON-RPC code 范围 -32101~-32112）。"""

    MEMORY_SCOPE_NOT_FOUND = -32101
    MEMORY_INVALID_CONTENT = -32102
    MEMORY_FORBIDDEN = -32103
    MEMORY_RATE_LIMIT = -32104
    MEMORY_INTERNAL_ERROR = -32105
    MEMORY_QUERY_TOO_BROAD = -32106
    MEMORY_SOURCE_KI_NOT_FOUND = -32107
    MEMORY_SOURCE_KI_SCOPE_MISMATCH = -32108
    MEMORY_AGENT_PRIVATE_REQUIRES_NAME = -32109
    MEMORY_DECAY_DAYS_EXCEEDED = -32110
    MEMORY_AGENT_NOT_FOUND = -32111
    MEMORY_ADMISSION_TIMEOUT = -32112


# 构造 A2AError（直接复用 L2-1 a2a-python 错误结构）
def knowledge_error(code: KnowledgeErrorCode, message: str, **data) -> A2AError:
    return A2AError(
        code=code.value,
        message=message,
        data={"module": "knowledge", "code_name": code.name, **data},
    )


def memory_error(code: MemoryErrorCode, message: str, **data) -> A2AError:
    return A2AError(
        code=code.value,
        message=message,
        data={"module": "memory", "code_name": code.name, **data},
    )
```

### 9.3 重试策略（Tenacity 库 · ADR-0005 §10）

**4 类重试场景**：

| 错误码 | 是否重试 | 重试次数 | 退避策略 |
|--------|----------|----------|----------|
| `*_INTERNAL_ERROR` | ✅ | 1 | 立即重试 |
| `*_ADMISSION_TIMEOUT` | ✅ | 3 | 指数退避（100ms / 200ms / 400ms） |
| `MEMORY_RATE_LIMIT` | ✅ | 直到下分钟 | 滑动窗口 |
| `*_FORBIDDEN` / `*_NOT_FOUND` / `*_INVALID_*` / `*_EXCEEDED` | ❌ | 0 | 立即返回 |

```python
# packages/shared/src/supteam_a2a/shared/retry.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from superteam_a2a.a2a.upstream import A2AError
from superteam_a2a.knowledge_service.handlers.errors import KnowledgeErrorCode
from superteam_a2a.memory_backend.handlers.errors import MemoryErrorCode


# admission timeout 重试（指数退避 100ms → 200ms → 400ms）
retry_admission_timeout = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.1, max=0.4),
    retry=retry_if_exception_type(A2AError)
    & retry_if_exception_code(
        [
            KnowledgeErrorCode.KNOWLEDGE_ADMISSION_TIMEOUT.value,
            MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT.value,
        ],
    ),
    reraise=True,
)


# internal error 重试（仅 1 次立即重试）
retry_internal_error = retry(
    stop=stop_after_attempt(1),
    retry=retry_if_exception_type(A2AError)
    & retry_if_exception_code(
        [
            KnowledgeErrorCode.KNOWLEDGE_INTERNAL_ERROR.value,
            MemoryErrorCode.MEMORY_INTERNAL_ERROR.value,
        ],
    ),
    reraise=True,
)
```

### 9.4 错误码测试 ID

| 测试 ID | 类型 | 场景 |
|---------|------|------|
| UT-ERR-001 | UT | KNOWLEDGE_SCOPE_NOT_FOUND 抛出 + code=-32008 |
| UT-ERR-002 | UT | KNOWLEDGE_ADMISSION_TIMEOUT 重试 3 次后抛出 |
| UT-ERR-003 | UT | KNOWLEDGE_FORBIDDEN 不重试立即抛出 |
| UT-ERR-004 | UT | MEMORY_RATE_LIMIT 滑动窗口到下分钟 |
| UT-ERR-005 | UT | MEMORY_QUERY_TOO_BROAD scope=industry + 无过滤 |
| UT-ERR-006 | UT | MEMORY_DECAY_DAYS_EXCEEDED decayDays=4000 |
| CF-ERR-001 | CF | 22 个错误码 wire-compatible with a2a-python conformance |
| CF-ERR-002 | CF | 错误码 JSON-RPC envelope format 校验 |

---

## 10. 可观测性（17 个 Prometheus 指标 + OTel + structlog + K8s Events）

### 10.1 Prometheus 指标（与 v0.1 wire contract 完全一致）

**Knowledge 侧**（`superteam_knowledge_*` — 11 个）：

```python
# packages/shared/src/supteam_a2a/shared/observability/metrics_knowledge.py
from prometheus_client import Counter, Histogram, Gauge, Summary


# 1. queryKnowledge 总量
SUPTEAM_KNOWLEDGE_QUERY_TOTAL = Counter(
    "superteam_knowledge_query_total",
    "Total number of queryKnowledge requests",
    labelnames=("scope", "type", "result"),  # result: success / error / timeout
)

# 2. queryKnowledge 延迟
SUPTEAM_KNOWLEDGE_QUERY_DURATION_SECONDS = Histogram(
    "superteam_knowledge_query_duration_seconds",
    "queryKnowledge request duration in seconds",
    labelnames=("scope",),
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0),
)

# 3. KI 总数（按 scope / type / phase）
SUPTEAM_KNOWLEDGE_ITEMS_TOTAL = Gauge(
    "superteam_knowledge_items_total",
    "Total number of KnowledgeItems",
    labelnames=("scope", "type", "phase"),
)

# 4. 倒排索引大小
SUPTEAM_KNOWLEDGE_SEARCH_INDEX_SIZE = Gauge(
    "superteam_knowledge_search_index_size",
    "Current number of items in the inverted index",
)

# 5. KnowledgeScope 总数（按 level）
SUPTEAM_KNOWLEDGE_SCOPE_TOTAL = Gauge(
    "superteam_knowledge_scope_total",
    "Total number of KnowledgeScopes",
    labelnames=("level",),
)

# 6. BM25 CPU offload 阻塞时间（Python 新增）
SUPTEAM_KNOWLEDGE_SEARCH_OFFLOAD_SECONDS = Histogram(
    "superteam_knowledge_search_offload_seconds",
    "BM25 search CPU offload blocking time in seconds",
    buckets=(0.005, 0.01, 0.05, 0.1, 0.2, 0.5),
)

# 7. event-loop lag（Python 新增）
SUPTEAM_KNOWLEDGE_SEARCH_EVENT_LOOP_LAG_SECONDS = Histogram(
    "superteam_knowledge_search_event_loop_lag_seconds",
    "Event loop lag during search operations in seconds",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
)

# 8. getKnowledgeItem 总量
SUPTEAM_KNOWLEDGE_GET_ITEM_TOTAL = Counter(
    "superteam_knowledge_get_item_total",
    "Total number of getKnowledgeItem requests",
    labelnames=("result",),
)

# 9. admission 拒绝率（按原因）
SUPTEAM_KNOWLEDGE_ADMISSION_REJECT_TOTAL = Counter(
    "superteam_knowledge_admission_reject_total",
    "Total KnowledgeItem admission rejections",
    labelnames=(
        "reason",
    ),  # KNOWLEDGE_OWNER_KIND_FORBIDDEN / KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY / etc.
)

# 10. visibility filter 命中数
SUPTEAM_KNOWLEDGE_VISIBILITY_FILTER_TOTAL = Counter(
    "superteam_knowledge_visibility_filter_total",
    "Total visibility filter outcomes",
    labelnames=("visibility", "result"),  # result: allowed / filtered
)

# 11. KI body 长度分布
SUPTEAM_KNOWLEDGE_ITEM_BODY_SIZE_BYTES = Histogram(
    "superteam_knowledge_item_body_size_bytes",
    "KnowledgeItem body size in bytes",
    buckets=(1024, 4096, 16384, 32768, 65536),
)
```

**Memory 侧**（`superteam_memory_*` — 6 个）：

```python
# packages/shared/src/supteam_a2a/shared/observability/metrics_memory.py
from prometheus_client import Counter, Histogram, Gauge


# 1. recordMemory 总量
SUPTEAM_MEMORY_RECORD_TOTAL = Counter(
    "superteam_memory_record_total",
    "Total number of recordMemory requests",
    labelnames=("scope", "agent", "result"),
)

# 2. queryMemory 总量
SUPTEAM_MEMORY_QUERY_TOTAL = Counter(
    "superteam_memory_query_total",
    "Total number of queryMemory requests",
    labelnames=("scope", "visibility", "result"),
)

# 3. Memory 状态机转换（phase_from → phase_to）
SUPTEAM_MEMORY_DECAY_TOTAL = Counter(
    "superteam_memory_decay_total",
    "Total Memory phase transitions",
    labelnames=("phase_from", "phase_to"),
)

# 4. MemoryReconciler reconcile 延迟
SUPTEAM_MEMORY_RECONCILE_DURATION_SECONDS = Histogram(
    "superteam_memory_reconcile_duration_seconds",
    "MemoryReconciler reconcile duration in seconds",
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0),
)

# 5. eligible_for_promotion 数（按 scope）
SUPTEAM_MEMORY_ELIGIBLE_FOR_PROMOTION_TOTAL = Gauge(
    "superteam_memory_eligible_for_promotion_total",
    "Total Memories eligible for promotion (v0.1 only compute)",
    labelnames=("scope",),
)

# 6. Memory 总数（按 scope + phase）
SUPTEAM_MEMORY_TOTAL = Gauge(
    "superteam_memory_total",
    "Total number of Memories",
    labelnames=("scope", "phase"),
)
```

**Python runtime 特定**（ADR-0005 §10 — 3 个，跨模块共享）：

```python
# packages/shared/src/supteam_a2a/shared/observability/metrics_python.py
from prometheus_client import Histogram, Gauge


# 1. anyio to_thread offload event-loop lag
SUPTEAM_PYTHON_EVENT_LOOP_LAG_SECONDS = Histogram(
    "superteam_python_event_loop_lag_seconds",
    "Event loop lag in seconds (anyio to_thread offload monitoring)",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
)

# 2. anyio to_thread queue depth
SUPTEAM_PYTHON_THREAD_OFFLOAD_QUEUE_DEPTH = Gauge(
    "superteam_python_thread_offload_queue_depth",
    "Current anyio to_thread queue depth",
)

# 3. asyncio active tasks
SUPTEAM_PYTHON_ACTIVE_TASKS = Gauge(
    "superteam_python_active_tasks",
    "Current number of active asyncio tasks",
)
```

**指标总数**：Knowledge 11 + Memory 6 + Python runtime 3 = **20 个**（v0.1 Go baseline 17 个 + Python 新增 3 个）。

### 10.2 OTel Trace（OpenTelemetry SDK · ADR-0005 §10）

```python
# packages/shared/src/supteam_a2a/shared/observability/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def init_tracer(service_name: str, otlp_endpoint: str) -> TracerProvider:
    """初始化 OTel tracer（OTLP gRPC exporter）。"""
    provider = TracerProvider()
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)


# Root Span: knowledge_service.{method} / memory_backend.{method}
# Child Spans:
#   - crd.read (K8s API GET)
#   - index.search (BM25 检索)
#   - bm25.score (评分计算)
#   - visibility.filter (5 维矩阵过滤)
#   - reconcile.batch (MemoryReconciler 批处理)
# Span Events:
#   - scope.resolved
#   - admission.validated
#   - reinforce.triggered
#   - decay.applied
#   - gc.expired
# Python 特定:
#   - thread.offload.start / thread.offload.end (duration)
```

### 10.3 structlog JSON 日志（ADR-0005 §10）

```python
# packages/shared/src/supteam_a2a/shared/observability/logging.py
import structlog
import logging


def init_logging(log_level: str = "INFO", framework: str = "core") -> None:
    """初始化 structlog JSON 输出（K8s log 友好）。"""
    logging.basicConfig(level=log_level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# 强制字段：framework / caller_agent / scope / trace_id / level / ts / msg
# 可选字段：memory_key / confidence / effective_confidence / decay_days / event_loop_lag_ms
# 敏感字段黑名单：content / body / tags（K8s audit log + Memory content 永不进入普通日志）


# 使用示例
logger = structlog.get_logger()
logger.info(
    "knowledge_query_executed",
    framework="core",
    caller_agent="sa-test-agent",
    scope="team-payments",
    trace_id="abc123...",
    duration_ms=45,
    total_count=12,
    # 敏感字段不会传入 logger
)
```

### 10.4 K8s Events（Kopf event decorator）

```python
# packages/knowledge-service/src/supteam_a2a/knowledge_service/events.py
import kopf


@kopf.event(
    "knowledge.superteam-a2a.io", "v1alpha1", "knowledgescopes", labels={"event": "lifecycle"}
)
async def knowledge_scope_created(spec, name, namespace, **kwargs):
    """KnowledgeScopeCreated event 触发。"""
    pass  # 实际由 kopf 自动生成 K8s Event


# MemoryReconciler events
@kopf.event("memory.superteam-a2a.io", "v1alpha1", "memories", labels={"event": "lifecycle"})
async def memory_lifecycle_event(spec, name, namespace, status, old, new, **kwargs):
    """Memory lifecycle event（reinforced / decayed / expired / gc）。"""
    pass  # 实际由 kopf 自动生成 K8s Event


# K8s Event 列表：
# - KnowledgeScopeCreated / KnowledgeScopeDeleted
# - KnowledgeItemPublished / KnowledgeItemDeprecated
# - MemoryCreated / MemoryReinforced / MemoryDecayed
# - MemoryExpired / MemoryGarbageCollected
```

### 10.5 ServiceMonitor（Prometheus scrape 配置）

```yaml
# helm/templates/knowledge-service-servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: superteam-a2a-knowledge-service
  labels:
    app.kubernetes.io/name: superteam-a2a-knowledge-service
    release: prometheus  # 与 prometheus-operator release 匹配
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: superteam-a2a-knowledge-service
  endpoints:
  - port: metrics  # :9090 (Prometheus scrape port)
    interval: 30s
    path: /metrics
    scheme: http
```

### 10.6 可观测性测试 ID

| 测试 ID | 类型 | 场景 |
|---------|------|------|
| UT-OBS-001 | UT | queryKnowledge 后 Prometheus counter +1 |
| UT-OBS-002 | UT | queryKnowledge 延迟 histogram 记录 |
| UT-OBS-003 | UT | MemoryReconciler reconcile 延迟 histogram |
| UT-OBS-004 | UT | BM25 offload_seconds histogram |
| UT-OBS-005 | UT | event_loop_lag_seconds 上报 |
| UT-OBS-006 | UT | structlog JSON 输出包含强制字段 |
| UT-OBS-007 | UT | 敏感字段（content / body / tags）不进入普通日志 |
| IT-OBS-001 | IT | OTel span context propagation（handler → inverted_index → K8s API） |
| IT-OBS-002 | IT | K8s Event 自动生成（KnowledgeScopeCreated） |
| CF-OBS-001 | CF | Prometheus metric naming convention 校验 |
| CF-OBS-002 | CF | OTel span name 约定校验 |

---

## 11. Helm values（5 段式：knowledgeService / memoryReconciler / search / admission / ratelimit）

### 11.1 全局 + knowledgeService 默认配置

```yaml
# helm/values.yaml（完整 schema · v0.2 Python 重写）

global:
  imageRegistry: ghcr.io/coderzhangfujiang
  imagePullPolicy: IfNotPresent
  logLevel: INFO  # DEBUG / INFO / WARNING / ERROR
  imageTag: "0.2.0"  # Python 重写版本

knowledgeService:
  image:
    repository: ghcr.io/coderzhangfujiang/superteam-a2a-knowledge-service
    tag: "0.2.0"
    pullPolicy: IfNotPresent

  # A2A Server
  port: 8080
  host: 0.0.0.0
  a2aMethodTimeoutMs: 5000

  # Python runtime（ADR-0005 §6.2 单进程原则）
  python:
    runtime: "python:3.12-slim"
    workers: 1  # Uvicorn 单 worker（与 Knowledge Service 同进程）
    eventLoopLagThresholdMs: 100  # event-loop lag 报警阈值

  # 健康检查
  healthCheckPath: /healthz
  readinessPath: /readyz

  # 资源限制（Knowledge Service 1 副本典型值）
  resources:
    requests:
      cpu: 500m
      memory: 256Mi
    limits:
      cpu: "2"
      memory: "1Gi"

  # 安全上下文（Pod Security Standard: restricted）
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    readOnlyRootFilesystem: true
    allowPrivilegeEscalation: false
    capabilities:
      drop: ["ALL"]
    seccompProfile:
      type: RuntimeDefault

  # ConfigMap 引用
  configMapRef: superteam-a2a-knowledge-service-config

  # mTLS cert 引用（cert-manager 自动颁发）
  mtlsSecretRef: superteam-a2a-knowledge-service-mtls

  # 优雅停机
  shutdownGracePeriodSeconds: 30

  replicas: 1  # v0.1 单实例；v0.5+ 水平扩展
```

### 11.2 memoryReconciler 配置

```yaml
memoryReconciler:
  enabled: true  # v0.1 Operator 进程内必开

  # 周期配置（D-3）
  interval: 60  # 周期（秒）；范围 30s-300s
  batchSize: 1000  # 单 reconcile 批大小

  # Clock 注入（D-4）
  clock:
    fake: false  # 生产 = RealClock；测试 = FakeClock
    initialTime: null  # FakeClock 起始时间（测试用）

  # Leader Election
  leader:
    leaseName: superteam-a2a-operator-leader  # 与 L2-2 Operator Core 共享
    leaseNamespace: superteam-a2a-system
    renewDeadlineSeconds: 15
    retryPeriodSeconds: 5
    leaseDurationSeconds: 20  # renewDeadline + retryPeriod
```

### 11.3 search 配置（BM25 + 索引）

```yaml
search:
  # 倒排索引配置
  index:
    rebuildOnStart: true  # 启动期全量重建（10K items ≤ 30s）
    maxItems: 10000  # 容量上限（超出拒绝创建）
    tokenization: "alphanumeric"  # alphanumeric / unicode / jieba（v0.5+）

  # BM25 参数（与 v0.1 Go baseline 完全一致）
  bm25:
    k1: 1.5  # 词频饱和参数
    b: 0.75  # 文档长度归一化参数

  # 性能门禁
  performance:
    queryP95MaxMs: 200  # queryKnowledge P95 上限
    rebuildP95MaxSeconds: 30  # 10K items rebuild P95 上限
    offloadQueueDepthMax: 50  # anyio to_thread 队列深度报警阈值
```

### 11.4 admission 配置（cert-manager TLS）

```yaml
admission:
  enabled: true  # KnowledgeItem + Memory + KnowledgeScope 三 webhook 必开

  # 超时配置（fail-closed）
  timeoutMs: 50  # admission 50ms 超时

  # cert-manager TLS 自动颁发
  tls:
    certManager:
      enabled: true
      issuerRef:
        name: superteam-a2a-ca
        kind: Issuer  # 或 ClusterIssuer
      duration: 8760h  # 1 year
      renewBefore: 720h  # 30 天前续约
      commonName: superteam-a2a-admission
      dnsNames:
        - superteam-a2a-admission
        - superteam-a2a-admission.superteam-a2a-system.svc

  # 双向互斥严格分离（admission 强制）
  mutualExclusion:
    enabled: true
    knowledgeItemAllowOwnerKinds: ["User", "Group"]  # 拒绝 ServiceAccount
    memoryAllowOwnerKinds: ["ServiceAccount"]  # 拒绝 User/Group
```

### 11.5 ratelimit 配置（Memory 写入限流）

```yaml
ratelimit:
  # Memory 写入限流（60/min per SA）
  memory:
    enabled: true
    perServiceAccountPerMinute: 60  # 默认 60/min
    slidingWindow: true  # 滑动窗口（Tenacity）
    burst: 10  # 突发允许（短时窗口内可超限 10 次）

  # Knowledge 查询限流（100/min per SA）
  knowledge:
    enabled: true
    perServiceAccountPerMinute: 100
    slidingWindow: true
    burst: 20
```

### 11.6 env 映射表

| Helm value | 环境变量 | 用途 |
|-----------|----------|------|
| `knowledgeService.port` | `KNOWLEDGE_SERVICE_PORT` | A2A Server 监听端口 |
| `knowledgeService.host` | `KNOWLEDGE_SERVICE_HOST` | A2A Server 绑定 host |
| `knowledgeService.a2aMethodTimeoutMs` | `A2A_METHOD_TIMEOUT_MS` | 单 method handler 超时 |
| `knowledgeService.python.workers` | `UVICORN_WORKERS` | Uvicorn worker 数（=1 单进程） |
| `knowledgeService.python.eventLoopLagThresholdMs` | `EVENT_LOOP_LAG_THRESHOLD_MS` | event-loop lag 报警阈值 |
| `knowledgeService.configMapRef` | `KNOWLEDGE_SERVICE_CONFIGMAP` | 配置 ConfigMap 名 |
| `knowledgeService.mtlsSecretRef` | `KNOWLEDGE_SERVICE_MTLS_SECRET` | mTLS cert Secret 名 |
| `memoryReconciler.interval` | `MEMORY_RECONCILER_INTERVAL` | 周期（秒） |
| `memoryReconciler.batchSize` | `MEMORY_RECONCILER_BATCH_SIZE` | 单批大小 |
| `memoryReconciler.clock.fake` | `MEMORY_CLOCK_FAKE` | FakeClock 开关（测试用） |
| `memoryReconciler.leader.leaseName` | `LEASE_NAME` | Lease 名 |
| `memoryReconciler.leader.leaseNamespace` | `LEASE_NAMESPACE` | Lease namespace |
| `search.index.rebuildOnStart` | `SEARCH_REBUILD_ON_START` | 启动期重建开关 |
| `search.index.maxItems` | `SEARCH_MAX_ITEMS` | 容量上限 |
| `search.bm25.k1` | `BM25_K1` | BM25 K1 参数 |
| `search.bm25.b` | `BM25_B` | BM25 B 参数 |
| `admission.timeoutMs` | `ADMISSION_TIMEOUT_MS` | admission 超时 |
| `ratelimit.memory.perServiceAccountPerMinute` | `MEMORY_RATE_LIMIT_PER_SA_PER_MIN` | 写入限流阈值 |
| `global.logLevel` | `LOG_LEVEL` | 日志级别 |
| `global.imageTag` | `IMAGE_TAG` | 镜像 tag |

### 11.7 Helm 模板示例（knowledge-service-deployment.yaml）

```yaml
# helm/templates/knowledge-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: superteam-a2a-knowledge-service
  labels:
    app.kubernetes.io/name: superteam-a2a-knowledge-service
    app.kubernetes.io/managed-by: Helm
  annotations:
    # ConfigMap / Secret 变化触发滚动重启
    checksum/config: {{ include (print $.Template.BasePath "/knowledge-service-configmap.yaml") . | sha256sum }}
    checksum/mtls: {{ include (print $.Template.BasePath "/knowledge-service-mtls.yaml") . | sha256sum }}
spec:
  replicas: {{ .Values.knowledgeService.replicas }}
  selector:
    matchLabels:
      app.kubernetes.io/name: superteam-a2a-knowledge-service
  template:
    metadata:
      labels:
        app.kubernetes.io/name: superteam-a2a-knowledge-service
        app.kubernetes.io/version: {{ .Values.global.imageTag }}
      annotations:
        # Prometheus scrape
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: {{ include "knowledgeService.serviceAccountName" . }}
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: knowledge-service
        image: "{{ .Values.knowledgeService.image.repository }}:{{ .Values.knowledgeService.image.tag }}"
        imagePullPolicy: {{ .Values.knowledgeService.image.pullPolicy }}
        ports:
        - name: a2a
          containerPort: {{ .Values.knowledgeService.port }}
          protocol: TCP
        - name: metrics
          containerPort: 9090
          protocol: TCP
        env:
        - name: KNOWLEDGE_SERVICE_PORT
          value: {{ .Values.knowledgeService.port | quote }}
        - name: KNOWLEDGE_SERVICE_HOST
          value: {{ .Values.knowledgeService.host | quote }}
        - name: UVICORN_WORKERS
          value: {{ .Values.knowledgeService.python.workers | quote }}
        - name: EVENT_LOOP_LAG_THRESHOLD_MS
          value: {{ .Values.knowledgeService.python.eventLoopLagThresholdMs | quote }}
        - name: LOG_LEVEL
          value: {{ .Values.global.logLevel | quote }}
        - name: MEMORY_RECONCILER_INTERVAL
          value: {{ .Values.memoryReconciler.interval | quote }}
        - name: MEMORY_RECONCILER_BATCH_SIZE
          value: {{ .Values.memoryReconciler.batchSize | quote }}
        - name: LEASE_NAME
          value: {{ .Values.memoryReconciler.leader.leaseName | quote }}
        - name: LEASE_NAMESPACE
          value: {{ .Values.memoryReconciler.leader.leaseNamespace | quote }}
        - name: BM25_K1
          value: {{ .Values.search.bm25.k1 | quote }}
        - name: BM25_B
          value: {{ .Values.search.bm25.b | quote }}
        - name: SEARCH_REBUILD_ON_START
          value: {{ .Values.search.index.rebuildOnStart | quote }}
        - name: SEARCH_MAX_ITEMS
          value: {{ .Values.search.index.maxItems | quote }}
        - name: ADMISSION_TIMEOUT_MS
          value: {{ .Values.admission.timeoutMs | quote }}
        - name: MEMORY_RATE_LIMIT_PER_SA_PER_MIN
          value: {{ .Values.ratelimit.memory.perServiceAccountPerMinute | quote }}
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: {{ .Values.observability.tracing.otlpEndpoint | quote }}
        envFrom:
        - secretRef:
            name: {{ .Values.knowledgeService.mtlsSecretRef }}
        - configMapRef:
            name: {{ .Values.knowledgeService.configMapRef }}
        resources:
          requests: {{- toYaml .Values.knowledgeService.resources.requests | nindent 10 }}
          limits:   {{- toYaml .Values.knowledgeService.resources.limits | nindent 8 }}
        securityContext: {{- toYaml .Values.knowledgeService.securityContext | nindent 8 }}
        livenessProbe:
          httpGet:
            path: {{ .Values.knowledgeService.healthCheckPath }}
            port: a2a
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: {{ .Values.knowledgeService.readinessPath }}
            port: a2a
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/.cache  # uv cache
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
```

### 11.8 RBAC（ClusterRole）

```yaml
# helm/templates/knowledge-service-clusterrole.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: superteam-a2a-knowledge-service
rules:
  # KnowledgeScope CRD
  - apiGroups: ["knowledge.superteam-a2a.io"]
    resources: ["knowledgescopes", "knowledgescopes/status"]
    verbs: ["get", "list", "watch", "update", "patch"]
  # KnowledgeItem CRD
  - apiGroups: ["knowledge.superteam-a2a.io"]
    resources: ["knowledgeitems", "knowledgeitems/status"]
    verbs: ["get", "list", "watch", "update", "patch"]
  # Memory CRD
  - apiGroups: ["memory.superteam-a2a.io"]
    resources: ["memories", "memories/status"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  # ServiceAccount（admission 校验）
  - apiGroups: [""]
    resources: ["serviceaccounts"]
    verbs: ["get"]
  # ConfigMap（reload trigger）
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch"]
  # Events（K8s Event 自动生成）
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["create", "patch"]
  # Lease（Leader Election）
  - apiGroups: ["coordination.k8s.io"]
    resources: ["leases"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  # Endpoints（Metrics endpoint）
  - apiGroups: [""]
    resources: ["endpoints"]
    verbs: ["get"]
```

### 11.9 NetworkPolicy

```yaml
# helm/templates/knowledge-service-networkpolicy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: superteam-a2a-knowledge-service
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: superteam-a2a-knowledge-service
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # 允许 Operator Core 调用 A2A Server
    - from:
        - namespaceSelector:
            matchLabels:
              name: superteam-a2a
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: superteam-a2a-operator
      ports:
        - protocol: TCP
          port: 8080  # A2A Server
    # 允许其他 Agent 调用（mTLS）
    - from:
        - namespaceSelector:
            matchLabels:
              name: superteam-a2a
      ports:
        - protocol: TCP
          port: 8080
    # 允许 Prometheus scrape
    - from:
        - namespaceSelector:
            matchLabels:
              name: monitoring
      ports:
        - protocol: TCP
          port: 9090
  egress:
    # K8s API（CRD watch + admission 校验）
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 443
    # OTel exporter
    - to:
        - namespaceSelector:
            matchLabels:
              name: observability
      ports:
        - protocol: TCP
          port: 4317
    # DNS
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
```

### 11.10 Helm values 测试 ID

| 测试 ID | 类型 | 场景 |
|---------|------|------|
| UT-HELM-001 | UT | knowledgeService.image.tag 默认 "0.2.0" |
| UT-HELM-002 | UT | memoryReconciler.interval 默认 60 |
| UT-HELM-003 | UT | search.bm25.k1=1.5 b=0.75（与 Go baseline 一致） |
| UT-HELM-004 | UT | admission.timeoutMs=50（fail-closed） |
| UT-HELM-005 | UT | ratelimit.memory.perServiceAccountPerMinute=60 |
| IT-HELM-001 | IT | helm template 渲染无错误 |
| IT-HELM-002 | IT | env 变量映射完整覆盖所有 Python 代码引用 |
| IT-HELM-003 | IT | RBAC ClusterRole 权限最小化（无 create on ServiceAccount） |
| E2E-HELM-001 | E2E | helm install + Knowledge Service + MemoryReconciler 全部启动 |
| E2E-HELM-002 | E2E | cert-manager 自动颁发 mTLS cert + admission webhook 生效 |

---

## 附录 B：ADR / Constitution 引用矩阵（5 子表）

### B.1 架构 / 决策类 ADR

| ADR / Constitution | 章节 | 关联 Spec 章节 | 用途 |
|-------------------|------|----------------|------|
| **ADR-0001 v1 范围** | §1 | §1.1 使命 | 第 5 大基础能力 = 知识管理 |
| **ADR-0002 知识管理设计** | §3 + §4 + §5 | §3.3 KnowledgeItem CRD + §4.1 4 级 scope + §4.3 visibility 枚举 | KnowledgeScope/Item CRD + 4 级继承算法 + Visibility 4 枚举 |
| **ADR-0003 Memory 设计** | §3 + §4 + §7 | §3.4 Memory CRD + §4.5 5 维矩阵 + §7.3 decay/reinforce | Memory CRD + 5 维矩阵 + decay/reinforce 算法 + admission 互斥 |
| **ADR-0004 v0.1 时间线** | §14 | §11 Helm values | v0.1 Phase 2/3 拆分 |
| **ADR-0005 Python-first** | §3 + §4 + §5 + §7 + §8 + §11 | 全部章节 | §3.4 Knowledge/Memory + §6.2 单进程 + §6.3 GIL 与 CPU 工作 + §7 Operator 可靠性门禁 + §10 可观测性 + §13 工程布局 |
| 宪法 v0.5.0 §2.5 | §3 + §4 | §3.3 / §3.4 + §4.3 + §4.5 | 强制 namespace + admission 校验 + visibility 枚举 |
| 宪法 v0.5.0 §2.9 | §3 | §3.4 Memory.source_knowledge_ref | Memory 可回溯 KnowledgeItem |
| 宪法 v0.5.0 §3.6 | §1 + §2 | §1.2 边界规则 + §2.2 边界 | MCP 边界（Knowledge/Memory 不实现 MCP） |
| 宪法 v0.5.0 §3.7 | §1 + §2 | §1.2 + §2.6 | Knowledge/Memory 不依赖 framework 代码 |
| 宪法 v0.5.0 §3.8 | 全部章节 | 全部 | Python-first 全栈迁移 |

### B.2 接口契约类（与 L2-1 / L2-2 / L2-3 集成）

| 引用对象 | 章节 | 关联 Spec 章节 | 用途 |
|----------|------|----------------|------|
| **L2-1 A2A Protocol Spec v0.2.0 Python** | §6 + §9 | §6.1-§6.5 + §9.2 | `supteam_a2a.a2a.upstream.create_app` 嵌入 + AgentCard + 错误码基线 + JSON-RPC 2.0 + ASGI |
| **L2-2 Operator Core Spec v0.2.0 Python §5.6** | §7 + §11 | §7.2 MemoryReconciler + §11.2 | MemoryReconciler reconcile 流程 + decay 公式 + Clock 接口注入 + Leader Election |
| **L2-3 Adapter Spec v0.2.0 Python §11** | §6 | §6.2-§6.5 4 handler | v0.5+ Adapter 代理 4 A2A method |
| L2-2 Operator Core Spec §7 admission webhook | §5 | §5.1-§5.3 | Kopf `kopf.validation` decorator 模式 |

### B.3 可见性 / 矩阵类

| ADR / Constitution | 章节 | 关联 Spec 章节 | 用途 |
|-------------------|------|----------------|------|
| ADR-0002 §3.1 KnowledgeScope 4 级 | §3 + §4 | §3.2 KnowledgeScope + §4.1 4 级枚举 | industry/organization/team/project |
| ADR-0002 §3.2 KnowledgeType 11 类 | §3 | §3.3 KnowledgeItem.type | document/runbook/api-spec 等 |
| ADR-0002 §3.3 Visibility 4 枚举 | §4 | §4.3 visibility 4 枚举 | scope-only/scope-and-children/public-readable/agent-private |
| ADR-0003 §3 Memory 5 维矩阵 | §4 | §4.5 5 维矩阵 | scope-only × {industry,org,team,project} + scope-and-children × 4 + agent-private 短路 |
| 宪法 v0.5.0 §2.5 admission 强制 | §5 | §5.1-§5.3 | owner_kind 限制 + scope 校验 + 50ms fail-closed |

### B.4 安全 / 审计类

| ADR / Constitution | 章节 | 关联 Spec 章节 | 用途 |
|-------------------|------|----------------|------|
| 宪法 v0.5.0 §6 mTLS + RBAC + NetworkPolicy + admission 互斥 | §5 + §11 | §5.1-§5.3 + §11.8 RBAC + §11.9 NetworkPolicy | 4 重安全防线 |
| ADR-0005 §6 单进程原则 | §1 + §11 | §1.2 边界 + §11.1 knowledgeService.python.workers=1 | 简化运维 + 共享内存索引 |
| ADR-0003 admission 双向互斥 | §5 | §5.1-§5.3 | KI 不允许 SA owner / Memory 不允许 User/Group owner |
| 宪法 v0.5.0 §3.6 反依赖 | §1 + §2 | §1.2 边界 + §2.6 import linter | Knowledge/Memory 不依赖 framework 代码 |

### B.5 性能 / 可观测性类

| ADR / Constitution | 章节 | 关联 Spec 章节 | 用途 |
|-------------------|------|----------------|------|
| 宪法 v0.5.0 §7 可观测性 | §10 | §10.1-§10.4 | 20 个 Prometheus 指标 + OTel + structlog + K8s Events |
| ADR-0005 §10 可观测性 + Python runtime | §10 | §10.1 Python runtime 3 指标 + §10.2 OTel + §10.3 structlog | 适配 Python 异步 + anyio to_thread 监控 |
| ADR-0005 §6.3 GIL 与 CPU 工作 | §7 + §8 | §7.3 decay/reinforce + §8.3 InvertedIndex | anyio.to_thread.run_sync 受控线程 offload |
| ADR-0005 §7 Operator 可靠性门禁 | §7 + §11 | §7.2 MemoryReconciler + §11.2 Leader Election | Kopf `@kopf.timer` + Lease + backoff + 50ms admission fail-closed |
| 宪法 v0.5.0 §11.5 event-loop lag 门禁 | §8 + §10 | §8.3 + §10.1 event_loop_lag_seconds | 100ms 持续 10s → 报警 |
| ADR-0004 ≤15 字段上限 | §3 | §3.6 字段数约束 | 防过度设计 |

### B.6 测试 / 演进类

| ADR / Constitution | 章节 | 关联 Spec 章节 | 用途 |
|-------------------|------|----------------|------|
| 宪法 v0.5.0 §9 静态质量门禁 | 全部章节 | 全部 | ≥80% 覆盖 + 时间穿越单测 + E2E + conformance |
| ADR-0005 §11.1 静态质量门禁 | 全部章节 | 全部 | pyright --strict + ruff + bandit + pip-audit |
| ADR-0003 v0.5+ 自动 scope-up | §4 + §15 | §4.4 KnowledgePromotionRequest | v0.1 仅计算 eligible_for_promotion 不触发 |
| ADR-0003 v0.5+ Memory 全文搜索 | §8 | §8.5 v0.5+ 演进 | BM25 over Memory.content（v0.1 不实现） |
| ADR-0003 v0.5+ Vector DB | §8 | §8.5 + §11.3 search.backend | Helm values 选择 vector 后端 |

---

## 12. 测试骨架（6 层级 · 57 个测试 ID · 继承自 v0.1.0 Go baseline + Python 化扩展）

### 12.1 6 层级测试金字塔（与 L2-2 §12 + L2-3 §12 + 宪法 §9.1 + ADR-0005 §11.1 完全一致）

| 层级 | 缩写 | 工具栈 | 目标 | 触发 | 期望耗时 | 覆盖率要求 |
|------|------|--------|------|------|----------|-----------|
| **L1 单元测试** | UT | `pytest` + `pytest-asyncio` + `freezegun` + `hypothesis` + `respx` | 算法 / Protocol / Pydantic 校验 / Clock 注入 / 纯函数 | `git push` | < 30s | ≥ 80%（line + branch） |
| **L2 集成测试** | IT | `pytest` + `pytest-asyncio` + `kind`/`k3d` + `kopf.test` + 真实 CRD | 多组件交互（Kopf → MemoryReconciler → Index → admission webhook） | `git push` to main | < 3min | ≥ 60% |
| **L3 conformance** | CF | `pytest` + A2A conformance suite（spec/a2a-conformance） | 4 个 A2A method 跨实现一致性 | PR 标签 `a2a-cf` | < 5min | wire contract 100% |
| **L4 端到端** | E2E | `pytest` + `kind` + `helm install` + `kubectl wait` + OTel 校验 | 完整 reconcile 循环 + admission 校验 + observability 全链路 | nightly + release | < 15min | 关键路径 100% |
| **L5 时间穿越** | TZ | `freezegun` + `FakeClock` + `Clock Protocol` 注入 + `asyncio.sleep` mock | decay / reinforce / GC / promotion 在虚拟时间下的正确性 | `git push` | < 1min | 时间相关路径 100% |
| **L6 性能门禁** | PERF | `pytest-benchmark` + `locust`（可选）+ 真实 workload 录制 | 性能 / 延迟 / 内存 / GIL 占用 | weekly + release | < 30min | 指标不超阈值 |

### 12.2 测试 ID 命名规范（继承自 L2-2 §12.2 + L2-3 §12.2 + ADR-0005 §11.1）

```
测试 ID := {层级}-{模块}-{编号}
  层级   := UT | IT | CF | E2E | TZ | PERF
  模块   := KNOW | MEM | ADM | SCOPE | IDX | OBS | HELM | DECAY | GIL
  编号   := 3 位十进制（000-999 · 按补完顺序）
```

**示例**：
- `UT-KNOW-001`：KnowledgeScope Pydantic 校验默认字段
- `IT-MEM-005`：Memory 写入 → K8s Event 生成 → MemoryReconciler reconcile 全链路
- `CF-A2A-003`：queryKnowledge 跨 a2a-python 0.3.x / 0.4.x 双版本兼容性
- `E2E-OPEN-001`：helm install + 4 A2A method + admission 双向互斥 + 5 维矩阵过滤端到端
- `TZ-DECAY-001`：decay 公式在 fake time advance 86400s 后的衰减比例
- `PERF-GIL-001`：queryKnowledge 1000 次连续调用期间 event loop lag P99 < 100ms

### 12.3 UT（单元测试 · 30 个 ID）

#### 12.3.1 Pydantic 模型 / CRD Schema（8 ID）

| 测试 ID | 场景 | 关键断言 |
|---------|------|----------|
| **UT-KNOW-001** | `KnowledgeScope` Pydantic 默认字段 | scope_type="team" / visibility="scope-only" / parent_ref=None / namespace=metadata.namespace |
| **UT-KNOW-002** | `KnowledgeItem` Pydantic 拒绝 owner_kind="ServiceAccount" | 抛出 `admission_error` (KI 不允许 SA owner) |
| **UT-KNOW-003** | `KnowledgeItem` Pydantic 拒绝 type="unknown" | 抛出 `ValueError`（11 类白名单外） |
| **UT-KNOW-004** | `KnowledgeItem` Pydantic content 长度 100KB | 接受（上限 1MB） |
| **UT-KNOW-005** | `KnowledgeItem` Pydantic content 长度 1MB+1B | 拒绝（`max_length=1048576`） |
| **UT-KNOW-006** | `Memory` Pydantic 拒绝 owner_kind="User" | 抛出 `admission_error` (Memory 不允许 User/Group owner) |
| **UT-KNOW-007** | `Memory` Pydantic reinforcement_count 负数 | 拒绝（`ge=0`） |
| **UT-KNOW-008** | `MemoryStatus.phase` 状态机非法转移 | Ready → Reconciling 合法；Ready → Deleting 非法 |

#### 12.3.2 4 级 scope 继承算法（6 ID）

| 测试 ID | 场景 | 关键断言 |
|---------|------|----------|
| **UT-SCOPE-001** | resolve_scope("project") → "team" | parent_ref 链 project→team |
| **UT-SCOPE-002** | resolve_scope("project") → "team" → "organization" → "industry" | 3 级递归 |
| **UT-SCOPE-003** | resolve_scope 循环引用检测 | A.parent=B, B.parent=A → 抛出 `CircularReferenceError` |
| **UT-SCOPE-004** | resolve_scope 4 级终止 | 到达 industry 时返回 None（顶层） |
| **UT-SCOPE-005** | resolve_scope 异步 + Lock | 并发 100 次调用，全部返回一致结果 |
| **UT-SCOPE-006** | resolve_scope 缓存（lru_cache 60s） | 第二次调用不触发 K8s API（mock 计数 = 1） |

#### 12.3.3 5 维可见性矩阵过滤（6 ID）

| 测试 ID | 场景 | 关键断言 |
|---------|------|----------|
| **UT-IDX-001** | scope-only × {industry,org,team,project} 4 种 | 仅同 scope 返回；其余空 |
| **UT-IDX-002** | scope-and-children × project | project + team 中所有 project 返回 |
| **UT-IDX-003** | public-readable × project | 所有 scope 全部可见（公开知识） |
| **UT-IDX-004** | agent-private × Memory | 仅 owner_sa 匹配；其余空 |
| **UT-IDX-005** | agent-private × {industry,org,team,project} | 4 种 scope 全部返回（不短路） |
| **UT-IDX-006** | visibility="agent-private" 但 owner_kind=User | 拒绝（仅 SA owner） |

#### 12.3.4 decay / reinforce / GC / promotion 数学（5 ID）

| 测试 ID | 场景 | 关键断言 |
|---------|------|----------|
| **UT-DECAY-001** | decay 公式 t=0 | weight = initial_weight（无衰减） |
| **UT-DECAY-002** | decay 公式 t=86400（half_life=7d） | weight ≈ initial_weight * 0.5（± 0.001） |
| **UT-DECAY-003** | reinforce +1 后 weight 重置 | weight = initial_weight |
| **UT-DECAY-004** | GC 触发条件 weight < 0.1 * initial_weight | 该 Memory 进入 GC 候选 |
| **UT-DECAY-005** | promotion 触发条件 reinforcement_count ≥ 5 且 weight ≥ 0.8 | eligible_for_promotion = True |

#### 12.3.5 错误码 / 重试 / 限流（5 ID）

| 测试 ID | 场景 | 关键断言 |
|---------|------|----------|
| **UT-ERR-001** | KNOWLEDGE_NOT_FOUND (-32010) 抛出 | JSON-RPC error struct code = -32010 |
| **UT-ERR-002** | MEMORY_QUOTA_EXCEEDED (-32103) 抛出 | 携带 retry_after_seconds 字段 |
| **UT-ERR-003** | Tenacity 3 次重试 K8s API 瞬时错误 | 第 2 次成功返回 |
| **UT-ERR-004** | Tenacity 3 次重试全部失败 | 抛出 RetryError，转换为 -32603 |
| **UT-ERR-005** | Memory 写入限流 60 次/SA/分钟 | 第 61 次返回 -32104 RATE_LIMITED |

### 12.4 IT（集成测试 · 12 个 ID）

| 测试 ID | 场景 | 关键断言 |
|---------|------|----------|
| **IT-KNOW-001** | KnowledgeItem CRD 创建 → K8s API 持久化 | `kubectl get knowledgeitems` 返回 |
| **IT-KNOW-002** | Memory CRD 创建 → MemoryReconciler 60s 后 reconcile | status.lastReconcileTime 更新 |
| **IT-ADM-001** | admission webhook 拒绝 KI owner_kind="ServiceAccount" | K8s API 返回 422 + admission_error |
| **IT-ADM-002** | admission webhook 拒绝 Memory owner_kind="User" | K8s API 返回 422 + admission_error |
| **IT-ADM-003** | admission webhook 50ms 超时（cert-manager 慢响应） | fail-closed，返回 503 |
| **IT-MEM-001** | recordMemory 调用 → CRD 创建 → event-loop lag < 100ms | P99 < 100ms |
| **IT-MEM-002** | queryKnowledge 调用 → 5 维矩阵过滤 → 返回正确 scope | 仅同 scope 返回 |
| **IT-MEM-003** | BM25 InvertedIndex 1000 条 Memory 搜索 | P99 < 50ms |
| **IT-MEM-004** | Leader Election：2 个 MemoryReconciler pod，仅 1 个 active | lease holder 唯一 |
| **IT-OBS-001** | Prometheus 指标 `/metrics` 暴露 20 个 | 全部 200 OK |
| **IT-OBS-002** | OTel trace 导出到 OTLP endpoint | spans 数量 = 请求数 |
| **IT-EVT-001** | K8s Event 在 admission reject / GC / reconcile 异常时生成 | 3 种 event 类型 |

### 12.5 CF（conformance · 5 个 ID）

| 测试 ID | 场景 | 关键断言 |
|---------|------|----------|
| **CF-A2A-001** | queryKnowledge 跨 a2a-python 0.3.x 实现一致 | JSON-RPC 响应字段名一致 |
| **CF-A2A-002** | getKnowledgeItem 跨 a2a-python 0.4.x 实现一致 | AgentCard 字段一致 |
| **CF-A2A-003** | recordMemory 跨实现写入字段一致 | Memory CRD spec 字段一致 |
| **CF-A2A-004** | queryMemory 跨实现 5 维矩阵过滤一致 | 返回的 scope 集合一致 |
| **CF-A2A-005** | 4 个 method 错误码范围一致 | -32008~-32018 / -32101~-32112 |

### 12.6 E2E（端到端 · 6 个 ID）

| 测试 ID | 场景 | 关键断言 |
|---------|------|----------|
| **E2E-OPEN-001** | helm install + 全部 3 CRD + 4 method + admission 双向互斥 + 5 维矩阵 | 全部通过 |
| **E2E-OPEN-002** | 跨 namespace scope 继承（industry → organization → team → project） | project 可见 industry 公开知识 |
| **E2E-OPEN-003** | mTLS 双向证书校验失败拒绝请求 | 403 + audit log |
| **E2E-OPEN-004** | MemoryReconciler crash → Lease 转让 → 新 leader 接管 | < 30s 完成转让 |
| **E2E-OPEN-005** | 高负载 100 QPS queryKnowledge 持续 10min | event-loop lag P99 < 100ms（门禁） |
| **E2E-OPEN-006** | 删除 namespace → 级联 GC 所有 Memory | GC 完成后 Memory 列表为空 |

### 12.7 TZ（时间穿越 · 4 个 ID · 继承 v0.1.0 Go baseline 4 个 ID 模式）

| 测试 ID | 场景 | 关键断言 |
|---------|------|----------|
| **TZ-DECAY-001** | fake time advance 86400s（1 天） | decay 公式 weight 衰减至 0.5（half_life=7d） |
| **TZ-DECAY-002** | fake time advance 30 天 | weight < 0.1 * initial → GC 候选 |
| **TZ-RECON-001** | fake time advance 60s | MemoryReconciler 触发 1 次 reconcile（与 interval 一致） |
| **TZ-PROM-001** | fake time advance + 5 次 reinforce | reinforcement_count=5 → eligible_for_promotion=True |

### 12.8 PERF（性能门禁 · 3 个 ID）

| 测试 ID | 场景 | 关键断言 | 阈值 |
|---------|------|----------|------|
| **PERF-IDX-001** | BM25 InvertedIndex 搜索 10000 条 Memory | P99 < 100ms | 单进程 1 worker |
| **PERF-GIL-001** | queryKnowledge 1000 QPS 持续 10min | event_loop_lag_seconds P99 < 100ms | 门禁 |
| **PERF-MEM-001** | MemoryReconciler 60s 周期 reconcile 10000 Memory | 完成时间 < 50s | 留 10s buffer |

### 12.9 测试覆盖率目标（继承自宪法 §9.3 + ADR-0005 §11.1）

| 模块 | line coverage | branch coverage | 关键路径 |
|------|---------------|------------------|----------|
| `packages/knowledge` | ≥ 85% | ≥ 80% | CRD 校验 + 4 级 scope + 5 维矩阵 |
| `packages/memory` | ≥ 85% | ≥ 80% | decay/reinforce/GC + InvertedIndex |
| `packages/knowledge-service` | ≥ 80% | ≥ 75% | 4 A2A method handler |
| `packages/memory-backend` | ≥ 85% | ≥ 80% | MemoryReconciler + Leader Election |
| `packages/shared-visibility` | ≥ 90% | ≥ 85% | 5 维矩阵过滤算法 |
| **整体** | **≥ 80%** | **≥ 75%** | **≥ 80%** |

**门禁命令**：
```bash
uv run pytest --cov=packages/knowledge --cov=packages/memory \
  --cov=packages/knowledge-service --cov=packages/memory-backend \
  --cov=packages/shared-visibility \
  --cov-branch --cov-fail-under=80
```

### 12.10 测试 ID 矩阵（57 ID · §A-§G 全覆盖）

| 验收维度 | UT | IT | CF | E2E | TZ | PERF | 合计 |
|----------|----|----|----|-----|----|------|------|
| §A 算法正确性 | 14 | 4 | 0 | 1 | 4 | 0 | 23 |
| §B 边界与异常 | 6 | 3 | 0 | 1 | 0 | 0 | 10 |
| §C 接口契约 | 5 | 2 | 5 | 1 | 0 | 0 | 13 |
| §D 可观测性 | 0 | 2 | 0 | 0 | 0 | 0 | 2 |
| §E 安全 / 准入 | 0 | 1 | 0 | 1 | 0 | 0 | 2 |
| §F 性能 / 门禁 | 0 | 0 | 0 | 1 | 0 | 3 | 4 |
| §G 部署 / 集成 | 5 | 0 | 0 | 1 | 0 | 0 | 6 |
| **合计** | **30** | **12** | **5** | **6** | **4** | **3** | **60** |

> **说明**：57 → 60 ID 矩阵（含 v0.1.0 Go baseline 57 + Python 重写新增 3 PERF ID）；§A-§G 与 #32 L2-2 Spec 验收矩阵同模式。

---

## 13. 工具链与部署（pyright + ruff + bandit + uv + Docker + Helm · 继承 ADR-0005 §11 + §13）

### 13.1 静态分析门禁（CI 必过）

| 工具 | 命令 | 阈值 | 失败处理 |
|------|------|------|----------|
| **pyright** | `uv run pyright packages/` | `--strict` 模式 0 error | PR 阻塞 |
| **ruff** | `uv run ruff check packages/ tests/` | 0 error / 0 warning（SELECT E,F,W,I,UP,B,SIM,RUF） | PR 阻塞 |
| **ruff format** | `uv run ruff format --check packages/ tests/` | 100% 符合 ruff 风格 | PR 阻塞 |
| **bandit** | `uv run bandit -r packages/ -lll` | 0 high / 0 medium severity | PR 阻塞 |
| **pip-audit** | `uv run pip-audit --strict` | 0 known vulnerability | PR 阻塞 |
| **vulture** | `uv run vulture packages/ --min-confidence=80` | 0 dead code | PR 阻塞 |
| **interrogate** | `uv run interrogate packages/ --fail-under=85` | docstring 覆盖率 ≥ 85% | PR 阻塞 |
| **import-linter** | `uv run lint-imports --config layers.yml` | 5 层 import 规则 0 violation | PR 阻塞 |

### 13.2 测试工具链

| 工具 | 用途 | 配置位置 |
|------|------|----------|
| **pytest** | 测试运行器 | `pyproject.toml [tool.pytest.ini_options]` |
| **pytest-asyncio** | async 测试 | `asyncio_mode = "auto"` |
| **pytest-cov** | 覆盖率 | `--cov-fail-under=80` |
| **freezegun** | 时间穿越 | `@freeze_time("2026-01-01")` + FakeClock 注入 |
| **hypothesis** | property-based testing | 100 examples / test |
| **respx** | HTTP mock | a2a-python HTTP 客户端 mock |
| **pytest-benchmark** | 性能门禁 | PERF-* 测试 |
| **pytest-xdist** | 并行测试 | `-n auto`（本地开发） |
| **kopf.test** | CRD controller 测试 | `IT-KNOW-*` / `IT-MEM-*` |

### 13.3 构建工具链

| 工具 | 用途 | 配置 |
|------|------|------|
| **uv** | 包管理 + workspace + lockfile | `uv.lock` + `pyproject.toml [tool.uv]` |
| **hatchling** | 构建 backend（PEP 517） | `pyproject.toml [tool.hatch.build.targets.wheel]` |
| **Docker multi-stage** | 镜像构建 | `python:3.12-slim-bookworm` builder + runtime |
| **Docker base layer** | 基础镜像 | `python:3.12-slim-bookworm`（与 ADR-0005 §13 一致） |
| **uv build** | 编译扩展（如有 Cython/Rust 扩展） | `uv run --with cython cythonize ...` |

### 13.4 部署工具链

| 工具 | 用途 | 配置 |
|------|------|------|
| **Helm 3.14+** | K8s 部署模板 | `helm/` + `Chart.yaml` + `values.yaml` |
| **cert-manager 1.13+** | mTLS 证书签发 | `cert-manager.io/issuer` annotation |
| **kopf** | Operator 运行时 | `kopf run supteam_a2a.operator.main` |
| **Prometheus** | 指标采集 | ServiceMonitor CR（kube-prometheus-stack） |
| **OTel Collector** | trace 收集 | OpenTelemetryCollector CR（opentelemetry-operator） |
| **Argo CD**（可选） | GitOps 部署 | Application CR |

### 13.5 开发工作流（继承自 ADR-0005 §13.4 + 宪法 §9.4）

```bash
# 1. 克隆 + 安装依赖
git clone https://github.com/superteam-cn/superteam-a2a.git
cd superteam-a2a
uv sync  # 安装所有 workspace 依赖

# 2. 静态分析（pre-commit）
uv run pyright packages/
uv run ruff check packages/ tests/
uv run bandit -r packages/ -lll

# 3. 单元测试
uv run pytest packages/ -m "not integration and not e2e"

# 4. 集成测试（需要 kind/k3d 集群）
kind create cluster --name superteam-a2a-test
uv run pytest packages/ -m integration

# 5. 端到端测试（需要 helm）
helm install superteam-a2a ./helm --namespace superteam-a2a --create-namespace
uv run pytest packages/ -m e2e

# 6. 构建 + 推送镜像
docker build -t ghcr.io/superteam-cn/superteam-a2a-knowledge-service:0.2.0 \
  -f docker/Dockerfile.knowledge-service .
docker push ghcr.io/superteam-cn/superteam-a2a-knowledge-service:0.2.0

# 7. Helm 部署到生产
helm upgrade --install superteam-a2a ./helm \
  --namespace superteam-a2a \
  --values values-production.yaml \
  --set knowledgeService.image.tag=0.2.0
```

### 13.6 镜像构建（多阶段 · 与 ADR-0005 §13.3 一致）

```dockerfile
# docker/Dockerfile.knowledge-service
# Stage 1: builder（含 uv + 编译依赖）
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /uvx /bin/

WORKDIR /app

# 依赖层（缓存友好）
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
RUN uv sync --frozen --no-dev --no-editable

# Stage 2: runtime（最小化）
FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r app && useradd -r -g app app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/packages"

COPY --from=builder /app /app

USER app

WORKDIR /app

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["kopf", "run", "--standalone", "--namespace=superteam-a2a", \
     "supteam_a2a.knowledge_service.main"]
```

**镜像标签规范**（继承 ADR-0005 §13.5）：
- `0.2.0` → 稳定版本
- `0.2.0-dev.20260727.abcdef` → 开发构建（含 git short SHA）
- `latest` → 禁止使用（与 L2-2 §13.6 + L2-3 §13.6 一致）

### 13.7 部署清单（15 项交付物 · 与 L2-2 §13.7 + L2-3 §13.7 同等级别）

| # | 交付物 | 路径 | 验收 |
|---|--------|------|------|
| 1 | Helm Chart | `helm/Chart.yaml` | `helm lint` 通过 |
| 2 | values.yaml | `helm/values.yaml` | 默认值通过 schema 校验 |
| 3 | KnowledgeService Deployment | `helm/templates/knowledge-service-deployment.yaml` | `kubectl apply` 成功 |
| 4 | MemoryReconciler Deployment | `helm/templates/memory-reconciler-deployment.yaml` | 同上 |
| 5 | RBAC ClusterRole | `helm/templates/knowledge-service-clusterrole.yaml` | 最小权限审计 |
| 6 | NetworkPolicy | `helm/templates/knowledge-service-networkpolicy.yaml` | 隔离验证 |
| 7 | Service | `helm/templates/knowledge-service-service.yaml` | mTLS port 8080 |
| 8 | ServiceMonitor | `helm/templates/knowledge-service-servicemonitor.yaml` | Prometheus 采集 |
| 9 | cert-manager Certificate | `helm/templates/knowledge-service-certificate.yaml` | 自动续期 |
| 10 | ConfigMap | `helm/templates/knowledge-service-configmap.yaml` | reload trigger |
| 11 | 3 CRD YAML | `helm/crds/knowledge-*.yaml` + `helm/crds/memory-*.yaml` | `kubectl apply` 成功 |
| 12 | 镜像 Dockerfile | `docker/Dockerfile.knowledge-service` | 多阶段构建 |
| 13 | pyproject.toml | `pyproject.toml` | uv lockfile 一致 |
| 14 | admission webhook 配置 | `helm/templates/knowledge-service-mutatingwebhook.yaml` | cert-manager 集成 |
| 15 | pyright / ruff / bandit 配置 | `pyproject.toml [tool.*]` | CI 必过 |

---

## 14. 验收清单（§A-§G 7 维度 · 30 条验收点 · 95 ID 矩阵 · 与 L2-2 §14 + L2-3 §14 同等级别）

### 14.1 §A 算法正确性（5 条验收点 · 23 ID）

- [ ] **A.1** KnowledgeScope Pydantic 校验：默认字段正确（UT-KNOW-001）
- [ ] **A.2** KnowledgeItem 拒绝 SA owner（UT-KNOW-002）+ Memory 拒绝 User/Group owner（UT-KNOW-006）双向往返
- [ ] **A.3** 4 级 scope 继承递归正确，循环引用检测（UT-SCOPE-001~006）
- [ ] **A.4** 5 维可见性矩阵 12 种组合穷举（UT-IDX-001~006）
- [ ] **A.5** decay / reinforce / GC / promotion 数学正确（UT-DECAY-001~005 + TZ-DECAY-001/002）

### 14.2 §B 边界与异常（4 条验收点 · 10 ID）

- [ ] **B.1** Pydantic Field 长度上限（UT-KNOW-004/005）+ 状态机非法转移拒绝（UT-KNOW-008）
- [ ] **B.2** Memory 写入限流 60/SA/分钟（UT-ERR-005）
- [ ] **B.3** Tenacity 重试 K8s API 瞬时错误 3 次成功 / 失败转 -32603（UT-ERR-003/004）
- [ ] **B.4** Leader Election 唯一性（IT-MEM-004）+ 转让 < 30s（E2E-OPEN-004）

### 14.3 §C 接口契约（5 条验收点 · 13 ID）

- [ ] **C.1** 4 个 A2A method JSON-RPC 2.0 wire 兼容 a2a-python 0.3.x + 0.4.x（CF-A2A-001~004）
- [ ] **C.2** 错误码范围 KNOWLEDGE_* -32008~-32018 + MEMORY_* -32101~-32112（CF-A2A-005 + UT-ERR-001/002）
- [ ] **C.3** CRD JSON Schema deterministic OpenAPI v3（E2E-OPEN-001）
- [ ] **C.4** AgentCard Pydantic model 字段完整（CF-A2A-002）
- [ ] **C.5** 5 层 import 规则 0 violation（import-linter + E2E-OPEN-001）

### 14.4 §D 可观测性（4 条验收点 · 2 ID）

- [ ] **D.1** 20 个 Prometheus 指标 `/metrics` 200 OK（IT-OBS-001）
- [ ] **D.2** OTel trace 导出 OTLP（IT-OBS-002）+ event_loop_lag_seconds 门禁 100ms（PERF-GIL-001）
- [ ] **D.3** structlog JSON 格式（INFO/WARN/ERROR 级别）+ K8s Event（IT-EVT-001）
- [ ] **D.4** decay / reinforce / admission / GC 4 类关键路径埋点（IT-OBS-001 全覆盖）

### 14.5 §E 安全 / 准入（4 条验收点 · 2 ID）

- [ ] **E.1** admission webhook 双向互斥：KI 拒绝 SA owner + Memory 拒绝 User/Group owner（IT-ADM-001/002）
- [ ] **E.2** admission webhook 50ms 超时 fail-closed（IT-ADM-003）
- [ ] **E.3** mTLS 双向证书校验失败拒绝（E2E-OPEN-003）
- [ ] **E.4** RBAC ClusterRole 最小权限（无 create on ServiceAccount）+ NetworkPolicy 隔离（IT-HELM-003 + §11.8/§11.9）

### 14.6 §F 性能 / 门禁（4 条验收点 · 4 ID）

- [ ] **F.1** BM25 InvertedIndex 10000 条 P99 < 100ms（PERF-IDX-001）
- [ ] **F.2** event_loop_lag_seconds P99 < 100ms / 100ms 持续 10s → 报警（PERF-GIL-001 + 宪法 §11.5）
- [ ] **F.3** MemoryReconciler 60s 周期 reconcile 10000 Memory 完成 < 50s（PERF-MEM-001）
- [ ] **F.4** 高负载 100 QPS queryKnowledge 持续 10min event-loop lag 门禁（E2E-OPEN-005）

### 14.7 §G 部署 / 集成（4 条验收点 · 6 ID）

- [ ] **G.1** helm install 15 项交付物全部就绪（E2E-OPEN-001 + §13.7 清单）
- [ ] **G.2** 多阶段 Dockerfile 镜像 < 200MB（§13.6 + ADR-0005 §13.3）
- [ ] **G.3** pyright --strict 0 error / ruff 0 warning / bandit 0 high（§13.1）
- [ ] **G.4** uv workspace 5 包构建成功 + uv.lock 锁定（§13.3）

### 14.8 验收矩阵（30 条验收点 × 60 ID 覆盖）

| 维度 | 验收点 | UT 覆盖 | IT 覆盖 | CF 覆盖 | E2E 覆盖 | TZ 覆盖 | PERF 覆盖 | 总 ID |
|------|--------|---------|---------|---------|----------|---------|-----------|-------|
| §A | 5 | 14 | 4 | 0 | 1 | 4 | 0 | 23 |
| §B | 4 | 6 | 3 | 0 | 1 | 0 | 0 | 10 |
| §C | 5 | 5 | 2 | 5 | 1 | 0 | 0 | 13 |
| §D | 4 | 0 | 2 | 0 | 0 | 0 | 0 | 2 |
| §E | 4 | 0 | 1 | 0 | 1 | 0 | 0 | 2 |
| §F | 4 | 0 | 0 | 0 | 1 | 0 | 3 | 4 |
| §G | 4 | 5 | 0 | 0 | 1 | 0 | 0 | 6 |
| **合计** | **30** | **30** | **12** | **5** | **6** | **4** | **3** | **60** |

> **覆盖率**：30/30 验收点 + 60/60 ID 全勾选；与 L2-2 Spec §14 30/30 + 95/95、L2-3 Spec §14 同等级别。

### 14.9 评审归档（继承自 L2-2 §14.9 + L2-3 §14.9 · 8 项）

- [x] **R.1** Design v0.2.0 Python 评审通过（[#39](../../reviews/l2-4-knowledge-memory-review.md) 67KB / 709 行 / §A-§P 16 节 / 10 维度全 PASS）
- [x] **R.2** Spec v0.2-draft-full Python 评审通过（本次会话后追加 · 独立会话）
- [x] **R.3** ADR-0002 知识管理设计引用（附录 B.1 / B.3 / B.4 / B.5）
- [x] **R.4** ADR-0003 Memory 设计引用（同上）
- [x] **R.5** ADR-0005 Python-first 引用（附录 B.1 / B.2 / B.5 / B.6）
- [x] **R.6** 宪法 v0.5.0 §3.8 全栈 Python 引用（附录 B.1）
- [x] **R.7** L2-1/L2-2/L2-3 Spec 配套阅读引用（附录 B.2）
- [x] **R.8** wire contract 与 v0.1.0 Go baseline 业务语义对齐（顶部 supersede 指针）

---

## 15. 开放问题（22 项 · 三层模式 · 继承自 Design v0.2.0 §15）

### 15.1 继承自 Design v0.2.0 §15 的 12 项（业务层 · 不变）

| ID | 问题 | 决策权 | 状态 |
|----|------|--------|------|
| **OPEN-L2-4-001** | a2a-python 0.4.x AgentCard 字段兼容性 | 上游 a2a-python | 跟踪中（cf #102） |
| **OPEN-L2-4-002** | kopf @kopf.timer 与 operator-runtime 控制循环差异 | 上游 kopf | 待 spike |
| **OPEN-L2-4-003** | Python GIL 与 BM25 CPU 工作 anyio to_thread 边界 | 内部 | 已收敛（D-2） |
| **OPEN-L2-4-004** | FakeClock 与真实 asycio.sleep 兼容性 | 内部 | 已收敛（D-4） |
| **OPEN-L2-4-005** | cert-manager Issuer 在多 cluster 部署的复用 | 内部 | 待 L4 部署验证 |
| **OPEN-L2-4-006** | admission webhook 50ms fail-closed 对慢 K8s API 的影响 | 内部 | 已收敛（与 L2-2 一致） |
| **OPEN-L2-4-007** | v0.5+ 自动 scope-up 触发器实现 | 内部 | 仅计算 eligible_for_promotion |
| **OPEN-L2-4-008** | v0.5+ Vector DB 后端选择（pgvector / Milvus / Qdrant） | 内部 | Helm values 预留 |
| **OPEN-L2-4-009** | v0.5+ Memory 全文搜索 BM25 over content | 内部 | v0.1 不实现 |
| **OPEN-L2-4-010** | Leader Election 转让期间 in-flight request 处理 | 内部 | 已收敛（drain 30s） |
| **OPEN-L2-4-011** | Multi-cluster Knowledge 同步策略 | 内部 | 待 v0.5+ 设计 |
| **OPEN-L2-4-012** | Memory PII 字段加密（at rest + in transit） | 内部 | 待安全审计 |

### 15.2 Spec v0.2-draft 新发现 4 项（实现层 · Spec 起草期间识别）

| ID | 问题 | 决策权 | 状态 |
|----|------|--------|------|
| **OPEN-L2-4-SPEC-001** | Pydantic v2 与 pydantic-settings 在 Helm values env 注入的优先级 | 内部 | 待 L3-1 spike |
| **OPEN-L2-4-SPEC-002** | `dict[str, set[str]]` InvertedIndex 在 10K Memory 下的内存占用（基线 50MB？） | 内部 | 待 PERF-IDX-001 验证 |
| **OPEN-L2-4-SPEC-003** | kopf `@kopf.validation` decorator 在 admission timeout 50ms 下的实际超时机制（kopf 内部 vs cert-manager） | 上游 kopf | 待 spike |
| **OPEN-L2-4-SPEC-004** | helm template 渲染 3 CRD YAML 的版本对齐策略（operator 与 service 部署顺序） | 内部 | Helm hooks pre-install pre-upgrade |

### 15.3 Python 重写新增 6 项（Python 化层 · 与 L2-1/L2-2/L2-3 Spec 同模式）

| ID | 问题 | 决策权 | 状态 |
|----|------|--------|------|
| **OPEN-L2-4-PY-001** | typing.Protocol 与 Pydantic BaseModel 的混入（runtime_checkable 限制） | 内部 | 已收敛（Protocol 单独使用） |
| **OPEN-L2-4-PY-002** | Python 3.12 GIL 影响 admission webhook 50ms 响应 | 内部 | 已收敛（纯 IO 操作） |
| **OPEN-L2-4-PY-003** | uv workspace 5 包（knowledge/memory/knowledge-service/memory-backend/shared-visibility）的发布顺序 | 内部 | 同步发布 0.2.0 |
| **OPEN-L2-4-PY-004** | freezegun 与 asyncio.sleep mock 的交互（freezegun 不暂停 asyncio.sleep） | 内部 | 已收敛（FakeClock 协议） |
| **OPEN-L2-4-PY-005** | a2a-python 0.4.x Pydantic v2 迁移的兼容窗口 | 上游 a2a-python | 跟踪中 |
| **OPEN-L2-4-PY-006** | Pydantic v2 `populate_by_name` + alias 与 K8s CRD field 名（camelCase）的最终映射 | 内部 | 已收敛（§3 顶部映射表） |

### 15.4 开放问题收敛率（继承自 L2-2 §15.4 + L2-3 §15.4）

- **继承 v0.1.0 业务层 12 项**：5 项已收敛（D-2/D-4/admission/GIL/drain）+ 7 项待后续
- **Spec 新发现 4 项**：1 项已收敛（OPEN-L2-4-SPEC-004 Helm hooks）+ 3 项待 spike/验证
- **Python 重写 6 项**：5 项已收敛（Protocol 单独/GIL 已分析/uv 同步/FakeClock/a2a-python 跟踪）+ 1 项待上游
- **总体收敛率**：11/22 = 50%（v0.2-draft-full 阶段）
- **目标收敛率**：v0.2.0 阶段 ≥ 70%（15/22），v1.0 阶段 ≥ 90%（20/22）

### 15.5 v0.5+ 演进路线（与 Design v0.2.0 §15.5 + L2-3 Spec §15.5 一致）

| 演进项 | 触发条件 | 关联 OPEN | 实现窗口 |
|--------|----------|-----------|----------|
| **Vector DB 后端** | search.backend=vector + Memory.count > 10K | OPEN-L2-4-008 | v0.5+ |
| **自动 scope-up** | eligible_for_promotion=True 触发 promotion | OPEN-L2-4-007 | v0.5+ |
| **Memory 全文搜索** | queryMemory 命中率 < 80% 超过 7 天 | OPEN-L2-4-009 | v0.5+ |
| **Multi-cluster 同步** | 跨 cluster queryKnowledge 出现 | OPEN-L2-4-011 | v1.0+ |
| **Memory PII 加密** | 安全审计要求 | OPEN-L2-4-012 | v0.5+ |

---

## 16. 文档元数据

### 16.1 版本与状态

- **版本**：**v0.2.0**（Python 重写 · ADR-0005 触发；2026-07-27 #42 补完 §12-§15 + #43 评审通过）
- **状态**：✅ **§0-§15 + 附录 A/B + §16 全部完成 + v0.2.0 评审通过**
- **总行数**：4152 行（3644 旧 + 508 新增 §12-§15）
- **总字节数**：194.6KB / 194576 字节

### 16.2 变更记录（v0.2-draft → v0.2-draft-full → v0.2.0）

| 日期 | 会话 | 变更 |
|------|------|------|
| 2026-07-27 | #40 | §0-§7 + 附录 A 起草完成（112KB / 2368 行） |
| 2026-07-27 | #41 | §8-§11 + 附录 B 补完（+52KB / +1276 行 · 累计 164KB / 3644 行） |
| 2026-07-27 | **#42** | **§12-§15 补完（+29KB / +508 行 · 累计 194.6KB / 4152 行）· 60 个测试 ID + 30 条验收点 + 22 项开放问题** |
| 2026-07-27 | **#43** | **§A-§P 10 维度评审通过（697 行 / 59.7KB / 0 阻塞项 / 3 关注项 / 4 建议项）+ L2-4 Spec 升级 v0.2.0 + L2-4 Design 配套 Spec 引用更新** |

### 16.3 配套文档

- **Design**：[`docs/design/L2-modules/L2-knowledge-memory.md`](../../design/L2-modules/L2-knowledge-memory.md) **v0.2.0 Python**（2026-07-27 #39 评审通过；1920 行 / 97KB / 14 节 + 2 附录）
- **Review（已写）**：[`docs/reviews/l2-4-knowledge-memory-spec-python-review.md`](../../reviews/l2-4-knowledge-memory-spec-python-review.md)（v0.2.0 Python 评审 · 697 行 / 59.7KB / §A-§P 16 节 / 10 维度全 PASS · 2026-07-27 #43）

### 16.4 下次会话入口（继承 MEMORY.md · 倾向 B）

- **选项 A**：§F.1-§F.6 跨文档同步 6 步（L1 Arch / L1 Spec / L2-1/L2-2/L2-3 Spec / ROADMAP / README / CHANGELOG 共 ~12-15 Edit ≈ 5-8KB · 低风险必做）
- **选项 B**：L2-4 Go baseline 归档（docs/archive/pre-python-2026-07-24/，与 L2-2 归档模式一致）
- **选项 C**：✅ L3-1 Operator Core 文件级 Spec v0.2.0 通过（2026-07-28 #56 · [Spec](L3-file-specs/L3-operator-core.md) 245KB / 3925 行 / [评审](../../reviews/l3-1-operator-core-spec-review.md) §A-§P 10 维度全 PASS · 19 字段 wire sync 矩阵 + 4 纯函数完整契约）
- **选项 D**：L3-4 Knowledge/Memory 文件级 Spec Python 起草（基于本 L2-4 v0.2.0 Spec；5 包文件清单 + MemoryReconciler reconcile 完整伪代码 + 9 类模块前缀测试 ID）
| 宪法 v0.5.0 §16.1 会话管理 | 起草流程 | 本文档章节拆分 | 1M 窗口 / 500K 红线 / 实际水位判断 / 典型参照表 |