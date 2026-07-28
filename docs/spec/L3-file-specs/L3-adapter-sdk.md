# L3 文件级 Spec：Adapter SDK（编排层 Adapter 框架 SDK · Python-first）

> **⚠️ ADR-0005 supersede + 归档标记（2026-07-28）**：本 v0.2-draft Spec 文档**仅 supersede Go framework adapter / sigs.k8s.io/cli-runtime 实现条款**；wire contract（Adapter Protocol + FrameworkAdapter Protocol + AgentCardConverter + 6 framework matrix + 4 配置优先级 + 错误码 7 项）与 v0.2.0 Spec 业务语义**完全继续有效**。L2-3 v0.1.0 Go baseline 已归档至 [`docs/archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md`](../../archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md)（2026-07-24 归档 / 2026-07-26 #37 评审前未独立评审 / L2-3 v0.2.0 Python 重写已被 L2-3 v0.2.0 Spec 完全覆盖）。
>
> **Python 重写入口**：依据 L1 v0.2.0 Architecture §3.5 + §4.3 C-3 + ADR-0005 §3.3 + §13.1 + L2-3 v0.2.0 Spec §3-§6 落地，11 文件 SDK + 6 framework adapter 子包 → uv workspace `packages/adapter-sdk/src/superteam_a2a/adapter/`；6 framework 集成（LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents）→ 6 framework subpackage 独立仓库 + FrameworkAdapter Protocol（typing.Protocol + `@runtime_checkable`）；AgentCard 转换 → Pydantic v2 + A2AClient（L3-2 §6 复用）；4 层配置优先级（CRD spec > env > sidecar file > defaults）→ Pydantic v2 BaseSettings + 显式 merge 顺序 + 单元测试覆盖。
>
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-3（Adapter SDK，见 L1 Architecture §4.3）
> **代码位置**：`packages/adapter-sdk/src/superteam_a2a/adapter/`（**ADR-0005 §13.1 uv workspace 布局**，替代原 baseline 的 `src/adapter-sdk/`）
> **版本**：**v0.2-draft**（2026-07-28 起 Python 重写 + L3-1 v0.2.0 #56 + L3-2 v0.2.0 #54 L3 阶段 1/4 ~ 2/4 已通过）
> **状态**：✅ **v0.2-draft 骨架稿已落地，待独立评审**（#56 本次骨架 + §0-§2 + 附录 A 占位 + 附录 B 占位；§3-§10 + 附录 A 完整版 + 附录 B 5 子表 留待补完）——头部 + §0-§2 + 附录 A/B 占位 全部落地，5 个待补完章节标记
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

### 1.3 文件清单总览（11 + 6 + 22 = 39 文件级契约）

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
| 6 framework 名称不变（`langchain` / `autogen` / `crewai` / `sk` / `strands` / `smolagents`） | L2-3 §3.1 + L1 §4.3 + ADR-0005 | §1.3.2 表格 + 6 framework `adapter.py` 文件 |
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

## 附录 A：跨模块引用清单（v0.2-draft 占位）

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
| 2026-07-28 #57（本会话） | L3-3 v0.2-draft 骨架 + 13 边界规则 + 6 框架独立 metrics + 11 文件 SDK + 22 framework 顶层文件清单 | §0-§2 + 附录 A/B 占位；§3-§10 待补完 → v0.2-draft-full |

### M.3 下一会话固定入口

1. **补完 L3-3 §3-§10 + 完整附录 A + 附录 B**（建议拆 §3-§6 + §7-§10+附录 B 两会话避免 §16.1 红线）：
   - §3 FrameworkAdapter Protocol 文件级契约（types + 5 生命周期方法 + duck typing 校验）
   - §4 AgentCardConverter 文件级契约（framework 字段映射 + 6 框架独立 converter 引用）
   - §5 6 framework adapter 子包文件级契约（22 文件全展开 + 6 framework 共同契约）
   - §6 4 层配置优先级 merge 函数完整实现（CRD > env > sidecar file > defaults）
   - §7 10 Prometheus 指标 + OTel + structlog（6 框架 + 4 复用 L3-2）
   - §8 5 类 Tenacity 策略 + 7 错误码 enum + 错误传播通道
   - §9 Helm values 11.1-11.6（6 framework 子包各自 Helm 模板 + RBAC + NetworkPolicy）
   - §10 测试策略 + 工具链（159 测试 ID 矩阵 + 6 重静态门禁 + uv workspace + Dockerfile）
   - 附录 A 6 子表（30 行）
   - 附录 B 5 子表（49 行）
2. **升级 v0.2-draft-full**（完整版升级）：头部版本 v0.2-draft → v0.2-draft-full + 状态行 + 落地记录新增 + 入口更新。
3. **独立评审 L3-3 v0.2-draft-full**：创建 `docs/reviews/l3-3-adapter-sdk-spec-review.md`，按 §A-§P / 10 维度核验 §9 的 159 测试 ID + 39 文件级契约 + 附录 B 五表（参照 L3-2 #54 评审模板 18KB / 217 行）。
4. **评审通过 + §F 6 步同步 + git commit**（参照 L3-1 #56 + L3-2 #54 commit 模板）。
5. **L3-4 Hello Agent 启动**：基于 L3-2 v0.2.0 + L3-1 v0.2.0 + L3-3 v0.2.0（不依赖 framework adapter，纯 A2A ping/pong 10 行代码）。

---

> **签署**：本 L3-3 Adapter SDK 文件级 Spec Python v0.2-draft 由 #56 + #57 共同形成，依据 [L2-3 Adapter Spec v0.2.0](../../spec/L2-module-specs/L2-adapter.md)、[L2-3 Adapter Design v0.2.0](../../design/L2-modules/L2-adapter.md)、[L3-1 Operator Core v0.2.0](../../spec/L3-file-specs/L3-operator-core.md)、[L3-2 A2A Core v0.2.0](../../spec/L3-file-specs/L3-a2a-core.md)、[L2-3 Go baseline（已归档）](../../archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md) 与 Constitution v0.5.0 编写。**当前骨架稿仅具备进入独立评审的准备条件；§3-§10 + 完整附录 A/B 补完后才能进入独立评审。**
