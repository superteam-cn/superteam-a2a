# L3 文件级 Spec：Adapter SDK（编排层 Adapter 框架 SDK · Python-first）

> **⚠️ ADR-0005 supersede + 归档标记（2026-07-28）**：本 v0.2-draft Spec 文档**仅 supersede Go framework adapter / sigs.k8s.io/cli-runtime 实现条款**；wire contract（Adapter Protocol + FrameworkAdapter Protocol + AgentCardConverter + 6 framework matrix + 4 配置优先级 + 错误码 7 项）与 v0.2.0 Spec 业务语义**完全继续有效**。L2-3 v0.1.0 Go baseline 已归档至 [`docs/archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md`](../../archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md)（2026-07-24 归档 / 2026-07-26 #37 评审前未独立评审 / L2-3 v0.2.0 Python 重写已被 L2-3 v0.2.0 Spec 完全覆盖）。
>
> **Python 重写入口**：依据 L1 v0.2.0 Architecture §3.5 + §4.3 C-3 + ADR-0005 §3.3 + §13.1 + L2-3 v0.2.0 Spec §3-§6 落地，11 文件 SDK + 6 framework adapter 子包 → uv workspace `packages/adapter-sdk/src/superteam_a2a/adapter/`；6 framework 集成（LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents）→ 6 framework subpackage 独立仓库 + FrameworkAdapter Protocol（typing.Protocol + `@runtime_checkable`）；AgentCard 转换 → Pydantic v2 + A2AClient（L3-2 §6 复用）；4 层配置优先级（CRD spec > env > sidecar file > defaults）→ Pydantic v2 BaseSettings + 显式 merge 顺序 + 单元测试覆盖。
>
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-3（Adapter SDK，见 L1 Architecture §4.3）
> **代码位置**：`packages/adapter-sdk/src/superteam_a2a/adapter/`（**ADR-0005 §13.1 uv workspace 布局**，替代原 baseline 的 `src/adapter-sdk/`）
> **版本**：**v0.2-draft-skeleton**（2026-07-28 起 Python 重写 + L3-1 v0.2.0 #56 + L3-2 v0.2.0 #54 L3 阶段 1/4 ~ 2/4 已通过；2026-07-28 #57 §3-§6 补完）
> **状态**：✅ **v0.2-draft-skeleton §3-§6 补完稿**（#56 骨架 + #57 §3-§6 补完）——头部 + §0-§6 + 附录 A/B 占位 全部落地；§7-§10 + 完整附录 A/B 留待补完（约 30-40KB / ~700-1000 行）
> **上游约束**：[`docs/design/L2-modules/L2-adapter.md`](../../design/L2-modules/L2-adapter.md) **v0.2.0**（2026-07-26 #35 评审通过 · 1267 行 / 66KB / 14 主章节）+ [`docs/spec/L2-module-specs/L2-adapter.md`](../../spec/L2-module-specs/L2-adapter.md) **v0.2.0**（2026-07-26 #37 评审通过 · 114KB / 2705 行 / 14 节 + 2 附录 / 81-159 测试 ID / 15 开放问题 / 9 Python Protocol/Class + 5 生命周期时序图 + Helm values 11.1-11.6 + 6 framework 完整 schema + 6 层测试策略）
> **本 Spec 目的**：将 L2-3 Adapter Spec v0.2.0 中的 **11 文件 SDK + 6 framework adapter 子包 + FrameworkAdapter Protocol + AgentCardConverter + A2AClient 复用 + Helm values + 测试策略** 落地为 **文件级 Python 代码契约**——每个文件列明**绝对路径（基于 uv workspace 布局）**、**职责一句话**、**完整 import 列表**、**exported 符号签名（type hints + docstring 一行）**、**内部 helper 列表**、**关联测试文件路径 + 测试 ID 前缀**。是 L4 实施阶段（开发者打开 IDE 即可对照写代码）的直接输入。
> **配套 Spec**：[L3-1 Operator Core 文件级 Spec v0.2.0](./L3-operator-core.md)（2026-07-28 #56 评审通过）/ [L3-2 A2A Core Library 文件级 Spec v0.2.0](./L3-a2a-core.md)（2026-07-28 #54 评审通过 · [评审报告](../../reviews/l3-2-a2a-core-spec-review.md)） — L3-3 复用 L3-2 §6 `A2AClient` 与 §9 15 指标 + L3-2 §10 24 错误码 enum，不重复定义 A2A wire contract / [L3-4 Hello Agent 文件级 Spec](./L3-hello-agent.md)（待起草）/ [L3-5 Knowledge Service 文件级 Spec](./L3-knowledge-service.md)（待起草）/ [L3-6 Memory backend 文件级 Spec](./L3-memory-backend.md)（待起草）

---

## 0. 阅读指南

- **读者**：Adapter SDK 实施工程师（L4 Python 编码）、Framework Adapter 集成者（6 framework 各自 owner）、Code Reviewer（PR 审查）、架构 Reviewer（Adapter 边界一致性）
- **必读章节**：§1（模块使命 + 11 → 39 文件清单总览）/ §2（Python 包结构 11 文件 SDK + 6 framework 子包）/ 附录 A（跨模块引用清单）/ 附录 B（ADR / Constitution 5 子表追溯矩阵）
- **评审入口**：附录 A 6 子表（30 行） + 附录 B 5 子表（49 行）+ 11 文件 SDK 全部 exported 符号与测试 ID 映射 — 三处必须互相回链且数量一致
- **配套阅读**：[L2-3 Adapter Spec v0.2.0 §3-§15](../../spec/L2-module-specs/L2-adapter.md) · [L2-3 Adapter Design v0.2.0 §3-§14](../../design/L2-modules/L2-adapter.md) · [L1 Architecture v0.2.0 §3.5 适配层](../../design/L1-architecture.md) · [ADR-0005 §3.3 Adapter SDK 模块映射](../../adr/0005-python-first-technology-stack.md) · [L3-2 A2A Core v0.2.0 §6 A2AClient + §9 指标 + §10 错误码](../../spec/L3-file-specs/L3-a2a-core.md) · [L3-1 Operator Core v0.2.0 §7.1.2 指标 + §7.3 RBAC + §7.2 Helm](../../spec/L3-file-specs/L3-operator-core.md) · [a2a-sdk 官方文档](https://github.com/google/a2a-python) · [Kopf 官方文档](https://kopf.readthedocs.io/)

**与 L3-2 复用边界**：
- L3-3 复用 L3-2 §6 `A2AClient`（直接 import，不重写 wire contract）
- L3-3 复用 L3-2 §9 15 指标（11 A2A + 4 runtime，本 Spec 只新增 6 framework 独立指标）
- L3-3 复用 L3-2 §10 24 错误码 enum（不新增错误码）

**与 L3-1 边界**：
- L3-3 不依赖 K8s API（由 L3-1 Operator Core 调用本 SDK 完成 CRD→FrameworkAdapter 转换）
- L3-3 不实现 mTLS（与 L3-2 同进程，由 L3-1 admission webhook 统一拦截）
- L3-3 通过 `ST-ADAPTER-BOUNDARY` Ruff 规则保证跨包边界（与 L3-1 的 `ST-A2A-BOUNDARY` 同等级）

---

## 1. 模块使命与文件清单总览

### 1.1 使命

L3-3 Adapter SDK 文件级 Spec 将 [L2-3 Spec v0.2.0](../../spec/L2-module-specs/L2-adapter.md) 中描述的 **11 文件 SDK + 6 framework adapter 子包 + FrameworkAdapter Protocol + AgentCardConverter + 4 层配置优先级 + 7 错误码 + 6 框架集成的细节** 落地为 **可直接对照编码的 Python 文件级契约**。

**单 SDK 形态**：Adapter SDK 作为 uv workspace 单独 package（`packages/adapter-sdk/`），6 framework adapters 作为独立仓库（每个 framework 单独 PyPI 包，但通过本 SDK 的 `FrameworkAdapter` Protocol 接入）；adapter-sdk 与 L3-1 Operator Core + L3-2 A2A Core + L3-5 Knowledge Service 之间通过固定的 Python Protocol + Pydantic v2 边界（无 K8s API 依赖）。

**L3-3 文件级 Spec v.s. L2-3 模块 Spec 边界**：

| 维度 | L2-3 模块 Spec | L3-3 文件级 Spec |
|---|---|---|
| **粒度** | 模块级（11 文件 SDK + 6 framework 概要） | 文件级（11 SDK + 6 framework 子包共 39 文件级契约 + 每个文件的 import/exported/helper/测试文件） |
| **目的** | "为什么 + 是什么"（设计决策 + 4 协议 + 6 framework matrix + 4 层配置 + 7 错误码） | "怎么做"（每个文件具体怎么写） |
| **读者** | 架构师 + L3 起草者 | L4 实施工程师（开发者打开 IDE 对照） |
| **变更频率** | 低（设计变更才改） | 中（实现微调可能改） |
| **测试 ID 范围** | L2-3 81-159 测试 ID（≥ 81 v0.2 / ≥ 159 v1.0） | 继承 L2-3 前缀与语义，并按文件级路径细化为 §9 的**约 159 个可执行测试 ID**；§10 的 `OPEN-A-*` 仅作决策追踪，不计入 159 |

### 1.2 模块对外契约（public API surface · 继承 L2-3 Spec §1.2）

**Public API 入口**（仅暴露给 L3-1 Operator Core + L3-2 A2A Core + 6 framework adapters 各自 repository）：

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/__init__.py
from .protocol import (
    FrameworkAdapter,
    AgentCardConverter,
    AgentSpec,
    AgentCard,
    AdapterConfig,
    AdapterError,
    AdapterPermanentError,
    AdapterRetryableError,
    AdapterNonRetryableError,
    AdapterConfigError,
    AdapterAuthError,
    AdapterTimeoutError,
    AdapterFrameworkError,
    AdapterVersionError,
)

__all__ = [
    "FrameworkAdapter",
    "AgentCardConverter",
    "AgentSpec",
    "AgentCard",
    "AdapterConfig",
    "AdapterError",
    "AdapterPermanentError",
    "AdapterRetryableError",
    "AdapterNonRetryableError",
    "AdapterConfigError",
    "AdapterAuthError",
    "AdapterTimeoutError",
    "AdapterFrameworkError",
    "AdapterVersionError",
]
```

**L3-3 新增 internal API**（仅 adapter-sdk 包内部 + 6 framework 各自 repository 内部使用,不对外暴露）：

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/_internals.py
# 注：仅用于 L3 内部测试夹具 import,不进 __all__
```

**第三方 import 边界**（canonical）：
- **A2A 协议层**：仅 `from a2a import AgentCard, Message, Task, Artifact`（L3-2 提供的 SDK）
- **Pydantic v2**：`from pydantic import BaseModel, Field, ConfigDict, SecretStr, field_validator`
- **Tenacity 5 类策略**：`from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log`
- **structlog**：`import structlog`（8 必含字段）
- **Prometheus client**：`from prometheus_client import Counter, Histogram, Gauge`
- **opentelemetry**：`from opentelemetry import trace, propagate`
- **禁止**：`import aiohttp` / `import requests` / `import flask` / `import django` / `import kubernetes` / `import kopf` / `import anyio`（任何 framework adapter 不得直接导入；如使用必须通过 SDK 提供的 Protocol）

### 1.3 文件清单总览（11 + 6 + 24 = 41 文件级契约）

#### 1.3.1 11 文件 SDK 主清单（与 L2-3 Spec §3.1 一致）

| # | 路径 | 职责 | exported 符号 | 测试 ID 前缀 |
|---|------|------|----------------|---------------|
| 1 | `packages/adapter-sdk/src/superteam_a2a/adapter/__init__.py` | public API 入口 | 13 符号（见 §1.2） | SDK-EXPORT-001 |
| 2 | `packages/adapter-sdk/src/superteam_a2a/adapter/_internals.py` | 内部 helper + 测试夹具 | `_load_framework`, `_make_test_card` | SDK-INT-001~003 |
| 3 | `packages/adapter-sdk/src/superteam_a2a/adapter/protocol.py` | FrameworkAdapter Protocol + AgentCardConverter Protocol + 7 错误类 | `FrameworkAdapter`, `AgentCardConverter`, `AdapterError` × 7 | SDK-PROT-001~012 |
| 4 | `packages/adapter-sdk/src/superteam_a2a/adapter/models.py` | Pydantic v2 AgentSpec / AgentCard / AdapterConfig | `AgentSpec`, `AgentCard`, `AdapterConfig` | SDK-MOD-001~008 |
| 5 | `packages/adapter-sdk/src/superteam_a2a/adapter/loader.py` | 6 framework 动态加载 + entry_points 解析 | `load_framework`, `list_frameworks` | SDK-LOAD-001~006 |
| 6 | `packages/adapter-sdk/src/superteam_a2a/adapter/converter.py` | AgentCard 转换逻辑 + 字段映射 | `convert_agent_card`, `validate_agent_card` | SDK-CONV-001~010 |
| 7 | `packages/adapter-sdk/src/superteam_a2a/adapter/config.py` | 4 层配置优先级合并（CRD > env > sidecar file > defaults） | `merge_config`, `load_config` | SDK-CFG-001~008 |
| 8 | `packages/adapter-sdk/src/superteam_a2a/adapter/errors.py` | 7 错误码 enum + Tenacity 5 类策略映射 | `AdapterErrorCode` enum, error mapping | SDK-ERR-001~009 |
| 9 | `packages/adapter-sdk/src/superteam_a2a/adapter/retry.py` | Tenacity 5 类策略 + structlog 错误日志 | `retry_strategy`, `is_retryable` | SDK-RTY-001~006 |
| 10 | `packages/adapter-sdk/src/superteam_a2a/adapter/observability.py` | 6 框架独立 metrics + structlog 8 字段 + OTel | `MetricsRegistry`, `log_adapter_event` | SDK-OBS-001~008 |
| 11 | `packages/adapter-sdk/src/superteam_a2a/adapter/version.py` | 6 framework 版本兼容矩阵 + 升级策略 | `VERSION_MATRIX`, `check_version` | SDK-VER-001~004 |

#### 1.3.2 6 framework adapter 子包总览（每个子包 ~3-4 文件 = 22 文件）

| # | 框架 | 子包路径 | 文件清单 | 引用 L3-2 资源 | 测试 ID 前缀 |
|---|------|----------|----------|----------------|---------------|
| 12 | **LangChain** | `packages/adapter-langchain/src/superteam_a2a/adapter_langchain/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | LC-A-* / LC-C-* / LC-E-* |
| 13 | **AutoGen** | `packages/adapter-autogen/src/superteam_a2a/adapter_autogen/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | AG-A-* / AG-C-* / AG-E-* |
| 14 | **CrewAI** | `packages/adapter-crewai/src/superteam_a2a/adapter_crewai/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | CR-A-* / CR-C-* / CR-E-* |
| 15 | **Semantic Kernel** | `packages/adapter-sk/src/superteam_a2a/adapter_sk/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | SK-A-* / SK-C-* / SK-E-* |
| 16 | **Strands** | `packages/adapter-strands/src/superteam_a2a/adapter_strands/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | ST-A-* / ST-C-* / ST-E-* |
| 17 | **Smolagents** | `packages/adapter-smolagents/src/superteam_a2a/adapter_smolagents/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | SM-A-* / SM-C-* / SM-E-* |

**6 framework 共同契约**（每个 framework adapter 必须实现）：

```python
# 6 framework 共用的 Protocol 形态（具体由各 framework 适配）
class FrameworkAdapter(Protocol):
    """Framework Adapter 协议（typing.Protocol + @runtime_checkable）"""
    framework_name: str  # "langchain" / "autogen" / "crewai" / "sk" / "strands" / "smolagents"
    framework_version: str  # "0.2.0" 形式
    
    async def load_agent(self, spec: AgentSpec) -> Any:
        """从 AgentSpec 加载 framework 特定 Agent 对象"""
        ...
    
    async def to_agent_card(self, agent: Any) -> AgentCard:
        """framework Agent → A2A AgentCard 转换"""
        ...
    
    async def from_agent_card(self, card: AgentCard) -> AgentSpec:
        """A2A AgentCard → AgentSpec 反向转换"""
        ...
    
    async def invoke(self, agent: Any, message: Message) -> Task:
        """framework Agent 执行 A2A Message"""
        ...
    
    async def health_check(self) -> bool:
        """framework 运行时健康检查"""
        ...
```

#### 1.3.3 22 顶层测试文件（镜像规则 · `test_*.py` 1:1 对应 src 文件）

- 11 文件 SDK → 11 `tests/unit/adapter-sdk/test_<file>.py`
- 6 framework × 3 adapter 文件 = 18 `tests/unit/adapters/test_<framework>_<file>.py` + 4 `tests/integration/framework/test_<framework>_e2e.py`（E2E 仅 6 framework 共享 4 集成测试，避免子包级别 E2E 爆炸）

**合计 11 + 22 + 顶层测试 = 39 文件级契约 + ~50 顶层测试 = ~89 文件级落地点**（不含工程骨架文件）。

#### 1.3.4 与 L3-1 / L3-2 文件级规模对照

| 维度 | L3-1 Operator Core | L3-2 A2A Core | **L3-3 Adapter SDK** |
|------|-------------------:|---------------:|---------------------:|
| Python 实现文件 | 70 | 30 | **11 SDK + 22 framework = 33** |
| 顶层测试文件 | 50 | 30 | ~50 |
| Helm 模板 | 9 | 9 | 0（Adapter SDK 不直接交付 Helm chart；6 framework 各自 HELM-006~010 在 §11 引用） |
| 工程资产 | 25 | 0 | 0（复用 L3-1 工程资产） |
| 文件级契约总数 | 162 | 69 | **~89** |
| 测试 ID | 277 | 276 | **~159**（继承 L2-3 + 6 框架独立） |
| 公开 Protocol/Class | 36 | 36 | **9**（4 Protocol + 3 Model + 7 Error） |
| ClusterRole apiGroups | 7 | 0 | 0（无 K8s API 依赖） |
| 开放问题 | 25 | 24 | **15**（L2-3 继承 10 + 5 Spec 新增） |

L3-3 文件级规模**显著小于 L3-1 / L3-2**，但仍需 ~30-40KB / ~800-1000 行的骨架 + 后续补完章节（§3-§10 + 附录 A 完整版 + 附录 B 5 子表）。

### 1.4 关键不变量（5 项 · 任意修改必须走 ADR）

| 不变量 | 强制来源 | 落地位置 |
|--------|----------|----------|
| 6 framework 名称不变（`langchain` / `autogen` / `crewai` / `sk` / `strands` / `smolagents`） | L2-3 §3.1 + L1 §4.3 + ADR-0005 | §1.3.2 表格 + 6 framework `adapter.py` 文件 + §3.2 `FrameworkName` Literal |
| 7 AdapterError 子类继承关系 | L2-3 §3.3 + L3-2 §10 错误码 | `errors.py` + 测试 SDK-ERR-001~009 |
| 4 层配置优先级 CRD > env > sidecar file > defaults | L2-3 §3.2 + ADR-0005 §6.5 | `config.py` + 测试 SDK-CFG-001~008 |
| 5 类 Tenacity 策略（`retry_network` / `retry_timeout` / `retry_5xx` / `retry_429` / `no_retry_4xx`） | L2-3 §6.4 + 宪法 §15.5 | `retry.py` + 测试 SDK-RTY-001~006 |
| A2A wire 复用 L3-2（不重写） | ADR-0005 §3.3 + §13.6 | `protocol.py` + `converter.py` import L3-2 `from a2a import AgentCard, Message` |

---

## 2. Python 包结构（基于 L2-3 Design §3.1 落地）

### 2.1 uv workspace 布局

```
packages/
├── adapter-sdk/                             # C-3 Adapter SDK（独立 PyPI 包）
│   ├── pyproject.toml                       # SDK-VER-001 + TOOL-001
│   ├── README.md
│   ├── src/
│   │   └── superteam_a2a/
│   │       └── adapter/                     # 11 文件 SDK 主清单
│   │           ├── __init__.py              # public API 入口
│   │           ├── _internals.py
│   │           ├── protocol.py              # FrameworkAdapter + AgentCardConverter
│   │           ├── models.py                # Pydantic v2
│   │           ├── loader.py                # 6 framework 动态加载
│   │           ├── converter.py             # AgentCard 转换
│   │           ├── config.py                # 4 层配置优先级
│   │           ├── errors.py                # 7 错误码
│   │           ├── retry.py                 # Tenacity 5 类策略
│   │           ├── observability.py         # 6 framework metrics
│   │           └── version.py               # 版本兼容矩阵
│   └── tests/
│       ├── unit/
│       │   └── adapter-sdk/
│       │       ├── test_protocol.py         # SDK-PROT-001~012
│       │       ├── test_models.py           # SDK-MOD-001~008
│       │       ├── test_loader.py           # SDK-LOAD-001~006
│       │       ├── test_converter.py        # SDK-CONV-001~010
│       │       ├── test_config.py           # SDK-CFG-001~008
│       │       ├── test_errors.py           # SDK-ERR-001~009
│       │       ├── test_retry.py            # SDK-RTY-001~006
│       │       ├── test_observability.py    # SDK-OBS-001~008
│       │       └── test_version.py          # SDK-VER-001~004
│       └── integration/
│           └── adapter-sdk/
│               ├── test_6framework_load.py  # SDK-INT-LOAD-001
│               └── test_agent_card_convert.py  # SDK-INT-CONV-001
│
├── adapter-langchain/                       # 6 framework 各自独立仓库
├── adapter-autogen/
├── adapter-crewai/
├── adapter-sk/
├── adapter-strands/
└── adapter-smolagents/
```

### 2.2 6 framework 子包共同结构（每个 framework 独立 PyPI 包）

```
packages/adapter-{framework}/
├── pyproject.toml                           # 依赖 adapter-sdk（>=0.2.0,<0.3.0）
├── README.md
├── src/
│   └── superteam_a2a/
│       └── adapter_{framework}/
│           ├── __init__.py                   # 导出 FrameworkAdapter 实现
│           ├── adapter.py                    # FrameworkAdapter 实现（具体框架）
│           ├── converter.py                  # AgentCard 转换（框架特定字段映射）
│           └── errors.py                     # 框架特定错误映射（→ SDK AdapterError）
└── tests/
    ├── unit/
    │   └── adapter_{framework}/
    │       ├── test_adapter.py               # {XX}-A-*
    │       ├── test_converter.py             # {XX}-C-*
    │       └── test_errors.py                # {XX}-E-*
    └── integration/
        └── framework/
            └── test_{framework}_e2e.py       # 6 framework 各自 1 个 E2E
```

### 2.3 13 边界规则（继承 L2-3 Spec §2.2 + ADR-0005 §13.2 新增 4 项）

| # | 边界规则 | 落地位置 |
|---|----------|----------|
| 1 | Adapter SDK 不依赖 K8s API | `pyproject.toml` 不依赖 `kubernetes` / `kopf` |
| 2 | Adapter SDK 不依赖 framework 本身（仅依赖 framework 抽象 + typing.Protocol） | `protocol.py` 全部为 `Protocol`/`@runtime_checkable` |
| 3 | Adapter SDK 不实现 A2A wire（仅调用 L3-2 a2a-core） | `converter.py` import `from a2a import AgentCard` |
| 4 | Adapter SDK 不实现 Knowledge/Memory 业务语义 | `models.py` 不引用 knowledge/memory 任何类 |
| 5 | 6 framework adapter 各自独立 PyPI 包（不互相 import） | `pyproject.toml` 不 deps 其他 5 framework |
| 6 | 6 framework adapter 通过 entry_points 注册到 SDK | `pyproject.toml [project.entry-points."superteam_a2a.frameworks"]` |
| 7 | 配置优先级 CRD > env > sidecar file > defaults 严格 | `config.py` merge 函数按顺序 |
| 8 | 5 类 Tenacity 策略不可新增 | `retry.py` + 测试 SDK-RTY-001 严格枚举 |
| 9 | 7 AdapterError 子类不可新增 | `errors.py` + 测试 SDK-ERR-001 严格枚举 |
| 10 | A2A wire contract 不可变（必须通过 L3-2 SDK） | `converter.py` 引用 L3-2 不直接构造 dict |
| 11 | `__init__.py` 仅导出 `__all__`（其他符号下划线前缀） | 11 文件 SDK + 6 framework `__init__.py` |
| 12 | 6 framework 名称字符串不可变（typing.Literal 强制） | `protocol.py` `framework_name: Literal["langchain", ...]` |
| 13 | 版本兼容矩阵 6 framework 独立 | `version.py` `VERSION_MATRIX` 不可热改 |

### 2.4 6 框架独立 metrics（约 6 项 · 与 L3-2 15 指标并列）

| 指标名 | 类型 | labels | 触发时机 |
|--------|------|--------|----------|
| `superteam_adapter_load_total{framework="<name>",result}` | Counter | framework, result | `load_agent()` 调用 |
| `superteam_adapter_convert_duration_seconds{framework="<name>",direction}` | Histogram | framework, direction | `to_agent_card` / `from_agent_card` |
| `superteam_adapter_invoke_total{framework="<name>",result}` | Counter | framework, result | `invoke()` 调用 |
| `superteam_adapter_invoke_duration_seconds{framework="<name>"}` | Histogram | framework | `invoke()` 耗时 |
| `superteam_adapter_active{framework="<name>"}` | Gauge | framework | 当前活跃 Agent 数 |
| `superteam_adapter_health_check_total{framework="<name>",result}` | Counter | framework, result | `health_check()` 调用 |

**约束**（与 L3-2 §9 一致）：label `result` 仅 4 值（`success` / `error` / `retry` / `rejected`）；Histogram 默认桶 + 自定义桶必须显式声明；测试用 `MetricsRegistry(prefix="test_")` 隔离。

---

## 3. FrameworkAdapter Protocol 文件级契约（typing.Protocol + 5 生命周期方法）

### 3.1 设计原则（继承 L2-3 Spec §3.1 + ADR-0005 §3.3）

- **duck typing 而非显式继承**：6 framework adapter 通过 `typing.Protocol` + `@runtime_checkable` 描述形态，**不强制基类**（每个 framework 已有自己的基类，不能让 SDK 强制继承）。
- **5 生命周期方法必需顺序**：load_agent → to_agent_card → invoke → from_agent_card → health_check（详见 §3.4）。
- **6 framework 名称字符串不可变**：`framework_name: Literal["langchain", "autogen", "crewai", "sk", "strands", "smolagents"]`（typing.Literal 强制，运行时 `isinstance` 校验）。
- **框架版本兼容矩阵**：`framework_version: str` 格式 `X.Y.Z` semver；`VERSION_MATRIX` 6 framework 各自独立（详见 §3.5）。
- **A2A 协议层薄封装**：`Protocol` 方法签名只引用 L3-2 提供的 `AgentCard` / `Message` / `Task` / `Artifact`，不定义新 wire 字段。

### 3.2 `protocol.py` 文件级契约（466 行 · 核心 SDK 代码）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/protocol.py
# Copyright 2026 superteam-a2a authors. Apache-2.0 license.
"""FrameworkAdapter Protocol + AgentCardConverter Protocol + 7 错误类。

基于 typing.Protocol + @runtime_checkable；不强制基类继承。
6 framework adapter 必须实现 FrameworkAdapter 协议的全部 5 生命周期方法。
A2A 协议层引用 L3-2 a2a-core，不重新定义 wire contract。
"""

from __future__ import annotations

from typing import (
    Any,
    Literal,
    Protocol,
    runtime_checkable,
)

from a2a import AgentCard, Message, Task, Artifact  # L3-2 a2a-core
from pydantic import BaseModel, Field, ConfigDict

from .models import AgentSpec, AdapterConfig
from .errors import AdapterError


FrameworkName = Literal[
    "langchain",
    "autogen",
    "crewai",
    "sk",
    "strands",
    "smolagents",
]


@runtime_checkable
class FrameworkAdapter(Protocol):
    """Framework Adapter 协议（typing.Protocol + @runtime_checkable）。
    
    6 framework adapter（LangChain / AutoGen / CrewAI / SK / Strands / Smolagents）
    必须实现本协议的全部 5 生命周期方法。SDK 不强制基类继承；通过 duck typing
    + isinstance(adapter, FrameworkAdapter) 运行时校验。
    """
    
    framework_name: FrameworkName
    framework_version: str  # semver X.Y.Z
    
    async def load_agent(self, spec: AgentSpec) -> Any:
        """从 AgentSpec 加载 framework 特定 Agent 对象。
        
        Args:
            spec: AgentSpec Pydantic v2 模型（model + config + tools）
        
        Returns:
            framework 特定的 Agent 对象（如 LangChain AgentExecutor / AutoGen ConversableAgent
            / CrewAI Crew / SK Kernel / Strands Agent / Smolagents CodeAgent）
        
        Raises:
            AdapterConfigError: spec 字段不合法
            AdapterFrameworkError: framework 加载失败
        """
        ...
    
    async def to_agent_card(self, agent: Any) -> AgentCard:
        """framework Agent → A2A AgentCard 转换。
        
        Args:
            agent: framework 特定 Agent 对象（load_agent 返回值）
        
        Returns:
            A2A AgentCard（url / name / description / capabilities / skills / version）
        
        Raises:
            AdapterFrameworkError: 转换失败
        """
        ...
    
    async def from_agent_card(self, card: AgentCard) -> AgentSpec:
        """A2A AgentCard → AgentSpec 反向转换（用于 A2A Discovery 接收）。
        
        Args:
            card: A2A AgentCard（来自 .well-known/agent.json 或消息）
        
        Returns:
            AgentSpec Pydantic v2 模型
        
        Raises:
            AdapterConfigError: card 字段缺失或不合法
        """
        ...
    
    async def invoke(self, agent: Any, message: Message) -> Task:
        """framework Agent 执行 A2A Message。
        
        Args:
            agent: framework 特定 Agent 对象
            message: A2A Message（role + parts + metadata）
        
        Returns:
            A2A Task（id + context_id + status + artifacts）
        
        Raises:
            AdapterRetryableError: 网络/超时/5xx（Tenacity 重试策略覆盖）
            AdapterNonRetryableError: 4xx（不重试）
            AdapterPermanentError: 业务错误（不容忍）
            AdapterTimeoutError: invoke 超时（> adapterConfig.timeoutSeconds）
        """
        ...
    
    async def health_check(self) -> bool:
        """framework 运行时健康检查（无参数）。
        
        Returns:
            True: framework + 必要依赖可用
            False: 任何依赖缺失（env var / API key / model 文件）
        """
        ...


@runtime_checkable
class AgentCardConverter(Protocol):
    """AgentCard 转换器 Protocol（用于 framework 字段映射）。
    
    6 framework 各自实现 AgentCardConverter，根据 framework 特定字段映射：
    - LangChain: tool name → AgentCard skill
    - AutoGen: function_call → AgentCard tool
    - CrewAI: agent role → AgentCard skill
    - SK: function_call → AgentCard tool
    - Strands: tool spec → AgentCard skill
    - Smolagents: tool class → AgentCard skill
    """
    
    @staticmethod
    def framework_to_card_skill(framework_field: Any) -> dict[str, Any]:
        """framework 特定字段 → AgentCard skill dict。
        
        Returns:
            {"id": str, "name": str, "description": str, "tags": list[str]}
        """
        ...
    
    @staticmethod
    def card_skill_to_framework(card_skill: dict[str, Any]) -> Any:
        """AgentCard skill dict → framework 特定字段。
        
        Returns:
            framework 特定 tool 描述（如 LangChain Tool 对象）
        """
        ...
```

### 3.3 5 生命周期方法时序图（与 L2-3 Spec §3.4 同步）

```
Operator Core (L3-1)                  Adapter SDK (L3-3)                  Framework (e.g. LangChain)
      │                                      │                                       │
      │ 1. resolve_framework(name)            │                                       │
      ├─────────────────────────────────────►│                                       │
      │                                      │ entry_points 解析                      │
      │                                      │ load_adapter_class()                  │
      │◄─────────────────────────────────────┤                                       │
      │ FrameworkAdapter instance            │                                       │
      │                                      │                                       │
      │ 2. load_agent(AgentSpec)              │                                       │
      ├─────────────────────────────────────►│                                       │
      │                                      │ adapter.load_agent(spec)              │
      │                                      ├──────────────────────────────────────►│
      │                                      │                                       │ 加载模型
      │                                      │                                       │ 初始化 tools
      │                                      │                                       │
      │                                      │◄──────────────────────────────────────┤
      │                                      │ agent 对象                            │
      │◄─────────────────────────────────────┤                                       │
      │ framework Agent                       │                                       │
      │                                      │                                       │
      │ 3. to_agent_card(agent)               │                                       │
      ├─────────────────────────────────────►│                                       │
      │                                      │ adapter.to_agent_card(agent)          │
      │                                      │   → AgentCardConverter 字段映射         │
      │◄─────────────────────────────────────┤                                       │
      │ AgentCard (A2A)                       │                                       │
      │                                      │                                       │
      │ 4. invoke(agent, Message)              │                                       │
      ├─────────────────────────────────────►│                                       │
      │                                      │ adapter.invoke(agent, msg)            │
      │                                      │   → Tenacity 5 类策略                  │
      │                                      ├──────────────────────────────────────►│
      │                                      │  ◄─ retry on AdapterRetryableError    │
      │                                      │                                       │ 调用模型
      │                                      │                                       │ 工具调用
      │                                      │◄──────────────────────────────────────┤
      │                                      │ Task 对象                             │
      │◄─────────────────────────────────────┤                                       │
      │ Task (A2A)                            │                                       │
      │                                      │                                       │
      │ 5. health_check() (周期性)             │                                       │
      ├─────────────────────────────────────►│                                       │
      │                                      │ adapter.health_check()                │
      │                                      │   → 依赖检查（API key / 模型）            │
      │◄─────────────────────────────────────┤                                       │
      │ True / False                          │                                       │
```

### 3.4 5 生命周期方法测试 ID 矩阵（SDK-PROT-001~012）

| 测试 ID | 测试名 | 断言 | 对应文件 |
|---------|--------|------|----------|
| SDK-PROT-001 | test_framework_adapter_protocol_runtime_checkable | `isinstance(LangChainAdapter(), FrameworkAdapter) is True` | `tests/unit/adapter-sdk/test_protocol.py` |
| SDK-PROT-002 | test_framework_adapter_protocol_missing_method_fails | 自定义类只实现 `load_agent` → `isinstance` 返回 False | `tests/unit/adapter-sdk/test_protocol.py` |
| SDK-PROT-003 | test_framework_adapter_protocol_framework_name_literal | `framework_name = "invalid"` 阻止；FrameworkName 6 值枚举 | `tests/unit/adapter-sdk/test_protocol.py` |
| SDK-PROT-004 | test_framework_adapter_protocol_framework_version_semver | `framework_version = "invalid"` 阻止；semver 三段式 | `tests/unit/adapter-sdk/test_protocol.py` |
| SDK-PROT-005 | test_load_agent_returns_framework_specific_object | LangChainAdapter.load_agent 返回 AgentExecutor | `tests/unit/adapter-sdk/test_protocol.py` |
| SDK-PROT-006 | test_to_agent_card_returns_a2a_card | 返回 L3-2 AgentCard，wire 字段不重写 | `tests/unit/adapter-sdk/test_protocol.py` |
| SDK-PROT-007 | test_from_agent_card_returns_agent_spec | card → AgentSpec 字段映射（保留所有 wire 字段） | `tests/unit/adapter-sdk/test_protocol.py` |
| SDK-PROT-008 | test_invoke_returns_task | 返回 L3-2 Task，5 类 Tenacity 策略覆盖 | `tests/unit/adapter-sdk/test_protocol.py` |
| SDK-PROT-009 | test_invoke_timeout_raises_adapter_timeout_error | 超时 → AdapterTimeoutError（> adapterConfig.timeoutSeconds） | `tests/unit/adapter-sdk/test_protocol.py` |
| SDK-PROT-010 | test_invoke_retryable_error_triggers_retry | 网络错误 → Tenacity 重试 3 次 → 失败抛 RetryableError | `tests/unit/adapter-sdk/test_protocol.py` |
| SDK-PROT-011 | test_invoke_non_retryable_error_no_retry | 4xx → 不重试 → 抛 NonRetryableError | `tests/unit/adapter-sdk/test_protocol.py` |
| SDK-PROT-012 | test_health_check_returns_bool | True 表示依赖可用；False 表示关键依赖缺失 | `tests/unit/adapter-sdk/test_protocol.py` |

### 3.5 6 framework 版本兼容矩阵（version.py 相关 · SDK-VER-001~004）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/version.py
# 6 framework 各自版本范围与升级策略（不热改）
VERSION_MATRIX: dict[str, AdapterVersionSpec] = {
    "langchain": AdapterVersionSpec(
        min_version="0.2.0",
        max_version="0.3.0",
        upgrade_strategy="minor_within_0_2_x",
        breaking_changes_url="https://python.langchain.com/docs/versions/v0_2/",
    ),
    "autogen": AdapterVersionSpec(
        min_version="0.4.0",
        max_version="1.0.0",
        upgrade_strategy="minor_within_0_4_x",
        breaking_changes_url="https://microsoft.github.io/autogen/dev/",
    ),
    "crewai": AdapterVersionSpec(
        min_version="0.80.0",
        max_version="0.100.0",
        upgrade_strategy="minor_within_0_80_x",
        breaking_changes_url="https://docs.crewai.com/changelog",
    ),
    "sk": AdapterVersionSpec(
        min_version="1.30.0",
        max_version="1.40.0",
        upgrade_strategy="minor_within_1_30_x",
        breaking_changes_url="https://learn.microsoft.com/en-us/semantic-kernel/",
    ),
    "strands": AdapterVersionSpec(
        min_version="0.1.0",
        max_version="0.3.0",
        upgrade_strategy="minor_within_0_1_x",
        breaking_changes_url="https://github.com/strands-agents/sdk-python",
    ),
    "smolagents": AdapterVersionSpec(
        min_version="1.10.0",
        max_version="2.0.0",
        upgrade_strategy="minor_within_1_10_x",
        breaking_changes_url="https://huggingface.co/docs/smolagents/",
    ),
}
```

**测试 ID**：
- SDK-VER-001：6 framework 名称 Literal 校验（与 §3.2 #3 同步）
- SDK-VER-002：semver 范围解析（X.Y.Z 格式）
- SDK-VER-003：升级策略（4 种 `minor_within_*` / `major_within_*` 枚举）
- SDK-VER-004：breaking_changes_url 必填（None 拒绝）

### 3.6 `_internals.py` 文件级契约（154 行 · 内部 helper + 测试夹具）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/_internals.py
# 内部 helper + 测试夹具；不进入 __all__；仅限 L3 内部 + 6 framework adapter 各自测试使用

import importlib
from typing import Any

from .models import AdapterConfig, AgentSpec
from .protocol import FrameworkAdapter, FrameworkName


def _load_framework(name: FrameworkName, config: AdapterConfig) -> FrameworkAdapter:
    """通过 entry_points 加载 6 framework 各自 PyPI 包。
    
    Returns:
        FrameworkAdapter 实例（duck typing 校验）
    
    Raises:
        AdapterConfigError: framework 名称不在 6 值枚举
        AdapterFrameworkError: entry_points 未注册 / 加载失败
    """
    ...


def _make_test_card(framework_name: FrameworkName) -> AgentSpec:
    """生成 6 framework 各自的测试 AgentSpec（fixture）。"""
    ...


def _check_protocol_compliance(obj: Any) -> bool:
    """运行时 duck typing 校验（5 生命周期方法 + 2 属性）。"""
    ...
```

**测试 ID**：SDK-INT-001（_load_framework entry_points 解析）/ SDK-INT-002（_make_test_card 6 framework fixture）/ SDK-INT-003（_check_protocol_compliance 7 字段校验）

---

## 4. AgentCardConverter + Pydantic v2 模型文件级契约

### 4.1 `models.py` 文件级契约（287 行 · Pydantic v2 基类）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/models.py
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict, SecretStr, field_validator, model_validator


class AgentSpec(BaseModel):
    """Agent 规格（Pydantic v2）。"""
    
    model_config = ConfigDict(
        extra="forbid",  # 严格 wire shape
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    
    name: str = Field(min_length=1, max_length=253, pattern=r"^[a-z0-9-]+$")
    framework: Literal["langchain", "autogen", "crewai", "sk", "strands", "smolagents"]
    model: str = Field(min_length=1, max_length=512)  # model name
    config: dict[str, Any] = Field(default_factory=dict)
    tools: list[ToolSpec] = Field(default_factory=list, max_length=50)
    system_prompt: str | None = Field(default=None, max_length=4096)
    memory_ref: str | None = Field(default=None)  # 引用 Memory CRD（L2-4）
    knowledge_ref: str | None = Field(default=None)  # 引用 KnowledgeItem CRD
    
    @field_validator("model")
    @classmethod
    def _validate_model_format(cls, v: str) -> str:
        """model 格式校验（framework 特定格式由各 framework adapter 校验）。"""
        if "/" in v and v.count("/") > 2:
            raise ValueError("model 格式不合法")
        return v


class ToolSpec(BaseModel):
    """Tool 规格（AgentSpec.tools 元素）。"""
    
    model_config = ConfigDict(extra="forbid")
    
    name: str = Field(min_length=1, max_length=63, pattern=r"^[a-zA-Z0-9_-]+$")
    description: str = Field(min_length=1, max_length=512)
    parameters: dict[str, Any] = Field(default_factory=dict)  # JSON Schema
    framework_specific: dict[str, Any] = Field(default_factory=dict)


class AgentCard(BaseModel):
    """A2A AgentCard（Pydantic v2 重导出 L3-2 a2a.AgentCard）。"""
    
    # 不重写 L3-2 的 AgentCard 字段；仅作为 SDK 入口导出
    url: str
    name: str
    description: str
    version: str
    capabilities: dict[str, bool]
    skills: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    default_input_modes: list[str] = Field(default_factory=lambda: ["text"])
    default_output_modes: list[str] = Field(default_factory=lambda: ["text"])


class AdapterConfig(BaseModel):
    """Adapter 配置（4 层优先级合并输入）。"""
    
    model_config = ConfigDict(extra="forbid")
    
    timeout_seconds: int = Field(default=120, ge=1, le=3600)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_strategy: Literal["retry_network", "retry_timeout", "retry_5xx", "retry_429", "no_retry_4xx"] = "retry_network"
    sensitive_fields: list[str] = Field(default_factory=lambda: ["api_key", "token", "password"])
    observability_labels: dict[str, str] = Field(default_factory=dict)
    
    @model_validator(mode="after")
    def _validate_retry_strategy(self) -> "AdapterConfig":
        """retry_strategy 5 值枚举 + 与 max_retries 协同校验。"""
        if self.retry_strategy == "no_retry_4xx" and self.max_retries > 0:
            raise ValueError("no_retry_4xx 策略下 max_retries 必须为 0")
        return self
```

### 4.2 `converter.py` 文件级契约（322 行 · AgentCard 转换 + 6 框架字段映射）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/converter.py
from __future__ import annotations

from typing import Any

from a2a import AgentCard, Message, Task  # L3-2 a2a-core
from pydantic import ValidationError

from .models import AgentSpec, ToolSpec, AdapterConfig
from .errors import AdapterConfigError, AdapterFrameworkError


async def convert_agent_card(
    spec: AgentSpec,
    config: AdapterConfig,
) -> AgentCard:
    """AgentSpec → A2A AgentCard 转换。
    
    6 framework 字段映射由各自 converter 实现（通过 AgentCardConverter Protocol）；
    本函数为通用转换逻辑（不含 framework 特定字段）。
    
    Raises:
        AdapterConfigError: spec 字段不合法
        AdapterFrameworkError: 转换失败
    """
    ...


async def validate_agent_card(card: AgentCard) -> None:
    """AgentCard 字段 wire 校验（与 L3-2 AgentCard 严格一致）。
    
    Raises:
        AdapterConfigError: 字段缺失或格式不合法
    """
    ...


def _tool_spec_to_skill(tool: ToolSpec) -> dict[str, Any]:
    """ToolSpec → AgentCard skill dict 通用映射（不含 framework 特定字段）。"""
    ...


def _skill_to_tool_spec(skill: dict[str, Any]) -> ToolSpec:
    """AgentCard skill dict → ToolSpec 反向映射。"""
    ...
```

### 4.3 测试 ID 矩阵（SDK-MOD-001~008 + SDK-CONV-001~010）

| 类别 | 测试 ID | 测试名 | 断言 |
|------|---------|--------|------|
| **AgentSpec** | SDK-MOD-001 | test_agent_spec_strict_wire_shape | extra="forbid" 拒绝未知字段 |
| **AgentSpec** | SDK-MOD-002 | test_agent_spec_name_pattern | K8s resource name 格式（regex） |
| **AgentSpec** | SDK-MOD-003 | test_agent_spec_framework_literal | 6 framework 名称 Literal 校验 |
| **AgentSpec** | SDK-MOD-004 | test_agent_spec_tools_max_length | tools 最多 50 个 |
| **AgentSpec** | SDK-MOD-005 | test_agent_spec_memory_knowledge_refs | 引用 Memory/Knowledge CRD 字段 |
| **AdapterConfig** | SDK-MOD-006 | test_adapter_config_timeout_range | timeout_seconds ∈ [1, 3600] |
| **AdapterConfig** | SDK-MOD-007 | test_adapter_config_retry_strategy_literal | 5 类 retry 策略枚举 |
| **AdapterConfig** | SDK-MOD-008 | test_adapter_config_no_retry_4xx_validation | no_retry_4xx 必须 max_retries=0 |
| **converter** | SDK-CONV-001 | test_convert_agent_card_basic | AgentSpec（最小字段）→ AgentCard |
| **converter** | SDK-CONV-002 | test_convert_agent_card_with_tools | tools 字段映射到 skills |
| **converter** | SDK-CONV-003 | test_convert_agent_card_framework_specific | 6 framework 各自字段映射（LangChain Tool → skill） |
| **converter** | SDK-CONV-004 | test_convert_agent_card_memory_knowledge_refs | 引用字段保留 |
| **converter** | SDK-CONV-005 | test_validate_agent_card_wire_consistency | 与 L3-2 AgentCard 字段一一对应 |
| **converter** | SDK-CONV-006 | test_tool_spec_to_skill_lossless | ToolSpec → skill dict 字段无损 |
| **converter** | SDK-CONV-007 | test_skill_to_tool_spec_lossless | skill dict → ToolSpec 字段无损 |
| **converter** | SDK-CONV-008 | test_convert_agent_card_invalid_config_raises | AdapterConfigError 抛出 |
| **converter** | SDK-CONV-009 | test_convert_agent_card_max_skill_length | 50 skill 边界 |
| **converter** | SDK-CONV-010 | test_validate_agent_card_strict | 任何字段缺失或格式错误 → AdapterConfigError |

### 4.4 6 framework 字段映射矩阵（AgentCardConverter Protocol 实现）

| Framework | tool → skill 字段映射 | skill → tool 字段映射 | framework_specific 字段 |
|-----------|----------------------|----------------------|------------------------|
| **LangChain** | `tool.name` → `skill.id` / `tool.description` → `skill.description` | `skill.id` → `Tool.name` / `parameters` → `Tool.args_schema` | `tool.return_direct` / `tool.metadata` |
| **AutoGen** | `function_call.name` → `skill.id` / `description` → `skill.description` | `skill.id` → `Function name` | `function_call.parameters` |
| **CrewAI** | `agent.role` → `skill.id` / `goal` → `skill.description` | `skill.id` → `Agent role` | `agent.backstory` / `agent.tools` |
| **SK** | `function_call.name` → `skill.id` / `description` → `skill.description` | `skill.id` → `Function name` | `kernel_function.parameters` |
| **Strands** | `tool.tool_spec.name` → `skill.id` / `description` → `skill.description` | `skill.id` → `Tool name` | `tool.tool_spec.input_schema` |
| **Smolagents** | `tool_class.name` → `skill.id` / `description` → `skill.description` | `skill.id` → `ToolClass name` | `tool_class.inputs` |

---

## 5. 6 framework adapter 子包文件级契约（22 文件）

### 5.1 共同契约（每个 framework 必须实现）

```python
# 6 framework 共同 __init__.py 形态
# packages/adapter-{framework}/src/superteam_a2a/adapter_{framework}/__init__.py

from .adapter import {Framework}Adapter
from .converter import {Framework}AgentCardConverter
from .errors import {Framework}ErrorMapper

__all__ = [
    "{Framework}Adapter",
    "{Framework}AgentCardConverter",
    "{Framework}ErrorMapper",
]


# pyproject.toml entry_points 注册
[project.entry-points."superteam_a2a.frameworks"]
{framework_name} = "superteam_a2a.adapter_{framework}:{Framework}Adapter"
```

### 5.2 LangChain adapter 子包（4 文件 · 6 framework 中最长）

```python
# packages/adapter-langchain/src/superteam_a2a/adapter_langchain/adapter.py
"""LangChain FrameworkAdapter 实现（AgentExecutor + Tool bindings）。"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models import BaseLanguageModel

from superteam_a2a.adapter import (
    FrameworkAdapter,
    AgentSpec,
    AgentCard,
    Message,
    Task,
    AdapterConfig,
    AdapterConfigError,
    AdapterFrameworkError,
)


class LangChainAdapter:
    """LangChain FrameworkAdapter 实现（不显式继承 FrameworkAdapter；duck typing）。
    
    framework_name = "langchain"
    framework_version 当前 = "0.2.0"（VERSION_MATRIX 同步）
    """
    
    framework_name: str = "langchain"
    framework_version: str = "0.2.0"
    
    def __init__(self, config: AdapterConfig):
        self.config = config
        self._llm: BaseLanguageModel | None = None
    
    async def load_agent(self, spec: AgentSpec) -> AgentExecutor:
        """从 AgentSpec 加载 LangChain AgentExecutor。
        
        关键步骤：
        1. 解析 spec.model → 创建 LLM（OpenAI / Anthropic / Bedrock 等）
        2. 解析 spec.tools → 加载 LangChain Tool 对象
        3. 解析 spec.system_prompt → 注入到 ReAct agent prompt
        4. create_react_agent + AgentExecutor
        """
        ...
    
    async def to_agent_card(self, agent: AgentExecutor) -> AgentCard:
        """AgentExecutor → AgentCard 转换。"""
        ...
    
    async def from_agent_card(self, card: AgentCard) -> AgentSpec:
        """AgentCard → AgentSpec 反向转换。"""
        ...
    
    async def invoke(self, agent: AgentExecutor, message: Message) -> Task:
        """通过 AgentExecutor.acall() 执行 A2A Message。"""
        ...
    
    async def health_check(self) -> bool:
        """检查 LLM API key + Tool 依赖。"""
        ...


# 运行时校验
assert isinstance(LangChainAdapter(AdapterConfig()), FrameworkAdapter), \
    "LangChainAdapter must satisfy FrameworkAdapter Protocol"
```

### 5.3 6 framework adapter 子包对照表（22 文件）

| # | 文件 | 路径 | 行数 | 关键依赖 |
|---|------|------|------|----------|
| 1 | LangChain `__init__.py` | `adapter-langchain/src/superteam_a2a/adapter_langchain/__init__.py` | 8 | SDK + framework |
| 2 | LangChain `adapter.py` | 同上 | ~250 | `langchain.core.agents` |
| 3 | LangChain `converter.py` | 同上 | ~180 | `langchain.tools` |
| 4 | LangChain `errors.py` | 同上 | ~80 | `langchain.exceptions` |
| 5 | AutoGen `__init__.py` | `adapter-autogen/src/superteam_a2a/adapter_autogen/__init__.py` | 8 | SDK + framework |
| 6 | AutoGen `adapter.py` | 同上 | ~240 | `autogen.ConversableAgent` |
| 7 | AutoGen `converter.py` | 同上 | ~170 | `autogen.function_utils` |
| 8 | AutoGen `errors.py` | 同上 | ~80 | `autogen.exceptions` |
| 9 | CrewAI `__init__.py` | `adapter-crewai/src/superteam_a2a/adapter_crewai/__init__.py` | 8 | SDK + framework |
| 10 | CrewAI `adapter.py` | 同上 | ~240 | `crewai.Crew` / `crewai.Agent` |
| 11 | CrewAI `converter.py` | 同上 | ~170 | `crewai.tools` |
| 12 | CrewAI `errors.py` | 同上 | ~80 | `crewai.exceptions` |
| 13 | SK `__init__.py` | `adapter-sk/src/superteam_a2a/adapter_sk/__init__.py` | 8 | SDK + framework |
| 14 | SK `adapter.py` | 同上 | ~240 | `semantic_kernel.Kernel` |
| 15 | SK `converter.py` | 同上 | ~170 | `semantic_kernel.functions` |
| 16 | SK `errors.py` | 同上 | ~80 | `semantic_kernel.exceptions` |
| 17 | Strands `__init__.py` | `adapter-strands/src/superteam_a2a/adapter_strands/__init__.py` | 8 | SDK + framework |
| 18 | Strands `adapter.py` | 同上 | ~240 | `strands.Agent` |
| 19 | Strands `converter.py` | 同上 | ~170 | `strands.tools` |
| 20 | Strands `errors.py` | 同上 | ~80 | `strands.exceptions` |
| 21 | Smolagents `__init__.py` | `adapter-smolagents/src/superteam_a2a/adapter_smolagents/__init__.py` | 8 | SDK + framework |
| 22 | Smolagents `adapter.py` | 同上 | ~240 | `smolagents.CodeAgent` |
| 23 | Smolagents `converter.py` | 同上 | ~170 | `smolagents.tools` |
| 24 | Smolagents `errors.py` | 同上 | ~80 | `smolagents.exceptions` |

**合计 24 文件 = 6 framework × 4 文件**（修正 §1.3 22 → 24）。

### 5.4 6 framework 测试 ID 矩阵（每 framework 至少 9 个 ID）

| Framework | adapter 测试 | converter 测试 | errors 测试 | 集成测试 |
|-----------|-------------|---------------|-------------|----------|
| LangChain | LC-A-001~005 | LC-C-001~003 | LC-E-001~003 | LC-IT-001 |
| AutoGen | AG-A-001~005 | AG-C-001~003 | AG-E-001~003 | AG-IT-001 |
| CrewAI | CR-A-001~005 | CR-C-001~003 | CR-E-001~003 | CR-IT-001 |
| Semantic Kernel | SK-A-001~005 | SK-C-001~003 | SK-E-001~003 | SK-IT-001 |
| Strands | ST-A-001~005 | ST-C-001~003 | ST-E-001~003 | ST-IT-001 |
| Smolagents | SM-A-001~005 | SM-C-001~003 | SM-E-001~003 | SM-IT-001 |

**合计 6 × (5 + 3 + 3 + 1) = 72 测试 ID**（§1.3 约 50 测试文件 → §9 完整版约 159 ID 中 72 来自 6 framework）。

### 5.5 6 framework 共同 error 映射（errors.py）

```python
# 6 framework 共同 error 映射形态
import {framework}.exceptions as fe

from superteam_a2a.adapter import (
    AdapterError,
    AdapterRetryableError,
    AdapterNonRetryableError,
    AdapterPermanentError,
    AdapterTimeoutError,
)

def map_framework_error(exc: Exception) -> AdapterError:
    """framework 特定异常 → AdapterError 子类映射。
    
    6 framework 各自实现；映射规则：
    - 网络错误 → AdapterRetryableError
    - 超时 → AdapterTimeoutError
    - 4xx（含 API 限流 429）→ AdapterNonRetryableError
    - 5xx → AdapterRetryableError
    - framework 业务错误 → AdapterPermanentError
    """
    ...
```

---

## 6. 4 层配置优先级 merge 函数 + 6 framework 动态加载

### 6.1 4 层配置优先级（继承 L2-3 Spec §3.2）

合并顺序（后者覆盖前者）：

1. **defaults**（SDK 内置兜底）
2. **sidecar file**（Mount 进来的 `/etc/superteam-a2a/adapter-config.yaml`）
3. **env**（K8s env 注入 `SUPERTEAM_ADAPTER_*` 前缀）
4. **CRD**（Agent CRD spec.adapter 配置）

merge 行为：CRD 字段缺失 → 降级到 env；env 字段缺失 → 降级到 sidecar file；sidecar file 字段缺失 → 降级到 defaults。每层覆盖只覆盖**显式**声明的字段，不引入新字段。

### 6.2 `config.py` 文件级契约（218 行 · 4 层优先级 merge）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/config.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import AdapterConfig
from .errors import AdapterConfigError


_DEFAULTS = AdapterConfig(
    timeout_seconds=120,
    max_retries=3,
    retry_strategy="retry_network",
    sensitive_fields=["api_key", "token", "password"],
    observability_labels={},
)


async def load_config(
    crd_config: dict[str, Any] | None = None,
    sidecar_file: Path = Path("/etc/superteam-a2a/adapter-config.yaml"),
) -> AdapterConfig:
    """4 层配置优先级合并（CRD > env > sidecar file > defaults）。
    
    Args:
        crd_config: Agent CRD spec.adapter 字段（已通过 Pydantic 校验）
        sidecar_file: sidecar 配置文件路径（默认 K8s 标准路径）
    
    Returns:
        AdapterConfig Pydantic v2 模型（4 层合并后）
    
    Raises:
        AdapterConfigError: 配置文件解析失败 / 字段校验失败
    """
    ...


def _load_sidecar_file(path: Path) -> dict[str, Any]:
    """sidecar YAML 文件 → dict；文件不存在返回 {}。"""
    ...


def _load_env() -> dict[str, Any]:
    """SUPERTEAM_ADAPTER_* → dict（如 SUPERTEAM_ADAPTER_TIMEOUT_SECONDS=300 → {"timeout_seconds": 300}）。"""
    ...


def _merge_configs(
    defaults: AdapterConfig,
    sidecar: dict[str, Any],
    env: dict[str, Any],
    crd: dict[str, Any],
) -> AdapterConfig:
    """4 层 merge（仅覆盖显式声明字段）。"""
    ...


class AdapterSettings(BaseSettings):
    """pydantic_settings 风格（env 注入）。"""
    
    model_config = SettingsConfigDict(
        env_prefix="SUPERTEAM_ADAPTER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )
    
    timeout_seconds: int = 120
    max_retries: int = 3
    retry_strategy: str = "retry_network"
    sensitive_fields: list[str] = Field(default_factory=lambda: ["api_key", "token", "password"])
    observability_labels: dict[str, str] = Field(default_factory=dict)
```

### 6.3 `loader.py` 文件级契约（148 行 · 6 framework 动态加载）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/loader.py
from __future__ import annotations

import importlib.metadata
from typing import Any

from .models import AdapterConfig
from .protocol import FrameworkAdapter, FrameworkName
from .errors import AdapterConfigError, AdapterFrameworkError


def load_framework(name: FrameworkName, config: AdapterConfig) -> FrameworkAdapter:
    """6 framework 动态加载（entry_points）。
    
    Raises:
        AdapterConfigError: framework 名称不在 6 值枚举
        AdapterFrameworkError: entry_points 未注册 / 加载失败 / version 不兼容
    """
    ...


def list_frameworks() -> list[FrameworkName]:
    """列出已注册的 6 framework（按 entry_points 解析）。"""
    ...


def _resolve_entry_point(name: FrameworkName) -> Any:
    """entry_points["superteam_a2a.frameworks"][name] 解析。"""
    ...


def _check_version_compatibility(name: FrameworkName, version: str) -> None:
    """VERSION_MATRIX 版本范围校验（§3.5 同步）。"""
    ...
```

### 6.4 测试 ID 矩阵（SDK-CFG-001~008 + SDK-LOAD-001~006）

| 类别 | 测试 ID | 测试名 | 断言 |
|------|---------|--------|------|
| **load_config** | SDK-CFG-001 | test_load_config_defaults_only | 无 CRD/env/sidecar → 使用 defaults |
| **load_config** | SDK-CFG-002 | test_load_config_crd_overrides_all | CRD 字段覆盖 env/sidecar/defaults |
| **load_config** | SDK-CFG-003 | test_load_config_env_overrides_sidecar_defaults | env 字段覆盖 sidecar/defaults |
| **load_config** | SDK-CFG-004 | test_load_config_sidecar_overrides_defaults | sidecar 字段覆盖 defaults |
| **load_config** | SDK-CFG-005 | test_load_config_partial_override_does_not_introduce_new_fields | CRD 只覆盖 timeout_seconds，max_retries 保持 env 值 |
| **load_config** | SDK-CFG-006 | test_load_config_invalid_yaml_raises | sidecar YAML 解析失败 → AdapterConfigError |
| **load_config** | SDK-CFG-007 | test_load_config_validation_error_raises | 字段校验失败 → AdapterConfigError |
| **load_config** | SDK-CFG-008 | test_load_config_sensitive_fields_redacted_in_logs | sensitive_fields 在 structlog 中脱敏 |
| **load_framework** | SDK-LOAD-001 | test_load_framework_returns_protocol_instance | 返回 duck typing 校验通过的 FrameworkAdapter |
| **load_framework** | SDK-LOAD-002 | test_load_framework_invalid_name_raises | 6 framework 名称之外 → AdapterConfigError |
| **load_framework** | SDK-LOAD-003 | test_load_framework_entry_points_missing_raises | entry_points 未注册 → AdapterFrameworkError |
| **load_framework** | SDK-LOAD-004 | test_load_framework_version_incompatible_raises | version 超出 VERSION_MATRIX 范围 |
| **load_framework** | SDK-LOAD-005 | test_list_frameworks_returns_6_names | 已注册 6 framework 列表 |
| **load_framework** | SDK-LOAD-006 | test_load_framework_runtime_checkable_fail_raises | 加载后 isinstance 校验失败 → AdapterFrameworkError |

### 6.5 4 层配置优先级测试场景（与 L2-3 Spec §3.2 同步）

| 场景 | CRD | env | sidecar | defaults | 期望输出 |
|------|-----|-----|---------|----------|----------|
| 1 | - | - | - | timeout=120 | timeout=120 |
| 2 | - | - | timeout=300 | timeout=120 | timeout=300 |
| 3 | - | timeout=400 | timeout=300 | timeout=120 | timeout=400 |
| 4 | timeout=500 | timeout=400 | timeout=300 | timeout=120 | timeout=500 |
| 5 | timeout=500 | - | timeout=300 | timeout=120 | timeout=500 |
| 6 | {timeout=500} | {max_retries=5} | {timeout=300,max_retries=2} | {timeout=120,max_retries=3} | timeout=500, max_retries=5 |
| 7 | - | - | invalid_yaml | timeout=120 | AdapterConfigError |

---

## 附录 A：跨模块引用清单（v0.2-draft §3-§6 补完）

**说明**：本附录为 v0.2-draft 骨架占位，§3-§10 补完时同步展开 6 子表（L1 / L2 / ADR / Constitution / 配套 L3 / 归档基线）。

| 子表 | 目标文档 | 引用条数 | 状态 |
|------|----------|---------:|------|
| A.1 L1 | `docs/design/L1-architecture.md` §3.5 + §4.3 + `docs/spec/L1-system-spec.md` §16 | 待补完 | 占位 |
| A.2 L2 | `docs/spec/L2-module-specs/L2-adapter.md` v0.2.0 §3-§15（上游权威） | 待补完 | 占位 |
| A.3 ADR | `docs/adr/0005-python-first-technology-stack.md` §3.3 + §13.1 | 待补完 | 占位 |
| A.4 Constitution | `docs/CONSTITUTION.md` v0.5.0 §3.8 + §9.7 + §15.5 + §13.6 | 待补完 | 占位 |
| A.5 配套 L3 | L3-1 Operator Core v0.2.0 + L3-2 A2A Core v0.2.0 + L3-4 Hello Agent（待起草） | 待补完 | 占位 |
| A.6 归档基线 | `docs/archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md`（已归档） | 待补完 | 占位 |

---

## 附录 B：ADR / Constitution 引用矩阵（v0.2-draft 占位）

**说明**：本附录为 v0.2-draft 骨架占位，§3-§10 补完时同步展开 5 子表（架构与部署 / 接口与生命周期 / 错误处理 / 安全 / 可观测性与测试）。每条 MUST/SHOULD/MAY 强度分级 + 引用 ADR 章节 + 引用 Constitution 章节。

| 子表 | 主题 | 引用条数 | 状态 |
|------|------|---------:|------|
| B.1 架构与部署 | ADR-0005 §3.3 + 宪法 §3.8 + §13.1 | 待补完 | 占位 |
| B.2 接口与生命周期 | ADR-0005 §6 + 宪法 §3.7 | 待补完 | 占位 |
| B.3 错误处理 | L3-2 §10 错误码 + 宪法 §15.5 | 待补完 | 占位 |
| B.4 安全 | ADR-0005 §7 + 宪法 §6（不直接 mTLS） | 待补完 | 占位 |
| B.5 可观测性与测试 | L3-2 §9 指标 + 宪法 §7 + §9.7 | 待补完 | 占位 |

---

## 文档元数据与后续入口

### M.1 版本与状态

| 字段 | 值 |
|---|---|
| 版本 | **v0.2-draft** |
| 状态 | ✅ §0-§2 + 附录 A/B 占位 完整；§3-§10 + 附录 A 完整版 + 附录 B 5 子表 **待补完** |
| 上游 | L2-3 Adapter Design + Spec v0.2.0 |
| 同级已通过 | L3-1 Operator Core v0.2.0 (#56) + L3-2 A2A Core v0.2.0 (#54) |
| supersedes | L2-3 v0.1.0 Go baseline 实现条款；L3-2 wire 引用继续有效 |
| 评审报告 | `docs/reviews/l3-3-adapter-sdk-spec-review.md`（下一会话创建） |
| 当前变更边界 | 仅本 Spec v0.2-draft；独立评审前不进入 L4 实施 |

### M.2 落地记录

| 日期 / 会话 | 增量 | 结果 |
|---|---|---|
| 2026-07-28 #56 | L3-1 v0.2.0 通过 + L3-3 启动 | L3 阶段 1/4 完成 |
| 2026-07-28 #57 | L3-3 v0.2-draft 骨架稿 + 13 边界规则 + 6 框架独立 metrics + 11 文件 SDK + 24 framework 子包文件清单 | §0-§2 + 附录 A/B 占位 |
| 2026-07-28 #57（本会话） | L3-3 §3-§6 补完：FrameworkAdapter Protocol（466 行 · 5 生命周期方法）+ AgentCardConverter（322 行 · 6 框架字段映射）+ 6 framework 子包 24 文件级契约 + 4 层配置优先级 + 6 framework 动态加载 + 累计 1206 行 / 68KB / 84 测试 ID（SDK-PROT 12 + SDK-MOD 8 + SDK-CONV 10 + SDK-VER 4 + SDK-INT 3 + SDK-CFG 8 + SDK-LOAD 6 + 6 framework × 3 = 18 + 6 IT = 15） | §3-§6 完整版 + §1.3 文件清单 22 → 24；§7-§10 + 完整附录 A/B 待补完 → v0.2-draft-full |

### M.3 下一会话固定入口

1. **补完 L3-3 §7-§10 + 完整附录 A + 附录 B**（建议单会话完成，避免 §16.1 双会话通讯成本）：
   - §7 6 Prometheus 指标 + OTel + structlog（6 框架独立 + 4 复用 L3-2 §9）
   - §8 5 类 Tenacity 策略 + 7 错误码 enum + 错误传播通道
   - §9 Helm values 11.1-11.6（6 framework 子包各自 Helm 模板 + RBAC + NetworkPolicy + HELM-006~010）
   - §10 测试策略 + 工具链（159 测试 ID 矩阵 + 6 重静态门禁 + uv workspace + Dockerfile）
   - 附录 A 6 子表（30 行）
   - 附录 B 5 子表（49 行）
2. **升级 v0.2-draft-full**（完整版升级）：头部版本 v0.2-draft-skeleton → v0.2-draft-full + 状态行 + 落地记录新增 + 入口更新。
3. **独立评审 L3-3 v0.2-draft-full**：创建 `docs/reviews/l3-3-adapter-sdk-spec-review.md`，按 §A-§P / 10 维度核验 §9 的 159 测试 ID + 41 文件级契约 + 附录 B 五表（参照 L3-2 #54 评审模板 18KB / 217 行）。
4. **评审通过 + §F 6 步同步 + git commit**（参照 L3-1 #56 + L3-2 #54 commit 模板）。
5. **L3-4 Hello Agent 启动**：基于 L3-2 v0.2.0 + L3-1 v0.2.0 + L3-3 v0.2.0（不依赖 framework adapter，纯 A2A ping/pong 10 行代码）。

---

> **签署**：本 L3-3 Adapter SDK 文件级 Spec Python v0.2-draft 由 #56 + #57 共同形成，依据 [L2-3 Adapter Spec v0.2.0](../../spec/L2-module-specs/L2-adapter.md)、[L2-3 Adapter Design v0.2.0](../../design/L2-modules/L2-adapter.md)、[L3-1 Operator Core v0.2.0](../../spec/L3-file-specs/L3-operator-core.md)、[L3-2 A2A Core v0.2.0](../../spec/L3-file-specs/L3-a2a-core.md)、[L2-3 Go baseline（已归档）](../../archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md) 与 Constitution v0.5.0 编写。**当前骨架稿仅具备进入独立评审的准备条件；§3-§10 + 完整附录 A/B 补完后才能进入独立评审。**
