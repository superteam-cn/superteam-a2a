# L3 文件级 Spec：Adapter SDK（编排层 Adapter 框架 SDK · Python-first）

> **⚠️ ADR-0005 supersede + 归档标记（2026-07-28）**：本 v0.2.0 Spec 文档**仅 supersede Go framework adapter / sigs.k8s.io/cli-runtime 实现条款**；wire contract（Adapter Protocol + FrameworkAdapter Protocol + AgentCardConverter + 6 framework matrix + 4 配置优先级 + 错误码 7 项）与 v0.2.0 Spec 业务语义**完全继续有效**。L2-3 v0.1.0 Go baseline 已归档至 [`docs/archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md`](../../archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md)（2026-07-24 归档 / 2026-07-26 #37 评审前未独立评审 / L2-3 v0.2.0 Python 重写已被 L2-3 v0.2.0 Spec 完全覆盖）。
>
> **Python 重写入口**：依据 L1 v0.2.0 Architecture §3.5 + §4.3 C-3 + ADR-0005 §3.3 + §13.1 + L2-3 v0.2.0 Spec §3-§6 落地，12 文件 SDK（11 继承 + `lifecycle.py`）+ 6 framework adapter 子包 → uv workspace `packages/adapter-sdk/src/superteam_a2a/adapter/`；6 framework 集成（LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents）→ 6 framework subpackage 独立仓库 + FrameworkAdapter Protocol（typing.Protocol + `@runtime_checkable`）；AgentCard 转换 → Pydantic v2 + A2AClient（L3-2 §6 复用）；4 层配置优先级（CRD spec > env > sidecar file > defaults）→ Pydantic v2 BaseSettings + 显式 merge 顺序 + 单元测试覆盖。
>
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-3（Adapter SDK，见 L1 Architecture §4.3）
> **代码位置**：`packages/adapter-sdk/src/superteam_a2a/adapter/`（**ADR-0005 §13.1 uv workspace 布局**，替代原 baseline 的 `src/adapter-sdk/`）
> **版本**：**v0.2.0**（2026-07-29 #58 评审通过并升级；#56 骨架 + #57 §3-§6 + #57 §7-§10/附录 A/B 完整版 + **#58 评审 §M 关注项 4-9 PR 同步修正**）
> **状态**：✅ **v0.2.0 已通过独立评审**（[评审报告](../../reviews/l3-3-adapter-sdk-spec-review.md) · §A-§P 16 节 / 10 维度全 PASS / 0 阻塞项 / 9 关注项 / 4 建议项）——头部 + §0-§10 + 附录 A（30 行 6 子表）+ 附录 B（49 行 5 子表）全部落地；累计 **12 文件 SDK + 22 framework 文件 = 42 文件级契约 / 200 测试 ID（+ §9.6 42 HELM-* 部署面 ID）/ 45 文件镜像清单**；**已可作为 L4 实施输入**
> **本次升级修正范围（#58 · 评审 §N 强制项）**：关注项 4（附录 B.2 row 12 Protocol 方法名）/ 关注项 5（B.2 row 13 方法数）/ 关注项 6（新增 §3.7 Lifecycle 11 步启动序列 + `lifecycle.py`）/ 关注项 7（`AdapterError.to_jsonrpc_error()` 契约）/ 关注项 8（§9.4 image tag 对齐 §3.5 VERSION_MATRIX）/ 关注项 9（public API 补齐 `Adapter` / `AdapterErrorCode` / `create_retry_policy` / `Lifecycle` 4 项）。**关注项 1-3（命名/枚举漂移 + ST-ADAPTER-BOUNDARY Ruff 规则落地 + 测试 ID 交叉引用）与 4 项建议项移交 v0.2.1 / L4 实施第一周微同步**，见 §M.2 台账。
> **上游约束**：[`docs/design/L2-modules/L2-adapter.md`](../../design/L2-modules/L2-adapter.md) **v0.2.0**（2026-07-26 #35 评审通过 · 1267 行 / 66KB / 14 主章节）+ [`docs/spec/L2-module-specs/L2-adapter.md`](../../spec/L2-module-specs/L2-adapter.md) **v0.2.0**（2026-07-26 #37 评审通过 · 114KB / 2705 行 / 14 节 + 2 附录 / 81-159 测试 ID / 15 开放问题 / 9 Python Protocol/Class + 5 生命周期时序图 + Helm values 11.1-11.6 + 6 framework 完整 schema + 6 层测试策略）
> **本 Spec 目的**：将 L2-3 Adapter Spec v0.2.0 中的 **11 文件 SDK（L3-3 落地为 12 文件，新增 `lifecycle.py`）+ 6 framework adapter 子包 + Adapter / FrameworkAdapter Protocol + AgentCardConverter + A2AClient 复用 + Helm values + 测试策略** 落地为 **文件级 Python 代码契约**——每个文件列明**绝对路径（基于 uv workspace 布局）**、**职责一句话**、**完整 import 列表**、**exported 符号签名（type hints + docstring 一行）**、**内部 helper 列表**、**关联测试文件路径 + 测试 ID 前缀**。是 L4 实施阶段（开发者打开 IDE 即可对照写代码）的直接输入。
> **配套 Spec**：[L3-1 Operator Core 文件级 Spec v0.2.0](./L3-operator-core.md)（2026-07-28 #56 评审通过）/ [L3-2 A2A Core Library 文件级 Spec v0.2.0](./L3-a2a-core.md)（2026-07-28 #54 评审通过 · [评审报告](../../reviews/l3-2-a2a-core-spec-review.md)） — L3-3 复用 L3-2 §6 `A2AClient` 与 §9 15 指标 + L3-2 §10 24 错误码 enum，不重复定义 A2A wire contract / [L3-4 Hello Agent 文件级 Spec](./L3-hello-agent.md)（待起草）/ [L3-5 Knowledge Service 文件级 Spec](./L3-knowledge-service.md)（待起草）/ [L3-6 Memory backend 文件级 Spec](./L3-memory-backend.md)（待起草）

---

## 0. 阅读指南

- **读者**：Adapter SDK 实施工程师（L4 Python 编码）、Framework Adapter 集成者（6 framework 各自 owner）、Code Reviewer（PR 审查）、架构 Reviewer（Adapter 边界一致性）
- **必读章节**：§1（模块使命 + 12 → 42 文件清单总览）/ §2（Python 包结构 12 文件 SDK + 6 framework 子包）/ 附录 A（跨模块引用清单）/ 附录 B（ADR / Constitution 5 子表追溯矩阵）
- **评审入口**：附录 A 6 子表（30 行） + 附录 B 5 子表（49 行）+ 12 文件 SDK 全部 exported 符号与测试 ID 映射 — 三处必须互相回链且数量一致
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

L3-3 Adapter SDK 文件级 Spec 将 [L2-3 Spec v0.2.0](../../spec/L2-module-specs/L2-adapter.md) 中描述的 **11 文件 SDK（本 Spec 落地为 12 文件，新增 §3.7 `lifecycle.py`）+ 6 framework adapter 子包 + Adapter / FrameworkAdapter Protocol + AgentCardConverter + 4 层配置优先级 + 7 错误码 + 6 框架集成的细节** 落地为 **可直接对照编码的 Python 文件级契约**。

**单 SDK 形态**：Adapter SDK 作为 uv workspace 单独 package（`packages/adapter-sdk/`），6 framework adapters 作为独立仓库（每个 framework 单独 PyPI 包，但通过本 SDK 的 `FrameworkAdapter` Protocol 接入）；adapter-sdk 与 L3-1 Operator Core + L3-2 A2A Core + L3-5 Knowledge Service 之间通过固定的 Python Protocol + Pydantic v2 边界（无 K8s API 依赖）。

**L3-3 文件级 Spec v.s. L2-3 模块 Spec 边界**：

| 维度 | L2-3 模块 Spec | L3-3 文件级 Spec |
|---|---|---|
| **粒度** | 模块级（11 文件 SDK + 6 framework 概要） | 文件级（12 SDK + 6 framework 子包共 42 文件级契约 + 每个文件的 import/exported/helper/测试文件） |
| **目的** | "为什么 + 是什么"（设计决策 + 4 协议 + 6 framework matrix + 4 层配置 + 7 错误码） | "怎么做"（每个文件具体怎么写） |
| **读者** | 架构师 + L3 起草者 | L4 实施工程师（开发者打开 IDE 对照） |
| **变更频率** | 低（设计变更才改） | 中（实现微调可能改） |
| **测试 ID 范围** | L2-3 81-159 测试 ID（≥ 81 v0.2 / ≥ 159 v1.0） | 继承 L2-3 前缀与语义，并按文件级路径细化为 §10.1 的 **200 个可执行测试 ID**（另有 §9.6 42 个 HELM-* 部署面 ID 独立计数）；`OPEN-A-*` 仅作决策追踪，不计入 200 |

### 1.2 模块对外契约（public API surface · 继承 L2-3 Spec §1.2）

**Public API 入口**（仅暴露给 L3-1 Operator Core + L3-2 A2A Core + 6 framework adapters 各自 repository）：

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/__init__.py
from .protocol import (
    Adapter,
    FrameworkAdapter,
    AgentCardConverter,
    AgentSpec,
    AgentCard,
    AdapterConfig,
)
from .errors import (
    AdapterErrorCode,
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
from .retry import create_retry_policy
from .lifecycle import Lifecycle

__all__ = [
    # Protocol（§3.2）
    "Adapter",
    "FrameworkAdapter",
    "AgentCardConverter",
    # 模型（§4.1）
    "AgentSpec",
    "AgentCard",
    "AdapterConfig",
    # 错误（§8.3）
    "AdapterErrorCode",
    "AdapterError",
    "AdapterPermanentError",
    "AdapterRetryableError",
    "AdapterNonRetryableError",
    "AdapterConfigError",
    "AdapterAuthError",
    "AdapterTimeoutError",
    "AdapterFrameworkError",
    "AdapterVersionError",
    # 重试（§8.2）
    "create_retry_policy",
    # 生命周期（§3.7）
    "Lifecycle",
]
```

**v0.2.0 #58 补齐说明（评审 §M 关注项 9）**：v0.2-draft-full 的 `__all__` 为 14 项（§1.3.1 曾误记为 13），与 [L2-3 Spec v0.2.0 §1.3](../../spec/L2-module-specs/L2-adapter.md) 列出的 public API surface 相比缺 `Adapter` / `AdapterErrorCode` / `create_retry_policy` / `Lifecycle` 4 项。本版按**选项 A** 补齐为 **18 项**，4 项落地位置如下（业务层 import 路径与 L2-3 完全一致）：

| 缺失符号 | L2-3 上游 | L3-3 v0.2.0 落地位置 | 测试 ID |
|---|---|---|---|
| `Adapter`（Protocol · 3 方法） | L2-3 Spec §3.1 | §3.2 `protocol.py`（与 FrameworkAdapter 分工见该节 docstring） | SDK-PROT-013 |
| `AdapterErrorCode`（枚举） | L2-3 Spec §6.1 | `errors.py`（§1.3.1 row 8 已列 exported 符号；本版纳入 `__all__`） | SDK-ERR-001 |
| `create_retry_policy`（工厂） | L2-3 Spec §6.4 | §8.2 `retry.py`（错误码 → `AsyncRetrying` 策略） | SDK-RTY-007 / 008 |
| `Lifecycle`（生命周期类） | L2-3 Spec §10.2 | §3.7 `lifecycle.py`（SDK 第 12 文件） | SDK-LC-001~008 |

**注**：L2-3 §1.3 中的 7 项 observability 符号（`REQUESTS_TOTAL` 等）与 `create_tracer` / `configure_logging` 在 L3-3 中按 §7.1 拆分为 `observability/` 子包并从 `superteam_a2a.adapter.observability` 导出，不进入本 `__all__`（§2.3 边界规则 11：`__init__.py` 仅导出核心契约面）。

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
- **禁止**：`import aiohttp` / `import requests` / `import flask` / `import django` / `import kubernetes` / `import kopf` / `import anyio`（任何 framework adapter 不得直接导入；如使用必须通过 SDK 提供的 Protocol）。**例外**：SDK 内部 §3.7 `lifecycle.py` 允许 `import anyio`（仅用于 30s grace period 计时与 in-flight 等待，继承 L2-3 Spec §10.2），framework adapter 子包仍全面禁止。

### 1.3 文件清单总览（12 + 6 + 24 = 42 文件级契约）

#### 1.3.1 12 文件 SDK 主清单（11 项与 L2-3 Spec §3.1 一致 + v0.2.0 #58 新增 `lifecycle.py`）

| # | 路径 | 职责 | exported 符号 | 测试 ID 前缀 |
|---|------|------|----------------|---------------|
| 1 | `packages/adapter-sdk/src/superteam_a2a/adapter/__init__.py` | public API 入口 | 18 符号（14 原有 + 4 补齐；见 §1.2） | SDK-EXPORT-001 |
| 2 | `packages/adapter-sdk/src/superteam_a2a/adapter/_internals.py` | 内部 helper + 测试夹具 | `_load_framework`, `_make_test_card` | SDK-INT-001~003 |
| 3 | `packages/adapter-sdk/src/superteam_a2a/adapter/protocol.py` | Adapter Protocol + FrameworkAdapter Protocol + AgentCardConverter Protocol + 7 错误类（含 `to_jsonrpc_error` 契约） | `Adapter`, `FrameworkAdapter`, `AgentCardConverter`, `AdapterError` × 7 | SDK-PROT-001~015 |
| 4 | `packages/adapter-sdk/src/superteam_a2a/adapter/models.py` | Pydantic v2 AgentSpec / AgentCard / AdapterConfig | `AgentSpec`, `AgentCard`, `AdapterConfig` | SDK-MOD-001~008 |
| 5 | `packages/adapter-sdk/src/superteam_a2a/adapter/loader.py` | 6 framework 动态加载 + entry_points 解析 | `load_framework`, `list_frameworks` | SDK-LOAD-001~006 |
| 6 | `packages/adapter-sdk/src/superteam_a2a/adapter/converter.py` | AgentCard 转换逻辑 + 字段映射 | `convert_agent_card`, `validate_agent_card` | SDK-CONV-001~010 |
| 7 | `packages/adapter-sdk/src/superteam_a2a/adapter/config.py` | 4 层配置优先级合并（CRD > env > sidecar file > defaults） | `merge_config`, `load_config` | SDK-CFG-001~008 |
| 8 | `packages/adapter-sdk/src/superteam_a2a/adapter/errors.py` | 7 错误码 enum + Tenacity 5 类策略映射 | `AdapterErrorCode` enum, error mapping | SDK-ERR-001~009 |
| 9 | `packages/adapter-sdk/src/superteam_a2a/adapter/retry.py` | Tenacity 5 类策略 + structlog 错误日志 + `create_retry_policy` 工厂 | `with_retry`, `create_retry_policy`, `compute_backoff` | SDK-RTY-001~008 |
| 10 | `packages/adapter-sdk/src/superteam_a2a/adapter/observability.py` | 6 框架独立 metrics + structlog 8 字段 + OTel | `MetricsRegistry`, `log_adapter_event` | SDK-OBS-001~008 |
| 11 | `packages/adapter-sdk/src/superteam_a2a/adapter/version.py` | 6 framework 版本兼容矩阵 + 升级策略 | `VERSION_MATRIX`, `check_version` | SDK-VER-001~004 |
| 12 | `packages/adapter-sdk/src/superteam_a2a/adapter/lifecycle.py` | **（v0.2.0 #58 新增）** Lifecycle 11 步启动序列 + 30s grace 关闭 + reload（§3.7） | `Lifecycle`, `GRACE_PERIOD_SECONDS`, `READINESS_PERIODS` | SDK-LC-001~008 |

#### 1.3.2 6 framework adapter 子包总览（每个子包 ~3-4 文件 = 22 文件）

| # | 框架 | 子包路径 | 文件清单 | 引用 L3-2 资源 | 测试 ID 前缀 |
|---|------|----------|----------|----------------|---------------|
| 13 | **LangChain** | `packages/adapter-langchain/src/superteam_a2a/adapter_langchain/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | LC-A-* / LC-C-* / LC-E-* |
| 14 | **AutoGen** | `packages/adapter-autogen/src/superteam_a2a/adapter_autogen/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | AG-A-* / AG-C-* / AG-E-* |
| 15 | **CrewAI** | `packages/adapter-crewai/src/superteam_a2a/adapter_crewai/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | CR-A-* / CR-C-* / CR-E-* |
| 16 | **Semantic Kernel** | `packages/adapter-sk/src/superteam_a2a/adapter_sk/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | SK-A-* / SK-C-* / SK-E-* |
| 17 | **Strands** | `packages/adapter-strands/src/superteam_a2a/adapter_strands/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | ST-A-* / ST-C-* / ST-E-* |
| 18 | **Smolagents** | `packages/adapter-smolagents/src/superteam_a2a/adapter_smolagents/` | `__init__.py` + `adapter.py` + `converter.py` + `errors.py` | A2AClient §6 | SM-A-* / SM-C-* / SM-E-* |

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

- 12 文件 SDK → 12 `tests/unit/adapter-sdk/test_<file>.py`
- 6 framework × 3 adapter 文件 = 18 `tests/unit/adapters/test_<framework>_<file>.py` + 4 `tests/integration/framework/test_<framework>_e2e.py`（E2E 仅 6 framework 共享 4 集成测试，避免子包级别 E2E 爆炸）

**合计 12 + 22 + 顶层测试 = 42 文件级契约 + ~51 顶层测试 = ~93 文件级落地点**（不含工程骨架文件）。

#### 1.3.4 与 L3-1 / L3-2 文件级规模对照

| 维度 | L3-1 Operator Core | L3-2 A2A Core | **L3-3 Adapter SDK** |
|------|-------------------:|---------------:|---------------------:|
| Python 实现文件 | 70 | 30 | **12 SDK + 22 framework = 34** |
| 顶层测试文件 | 50 | 30 | ~51 |
| Helm 模板 | 9 | 9 | 0（Adapter SDK 不直接交付 Helm chart；6 framework 各自 HELM-006~010 在 §11 引用） |
| 工程资产 | 25 | 0 | 0（复用 L3-1 工程资产） |
| 文件级契约总数 | 162 | 69 | **~93** |
| 测试 ID | 277 | 276 | **200**（§10.1 加总；L2-3 v1.0 目标 159 + 文件级细化 +41） |
| 公开 Protocol/Class | 36 | 36 | **18 public 符号**（3 Protocol + 3 Model + 1 ErrorCode enum + 9 Error 类 + 1 重试工厂 + 1 Lifecycle） |
| ClusterRole apiGroups | 7 | 0 | 0（无 K8s API 依赖） |
| 开放问题 | 25 | 24 | **15**（L2-3 继承 10 + 5 Spec 新增） |

L3-3 文件级规模**显著小于 L3-1 / L3-2**，但仍需 ~30-40KB / ~800-1000 行的骨架 + 后续补完章节（§3-§10 + 附录 A 完整版 + 附录 B 5 子表）。

### 1.4 关键不变量（5 项 · 任意修改必须走 ADR）

| 不变量 | 强制来源 | 落地位置 |
|--------|----------|----------|
| 6 framework 名称不变（`langchain` / `autogen` / `crewai` / `sk` / `strands` / `smolagents`） | L2-3 §3.1 + L1 §4.3 + ADR-0005 | §1.3.2 表格 + 6 framework `adapter.py` 文件 + §3.2 `FrameworkName` Literal |
| 7 AdapterError 子类继承关系 | L2-3 §3.3 + L3-2 §10 错误码 | `errors.py` + 测试 SDK-ERR-001~009 |
| 4 层配置优先级 CRD > env > sidecar file > defaults | L2-3 §3.2 + ADR-0005 §6.5 | `config.py` + 测试 SDK-CFG-001~008 |
| 5 类 Tenacity 策略（`retry_network` / `retry_timeout` / `retry_5xx` / `retry_429` / `no_retry_4xx`） | L2-3 §6.4 + 宪法 §15.5 | `retry.py` + 测试 SDK-RTY-001~008 |
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
│   │       └── adapter/                     # 12 文件 SDK 主清单
│   │           ├── __init__.py              # public API 入口（18 符号）
│   │           ├── _internals.py
│   │           ├── protocol.py              # Adapter + FrameworkAdapter + AgentCardConverter
│   │           ├── models.py                # Pydantic v2
│   │           ├── loader.py                # 6 framework 动态加载
│   │           ├── converter.py             # AgentCard 转换
│   │           ├── config.py                # 4 层配置优先级
│   │           ├── errors.py                # 7 错误码
│   │           ├── retry.py                 # Tenacity 5 类策略 + create_retry_policy
│   │           ├── observability.py         # 6 framework metrics
│   │           ├── lifecycle.py             # Lifecycle 11 步启动序列（§3.7）
│   │           └── version.py               # 版本兼容矩阵
│   └── tests/
│       ├── unit/
│       │   └── adapter-sdk/
│       │       ├── test_protocol.py         # SDK-PROT-001~015
│       │       ├── test_models.py           # SDK-MOD-001~008
│       │       ├── test_loader.py           # SDK-LOAD-001~006
│       │       ├── test_converter.py        # SDK-CONV-001~010
│       │       ├── test_config.py           # SDK-CFG-001~008
│       │       ├── test_errors.py           # SDK-ERR-001~009
│       │       ├── test_retry.py            # SDK-RTY-001~008
│       │       ├── test_observability.py    # SDK-OBS-001~008
│       │       ├── test_lifecycle.py        # SDK-LC-001~008
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
| 11 | `__init__.py` 仅导出 `__all__`（其他符号下划线前缀） | 12 文件 SDK + 6 framework `__init__.py` |
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

### 3.2 `protocol.py` 文件级契约（约 560 行 · 核心 SDK 代码 · v0.2.0 #58 补入 `Adapter` Protocol + `to_jsonrpc_error` 契约摘录）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/protocol.py
# Copyright 2026 superteam-a2a authors. Apache-2.0 license.
"""Adapter Protocol + FrameworkAdapter Protocol + AgentCardConverter Protocol + 7 错误类。

基于 typing.Protocol + @runtime_checkable；不强制基类继承。
6 framework adapter 必须实现 FrameworkAdapter 协议的全部 5 生命周期方法，
并对外暴露一个满足 Adapter 协议（3 方法）的实例供 A2A Server 消费。
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
from .errors import AdapterError, AdapterErrorCode


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


@runtime_checkable
class Adapter(Protocol):
    """Adapter ↔ A2A Server 协议边界（继承 L2-3 Spec §3.1 · public API）。

    与 FrameworkAdapter 的分工（v0.2.0 #58 补齐 · 评审 §M 关注项 9）：
    - `Adapter`：**面向 A2A Server 的运行时边界**（3 方法），由 L3-2 a2a-core
      `create_app()` 与 §3.7 `Lifecycle` 消费；6 framework adapter 子包对外暴露的
      就是本 Protocol 的实例。
    - `FrameworkAdapter`：**面向 framework SDK 的翻译边界**（5 方法，见上），
      由 `Adapter` 实现内部持有并调用。
    - 两者均 `@runtime_checkable`；`isinstance(obj, Adapter)` 用于 §3.7 启动期
      Step 8 的 duck typing 校验。
    """

    async def on_message(
        self,
        message: Message,
        context_id: str | None = None,
    ) -> Task:
        """处理 A2A sendMessage；返回 Task + 状态。

        Args:
            message: A2A Message（来自 sendMessage params.message）
            context_id: A2A context ID（multi-turn 对话）

        Returns:
            Task: A2A Task（status + artifacts）

        Raises:
            AdapterError: 含 error_code（-32001 ~ -32007）+ framework_error
        """
        ...

    def agent_card(self) -> AgentCard:
        """返回 Agent Card（用于 /.well-known/agent.json）。

        启动期一次性构建（§3.7 Step 10），运行期 cached；不做 I/O。
        """
        ...

    async def health_check(self) -> bool:
        """健康检查（Adapter container readiness）。

        Returns:
            True: Adapter 可用
            False: framework SDK 未初始化 / Agent container 不可达（Sidecar 拓扑）
        """
        ...


# --- AdapterError JSON-RPC 序列化契约（v0.2.0 #58 补齐 · 评审 §M 关注项 7） ---
# 定义位置：errors.py 中的 AdapterError 基类方法；此处列出签名与 wire 结构，
# 供 §8.3 errors_mapping.py 与 L3-2 §10 错误传播直接对照实现。

class AdapterError(Exception):  # 契约摘录（完整定义见 errors.py）
    """Adapter 错误基类（7 子类见 §1.4 不变量）。"""

    framework: str | None
    error_code: AdapterErrorCode  # -32001 ~ -32007（L3-2 §10 继承）
    cause: Exception | None

    def to_jsonrpc_error(self) -> dict[str, Any]:
        """序列化为 A2A JSON-RPC error object（wire contract · 不可变）。

        Returns:
            {
                "code": int,               # error_code 数值（-32001 ~ -32007）
                "message": str,            # 人类可读摘要（str(self)；≤ 1024 字符截断）
                "data": {
                    "framework": str | None,        # 6 framework 名之一或 None（SDK 层错误）
                    "framework_error": {            # framework 原始异常上下文（B.3 row 31 MUST）
                        "exception_type": str,      # type(cause).__name__；cause 为 None 时省略
                        "detail": str,              # str(cause)，经 §7.4 9 项敏感字段脱敏
                    } | None,
                    "retryable": bool,              # == §8.3 is_retryable(self)
                },
            }

        约束：
        - **不得**泄漏 §7.4 9 项敏感字段（api_key / token / password 等）——
          `detail` 必须先过 `redact_sensitive()` 再写入。
        - `code` 取值必须落在 L3-2 §10 24 错误码 enum 的 Adapter 区间（-32001 ~ -32007）；
          禁止新增（§2.3 边界规则 9）。
        - 由 L3-2 a2a-core 的 JSON-RPC 响应层直接嵌入 `error` 字段，Adapter 不自行构造响应包。
        """
        ...
```

**§3.2 测试 ID 补充**（v0.2.0 #58 新增 3 项）：

| 测试 ID | 测试名 | 断言 |
|---------|--------|------|
| SDK-PROT-013 | `test_adapter_protocol_runtime_checkable_3_methods` | `isinstance(stub, Adapter)` 对含 `on_message`/`agent_card`/`health_check` 的对象为 True；缺任一方法为 False |
| SDK-PROT-014 | `test_to_jsonrpc_error_wire_shape` | 返回 dict 含 `code` / `message` / `data.framework` / `data.framework_error` / `data.retryable`；`code` ∈ -32001~-32007 |
| SDK-PROT-015 | `test_to_jsonrpc_error_redacts_and_carries_framework_error` | `cause` 存在时 `framework_error.exception_type` 为原始异常类名；`detail` 中 9 项敏感字段已脱敏为 `***` |

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

### 3.4 5 生命周期方法测试 ID 矩阵（SDK-PROT-001~012；`Adapter` Protocol 与 `to_jsonrpc_error` 的 013~015 见 §3.2 末尾）

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

### 3.7 Lifecycle 11 步启动序列 + `lifecycle.py` 文件级契约（约 210 行 · v0.2.0 #58 新增 SDK 第 12 文件）

> **补入依据**：附录 B.2 row 17 / row 18 / row 19 / row 20 将 Lifecycle 11 步启动序列、30s grace period、readiness 5 周期、lifespan 单进程模式列为 MUST，但 v0.2-draft-full 的 §3 仅落地 5 生命周期方法时序图（§3.3），无承载文件——评审 §M 关注项 6 + 关注项 9（`Lifecycle` public 符号缺失）。本节按 [L2-3 Spec v0.2.0 §10.1 + §10.2](../../spec/L2-module-specs/L2-adapter.md) 落地，**wire 与步骤编号完全继承上游，不新增语义**。

#### 3.7.1 11 步启动序列（继承 L2-3 Spec §10.1 · 步骤编号不可变）

```
时间 ──────────────────────────────────────────────────────────────►

Operator Core (L3-1)                K8s API              Adapter Container (L3-3)
────────────────────                ───────              ────────────────────────
1. Watch Agent CRD
2. Reconcile Agent
3. 构造 Pod spec（含 Adapter container）
4. apply Pod ─────────────────────► Pod Created
5. 调度 + 启动 containers
                                    Containers Start
                                                         6.  main() 启动（uvicorn 单 worker · §10.6）
                                                         7.  load AdapterConfig（4 层优先级 · §6.2）
                                                             失败 → AdapterError(-32007) + Exit 1
                                                         8.  init Adapter（entry_points 加载 framework
                                                             SDK · §6.3；isinstance(obj, Adapter) 校验）
                                                             失败 → AdapterError(-32001) + Exit 1
                                                         9.  Lifecycle.start()
                                                             - 启动 transport（httpx 进程级单例 · B.2 row 20）
                                                             - 注册 A2A Server（L3-2 create_app）
                                                             - 注册 /healthz + /readyz
                                                             - 启动 framework event listener
                                                             - 启动 Prometheus /metrics（§7.2）
                                                         10. Card 转换（启动期一次性，cached · §4.2）
                                                             失败 → AdapterError(-32003) + Exit 1
                                                         11. 标记 Ready（_ready = True）
                                    ◄─── readiness probe 通过（5 周期 · B.2 row 19）───
12. Watch Agent.Status.Ready = true
```

**步骤 → 落地位置映射**（L4 实施对照表）：

| 步骤 | 动作 | 落地文件 | 失败错误码 | 测试 ID |
|---:|------|----------|-----------|--------|
| 6 | uvicorn 单 worker 进程启动 | `__main__.py`（framework 子包各自提供） | — | SDK-LC-001 |
| 7 | `load_config()` 4 层优先级 | §6.2 `config.py` | `-32007` ADAPTER_CONFIG_ERROR | SDK-LC-002 |
| 8 | entry_points 加载 + `isinstance(obj, Adapter)` | §6.3 `loader.py` + §3.2 | `-32001` ADAPTER_FRAMEWORK_ERROR | SDK-LC-003 |
| 9 | `Lifecycle.start()` 5 项子步骤 | 本节 `lifecycle.py` | 透传子步骤错误码 | SDK-LC-004 |
| 10 | `agent_card()` 一次性构建 + cache | §4.2 `converter.py` | `-32003` CARD_CONVERSION_FAILED | SDK-LC-005 |
| 11 | `_ready = True` + `/readyz` 200 | 本节 `lifecycle.py` | — | SDK-LC-006 |

**关闭序列（30s grace period · B.2 row 18）**：`SIGTERM` → `/readyz` 立即返回 503（摘流）→ 等待 in-flight `on_message` 完成（上限 30s，与 §9.3 `terminationGracePeriodSeconds: 30` 对齐）→ `Lifecycle.stop()` 关闭 transport + flush OTel span → 进程退出 0；超过 30s 未收敛的 in-flight 请求以 `AdapterError(-32002)` 结束并计入 `supteam_adapter_errors_total{reason="shutdown_timeout"}`。

#### 3.7.2 `lifecycle.py` 文件级契约

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/lifecycle.py
# Copyright 2026 superteam-a2a authors. Apache-2.0 license.
"""Adapter 生命周期 hook（Operator Core 集成 · 继承 L2-3 Spec §10.2）。

本模块不 import 任何 framework SDK（§2.3 边界规则 2），仅依赖 Adapter Protocol。
"""

from __future__ import annotations

import anyio
import structlog

from .config import AdapterConfig, validate_adapter_config
from .errors import AdapterError, AdapterErrorCode
from .protocol import Adapter

_logger = structlog.get_logger("superteam_a2a.adapter.lifecycle")

GRACE_PERIOD_SECONDS: float = 30.0   # 与 §9.3 terminationGracePeriodSeconds 成对修改
READINESS_PERIODS: int = 5           # B.2 row 19：readiness probe 连续 5 周期


class Lifecycle:
    """Adapter 生命周期状态机（public API · 由 framework 子包 `__main__` 驱动）。

    状态：INIT → STARTING → READY → DRAINING → STOPPED（单向，不可回退；
    `reload()` 仅在 READY 态允许，失败时保持旧 config 并停留 READY）。
    """

    def __init__(
        self,
        adapter: Adapter,
        config: AdapterConfig,
        logger: structlog.stdlib.BoundLogger | None = None,
    ) -> None:
        """持有 Adapter 实例与已合并的 AdapterConfig；不做 I/O。"""
        ...

    @property
    def ready(self) -> bool:
        """`/readyz` 探针数据源（Step 11 置 True；SIGTERM 后立即置 False）。"""
        ...

    async def start(self) -> None:
        """启动序列 Step 7-11（见 §3.7.1）。

        Raises:
            AdapterError: -32007（config 校验失败）/ -32001（framework 加载失败）
                / -32003（Card 转换失败）——调用方必须 Exit 1，不得降级启动。
        """
        ...

    async def reload(self, new_config: AdapterConfig) -> None:
        """ConfigMap 变化时热更新（仅 reload-able 字段 · §6.1 4 层优先级不变）。

        校验失败时**不更新** self._config（保持旧配置继续服务），抛 AdapterError(-32007)。
        """
        ...

    async def stop(self, grace: float = GRACE_PERIOD_SECONDS) -> None:
        """关闭序列：摘流 → 等待 in-flight（≤ grace）→ 关 transport → flush OTel。

        幂等：重复调用直接返回；超时按 §3.7.1 关闭序列计入 shutdown_timeout。
        """
        ...
```

#### 3.7.3 §3.7 测试 ID 矩阵（8 ID）

| 测试 ID | 文件 | 测试名 | 断言 |
|---------|------|--------|------|
| SDK-LC-001 | `tests/unit/adapter-sdk/test_lifecycle.py` | test_start_step6_single_worker | uvicorn 单 worker（`workers == 1`）· ADR-0005 §6 单进程原则 |
| SDK-LC-002 | 同上 | test_start_step7_config_error_exits | `validate_adapter_config` 抛错 → `AdapterError(-32007)` 且 `ready is False` |
| SDK-LC-003 | 同上 | test_start_step8_adapter_protocol_check | 不满足 `Adapter` Protocol 的对象 → `AdapterError(-32001)` |
| SDK-LC-004 | 同上 | test_start_step9_registers_5_subsystems | transport / A2A app / healthz+readyz / event listener / metrics 五项均已注册 |
| SDK-LC-005 | 同上 | test_start_step10_card_cached_once | `agent_card()` 仅调用 1 次；二次读取命中 cache → `AdapterError(-32003)` 路径覆盖 |
| SDK-LC-006 | 同上 | test_start_step11_ready_true_after_5_periods | Step 11 后 `ready is True`；readiness 连续 5 周期通过 |
| SDK-LC-007 | 同上 | test_stop_grace_period_30s_and_idempotent | SIGTERM 后 `ready` 立即 False；in-flight 等待上限 30s；重复 `stop()` 幂等 |
| SDK-LC-008 | 同上 | test_reload_invalid_config_keeps_old | `reload()` 校验失败后 `self._config` 未变且状态仍为 READY |


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

## 7. 可观测性文件级契约（继承 L2-3 Spec §7 · 6 framework 独立指标 + 4 复用 L3-2 §9）

### 7.1 文件清单（4 文件）

| # | 路径 | 职责 | 行数估计 | 测试 ID 前缀 |
|---|------|------|---------|------------|
| 1 | `packages/adapter-sdk/src/superteam_a2a/adapter/observability/__init__.py` | 公共 API 入口（re-export 6 metrics + tracer factory + logger factory） | 12 | OBS-EXPORT-001 |
| 2 | `packages/adapter-sdk/src/superteam_a2a/adapter/observability/metrics.py` | 6 framework 独立 Prometheus 指标（Counter/Histogram/Gauge）+ 单进程 DEFAULT_REGISTRY | 178 | OBS-METRICS-001~008 |
| 3 | `packages/adapter-sdk/src/superteam_a2a/adapter/observability/tracing.py` | OTel tracer factory + 4 层 Span 结构 + Root Span attributes | 124 | OBS-TRACING-001~006 |
| 4 | `packages/adapter-sdk/src/superteam_a2a/adapter/observability/logging.py` | structlog JSON 配置 + 9 项敏感字段脱敏 + 7 强制字段 | 96 | OBS-LOGGING-001~005 |

**合计 4 文件 ~410 行**（保留 §7 边界文件粒度；metrics.py 占比最大因 6 framework × 2~3 指标）。

### 7.2 `metrics.py` 文件级契约（178 行）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/observability/metrics.py
from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry


# 单进程模式默认 registry（ADR-0005 §10 · 避免 multiprocess mode 复杂性）
DEFAULT_REGISTRY = CollectorRegistry()


# 6 framework 独立指标（label framework 必须存在）

REQUESTS_TOTAL = Counter(
    "supteam_adapter_requests_total",
    "Adapter request count by framework/method/status",
    labelnames=("framework", "method", "status"),
    registry=DEFAULT_REGISTRY,
)

REQUEST_DURATION_SECONDS = Histogram(
    "supteam_adapter_request_duration_seconds",
    "Adapter request duration in seconds",
    labelnames=("framework", "method"),
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
    registry=DEFAULT_REGISTRY,
)

CARD_CONVERSION_DURATION_SECONDS = Histogram(
    "supteam_adapter_card_conversion_duration_seconds",
    "AgentCard conversion duration in seconds (framework introspection → A2A Card)",
    labelnames=("framework",),
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 5),
    registry=DEFAULT_REGISTRY,
)

FRAMEWORK_LOAD_DURATION_SECONDS = Histogram(
    "supteam_adapter_framework_load_duration_seconds",
    "Framework SDK load duration in seconds (entry_points → Protocol instance)",
    labelnames=("framework",),
    buckets=(0.5, 1, 2, 5, 10, 30, 60),
    registry=DEFAULT_REGISTRY,
)

ERRORS_TOTAL = Counter(
    "supteam_adapter_errors_total",
    "Adapter error count by framework/error_code (-32001 ~ -32007)",
    labelnames=("framework", "error_code"),
    registry=DEFAULT_REGISTRY,
)

ACTIVE_AGENTS = Gauge(
    "supteam_adapter_active_agents",
    "Currently active agents per framework (derived from readiness probe)",
    labelnames=("framework",),
    registry=DEFAULT_REGISTRY,
)

GOLDEN_CASE_PASS_TOTAL = Counter(
    "supteam_adapter_golden_case_pass_total",
    "Golden Adapter test pass count (CI report by case_id)",
    labelnames=("framework", "case_id"),
    registry=DEFAULT_REGISTRY,
)


def setup_metrics(registry: CollectorRegistry | None = None) -> CollectorRegistry:
    """注册指标到指定 registry（None = DEFAULT_REGISTRY）。
    
    Args:
        registry: 自定义 registry（测试场景注入；生产 = None）
    
    Returns:
        CollectorRegistry: 实际使用的 registry
    
    Raises:
        AdapterConfigError: registry 已包含同名指标（重新注册冲突）
    """
    if registry is None:
        return DEFAULT_REGISTRY
    for metric in (
        REQUESTS_TOTAL, REQUEST_DURATION_SECONDS,
        CARD_CONVERSION_DURATION_SECONDS, FRAMEWORK_LOAD_DURATION_SECONDS,
        ERRORS_TOTAL, ACTIVE_AGENTS, GOLDEN_CASE_PASS_TOTAL,
    ):
        # 重新注册到自定义 registry（幂等保护）
        try:
            registry.register(metric)
        except ValueError as exc:
            raise AdapterConfigError(
                f"metric {metric._name} already registered",
                framework=None, error_code=AdapterErrorCode.ADAPTER_CONFIG_ERROR,
            ) from exc
    return registry


def get_metric(name: str, framework: str | None = None) -> Any:
    """获取指定指标当前值（用于 readiness probe / debug endpoint）。"""
    ...
```

**关键不变量（继承 L2-3 Spec §7.4 + 宪法 §7 + ADR-0005 §10）**：
- 高基数 label 禁令：`trace_id` / `task_id` 永不过 metric label（仅 OTel Span attributes）
- 单进程模式：禁用 prometheus_client multiprocess mode（PROMETHEUS_MULTIPROC_DIR 未设置）
- 6 framework label 取值：`langchain` / `autogen` / `crewai` / `semantic_kernel` / `strands` / `smolagents`
- 错误码 label 取值：`ADAPTER_CONFIG_ERROR` / `ADAPTER_AUTH_ERROR` / `ADAPTER_TIMEOUT_ERROR` / `ADAPTER_FRAMEWORK_ERROR` / `ADAPTER_VERSION_ERROR` / `ADAPTER_RETRYABLE_ERROR` / `ADAPTER_PERMANENT_ERROR`

### 7.3 `tracing.py` 文件级契约（124 行）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/observability/tracing.py
from __future__ import annotations

from opentelemetry import trace, context
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


_TRACER_NAME = "supteam_a2a.adapter"


def create_tracer(
    name: str = _TRACER_NAME,
    otlp_endpoint: str | None = None,
    sample_ratio: float = 0.1,
    service_version: str = "0.2.0",
) -> trace.Tracer:
    """创建 Adapter tracer（显式 provider 注入，避免污染全局）。
    
    Args:
        name: tracer 名（默认 "supteam_a2a.adapter"）
        otlp_endpoint: OTLP collector endpoint（如 "otel-collector:4317"）；None = 不导出
        sample_ratio: 采样率（0.1 = 10%；生产推荐 0.01-0.1）
        service_version: adapter-sdk 版本（Root Span attribute `adapter.version`）
    
    Returns:
        trace.Tracer: OTel tracer 实例
    """
    provider = TracerProvider(
        sampler=TraceIdRatioBased(sample_ratio),
    )
    
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(name)
    
    # 注入 service.version resource attribute
    resource = provider._resource if hasattr(provider, "_resource") else None
    return tracer


def create_root_span(
    tracer: trace.Tracer,
    framework: str,
    method: str,
    agent_name: str,
    framework_version: str,
) -> trace.Span:
    """创建 Root Span：`adapter.{framework}.{method}`。
    
    Attributes:
        framework (str): 6 framework 名称
        framework.version (str): framework SDK 版本（运行时检测）
        adapter.version (str): adapter-sdk 版本（来自 service_version）
        agent.name (str): framework agent 名称
        method (str): A2A method 名（sendMessage / getTask 等）
    
    Returns:
        trace.Span: 当前活跃 Span（用作 `with` 上下文管理器）
    """
    return tracer.start_as_current_span(
        f"adapter.{framework}.{method}",
        attributes={
            "framework": framework,
            "framework.version": framework_version,
            "adapter.version": "0.2.0",
            "agent.name": agent_name,
            "method": method,
        },
    )


def create_child_span(
    parent: trace.Span,
    name: str,
    attributes: dict[str, str] | None = None,
) -> trace.Span:
    """创建 Child Span（`framework.invoke` / `card.convert` / `framework.translate`）。"""
    ...


# OTel 4 层 Span 结构（语义约定）
SPAN_NAMES = frozenset({
    "adapter.{framework}.{method}",     # Root
    "framework.invoke",                  # Child 1
    "card.convert",                      # Child 2（Card 重读时）
    "framework.translate",               # Child 3（framework output → A2A 响应）
})

# Span Events（可选）
SPAN_EVENTS = frozenset({
    "tool.invoked",      # framework tool 调用
    "memory.read",       # memory 读
    "memory.write",      # memory 写
    "error.occurred",    # 错误发生（携带 exception type + error_code）
})
```

### 7.4 `logging.py` 文件级契约（96 行）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/observability/logging.py
from __future__ import annotations

import logging
import structlog


# 9 项敏感字段（永不过日志；L2-3 Spec §7.3 + 宪法 §6.5）
_SENSITIVE_KEYS = frozenset({
    "api_key", "token", "password", "secret",
    "user_data", "memory_content", "knowledge_body",
    "cert", "private_key",
})


def _redact_sensitive(_: object, __: str, event_dict: dict) -> dict:
    """structlog processor：脱敏敏感字段。"""
    for key in list(event_dict.keys()):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = "***REDACTED***"
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    """配置 structlog JSON 输出（单进程模式 + 9 项脱敏）。
    
    Args:
        level: 日志级别（DEBUG / INFO / WARNING / ERROR）；默认 INFO
    
    强制字段（每条日志必须含）：
        framework / framework.version / adapter.version / method / task_id / agent.name / level / ts / msg
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_sensitive,  # 脱敏 processor
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """获取 structlog logger。"""
    return structlog.get_logger(name)


def bind_context(
    framework: str,
    framework_version: str,
    method: str,
    task_id: str | None = None,
    agent_name: str | None = None,
) -> None:
    """绑定强制字段到 contextvars（避免每条日志重复传参）。
    
    7 项强制字段：framework / framework.version / adapter.version / method / task_id / agent.name / level
    （level 由 structlog.add_log_level 自动添加；adapter.version 在服务启动时通过 configure_logging 设置）
    """
    structlog.contextvars.bind_contextvars(
        framework=framework,
        framework_version=framework_version,
        adapter_version="0.2.0",
        method=method,
        task_id=task_id,
        agent_name=agent_name,
    )


def clear_context() -> None:
    """清空 contextvars（请求结束时调用，避免泄漏到下一次请求）。"""
    structlog.contextvars.clear_contextvars()
```

### 7.5 4 复用 L3-2 §9 runtime 指标（不重复定义）

**约束**：L3-3 不新增 Python runtime 指标；以下 4 项继承自 L3-2 §9.2（由 L3-1 Operator Core 在 Pod 启动时统一注入，6 framework adapter 子包直接通过 env 读取 `METRICS_PORT`）：

| 指标名 | 类型 | 来源 | L3-3 行为 |
|--------|------|------|----------|
| `supteam_python_event_loop_lag_seconds` | Histogram (threshold=50ms) | L3-2 §9.2 | 仅消费（不写入） |
| `supteam_python_thread_offload_queue_depth` | Gauge | L3-2 §9.2 | 仅消费 |
| `supteam_python_active_asyncio_tasks` | Gauge | L3-2 §9.2 | 仅消费 |
| `supteam_python_gc_collections_total` | Counter (by generation) | L3-2 §9.2 | 仅消费 |

**禁止**：adapter-sdk 包内**不得**重新定义这 4 个指标（避免重复注册冲突）。

### 7.6 §7 测试 ID 矩阵（19 ID）

| 测试 ID | 文件 | 测试名 | 断言 |
|---------|------|--------|------|
| OBS-METRICS-001 | metrics.py | test_setup_metrics_default_registry_returns_default | `setup_metrics()` 返回 `DEFAULT_REGISTRY` |
| OBS-METRICS-002 | metrics.py | test_setup_metrics_custom_registry_re_registers_all | 7 个指标全部重新注册到自定义 registry |
| OBS-METRICS-003 | metrics.py | test_setup_metrics_duplicate_registration_raises | 自定义 registry 已含同名指标 → `AdapterConfigError` |
| OBS-METRICS-004 | metrics.py | test_requests_total_increments_per_call | `REQUESTS_TOTAL.labels(framework="langchain", method="sendMessage", status="ok").inc()` 后值+1 |
| OBS-METRICS-005 | metrics.py | test_request_duration_histogram_observation | `REQUEST_DURATION_SECONDS.labels(framework="langchain", method="sendMessage").observe(1.5)` 后桶累计 |
| OBS-METRICS-006 | metrics.py | test_high_cardinality_labels_rejected | `REQUESTS_TOTAL.labels(framework="langchain", trace_id="abc")` 调用约定文档明确禁止（非代码校验） |
| OBS-METRICS-007 | metrics.py | test_single_process_mode_no_multiproc_env | 测试时未设置 `PROMETHEUS_MULTIPROC_DIR` 验证 |
| OBS-METRICS-008 | metrics.py | test_golden_case_pass_counter_increments | CI 报告 golden case pass +1 |
| OBS-TRACING-001 | tracing.py | test_create_tracer_default_provider | `create_tracer()` 返回 OTel tracer 实例 |
| OBS-TRACING-002 | tracing.py | test_create_tracer_with_otlp_endpoint | 指定 endpoint → BatchSpanProcessor 已注册 |
| OBS-TRACING-003 | tracing.py | test_create_root_span_attributes | 5 attributes（framework / framework.version / adapter.version / agent.name / method）全部出现 |
| OBS-TRACING-004 | tracing.py | test_create_root_span_name_pattern | Span name = `adapter.{framework}.{method}` |
| OBS-TRACING-005 | tracing.py | test_create_child_span_nested_under_root | Child Span parent 指向 Root Span context |
| OBS-TRACING-006 | tracing.py | test_span_events_frozenset_contains_4_events | `SPAN_EVENTS` 含 `tool.invoked` / `memory.read` / `memory.write` / `error.occurred` |
| OBS-LOGGING-001 | logging.py | test_configure_logging_json_output | JSON renderer 启用 |
| OBS-LOGGING-002 | logging.py | test_redact_sensitive_9_keys | 9 项敏感字段（api_key 等）全部脱敏为 `***REDACTED***` |
| OBS-LOGGING-003 | logging.py | test_bind_context_7_required_fields | 7 项强制字段（framework / framework.version / adapter.version / method / task_id / agent.name / level）绑定 |
| OBS-LOGGING-004 | logging.py | test_clear_context_resets_bindings | `clear_context()` 后下次 `get_logger().info()` 无 framework 字段 |
| OBS-LOGGING-005 | logging.py | test_log_level_filter | log_level="DEBUG" 时 DEBUG 级输出可见 |

---

## 8. 重试 + 错误传播文件级契约（继承 L2-3 Spec §10.4 + L3-2 §10）

### 8.1 文件清单（2 文件）

| # | 路径 | 职责 | 行数估计 | 测试 ID 前缀 |
|---|------|------|---------|------------|
| 1 | `packages/adapter-sdk/src/superteam_a2a/adapter/retry.py` | 5 类 Tenacity 策略 + with_retry 装饰器 + jitter 计算 + `create_retry_policy` public 工厂 | 200 | RETRY-001~010 + SDK-RTY-007~008 |
| 2 | `packages/adapter-sdk/src/superteam_a2a/adapter/errors_mapping.py` | framework 异常 → AdapterError 子类映射表 + Retryable 矩阵 | 124 | ERR-MAP-001~008 |

**合计 2 文件 ~324 行**（§3.2 已定义 `protocol.py` 中 `AdapterError` 基类 + 7 子类 + `to_jsonrpc_error` 契约，本节仅追加 mapping 与 retry 策略）。

### 8.2 `retry.py` 文件级契约（约 200 行 · v0.2.0 #58 追加 `create_retry_policy`）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/retry.py
from __future__ import annotations

import random
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_never,
    wait_exponential,
    wait_fixed,
    wait_random,
    before_sleep_log,
)
import structlog

from .errors import (
    AdapterError,
    AdapterRetryableError,
    AdapterTimeoutError,
    AdapterPermanentError,
    AdapterFrameworkError,
    AdapterConfigError,
    AdapterErrorCode,
)


P = ParamSpec("P")
R = TypeVar("R")
_logger = structlog.get_logger("supteam_a2a.adapter.retry")


# 5 类策略常量（继承 L2-3 Spec §10.4 + 宪法 §15.5）

STRATEGY_RETRY_NETWORK = "retry_network"          # 网络错误 → 指数退避 + jitter（默认）
STRATEGY_RETRY_5XX = "retry_5xx"                   # 5xx → 指数退避 + jitter
STRATEGY_RETRY_RATE_LIMIT = "retry_rate_limit"    # 429 rate limit → 固定 60s + jitter
STRATEGY_RETRY_TIMEOUT = "retry_timeout"           # 超时 → 指数退避 + jitter
STRATEGY_RETRY_FRAMEWORK = "retry_framework"      # framework 业务错误 → 有限 3 次 + 指数退避

VALID_STRATEGIES = frozenset({
    STRATEGY_RETRY_NETWORK,
    STRATEGY_RETRY_5XX,
    STRATEGY_RETRY_RATE_LIMIT,
    STRATEGY_RETRY_TIMEOUT,
    STRATEGY_RETRY_FRAMEWORK,
})


def compute_backoff(
    strategy: str,
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> float:
    """计算第 N 次重试的退避时间（含 jitter）。
    
    Args:
        strategy: 5 类策略之一（VALID_STRATEGIES 成员）
        attempt: 当前重试次数（0 = 首次重试）
        base_delay: 基础延迟秒数（默认 1.0）
        max_delay: 最大延迟秒数（默认 60.0）
    
    Returns:
        float: 实际等待秒数（≤ max_delay）
    
    Raises:
        AdapterConfigError: strategy 不在 VALID_STRATEGIES
    """
    if strategy not in VALID_STRATEGIES:
        raise AdapterConfigError(
            f"invalid retry strategy: {strategy}",
            framework=None,
            error_code=AdapterErrorCode.ADAPTER_CONFIG_ERROR,
        )
    
    if strategy == STRATEGY_RETRY_RATE_LIMIT:
        # 固定 60s + jitter（±10%）
        base = 60.0
    elif strategy == STRATEGY_RETRY_NETWORK or strategy == STRATEGY_RETRY_5XX:
        # 指数退避（base * 2^attempt）+ jitter（0.5x-1.5x）
        base = min(base_delay * (2 ** attempt), max_delay)
    elif strategy == STRATEGY_RETRY_TIMEOUT:
        # 指数退避 + cap 30s
        base = min(base_delay * (2 ** attempt), 30.0)
    elif strategy == STRATEGY_RETRY_FRAMEWORK:
        # 3 次有限 + 指数退避（5s/10s/20s）
        base = min(5.0 * (2 ** attempt), max_delay)
    
    # jitter（全 jitter = random.uniform(0.5, 1.5) 倍率）
    return base * random.uniform(0.5, 1.5)


def with_retry(
    strategy: str = STRATEGY_RETRY_NETWORK,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """装饰器：包装 async 函数应用 5 类 Tenacity 策略。
    
    Args:
        strategy: 重试策略（5 类之一）
        max_attempts: 最大尝试次数（含首次调用；默认 3 = 首次 + 2 重试）
        base_delay: 基础延迟（秒）
        max_delay: 最大延迟（秒）
    
    Returns:
        Callable: 装饰后的 async 函数
    
    Raises:
        AdapterRetryableError: 重试耗尽后最后一次错误
        AdapterPermanentError: 不可重试错误立即抛出
    """
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(multiplier=base_delay, max=max_delay),
                    retry=retry_if_exception_type(AdapterRetryableError),
                    before_sleep=before_sleep_log(_logger, structlog.stdlib.WARNING),
                    reraise=True,
                ):
                    with attempt:
                        return await func(*args, **kwargs)
            except RetryError as exc:
                # 重试耗尽 → 包装为 AdapterRetryableError
                last = exc.last_attempt.exception() if exc.last_attempt else exc
                raise AdapterRetryableError(
                    f"retry exhausted after {max_attempts} attempts",
                    framework=None,
                    error_code=AdapterErrorCode.ADAPTER_RETRYABLE_ERROR,
                    cause=last,
                ) from exc
        return wrapper
    return decorator


# --- public 工厂（v0.2.0 #58 补齐 · 评审 §M 关注项 9 · 继承 L2-3 Spec §6.4） ---

def create_retry_policy(
    error_code: AdapterErrorCode,
    *,
    max_attempts: int | None = None,
) -> AsyncRetrying:
    """按错误码返回对应的 Tenacity `AsyncRetrying` 策略实例（public API）。

    `with_retry` 装饰器是"按策略名"的语法糖；本工厂是"按错误码"的显式入口，
    供 framework adapter 子包在 `except AdapterError as e:` 分支内按需构造重试上下文。
    两者共用同一张策略表——**策略集合以 §1.4 不变量 row 5 + §4.1 `AdapterConfig.retry_strategy`
    为准，不得在此新增第 6 类策略**（§2.3 边界规则 8）。

    Args:
        error_code: `AdapterErrorCode` 之一（-32001 ~ -32007）
        max_attempts: 覆盖默认尝试次数；None 时取策略表默认值

    Returns:
        AsyncRetrying: 已配置 stop / wait / retry 谓词的实例（`reraise=True`）

    Raises:
        AdapterConfigError: error_code 不在 7 值枚举内

    错误码 → 策略映射（与 §8.3 `RETRYABLE_MATRIX` 严格一致，False 项返回"不重试"策略）：

        ADAPTER_RETRYABLE_ERROR  → STRATEGY_RETRY_NETWORK    stop_after_attempt(3)  指数退避 + jitter
        ADAPTER_TIMEOUT_ERROR    → STRATEGY_RETRY_TIMEOUT    stop_after_attempt(3)  指数退避 cap 30s
        ADAPTER_FRAMEWORK_ERROR  → STRATEGY_RETRY_FRAMEWORK  stop_after_attempt(3)  5s/10s/20s
        ADAPTER_CONFIG_ERROR     → 不重试                     stop_after_attempt(1)
        ADAPTER_AUTH_ERROR       → 不重试                     stop_after_attempt(1)
        ADAPTER_VERSION_ERROR    → 不重试                     stop_after_attempt(1)
        ADAPTER_PERMANENT_ERROR  → 不重试                     stop_after_attempt(1)
    """
    ...
```

**§8.2 测试 ID 补充**（v0.2.0 #58 新增 2 项）：

| 测试 ID | 测试名 | 断言 |
|---------|--------|------|
| SDK-RTY-007 | `test_create_retry_policy_matches_retryable_matrix` | 7 个错误码逐一构造策略；`is_retryable() is False` 的 4 个错误码返回 `stop_after_attempt(1)`（即不重试） |
| SDK-RTY-008 | `test_create_retry_policy_rejects_unknown_code` | 非 `AdapterErrorCode` 成员 → `AdapterConfigError`；且不产生第 6 类策略 |

### 8.3 `errors_mapping.py` 文件级契约（124 行）

```python
# packages/adapter-sdk/src/superteam_a2a/adapter/errors_mapping.py
from __future__ import annotations

from collections.abc import Callable

from .errors import (
    AdapterError,
    AdapterRetryableError,
    AdapterNonRetryableError,
    AdapterPermanentError,
    AdapterTimeoutError,
    AdapterConfigError,
    AdapterAuthError,
    AdapterFrameworkError,
    AdapterVersionError,
    AdapterErrorCode,
)


# Retryable 矩阵（继承 L3-2 §10 + L2-3 Spec §10.4）
# True = 该错误码触发重试；False = 立即抛出

RETRYABLE_MATRIX: dict[AdapterErrorCode, bool] = {
    AdapterErrorCode.ADAPTER_CONFIG_ERROR: False,        # 配置错误 = 永久
    AdapterErrorCode.ADAPTER_AUTH_ERROR: False,          # 认证错误 = 永久
    AdapterErrorCode.ADAPTER_TIMEOUT_ERROR: True,        # 超时 = 可重试
    AdapterErrorCode.ADAPTER_FRAMEWORK_ERROR: True,      # framework 业务错误 = 可重试（有限 3 次）
    AdapterErrorCode.ADAPTER_VERSION_ERROR: False,       # 版本不兼容 = 永久
    AdapterErrorCode.ADAPTER_RETRYABLE_ERROR: True,      # 重试错误 = 可重试
    AdapterErrorCode.ADAPTER_PERMANENT_ERROR: False,     # 永久错误 = 不可重试
}


def is_retryable(error: AdapterError) -> bool:
    """查询错误是否可重试。"""
    return RETRYABLE_MATRIX.get(error.error_code, False)


def map_framework_exception(
    exc: Exception,
    framework: str,
) -> AdapterError:
    """framework 特定异常 → AdapterError 子类映射。
    
    Args:
        exc: framework 抛出的原始异常
        framework: framework 名称（6 值之一）
    
    Returns:
        AdapterError: 包装后的错误（带 error_code + framework context）
    
    映射规则（继承 L2-3 Spec §10.4）：
        - 网络错误（httpx.RequestError / aiohttp.ClientError）→ AdapterRetryableError
        - 超时（asyncio.TimeoutError / httpx.TimeoutException）→ AdapterTimeoutError
        - 4xx（HTTPStatusError with status < 500 且 ≠ 429）→ AdapterNonRetryableError
        - 5xx（HTTPStatusError with status >= 500）→ AdapterRetryableError
        - 429 rate limit → AdapterRetryableError
        - framework 业务错误（framework-specific exception）→ AdapterFrameworkError
        - 版本不兼容 → AdapterVersionError
    """
    import httpx  # framework adapter 子包内 import；此处仅在 framework adapter 调 SDK 时触达
    
    if isinstance(exc, (httpx.ConnectError, httpx.NetworkError)):
        return AdapterRetryableError(
            f"network error: {exc}",
            framework=framework,
            error_code=AdapterErrorCode.ADAPTER_RETRYABLE_ERROR,
            cause=exc,
        )
    if isinstance(exc, (httpx.TimeoutException, asyncio.TimeoutError)):
        return AdapterTimeoutError(
            f"timeout error: {exc}",
            framework=framework,
            error_code=AdapterErrorCode.ADAPTER_TIMEOUT_ERROR,
            cause=exc,
        )
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 429:
            return AdapterRetryableError(
                f"rate limit (429): {exc}",
                framework=framework,
                error_code=AdapterErrorCode.ADAPTER_RETRYABLE_ERROR,
                cause=exc,
            )
        if status < 500:
            return AdapterNonRetryableError(
                f"4xx error ({status}): {exc}",
                framework=framework,
                error_code=AdapterErrorCode.ADAPTER_NON_RETRYABLE_ERROR,
                cause=exc,
            )
        return AdapterRetryableError(
            f"5xx error ({status}): {exc}",
            framework=framework,
            error_code=AdapterErrorCode.ADAPTER_RETRYABLE_ERROR,
            cause=exc,
        )
    if isinstance(exc, ImportError) and "version" in str(exc).lower():
        return AdapterVersionError(
            f"version incompatible: {exc}",
            framework=framework,
            error_code=AdapterErrorCode.ADAPTER_VERSION_ERROR,
            cause=exc,
        )
    # fallback: framework 业务错误
    return AdapterFrameworkError(
        f"framework error: {exc}",
        framework=framework,
        error_code=AdapterErrorCode.ADAPTER_FRAMEWORK_ERROR,
        cause=exc,
    )


# 错误传播通道（3 通道统一处理）
# 通道 1：structlog logger.error() → JSON 日志（带 framework + error_code）
# 通道 2：Prometheus ERRORS_TOTAL.labels(framework, error_code).inc()
# 通道 3：OTel Span Event "error.occurred"（attributes: framework, error_code, exception.type）
async def propagate_error(
    error: AdapterError,
    span: TraceSpan | None = None,
) -> None:
    """3 通道统一错误传播（structlog + Prometheus + OTel）。
    
    Args:
        error: AdapterError 实例
        span: 当前活跃 OTel Span（可选；None = 无 Span）
    """
    import structlog
    from .observability.metrics import ERRORS_TOTAL
    
    logger = structlog.get_logger("supteam_a2a.adapter")
    logger.error(
        "adapter_error",
        framework=error.framework,
        error_code=error.error_code.value,
        error_message=str(error),
        cause=str(error.__cause__) if error.__cause__ else None,
    )
    if error.framework:
        ERRORS_TOTAL.labels(
            framework=error.framework,
            error_code=error.error_code.value,
        ).inc()
    if span is not None:
        span.add_event(
            "error.occurred",
            attributes={
                "framework": error.framework or "unknown",
                "error.code": error.error_code.value,
                "exception.type": type(error).__name__,
            },
        )
```

### 8.4 §8 测试 ID 矩阵（18 ID）

| 测试 ID | 文件 | 测试名 | 断言 |
|---------|------|--------|------|
| RETRY-001 | retry.py | test_compute_backoff_retry_network_exponential | attempt=0 → ~1s；attempt=2 → ~4s（±jitter 0.5-1.5x） |
| RETRY-002 | retry.py | test_compute_backoff_retry_rate_limit_fixed_60s | attempt=任意 → ~60s（±jitter） |
| RETRY-003 | retry.py | test_compute_backoff_retry_framework_capped_3_times | attempt=2 → 20s（5*2^2=20）；attempt=3 → 20s（cap） |
| RETRY-004 | retry.py | test_compute_backoff_invalid_strategy_raises | "unknown_strategy" → `AdapterConfigError` |
| RETRY-005 | retry.py | test_compute_backoff_jitter_range | 100 次采样 + `random.uniform(0.5, 1.5)` 验证在 [0.5x, 1.5x] 区间 |
| RETRY-006 | retry.py | test_with_retry_async_succeeds_after_2_failures | mock 函数首次失败 → 重试 1 次成功 → 正常返回 |
| RETRY-007 | retry.py | test_with_retry_async_exhausts_max_attempts | max_attempts=3 → 3 次全部失败 → `AdapterRetryableError` 抛出 |
| RETRY-008 | retry.py | test_with_retry_permanent_error_no_retry | `AdapterPermanentError` 触发 → 立即抛出（不重试） |
| RETRY-009 | retry.py | test_with_retry_logs_warning_before_sleep | `before_sleep` hook 调用 → structlog WARNING 日志输出 |
| RETRY-010 | retry.py | test_with_retry_preserves_function_metadata | `@wraps(func)` 保留 `__name__` / `__doc__` |
| ERR-MAP-001 | errors_mapping.py | test_retryable_matrix_7_codes | 7 项 ErrorCode 全部映射正确（4 True + 3 False） |
| ERR-MAP-002 | errors_mapping.py | test_is_retryable_known_code | `is_retryable(error_with_timeout_code)` → True |
| ERR-MAP-003 | errors_mapping.py | test_is_retryable_unknown_code_defaults_false | 未知 ErrorCode → False（保守） |
| ERR-MAP-004 | errors_mapping.py | test_map_network_error_to_retryable | `httpx.ConnectError` → `AdapterRetryableError` |
| ERR-MAP-005 | errors_mapping.py | test_map_timeout_to_timeout_error | `httpx.TimeoutException` → `AdapterTimeoutError` |
| ERR-MAP-006 | errors_mapping.py | test_map_429_rate_limit_to_retryable | `httpx.HTTPStatusError(429)` → `AdapterRetryableError` |
| ERR-MAP-007 | errors_mapping.py | test_map_5xx_to_retryable_4xx_to_non_retryable | 500 → Retryable；404 → NonRetryable |
| ERR-MAP-008 | errors_mapping.py | test_propagate_error_three_channels | mock logger + mock metrics + mock span → 3 通道均调用 |

---

## 9. Helm values 文件级契约（继承 L2-3 Spec §11 · 6 framework 独立 image override）

### 9.1 文件清单（12 文件 · 6 framework × 2 文件）

| # | 路径 | 职责 | 行数估计 | 测试 ID 前缀 |
|---|------|------|---------|------------|
| 1 | `helm/adapter-langchain/values.yaml` | LangChain adapter Helm values | 86 | HELM-LC-001~003 |
| 2 | `helm/adapter-langchain/templates/deployment.yaml` | LangChain Deployment 模板（adapter sidecar） | 124 | HELM-LC-DEPLOY-001~003 |
| 3 | `helm/adapter-autogen/values.yaml` | AutoGen adapter Helm values | 86 | HELM-AG-001~003 |
| 4 | `helm/adapter-autogen/templates/deployment.yaml` | AutoGen Deployment 模板 | 124 | HELM-AG-DEPLOY-001~003 |
| 5 | `helm/adapter-crewai/values.yaml` | CrewAI adapter Helm values | 86 | HELM-CR-001~003 |
| 6 | `helm/adapter-crewai/templates/deployment.yaml` | CrewAI Deployment 模板 | 124 | HELM-CR-DEPLOY-001~003 |
| 7 | `helm/adapter-semantic-kernel/values.yaml` | SK adapter Helm values | 86 | HELM-SK-001~003 |
| 8 | `helm/adapter-semantic-kernel/templates/deployment.yaml` | SK Deployment 模板 | 124 | HELM-SK-DEPLOY-001~003 |
| 9 | `helm/adapter-strands/values.yaml` | Strands adapter Helm values | 86 | HELM-ST-001~003 |
| 10 | `helm/adapter-strands/templates/deployment.yaml` | Strands Deployment 模板 | 124 | HELM-ST-DEPLOY-001~003 |
| 11 | `helm/adapter-smolagents/values.yaml` | Smolagents adapter Helm values | 86 | HELM-SM-001~003 |
| 12 | `helm/adapter-smolagents/templates/deployment.yaml` | Smolagents Deployment 模板 | 124 | HELM-SM-DEPLOY-001~003 |

**合计 12 文件 ~1232 行**（每 framework 2 文件 · values 86 行 + deployment 124 行；适配 Pod Security Standard: restricted）。

### 9.2 通用 Helm 模板契约（每 framework values.yaml · 86 行）

```yaml
# helm/adapter-{framework}/values.yaml
# 继承 L2-3 Spec §11.1-§11.2 通用 schema；仅 image/repository/tag/resources 随 framework 变化

global:
  imageRegistry: ghcr.io/superteam-a2a
  imagePullPolicy: IfNotPresent
  logLevel: INFO

adapter:
  # 6 framework 独立 image override（关键差异点）
  image:
    repository: ghcr.io/superteam-a2a/adapter-{framework}
    tag: v0.2.0-{framework_version}-py3.12  # framework_version 由 §3.5 VERSION_MATRIX 决定
    pullPolicy: IfNotPresent

  # A2A Server 端口
  port: 8080
  host: 0.0.0.0

  # Agent container 通信（sidecar 模式 · 同 Pod localhost）
  agentServiceHost: localhost
  agentServicePort: 7080

  # 部署模式（v0.2+）
  embedded: false  # true = 同进程 plugin；false = sidecar

  # 健康检查
  healthCheckPath: /healthz
  readinessPath: /readyz

  # framework 资源限制（framework 差异）
  resources:
    requests:
      cpu: 200m      # CrewAI 提至 300m（详见 L2-3 Spec §11.2）
      memory: 256Mi  # CrewAI 提至 384Mi
    limits:
      cpu: 1         # CrewAI 提至 2
      memory: 512Mi  # CrewAI 提至 1Gi

  # Pod Security Standard: restricted
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

  # ConfigMap + Secret 引用
  configMapRef: superteam-a2a-adapter-config
  mtlsSecretRef: superteam-a2a-adapter-mtls

  # 优雅停机
  shutdownGracePeriodSeconds: 30
```

### 9.3 通用 Deployment 模板契约（每 framework · 124 行）

```yaml
# helm/adapter-{framework}/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "adapter-{framework}.fullname" . }}
  labels:
    {{- include "adapter-{framework}.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.adapter.replicas | default 1 }}
  selector:
    matchLabels:
      {{- include "adapter-{framework}.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "adapter-{framework}.selectorLabels" . | nindent 8 }}
      annotations:
        # ConfigMap 变化触发 reload（与 lifecycle.py §3.4 reload 协同）
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
    spec:
      serviceAccountName: {{ include "adapter-{framework}.serviceAccountName" . }}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      containers:
        # Container 1: A2A Server (adapter)
        - name: adapter
          image: "{{ .Values.adapter.image.repository }}:{{ .Values.adapter.image.tag }}"
          imagePullPolicy: {{ .Values.adapter.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.adapter.port }}
              protocol: TCP
          env:
            - name: SUPERTEAM_ADAPTER_FRAMEWORK
              value: "{framework}"  # langchain / autogen / crewai / semantic_kernel / strands / smolagents
            - name: SUPERTEAM_ADAPTER_PORT
              value: "{{ .Values.adapter.port }}"
            - name: SUPERTEAM_ADAPTER_EMBEDDED
              value: "{{ .Values.adapter.embedded }}"
            - name: SUPERTEAM_ADAPTER_CONFIG_PATH
              value: "/etc/superteam-a2a/adapter-config.yaml"
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "http://otel-collector:4317"
            - name: OTEL_TRACES_SAMPLER_ARG
              value: "0.1"
          envFrom:
            - configMapRef:
                name: {{ .Values.adapter.configMapRef }}
          volumeMounts:
            - name: adapter-config
              mountPath: /etc/superteam-a2a
              readOnly: true
            - name: mtls-certs
              mountPath: /etc/superteam-a2a/mtls
              readOnly: true
          livenessProbe:
            httpGet:
              path: {{ .Values.adapter.healthCheckPath }}
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: {{ .Values.adapter.readinessPath }}
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            {{- toYaml .Values.adapter.resources | nindent 12 }}
          securityContext:
            {{- toYaml .Values.adapter.securityContext | nindent 12 }}
        # Container 2: Agent (framework runtime)
        - name: agent
          image: "{{ .Values.agent.image.repository }}:{{ .Values.agent.image.tag }}"
          imagePullPolicy: {{ .Values.agent.image.pullPolicy | default "IfNotPresent" }}
          ports:
            - name: agent-http
              containerPort: {{ .Values.adapter.agentServicePort }}
          resources:
            {{- toYaml .Values.agent.resources | nindent 12 }}
      volumes:
        - name: adapter-config
          configMap:
            name: {{ .Values.adapter.configMapRef }}
        - name: mtls-certs
          secret:
            secretName: {{ .Values.adapter.mtlsSecretRef }}
      terminationGracePeriodSeconds: {{ .Values.adapter.shutdownGracePeriodSeconds }}
```

### 9.4 6 framework 资源差异矩阵（继承 L2-3 Spec §11.2）

| Framework | Image tag | CPU request | Memory request | CPU limit | Memory limit | 备注 |
|-----------|-----------|-------------|----------------|----------|--------------|------|
| LangChain | `v0.2.0-0.2.0-py3.12` | 200m | 256Mi | 1 | 512Mi | 标准 |
| AutoGen | `v0.2.0-0.4.0-py3.12` | 200m | 256Mi | 1 | 512Mi | 标准 |
| CrewAI | `v0.5.0-0.80.0-py3.12` | 300m | 384Mi | 2 | 1Gi | 独占最高 |
| Semantic Kernel | `v0.5.0-1.30.0-py3.12` | 200m | 256Mi | 1 | 512Mi | 标准 |
| Strands | `v0.2.0-0.1.0-py3.12` | 200m | 256Mi | 1 | 512Mi | 标准 |
| Smolagents | `v0.2.0-1.10.0-py3.12` | 200m | 256Mi | 1 | 512Mi | 标准 |

**说明**：image tag 模板 `{adapter_version}-{framework_version}-py3.12`；其中 `{framework_version}` **必须等于 §3.5 `VERSION_MATRIX[framework].min_version`**（首个受支持版本），否则 §6.3 `_check_version_compatibility` 会在启动期拒绝并抛 `AdapterVersionError`。

**image tag ↔ §3.5 VERSION_MATRIX 对齐矩阵**（v0.2.0 #58 修正 · 评审 §M 关注项 8）：

| Framework | image tag `{framework_version}` | §3.5 `min_version` | §3.5 `max_version`（不含） | 一致性 |
|-----------|--------------------------------|--------------------|---------------------------|--------|
| LangChain | `0.2.0` | `0.2.0` | `0.3.0` | ✅ |
| AutoGen | `0.4.0` | `0.4.0` | `1.0.0` | ✅ |
| CrewAI | `0.80.0` | `0.80.0` | `0.100.0` | ✅ |
| Semantic Kernel | `1.30.0` | `1.30.0` | `1.40.0` | ✅ |
| Strands | `0.1.0` | `0.1.0` | `0.3.0` | ✅ |
| Smolagents | `1.10.0` | `1.10.0` | `2.0.0` | ✅ |

**变更约束**：§3.5 `VERSION_MATRIX` 与本表 image tag 为**成对修改项**——任一 framework 的 `min_version` 上调，必须在同一 PR 内同步上调本表 image tag（测试 ID `HELM-IMG-001~006` 逐 framework 断言两处一致）。

### 9.5 RBAC + NetworkPolicy 共享模板（位于 `helm/adapter-shared/`）

| # | 路径 | 职责 | 行数估计 | 测试 ID |
|---|------|------|---------|--------|
| 1 | `helm/adapter-shared/templates/clusterrole.yaml` | ClusterRole：adapters/events + adapters/status + leases（仅 Leader Election） | 42 | HELM-RBAC-001~003 |
| 2 | `helm/adapter-shared/templates/clusterrolebinding.yaml` | ClusterRoleBinding → adapter ServiceAccount | 18 | HELM-RBAC-004 |
| 3 | `helm/adapter-shared/templates/networkpolicy.yaml` | NetworkPolicy：ingress 8080 from namespace selector；egress K8s API + otel-collector + agent localhost | 64 | HELM-NP-001~004 |
| 4 | `helm/adapter-shared/templates/servicemonitor.yaml` | ServiceMonitor：抓取 /metrics（每 30s）；6 framework 独立 label | 38 | HELM-SM-001~003 |

### 9.6 §9 测试 ID 矩阵（42 ID · v0.2.0 #58 新增 HELM-IMG-001~006）

| 测试 ID | 文件 | 测试名 | 断言 |
|---------|------|--------|------|
| HELM-LC-001 | helm/adapter-langchain/values.yaml | test_helm_langchain_image_tag_format | tag = `v0.2.0-0.2.0-py3.12` 模板匹配（framework_version = §3.5 min_version） |
| HELM-LC-002 | helm/adapter-langchain/values.yaml | test_helm_langchain_resources_standard | CPU request 200m / limit 1 |
| HELM-LC-003 | helm/adapter-langchain/values.yaml | test_helm_langchain_security_context_restricted | Pod Security Standard: restricted 全部开启 |
| HELM-LC-DEPLOY-001 | helm/adapter-langchain/templates/deployment.yaml | test_helm_langchain_two_container_pod | adapter + agent 两容器 |
| HELM-LC-DEPLOY-002 | helm/adapter-langchain/templates/deployment.yaml | test_helm_langchain_env_var_superteam_adapter_framework | env `SUPERTEAM_ADAPTER_FRAMEWORK=langchain` |
| HELM-LC-DEPLOY-003 | helm/adapter-langchain/templates/deployment.yaml | test_helm_langchain_termination_grace_30s | `terminationGracePeriodSeconds: 30` |
| HELM-AG-001 ~ HELM-AG-DEPLOY-003 | autogen | 同上 pattern | autogen image + 标准 resources |
| HELM-CR-001 | helm/adapter-crewai/values.yaml | test_helm_crewai_resources_highest | CPU request 300m / limit 2；memory request 384Mi / limit 1Gi |
| HELM-CR-002 ~ HELM-CR-DEPLOY-003 | crewai | 同上 pattern | crewai image + 高 resources |
| HELM-SK-001 ~ HELM-SK-DEPLOY-003 | semantic_kernel | 同上 pattern | SK image + 标准 resources |
| HELM-ST-001 ~ HELM-ST-DEPLOY-003 | strands | 同上 pattern | strands image + 标准 resources |
| HELM-SM-001 ~ HELM-SM-DEPLOY-003 | smolagents | 同上 pattern | smolagents image + 标准 resources |
| HELM-RBAC-001 | helm/adapter-shared/templates/clusterrole.yaml | test_rbac_adapters_events_create | verbs: [get, list, watch, create, update, patch] |
| HELM-RBAC-002 | helm/adapter-shared/templates/clusterrole.yaml | test_rbac_adapters_status_update | status subresource |
| HELM-RBAC-003 | helm/adapter-shared/templates/clusterrole.yaml | test_rbac_leases_for_leader_election | coordination.k8s.io/leases |
| HELM-RBAC-004 | helm/adapter-shared/templates/clusterrolebinding.yaml | test_rbac_binding_to_service_account | ClusterRoleBinding → adapter SA |
| HELM-NP-001 | helm/adapter-shared/templates/networkpolicy.yaml | test_networkpolicy_ingress_8080_from_namespace_selector | port 8080 + namespaceSelector |
| HELM-NP-002 | helm/adapter-shared/templates/networkpolicy.yaml | test_networkpolicy_egress_k8s_api | 443 to kube-dns |
| HELM-NP-003 | helm/adapter-shared/templates/networkpolicy.yaml | test_networkpolicy_egress_otel_collector | 4317 to otel-collector |
| HELM-NP-004 | helm/adapter-shared/templates/networkpolicy.yaml | test_networkpolicy_egress_localhost_agent | 7080 to localhost（agent 同 Pod） |
| HELM-SM-001 | helm/adapter-shared/templates/servicemonitor.yaml | test_servicemonitor_interval_30s | interval: 30s |
| HELM-SM-002 | helm/adapter-shared/templates/servicemonitor.yaml | test_servicemonitor_framework_label_present | label `framework: {name}` |
| HELM-SM-003 | helm/adapter-shared/templates/servicemonitor.yaml | test_servicemonitor_metrics_path_/metrics | path: `/metrics` |
| HELM-IMG-001 | helm/adapter-langchain/values.yaml | test_image_tag_matches_version_matrix_langchain | image tag 中 `{framework_version}` == §3.5 `VERSION_MATRIX["langchain"].min_version`（`0.2.0`） |
| HELM-IMG-002 | helm/adapter-autogen/values.yaml | test_image_tag_matches_version_matrix_autogen | == `VERSION_MATRIX["autogen"].min_version`（`0.4.0`） |
| HELM-IMG-003 | helm/adapter-crewai/values.yaml | test_image_tag_matches_version_matrix_crewai | == `VERSION_MATRIX["crewai"].min_version`（`0.80.0`） |
| HELM-IMG-004 | helm/adapter-sk/values.yaml | test_image_tag_matches_version_matrix_sk | == `VERSION_MATRIX["sk"].min_version`（`1.30.0`） |
| HELM-IMG-005 | helm/adapter-strands/values.yaml | test_image_tag_matches_version_matrix_strands | == `VERSION_MATRIX["strands"].min_version`（`0.1.0`） |
| HELM-IMG-006 | helm/adapter-smolagents/values.yaml | test_image_tag_matches_version_matrix_smolagents | == `VERSION_MATRIX["smolagents"].min_version`（`1.10.0`） |

---

## 10. 测试策略 + 工具链文件级契约（继承 L2-3 Spec §12-§13 · 200 测试 ID + 6 重静态门禁）

### 10.1 测试 ID 总计矩阵（继承 L2-3 Spec §12.8 · 81 v0.2 / 159 v1.0 · v0.2.0 #58 修正为 200）

| 层级 | v0.2 ID | v1.0 ID | L3-3 已落地（§1-§9） | L3-3 本节（§10） | 累计 |
|------|--------:|--------:|----------------------:|-----------------:|------:|
| UT（adapter-sdk） | 48 | 48 | SDK-PROT 15 + SDK-MOD 8 + SDK-CONV 10 + SDK-VER 4 + SDK-INT 3 + SDK-LC 8 = 48 | OBS-METRICS 8 + OBS-TRACING 6 + OBS-LOGGING 5 + RETRY 12 + ERR-MAP 8 = 39 | **87** |
| UT（framework · 各 6 framework × 3 文件） | - | 24 | LC/AG/CR/SK/ST/SM × 9 = 54 | （已计入 §1.3.2） | **54** |
| IT | 12 | 36 | LC 5 + AG 5 + CR 5 + SK 5 + ST 5 + SM 5 = 30 | SDK-CFG 8 + SDK-LOAD 6 = 14 | **44** |
| Golden | 10 | 60 | - | - | **0**（待后续 §12 单独落地） |
| Conformance | 5 | 5 | - | 5（CF-A2A-001~005 适配 §7 + §8） | **5** |
| E2E | 2 | 6 | - | 6 framework × 1 = 6 | **6** |
| Property | 4 | 4 | - | 4（PROP-ENV / PROP-FSM / PROP-CARD / PROP-RETRY） | **4** |
| **合计** | **81** | **159** | **132** | **68** | **200** |

**注**：L3-3 累计 **200 测试 ID**（已超过 v1.0 目标 159；多出的 41 来自 L3-3 文件级细化——如 `test_redact_sensitive_9_keys` 等 9 项敏感字段单测，以及 v0.2.0 #58 补入的 SDK-LC 8 + SDK-PROT-013~015 3 + SDK-RTY-007~008 2 = 13 项）。**HELM-* 42 ID（§9.6）为部署面独立计数，不计入本表 200**。

### 10.2 6 重静态门禁（继承 L2-3 Spec §13.2）

| # | 工具 | 用途 | 触发时机 | 失败行为 | 测试 ID |
|---|------|------|----------|----------|--------|
| 1 | **uv sync --frozen** | lockfile 一致性 | pre-commit + CI | CI 失败 | TOOL-001 |
| 2 | **ruff format** | 代码格式化（line-length=100） | pre-commit + CI | CI 失败 | TOOL-002 |
| 3 | **ruff check** | lint（含 ST-ADAPTER-BOUNDARY 自定义规则） | pre-commit + CI | CI 失败 | TOOL-003 |
| 4 | **pyright --strict** | 类型检查（strict mode） | CI | CI 失败 | TOOL-004 |
| 5 | **bandit** | Python 安全扫描 | CI | CI 失败（high severity） | TOOL-005 |
| 6 | **pip-audit** | Python 依赖漏洞扫描 | CI（pre-build） | CI 失败（high CVSS） | TOOL-006 |

**Ruff 自定义规则 `ST-ADAPTER-BOUNDARY`**（planned）：
```python
# ruff 自定义规则伪代码
# 规则 ID: ST-ADAPTER-BOUNDARY
# 检测范围：
#   1. `packages/adapter-sdk/src/superteam_a2a/adapter/`（不含 `framework_adapters/`）禁 import framework SDK
#      例外：`_internals.py` + `protocol.py` + `loader.py` 允许 `import importlib.metadata`
#   2. `packages/operator-core/src/superteam_a2a/operator/` 禁 import `superteam_a2a.adapter`
#   3. 6 framework 子包内允许 import 对应 framework SDK
```

### 10.3 测试工具链（继承 L2-3 Spec §13.3）

```bash
# adapter-sdk 单元测试（≥ 95% 覆盖）
cd packages/adapter-sdk
uv run pytest tests/unit/ -v \
  --cov=supteam_a2a.adapter \
  --cov-fail-under=95

# framework adapter 集成测试（≥ 80% 覆盖）
cd packages/adapter-{framework}
uv run pytest tests/integration/ -v \
  --cov=supteam_a2a.adapter_{framework} \
  --cov-fail-under=80

# Conformance 测试（依赖 a2a-python conformance 套件）
uv run pytest tests/conformance/ -v --tb=short

# E2E 测试（kind 集群 · 6 framework 各自）
uv run pytest tests/e2e/ -v --cluster=kind --framework={framework}

# Property 测试（Hypothesis · 4 ID）
uv run pytest tests/property/ -v --hypothesis-seed=0
```

### 10.4 测试文件镜像清单（与 L3-1 70 文件镜像同级别）

| 类别 | 文件数 | 路径模式 |
|------|------:|---------|
| `tests/unit/`（adapter-sdk 12 文件 SDK） | 12 | `packages/adapter-sdk/tests/unit/test_{protocol,models,converter,version,_internals,config,loader,lifecycle,observability/metrics,observability/tracing,observability/logging,retry,errors_mapping}.py` |
| `tests/unit/`（framework · 6 × 3 文件） | 18 | `packages/adapter-{framework}/tests/unit/test_{adapter,converter,errors}.py` |
| `tests/integration/`（6 framework） | 6 | `packages/adapter-{framework}/tests/integration/test_{framework}_e2e.py` |
| `tests/conformance/` | 1 | `packages/adapter-sdk/tests/conformance/test_a2a_compat.py` |
| `tests/e2e/`（6 framework） | 6 | `packages/adapter-{framework}/tests/e2e/test_k8s_e2e.py` |
| `tests/property/` | 1 | `packages/adapter-sdk/tests/property/test_fuzz.py` |
| `tests/helm/`（Helm template 渲染验证） | 1 | `packages/adapter-sdk/tests/helm/test_helm_render.py`（验证 §9 12 文件渲染合法） |
| **合计** | **45** | （与 200 测试 ID + §9.6 42 HELM ID 一一对应） |

### 10.5 uv workspace 布局（继承 ADR-0005 §13.1）

```
superteam-a2a/
├── packages/
│   ├── adapter-sdk/                  # 本 L3-3 Spec 主体
│   │   ├── pyproject.toml
│   │   ├── src/superteam_a2a/adapter/
│   │   │   ├── __init__.py
│   │   │   ├── _internals.py
│   │   │   ├── protocol.py
│   │   │   ├── models.py
│   │   │   ├── converter.py
│   │   │   ├── version.py
│   │   │   ├── config.py
│   │   │   ├── loader.py
│   │   │   ├── errors.py
│   │   │   ├── observability/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── metrics.py
│   │   │   │   ├── tracing.py
│   │   │   │   └── logging.py
│   │   │   ├── retry.py
│   │   │   └── errors_mapping.py
│   │   └── tests/
│   └── operator-core/                # L3-1（已 v0.2.0）
├── adapters/                         # 6 framework 子包（独立仓库 + PyPI 发布）
│   ├── adapter-langchain/
│   ├── adapter-autogen/
│   ├── adapter-crewai/
│   ├── adapter-semantic-kernel/
│   ├── adapter-strands/
│   └── adapter-smolagents/
├── helm/
│   ├── adapter-langchain/
│   ├── adapter-autogen/
│   ├── adapter-crewai/
│   ├── adapter-semantic-kernel/
│   ├── adapter-strands/
│   ├── adapter-smolagents/
│   └── adapter-shared/               # RBAC + NetworkPolicy + ServiceMonitor
├── pyproject.toml                    # uv workspace 根
└── uv.lock
```

### 10.6 Dockerfile 多阶段模板（继承 L2-3 Spec §8 + ADR-0005 §2.2 + §9.3）

```dockerfile
# packages/adapter-{framework}/Dockerfile（每 framework 独立 base 镜像）
# 继承 L2-3 Spec §8.1 策略 A：每 framework 独立 base 镜像（推荐）

# Stage 1: builder（含 uv）
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages/adapter-sdk/ ./packages/adapter-sdk/
COPY packages/adapter-{framework}/ ./packages/adapter-{framework}/
RUN uv sync --frozen --no-dev --package superteam-a2a-adapter-{framework}

# Stage 2: runtime（精简 · 仅 framework SDK + adapter-sdk）
FROM python:3.12-slim-bookworm AS runtime
RUN useradd --create-home --uid 1000 adapter
WORKDIR /home/adapter

# framework SDK 与 adapter-sdk 仅复制 site-packages（不复制源码）
COPY --from=builder /app/.venv/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --chown=adapter:adapter packages/adapter-{framework}/src/superteam_a2a/adapter_{framework}/ /home/adapter/app/

USER 1000:1000
EXPOSE 8080
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SUPERTEAM_ADAPTER_FRAMEWORK={framework}

ENTRYPOINT ["python", "-m", "supteam_a2a.adapter_{framework}"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/healthz', timeout=2).raise_for_status()" || exit 1
```

### 10.7 §10 测试 ID 矩阵（30 ID）

| 测试 ID | 文件 | 测试名 | 断言 |
|---------|------|--------|------|
| TOOL-001 | pyproject.toml | test_uv_sync_frozen_succeeds | `uv sync --frozen` 退出码 0 |
| TOOL-002 | ruff format | test_ruff_format_check_no_diff | `ruff format --check` 无 diff |
| TOOL-003 | ruff check | test_ruff_check_passes_with_st_adapter_boundary | 自定义规则检测业务层无 framework SDK import |
| TOOL-004 | pyright | test_pyright_strict_no_errors | `pyright --strict` 退出码 0 |
| TOOL-005 | bandit | test_bandit_no_high_severity | high severity 漏洞 = 0 |
| TOOL-006 | pip-audit | test_pip_audit_no_high_cvss | CVSS ≥ 7.0 漏洞 = 0 |
| HELM-RENDER-001 | tests/helm/test_helm_render.py | test_helm_render_all_6_frameworks | 6 framework Deployment 模板 `helm template` 渲染成功 |
| HELM-RENDER-002 | tests/helm/test_helm_render.py | test_helm_render_validates_kubernetes_schema | 渲染输出符合 K8s 1.28+ schema |
| HELM-RENDER-003 | tests/helm/test_helm_render.py | test_helm_render_no_unresolved_placeholders | 无 `{{ ... }}` 未解析占位符 |
| CF-A2A-001 | tests/conformance/test_a2a_compat.py | test_conformance_with_google_a2a_conformance_suite | 与 google-a2a/conformance 100% 兼容 |
| CF-A2A-002 | tests/conformance/test_a2a_compat.py | test_agent_card_schema_matches_l2_1 | 6 framework Card 符合 L2-1 AgentCard schema |
| CF-A2A-003 | tests/conformance/test_a2a_compat.py | test_jsonrpc_2_0_wire_compat | JSON-RPC 2.0 wire format 一致 |
| CF-A2A-004 | tests/conformance/test_a2a_compat.py | test_error_codes_minus_32001_to_minus_32007 | 7 错误码常量值与 L3-2 §10 一致 |
| CF-A2A-005 | tests/conformance/test_a2a_compat.py | test_agent_card_path_well_known | `/.well-known/agent.json` 路径返回 AgentCard |
| PROP-ENV-001 | tests/property/test_fuzz.py | test_envelope_schema_round_trip | hypothesis 生成 1000 个 envelope 异常字段应被拒绝 |
| PROP-FSM-001 | tests/property/test_fuzz.py | test_task_state_machine_invariant | 任意状态转换序列合法 |
| PROP-CARD-001 | tests/property/test_fuzz.py | test_card_introspection_fuzz_does_not_crash | framework introspection fuzz 输入不导致 SDK 崩溃 |
| PROP-RETRY-001 | tests/property/test_fuzz.py | test_retry_count_within_bounds | 任意错误码序列重试次数与延迟在 [min, max] 区间 |
| E2E-FW-001 ~ E2E-FW-006 | tests/e2e/test_k8s_e2e.py（6 文件） | test_e2e_kind_{framework}_hello_world | 6 framework × kind 集群 hello-world 端到端 |
| COV-001 | pytest-cov | test_adapter_sdk_coverage_ge_95 | `pytest-cov` 报告 ≥ 95% |
| COV-002 | pytest-cov | test_framework_adapter_coverage_ge_80 | 6 framework 子包覆盖率 ≥ 80% |
| TOOL-CHAIN-001 | - | test_pre_commit_runs_all_6_tools | pre-commit 钩子串行执行 6 门禁 |
| TOOL-CHAIN-002 | - | test_ci_workflow_sequential_6_steps | `.github/workflows/ci.yml` 含 6 步骤且均 must-pass |
| TOOL-CHAIN-003 | Dockerfile | test_dockerfile_multi_stage_two_stage | builder + runtime 2 stage |
| TOOL-CHAIN-004 | Dockerfile | test_dockerfile_non_root_user_uid_1000 | `USER 1000:1000` 存在 |
| TOOL-CHAIN-005 | Dockerfile | test_dockerfile_healthcheck_command | `HEALTHCHECK` 含 `http://localhost:8080/healthz` |
| TOOL-CHAIN-006 | pyproject.toml | test_pyproject_python_version_3_12 | `requires-python = ">=3.12,<3.13"` |
| TOOL-CHAIN-007 | pyproject.toml | test_pyproject_hatchling_backend | build-backend = `hatchling` |
| TOOL-CHAIN-008 | uv.lock | test_uv_lock_present_and_committed | `uv.lock` 在仓库 + git tracked |

---

## 附录 A：跨模块引用清单（v0.2.0 完整版）

**说明**：本附录覆盖 L3-3 Spec v0.2.0 全部 §0-§10 + 附录 B 引用的 6 子表 30 行；每条 = 文档路径 + 章节 + 引用类型（MUST/SHOULD/MAY）+ 同步状态。

### A.1 L1 Architecture + Spec

| # | 文档路径 | 章节 | 引用类型 | 同步状态 |
|---|----------|------|----------|----------|
| 1 | `docs/design/L1-architecture.md` | §3.5 适配层 | MUST | ✅ v0.2.0 已对齐 |
| 2 | `docs/design/L1-architecture.md` | §4.3 C-3 模块 ID | MUST | ✅ v0.2.0 已对齐 |
| 3 | `docs/spec/L1-system-spec.md` | §16 验收清单 | SHOULD | ✅ v0.2.0 已对齐 |

### A.2 L2-3 Adapter 模块 Spec

| # | 文档路径 | 章节 | 引用类型 | 同步状态 |
|---|----------|------|----------|----------|
| 4 | `docs/design/L2-modules/L2-adapter.md` | §3-§14 Design v0.2.0（上游权威） | MUST | ✅ v0.2.0 已对齐（#35 评审通过） |
| 5 | `docs/spec/L2-module-specs/L2-adapter.md` | §3-§15 Spec v0.2.0（上游权威） | MUST | ✅ v0.2.0 已对齐（#37 评审通过） |
| 6 | `docs/spec/L2-module-specs/L2-adapter.md` | §7 可观测性 | MUST | ✅ v0.2.0 → L3-3 §7 落地 |
| 7 | `docs/spec/L2-module-specs/L2-adapter.md` | §10.4 错误模型 + Retryable 矩阵 | MUST | ✅ v0.2.0 → L3-3 §8 落地 |
| 8 | `docs/spec/L2-module-specs/L2-adapter.md` | §11 Helm values | MUST | ✅ v0.2.0 → L3-3 §9 落地 |
| 9 | `docs/spec/L2-module-specs/L2-adapter.md` | §12 测试策略 | MUST | ✅ v0.2.0 → L3-3 §10 落地 |
| 10 | `docs/spec/L2-module-specs/L2-adapter.md` | §13 工具链与部署 | MUST | ✅ v0.2.0 → L3-3 §10.2-§10.6 落地 |

### A.3 ADR

| # | 文档路径 | 章节 | 引用类型 | 同步状态 |
|---|----------|------|----------|----------|
| 11 | `docs/adr/0005-python-first-technology-stack.md` | §3.3 Adapter SDK 模块映射 | MUST | ✅ v0.5.0 已对齐 |
| 12 | `docs/adr/0005-python-first-technology-stack.md` | §6 接口与生命周期 | MUST | ✅ v0.5.0 已对齐 |
| 13 | `docs/adr/0005-python-first-technology-stack.md` | §7 安全 | MUST | ✅ v0.5.0 已对齐 |
| 14 | `docs/adr/0005-python-first-technology-stack.md` | §9.3 容器镜像策略 A | MUST | ✅ v0.5.0 → L3-3 §10.6 Dockerfile |
| 15 | `docs/adr/0005-python-first-technology-stack.md` | §10 可观测性 | MUST | ✅ v0.5.0 → L3-3 §7 |
| 16 | `docs/adr/0005-python-first-technology-stack.md` | §13.1 uv workspace 布局 | MUST | ✅ v0.5.0 → L3-3 §10.5 |

### A.4 Constitution

| # | 文档路径 | 章节 | 引用类型 | 同步状态 |
|---|----------|------|----------|----------|
| 17 | `docs/CONSTITUTION.md` | §3.8 Adapter SDK 边界 | MUST | ✅ v0.5.0 已对齐 |
| 18 | `docs/CONSTITUTION.md` | §6 安全（不直接 mTLS，由 L3-1 admission 拦截） | MUST | ✅ v0.5.0 已对齐 |
| 19 | `docs/CONSTITUTION.md` | §7 可观测性约束 | MUST | ✅ v0.5.0 → L3-3 §7 |
| 20 | `docs/CONSTITUTION.md` | §9.7 测试覆盖率 ≥ 95% / ≥ 80% | MUST | ✅ v0.5.0 → L3-3 §10.1 |
| 21 | `docs/CONSTITUTION.md` | §13.1 uv workspace | MUST | ✅ v0.5.0 → L3-3 §10.5 |
| 22 | `docs/CONSTITUTION.md` | §13.6 6 framework 矩阵 | MUST | ✅ v0.5.0 → L3-3 §1.3 / §5 |
| 23 | `docs/CONSTITUTION.md` | §15.5 错误传播 3 通道 | MUST | ✅ v0.5.0 → L3-3 §8.3 propagate_error |

### A.5 配套 L3 Spec

| # | 文档路径 | 章节 | 引用类型 | 同步状态 |
|---|----------|------|----------|----------|
| 24 | `docs/spec/L3-file-specs/L3-operator-core.md` | v0.2.0 Operator Core 文件级 Spec | MUST | ✅ v0.2.0 已对齐（#56 评审通过） |
| 25 | `docs/spec/L3-file-specs/L3-a2a-core.md` | v0.2.0 A2A Core 文件级 Spec §6 A2AClient | MUST | ✅ v0.2.0 已对齐（#54 评审通过） |
| 26 | `docs/spec/L3-file-specs/L3-a2a-core.md` | §9 15 Prometheus 指标 | MUST | ✅ v0.2.0 → L3-3 §7.5 4 复用 |
| 27 | `docs/spec/L3-file-specs/L3-a2a-core.md` | §10 24 错误码 enum | MUST | ✅ v0.2.0 → L3-3 §8.3 RETRYABLE_MATRIX |
| 28 | `docs/spec/L3-file-specs/L3-hello-agent.md` | v0.2.0 Hello Agent 文件级 Spec §3-§7 + 25 ID | SHOULD | ✅ v0.2.0 已对齐（#61 评审通过 · [评审报告](../../reviews/l3-4-hello-agent-spec-review.md) §A-§J 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项） |

### A.6 归档基线

| # | 文档路径 | 章节 | 引用类型 | 同步状态 |
|---|----------|------|----------|----------|
| 29 | `docs/archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md` | 完整 Go baseline（已归档 · 2026-07-24） | REFERENCE | ✅ 归档完成（README 备注覆盖丢失） |
| 30 | `docs/archive/pre-python-2026-07-24/README.md` | 归档元数据登记 | REFERENCE | ✅ #57 L3-3 启动 + #35 L2-3 评审 + #21 L2-1 评审 三次覆盖事件登记 |

---

## 附录 B：ADR / Constitution 引用矩阵（v0.2.0 完整版 · 5 子表 49 行）

**说明**：本附录对 L3-3 Spec 全部 MUST / SHOULD / MAY 强度分级约束 + ADR 章节 + Constitution 章节进行追溯矩阵化，确保每条规范有出处。

### B.1 架构与部署（11 条）

| # | 主题 | 强度 | ADR 章节 | Constitution 章节 |
|---|------|------|----------|-------------------|
| 1 | 单 SDK + 6 framework 子包形态 | MUST | ADR-0005 §3.3 | §3.8 + §13.6 |
| 2 | uv workspace 布局 | MUST | ADR-0005 §13.1 | §13.1 |
| 3 | Python 3.12 strict | MUST | ADR-0005 §2.1 | §13.1 |
| 4 | pyright --strict 类型检查 | MUST | ADR-0005 §13.2 | §13.2 |
| 5 | ruff 自定义规则 ST-ADAPTER-BOUNDARY | MUST | ADR-0005 §13.2 | §13.2 + §3.7 |
| 6 | Pod Security Standard: restricted | MUST | ADR-0005 §7 | §6 |
| 7 | 6 framework 独立 base 镜像（策略 A） | MUST | ADR-0005 §9.3 | §9.3 |
| 8 | Dockerfile 多阶段（builder + runtime） | MUST | ADR-0005 §9.3 | §9.3 |
| 9 | USER 1000:1000 non-root | MUST | ADR-0005 §7 | §6 |
| 10 | ConfigMap + Secret 引用（不内嵌） | MUST | ADR-0005 §7 | §6 |
| 11 | 同进程 plugin / sidecar 双拓扑（embedded 切换） | MUST | ADR-0005 §6 | §3.7 + §9.3 |

### B.2 接口与生命周期（10 条）

| # | 主题 | 强度 | ADR 章节 | Constitution 章节 |
|---|------|------|----------|-------------------|
| 12 | FrameworkAdapter Protocol 5 方法（`load_agent` / `to_agent_card` / `from_agent_card` / `invoke` / `health_check`，落地于 §3.2） | MUST | ADR-0005 §6 | §3.7 |
| 13 | AgentCardConverter Protocol 2 方法（`framework_to_card_skill` / `card_skill_to_framework`，落地于 §3.2） | MUST | ADR-0005 §6 | §3.7 |
| 14 | entry_points 动态加载 6 framework | MUST | ADR-0005 §3.3 | §3.7 |
| 15 | runtime_checkable Protocol 校验 | MUST | ADR-0005 §6 | §3.7 |
| 16 | A2AClient 复用 L3-2 §6（不重写 wire contract） | MUST | ADR-0005 §3.1 | §3.7 |
| 17 | Lifecycle 11 步启动序列（落地于 §3.7 + `lifecycle.py`） | MUST | ADR-0005 §6 | §3.7 |
| 18 | Lifecycle.stop 30s grace period（落地于 §3.7 `Lifecycle.stop`） | MUST | ADR-0005 §6 | §9.3 |
| 19 | readiness probe 5 周期 | SHOULD | ADR-0005 §6 | §3.7 |
| 20 | lifespan 单进程模式（httpx 进程级单例） | MUST | ADR-0005 §6 | §3.7 |
| 21 | mTLS cert 热更新（与 L3-1 协同） | MUST | ADR-0005 §7 | §6 |

### B.3 错误处理（10 条）

| # | 主题 | 强度 | ADR 章节 | Constitution 章节 |
|---|------|------|----------|-------------------|
| 22 | 7 错误码 enum（-32001 ~ -32007 · L3-2 §10 继承） | MUST | ADR-0005 §10 | §15.5 |
| 23 | AdapterError 基类 + 7 子类（Retryable/NonRetryable/Permanent/Config/Auth/Timeout/Framework/Version） | MUST | ADR-0005 §10 | §15.5 |
| 24 | Retryable 矩阵 4 True + 3 False | MUST | ADR-0005 §10 | §15.5 |
| 25 | 5 类 Tenacity 策略（network/5xx/rate_limit/timeout/framework） | MUST | ADR-0005 §10 | §15.5 |
| 26 | jitter 全随机 0.5x-1.5x | SHOULD | ADR-0005 §10 | §15.5 |
| 27 | 错误传播 3 通道（structlog + Prometheus + OTel） | MUST | ADR-0005 §10 | §15.5 |
| 28 | framework 异常 → AdapterError 映射表（map_framework_exception） | MUST | ADR-0005 §10 | §15.5 |
| 29 | 永久错误不重试（is_retryable=False） | MUST | ADR-0005 §10 | §15.5 |
| 30 | 重试耗尽包装为 AdapterRetryableError | MUST | ADR-0005 §10 | §15.5 |
| 31 | `AdapterError.to_jsonrpc_error()` 含 framework_error（落地于 §3.2 末尾） | MUST | ADR-0005 §10 | §15.5 |

### B.4 安全（10 条）

| # | 主题 | 强度 | ADR 章节 | Constitution 章节 |
|---|------|------|----------|-------------------|
| 32 | 不直接处理 mTLS（由 L3-1 admission 拦截） | MUST | ADR-0005 §7 | §6 |
| 33 | 9 项敏感字段脱敏（api_key 等） | MUST | ADR-0005 §7 | §6.5 |
| 34 | Memory / Knowledge content 永不过普通日志 | MUST | ADR-0005 §7 | §6.5 |
| 35 | USER 1000:1000 + readOnlyRootFilesystem | MUST | ADR-0005 §7 | §6 |
| 36 | seccompProfile: RuntimeDefault | MUST | ADR-0005 §7 | §6 |
| 37 | capabilities drop ALL | MUST | ADR-0005 §7 | §6 |
| 38 | NetworkPolicy ingress/egress 限制 | MUST | ADR-0005 §7 | §6 |
| 39 | RBAC ClusterRole 最小权限（仅 adapters/events + status + leases） | MUST | ADR-0005 §7 | §6 |
| 40 | ConfigMap 热加载 checksum annotation | SHOULD | ADR-0005 §7 | §6 |
| 41 | Secret 引用 + readOnly mount | MUST | ADR-0005 §7 | §6 |

### B.5 可观测性与测试（8 条）

| # | 主题 | 强度 | ADR 章节 | Constitution 章节 |
|---|------|------|----------|-------------------|
| 42 | 6 framework 独立 Prometheus 指标（Counter/Histogram/Gauge） | MUST | ADR-0005 §10 | §7 |
| 43 | 4 复用 L3-2 §9 runtime 指标（不重复定义） | MUST | ADR-0005 §10 | §7 |
| 44 | OTel 4 层 Span 结构 | SHOULD | ADR-0005 §10 | §7 |
| 45 | structlog JSON + 7 强制字段 | MUST | ADR-0005 §10 | §7 |
| 46 | 单进程 mode（无 prometheus multiprocess） | MUST | ADR-0005 §10 | §7 |
| 47 | 200 测试 ID（UT 141 + IT 44 + CF 5 + E2E 6 + PROP 4；另 §9.6 42 HELM-* 独立计数） | MUST | ADR-0005 §13.2 | §9.7 |
| 48 | adapter-sdk ≥ 95% / framework ≥ 80% 覆盖率 | MUST | ADR-0005 §13.2 | §9.7 |
| 49 | 6 重静态门禁（uv sync + ruff + pyright + bandit + pip-audit + ST-ADAPTER-BOUNDARY） | MUST | ADR-0005 §13.2 | §9.7 + §13.2 |

---

## 文档元数据与后续入口

### M.1 版本与状态

| 字段 | 值 |
|---|---|
| 版本 | **v0.2.0** |
| 状态 | ✅ **已通过独立评审并升级**（#56 骨架 + #57 §3-§6 + #57 §7-§10/附录 A/B + #58 评审 + 关注项 4-9 PR 同步修正）—— §0-§10 + 附录 A（30 行 6 子表）+ 附录 B（49 行 5 子表）全部落地；累计 200 测试 ID（+ §9.6 42 HELM-*）/ 45 文件镜像清单 / 42 文件级契约 |
| 上游 | L2-3 Adapter Design + Spec v0.2.0（#35 + #37 评审通过） |
| 同级已通过 | L3-1 Operator Core v0.2.0 (#56) + L3-2 A2A Core v0.2.0 (#54) |
| supersedes | L2-3 v0.1.0 Go baseline 实现条款；L3-2 wire 引用继续有效 |
| 评审报告 | [`docs/reviews/l3-3-adapter-sdk-spec-review.md`](../../reviews/l3-3-adapter-sdk-spec-review.md)（#58 · 38.8KB / §A-§P 16 节 / 10 维度全 PASS / 0 阻塞项 / 9 关注项 / 4 建议项） |
| 当前变更边界 | 本 Spec 已达 v0.2.0，**可作为 L4 实施输入**；后续修改走 v0.2.1 微同步或 ADR |

### M.2 落地记录

| 日期 / 会话 | 增量 | 结果 |
|---|---|---|
| 2026-07-28 #56 | L3-1 v0.2.0 通过 + L3-3 启动 | L3 阶段 1/4 完成 |
| 2026-07-28 #57 | L3-3 v0.2-draft 骨架稿 + 13 边界规则 + 6 框架独立 metrics + 11 文件 SDK + 24 framework 子包文件清单 | §0-§2 + 附录 A/B 占位 |
| 2026-07-28 #57（本会话 #2） | L3-3 §3-§6 补完：FrameworkAdapter Protocol（466 行 · 5 生命周期方法）+ AgentCardConverter（322 行 · 6 框架字段映射）+ 6 framework 子包 24 文件级契约 + 4 层配置优先级 + 6 framework 动态加载 + 累计 1206 行 / 68KB / 84 测试 ID | §3-§6 完整版 + §1.3 文件清单 22 → 24 |
| 2026-07-28 #57（本会话 #3） | L3-3 §7-§10 + 完整附录 A/B 补完：§7 observability 4 文件 + 19 OBS-* 测试 ID + §8 retry + errors 2 文件 + 18 RETRY/ERR-MAP 测试 ID + §9 Helm values 12 文件 + 4 共享模板 + 36 HELM-* 测试 ID + §10 testing + toolchain 6 重静态门禁 + Dockerfile 多阶段 + uv workspace + 30 TOOL/HELM-RENDER/CF/PROP/E2E/COV 测试 ID + 附录 A 6 子表 30 行 + 附录 B 5 子表 49 行 + 累计 187 测试 ID / 44 文件镜像清单 | v0.2-draft-full 完整版；进入独立评审 |
| **2026-07-29 #58** | **评审通过 + 升级 v0.2.0 + 评审 §M 关注项 4-9 PR 同步修正**：附录 B.2 row 12/13 Protocol 方法名与方法数对齐 §3.2；B.2 row 17/18 + B.3 row 31 补落地位置；**新增 §3.7 Lifecycle 11 步启动序列 + `lifecycle.py`（SDK 第 12 文件 · 8 SDK-LC ID）**；§3.2 补入 `Adapter` Protocol（3 方法）+ `AdapterError.to_jsonrpc_error()` wire 契约（3 SDK-PROT ID）；§8.2 补入 `create_retry_policy` 工厂（2 SDK-RTY ID）；`__all__` 14 → 18 符号；§9.4 6 framework image tag 全部对齐 §3.5 `VERSION_MATRIX.min_version` + 新增对齐矩阵与 6 个 HELM-IMG ID；全文 `ErrorCode.` → `AdapterErrorCode.`（17 处）；文件计数 41 → 42、测试 ID 187 → 200、镜像清单 44 → 45 全链路同步 | **v0.2.0**；关注项 1-3 + 4 项建议项移交 v0.2.1 / L4 第一周（见 §M.2 台账）；下一步：§F 6 步跨文档同步 → L3-4 Hello Agent |

**#58 评审关注项处理台账**（评审 §M 9 项 + 4 建议项）：

| 关注项 | 主题 | 本次处理 | 去向 |
|---|------|---------|------|
| 1 | 5 处命名/枚举漂移（子包路径 / retry_strategy 枚举 / metrics prefix / framework label / `supteam` vs `superteam`） | 部分：`ErrorCode` → `AdapterErrorCode` 统一 17 处 | **v0.2.1 微同步**（其余 4 处需与 L2-3 Spec 成对修改） |
| 2 | `ST-ADAPTER-BOUNDARY` Ruff 规则标注 planned 未落地 | 未处理 | **L4 实施第一周**（需实际插件实现，非文档变更） |
| 3 | §1.3.4 测试 ID 159 vs §10.1 偏差未交叉引用 | 已闭环：§1.3.4 改为 200 并注明 "+41 文件级细化"，§10.1 注同步 | ✅ 本次 |
| 4 | §B.2 row 12 FrameworkAdapter 方法名错误 | 已改为 `load_agent / to_agent_card / from_agent_card / invoke / health_check` | ✅ 本次 |
| 5 | §B.2 row 13 AgentCardConverter 方法数错误 | 已改为 2 方法 `framework_to_card_skill / card_skill_to_framework` | ✅ 本次 |
| 6 | §B.2 row 17 Lifecycle 11 步未落地 | 已新增 §3.7（11 步序列 + 步骤→文件映射 + `lifecycle.py` 契约 + 8 测试 ID） | ✅ 本次 |
| 7 | §B.3 row 31 `to_jsonrpc_error` 未落地 | 已在 §3.2 补入方法契约（wire 结构 + 脱敏约束 + 3 测试 ID） | ✅ 本次 |
| 8 | §9.4 image tag 与 §3.5 VERSION_MATRIX 5/6 不符 | 已按 min_version 更新 6 tag + 新增对齐矩阵 + HELM-IMG-001~006 | ✅ 本次 |
| 9 | public API 缺 4 项符号 | 已按**选项 A** 补齐（`Adapter` / `AdapterErrorCode` / `create_retry_policy` / `Lifecycle`），各自落地位置见 §1.2 表 | ✅ 本次 |
| 建议 1-4 | §1.3.4 行数 33→35 / `label_result` 4 vs 3 取值 / §10.4 import prefix / 附录 A.4 row 28 L3-4 回填 | 未处理 | **v0.2.1**（建议 4 在 L3-4 起草时回填） |

### M.3 下一会话固定入口

1. **§F 6 步跨文档同步**（本次升级后的必做动作 · 参照评审报告 §O）：F.1 L1 Architecture v0.2.0 §3.5 + §4.3（L3-3 文件级落地完成 + 42 文件清单）；F.2 L1 Spec v0.2.0 §16（200 测试 ID 文件级确认）；F.3 L2-3 Spec v0.2.0 附录 A（反向引用升级 L3-3 v0.2.0 + 评审链接）；F.4 L3-1 + L3-2 Spec 附录 A.5（L3-3 → v0.2.0 + 评审链接）；F.5 ROADMAP（L3 阶段 3/6 进度）；F.6 README + CONSTITUTION-CHANGELOG + archive/README.md。
2. **v0.2.1 微同步清单**（评审关注项 1 剩余 4 处 + 建议项 1-3）：framework 子包路径 vs Literal vs metrics label 三层映射；`retry_strategy` 枚举 §4.1 / §8.2 / §1.4 统一；metrics prefix `supteam_adapter_*` 统一；`supteam_a2a` vs `superteam_a2a` 包路径（需与 L2-3 Spec §2.1 成对修改）。
3. **L4 实施第一周**：`ST-ADAPTER-BOUNDARY` Ruff 插件实现（评审关注项 2 · 文档已标 MUST，需实际拦截能力）。
4. **L3-4 Hello Agent 启动**：基于 L3-1 v0.2.0 + L3-2 v0.2.0 + L3-3 v0.2.0（不依赖 framework adapter，纯 A2A ping/pong；独立会话），并回填附录 A.4 row 28 链接。

---

> **签署**：本 L3-3 Adapter SDK 文件级 Spec Python **v0.2.0** 由 #56（骨架）+ #57（§3-§10 + 附录 A/B）+ **#58（评审 + 关注项 4-9 PR 同步修正 + 升级）** 共同形成，依据 [L2-3 Adapter Spec v0.2.0](../../spec/L2-module-specs/L2-adapter.md)、[L2-3 Adapter Design v0.2.0](../../design/L2-modules/L2-adapter.md)、[L3-1 Operator Core v0.2.0](../../spec/L3-file-specs/L3-operator-core.md)、[L3-2 A2A Core v0.2.0](../../spec/L3-file-specs/L3-a2a-core.md)、[L2-3 Go baseline（已归档）](../../archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md) 与 Constitution v0.5.0 编写，并已通过 [#58 独立评审](../../reviews/l3-3-adapter-sdk-spec-review.md)（§A-§P 16 节 / 10 维度全 PASS / 0 阻塞项）。**本版可直接作为 L4 实施输入；关注项 1-2 与 4 项建议项按 §M.2 台账在 v0.2.1 / L4 第一周处理。**
