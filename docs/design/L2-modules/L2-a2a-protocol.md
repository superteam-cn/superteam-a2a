# L2 模块设计：A2A Protocol（通信层 · Python）

> **层级**：L2 — 模块设计
> **模块 ID**：C-2（A2A Core Library，见 L1 v0.2.0 Architecture §4.1）
> **代码位置**：`packages/a2a-core/src/superteam_a2a/a2a/`（**Python-first · ADR-0005 §13 工程布局**）
> **版本**: **v0.2.0**（Python 重写 · ADR-0005 触发；2026-07-24 评审通过）
> **状态**: ✅ **已评审通过**（依据 [`docs/reviews/l2-1-a2a-protocol-review.md`](../../reviews/l2-1-a2a-protocol-review.md) 2026-07-24；10 维度全 PASS）
> **配套 Spec**: [`docs/spec/L2-module-specs/L2-a2a-protocol.md`](../../spec/L2-module-specs/L2-a2a-protocol.md)（**v0.2.0** 同日同步评审通过）
> **配套评审**: [`docs/reviews/l2-1-a2a-protocol-review.md`](../../reviews/l2-1-a2a-protocol-review.md)（✅ 2026-07-24；10 维度全 PASS）
> **supersedes**: v0.1.0 Go baseline（[`docs/reviews/l2-1-a2a-protocol-review.md`](../../reviews/l2-1-a2a-protocol-review.md) 2026-07-23 通过；**仅 supersede Go struct / Go package / Go HTTP server / Go JSON-RPC envelope 实现条款；wire contract（A2A JSON-RPC / 6 method 字段 / Agent Card 路径 / 错误码 / 任务状态机 / metric name）继续有效**）
> **依据**：[`CONSTITUTION.md`](../../../CONSTITUTION.md) **v0.5.0** §3.8 Python-first + §6 mTLS + §7 可观测性 + §9.7 静态质量 + §13.6 维护 A2A Python SDK；[ADR-0005](../../adr/0005-python-first-technology-stack.md) §3.2 A2A Core 模块映射 + §8 SDK 门禁；[L1 Architecture v0.2.0](../L1-architecture.md) §3.4 / §7 + [L1 Spec v0.2.0](../../spec/L1-system-spec.md) §5 / §15
> **MVP 例外**: §14.5 适用

---

## 0. 阅读指南

本文档定义 `superteam-a2a` **L2-1 A2A Protocol 模块**（通信层 · C-2）的 **Python 实现设计**：包结构、compatibility adapter 边界、4 个项目扩展 method router、mTLS / SPIFFE 集成、单进程 / async-first 边界、协议升级兼容策略。**不**涉及具体函数签名、JSON Schema 字段约束（这些在 L3-2 Spec 定义）；**不**涉及业务语义（wire contract 完全继承 v0.1.0）。

**读者**：L3-2 Spec 作者、Adapter SDK 作者、Knowledge Service / Memory backend 作者、架构评审者。

**关键变化**（与 v0.1.0 Go baseline 对照）：

| 维度 | v0.1.0 Go | v0.2 Python |
|------|-----------|-------------|
| **SDK 来源** | 自研 Go envelope + types | **官方 `a2a-sdk`（`a2aproject/a2a-python`）+ `superteam_a2a.a2a.upstream` boundary** |
| **HTTP server** | `net/http` + `gorilla/mux` | **ASGI（Uvicorn 单 worker）** |
| **HTTP client** | 标准库 `net/http` | **`httpx.AsyncClient` 进程级连接池** |
| **JSON-RPC** | 自研 envelope | **官方 SDK envelope + Pydantic 校验** |
| **mTLS** | `crypto/tls` | **`ssl.SSLContext` + cert-manager mounted cert** |
| **任务状态机** | 自研 FSM | **官方 SDK TaskState + MemoryReconciler 调用方控** |
| **错误码** | 自定义 enum + 错误响应 | **官方 SDK error code + 项目 extension error code prefix `KNOWLEDGE_*` / `MEMORY_*`** |
| **测试 / conformance** | Go `testing` + 自研 conformance | **pytest + 官方 conformance suite + contract test** |

---

## 1. 模块使命与边界

### 1.1 使命

L2-1 是 `superteam-a2a` **通信层的唯一实现**：暴露 A2A JSON-RPC 2.0 端点（含 6 个 v0.1 method）供所有 Agent 通过 mTLS 调用；解析对端 Agent Card；执行 Discovery + Retry + Circuit Breaker + P2C + mTLS 身份校验；产出指标 / Trace / 日志；为业务层（Knowledge Service / MemoryReconciler / Operator / Adapter SDK）提供 SDK 形式的客户端。

### 1.2 系统边界

**模块内**（v0.2 Python-first）：
- 官方 `a2a-sdk` envelope / types / ASGI server / async client 的复用与边界封装（`superteam_a2a.a2a.upstream`）
- 4 个项目扩展 method 的 router 注册（`a2a.queryKnowledge` / `a2a.getKnowledgeItem` / `a2a.recordMemory` / `a2a.queryMemory`）
- mTLS / SPIFFE / 证书热更新（Python `ssl.SSLContext`）
- Discovery：K8s Service / DNS / EndpointSlice watch + Agent Card 拉取
- 客户端：重试 + 退避 + 熔断 + P2C + connection pool（`httpx.AsyncClient`）
- 业务授权 / 限流 / 指标 / Trace / 结构化日志
- 项目私有 DTO（Pydantic v2 strict）：`a2a.upstream` 边界的内部类型
- conformance suite 接入与 contract test

**系统外**（明确不实现）：
- 任何 Agent 框架内部逻辑（LangChain / AutoGen / CrewAI 等）→ Adapter SDK 负责
- 业务语义实现（Knowledge 检索算法、Memory 衰减算法）→ Knowledge Service / MemoryReconciler 模块负责
- CRD 生命周期管理（CRUD / admission webhook / finalizer）→ Operator Core 模块负责
- LLM Provider / MCP Server → Agent 框架负责
- 跨集群联邦 / Token-based federation → v0.5+ 范畴
- A2A Stream（`a2a.subscribeTask` / `a2a.cancelTask`）→ v0.5+ 范畴（v0.1 仅 sync）

### 1.3 价值主张

| 维度 | 承诺 |
|------|------|
| **业务模块作者** | 1 行 import 获取全部 A2A 类型 + client；业务逻辑无需感知协议细节 |
| **项目扩展 method 作者** | `Protocol` 接口 + `@router.register("a2a.methodName")` 装饰器即可注册 |
| **运维者** | 标准 ASGI 进程；统一 `/metrics` `/healthz` `/readyz`；mTLS 透明 |
| **上游** | 跟随 `a2aproject/a2a-python` 主分支，contract test 防止 silent break |

---

## 2. a2a-python spike 结论（ADR-0005 §8 前置门禁 · 2026-07-24）

> **本节作为 L2-1 Python 设计的输入**，完成 ADR-0005 §8 要求的"只读文档验证或非产品 spike"。结论用于 §3-§8 的设计决策。

### 2.1 spike 范围与依据

依据 ADR-0005 §8，L2-1 Python 批准前必须确认 9 项关键问题。本 spike 通过公开网络调研（PyPI / GitHub release page / 搜索结果聚合）收敛结论；L3-2 重写时**必须**在 Python 环境实测所有路径（pin 精确版本号、确认 import 路径、跑通示例代码、跑通 conformance 套件）。

### 2.2 9 项 spike 结论

| # | 项目 | 结论 | 依据 |
|---|------|------|------|
| 1 | **官方包名 / PyPI** | 包名待 PyPI 验证（组织已从 `google-a2a` 改名 `a2aproject`）；预计为 `a2a-sdk` 或 `a2a-python`。L3-2 必须 `pip index versions` 实测 | [a2aproject/a2a-python](https://github.com/a2aproject/a2a-python)（原 [google-a2a/a2a-python](https://github.com/google-a2a/a2a-python) 已重定向） |
| 2 | **Python 支持版本** | ADR-0005 §2.2 锁定 Python 3.12+；具体 `requires-python` L3-2 必须读 `pyproject.toml` 验证 | 已知最新 release v0.3.26（2026-04-09） |
| 3 | **当前协议版本（protocolVersion）** | 跟随 A2A 主仓库 `a2aproject/A2A` 最新版本；v0.1 锁定 A2A v0.3 核心子集；SDK 升级时 protocolVersion 不破坏 | [a2aproject/A2A](https://github.com/a2aproject/A2A) |
| 4 | **核心类型** | SDK 提供 `AgentCard` / `Message` / `Part` / `Task` / `Artifact` / `TaskStatus` / JSON-RPC envelope（`JSONRPCRequest` / `JSONRPCResponse` / `JSONRPCError`）；**项目不重新定义** | [a2a-python/src/a2a/server/apps/jsonrpc/jsonrpc_app.py](https://github.com/a2aproject/a2a-python/blob/174d58dd/src/a2a/server/apps/jsonrpc/jsonrpc_app.py) |
| 5 | **ASGI server 与 async client** | ASGI JSON-RPC app 由 SDK 提供；async client 基于 `httpx.AsyncClient`（SDK 内部使用）；L2-1 通过 SDK 入口暴露 | ADR-0005 §2.2 + SDK ASGI app 路径 |
| 6 | **JSON-RPC / HTTP / SSE 边界** | sync JSON-RPC over HTTP（v0.1）；SSE v0.5+；项目 4 个扩展 method 走同一 JSON-RPC envelope | L1 v0.2.0 Architecture §3.4 + Spec §5 |
| 7 | **自定义 method 注册扩展点** | **官方 SDK 不直接提供**项目级 method 注册 API；通过 **compatibility adapter 边界 router**（§4）注入到 SDK ASGI app 之外 | ADR-0005 §8 + §3.2；与上游保持隔离 |
| 8 | **mTLS 自定义 transport** | SDK 通过 Starlette/Uvicorn 暴露；mTLS 通过 Uvicorn `--ssl-keyfile` / `--ssl-certfile` / `--ssl-ca-certs` 注入；项目通过 Helm values 挂载 cert-manager 颁发的 cert；**证书热更新**通过 SIGTERM + Uvicorn reload 或自定义 ssl.SSLContext reload | [Uvicorn SSL docs](https://www.uvicorn.org/deployment/#running-with-https) + ADR-0005 §9.1 |
| 9 | **conformance 套件接入方式 + upstream error/type 兼容策略** | conformance suite 由 SDK 提供（具体路径 L3-2 实测）；upstream 升级通过 **contract test 套件**（Pydantic JSON Schema diff + wire JSON sample 回放）锁定 wire 一致性；minor upgrade 不破坏；major upgrade 走 ADR | ADR-0005 §8 + §11.2 conformance 门禁 |

### 2.3 spike 通过条件

✅ **9 项全部收敛**（结论见 §2.2）。L2-1 设计可以基于上述结论起草。L3-2 Spec 重写时**必须**重新实测所有路径，并在 L3 评审前报告任何实测与本 spike 结论的偏差。

### 2.4 已知未决（移交 L3-2）

| # | 项 | 影响 | 处理 |
|---|----|------|------|
| U-1 | 精确 PyPI 包名（`a2a-sdk` vs `a2a-python`） | L3-2 `pyproject.toml` 依赖声明 | L3-2 第一步 `pip index versions a2a-*` |
| U-2 | `requires-python` 精确下限 | L3-2 CI 矩阵 | L3-2 第一步 `pip show` |
| U-3 | conformance 套件确切 import 路径 / 入口命令 | L3-2 测试 setup | L3-2 在 Python venv 实测 |
| U-4 | `py-spiffe` Workload API 是否满足 SVID watch + 热更新 | L3-2 mTLS 实现路径 | ADR-0005 §9.1：v0.1 用 cert-manager mounted cert + URI SAN；不满足时回退 |
| U-5 | SDK ASGI server 是否原生支持 method-level 中间件链（如认证 / 限流 / 指标） | L4 实现细节 | L3-2 实测；不满足时通过 ASGI middleware 包装 |

---

## 3. Python 包结构（ADR-0005 §13 工程布局）

### 3.1 包布局（`packages/a2a-core/src/superteam_a2a/a2a/`）

```
superteam_a2a.a2a/
├── __init__.py                # 公共 API surface（仅 re-export upstream 类型 + 4 个 router）
├── upstream.py                # ⚠️ boundary — 所有官方 SDK import 必须仅经此模块
├── upstream_types.py          # 业务层使用的 Pydantic 类型（项目私有 DTO）
├── server/
│   ├── __init__.py
│   ├── app.py                 # create_app(card, handlers, mTLS_config) -> ASGI app
│   ├── middlewares.py         # AuthMiddleware / RateLimitMiddleware / TracingMiddleware
│   └── lifespan.py            # asynccontextmanager：graceful shutdown 顺序（§5.4）
├── client/
│   ├── __init__.py
│   ├── client.py              # A2AClient（基于 httpx.AsyncClient）
│   ├── retry.py               # Tenacity retry policy
│   ├── circuit_breaker.py     # circuit breaker + P2C
│   └── discovery.py           # K8s Service / DNS / EndpointSlice / Agent Card
├── extensions/                # ⚠️ 项目 4 个扩展 method router
│   ├── __init__.py
│   ├── base.py                # ExtensionRouter protocol（@router.register）
│   ├── query_knowledge.py     # a2a.queryKnowledge
│   ├── get_knowledge_item.py  # a2a.getKnowledgeItem
│   ├── record_memory.py       # a2a.recordMemory
│   └── query_memory.py        # a2a.queryMemory
├── mtls/
│   ├── __init__.py
│   ├── ssl_context.py         # load cert-manager mounted cert → ssl.SSLContext
│   ├── spiffe.py              # URI SAN SPIFFE ID 解析（py-spiffe 验证通过后启用）
│   └── hot_reload.py          # 证书热更新（inotify / k8s watch）
├── observability/
│   ├── __init__.py
│   ├── metrics.py             # prometheus-client Counter / Histogram / Gauge
│   ├── tracing.py             # OpenTelemetry provider 注入（显式，避免污染）
│   └── logging.py             # structlog setup（JSON 输出）
├── errors.py                  # 项目扩展错误码（KNOWLEDGE_* / MEMORY_*）
└── _internal/                 # ⚠️ private — 业务层禁止 import
    └── __init__.py
```

### 3.2 边界规则（ADR-0005 §3.2 关键原则）

```
┌─────────────────────────────────────────────────────────┐
│  Official a2a-sdk (a2aproject/a2a-python)               │
│  src/a2a/{types, server, client, utils, ...}            │
└──────────────────────────┬──────────────────────────────┘
                           │ 唯一 import 入口
                           ▼
        ┌─────────────────────────────────────┐
        │  superteam_a2a.a2a.upstream         │  ← ⚠️ boundary
        │  re-exports + 版本 / 类型锁定       │
        └────────────────┬────────────────────┘
                         │
        ┌────────────────▼─────────────────────┐
        │  superteam_a2a.a2a.*                 │
        │  (server / client / extensions /     │
        │   mtls / observability / errors)     │
        └────────────────┬─────────────────────┘
                         │ import 业务 DTO
                         ▼
        ┌─────────────────────────────────────┐
        │  Business layer                      │
        │  (Knowledge Service / MemoryBackend  │
        │   / Operator / Adapter SDK)          │
        └─────────────────────────────────────┘
```

**关键约束**（与 ADR-0005 §3.2 一致）：

1. **所有官方 SDK import 必须仅经 `superteam_a2a.a2a.upstream`**（用 ruff / pyright 自定义 import linter 检测）
2. 业务层禁止直接 `from a2a import ...`（违反 boundary）
3. upstream 版本升级通过 ADR 决策；不绕过 boundary 散弹式更新
4. 项目私有 DTO（`upstream_types.py`）只覆盖扩展 method 与项目资源；不复制 SDK 标准类型

---

## 4. compatibility adapter（4 个项目扩展 method）

### 4.1 设计动机

官方 SDK v0.3.x 不直接提供"项目级 method 注册 API"。L2-1 需要暴露 4 个项目扩展 method（`queryKnowledge` / `getKnowledgeItem` / `recordMemory` / `queryMemory`），而**不能 fork / 修改 SDK**（ADR-0005 §17.3 不可接受的退出方式）。

解决方案：**compatibility adapter 边界 router**——在 SDK ASGI app 之外叠加一个 Starlette/FastAPI sub-app，路由匹配扩展 method 后调用业务 handler；SDK ASGI app 处理标准 method。

### 4.2 架构

```python
# 示意，完整代码在 L3-2 Spec
# packages/a2a-core/src/superteam_a2a/a2a/server/app.py
from starlette.applications import Starlette
from starlette.routing import Route
from a2a.server.apps.jsonrpc import jsonrpc_app  # via upstream
from superteam_a2a.a2a.upstream import AgentCard
from superteam_a2a.a2a.extensions import (
    QueryKnowledgeRouter,
    GetKnowledgeItemRouter,
    RecordMemoryRouter,
    QueryMemoryRouter,
)


def create_app(
    card: AgentCard,
    mtls_config: MtlsConfig | None = None,
    middlewares: list[Middleware] | None = None,
) -> Starlette:
    """构造 A2A ASGI app；4 个项目扩展 method 注册到 Starlette sub-app。

    SDK 处理 sendMessage / getTask / cancelTask / subscribeTask；
    extension routers 处理 queryKnowledge / getKnowledgeItem /
    recordMemory / queryMemory。
    """
    # 1. 标准 method 由 SDK 处理
    sdk_app = jsonrpc_app(agent_card=card)

    # 2. 项目扩展 method 由 Starlette sub-app 处理（compatibility adapter）
    extension_app = Starlette(
        routes=[
            Route("/a2a/jsonrpc", endpoint=_dispatch_extension, methods=["POST"]),
        ]
    )

    # 3. 合并 + middleware 链
    app = Starlette(
        routes=[
            Mount("/", sdk_app),
            Mount("/", extension_app),
            # /.well-known/agent.json 由 SDK 提供
            Route("/healthz", endpoint=liveness, methods=["GET"]),
            Route("/readyz", endpoint=readiness, methods=["GET"]),
            Route("/metrics", endpoint=metrics_endpoint, methods=["GET"]),
        ]
    )

    # 4. middleware 链顺序：trace → auth (mTLS) → rate-limit → metrics
    app.add_middleware(TracingMiddleware)
    if mtls_config:
        app.add_middleware(MtlsMiddleware, config=mtls_config)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(MetricsMiddleware)

    return app
```

### 4.3 4 个 Extension Router 设计

```python
# packages/a2a-core/src/superteam_a2a/a2a/extensions/base.py
from typing import Protocol, runtime_checkable
from superteam_a2a.a2a.upstream_types import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
)


@runtime_checkable
class ExtensionRouter(Protocol):
    """项目扩展 method router 协议。

    L2-1 通过 inspect 找出所有实现类；L2-4 Knowledge/Memory 模块
    提供具体实现（QueryKnowledgeRouter / RecordMemoryRouter 等）。
    """

    method_name: str  # e.g. "a2a.queryKnowledge"

    async def handle(self, request: JSONRPCRequest) -> JSONRPCResponse | JSONRPCError:
        """处理单个 JSON-RPC 请求；返回响应或错误。"""
        ...
```

### 4.4 router 注册示例（示意）

```python
# packages/a2a-core/src/superteam_a2a/a2a/extensions/query_knowledge.py
# 由 L2-4 Knowledge/Memory 模块提供实现；L2-1 仅定义 protocol
class QueryKnowledgeRouter:
    method_name = "a2a.queryKnowledge"
    
    def __init__(
        self,
        knowledge_service: KnowledgeServiceProtocol,
        metrics: A2aMetrics,
    ):
        self._service = knowledge_service
        self._metrics = metrics
    
    async def handle(self, request: JSONRPCRequest) -> JSONRPCResponse | JSONRPCError:
        # 1. Pydantic 校验 params
        try:
            params = QueryKnowledgeRequest.model_validate(request.params)
        except ValidationError as e:
            return JSONRPCError(code=-32602, message="Invalid params", data=str(e))
        
        # 2. 调用业务层（异步）
        try:
            response = await self._service.query_knowledge(params)
        except KnowledgeScopeNotFound:
            return JSONRPCError(code=-32400, message="KNOWLEDGE_SCOPE_NOT_FOUND")
        # ... 错误码见 §7
        
        # 3. 返回 JSONRPCResponse
        return JSONRPCResponse(id=request.id, result=response.model_dump(by_alias=True))
```

### 4.5 关键不变量（与 v0.1.0 一致）

- **wire shape**：JSON 字段名 / camelCase / 时间格式 RFC 3339 / 错误码语义与 v0.1.0 完全一致
- **错误响应**：JSON-RPC 2.0 标准 `error.code` / `error.message` / `error.data`；HTTP 状态码由 envelope 映射
- **方法路径**：`POST /a2a/jsonrpc`（标准 method 与扩展 method 同一路径，由 JSON-RPC `method` 字段分发）
- **Agent Card**：`GET /.well-known/agent.json`（SDK 标准）

---

## 5. ASGI server 与单进程原则（ADR-0005 §6.2）

### 5.1 进程模型

**L2-1 进程内**：单个 Uvicorn worker + 单 event loop + 单 Python 进程（ADR-0005 §6.2 单进程原则）。

```python
# uvicorn 启动（Helm chart 模板生成）
uvicorn superteam_a2a.a2a.server.app:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 1 \                       # ⚠️ 强制 1
    --loop uvloop \                    # 高性能 event loop
    --http httptools \
    --ssl-keyfile=/etc/tls/tls.key \
    --ssl-certfile=/etc/tls/tls.crt \
    --ssl-ca-certs=/etc/tls/ca.crt \
    --ssl-version=3 \                  # TLS 1.3
    --lifespan on
```

**Helm values**（与 L1 Spec §9.5 一致）：
```yaml
knowledgeService:
  python:
    workers: 1                         # 强制（schema.json const: 1）
    eventLoopLagThresholdMs: 50        # event-loop lag 告警阈值
```

### 5.2 水平扩展

- 不支持同 Pod 多 worker（违反 ADR-0005 §6.2 一致性约束）
- 通过 K8s Deployment `replicas: N` 水平扩展；Knowledge Service + MemoryReconciler 共用 Deployment（v0.1 单实例 + 后续 v0.5+ 多实例）
- 状态一致性：本地 TaskStore / Discovery cache / BM25 index 必须**进程内单实例**；多实例需要外部一致性存储（v0.5+ 评估）

### 5.3 mTLS / SPIFFE（ADR-0005 §9.1）

```python
# packages/a2a-core/src/superteam_a2a/a2a/mtls/ssl_context.py
# 示意，完整在 L3-2 Spec
import ssl
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import serialization


def build_server_ssl_context(
    cert_dir: Path = Path("/etc/tls"),
) -> ssl.SSLContext:
    """从 cert-manager 挂载的 cert 文件构造 ssl.SSLContext。
    
    cert-manager 通过 Secret 挂载到 Pod：
      /etc/tls/tls.crt     # server cert
      /etc/tls/tls.key     # server key
      /etc/tls/ca.crt      # client CA (for mTLS verification)
    
    要求：TLS 1.3+；客户端证书必须校验；URI SAN SPIFFE ID 解析。
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.load_cert_chain(
        certfile=cert_dir / "tls.crt",
        keyfile=cert_dir / "tls.key",
    )
    ctx.load_verify_locations(cafile=cert_dir / "ca.crt")
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


def extract_spiffe_id(cert: x509.Certificate) -> str | None:
    """从客户端证书 URI SAN 解析 SPIFFE ID。"""
    for ext in cert.extensions:
        if isinstance(ext.value, x509.SubjectAlternativeName):
            for name in ext.value:
                if isinstance(name, x509.UniformResourceIdentifier):
                    uri = name.value
                    if uri.startswith("spiffe://"):
                        return uri
    return None
```

**证书热更新**（ADR-0005 §9.1）：cert-manager 在证书到期前自动轮换；通过 `inotify` watch `/etc/tls/` 或 K8s Secret watch 检测到文件变化 → 重建 `ssl.SSLContext` → 原子替换 Uvicorn 当前 ctx。**SIGTERM 优雅停机顺序**（§5.4）也需覆盖 reload 流程。

**SPIFFE Workload API**（U-4 移交）：`py-spiffe` 在 L3-2 实测；不满足 SVID watch + 热更新时回退 cert-manager mounted cert + URI SAN（ADR-0005 §9.1）。

### 5.4 优雅停机（ADR-0005 §6.4）

```python
# packages/a2a-core/src/superteam_a2a/a2a/server/lifespan.py
from contextlib import asynccontextmanager
from starlette.applications import Starlette
import asyncio
import signal


@asynccontextmanager
async def lifespan(app: Starlette):
    """L2-1 进程生命周期：
    
    Startup:  1. load SSL context
              2. init metrics / tracing / logging
              3. init ExtensionRouters（注入业务 handler）
              4. start K8s watch (Discovery / EndpointSlice)
              5. readiness=true
    
    Shutdown (SIGTERM): 1. readiness=false
                       2. 停止接收新请求（Uvicorn drain）
                       3. 等待 in-flight 完成（grace timeout 30s）
                       4. flush trace / metrics
                       5. 关闭 K8s watch
                       6. close httpx connection pool
    """
    # startup
    await init_observability()
    await init_routers()
    await start_k8s_watch()
    set_readiness(True)
    
    try:
        yield
    finally:
        # shutdown
        set_readiness(False)
        await drain_in_flight(timeout=30.0)
        await flush_observability()
        await stop_k8s_watch()
        await close_connection_pool()
```

**关键不变量**：
- 不吞掉 `asyncio.CancelledError`
- 测试覆盖 shutdown timeout 和 partial failure
- Helm chart `terminationGracePeriodSeconds: 60`（给足时间）

---

## 6. async-first 与 CPU offload（ADR-0005 §6.1 / §6.3）

### 6.1 async 边界

所有跨网络 / 磁盘 / K8s I/O 使用 `async/await`：

| 路径 | 实现 |
|------|------|
| K8s API | `kubernetes_asyncio` |
| A2A HTTP server | SDK ASGI（async handlers） |
| A2A HTTP client | `httpx.AsyncClient` |
| Agent Card Discovery | `httpx.AsyncClient` + `socket.getaddrinfo` |
| OTel exporter | OTel Python async export pipeline |
| BM25 index search | `anyio.to_thread.run_sync` offload（§6.2） |
| Memory batch decay | `anyio.to_thread.run_sync` offload（§6.2） |

**禁止**：
- 在 async handler 内直接调用阻塞 SDK（无替代方案时用 `anyio.to_thread.run_sync`）
- 跨进程阻塞调用（违反单进程原则）

### 6.2 CPU offload（anyio 线程池）

```python
# packages/a2a-core/src/superteam_a2a/a2a/utils/offload.py
# 示意
import anyio
from functools import partial


async def offload_cpu(func, *args, **kwargs):
    """将 CPU 密集型工作 offload 到固定线程池。
    
    线程池容量：默认 8 workers（Helm values 可配）。
    超过队列深度 → Prometheus 指标告警。
    """
    return await anyio.to_thread.run_sync(
        partial(func, *args, **kwargs),
        limiter=_cpu_limiter,  # anyio CapacityLimiter(8)
    )


_cpu_limiter = anyio.CapacityLimiter(8)
```

**适用场景**：
- BM25 评分 > 1K items（Knowledge Service）
- Memory batch decay（MemoryReconciler）
- JSON 反序列化 + 校验大 payload
- 任何 Pydantic validation > 1ms 的路径

### 6.3 事件循环监控（Python runtime 指标 · ADR-0005 §10）

```python
# packages/a2a-core/src/superteam_a2a/a2a/observability/event_loop.py
# 示意
import asyncio
import time
from prometheus_client import Histogram


EVENT_LOOP_LAG = Histogram(
    "superteam_python_event_loop_lag_seconds",
    "Event loop lag detection (Python runtime)",
    labelnames=["component"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)


async def measure_event_loop_lag(interval: float = 1.0):
    """定期检测 event loop lag；超过阈值触发 Warning Event。"""
    while True:
        start = time.perf_counter()
        await asyncio.sleep(interval)
        actual = time.perf_counter() - start
        lag = actual - interval
        EVENT_LOOP_LAG.labels(component="a2a-core").observe(lag)
        if lag > 0.050:  # 50ms 阈值（Helm values 可配）
            emit_warning_event(f"event loop lag {lag * 1000:.1f}ms exceeds threshold")
```

---

## 7. 错误模型（与 v0.1.0 完全一致）

### 7.1 wire shape 锁定

```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "error": {
    "code": -32400,
    "message": "KNOWLEDGE_SCOPE_NOT_FOUND",
    "data": {"detail": "scope team-payments-platform not found"}
  }
}
```

### 7.2 错误码表（与 L1 Spec §5.7 + §8.3 一致）

**通用错误码**（SDK 提供）：

| Code | 含义 | HTTP Status |
|------|------|-------------|
| -32700 | Parse error | 400 |
| -32600 | Invalid Request | 400 |
| -32601 | Method not found | 404 |
| -32602 | Invalid params | 422 |
| -32603 | Internal error | 500 |
| -32001 | Task not found | 404 |
| -32002 | Task timeout | 504 |
| -32003 | Task cancelled | 410 |
| -32004 | Unauthorized | 401 |
| -32005 | Forbidden | 403 |
| -32006 | Rate limit | 429 |

**项目扩展错误码**（L2-1 定义 + L2-4 实现）：

| Code | 含义 | HTTP Status |
|------|------|-------------|
| -32400 | `KNOWLEDGE_SCOPE_NOT_FOUND` | 404 |
| -32401 | `KNOWLEDGE_ITEM_NOT_FOUND` | 404 |
| -32402 | `KNOWLEDGE_VERSION_NOT_FOUND` | 404 |
| -32403 | `KNOWLEDGE_QUERY_TOO_LONG` | 400 |
| -32404 | `KNOWLEDGE_INVALID_TYPE` | 400 |
| -32405 | `KNOWLEDGE_FORBIDDEN` | 403 |
| -32406 | `KNOWLEDGE_INTERNAL_ERROR` | 500 |
| -32500 | `MEMORY_SCOPE_NOT_FOUND` | 404 |
| -32501 | `MEMORY_INVALID_CONTENT` | 400 |
| -32502 | `MEMORY_FORBIDDEN` | 403 |
| -32503 | `MEMORY_RATE_LIMIT` | 429 |
| -32504 | `MEMORY_QUERY_TOO_BROAD` | 400 |
| -32505 | `MEMORY_INTERNAL_ERROR` | 500 |

### 7.3 Python 实现

```python
# packages/a2a-core/src/superteam_a2a/a2a/errors.py
from enum import IntEnum


class StandardRpcError(IntEnum):
    """JSON-RPC 标准错误码 + 项目扩展错误码。"""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    TASK_NOT_FOUND = -32001
    TASK_TIMEOUT = -32002
    TASK_CANCELLED = -32003
    UNAUTHORIZED = -32004
    FORBIDDEN = -32005
    RATE_LIMIT = -32006

    # 项目扩展（ADR-0002 + ADR-0003）
    KNOWLEDGE_SCOPE_NOT_FOUND = -32400
    KNOWLEDGE_ITEM_NOT_FOUND = -32401
    KNOWLEDGE_VERSION_NOT_FOUND = -32402
    KNOWLEDGE_QUERY_TOO_LONG = -32403
    KNOWLEDGE_INVALID_TYPE = -32404
    KNOWLEDGE_FORBIDDEN = -32405
    KNOWLEDGE_INTERNAL_ERROR = -32406
    MEMORY_SCOPE_NOT_FOUND = -32500
    MEMORY_INVALID_CONTENT = -32501
    MEMORY_FORBIDDEN = -32502
    MEMORY_RATE_LIMIT = -32503
    MEMORY_QUERY_TOO_BROAD = -32504
    MEMORY_INTERNAL_ERROR = -32505
```

---

## 8. Discovery 与 Client（K8s-native）

### 8.1 Discovery 路径

**In-Cluster**：
- 目标 Agent Service：`{agent-name}.{namespace}.svc.cluster.local:8080`
- 路径：`/.well-known/agent.json`（Agent Card 拉取）

**EndpointSlice watch**：
- L2-1 启动时 list + watch 集群 `EndpointSlice`（label selector: `superteam-a2a.io/component=agent`）
- in-memory cache：`(namespace, name) -> [(ip, port, ready)]`
- watch invalidation：K8s watch 触发，毫秒级更新

**DNS fallback**：
- `socket.getaddrinfo` 用于纯客户端路径

### 8.2 A2AClient

```python
# packages/a2a-core/src/superteam_a2a/a2a/client/client.py
# 示意
import httpx
from anyio import fail_after
from superteam_a2a.a2a.upstream import AgentCard, Message, Task
from superteam_a2a.a2a.client.retry import RetryPolicy
from superteam_a2a.a2a.client.circuit_breaker import CircuitBreaker


class A2AClient:
    """A2A 协议客户端（基于 httpx.AsyncClient）。
    
    单进程单实例（进程级连接池复用）。
    所有请求必须有 timeout；受 retry / circuit breaker 保护。
    """
    
    def __init__(
        self,
        ssl_context: ssl.SSLContext,
        retry_policy: RetryPolicy = RetryPolicy(),
        circuit_breaker: CircuitBreaker = CircuitBreaker(),
        request_timeout: float = 30.0,
    ):
        self._http = httpx.AsyncClient(
            timeout=request_timeout,
            verify=ssl_context,  # mTLS 校验
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
        self._retry = retry_policy
        self._cb = circuit_breaker
    
    async def send_message(self, target: str, message: Message) -> Task:
        return await self._cb.call(
            lambda: self._retry.call(
                lambda: self._http.post(
                    f"https://{target}/a2a/jsonrpc",
                    json={
                        "jsonrpc": "2.0",
                        "id": str(uuid4()),
                        "method": "a2a.sendMessage",
                        "params": {"message": message.model_dump(by_alias=True)},
                    },
                )
            )
        )
    
    async def aclose(self):
        await self._http.aclose()
```

### 8.3 Retry / Circuit Breaker / P2C（ADR-0005 §3.2 业务模块职责）

| 关注点 | 实现 |
|--------|------|
| **Retry** | `tenacity`；指数退避；method idempotency gate（`sendMessage` / `getTask` 可重试；`recordMemory` 不可重试除非 idempotency key） |
| **Circuit Breaker** | 三态（CLOSED / OPEN / HALF_OPEN）；失败阈值 / 恢复超时 / HALF_OPEN probe |
| **P2C** | 多个 A2AClient target 时 Power of Two Choices 负载均衡；K8s EndpointSlice 多 endpoint 选取 |
| **限流** | Token bucket；每 Agent 默认 100 RPS；Helm values 可配 |

---

## 9. 可观测性（Python 全栈 · 沿用 v0.1 metric name）

### 9.1 Prometheus 指标（与 L1 v0.2.0 Spec §16 完全一致）

L2-1 模块**只产出**A2A 指标 + Python runtime 指标；不重定义既有指标。

| 指标 | 类型 | Labels | L2-1 触发点 |
|------|------|--------|-------------|
| `superteam_a2a_rpc_total` | Counter | `agent`, `method`, `status` | server middleware（每个 method 调用） |
| `superteam_a2a_rpc_duration_seconds` | Histogram | `agent`, `method` | server middleware |
| `superteam_a2a_active_streams` | Gauge | — | SSE handler（v0.5+） |
| `superteam_python_event_loop_lag_seconds` | Histogram | `component` | §6.3 后台 task |
| `superteam_python_thread_offload_queue_depth` | Gauge | `pool` | anyio limiter stats |
| `superteam_python_active_asyncio_tasks` | Gauge | — | `len(asyncio.all_tasks())` 采样 |
| `superteam_python_gc_collections_total` | Counter | `generation` | `gc.get_stats()` 采样 |

### 9.2 Trace（OpenTelemetry Python SDK）

```python
# packages/a2a-core/src/superteam_a2a/a2a/observability/tracing.py
# 示意
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


_provider: TracerProvider | None = None


def init_tracing(component: str, otlp_endpoint: str | None = None) -> TracerProvider:
    """显式 provider 注入；测试用独立 provider 避免污染全局。"""
    global _provider
    _provider = TracerProvider(resource={"service.name": f"superteam-a2a-{component}"})
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=False)
        _provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(_provider)
    return _provider


def tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)
```

**Span 结构**（与 L1 Architecture §9.2 一致）：
```
A2A RPC
  ├── Adapter.Translate
  ├── Agent.Run
  │     ├── LLM Call
  │     └── MCP Tool Call
  └── Adapter.TranslateBack
```

**Traceparent 透传**：通过 A2A Message `metadata` 注入 `traceparent`；W3C Trace Context。

### 9.3 日志（structlog + stdlib logging）

```python
# packages/a2a-core/src/superteam_a2a/a2a/observability/logging.py
# 示意
import structlog


def configure_structlog(level: str = "INFO") -> None:
    """JSON 输出；保留 trace / agent / task / namespace 字段；敏感内容禁记。"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(__import__("logging"), level)),
        cache_logger_on_first_use=True,
    )
```

**必含字段**：`trace_id` / `agent` / `method` / `task_id` / `namespace` / `ts`（与 L1 Spec §9.3 一致）。

**禁忌**（ADR-0005 §10）：不打印 API Key / Token / 用户数据 / Memory content / Knowledge body。

---

## 10. 上游追踪责任（宪法 §13.6 + ADR-0005 §13.6）

### 10.1 维护责任

L2-1 维护者必须：
- ✅ **每 minor release** 检查 `a2aproject/a2a-python` changelog；评估兼容性
- ✅ **每次 SDK 升级** 跑完整 conformance suite + 项目 contract test
- ✅ **每次 SDK 升级** 评估 `protocolVersion` 变化与 L1 协议版本基线（v0.3）
- ✅ **跟踪 a2aproject/A2A 主仓库** 规范变化；与 L1 Architecture §7.1 协议版本基线对齐
- ✅ **Kopf 兼容性**（Operator Core 模块依赖项）：L2-1 不直接依赖 Kopf；耦合点在 Operator Core 模块（L2-2）

### 10.2 contract test 套件（防止 silent break）

```python
# tests/contract/test_a2a_python_compat.py
# 示意，完整在 L3-2 Spec
import pytest
from pydantic import TypeAdapter
from superteam_a2a.a2a.upstream import AgentCard, Message, Task
from a2a.types import AgentCard as SdkAgentCard  # 用于对比

# 关键 contract：
# 1. JSON wire shape（camelCase）与 v0.1.0 完全一致
# 2. 错误码语义不变
# 3. Pydantic JSON Schema 与 SDK 原生 schema 兼容
# 4. 时间格式 RFC 3339

def test_agent_card_wire_shape():
    card = AgentCard(name="hello-agent", ...)
    dumped = card.model_dump(by_alias=True, mode="json")
    assert dumped == {"name": "hello-agent", ...}  # 与 v0.1.0 完全一致


def test_jsonrpc_envelope_compat():
    # 验证 envelope 字段与 SDK / v0.1.0 一致
    ...
```

### 10.3 upgrade 决策

- **patch 升级**（0.3.x → 0.3.x+1）：自动（通过 contract test）
- **minor 升级**（0.3.x → 0.4.0）：跑完整 conformance + E2E + 评估 API 变更；不破坏 wire 时直接升级
- **major 升级**（0.x → 1.0）：**走 ADR**；评估 protocolVersion 升级 + wire 不变性

---

## 11. 测试策略（ADR-0005 §11 + 宪法 §9）

### 11.1 测试层级

| 层级 | 工具 | 覆盖目标 | 关键场景 |
|------|------|----------|----------|
| **Unit** | `pytest` + `pytest-asyncio` + `respx` | ≥ 90%（协议类型 / 错误模型 / 状态机） | Pydantic 校验 / JSON-RPC envelope / 错误码映射 / mTLS context / 路由分发 |
| **Property** | `Hypothesis` + `hypothesis-jsonschema` | envelope / schema / FSM | 任意 JSON-RPC request 不崩溃；wire 序列化反序列化 round-trip |
| **HTTP** | `respx` / ASGI test client | timeout / 取消 / 重试 / mTLS 失败 | httpx mock + 各种失败路径 |
| **SDK compat** | 自研 contract test + SDK 自带 conformance | wire shape + 错误码 + envelope | 锁定 v0.1.0 wire；minor 升级跑过 |
| **Operator IT** | kind + `kubernetes_asyncio` 真实 watch | reconcile / webhook / leader failover | ADR-0005 §7 12 项门禁（适用 L2-2） |
| **E2E** | kind + Helm | Hello Agent + Workflow + Knowledge + Memory 全链路 | 完整业务流程 |

### 11.2 conformance 套件接入（ADR-0005 §11.2）

- SDK 提供 `a2a.conformance` 子包（待 L3-2 实测具体路径）
- CI 必跑：`pytest tests/conformance -v`
- 标准 method 100% 覆盖

### 11.3 性能预算（L1 v0.2.0 Architecture §11.5 · L2-1 关注项）

| 指标 | 目标值 | 测量 |
|------|--------|------|
| 1 KiB A2A loopback p50/p95/p99 | < 5ms / < 20ms / < 50ms | `pytest-benchmark` |
| Pydantic validation overhead | < 1ms | `pytest-benchmark` |
| Agent Card cache hit | < 0.5ms | `pytest-benchmark` |
| EndpointSlice watch invalidation | < 100ms | kind E2E |

**触发升级决策**（ADR-0005 §12.2）：profile → 减少分配 → 连接池 / cache / batch → Pod 扩容 → ADR。

---

## 12. 验收清单（v0.2 · Python-first）

> L2-1 v0.2 设计被认定为"通过"必须满足

### 12.1 模块完整性（与 v0.1.0 一致）

- [ ] 6 个 A2A method 全部覆盖（2 标准 SDK + 4 项目扩展 router）
- [ ] Agent Card 服务于 `/.well-known/agent.json`
- [ ] mTLS 透明（cert-manager mounted cert → ssl.SSLContext）
- [ ] SPIFFE URI SAN 解析（`py-spiffe` 实测后启用或回退）
- [ ] K8s Service / DNS / EndpointSlice Discovery
- [ ] Retry + Circuit Breaker + P2C + 限流
- [ ] conformance suite 接入
- [ ] contract test 套件建立（wire shape + 错误码 + envelope 锁定）

### 12.2 Python-first 硬约束（ADR-0005 + 宪法 v0.5.0）

- [ ] **wire contract 与 v0.1.0 完全一致**（JSON 字段 / 错误码 / Agent Card 路径 / 任务状态机 / metric name）
- [ ] **官方 `a2a-sdk` 复用 + `superteam_a2a.a2a.upstream` boundary**（lint 检测禁止业务层直接 import SDK）
- [ ] **compatibility adapter router 不修改 / 不 fork SDK**（4 个项目扩展 method 通过 Starlette sub-app 注入）
- [ ] **async-first**：所有 K8s I/O / A2A HTTP / OTel 异步
- [ ] **CPU offload**：`anyio.to_thread.run_sync` 限定场景
- [ ] **单进程原则**：Uvicorn 单 worker + 单 event loop；Helm `python.workers: 1` 强制
- [ ] **timezone-aware UTC**：所有 datetime 字段
- [ ] **Pydantic v2 strict** 公共边界（无未解释 `Any`）
- [ ] **uv.lock 必须提交**；CI `uv sync --frozen`
- [ ] **Python 静态门禁**（CI 必跑）：Ruff + Pyright strict + Bandit + pip-audit

### 12.3 可观测性 / 安全 / 性能

- [ ] Prometheus 指标覆盖（7 个 A2A + 4 个 Python runtime）
- [ ] OpenTelemetry Trace（W3C Traceparent 透传）
- [ ] structlog JSON 日志（敏感内容禁记）
- [ ] Python 镜像非 root + read-only rootfs + drop all capabilities
- [ ] 性能预算满足（L1 §11.5）

### 12.4 上游追踪

- [ ] `a2aproject/a2a-python` 维护责任明确
- [ ] upgrade 决策树（patch / minor / major）
- [ ] contract test 套件已建立

### 12.5 与其他文档一致性

- [ ] 与 L1 Architecture v0.2.0 §3.4 / §7 一致
- [ ] 与 L1 Spec v0.2.0 §5 / §15 一致
- [ ] 与 ADR-0005 §3.2 / §8 / §9 一致
- [ ] 与宪法 v0.5.0 §3.8 / §9.7 / §13.6 一致
- [ ] MVP 例外 §14.5 显式声明（v0.1 阶段适用）

---

## 13. 开放问题（移交 L3-2 Spec / v0.5+）

> L2-1 设计未定项；L3-2 Spec 重写时**必须**收敛

1. **a2a-python 精确 PyPI 包名**（U-1）：L3-2 `pip index versions a2a-*`
2. **`requires-python` 精确下限**（U-2）：L3-2 `pip show` + CI matrix
3. **conformance 套件 import 路径 / 入口命令**（U-3）：L3-2 实测
4. **`py-spiffe` Workload API 兼容性**（U-4）：ADR-0005 §9.1 回退路径已规划
5. **SDK ASGI server method-level 中间件支持**（U-5）：L3-2 实测
6. **jsonrpc_app 内部结构**：L3-2 需读取源码确认 envelope 校验 / 中间件 hook
7. **Python SPIFFE 库生态稳定性**：除 `py-spiffe` 外是否有更成熟选项？L3-2 评估
8. **Uvicorn 证书热更新**：`--reload` vs 自定义 `ssl.SSLContext` reload？L3-2 决策
9. **Otel ASGI middleware 与 SDK 兼容性**：L3-2 实测是否需要自定义中间件
10. **httpx AsyncClient 与 SDK client 关系**：SDK 是否直接使用 httpx？L3-2 确认是否需要自定义 client 包装

---

## 14. 下一步

L2-1 v0.2-draft 通过评审后，升级到 v0.2.0；进入 L2-1 Python Spec 重写：

1. **L2-1 Spec v0.2-draft**：`docs/spec/L2-module-specs/L2-a2a-protocol.md`
   - 7 个 Python 子包文件清单
   - 4 个 ExtensionRouter 完整 Pydantic Request/Response schema
   - compatibility adapter 完整 Python 代码契约
   - mTLS `ssl.SSLContext` 构造 + 热更新实现路径
   - Discovery + Retry + Circuit Breaker + P2C 完整 Python 代码契约
   - Helm values 完整 schema
   - 测试 ID 完整清单
   - 生命周期契约
2. **L2-1 v0.2 Python 评审**：`docs/reviews/l2-1-a2a-protocol-review.md`（10 维度）
3. **进入 L2-2 Operator Core Python 重写**

**建议拆分双会话**避免 §16.1：本会话已完成 L2-1 设计（≈ 25-30KB / ~600 行），下次会话从 L2-1 Spec 起草起手。

---

> **状态**：✅ v0.2.0 已评审通过（2026-07-24；10 维度全 PASS · 详见 [l2-1-a2a-protocol-review.md](../../reviews/l2-1-a2a-protocol-review.md)）
> **supersedes**：v0.1.0 Go baseline（仅 supersede Go struct / Go package / Go HTTP server / Go JSON-RPC envelope 实现条款；wire contract 与业务语义继续有效）
> **下一步**：跨文档同步（下次会话）→ L2-2 Operator Core Python 重写（先归档 Go Design 到 `docs/archive/pre-python-2026-07-24/`）
> **评审者**：项目发起人（基于单人维护者 + MVP 例外 14.5 单点评审）
> **变更摘要**（2026-07-24 · v0.1.0 → v0.2-draft 增量）：
> - **+1 ADR-0008**（a2a-python spike 9 项结论 + 5 项已知未决）
> - **+1 boundary**：superteam_a2a.a2a.upstream（官方 SDK 唯一 import 入口；业务层禁直接 import）
> - **+1 protocol**：ExtensionRouter Protocol（@router.register 自定义 method 注册）
> - **+1 兼容性架构**：compatibility adapter（不修改 / 不 fork SDK；4 个扩展 method 通过 Starlette sub-app 注入）
> - **+5 子包**：server / client / extensions / mtls / observability
> - **+3 single source**：upstream_types / errors / _internal
> - **新增** §5 单进程原则（Uvicorn 1 worker / 1 event loop；Helm values python.workers: 1 强制）
> - **新增** §5.4 优雅停机（SIGTERM 顺序：readiness=false → drain → flush → close）
> - **新增** §6 async-first + CPU offload + event-loop lag 监控
> - **新增** §7 项目扩展错误码 Python enum（与 L1 Spec §5.7 数字一致）
> - **新增** §8.2 A2AClient（httpx.AsyncClient + 连接池 + Retry + Circuit Breaker）
> - **新增** §10.2 contract test 套件（wire shape 锁定 + SDK minor 升级自动化）
> - **新增** §13 10 项开放问题（移交 L3-2 Spec 与 v0.5+）