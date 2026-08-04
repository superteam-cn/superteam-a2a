# L2 模块设计：Knowledge / Memory（知识管理 + 持久化记忆 · Python-first）

> **层级**：L2 — 模块设计
> **模块 ID**：C-4（Knowledge / Memory，见 L1 v0.2.0 Architecture §3.5.2 / §3.5.3）
> **代码位置**：`packages/knowledge/src/supteam_a2a/knowledge/` + `packages/memory/src/supteam_a2a/memory/` + `packages/knowledge-service/src/supteam_a2a/knowledge_service/` + `packages/memory-backend/src/supteam_a2a/memory_backend/` + `packages/shared-visibility/src/supteam_a2a/shared/visibility/`（**Python-first · ADR-0005 §13 工程布局 · uv workspace**）
> **版本**：**v0.2.0**（Python 重写 · ADR-0005 触发；2026-07-26 起草 + 2026-07-27 评审通过）
> **状态**：✅ v0.2.0 已评审通过（[`docs/reviews/l2-4-knowledge-memory-python-review.md`](../../reviews/l2-4-knowledge-memory-python-review.md) §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项；与 v0.1.0 Go baseline wire contract 完全继承）
> **supersedes**：v0.1.0 Go baseline（[`docs/reviews/l2-4-knowledge-memory-review.md`](../../reviews/l2-4-knowledge-memory-review.md) 2026-07-24 通过；**仅 supersede Go struct / Go interface / Go package / Go 镜像块 / kubebuilder annotation 实现条款**；wire contract（3 CRD 字段 / 4 A2A method / 5 维可见性矩阵 / decay/reinforce 算法 / admission 双向互斥 / BM25 评分 / 状态机）与 v0.1 业务语义**完全继续有效**）
> **配套 Spec**：[`docs/spec/L2-module-specs/L2-knowledge-memory.md`](../../spec/L2-module-specs/L2-knowledge-memory.md)（**v0.2.0 Python** · 2026-07-27 #43 评审通过 · 4152 行 / 194.6KB / §0-§15 + 附录 A/B + §16 元数据 / 60 测试 ID + 30 验收点 + 22 开放问题 / [评审报告 §A-§P 10 维度全 PASS](../../reviews/l2-4-knowledge-memory-spec-python-review.md) · 697 行 / 59.7KB / 0 阻塞项 · 3 关注项 · 4 建议项）
> **归档路径**（**待执行 · 下次会话**）：v0.1.0 Go baseline Design + Spec 将在 L2-4 Spec v0.2.0 评审通过后归档至 `docs/archive/pre-python-2026-07-24/L2-knowledge-memory-{design,spec}-v0.1.0-go-baseline.md`（与 L2-2 归档模式一致 · 与 L2-1 / L2-3 同模式事故补救）
> **依据**：[`CONSTITUTION.md`](../../../CONSTITUTION.md) **v0.5.0** §2.5 显式优于隐式 + §2.9 记忆可追溯 + §3.6 MCP 边界 + §3.7 反依赖 + §3.8 Python-first + §6 安全 + §7 可观测性 + §9.7 静态质量；[ADR-0005](../../adr/0005-python-first-technology-stack.md) §3.4 Knowledge/Memory + §6.2 单进程 + §6.3 GIL 与 CPU 工作 + §7 Operator 可靠性门禁 + §10 可观测性 + §13 工程布局；[L1 Architecture v0.2.0](../L1-architecture.md) §3.5.2 / §3.5.3 运行时层 + §5.2.2-5.2.4 CRD + §6 模块清单 + §11.5 Python 性能预算；[L1 Spec v0.2.0](../../spec/L1-system-spec.md) §5 CRD + §15 部署 + §16 Python runtime；[ADR-0002 知识管理设计](../../adr/0002-knowledge-management-design.md) + [ADR-0003 Memory 设计](../../adr/0003-memory-design.md) + [ADR-0004 v0.1 时间线](../../adr/0004-v01-scope-extension-knowledge-and-memory.md)
> **MVP 例外**：§14.5 适用（单人维护者 + 模块数 = 4 不合并）
> **本模块目的**：实现 v0.1 知识管理第 5 大基础能力的 **Python 实现栈承载**。本设计**完全继承** v0.1.0 Go baseline 的 wire contract 与业务语义，**仅替换实现栈**：Go struct → Pydantic v2 BaseModel；Go interface → typing.Protocol + @runtime_checkable；Go controller-runtime reconcile → Kopf `@kopf.timer` + async service；Go BM25 → Python 内存 map + anyio.to_thread.run_sync CPU offload；Go `kubebuilder:validation:` → Pydantic `Field(...)` + JSON Schema 2020-12 → deterministic OpenAPI v3 CRD 生成；Memory decay/reinforce/GC/promotion 算法**数学等价**；Clock 用 `Protocol` 注入 + `FakeClock` 时间穿越单测

---

## 0. 阅读指南

本文档定义 `superteam-a2a` **L2-4 Knowledge / Memory 模块**（运行时层 · C-4）的 **Python 实现设计**：Pydantic v2 CRD 类型、typing.Protocol 算法抽象、Kopf MemoryReconciler 周期 reconcile、内存 BM25 倒排索引、5 维可见性矩阵、admission 双向互斥、4 A2A method handler、Knowledge Service Agent Card、Helm values 配置面、可观测性埋点。**不**涉及具体函数签名、JSON Schema 字段约束（这些在 L3-5/L3-6 Spec 定义）；**不**涉及业务语义（wire contract 完全继承 v0.1.0）。

**读者**：L3-5 / L3-6 Spec 作者、Operator Core 维护者、CRD / admission webhook 贡献者、知识管理 Agent 作者、架构评审者。

**关键变化**（与 v0.1.0 Go baseline 对照）：

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
| **BM25 倒排索引** | Go `map[string][]Item.ID` | **Python `dict[str, list[str]]` + `anyio.to_thread.run_sync` CPU offload** |
| **search 路径** | 同步 in-process | **`async def query()` 入口 + `await anyio.to_thread.run_sync(_search_blocking, query)` offload** |
| **A2A Server 嵌入** | Go `a2a.NewServer(handler)` | **ASGI（Uvicorn 单 worker）+ 官方 `a2a-python` + `supteam_a2a.a2a.upstream` 边界** |
| **错误码** | Go 常量 + `errors.New` | **StrEnum + `a2a-python` JSON-RPC error struct（KNOWLEDGE_* -32008~-32014 / MEMORY_* -32101~-32106）** |
| **可观测性** | `prometheus/client_golang` + `go.opentelemetry.io` | **`prometheus-client` 单进程 + `opentelemetry-sdk` + `structlog`** |
| **admission webhook** | Go `admissionv1.Handler` | **Kopf `kopf.validation` decorator + cert-manager TLS + 50ms 超时 fail-closed** |
| **镜像基线** | `golang:1.22-alpine` + 静态 Go 二进制 | **`python:3.12-slim` 多阶段 + uv build** |
| **测试** | `testing` + `gomock` + envtest | **`pytest` + `pytest-asyncio` + `respx` + `hypothesis` + `freezegun` 时间穿越** |

**与 v0.1.0 Go baseline 关系**：
- v0.1.0 Go baseline 仍作为 **迁移业务语义输入**（已被顶部 supersede 指针标记为「迁移输入」）
- 本 v0.2 设计 **完全替代** Go baseline 的 Python 实现决策（Pydantic + Protocol + ASGI + uv workspace + Kopf）
- 业务语义（3 CRD 字段约束 / 4 级 scope 继承 / 5 维矩阵 / admission 双向互斥 / 4 A2A method / decay/reinforce/GC/promotion 算法 / 错误码范围 / BM25 评分 / Helm values / 测试矩阵 / 部署形态）与 v0.1.0 **完全一致**

---

## 1. 模块使命与边界

### 1.1 使命

L2-4 Knowledge / Memory 是 `superteam-a2a` **运行时层（Runtime Layer）** 的实现子层，承担 **v0.1 第 5 大基础能力 = 知识管理 + 持久化记忆**。它由 **3 个 CRD**（KnowledgeScope / KnowledgeItem / Memory）+ **1 个特殊 Agent**（Knowledge Service · CRD-driven 无 framework adapter）+ **2 类 A2A method**（共 4 个 method：queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）+ **1 个 Controller**（MemoryReconciler 后台调节）+ **2 个 admission webhook**（KI 互斥 + Memory 互斥）组成。

**Knowledge 是"人写的"显性知识**（runbook / API spec / 架构图 / FAQ / troubleshooting），通过 `kubectl apply` + 4 级 scope 继承 + 内存 BM25 检索访问；**Memory 是"Agent 写的"经验沉淀**（confidence + decay + reinforce + GC + promotion 阶段机），通过 A2A method 写入，MemoryReconciler 60s 周期后台调节。二者通过 **admission webhook 双向互斥**严格区分（KnowledgeItem.OwnerRef.Kind ∈ {User, Group} vs Memory.AgentRef.Kind == ServiceAccount）。

**单部署形态**：Knowledge Service + Memory backend **共享 Deployment / 共享进程 / 共享内存倒排索引**（避免 RPC 跨界 + 简化单人维护）；MemoryReconciler 与 L2-2 Operator Core 同进程共享 Leader Election（Lease 锁）。

### 1.2 系统边界

**模块内**（v0.2 Python-first · 本设计详述）：

- **3 个 Pydantic v2 CRD types**：KnowledgeScope（6 spec + 6 status）/ KnowledgeItem（9 spec + 引用类型）/ Memory（12 spec + 7 status）
- **Knowledge Service Agent**：`AgentCard` Pydantic model + 4 个 A2A method handler（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）
- **5 维可见性矩阵**：`MemoryVisibility` StrEnum + `is_memory_visible_to()` Protocol + 12 种 scope × visibility 组合穷举
- **4 级 scope 继承算法**：`resolve_effective_scopes()` async 函数 + 循环引用检测 + parent 跨级拒绝
- **MemoryReconciler**：Kopf `@kopf.timer(interval=60.0)` + `MemoryReconciler` async service + Leader Election via Lease
- **decay / reinforce / GC / promotion 数学**：`apply_decay()` / `apply_reinforce()` / `gc_expired()` / `is_eligible_for_promotion()` 全部纯函数（无 I/O）+ `Clock` Protocol 注入 + `FakeClock` 时间穿越单测
- **内存 BM25 倒排索引**：`InvertedIndex` Protocol + `RealInvertedIndex` 实现 + `anyio.to_thread.run_sync` CPU offload
- **2 个 admission webhook**：KnowledgeItem admission（`kopf.validation` decorator）+ Memory admission（独立 decorator）；双向互斥严格分离
- **可观测性埋点**：`superteam_knowledge_*`（11 个）+ `superteam_memory_*`（6 个）Prometheus 指标 + OTel Span + structlog JSON 日志
- **Helm values 完整配置面**：`knowledgeService` + `memoryReconciler` + `search` + `admission` + `ratelimit` 5 段式
- **测试骨架**：UT 32 + IT 15 + E2E 6 + CF 4 = **57 ID**（时间穿越 + admission 互斥 + 12 种矩阵组合 + 10K items P95 ≤ 200ms 性能门禁）

**模块外**（其他 L2 模块负责）：

- ❌ **A2A 协议本身**（→ L2-1 A2A Protocol · Knowledge Service 只消费其 SDK 嵌入 Server）
- ❌ **Operator 编排逻辑**（→ L2-2 Operator Core · MemoryReconciler 是 L2-2 的子控制器 / 共享 Lease）
- ❌ **Framework Adapter 集成**（→ L2-3 · Knowledge Service 是 CRD-driven 无 framework adapter；Memory 不暴露为 Agent）
- ❌ **Knowledge Graph / 知识图谱**（→ v0.5+，复杂度超单人 2h/天 维护能力）
- ❌ **Vector DB 集成**（→ v0.1 用 etcd + 内存倒排；v0.5+ 可选 Chroma / Qdrant）
- ❌ **自动化 scope-up**（→ v0.1 手动 `kubectl patch`；v0.5+ `KnowledgePromotionRequest` CRD）
- ❌ **Memory 分支 / 快照**（→ v0.1 覆盖更新）
- ❌ **跨 cluster 联邦**（→ v0.1 单 cluster）
- ❌ **Memory 加密静态存储**（→ v0.1 依赖 etcd encryption-at-rest）
- ❌ **Knowledge 评论 / 协作**（→ K8s audit log + GitOps 替代）
- ❌ **MCP 协议实现**（→ 宪法 §3.6 反依赖：Knowledge / Memory 不实现 MCP）

### 1.3 价值主张

| 维度 | 承诺 |
|------|------|
| **Agent 作者** | 5 行 YAML（`framework` / `image` / `card` / `resources` / `healthCheck`）+ A2A method 即可 queryKnowledge / recordMemory |
| **文档贡献者** | `kubectl apply` Markdown KI；scope 自动继承；4 类 visibility 受 admission 强制 |
| **Operator 维护者** | 标准 Kopf timer + Lease + admission webhook；Python 单进程可调试 |
| **架构评审者** | 业务语义（3 CRD / 5 维矩阵 / 4 method）= v0.1 Go baseline；实现栈 = Python 栈迁移 |
| **未来演进** | v0.5+ Vector DB / scope-up 自动 / Memory 全文搜索 = Helm values + Adapter Protocol 替换实现 |

---

## 2. Knowledge / Memory Python 实现决策（spike 风格 · ADR-0005 §8 前置门禁）

> **本节作为 L2-4 Python 设计的决策输入**，完成 ADR-0005 §8 要求的"只读文档验证或非产品 spike"。结论用于 §3-§14 的设计选择。本节在 L3-5 / L3-6 重写时**必须**重新实测所有路径（pin 精确版本、确认 import 路径、跑通示例 + 最小 a2a-python SDK 调用 + Kopf timer 触发），并在 L3 评审前报告任何偏差。

### 2.1 决策范围与依据

依据 ADR-0005 §3.4（Knowledge / Memory）+ §6.2（单进程）+ §6.3（GIL 与 CPU 工作）+ §7（Operator 可靠性门禁）+ §13（工程布局），L2-4 Python 批准前必须确认 **5 项关键决策**：

| # | 决策点 | 默认 | 备选 | 锁定依据 |
|---|--------|------|------|----------|
| D-1 | CRD types 实现形式 | **Pydantic v2 BaseModel + `populate_by_name` + alias** | dataclass + marshmallow | ADR-0005 §5.1 + §3.4；Pydantic 与官方 A2A SDK 类型互转最直接 |
| D-2 | 内存 BM25 倒排索引形态 | **`dict[str, list[str]]` + `anyio.to_thread.run_sync` 受控 offload** | numpy 矩阵 + sklearn | ADR-0005 §6.3 + §3.4；10K items 规模无需重型 NLP 库；offload 满足 event-loop lag 门禁 |
| D-3 | MemoryReconciler 周期触发 | **Kopf `@kopf.timer(interval=60.0)` + 独立 async service** | asyncio 自循环 | ADR-0005 §7 可靠性门禁 7-8；Kopf 提供 operator 重启恢复 + Leader Election + backoff |
| D-4 | Clock 注入形式 | **`typing.Protocol[now, advance]` + `RealClock` + `FakeClock`** | `datetime.utcnow()` 直接调用 | ADR-0005 §3.4 + §11 测试；时间穿越单测必须可注入 |
| D-5 | admission webhook 部署 | **Kopf `kopf.validation` decorator（operator 进程内嵌）** | 独立 webhook Deployment | ADR-0005 §3.4 + §6.2；operator 内嵌简化运维；cert-manager 挂 TLS |

**默认表格说明**：上述 5 项为占位默认值；L3-5 / L3-6 实测后补完每项的精确版本号、风险评估、metric 名影响。

### 2.2 5 项决策详细说明

#### D-1：Pydantic v2 BaseModel 表达 CRD

**Schema 概要**（完整 Pydantic model 在 L3-5 Spec）：

```python
# packages/knowledge/src/supteam_a2a/knowledge/apis/v1alpha1/knowledgescope.py
# 完整代码 + JSON Schema 推导在 L3-5 Spec
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

    include_types: list[str] | None = Field(default=None, max_length=11)
    exclude_types: list[str] | None = Field(default=None, max_length=11)


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
    # 7 = 6 spec + labels（可选）— labels 不计入 spec 字段数；ADR-0004 防过度设计 ≤15 上限达标


class KnowledgeScopeStatus(BaseModel):
    """KnowledgeScope CRD status（6 字段）。"""

    model_config = ConfigDict(extra="forbid")

    phase: ScopePhase | None = None  # Pending / Active / Error / Deleting
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

**JSON Schema 生成链路**（ADR-0005 §5.2）：

```
Pydantic model.model_json_schema()
   ↓ (deterministic sort + x-kubernetes-* injection)
deterministic OpenAPI v3 CRD YAML
   ↓ (CI validate: stable diff + round-trip test + kubectl apply dry-run)
checked-in: charts/superteam-a2a/crds/knowledgescope.yaml
```

**关键约束**：
- 所有时间字段必须 `AwareDatetime`（UTC）；业务层 `datetime.now(UTC)`
- enum 使用 `StrEnum`（与 wire 字符串值兼容；避免 IntEnum 序列化问题）
- 不可变 value object 加 `frozen=True`
- `populate_by_name=True` + `alias` 实现 wire camelCase ↔ Pythonic snake_case 单向映射（wire 是 source of truth）
- `extra="forbid"` 在 strict 模式下禁止未声明字段（与 K8s API server strict 校验一致）

#### D-2：内存 BM25 + 受控线程 offload

**Schema 概要**：

```python
# packages/knowledge/src/supteam_a2a/knowledge/search/inverted_index.py
# 完整代码 + BM25 评分公式在 L3-5 Spec
import math
from collections import Counter, defaultdict
from typing import Protocol, runtime_checkable
from anyio import to_thread
from superteam_a2a.knowledge.apis.v1alpha1 import KnowledgeItem


# BM25 参数（与 Go baseline 完全一致）
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
        # item name → token Counter（用于 BM25 长度归一化）
        self._doc_lens: dict[str, int] = {}
        # item name → KnowledgeItem 引用
        self._items: dict[str, KnowledgeItem] = {}
        self._avg_doc_len: float = 0.0
        self._lock = asyncio.Lock()

    async def search(
        self,
        query: str,
        scope_chain: list[str],
        type_filter: list[str] | None = None,
        tag_filter: list[str] | None = None,
        max_results: int = 10,
    ) -> list[tuple[KnowledgeItem, float]]:
        # 异步入口 + 受控线程 offload（满足 ADR-0005 §6.3 + L1 §11.5 event-loop lag 门禁）
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
        """BM25 评分公式（与 Go baseline math 完全等价）。"""
        doc_tokens = self._doc_lens[doc_name]
        score = 0.0
        for term in query_tokens:
            tf = self._postings.get(term, set()).__contains__(doc_name)
            if not tf:
                continue
            # 实际 tf 需要 Counter；这里简化用 postings 长度估算
            # 完整实现使用 doc_token_counter[term]
            df = len(self._postings.get(term, set()))
            idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
            tf_norm = (1) / (1 + BM25_B * (doc_tokens / self._avg_doc_len - 1))
            score += idf * tf_norm
        return score

    # ... rebuild / upsert / remove / size 实现
```

**与 Go baseline 对照**：
- v0.1.0 Go：`map[string][]KnowledgeItem.ID` + Go BM25 函数 + sync.RWMutex
- v0.2 Python：`defaultdict(set)` + Python BM25 函数 + asyncio.Lock + `to_thread.run_sync` CPU offload
- 行为兼容性：**完全一致**（BM25 K1=1.5 / B=0.75 / 评分公式不变）

**线程 offload 约束**（ADR-0005 §6.3）：
- 默认 `to_thread` limiter = 40 线程（anyio 默认）
- 单次 search `to_thread.run_sync` 超时 5s（Helm values 可配）
- `event_loop_lag_seconds` 指标（ADR-0005 §10）：> 100ms 持续 10s → 报警
- 10K items rebuild 时间 ≤ 30s（Helm values `search.rebuildOnStart: true`）

#### D-3：Kopf `@kopf.timer` + 独立 async service

**架构**：

```
┌─────────────────────────────────────────────────────────┐
│ Operator Process (uvicorn 单 worker · 单 event loop)   │
│                                                         │
│  ┌─────────────────────┐   ┌─────────────────────────┐  │
│  │ Kopf daemon         │   │ MemoryReconciler        │  │
│  │ (K8s API watch)     │   │ async service           │  │
│  │                     │   │                         │  │
│  │ AgentReconciler     │   │ @kopf.timer(60s)        │  │
│  │ AgentSetReconciler  │   │   ↓                     │  │
│  │ WorkflowReconciler  │   │ _reconcile_all_memories │  │
│  │ KnowledgeItem Ctl   │   │   - decay batch         │  │
│  │ admission webhook   │   │   - GC expired          │  │
│  └─────────────────────┘   │   - promote compute     │  │
│                            └─────────────────────────┘  │
│                                                         │
│  Leader Election via coordination.k8s.io/v1 Lease      │
└─────────────────────────────────────────────────────────┘
```

**Schema 概要**：

```python
# packages/operator/src/supteam_a2a/operator/handlers/memory.py
# 完整代码在 L2-2 Operator Core Spec v0.2.0 Python §5.6 + L3-5 Spec
import asyncio
from datetime import timedelta
from typing import Protocol, runtime_checkable
import kopf
from superteam_a2a.memory.lifecycle import (
    apply_decay,
    apply_reinforce,
    gc_expired,
    is_eligible_for_promotion,
)
from superteam_a2a.shared.clock import Clock, RealClock
from superteam_a2a.shared.leader import LeaseLeader
from superteam_a2a.shared.observability import (
    SUPTEAM_MEMORY_DECAY_TOTAL,
    SUPTEAM_MEMORY_RECONCILE_DURATION_SECONDS,
)


@runtime_checkable
class MemoryReconcilerService(Protocol):
    """MemoryReconciler 业务抽象（L2-2 Operator Core §5.6）。"""

    async def reconcile_all(self, now: "datetime") -> ReconcileSummary:
        """单次全集群 Memory reconcile；返回计数摘要。"""
        ...


class RealMemoryReconcilerService:
    """生产实现：批量 reconcile + Leader Election + 周期触发。"""

    BATCH_SIZE = 1000  # 单 reconcile 批大小；Helm values 可配

    def __init__(
        self,
        clock: Clock,  # Protocol 注入（默认 RealClock；测试 FakeClock）
        leader: LeaseLeader,
        memory_store: "MemoryStoreProtocol",
    ) -> None:
        self._clock = clock
        self._leader = leader
        self._store = memory_store

    async def reconcile_all(self, now: "datetime") -> ReconcileSummary:
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
        await self._store.patch_status(
            mem.metadata.name,
            {
                "phase": _phase_for(new_effective).value,
                "effectiveConfidence": new_effective,
                "lastDecayedAt": now,
                "eligibleForPromotion": eligible,
            },
        )
        if old_phase != _phase_for(new_effective):
            SUPTEAM_MEMORY_DECAY_TOTAL.labels(
                phase_from=old_phase.value,
                phase_to=_phase_for(new_effective).value,
            ).inc()
            summary.phase_transitions += 1


# Kopf timer decorator（与 L2-2 Operator Core Spec §5.6 对齐）
@kopf.timer("memories", interval=60.0, idle=30.0)
async def memory_reconcile_timer(
    now: "datetime",
    memory_reconciler: MemoryReconcilerService,
    **_,
) -> None:
    """60s 周期触发 MemoryReconciler（与 Go baseline 一致）。"""
    summary = await memory_reconciler.reconcile_all(now)
    kopf.info(
        event=memory_reconcile_timer.__name__,
        decayed=summary.phase_transitions,
        expired=summary.expired,
        promoted=summary.eligible_for_promotion,
    )
```

**与 Go baseline 对照**：
- v0.1.0 Go：controller-runtime `Reconcile(ctx, req) (Result, error)` + `RequeueAfter: 60s`
- v0.2 Python：Kopf `@kopf.timer` + 独立 async service + 显式 `LeaseLeader.is_leader()` 单活
- 行为兼容性：**完全一致**（周期 60s + 批量 1000 + 单活 Leader + decay / GC / promotion 算法数学等价）

**Operator 可靠性门禁**（ADR-0005 §7，12 项）：
1. ✅ create/update/resume/delete handler 幂等（Kopf 默认）
2. ✅ Operator 重启后 progress 恢复（Kopf resourceVersion watch）
3. ✅ finalizer 失败重试和删除不泄漏（Kopf finalizer semantics）
4. ✅ API conflict / 409 重试（Kopf retry/backoff）
5. ✅ watch reconnect 与 resourceVersion 过期（Kopf auto-reconnect）
6. ✅ event storm/backpressure（Kopf workqueue 限流）
7. ✅ leader failover（Lease）
8. ✅ timer/daemon 仅 leader 执行（`await leader.is_leader()`）
9. ✅ status patch 不覆盖 spec（`_store.patch_status` 显式 status 子路径）
10. ✅ webhook TLS reload 与 fail-closed（cert-manager + 50ms 超时）
11. ✅ 多 namespace watch 权限（Kopf multi-namespace mode）
12. ✅ graceful shutdown 后任务可恢复（asyncio TaskGroup + signal handler）

#### D-4：Clock Protocol 注入 + FakeClock

**Schema**：

```python
# packages/shared/src/supteam_a2a/shared/clock.py
# 完整代码 + 时间穿越单测在 L3-5 / L3-6 Spec
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """时间源抽象（ADR-0005 §3.4 + L2-2 §5.6）。"""
    
    def now(self) -> datetime:
        """返回 timezone-aware UTC 当前时间。"""
        ...
    
    def advance(self, delta: timedelta) -> datetime:
        """Fake-only：推进时间到 now + delta（生产 RealClock raise NotImplementedError）。"""
        ...


class RealClock:
    """生产实现：委托 datetime.now(UTC)。"""
    
    def now(self) -> datetime:
        return datetime.now(UTC)
    
    def advance(self, delta: timedelta) -> datetime:
        raise NotImplementedError("RealClock.advance 仅用于测试")


class FakeClock:
    """测试实现：可注入 + 可推进（freezegun 风格）。"""
    
    def __init__(self, start: datetime | None = None) -> None:
        self._now: datetime = start or datetime(2026, 7, 24, 0, 0, 0, tzinfo=UTC)
    
    def now(self) -> datetime:
        return self._now
    
    def advance(self, delta: timedelta) -> datetime:
        self._now += delta
        return self._now
```

**decay / reinforce 数学等价**（与 Go baseline 公式一致）：

```python
# packages/memory/src/supteam_a2a/memory/lifecycle/decay.py
import math


def apply_decay(memory: Memory, now: datetime) -> float:
    """decay 公式：effectiveConfidence = confidence * exp(-elapsed_days / decayDays)。

    与 Go baseline ADR-0003 §4.1 数学完全等价；时间由 Clock 注入。
    """
    if memory.spec.decay_days == 0:
        return memory.spec.confidence  # 不衰减

    last_reinforced = memory.status.last_reinforced_at or memory.metadata.creation_timestamp
    elapsed_days = (now - last_reinforced).total_seconds() / 86400.0
    return memory.spec.confidence * math.exp(-elapsed_days / memory.spec.decay_days)


def apply_reinforce(memory: Memory, now: datetime, hit_count: int = 1) -> Memory:
    """reinforce 公式：reinforcedCount += hit_count；confidence 不变；lastReinforcedAt = now。

    与 Go baseline ADR-0003 §4.2 数学完全等价。
    """
    return memory.model_copy(
        update={
            "spec": memory.spec.model_copy(
                update={
                    "reinforced_count": memory.spec.reinforced_count + hit_count,
                }
            ),
            "status": (memory.status or MemoryStatus()).model_copy(
                update={
                    "last_reinforced_at": now,
                }
            ),
        }
    )


def is_eligible_for_promotion(memory: Memory, effective: float) -> bool:
    """promotion 资格（v0.1 仅算不触发；详见 ADR-0003 §4.3）。

    规则：reinforced_count ≥ 5 AND effective ≥ 0.7 AND age ≥ 7d。
    """
    age_days = (datetime.now(UTC) - memory.metadata.creation_timestamp).days
    return memory.spec.reinforced_count >= 5 and effective >= 0.7 and age_days >= 7
```

**与 Go baseline 对照**：
- v0.1.0 Go：`interface { Now() time.Time }` + `k8s.io/utils/clock.Clock` + `clock.NewFakeClock(...)`
- v0.2 Python：`Protocol[now, advance]` + `RealClock` + `FakeClock`
- 行为兼容性：**完全一致**（数学公式 + 时间穿越单测模式）

#### D-5：admission webhook · operator 进程内嵌

**架构**：

```
Operator Deployment (Kopf daemon)
  │
  ├─ Kopf validation webhook server (TLS by cert-manager)
  │   ├─ /validate/knowledgescope
  │   ├─ /validate/knowledgeitem    ← KI 互斥规则（ownerRef.Kind ∈ {User, Group}）
  │   ├─ /validate/memory           ← Memory 互斥规则（agentRef.Kind == ServiceAccount）
  │   └─ /validate/memorysourceknowledge ← Memory.sourceKnowledgeRef → KI 追溯
  │
  └─ failure mode: 50ms 超时 fail-closed（默认拒绝写入；附录 B B.6）
```

**Schema 概要**：

```python
# packages/operator/src/supteam_a2a/operator/handlers/memory_admission.py
# 完整代码在 L2-2 Spec v0.2.0 Python + L3-5 Spec
import kopf
from superteam_a2a.knowledge.apis.v1alpha1 import KnowledgeItem, KnowledgeScope
from superteam_a2a.memory.apis.v1alpha1 import Memory
from superteam_a2a.shared.errors import AdmissionRejected


@kopf.validation("knowledgeitems", "create", "update")
async def validate_knowledge_item(
    spec: KnowledgeItemSpec,
    **_,
) -> None:
    """KnowledgeItem admission 互斥规则（左侧）。"""
    # 1. ownerRef.Kind 必须 User / Group（拒绝 ServiceAccount）
    if spec.owner_ref.kind == SubjectKind.SERVICE_ACCOUNT:
        raise AdmissionRejected(
            code="KNOWLEDGE_OWNER_KIND_FORBIDDEN",
            message="KnowledgeItem.ownerRef.Kind must be User or Group; "
            "ServiceAccount owned Memories are tracked separately.",
        )

    # 2. visibility == public-readable 必须 scope.level == industry
    if (
        spec.visibility == KnowledgeVisibility.PUBLIC_READABLE
        and spec.scope_ref.level != ScopeLevel.INDUSTRY
    ):
        raise AdmissionRejected(
            code="KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY",
            message="KnowledgeItem.visibility == public-readable requires scope.level == industry.",
        )

    # 3. visibility == agent-private v0.1 拒绝
    if spec.visibility == KnowledgeVisibility.AGENT_PRIVATE:
        raise AdmissionRejected(
            code="KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS",
            message="KnowledgeItem.visibility == agent-private is reserved for v0.5+",
        )

    # 4. scopeRef 存在 + level 合法 + parent 关系合法
    scope = await fetch_scope(spec.scope_ref.name)
    if scope is None:
        raise AdmissionRejected(
            code="KNOWLEDGE_SCOPE_NOT_FOUND",
            message=f"KnowledgeScope {spec.scope_ref.name} not found.",
        )
    if scope.spec.level != spec.scope_ref.level:
        raise AdmissionRejected(
            code="KNOWLEDGE_SCOPE_LEVEL_MISMATCH",
            message=f"scope.level {scope.spec.level} != reference level {spec.scope_ref.level}",
        )


@kopf.validation("memories", "create", "update")
async def validate_memory(
    spec: MemorySpec,
    **_,
) -> None:
    """Memory admission 互斥规则（右侧）。"""
    # 1. agentRef.Kind 必须 ServiceAccount（拒绝 User / Group）
    if spec.agent_ref.kind != SubjectKind.SERVICE_ACCOUNT:
        raise AdmissionRejected(
            code="MEMORY_AGENT_KIND_FORBIDDEN",
            message="Memory.agentRef.Kind must be ServiceAccount; "
            "User/Group owned knowledge uses KnowledgeItem.",
        )

    # 2. scopeRef 必须存在
    scope = await fetch_scope(spec.scope_ref.name)
    if scope is None:
        raise AdmissionRejected(
            code="MEMORY_SCOPE_NOT_FOUND",
            message=f"KnowledgeScope {spec.scope_ref.name} not found.",
        )

    # 3. sourceKnowledgeRef 若存在 → KI 必须存在 + scope 匹配
    if spec.source_knowledge_ref is not None:
        ki = await fetch_knowledge_item(
            spec.source_knowledge_ref.name,
            spec.source_knowledge_ref.scope,
        )
        if ki is None:
            raise AdmissionRejected(
                code="MEMORY_SOURCE_KNOWLEDGE_NOT_FOUND",
                message=f"sourceKnowledgeRef {spec.source_knowledge_ref.name} not found.",
            )
        if ki.spec.scope_ref.name != spec.scope_ref.name:
            raise AdmissionRejected(
                code="MEMORY_SOURCE_KNOWLEDGE_SCOPE_MISMATCH",
                message="Memory.scopeRef must match sourceKnowledgeRef.scope",
            )

    # 4. visibility == agent-private 必须 agentRef.Name != ""
    if spec.visibility == MemoryVisibility.AGENT_PRIVATE and not spec.agent_ref.name:
        raise AdmissionRejected(
            code="MEMORY_AGENT_PRIVATE_REQUIRES_AGENT_NAME",
            message="Memory.visibility == agent-private requires agentRef.Name.",
        )

    # 5. decayDays ≤ 3650
    if spec.decay_days > 3650:
        raise AdmissionRejected(
            code="MEMORY_DECAY_DAYS_TOO_LONG",
            message="Memory.decayDays must be ≤ 3650.",
        )
```

**与 Go baseline 对照**：
- v0.1.0 Go：`admissionv1.Handler` + `http.Handler` + 独立 webhook server Deployment
- v0.2 Python：Kopf `kopf.validation` decorator + cert-manager TLS + operator 内嵌
- 行为兼容性：**完全一致**（双向互斥规则 + 4 级 scope 校验 + 循环引用检测 + 50ms fail-closed）

**已知未决**（移交 L3-5）：

| # | 项 | 影响 | 处理 |
|---|----|------|------|
| U-1 | Kopf `kopf.validation` decorator 在 `kopf.timer` + admission 共存时的启动顺序 | L3-5 启动序列 | L3-5 实测；Kopf 文档默认 webhook 先于 timer 启动 |
| U-2 | cert-manager 挂 TLS 证书热更新是否需要 reload SSL context | L3-5 可观测性 + admission 不停机 | L3-5 验证 cert-manager `spec.renewBefore` + Kopf webhook reload |
| U-3 | admission webhook 50ms 超时 fail-closed 模式下 etcd 不可用时的 UX | L3-5 admission 错误码 | 默认 fail-closed；附录 B B.6 默认决策已锁定 |
| U-4 | MemoryReconciler 60s 周期 + 10K memories 批量 reconcile 时间预算 | L3-6 performance test | L3-6 实测 ≤ 30s；超则调 batch size 或考虑 scope hash 分片 |
| U-5 | Pydantic v2 BaseModel 在 K8s admission JSON 反序列化时的性能 | L3-5 admission 性能 | Pydantic v2 benchmark 显示 5-10x Go json.Unmarshal；监控 admission_duration_seconds |

### 2.3 与 L2-1 / L2-2 / L2-3 的 Python 化对齐

| 对齐点 | L2-1 A2A Protocol | L2-2 Operator Core | L2-3 Adapter | L2-4 Knowledge/Memory |
|--------|-------------------|--------------------|--------------|----------------------|
| 类型基线 | Pydantic v2 | Pydantic v2 | Pydantic v2 | **Pydantic v2（D-1）** |
| 算法抽象 | typing.Protocol | typing.Protocol | typing.Protocol | **typing.Protocol（D-4 Clock）** |
| Controller | a2a.Server 嵌入 | Kopf reconcile | n/a（被编排） | **Kopf `@kopf.timer`（D-3）** |
| CPU offload | n/a | anyio.to_thread | n/a | **anyio.to_thread.run_sync（D-2）** |
| admission | n/a | Kopf validation | n/a | **Kopf validation（D-5）** |
| 镜像基线 | python:3.12-slim | python:3.12-slim | python:3.12-slim | **python:3.12-slim** |
| Helm 镜像块 | a2a.python | operator.python | adapter.python | **knowledgeService.python + memoryReconciler.python** |

---

## 3. Python 包结构（ADR-0005 §13 工程布局）

### 3.1 总览（uv workspace · 5 个独立 package + 共享 sub-package）

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
- `shared/` 与 `shared-visibility/` 是 PEP 420 namespace package（与 ADR-0005 §2.2 一致）
- `operator` package 引用 `knowledge` / `memory` 作为 library（Operator Core 同时跑所有 Controller；ADR-0005 §3.1）
- `knowledge-service` / `memory-backend` 引用 `knowledge` / `memory` + `supteam_a2a.a2a.upstream`（L2-1 边界）

### 3.2 `packages/knowledge` 包布局（`packages/knowledge/src/supteam_a2a/knowledge/`）

```
supteam_a2a.knowledge/
├── __init__.py                # 公共 API surface（re-export CRD types + 关键 helper）
├── apis/                      # Pydantic v2 CRD types
│   └── v1alpha1/
│       ├── __init__.py
│       ├── knowledgescope.py  # KnowledgeScopeSpec + Status + KnowledgeScope + SubjectReference + ScopeReference + InheritRules + ScopeLevel + ScopePhase
│       ├── knowledgeitem.py   # KnowledgeItemSpec + Status + KnowledgeItem + ItemReference + KnowledgeType + KnowledgeVisibility
│       └── common.py          # 共享引用类型（ObjectMeta / Condition / LabelSelector）
├── scope/                     # 4 级继承算法
│   ├── __init__.py
│   ├── inheritance.py         # resolve_effective_scopes() async def + 循环引用检测 + parent 跨级拒绝
│   ├── validation.py          # 4 级 + 循环引用校验（admission 调用）
│   ├── inherit_rules.py       # includeTypes / excludeTypes 过滤
│   └── tests/                 # 12 种 scope 组合表驱动单测
├── admission/                 # admission webhook（双向互斥左侧 · D-5）
│   ├── __init__.py
│   ├── ki_webhook.py          # KnowledgeItem 互斥规则（kopf.validation decorator）
│   ├── scope_webhook.py       # KnowledgeScope 4 级 + 循环引用校验
│   └── tests/
├── search/                    # Operator 内存倒排索引
│   ├── __init__.py
│   ├── inverted_index.py      # RealInvertedIndex + InvertedIndex Protocol + BM25 评分（D-2）
│   ├── bm25.py                # BM25 评分公式（独立可测；K1=1.5 / B=0.75）
│   ├── rebuild.py             # 启动期全量重建 + watch 增量
│   └── tests/                 # 单元 + 性能测试（10K items P95 ≤ 200ms）
└── _internal/                 # ⚠️ private — 业务层禁止 import
    └── __init__.py
```

**关键约束**：
- `knowledge` 不依赖 `memory` package（资源模型层独立）
- `knowledge` 引用 `shared`（clock / leader / observability / errors）+ `shared-visibility`（5 维矩阵复用）
- Pydantic CRD types 必须支持 JSON Schema 推导（`model_json_schema()` 稳定排序）

### 3.3 `packages/memory` 包布局（`packages/memory/src/supteam_a2a/memory/`）

```
supteam_a2a.memory/
├── __init__.py                # 公共 API surface（re-export CRD types + lifecycle 函数）
├── apis/                      # Pydantic v2 CRD types
│   └── v1alpha1/
│       ├── __init__.py
│       ├── memory.py          # MemorySpec + Status + Memory + AgentReference + MemoryPhase + MemoryVisibility
│       └── common.py          # 共享引用类型
├── lifecycle/                 # decay / reinforce / GC / promotion 数学
│   ├── __init__.py
│   ├── decay.py               # apply_decay() 纯函数（D-4 + 数学等价）
│   ├── reinforce.py           # apply_reinforce() 纯函数
│   ├── promotion.py           # is_eligible_for_promotion() 纯函数（v0.1 仅算不触发）
│   ├── gc.py                  # gc_expired() 纯函数
│   ├── visibility.py          # is_memory_visible_to() 5 维矩阵过滤（共享 visibility）
│   └── tests/                 # 时间穿越单测（FakeClock 推进；freezegun 风格）
└── admission/                 # admission webhook（双向互斥右侧 · D-5）
    ├── __init__.py
    ├── m_webhook.py           # Memory 互斥规则（kopf.validation decorator；与 knowledge/admission/ki_webhook.go 协同部署）
    └── tests/
```

**关键约束**：
- `memory.lifecycle.*` 全部是**纯函数**（无 I/O、无 side effect）；Clock 通过参数注入（无 module-level global state）
- `memory.admission` 与 `knowledge.admission` 部署于同一 Operator 进程内（Kopf validation 同 namespace）

### 3.4 `packages/knowledge-service` 包布局

```
supteam_a2a.knowledge_service/
├── __init__.py
├── main.py                    # ASGI 入口 + Uvicorn 单 worker + 装载 4 handler
├── handlers/
│   ├── __init__.py
│   ├── query_knowledge.py     # a2a.queryKnowledge handler（基于 §4 4 method 详细规格）
│   ├── get_knowledge_item.py  # a2a.getKnowledgeItem handler
│   ├── record_memory.py       # a2a.recordMemory handler（代理到 memory_backend）
│   └── query_memory.py        # a2a.queryMemory handler（代理到 memory_backend）
├── card/
│   └── knowledge_service_card.json  # Agent Card JSON（§6 Pydantic model 推导）
├── config/
│   ├── __init__.py
│   └── loader.py              # 4 层配置加载（Secret > CRD > ConfigMap > Env）
└── tests/
    ├── unit/                  # 单元测试（mock framework）
    └── integration/           # 集成测试（真实 a2a-python SDK）
```

**关键约束**：
- `knowledge_service` 不依赖 `framework SDK`（CRD-driven 无 framework adapter；宪法 §3.6）
- `knowledge_service` 引用 `knowledge` + `memory` + `memory_backend` + `supteam_a2a.a2a.upstream`（L2-1 边界）
- ASGI 入口基于 `supteam_a2a.a2a.create_app`（L2-1 A2A Protocol Spec v0.2.0 Python §5）

### 3.5 `packages/memory-backend` 包布局

```
supteam_a2a.memory_backend/
├── __init__.py
├── main.py                    # ASGI 入口（与 knowledge-service 同进程；不单独启动）
├── handlers/
│   ├── __init__.py
│   ├── record_memory.py       # a2a.recordMemory 实际实现（knowledge_service 代理调用）
│   └── query_memory.py        # a2a.queryMemory 实际实现
├── store/
│   ├── __init__.py
│   ├── store.py               # MemoryStore Protocol + RealMemoryStore（CRD 即存储）
│   └── tests/
└── middleware/
    ├── __init__.py
    ├── ratelimit.py           # 60/min per SA（错误码 -32104；Tenacity sliding window）
    └── audit.py               # Memory 写入审计日志（K8s event + structured logger）
```

**关键约束**：
- `memory_backend` 与 `knowledge_service` **同 Deployment / 同进程**（共享内存倒排索引 + 单人维护简化）
- `memory_backend.main` 不单独启动；由 `knowledge_service.main` 在 lifespan startup 中 `import` 并装载 2 个 handler

### 3.6 边界规则（与 L2-1 §3.2 + 宪法 §3.7 + ADR-0005 §3.3 严格一致）

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
       │  superteam_a2a.knowledge_service  │  ← Knowledge Service + Memory backend
       │  superteam_a2a.memory_backend     │
       └────────────────┬─────────────────┘
                        │ 依赖
       ┌────────────────▼─────────────────┐
       │  superteam_a2a.knowledge          │  ← Knowledge 资源模型层
       │  superteam_a2a.memory             │  ← Memory 资源模型层
       └────────────────┬─────────────────┘
                        │ 依赖
       ┌────────────────▼─────────────────┐
       │  superteam_a2a.shared             │  ← 跨模块共享
       │  superteam_a2a.shared.visibility  │  ← 5 维矩阵
       └──────────────────────────────────┘
```

**关键约束**：
1. `knowledge` / `memory` / `knowledge_service` / `memory_backend` 严禁 import `framework SDK`（宪法 §3.6 反依赖）
2. `shared` / `shared-visibility` 是唯一被多个模块引用的公共包（避免循环依赖）
3. `operator` package（不在本模块）通过 K8s API watch CRD 编排 `knowledge_service` Deployment，不直接 import（Kopf CRD-driven）

---

## 4. Knowledge 4 级作用域（Python `Protocol` + Pydantic schema）

### 4.1 4 级作用域枚举 + 继承链

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

### 4.2 继承算法（Python 异步实现）

```python
# packages/knowledge/src/supteam_a2a/knowledge/scope/inheritance.py
# 完整代码 + 12 种组合表驱动单测在 L3-5 Spec
from typing import Protocol, runtime_checkable
from superteam_a2a.knowledge.apis.v1alpha1 import (
    KnowledgeScope,
    KnowledgeScopeSpec,
    ScopeLevel,
    ScopeReference,
)
from superteam_a2a.shared.errors import ScopeNotFound, ScopeCycle


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

    def __init__(self, k8s_client: "kubernetes_asyncio.client.CoreV1Api") -> None:
        self._k8s = k8s_client
        self._cache: dict[str, KnowledgeScope] = {}
        self._cache_lock = asyncio.Lock()

    async def get_scope(self, name: str) -> KnowledgeScope | None:
        if name in self._cache:
            return self._cache[name]
        # 实际实现：custom object API list by name
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
                raise ScopeCycle(
                    f"Cycle detected in scope inheritance at {current_name}",
                )
            visited.add(current_name)

            scope = await self.get_scope(current_name)
            if scope is None:
                raise ScopeNotFound(
                    f"KnowledgeScope {current_name} not found during inheritance resolution",
                )

            chain.insert(0, scope.metadata.name)  # 顶层在前

            # 终止条件：industry（parent_ref is None）
            if scope.spec.parent_ref is None:
                break

            # 检查 parent 跨级（精确递增 1 级）
            parent_scope = await self.get_scope(scope.spec.parent_ref.name)
            if parent_scope is None:
                raise ScopeNotFound(
                    f"Parent scope {scope.spec.parent_ref.name} not found",
                )
            if not _is_strict_child_level(scope.spec.level, parent_scope.spec.level):
                raise ScopeHierarchyViolation(
                    f"Scope {scope.metadata.name} (level={scope.spec.level}) "
                    f"parent {parent_scope.metadata.name} (level={parent_scope.spec.level}) "
                    f"violates strict level increment",
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

    # 内存倒排索引查询（CPU offload）
    candidates = await inverted_index.search(
        query=query,
        scope_chain=effective_scopes,
        type_filter=type_filter,
        tag_filter=tag_filter,
        max_results=max_results * 2,  # 多取一倍用于 visibility 过滤后截断
    )

    # visibility 过滤（公开方法调用，避免循环依赖）
    results: list[tuple[KnowledgeItem, float]] = []
    for item, score in candidates:
        # 应用 inheritRules（include / exclude type）
        if not _is_inherit_allowed(item, effective_scopes):
            continue
        # visibility 过滤（public-readable 仅 industry；agent-private v0.1 禁用）
        if not _is_visibility_allowed(item, scope_name):
            continue
        results.append((item, score))

    # 去重：同 ID 保留最新 version
    return _dedupe_by_id_keep_latest(results)[:max_results]
```

### 4.3 KnowledgeItem Visibility 枚举（4 类 StrEnum）

| Visibility | 含义 | 适用 Level |
|------------|------|------------|
| `scope-only` | 仅当前作用域成员可见 | 任意 |
| `scope-and-children` | 当前作用域 + 子作用域成员可见（**默认**） | 任意 |
| `public-readable` | **必须** industry scope 才允许 | industry only |
| `agent-private` | v0.1 **禁用**（保留给 v0.5+ SA-级隔离） | — |

**admission webhook 强制**（§3.2 + §3.3）：
- `public-readable` 必须 `level == industry`，否则 `KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY` 拒绝
- `agent-private` v0.1 拒绝（未来 v0.5+ 扩展）`KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS`

### 4.4 知识容量与性能约束

- 单集群 ≤ **10,000 KnowledgeItem**（超出拒绝创建；提示升级 Vector DB）
- Operator 内存倒排索引**重建 ≤ 30s**（10K items）
- `queryKnowledge` **P95 ≤ 200ms**（性能门禁；§11.2 测试）

---

## 5. Memory 5 维可见性矩阵（Python 过滤算法）

### 5.1 5 维矩阵过滤算法（4 scope × 3 visibility + agent-private 短路）

| visibility \ scope | industry | organization | team | project |
|---|---|---|---|---|
| `scope-only` | 仅 industry | 仅 org | 仅 team | 仅 project |
| `scope-and-children`（默认） | industry + 所有子 | org + 所有子 team/project | team + 所有子 project | 仅 project |
| `agent-private` | **仅 owner agent**（无视 scope） | **仅 owner agent** | **仅 owner agent** | **仅 owner agent** |

**实现要点**：

```python
# packages/memory/src/supteam_a2a/memory/lifecycle/visibility.py
# 完整代码 + 12 种组合穷举单测在 L3-6 Spec
from typing import Protocol, runtime_checkable
from superteam_a2a.memory.apis.v1alpha1 import Memory, MemoryVisibility


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
        
        # 规则 3：scope-and-children 继承链上
        if visibility == MemoryVisibility.SCOPE_AND_CHILDREN:
            return memory.spec.scope_ref.name in caller_scope_chain
        
        # 默认拒绝（防御性；不应到达）
        return False
```

### 5.2 MemorySpec 关键字段（12 个 · ADR-0003 §2.2）

| 字段 | 类型 | 必填 | 约束 | 用途 |
|------|------|------|------|------|
| `scope_ref` | ScopeReference | ✅ | namespace 内必须存在 | 4 级作用域挂载 |
| `agent_ref` | AgentReference | ✅ | **Kind 强制 ServiceAccount** | 写入 agent 标识 |
| `content` | dict[str, str] | ✅ | 1-20 KV pairs | 结构化记忆内容（vs KI 的 Markdown body） |
| `summary` | str | ✅ | 1-256 chars | 人工浏览 / list 显示 |
| `confidence` | float | ✅ | 0.0-1.0 | 由 decay/reinforce 自动更新 |
| `decay_days` | int | ✅ | 0-3650（0 = 不衰减） | 衰减周期（默认 30） |
| `reinforced_count` | int | ✅ | ≥ 0，monotonically increasing | 强化次数 |
| `visibility` | MemoryVisibility | ✅ | **仅 3 类**（不含 public-readable） | 5 维矩阵实现 |
| `memory_key` | str \| None | ❌ | ≤128 chars；三元组 (memory_key, scope_ref, agent_ref) 唯一 | 用于 reinforce 去重 |
| `source_knowledge_ref` | ItemReference \| None | ❌ | 若存在则 KI 必须存在 + scope 匹配 | 记忆可追溯链（宪法 §2.9） |
| `tags` | list[str] \| None | ❌ | ≤20 tags | list/filter 用 |

**字段数校验**（ADR-0004 防过度设计约束 ≤15 字段）：12 个 spec + 引用类型 = **距上限 3（临界但达标）**

### 5.3 admission 双向互斥规则（详细规格）

| 字段 | KnowledgeItem | Memory |
|------|---------------|--------|
| `owner_ref.Kind` / `agent_ref.Kind` | ∈ {User, Group} | == ServiceAccount |
| `visibility` 枚举 | scope-only / scope-and-children / public-readable / agent-private | scope-only / scope-and-children / agent-private |
| `body` / `content` 格式 | Markdown（≤64KB） | 结构化 KV（≤20 keys） |
| CRUD 入口 | kubectl apply + A2A query/get | A2A record/query only（**不能** kubectl apply Memory） |

**admission 错误码**（与 §7 错误码表对齐）：
- `KNOWLEDGE_OWNER_KIND_FORBIDDEN` (-32015)
- `KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY` (-32016)
- `KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS` (-32017)
- `MEMORY_AGENT_KIND_FORBIDDEN` (-32107)
- `MEMORY_SOURCE_KNOWLEDGE_NOT_FOUND` (-32108)
- `MEMORY_SOURCE_KNOWLEDGE_SCOPE_MISMATCH` (-32109)
- `MEMORY_AGENT_PRIVATE_REQUIRES_AGENT_NAME` (-32110)
- `MEMORY_DECAY_DAYS_TOO_LONG` (-32111)

---

## 6. Knowledge Service Agent（特殊 Agent · Python `AgentCard`）

参考 L1 Architecture §3.5.2 + L2-1 A2A Protocol Spec v0.2.0 Python §5（ASGI server 嵌入）+ Hello Agent（L1 §3.5.1）的 Card-driven 模式，Knowledge Service 是 **CRD-driven 无 framework adapter** Agent。

### 6.1 Agent Card Pydantic Model（`AgentCard` 推导）

```python
# packages/knowledge-service/src/supteam_a2a/knowledge_service/card/card.py
# 完整代码 + JSON 推导在 L3-5 Spec
from pydantic import BaseModel, Field, ConfigDict
from superteam_a2a.a2a.upstream import AgentSkill  # L2-1 边界


class KnowledgeServiceCard(BaseModel):
    """Knowledge Service Agent Card（Pydantic 推导 AgentCard JSON）。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(default="superteam-a2a.knowledge-service", frozen=True)
    version: str = Field(default="0.2.0", description="Python 重写版本")
    description: str = Field(
        default="Internal knowledge service for superteam-a2a. "
        "Provides free-text query and item retrieval across the 4-level "
        "scope hierarchy, plus persistent memory record/query.",
    )
    provider: dict[str, str] = Field(
        default={
            "organization": "superteam-a2a",
            "url": "https://github.com/superteam-cn/superteam-a2a",
        }
    )
    skills: list[AgentSkill] = Field(
        default_factory=lambda: [
            AgentSkill(
                id="query_knowledge",
                name="Query Knowledge",
                description="Free-text search over KnowledgeItems with scope/type/tag filters.",
                input_schema={  # JSON Schema 2020-12
                    "type": "object",
                    "required": ["scope", "query"],
                    "properties": {
                        "scope": {"type": "string", "description": "KnowledgeScope name"},
                        "query": {"type": "string", "minLength": 1, "maxLength": 512},
                        "typeFilter": {
                            "type": "array",
                            "items": {
                                "enum": [
                                    "document",
                                    "runbook",
                                    "api-spec",
                                    "architecture",
                                    "faq",
                                    "best-practice",
                                    "template",
                                    "contract",
                                    "troubleshooting",
                                    "glossary",
                                    "other",
                                ]
                            },
                        },
                        "tagFilter": {"type": "array"},
                        "maxResults": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 10,
                        },
                    },
                },
                output_schema={  # items[] + totalCount
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
        ]
    )
    capabilities: dict[str, bool] = Field(
        default={
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        }
    )
    authentication: dict[str, list[str]] = Field(default={"schemes": ["mtls"]})
```

### 6.2 部署形态

- **Deployment**：1 副本（v0.1 单实例，水平扩展推 v0.5+）
- **ServiceAccount**：独立 SA（`superteam-a2a-knowledge-service`），**不是 default**
- **NetworkPolicy**：仅允许 Operator + 其他 Agent 调用
- **不暴露 HTTP**：仅 A2A mTLS（cert-manager 颁发）
- **挂载 4 个 A2A method**（与 Memory backend 共享同 Deployment）：
  - `a2a.queryKnowledge` / `a2a.getKnowledgeItem`（Knowledge 主接口）
  - `a2a.recordMemory` / `a2a.queryMemory`（Memory 副接口）

---

## 7. 4 个 A2A method 详细规格

### 7.1 `a2a.queryKnowledge`

**Request / Response Pydantic DTO**（完整 schema 在 L3-5 Spec）：

```python
class QueryKnowledgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: str = Field(..., min_length=1, max_length=128)
    query: str = Field(..., min_length=1, max_length=512)
    type_filter: list[str] | None = Field(default=None, max_length=11, alias="typeFilter")
    tag_filter: list[str] | None = Field(default=None, alias="tagFilter")
    max_results: int = Field(default=10, ge=1, le=50, alias="maxResults")


class QueryKnowledgeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[
        KnowledgeItemSummary
    ]  # name + scope + type + title + summary + version + relevanceScore
    total_count: int = Field(..., ge=0, alias="totalCount")
```

**错误码**（a2a-python JSON-RPC error struct）：
- `KNOWLEDGE_SCOPE_NOT_FOUND` (-32008)
- `KNOWLEDGE_QUERY_TOO_LONG` (-32009)
- `KNOWLEDGE_INVALID_TYPE` (-32010)
- `KNOWLEDGE_INTERNAL_ERROR` (-32011)
- `KNOWLEDGE_ADMISSION_TIMEOUT` (-32018) — 新增 admission 50ms fail-closed

### 7.2 `a2a.getKnowledgeItem`

**错误码**：
- `KNOWLEDGE_ITEM_NOT_FOUND` (-32012)
- `KNOWLEDGE_VERSION_NOT_FOUND` (-32013)
- `KNOWLEDGE_FORBIDDEN` (-32014，agent-private 且 caller ≠ owner)
- `KNOWLEDGE_INTERNAL_ERROR` (-32011)

### 7.3 `a2a.recordMemory`

**错误码**：
- `MEMORY_SCOPE_NOT_FOUND` (-32101)
- `MEMORY_INVALID_CONTENT` (-32102)
- `MEMORY_FORBIDDEN` (-32103)
- `MEMORY_RATE_LIMIT` (-32104，60/min per SA)
- `MEMORY_INTERNAL_ERROR` (-32105)
- `MEMORY_ADMISSION_TIMEOUT` (-32112) — 新增 admission 50ms fail-closed

### 7.4 `a2a.queryMemory`

**错误码**：
- `MEMORY_SCOPE_NOT_FOUND` (-32101)
- `MEMORY_FORBIDDEN` (-32103)
- `MEMORY_QUERY_TOO_BROAD` (-32106，scope=industry + 无 tag/confidence 过滤被拒)
- `MEMORY_INTERNAL_ERROR` (-32105)
- `MEMORY_ADMISSION_TIMEOUT` (-32112)

**完整 Request/Response Pydantic DTO** 在 L3-5 Spec 详述（与 Go baseline wire contract 完全一致）。

---

## 8. CRD Schema 概要（Pydantic 单一来源 · ADR-0005 §5）

### 8.1 KnowledgeScope CRD（§3.2 + §3.3）

**Spec 字段（6 个 · 与 v0.1 Go baseline 完全继承）**：
- `level` (ScopeLevel StrEnum) — **必填**
- `display_name` (str, 1-64) — **必填**
- `description` (str, 0-512) — 可选
- `parent_ref` (ScopeReference) — 可选（industry 必须 None）
- `owner_ref` (SubjectReference: {kind: User|Group|SA, name: str}) — **必填**
- `inherit_rules` (InheritRules) — 可选
- + labels (map) — 可选（不计 spec 字段数）

**Status 字段（6 个）**：phase + message + conditions + item_count + child_scopes + observed_generation

### 8.2 KnowledgeItem CRD

**Spec 字段（9 个）**：scope_ref + type + title + body + summary + tags + visibility + owner_ref + source_uri + version

**Status 字段**：phase + conditions + last_queried_at + ...（ADR-0002 详细）

### 8.3 Memory CRD

**Spec 字段（12 个，详见 §5.2 表格）**

**Status 字段（7 个）**：
- `phase` (MemoryPhase: Active/Decaying/Promotable/Expired/Error)
- `message` (str)
- `conditions` (list[Condition])
- `last_decayed_at` (AwareDatetime | None)
- `last_reinforced_at` (AwareDatetime | None)
- `effective_confidence` (float，Reconciler 更新)
- `eligible_for_promotion` (bool，v0.1 仅计算不触发)
- `observed_generation` (int)

### 8.4 CRD YAML 生成链路（ADR-0005 §5.2）

```
Pydantic BaseModel.model_json_schema()
   ↓ (deterministic sort + x-kubernetes-* extensions injection)
deterministic OpenAPI v3 schema
   ↓ (kubectl apply dry-run + round-trip test)
checked-in: charts/superteam-a2a/crds/knowledgescope.yaml
            charts/superteam-a2a/crds/knowledgeitem.yaml
            charts/superteam-a2a/crds/memory.yaml
```

**CI 门禁**：
- `uv run python scripts/crd_gen.py` — 生成 CRD YAML
- `git diff --exit-code charts/superteam-a2a/crds/` — 无 diff 才允许提交
- `kubectl apply --dry-run=server -f charts/superteam-a2a/crds/` — schema 校验通过
- Pydantic ↔ YAML round-trip test（fixture 验证）

### 8.5 字段数约束（防过度设计 · ADR-0004）

| CRD | spec 字段数 | 上限 | 距离 |
|-----|------------|------|------|
| KnowledgeScope | 6 + 引用类型 | 15 | 距上限 9 |
| KnowledgeItem | 9 + 引用类型 | 15 | 距上限 6 |
| Memory | 12 + 引用类型 | 15 | **距上限 3（临界）** |

---

## 9. 检索路径（Python BM25 + 受控线程 offload · D-2）

### 9.1 存储策略

| 数据 | 存储 | 理由 |
|------|------|------|
| KnowledgeItem | K8s **etcd**（CRD 即存储） | 无外部依赖；v0.1 简化 |
| Memory | K8s **etcd**（CRD 即存储） | 无外部依赖；v0.1 简化 |
| 倒排索引 | **Operator 进程内存**（`RealInvertedIndex`） | 10K items 重建 ≤30s 可接受 |

### 9.2 检索流程（queryKnowledge）

```
A2A method request (a2a.queryKnowledge)
       ↓
KnowledgeService handler (knowledge_service/handlers/query_knowledge.py)
       ↓
1. scope 存在性检查 → ScopeResolver.get_scope() (D-2)
2. typeFilter / tagFilter 校验（§7.1 Request Pydantic 已校验）
3. resolve_effective_scopes(scope_name) → 继承链 [industry, org, team, project]
4. InvertedIndex.search(query, scope_chain, ...) → 候选 KnowledgeItem
       ↓ to_thread.run_sync (CPU offload 满足 event-loop lag 门禁)
   BM25 评分 + scope 过滤 + typeFilter/tagFilter + maxResults 截断
       ↓
5. visibility 过滤（public-readable 仅 industry；agent-private v0.1 禁用）
6. inheritRules 过滤（includeTypes / excludeTypes）
7. 去重：同 ID 保留最新 version
8. 返回 items[] + totalCount (Pydantic QueryKnowledgeResponse)
```

### 9.3 v0.5+ 演进（非 v0.1 范围）

- 可选 Vector DB 后端（Chroma / Qdrant）
- Operator 实现 vector backend interface
- Helm values 选择 backend 实现
- 自动 scope-up（`KnowledgePromotionRequest` CRD）

---

## 10. 持久化层（CRD 即存储 + 内存倒排 · v0.1 无外部依赖）

### 10.1 为什么不用 PG / Vector DB

- **单人维护成本**：2h/天 运维 PG / Chroma 集群超出预算
- **数据一致性**：CRD 即存储天然 K8s RBAC + audit log 支持
- **容量充足**：10K items + 50K memories × 1KB ≈ 60MB，远低于 etcd 默认 8GB
- **可演进**：v0.5+ 可加 Vector DB（不影响 API 契约）

### 10.2 Operator 内存倒排索引（D-2）

| 项 | v0.2 Python | 备注 |
|----|-------------|------|
| 实现 | `dict[str, set[str]]` post_listing + `dict[str, int]` doc_lens | 启动时全量重建；watch 增量更新 |
| 评分 | BM25（K1=1.5, B=0.75） | 与 Go baseline 公式完全等价 |
| 重建时间 | ≤ 30s @ 10K items | `anyio.to_thread.run_sync` offload |
| 容量上限 | 10K items | 超出拒绝创建 |
| CPU offload | `anyio.to_thread.run_sync`（默认 40 线程） | ADR-0005 §6.3 |
| 锁 | `asyncio.Lock`（避免 race） | single-writer 多 reader |

### 10.3 MemoryReconciler 周期（D-3）

- **周期**：60s（Kopf `@kopf.timer(interval=60.0)`）
- **批量**：单 reconcile ≤ 1000 Memory（`MemoryReconcilerService.BATCH_SIZE`，Helm values 可配）
- **时钟**：`Clock` Protocol 注入（默认 `RealClock`；测试 `FakeClock` 时间穿越）
- **Leader Election**：`coordination.k8s.io/v1` Lease（与 L2-2 Operator Core 共享）
- **失败重试**：Kopf `backoff` 装饰器；指数退避；上限 5min

---

## 11. 可观测性（Python 指标 + structlog + OTel）

### 11.1 Prometheus 指标（与 v0.1 wire contract 完全一致）

**Knowledge 侧**（`superteam_knowledge_*` — 11 个）：
- `superteam_knowledge_query_total` (Counter: scope, type, result)
- `superteam_knowledge_query_duration_seconds` (Histogram: scope)
- `superteam_knowledge_items_total` (Gauge: scope, type, phase)
- `superteam_knowledge_search_index_size` (Gauge)
- `superteam_knowledge_scope_total` (Gauge: level)
- `superteam_knowledge_search_offload_seconds` (Histogram · Python 新增)
- `superteam_knowledge_search_event_loop_lag_seconds` (Histogram · Python 新增)
- ...

**Memory 侧**（`superteam_memory_*` — 6 个）：
- `superteam_memory_record_total` (Counter: scope, agent, result)
- `superteam_memory_query_total` (Counter: scope, visibility, result)
- `superteam_memory_decay_total` (Counter: phase_from, phase_to)
- `superteam_memory_reconcile_duration_seconds` (Histogram)
- `superteam_memory_eligible_for_promotion_total` (Gauge: scope)
- `superteam_memory_total` (Gauge: scope, phase)

**Python runtime 特定**（ADR-0005 §10）：
- `superteam_python_event_loop_lag_seconds` (Histogram) — anyio to_thread offload 监控
- `superteam_python_thread_offload_queue_depth` (Gauge) — to_thread 队列深度
- `superteam_python_active_tasks` (Gauge) — asyncio Task 活跃数

### 11.2 OTel Trace

- **Root Span**：`knowledge_service.{method}` / `memory_backend.{method}`
- **Child Spans**：`crd.read` / `index.search` / `bm25.score` / `visibility.filter` / `reconcile.batch`
- **Span Events**：`scope.resolved` / `admission.validated` / `reinforce.triggered` / `decay.applied` / `gc.expired`
- **Python 特定**：`thread.offload.start` / `thread.offload.end`（duration）

### 11.3 结构化 JSON 日志（structlog · ADR-0005 §10）

**强制字段**：`framework`（固定 "core"）/ `caller_agent` / `scope` / `trace_id` / `level` / `ts` / `msg`
**可选字段**：`memory_key` / `confidence` / `effective_confidence` / `decay_days` / `event_loop_lag_ms`

**敏感字段黑名单**：`content` / `body` / `tags`（K8s audit log + Memory content 永不进入普通日志）

### 11.4 K8s Events

| Event | 触发 |
|-------|------|
| `KnowledgeScopeCreated` / `KnowledgeScopeDeleted` | scope CR 创建 / 删除 |
| `KnowledgeItemPublished` / `KnowledgeItemDeprecated` | KI phase 转换 |
| `MemoryCreated` / `MemoryReinforced` / `MemoryDecayed` / `MemoryExpired` / `MemoryGarbageCollected` | Memory lifecycle |

**Python 实现**：`kopf.event` 装饰器 + K8s Event API（与 L2-2 Operator Core 一致）。

---

## 12. 测试策略（pytest + pytest-asyncio + FakeClock 时间穿越）

### 12.1 单元测试（`knowledge/` + `memory/` + `shared/visibility/`）

| 范围 | 覆盖率目标 | 测试类型 |
|------|-----------|----------|
| `knowledge/scope/inheritance.py` | 100% | 表驱动（12 种 scope 组合）+ pytest-asyncio |
| `knowledge/search/inverted_index.py` | ≥ 90% | 真实 BM25 fixture + performance benchmark |
| `memory/lifecycle/{decay,reinforce,promotion,gc}.py` | 100% | **时间穿越**（FakeClock）+ freezegun 风格 |
| `shared/visibility/5 维矩阵` | 100% | 4×3 = 12 种 visibility × scope 组合穷举 |
| admission webhook | 100% | KI 互斥 + Memory 互斥 + scope 校验 + 50ms timeout fail-closed |

### 12.2 集成测试（envtest · Kopf in-process）

- KnowledgeScope 创建 → 4 级继承校验
- KnowledgeItem 创建 → admission 通过 → list/get 成功
- Memory record/query → visibility 过滤 → agent-private 短路
- 周期 reconcile 触发 decay → effective_confidence 更新
- Leader Election failover（停止 leader → 新 leader 接管 ≤ 30s）
- admission 50ms timeout fail-closed（mock K8s API 延迟 100ms → 拒绝写入）

### 12.3 E2E 测试（kind）

- **E2E-K-001**：knowledge-quickstart（创建 industry + org + team + project scope → 创建 5 KI → queryKnowledge 命中继承链）
- **E2E-K-002**：visibility 矩阵穷举（4 visibility × 4 scope = 16 种）
- **E2E-M-001**：memory-record-query（agent 写 1 memory → queryMemory 命中 → reinforce → decay P95 ≤ 300ms）
- **E2E-M-002**：admission 互斥（KI.ServiceAccount.ownerRef 拒绝 / Memory.User.agentRef 拒绝）
- **E2E-M-003**（Python 新增）：MemoryReconciler Python 路径（FakeClock 推进 30 天 → effective_confidence = 0.368）
- **E2E-M-004**（Python 新增）：Leader Election failover（kill leader pod → 30s 内新 leader 接管）

### 12.4 时间穿越测试（decay 关键 · D-4）

```python
# packages/memory/tests/unit/lifecycle/test_decay.py
def test_decay_over_30_days():
    """30 天后 effectiveConfidence 应为 1.0 * exp(-1) ≈ 0.368。"""
    fake_clock = FakeClock(start=datetime(2026, 7, 24, 0, 0, 0, tzinfo=UTC))
    memory = Memory(
        spec=MemorySpec(
            confidence=1.0,
            decay_days=30,
            scope_ref=ScopeReference(name="team-test"),
            agent_ref=AgentReference(kind=SubjectKind.SERVICE_ACCOUNT, name="test-agent"),
            content={"key": "value"},
            summary="test",
            reinforced_count=0,
            visibility=MemoryVisibility.SCOPE_AND_CHILDREN,
        ),
        metadata=ObjectMeta(name="test", creation_timestamp=fake_clock.now()),
    )

    fake_clock.advance(timedelta(days=30))  # 30 天后

    effective = apply_decay(memory, fake_clock.now())
    assert abs(effective - 0.368) < 0.01  # exp(-1) ≈ 0.368
```

### 12.5 性能测试

- **Knowledge**：10K items queryKnowledge P95 ≤ 200ms
- **Memory**：50K memories recordMemory P95 ≤ 200ms + queryMemory P95 ≤ 300ms
- **MemoryReconciler**：60s 周期 reconcile 全集群 50K memories ≤ 30s（`@kopf.timer` interval 兜底）
- **BM25 倒排索引 CPU offload**：search 阻塞时间 ≤ 100ms（event-loop lag 门禁）

### 12.6 Conformance 测试

- A2A method 4 个 100% wire-compatible with `google-a2a/conformance`
- admission webhook 拒绝率 + 通过率 + 50ms timeout 行为
- 错误码范围 -32008 ~ -32112（与 Go baseline 完全一致）

### 12.7 静态质量门禁（ADR-0005 §11.1）

- `pyright --strict` — 公共 API 零未解释 `Any`
- `ruff check .` — 无 ignore 绕过
- `bandit -r packages/knowledge packages/memory packages/knowledge-service packages/memory-backend`
- `pip-audit` — Python 依赖安全

---

## 13. 与其他模块的接口契约

### 13.1 与 L2-1 A2A Protocol v0.2.0 Python

| 接口 | 方向 | 形式 |
|------|------|------|
| `supteam_a2a.a2a.upstream.create_app` | KnowledgeService 内嵌 | 启动 `create_app(handlers=...)` 注册 4 个 method handler |
| `supteam_a2a.a2a.upstream.AgentCard` | KnowledgeService 提供 | Pydantic `KnowledgeServiceCard` 推导（§6.1） |
| `supteam_a2a.a2a.upstream.Message/Task/Part` | 4 handler 收发 | Pydantic 类型 + JSON-RPC envelope |

### 13.2 与 L2-2 Operator Core v0.2.0 Python

Operator Core 提供 4 类能力：

1. **CRD Controller**（`memory_handler.py` · D-3）：Kopf `@kopf.timer(interval=60.0)` + `MemoryReconciler` service + Leader Election
2. **CRD Controller**（`knowledge_scope_handler.py` / `knowledge_item_handler.py`）：状态更新 + 校验
3. **admission webhook**：4 级 scope 继承 + 循环引用 + KI/Memory 双向互斥（Kopf `kopf.validation` decorator · D-5）
4. **Finalizer**：`memory.superteam-a2a.io/cleanup`（Memory 删除时清理关联资源）

**集成点**（L2-2 Spec v0.2.0 Python §5.6 引用本设计 §10.3）：
- `MemoryReconciler` 在 L2-2 Operator Core 同进程运行；引用 `supteam_a2a.memory.lifecycle.apply_decay` 等纯函数
- Leader Election 通过 `supteam_a2a.shared.leader.LeaseLeader`（与 Agent / AgentSet / Workflow Reconciler 共享）

### 13.3 与 L2-3 Adapter v0.2.0 Python（v0.5+ 代理调用）

L2-3 Adapter 可代理调用：
- `a2a.queryKnowledge` → Adapter `Adapter.on_message` → httpx → Knowledge Service
- `a2a.getKnowledgeItem` → Adapter `Adapter.on_message`
- `a2a.recordMemory` → Adapter `Adapter.on_message`
- `a2a.queryMemory` → Adapter `Adapter.on_message`

**v0.1 状态**：不强制实现（Knowledge Service 可直接被其他 Agent 调用）；v0.5+ L2-3 Spec 显式规定 4 method 代理。

### 13.4 admission webhook 详细规格（D-5）

**KnowledgeItem admission webhook**（`knowledge/admission/ki_webhook.py`）：
- ✅ `owner_ref.kind` ∈ {User, Group}（拒绝 ServiceAccount）→ `KNOWLEDGE_OWNER_KIND_FORBIDDEN`
- ✅ `visibility == public-readable` 必须 `scope.level == industry` → `KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY`
- ✅ `visibility == agent-private` v0.1 拒绝 → `KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS`
- ✅ `scope_ref` 存在 + level 合法 + parent 关系合法
- ✅ 50ms 超时 fail-closed（etcd 不可用时拒绝写入）

**Memory admission webhook**（`memory/admission/m_webhook.py`）：
- ✅ `agent_ref.name` 对应 ServiceAccount 存在
- ✅ `scope_ref` 对应 KnowledgeScope 存在
- ✅ `source_knowledge_ref` 若存在 → KI 存在 + scope 匹配
- ✅ `visibility == agent-private` 必须 `agent_ref.name != ""`
- ✅ `decay_days ≤ 3650`
- ✅ 50ms 超时 fail-closed

### 13.5 与外部依赖

- **cert-manager**：mTLS 证书颁发（KnowledgeService + Memory 同 deployment）
- **OpenTelemetry Collector**：OTLP exporter（v0.1 强制开启）
- **K8s RBAC**：ServiceAccount `superteam-a2a-knowledge-service` + ClusterRole/Role 自动生成

---

## 14. 部署形态（uv workspace + Helm values Python 镜像块）

### 14.1 Knowledge Service Deployment（与 Memory backend 共享）

```
┌─────────────────────────────────────────────────────────┐
│ Pod: superteam-a2a-knowledge-service (1 副本 v0.1)       │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Container: knowledge-service                     │   │
│  │ (python:3.12-slim + uv 多阶段镜像)               │   │
│  │                                                  │   │
│  │  :8080 ASGI / Uvicorn 单 worker                  │   │
│  │       │                                          │   │
│  │       ├─ a2a.queryKnowledge handler              │   │
│  │       ├─ a2a.getKnowledgeItem handler            │   │
│  │       ├─ a2a.recordMemory handler                │   │
│  │       └─ a2a.queryMemory handler                 │   │
│  │                                                  │   │
│  │  共享：In-process 倒排索引（10K items）          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ServiceAccount: superteam-a2a-knowledge-service        │
│  mTLS cert: cert-manager 自动颁发                       │
│  NetworkPolicy: 仅允许 Operator + 其他 Agent            │
└─────────────────────────────────────────────────────────┘
```

**为什么不拆分两个 Deployment**：
- 知识 + 记忆是互补能力，共享内存索引（避免 RPC 跨界）
- 单人维护成本：单 Deployment 简化 Helm chart
- v0.5+ 可拆分（如果规模超 1 副本倒排索引同步成本上升）

### 14.2 MemoryReconciler（Operator 进程内 · D-3）

- 部署于 **Operator 同 Deployment / 同进程**（`packages/operator`）
- 60s 周期 reconcile 全集群 Memory
- 单 leader（K8s Lease）
- v0.5+ 水平扩展（Helm values `memoryReconciler.replicas: N`）

### 14.3 持久化层

- **CRD 即存储**：K8s etcd（无 PG / Vector DB）
- **Operator 内存倒排索引**：10K items 进程内 `dict`
- **etcd 加密**：v0.1 默认开启（依赖 K8s 集群 etcd encryption-at-rest）

### 14.4 Helm values（详情见后续 Spec v0.2-draft Python）

**Python 镜像块**（ADR-0005 §13 + L1 v0.2.0 §9.5）：

```yaml
knowledgeService:
  image:
    repository: ghcr.io/coderzhangfujiang/superteam-a2a-knowledge-service
    tag: "0.2.0"  # Python 重写版本
    pullPolicy: IfNotPresent
  python:
    runtime: "python:3.12-slim"
    workers: 1  # 单进程原则（ADR-0005 §6.2）
    eventLoopLagThresholdMs: 100
  resources:
    limits:
      cpu: "2"
      memory: "1Gi"
    requests:
      cpu: "500m"
      memory: "256Mi"
  replicas: 1
  healthCheck:
    livenessProbe:
      httpGet: { path: /healthz, port: 8080 }
      initialDelaySeconds: 10
      periodSeconds: 30
    readinessProbe:
      httpGet: { path: /readyz, port: 8080 }
      initialDelaySeconds: 5
      periodSeconds: 10

memoryReconciler:
  enabled: true
  interval: 60  # 周期（秒）
  batchSize: 1000
  clock:
    fake: false  # 生产 = RealClock；测试 = FakeClock
  leader:
    leaseName: superteam-a2a-operator-leader
    leaseNamespace: superteam-a2a-system
    renewDeadlineSeconds: 15
    retryPeriodSeconds: 5

search:
  index:
    rebuildOnStart: true
    maxItems: 10000  # 容量上限
  bm25:
    k1: 1.5
    b: 0.75

admission:
  enabled: true
  timeoutMs: 50  # admission 50ms 超时 fail-closed
  tls:
    certManager:
      issuerRef: { name: superteam-a2a-ca, kind: Issuer }

ratelimit:
  memory:
    perServiceAccountPerMinute: 60
    slidingWindow: true  # Tenacity sliding window
```

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

## 附录 B：开放问题

继承 v0.1.0 Go baseline 12 项 + Spec 新增 4 项 + Python 重写新增 6 项 = **22 项**。

### B.1 继承 v0.1.0 Go baseline（12 项）

| # | 问题 | 默认决策 | 待确认 |
|---|------|----------|--------|
| B.1 | Knowledge Service 是否要拆分为 Knowledge + Memory 两个独立 Deployment？ | v0.1 单 Deployment 共享（避免倒排索引重建 + 单人维护） | 用户 |
| B.2 | Memory 与 Knowledge Service 是否共享同一个 ServiceAccount？ | 共享（`superteam-a2a-knowledge-service`） | 用户 |
| B.3 | v0.1 阶段是否有 Memory 内存索引 / 全文搜索需求？ | 否 — 仅 memoryKeyPattern + tag + confidence 过滤 | 用户 |
| B.4 | Memory 自动 scope-up 的 v0.5+ 详细设计？ | 引入 KnowledgePromotionRequest CRD | 用户（v0.5+） |
| B.5 | Knowledge Service 是否需要 rate limiting（per-SA）？ | 是 — Memory rate limit 60/min per SA + Knowledge 100/min per SA | 用户 |
| B.6 | admission webhook 失败模式（若 etcd 不可用）？ | 50ms 超时 → 拒绝写入（fail-closed） | 用户 |
| B.7 | 多 cluster 知识复制（v1.0+）？ | v0.1 不实现；v1.0+ ADR 评估 | 用户（v1.0+） |
| B.8 | Memory 与会话上下文（session context）的边界？ | session context 单 Agent 私有不持久化；Memory 是 Agent 团队共享的经验 | 用户 |
| B.9 | Memory 写入是否要记录到审计日志？ | 是 — K8s audit log + structured logger（不引入额外 audit log 系统） | 用户 |
| B.10 | KnowledgeItem 的 version 字段是显式还是自动？ | 显式（用户 `kubectl patch` 时手动 +1） | 用户 |
| B.11 | MemoryReconciler 周期 60s 是否过短/过长？ | 60s 默认；Helm values 可配（30s-300s） | 用户 |
| B.12 | Knowledge Service 是否需要水平扩展（HPA）？ | v0.1 不需要（1 副本足够 10K items）；v0.5+ 评估 | 用户（v0.5+） |

### B.2 Spec 新增（继承 v0.1.0 Go baseline 4 项）

| # | 问题 | 默认决策 | 待确认 |
|---|------|----------|--------|
| B.13 | Memory status.eligible_for_promotion 字段超限（v0.1 仅计算不触发）？ | v0.1 接受超限 1 字段（调试价值 + v0.5+ 触发 KnowledgePromotionRequest 有用） | 用户 |
| B.14 | admission webhook 部署形态（operator 进程内 vs 独立 Deployment）？ | v0.2 Python 采用 operator 内嵌（Kopf `kopf.validation`）；v0.5+ 评估独立 Deployment 性能隔离 | 用户 |
| B.15 | Memory 写入是否需要 PV 缓存层（性能）？ | v0.1 仅 etcd；v0.5+ PV 缓存（如 MemoryStore Protocol 实现可替换） | 用户（v0.5+） |
| B.16 | rate limiting 是否区分 read/write SA 配额？ | v0.1 Memory 写 60/min + 读 1000/min per SA（默认 read 远大于 write） | 用户 |

### B.3 Python 重写新增（6 项）

| # | 问题 | 默认决策 | 待确认 |
|---|------|----------|--------|
| B.17 | Kopf `@kopf.timer` + admission webhook 共存启动顺序？ | L3-5 实测；Kopf 默认 webhook 先于 timer 启动 | L3-5 |
| B.18 | cert-manager TLS 证书热更新是否需要 reload SSL context？ | L3-5 验证；Kopf webhook reload + cert-manager `renewBefore: 720h` | L3-5 |
| B.19 | `anyio.to_thread.run_sync` CPU offload 线程池容量？ | anyio 默认 40 线程；L3-5 实测 10K items search ≤ 100ms | L3-5 |
| B.20 | Pydantic v2 BaseModel 在 K8s admission JSON 反序列化性能？ | L3-5 benchmark 显示 5-10x Go json.Unmarshal；监控 admission_duration_seconds；如不达标考虑 `orjson` | L3-5 |
| B.21 | MemoryReconciler 60s 周期 + 50K memories 批量 reconcile 时间预算？ | L3-6 实测 ≤ 30s；超则调 batch size 或 scope hash 分片 | L3-6 |
| B.22 | 5 维矩阵 `is_memory_visible_to()` 在 50K memories 查询时的延迟？ | L3-6 实测 P95 ≤ 50ms（dict 查找 + set 成员检测） | L3-6 |

---

## 变更记录

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| v0.1-draft | 2026-07-24 | 初稿：14 节 + 2 附录；3 CRD 概要（KnowledgeScope / KnowledgeItem / Memory）+ 4 A2A method + Knowledge Service Agent Card 草案 + 5 维矩阵 + 检索路径 + 持久化层 + 可观测性 + 12 项开放问题 | Claude Code（会话 cont12） |
| v0.1.0 | 2026-07-24 | 评审通过：[l2-4-knowledge-memory-review.md](../reviews/l2-4-knowledge-memory-review.md) §A 10 维度全通过 + 颗粒度决议保留完整版（设计 41KB + Spec 99KB）；附录 B 升级为 16 项（继承设计 12 项 + Spec 新增 4 项双层开放问题模式） | 项目发起人（基于 MVP 例外 14.5 单点评审；会话 cont14） |
| v0.2-draft | 2026-07-26 | **Python 重写**：14 节 + 2 附录；ADR-0005 §3.4/§6.2/§6.3/§7/§10/§13 落地；5 项 Python 化关键决策（D-1 Pydantic v2 / D-2 BM25 + anyio to_thread / D-3 Kopf timer + Leader / D-4 Clock Protocol + FakeClock / D-5 Kopf admission）；附录 B 扩展为 22 项（继承 12 + Spec 新增 4 + Python 重写新增 6 三层开放问题模式）；**wire contract（3 CRD / 4 method / 5 维矩阵 / admission 互斥 / 错误码 -32008~-32112）与 v0.1.0 Go baseline 完全继承** | Claude Code（会话 cont38） |
| v0.2.0 | 2026-07-27 | 评审通过：[l2-4-knowledge-memory-python-review.md](../reviews/l2-4-knowledge-memory-python-review.md) §A-§P 10 维度全 PASS（0 阻塞项 · 3 关注项移交 L3-5/L3-6/Spec 起草 · 4 建议项）+ 颗粒度决议保留完整版（97KB / 1920 行 vs 目标 30-45KB / 1100-1300 行 · 2.2-3.2x · 与 L2-2/L2-3 同等级）+ L2-4 Go baseline 归档元数据登记（README 备注覆盖丢失，与 L2-1/L2-3 同模式） | 项目发起人（基于 MVP 例外 14.5 单点评审；会话 cont39） |