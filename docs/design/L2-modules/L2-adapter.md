# L2 模块设计：Adapter（框架适配层 · Python-first）

> **层级**：L2 — 模块设计
> **模块 ID**：C-3（Adapter，见 L1 v0.2.0 Architecture §4.1）
> **代码位置**：`packages/adapter-sdk/src/supteam_a2a/adapter/` + `adapters/{framework}/src/supteam_a2a/adapters/{framework}/`（**Python-first · ADR-0005 §13 工程布局**）
> **版本**:**v0.2.0**（Python 重写 · ADR-0005 触发；2026-07-26 升级；评审通过 [`docs/reviews/l2-3-adapter-python-review.md`](../../reviews/l2-3-adapter-python-review.md) §A-§P 10 维度全 PASS）
> **状态**:✅ **v0.2.0**（2026-07-26 #35 会话评审通过；0 阻塞项 · 3 关注项移交 L3-3 / Spec 起草 · 4 建议项；与 v0.1.0 Go baseline wire contract 完全继承）
> **supersedes**: v0.1.0 Go baseline（[`docs/reviews/l2-3-adapter-review.md`](../../reviews/l2-3-adapter-review.md) 2026-07-24 通过；**仅 supersede Go interface / Go package / Go 镜像块 / Go 静态编译 实现条款**；wire contract（Adapter 契约 / 5 行 YAML 原则 / 6 框架矩阵 / Card 转换 / 错误码 / 镜像策略）与 v0.1 业务语义**完全继续有效**）
> **配套 Spec**：[`docs/spec/L2-module-specs/L2-adapter.md`](../../spec/L2-module-specs/L2-adapter.md)（**v0.2.0 Python**；2026-07-26 #36 起草完整版 + #37 评审通过；114KB / 2705 行 / 14 节 + 2 附录；与本 Design 1-to-1 对应）
> **归档路径**（计划）：v0.1.0 Go baseline Design + Spec 将在 v0.2.0 评审通过后归档至 `docs/archive/pre-python-2026-07-24/L2-adapter-{design,spec}-v0.1.0-go-baseline.md`（与 L2-2 归档模式一致）
> **依据**：[`CONSTITUTION.md`](../../../CONSTITUTION.md) **v0.5.0** §2.2 多框架多元主义 + §3.7 反依赖 + §3.8 Python-first + §4.7 Golden Adapter + §7 可观测性 + §9.7 静态质量；[ADR-0005](../../adr/0005-python-first-technology-stack.md) §3.3 Adapter SDK + §6.3 GIL 与 CPU 工作 + §7 Operator 可靠性门禁 + §8 SDK 门禁 + §13 工程布局；[L1 Architecture v0.2.0](../L1-architecture.md) §3.5 运行时层 + §6 Adapter 架构 + §11.5 Python 性能预算；[L1 Spec v0.2.0](../../spec/L1-system-spec.md) §5 CRD + §15 部署；[L2-1 A2A Protocol v0.2.0](../L2-modules/L2-a2a-protocol.md) §3 包结构 + §4 compatibility adapter + §5 ASGI server
> **MVP 例外**: §14.5 适用

---

## 0. 阅读指南

本文档定义 `superteam-a2a` **L2-3 Adapter 模块**（运行时层 · C-3）的 **Python 实现设计**：typing.Protocol 契约、6 framework adapter matrix、同进程 plugin vs Sidecar 拓扑决策、镜像打包策略、Card 转换层、错误码、可观测性、测试矩阵。**不**涉及具体函数签名、JSON Schema 字段约束（这些在 L3-3 Spec 定义）；**不**涉及业务语义（wire contract 完全继承 v0.1.0）。

**读者**：L3-3 Spec 作者、framework adapter 贡献者、Operator Core 维护者、架构评审者。

**关键变化**（与 v0.1.0 Go baseline 对照）：

| 维度 | v0.1.0 Go | v0.2 Python |
|------|-----------|-------------|
| **Adapter 抽象** | Go `interface Adapter` | **Python `typing.Protocol` + ABC** |
| **HTTP server** | Go `net/http` | **ASGI（Uvicorn 单 worker）+ 官方 a2a-sdk** |
| **Card 转换** | Go struct 转换 | **Pydantic v2 + 官方 a2a-sdk `AgentCard` type** |
| **配置加载** | `client-go` ConfigMap | **`kubernetes_asyncio` + Pydantic Settings** |
| **HTTP client (A2A→Agent)** | `net/http` | **`httpx.AsyncClient` 进程级连接池** |
| **镜像基线** | `python:3.11-slim` + 静态 Go 二进制 | **`python:3.12-slim` + 多阶段（pyproject.toml + uv build）** |
| **错误码** | Go 常量 + `errors.New` | **StrEnum + `a2a-python` JSON-RPC error struct** |
| **可观测性** | `prometheus/client_golang` + `go.opentelemetry.io` | **`prometheus-client` + `opentelemetry-sdk` + `structlog`** |
| **测试** | `testing` + `gomock` | **`pytest` + `pytest-asyncio` + `respx` + `hypothesis`** |
| **framework SDK 桥接** | 经 gRPC / HTTP 跨进程 | **同进程 plugin（Python-native）或 Sidecar（非 Python）** |

**与 v0.1.0 Go baseline 关系**：
- v0.1.0 Go baseline 仍作为 **迁移业务语义输入**（已被顶部 ADR-0005 supersede 指针标记为「迁移输入」）
- 本 v0.2 设计 **完全替代** Go baseline 的 Python 实现决策（typing.Protocol + Pydantic + ASGI + uv workspace）
- 业务语义（6 框架矩阵 / 5 行 YAML / Card 转换失败处理 / 错误码范围 / 镜像策略 / 集成接口契约）与 v0.1.0 **完全一致**

---

## 1. 模块使命与边界

### 1.1 使命

L2-3 Adapter 是 `superteam-a2a` **运行时层（Runtime Layer）** 的实现子层，承载 **6 个 Agent framework（LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents）** 与 **A2A 协议** 之间的双向翻译：

1. **A2A Server 嵌入**：基于 L2-1 官方 `a2a-sdk` 与 `superteam_a2a.a2a.upstream` 边界，暴露 JSON-RPC 2.0 端点
2. **框架协议转换**：把 A2A `Message` / `Part` / `Task` 翻译为 framework 原生调用（LCEL Runnable / CrewAI kickoff / Kernel.invoke 等），再把 framework 输出翻译回 A2A `Artifact`
3. **Agent Card 转换**：把 framework 原生元数据（`agent.name` / `agent.tools` / `kernel.plugins`）转换为 A2A standard `AgentCard`（`/.well-known/agent.json`）
4. **配置注入**：从 K8s `Secret` / `ConfigMap` / env 三层优先级加载 framework 配置
5. **错误码映射**：framework 原生异常 → A2A 域错误码（含 Adapter 扩展错误 -32001 ~ -32099）
6. **可观测性埋点**：`supteam_adapter_*` Prometheus 指标 + OTel Span + JSON 结构化日志
7. **Golden Adapter 测试**：每 framework ≥ 5（v0.5）/ ≥ 10（v1.0）个 Golden Cases（宪法 §4.7 强制）

**单部署形态**：每 framework adapter 独立 Python 容器（`python:3.12-slim` 多阶段），与 Agent container 同 Pod 部署（Sidecar 模式）或同进程 plugin（Python-native framework 路径）；由 Operator Core 决策而非用户。

### 1.2 系统边界

**模块内**（v0.2 Python-first · 本设计详述）：
- 6 个 framework adapter 子包（LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents）+ contrib（v1.5+）
- `adapter-sdk` 通用抽象层（无 framework 依赖）：Adapter Protocol / FrameworkAdapter Protocol / Card 转换 / 配置加载 / 错误码 / 重试 / 可观测性 / 生命周期 hook
- A2A Server 嵌入封装（基于 L2-1 `a2a.upstream` SDK）
- 容器镜像打包（每 framework 独立 base + 共享 adapter-sdk）
- Pydantic v2 schema 表达 Adapter 配置 / Agent Card 元数据
- Helm values 完整配置面（per-framework image / resource / health check）
- 集成测试 ID 矩阵（每 framework ≥ 6 IT 起步 + Golden Cases）

**模块外**（其他 L2 模块负责）：
- ❌ Agent 业务逻辑实现（→ framework + Agent 作者）
- ❌ Operator 编排逻辑（→ L2-2 Operator Core）
- ❌ Knowledge / Memory 业务逻辑（→ L2-4 Knowledge / Memory）
- ❌ A2A 协议本身（→ L2-1 A2A Protocol — Adapter 只嵌入其 Server SDK）
- ❌ CRD 生命周期管理（→ L2-2 — Adapter 是被编排的资源）
- ❌ MCP 协议实现（→ 框架自带 MCP client，Adapter 不重复造轮子；宪法 §3.6）
- ❌ SSE Streaming 协议（→ L2-1 范围，v0.5+ 实现）

### 1.3 价值主张

| 维度 | 承诺 |
|------|------|
| **framework 贡献者** | 实现 `typing.Protocol` 即可；通用 SDK / Card 转换 / 错误码 / OTel 由 `adapter-sdk` 提供 |
| **Operator Core 维护者** | Adapter container 资源模型 + 启动 / 停止 / 重载 hook 标准化 |
| **Agent 作者** | 5 行 YAML（`framework` / `image` / `card` / `resources` / `healthCheck`）即可启用 |
| **运维者** | 标准 ASGI 进程；统一 `/metrics` `/healthz` `/readyz`；mTLS 透明 |
| **framework 升级** | 镜像 tag 锁版本（`{framework-version}-{adapter-version}-py{python-version}`），独立升级不影响其他 framework |

---

## 2. Adapter Python 实现决策（spike 风格 · ADR-0005 §8 前置门禁）

> **本节作为 L2-3 Python 设计的决策输入**，完成 ADR-0005 §8 要求的"只读文档验证或非产品 spike"。结论用于 §3-§13 的设计选择。本节在 L3-3 重写时**必须**重新实测所有路径（pin 精确版本、确认 import 路径、跑通示例 + 最小 framework SDK 调用），并在 L3 评审前报告任何偏差。

### 2.1 决策范围与依据

依据 ADR-0005 §3.3 + §6.3 + §8，L2-3 Python 批准前必须确认 5 项关键决策：

| # | 决策点 | 默认 | 备选 | 锁定依据 |
|---|--------|------|------|----------|
| D-1 | `Adapter` 抽象形式 | `typing.Protocol` + `@runtime_checkable` | `abc.ABC` | ADR-0005 §3.3；Protocol 允许第三方 framework 不依赖 SDK 即可 duck-type |
| D-2 | Python-native framework 部署模式 | **同进程 plugin**（Adapter + Agent 单 Python 进程） | Sidecar | ADR-0005 §3.3 + L1 §6.4；Python-native 框架无跨语言桥接成本 |
| D-3 | 非 Python framework 部署模式 | **Sidecar**（Adapter container + Agent container 同 Pod localhost） | 同进程 plugin | ADR-0005 §3.3 + L1 §6.4；非 Python 框架必须 Sidecar |
| D-4 | Card 转换实现 | Pydantic v2 + `pydantic-settings` + framework 原生 introspection | static YAML | 宪法 §3.8；动态推导避免 5 行 YAML 中的 `card` 字段成为必填 |
| D-5 | HTTP client (A2A→Agent container 通信) | `httpx.AsyncClient` 进程级连接池 + timeout | `aiohttp` | ADR-0005 §2.2；httpx 与 ASGI / a2a-sdk 内部一致 |

**默认表格说明**：上述 5 项为占位默认值；L3-3 实测后补完每项的精确版本号、风险评估、metric 名影响。

### 2.2 5 项决策详细说明

#### D-1：`typing.Protocol` 抽象

**Schema**：

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/protocol.py
# 完整代码在 L3-3 Spec
from typing import Protocol, runtime_checkable
from a2a import AgentCard, Message, Task, Part  # via superteam_a2a.a2a.upstream


@runtime_checkable
class Adapter(Protocol):
    """Adapter ↔ A2A Server 协议边界（ADR-0005 §3.3）。"""
    
    async def on_message(
        self, message: Message, context_id: str | None,
    ) -> Task:
        """处理 A2A sendMessage；返回 Task + 状态。"""
        ...
    
    def agent_card(self) -> AgentCard:
        """返回 Agent Card（用于 /.well-known/agent.json）。"""
        ...
    
    async def health_check(self) -> bool:
        """健康检查（Adapter container readiness）。"""
        ...


class FrameworkAdapter(Protocol):
    """框架特定扩展钩子（v0.1 Hello Agent 必实现）。"""
    
    async def on_framework_event(self, event: dict) -> None:
        """框架事件回调（如 LangChain chain run event）。"""
        ...
```

**与 Go baseline 对照**：
- v0.1.0 Go：`interface Adapter` (struct embed) + `interface FrameworkAdapter`
- v0.2 Python：`typing.Protocol` + `@runtime_checkable`（允许 `isinstance` 检查）
- 行为兼容性：完全一致（方法签名 + 语义不变）

#### D-2：Python-native framework 同进程 plugin

**适用框架**（v0.2 Python 计划）：
- **LangChain**（Python-native）→ 同进程 plugin
- **AutoGen**（Python-native）→ 同进程 plugin
- **CrewAI**（Python-native）→ Sidecar（v0.5） 或 同进程 plugin（v1.0 评估）
- **Semantic Kernel**（Python + .NET 双实现）→ Python 路径同进程 plugin；.NET 路径 Sidecar
- **Strands**（Python-native）→ Sidecar（v1.0）
- **Smolagents**（Python-native）→ Sidecar（v1.0）

**同进程 plugin 架构**：

```
┌──────────────────────────────────────────┐
│ Single Python Process (uvicorn)          │
│  ┌──────────┐  ┌──────────┐               │
│  │ Adapter  │◄─│ Agent    │               │
│  │ (uvicorn) │ (framework)│               │
│  └──────────┘  └──────────┘               │
│  in-process / asyncio                    │
└──────────────────────────────────────────┘
```

**优势**：
- 进程数 -1（资源占用降低）
- 通信延迟 -90%（localhost IPC 替换 HTTP 反序列化）
- OTel context 跨 Adapter ↔ Agent 自动串联（ADR-0005 §10）

**劣势**：
- Framework SDK 错误可能 kill 整个进程（需 framework-specific exception handler）
- GIL 竞争（虽然 Python Agent SDK 主要 I/O 密集）
- 框架依赖污染 Adapter 镜像（每 framework 独立镜像，仍可接受）

#### D-3：非 Python framework Sidecar 模式

**适用框架**（v0.5+）：
- 任何非 Python framework（JS / .NET / Java / Rust / Go 框架）
- 暂未列入 v0.1-v1.0 官方名单（v1.5+ 社区贡献）

**Sidecar 架构**：

```
┌──────────────────────────────────────────┐
│ Agent Pod                                │
│  ┌──────────────────┐  ┌────────────────┐│
│  │ Adapter Container│  │ Agent Container││
│  │ (Python :7080)   │  │ (任意语言:8080)││
│  │  :8080 A2A Server│  │  framework SDK ││
│  │   ↕ localhost    │  │                ││
│  └──────────────────┘  └────────────────┘│
└──────────────────────────────────────────┘
```

**通信协议**：
- 默认 HTTP/JSON（`httpx.AsyncClient`）
- v1.5+ 可选 gRPC（CONN-007 开放问题）

#### D-4：Card 转换 Pydantic v2

**Schema**：

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/card.py
# 完整代码在 L3-3 Spec
from pydantic import BaseModel, Field, ConfigDict
from a2a import AgentCard, AgentSkill  # via superteam_a2a.a2a.upstream


class AdapterCardConfig(BaseModel):
    """Adapter 启动时从 framework introspection 推导的 Card 配置。"""
    
    model_config = ConfigDict(extra="forbid", frozen=True)
    
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(..., min_length=1, max_length=2048)
    skills: list[AgentSkill] = Field(default_factory=list)
    memory_capabilities: MemoryCapabilities | None = None
    streaming: bool = False
```

**错误处理**（与 v0.1.0 wire contract 一致）：
- **必填字段缺失** → Fatal，`CARD_CONVERSION_FAILED (-32003)` 启动失败
- **可选字段缺失** → 默认值（description 为空则用 name）
- **JSON Schema 推导失败** → warning + `inputModes: ["text/plain"]` 降级

#### D-5：`httpx.AsyncClient` 进程级连接池

**Schema**：

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/transport.py
# 完整代码在 L3-3 Spec
import httpx
from superteam_a2a.a2a.upstream import MtlsConfig


def create_agent_client(
    base_url: str, mtls_config: MtlsConfig | None = None,
    timeout: float = 30.0,
) -> httpx.AsyncClient:
    """构造 A2A→Agent container 客户端（Sidecar 模式）。
    
    - 进程级单例（lifespan startup 创建，shutdown 关闭）
    - 连接池：max_connections=100，max_keepalive=20
    - mTLS：ssl_context 由 mtls_config 注入
    - timeout：connect=5s, read=30s, write=30s, pool=5s
    """
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(timeout, connect=5.0, read=timeout, write=timeout, pool=5.0),
        limits=httpx.Limits(max_connections=100, max_keepalive=20),
        verify=mtls_config.ssl_context if mtls_config else True,
    )
```

### 2.3 已知未决（移交 L3-3）

| # | 项 | 影响 | 处理 |
|---|----|------|------|
| U-1 | 6 个 framework SDK 的精确 PyPI 包名 + `requires-python` | L3-3 `pyproject.toml` 依赖声明 | L3-3 第一步 `pip index versions` + `pip show` |
| U-2 | 6 个 framework 的 Card 转换 introspection API 稳定性 | L3-3 Card 转换实现 | L3-3 在 Python venv 实测每个 framework 的最小 Card 推导 |
| U-3 | `prometheus-client` multiprocess mode 在 Sidecar 模式下的必要性 | L3-3 可观测性实现 | ADR-0005 §10：单进程无需 multiprocess；Sidecar 模式评估 |
| U-4 | 6 个 framework 锁版本范围（major / minor / patch policy） | L3-3 镜像 tag 策略 | 沿用 v0.1.0 决定（v0.5 锁 major；v1.0 锁 minor） |
| U-5 | Adapter container crash 时 framework 进程是否需要 graceful shutdown 协调 | L3-3 生命周期契约 | L3-3 在 kind 实测；引入 `asyncio.shield` + lifecycle hook |

---

## 3. Python 包结构（ADR-0005 §13 工程布局）

### 3.1 总览（uv workspace + adapter-sdk + 6 个 framework adapter sub-packages）

**ADR-0005 §13 工程布局**：

```
pyproject.toml                          # uv workspace 根 + 共享工具配置（ruff / pyright / pytest）
uv.lock                                 # 单一 lockfile，CI 必须 `uv sync --frozen`

packages/
  adapter-sdk/src/supteam_a2a/adapter/  # 通用 Adapter 抽象（无 framework 依赖）
  adapters/                             # 6 个 framework adapter 独立 workspace package
    langchain/src/supteam_a2a/adapters/langchain/
    autogen/src/supteam_a2a/adapters/autogen/
    crewai/src/supteam_a2a/adapters/crewai/
    semantic-kernel/src/supteam_a2a/adapters/semantic_kernel/
    strands/src/supteam_a2a/adapters/strands/
    smolagents/src/supteam_a2a/adapters/smolagents/
```

### 3.2 `adapter-sdk` 包布局（`packages/adapter-sdk/src/supteam_a2a/adapter/`）

```
superteam_a2a.adapter/
├── __init__.py                # 公共 API surface（re-export Adapter / FrameworkAdapter / 关键 helper）
├── protocol.py                # Adapter / FrameworkAdapter Protocol（§2.2 D-1）
├── card.py                    # AgentCardConverter Protocol + 默认 Pydantic 实现（§2.2 D-4）
├── config.py                  # AdapterConfig（Pydantic BaseSettings）+ 三层优先级加载（§8）
├── errors.py                  # 7 个 Adapter 扩展错误码常量（-32001 ~ -32007）+ A2A 错误转换（§9）
├── server.py                  # A2A Server 嵌入封装（基于 L2-1 superteam_a2a.a2a.create_app）
├── transport.py               # httpx.AsyncClient 工厂（Sidecar 模式，§2.2 D-5）
├── retry.py                   # Tenacity retry policy（基于错误码分类）
├── observability/
│   ├── __init__.py
│   ├── metrics.py             # supteam_adapter_* Prometheus 指标注册
│   ├── tracing.py             # OpenTelemetry provider 注入（显式，避免污染全局）
│   └── logging.py             # structlog setup（JSON 输出 + framework 字段）
├── lifecycle.py               # Start/Stop/Reload hook（同进程 plugin + Sidecar 双形态）
└── _internal/                 # ⚠️ private — 业务层禁止 import
    └── __init__.py
```

**关键约束**：
- `adapter-sdk` 不依赖任何 framework（确保各 framework adapter 子包可独立升级）
- `adapter-sdk` 仅依赖 `superteam_a2a.a2a`（L2-1）+ `pydantic` + `httpx` + `tenacity` + `prometheus-client` + `opentelemetry-sdk` + `structlog`
- 所有 `a2a` 类型导入必须经 `superteam_a2a.a2a.upstream`（与 L2-1 §3.2 边界规则一致）

### 3.3 Framework Adapter 子包布局（以 LangChain 为例；其他 5 个对称）

```
adapters/langchain/src/supteam_a2a/adapters/langchain/
├── __init__.py                # 公共 API surface（re-export LangChainAdapter）
├── adapter.py                 # LangChainAdapter class（Adapter Protocol 实现）
├── card.py                    # LangChain Tool → A2A AgentSkill 转换
├── chain.py                   # LCEL Runnable → A2A sendMessage handler
├── memory.py                  # LangChain memory backend → A2A Memory method 代理（v1.0+）
├── pyproject.toml             # 独立依赖：langchain-core + langchain + adapters-sdk
└── tests/
    ├── __init__.py
    ├── unit/                  # 单元测试（mock framework）
    │   ├── test_adapter.py
    │   ├── test_card.py
    │   └── test_chain.py
    ├── integration/           # 集成测试（真实 framework SDK + a2a SDK）
    │   ├── test_happy_path.py
    │   ├── test_tool_call.py
    │   └── test_card_discovery.py
    └── golden/                # Golden Cases fixture（宪法 §4.7 强制）
        ├── case-01-basic-rag.yaml
        ├── case-02-tool-call.yaml
        └── case-NN-{name}.yaml
```

**关键约束**：
- 每个 framework adapter 子包有 **独立 `pyproject.toml`** + 独立 `uv.lock` 锁版本
- framework 依赖（`langchain-core` / `autogen-agentchat` / `crewai` / `semantic-kernel` / `strands-agents` / `smolagents`）仅存在于对应子包
- `adapter-sdk` 与 Operator Core 严禁依赖任何 framework（ADR-0005 §3.3 + 宪法 §3.7）

### 3.4 边界规则（与 L2-1 §3.2 对齐）

```
┌─────────────────────────────────────────────────────────┐
│  framework SDK (langchain / autogen / crewai / etc.)    │
│  PyPI: langchain-core / autogen-agentchat / ...        │
└──────────────────────────┬──────────────────────────────┘
                           │ 唯一 import 入口
                           ▼
        ┌─────────────────────────────────────┐
        │  superteam_a2a.adapters.{framework} │  ← framework adapter 子包
        │  (Adapter Protocol 实现)            │
        └────────────────┬────────────────────┘
                         │ 依赖
        ┌────────────────▼────────────────────┐
        │  superteam_a2a.adapter.*            │  ← adapter-sdk 通用抽象
        │  (protocol / card / config / etc.)  │
        └────────────────┬────────────────────┘
                         │ 依赖
        ┌────────────────▼─────────────────────┐
        │  superteam_a2a.a2a.upstream          │  ← ⚠️ boundary（L2-1）
        │  (官方 a2a-sdk 唯一 import 入口)     │
        └──────────────────────────────────────┘
```

**关键约束**（与 ADR-0005 §3.3 + 宪法 §3.7 一致）：

1. **framework SDK import 仅在 framework adapter 子包内**（用 ruff / pyright 自定义 import linter 检测）
2. `adapter-sdk` 严禁依赖任何 framework
3. Operator Core 严禁 import `adapter-sdk` 或 framework adapter（Operator 只通过 K8s CRD 编排 Adapter container）
4. framework SDK 升级通过独立 workspace package 决策，不影响其他 framework

---

## 4. Adapter Protocol 接口（Python `typing.Protocol`）

### 4.1 核心 Protocol（与 L1 Architecture §6.3 完全对齐）

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/protocol.py
# 完整实现 + 测试在 L3-3 Spec
from typing import Protocol, runtime_checkable
from a2a import AgentCard, Message, Task  # via superteam_a2a.a2a.upstream


@runtime_checkable
class Adapter(Protocol):
    """Adapter ↔ A2A Server 协议边界（ADR-0005 §3.3 + L1 Architecture §6.3）。"""
    
    async def on_message(
        self, message: Message, context_id: str | None,
    ) -> Task:
        """处理 A2A sendMessage；返回 Task + 状态。
        
        Args:
            message: A2A Message（来自 sendMessage params.message）
            context_id: A2A context ID（用于 multi-turn 对话）
        
        Returns:
            Task: A2A Task（status + artifacts）
        
        Raises:
            CardConversionFailed: 启动时 Card 转换失败（-32003）
            FrameworkNotLoaded: framework SDK 未加载（-32001）
            ToolInvocationFailed: framework tool 调用异常（-32004）
        """
        ...
    
    def agent_card(self) -> AgentCard:
        """返回 Agent Card（用于 /.well-known/agent.json）。
        
        Card 转换由 §6 详述；启动时构建，运行期 cached。
        """
        ...
    
    async def health_check(self) -> bool:
        """健康检查（Adapter container readiness）。
        
        Returns:
            True: Adapter 可用
            False: Framework SDK 未初始化 / Agent container 不可达（Sidecar）
        """
        ...


class FrameworkAdapter(Protocol):
    """框架特定扩展钩子（Framework authors 必实现）。"""
    
    async def on_framework_event(self, event: dict) -> None:
        """框架事件回调（如 LangChain chain run event / AutoGen message event）。
        
        用于 framework-specific observability；非必须。
        """
        ...
```

### 4.2 6 框架映射（每 framework 实现 Adapter Protocol）

```python
# adapters/langchain/src/supteam_a2a/adapters/langchain/adapter.py
# 完整实现 + 测试在 L3-3 Spec
from superteam_a2a.adapter import Adapter
from superteam_a2a.a2a.upstream import AgentCard, Message, Task


class LangChainAdapter(Adapter):
    """LangChain framework adapter（v0.2 同进程 plugin）。"""
    
    def __init__(
        self,
        runnable: Runnable,  # langchain_core.runnables.Runnable
        config: LangChainAdapterConfig,
    ):
        self._runnable = runnable
        self._config = config
        self._card = self._build_card()  # §6 Card 转换
    
    async def on_message(
        self, message: Message, context_id: str | None,
    ) -> Task:
        # 1. 转换 A2A Message → LangChain input
        lc_input = self._convert_message_to_lc(message)
        # 2. 调用 framework（CPU 工作通过 anyio.to_thread offload）
        lc_output = await anyio.to_thread.run_sync(
            self._runnable.invoke, lc_input,
        )
        # 3. 转换 framework output → A2A Task
        return self._convert_lc_to_task(lc_output, context_id)
    
    def agent_card(self) -> AgentCard:
        return self._card
    
    async def health_check(self) -> bool:
        # LangChain 总是 loaded（同进程 plugin）
        return self._runnable is not None
```

**6 个 framework adapter 关键差异**（与 v0.1.0 wire contract 完全一致）：

| Framework | 入口点 | Card 转换点 | 部署模式 |
|-----------|--------|-------------|----------|
| LangChain | `langchain_core.runnables.Runnable.invoke` | `Runnable.get_input_schema()` → A2A skills | 同进程 plugin (v0.2) |
| AutoGen | `autogen_agentchat.ConversableAgent.on_messages` | `function_map` → A2A skills | 同进程 plugin (v0.2) |
| CrewAI | `crewai.Crew.kickoff` | `Agent.tools + Task.tools` → A2A skills | Sidecar (v0.5) |
| Semantic Kernel | `semantic_kernel.Kernel.invoke` | `kernel.plugins` → A2A skills | 同进程 plugin (Python) / Sidecar (.NET) |
| Strands | `strands.Agent` | `agent.tools` → A2A skills | Sidecar (v1.0) |
| Smolagents | `smolagents.CodeAgent.run` / `ToolCallingAgent.run` | `agent.tools` + `interpreter` → A2A skills | Sidecar (v1.0) |

### 4.3 关键约束（与 L1 Architecture §6.3 + 宪法 §3.7 一致）

1. **Adapter 不得 import 任何 Agent framework**（与 Operator 规则一致，宪法 §3.7）
2. **Adapter 必须复用 A2A Core 的 Server / Schema / TLS / 限流 / Trace**，不复制协议实现（ADR-0005 §3.3）
3. **Adapter 镜像基线 `python:3.12-slim` 多阶段构建**（ADR-0005 §2.2）
4. **Adapter 严禁持有 LLM API key**（L1 Architecture §6.4 + 宪法 §3.5.3）；该 Secret 由 Agent container 持有

---

## 5. 6 框架适配矩阵（与 v0.1.0 wire contract 完全一致）

| 框架 | 版本策略 | 入口点 | Card 转换复杂度 | 主要限制 | 里程碑 |
|------|----------|--------|----------------|----------|--------|
| **LangChain** | v0.2 锁 `langchain>=0.1,<0.3` | `langchain_core.runnables.Runnable.invoke()` | 中（LCEL chain → A2A sendMessage） | Memory backend 不直接对接 A2A Memory（需经 Adapter 代理） | v0.2 |
| **AutoGen** | v0.2 锁 `autogen-agentchat>=0.2,<0.4` | `autogen_agentchat.ConversableAgent.on_messages()` | 高（多 agent 对话 → A2A multi-agent） | GroupChat 拓扑映射复杂（manager agent ↔ UserProxy ↔ Assistant） | v0.2 |
| **CrewAI** | v0.5 锁 `crewai>=0.30,<0.80` | `crewai.Crew.kickoff()` | 中（Crew tasks → A2A workflow DAG） | Sequential/Parallel/Hierarchical 拓扑需完整支持 | v0.5 |
| **Semantic Kernel** | v0.5 锁 `semantic-kernel>=1.0,<2.0` | `semantic_kernel.Kernel.invoke()` | 中（plugins → A2A skills） | Python + .NET 双实现需维护两条代码路径 | v0.5 |
| **Strands** | v1.0 锁 `strands-agents>=1.0` | `strands.Agent()` | 低（单 agent 风格） | 新框架（2024 末 GA），生态不成熟，依赖上游稳定性 | v1.0 |
| **Smolagents** | v1.0 锁 `smolagents>=1.0,<2.0` | `smolagents.CodeAgent.run()` / `ToolCallingAgent.run()` | 低（code agent 风格） | 仅 CodeAgent + ToolCallingAgent 两类需支持 | v1.0 |

**说明**（与 v0.1.0 完全一致）：
- **版本策略**：v0.2/v0.5 阶段只锁主版本（`>=0.x,<0.(x+1)`），v1.0 阶段可考虑更紧的范围（如 `<0.x.5`）以避免次版本升级引入破坏性变更
- **里程碑依据**：ADR-0001（v0.5 = LangChain + AutoGen）+ L1 §6.5（路线图）；v0.2 同进程 plugin 优先级前置（P0）；CrewAI/Semantic Kernel 推迟到 v0.5 因 GroupChat 多 agent 复杂度
- **Card 转换复杂度** 评级依据：转换点数量 + 嵌套深度 + 框架特性对齐成本

---

## 6. A2A Card 转换层

A2A Agent Card（[L2-1 types/agent_card.py](../L2-modules/L2-a2a-protocol.md)）是 Agent 自描述的标准格式。**Adapter 必须把框架原生元数据转换为标准 A2A Agent Card**，否则 Agent Card discovery 会失败（L2-1 §4.1 `/.well-known/agent.json`）。

### 6.1 5 个关键转换点（与 v0.1.0 wire contract 完全一致）

| # | 字段 | 来源（框架原生） | 目标（A2A Card） | 备注 |
|---|------|------------------|------------------|------|
| 1 | `name` | `agent.name` / `ConversableAgent.name` | A2A `name` | 必填，唯一性约束 |
| 2 | `description` | `agent.description` / `role + goal + backstory`（CrewAI） | A2A `description` | 必填，用于 discovery 搜索 |
| 3 | `skills[]` | `agent.tools` / `function_map` / `kernel.plugins` | A2A `skills[]`（每元素含 name + description + inputModes + outputModes） | 核心转换点，详见 §6.2 |
| 4 | `memoryCapabilities` | 框架 memory backend 类型 | A2A `memoryCapabilities: { recordable, queryable, scopes[] }` | v1.0 起需支持 |
| 5 | `streaming` | 框架是否支持 streaming | A2A `streaming: bool` | v0.5+（SSE 实现后） |

### 6.2 各框架 skills 转换细节（与 v0.1.0 wire contract 完全一致）

| 框架 | 工具 / Skill 来源 | 转换规则 |
|------|-------------------|----------|
| LangChain | `agent.get_input_schema()` + tool name + tool description | 每个 tool → 一个 A2A skill（`name` = tool name；`description` = tool description；`inputModes` = schema 推导的 JSON Schema；`outputModes` = `["text/plain"]`） |
| AutoGen | `ConversableAgent.function_map`（dict[str, Callable]） | 每个 function → 一个 A2A skill；function docstring → skill description；function signature → JSON Schema |
| CrewAI | `Agent.tools` + `Task.tools` | 同 LangChain；但 CrewAI tools 是 Pydantic 模型，需先 JSON Schema 化 |
| Semantic Kernel | `kernel.plugins[name].functions[name]` | 每个 kernel function → 一个 A2A skill；`function.description` → skill description；kernel 参数 → JSON Schema |
| Strands | `agent.tools`（Tool 对象列表） | 同 LangChain；Strands tools 自带 `tool_spec` |
| Smolagents | `agent.tools` + CodeAgent `interpreter` | 普通 tool → A2A skill；CodeAgent interpreter → 单独标记为 `code_execution: true` |

### 6.3 Card 转换失败处理（与 v0.1.0 完全一致）

- **必填字段缺失** → 启动失败（Fatal），错误码 `-32003 CARD_CONVERSION_FAILED`
- **可选字段缺失** → 使用默认值（如 description 为空则使用 `name`）
- **JSON Schema 推导失败** → 记录 warning，skill 仍注册但 `inputModes: ["text/plain"]`（降级）

### 6.4 Pydantic schema 表达

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/card.py
# 完整代码在 L3-3 Spec
from pydantic import BaseModel, Field, ConfigDict
from a2a import AgentCard, AgentSkill  # via superteam_a2a.a2a.upstream


class AdapterCardConfig(BaseModel):
    """Adapter 启动时从 framework introspection 推导的 Card 配置。"""
    
    model_config = ConfigDict(extra="forbid", frozen=True)
    
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(..., min_length=1, max_length=2048)
    skills: list[AgentSkill] = Field(default_factory=list)
    memory_capabilities: MemoryCapabilities | None = None
    streaming: bool = False


class MemoryCapabilities(BaseModel):
    """A2A Memory capabilities 表达。"""
    
    model_config = ConfigDict(extra="forbid", frozen=True)
    
    recordable: bool = False
    queryable: bool = False
    scopes: list[str] = Field(default_factory=list)
```

---

## 7. 容器镜像打包策略（ADR-0005 §2.2 + §9.3）

### 7.1 策略 A：每框架独立 base 镜像（**推荐**）

```
┌────────────────────────────────────────────────┐
│  superteam-a2a/adapter-langchain:v0.2.0-py3.12│
├────────────────────────────────────────────────┤
│ Layer 5:  framework-specific code              │
│ Layer 4:  langchain-core 0.1.x + dependencies  │
│ Layer 3:  adapter-sdk (shared package)         │
│ Layer 2:  framework adapter package            │
│ Layer 1:  python:3.12-slim                     │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│  superteam-a2a/adapter-autogen:v0.2.0-py3.12   │
├────────────────────────────────────────────────┤
│ Layer 5:  framework-specific code              │
│ Layer 4:  autogen-agentchat 0.2.x + deps       │
│ Layer 3:  adapter-sdk (shared package)         │
│ Layer 2:  autogen adapter package              │
│ Layer 1:  python:3.12-slim                     │
└────────────────────────────────────────────────┘
```

**优势**：
- 镜像大小可控（每框架仅含必要依赖，~200-400 MB）
- 升级独立（LangChain 升 0.2 不影响 AutoGen 部署）
- 故障隔离（框架依赖问题不影响其他 framework）
- CI 缓存友好（Layer 3 `adapter-sdk` 共享，registry pull 更快）

**劣势**：
- 镜像数量多（v1.0 = 6 个官方镜像 + contrib N 个）
- Layer 1 + Layer 3 跨镜像重复存储（可接受 — 总增量 ~50 MB）

### 7.2 策略 B：统一 multi-base 镜像（**不推荐**）

```
┌────────────────────────────────────────────────┐
│  superteam-a2a/adapter-unified:v1.0.0          │
├────────────────────────────────────────────────┤
│ Layer 5:  framework selector (env var)         │
│ Layer 4:  langchain + autogen + crewai + ...   │
│ Layer 3:  python:3.12                          │
│ Layer 2:  adapter-sdk                          │
│ Layer 1:  debian-slim                          │
└────────────────────────────────────────────────┘
```

**劣势**：
- 镜像体积爆炸（~1.5 GB，所有框架依赖全打包）
- 依赖冲突概率高（langchain 0.1 + autogen 0.2 可能 Python 包版本冲突）
- 升级耦合（任一 framework 升级需重建整个镜像）

### 7.3 镜像构建流程（ADR-0005 §9.2 供应链）

1. **CI 触发**：GitHub Actions on push to `adapters/{framework}/**`
2. **多阶段构建**：
   - Stage 1（builder）：`uv build` framework adapter package（wheel）
   - Stage 2（runtime）：`python:3.12-slim` + framework deps + `adapter-sdk` + 复制 builder wheel
3. **镜像 tag 策略**：`{framework}:{adapter-version}-{framework-version}-py{python-version}`
   - 例：`adapter-langchain:v0.2.0-0.1.5-py3.12`
4. **签名 + 验证**：cosign 签名 + SLSA L3 provenance + pip-audit + Trivy + Bandit
5. **lockfile 提交**：`uv.lock` 必须 checked-in；CI `uv sync --frozen`

### 7.4 镜像安全约束（ADR-0005 §9.3 运行时）

- 非 root user（`uid: 1000`）
- read-only rootfs
- drop all capabilities
- `allowPrivilegeEscalation: false`
- `runAsNonRoot: true`
- framework Adapter 与 Agent container 使用不同镜像和 ServiceAccount

---

## 8. 配置注入与 Secret 管理

### 8.1 配置源优先级（从高到低）

| 优先级 | 来源 | 适用场景 | 注入时机 |
|--------|------|----------|----------|
| 1（最高） | K8s `Secret`（envFrom / volumeMount） | mTLS cert、LLM API key、第三方服务 token | Adapter 启动时 + 热加载（K8s 1.27+） |
| 2 | `Agent` CRD `spec.adapter.config` | 用户声明的 framework 特定配置（如 LangChain `max_iterations`） | Adapter 启动时 |
| 3 | `ConfigMap` | 集群级默认 + 框架特定默认（如 LangChain 默认 model） | Adapter 启动时 |
| 4（最低） | 环境变量 | Operator 注入（`POD_NAME`、`NAMESPACE`、`ADAPTER_PORT`） | Adapter 启动时（不可变） |

### 8.2 Pydantic Settings 三层优先级加载

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/config.py
# 完整代码在 L3-3 Spec
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from superteam_a2a.a2a.upstream import AgentCard


class AdapterConfig(BaseSettings):
    """Adapter 通用配置（从 env / ConfigMap / Secret 三层加载）。"""
    
    model_config = SettingsConfigDict(
        env_prefix="ADAPTER_",
        env_file=".env",
        extra="forbid",
    )
    
    framework: str = Field(..., description="framework name")
    port: int = Field(default=8080, ge=1024, le=65535)
    log_level: str = Field(default="INFO")
    agent_card_path: str | None = Field(default=None)
    
    # mTLS（cert-manager mounted）
    mtls_cert_path: str | None = Field(default=None)
    mtls_key_path: str | None = Field(default=None)
    mtls_ca_path: str | None = Field(default=None)


class FrameworkAdapterConfig(BaseModel):
    """Framework 特定配置（从 Agent CRD spec.adapter.config 加载）。"""
    
    model_config = ConfigDict(extra="forbid", frozen=True)
    
    # framework-specific 字段（如 LangChain max_iterations）
    # 各 framework adapter 子包扩展
```

### 8.3 Secret 隔离原则（与 v0.1.0 wire contract 完全一致）

- **Adapter 容器不应持有 LLM API key** — 该 Secret 由 **Agent 容器** 持有（通过 volumeMount 挂载）
- **Adapter 只持有协议层 Secret**：mTLS cert、prometheus pushgateway token
- 理由：Adapter 是无状态翻译层，重启频率高；持有业务 Secret 增加泄露面

### 8.4 5 行 YAML 原则（与 L1 Architecture §6.2 完全一致）

```yaml
spec:
  adapter:
    framework: langchain          # 1. 框架名（枚举：langchain / autogen / crewai / semantic_kernel / strands / smolagents / hello）
    image: my-agent:latest        # 2. Agent 容器镜像
    card: ./agent-card.yaml       # 3. Agent Card（可选，默认由 framework introspection 推导）
    resources:                    # 4. 资源（可选，参考 L1 §11.1 默认限制）
      limits: { cpu: "1", memory: "2Gi" }
    healthCheck: /healthz         # 5. 健康检查路径（可选，默认 /healthz）
```

---

## 9. 错误码与重试

### 9.1 错误码体系（与 v0.1.0 wire contract 完全一致）

Adapter 扩展错误码（基于 L2-1 `errors.py` JSON-RPC 标准 + 扩展）：

| 错误码 | 常量 | 含义 | 是否可重试 |
|--------|------|------|------------|
| `-32001` | `FRAMEWORK_NOT_LOADED` | framework SDK 未成功加载（ImportError） | ❌ 永久（需升级 adapter 镜像） |
| `-32002` | `FRAMEWORK_VERSION_INCOMPATIBLE` | framework 版本与 adapter 不兼容 | ❌ 永久 |
| `-32003` | `CARD_CONVERSION_FAILED` | Agent Card 转换失败（必填字段缺失） | ❌ 永久（启动失败） |
| `-32004` | `TOOL_INVOCATION_FAILED` | framework tool 调用异常 | ✅ 可重试（业务侧决定） |
| `-32005` | `MEMORY_BACKEND_UNAVAILABLE` | framework memory backend 不可用 | ✅ 可降级（读为空，写入本地队列） |
| `-32006` | `AGENT_CONTAINER_UNREACHABLE` | localhost:7080 Agent container 无响应（Sidecar 模式） | ✅ 可重试（网络抖动） |
| `-32007` | `CONFIG_VALIDATION_FAILED` | 配置校验失败（如 model name 格式错误） | ❌ 永久（需修复 Agent CRD） |

### 9.2 Python 实现（StrEnum + A2A error struct）

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/errors.py
# 完整代码在 L3-3 Spec
from enum import StrEnum
from a2a import JSONRPCError  # via superteam_a2a.a2a.upstream


class AdapterErrorCode(StrEnum):
    """Adapter 扩展错误码（与 L2-1 §7 errors.py 协调）。"""
    
    FRAMEWORK_NOT_LOADED = "-32001"
    FRAMEWORK_VERSION_INCOMPATIBLE = "-32002"
    CARD_CONVERSION_FAILED = "-32003"
    TOOL_INVOCATION_FAILED = "-32004"
    MEMORY_BACKEND_UNAVAILABLE = "-32005"
    AGENT_CONTAINER_UNREACHABLE = "-32006"
    CONFIG_VALIDATION_FAILED = "-32007"


class AdapterError(Exception):
    """Adapter 域错误。"""
    
    def __init__(
        self,
        code: AdapterErrorCode,
        message: str,
        framework_error: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.framework_error = framework_error
        super().__init__(message)
    
    def to_jsonrpc_error(self) -> JSONRPCError:
        """转换为 A2A JSON-RPC error。"""
        return JSONRPCError(
            code=int(self.code),
            message=self.message,
            data={"framework_error": self.framework_error} if self.framework_error else None,
        )
```

### 9.3 重试策略（Tenacity · ADR-0005 §2.2）

| 错误类型 | 重试次数 | 退避策略 | 最大延迟 |
|----------|----------|----------|----------|
| 框架超时（>30s） | 3 | 指数退避 + jitter（base=1s, factor=2） | 16s |
| 框架版本不兼容 | 0 | — | — |
| 工具调用失败 | 3 | 指数退避 | 8s |
| Memory backend 不可用 | ∞（带 backoff） | 指数退避（base=5s, factor=2） | 300s |
| Agent container unreachable | 5 | 线性退避（1s/次） | 5s |

**jitter 计算**：`delay = base * 2^attempt + random(0, base * 2^attempt * 0.1)`

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/retry.py
# 完整代码在 L3-3 Spec
from tenacity import (
    AsyncRetrying, retry_if_exception_type,
    stop_after_attempt, wait_exponential_jitter,
)
from superteam_a2a.adapter.errors import AdapterError, AdapterErrorCode


def create_retry_policy(error_code: AdapterErrorCode) -> AsyncRetrying:
    """根据错误码返回对应的 Tenacity retry policy。"""
    if error_code == AdapterErrorCode.TOOL_INVOCATION_FAILED:
        return AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential_jitter(initial=1, max=8),
            retry=retry_if_exception_type(AdapterError),
        )
    # ... 其他错误码
```

### 9.4 错误传播（与 v0.1.0 wire contract 完全一致）

- Adapter → A2A Server（HTTP response）：JSON-RPC `error.code` + `error.message` + `error.data.framework_error`（框架原生异常详情，仅 debug 模式返回）
- Adapter → OTel Span：标记 Span status（OK / ERROR）+ error.type + error.message
- Adapter → Prometheus：`supteam_adapter_errors_total{framework, error_code}` +1

---

## 10. 可观测性（Python 全栈 · 沿用 v0.1 metric name）

### 10.1 Prometheus 指标（`supteam_adapter_*`）

| 指标名 | 类型 | 标签 | 用途 |
|--------|------|------|------|
| `supteam_adapter_requests_total` | Counter | `framework`, `method`, `status` | 每 framework 每 method 的请求数 |
| `supteam_adapter_request_duration_seconds` | Histogram | `framework`, `method` | 请求延迟分布（buckets: 0.1/0.5/1/2/5/10/30s） |
| `supteam_adapter_card_conversion_duration_seconds` | Histogram | `framework` | Card 转换延迟（启动期） |
| `supteam_adapter_framework_load_duration_seconds` | Histogram | `framework` | framework SDK 加载延迟（启动期） |
| `supteam_adapter_errors_total` | Counter | `framework`, `error_code` | 错误计数（error_code 见 §9.1） |
| `supteam_adapter_active_agents` | Gauge | `framework` | 当前活跃 Agent 数（由 readiness probe 推导） |
| `supteam_adapter_golden_case_pass_total` | Counter | `framework`, `case_id` | Golden Case 通过数（CI 报告） |

**Python 实现**（`prometheus-client` 单进程模式，ADR-0005 §10）：

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/observability/metrics.py
# 完整代码在 L3-3 Spec
from prometheus_client import Counter, Histogram, Gauge


REQUESTS_TOTAL = Counter(
    "supteam_adapter_requests_total",
    "Adapter request count",
    labelnames=("framework", "method", "status"),
)

REQUEST_DURATION_SECONDS = Histogram(
    "supteam_adapter_request_duration_seconds",
    "Adapter request duration in seconds",
    labelnames=("framework", "method"),
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
)

# ... 其他指标
```

### 10.2 OpenTelemetry Trace

- **Root Span**：`adapter.{framework}.{method}`（如 `adapter.langchain.sendMessage`）
  - Attributes: `framework`, `framework.version`, `adapter.version`, `agent.name`
- **Child Spans**：
  - `framework.invoke`（调用 framework SDK）
  - `card.convert`（如 method 触发 Card 重读）
  - `framework.translate`（框架输出 → A2A 响应）
- **Span Events**：`tool.invoked`, `memory.read`, `memory.write`, `error.occurred`

**Python 实现**（显式 provider 注入，避免污染全局）：

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/observability/tracing.py
# 完整代码在 L3-3 Spec
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def create_tracer(name: str = "supteam_a2a.adapter") -> trace.Tracer:
    """创建 Adapter tracer（显式 provider 注入）。"""
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(...))  # OTLP exporter
    trace.set_tracer_provider(provider)
    return trace.get_tracer(name)
```

### 10.3 结构化日志（structlog + JSON）

**JSON 格式**，强制字段（与 v0.1.0 wire contract 完全一致）：
- `framework`（如 `langchain`）
- `framework.version`（如 `0.1.5`）
- `adapter.version`（如 `0.2.0`）
- `method`（A2A method 名）
- `task_id`（来自 A2A request）
- `agent.name`
- `level`, `ts`, `msg`

可选字段：
- `error.code`, `error.message`, `error.stack`
- `duration_ms`, `retry_count`

**Python 实现**（ADR-0005 §10 structlog + 敏感内容禁记）：

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/observability/logging.py
# 完整代码在 L3-3 Spec
import structlog


def configure_logging(level: str = "INFO") -> None:
    """配置 structlog JSON 输出。"""
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(get_level(level)),
        logger_factory=structlog.PrintLoggerFactory(),
    )
```

### 10.4 关键约束（与 L1 Architecture §9 + 宪法 §7 一致）

- Message / Memory / Knowledge content 永不进入普通日志
- 高基数 label 禁令（trace_id / task_id 不过 metric）
- event-loop lag、thread-offload queue depth、active tasks（Python runtime 指标）
- 单进程模式（避免 multiprocess mode 复杂性）

---

## 11. 测试策略（Python · pytest + hypothesis）

### 11.1 单元测试（`adapter-sdk` + framework 子包）

| 范围 | 覆盖率目标 | 测试类型 |
|------|-----------|----------|
| `adapter-sdk`（protocol / card / config / errors / observability / retry / lifecycle） | ≥ 95% | 表驱动 + `mock` + `pytest-asyncio` |
| `langchain`, `autogen`, `crewai`, `semantic_kernel`, `strands`, `smolagents` | ≥ 80% | 表驱动 + 真实 framework SDK（小型 model） |

**测试工具**：pytest + pytest-asyncio + pytest-cov + respx + hypothesis

### 11.2 集成测试（每 framework 必含）

| 测试 ID | 场景 | 框架通用 |
|---------|------|----------|
| IT-001 | happy path：`sendMessage` → framework invoke → A2A 响应 | ✅ |
| IT-002 | tool invocation：`sendMessage` 携带 tool call → framework 执行 tool → A2A 响应 | ✅ |
| IT-003 | Card discovery：`GET /.well-known/agent.json` 返回正确 A2A Card | ✅ |
| IT-004 | error path：framework 超时 → 错误码 `-32004` + 重试 3 次 | ✅ |
| IT-005 | memory read/write（v1.0+）：`recordMemory` / `queryMemory` 经 framework memory backend | v1.0+ |
| IT-006 | 同进程 plugin 与 Sidecar 模式切换 | v0.2+ |

每 framework 6 个 IT 起步（v0.2 LangChain + AutoGen = 12 IT；v1.0 6 框架 = 36 IT）。

### 11.3 Golden Adapter 测试（宪法 §4.7 强制）

| 版本 | 每框架 Golden Cases | 涵盖 |
|------|---------------------|------|
| v0.5 | ≥ 5 | 基础 LCEL / ConversableAgent 用法 + 1 个 tool call + 1 个 error path + 1 个 memory + 1 个 streaming 模拟 |
| v1.0 | ≥ 10 | 上述 + 5 个 framework 特性深度用例（多 agent、graph、plugin、interpreter 等） |

**Golden Case 来源**：`adapters/{framework}/tests/golden/case-{NN}-{name}.yaml`（fixture 文件 + 期望 A2A 响应）

### 11.4 Conformance 测试

- 与上游 `a2a-python` conformance 套件 100% 通过
- 每个 framework 必须通过至少 1 个 conformance case
- CI 每日定时跑（detect upstream A2A protocol drift）

### 11.5 Property / Fuzz 测试（Hypothesis）

- **envelope/schema**：A2A envelope schema round-trip + 异常字段拒绝
- **FSM**：Task 状态机 invariant（任何状态转换合法）
- **Card 转换**：framework introspection 输入 fuzz → Card 转换不应崩溃
- **retry policy**：任意错误码序列 → 重试次数与延迟在预期范围内

### 11.6 E2E 测试（Operator + Adapter 联动 · kind）

- `tests/e2e/adapter-langchain-hello.yaml`（v0.2）
- `tests/e2e/adapter-autogen-hello.yaml`（v0.2）
- `tests/e2e/adapter-{framework}-sdlc.yaml`（v1.0，每框架一个完整 SDLC 工作流）

### 11.7 性能基准（pytest-benchmark · ADR-0005 §12）

- 1 KiB A2A loopback p50/p95/p99（同进程 plugin vs Sidecar）
- Card conversion 延迟
- framework SDK load 延迟
- event-loop lag（高负载下）
- RSS / CPU per Pod

---

## 12. 与其他模块的接口契约

### 12.1 与 L2-1 A2A Protocol

| 接口 | 方向 | 形式 |
|------|------|------|
| `superteam_a2a.a2a.create_app()` | Adapter 嵌入 | Adapter container 启动时 `create_app(card=adapter.agent_card())` 注册 framework handler |
| `superteam_a2a.a2a.upstream.AgentCard` | Adapter 提供 | `card.py` 实现转换接口 |
| `superteam_a2a.a2a.A2AClient`（可选） | Adapter 调用 | Adapter 可主动调用其他 Agent（multi-agent 协作） |

**关键约束**：Adapter 不得直接 `from a2a import ...`；必须经 `superteam_a2a.a2a.upstream`（与 L2-1 §3.2 边界规则一致）。

### 12.2 与 L2-2 Operator Core

Operator Core 创建 Adapter container 作为 Pod sidecar（同进程 plugin 路径合并到 Agent container）：

```yaml
# Operator 生成的 Pod spec（Sidecar 模式 · 节选）
spec:
  containers:
  - name: adapter                    # ← 本模块
    image: superteam-a2a/adapter-langchain:v0.2.0-0.1.5-py3.12
    ports:
    - containerPort: 8080            # A2A Server
    env:
    - name: ADAPTER_FRAMEWORK
      value: langchain
    - name: AGENT_SERVICE_HOST        # Agent container DNS（sidecar 模式 = localhost）
      value: localhost
    - name: AGENT_SERVICE_PORT
      value: "7080"
  - name: agent                      # 框架容器
    image: my-agent:latest
    ports:
    - containerPort: 7080            # framework server
```

**同进程 plugin 模式**（v0.2 LangChain / AutoGen）：

```yaml
# Operator 生成的 Pod spec（同进程 plugin · 节选）
spec:
  containers:
  - name: agent-with-adapter        # 单 Python 进程
    image: superteam-a2a/adapter-langchain:v0.2.0-0.1.5-py3.12
    ports:
    - containerPort: 8080            # A2A Server
    command: ["uvicorn", "superteam_a2a.adapters.langchain.app:create_app"]
    env:
    - name: ADAPTER_FRAMEWORK
      value: langchain
    - name: ADAPTER_EMBEDDED
      value: "true"
```

引用 L2-2 Operator Core v0.2.0 Spec §3.2.4 Owned resources 中 Adapter container 部分。

### 12.3 与 Agent CRD

`Agent.spec.adapter` 字段（引用 L1 v0.2.0 Architecture §5.2.1 Agent CRD）：

```yaml
spec:
  adapter:
    framework: langchain          # 必填，枚举：langchain / autogen / crewai / semantic_kernel / strands / smolagents / hello
    image: my-agent:latest        # 必填，Agent 容器镜像
    card: ./agent-card.yaml       # 可选，默认由框架运行时推导
    resources:                    # 可选，参考 L1 §11.1 默认限制
      limits: { cpu: "1", memory: "2Gi" }
    healthCheck: /healthz         # 可选，默认 /healthz
    embedded: false               # v0.2+ 可选 true（仅 Python-native framework）
```

### 12.4 与 Framework SDK

- **同进程 plugin 模式**：Adapter 直接 import framework SDK（单 Python 进程）
- **Sidecar 模式**：Adapter 通过 **HTTP/JSON**（`httpx.AsyncClient`）调用 Agent container（gRPC 作为 v1.5+ 可选）
- 框架 SDK 在 Agent container 内部运行（**不在 Adapter container 内**）—— Adapter 只是 protocol 翻译层

### 12.5 与 L2-4 Knowledge / Memory（v1.0+）

若 framework memory backend 不可用（`MEMORY_BACKEND_UNAVAILABLE -32005`），Adapter 降级到 L2-4 Knowledge/Memory A2A method（`a2a.recordMemory` / `a2a.queryMemory`）作为代理（详见 v0.1.0 §8.6 开放问题）。

---

## 13. 部署形态（同进程 plugin / Sidecar）

### 13.1 Sidecar 模式（**v0.1 推荐；v0.5+ 通用**）

```
┌──────────────────────────────────────────┐
│ Agent Pod                                │
│                                          │
│  ┌──────────────────┐  ┌────────────────┐│
│  │ Adapter Container│  │ Agent Container││
│  │ (Python :7080)   │  │ (任意语言:8080)││
│  │  :8080 A2A Server│  │  framework SDK ││
│  │   ↕ localhost    │  │                ││
│  └──────────────────┘  └────────────────┘│
│                                          │
│  Shared: emptyDir volume for IPC (opt)   │
└──────────────────────────────────────────┘
```

**优势**：
- Adapter 与 Agent 容器共享 Pod 网络（localhost）
- 资源独立限制（Adapter 限制 256MB；Agent 限制 2GB）
- 独立重启（framework 升级不影响 Adapter）
- 非 Python framework 兼容

**劣势**：
- 进程数 +1（资源开销略高）
- localhost IPC 序列化开销

### 13.2 同进程 plugin 模式（**v0.2 Python-native 优先**）

```
┌──────────────────────────────────────────┐
│ Agent Pod                                │
│  ┌────────────────────────────────┐      │
│  │  Single Python Process (uvicorn)      │
│  │  ┌──────────┐  ┌──────────┐    │      │
│  │  │ Adapter  │◄─│ Agent    │    │      │
│  │  │ (uvicorn) │ (framework)│    │      │
│  │  └──────────┘  └──────────┘    │      │
│  │  in-process / asyncio          │      │
│  └────────────────────────────────┘      │
└──────────────────────────────────────────┘
```

**适用**（v0.2 Python 计划）：
- LangChain（Python-native）
- AutoGen（Python-native）
- Semantic Kernel Python 路径

**不适用**：
- 任何非 Python framework
- CrewAI v0.5（GroupChat 多 agent 复杂度高，v0.5 默认 Sidecar）
- Strands / Smolagents v1.0（生态稳定性待观察）

**优势**：
- 进程数 -1（资源占用降低）
- 通信延迟 -90%（localhost IPC 替换 HTTP 反序列化）
- OTel context 跨 Adapter ↔ Agent 自动串联

**劣势**：
- Framework SDK 错误可能 kill 整个进程（需 framework-specific exception handler）
- GIL 竞争（虽然 Python Agent SDK 主要 I/O 密集）
- 框架依赖污染 Adapter 镜像（每 framework 独立镜像，仍可接受）

### 13.3 Init Container 模式（**不推荐**）

Adapter 作为 init container，仅启动时配置注入。**不推荐**因为：
- 无法处理运行时 A2A 请求（init container 启动后即退出）
- 不符合 L1 §6.4 Adapter 拓扑设计

### 13.4 部署模式决策（Operator Core 依据 Agent CRD `spec.adapter.embedded` 字段）

| `embedded` | 部署模式 | 适用 framework |
|------------|----------|----------------|
| `true` | 同进程 plugin | LangChain / AutoGen / Semantic Kernel Python |
| `false`（默认） | Sidecar | CrewAI / Strands / Smolagents / 非 Python |

**CRD 校验**（Operator Core admission webhook）：`embedded: true` 仅允许 Python-native framework；否则拒绝。

### 13.5 资源限制（与 L1 v0.2.0 Architecture §11.1 对齐）

| 模式 | CPU limit | Memory limit | 说明 |
|------|-----------|--------------|------|
| Sidecar Adapter | 500m | 256Mi | 轻量协议翻译 |
| 同进程 plugin | 1 | 1Gi | 包含 framework SDK |
| Agent container | 1 | 2Gi | LLM 调用 + 业务逻辑 |

---

## 14. 开放问题

| # | 问题 | 默认决策 | 待确认 |
|---|------|----------|--------|
| O-1 | 同进程 plugin 模式下 framework SDK 崩溃如何隔离？ | framework-specific exception handler + `asyncio.shield` 包装 framework invoke | L3-3 实测 |
| O-2 | 6 framework 的 Card 转换 introspection API 是否稳定？ | L3-3 在 venv 实测每个 framework；不稳定的降级到 static YAML card | L3-3 |
| O-3 | Sidecar 模式 `httpx.AsyncClient` 是否需要 mTLS？ | v0.1 同 Pod localhost 通信（无须 mTLS）；v0.5+ 跨 Pod Adapter 通信需要 mTLS + SPIFFE | L3-3 |
| O-4 | framework upgrade 兼容性如何长期保障？ | adapter 锁定 framework major 版本；minor 升级需回归测试 + Golden Case | L1 + 用户 |
| O-5 | 第三方贡献 adapter 的 review 流程？ | 准入清单（参考 contrib/README.md）+ 2 名 maintainer LGTM | 用户 |
| O-6 | adapter 版本与 framework 版本的版本矩阵管理？ | 镜像 tag 含双版本号；deprecation 公告 6 个月前 | 用户 |
| O-7 | Sidecar 模式资源开销是否过高？（每 Agent Pod 多 256MB Adapter） | 默认 Sidecar；嵌入式仅限 Python-native framework v0.2+ | 用户 |
| O-8 | framework 升级导致的 A2A Memory 兼容性问题？ | framework memory 不可用时降级到 A2A Memory service 代理 | v1.0+ |
| O-9 | Adapter 是否需要支持 framework 自定义 transport（如 gRPC）？ | 默认 HTTP/JSON；gRPC 作为 v1.5+ 可选优化 | v1.5+ |
| O-10 | 6 framework SDK 的 License 一致性如何审计？ | 仅采纳 Apache 2.0 / MIT / BSD-3 兼容 license | CI 自动检测 + 用户 review |

---

## 附录 A：跨模块引用

| 引用对象 | 位置 | 用途 |
|----------|------|------|
| L1 Architecture v0.2.0 §6 | [docs/design/L1-architecture.md](../L1-architecture.md) | Adapter 角色 + 5 行 YAML + 接口 + 拓扑 + 路线图 |
| L1 Architecture §6.5 | 同上 | 官方 Adapter 路线图（v0.1-v1.5） |
| L1 Architecture §11.5 | 同上 | Python 性能预算（adapter SDK 锁版本 + RSS / CPU 预算） |
| L1 Spec v0.2.0 §5 | [docs/spec/L1-system-spec.md](../../spec/L1-system-spec.md) | Agent CRD spec.adapter 字段 |
| L1 Spec v0.2.0 §16 | 同上 | 指标命名规范（与 §10.1 一致） |
| L2-1 A2A Protocol v0.2.0 Design | [docs/design/L2-modules/L2-a2a-protocol.md](../L2-modules/L2-a2a-protocol.md) | A2A Server SDK 嵌入（§3 包结构 + §4 compatibility）+ Agent Card types（§7.2） |
| L2-1 A2A Protocol v0.2.0 Spec | [docs/spec/L2-module-specs/L2-a2a-protocol.md](../../spec/L2-module-specs/L2-a2a-protocol.md) | JSON-RPC method + error codes（与 §9 一致） |
| L2-2 Operator Core v0.2.0 Spec | [docs/spec/L2-module-specs/L2-operator-core.md](../../spec/L2-module-specs/L2-operator-core.md) | Owned resources 中 Adapter container 部分（§3.2.4） |
| L2-4 Knowledge / Memory v0.1.0 Design | [docs/design/L2-modules/L2-knowledge-memory.md](../L2-modules/L2-knowledge-memory.md) | Memory 降级路径（§12.5） |
| ADR-0001 v1 范围声明 | [docs/adr/0001-v1-scope-statement.md](../../adr/0001-v1-scope-statement.md) | 6 framework adapters 范围 |
| ADR-0004 v0.1 时间线延长 | [docs/adr/0004-v01-scope-extension-knowledge-and-memory.md](../../adr/0004-v01-scope-extension-knowledge-and-memory.md) | v0.1 = 0 framework adapters；v0.2 = 2；v0.5 = 4；v1.0 = 6 |
| ADR-0005 Python-first | [docs/adr/0005-python-first-technology-stack.md](../../adr/0005-python-first-technology-stack.md) | §3.3 Adapter SDK + §13 工程布局 |
| 宪法 v0.5.0 §2.2 多框架多元主义 | [CONSTITUTION.md](../../../CONSTITUTION.md) | 所有框架必须支持 |
| 宪法 §3.7 反依赖 | 同上 | Operator 不得 import 框架代码（Adapter 可，但通过独立容器隔离） |
| 宪法 §4.7 Golden Adapter | 同上 | 每框架 ≥ 5/10 个 Golden Cases |
| 宪法 §7 可观测性 | 同上 | supteam_* 指标 + OTel + JSON 日志 |
| 宪法 §9.7 静态质量 | 同上 | ruff + pyright strict + bandit + pip-audit |

---

## 附录 B：ADR / Constitution 引用矩阵

| 决策 | 引用 | 章节 | 状态 |
|------|------|------|------|
| `typing.Protocol` 作为 Adapter 抽象 | ADR-0005 | §3.3 | Accepted |
| Python-native framework 同进程 plugin | ADR-0005 + L1 Arch | §3.3 + §6.4 | Accepted |
| 非 Python framework Sidecar 模式 | ADR-0005 + L1 Arch | §3.3 + §6.4 | Accepted |
| framework SDK import 仅在 framework adapter 子包 | 宪法 §3.7 + ADR-0005 §3.3 | — | 强制 |
| `python:3.12-slim` 多阶段镜像 | ADR-0005 | §2.2 + §9.3 | Accepted |
| Adapter 镜像非 root + read-only rootfs | 宪法 §3.5 + ADR-0005 §9.3 | — | 强制 |
| 5 行 YAML 契约 | L1 Arch v0.2.0 | §6.2 | Accepted |
| 6 框架适配矩阵 | L1 Arch v0.2.0 + L2-3 v0.1.0 | §6.5 + §5 | 继承 v0.1.0 |
| Adapter 错误码范围 -32001 ~ -32007 | L2-1 v0.2.0 + L2-3 v0.1.0 | §7 + §9 | 继承 v0.1.0 |
| Golden Adapter 测试强制 | 宪法 §4.7 | — | 强制 |
| Supteam_adapter_* 指标命名 | L1 v0.2.0 + L2-3 v0.1.0 | §16 + §10 | 继承 v0.1.0 |
| mTLS / cert-manager 挂载 | ADR-0005 §9.1 + L1 Arch v0.2.0 | §10.2 | Accepted |
| 单进程 Uvicorn worker | ADR-0005 §6.2 + L1 Arch v0.2.0 | §11.5 | Accepted |
| Adapter 不持有 LLM API key | L1 Arch v0.2.0 + 宪法 §3.5.3 | §6.4 + §3.5.3 | 强制 |

---

## 变更记录

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| v0.1-draft | 2026-07-24 | 初稿：12 节 + 2 附录；6 框架适配矩阵 + Card 转换层 + 镜像策略 + 错误码 + Golden Adapter 测试 | Claude Code (#11 会话) |
| v0.1.0 | 2026-07-24 | 评审通过（[l2-3-adapter-review.md](../reviews/l2-3-adapter-review.md) §A 10 维度全通过）；附录 B 8 项开放问题保留移交 L3 | 项目发起人（基于 MVP 例外 14.5 单点评审；#12 会话） |
| v0.1.0 + ADR-0005 指针 | 2026-07-24 | 顶部追加 ADR-0005 supersede 指针（标记为「迁移输入」），Go 实现条款已 supersede | 项目发起人（#18 会话） |
| **v0.2-draft** | **2026-07-26** | **Python 重写：14 节 + 2 附录；typing.Protocol + uv workspace + 同进程 plugin + Sidecar 双形态 + Pydantic v2 + Tenacity + structlog + 5 项 Python 实现决策 + 14 项开放问题（含 5 项 §2.3 移交 L3-3）** | **Claude Code (#34 会话)** |
| **v0.2.0** | **2026-07-26** | **#35 会话评审通过：[l2-3-adapter-python-review.md](../../reviews/l2-3-adapter-python-review.md) §A-§P 10 维度全 PASS（0 阻塞项 · 3 关注项 · 4 建议项）；5 项 Python 实现决策 D-1~D-5 锁定；66KB / 1267 行颗粒度偏差合理（2.3x · §N.3 决议保留完整版）；wire contract 与 v0.1.0 Go baseline 完全继承（11/11 项）；与 L1 v0.2.0 + L2-1 v0.2.0 + L2-2 v0.2.0 + L2-4 v0.1.0 + ADR-0005 + 宪法 v0.5.0 严格一致；下次会话入口：L2-3 Spec v0.2-draft Python 起草（独立会话；30-40KB / ~800-1000 行；建议拆 Spec 起草 + 评审两会话避免 §16.1 红线）** | **项目发起人（基于 MVP 例外 14.5 单点评审；#35 会话）** |
