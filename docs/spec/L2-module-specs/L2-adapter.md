# L2 模块 Spec：Adapter（框架适配层 · Python-first）

> **⚠️ ADR-0005 supersede 指针（2026-07-26）**：本 v0.2-draft Python Spec 文档**仅 supersede Go interface / Go package / Helm values Go 镜像块 实现条款**；wire contract（Adapter 契约 / 5 行 YAML 原则 / 6 框架矩阵 / Card 转换 / 错误码 / 镜像策略 / 测试 ID / 生命周期契约）与 v0.1.0 Go baseline 业务语义**完全继续有效**。L1 v0.2.0 / L2-1 v0.2.0 / L2-2 v0.2.0 已于 2026-07-24 评审通过，依据 ADR-0005 Python-first 全栈迁移 + 宪法 v0.5.0 §3.8。
>
> **Python 重写映射**：Go `interface Adapter`（8 方法）→ Python `typing.Protocol` + `@runtime_checkable`（3 核心方法 + FrameworkAdapter 扩展）；Go `AdapterError` → Python `AdapterError(Exception)` + `StrEnum` 错误码；Go `client-go` ConfigMap → Python `kubernetes_asyncio` + `pydantic-settings`；Go `net/http` → ASGI (Uvicorn 单 worker) + `httpx.AsyncClient`；Helm values `python:3.12-slim` 多阶段镜像替代 Go 静态二进制
>
> **层级**：L2 — 模块 Spec
> **模块 ID**：C-3（Adapter，见 L1 v0.2.0 Architecture §4.1）
> **代码位置**：`packages/adapter-sdk/src/supteam_a2a/adapter/` + `adapters/{framework}/src/supteam_a2a/adapters/{framework}/`（**Python-first · ADR-0005 §13 工程布局 · uv workspace**）
> **版本**：**v0.2.0**（Python 重写 · 2026-07-26 #36 起草完整版 + #37 评审通过；14 节 + 2 附录 / 114KB / 2705 行）
> **状态**：✅ **v0.2.0**（2026-07-26 #37 会话评审通过；[l2-3-adapter-spec-python-review.md](../reviews/l2-3-adapter-spec-python-review.md) §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项；与 v0.2.0 Design + v0.1.0 Go baseline wire contract 完全继承）
> **配套设计**：[`docs/design/L2-modules/L2-adapter.md`](../../design/L2-modules/L2-adapter.md) **v0.2.0 Python**（2026-07-26 #35 评审通过；1267 行 / 66KB / 14 节 + 2 附录；本 Spec 的设计依据）
> **Go baseline（v0.1.0 · 归档丢失）**：v0.1.0 Go Spec 1044 行 / 43KB / 7 节 + 2 附录（已被 v0.2-draft Python 覆盖；wire contract / 业务语义完全继续有效）
> **本模块目的**：把 [`docs/design/L2-modules/L2-adapter.md`](../../design/L2-modules/L2-adapter.md) v0.2.0 中的 6 框架适配设计落地为 **Python 代码契约**（typing.Protocol + Pydantic）、**Helm values 配置面**（uv 多阶段镜像）、**测试骨架**（6 层级 + 100+ 测试 ID）与 **生命周期契约**（5 时序图）。它是 L2-1 A2A Protocol（嵌入 Server SDK）与 L2-2 Operator Core（创建 Adapter container）的**下游实现**，自身无 Controller（无 reconcile 逻辑）。

---

## 0. 阅读指南

- **读者**：框架贡献者（实现 framework adapter 子包）、Operator Core 维护者（了解 Adapter container 资源模型 + 生命周期契约）、Agent 作者（理解 5 行 YAML 契约 + Helm 配置）、L3-3 文件级 Spec 作者（实现输入）
- **必读章节**：§1（模块概述 + public API surface）/ §2（包结构 + 文件清单）/ §3（Adapter Protocol）/ §6（错误码）/ §11（Helm values）/ §12（测试骨架）
- **可选章节**：§4（Card 转换）/ §5（配置）/ §7（可观测性）/ §10（生命周期契约，Operator Core 集成时必读）
- **配套阅读**：[L2-3 Design v0.2.0](../../design/L2-modules/L2-adapter.md) · [L2-1 A2A Protocol Spec v0.2.0 Python](./L2-a2a-protocol.md) · [L2-2 Operator Core Design v0.2.0 Python](../../design/L2-modules/L2-operator-core.md) + [L2-2 Operator Core Spec v0.2.0 Python](./L2-operator-core.md) · [L1 Architecture v0.2.0 §6](../../design/L1-architecture.md) · [ADR-0005](../../adr/0005-python-first-technology-stack.md)

---

## 1. 模块概述 + Public API Surface

### 1.1 模块职责

L2-3 Adapter 是 `superteam-a2a` **运行时层（Runtime Layer）** 的实现子层，承载 6 个 Agent framework（LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents）与 A2A 协议之间的双向翻译。本 Spec 定义：

1. **Adapter Protocol 契约**（typing.Protocol + @runtime_checkable）
2. **6 framework adapter 子包**（每 framework 独立 workspace package）
3. **Card 转换层**（Pydantic v2 + 官方 `a2a.AgentCard`）
4. **配置注入**（Pydantic Settings + 4 层优先级）
5. **错误码 + 重试**（StrEnum + Tenacity）
6. **可观测性埋点**（Prometheus + OTel + structlog）
7. **容器镜像打包**（uv workspace + python:3.12-slim 多阶段）
8. **生命周期契约**（5 时序图 + Operator Core 集成）
9. **Helm values**（6 framework 独立 image override + Pod Security restricted）
10. **测试骨架**（6 层级 + 100+ 测试 ID）

### 1.2 Public API Surface（边界规则）

**三层 import 规则**（与 L2-1 §3.2 + 宪法 §3.7 + ADR-0005 §3.3 严格一致）：

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

**关键约束**：
1. **framework SDK import 仅在 framework adapter 子包内**（用 ruff / pyright 自定义 import linter 检测；规则名 `ST-ADAPTER-BOUNDARY`）
2. `adapter-sdk` 严禁依赖任何 framework（确保各 framework adapter 子包可独立升级）
3. Operator Core 严禁 import `adapter-sdk` 或 framework adapter（Operator 只通过 K8s CRD 编排 Adapter container）
4. framework SDK 升级通过独立 workspace package 决策，不影响其他 framework

### 1.3 公共 API 一览（来自 adapter-sdk）

```python
# adapter-sdk 公共 API（业务层可 import）
from superteam_a2a.adapter import (
    # Adapter Protocol（§3.1）
    Adapter,
    FrameworkAdapter,
    # Card 转换（§4.1）
    AgentCardConverter,
    AdapterCardConfig,
    MemoryCapabilities,
    # 配置（§5.1）
    AdapterConfig,
    FrameworkAdapterConfig,
    # 错误（§6.1）
    AdapterErrorCode,
    AdapterError,
    create_retry_policy,
    # 可观测性（§7.1）
    REQUESTS_TOTAL,
    REQUEST_DURATION_SECONDS,
    CARD_CONVERSION_DURATION_SECONDS,
    FRAMEWORK_LOAD_DURATION_SECONDS,
    ERRORS_TOTAL,
    ACTIVE_AGENTS,
    GOLDEN_CASE_PASS_TOTAL,
    create_tracer,
    configure_logging,
    # 生命周期（§10.2）
    Lifecycle,
)
```

**私有 API**（`_internal/`）：业务层严禁 import；包含 framework SDK 加载器、证书 watcher、metrics 注册器等。

### 1.4 与其他模块的契约

| 模块 | 接口 | 方向 |
|------|------|------|
| L2-1 A2A Protocol | `superteam_a2a.a2a.create_app(card=...)` | Adapter 嵌入 |
| L2-1 A2A Protocol | `superteam_a2a.a2a.upstream.AgentCard` | Adapter 提供 |
| L2-1 A2A Protocol | `superteam_a2a.a2a.A2AClient`（可选） | Adapter 调用（multi-agent 协作） |
| L2-2 Operator Core | K8s CRD `Agent.spec.adapter` | Operator 创建 Adapter container |
| L2-4 Knowledge / Memory | `queryKnowledge` / `recordMemory` 等 4 method | v1.0+ Adapter 代理（Memory 降级路径） |
| Agent container（Sidecar 模式） | HTTP/JSON localhost:7080 | Adapter 调用（framework SDK） |

---

## 2. 包结构与文件清单（ADR-0005 §13 工程布局）

### 2.1 总览（uv workspace + adapter-sdk + 6 framework adapter sub-packages）

```
pyproject.toml                          # uv workspace 根 + 共享工具配置（ruff / pyright / pytest）
uv.lock                                 # 单一 lockfile，CI 必须 `uv sync --frozen`

packages/
  adapter-sdk/
    pyproject.toml                      # 独立依赖：pydantic + httpx + tenacity + prometheus-client + opentelemetry-sdk + structlog
    src/supteam_a2a/adapter/            # 通用 Adapter 抽象（无 framework 依赖）
      __init__.py                       # 公共 API surface（§1.3）
      protocol.py                       # Adapter / FrameworkAdapter Protocol（§3.1）
      card.py                           # AgentCardConverter Protocol + Pydantic 实现（§4.1）
      config.py                         # AdapterConfig（Pydantic BaseSettings）+ 4 层优先级加载（§5.1）
      errors.py                         # 7 个错误码常量（-32001 ~ -32007）+ A2A 错误转换（§6.1）
      retry.py                          # Tenacity retry policy（§6.3）
      observability/
        __init__.py
        metrics.py                      # supteam_adapter_* Prometheus 指标注册（§7.1）
        tracing.py                      # OpenTelemetry provider 注入（显式，§7.2）
        logging.py                      # structlog setup（JSON 输出，§7.3）
      server.py                         # A2A Server 嵌入封装（基于 L2-1 superteam_a2a.a2a.create_app，§3.3）
      transport.py                      # httpx.AsyncClient 工厂（Sidecar 模式，§3.4）
      lifecycle.py                      # Start/Stop/Reload hook（§10.2）
      _internal/                        # ⚠️ private — 业务层禁止 import
        __init__.py
    tests/                              # adapter-sdk 单元测试（≥ 95% 覆盖目标）
      unit/
        test_protocol.py                # UT-PROT-ADAPTER-001 ~ 003
        test_card.py                    # UT-PROT-CARD-001 ~ 006
        test_config.py                  # UT-PROT-CONFIG-001 ~ 005
        test_errors.py                  # UT-PROT-ERROR-001 ~ 004
        test_retry.py                   # UT-PROT-RETRY-001 ~ 006
        test_metrics.py                 # UT-PROT-METRICS-001 ~ 003
        test_tracing.py                 # UT-PROT-TRACING-001 ~ 003
        test_logging.py                 # UT-PROT-LOGGING-001 ~ 004
        test_server.py                  # UT-PROT-SERVER-001 ~ 004
        test_transport.py               # UT-PROT-TRANSPORT-001 ~ 005
        test_lifecycle.py               # UT-PROT-LIFECYCLE-001 ~ 005
        test_boundary.py                # UT-PROT-BOUNDARY-001 ~ 003（linter 检测）

adapters/                               # 6 个 framework adapter 独立 workspace package
  langchain/
    pyproject.toml                      # 独立依赖：langchain-core + langchain + adapter-sdk
    src/supteam_a2a/adapters/langchain/
      __init__.py                       # 公共 API surface
      adapter.py                        # LangChainAdapter class（§3.5）
      card.py                           # LangChain Tool → A2A AgentSkill（§4.2）
      chain.py                          # LCEL Runnable → A2A sendMessage handler（§3.5）
      memory.py                         # LangChain memory → A2A Memory 代理（v1.0+）
      transport.py                      # httpx.AsyncClient 工厂（同进程 plugin 无用）
    tests/
      unit/                             # UT-LC-001 ~ 010
      integration/                      # IT-LC-001 ~ 006
      golden/                           # GLC-01 ~ 10（v1.0 10 个 / v0.5 5 个）
        case-01-basic-rag.yaml
        case-02-tool-call.yaml
        case-03-memory.yaml
        case-04-error.yaml
        case-05-streaming-mock.yaml
        case-NN-{name}.yaml

  autogen/
    pyproject.toml                      # 独立依赖：autogen-agentchat + adapter-sdk
    src/supteam_a2a/adapters/autogen/
      __init__.py
      adapter.py                        # AutoGenAdapter class（§3.6）
      conversable.py                    # ConversableAgent → A2A sendMessage
      group_chat.py                     # GroupChat → A2A multi-agent
      function_map.py                   # function_map → A2A skills（§4.2）
    tests/
      unit/                             # UT-AG-001 ~ 010
      integration/                      # IT-AG-001 ~ 006
      golden/                           # GAG-01 ~ 10

  crewai/
    pyproject.toml                      # 独立依赖：crewai + adapter-sdk（v0.5 上线）
    src/supteam_a2a/adapters/crewai/
      __init__.py
      adapter.py                        # CrewAdapter class（§3.7）
      crew.py                           # Crew.kickoff() → A2A workflow DAG
      tasks.py                          # Crew Task → A2A Task 状态机
      agents.py                         # Crew Agent → A2A AgentCard
    tests/
      unit/                             # UT-CR-001 ~ 010
      integration/                      # IT-CR-001 ~ 006
      golden/                           # GCR-01 ~ 10

  semantic_kernel/
    pyproject.toml                      # 独立依赖：semantic-kernel + adapter-sdk（v0.5 上线）
    src/supteam_a2a/adapters/semantic_kernel/
      __init__.py
      adapter.py                        # KernelAdapter class（§3.8）
      plugins.py                        # kernel.plugins → A2A skills
    tests/
      unit/                             # UT-SK-001 ~ 010
      integration/                      # IT-SK-001 ~ 006
      golden/                           # GSK-01 ~ 10

  strands/
    pyproject.toml                      # 独立依赖：strands-agents + adapter-sdk（v1.0 上线）
    src/supteam_a2a/adapters/strands/
      __init__.py
      adapter.py                        # StrandsAdapter class（§3.9）
      tools.py                          # agent.tools → A2A skills
    tests/
      unit/                             # UT-ST-001 ~ 010
      integration/                      # IT-ST-001 ~ 006
      golden/                           # GST-01 ~ 10

  smolagents/
    pyproject.toml                      # 独立依赖：smolagents + adapter-sdk（v1.0 上线）
    src/supteam_a2a/adapters/smolagents/
      __init__.py
      adapter.py                        # SmolagentsAdapter class（§3.10）
      code_agent.py                     # CodeAgent.run() → A2A
      tool_calling_agent.py             # ToolCallingAgent.run() → A2A
      interpreter.py                    # CodeAgent interpreter 隔离执行
    tests/
      unit/                             # UT-SM-001 ~ 010
      integration/                      # IT-SM-001 ~ 006
      golden/                           # GSM-01 ~ 10

contrib/                                # 第三方贡献 adapters（v1.5+）
  README.md                             # 贡献指南 + 准入审查清单
```

**关键约束**：
- 每个 framework adapter 子包有 **独立 `pyproject.toml`** + 独立 `uv.lock` 锁版本
- framework 依赖（`langchain-core` / `autogen-agentchat` / `crewai` / `semantic-kernel` / `strands-agents` / `smolagents`）仅存在于对应子包
- `adapter-sdk` 与 Operator Core 严禁依赖任何 framework（ADR-0005 §3.3 + 宪法 §3.7）
- `pyproject.toml` 根共享 ruff / pyright / pytest 配置；子包可覆盖

### 2.2 adapter-sdk 包约束（详细）

```toml
# packages/adapter-sdk/pyproject.toml
[project]
name = "supteam-a2a-adapter-sdk"
version = "0.2.0"
requires-python = ">=3.12,<3.13"
dependencies = [
    "pydantic>=2.5,<3.0",
    "pydantic-settings>=2.1,<3.0",
    "httpx>=0.27,<1.0",
    "tenacity>=8.2,<9.0",
    "prometheus-client>=0.20,<1.0",
    "opentelemetry-api>=1.27,<2.0",
    "opentelemetry-sdk>=1.27,<2.0",
    "opentelemetry-exporter-otlp>=1.27,<2.0",
    "structlog>=24.1,<25.0",
    "anyio>=4.3,<5.0",
    "supteam-a2a-core>=0.2.0",  # L2-1 A2A Protocol 依赖
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9.0",
    "pytest-asyncio>=0.23,<1.0",
    "pytest-cov>=5.0,<6.0",
    "respx>=0.21,<1.0",
    "hypothesis>=6.100,<7.0",
    "ruff>=0.5,<1.0",
    "pyright>=1.1,<2.0",
    "bandit>=1.7,<2.0",
    "pip-audit>=2.7,<3.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "ASYNC", "S", "B", "A", "C4", "DTZ", "T10", "RET", "SIM"]
ignore = ["S101"]  # Allow assert in tests

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "S106"]

[tool.pyright]
strict = true
pythonVersion = "3.12"

[[tool.pyright.executionEnvironments]]
root = "src"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests/unit"]
addopts = "--cov=supteam_a2a.adapter --cov-report=term-missing --cov-fail-under=95"
```

### 2.3 framework adapter 子包约束（以 LangChain 为例）

```toml
# adapters/langchain/pyproject.toml
[project]
name = "supteam-a2a-adapter-langchain"
version = "0.2.0"
requires-python = ">=3.12,<3.13"
dependencies = [
    "supteam-a2a-adapter-sdk>=0.2.0",
    "langchain-core>=0.1,<0.3",
    "langchain>=0.1,<0.3",
    "langchain-community>=0.0.20,<1.0",  # 可选
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9.0",
    "pytest-asyncio>=0.23,<1.0",
    "respx>=0.21,<1.0",
    "hypothesis>=6.100,<7.0",
    "langchain-openai>=0.1,<1.0",  # 测试用小模型
]

[tool.ruff]
inherit = "../../pyproject.toml"

[tool.pyright]
inherit = "../../pyproject.toml"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests/unit", "tests/integration", "tests/golden"]
addopts = "--cov=supteam_a2a.adapters.langchain --cov-report=term-missing --cov-fail-under=80"
```

---

## 3. Adapter Protocol（typing.Protocol + @runtime_checkable）

### 3.1 核心 Protocol（与 L1 v0.2.0 Architecture §6.3 完全对齐）

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/protocol.py
from typing import Protocol, runtime_checkable, Any
from superteam_a2a.a2a.upstream import AgentCard, Message, Task, Part


@runtime_checkable
class Adapter(Protocol):
    """Adapter ↔ A2A Server 协议边界（ADR-0005 §3.3 + L1 Architecture §6.3）。
    
    所有 framework adapter 必须实现此 Protocol；通过 duck-typing 检测。
    """
    
    async def on_message(
        self,
        message: Message,
        context_id: str | None = None,
    ) -> Task:
        """处理 A2A sendMessage；返回 Task + 状态。
        
        Args:
            message: A2A Message（来自 sendMessage params.message）
            context_id: A2A context ID（用于 multi-turn 对话）
        
        Returns:
            Task: A2A Task（status + artifacts）
        
        Raises:
            AdapterError: 包含 code (-32001 ~ -32007) + framework_error
        """
        ...
    
    def agent_card(self) -> AgentCard:
        """返回 Agent Card（用于 /.well-known/agent.json）。
        
        Card 转换由 §4 详述；启动时构建，运行期 cached。
        """
        ...
    
    async def health_check(self) -> bool:
        """健康检查（Adapter container readiness）。
        
        Returns:
            True: Adapter 可用
            False: Framework SDK 未初始化 / Agent container 不可达（Sidecar）
        """
        ...


@runtime_checkable
class FrameworkAdapter(Protocol):
    """框架特定扩展钩子（Framework authors 必实现）。"""
    
    async def on_framework_event(self, event: dict[str, Any]) -> None:
        """框架事件回调（如 LangChain chain run event / AutoGen message event）。
        
        用于 framework-specific observability；非必须。
        """
        ...
```

**关键约束**：
- `@runtime_checkable` 允许 `isinstance(obj, Adapter)` 检查（Pyright strict 兼容）
- Protocol 方法签名必须严格对齐；运行时错误通过 `AdapterError` 抛出
- Protocol 不依赖任何 framework（确保 `adapter-sdk` 可独立测试）

### 3.2 AgentCardConverter Protocol

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/card.py
from typing import Protocol, runtime_checkable
from superteam_a2a.a2a.upstream import AgentCard, AgentSkill


@runtime_checkable
class AgentCardConverter(Protocol):
    """Agent Card 转换器（framework → A2A）。
    
    每 framework adapter 子包提供默认实现；用户可自定义。
    """
    
    def convert(
        self,
        framework_agent: Any,
        required_fields: tuple[str, ...] = ("name", "description"),
    ) -> AgentCard:
        """将 framework agent 转换为 A2A AgentCard。
        
        Args:
            framework_agent: framework 原生 agent 对象（任意类型）
            required_fields: 必填字段列表；缺失抛 AdapterError(-32003)
        
        Returns:
            AgentCard: A2A standard AgentCard
        
        Raises:
            AdapterError(code=-32003): 必填字段缺失
        """
        ...
    
    def required_fields(self) -> tuple[str, ...]:
        """返回必填字段列表（用于启动期校验）。"""
        ...
```

**默认实现** `DefaultAgentCardConverter` 通过反射调用 framework agent 的 5 个关键方法：

```python
class DefaultAgentCardConverter:
    """默认 AgentCard 转换器（反射实现）。"""
    
    def convert(
        self,
        framework_agent: Any,
        required_fields: tuple[str, ...] = ("name", "description"),
    ) -> AgentCard:
        # 1. 反射调用 5 个关键方法
        name = getattr(framework_agent, "name", None) or getattr(framework_agent, "get_name", lambda: None)()
        description = getattr(framework_agent, "description", None) or getattr(framework_agent, "get_description", lambda: None)()
        tools = getattr(framework_agent, "tools", None) or getattr(framework_agent, "get_tools", lambda: [])()
        memory_caps = getattr(framework_agent, "memory_capabilities", None) or MemoryCapabilities()
        streaming = getattr(framework_agent, "streaming", False)
        
        # 2. 必填字段缺失 → -32003
        if not name:
            raise AdapterError(
                code=AdapterErrorCode.CARD_CONVERSION_FAILED,
                message=f"Missing required field: name",
            )
        if not description:
            raise AdapterError(
                code=AdapterErrorCode.CARD_CONVERSION_FAILED,
                message=f"Missing required field: description",
            )
        
        # 3. tools → skills 转换
        skills = [self._tool_to_skill(t) for t in tools]
        
        # 4. 构造 AgentCard
        return AgentCard(
            name=name,
            description=description,
            skills=skills,
            memory_capabilities=memory_caps,
            streaming=streaming,
        )
    
    def _tool_to_skill(self, tool: Any) -> AgentSkill:
        """framework tool → A2A AgentSkill 转换。"""
        # 各 framework 实现覆盖此方法
        return AgentSkill(
            name=getattr(tool, "name", str(tool)),
            description=getattr(tool, "description", ""),
            input_modes=["text/plain"],  # 降级（JSON Schema 推导失败时）
            output_modes=["text/plain"],
        )
    
    def required_fields(self) -> tuple[str, ...]:
        return ("name", "description")
```

### 3.3 A2A Server 嵌入封装

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/server.py
from starlette.applications import Starlette
from superteam_a2a.a2a import create_app
from superteam_a2a.adapter.protocol import Adapter


def create_adapter_app(
    adapter: Adapter,
    mtls_config: MtlsConfig | None = None,
    middlewares: list[Middleware] | None = None,
) -> Starlette:
    """构造 Adapter A2A Server 应用。
    
    Args:
        adapter: Adapter Protocol 实现
        mtls_config: mTLS 配置（L2-1 §4）
        middlewares: ASGI middleware 链（顺序：Tracing → Auth → RateLimit → Metrics）
    
    Returns:
        Starlette: ASGI 应用实例（Uvicorn 启动）
    """
    return create_app(
        card=adapter.agent_card(),
        mtls_config=mtls_config,
        middlewares=middlewares,
        # Adapter 注入：每个 A2A method 调用 adapter.on_message()
        adapter_handler=adapter.on_message,
        health_check=adapter.health_check,
    )
```

### 3.4 HTTP Client（A2A → Agent container · Sidecar 模式）

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/transport.py
import httpx
from superteam_a2a.a2a.upstream import MtlsConfig


def create_agent_client(
    base_url: str = "http://localhost:7080",
    mtls_config: MtlsConfig | None = None,
    timeout: float = 30.0,
    max_connections: int = 100,
    max_keepalive: int = 20,
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
        limits=httpx.Limits(max_connections=max_connections, max_keepalive=max_keepalive),
        verify=mtls_config.ssl_context if mtls_config else True,
    )
```

### 3.5 LangChain Adapter 实现（示例）

```python
# adapters/langchain/src/supteam_a2a/adapters/langchain/adapter.py
from typing import Any
from langchain_core.runnables import Runnable
from superteam_a2a.adapter import (
    Adapter,
    AdapterError,
    AdapterErrorCode,
    FrameworkAdapter,
    AgentCardConverter,
)
from superteam_a2a.adapter.card import AdapterCardConfig, MemoryCapabilities
from superteam_a2a.a2a.upstream import AgentCard, Message, Task


class LangChainAdapter(Adapter, FrameworkAdapter):
    """LangChain framework adapter（v0.2 同进程 plugin）。
    
    Args:
        runnable: langchain_core.runnables.Runnable（用户 LCEL chain）
        config: LangChainAdapterConfig（framework-specific 配置）
        card_converter: AgentCardConverter Protocol 实现（可选，默认使用反射转换）
    """
    
    def __init__(
        self,
        runnable: Runnable,
        config: "LangChainAdapterConfig",
        card_converter: AgentCardConverter | None = None,
    ):
        self._runnable = runnable
        self._config = config
        self._card_converter = card_converter or DefaultAgentCardConverter()
        # Card 在启动时构建并缓存
        self._card = self._card_converter.convert(runnable)
    
    async def on_message(
        self,
        message: Message,
        context_id: str | None = None,
    ) -> Task:
        try:
            # 1. 转换 A2A Message → LangChain input
            lc_input = self._convert_message_to_lc(message)
            # 2. 调用 framework（CPU 工作通过 anyio.to_thread offload）
            lc_output = await anyio.to_thread.run_sync(
                self._runnable.invoke, lc_input,
            )
            # 3. 转换 framework output → A2A Task
            return self._convert_lc_to_task(lc_output, context_id)
        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(
                code=AdapterErrorCode.TOOL_INVOCATION_FAILED,
                message=f"LangChain invocation failed: {e!s}",
                framework_error={"exception_type": type(e).__name__},
            )
    
    def agent_card(self) -> AgentCard:
        return self._card
    
    async def health_check(self) -> bool:
        # LangChain 总是 loaded（同进程 plugin）
        return self._runnable is not None
    
    async def on_framework_event(self, event: dict[str, Any]) -> None:
        # LangChain callback handler（可选）
        # 记录到 OTel Span event
        span = trace.get_current_span()
        if span:
            span.add_event("framework.event", attributes={"event_type": event.get("type")})
```

### 3.6-3.10 其他 5 Framework Adapter 实现概要

**AutoGen Adapter**（§3.6）：基于 `autogen_agentchat.ConversableAgent.on_messages()`，Card 转换点为 `function_map`（dict[str, Callable]），GroupChat 多 agent 拓扑映射复杂。

**CrewAI Adapter**（§3.7）：基于 `crewai.Crew.kickoff()`，Card 转换点为 `Agent.tools + Task.tools`（Pydantic 模型），Sequential/Parallel/Hierarchical 拓扑需完整支持（v0.5 上线，Sidecar 模式）。

**Semantic Kernel Adapter**（§3.8）：基于 `semantic_kernel.Kernel.invoke()`，Card 转换点为 `kernel.plugins[name].functions[name]`，Python + .NET 双实现需维护两条代码路径（v0.5 上线）。

**Strands Adapter**（§3.9）：基于 `strands.Agent()`，Card 转换点为 `agent.tools`（Tool 对象列表），Strands tools 自带 `tool_spec`（v1.0 上线，Sidecar 模式）。

**Smolagents Adapter**（§3.10）：基于 `smolagents.CodeAgent.run()` / `ToolCallingAgent.run()`，Card 转换点为 `agent.tools + CodeAgent interpreter`，interpreter 单独标记 `code_execution: true`（v1.0 上线，Sidecar 模式）。

**关键约束**（与 L1 v0.2.0 Architecture §6.3 + 宪法 §3.7 一致）：
1. **Adapter 不得 import 任何 Agent framework**（与 Operator 规则一致，宪法 §3.7）
2. **Adapter 必须复用 A2A Core 的 Server / Schema / TLS / 限流 / Trace**，不复制协议实现（ADR-0005 §3.3）
3. **Adapter 镜像基线 `python:3.12-slim` 多阶段构建**（ADR-0005 §2.2）
4. **Adapter 严禁持有 LLM API key**（L1 v0.2.0 Architecture §6.4 + 宪法 §3.5.3）；该 Secret 由 Agent container 持有

---

## 4. A2A Card 转换层

### 4.1 Pydantic Schema

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/card.py
from pydantic import BaseModel, Field, ConfigDict
from superteam_a2a.a2a.upstream import AgentCard, AgentSkill


class AdapterCardConfig(BaseModel):
    """Adapter 启动时从 framework introspection 推导的 Card 配置。
    
    用于 cached Card 的运行时覆盖（如 reload 时）。
    """
    
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


def build_agent_card(config: AdapterCardConfig) -> AgentCard:
    """从 AdapterCardConfig 构造 A2A AgentCard。"""
    return AgentCard(
        name=config.name,
        description=config.description,
        skills=config.skills,
        memory_capabilities=config.memory_capabilities,
        streaming=config.streaming,
    )
```

### 4.2 各 framework skills 转换细节

```python
# adapters/langchain/src/supteam_a2a/adapters/langchain/card.py
from langchain_core.tools import BaseTool
from superteam_a2a.adapter import AgentSkill


def langchain_tool_to_skill(tool: BaseTool) -> AgentSkill:
    """LangChain Tool → A2A AgentSkill 转换。
    
    每个 tool → 一个 A2A skill：
    - name = tool.name
    - description = tool.description
    - input_modes = JSON Schema 推导（失败则降级 ["text/plain"]）
    - output_modes = ["text/plain"]
    """
    try:
        # 从 tool.args_schema 推导 JSON Schema
        schema = tool.args_schema.schema() if hasattr(tool, "args_schema") else {}
        input_modes = ["application/json"] if schema else ["text/plain"]
    except Exception:
        # 推导失败 → 降级
        input_modes = ["text/plain"]
    
    return AgentSkill(
        name=tool.name,
        description=tool.description,
        input_modes=input_modes,
        output_modes=["text/plain"],
    )
```

**6 framework skills 转换规则**（与 v0.2 Design §6.2 一致）：

| Framework | 工具来源 | 转换规则 |
|-----------|----------|----------|
| LangChain | `agent.get_input_schema()` + tool name + tool description | 每个 tool → 1 个 skill；name = tool.name；description = tool.description；inputModes = JSON Schema 推导；outputModes = `["text/plain"]` |
| AutoGen | `ConversableAgent.function_map`（dict[str, Callable]） | 每个 function → 1 个 skill；docstring → description；signature → JSON Schema |
| CrewAI | `Agent.tools` + `Task.tools` | 同 LangChain；但 CrewAI tools 是 Pydantic 模型，需先 JSON Schema 化 |
| Semantic Kernel | `kernel.plugins[name].functions[name]` | 每个 kernel function → 1 个 skill；function.description → description；kernel 参数 → JSON Schema |
| Strands | `agent.tools`（Tool 对象列表） | 同 LangChain；Strands tools 自带 `tool_spec` |
| Smolagents | `agent.tools` + CodeAgent `interpreter` | 普通 tool → skill；CodeAgent interpreter → 单独标记 `code_execution: true` |

### 4.3 Card 转换失败处理（与 v0.2 Design §6.3 完全一致）

- **必填字段缺失** → 启动失败（Fatal），错误码 `-32003 CARD_CONVERSION_FAILED`
- **可选字段缺失** → 使用默认值（如 description 为空则使用 `name`）
- **JSON Schema 推导失败** → 记录 warning，skill 仍注册但 `inputModes: ["text/plain"]`（降级）

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/card.py
import structlog

logger = structlog.get_logger(__name__)


def safe_skill_conversion(tool: Any, framework: str) -> AgentSkill | None:
    """安全的 tool → skill 转换（处理 JSON Schema 推导失败）。"""
    try:
        return convert_tool_to_skill(tool)
    except Exception as e:
        logger.warning(
            "card_conversion_fallback",
            framework=framework,
            tool_name=getattr(tool, "name", str(tool)),
            error=str(e),
        )
        return AgentSkill(
            name=getattr(tool, "name", "unknown"),
            description=getattr(tool, "description", ""),
            input_modes=["text/plain"],  # 降级
            output_modes=["text/plain"],
        )
```

---

## 5. 配置注入与 Secret 管理

### 5.1 Pydantic Settings 三层优先级加载

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/config.py
from typing import Literal
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AdapterConfig(BaseSettings):
    """Adapter 通用配置（从 env / ConfigMap / Secret 三层加载）。
    
    优先级（高 → 低）：Secret > ConfigMap > Env
    """
    
    model_config = SettingsConfigDict(
        env_prefix="ADAPTER_",
        env_file=".env",
        extra="forbid",
        case_sensitive=False,
    )
    
    # 必填
    framework: Literal["langchain", "autogen", "crewai", "semantic_kernel", "strands", "smolagents", "hello"]
    
    # A2A Server
    port: int = Field(default=8080, ge=1024, le=65535)
    host: str = Field(default="0.0.0.0")
    
    # Agent container 通信（Sidecar 模式）
    agent_service_host: str = Field(default="localhost")
    agent_service_port: int = Field(default=7080, ge=1024, le=65535)
    
    # 部署模式（v0.2+）
    embedded: bool = Field(default=False)  # True = 同进程 plugin；False = Sidecar
    
    # 可观测性
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    otlp_endpoint: str | None = Field(default="http://otel-collector:4317")
    metrics_enabled: bool = Field(default=True)
    
    # mTLS（cert-manager mounted）
    mtls_cert_path: str | None = Field(default="/etc/tls/tls.crt")
    mtls_key_path: str | None = Field(default="/etc/tls/tls.key")
    mtls_ca_path: str | None = Field(default="/etc/tls/ca.crt")
    mtls_spiffe_required: bool = Field(default=True)
    
    # 框架特定配置（CRD spec.adapter.config 加载）
    framework_config_path: str | None = Field(default=None)  # 指向挂载的 framework 配置 YAML
    
    # 健康检查
    health_check_path: str = Field(default="/healthz")
    readiness_path: str = Field(default="/readyz")
    
    # 优雅停机
    shutdown_grace_period_seconds: int = Field(default=30, ge=5, le=120)


class FrameworkAdapterConfig(BaseModel):
    """Framework 特定配置（从 Agent CRD spec.adapter.config 加载）。
    
    各 framework adapter 子包扩展此基类。
    """
    
    model_config = ConfigDict(extra="forbid", frozen=True)
    
    # framework-specific 字段（如 LangChain max_iterations）
    # 各 framework adapter 子包扩展
```

### 5.2 4 层优先级加载契约

| 优先级 | 来源 | 适用场景 | 注入时机 |
|--------|------|----------|----------|
| 1（最高） | K8s `Secret`（envFrom / volumeMount） | mTLS cert、LLM API key、第三方服务 token | Adapter 启动时 + 热加载（K8s 1.27+） |
| 2 | `Agent` CRD `spec.adapter.config` | 用户声明的 framework 特定配置（如 LangChain `max_iterations`） | Adapter 启动时 |
| 3 | `ConfigMap` | 集群级默认 + 框架特定默认（如 LangChain 默认 model） | Adapter 启动时 |
| 4（最低） | 环境变量 | Operator 注入（`POD_NAME`、`NAMESPACE`、`ADAPTER_PORT`） | Adapter 启动时（不可变） |

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/config.py
from pathlib import Path
import yaml
import structlog

logger = structlog.get_logger(__name__)


async def load_framework_config(
    config_path: str | None,
    secret_refs: dict[str, str] | None = None,
) -> dict[str, Any]:
    """从 CRD config + Secret 合并 framework 配置。
    
    Args:
        config_path: framework 配置 YAML 文件路径（Operator 挂载）
        secret_refs: Secret 引用字典（key → file path）
    
    Returns:
        dict: 合并后的 framework 配置
    """
    config: dict[str, Any] = {}
    
    # 1. 加载 YAML 配置
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
        logger.info("framework_config_loaded", path=config_path)
    
    # 2. 合并 Secret 引用（仅协议层 Secret）
    if secret_refs:
        for key, secret_path in secret_refs.items():
            if Path(secret_path).exists():
                secret_value = Path(secret_path).read_text().strip()
                config[f"_secret_{key}"] = secret_value
                logger.info("secret_loaded", key=key)
    
    return config
```

### 5.3 Secret 隔离原则（与 v0.2 Design §8.3 完全一致）

- **Adapter 容器不应持有 LLM API key** —— 该 Secret 由 **Agent 容器** 持有（通过 volumeMount 挂载）
- **Adapter 只持有协议层 Secret**：mTLS cert、prometheus pushgateway token
- 理由：Adapter 是无状态翻译层，重启频率高；持有业务 Secret 增加泄露面

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/config.py
from pydantic import field_validator


class AdapterConfig(BaseSettings):
    """...（继承自 §5.1）"""
    
    @field_validator("llm_api_key", mode="before")
    @classmethod
    def reject_llm_api_key(cls, v: Any) -> Any:
        """拒绝 Adapter 持有 LLM API key（仅 Agent container 持有）。"""
        if v is not None:
            raise ValueError(
                "Adapter MUST NOT hold LLM API key. "
                "Use Agent container's Secret mount instead. (Constitution §3.5.3)"
            )
        return v
```

### 5.4 5 行 YAML 契约（与 L1 v0.2.0 Architecture §6.2 完全一致）

```yaml
# Agent CRD spec（YAML 片段）
spec:
  adapter:
    framework: langchain          # 1. 框架名（枚举：langchain / autogen / crewai / semantic_kernel / strands / smolagents / hello）
    image: my-agent:latest        # 2. Agent 容器镜像
    card: ./agent-card.yaml       # 3. Agent Card（可选，默认由 framework introspection 推导）
    resources:                    # 4. 资源（可选，参考 L1 §11.1 默认限制）
      limits: { cpu: "1", memory: "2Gi" }
    healthCheck: /healthz         # 5. 健康检查路径（可选，默认 /healthz）
    embedded: false               # v0.2+ 可选 true（仅 Python-native framework）
```

### 5.5 配置校验

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/config.py
from pydantic import ValidationError


def validate_adapter_config(config: AdapterConfig) -> None:
    """启动期校验 AdapterConfig。
    
    Raises:
        AdapterError(-32007 CONFIG_VALIDATION_FAILED): 校验失败
    """
    try:
        # Pydantic 自动校验（extra="forbid" 强制）
        AdapterConfig.model_validate(config.model_dump())
    except ValidationError as e:
        raise AdapterError(
            code=AdapterErrorCode.CONFIG_VALIDATION_FAILED,
            message=f"Adapter config validation failed: {e!s}",
            framework_error={"validation_errors": e.errors()},
        )
    
    # 额外业务校验
    if config.embedded and config.framework not in ("langchain", "autogen", "semantic_kernel"):
        raise AdapterError(
            code=AdapterErrorCode.CONFIG_VALIDATION_FAILED,
            message=f"embedded=true only allowed for Python-native frameworks, got: {config.framework}",
        )
```

---

## 6. 错误码与重试

### 6.1 Adapter 错误码体系（与 v0.2 Design §9.1 + L2-1 §7 严格一致）

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/errors.py
from enum import StrEnum
from superteam_a2a.a2a.upstream import JSONRPCError


class AdapterErrorCode(StrEnum):
    """Adapter 扩展错误码（与 L2-1 §7 errors.py 协调）。
    
    范围 -32001 ~ -32007（与 L2-1 A2A 域错误码范围对齐）。
    """
    
    FRAMEWORK_NOT_LOADED = "-32001"
    FRAMEWORK_VERSION_INCOMPATIBLE = "-32002"
    CARD_CONVERSION_FAILED = "-32003"
    TOOL_INVOCATION_FAILED = "-32004"
    MEMORY_BACKEND_UNAVAILABLE = "-32005"
    AGENT_CONTAINER_UNREACHABLE = "-32006"
    CONFIG_VALIDATION_FAILED = "-32007"


class AdapterError(Exception):
    """Adapter 域错误。
    
    Args:
        code: AdapterErrorCode（7 个之一）
        message: 错误消息（用于 A2A response.error.message）
        framework_error: framework 原生异常详情（仅 debug 模式序列化到 A2A response.data）
    """
    
    def __init__(
        self,
        code: AdapterErrorCode,
        message: str,
        framework_error: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message
        self.framework_error = framework_error
        super().__init__(message)
    
    def to_jsonrpc_error(self, include_framework_error: bool = False) -> JSONRPCError:
        """转换为 A2A JSON-RPC error。
        
        Args:
            include_framework_error: 是否包含 framework_error 到 data 字段（debug 模式）
        """
        data = None
        if include_framework_error and self.framework_error:
            data = {"framework_error": self.framework_error}
        return JSONRPCError(
            code=int(self.code),
            message=self.message,
            data=data,
        )
    
    @property
    def is_retryable(self) -> bool:
        """错误是否可重试（业务侧可依据此属性决定）。"""
        return self.code in (
            AdapterErrorCode.TOOL_INVOCATION_FAILED,
            AdapterErrorCode.MEMORY_BACKEND_UNAVAILABLE,
            AdapterErrorCode.AGENT_CONTAINER_UNREACHABLE,
        )
```

### 6.2 7 错误码详解（与 v0.2 Design §9.1 表严格一致）

| 错误码 | 常量 | 含义 | Retryable | 默认重试策略 |
|--------|------|------|-----------|-------------|
| `-32001` | `FRAMEWORK_NOT_LOADED` | framework SDK 未成功加载（ImportError） | ❌ 永久 | — |
| `-32002` | `FRAMEWORK_VERSION_INCOMPATIBLE` | framework 版本与 adapter 不兼容 | ❌ 永久 | — |
| `-32003` | `CARD_CONVERSION_FAILED` | Agent Card 转换失败（必填字段缺失） | ❌ 永久（启动失败） | — |
| `-32004` | `TOOL_INVOCATION_FAILED` | framework tool 调用异常 | ✅ 可重试 | 3 次指数退避 + jitter (base=1s, max=8s) |
| `-32005` | `MEMORY_BACKEND_UNAVAILABLE` | framework memory backend 不可用 | ✅ 可降级 | 无限退避 (base=5s, max=300s) |
| `-32006` | `AGENT_CONTAINER_UNREACHABLE` | localhost:7080 Agent container 无响应（Sidecar 模式） | ✅ 可重试 | 5 次线性退避 (1s/次, max=5s) |
| `-32007` | `CONFIG_VALIDATION_FAILED` | 配置校验失败（如 model name 格式错误） | ❌ 永久 | — |

### 6.3 Tenacity 重试策略

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/retry.py
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
    wait_random,
)
from superteam_a2a.adapter.errors import AdapterError, AdapterErrorCode


def create_retry_policy(error_code: AdapterErrorCode) -> AsyncRetrying:
    """根据错误码返回对应的 Tenacity retry policy。
    
    Args:
        error_code: AdapterErrorCode
    
    Returns:
        AsyncRetrying: Tenacity 重试实例
    """
    if error_code == AdapterErrorCode.TOOL_INVOCATION_FAILED:
        return AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential_jitter(initial=1, max=8),
            retry=retry_if_exception_type(AdapterError),
            reraise=True,
        )
    elif error_code == AdapterErrorCode.MEMORY_BACKEND_UNAVAILABLE:
        return AsyncRetrying(
            stop=stop_after_attempt(-1),  # infinite
            wait=wait_exponential_jitter(initial=5, max=300),
            retry=retry_if_exception_type(AdapterError),
            reraise=True,
        )
    elif error_code == AdapterErrorCode.AGENT_CONTAINER_UNREACHABLE:
        return AsyncRetrying(
            stop=stop_after_attempt(5),
            wait=wait_random(0, 1),  # 线性退避（1s/次）
            retry=retry_if_exception_type(AdapterError),
            reraise=True,
        )
    else:
        # 默认不重试（永久错误）
        return AsyncRetrying(
            stop=stop_after_attempt(1),
            retry=retry_if_exception_type(AdapterError),
            reraise=True,
        )


async def with_retry(
    error_code: AdapterErrorCode,
    func: Callable[..., Awaitable[T]],
    *args,
    **kwargs,
) -> T:
    """使用对应策略执行 async 函数。"""
    policy = create_retry_policy(error_code)
    async for attempt in policy:
        with attempt:
            return await func(*args, **kwargs)
```

**jitter 计算公式**（Tenacity 内置）：
```
delay = min(initial * factor^attempt, max) + random(0, delay * 0.1)
```

### 6.4 错误传播 3 通道（与 v0.2 Design §9.4 严格一致）

- **Adapter → A2A Server（HTTP response）**：JSON-RPC `error.code` + `error.message` + `error.data.framework_error`（框架原生异常详情，仅 debug 模式返回）
- **Adapter → OTel Span**：标记 Span status（OK / ERROR）+ error.type + error.message
- **Adapter → Prometheus**：`supteam_adapter_errors_total{framework, error_code}` +1

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/errors.py
from opentelemetry import trace
from superteam_a2a.adapter.observability.metrics import ERRORS_TOTAL


async def propagate_error(
    error: AdapterError,
    framework: str,
    debug_mode: bool = False,
) -> JSONRPCError:
    """错误传播 3 通道统一处理。"""
    # 1. Prometheus 计数
    ERRORS_TOTAL.labels(
        framework=framework,
        error_code=error.code.value,
    ).inc()
    
    # 2. OTel Span 标记
    span = trace.get_current_span()
    if span:
        span.set_status(trace.Status(trace.StatusCode.ERROR))
        span.set_attribute("error.type", error.code.name)
        span.set_attribute("error.message", error.message)
        if error.framework_error:
            span.set_attribute("error.framework_type", error.framework_error.get("exception_type"))
    
    # 3. 返回 A2A JSON-RPC error
    return error.to_jsonrpc_error(include_framework_error=debug_mode)
```

---

## 7. 可观测性

### 7.1 Prometheus 指标（7 个 `supteam_adapter_*`）

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/observability/metrics.py
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry


# 默认 registry（单进程模式，ADR-0005 §10）
DEFAULT_REGISTRY = CollectorRegistry()


REQUESTS_TOTAL = Counter(
    "supteam_adapter_requests_total",
    "Adapter request count",
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
    "Card conversion duration in seconds",
    labelnames=("framework",),
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 5),
    registry=DEFAULT_REGISTRY,
)

FRAMEWORK_LOAD_DURATION_SECONDS = Histogram(
    "supteam_adapter_framework_load_duration_seconds",
    "Framework SDK load duration in seconds",
    labelnames=("framework",),
    buckets=(0.5, 1, 2, 5, 10, 30, 60),
    registry=DEFAULT_REGISTRY,
)

ERRORS_TOTAL = Counter(
    "supteam_adapter_errors_total",
    "Adapter error count",
    labelnames=("framework", "error_code"),
    registry=DEFAULT_REGISTRY,
)

ACTIVE_AGENTS = Gauge(
    "supteam_adapter_active_agents",
    "Currently active agents (derived from readiness probe)",
    labelnames=("framework",),
    registry=DEFAULT_REGISTRY,
)

GOLDEN_CASE_PASS_TOTAL = Counter(
    "supteam_adapter_golden_case_pass_total",
    "Golden Case pass count (CI report)",
    labelnames=("framework", "case_id"),
    registry=DEFAULT_REGISTRY,
)


def setup_metrics(registry: CollectorRegistry | None = None) -> CollectorRegistry:
    """注册指标到 registry。
    
    Args:
        registry: 自定义 registry（None = 默认单进程 registry）
    
    Returns:
        CollectorRegistry: 实际使用的 registry
    """
    if registry is None:
        return DEFAULT_REGISTRY
    # 重新注册所有指标到自定义 registry
    for metric in [REQUESTS_TOTAL, REQUEST_DURATION_SECONDS, ...]:
        # ... register logic
    return registry
```

### 7.2 OpenTelemetry Trace（4 层 Span 结构）

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/observability/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def create_tracer(
    name: str = "supteam_a2a.adapter",
    otlp_endpoint: str | None = None,
    sample_ratio: float = 0.1,
) -> trace.Tracer:
    """创建 Adapter tracer（显式 provider 注入，避免污染全局）。
    
    Args:
        name: tracer 名（默认 "supteam_a2a.adapter"）
        otlp_endpoint: OTLP collector endpoint
        sample_ratio: 采样率（0.1 = 10%）
    
    Returns:
        trace.Tracer: OTel tracer 实例
    """
    provider = TracerProvider(
        sampler=trace.sampling.TraceIdRatioBased(sample_ratio),
    )
    
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    
    trace.set_tracer_provider(provider)
    return trace.get_tracer(name)


def create_root_span(
    tracer: trace.Tracer,
    framework: str,
    method: str,
    agent_name: str,
) -> trace.Span:
    """创建 Root Span（adapter.{framework}.{method}）。"""
    return tracer.start_as_current_span(
        f"adapter.{framework}.{method}",
        attributes={
            "framework": framework,
            "framework.version": framework_version,
            "adapter.version": "0.2.0",
            "agent.name": agent_name,
        },
    )
```

**OTel 4 层 Span 结构**：
```
adapter.{framework}.{method}              ← Root Span
  ├─ framework.invoke                     ← Child（调用 framework SDK）
  ├─ card.convert                         ← Child（Card 重读时）
  └─ framework.translate                  ← Child（framework output → A2A 响应）
```

**Span Events**：tool.invoked / memory.read / memory.write / error.occurred

### 7.3 structlog JSON 日志

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/observability/logging.py
import logging
import structlog


# 敏感字段（永不进入日志）
_SENSITIVE_KEYS = frozenset({
    "api_key", "token", "password", "secret",
    "user_data", "memory_content", "knowledge_body",
    "cert", "private_key", "mtls_cert", "llm_api_key",
})


def _redact_sensitive(_, __, event_dict: dict) -> dict:
    """structlog processor：脱敏敏感字段。"""
    for key in list(event_dict.keys()):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = "***REDACTED***"
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    """配置 structlog JSON 输出。
    
    强制字段：framework / framework.version / adapter.version / method / task_id / agent.name / level / ts / msg
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
```

**强制字段映射**：
| 字段 | 来源 |
|------|------|
| `framework` | framework adapter 名称 |
| `framework.version` | framework SDK 版本（运行时检测） |
| `adapter.version` | adapter-sdk 版本 |
| `method` | A2A method 名（如 `sendMessage`） |
| `task_id` | 来自 A2A request context |
| `agent.name` | framework agent.name |
| `level`, `ts`, `msg` | structlog 内置 |

### 7.4 关键约束（与 v0.2 Design §10.4 + 宪法 §7 + ADR-0005 §10 一致）

- **Message / Memory / Knowledge content 永不进入普通日志**（仅 OTel Span attributes 允许 metadata）
- **高基数 label 禁令**：`trace_id` / `task_id` 不过 metric label
- **Python runtime 指标**（v0.2+ 新增，与 L2-1 §9.2 对齐）：
  - `supteam_python_event_loop_lag_seconds`（Histogram，threshold=50ms）
  - `supteam_python_thread_offload_queue_depth`（Gauge）
  - `supteam_python_active_asyncio_tasks`（Gauge）
  - `supteam_python_gc_collections_total`（Counter，按 generation 分）
- **单进程模式**（避免 prometheus-client multiprocess mode 复杂性；ADR-0005 §10）

---

## 8. 容器镜像打包（ADR-0005 §2.2 + §9.3）

### 8.1 策略 A：每 framework 独立 base 镜像（推荐）

**Dockerfile 多阶段模板**（以 LangChain 为例）：

```dockerfile
# adapters/langchain/Dockerfile
# syntax=docker/dockerfile:1.7

# ============ Stage 1: builder ============
FROM python:3.12-slim AS builder

# uv 安装（Astral 官方）
RUN pip install --no-cache-dir uv==0.5.0

WORKDIR /build

# 复制 workspace 配置
COPY pyproject.toml uv.lock ./
COPY packages/adapter-sdk/pyproject.toml ./packages/adapter-sdk/
COPY packages/adapter-sdk/src ./packages/adapter-sdk/src
COPY adapters/langchain/pyproject.toml ./adapters/langchain/
COPY adapters/langchain/src ./adapters/langchain/src

# uv sync（仅 framework 适配所需依赖）
RUN uv sync --frozen --no-dev \
    --package superteam-a2a-adapter-langchain \
    --python python3.12

# 构建 wheel
RUN uv build --package superteam-a2a-adapter-langchain --out-dir /wheels

# ============ Stage 2: runtime ============
FROM python:3.12-slim AS runtime

# 安全：非 root user
RUN groupadd --gid 1000 adapter && \
    useradd --uid 1000 --gid adapter --shell /bin/bash --create-home adapter

# 复制 builder 产物
COPY --from=builder /wheels /wheels
COPY --from=builder /build/.venv /app/.venv

# 安装 framework adapter wheel
RUN pip install --no-cache-dir --no-index --find-links=/wheels \
        superteam-a2a-adapter-langchain && \
    rm -rf /wheels

WORKDIR /app

# 安全：read-only rootfs 兼容
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ADAPTER_FRAMEWORK=langchain

USER adapter

EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# 启动命令
ENTRYPOINT ["uvicorn", "supteam_a2a.adapters.langchain.app:create_app", \
            "--host", "0.0.0.0", "--port", "8080", \
            "--workers", "1", \
            "--loop", "uvloop", \
            "--http", "httptools", \
            "--lifespan", "on"]
```

### 8.2 镜像层结构

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
- 镜像大小可控（每 framework 仅含必要依赖，~200-400 MB）
- 升级独立（LangChain 升 0.2 不影响 AutoGen 部署）
- 故障隔离（框架依赖问题不影响其他 framework）
- CI 缓存友好（Layer 3 `adapter-sdk` 共享，registry pull 更快）

### 8.3 镜像构建流程（CI）

```yaml
# .github/workflows/adapter-build.yaml（节选）
name: Build Adapter Images

on:
  push:
    paths:
      - 'adapters/langchain/**'
      - 'packages/adapter-sdk/**'
      - 'pyproject.toml'
      - 'uv.lock'

jobs:
  build:
    runs-on: ubuntu-22.04
    permissions:
      contents: read
      id-token: write  # cosign keyless OIDC
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Extract framework version
        id: version
        run: |
          FRAMEWORK_VERSION=$(grep '^version' adapters/langchain/pyproject.toml | head -1 | cut -d'"' -f2)
          ADAPTER_VERSION=$(grep '^version' packages/adapter-sdk/pyproject.toml | head -1 | cut -d'"' -f2)
          echo "framework_version=${FRAMEWORK_VERSION}" >> $GITHUB_OUTPUT
          echo "adapter_version=${ADAPTER_VERSION}" >> $GITHUB_OUTPUT
      
      - name: Build image
        run: |
          docker build \
            --tag ghcr.io/superteam-a2a/adapter-langchain:${{ steps.version.outputs.adapter_version }}-${{ steps.version.outputs.framework_version }}-py3.12 \
            --file adapters/langchain/Dockerfile \
            .
      
      - name: Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ghcr.io/superteam-a2a/adapter-langchain:${{ steps.version.outputs.adapter_version }}-${{ steps.version.outputs.framework_version }}-py3.12
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
      
      - name: Cosign keyless sign
        uses: sigstore/cosign-installer@main
        with:
          cosign-release: 'v2.2.4'
      
      - run: |
          cosign sign --yes ghcr.io/superteam-a2a/adapter-langchain@${{ github.sha }}
      
      - name: Generate SLSA provenance
        uses: slsa-framework/slsa-github-generator@v1.9.0
        with:
          image: ghcr.io/superteam-a2a/adapter-langchain:${{ steps.version.outputs.adapter_version }}-${{ steps.version.outputs.framework_version }}-py3.12
```

### 8.4 镜像签名 + 验证

| 工具 | 用途 | 集成方式 |
|------|------|----------|
| **cosign** | 镜像签名 + 验证 | GitHub Actions OIDC + cosign keyless |
| **SLSA L3** | Provenance 生成 | slsa-framework/slsa-github-generator |
| **Trivy** | 漏洞扫描 | CI 强制（CRITICAL+HIGH 失败即终止） |
| **pip-audit** | Python 依赖漏洞扫描 | CI pre-build 步骤 |
| **Bandit** | Python 代码安全扫描 | CI pre-build 步骤 |
| **cosign verify** | 部署时验证 | K8s admission policy（cosign-policy-controller） |

### 8.5 镜像 tag 策略

格式：`{framework}:{adapter-version}-{framework-version}-py{python-version}`

示例：
- `adapter-langchain:v0.2.0-0.1.5-py3.12`
- `adapter-autogen:v0.2.0-0.2.3-py3.12`
- `adapter-crewai:v0.5.0-0.65.0-py3.12`

**版本策略**：
- v0.2 / v0.5 阶段只锁主版本（`>=0.x,<0.(x+1)`）
- v1.0 阶段可考虑更紧的范围（如 `<0.x.5`）以避免次版本升级引入破坏性变更

### 8.6 镜像安全约束（ADR-0005 §9.3 运行时）

```yaml
# Helm values：Pod Security Standard restricted
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
```

---

## 9. 部署形态（同进程 plugin / Sidecar）

### 9.1 Sidecar 模式（v0.1 推荐；v0.5+ 通用）

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

**Pod spec**（Helm 模板生成）：

```yaml
# 引用 L2-2 Operator Core v0.2.0 Spec §3.2.4 Owned resources 中 Adapter container 部分
spec:
  containers:
  - name: adapter                    # ← 本模块
    image: ghcr.io/superteam-a2a/adapter-langchain:v0.2.0-0.1.5-py3.12
    ports:
    - containerPort: 8080            # A2A Server
    env:
    - name: ADAPTER_FRAMEWORK
      value: langchain
    - name: AGENT_SERVICE_HOST        # Agent container DNS（sidecar 模式 = localhost）
      value: localhost
    - name: AGENT_SERVICE_PORT
      value: "7080"
    - name: ADAPTER_EMBEDDED
      value: "false"
  - name: agent                      # 框架容器
    image: my-agent:latest
    ports:
    - containerPort: 7080            # framework server
```

### 9.2 同进程 plugin 模式（v0.2 Python-native 优先）

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
- Framework SDK 错误可能 kill 整个进程（需 framework-specific exception handler + `asyncio.shield` 包装，O-1 待 L3-3 实测）
- GIL 竞争（虽然 Python Agent SDK 主要 I/O 密集）
- 框架依赖污染 Adapter 镜像（每 framework 独立镜像，仍可接受）

**Pod spec**（Helm 模板生成）：

```yaml
spec:
  containers:
  - name: agent-with-adapter        # 单 Python 进程
    image: ghcr.io/superteam-a2a/adapter-langchain:v0.2.0-0.1.5-py3.12
    ports:
    - containerPort: 8080            # A2A Server
    command: ["uvicorn", "supteam_a2a.adapters.langchain.app:create_app"]
    env:
    - name: ADAPTER_FRAMEWORK
      value: langchain
    - name: ADAPTER_EMBEDDED
      value: "true"
```

### 9.3 部署模式决策（Operator Core 依据 Agent CRD `spec.adapter.embedded` 字段）

| `embedded` | 部署模式 | 适用 framework | CRD 校验 |
|------------|----------|----------------|----------|
| `true` | 同进程 plugin | LangChain / AutoGen / Semantic Kernel Python | admission webhook：仅允许 Python-native |
| `false`（默认） | Sidecar | CrewAI / Strands / Smolagents / 非 Python | 默认 |

### 9.4 Init Container 模式（不推荐）

Adapter 作为 init container，仅启动时配置注入。**不推荐**因为：
- 无法处理运行时 A2A 请求（init container 启动后即退出）
- 不符合 L1 v0.2.0 Architecture §6.4 Adapter 拓扑设计

### 9.5 资源限制（与 L1 v0.2.0 Architecture §11.1 对齐）

| 模式 | CPU limit | Memory limit | 说明 |
|------|-----------|--------------|------|
| Sidecar Adapter | 500m | 256Mi | 轻量协议翻译 |
| 同进程 plugin | 1 | 1Gi | 包含 framework SDK |
| Agent container | 1 | 2Gi | LLM 调用 + 业务逻辑 |

---

## 10. 生命周期契约（与 Operator Core 集成）

> Adapter 无独立 Controller（无 reconcile 逻辑）。本节定义 Adapter container 与 Operator Core 的**交互契约**（5 时序图）。

### 10.1 启动序列（Operator 创建 Pod → Adapter container start · 11 步）

```
时间 ──────────────────────────────────────────────────────────────►

Operator Core                          K8s API              Adapter Container
─────────────                          ───────              ────────────────
1. Watch Agent CRD
2. Reconcile Agent
3. 构造 Pod spec
   (含 Adapter container)
4. kubectl apply Pod ────────────────► Pod Created
5. K8s 调度 + 启动 containers
                                       Containers Start
                                                             6. main() 启动（uvicorn）
                                                             7. load AdapterConfig（4 层优先级）
                                                                - 失败 → AdapterError(-32007) + Exit 1
                                                             8. init AdapterProtocol（framework SDK 加载）
                                                                - 失败 → AdapterError(-32001) + Exit 1
                                                             9. Lifecycle.Start
                                                                - 启动 transport (httpx)
                                                                - 注册 A2A Server (create_app)
                                                                - 注册 /healthz + /readyz
                                                                - 启动 framework event listener
                                                                - 启动 Prometheus /metrics
                                                             10. Card 转换（启动期一次性）
                                                                - 失败 → AdapterError(-32003) + Exit 1
                                                             11. 标记 Ready
                                          ◄──── readiness probe 通过 ────
12. Watch Agent.Status.Ready = true
```

### 10.2 Lifecycle 实现契约

```python
# packages/adapter-sdk/src/supteam_a2a/adapter/lifecycle.py
import anyio
from superteam_a2a.adapter.protocol import Adapter
from superteam_a2a.adapter.config import AdapterConfig, validate_adapter_config
from superteam_a2a.adapter.errors import AdapterError, AdapterErrorCode


class Lifecycle:
    """Adapter 生命周期 hook（Operator Core 集成）。"""
    
    def __init__(
        self,
        adapter: Adapter,
        config: AdapterConfig,
        logger: structlog.stdlib.BoundLogger,
    ):
        self._adapter = adapter
        self._config = config
        self._logger = logger
        self._ready = False
    
    async def start(self) -> None:
        """启动序列（对应 §10.1 时序图步骤 7-11）。"""
        # Step 7: 配置校验
        try:
            validate_adapter_config(self._config)
        except AdapterError as e:
            self._logger.error("config_validation_failed", error=str(e))
            raise
        
        # Step 8: framework SDK 加载（framework adapter 子包内）
        try:
            await self._adapter.startup()  # framework-specific
        except Exception as e:
            raise AdapterError(
                code=AdapterErrorCode.FRAMEWORK_NOT_LOADED,
                message=f"Framework SDK load failed: {e!s}",
                framework_error={"exception_type": type(e).__name__},
            )
        
        # Step 10: Card 转换（启动期一次性，cached）
        try:
            card = self._adapter.agent_card()
            self._logger.info(
                "card_built",
                framework=self._config.framework,
                skills_count=len(card.skills),
                streaming=card.streaming,
            )
        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(
                code=AdapterErrorCode.CARD_CONVERSION_FAILED,
                message=f"Card conversion failed: {e!s}",
                framework_error={"exception_type": type(e).__name__},
            )
        
        # Step 11: 标记 Ready
        self._ready = True
        self._logger.info(
            "adapter_ready",
            framework=self._config.framework,
            embedded=self._config.embedded,
            port=self._config.port,
        )
    
    async def reload(self, new_config: AdapterConfig) -> None:
        """Reload 序列（ConfigMap 变化时）。"""
        try:
            validate_adapter_config(new_config)
        except AdapterError as e:
            self._logger.error("config_validation_failed_reload", error=str(e))
            raise  # 不更新 self._config（保持旧 config）
        
        old_config = self._config
        self._config = new_config
        
        try:
            # framework SDK 重新加载（仅 reload-able 字段）
            await self._adapter.reload(new_config)
            self._logger.info("config_reloaded", framework=new_config.framework)
        except Exception as e:
            self._config = old_config  # 回滚
            raise AdapterError(
                code=AdapterErrorCode.CONFIG_VALIDATION_FAILED,
                message=f"Reload failed, rolled back: {e!s}",
            )
    
    async def stop(self) -> None:
        """优雅停机序列（对应 §10.4 时序图）。"""
        # Step 1: 标记不再接受新请求（readiness probe 失败）
        self._ready = False
        
        # Step 2: 等待 in-flight 请求完成（最多 shutdown_grace_period_seconds）
        await anyio.sleep(self._config.shutdown_grace_period_seconds)
        
        # Step 3: 优雅关闭 framework SDK
        await self._adapter.shutdown()
        
        # Step 4: 关闭 transport
        # (framework adapter 子包实现)
        
        self._logger.info("adapter_stopped", framework=self._config.framework)
    
    @property
    def is_ready(self) -> bool:
        """健康检查端点 /readyz 调用。"""
        return self._ready
```

### 10.3 Card 转换时序（启动期一次性 · 5 步）

```
1. Lifecycle.Start
2. adapter.startup（framework SDK 加载）
3. adapter.agent_card(ctx)
   ├─ cardConverter.convert(framework_agent)
   │  ├─ 反射调用 framework agent 的 5 个关键方法
   │  ├─ 必填字段缺失 → AdapterError{code: -32003}（Fatal）
   │  └─ 可选字段缺失 → 使用默认值 + log warning
   └─ 缓存到 self._card（避免每次请求重新推导）
4. 注册 A2A Server handler（携带 AgentCard）
5. A2A Server 暴露 /.well-known/agent.json
```

### 10.4 Reload 序列（ConfigMap 变化 · 5 步）

```
ConfigMap changed
       │
       ▼
Adapter 收到 watch event (K8s API)
       │
       ▼
Lifecycle.reload(new_config)
   ├─ validate new_config（§5.5）
   │  └─ 校验失败 → AdapterError{code: -32007} + 回滚到旧 config + log error
   ├─ adapter.reload(new_config)
   │  └─ framework SDK 重新加载（如 LangChain temperature 变化）
   ├─ 更新 OTel resource attributes（adapter.config_version）
   └─ Prometheus config reload event counter +1
```

### 10.5 优雅停机（SIGTERM · 6 步）

```
K8s 发送 SIGTERM (preStop hook 前 30s)
       │
       ▼
Adapter 收到 SIGTERM
       │
       ▼
Lifecycle.stop()
   ├─ Step 1: 标记不再接受新 A2A 请求（readiness=false → 503 Service Unavailable）
   ├─ Step 2: 等待 in-flight 请求完成（最多 shutdown_grace_period_seconds = 30s）
   ├─ Step 3: adapter.shutdown（framework SDK 优雅关闭）
   ├─ Step 4: 关闭 transport (httpx.AsyncClient)
   ├─ Step 5: flush OTel BatchSpanProcessor
   └─ Step 6: 退出（exit 0）
```

### 10.6 错误恢复（Adapter 崩溃 → K8s restart · 5 步）

```
Adapter container crash
       │
       ▼
K8s kubelet 重启 container (exponentialBackoff: 10s/30s/1m/2m/5m)
       │
       ▼
Adapter 重启 → 执行 §10.1 启动序列
```

**Adapter 崩溃时的 Operator 行为**：
- Adapter container crash → Pod restart（K8s Deployment 默认）
- Pod restart 多次失败 → K8s CrashLoopBackOff
- Operator 监测 Agent.Status.Ready = false → 触发 reconcile
- Operator 更新 Agent.Status.Conditions 中 `AdapterReady=False` + reason

---

## 11. Helm values（完整 schema · 6 framework 独立 image override）

### 11.1 全局 + Adapter 默认配置

```yaml
# helm/values.yaml（完整 schema）

global:
  imageRegistry: ghcr.io/superteam-a2a
  imagePullPolicy: IfNotPresent
  logLevel: INFO  # DEBUG / INFO / WARNING / ERROR

adapter:
  image:
    repository: ghcr.io/superteam-a2a/adapter
    tag: v0.2.0
    pullPolicy: IfNotPresent

  # A2A Server
  port: 8080
  host: 0.0.0.0

  # Agent container 通信（sidecar 模式）
  agentServiceHost: localhost
  agentServicePort: 7080

  # 部署模式（v0.2+）
  embedded: false

  # 健康检查
  healthCheckPath: /healthz
  readinessPath: /readyz

  # 资源限制（sidecar 模式典型值）
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 256Mi

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

  # ConfigMap 引用（默认 adapter 配置）
  configMapRef: superteam-a2a-adapter-config

  # mTLS cert 引用（Secret 名）
  mtlsSecretRef: superteam-a2a-adapter-mtls

  # 优雅停机
  shutdownGracePeriodSeconds: 30
```

### 11.2 6 Framework 镜像覆盖

```yaml
frameworks:
  langchain:
    image:
      repository: ghcr.io/superteam-a2a/adapter-langchain
      tag: v0.2.0-0.1.5-py3.12
    resources:
      requests: { cpu: 200m, memory: 256Mi }
      limits: { cpu: 1, memory: 512Mi }

  autogen:
    image:
      repository: ghcr.io/superteam-a2a/adapter-autogen
      tag: v0.2.0-0.2.3-py3.12
    resources:
      requests: { cpu: 200m, memory: 256Mi }
      limits: { cpu: 1, memory: 512Mi }

  crewai:
    image:
      repository: ghcr.io/superteam-a2a/adapter-crewai
      tag: v0.5.0-0.65.0-py3.12
    resources:
      requests: { cpu: 300m, memory: 384Mi }
      limits: { cpu: 2, memory: 1Gi }  # crewai 独占最高

  semantic_kernel:
    image:
      repository: ghcr.io/superteam-a2a/adapter-semantic-kernel
      tag: v0.5.0-1.15.0-py3.12
    resources:
      requests: { cpu: 200m, memory: 256Mi }
      limits: { cpu: 1, memory: 512Mi }

  strands:
    image:
      repository: ghcr.io/superteam-a2a/adapter-strands
      tag: v1.0.0-1.0.0-py3.12
    resources:
      requests: { cpu: 200m, memory: 256Mi }
      limits: { cpu: 1, memory: 512Mi }

  smolagents:
    image:
      repository: ghcr.io/superteam-a2a/adapter-smolagents
      tag: v1.0.0-1.5.0-py3.12
    resources:
      requests: { cpu: 200m, memory: 256Mi }
      limits: { cpu: 1, memory: 512Mi }
```

### 11.3 可观测性 + RBAC + NetworkPolicy

```yaml
# 可观测性
observability:
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
      interval: 30s
      labels:
        release: prometheus

  tracing:
    enabled: true
    otlpEndpoint: http://otel-collector:4317
    sampleRate: 0.1

  logging:
    format: json  # json / text
    level: INFO

# RBAC
rbac:
  create: true
  serviceAccount:
    create: true
    name: superteam-a2a-adapter
  # ClusterRole / ClusterRoleBinding 见 templates/

# NetworkPolicy
networkPolicy:
  enabled: true
  ingress:
    # 允许 Operator Core 调用 A2A Server
    - from:
        - namespaceSelector:
            matchLabels:
              name: superteam-a2a
      ports:
        - protocol: TCP
          port: 8080
  egress:
    # 允许 OTel exporter
    - to:
        - namespaceSelector:
            matchLabels:
              name: observability
      ports:
        - protocol: TCP
          port: 4317
    # 允许 LLM provider API（如 OpenAI / Anthropic）
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 443
```

### 11.4 env 映射表

| Helm value | 环境变量 | 用途 |
|-----------|----------|------|
| `adapter.port` | `ADAPTER_PORT` | A2A Server 监听端口 |
| `adapter.host` | `ADAPTER_HOST` | A2A Server 绑定 host |
| `adapter.agentServiceHost` | `AGENT_SERVICE_HOST` | Agent container host（sidecar 模式） |
| `adapter.agentServicePort` | `AGENT_SERVICE_PORT` | Agent container port（sidecar 模式） |
| `adapter.embedded` | `ADAPTER_EMBEDDED` | 同进程 plugin 开关（v0.2+） |
| `adapter.configMapRef` | `ADAPTER_CONFIGMAP_NAME` | 配置 ConfigMap 名 |
| `adapter.mtlsSecretRef` | `ADAPTER_MTLS_SECRET` | mTLS cert Secret 名 |
| `frameworks.{fw}.image.repository` | `ADAPTER_IMAGE_{FW}` | framework adapter 镜像 |
| `frameworks.{fw}.image.tag` | `ADAPTER_TAG_{FW}` | framework adapter 镜像 tag |
| `observability.tracing.otlpEndpoint` | `OTEL_EXPORTER_OTLP_ENDPOINT` | OTel collector 地址 |
| `observability.metrics.serviceMonitor.enabled` | —（通过 ServiceMonitor CR 启用） | Prometheus scrape |
| `global.logLevel` | `ADAPTER_LOG_LEVEL` | 日志级别 |
| `adapter.framework` | `ADAPTER_FRAMEWORK` | framework 名称（运行时检测） |

### 11.5 Helm 模板示例（adapter-deployment.yaml）

```yaml
# helm/templates/adapter-deployment.yaml
{{- range $fw, $cfg := .Values.frameworks }}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: superteam-a2a-adapter-{{ $fw }}
  labels:
    app.kubernetes.io/name: superteam-a2a-adapter
    app.kubernetes.io/instance: {{ $fw }}
    app.kubernetes.io/managed-by: Helm
  annotations:
    # 触发 ConfigMap 变化时滚动重启
    checksum/config: {{ include (print $.Template.BasePath "/adapter-configmap.yaml") . | sha256sum }}
spec:
  replicas: 1  # Adapter 是 per-Agent 的，由 AgentSet Controller 扩缩
  selector:
    matchLabels:
      app.kubernetes.io/name: superteam-a2a-adapter
      app.kubernetes.io/instance: {{ $fw }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: superteam-a2a-adapter
        app.kubernetes.io/instance: {{ $fw }}
        app.kubernetes.io/version: {{ $cfg.image.tag }}
    spec:
      serviceAccountName: {{ include "adapter.serviceAccountName" $ }}
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: adapter
        image: "{{ $cfg.image.repository }}:{{ $cfg.image.tag }}"
        imagePullPolicy: {{ $.Values.global.imagePullPolicy }}
        ports:
        - name: a2a
          containerPort: {{ $.Values.adapter.port }}
          protocol: TCP
        env:
        - name: ADAPTER_FRAMEWORK
          value: {{ $fw }}
        - name: ADAPTER_PORT
          value: {{ $.Values.adapter.port | quote }}
        - name: ADAPTER_EMBEDDED
          value: {{ $.Values.adapter.embedded | quote }}
        - name: AGENT_SERVICE_HOST
          value: {{ $.Values.adapter.agentServiceHost | quote }}
        - name: AGENT_SERVICE_PORT
          value: {{ $.Values.adapter.agentServicePort | quote }}
        - name: ADAPTER_LOG_LEVEL
          value: {{ $.Values.global.logLevel | quote }}
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: {{ $.Values.observability.tracing.otlpEndpoint | quote }}
        envFrom:
        - secretRef:
            name: {{ $.Values.adapter.mtlsSecretRef }}
        - configMapRef:
            name: {{ $.Values.adapter.configMapRef }}
        resources:
          requests: {{- toYaml $cfg.resources.requests | nindent 10 }}
          limits:   {{- toYaml $cfg.resources.limits | nindent 10 }}
        securityContext: {{- toYaml $.Values.adapter.securityContext | nindent 8 }}
        livenessProbe:
          httpGet:
            path: {{ $.Values.adapter.healthCheckPath }}
            port: a2a
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: {{ $.Values.adapter.readinessPath }}
            port: a2a
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
{{- end }}
```

### 11.6 RBAC（ClusterRole）

```yaml
# helm/templates/adapter-clusterrole.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: superteam-a2a-adapter
rules:
  # ConfigMap watch（reload trigger）
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch"]
  # Agent CRD 状态更新（可选；通常由 Operator 写入）
  - apiGroups: ["superteam-a2a.io"]
    resources: ["agents", "agents/status"]
    verbs: ["get", "list", "watch", "update", "patch"]
  # 自定义 framework config ConfigMap
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["supteam-a2a-adapter-config", "supteam-a2a-adapter-{framework}-config"]
    verbs: ["get", "list", "watch"]
  # Secret（仅 mTLS）
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["supteam-a2a-adapter-mtls"]
    verbs: ["get"]
```

---

## 12. 测试策略 + ID 矩阵（6 层级）

### 12.1 覆盖率目标

| 范围 | 覆盖率目标 | 测试类型 |
|------|-----------|----------|
| `adapter-sdk`（protocol / card / config / errors / observability / retry / lifecycle / server / transport / boundary） | ≥ 95% | 表驱动 + `mock` + `pytest-asyncio` + `hypothesis` |
| `langchain`, `autogen`, `crewai`, `semantic_kernel`, `strands`, `smolagents` | ≥ 80% | 表驱动 + 真实 framework SDK（小型 model） |

**测试工具**：pytest + pytest-asyncio + pytest-cov + respx + hypothesis

### 12.2 单元测试（adapter-sdk · 48 ID）

| 测试 ID | 范围 | 描述 | 优先级 |
|---------|------|------|--------|
| UT-PROT-ADAPTER-001 | `protocol.py` | Adapter Protocol 实例化（runtime_checkable isinstance） | P0 |
| UT-PROT-ADAPTER-002 | `protocol.py` | Adapter.on_message async 方法契约 | P0 |
| UT-PROT-ADAPTER-003 | `protocol.py` | Adapter.health_check 返回 bool | P0 |
| UT-PROT-CARD-001 | `card.py` | AgentCardConverter.convert happy path | P0 |
| UT-PROT-CARD-002 | `card.py` | 必填字段 name 缺失 → AdapterError(-32003) | P0 |
| UT-PROT-CARD-003 | `card.py` | 必填字段 description 缺失 → AdapterError(-32003) | P0 |
| UT-PROT-CARD-004 | `card.py` | 可选字段缺失使用默认值 + log warning | P0 |
| UT-PROT-CARD-005 | `card.py` | JSON Schema 推导失败降级 inputModes=["text/plain"] | P0 |
| UT-PROT-CARD-006 | `card.py` | MemoryCapabilities Pydantic 严格校验 | P0 |
| UT-PROT-CONFIG-001 | `config.py` | AdapterConfig 4 层优先级加载（Secret > CRD > ConfigMap > Env） | P0 |
| UT-PROT-CONFIG-002 | `config.py` | framework 枚举校验（非法值拒绝） | P0 |
| UT-PROT-CONFIG-003 | `config.py` | embedded=true + 非 Python framework 拒绝 | P0 |
| UT-PROT-CONFIG-004 | `config.py` | Pydantic Settings extra="forbid" 拒绝未知字段 | P0 |
| UT-PROT-CONFIG-005 | `config.py` | llm_api_key 字段拒绝（Constitution §3.5.3） | P0 |
| UT-PROT-ERROR-001 | `errors.py` | 7 错误码常量值（-32001 ~ -32007） | P0 |
| UT-PROT-ERROR-002 | `errors.py` | AdapterError.to_jsonrpc_error 含/不含 framework_error | P0 |
| UT-PROT-ERROR-003 | `errors.py` | is_retryable 属性（4 类可重试 + 3 类不可） | P0 |
| UT-PROT-ERROR-004 | `errors.py` | propagate_error 3 通道统一处理 | P0 |
| UT-PROT-RETRY-001 | `retry.py` | TOOL_INVOCATION_FAILED 重试 3 次 + 指数退避 | P0 |
| UT-PROT-RETRY-002 | `retry.py` | MEMORY_BACKEND_UNAVAILABLE 无限退避 | P0 |
| UT-PROT-RETRY-003 | `retry.py` | AGENT_CONTAINER_UNREACHABLE 5 次线性退避 | P0 |
| UT-PROT-RETRY-004 | `retry.py` | 永久错误（FRAMEWORK_NOT_LOADED）不重试 | P0 |
| UT-PROT-RETRY-005 | `retry.py` | jitter 计算公式正确性 | P1 |
| UT-PROT-RETRY-006 | `retry.py` | with_retry 包装函数 | P0 |
| UT-PROT-METRICS-001 | `metrics.py` | 7 个 Counter/Histogram/Gauge 注册 | P0 |
| UT-PROT-METRICS-002 | `metrics.py` | label 基数约束（不接受 trace_id） | P0 |
| UT-PROT-METRICS-003 | `metrics.py` | 单进程模式（multiprocess mode 拒绝） | P1 |
| UT-PROT-TRACING-001 | `tracing.py` | create_tracer 显式 provider 注入 | P0 |
| UT-PROT-TRACING-002 | `tracing.py` | Root Span attributes（framework / method / agent.name） | P0 |
| UT-PROT-TRACING-003 | `tracing.py` | Child Span 嵌套（framework.invoke / card.convert / framework.translate） | P1 |
| UT-PROT-LOGGING-001 | `logging.py` | structlog JSON 输出格式 | P0 |
| UT-PROT-LOGGING-002 | `logging.py` | 9 项敏感字段脱敏（api_key / token / password / secret / user_data / memory_content / knowledge_body / cert / private_key） | P0 |
| UT-PROT-LOGGING-003 | `logging.py` | 7 强制字段（framework / framework.version / adapter.version / method / task_id / agent.name / level） | P0 |
| UT-PROT-LOGGING-004 | `logging.py` | 3 可选字段（error.code / error.message / duration_ms） | P1 |
| UT-PROT-SERVER-001 | `server.py` | create_adapter_app 嵌入 create_app | P0 |
| UT-PROT-SERVER-002 | `server.py` | middleware 链顺序（Tracing → Auth → RateLimit → Metrics） | P0 |
| UT-PROT-SERVER-003 | `server.py` | /healthz + /readyz + /metrics + /.well-known/agent.json 注册 | P0 |
| UT-PROT-SERVER-004 | `server.py` | A2A method handler 注册（sendMessage / getTask 等） | P0 |
| UT-PROT-TRANSPORT-001 | `transport.py` | httpx.AsyncClient 工厂（Sidecar 模式） | P0 |
| UT-PROT-TRANSPORT-002 | `transport.py` | 连接池参数（max_connections=100 / max_keepalive=20） | P0 |
| UT-PROT-TRANSPORT-003 | `transport.py` | timeout 参数（connect=5s / read=30s / write=30s / pool=5s） | P0 |
| UT-PROT-TRANSPORT-004 | `transport.py` | mTLS ssl_context 注入 | P0 |
| UT-PROT-TRANSPORT-005 | `transport.py` | 进程级单例（lifespan 生命周期） | P1 |
| UT-PROT-LIFECYCLE-001 | `lifecycle.py` | Lifecycle.start 11 步启动序列 | P0 |
| UT-PROT-LIFECYCLE-002 | `lifecycle.py` | Lifecycle.reload ConfigMap 变化处理 | P0 |
| UT-PROT-LIFECYCLE-003 | `lifecycle.py` | Lifecycle.stop 优雅停机（30s grace period） | P0 |
| UT-PROT-LIFECYCLE-004 | `lifecycle.py` | Lifecycle.is_ready 属性（readiness probe） | P0 |
| UT-PROT-LIFECYCLE-005 | `lifecycle.py` | 启动失败 → AdapterError + Exit 1 | P0 |
| UT-PROT-BOUNDARY-001 | `_internal/` | 业务层禁 import（ruff ST-ADAPTER-BOUNDARY 检测） | P0 |
| UT-PROT-BOUNDARY-002 | `_internal/` | framework SDK import 仅在 framework adapter 子包 | P0 |
| UT-PROT-BOUNDARY-003 | `_internal/` | Operator Core 禁 import adapter-sdk | P0 |

**目标覆盖率**：adapter-sdk ≥ 95%（48 个 ID 覆盖全部 11 文件）

### 12.3 集成测试（每 framework · 36 ID）

| 测试 ID | 范围 | 描述 | 优先级 |
|---------|------|------|--------|
| IT-LC-001 ~ 006 | LangChain | happy path / tool / Card / error / memory（同进程 plugin）/ embedded 切换 | P0 |
| IT-AG-001 ~ 006 | AutoGen | happy path / tool / GroupChat / Card / error / embedded 切换 | P0 |
| IT-CR-001 ~ 006 | CrewAI | happy path / Sequential / Parallel / Card / error / Sidecar 切换 | P1 |
| IT-SK-001 ~ 006 | Semantic Kernel | happy path / plugin / Card / error / Python vs .NET 双实现 / embedded 切换 | P1 |
| IT-ST-001 ~ 006 | Strands | happy path / tool / Card / error / Sidecar 切换 | P1 |
| IT-SM-001 ~ 006 | Smolagents | CodeAgent / ToolCallingAgent / Card / interpreter / error / Sidecar 切换 | P1 |

**总计**：v0.2 = 12 IT（LangChain 6 + AutoGen 6）；v1.0 = 36 IT

### 12.4 Golden Adapter 测试（宪法 §4.7 强制 · 60 ID）

| 版本 | Framework | 测试 ID | Fixture | 描述 |
|------|-----------|---------|---------|------|
| v0.5 | LangChain | GLC-01 ~ GLC-05 | `case-{01-05}-{name}.yaml` | 基础 LCEL / tool call / error path / memory / streaming 模拟 |
| v0.5 | AutoGen | GAG-01 ~ GAG-05 | 同上 | ConversableAgent / function_map / GroupChat / error / memory |
| v1.0 | CrewAI | GCR-01 ~ GCR-10 | 10 cases | Crew + Tasks + DAG（3 种拓扑） |
| v1.0 | Semantic Kernel | GSK-01 ~ GSK-10 | 10 cases | Kernel + Plugins + Python/.NET |
| v1.0 | Strands | GST-01 ~ GST-10 | 10 cases | Strands + tools |
| v1.0 | Smolagents | GSM-01 ~ GSM-10 | 10 cases | CodeAgent + ToolCallingAgent + interpreter |

**总计**：v0.5 = 10 Golden Cases；v1.0 = 60 Golden Cases

### 12.5 Conformance 测试（CF · 5 ID）

| 测试 ID | 描述 | 优先级 |
|---------|------|--------|
| CF-A2A-001 | 与 `google-a2a/conformance` 套件 100% 兼容 | P0 |
| CF-A2A-002 | Agent Card schema 校验（每个 framework 的 Card 符合 L2-1 AgentCard） | P0 |
| CF-A2A-003 | JSON-RPC 2.0 wire protocol 兼容 | P0 |
| CF-A2A-004 | error code 范围 -32001 ~ -32007 与 L2-1 §7 一致 | P0 |
| CF-A2A-005 | agent_card path `/.well-known/agent.json` | P0 |

### 12.6 E2E 测试（kind · 6 ID）

| 测试 ID | 描述 | 优先级 |
|---------|------|--------|
| E2E-LC-001 | kind + adapter-langchain + hello-world demo | P0 |
| E2E-AG-001 | kind + adapter-autogen + hello-world demo | P0 |
| E2E-CR-001 | kind + adapter-crewai + sdlc workflow | P1 |
| E2E-SK-001 | kind + adapter-semantic-kernel + sdlc workflow | P1 |
| E2E-ST-001 | kind + adapter-strands + sdlc workflow | P1 |
| E2E-SM-001 | kind + adapter-smolagents + sdlc workflow | P1 |

### 12.7 Property / Fuzz 测试（Hypothesis · 4 ID）

| 测试 ID | 描述 | 优先级 |
|---------|------|--------|
| PROP-ENV-001 | A2A envelope schema round-trip + 异常字段拒绝 | P0 |
| PROP-FSM-001 | Task 状态机 invariant（任何状态转换合法） | P0 |
| PROP-CARD-001 | framework introspection 输入 fuzz → Card 转换不应崩溃 | P0 |
| PROP-RETRY-001 | 任意错误码序列 → 重试次数与延迟在预期范围内 | P1 |

### 12.8 测试 ID 总计

| 层级 | v0.2 | v1.0 |
|------|------|------|
| UT | 48 | 48 |
| IT | 12 | 36 |
| Golden | 10 | 60 |
| Conformance | 5 | 5 |
| E2E | 2 | 6 |
| Property | 4 | 4 |
| **合计** | **81** | **159** |

---

## 13. 工具链与部署

### 13.1 依赖管理（uv workspace）

```bash
# 安装所有 workspace 依赖
uv sync --frozen

# 安装单个 framework adapter 子包（开发时）
uv sync --frozen --package superteam-a2a-adapter-langchain

# 添加新依赖（framework adapter 子包）
uv add --package superteam-a2a-adapter-langchain langchain-openai

# 更新 lockfile
uv lock --upgrade-package langchain-core

# CI 强制 frozen
uv sync --frozen --all-extras
```

### 13.2 静态门禁（CI 强制 · 6 项）

| 工具 | 用途 | 触发时机 | 失败行为 |
|------|------|----------|----------|
| **uv sync --frozen** | lockfile 一致性 | pre-commit + CI | CI 失败 |
| **ruff format** | 代码格式化 | pre-commit + CI | CI 失败 |
| **ruff check** | 代码 lint（含 ST-ADAPTER-BOUNDARY） | pre-commit + CI | CI 失败 |
| **pyright** | 类型检查（strict mode） | CI | CI 失败 |
| **bandit** | Python 安全扫描 | CI | CI 失败（high severity） |
| **pip-audit** | Python 依赖漏洞扫描 | CI（pre-build） | CI 失败（high CVSS） |

**Ruff 自定义规则 ST-ADAPTER-BOUNDARY**（planned · 实施细节 L3-3）：

```python
# ruff 自定义规则示例（伪代码）
# 检测：业务层（adapter-sdk）禁 import framework SDK
# 例外：framework adapter 子包内允许
# 检测：Operator Core 禁 import adapter-sdk
```

### 13.3 测试工具链

```bash
# adapter-sdk 单元测试（≥ 95% 覆盖）
cd packages/adapter-sdk
pytest tests/unit/ -v --cov=supteam_a2a.adapter --cov-fail-under=95

# framework adapter 集成测试
cd adapters/langchain
pytest tests/integration/ -v --cov=supteam_a2a.adapters.langchain --cov-fail-under=80

# Golden Adapter 测试
pytest tests/golden/ -v --tb=short

# Conformance 测试（依赖 a2a-python conformance 套件）
pytest tests/conformance/ -v

# E2E 测试（kind 集群）
pytest tests/e2e/ -v --cluster=kind

# Property / Fuzz 测试（Hypothesis）
pytest tests/property/ -v --hypothesis-seed=42
```

### 13.4 镜像构建 + 发布

```bash
# 本地构建（单个 framework）
docker build -f adapters/langchain/Dockerfile \
    -t ghcr.io/superteam-a2a/adapter-langchain:dev \
    .

# 多 framework 并行构建
docker buildx build --platform linux/amd64,linux/arm64 \
    -f adapters/langchain/Dockerfile \
    -t ghcr.io/superteam-a2a/adapter-langchain:v0.2.0-0.1.5-py3.12 \
    --push \
    .

# 签名 + 验证
cosign sign --yes ghcr.io/superteam-a2a/adapter-langchain@sha256:...
cosign verify --certificate-identity-regexp 'https://github.com/superteam-a2a' \
    ghcr.io/superteam-a2a/adapter-langchain@sha256:...
```

### 13.5 部署工具链

```bash
# Helm 安装（默认 langchain）
helm install adapter helm/ \
    --set frameworks.langchain.image.tag=v0.2.0-0.1.5-py3.12

# 多 framework 部署
helm install adapter helm/ \
    --set frameworks.langchain.image.tag=v0.2.0-0.1.5-py3.12 \
    --set frameworks.autogen.image.tag=v0.2.0-0.2.3-py3.12

# Helm unittest
helm unittest helm/

# Helm lint
helm lint helm/

# K8s 部署验证
kubectl get pods -l app.kubernetes.io/name=superteam-a2a-adapter
kubectl logs -l app.kubernetes.io/name=superteam-a2a-adapter --tail=100

# Adapter 健康检查
curl http://adapter-pod:8080/healthz
curl http://adapter-pod:8080/readyz
curl http://adapter-pod:8080/.well-known/agent.json | jq
curl http://adapter-pod:8080/metrics | grep supteam_adapter_
```

---

## 附录 A：跨模块引用

| 引用对象 | 位置 | 用途 |
|----------|------|------|
| **L2-3 Adapter 设计 v0.2.0** | [`docs/design/L2-modules/L2-adapter.md`](../../design/L2-modules/L2-adapter.md) | 设计依据（本 Spec 是其落地；2026-07-26 #35 评审通过） |
| **L2-1 A2A Protocol Spec v0.2.0** | [`docs/spec/L2-module-specs/L2-a2a-protocol.md`](./L2-a2a-protocol.md) | `create_app()` 嵌入 / AgentCard types / 错误码基线 / mTLS / SPIFFE / Discovery（2026-07-24 评审通过；模块 ID C-2） |
| **L2-2 Operator Core Spec v0.2.0** | [`docs/spec/L2-module-specs/L2-operator-core.md`](./L2-operator-core.md) | Owned resources（Adapter container）+ reconcile 契约 + admission 校验（2026-07-25 评审通过） |
| **L2-2 Operator Core Design v0.2.0** | [`docs/design/L2-modules/L2-operator-core.md`](../../design/L2-modules/L2-operator-core.md) | Python 重写 + 评审通过 2026-07-25（80KB / 1583 行；模块 ID C-1） |
| **L2-4 Knowledge / Memory Spec v0.2.0** | [`docs/spec/L2-module-specs/L2-knowledge-memory.md`](./L2-knowledge-memory.md) | v1.0+ Adapter 代理 4 A2A method（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）· 2026-07-27 #43 评审通过 · 4152 行 / 194.6KB / §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项 · [评审报告](../../reviews/l2-4-knowledge-memory-spec-python-review.md) |
| **L2-4 Knowledge / Memory Design v0.2.0** | [`docs/design/L2-modules/L2-knowledge-memory.md`](../../design/L2-modules/L2-knowledge-memory.md) | Memory 降级路径（§12.5）· 2026-07-27 #39 评审通过 · 1920 行 / 97KB / 14 节 + 2 附录 |
| **L1 Architecture v0.2.0** | [`docs/design/L1-architecture.md`](../../design/L1-architecture.md) | Adapter 角色 + 5 行 YAML + 接口 + 拓扑 + 路线图 + §11.5 Python 性能预算（2026-07-24 评审通过） |
| **L1 Architecture §5.2.1** | 同上 | Agent CRD `spec.adapter` 字段（含 v0.2 `embedded` 字段） |
| **L1 Spec v0.2.0** | [`docs/spec/L1-system-spec.md`](../../spec/L1-system-spec.md) | §5 CRD + §15 部署 + §16 指标命名（2026-07-24 评审通过） |
| **ADR-0001 v1 范围声明** | [`docs/adr/0001-v1-scope-statement.md`](../../adr/0001-v1-scope-statement.md) | 6 framework adapters 范围 |
| **ADR-0004 v0.1 时间线延长** | [`docs/adr/0004-v01-scope-extension-knowledge-and-memory.md`](../../adr/0004-v01-scope-extension-knowledge-and-memory.md) | v0.1=0 / v0.5=2 / v1.0=6 |
| **ADR-0005 Python-first** | [`docs/adr/0005-python-first-technology-stack.md`](../../adr/0005-python-first-technology-stack.md) | §3.3 Adapter SDK + §6 异步 + §7 镜像 + §9 安全 + §10 可观测 + §13 工程布局（2026-07-24 通过） |
| **ADR-0008 A2A-python SDK 选择** | [`docs/adr/0008-a2a-python-sdk-decision.md`](../../adr/0008-a2a-python-sdk-decision.md)（L2-1 配套） | a2a-python SDK 版本锁定 |
| **宪法 v0.5.0 §2.2 多框架多元主义** | [`CONSTITUTION.md`](../../../CONSTITUTION.md) | 所有框架必须支持 |
| **宪法 §3.7 反依赖** | 同上 | Operator 不得 import 框架代码（Adapter 可，但通过独立容器隔离） |
| **宪法 §3.8 Python-first** | 同上 | 全栈 Python（ADR-0005 supersede Go） |
| **宪法 §4.7 Golden Adapter** | 同上 | 每框架 ≥ 5/10 个 Golden Cases |
| **宪法 §7 可观测性** | 同上 | supteam_adapter_* 指标 + OTel + JSON 日志 |
| **宪法 §9.7 静态质量** | 同上 | ruff + pyright strict + bandit + pip-audit |
| **宪法 §14.4 L2 评审门禁** | 同上 | 设计 + Spec + 评审三步门禁 |
| **宪法 §14.5 MVP 例外** | 同上 | 单点评审适用（2026-07-24 内有效） |
| **MVP 例外 §14.5** | 同上 | 单点评审已采用（与 L2-1 / L2-2 / L2-4 一致） |

---

## 14. 验收清单（30 项 · 全 PASS 自检）

### 14.1 模块完整性（10 项）

- [x] §1 模块职责 + Public API surface 完整（边界规则 3 层）
- [x] §2 包结构与文件清单完整（adapter-sdk + 6 framework adapter 子包）
- [x] §3 Adapter Protocol + FrameworkAdapter + AgentCardConverter 3 个 Protocol 完整
- [x] §4 Card 转换层（5 转换点 + 6 framework skills + Pydantic schema）
- [x] §5 配置注入（AdapterConfig + FrameworkAdapterConfig + 4 层优先级 + Secret 隔离）
- [x] §6 错误码与重试（7 错误码 + StrEnum + Tenacity 5 类策略 + 3 传播通道）
- [x] §7 可观测性（7 Prometheus + OTel 4 层 + structlog JSON + 9 敏感字段脱敏）
- [x] §8 容器镜像（uv workspace + Dockerfile 多阶段 + 6 framework 独立 base + cosign + SLSA）
- [x] §9 部署形态（Sidecar + 同进程 plugin + Init Container 不推荐 + 决策表 + 资源限制）
- [x] §10 生命周期契约（5 时序图：启动 / Card / Reload / 优雅停机 / 错误恢复）

### 14.2 Python-first 硬约束（10 项）

- [x] typing.Protocol + @runtime_checkable（§3.1 Adapter + FrameworkAdapter + AgentCardConverter）
- [x] Pydantic v2 + extra="forbid" + frozen=True（§4.1 + §5.1 + §5.5）
- [x] 异步优先 + async handler（§3.1 on_message / health_check）
- [x] 单进程原则（Uvicorn 1 worker + uvloop + httptools，§8.1 Dockerfile ENTRYPOINT）
- [x] boundary 强制 lint（§1.2 边界规则 3 层 + §13.2 ST-ADAPTER-BOUNDARY）
- [x] uv workspace + uv.lock --frozen（§2 总览 + §13.1 工具链）
- [x] 静态门禁 ruff + pyright strict + bandit + pip-audit（§13.2 6 项 CI 强制）
- [x] COSIGN 签名 + SLSA L3 provenance（§8.4）
- [x] Adapter 不持有 LLM API key（§5.3 Secret 隔离 + §5.5 reject_llm_api_key validator）
- [x] 敏感字段禁记（§7.3 _SENSITIVE_KEYS 9 项脱敏 + §7.4 关键约束）

### 14.3 可观测性 + 安全 + 性能（5 项）

- [x] 7 Prometheus 指标 + OTel 4 层 Span + structlog JSON（§7.1-7.3）
- [x] Pod Security restricted + mTLS 透明 + Secret 隔离（§8.6 + §5.3）
- [x] 同进程 plugin CPU offload via anyio.to_thread.run_sync（§3.5 LangChain 示例）
- [x] 资源限制 Sidecar 256Mi + 同进程 plugin 1Gi + Agent 2Gi（§9.5）
- [x] Python runtime 指标 4 项 + event-loop lag + thread-offload queue depth（§7.4）

### 14.4 跨文档一致性 + 测试 + 开放问题（5 项）

- [x] 21 项跨模块引用 + 附录 B ADR/Constitution 引用矩阵
- [x] 6 层测试策略（UT / IT / Golden / Conformance / E2E / Property）= 159 ID（v1.0）
- [x] Golden Adapter 强制 v0.5 ≥ 5 / v1.0 ≥ 10 per framework（§12.4）
- [x] §15 开放问题（继承 v0.2 Design 10 项 + Spec 新增 5 项 = 15 项双层模式）
- [x] 与 L1 v0.2.0 + L2-1 v0.2.0 + L2-2 v0.2.0 + L2-4 v0.1.0 + ADR-0005 + 宪法 v0.5.0 严格一致

---

## 15. 开放问题（继承 v0.2 Design 10 项 + Spec 新增 5 项 = 15 项双层模式）

### 15.1 继承自 v0.2 Design 附录 B（10 项）

| # | 问题 | 默认决策 | 待确认 |
|---|------|----------|--------|
| O-1 | 同进程 plugin 模式下 framework SDK 崩溃隔离 | framework-specific exception handler + `asyncio.shield` 包装 framework invoke | L3-3 实测 |
| O-2 | 6 framework Card 转换 introspection API 稳定性 | L3-3 venv 实测每个 framework；不稳定的降级到 static YAML card | L3-3 |
| O-3 | Sidecar 模式 `httpx.AsyncClient` 是否需要 mTLS？ | v0.1 同 Pod localhost 通信（无须 mTLS）；v0.5+ 跨 Pod Adapter 通信需要 mTLS + SPIFFE | L3-3 |
| O-4 | framework upgrade 兼容性如何长期保障？ | adapter 锁定 framework major 版本；minor 升级需回归测试 + Golden Case | L1 + 用户 |
| O-5 | 第三方贡献 adapter 的 review 流程？ | 准入清单（参考 contrib/README.md）+ 2 名 maintainer LGTM | 用户 |
| O-6 | adapter 版本与 framework 版本的版本矩阵管理？ | 镜像 tag 含双版本号；deprecation 公告 6 个月前 | 用户 |
| O-7 | Sidecar 模式资源开销是否过高？（每 Agent Pod 多 256MB Adapter） | 默认 Sidecar；嵌入式仅限 Python-native framework v0.2+ | 用户 |
| O-8 | framework 升级导致的 A2A Memory 兼容性问题？ | framework memory 不可用时降级到 A2A Memory service 代理 | v1.0+ |
| O-9 | Adapter 是否需要支持 framework 自定义 transport（如 gRPC）？ | 默认 HTTP/JSON；gRPC 作为 v1.5+ 可选优化 | v1.5+ |
| O-10 | 6 framework SDK 的 License 一致性如何审计？ | 仅采纳 Apache 2.0 / MIT / BSD-3 兼容 license | CI 自动检测 + 用户 review |

### 15.2 Spec 新增（5 项双层模式）

| # | 问题 | 默认决策 | 待确认 |
|---|------|----------|--------|
| **B.11（Spec 新增）** | uv workspace 多 framework 子包并行构建性能？ | 利用 uv cache + Docker BuildKit 并行构建；CI matrix 测试 | L3-3 |
| **B.12（Spec 新增）** | Adapter 镜像 cosign 签名 + SLSA provenance 完整链路验证？ | GitHub Actions OIDC + cosign keyless + SLSA L3 + admission policy 强制 | L3-3 |
| **B.13（Spec 新增）** | Adapter 是否需要 ratelimit per-Agent（独立于 A2A Server ratelimit middleware）？ | 不重复实现；由 L2-1 §6 ratelimit middleware 提供 | L3-3 |
| **B.14（Spec 新增）** | 同进程 plugin 模式下 event-loop lag 是否需要独立监控？ | 与 L2-1 §9.2 Python runtime 指标统一（event_loop_lag_seconds Histogram + 50ms threshold） | L3-3 |
| **B.15（Spec 新增）** | framework 自定义 transport（如 gRPC v1.5+）如何在 Adapter Protocol 暴露？ | 预留 `Adapter.transport` Protocol 属性（v1.5+ 默认 HTTP/JSON） | v1.5+ |

**总评**：15 项开放问题均有默认决策（不挂空），覆盖 crash 隔离 / Card 稳定性 / mTLS / 升级 / 第三方贡献 / 版本矩阵 / 资源开销 / Memory 兼容 / transport / License / 构建性能 / 供应链 / ratelimit / event-loop / 自定义 transport 15 维度。

---

## 附录 B：ADR / Constitution 引用矩阵

| 决策 | 引用 | 章节 | 状态 |
|------|------|------|------|
| `typing.Protocol` 作为 Adapter 抽象 | ADR-0005 | §3.3 | Accepted |
| `@runtime_checkable` Protocol 允许 `isinstance` | 宪法 v0.5.0 | §3.8 | 强制 |
| Python-native framework 同进程 plugin | ADR-0005 + L1 v0.2.0 Arch | §3.3 + §6.4 | Accepted |
| 非 Python framework Sidecar 模式 | ADR-0005 + L1 v0.2.0 Arch | §3.3 + §6.4 | Accepted |
| framework SDK import 仅在 framework adapter 子包 | 宪法 §3.7 + ADR-0005 §3.3 | — | 强制 |
| `adapter-sdk` 严禁依赖 framework | ADR-0005 §3.3 | — | 强制 |
| Operator Core 严禁 import adapter-sdk | 宪法 §3.7 | — | 强制 |
| `python:3.12-slim` 多阶段镜像 | ADR-0005 | §2.2 + §9.3 | Accepted |
| uv workspace + uv.lock --frozen | ADR-0005 | §13 工程布局 | 强制 |
| 每 framework 独立 base 镜像 | ADR-0005 | §9.3 | Accepted |
| 镜像 tag `{framework}:{adapter-version}-{framework-version}-py{python-version}` | L1 v0.2.0 Arch + L2-3 v0.2.0 Design | §6 + §8 | 继承 |
| Adapter 镜像非 root + read-only rootfs | 宪法 §3.5 + ADR-0005 §9.3 | — | 强制 |
| Pod Security Standard restricted | 宪法 §6 | — | 强制 |
| Adapter 镜像 cosign 签名 + SLSA L3 | ADR-0005 | §9.3 | 强制 |
| 5 行 YAML 契约 | L1 v0.2.0 Arch | §6.2 | Accepted |
| 6 框架适配矩阵 | L1 v0.2.0 Arch + L2-3 v0.2.0 Design | §6.5 + §5 | 继承 v0.2.0 |
| Agent CRD `spec.adapter.embedded` 字段（v0.2+） | L1 v0.2.0 Arch | §6.4 | Accepted |
| Adapter 错误码范围 -32001 ~ -32007 | L2-1 v0.2.0 Spec + L2-3 v0.2.0 Design | §7 + §9 | 继承 v0.2.0 |
| `AdapterErrorCode(StrEnum)` + `AdapterError` | L2-1 v0.2.0 Spec | §7 + §8 | 继承 |
| Tenacity 重试策略 | ADR-0005 §2.2 | §6.3 | Accepted |
| Golden Adapter 测试强制 | 宪法 §4.7 | — | 强制 |
| `supteam_adapter_*` 指标命名 | L1 v0.2.0 Spec + L2-3 v0.2.0 Design | §16 + §10 | 继承 |
| 单进程 Uvicorn worker + uvloop + httptools | ADR-0005 §6.2 + L1 v0.2.0 Arch | §11.5 | Accepted |
| OTel 显式 provider 注入（避免污染全局） | ADR-0005 §10.1 | §7.2 | 强制 |
| structlog JSON + 9 项敏感字段脱敏 | ADR-0005 §10 | §7.3 | 强制 |
| mTLS / cert-manager 挂载 | ADR-0005 §9.1 + L1 v0.2.0 Arch | §10.2 | Accepted |
| Adapter 不持有 LLM API key | L1 v0.2.0 Arch v0.2.0 + 宪法 §3.5.3 | §6.4 + §3.5.3 | 强制 |
| ruff + pyright strict + bandit + pip-audit 静态门禁 | 宪法 §9.7 + ADR-0005 §13 | §13.2 | 强制 |
| 同进程 plugin `anyio.to_thread.run_sync` CPU offload | ADR-0005 §6.3 | §3.5 | 强制 |
| ASGI middleware 链顺序（Tracing → Auth → RateLimit → Metrics） | L2-1 v0.2.0 Spec | §6.2 | 继承 |
| ruff ST-ADAPTER-BOUNDARY 自定义规则 | ADR-0005 §3.3 + 宪法 §3.7 | §13.2 | 强制 |
| Python runtime 4 指标（event-loop lag / offload queue / active tasks / GC） | L2-1 v0.2.0 Spec | §9.2 | 继承 |

---

## 变更记录

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| v0.1-draft | 2026-07-24 | 初稿：7 节 + 2 附录；Go Package 布局（src/adapters/）+ Exported API（9 个 interface/struct）+ Helm values（6 框架覆盖）+ CRD Schema 引用 + 生命周期契约 5 步时序 + 测试骨架（UT 20 + IT 21 + Golden 50 + CF 3 + E2E 6 = 100 ID） | Claude Code (会话 cont10) |
| v0.1.0 | 2026-07-24 | 评审通过（[l2-3-adapter-review.md](../../reviews/l2-3-adapter-review.md) §A 10 维度全通过 + §F.4 颗粒度决议保留完整版 + §F.6 跨文档同步完成）；附录 B 升级为 12 项（继承设计 8 项 + Spec 新增 4 项双层开放问题模式） | 项目发起人（基于 MVP 例外 14.5 单点评审；会话 cont11） |
| v0.1.0 + ADR-0005 指针 | 2026-07-24 | 顶部追加 ADR-0005 supersede 指针（标记为「迁移输入」），Go 实现条款已 supersede | 项目发起人（#18 会话） |
| **v0.2-draft** | **2026-07-26** | **Python 重写：14 节 + 2 附录；uv workspace + adapter-sdk + 6 framework adapter 子包；Adapter Protocol + FrameworkAdapter + AgentCardConverter（typing.Protocol + @runtime_checkable）；4 层配置优先级 + 7 错误码 + StrEnum + Tenacity 5 类策略 + 3 传播通道；7 Prometheus + OTel 4 层 + structlog JSON + 9 敏感字段脱敏；Dockerfile 多阶段模板 + 6 framework 独立 base + cosign + SLSA L3；Sidecar + 同进程 plugin 双拓扑 + Init Container 不推荐 + 5 生命周期时序图；完整 Helm values 11.1-11.6（含 6 framework + RBAC + NetworkPolicy + Helm unittest）；6 层测试策略（UT 48 + IT 12 + Golden 10 + CF 5 + E2E 2 + Property 4 = 81 ID v0.2 / 159 ID v1.0）；uv workspace + 6 项静态门禁 + Ruff ST-ADAPTER-BOUNDARY；15 项开放问题双层模式（继承设计 10 + Spec 新增 5）；附录 A 21 项引用 + 附录 B 32 行 ADR/Constitution 引用矩阵；总计 ~99KB / 2579 行（颗粒度偏差合理：uv workspace 11 文件 SDK + 6 framework 子包 + 9 Protocol/Class 完整契约 + 6 层测试 ID 矩阵）** | **Claude Code (#36 会话)** |
| **v0.2.0** | **2026-07-26** | **#37 会话评审通过：[l2-3-adapter-spec-python-review.md](../../reviews/l2-3-adapter-spec-python-review.md) §A-§P 10 维度全 PASS（0 阻塞项 · 3 关注项 · 4 建议项）；uv workspace 工程布局完整（adapter-sdk + 6 framework 子包 + 11 文件 SDK）+ 9 个 Python Protocol/Class 完整契约 + 5 生命周期契约时序图 + Helm values 11.1-11.6 完整 schema + 6 层测试策略 81-159 测试 ID 矩阵；114KB / 2705 行颗粒度偏差 2.85x 与 L2-2 Spec v0.2.0 103KB / 1890 行 / 2.58x 同等级保留完整版（§N.3 决议）；wire contract 与 v0.2.0 Design + v0.1.0 Go baseline 完全继承（14/14 项）；与 L1 v0.2.0 + L2-1 v0.2.0 + L2-2 v0.2.0 + L2-4 v0.1.0 + ADR-0005 + 宪法 v0.5.0 严格一致；**L2 阶段 3/4 Python 化完成**（L2-1 v0.2.0 + L2-2 v0.2.0 + L2-3 v0.2.0 已通过；L2-4 v0.1.0 Go baseline 未 Python 化）；下次会话入口：L3-1 Operator Core 文件级 Spec Python 起草（独立任务；基于 L2-2 v0.2.0 Design + Spec）→ L2-4 Knowledge/Memory Python 重写** | **项目发起人（基于 MVP 例外 14.5 单点评审；#37 会话）** |

---

> **状态**：✅ **v0.2.0**（#36 起草完整版 + #37 评审通过 10 维度全 PASS；0 阻塞项）
> **下次会话入口**：L3-1 Operator Core 文件级 Spec Python 起草（独立任务；基于 L2-2 v0.2.0 Design + Spec；70 文件清单 + 4 Controllers reconcile 伪代码 + 122 UT + 11 IT + 6 E2E）→ L2-4 Knowledge/Memory Python 重写