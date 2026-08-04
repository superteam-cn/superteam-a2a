# L2 模块规格：A2A Protocol（v0.2 · Python-first）

> **层级**：L2 — 模块 Spec
> **模块 ID**：C-2（A2A Core Library，见 L1 v0.2.0 Architecture §4.1）
> **代码位置**：`packages/a2a-core/src/superteam_a2a/a2a/`（**Python-first · ADR-0005 §13 工程布局**）
> **版本**：**v0.2.0**（**Python 重写 · ADR-0005 触发**；2026-07-24 评审通过）
> **状态**：✅ **已评审通过**（依据 [`docs/reviews/l2-1-a2a-protocol-review.md`](../../reviews/l2-1-a2a-protocol-review.md) 2026-07-24；10 维度全 PASS）
> **配套设计**：[`docs/design/L2-modules/L2-a2a-protocol.md`](../../design/L2-modules/L2-a2a-protocol.md) **v0.2.0**（同日同步评审通过）
> **配套评审**：[`docs/reviews/l2-1-a2a-protocol-review.md`](../../reviews/l2-1-a2a-protocol-review.md)（✅ 2026-07-24；10 维度全 PASS）
> **supersedes**：v0.1.0 Go baseline（[`docs/spec/L2-module-specs/L2-a2a-protocol.md`](../../spec/L2-module-specs/L2-a2a-protocol.md) 2026-07-23 通过；**仅 supersede Go struct / Go package / Go HTTP server / Go JSON-RPC envelope 实现条款；wire contract（A2A JSON-RPC / 6 method 字段 / Agent Card 路径 / 错误码 / 任务状态机 / metric name）继续有效**）
> **依据**：[`CONSTITUTION.md`](../../../CONSTITUTION.md) **v0.5.0** §3.8 Python-first + §6 mTLS + §7 可观测性 + §9.7 静态质量 + §13.6 维护 A2A Python SDK；[ADR-0005](../../adr/0005-python-first-technology-stack.md) §3.2 A2A Core 模块映射 + §8 SDK 门禁 + §9.1 mTLS；[L1 Architecture v0.2.0](../L1-architecture.md) §3.4 + §7 + §9.2；[L1 Spec v0.2.0](../../spec/L1-system-spec.md) §5 + §15 + §16
> **MVP 例外**：§14.5 适用

---

## 0. 阅读指南

本文档定义 `superteam-a2a` **L2-1 A2A Protocol 模块**（通信层 · C-2）的 **Python 文件级契约**：7 个子包的完整文件清单、4 个 ExtensionRouter 的 Pydantic schema、`ssl.SSLContext` 构造 + 热更新路径、Discovery/Retry/CB/P2C 完整契约、Helm values schema、测试 ID 矩阵、生命周期时序、Python-first 硬约束验收。**不**重复设计决策的"为什么"（见配套设计 v0.2-draft）；**不**定义每个函数的具体实现（L3-2 文件级 Spec 负责）。

> **下游落地**：[L3-2 A2A Core Library 文件级 Spec v0.2.0](../../file-specs/L3-a2a-core.md)（2026-07-28 #54 评审通过 · 2852 行 / 160KB / 30 文件 + 9 Helm + 30 测试 / 276 测试 ID / 24 错误码 / 15 指标；[评审报告](../../reviews/l3-2-a2a-core-spec-review.md) §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项）

**读者**：L3-2 Spec 作者、Adapter SDK 作者、Knowledge Service / Memory backend 作者、架构评审者。

**与 L2-1 设计的边界**：

| L2-1 设计文档（v0.2-draft） | L2-1 Spec 文档（本） |
|------------------------------|----------------------|
| 概念 / 架构图 / 选型理由 / 包布局概念 | 文件清单 / 函数签名 / 默认值 / Pydantic schema |
| 状态机图 + 守卫规则 | Pydantic state model + 测试用例 ID 矩阵 |
| 错误码名单（数字） | 错误码 → Python enum + wire JSON + Retryable 矩阵 |
| 关键算法文字描述 | 算法接口签名 + 输入/输出契约 |
| 边界规则叙述 | boundary lint 规则 + 检测点 |

**wire contract 不变性**（与 v0.1.0 Go baseline 完全一致，contract test 锁定）：

- JSON 字段名 / camelCase / 时间格式 RFC 3339 / 错误码语义
- Agent Card 路径 `GET /.well-known/agent.json`
- 方法路径 `POST /a2a/jsonrpc`
- 7 个 A2A + 4 个 Python runtime Prometheus 指标名
- 6 个 v0.1 method（`sendMessage` / `getTask` + 4 个扩展）+ 1 个项目保留 `cancelTask` 占位（v0.5+ 启用）

---

## 1. 模块概述

### 1.1 使命与边界

L2-1 是 `superteam-a2a` 通信层的唯一实现。完整使命陈述、系统边界、价值主张见配套设计 v0.2-draft §1。

**模块内**（v0.2 Python-first · 本 Spec 详述）：
- 官方 `a2a-sdk` envelope / types / ASGI server / async client 的复用与边界封装
- 4 个项目扩展 method 的 router 注册
- mTLS / SPIFFE / 证书热更新（Python `ssl.SSLContext`）
- Discovery：K8s Service / DNS / EndpointSlice watch + Agent Card 拉取
- 客户端：重试 + 退避 + 熔断 + P2C + connection pool
- 业务授权 / 限流 / 指标 / Trace / 结构化日志
- 项目私有 DTO（Pydantic v2 strict）
- conformance suite 接入与 contract test

**系统外**：Agent 框架逻辑 / 业务语义（Knowledge 检索、Memory 衰减）/ CRD 生命周期 / LLM Provider / MCP Server / 跨集群联邦 / A2A Stream（v0.5+）。

### 1.2 模块对外契约（public API surface）

```python
# packages/a2a-core/src/superteam_a2a/a2a/__init__.py
"""A2A Core Library — communication layer of superteam-a2a.

Public surface: re-export upstream types + 4 routers + factory functions.
All business modules import from here, never from `a2a` directly.
"""

from superteam_a2a.a2a.upstream import (
    # SDK re-exports（仅枚举，禁止业务层绕过）
    AgentCard,
    Message,
    Part,
    Task,
    Artifact,
    TaskState,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
)
from superteam_a2a.a2a.upstream_types import (
    # 项目私有 DTO
    QueryKnowledgeRequest,
    QueryKnowledgeResponse,
    GetKnowledgeItemRequest,
    GetKnowledgeItemResponse,
    RecordMemoryRequest,
    RecordMemoryResponse,
    QueryMemoryRequest,
    QueryMemoryResponse,
)
from superteam_a2a.a2a.server.app import create_app
from superteam_a2a.a2a.client.client import A2AClient
from superteam_a2a.a2a.errors import StandardRpcError, ProjectRpcError
from superteam_a2a.a2a.mtls import MtlsConfig, build_server_ssl_context, extract_spiffe_id
from superteam_a2a.a2a.extensions import (
    ExtensionRouter,
    QueryKnowledgeRouter,
    GetKnowledgeItemRouter,
    RecordMemoryRouter,
    QueryMemoryRouter,
)
```

**boundary 强制**（ADR-0005 §3.2 + 宪法 §3.8）：
- 业务层（Knowledge Service / MemoryReconciler / Operator / Adapter SDK）**禁止**直接 `import a2a`
- 仅允许 `from superteam_a2a.a2a import ...`
- CI 通过自定义 Ruff 规则 `ST-A2A-BOUNDARY` 检测（见 §11.4）

---

## 2. 包结构与文件清单

### 2.1 完整文件清单（7 子包 + 3 single-source）

```
packages/a2a-core/src/superteam_a2a/a2a/
├── __init__.py                                  # public surface（§1.2）
├── upstream.py                                  # ⚠️ boundary — SDK 唯一 import 入口
├── upstream_types.py                            # 项目私有 Pydantic DTO（§3.4）
├── errors.py                                    # StandardRpcError + ProjectRpcError（§8）
├── server/
│   ├── __init__.py
│   ├── app.py                                   # create_app() — ASGI 工厂
│   ├── middlewares.py                           # 4 个 ASGI middleware
│   └── lifespan.py                              # asynccontextmanager 生命周期（§13）
├── client/
│   ├── __init__.py
│   ├── client.py                                # A2AClient（§5.4）
│   ├── retry.py                                 # RetryPolicy（Tenacity wrapper）
│   ├── circuit_breaker.py                       # CircuitBreaker + P2C selector
│   ├── discovery.py                             # K8s + DNS + Agent Card 缓存
│   └── agent_card_cache.py                      # TTL cache + invalidation
├── extensions/
│   ├── __init__.py                              # 4 个 router re-export
│   ├── base.py                                  # ExtensionRouter Protocol
│   ├── query_knowledge.py                       # 占位 + 接口（实现由 L2-4 提供）
│   ├── get_knowledge_item.py                    # 占位 + 接口
│   ├── record_memory.py                         # 占位 + 接口
│   └── query_memory.py                          # 占位 + 接口
├── mtls/
│   ├── __init__.py
│   ├── ssl_context.py                           # build_server_ssl_context（§4.2）
│   ├── spiffe.py                                # extract_spiffe_id（§4.3）
│   └── hot_reload.py                            # 证书热更新（§4.4）
├── observability/
│   ├── __init__.py
│   ├── metrics.py                               # Prometheus 7+4 指标（§9.1）
│   ├── tracing.py                               # OTel provider 注入（§9.2）
│   ├── logging.py                               # structlog setup（§9.3）
│   └── event_loop.py                            # event-loop lag 监控（§7.3）
├── utils/
│   ├── __init__.py
│   └── offload.py                               # anyio.to_thread.run_sync（§7.2）
└── _internal/                                   # ⚠️ private — 业务层禁 import
    ├── __init__.py
    └── _wire.py                                 # 内部 wire helpers
```

**文件计数**：7 子包 + `__init__.py` = 32 个 `.py` 文件（含 1 个 private `_internal/`）。

### 2.2 边界规则（与 Design §3.2 一致 · ADR-0005 §3.2）

| 层 | 模块 | 允许 import | 禁止 import |
|----|------|-------------|-------------|
| 边界层 | `a2a.upstream` | `a2a.*`（官方 SDK） | 业务层任何符号 |
| 项目核心 | `a2a.*`（server/client/extensions/mtls/observability/errors） | `a2a.upstream` | 业务层符号 |
| 业务层 | Knowledge Service / MemoryReconciler / Operator / Adapter | `superteam_a2a.a2a.*`（经 `__init__.py` re-export） | `a2a.*`（裸 SDK import） |

**lint 规则**：自定义 Ruff 规则 `ST-A2A-BOUNDARY`（§11.4）扫描 `import a2a` / `from a2a import` 模式；命中即失败。

---

## 3. compatibility adapter（4 个项目扩展 method）

### 3.1 架构（与 Design §4.2 一致）

```
Starlette App
├── Mount("/") → SDK jsonrpc_app       # sendMessage / getTask / cancelTask
├── Mount("/") → extension sub-app    # queryKnowledge / getKnowledgeItem / recordMemory / queryMemory
├── Route("/.well-known/agent.json")  # SDK 提供
├── Route("/healthz")                 # L2-1 liveness
├── Route("/readyz")                  # L2-1 readiness
└── Route("/metrics")                 # Prometheus exposition
```

### 3.2 ExtensionRouter Protocol（占位协议 · 实现由 L2-4 Knowledge/Memory 提供）

```python
# packages/a2a-core/src/superteam_a2a/a2a/extensions/base.py
from typing import Protocol, runtime_checkable
from superteam_a2a.a2a.upstream import JSONRPCRequest, JSONRPCResponse, JSONRPCError


@runtime_checkable
class ExtensionRouter(Protocol):
    """项目扩展 method router 协议。

    L2-1 通过 inspect 找出所有实现类；L2-4 Knowledge/Memory 模块
    提供具体实现（QueryKnowledgeRouter 等）。
    """

    method_name: str  # e.g. "a2a.queryKnowledge"

    async def handle(self, request: JSONRPCRequest) -> JSONRPCResponse | JSONRPCError:
        """处理单个 JSON-RPC 请求；返回响应或错误。"""
        ...
```

### 3.3 4 个扩展 method 的 Pydantic schema（项目私有 DTO）

#### 3.3.1 `a2a.queryKnowledge`

```python
# packages/a2a-core/src/superteam_a2a/a2a/upstream_types.py
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class KnowledgeScopeLevel(StrEnum):
    """4 级 scope（ADR-0002 §3）。"""

    INDUSTRY = "industry"
    ORGANIZATION = "organization"
    TEAM = "team"
    PROJECT = "project"


class QueryKnowledgeRequest(BaseModel):
    """a2a.queryKnowledge 请求 params。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )
    query: str = Field(min_length=1, max_length=2048)
    scope_level: KnowledgeScopeLevel
    scope_id: str = Field(min_length=1, max_length=253)
    agent_id: str = Field(min_length=1, max_length=253)  # 用于 agent-private 维度
    top_k: int = Field(default=10, ge=1, le=100)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    include_body: bool = False  # True 时返回 KnowledgeItem body（>10KB 触发截断）
    traceparent: str | None = None  # W3C Trace Context 透传


class KnowledgeItemSummary(BaseModel):
    """查询结果条目（不含 body）。"""

    item_id: str
    title: str
    scope_level: KnowledgeScopeLevel
    scope_id: str
    score: float
    snippet: str | None = None  # 前 200 字符
    updated_at: datetime
    version: int


class QueryKnowledgeResponse(BaseModel):
    """a2a.queryKnowledge 响应 result。"""

    items: list[KnowledgeItemSummary]
    total: int
    next_cursor: str | None = None  # 分页游标（base64 opaque）
```

#### 3.3.2 `a2a.getKnowledgeItem`

```python
class GetKnowledgeItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_id: str = Field(min_length=1, max_length=253)
    version: int | None = None  # None → latest
    traceparent: str | None = None


class GetKnowledgeItemResponse(BaseModel):
    item_id: str
    title: str
    body: str  # markdown / 原始文本；>10KB 截断并设置 truncated=True
    truncated: bool = False
    mime_type: str = "text/markdown"
    scope_level: KnowledgeScopeLevel
    scope_id: str
    agent_private_owner: str | None  # agent-private 维度持有者
    version: int
    created_at: datetime
    updated_at: datetime
```

#### 3.3.3 `a2a.recordMemory`

```python
class MemoryContentType(StrEnum):
    FACT = "fact"
    PREFERENCE = "preference"
    SKILL = "skill"
    CONTEXT = "context"


class RecordMemoryRequest(BaseModel):
    """a2a.recordMemory 请求 params。

    idempotency_key 必填 — ADR-0003 §6 + L2-4 Design §6.2 要求
    recordMemory 不可重试除非 idempotency key。
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    idempotency_key: str = Field(min_length=8, max_length=128)
    scope_level: KnowledgeScopeLevel
    scope_id: str = Field(min_length=1, max_length=253)
    agent_id: str = Field(min_length=1, max_length=253)  # Memory 持有者
    content_type: MemoryContentType
    content: str = Field(min_length=1, max_length=8192)
    confidence: float = Field(ge=0.0, le=1.0)
    referenced_items: list[str] = Field(default_factory=list, max_length=32)
    referenced_task_id: str | None = None
    traceparent: str | None = None

    @field_validator("idempotency_key")
    @classmethod
    def _validate_key_format(cls, v: str) -> str:
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("idempotency_key must be alphanumeric + -/_")
        return v


class RecordMemoryResponse(BaseModel):
    memory_id: str
    recorded_at: datetime
    expires_at: datetime  # decay 公式计算；详见 L2-4 Design §6.3
```

#### 3.3.4 `a2a.queryMemory`

```python
class MemoryVisibility(StrEnum):
    """5 维矩阵 = scope_level (4) × agent_private (orthogonal)。

    effective_visibility 计算：
    - inherited：scope 继承规则（见 L2-4 Design §5）
    - agent_private：仅 agent_id 自己可见
    """

    INHERITED = "inherited"
    AGENT_PRIVATE = "agent-private"


class QueryMemoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    query: str = Field(min_length=1, max_length=2048)
    scope_level: KnowledgeScopeLevel | None = None  # None → 全 scope
    scope_id: str | None = None
    agent_id: str = Field(min_length=1, max_length=253)  # 必须：决定私有维度
    visibility: MemoryVisibility = MemoryVisibility.INHERITED
    content_types: list[MemoryContentType] | None = None
    min_confidence: float = Field(default=0.3, ge=0.0, le=1.0)
    top_k: int = Field(default=20, ge=1, le=100)
    include_expired: bool = False  # True → 返回已 decay 的（仅审计）
    traceparent: str | None = None


class MemorySummary(BaseModel):
    memory_id: str
    content_preview: str  # 前 100 字符
    content_type: MemoryContentType
    confidence: float
    scope_level: KnowledgeScopeLevel
    scope_id: str
    agent_id: str  # 持有者
    visibility: MemoryVisibility
    created_at: datetime
    expires_at: datetime
    decay_score: float  # 当前 effective score


class QueryMemoryResponse(BaseModel):
    memories: list[MemorySummary]
    total: int
    next_cursor: str | None = None
```

### 3.4 router 注册流程

```python
# packages/a2a-core/src/superteam_a2a/a2a/extensions/__init__.py
from importlib import import_module
from inspect import isclass
from pkgutil import iter_modules
from .base import ExtensionRouter

_DISCOVERED: dict[str, ExtensionRouter] = {}


def discover_routers(package: str = "superteam_a2a.a2a.extensions") -> None:
    """通过 pkgutil + inspect 找出所有 ExtensionRouter 实现类。

    实现约束：
    - 必须定义类属性 method_name: str
    - 必须实现 async handle(JSONRPCRequest) -> JSONRPCResponse | JSONRPCError
    - 不允许重复 method_name（启动期 ValueError）
    """
    for module_info in iter_modules(__path__, prefix=f"{package}."):
        module = import_module(module_info.name)
        for name in dir(module):
            obj = getattr(module, name)
            if isclass(obj) and obj is not ExtensionRouter and issubclass(obj, ExtensionRouter):
                if obj.method_name in _DISCOVERED:
                    raise ValueError(f"duplicate router method_name: {obj.method_name}")
                _DISCOVERED[obj.method_name] = obj()


def dispatch(request: JSONRPCRequest) -> JSONRPCResponse | JSONRPCError:
    """根据 request.method 分发到对应 router。

    未注册 method 返回 JSONRPCError(code=-32601, message="Method not found")。
    """
    router = _DISCOVERED.get(request.method)
    if router is None:
        return JSONRPCError(
            id=request.id,
            code=-32601,
            message=f"Method not found: {request.method}",
        )
    return await router.handle(request)
```

**关键不变量**（与 Design §4.5 一致）：
- wire shape：JSON 字段名 / camelCase / 时间格式 RFC 3339 / 错误码语义
- 方法路径：`POST /a2a/jsonrpc`（标准与扩展方法同一路径，由 JSON-RPC `method` 字段分发）
- Agent Card：`GET /.well-known/agent.json`（SDK 标准）

---

## 4. mTLS / SPIFFE（ADR-0005 §9.1 + 宪法 §6.1）

### 4.1 cert-manager 挂载契约

```
Pod
└── /etc/tls/                 # volumeMount: cert-manager Secret
    ├── tls.crt               # server certificate (PEM)
    ├── tls.key               # server private key (PEM)
    └── ca.crt                # client CA bundle (PEM, 用于 mTLS 验证)
```

**文件存在性检查**（启动期）：3 个文件必须存在且非空；缺失 → `MtlsConfigError` + readiness=false。

### 4.2 build_server_ssl_context 契约

```python
# packages/a2a-core/src/superteam_a2a/a2a/mtls/ssl_context.py
import ssl
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class MtlsConfig:
    cert_dir: Path = Path("/etc/tls")
    min_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_3
    verify_mode: ssl.VerifyMode = ssl.CERT_REQUIRED
    spiffe_required: bool = True  # False → 仅校验 cert，不解析 SPIFFE ID


def build_server_ssl_context(config: MtlsConfig = MtlsConfig()) -> ssl.SSLContext:
    """构造 mTLS server SSLContext。

    Returns:
        ssl.SSLContext 配置好的 server context

    Raises:
        MtlsConfigError: cert/key 文件缺失或格式错误
    """
    # 实现契约：见 L3-2 Spec
    ...


class MtlsConfigError(RuntimeError):
    """cert/key 文件缺失或解析失败。"""
```

**约束**：
- 最低 TLS 1.3（`ctx.minimum_version = ssl.TLSVersion.TLSv1_3`）
- 客户端证书必须校验（`ctx.verify_mode = ssl.CERT_REQUIRED`）
- 私钥文件 mode 必须 0600（启动期 `stat.S_IMODE` 检查）
- ALPN 协议：`["h2", "http/1.1"]`（mTLS over HTTP/2 preferred）

### 4.3 extract_spiffe_id 契约

```python
# packages/a2a-core/src/superteam_a2a/a2a/mtls/spiffe.py
from cryptography import x509


def extract_spiffe_id(cert: x509.Certificate) -> str | None:
    """从客户端证书 URI SAN 解析 SPIFFE ID。

    URI 格式：spiffe://<trust_domain>/<path>
    Returns: 完整 SPIFFE ID 字符串 或 None（无 SPIFFE SAN）

    Raises:
        SpiffeIdFormatError: URI 存在但格式非法
    """
    ...


class SpiffeIdFormatError(ValueError):
    """SPIFFE ID 格式非法（不是 spiffe:// 前缀或 path 为空）。"""


def validate_spiffe_id(spiffe_id: str, expected_trust_domain: str) -> None:
    """校验 SPIFFE ID 的 trust_domain 与预期一致。

    Raises:
        SpiffeIdFormatError: trust_domain 不匹配
    """
    if not spiffe_id.startswith(f"spiffe://{expected_trust_domain}/"):
        raise SpiffeIdFormatError(f"SPIFFE ID trust_domain mismatch: {spiffe_id}")
    path = spiffe_id.removeprefix(f"spiffe://{expected_trust_domain}/")
    if not path:
        raise SpiffeIdFormatError("SPIFFE ID path is empty")
```

**SPIFFE ID 格式**（RFC 8414 + ADR-0005 §9.1）：
- scheme：`spiffe://`
- trust_domain：项目默认 `superteam-a2a.local`（Helm values 可配）
- path：`/<agent-namespace>/<agent-name>` 或 `/operator/<operator-name>`

### 4.4 证书热更新契约

```python
# packages/a2a-core/src/superteam_a2a/a2a/mtls/hot_reload.py
from pathlib import Path
import asyncio
import ssl
from anyio import fail_after


class CertWatcher:
    """cert-manager mounted cert 文件变更检测 → 重建 SSLContext。"""

    def __init__(
        self,
        cert_dir: Path = Path("/etc/tls"),
        check_interval_seconds: float = 30.0,
        reload_timeout_seconds: float = 5.0,
    ):
        self._cert_dir = cert_dir
        self._interval = check_interval_seconds
        self._timeout = reload_timeout_seconds
        self._current: ssl.SSLContext | None = None
        self._lock = asyncio.Lock()
        self._on_reload: list[Callable[[ssl.SSLContext], Awaitable[None]]] = []

    async def start(self) -> ssl.SSLContext:
        """启动 watcher；返回初始 SSLContext。

        Raises:
            MtlsConfigError: 初始加载失败
        """
        ...

    async def stop(self) -> None:
        """停止 watcher；幂等。"""
        ...

    def on_reload(self, callback: Callable[[ssl.SSLContext], Awaitable[None]]) -> None:
        """注册 SSLContext 重新加载回调（Uvicorn 替换）。"""
        self._on_reload.append(callback)

    @property
    def current(self) -> ssl.SSLContext:
        """获取当前 SSLContext。"""
        if self._current is None:
            raise RuntimeError("CertWatcher not started")
        return self._current
```

**关键不变量**：
- 检查间隔：默认 30s（Helm values `certWatcher.intervalSeconds` 可配）
- reload timeout：5s（超时则保留旧 context，记 ERROR 日志）
- 文件 mtime 检测：`stat().st_mtime_ns` 与上次对比
- 失败回退：reload 失败时**保留旧 SSLContext**（保证可用性）

### 4.5 与 Uvicorn 集成（§6 配合）

```python
# 启动契约（lifespan 中调用）
async def lifespan(app):
    watcher = CertWatcher(cert_dir=Path("/etc/tls"))
    ssl_context = await watcher.start()
    app.state.ssl_context = ssl_context  # Uvicorn 启动时已绑定

    # 注册替换回调（如 Uvicorn reload SSL — L3-2 实现）
    async def _swap(new_ctx: ssl.SSLContext) -> None:
        # 原子替换；L3-2 实现具体 Uvicorn SSLConfig 替换
        app.state.ssl_context = new_ctx
        logger.info("ssl_context_reloaded")

    watcher.on_reload(_swap)

    try:
        yield
    finally:
        await watcher.stop()
```

---

## 5. Discovery + Client（K8s-native）

### 5.1 Discovery 路径（Design §8.1 展开）

**In-Cluster**：
- 目标 Agent Service：`{agent-name}.{namespace}.svc.cluster.local:8080`
- Agent Card 路径：`GET https://{target}/.well-known/agent.json`

**EndpointSlice watch**：

```python
# packages/a2a-core/src/superteam_a2a/a2a/client/discovery.py
from dataclasses import dataclass
from collections.abc import AsyncIterator


@dataclass(frozen=True)
class Endpoint:
    namespace: str
    name: str  # Service name
    ip: str
    port: int
    ready: bool


@dataclass(frozen=True)
class AgentTarget:
    namespace: str
    name: str
    endpoints: tuple[Endpoint, ...]
    agent_card_url: str  # https://{name}.{namespace}.svc.cluster.local:8080/.well-known/agent.json


class Discovery:
    """K8s Service / EndpointSlice watch + Agent Card 缓存。"""

    LABEL_SELECTOR = "superteam-a2a.io/component=agent"

    def __init__(
        self,
        k8s_client: kubernetes_asyncio.client.CoreV1Api,
        agent_card_ttl_seconds: float = 300.0,
        watch_reconnect_seconds: float = 5.0,
    ): ...

    async def start(self) -> None:
        """启动 EndpointSlice watch；触发首次 list + 后续 watch。"""
        ...

    async def stop(self) -> None:
        """停止 watch；幂等。"""
        ...

    async def list_targets(self, namespace: str | None = None) -> list[AgentTarget]:
        """列出当前所有可达 AgentTarget。

        namespace=None → 所有 namespace（需 RBAC 权限）
        """
        ...

    async def watch_targets(self) -> AsyncIterator[DiscoveryEvent]:
        """watch 事件流（ADDED / MODIFIED / DELETED）。"""
        ...

    async def get_agent_card(self, target: AgentTarget) -> AgentCard:
        """拉取并缓存 Agent Card；TTL 内复用。"""
        ...
```

**关键约束**：
- 启动期 list 一次 → 后续 watch（`resourceVersion` 续传）
- watch reconnect：断连后 backoff 重连，指数退避 1s → 30s
- Agent Card cache：TTL 默认 300s（Helm values 可配）；cache key = `(namespace, name, version)`

### 5.2 DNS fallback

```python
async def resolve_dns(target: str) -> list[str]:
    """socket.getaddrinfo → IP 列表（IPv4 + IPv6）。

    用于无 K8s RBAC 权限的客户端路径（开发环境）。
    """
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(target, 8080, type=socket.SOCK_STREAM)
    return list({i[4][0] for i in infos})
```

### 5.3 A2AClient 契约

```python
# packages/a2a-core/src/superteam_a2a/a2a/client/client.py
import httpx
import ssl
from superteam_a2a.a2a.upstream import AgentCard, Message, Task
from .retry import RetryPolicy
from .circuit_breaker import CircuitBreaker


class A2AClient:
    """A2A 协议客户端（基于 httpx.AsyncClient）。

    单进程单实例（进程级连接池复用）。
    所有请求必须有 timeout；受 retry / circuit breaker 保护。
    """

    DEFAULT_TIMEOUT_SECONDS = 30.0
    DEFAULT_MAX_CONNECTIONS = 100
    DEFAULT_MAX_KEEPALIVE = 20

    def __init__(
        self,
        ssl_context: ssl.SSLContext,
        retry_policy: RetryPolicy | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        request_timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        max_keepalive: int = DEFAULT_MAX_KEEPALIVE,
        discovery: Discovery | None = None,
        metrics: A2aMetrics | None = None,
    ): ...

    async def send_message(self, target: str, message: Message) -> Task:
        """a2a.sendMessage 调用；受 retry + CB 保护。

        Returns: Task（同步调用返回）
        Raises:
            A2ATimeoutError: 超时（retryable）
            A2AMethodError: JSON-RPC error（按 code 判断 retryable）
            CircuitOpenError: 熔断器 OPEN
        """
        ...

    async def get_task(self, target: str, task_id: str) -> Task:
        """a2a.getTask 调用。"""
        ...

    async def query_knowledge(
        self, target: str, request: QueryKnowledgeRequest
    ) -> QueryKnowledgeResponse:
        """a2a.queryKnowledge 调用（项目扩展 method）。"""
        ...

    async def get_knowledge_item(
        self, target: str, request: GetKnowledgeItemRequest
    ) -> GetKnowledgeItemResponse:
        """a2a.getKnowledgeItem 调用。"""
        ...

    async def record_memory(
        self, target: str, request: RecordMemoryRequest
    ) -> RecordMemoryResponse:
        """a2a.recordMemory 调用；idempotency_key 强制。"""
        ...

    async def query_memory(self, target: str, request: QueryMemoryRequest) -> QueryMemoryResponse:
        """a2a.queryMemory 调用。"""
        ...

    async def aclose(self) -> None:
        """关闭底层 httpx 连接池；幂等。"""
        ...
```

### 5.4 Retry 策略（Tenacity wrapper）

```python
# packages/a2a-core/src/superteam_a2a/a2a/client/retry.py
from dataclasses import dataclass
from enum import StrEnum


class RetryDecision(StrEnum):
    """按 method + error code 判断是否重试。"""

    DO_RETRY = "do-retry"
    DO_NOT_RETRY = "do-not-retry"
    METHOD_NOT_IDEMPOTENT = "method-not-idempotent"


# method_idempotency 表（与 Design §8.3 + ADR-0003 §6 一致）
METHOD_IDEMPOTENT = frozenset(
    {
        "a2a.sendMessage",  # 业务侧按 idempotency_key 决定
        "a2a.getTask",
        "a2a.getKnowledgeItem",
        "a2a.queryKnowledge",
        "a2a.queryMemory",
        # "a2a.recordMemory" — NOT idempotent（除非 idempotency_key）
    }
)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_seconds: float = 0.5
    max_delay_seconds: float = 10.0
    backoff_multiplier: float = 2.0
    jitter_factor: float = 0.1  # ±10% 抖动

    def decide(
        self,
        method: str,
        error_code: int,
        idempotency_key: str | None = None,
    ) -> RetryDecision:
        """判定是否重试。

        规则：
        - method not in METHOD_IDEMPOTENT 且无 idempotency_key → DO_NOT_RETRY
        - method in METHOD_IDEMPOTENT → DO_RETRY（除非 -32600/-32601/-32602）
        - recordMemory + idempotency_key → DO_RETRY
        """
        ...

    def compute_delay(self, attempt: int) -> float:
        """指数退避 + 抖动；attempt 从 0 开始。"""
        base = min(
            self.initial_delay_seconds * (self.backoff_multiplier**attempt),
            self.max_delay_seconds,
        )
        jitter = base * self.jitter_factor * (2 * random.random() - 1)
        return max(0.0, base + jitter)
```

**Retryable 错误码**（与 v0.1.0 Go baseline 一致）：

| Error Code | Retryable | 备注 |
|------------|-----------|------|
| -32700 Parse error | ❌ | 请求格式错误，不重试 |
| -32600 Invalid Request | ❌ | 同上 |
| -32601 Method not found | ❌ | 同上 |
| -32602 Invalid params | ❌ | 同上 |
| -32603 Internal error | ✅ | 指数退避 |
| -32001 Task not found | ❌ | 业务语义，不重试 |
| -32002 Task timeout | ✅（仅 idempotent） | 同上 |
| -32003 Task cancelled | ❌ | 终态 |
| -32004 Unauthorized | ❌ | 认证失败，不重试 |
| -32005 Forbidden | ❌ | 授权失败 |
| -32006 Rate limit | ✅ | 退避重试（尊重 Retry-After 头） |
| -32400 ~ -32406 Knowledge errors | ❌ | 业务语义错误 |
| -32500 ~ -32505 Memory errors | ❌ | 业务语义错误 |
| 网络超时 / 连接失败 | ✅ | 依赖 method idempotency |

### 5.5 Circuit Breaker + P2C

```python
# packages/a2a-core/src/superteam_a2a/a2a/client/circuit_breaker.py
from enum import StrEnum
from dataclasses import dataclass


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


@dataclass(frozen=True)
class CircuitBreakerConfig:
    failure_threshold: int = 5  # CLOSED → OPEN
    success_threshold: int = 2  # HALF_OPEN → CLOSED
    open_duration_seconds: float = 30.0  # OPEN → HALF_OPEN


class CircuitBreaker:
    """三态熔断器（CLOSED / OPEN / HALF_OPEN）。

    状态转换：
    - CLOSED → OPEN：连续失败 >= failure_threshold
    - OPEN → HALF_OPEN：open_duration 后
    - HALF_OPEN → CLOSED：连续成功 >= success_threshold
    - HALF_OPEN → OPEN：任一失败

    实例化：每个 target 一个 CircuitBreaker（per-endpoint）；key = (namespace, name)
    """

    ...


class P2CSelector:
    """Power of Two Choices — 多个 endpoint 时随机选 2 个，pick 负载最低。

    用于 AgentSet 多副本选择：每个 AgentSet 多个 Pod 端点。
    """

    ...

    async def select(self, endpoints: list[Endpoint]) -> Endpoint:
        """P2C 选择；endpoints 长度 < 2 时直接 random choice。"""
        ...
```

### 5.6 限流（token bucket）

```python
# 实现由 Operator 或 Adapter 注入；A2AClient 默认无 server-side 限流（server middleware 实现）
# Client-side 限流仅在 multi-tenant Adapter SDK 场景启用
```

---

## 6. ASGI server 与单进程原则（ADR-0005 §6.2 + 宪法 §3.8）

### 6.1 进程模型

- **强制**：Uvicorn 1 worker + 1 event loop + 单 Python 进程
- Helm values `python.workers: 1` schema 强制 const
- 高性能 event loop：`uvloop`
- HTTP parser：`httptools`

### 6.2 create_app 工厂契约

```python
# packages/a2a-core/src/superteam_a2a/a2a/server/app.py
from starlette.applications import Starlette
from starlette.middleware import Middleware
from superteam_a2a.a2a.upstream import AgentCard
from superteam_a2a.a2a.mtls import MtlsConfig
from superteam_a2a.a2a.extensions import discover_routers, dispatch


def create_app(
    card: AgentCard,
    mtls_config: MtlsConfig | None = None,
    middlewares: list[Middleware] | None = None,
    enable_stdlib_extensions: bool = True,
) -> Starlette:
    """构造 A2A ASGI app。

    Args:
        card: 本 Agent 的 AgentCard（SDK 用于 /.well-known/agent.json）
        mtls_config: mTLS 配置；None → 不启用 mTLS（仅开发环境）
        middlewares: 额外 middleware 列表
        enable_stdlib_extensions: True → discover 4 个项目扩展 router

    Returns:
        配置好的 Starlette ASGI app
    """
    ...
```

**middleware 链顺序**（不可改）：
```
request → Tracing → Auth (mTLS) → RateLimit → Metrics → handler
response ← Tracing ← Auth ← RateLimit ← Metrics ← handler
```

### 6.3 启动契约（uvicorn CLI）

```bash
uvicorn superteam_a2a.a2a.server.app:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 1 \
    --loop uvloop \
    --http httptools \
    --ssl-keyfile=/etc/tls/tls.key \
    --ssl-certfile=/etc/tls/tls.crt \
    --ssl-ca-certs=/etc/tls/ca.crt \
    --ssl-version 3 \
    --lifespan on
```

**Helm values（对应）**：
```yaml
a2aCore:
  python:
    workers: 1                       # const（schema.json constraint）
    eventLoop: uvloop
    httpParser: httptools
    sslVersion: 3                    # TLS 1.3
```

### 6.4 优雅停机时序（§13 完整生命周期）

lifespan 启动 / 关闭顺序严格：

**启动**：
1. load mTLS config + build SSLContext
2. init metrics / tracing / logging
3. discover_routers（4 个项目扩展 method 注册）
4. init Discovery + start K8s watch
5. init A2AClient connection pool
6. readiness = true

**关闭（SIGTERM）**：
1. readiness = false（30s 内 K8s endpoint 摘除）
2. 停止接收新请求（Uvicorn drain）
3. 等待 in-flight 完成（grace timeout 30s）
4. flush trace / metrics
5. stop K8s watch
6. close httpx connection pool
7. close CertWatcher

---

## 7. async-first + CPU offload（ADR-0005 §6.1 / §6.3）

### 7.1 async 边界规则

| 路径 | 实现 | 强制 |
|------|------|------|
| K8s API | `kubernetes_asyncio` | 必须 |
| A2A HTTP server | SDK ASGI（async handlers） | 必须 |
| A2A HTTP client | `httpx.AsyncClient` | 必须 |
| Agent Card Discovery | `httpx.AsyncClient` + `socket.getaddrinfo` (loop) | 必须 |
| OTel exporter | OTel Python async export pipeline | 必须 |
| BM25 index search | `anyio.to_thread.run_sync` offload | 必须 |
| Memory batch decay | `anyio.to_thread.run_sync` offload | 必须 |
| JSON validation (>1ms) | `anyio.to_thread.run_sync` offload | 必须 |

**禁止**：
- async handler 内直接调用阻塞 SDK
- 跨进程阻塞调用（违反单进程原则）
- `time.sleep()`（必须 `await asyncio.sleep()`）

### 7.2 offload_cpu 契约

```python
# packages/a2a-core/src/superteam_a2a/a2a/utils/offload.py
from functools import partial
from anyio import CapacityLimiter
import anyio


_cpu_limiter: CapacityLimiter = CapacityLimiter(8)


def configure_cpu_pool(max_workers: int = 8) -> None:
    """运行时配置（lifespan 启动期调用一次）。"""
    global _cpu_limiter
    _cpu_limiter = CapacityLimiter(max_workers)


async def offload_cpu(func, /, *args, **kwargs):
    """CPU 密集型工作 offload 到固定线程池。

    适用：
    - BM25 评分 > 1K items
    - Memory batch decay
    - JSON 反序列化 + 校验大 payload
    - Pydantic validation > 1ms

    超过队列深度 → Prometheus 指标告警（§9.1 superteam_python_thread_offload_queue_depth）
    """
    return await anyio.to_thread.run_sync(
        partial(func, *args, **kwargs),
        limiter=_cpu_limiter,
    )
```

### 7.3 event-loop lag 监控

```python
# packages/a2a-core/src/superteam_a2a/a2a/observability/event_loop.py
import asyncio
import time
from prometheus_client import Histogram
from superteam_a2a.a2a.observability.metrics import _registry


EVENT_LOOP_LAG = Histogram(
    "superteam_python_event_loop_lag_seconds",
    "Event loop lag detection (Python runtime)",
    labelnames=("component",),
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    registry=_registry,
)


async def measure_event_loop_lag(
    interval_seconds: float = 1.0,
    threshold_seconds: float = 0.050,
    component: str = "a2a-core",
) -> None:
    """定期检测 event loop lag；超过阈值触发 Warning Event（不抛错）。

    契约：
    - 后台 task；lifespan 启动 / 关闭
    - 间隔 1s（默认）；threshold 50ms（默认，Helm values 可配）
    - 超阈值 → structlog warning event + Prometheus Histogram observe
    """
    ...
```

### 7.4 取消与异常处理

**关键不变量**（与 ADR-0005 §6.4 一致）：
- 所有 background task 用 `asyncio.TaskGroup`（structured concurrency）
- `CancelledError` 不吞；re-raise 触发 lifespan 关闭
- 测试必须覆盖 shutdown timeout 和 partial failure

---

## 8. 错误模型（与 v0.1.0 + L1 Spec §5.7 + §8.3 完全一致）

### 8.1 wire shape（contract test 锁定）

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

### 8.2 错误码 Python enum

```python
# packages/a2a-core/src/superteam_a2a/a2a/errors.py
from enum import IntEnum


class StandardRpcError(IntEnum):
    """JSON-RPC 2.0 标准错误码 + 项目扩展错误码。

    数字与 L1 Spec §5.7 + v0.1.0 Go baseline 完全一致；contract test 锁定。
    """

    # 标准 JSON-RPC
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # A2A 域（SDK 提供 + 项目扩展）
    TASK_NOT_FOUND = -32001
    TASK_TIMEOUT = -32002
    TASK_CANCELLED = -32003
    UNAUTHORIZED = -32004
    FORBIDDEN = -32005
    RATE_LIMIT = -32006

    # 项目扩展（ADR-0002 + ADR-0003 · Knowledge 范围）
    KNOWLEDGE_SCOPE_NOT_FOUND = -32400
    KNOWLEDGE_ITEM_NOT_FOUND = -32401
    KNOWLEDGE_VERSION_NOT_FOUND = -32402
    KNOWLEDGE_QUERY_TOO_LONG = -32403
    KNOWLEDGE_INVALID_TYPE = -32404
    KNOWLEDGE_FORBIDDEN = -32405
    KNOWLEDGE_INTERNAL_ERROR = -32406

    # 项目扩展（Memory 范围）
    MEMORY_SCOPE_NOT_FOUND = -32500
    MEMORY_INVALID_CONTENT = -32501
    MEMORY_FORBIDDEN = -32502
    MEMORY_RATE_LIMIT = -32503
    MEMORY_QUERY_TOO_BROAD = -32504
    MEMORY_INTERNAL_ERROR = -32505


class ProjectRpcError(IntEnum):
    """项目扩展错误码子集（仅 Knowledge + Memory）。"""

    KNOWLEDGE_SCOPE_NOT_FOUND = StandardRpcError.KNOWLEDGE_SCOPE_NOT_FOUND
    # ... 同上
```

### 8.3 错误响应构造

```python
def make_error_response(
    request_id: str | int | None,
    code: StandardRpcError,
    message: str | None = None,
    data: dict | None = None,
) -> JSONRPCError:
    """构造标准 JSON-RPC 错误响应。

    - code: StandardRpcError enum
    - message: 默认取 enum.name；可覆盖
    - data: dict（如 {"detail": "...", "field": "params.scope_id"}）
    """
    return JSONRPCError(
        id=request_id,
        code=code,
        message=message or code.name,
        data=data,
    )
```

### 8.4 Retryable 矩阵（与 §5.4 表一致）

| Code | name | Retryable | HTTP Status |
|------|------|-----------|-------------|
| -32700 | PARSE_ERROR | ❌ | 400 |
| -32600 | INVALID_REQUEST | ❌ | 400 |
| -32601 | METHOD_NOT_FOUND | ❌ | 404 |
| -32602 | INVALID_PARAMS | ❌ | 422 |
| -32603 | INTERNAL_ERROR | ✅ | 500 |
| -32001 | TASK_NOT_FOUND | ❌ | 404 |
| -32002 | TASK_TIMEOUT | ✅ (idempotent) | 504 |
| -32003 | TASK_CANCELLED | ❌ | 410 |
| -32004 | UNAUTHORIZED | ❌ | 401 |
| -32005 | FORBIDDEN | ❌ | 403 |
| -32006 | RATE_LIMIT | ✅ | 429 |
| -32400 ~ -32406 | KNOWLEDGE_* | ❌ | 4xx |
| -32500 ~ -32505 | MEMORY_* | ❌ | 4xx |

---

## 9. 可观测性（Python 全栈 · 沿用 v0.1 metric name）

### 9.1 Prometheus 指标（与 L1 v0.2.0 Spec §16 + L1 Arch §9.2 完全一致）

| 指标 | 类型 | Labels | 触发点 | 单位 |
|------|------|--------|--------|------|
| `superteam_a2a_rpc_total` | Counter | `agent`, `method`, `status` | server middleware（每个 method 调用） | requests |
| `superteam_a2a_rpc_duration_seconds` | Histogram | `agent`, `method` | server middleware | seconds |
| `superteam_a2a_active_streams` | Gauge | — | SSE handler（v0.5+，v0.1 留位） | streams |
| `superteam_a2a_circuit_breaker_state` | Gauge | `target`, `state` | CircuitBreaker 状态变化 | 0/1/2 |
| `superteam_a2a_retry_total` | Counter | `method`, `attempt` | RetryPolicy | retries |
| `superteam_a2a_discovery_watch_reconnects_total` | Counter | `namespace` | EndpointSlice watch | reconnects |
| `superteam_a2a_agent_card_cache_hits_total` | Counter | `cache` | AgentCard cache | hits |
| `superteam_python_event_loop_lag_seconds` | Histogram | `component` | §7.3 后台 task | seconds |
| `superteam_python_thread_offload_queue_depth` | Gauge | `pool` | anyio limiter stats | tasks |
| `superteam_python_active_asyncio_tasks` | Gauge | — | `len(asyncio.all_tasks())` 采样 | tasks |
| `superteam_python_gc_collections_total` | Counter | `generation` | `gc.get_stats()` 采样 | collections |

**label 基数约束**（L1 Arch §9.2）：
- `agent`：受控（同一集群 < 1000）
- `method`：固定 6 个
- `target`：受控（per-endpoint CB）
- `status`：固定 4 个（success / error / timeout / cancelled）
- `component`：固定 5 个（a2a-core / knowledge / memory / operator / adapter）

### 9.2 Trace（OpenTelemetry Python SDK · W3C Trace Context）

**Span 结构**（与 L1 Arch §9.2 一致）：
```
A2A RPC
  ├── Adapter.Translate
  ├── Agent.Run
  │     ├── LLM Call
  │     └── MCP Tool Call
  └── Adapter.TranslateBack
```

**显式 provider 注入**（避免污染全局）：

```python
# packages/a2a-core/src/superteam_a2a/a2a/observability/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


_provider: TracerProvider | None = None


def init_tracing(
    service_name: str,
    otlp_endpoint: str | None = None,
    sample_ratio: float = 1.0,
) -> TracerProvider:
    """显式 provider 注入。

    测试用独立 provider；不在 conftest 设置全局，避免污染其他测试。
    """
    global _provider
    _provider = TracerProvider(
        resource={"service.name": service_name},
        sampler=TraceIdRatioBased(sample_ratio),
    )
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=False)
        _provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(_provider)
    return _provider


def tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)
```

**Traceparent 透传**：通过 A2A Message `metadata` 字段注入 `traceparent`；W3C Trace Context 标准。

### 9.3 日志（structlog + stdlib logging）

**必含字段**（与 L1 Spec §9.3 一致）：`trace_id` / `agent` / `method` / `task_id` / `namespace` / `ts`

**敏感字段禁记**（ADR-0005 §10）：API Key / Token / 用户数据 / Memory content / Knowledge body / cert 原文 / private key

```python
# packages/a2a-core/src/superteam_a2a/a2a/observability/logging.py
import logging
import structlog


_SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "token",
        "password",
        "private_key",
        "cert",
        "memory_content",
        "knowledge_body",
        "user_data",
    }
)


def _redact_processor(logger, method_name, event_dict):
    """结构化日志敏感字段脱敏。"""
    for key in _SENSITIVE_KEYS:
        if key in event_dict:
            event_dict[key] = "[REDACTED]"
    return event_dict


def configure_structlog(level: str = "INFO") -> None:
    """JSON 输出；保留 trace / agent / task / namespace 字段。"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _redact_processor,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        cache_logger_on_first_use=True,
    )
```

---

## 10. 上游追踪责任（宪法 §13.6 + ADR-0005 §13.6）

### 10.1 维护责任

L2-1 维护者必须：
- ✅ **每 minor release** 检查 `a2aproject/a2a-python` changelog；评估兼容性
- ✅ **每次 SDK 升级** 跑完整 conformance suite + 项目 contract test
- ✅ **每次 SDK 升级** 评估 `protocolVersion` 变化与 L1 协议版本基线（v0.3）
- ✅ **跟踪 a2aproject/A2A 主仓库** 规范变化
- ✅ Kopf 兼容性（Operator Core 依赖项）：L2-1 不直接依赖 Kopf；耦合点在 L2-2

### 10.2 contract test 套件（wire shape + envelope 锁定）

```python
# tests/contract/test_a2a_python_compat.py
import pytest
from pydantic import TypeAdapter
from superteam_a2a.a2a.upstream import AgentCard, Message, Task
from a2a.types import AgentCard as SdkAgentCard  # upstream 验证


class TestWireShapeContract:
    """wire shape 必须与 v0.1.0 Go baseline 完全一致。"""

    def test_agent_card_wire_shape(self):
        """AgentCard JSON dump 与 v0.1.0 fixture 完全一致。"""
        card = AgentCard(name="hello-agent", ...)
        dumped = card.model_dump(by_alias=True, mode="json")
        assert dumped == LOAD_FIXTURE("agent_card_v0_1_0.json")

    def test_jsonrpc_envelope_compat(self):
        """JSON-RPC envelope 字段与 v0.1.0 一致。"""
        req = JSONRPCRequest(jsonrpc="2.0", id="req-1", method="a2a.sendMessage", params={...})
        dumped = req.model_dump(by_alias=True, mode="json")
        assert dumped == LOAD_FIXTURE("jsonrpc_request_v0_1_0.json")

    def test_error_codes_match(self):
        """错误码数字与 L1 Spec §5.7 一致。"""
        from superteam_a2a.a2a.errors import StandardRpcError
        assert StandardRpcError.PARSE_ERROR == -32700
        assert StandardRpcError.KNOWLEDGE_SCOPE_NOT_FOUND == -32400
        assert StandardRpcError.MEMORY_SCOPE_NOT_FOUND == -32500

    def test_time_format_rfc3339(self):
        """所有 datetime 字段 RFC 3339 + UTC。"""
        ...


class TestSdkUpgradeSmoke:
    """SDK minor upgrade 不破坏 wire contract。"""

    def test_sdk_agent_card_compat(self):
        """本项目 AgentCard 与上游 SDK AgentCard 兼容（同一 wire）。"""
        local = AgentCard(name="hello", ...)
        sdk = SdkAgentCard.model_validate(local.model_dump(by_alias=True))
        assert local.model_dump(by_alias=True) == sdk.model_dump(by_alias=True)
```

### 10.3 upgrade 决策（ADR-0005 §11）

- **patch**（0.3.x → 0.3.x+1）：自动（contract test pass → 升级）
- **minor**（0.3.x → 0.4.0）：跑完整 conformance + E2E + 评估 API 变更；不破坏 wire 时直接升级
- **major**（0.x → 1.0）：**走 ADR**；评估 protocolVersion 升级 + wire 不变性

---

## 11. 测试策略（ADR-0005 §11 + 宪法 §9.7）

### 11.1 测试层级

| 层级 | 工具 | 覆盖率目标 | 关键场景 |
|------|------|------------|----------|
| **Unit (UT)** | `pytest` + `pytest-asyncio` | ≥ 90% | Pydantic 校验 / JSON-RPC envelope / 错误码映射 / mTLS context / 路由分发 |
| **Property** | `Hypothesis` + `hypothesis-jsonschema` | envelope / schema / FSM | 任意 JSON-RPC request 不崩溃；wire 序列化反序列化 round-trip |
| **HTTP** | `respx` / ASGI test client | timeout / 取消 / 重试 / mTLS 失败 | httpx mock + 各种失败路径 |
| **SDK compat (CT)** | 自研 contract test + SDK 自带 conformance | wire shape + 错误码 + envelope | 锁定 v0.1.0 wire；minor 升级跑过 |
| **Operator IT** | kind + `kubernetes_asyncio` 真实 watch | reconcile / webhook / leader failover | ADR-0005 §7 12 项门禁（适用 L2-2） |
| **E2E** | kind + Helm | Hello Agent + Workflow + Knowledge + Memory 全链路 | 完整业务流程 |

### 11.2 测试 ID 矩阵（完整清单 · 100 ID）

| 类别 | ID 前缀 | 数量 | 说明 |
|------|---------|------|------|
| Pydantic schema | `UT-SCHEMA-` | 12 | 4 扩展 × 3 case（valid / invalid / boundary） |
| JSON-RPC envelope | `UT-ENV-` | 8 | wire shape + 错误码序列化 + 透传 |
| 错误码映射 | `UT-ERR-` | 17 | 17 错误码 × 1 case |
| ExtensionRouter | `UT-EXT-` | 12 | 4 router × 3 case（dispatch / unknown / duplicate） |
| mTLS context | `UT-MTLS-` | 8 | ssl.SSLContext 构造 + SPIFFE 解析 + 文件缺失 |
| Retry policy | `UT-RETRY-` | 6 | 退避计算 + idempotency gate + max attempts |
| Circuit breaker | `UT-CB-` | 8 | 3 状态转换 + threshold + half-open probe |
| Discovery | `UT-DISC-` | 6 | EndpointSlice mock + AgentCard cache TTL |
| Property | `PROP-` | 5 | envelope round-trip + arbitrary JSON-RPC 不崩溃 |
| HTTP mock | `HTTP-` | 8 | timeout / 取消 / 重试 / mTLS 失败 |
| SDK compat | `CT-` | 5 | wire shape + 错误码 + envelope 锁定 |
| Operator IT | `IT-` | 3 | watch reconnect / agent card pull / 多 namespace |
| E2E | `E2E-` | 2 | hello-agent + workflow 全链路 |
| **合计** | — | **100** | — |

**测试 ID 完整清单**（示例，详细在 L3-2 Spec）：

```
UT-SCHEMA-QK-001: QueryKnowledgeRequest 合法 + top_k=10
UT-SCHEMA-QK-002: QueryKnowledgeRequest query="" → ValidationError
UT-SCHEMA-QK-003: QueryKnowledgeRequest scope_level 非法 → ValidationError
UT-SCHEMA-GKI-001: GetKnowledgeItemRequest 合法
UT-SCHEMA-GKI-002: GetKnowledgeItemRequest item_id="" → ValidationError
UT-SCHEMA-GKI-003: GetKnowledgeItemRequest version=0 → ValidationError
UT-SCHEMA-RM-001: RecordMemoryRequest 合法 + idempotency_key="abc-123"
UT-SCHEMA-RM-002: RecordMemoryRequest 缺 idempotency_key → ValidationError
UT-SCHEMA-RM-003: RecordMemoryRequest idempotency_key 含特殊字符 → ValidationError
UT-SCHEMA-QM-001: QueryMemoryRequest 合法 + visibility=AGENT_PRIVATE
UT-SCHEMA-QM-002: QueryMemoryRequest scope_level + scope_id 不一致 → ValidationError
UT-SCHEMA-QM-003: QueryMemoryRequest min_confidence > 1.0 → ValidationError

UT-ENV-001: JSONRPCRequest dump camelCase 正确
UT-ENV-002: JSONRPCResponse dump 含 result 字段
UT-ENV-003: JSONRPCError dump 含 code/message/data
UT-ENV-004: id 字符串/数字/null 三种类型兼容
UT-ENV-005: params 字典/列表/None 三种类型兼容
UT-ENV-006: traceparent 透传保留
UT-ENV-007: 序列化 round-trip 一致
UT-ENV-008: 时间字段 RFC 3339

UT-ERR-001 ~ UT-ERR-017: 17 错误码各自映射

UT-EXT-001: QueryKnowledgeRouter.method_name == "a2a.queryKnowledge"
UT-EXT-002: 已知 method 分发成功
UT-EXT-003: 未知 method 返回 -32601
UT-EXT-004: discover_routers 检测重复 method_name → ValueError
... (共 12)

UT-MTLS-001: build_server_ssl_context 成功
UT-MTLS-002: tls.crt 缺失 → MtlsConfigError
UT-MTLS-003: tls.key 缺失 → MtlsConfigError
UT-MTLS-004: tls.key mode != 0600 → MtlsConfigError
UT-MTLS-005: extract_spiffe_id URI SAN 解析成功
UT-MTLS-006: extract_spiffe_id 无 SPIFFE SAN → None
UT-MTLS-007: validate_spiffe_id trust_domain 匹配
UT-MTLS-008: validate_spiffe_id trust_domain 不匹配 → SpiffeIdFormatError

UT-RETRY-001: compute_delay(0) = 0.5 ± jitter
UT-RETRY-002: compute_delay(3) 接近 max_delay
UT-RETRY-003: sendMessage 失败 → DO_RETRY
UT-RETRY-004: recordMemory 无 idempotency_key → DO_NOT_RETRY
UT-RETRY-005: recordMemory + idempotency_key → DO_RETRY
UT-RETRY-006: getTask + INVALID_PARAMS → DO_NOT_RETRY

UT-CB-001: CLOSED 失败 < threshold → 保持 CLOSED
UT-CB-002: CLOSED 失败 >= threshold → OPEN
UT-CB-003: OPEN 超时 → HALF_OPEN
UT-CB-004: HALF_OPEN 成功 → CLOSED
UT-CB-005: HALF_OPEN 失败 → OPEN
UT-CB-006: P2C select endpoints=[] → ValueError
UT-CB-007: P2C select endpoints=1 → random choice
UT-CB-008: P2C select endpoints=10 → 选 2 个 pick 最低

UT-DISC-001: list_targets 包含所有 namespace endpoint
UT-DISC-002: AgentCard cache hit < TTL
UT-DISC-003: AgentCard cache miss > TTL → 重新拉取
UT-DISC-004: watch_targets ADDED 事件触发
UT-DISC-005: watch_targets DELETED 事件触发
UT-DISC-006: watch reconnect backoff 1s → 30s

PROP-001: 任意 JSON-RPC request 序列化反序列化 round-trip
PROP-002: 任意 QueryKnowledgeRequest 不崩溃
PROP-003: 任意 RecordMemoryRequest 不崩溃
PROP-004: 任意 AgentCard JSON Schema 2020-12 valid
PROP-005: 任意错误码枚举值唯一

HTTP-001: A2AClient.send_message timeout → A2ATimeoutError
HTTP-002: A2AClient.send_message cancel → A2ACancelledError
HTTP-003: A2AClient.send_message 5xx → retry
HTTP-004: A2AClient.send_message mTLS cert invalid → A2AAuthError
HTTP-005: A2AClient.query_knowledge 404 → KNOWLEDGE_SCOPE_NOT_FOUND
HTTP-006: A2AClient.record_memory 重复 idempotency_key → 返回原 memory_id
HTTP-007: Retry-After 头 → 退避时间尊重
HTTP-008: Circuit OPEN → CircuitOpenError 不发起请求

CT-001: AgentCard wire shape 一致
CT-002: JSON-RPC envelope wire shape 一致
CT-003: 17 错误码数值一致
CT-004: 时间格式 RFC 3339
CT-005: SDK AgentCard 互转 round-trip

IT-001: EndpointSlice watch reconnect 后继续接收事件
IT-002: AgentCard 拉取过 mTLS 校验
IT-003: 多 namespace watch RBAC 正确

E2E-001: hello-agent 启动 → sendMessage → 收到 Task
E2E-002: workflow 触发 4 个扩展 method → 全链路成功
```

### 11.3 conformance 套件接入（ADR-0005 §11.2）

- SDK 提供 `a2a.conformance` 子包（具体路径 L3-2 实测）
- CI 必跑：`pytest tests/conformance -v`
- 标准 method 100% 覆盖

### 11.4 静态门禁（CI 必跑）

```bash
uv sync --frozen
ruff format --check .
ruff check .
ruff check --select ST-A2A-BOUNDARY .  # 自定义规则：禁止业务层 import a2a
pyright
bandit -r packages/a2a-core
pip-audit --strict
```

**Ruff 自定义规则 ST-A2A-BOUNDARY 检测**：
- `import a2a` → 报错（业务层必须经 superteam_a2a.a2a）
- `from a2a import ...` → 报错
- 例外：`packages/a2a-core/src/superteam_a2a/a2a/upstream.py`（boundary 模块）
- 例外：`packages/a2a-core/src/superteam_a2a/a2a/upstream_types.py`（项目私有 DTO）

### 11.5 性能预算（L1 v0.2.0 Arch §11.5 · L2-1 关注项）

| 指标 | 目标值 | 测量工具 |
|------|--------|----------|
| 1 KiB A2A loopback p50/p95/p99 | < 5ms / < 20ms / < 50ms | `pytest-benchmark` |
| Pydantic validation overhead | < 1ms | `pytest-benchmark` |
| Agent Card cache hit | < 0.5ms | `pytest-benchmark` |
| EndpointSlice watch invalidation | < 100ms | kind E2E |
| event-loop lag p99 | < 50ms | Prometheus histogram |

---

## 12. Helm values 完整 schema

### 12.1 a2aCore 段

```yaml
a2aCore:
  replicaCount: 1                       # v0.1 强制 1（多实例评估 v0.5+）
  image:
    repository: superteam-a2a/a2a-core
    tag: v0.2.0
    pullPolicy: IfNotPresent
  python:
    workers: 1                          # const：强制单进程
    eventLoop: uvloop                   # const
    httpParser: httptools               # const
    cpuOffloadWorkers: 8                # anyio CapacityLimiter
    eventLoopLagThresholdMs: 50         # 超阈值触发 warning event
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 2Gi
  mtls:
    enabled: true                       # v0.1 强制 true
    certDir: /etc/tls
    minVersion: "1.3"                   # const
    spiffeRequired: true
    trustDomain: superteam-a2a.local
    hotReload:
      enabled: true
      intervalSeconds: 30               # CertWatcher 检查间隔
      timeoutSeconds: 5
  service:
    port: 8080                          # const（Helm release + ServiceMonitor）
    targetPort: 8080
  observability:
    metrics:
      enabled: true
      path: /metrics
    tracing:
      enabled: true
      otlpEndpoint: null                # 默认空 → 由 OTEL_EXPORTER_OTLP_ENDPOINT 注入
      sampleRatio: 1.0
    logging:
      level: INFO
      format: json                      # const
  certWatcher:
    intervalSeconds: 30
    timeoutSeconds: 5
  terminationGracePeriodSeconds: 60     # 给足优雅停机时间
```

### 12.2 Pod Security（K8s 1.28+ restricted profile）

```yaml
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 65534                     # nobody
  runAsGroup: 65534
  fsGroup: 65534
  seccompProfile:
    type: RuntimeDefault
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true          # ⚠️ 与 cert hot reload 兼容（certDir volumeMount）
  capabilities:
    drop: ["ALL"]
```

### 12.3 RBAC（ServiceAccount + ClusterRole）

```yaml
rbac:
  serviceAccountName: superteam-a2a-a2a-core
  clusterRoles:
    - apiGroups: [""]
      resources: ["endpointslices"]
      verbs: ["get", "list", "watch"]
    - apiGroups: [""]
      resources: ["services"]
      verbs: ["get", "list", "watch"]
    - apiGroups: [""]
      resources: ["configmaps"]
      verbs: ["get"]
      resourceNames: ["superteam-a2a-config"]
```

---

## 13. 生命周期契约（时序图）

### 13.1 启动时序

```
[K8s Pod Start]
    │
    ▼
[Container Start]
    │
    ▼
[Uvicorn worker 1, event loop = uvloop]
    │
    ▼
[lifespan.__aenter__]
    │
    ├──→ 1. load MtlsConfig
    │        ├─ check tls.crt/key/ca.crt exists
    │        ├─ check tls.key mode == 0600
    │        └─ build_server_ssl_context()
    │
    ├──→ 2. init observability
    │        ├─ Prometheus _registry
    │        ├─ structlog configure
    │        └─ OTel provider (if OTEL_EXPORTER_OTLP_ENDPOINT)
    │
    ├──→ 3. discover_routers()
    │        └─ 4 routers registered in _DISCOVERED
    │
    ├──→ 4. init Discovery
    │        ├─ kubernetes_asyncio.CoreV1Api
    │        ├─ list EndpointSlice (label: superteam-a2a.io/component=agent)
    │        └─ watch EndpointSlice (background task)
    │
    ├──→ 5. init A2AClient
    │        └─ httpx.AsyncClient with ssl_context + connection pool
    │
    ├──→ 6. start CertWatcher
    │        └─ background task: check mtime every 30s
    │
    ├──→ 7. measure_event_loop_lag()
    │        └─ background task: check lag every 1s
    │
    └──→ 8. readiness = true  ──→  [EndpointSlice add Pod IP]
```

### 13.2 稳态（steady state）

```
[Background Tasks]
    ├── CertWatcher: every 30s check mtime → if changed, rebuild SSLContext + on_reload callback
    ├── measure_event_loop_lag: every 1s check lag → Prometheus histogram
    ├── Discovery watch: K8s watch → on EndpointSlice event → update cache
    ├── OTel BatchSpanProcessor: every 5s flush spans

[Request Flow]
    Client → POST /a2a/jsonrpc
        → TracingMiddleware (start span)
        → AuthMiddleware (mTLS verify + extract SPIFFE ID)
        → RateLimitMiddleware (token bucket)
        → MetricsMiddleware (record start)
        → SDK jsonrpc_app / extension router
        → Response
        → MetricsMiddleware (record end + duration)
        → Response → Client
```

### 13.3 关闭时序（SIGTERM）

```
[K8s SIGTERM (preStop hook → 30s sleep)]
    │
    ▼
[Uvicorn receive SIGTERM]
    │
    ▼
[lifespan.__aexit__]
    │
    ├──→ 1. readiness = false  ──→  [EndpointSlice remove Pod IP ~5s]
    │
    ├──→ 2. Uvicorn drain
    │        ├─ 停止 accept new connection
    │        └─ wait in-flight request to complete (max 30s)
    │
    ├──→ 3. flush OTel BatchSpanProcessor (force_flush, timeout 5s)
    │
    ├──→ 4. flush Prometheus (write_to_textfile → empty disk volume)
    │
    ├──→ 5. stop CertWatcher (cancel background task)
    │
    ├──→ 6. stop Discovery watch (kubernetes_asyncio watch close)
    │
    ├──→ 7. stop measure_event_loop_lag (cancel background task)
    │
    └──→ 8. close A2AClient (httpx.AsyncClient.aclose, max 5s)
```

### 13.4 证书热更新时序

```
[cert-manager renews cert → K8s Secret update]
    │
    ▼
[K8s kubelet sync Secret volume → /etc/tls/tls.crt mtime change]
    │
    ▼
[CertWatcher.check_and_reload (every 30s)]
    │
    ├──→ 1. stat mtime_ns vs cached
    │        └─ changed → trigger reload
    │
    ├──→ 2. load new cert/key with 5s timeout
    │        └─ fail → keep old context + ERROR log
    │
    └──→ 3. on_reload callbacks
             ├─ Uvicorn SSLConfig swap (L3-2 实现)
             └─ structlog info "ssl_context_reloaded"
```

---

## 14. 验收清单（v0.2 · Python-first）

> L2-1 v0.2 Spec 被认定为"通过"必须满足

### 14.1 模块完整性（与 v0.1.0 一致）

- [ ] 7 个 A2A method 全部覆盖（2 标准 SDK + 4 项目扩展 router + 1 占位 `cancelTask`）
- [ ] Agent Card 服务于 `/.well-known/agent.json`
- [ ] mTLS 透明（cert-manager mounted cert → ssl.SSLContext）
- [ ] SPIFFE URI SAN 解析（`py-spiffe` 实测后启用或回退）
- [ ] K8s Service / DNS / EndpointSlice Discovery
- [ ] Retry + Circuit Breaker + P2C + 限流
- [ ] conformance suite 接入
- [ ] contract test 套件建立（wire shape + 错误码 + envelope 锁定）

### 14.2 Python-first 硬约束（ADR-0005 + 宪法 v0.5.0）

- [ ] **wire contract 与 v0.1.0 完全一致**（JSON 字段 / 错误码 / Agent Card 路径 / 任务状态机 / metric name）
- [ ] **官方 `a2a-sdk` 复用 + `superteam_a2a.a2a.upstream` boundary**（Ruff `ST-A2A-BOUNDARY` 规则检测禁止业务层直接 import SDK）
- [ ] **compatibility adapter router 不修改 / 不 fork SDK**（4 个项目扩展 method 通过 Starlette sub-app 注入）
- [ ] **async-first**：所有 K8s I/O / A2A HTTP / OTel 异步
- [ ] **CPU offload**：`anyio.to_thread.run_sync` 限定场景（线程池容量可配）
- [ ] **单进程原则**：Uvicorn 单 worker + 单 event loop；Helm `python.workers: 1` 强制
- [ ] **timezone-aware UTC**：所有 datetime 字段（Pydantic 强制）
- [ ] **Pydantic v2 strict** 公共边界（`extra="forbid"` + 禁止未解释 `Any`）
- [ ] **uv.lock 必须提交**；CI `uv sync --frozen`
- [ ] **Python 静态门禁**（CI 必跑）：Ruff + Pyright strict + Bandit + pip-audit + Ruff `ST-A2A-BOUNDARY`

### 14.3 可观测性 / 安全 / 性能

- [ ] Prometheus 指标覆盖（7 个 A2A + 4 个 Python runtime）
- [ ] OpenTelemetry Trace（W3C Traceparent 透传）
- [ ] structlog JSON 日志（敏感内容禁记；`_SENSITIVE_KEYS` 脱敏）
- [ ] Python 镜像非 root + read-only rootfs + drop all capabilities
- [ ] 性能预算满足（L1 Arch §11.5：loopback p99 < 50ms）

### 14.4 上游追踪

- [ ] `a2aproject/a2a-python` 维护责任明确（§10.1 5 项 checklist）
- [ ] upgrade 决策树（patch / minor / major · §10.3）
- [ ] contract test 套件已建立（§10.2 5 个 CT ID）

### 14.5 与其他文档一致性

- [ ] 与 L1 Architecture v0.2.0 §3.4 / §7 / §9.2 一致
- [ ] 与 L1 Spec v0.2.0 §5 / §15 / §16 一致
- [ ] 与 ADR-0005 §3.2 / §8 / §9 / §13.6 一致
- [ ] 与宪法 v0.5.0 §3.8 / §9.7 / §13.6 一致
- [ ] MVP 例外 §14.5 显式声明（v0.1 阶段适用）
- [ ] 与 L2-1 Design v0.2-draft 决策一致（无矛盾）

### 14.6 跨文档同步

- [ ] L2-1 Design v0.2-draft 顶部增加"Spec v0.2-draft 配套"指针
- [ ] L2-1 Go Spec v0.1.0 顶部 supersede 指针确认（已存在）
- [ ] L3-1 / L3-2 文件级 Spec 起草输入清单更新（L3-2 必须依赖本 Spec）

---

## 15. 开放问题（移交 L3-2 Spec / v0.5+）

> L2-1 v0.2 Spec 未定项；L3-2 Spec 重写时**必须**收敛

1. **a2a-python 精确 PyPI 包名**（U-1）：L3-2 `pip index versions a2a-*` 确认
2. **`requires-python` 精确下限**（U-2）：L3-2 `pip show` + CI matrix 配置
3. **conformance 套件 import 路径 / 入口命令**（U-3）：L3-2 在 Python venv 实测
4. **`py-spiffe` Workload API 兼容性**（U-4）：ADR-0005 §9.1 回退路径已规划（cert-manager mounted cert + URI SAN）
5. **SDK ASGI server method-level 中间件支持**（U-5）：L3-2 实测；不满足时通过 ASGI middleware 包装
6. **jsonrpc_app 内部结构**：L3-2 需读取源码确认 envelope 校验 / 中间件 hook
7. **Python SPIFFE 库生态稳定性**：除 `py-spiffe` 外是否有更成熟选项？L3-2 评估
8. **Uvicorn 证书热更新**：`--reload` vs 自定义 `ssl.SSLContext` reload？L3-2 决策
9. **Otel ASGI middleware 与 SDK 兼容性**：L3-2 实测是否需要自定义中间件
10. **httpx AsyncClient 与 SDK client 关系**：SDK 是否直接使用 httpx？L3-2 确认是否需要自定义 client 包装
11. **Helm schema.json 校验**：CI 中是否集成 kubeconform？L3 决定
12. **Kopf admission webhook 与 L2-1 mTLS 共存**：L2-2 关注，L2-1 仅提供 ssl.SSLContext 构造 API
13. **Pyright strict 的 stdlib Any 处理**：`ssl.SSLContext` 等 stdlib 类型 Pyright 视为 `Any`，需 `type: ignore[no-any-expr]` 标注范围最小化
14. **RESpx mock 与 httpx 版本兼容**：CI matrix 测试
15. **fastapi vs starlette 选择**：L2-1 仅用 Starlette（更轻）；如有 FastAPI 需求需 ADR

---

## 附录 A：相关文档

| 文档 | 路径 | 关系 |
|------|------|------|
| L2-1 Design v0.2-draft | `docs/design/L2-modules/L2-a2a-protocol.md` | 配套设计（输入） |
| L2-1 Review（待起草） | `docs/reviews/l2-1-a2a-protocol-review.md` | 配套评审 |
| L2-1 Go Spec v0.1.0（superseded） | `docs/spec/L2-module-specs/L2-a2a-protocol.md` | 历史版本 |
| L1 Architecture v0.2.0 | `docs/design/L1-architecture.md` §3.4 / §7 / §9.2 | 上游架构 |
| L1 Spec v0.2.0 | `docs/spec/L1-system-spec.md` §5 / §15 / §16 | 上游规格 |
| ADR-0005 | `docs/adr/0005-python-first-technology-stack.md` | 本 Spec 的元决策 |
| ADR-0002 | `docs/adr/0002-knowledge-management-design.md` | 4 扩展 method 业务语义 |
| ADR-0003 | `docs/adr/0003-memory-design.md` | Memory 生命周期 |
| Constitution v0.5.0 | `CONSTITUTION.md` | 最高纲领 |
| L3-1 Operator Core | `docs/spec/L3-file-specs/L3-operator-core.md` v0.2.0（2026-07-28 #56 评审通过 · [评审](reviews/l3-1-operator-core-spec-review.md)） | 下游 Operator |
| L3-2 A2A Core | `docs/spec/L3-file-specs/L3-a2a-core.md` | 下游实现文件级 |
| L2-2 Operator Core Spec | `docs/spec/L2-module-specs/L2-operator-core.md` | 兄弟 Spec |
| L2-4 Knowledge/Memory Spec | `docs/spec/L2-module-specs/L2-knowledge-memory.md` | 业务实现扩展 router |

---

## 附录 B：ADR / Constitution 引用矩阵

| 本 Spec 条款 | 引用 | 关系 |
|--------------|------|------|
| §1.2 boundary | ADR-0005 §3.2 + 宪法 §3.8 | 必须遵守 |
| §3 compatibility adapter | ADR-0005 §8 + 宪法 §3.5 | 协议兼容 |
| §4 mTLS | ADR-0005 §9.1 + 宪法 §6.1 | 安全底线 |
| §5.4 Retryable | L1 Spec §5.7 + ADR-0003 §6 | wire contract |
| §6 单进程 | ADR-0005 §6.2 + 宪法 §3.8 | 实现约束 |
| §7 async-first | ADR-0005 §6.1 + 宪法 §3.8 | 实现约束 |
| §8 错误码 | L1 Spec §5.7 + ADR-0002/0003 | 业务语义 |
| §9 Prometheus 指标 | L1 Arch §9.2 + 宪法 §2.3 | 可观测性 |
| §9.3 敏感字段禁记 | ADR-0005 §10 + 宪法 §6.6 | 安全 |
| §10 上游追踪 | 宪法 §13.6 + ADR-0005 §13.6 | 维护责任 |
| §11.1 静态门禁 | ADR-0005 §11 + 宪法 §9.7 | 质量门禁 |
| §13 生命周期 | ADR-0005 §6.4 + 宪法 §3.2 | Operator 可靠性 |
| §14 验收清单 | 宪法 §14 | MVP 例外 |

---

> **状态**：✅ v0.2.0 已评审通过（2026-07-24；10 维度全 PASS）
> **下一步**：进入 L2-2 Operator Core Python 重写（先归档 L2-2 Go Design 到 `docs/archive/pre-python-2026-07-24/` 避免覆盖事故）
> **supersedes**：v0.1.0 Go baseline（仅 supersede Go struct / Go package / Go HTTP server / Go JSON-RPC envelope 实现条款；wire contract 与业务语义继续有效）
> **下一步**：L2-1 v0.2 Python 评审（10 维度）→ L2-1 v0.2.0 升级 → 进入 L2-2 Operator Core Python 重写
> **评审者**：项目发起人（基于单人维护者 + MVP 例外 §14.5 单点评审）
> **变更摘要**（2026-07-24 · v0.1.0 → v0.2-draft 增量）：
> - **+1 完整文件清单**：32 个 .py 文件（7 子包 + 3 single-source + 1 private）
> - **+4 Pydantic schema**：QueryKnowledge / GetKnowledgeItem / RecordMemory / QueryMemory 完整字段约束
> - **+1 Protocol**：ExtensionRouter Protocol（runtime_checkable）
> - **+1 discover_routers**：pkgutil + inspect 自动发现 + 重复检测
> - **+1 ssl.SSLContext 构造契约**：build_server_ssl_context + MtlsConfig dataclass
> - **+1 SPIFFE 解析契约**：extract_spiffe_id + validate_spiffe_id
> - **+1 证书热更新契约**：CertWatcher 类 + start/stop/on_reload + reload timeout 回退
> - **+1 Discovery 契约**：list_targets / watch_targets / get_agent_card + TTL cache
> - **+1 A2AClient 契约**：6 method + SSL + retry + CB + discovery 注入
> - **+1 RetryPolicy 契约**：RetryDecision 枚举 + METHOD_IDEMPOTENT 表 + jitter 计算
> - **+1 CircuitBreaker + P2C 契约**：3 状态转换 + threshold + P2C select
> - **+1 create_app 工厂契约**：card + mtls_config + middlewares + discover_routers
> - **+1 offload_cpu 契约**：anyio.to_thread.run_sync + CapacityLimiter 可配
> - **+1 event-loop lag 监控契约**：后台 task + threshold 告警
> - **+1 错误码 enum**：17 错误码 StandardRpcError + ProjectRpcError 子集
> - **+1 11 Prometheus 指标**：7 A2A + 4 Python runtime
> - **+1 OTel provider 注入契约**：init_tracing + 测试隔离
> - **+1 structlog 配置契约**：敏感字段脱敏 _SENSITIVE_KEYS
> - **+1 contract test 套件**：5 CT ID + wire shape 锁定
> - **+1 测试 ID 矩阵**：100 个测试 ID（UT 71 + PROP 5 + HTTP 8 + CT 5 + IT 3 + E2E 2 + 完整列表）
> - **+1 Ruff ST-A2A-BOUNDARY 规则**：boundary 检测（业务层禁直接 import SDK）
> - **+1 Helm values schema**：a2aCore 完整段（python / mtls / certWatcher / RBAC）+ Pod Security + RBAC
> - **+1 生命周期时序**：4 张时序图（启动 / 稳态 / 关闭 / 证书热更新）
> - **+1 验收清单**：14.1-14.6 六组（模块完整性 / Python-first 硬约束 / 可观测性安全性能 / 上游追踪 / 文档一致性 / 跨文档同步）
> - **+15 开放问题**：移交 L3-2 Spec 与 v0.5+
> - **+2 附录**：A 相关文档 + B ADR/Constitution 引用矩阵