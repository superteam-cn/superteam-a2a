# L3 文件级 Spec：A2A Core Library（通信层文件级 · Python-first）

> **⚠️ ADR-0005 supersede + 归档标记（2026-07-27）**：本 v0.2-draft Spec 文档**仅 supersede Go struct / Go package / Go HTTP server / Go JSON-RPC envelope 实现条款**；wire contract（6 method envelope / 4 endpoint / 14 error code / Task FSM / mTLS / metric name）与 v0.1-draft 业务语义**完全继续有效**。原 v0.1-draft Go baseline 已归档至 [`docs/archive/pre-python-2026-07-24/L3-a2a-core-spec-v0.1-draft-go-baseline.md`](../../archive/pre-python-2026-07-24/L3-a2a-core-spec-v0.1-draft-go-baseline.md)（2026-07-27 归档 / **未评审** / 62KB / 1446 行）。
>
> **Python 重写入口**：依据 L1 v0.2.0 Architecture §3.4 + ADR-0005 §3.2 + §8 + §13.1，7 个 Go 子包 → Python 子包（`superteam_a2a.a2a.upstream` boundary + 4 个 extension router + standard method 通过官方 `a2a-sdk`）；Go `net/http` server → **ASGI + Uvicorn 单 worker**；Go `goroutine` 业务逻辑 → **`asyncio` 协程 + `anyio.to_thread.run_sync` CPU offload**；Go Go context → Python `contextvars.ContextVar`。
>
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-2（A2A Core Library，见 L1 v0.2.0 Architecture §4.1）
> **代码位置**：`packages/a2a-core/src/superteam_a2a/a2a/`（**ADR-0005 §13.1 uv workspace 布局**，替代原 Go baseline 的 `src/a2a/`）
> **版本**：v0.2-draft（2026-07-27 起 Python 重写 + 2026-07-27 #44 Go baseline 归档）
> **状态**：🟢 v0.2-draft-full **§10-§12 补完稿（#50 骨架 + #51 §10-§12 补完）**——头部 + §0-§12 + 附录 A 已落地 + ⚠️ §13-§15 + 附录 B = **3 节 + 1 附录待后续 #52+ 会话补完**
> **Python 栈基线**：Python 3.12+（**ADR-0005 §3.1**）+ uv workspace + 官方 `a2a-sdk` envelope/ASGI 复用 + Pydantic v2 + httpx + OpenTelemetry + structlog + cert-manager
> **wire contract 不变性**（与 v0.1.0 Go baseline + L2-1 Spec v0.2.0 完全一致，contract test 锁定）：JSON 字段名 / camelCase / RFC 3339 时间 / Agent Card 路径 / 错误码 / 任务状态机 / metric name
> **上游约束**：[`docs/spec/L2-module-specs/L2-a2a-protocol.md`](../../spec/L2-module-specs/L2-a2a-protocol.md) **v0.2.0**（2026-07-24 评审通过 · 72KB / 1919 行 / 16 节 + 2 附录 / 14 错误码 / 100 测试 ID / 4 时序图 / 15 开放问题 / 80% 收敛率）
> **本 Spec 目的**：将 L2-1 A2A Protocol Spec v0.2.0 中的 **7 个子包 + 6 method + 4 endpoint + 24 error code + 15 Prometheus 指标 + ExtensionRouter Protocol** 落地为 **文件级 Python 代码契约**——每个文件列明**绝对路径（基于 uv workspace 布局）**、**职责一句话**、**完整 import 列表**、**exported 符号签名（type hints + docstring 一行）**、**内部 helper 列表**、**关联测试文件路径 + 测试 ID 前缀**。是 L4 实施阶段（开发者打开 IDE 即可对照写代码）的直接输入。
> **配套 Spec**：[L3-1 Operator Core 文件级 Spec v0.2-draft](./L3-operator-core.md)（2026-07-27 #49 §9 补完稿；70 文件清单 + 4 Controller）/ [L3-3 Adapter SDK](./L3-adapter-sdk.md)（待起草）/ [L3-4 Hello Agent](./L3-hello-agent.md)（待起草）/ [L3-5 Knowledge Service](./L3-knowledge-service.md)（待起草）/ [L3-6 Memory backend](./L3-memory-backend.md)（待起草）

---

## 0. 阅读指南

- **读者**：A2A Core 实施工程师（L4 Python 编码）、Code Reviewer（PR 审查）、架构 Reviewer（设计一致性）
- **必读章节**：§1（模块使命 + 30 文件清单总览）/ §2（Python 包结构）/ §3（4 extension method Pydantic schema + ExtensionRouter Protocol）/ §8（24 错误码）/ §11（276 ID 测试 ID 矩阵）/ §12（Helm values 9 模板 + A2aCoreConfig Pydantic）/ 附录 A（跨模块引用清单）
- **可选章节**：本次 v0.2-draft-full §10-§12 补完稿**不包含** §13 生命周期 + §14 验收清单 + §15 开放问题 + 附录 B ADR 矩阵（已在各 §标题占位；后续 #52+ 会话补完）
- **配套阅读**：[L2-1 A2A Protocol Spec v0.2.0](../../spec/L2-module-specs/L2-a2a-protocol.md) §1-§15 + 附录 A/B · [L2-1 A2A Protocol Design v0.2.0](../../design/L2-modules/L2-a2a-protocol.md) §3-§14 · [L1 Architecture v0.2.0 §3.4 通信层](../../design/L1-architecture.md) · [ADR-0005 §3.2 A2A Core 模块映射](../adr/0005-python-first-technology-stack.md) · [官方 a2a-python SDK 文档](https://github.com/a2a-mcp-go/a2a-python) · [httpx 异步客户端文档](https://www.python-httpx.org/async/) · [OpenTelemetry Python SDK 文档](https://opentelemetry.io/docs/languages/python/)

**与 L3-2 Go baseline 关系**：
- v0.1-draft Go baseline 已归档（**不可变，仅参考**：`../../../archive/pre-python-2026-07-24/L3-a2a-core-spec-v0.1-draft-go-baseline.md` 1446 行）
- 本 v0.2 Spec **完全替代** Go baseline 的 Python 实现决策（官方 a2a-sdk envelope 复用 + ASGI + Uvicorn + Pydantic v2 + httpx + structlog + Pydantic v2 errors）
- 业务语义（6 method / 4 endpoint / 24 error code / Task FSM / mTLS / metric name）与 v0.1-draft Go baseline **完全一致**

**规范词**：
- **必须（MUST）**：违反即与已评审上游设计冲突。
- **应（SHOULD）**：默认实现；偏离需在 PR 中解释。
- **可以（MAY）**：兼容扩展点，不属于 v0.1 验收门禁。
- 本文代码块是**签名契约**，允许 L4 调整私有 helper，但不得改变 exported API 语义。

**明确不在本模块实现**：
- Agent 框架调用与事件翻译：**L3-3 Adapter SDK**。
- Agent 业务逻辑与 Hello Agent：**L3-4**。
- Knowledge 搜索、作用域继承、Memory 生命周期：**L3-5 / L3-6**。
- CRD reconcile、Deployment/Service/EndpointSlice 生命周期：**L3-1 Operator Core**。
- `a2a.cancelTask`、`a2a.subscribeTask`、SSE：v0.5+，本模块不得提前暴露。
- MCP：Agent ↔ Tool 协议，不得作为 A2A Core 依赖。

---

## 1. 模块使命与文件清单总览

### 1.1 使命

L3-2 A2A Core 文件级 Spec 将 [L2-1 Spec v0.2.0](../../spec/L2-module-specs/L2-a2a-protocol.md) 中描述的 **7 个子包 + 6 method + 4 endpoint + 24 error code + 15 Prometheus 指标 + ExtensionRouter Protocol** 落地为 **可直接对照编码的 Python 文件级契约**。

**单部署形态**：与 Knowledge Service + Memory backend 共享同 Deployment（**单实例 v0.1，单 Python 进程 / 单 Uvicorn worker**，ADR-0005 §6.2 单进程原则；K8s HPA 通过 Pod 副本数伸缩，不用 worker 进程内多并发）。

**L3-2 文件级 Spec v.s. L2-1 模块 Spec 边界**：

| 维度 | L2-1 模块 Spec | L3-2 文件级 Spec |
|---|---|---|
| **粒度** | 模块级（7 子包 + 6 method + 4 endpoint 概要） | 文件级（30 文件精确路径 + 每个文件的 import/exported/helper/测试文件） |
| **目的** | "为什么 + 是什么"（设计决策 + 模块契约） | "怎么做"（每个文件具体怎么写） |
| **读者** | 架构师 + L3 起草者 | L4 实施工程师（开发者打开 IDE 对照） |
| **变更频率** | 低（设计变更才改） | 中（实现微调可能改） |
| **测试 ID 范围** | 100 UT + IT + CF + E2E（§11.2 ID 矩阵 · v0.2 占位） | L3-2 不创造新测试 ID；**继承 L2-1 ID 矩阵**，仅在测试文件中将 ID 落实到具体文件路径 |

### 1.2 模块对外契约（public API surface · 继承 L2-1 Spec §1.2）

**Public API 入口**（仅暴露给其他 L2/L3 模块，本 L3-2 不变更）：

```python
# packages/a2a-core/src/superteam_a2a/a2a/__init__.py
"""A2A Core Library — communication layer of superteam-a2a.

Public surface: re-export upstream types + 4 routers + factory functions.
All business modules import from here, never from `a2a` directly.
"""
from superteam_a2a.a2a.upstream import (
    # SDK re-exports（仅枚举，禁止业务层绕过）
    AgentCard, Message, Part, Task, Artifact, TaskState,
    JSONRPCRequest, JSONRPCResponse, JSONRPCError,
)
from superteam_a2a.a2a.upstream_types import (
    # 项目私有 DTO
    QueryKnowledgeRequest, QueryKnowledgeResponse,
    GetKnowledgeItemRequest, GetKnowledgeItemResponse,
    RecordMemoryRequest, RecordMemoryResponse,
    QueryMemoryRequest, QueryMemoryResponse,
)
from superteam_a2a.a2a.server.app import create_app
from superteam_a2a.a2a.client.client import A2AClient
from superteam_a2a.a2a.errors import StandardRpcError, ProjectRpcError
from superteam_a2a.a2a.mtls import MtlsConfig, build_server_ssl_context, extract_spiffe_id
from superteam_a2a.a2a.extensions import (
    ExtensionRouter,
    QueryKnowledgeRouter, GetKnowledgeItemRouter,
    RecordMemoryRouter, QueryMemoryRouter,
)

__all__ = [
    # SDK re-exports
    "AgentCard", "Message", "Part", "Task", "Artifact", "TaskState",
    "JSONRPCRequest", "JSONRPCResponse", "JSONRPCError",
    # DTO
    "QueryKnowledgeRequest", "QueryKnowledgeResponse",
    "GetKnowledgeItemRequest", "GetKnowledgeItemResponse",
    "RecordMemoryRequest", "RecordMemoryResponse",
    "QueryMemoryRequest", "QueryMemoryResponse",
    # Server + Client
    "create_app", "A2AClient",
    # Errors
    "StandardRpcError", "ProjectRpcError",
    # mTLS
    "MtlsConfig", "build_server_ssl_context", "extract_spiffe_id",
    # Extension routers
    "ExtensionRouter",
    "QueryKnowledgeRouter", "GetKnowledgeItemRouter",
    "RecordMemoryRouter", "QueryMemoryRouter",
]
```

**boundary 强制**（ADR-0005 §3.2 + 宪法 §3.8）：
- 业务层（Knowledge Service / Memory backend / Operator / Adapter SDK）**禁止**直接 `import a2a`
- 仅允许 `from superteam_a2a.a2a import ...`
- CI 通过自定义 Ruff 规则 `ST-A2A-BOUNDARY` 检测（见 §11.4 占位）

### 1.3 文件清单总览（30 个 Python 文件 + 9 Helm 模板）

> **完整文件清单在 §2.3 表格中分 7 子包展开**。本 §1.3 给汇总 + 测试 ID 前缀分布。

**30 Python 文件分 7 子包 + 3 single-source**：

| 子包 | 文件数 | 职责一句话 | 测试 ID 前缀 |
|---|---|---|---|
| `a2a/` (顶层 single-source) | 3 | public surface + boundary + DTO + errors | UT-T-01~22 + UT-E-01~15 |
| `a2a/server/` | 4 | ASGI app 工厂 + 4 middleware + lifespan | UT-SRV-01~07 + UT-MW-01~22 + UT-SRV-32~36 |
| `a2a/client/` | 5 | A2AClient + Retry + CB + Discovery + P2C + AgentCardCache | UT-CLI-01~78 |
| `a2a/extensions/` | 6 | ExtensionRouter Protocol + 4 router 占位 + 注册器 | UT-EXT-01~22 |
| `a2a/mtls/` | 4 | SSLContext + SPIFFE + 热更新 | UT-MT-01~18 |
| `a2a/observability/` | 4 | metrics + tracing + logging + event_loop | UT-OB-01~30 |
| `a2a/utils/` | 2 | offload + helpers | UT-UT-01~10 |
| `a2a/_internal/` | 2 | ⚠️ private wire helpers | 无（单测 in 子包 UT） |
| **小计** | **30** | | |

注 1：`_internal/` 是 `__init__.py` + `_wire.py` 共 2 个文件；业务层禁止 import；测试通过 `_internal._wire` 直测。

注 2：第 31-39 文件为 **9 Helm 模板**（`deploy/helm/a2a-core/templates/*.yaml`）——非 Python 文件，在 `deploy/helm/a2a-core/` 下，本表不计入 30。

**9 Helm 模板**（L3-2 在 §12 Helm values 段展开 · 后续 #51+ 补完）：

```
deploy/helm/a2a-core/
├── Chart.yaml                            # Helm chart 元数据
├── values.yaml                           # 默认 Helm values（开发环境）
├── values.schema.json                    # JSON Schema（从 A2aCoreConfig Pydantic 自动生成）
└── templates/
    ├── deployment.yaml                   # A2A Core Deployment（单容器 + Uvicorn 单 worker）
    ├── service.yaml                      # Service（8443 mTLS + 9090 metrics）
    ├── serviceaccount.yaml               # ServiceAccount
    ├── configmap.yaml                    # A2aCoreConfig + Agent Card 模板
    ├── secret-tls.yaml                   # cert-manager 注解（tls.crt / tls.key / ca.crt）
    ├── networkpolicy.yaml                # NetworkPolicy（限制 Pod egress）
    ├── prometheusrule.yaml               # 15 指标告警规则
    ├── servicemonitor.yaml               # ServiceMonitor（15 指标抓取）
    └── podmonitor.yaml                   # PodMonitor（补充 runtime 4 指标）
```

**30 Python 测试文件**（镜像 `src/superteam_a2a/a2a/` 结构，在 `packages/a2a-core/tests/` 下，本 L3-2 不逐文件列出，在 §11 测试策略段按测试 ID 矩阵展开 · 后续 #51+ 补完）。

### 1.4 关键不变量（跨 L3-2 全文件清单适用）

- ✅ **`a2a.upstream` 是 SDK 唯一 import 入口**：业务层只 `from superteam_a2a.a2a import ...`，禁止直接 `import a2a`
- ✅ **4 个 extension router 占位 + L2-4 Knowledge/Memory 实际实现**：L3-2 不实现 router 业务逻辑，仅定义 Protocol + 占位类（L2-4 启动时 #51+ 补完实际实现）
- ✅ **mTLS 强制（cert-manager 挂载 + 证书热更新）**：缺失证书 → `MtlsConfigError` + readiness=false
- ✅ **Uvicorn 单 worker（ADR-0005 §6.2 单进程原则）**：`--workers 1` 强制；多副本通过 K8s HPA 伸缩
- ✅ **`anyio.to_thread.run_sync` CPU offload**：纯 CPU 计算（如 JSON Schema 校验）必须 offload
- ✅ **15 Prometheus 指标 metric name 不变**：`superteam_a2a_*` (11) + `superteam_python_*` (4)
- ✅ **6 method wire shape 不变**：`a2a.sendMessage` / `a2a.getTask` / `a2a.queryKnowledge` / `a2a.getKnowledgeItem` / `a2a.recordMemory` / `a2a.queryMemory`（`a2a.cancelTask` 占位 v0.5+）
- ✅ **24 error code 数字不变**：JSON-RPC 标准 5 + A2A 域 6 + Knowledge 7 + Memory 6 = 24 错误码（L3-2 落地为 `StandardRpcError` + `ProjectRpcError` 双 IntEnum）

---

## 2. Python 包结构（基于 L2-1 Design §3.1 落地）

### 2.1 顶级目录布局（uv workspace · ADR-0005 §13.1）

```
superteam-a2a/                            # uv workspace 根（由 L4 pyproject.toml 锁定）
└── packages/
    └── a2a-core/                         # 本模块 monorepo 子包
        ├── pyproject.toml                # uv workspace 成员；Python 3.12+；name=superteam-a2a-a2a-core
        │                                 # deps: a2a-sdk>=0.3 pydantic>=2.6 httpx>=0.27 opentelemetry-api>=1.27
        │                                 # opentelemetry-sdk>=1.27 opentelemetry-exporter-otlp>=1.27 structlog>=24.1
        │                                 # tenacity>=9 anyio>=4.4 prometheus-client>=0.20 cryptography>=42
        │                                 # pydantic-settings>=2.2 kubernetes-asyncio>=30
        ├── README.md                     # 模块说明（开发环境 quick start）
        ├── LICENSE                       # Apache-2.0
        ├── CHANGELOG.md                  # 变更记录（v0.2.0 起始）
        ├── src/
        │   └── superteam_a2a/
        │       └── a2a/                  # 本 Spec 详述 30 文件
        │           ├── __init__.py
        │           ├── upstream.py
        │           ├── upstream_types.py
        │           ├── errors.py
        │           ├── server/
        │           │   ├── __init__.py
        │           │   ├── app.py
        │           │   ├── middlewares.py
        │           │   └── lifespan.py
        │           ├── client/
        │           │   ├── __init__.py
        │           │   ├── client.py
        │           │   ├── retry.py
        │           │   ├── circuit_breaker.py
        │           │   ├── discovery.py
        │           │   └── agent_card_cache.py
        │           ├── extensions/
        │           │   ├── __init__.py
        │           │   ├── base.py
        │           │   ├── query_knowledge.py
        │           │   ├── get_knowledge_item.py
        │           │   ├── record_memory.py
        │           │   └── query_memory.py
        │           ├── mtls/
        │           │   ├── __init__.py
        │           │   ├── ssl_context.py
        │           │   ├── spiffe.py
        │           │   └── hot_reload.py
        │           ├── observability/
        │           │   ├── __init__.py
        │           │   ├── metrics.py
        │           │   ├── tracing.py
        │           │   ├── logging.py
        │           │   └── event_loop.py
        │           ├── utils/
        │           │   ├── __init__.py
        │           │   └── offload.py
        │           └── _internal/
        │               ├── __init__.py
        │               └── _wire.py
        └── tests/                        # 镜像 src/ 结构（30 测试文件 + 5 顶层 fixtures = 35）
            ├── __init__.py
            ├── conftest.py               # 顶层 pytest fixtures（k8s_mock / fake_clock / cert_gen）
            ├── upstream_test.py          # UT-T-01~07
            ├── upstream_types_test.py    # UT-T-08~22
            ├── errors_test.py            # UT-E-01~15
            ├── server/                   # mirror src/a2a/server/
            │   ├── __init__.py
            │   ├── app_test.py           # UT-SRV-01~07
            │   ├── middlewares_test.py   # UT-MW-01~22
            │   └── lifespan_test.py      # UT-SRV-32~36
            ├── client/                   # mirror src/a2a/client/
            │   ├── __init__.py
            │   ├── client_test.py        # UT-CLI-01~14
            │   ├── retry_test.py         # UT-CLI-44~53
            │   ├── circuit_breaker_test.py  # UT-CLI-54~61
            │   ├── discovery_test.py     # UT-CLI-23~34
            │   ├── discovery_k8s_test.py # UT-CLI-35~43
            │   ├── p2c_test.py           # UT-CLI-67~73
            │   ├── agent_card_cache_test.py  # UT-CLI-74~78
            │   └── fixtures/
            │       ├── fake_clock.py     # FakeClock（仅测试消费）
            │       ├── certs.py          # 临时 CA/server/client cert
            │       └── transport.py      # deterministic RoundTripper
            ├── extensions/               # mirror src/a2a/extensions/
            │   ├── __init__.py
            │   ├── base_test.py          # UT-EXT-01~05
            │   ├── query_knowledge_test.py  # UT-EXT-06~10
            │   ├── get_knowledge_item_test.py  # UT-EXT-11~15
            │   ├── record_memory_test.py # UT-EXT-16~18
            │   └── query_memory_test.py  # UT-EXT-19~22
            ├── mtls/                     # mirror src/a2a/mtls/
            │   ├── __init__.py
            │   ├── ssl_context_test.py   # UT-MT-01~06
            │   ├── spiffe_test.py        # UT-MT-07~12
            │   └── hot_reload_test.py    # UT-MT-13~18
            ├── observability/            # mirror src/a2a/observability/
            │   ├── __init__.py
            │   ├── metrics_test.py       # UT-OB-01~13
            │   ├── tracing_test.py       # UT-OB-14~20
            │   ├── logging_test.py       # UT-OB-21~26
            │   └── event_loop_test.py    # UT-OB-27~30
            ├── utils/                    # mirror src/a2a/utils/
            │   ├── __init__.py
            │   └── offload_test.py       # UT-UT-01~10
            ├── integration/              # IT 集成测试（envtest + kind 集群）
            │   ├── __init__.py
            │   ├── server_client_test.py # IT-A2A-01~05
            │   ├── mtls_test.py          # IT-A2A-06~09
            │   ├── discovery_test.py     # IT-A2A-10~12
            │   ├── observability_test.py # IT-A2A-13~14
            │   └── memory_route_test.py  # IT-A2A-15（fake handler，不 import memory）
            ├── conformance/              # CF 协议一致性测试（contract test 锁定）
            │   ├── __init__.py
            │   ├── envelope_test.py      # CF-A2A-01~05
            │   ├── methods_test.py       # CF-A2A-06~17
            │   └── errors_test.py        # CF-A2A-18~22
            ├── e2e/                      # E2E 端到端测试（kind 集群 + A2A 真实调用）
            │   ├── __init__.py
            │   ├── hello_agent_test.py   # E2E-A2A-01
            │   ├── knowledge_e2e_test.py  # E2E-A2A-02
            │   ├── memory_e2e_test.py     # E2E-A2A-03
            │   ├── mTLS_e2e_test.py       # E2E-A2A-04
            │   └── chaos_test.py          # E2E-A2A-05（故障注入）
            └── testdata/
                ├── cards/hello-agent.json
                ├── requests/*.json
                ├── responses/*.json
                └── malformed/*.json
```

### 2.2 边界规则（继承 L2-1 Spec §2.2 · ADR-0005 §3.2 · 6 条规则）

| # | 规则 | 含义 | 依据 |
|---|------|------|------|
| 1 | **`a2a.upstream` 是 SDK 唯一 import 入口** | 业务层禁止 `import a2a`，仅 `from superteam_a2a.a2a import ...` | 宪法 §3.8 + ADR-0005 §3.2 |
| 2 | **A2A Core 不依赖业务模块** | A2A Core 不 import L2-3 Adapter / L2-4 Knowledge / L2-4 Memory / L3-1 Operator | ADR-0005 §3.2 + L1 Arch §3.4 |
| 3 | **A2A Core 不实现 Knowledge/Memory 业务语义** | 4 个 extension router 由 L2-4 Knowledge/Memory 提供；A2A Core 仅定义 Protocol + 注册 | L2-4 Design §3.2 + ADR-0003 §6 |
| 4 | **A2A Core 不调用 K8s API** | A2A Core 是无状态 server/client（仅做方法路由 + wire codec），不调用 K8s API；CRD lifecycle 由 L3-1 Operator 负责 | ADR-0005 §6 + L1 Arch §3.4 |
| 5 | **Uvicorn 单 worker（单进程）** | `--workers 1` 强制；多副本通过 K8s HPA 伸缩 | ADR-0005 §6.2 + 宪法 §3.8 |
| 6 | **`anyio.to_thread.run_sync` CPU offload** | 纯 CPU 计算（JSON Schema 校验、加密解密）必须 offload | ADR-0005 §6.3 + 宪法 §6 |

**lint 规则**：自定义 Ruff 规则 `ST-A2A-BOUNDARY`（§11.4 占位）扫描 `^import a2a` / `^from a2a` 模式；命中即失败。

### 2.3 文件清单（7 子包 + 30 Python 文件详细）

#### 2.3.1 `a2a/` 顶层 single-source（3 文件 · boundary 核心）

| 文件路径 | 职责 | exported 符号 | helper | 关联测试 |
|---|---|---|---|---|
| `__init__.py` | public surface（§1.2）| `__all__`（约 20 符号 re-export） | 无 | `tests/__init__.py` |
| `upstream.py` | ⚠️ boundary — SDK 唯一 import 入口 | SDK 类型的 re-export（`AgentCard`, `Message`, `Part`, `Task`, `Artifact`, `TaskState`, `JSONRPCRequest`, `JSONRPCResponse`, `JSONRPCError`） | `_validate_sdk_version()` | `tests/upstream_test.py` (UT-T-01~07) |
| `upstream_types.py` | 项目私有 Pydantic DTO（§3.3 4 method schema） | `KnowledgeScopeLevel`, `QueryKnowledgeRequest`, `QueryKnowledgeResponse`, `KnowledgeItemSummary`, `GetKnowledgeItemRequest`, `GetKnowledgeItemResponse`, `MemoryContentType`, `RecordMemoryRequest`, `RecordMemoryResponse`, `MemoryVisibility`, `QueryMemoryRequest`, `QueryMemoryResponse`, `MemorySummary` | `_validate_idempotency_key()` | `tests/upstream_types_test.py` (UT-T-08~22) |

#### 2.3.2 `a2a/server/` 子包（4 文件 · ASGI app 工厂 + 4 middleware + lifespan）

| 文件路径 | 职责 | exported 符号 | helper | 关联测试 |
|---|---|---|---|---|
| `server/__init__.py` | 导出 `create_app` 工厂 | `create_app` | 无 | `tests/server/__init__.py` |
| `server/app.py` | `create_app()` ASGI 工厂（Starlette + Mount SDK jsonrpc_app + extension sub-app + 4 endpoint） | `def create_app(config: A2aCoreConfig) -> Starlette` | `_mount_jsonrpc_app()`, `_mount_extensions()`, `_add_health_endpoints()` | `tests/server/app_test.py` (UT-SRV-01~07) + `tests/integration/server_client_test.py` (IT-A2A-01~05) |
| `server/middlewares.py` | 4 个 ASGI middleware（auth + ratelimit + recovery + trace） | `class AuthMiddleware`, `class RateLimitMiddleware`, `class RecoveryMiddleware`, `class TraceMiddleware` | `_extract_spiffe_from_cert()`, `_token_bucket_check()` | `tests/server/middlewares_test.py` (UT-MW-01~22) |
| `server/lifespan.py` | asynccontextmanager 生命周期（启动/停止 + graceful shutdown） | `@asynccontextmanager async def lifespan(app: Starlette) -> AsyncIterator[None]` | `_startup_observability()`, `_shutdown_observability()` | `tests/server/lifespan_test.py` (UT-SRV-32~36) |

#### 2.3.3 `a2a/client/` 子包（5 文件 · A2AClient + Retry + CB + Discovery + P2C + Cache）

| 文件路径 | 职责 | exported 符号 | helper | 关联测试 |
|---|---|---|---|---|
| `client/__init__.py` | 导出 `A2AClient` | `A2AClient` | 无 | `tests/client/__init__.py` |
| `client/client.py` | `A2AClient`（基于 `httpx.AsyncClient` + 6 typed wrappers） | `class A2AClient`, `async def send_message()`, `async def get_task()`, `async def query_knowledge()`, `async def get_knowledge_item()`, `async def record_memory()`, `async def query_memory()`, `async def aclose()` | `_build_request_payload()`, `_parse_response_payload()` | `tests/client/client_test.py` (UT-CLI-01~14) + `tests/integration/server_client_test.py` (IT-A2A-01~05) |
| `client/retry.py` | `RetryPolicy`（Tenacity wrapper + idempotency gate） | `class RetryDecision`(StrEnum), `METHOD_IDEMPOTENT`(frozenset), `@dataclass class RetryPolicy`, `def should_retry(method, error) -> RetryDecision` | `_compute_backoff()` | `tests/client/retry_test.py` (UT-CLI-44~53) |
| `client/circuit_breaker.py` | `CircuitBreaker` + `P2CSelector`（closed/open/half-open + 2-random endpoint selection） | `class CircuitBreaker`, `class CircuitState`(StrEnum), `class P2CSelector` | `_is_half_open_probe_due()` | `tests/client/circuit_breaker_test.py` (UT-CLI-54~61) |
| `client/discovery.py` | `Discovery`（K8s Service + EndpointSlice watch + Agent Card 拉取） | `@dataclass class Endpoint`, `@dataclass class AgentTarget`, `class Discovery`, `async def resolve_dns()` | `_list_endpoint_slices()`, `_watch_endpoint_slices()` | `tests/client/discovery_test.py` (UT-CLI-23~34) + `tests/integration/discovery_test.py` (IT-A2A-10~12) |
| `client/agent_card_cache.py` | TTL cache + invalidation | `class AgentCardCache`, `class CacheKey`(frozen=True) | `_compute_cache_key()` | `tests/client/agent_card_cache_test.py` (UT-CLI-74~78) |

#### 2.3.4 `a2a/extensions/` 子包（6 文件 · 4 extension router 占位）

| 文件路径 | 职责 | exported 符号 | helper | 关联测试 |
|---|---|---|---|---|
| `extensions/__init__.py` | 4 router re-export + 自动注册 | `def discover_routers()`, `async def dispatch(request)` | `_DISCOVERED: dict` | `tests/extensions/__init__.py` |
| `extensions/base.py` | `ExtensionRouter` Protocol | `@runtime_checkable class ExtensionRouter(Protocol)`, `method_name: str`, `async def handle()` | 无 | `tests/extensions/base_test.py` (UT-EXT-01~05) |
| `extensions/query_knowledge.py` | 占位 + Protocol 实现类（业务由 L2-4 Knowledge Service 实现） | `class QueryKnowledgeRouter(implements ExtensionRouter)`, `method_name = "a2a.queryKnowledge"`, `async def handle()` | `_validate_request()` | `tests/extensions/query_knowledge_test.py` (UT-EXT-06~10) |
| `extensions/get_knowledge_item.py` | 占位 + Protocol 实现类 | `class GetKnowledgeItemRouter(implements ExtensionRouter)`, `method_name = "a2a.getKnowledgeItem"`, `async def handle()` | `_validate_request()` | `tests/extensions/get_knowledge_item_test.py` (UT-EXT-11~15) |
| `extensions/record_memory.py` | 占位 + Protocol 实现类 | `class RecordMemoryRouter(implements ExtensionRouter)`, `method_name = "a2a.recordMemory"`, `async def handle()` | `_validate_idempotency_key()` | `tests/extensions/record_memory_test.py` (UT-EXT-16~18) |
| `extensions/query_memory.py` | 占位 + Protocol 实现类 | `class QueryMemoryRouter(implements ExtensionRouter)`, `method_name = "a2a.queryMemory"`, `async def handle()` | `_validate_request()` | `tests/extensions/query_memory_test.py` (UT-EXT-19~22) |

#### 2.3.5 `a2a/mtls/` 子包（4 文件 · SSLContext + SPIFFE + 热更新）

| 文件路径 | 职责 | exported 符号 | helper | 关联测试 |
|---|---|---|---|---|
| `mtls/__init__.py` | 导出 `MtlsConfig` + `build_server_ssl_context` + `extract_spiffe_id` | `MtlsConfig`, `build_server_ssl_context`, `extract_spiffe_id` | 无 | `tests/mtls/__init__.py` |
| `mtls/ssl_context.py` | `build_server_ssl_context` 构造 mTLS server SSLContext | `@dataclass class MtlsConfig`, `def build_server_ssl_context(config) -> ssl.SSLContext`, `class MtlsConfigError` | `_load_pem_file()`, `_check_key_permissions()` | `tests/mtls/ssl_context_test.py` (UT-MT-01~06) + `tests/integration/mtls_test.py` (IT-A2A-06~09) |
| `mtls/spiffe.py` | `extract_spiffe_id` 从客户端证书 URI SAN 解析 SPIFFE ID | `def extract_spiffe_id(cert) -> str \| None`, `class SpiffeIdFormatError`, `def validate_spiffe_id()` | `_parse_uri_san()` | `tests/mtls/spiffe_test.py` (UT-MT-07~12) |
| `mtls/hot_reload.py` | 证书热更新（每 5min 检查 + atomic 替换） | `class CertHotReloader`, `async def watch_and_reload()`, `async def reload_now()` | `_is_cert_expiring_soon()`, `_atomic_replace()` | `tests/mtls/hot_reload_test.py` (UT-MT-13~18) |

#### 2.3.6 `a2a/observability/` 子包（4 文件 · 15 指标 + OTel + structlog + event loop）

| 文件路径 | 职责 | exported 符号 | helper | 关联测试 |
|---|---|---|---|---|
| `observability/__init__.py` | 导出 `A2aMetrics` + `StructuredLogger` + `TracerProvider` + `EventLoopMonitor` | 4 个 facade 类 | 无 | `tests/observability/__init__.py` |
| `observability/metrics.py` | `A2aMetrics`（15 Prometheus 指标 = 11 A2A + 4 runtime） | `class A2aMetrics`, 15 个 `Counter`/`Gauge`/`Histogram`, `def render_latest() -> bytes` | `_labels_from_request()`, `_record_retry()` | `tests/observability/metrics_test.py` (UT-OB-01~13) + `tests/integration/observability_test.py` (IT-A2A-13~14) |
| `observability/tracing.py` | OTel provider 注入 + tracer 工厂 | `def init_tracing(service_name, otlp_endpoint, sample_ratio) -> TracerProvider`, `def tracer(name) -> Tracer` | `_create_otlp_exporter()` | `tests/observability/tracing_test.py` (UT-OB-14~20) |
| `observability/logging.py` | structlog setup（必含字段 6 个 + 敏感字段禁记） | `def configure_logging(level: str, json_format: bool) -> None`, `def get_logger(name) -> BoundLogger` | `_sensitive_filter()`, `_add_trace_context()` | `tests/observability/logging_test.py` (UT-OB-21~26) |
| `observability/event_loop.py` | event-loop lag 监控（每 10s 采样） | `class EventLoopMonitor`, `async def start()`, `async def stop()` | `_sample_lag()` | `tests/observability/event_loop_test.py` (UT-OB-27~30) |

#### 2.3.7 `a2a/utils/` 子包（2 文件 · CPU offload）

| 文件路径 | 职责 | exported 符号 | helper | 关联测试 |
|---|---|---|---|---|
| `utils/__init__.py` | 导出 `offload_cpu` | `offload_cpu` | 无 | `tests/utils/__init__.py` |
| `utils/offload.py` | `anyio.to_thread.run_sync` CPU offload 封装 | `async def offload_cpu(func, *args, **kwargs) -> Any`, `class ThreadPoolStats` | `_get_default_limiter()` | `tests/utils/offload_test.py` (UT-UT-01~10) |

#### 2.3.8 `a2a/_internal/` 子包（2 文件 · private · 业务层禁 import）

| 文件路径 | 职责 | exported 符号 | helper | 关联测试 |
|---|---|---|---|---|
| `_internal/__init__.py` | private boundary | （空或仅 `_wire` re-export） | 无 | 无（子包 UT 内联测试） |
| `_internal/_wire.py` | 内部 wire helpers（JSON-RPC envelope 解析 + 时间戳格式化 + UUID 生成） | `def parse_envelope(raw) -> JSONRPCRequest`, `def format_response(response) -> bytes`, `def generate_uuid7() -> str`, `def to_rfc3339(dt) -> str` | `_validate_envelope_shape()` | 无（单测通过 server/client UT 间接覆盖） |

### 2.4 wire contract 不变性（与 L2-1 Spec §0 完全一致 · contract test 锁定）

- ✅ **JSON 字段名**：camelCase（`messageId` / `taskId` / `itemId` / `memoryId` / `agentId` / `scopeLevel` / `scopeId` / `contentType` / `expiresAt` / `recordedAt` / `updatedAt` / `createdAt`）
- ✅ **时间格式**：RFC 3339（`2026-07-27T12:34:56.789Z`）· Pydantic `datetime` 序列化
- ✅ **错误码语义**：JSON-RPC 2.0 标准 5 码 + A2A 域 6 码 + Knowledge 7 码 + Memory 6 码 = **24 错误码**（L3-2 落地为 `StandardRpcError` + `ProjectRpcError` 双 IntEnum）
- ✅ **Agent Card 路径**：`GET /.well-known/agent.json`（SDK 标准）
- ✅ **JSON-RPC 路径**：`POST /a2a/jsonrpc`（标准与扩展方法同一路径）
- ✅ **健康/就绪端点**：`GET /healthz` + `GET /readyz` + `GET /metrics`
- ✅ **mTLS over HTTP/2 preferred**：ALPN `["h2", "http/1.1"]`
- ✅ **15 Prometheus 指标名**（与 L1 v0.2.0 Spec §16 + L1 Arch §9.2 完全一致）：
  - `superteam_a2a_rpc_total` / `superteam_a2a_rpc_duration_seconds` / `superteam_a2a_active_streams` / `superteam_a2a_circuit_breaker_state` / `superteam_a2a_retry_total` / `superteam_a2a_discovery_watch_reconnects_total` / `superteam_a2a_agent_card_cache_hits_total` / `superteam_a2a_cert_reload_failures_total` / `superteam_a2a_extension_router_dispatch_total` / `superteam_a2a_request_body_bytes` / `superteam_a2a_response_body_bytes` = **11 指标**
  - `superteam_python_event_loop_lag_seconds` / `superteam_python_thread_offload_queue_depth` / `superteam_python_active_asyncio_tasks` / `superteam_python_gc_collections_total` = **4 指标**
  - **合计 15 指标**
- ✅ **6 method 名**（与 v0.1 baseline 完全一致）：
  - `a2a.sendMessage` / `a2a.getTask` / `a2a.queryKnowledge` / `a2a.getKnowledgeItem` / `a2a.recordMemory` / `a2a.queryMemory`
  - `a2a.cancelTask` 占位（v0.5+ 启用）

---

## 3. compatibility adapter（4 个项目扩展 method · 继承 L2-1 Spec §3）

### 3.1 架构（与 L2-1 Design §4.2 一致）

```
Starlette App
├── Mount("/") → SDK jsonrpc_app       # sendMessage / getTask / cancelTask
├── Mount("/") → extension sub-app    # queryKnowledge / getKnowledgeItem / recordMemory / queryMemory
├── Route("/.well-known/agent.json")  # SDK 提供
├── Route("/healthz")                 # L3-2 liveness
├── Route("/readyz")                  # L3-2 readiness
└── Route("/metrics")                 # Prometheus exposition
```

**关键不变量**：
- 标准 method（`sendMessage` / `getTask`）由官方 `a2a-sdk` envelope + handler 提供
- 4 个项目扩展 method（Knowledge/Memory）由 L3-2 `extensions/` 子包定义 Protocol + 占位实现，L2-4 Knowledge Service / Memory backend 启动时通过 `discover_routers()` 注册实际实现
- L3-2 仅定义 Protocol + 占位类 + 注册流程；**不**实现业务逻辑

### 3.2 ExtensionRouter Protocol（继承 L2-1 Spec §3.2）

```python
# packages/a2a-core/src/superteam_a2a/a2a/extensions/base.py
from typing import Protocol, runtime_checkable
from superteam_a2a.a2a.upstream import JSONRPCRequest, JSONRPCResponse, JSONRPCError


@runtime_checkable
class ExtensionRouter(Protocol):
    """项目扩展 method router 协议。

    L3-2 通过 inspect 找出所有实现类；L2-4 Knowledge/Memory 模块
    提供具体实现（QueryKnowledgeRouter 等）。
    """

    method_name: str  # e.g. "a2a.queryKnowledge"

    async def handle(
        self, request: JSONRPCRequest
    ) -> JSONRPCResponse | JSONRPCError:
        """处理单个 JSON-RPC 请求；返回响应或错误。"""
        ...
```

**实现约束**：
- 必须定义类属性 `method_name: str`
- 必须实现 `async def handle(JSONRPCRequest) -> JSONRPCResponse | JSONRPCError`
- 不允许重复 `method_name`（启动期 `ValueError`）
- 实现类必须 `from .base import ExtensionRouter; class XxxRouter:` 显式继承（`@runtime_checkable` 要求）

### 3.3 4 个扩展 method 的 Pydantic schema（项目私有 DTO · 继承 L2-1 Spec §3.3）

> **本节列出 Pydantic schema 的关键约束；完整 schema 见 [`docs/spec/L2-module-specs/L2-a2a-protocol.md` §3.3](../../spec/L2-module-specs/L2-a2a-protocol.md)**。L3-2 在 `upstream_types.py` 中落地这些 schema。

#### 3.3.1 `a2a.queryKnowledge`

- **Request**：`query: str (1-2048)` + `scope_level: KnowledgeScopeLevel` + `scope_id: str (1-253)` + `agent_id: str (1-253)` + `top_k: int (1-100, default=10)` + `min_score: float (0.0-1.0, default=0.0)` + `include_body: bool (default=False)` + `traceparent: str | None`
- **Response**：`items: list[KnowledgeItemSummary]` + `total: int` + `next_cursor: str | None (base64 opaque)`
- **KnowledgeItemSummary**：`item_id` + `title` + `scope_level` + `scope_id` + `score` + `snippet | None` + `updated_at` + `version`

#### 3.3.2 `a2a.getKnowledgeItem`

- **Request**：`item_id: str (1-253)` + `version: int | None`（None → latest）+ `traceparent: str | None`
- **Response**：`item_id` + `title` + `body: str`（>10KB 截断 + `truncated=True`）+ `mime_type: str ("text/markdown")` + `scope_level` + `scope_id` + `agent_private_owner: str | None` + `version` + `created_at` + `updated_at`

#### 3.3.3 `a2a.recordMemory`

- **Request**：`idempotency_key: str (8-128, alphanumeric + -/_)` + `scope_level` + `scope_id` + `agent_id` + `content_type: MemoryContentType` + `content: str (1-8192)` + `confidence: float (0.0-1.0)` + `referenced_items: list[str] (max 32)` + `referenced_task_id: str | None` + `traceparent: str | None`
- **Response**：`memory_id: str` + `recorded_at: datetime` + `expires_at: datetime`（decay 公式计算）
- **idempotency 强制**：ADR-0003 §6 + L2-4 Design §6.2；`recordMemory` 不可重试除非 `idempotency_key`

#### 3.3.4 `a2a.queryMemory`

- **Request**：`query: str (1-2048)` + `scope_level | None`（None → 全 scope）+ `scope_id: str | None` + `agent_id: str`（必须：决定私有维度）+ `visibility: MemoryVisibility (default INHERITED)` + `content_types: list[MemoryContentType] | None` + `min_confidence: float (0.0-1.0, default=0.3)` + `top_k: int (1-100, default=20)` + `include_expired: bool (default=False)` + `traceparent: str | None`
- **Response**：`memories: list[MemorySummary]` + `total: int` + `next_cursor: str | None`
- **MemorySummary**：`memory_id` + `content_preview: str (前 100 字符)` + `content_type` + `confidence` + `scope_level` + `scope_id` + `agent_id`（持有者）+ `visibility` + `created_at` + `expires_at` + `decay_score: float`

### 3.4 router 注册流程（继承 L2-1 Spec §3.4）

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


async def dispatch(request: JSONRPCRequest) -> JSONRPCResponse | JSONRPCError:
    """根据 request.method 分发到对应 router。

    未注册 method 返回 JSONRPCError(code=-32601, message="Method not found")。
    """
    router = _DISCOVERED.get(request.method)
    if router is None:
        return JSONRPCError(
            id=request.id,
            code=StandardRpcError.METHOD_NOT_FOUND,
            message=f"Method not found: {request.method}",
        )
    return await router.handle(request)
```

**L3-2 占位 vs L2-4 实际实现关系**：
- L3-2 在 `extensions/query_knowledge.py` 等 4 文件定义占位类，handle 方法仅做参数校验 + 返回 TODO 错误
- L2-4 启动时在 Knowledge Service / Memory backend 启动 hook 中调用 `discover_routers()` 覆盖 `_DISCOVERED` 字典
- 实际生产路径：L2-4 实现的 router 类必须 import 自 `superteam_a2a.knowledge.routers` 等业务路径，**禁止** L2-4 反向 import L3-2 占位类

### 3.5 6 method wire 元数据（继承 L2-1 Spec §3.5 + ADR-0003 §6）

| Method | Idempotent | 自动重试 | capability | 备注 |
|--------|------------|----------|------------|------|
| `a2a.sendMessage` | 仅携带同一 `taskId` 时 | 是，需 `taskId` | `task-send` | 业务侧按 `idempotency_key` 决定 |
| `a2a.getTask` | 是 | 是 | `task-read` | 读方法 |
| `a2a.queryKnowledge` | 是（读取） | 是 | `knowledge-query` | 读方法 |
| `a2a.getKnowledgeItem` | 是 | 是 | `knowledge-get` | 读方法 |
| `a2a.recordMemory` | 否 | 否 | `memory-record` | 写方法；不可重试除非 `idempotency_key` |
| `a2a.queryMemory` | 是 | 是 | `memory-query` | 读方法 |

> L2 设计 §7.2 的文字表述存在 "queryKnowledge 黑名单/白名单" 同句歧义；L2 最终意图和读取语义均指向**白名单**，本 L3-2 锁定 `queryKnowledge` 为可重试。

---

## 4. mTLS / SPIFFE（ADR-0005 §9.1 + 宪法 §6.1 · 继承 L2-1 Spec §4）

### 4.1 cert-manager 挂载契约

```
Pod
└── /etc/tls/                 # volumeMount: cert-manager Secret
    ├── tls.crt               # server certificate (PEM)
    ├── tls.key               # server private key (PEM)
    └── ca.crt                # client CA bundle (PEM, 用于 mTLS 验证)
```

**文件存在性检查**（启动期）：3 个文件必须存在且非空；缺失 → `MtlsConfigError` + readiness=false。

### 4.2 build_server_ssl_context 契约（继承 L2-1 Spec §4.2）

```python
# packages/a2a-core/src/superteam_a2a/a2a/mtls/ssl_context.py
import ssl
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class MtlsConfig:
    cert_dir: Path = Path("/etc/tls")
    min_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_3
    verify_mode: ssl.VerifyMode = ssl.VerifyMode.CERT_REQUIRED
    spiffe_required: bool = True  # False → 仅校验 cert，不解析 SPIFFE ID


def build_server_ssl_context(config: MtlsConfig = MtlsConfig()) -> ssl.SSLContext:
    """构造 mTLS server SSLContext。

    Returns:
        ssl.SSLContext 配置好的 server context

    Raises:
        MtlsConfigError: cert/key 文件缺失或格式错误
    """
    # 实现契约：见 L3-2 Spec §4.6
    ...


class MtlsConfigError(RuntimeError):
    """cert/key 文件缺失或解析失败。"""
```

**约束**：
- 最低 TLS 1.3（`ctx.minimum_version = ssl.TLSVersion.TLSv1_3`）
- 客户端证书必须校验（`ctx.verify_mode = ssl.CERT_REQUIRED`）
- 私钥文件 mode 必须 0600（启动期 `stat.S_IMODE` 检查）
- ALPN 协议：`["h2", "http/1.1"]`（mTLS over HTTP/2 preferred）

### 4.3 extract_spiffe_id 契约（继承 L2-1 Spec §4.3）

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
    ...
```

### 4.4 证书热更新契约（继承 L2-1 Spec §4.4 + ADR-0005 §9.1）

```python
# packages/a2a-core/src/superteam_a2a/a2a/mtls/hot_reload.py
class CertHotReloader:
    """证书热更新（每 5min 检查 + atomic 替换）。

    启动期一次性 load_from_disk()；后台 task 每 5min 触发 watch_and_reload()。
    替换使用 atomic snapshot（旧 SSLContext 引用数降为 0 才回收）。
    """
    def __init__(
        self,
        config: MtlsConfig,
        reload_interval_seconds: float = 300.0,
    ): ...

    async def start(self) -> None:
        """启动后台 reload task；幂等。"""
        ...

    async def stop(self) -> None:
        """停止后台 task；幂等。"""
        ...

    def current_context(self) -> ssl.SSLContext:
        """返回当前有效的 SSLContext（atomic 引用）。"""
        ...

    async def _reload_if_expired(self) -> bool:
        """检查证书是否即将过期（<24h），若是则 reload；返回是否触发 reload。"""
        ...
```

**关键不变量**：
- reload 触发条件：证书剩余有效期 < 24h OR cert 文件 mtime 变化
- 替换使用 `context.set_alpn_protocols()` 不可变约束 → 每次 reload 新建 `ssl.SSLContext`，Uvicorn 引用计数降为 0 后由 GC 回收
- reload 失败不中断服务（保留旧 context + 记录告警 + emit metric `superteam_a2a_cert_reload_failures_total`）

### 4.5 与 Uvicorn 集成（继承 L2-1 Spec §4.5 + L3-2 §5.2）

Uvicorn 启动时通过 `ssl_keyfile` / `ssl_certfile` / `ssl_ca_certs` / `ssl_alpn_protocols` 4 参数挂载 mTLS：

```bash
uvicorn superteam_a2a.a2a.server.app:create_app \
  --factory \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile /etc/tls/tls.key \
  --ssl-certfile /etc/tls/tls.crt \
  --ssl-ca-certs /etc/tls/ca.crt \
  --ssl-alpn-protocols h2,http/1.1 \
  --workers 1
```

### 4.6 `mtls/` 子包 4 文件级契约概要

| 文件 | 完整实现要点 | 关联测试 ID |
|------|--------------|------------|
| `mtls/__init__.py` | 导出 `MtlsConfig` + `build_server_ssl_context` + `extract_spiffe_id` + `CertHotReloader` | (子包 UT) |
| `mtls/ssl_context.py` | 实现 `build_server_ssl_context`：① load PEM 文件 → ② check key permissions 0600 → ③ set min_version + verify_mode → ④ set ALPN → ⑤ return SSLContext | UT-MT-01~06 + IT-A2A-06~09 |
| `mtls/spiffe.py` | 实现 `extract_spiffe_id` + `validate_spiffe_id`：使用 `cryptography.x509` 解析 URI SAN；格式校验（spiffe:// 前缀 + trust_domain 一致） | UT-MT-07~12 |
| `mtls/hot_reload.py` | 实现 `CertHotReloader`：asyncio task 周期检查 + atomic 替换 + 失败回退旧 context | UT-MT-13~18 |

---

## 5. ASGI server 与单进程原则（ADR-0005 §6.2 + 宪法 §3.8 · 继承 L2-1 Spec §6）

### 5.1 进程模型

**单进程 / 单 worker / 多副本**：
- A2A Core 单 Pod = 单 Python 进程 = 单 Uvicorn worker（`--workers 1`）
- 多副本通过 K8s `Deployment.spec.replicas` 伸缩（建议 2-3 副本 + HPA）
- **禁止** `--workers N>1`：会破坏 in-process 状态（ExtensionRouter 注册表、Agent Card cache、Discovery watch）

### 5.2 create_app 工厂契约

```python
# packages/a2a-core/src/superteam_a2a/a2a/server/app.py
from starlette.applications import Starlette
from superteam_a2a.a2a.config import A2aCoreConfig


def create_app(config: A2aCoreConfig) -> Starlette:
    """ASGI app 工厂。

    装配流程：
    1. 创建 Starlette()
    2. Mount SDK jsonrpc_app（标准 3 method）
    3. Mount extension sub-app（4 project method）
    4. Add 4 health/metrics endpoints
    5. Add 4 middlewares（auth + ratelimit + recovery + trace）
    6. Set lifespan (lifespan.py)
    7. discover_routers() 4 extension router
    8. return app

    注意：Uvicorn 启动期在 --factory 模式下调用；不接受运行时配置变更。
    """
    ...
```

### 5.3 启动契约（uvicorn CLI · 继承 L2-1 Spec §6.3）

```bash
# L4 启动命令（生产环境）
uvicorn superteam_a2a.a2a.server.app:create_app \
  --factory \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile /etc/tls/tls.key \
  --ssl-certfile /etc/tls/tls.crt \
  --ssl-ca-certs /etc/tls/ca.crt \
  --ssl-alpn-protocols h2,http/1.1 \
  --workers 1 \
  --log-level info \
  --access-log \
  --proxy-headers
```

### 5.4 优雅停机时序

```
SIGTERM → Uvicorn 收到信号
  → lifespan.shutdown() 触发
    → EventLoopMonitor.stop()
    → CertHotReloader.stop()
    → A2AClient.aclose()（in-process client pool）
    → AgentCardCache.flush()
    → Discovery.stop()（停止 EndpointSlice watch）
    → metrics.render_latest() 最后一次
  → exit 0
```

### 5.5 `server/` 子包 4 文件级契约概要

| 文件 | 完整实现要点 | 关联测试 ID |
|------|--------------|------------|
| `server/__init__.py` | 导出 `create_app` | (子包 UT) |
| `server/app.py` | 实现 `create_app(config)`：① Starlette 工厂 → ② Mount SDK jsonrpc_app → ③ Mount extension sub-app → ④ Add 4 routes (agent_card/healthz/readyz/metrics) → ⑤ Add 4 middlewares → ⑥ lifespan 注入 → ⑦ discover_routers() | UT-SRV-01~07 + IT-A2A-01~05 |
| `server/middlewares.py` | 实现 4 ASGI middleware：① AuthMiddleware（从 peer cert 提取 SPIFFE ID + 注入 contextvar）② RateLimitMiddleware（token bucket 100 RPS / burst 200）③ RecoveryMiddleware（panic → -32603）④ TraceMiddleware（W3C traceparent 注入 + server span） | UT-MW-01~22 |
| `server/lifespan.py` | 实现 `lifespan(app)`：① startup 阶段（observability init + mtls context build + cert hot reload start + agent card cache warmup）② shutdown 阶段（逆序） | UT-SRV-32~36 |

---

## 6. Discovery + Client（K8s-native · 继承 L2-1 Spec §5）

### 6.1 Discovery 路径（继承 L2-1 Spec §5.1）

**In-Cluster**：
- 目标 Agent Service：`{agent-name}.{namespace}.svc.cluster.local:8443`
- Agent Card 路径：`GET https://{target}/.well-known/agent.json`

**EndpointSlice watch**：
- 启动期 list 一次 → 后续 watch（`resourceVersion` 续传）
- watch reconnect：断连后 backoff 重连，指数退避 1s → 30s
- Agent Card cache：TTL 默认 300s（Helm values 可配）；cache key = `(namespace, name, version)`

**Discovery 类契约**：

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
    agent_card_url: str  # https://{name}.{namespace}.svc.cluster.local:8443/.well-known/agent.json


class Discovery:
    """K8s Service / EndpointSlice watch + Agent Card 缓存。"""

    LABEL_SELECTOR = "superteam-a2a.io/component=agent"

    def __init__(
        self,
        k8s_client: kubernetes_asyncio.client.CoreV1Api,
        agent_card_ttl_seconds: float = 300.0,
        watch_reconnect_seconds: float = 5.0,
    ):
        ...

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

### 6.2 DNS fallback（继承 L2-1 Spec §5.2）

```python
async def resolve_dns(target: str) -> list[str]:
    """socket.getaddrinfo → IP 列表（IPv4 + IPv6）。

    用于无 K8s RBAC 权限的客户端路径（开发环境）。
    """
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(target, 8443, type=socket.SOCK_STREAM)
    return list({i[4][0] for i in infos})
```

### 6.3 A2AClient 契约（继承 L2-1 Spec §5.3）

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
    ):
        ...

    async def send_message(
        self, target: str, message: Message
    ) -> Task:
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

    async def query_memory(
        self, target: str, request: QueryMemoryRequest
    ) -> QueryMemoryResponse:
        """a2a.queryMemory 调用。"""
        ...

    async def aclose(self) -> None:
        """关闭底层 httpx 连接池；幂等。"""
        ...
```

### 6.4 Retry 策略（Tenacity wrapper · 继承 L2-1 Spec §5.4）

```python
# packages/a2a-core/src/superteam_a2a/a2a/client/retry.py
from dataclasses import dataclass
from enum import StrEnum


class RetryDecision(StrEnum):
    """按 method + error code 判断是否重试。"""
    DO_RETRY = "do-retry"
    DO_NOT_RETRY = "do-not-retry"
    METHOD_NOT_IDEMPOTENT = "method-not-idempotent"


# method_idempotency 表（与 L2-1 Spec §5.4 + ADR-0003 §6 一致）
METHOD_IDEMPOTENT = frozenset({
    "a2a.sendMessage",   # 业务侧按 idempotency_key 决定
    "a2a.getTask",
    "a2a.getKnowledgeItem",
    "a2a.queryKnowledge",
    "a2a.queryMemory",
    # "a2a.recordMemory" — NOT idempotent（除非 idempotency_key）
})


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_seconds: float = 0.5
    max_delay_seconds: float = 10.0
    backoff_multiplier: float = 2.0
    jitter: bool = True


def should_retry(method: str, error_code: int, attempt: int, policy: RetryPolicy) -> RetryDecision:
    """判断是否重试。

    逻辑：
    1. attempt >= max_attempts → DO_NOT_RETRY
    2. method not in METHOD_IDEMPOTENT → METHOD_NOT_IDEMPOTENT
    3. error_code 是 retryable 集合 → DO_RETRY
    4. else → DO_NOT_RETRY
    """
    ...
```

### 6.5 Circuit Breaker + P2C（继承 L2-1 Spec §5.5）

```python
# packages/a2a-core/src/superteam_a2a/a2a/client/circuit_breaker.py
class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class CircuitBreaker:
    """per-endpoint 熔断器（closed → open → half-open → closed）。"""

    def __init__(
        self,
        failure_threshold: int = 5,
        open_duration_seconds: float = 30.0,
        half_open_max_probes: int = 3,
    ): ...

    def record_success(self) -> None: ...
    def record_failure(self) -> None: ...
    def can_request(self) -> bool: ...
    def state(self) -> CircuitState: ...


class P2CSelector:
    """Power of Two Choices endpoint 选择器。"""

    def __init__(self, endpoints: list[Endpoint]): ...

    def select(self) -> Endpoint:
        """随机选 2 个 endpoint，挑 in-flight 数少的。"""
        ...
```

### 6.6 限流（token bucket · 继承 L2-1 Spec §5.6）

- **Server-side**：`RateLimitMiddleware` 全 Server 令牌桶 `100 RPS / burst 200`
- **PerKey=true** 时按 caller SPIFFE ID 限流（`PerKey` 默认 false）
- **Client-side**：`A2AClient` 自带 token bucket（默认 50 RPS / burst 100），防止客户端过载

### 6.7 `client/` 子包 5 文件级契约概要

| 文件 | 完整实现要点 | 关联测试 ID |
|------|--------------|------------|
| `client/__init__.py` | 导出 `A2AClient` + `RetryPolicy` + `CircuitBreaker` + `Discovery` | (子包 UT) |
| `client/client.py` | 实现 `A2AClient`：`httpx.AsyncClient` 封装 + 6 typed wrappers + retry/CB/timeout 集成 | UT-CLI-01~14 + IT-A2A-01~05 |
| `client/retry.py` | 实现 `RetryPolicy` + `should_retry`：Tenacity `@retry` decorator + idempotency gate | UT-CLI-44~53 |
| `client/circuit_breaker.py` | 实现 `CircuitBreaker` + `P2CSelector`：状态机 closed/open/half-open + 2-random endpoint selection | UT-CLI-54~61 + UT-CLI-67~73 |
| `client/discovery.py` | 实现 `Discovery` + `resolve_dns`：kubernetes_asyncio watch + Agent Card 拉取 + DNS fallback | UT-CLI-23~34 + UT-CLI-35~43 + IT-A2A-10~12 |
| `client/agent_card_cache.py` | 实现 `AgentCardCache`：TTL 缓存 + 失效（Discovery 事件触发） | UT-CLI-74~78 |

---

## 7. async-first + CPU offload（ADR-0005 §6.1 / §6.3 · 继承 L2-1 Spec §7）

### 7.1 async 边界规则

- **所有 I/O 函数 `async def`**：httpx / kubernetes_asyncio / asyncio 集成
- **CPU 密集计算走 `offload_cpu`**：JSON Schema 校验、加密解密、序列化/反序列化
- **禁止 `asyncio.run()` in async context**：使用 `asyncio.get_running_loop()`
- **禁止 blocking call in handler**：httpx 是 async，但 `requests` / `subprocess.run` / `time.sleep` 禁止

### 7.2 offload_cpu 契约（继承 L2-1 Spec §7.2）

```python
# packages/a2a-core/src/superteam_a2a/a2a/utils/offload.py
import anyio
from functools import partial
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


async def offload_cpu(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """anyio.to_thread.run_sync 封装。

    限制器默认 capacity=40（来自 anyio 默认）。
    用于纯 CPU 计算：JSON Schema 校验、加密解密、Pydantic model 序列化等。
    """
    ...


class ThreadPoolStats:
    """线程池统计（供 metrics 采集）。"""

    @property
    def current_threads(self) -> int: ...
    @property
    def idle_threads(self) -> int: ...
    @property
    def total_tasks_processed(self) -> int: ...
```

### 7.3 event-loop lag 监控（继承 L2-1 Spec §7.3）

```python
# packages/a2a-core/src/superteam_a2a/a2a/observability/event_loop.py
class EventLoopMonitor:
    """每 10s 采样 event loop lag → 写入 `superteam_python_event_loop_lag_seconds` Histogram。"""

    SAMPLE_INTERVAL_SECONDS = 10.0

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
```

### 7.4 取消与异常处理

- `asyncio.CancelledError` 必须向上传播（不可 swallow）
- 业务异常用 `try/except` 显式捕获后转换为 JSONRPCError（不可 silently drop）
- `httpx.TimeoutException` / `httpx.ConnectError` 转换为 retryable A2ATimeoutError
- `CircuitOpenError` 是非 retryable（直接返回 client 错误）

### 7.5 `utils/` 子包 2 文件级契约概要

| 文件 | 完整实现要点 | 关联测试 ID |
|------|--------------|------------|
| `utils/__init__.py` | 导出 `offload_cpu` + `ThreadPoolStats` | (子包 UT) |
| `utils/offload.py` | 实现 `offload_cpu` + `ThreadPoolStats`：`anyio.to_thread.run_sync` 包装 + limiter 状态读取 | UT-UT-01~10 |

---

## 8. 错误模型（与 v0.1.0 + L1 Spec §5.7 + §8.3 完全一致 · 继承 L2-1 Spec §8）

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

### 8.2 错误码 Python enum（24 错误码 · 继承 L2-1 Spec §8.2）

```python
# packages/a2a-core/src/superteam_a2a/a2a/errors.py
from enum import IntEnum


class StandardRpcError(IntEnum):
    """JSON-RPC 2.0 标准错误码 + 项目扩展错误码。

    数字与 L1 Spec §5.7 + v0.1.0 Go baseline 完全一致；contract test 锁定。
    """
    # 标准 JSON-RPC（5 码）
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # A2A 域（6 码 · SDK 提供 + 项目扩展）
    TASK_NOT_FOUND = -32001
    TASK_TIMEOUT = -32002
    TASK_CANCELLED = -32003
    UNAUTHORIZED = -32004
    FORBIDDEN = -32005
    RATE_LIMIT = -32006

    # 项目扩展（Knowledge 范围 · 7 码 · ADR-0002 §2）
    KNOWLEDGE_SCOPE_NOT_FOUND = -32400
    KNOWLEDGE_ITEM_NOT_FOUND = -32401
    KNOWLEDGE_VERSION_NOT_FOUND = -32402
    KNOWLEDGE_QUERY_TOO_LONG = -32403
    KNOWLEDGE_INVALID_TYPE = -32404
    KNOWLEDGE_FORBIDDEN = -32405
    KNOWLEDGE_INTERNAL_ERROR = -32406

    # 项目扩展（Memory 范围 · 6 码 · ADR-0003 §6）
    MEMORY_SCOPE_NOT_FOUND = -32500
    MEMORY_INVALID_CONTENT = -32501
    MEMORY_FORBIDDEN = -32502
    MEMORY_RATE_LIMIT = -32503
    MEMORY_QUERY_TOO_BROAD = -32504
    MEMORY_INTERNAL_ERROR = -32505


class ProjectRpcError(IntEnum):
    """项目扩展错误码子集（仅 Knowledge + Memory）。"""
    KNOWLEDGE_SCOPE_NOT_FOUND = StandardRpcError.KNOWLEDGE_SCOPE_NOT_FOUND
    KNOWLEDGE_ITEM_NOT_FOUND = StandardRpcError.KNOWLEDGE_ITEM_NOT_FOUND
    KNOWLEDGE_VERSION_NOT_FOUND = StandardRpcError.KNOWLEDGE_VERSION_NOT_FOUND
    KNOWLEDGE_QUERY_TOO_LONG = StandardRpcError.KNOWLEDGE_QUERY_TOO_LONG
    KNOWLEDGE_INVALID_TYPE = StandardRpcError.KNOWLEDGE_INVALID_TYPE
    KNOWLEDGE_FORBIDDEN = StandardRpcError.KNOWLEDGE_FORBIDDEN
    KNOWLEDGE_INTERNAL_ERROR = StandardRpcError.KNOWLEDGE_INTERNAL_ERROR
    MEMORY_SCOPE_NOT_FOUND = StandardRpcError.MEMORY_SCOPE_NOT_FOUND
    MEMORY_INVALID_CONTENT = StandardRpcError.MEMORY_INVALID_CONTENT
    MEMORY_FORBIDDEN = StandardRpcError.MEMORY_FORBIDDEN
    MEMORY_RATE_LIMIT = StandardRpcError.MEMORY_RATE_LIMIT
    MEMORY_QUERY_TOO_BROAD = StandardRpcError.MEMORY_QUERY_TOO_BROAD
    MEMORY_INTERNAL_ERROR = StandardRpcError.MEMORY_INTERNAL_ERROR
```

**错误码总数**：5 + 6 + 7 + 6 = **24 错误码**（与 L2-1 Spec §8.2 一致）。

### 8.3 错误响应构造（继承 L2-1 Spec §8.3）

```python
# packages/a2a-core/src/superteam_a2a/a2a/errors.py
from superteam_a2a.a2a.upstream import JSONRPCError, JSONRPCRequest


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

### 8.4 Retryable 矩阵（与 L2-1 Spec §5.4 表一致 · 继承 L2-1 Spec §8.4）

| Code range | name | Retryable | HTTP Status |
|------|------|-----------|-------------|
| -32700 ~ -32602 | 标准 JSON-RPC | ❌ | 400 / 404 / 422 |
| -32603 | INTERNAL_ERROR | ✅ | 500 |
| -32001 ~ -32006 | A2A 域 | 部分（TIMEOUT/RATE_LIMIT retryable）| 404 / 504 / 401 / 403 / 429 |
| -32400 ~ -32406 | KNOWLEDGE_* | ❌ | 4xx |
| -32500 ~ -32505 | MEMORY_* | ❌ | 4xx |

### 8.5 `errors.py` + `observability/` 子包 4 文件级契约概要

| 文件 | 完整实现要点 | 关联测试 ID |
|------|--------------|------------|
| `errors.py` | 实现 `StandardRpcError` + `ProjectRpcError` + `make_error_response` | UT-E-01~15 |
| `observability/__init__.py` | 导出 4 facade（`A2aMetrics` + `StructuredLogger` + `TracerProvider` + `EventLoopMonitor`） | (子包 UT) |
| `observability/metrics.py` | 实现 `A2aMetrics`：15 个指标（11 A2A + 4 runtime） | UT-OB-01~13 + IT-A2A-13~14 |
| `observability/tracing.py` | 实现 `init_tracing` + `tracer`：OTel provider 注入 + 显式 factory | UT-OB-14~20 |
| `observability/logging.py` | 实现 `configure_logging` + `get_logger`：structlog setup + 6 必含字段 + 敏感字段过滤 | UT-OB-21~26 |
| `observability/event_loop.py` | 实现 `EventLoopMonitor`：asyncio task 周期采样 event loop lag | UT-OB-27~30 |

---

## 9. 可观测性（Python 全栈 · 沿用 v0.1 metric name · 继承 L2-1 Spec §9）

### 9.1 Prometheus 指标（与 L1 v0.2.0 Spec §16 + L1 Arch §9.2 完全一致 · 11 + 4 = 15 指标）

| 指标 | 类型 | Labels | 触发点 | 单位 |
|------|------|--------|--------|------|
| `superteam_a2a_rpc_total` | Counter | `agent`, `method`, `status` | server middleware（每个 method 调用） | requests |
| `superteam_a2a_rpc_duration_seconds` | Histogram | `agent`, `method` | server middleware | seconds |
| `superteam_a2a_active_streams` | Gauge | — | SSE handler（v0.5+，v0.1 留位） | streams |
| `superteam_a2a_circuit_breaker_state` | Gauge | `target`, `state` | CircuitBreaker 状态变化 | 0/1/2 |
| `superteam_a2a_retry_total` | Counter | `method`, `attempt` | RetryPolicy | retries |
| `superteam_a2a_discovery_watch_reconnects_total` | Counter | `namespace` | EndpointSlice watch | reconnects |
| `superteam_a2a_agent_card_cache_hits_total` | Counter | `cache` | AgentCard cache | hits |
| `superteam_a2a_cert_reload_failures_total` | Counter | — | CertHotReloader | failures |
| `superteam_a2a_extension_router_dispatch_total` | Counter | `method`, `status` | extensions dispatch | dispatches |
| `superteam_a2a_request_body_bytes` | Histogram | `method` | server middleware | bytes |
| `superteam_a2a_response_body_bytes` | Histogram | `method` | server middleware | bytes |
| `superteam_python_event_loop_lag_seconds` | Histogram | `component` | §7.3 后台 task | seconds |
| `superteam_python_thread_offload_queue_depth` | Gauge | `pool` | anyio limiter stats | tasks |
| `superteam_python_active_asyncio_tasks` | Gauge | — | `len(asyncio.all_tasks())` 采样 | tasks |
| `superteam_python_gc_collections_total` | Counter | `generation` | `gc.get_stats()` 采样 | collections |

**指标总数**：11 (RPC + circuit + retry + discovery + cache + cert + extension + body bytes 2) + 4 (Python runtime) = **15 指标**（与 L2-1 Spec §9.1 一致）。

**label 基数约束**（L1 Arch §9.2）：
- `agent`：受控（同一集群 < 1000）
- `method`：固定 6 个
- `target`：受控（per-endpoint CB）
- `status`：固定 4 个（success / error / timeout / cancelled）
- `component`：固定 5 个（a2a-core / knowledge / memory / operator / adapter）

### 9.2 Trace（OpenTelemetry Python SDK · W3C Trace Context · 继承 L2-1 Spec §9.2）

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

### 9.3 日志（structlog + stdlib logging · 继承 L2-1 Spec §9.3）

**必含字段**（与 L1 Spec §9.3 一致）：`trace_id` / `agent` / `method` / `task_id` / `namespace` / `ts`

**敏感字段禁记**（ADR-0005 §10）：API Key / Token / 用户数据 / Memory content / Knowledge body / cert 原文 / private key

```python
# packages/a2a-core/src/superteam_a2a/a2a/observability/logging.py
import logging
import structlog


_SENSITIVE_KEYS = frozenset({
    "api_key", "token", "password", "secret",
    "memory_content", "knowledge_body", "tls_key", "private_key",
})


def configure_logging(level: str = "INFO", json_format: bool = True) -> None:
    """配置 structlog + stdlib logging。"""
    ...


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取带必含字段的 logger。"""
    ...
```

### 9.4 `observability/` 子包 4 文件级契约概要

见 §8.5 表格（observability/ 4 文件级契约概要）。

---

## 10. 上游追踪责任（宪法 §13.6 + ADR-0005 §13.6 · 继承 L2-1 Spec §10）

### 10.1 维护责任（继承 L2-1 Spec §10.1）

L3-2 实施者 + 维护者必须：

- ✅ **每 minor release** 检查 [`a2aproject/a2a-python`](https://github.com/a2aproject/a2a-python) 仓库 changelog；评估 API 兼容性 + wire shape 影响
- ✅ **每次 SDK 升级** 跑完整 conformance suite（§11.3）+ 项目 contract test（§10.2）+ L3-2 全部 30 测试文件
- ✅ **每次 SDK 升级** 评估 `protocolVersion` 变化与 L1 协议版本基线（v0.3）的兼容；若 SDK 升至 0.4+ 需走 §10.3 major upgrade 流程
- ✅ **跟踪 a2aproject/A2A 主仓库** 规范变化（每周 review 1 次 issue + PR 列表）
- ✅ **依赖与版本锁定**：`pyproject.toml` 中 `a2a-sdk>=0.3,<0.4` 约束 minor + patch 范围；lockfile 提交仓库
- ✅ **L4 PR 反向上游**：发现的 SDK bug 提交 PR 至 `a2aproject/a2a-python`（L4 → SDK 闭环）
- ✅ **公网 RFC 跟踪**：参与 [a2aproject/A2A discussions](https://github.com/a2aproject/A2A/discussions)；评估新 spec 章节影响

**L3-2 与 L2-1 / L3-1 / L3-3 的上游追踪责任划分**：

| 模块 | SDK 责任 | Helm/K8s 责任 | Test 责任 |
|------|----------|---------------|-----------|
| **L3-2 A2A Core** | a2a-sdk 全部 | Uvicorn / Starlette / cert-manager | contract test + conformance |
| L3-1 Operator Core | 无（不依赖 a2a-sdk） | Kopf / kubernetes_asyncio | envtest + leader failover |
| L3-3 Adapter SDK | a2a-sdk client 部分 + Agent 框架 SDK 6 类 | 无（in-process plugin 或 sidecar） | framework mock + 6 framework matrix |
| L2-1 A2A Protocol | a2a-sdk 全部（与 L3-2 重叠 · L3-2 落地） | 无（仅 spec） | wire shape contract test |

### 10.2 contract test 套件（wire shape + envelope 锁定 · 继承 L2-1 Spec §10.2）

**目标**：保证 L3-2 与 v0.1.0 Go baseline + L2-1 Python v0.2.0 的 wire contract 100% 一致；SDK 升级时如发现差异则立即阻断。

```python
# packages/a2a-core/tests/contract/test_a2a_python_compat.py
import pytest
from pydantic import TypeAdapter
from superteam_a2a.a2a.upstream import AgentCard, Message, Task
from superteam_a2a.a2a.errors import StandardRpcError
from a2a.types import AgentCard as SdkAgentCard  # upstream 验证
from tests.testdata import LOAD_FIXTURE  # fixture 加载器


class TestWireShapeContract:
    """wire shape 必须与 v0.1.0 Go baseline 完全一致。"""

    def test_agent_card_wire_shape(self):
        """AgentCard JSON dump 与 v0.1.0 fixture 完全一致。"""
        card = AgentCard(name="hello-agent", version="0.2.0", ...)
        dumped = card.model_dump(by_alias=True, mode="json")
        assert dumped == LOAD_FIXTURE("agent_card_v0_1_0.json")

    def test_jsonrpc_envelope_compat(self):
        """JSON-RPC envelope 字段与 v0.1.0 一致。"""
        req = JSONRPCRequest(jsonrpc="2.0", id="req-1", method="a2a.sendMessage", params={...})
        dumped = req.model_dump(by_alias=True, mode="json")
        assert dumped == LOAD_FIXTURE("jsonrpc_request_v0_1_0.json")

    def test_error_codes_match(self):
        """错误码数字与 L1 Spec §5.7 一致（24 码）。"""
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
        local = AgentCard(name="hello", version="0.2.0", ...)
        sdk = SdkAgentCard.model_validate(local.model_dump(by_alias=True))
        assert local.model_dump(by_alias=True) == sdk.model_dump(by_alias=True)
```

**测试 ID 前缀**：`CT-A2A-`（Contract Test A2A）共 5 ID（CT-A2A-001~005）
- CT-A2A-001 AgentCard wire shape 一致
- CT-A2A-002 JSON-RPC envelope wire shape 一致
- CT-A2A-003 24 错误码数值一致
- CT-A2A-004 时间格式 RFC 3339
- CT-A2A-005 SDK AgentCard 互转 round-trip

**CI 必跑**：`pytest tests/contract/ -v --tb=short`；如失败则阻断 SDK 升级 + 立即回归 L2-1 Python 评审。

### 10.3 upgrade 决策（ADR-0005 §11 + 继承 L2-1 Spec §10.3）

**semver 升级矩阵**：

| 升级类型 | 版本变化 | 决策流程 | 风险评估 |
|----------|----------|----------|----------|
| **patch** | 0.3.x → 0.3.x+1 | 自动（contract test pass → 升级） | 低（bug fix only） |
| **minor** | 0.3.x → 0.4.0 | 跑完整 conformance + E2E + 评估 API 变更；不破坏 wire 时直接升级 | 中（API 新增/弃用） |
| **major** | 0.x → 1.0 | **走 ADR**（评估 protocolVersion 升级 + wire 不变性）| 高（breaking change） |

**patch 升级自动流程**（`pyproject.toml` + `uv.lock`）：
```bash
# 自动 patch 升级（CI 月度任务）
uv lock --upgrade-package a2a-sdk
uv sync --frozen
pytest tests/contract/ tests/conformance/ -v  # contract + conformance 全 PASS
# PASS → 提交 uv.lock + 触发 E2E
# FAIL → 阻断升级 + 通知 a2a-sdk 上游 + 评估是否走 minor 流程
```

**minor 升级半自动流程**：
1. Review SDK changelog（`a2aproject/a2a-python/CHANGELOG.md`）
2. 跑完整 30 测试文件（UT/IT/CF/E2E）= 100+ ID
3. 评估 API 弃用/新增（grep `from a2a.types import` + `isinstance`）
4. 评估 wire shape 变化（contract test 全 PASS 即无变化）
5. 升级 `pyproject.toml` 的 `a2a-sdk>=0.4,<0.5` + 更新 lockfile
6. 提交 PR + 走 L2-1 评审（参照 #22 L2-1 Python 评审 31KB / 488 行 / 10 维度）

**major 升级走 ADR 流程**：
1. **新 ADR**：`docs/adr/0006-a2a-sdk-1.0-upgrade.md`（或新版本号）
2. **新协议版本**：`protocolVersion` 升级评估（v0.3 → v1.0 wire 不变 vs 变）
3. **wire 不变性评估**：是否破坏 `agent_card_v0_1_0.json` / `jsonrpc_request_v0_1_0.json` / 错误码数字 / Task FSM
4. **宪法升级**：若 wire 变 → 走宪法 v0.6.0+ 升级流程
5. **新 L1/L2/L3 评审**：3 层评审 + 跨文档同步

---

## 11. 测试策略（ADR-0005 §11 + 宪法 §9.7 · 继承 L2-1 Spec §11）

### 11.1 测试层级金字塔（继承 L2-1 Spec §11.1 · 6 层级）

| 层级 | 工具 | 覆盖率目标 | 关键场景 | 占比 |
|------|------|------------|----------|------|
| **Unit (UT)** | `pytest` + `pytest-asyncio` | ≥ 90%（`a2a.upstream` / `a2a.upstream_types` / `a2a.errors` ≥ 95%） | Pydantic 校验 / JSON-RPC envelope / 错误码映射 / mTLS context / 路由分发 / Retry 计算 / CircuitBreaker 状态机 / AgentCardCache TTL | 60% |
| **Property** | `Hypothesis` + `hypothesis-jsonschema` | N/A（fuzz-based）| 任意 JSON-RPC request 不崩溃；wire 序列化反序列化 round-trip | 5% |
| **HTTP mock (HTTP)** | `respx` / ASGI test client | timeout / 取消 / 重试 / mTLS 失败 / 5xx / Retry-After | httpx mock + 各种失败路径 | 10% |
| **SDK compat (CT)** | 自研 contract test + SDK 自带 conformance | wire shape + 错误码 + envelope 100% | 锁定 v0.1.0 wire；minor 升级跑过 | 5% |
| **Integration (IT)** | `envtest` + `kind` + `kubernetes_asyncio` 真实 watch | reconcile / webhook / leader failover / EndpointSlice watch reconnect / AgentCard 拉取过 mTLS / 多 namespace watch RBAC | ADR-0005 §7 12 项门禁 | 15% |
| **E2E** | `kind` + Helm | Hello Agent + Workflow + Knowledge + Memory 全链路 / mTLS 真实握手 / chaos 故障注入 | 完整业务流程 | 5% |

**测试 ID 总数估算**：30 UT 文件 × 4-5 case/文件 ≈ **100+ ID**（继承 L2-1 100 ID · L3-2 新增 5-10 ID 用于 cert hot reload + agent card cache + observability 等 Python 特有场景）。

### 11.2 测试 ID 矩阵（完整清单 · 105 ID · 继承 L2-1 100 + L3-2 新增 5）

> **9 大类测试 ID 前缀分布**（与 L3-1 Operator Core 测试 ID 前缀 11 类同模式）：

| 类别 | ID 前缀 | 数量 | 说明 |
|------|---------|------|------|
| Pydantic schema | `UT-T-` | 12 | 4 扩展 method × 3 case（valid / invalid / boundary）|
| JSON-RPC envelope | `UT-T-` | 8 | wire shape + 错误码序列化 + 透传 |
| 错误码映射 | `UT-E-` | 17 | 17 标准 + A2A 域错误码 × 1 case（Knowledge/Memory 6+6 走 ExtensionRouter 单独测试）|
| ExtensionRouter | `UT-EXT-` | 12 | 4 router × 3 case（dispatch / unknown / duplicate）|
| mTLS context | `UT-MT-` | 8 | ssl.SSLContext 构造 + SPIFFE 解析 + 文件缺失 + 私钥 mode 校验 |
| Retry policy | `UT-CLI-` | 6 | 退避计算 + idempotency gate + max attempts |
| Circuit breaker | `UT-CLI-` | 8 | 3 状态转换 + threshold + half-open probe |
| Discovery | `UT-CLI-` | 6 | EndpointSlice mock + AgentCard cache TTL |
| Property | `PROP-` | 5 | envelope round-trip + arbitrary JSON-RPC 不崩溃 |
| HTTP mock | `HTTP-` | 8 | timeout / 取消 / 重试 / mTLS 失败 / Retry-After / Circuit OPEN |
| SDK compat | `CT-` | 5 | wire shape + 错误码 + envelope 锁定 |
| Integration | `IT-` | 5 | watch reconnect + agent card pull + 多 namespace + cert hot reload + cert expiry |
| E2E | `E2E-` | 3 | hello-agent + workflow + chaos |
| **L3-2 新增** | `UT-OB-` / `UT-MT-` | **5** | event_loop_lag + observability 15 指标 + cert hot reload atomic + agent card cache invalidation + tracing OTel |
| **合计** | — | **105** | — |

**测试 ID 完整清单**（按文件分类，参照 L2-1 Spec §11.2 ID 命名规范 · 限定 L3-2 文件级映射）：

#### 11.2.1 `tests/upstream_test.py` (UT-T-01~07 · 7 ID)

```
UT-T-01: AgentCard Pydantic v2 strict mode 拒绝 extra field
UT-T-02: Message MessageID UUIDv7 合法
UT-T-03: Part.type=text 时 text 必填
UT-T-04: Part.type=file 时 fileUri 必填 + 绝对 URL
UT-T-05: TaskStatus 转换合法性（同状态幂等 / 跨状态合法）
UT-T-06: JSONRPCRequest id string/整数/null 三种类型兼容
UT-T-07: JSONRPCError code/message/data 序列化
```

#### 11.2.2 `tests/upstream_types_test.py` (UT-T-08~22 · 15 ID)

```
UT-T-08: QueryKnowledgeRequest 合法 + top_k=10
UT-T-09: QueryKnowledgeRequest query="" → ValidationError
UT-T-10: QueryKnowledgeRequest scope_level 非法 → ValidationError
UT-T-11: GetKnowledgeItemRequest 合法
UT-T-12: GetKnowledgeItemRequest item_id="" → ValidationError
UT-T-13: GetKnowledgeItemRequest version=0 → ValidationError
UT-T-14: RecordMemoryRequest 合法 + idempotency_key="abc-123"
UT-T-15: RecordMemoryRequest 缺 idempotency_key → ValidationError
UT-T-16: RecordMemoryRequest idempotency_key 含特殊字符 → ValidationError
UT-T-17: QueryMemoryRequest 合法 + visibility=AGENT_PRIVATE
UT-T-18: QueryMemoryRequest scope_level + scope_id 不一致 → ValidationError
UT-T-19: QueryMemoryRequest min_confidence > 1.0 → ValidationError
UT-T-20: KnowledgeItemSummary score 范围校验
UT-T-21: MemorySummary content_preview 截断 100 字符
UT-T-22: MemoryContentType 枚举值唯一
```

#### 11.2.3 `tests/errors_test.py` (UT-E-01~15 · 15 ID)

```
UT-E-01 ~ UT-E-05:   5 标准 JSON-RPC 码 wire + name
UT-E-06 ~ UT-E-11:   6 A2A 域错误码 wire + name
UT-E-12 ~ UT-E-15:   4 关键 Knowledge 错误码 wire (KNOWLEDGE_SCOPE_NOT_FOUND / KNOWLEDGE_ITEM_NOT_FOUND / KNOWLEDGE_VERSION_NOT_FOUND / KNOWLEDGE_FORBIDDEN)
```

#### 11.2.4 `tests/server/app_test.py` (UT-SRV-01~07 · 7 ID)

```
UT-SRV-01: create_app 返回 Starlette 实例
UT-SRV-02: create_app Mount SDK jsonrpc_app
UT-SRV-03: create_app Mount extension sub-app
UT-SRV-04: create_app 4 routes (agent_card / healthz / readyz / metrics) 注册
UT-SRV-05: create_app 4 middlewares (auth + ratelimit + recovery + trace) 注册
UT-SRV-06: lifespan contextmanager 装配正确
UT-SRV-07: discover_routers 启动期调用
```

#### 11.2.5 `tests/server/middlewares_test.py` (UT-MW-01~22 · 22 ID)

```
UT-MW-01: AuthMiddleware 从 peer cert 提取 SPIFFE ID
UT-MW-02: AuthMiddleware 注入 contextvar
UT-MW-03: AuthMiddleware 缺 SPIFFE → 401
UT-MW-04: AuthMiddleware trust_domain 不匹配 → 401
UT-MW-05: RateLimitMiddleware token bucket 100 RPS
UT-MW-06: RateLimitMiddleware burst 200
UT-MW-07: RateLimitMiddleware 超限 → 429
UT-MW-08: RateLimitMiddleware PerKey=false 时全局桶
UT-MW-09: RateLimitMiddleware PerKey=true 时按 SPIFFE ID 分桶
UT-MW-10: RecoveryMiddleware panic → -32603
UT-MW-11: RecoveryMiddleware 不 swallow CancelledError
UT-MW-12: TraceMiddleware W3C traceparent 注入
UT-MW-13: TraceMiddleware server span 开启
UT-MW-14: TraceMiddleware OTel context 注入
UT-MW-15 ~ UT-MW-22: 8 组合场景（auth+ratelimit / auth+trace / recovery+trace 等）
```

#### 11.2.6 `tests/server/lifespan_test.py` (UT-SRV-32~36 · 5 ID)

```
UT-SRV-32: lifespan.startup 阶段 observability init
UT-SRV-33: lifespan.startup 阶段 mtls context build
UT-SRV-34: lifespan.startup 阶段 cert hot reload start
UT-SRV-35: lifespan.shutdown 阶段逆序
UT-SRV-36: lifespan SIGTERM 优雅停机 < 30s
```

#### 11.2.7 `tests/client/client_test.py` (UT-CLI-01~14 · 14 ID)

```
UT-CLI-01: A2AClient send_message 成功
UT-CLI-02: A2AClient get_task 成功
UT-CLI-03: A2AClient query_knowledge 成功
UT-CLI-04: A2AClient get_knowledge_item 成功
UT-CLI-05: A2AClient record_memory 成功
UT-CLI-06: A2AClient query_memory 成功
UT-CLI-07: A2AClient aclose 幂等
UT-CLI-08: A2AClient aclose 后调用 → ClientError
UT-CLI-09: A2AClient ssl_context 必填
UT-CLI-10: A2AClient timeout 默认 30s
UT-CLI-11: A2AClient max_connections 默认 100
UT-CLI-12: A2AClient discovery=None 时不启用 K8s watch
UT-CLI-13: A2AClient metrics=None 时不记录 metric
UT-CLI-14: A2AClient httpx 连接池复用
```

#### 11.2.8 `tests/client/retry_test.py` (UT-CLI-44~53 · 10 ID)

```
UT-CLI-44: RetryPolicy 默认 max_attempts=3
UT-CLI-45: compute_delay(0) = 0.5 ± jitter
UT-CLI-46: compute_delay(3) 接近 max_delay
UT-CLI-47: should_retry sendMessage 失败 + idempotency_key → DO_RETRY
UT-CLI-48: should_retry recordMemory 无 idempotency_key → METHOD_NOT_IDEMPOTENT
UT-CLI-49: should_retry recordMemory + idempotency_key → DO_RETRY
UT-CLI-50: should_retry getTask + INVALID_PARAMS → DO_NOT_RETRY
UT-CLI-51: should_retry attempt >= max → DO_NOT_RETRY
UT-CLI-52: should_retry method not in METHOD_IDEMPOTENT → METHOD_NOT_IDEMPOTENT
UT-CLI-53: should_retry 错误码在 retryable 集合 → DO_RETRY
```

#### 11.2.9 `tests/client/circuit_breaker_test.py` (UT-CLI-54~61 + 67~73 · 15 ID)

```
UT-CLI-54: CircuitBreaker CLOSED 失败 < threshold → 保持 CLOSED
UT-CLI-55: CircuitBreaker CLOSED 失败 >= threshold → OPEN
UT-CLI-56: CircuitBreaker OPEN 超时 → HALF_OPEN
UT-CLI-57: CircuitBreaker HALF_OPEN 成功 → CLOSED
UT-CLI-58: CircuitBreaker HALF_OPEN 失败 → OPEN
UT-CLI-59: CircuitBreaker can_request 状态机
UT-CLI-60: CircuitBreaker state metric 上报
UT-CLI-61: CircuitBreaker failure_threshold 默认 5
UT-CLI-67: P2C select endpoints=[] → ValueError
UT-CLI-68: P2C select endpoints=1 → random choice
UT-CLI-69: P2C select endpoints=10 → 选 2 个 pick 最低
UT-CLI-70: P2C select in-flight count 跟踪
UT-CLI-71: P2C select 并发安全
UT-CLI-72: P2C select 同 in-flight 时 random
UT-CLI-73: P2C select metric 上报
```

#### 11.2.10 `tests/client/discovery_test.py` + `discovery_k8s_test.py` (UT-CLI-23~43 · 21 ID)

```
UT-CLI-23: Discovery start 触发首次 list
UT-CLI-24: Discovery start 触发后续 watch
UT-CLI-25: Discovery list_targets namespace=None 时全 namespace
UT-CLI-26: Discovery list_targets namespace="x" 时过滤
UT-CLI-27: Discovery watch_targets ADDED 事件
UT-CLI-28: Discovery watch_targets MODIFIED 事件
UT-CLI-29: Discovery watch_targets DELETED 事件
UT-CLI-30: Discovery watch reconnect backoff 1s → 30s
UT-CLI-31: Discovery get_agent_card TTL 内复用
UT-CLI-32: Discovery get_agent_card TTL 外重新拉取
UT-CLI-33: Discovery get_agent_card 404 → 标记不可达
UT-CLI-34: Discovery LABEL_SELECTOR = "superteam-a2a.io/component=agent"
UT-CLI-35 ~ UT-CLI-43: 9 K8s 集成场景（EndpointSlice mock / RBAC / watch resourceVersion 续传 / 多 namespace 并发 / 故障转移等）
```

#### 11.2.11 `tests/client/agent_card_cache_test.py` (UT-CLI-74~78 · 5 ID)

```
UT-CLI-74: AgentCardCache TTL 默认 300s
UT-CLI-75: AgentCardCache hit 返回缓存
UT-CLI-76: AgentCardCache miss 触发 fetch
UT-CLI-77: AgentCardCache invalidate 立即失效
UT-CLI-78: AgentCardCache 并发安全（asyncio.Lock）
```

#### 11.2.12 `tests/extensions/` (UT-EXT-01~22 · 22 ID)

```
UT-EXT-01: ExtensionRouter Protocol runtime_checkable
UT-EXT-02: QueryKnowledgeRouter.method_name == "a2a.queryKnowledge"
UT-EXT-03: discover_routers 检测重复 method_name → ValueError
UT-EXT-04: dispatch 已知 method → router.handle
UT-EXT-05: dispatch 未知 method → -32601 METHOD_NOT_FOUND
UT-EXT-06: QueryKnowledgeRouter 参数校验
UT-EXT-07: QueryKnowledgeRouter scope_level 非法
UT-EXT-08: QueryKnowledgeRouter top_k > 100
UT-EXT-09: QueryKnowledgeRouter top_k < 1
UT-EXT-10: QueryKnowledgeRouter include_body 截断 > 10KB
UT-EXT-11: GetKnowledgeItemRouter 参数校验
UT-EXT-12: GetKnowledgeItemRouter item_id 为空
UT-EXT-13: GetKnowledgeItemRouter version=None → latest
UT-EXT-14: GetKnowledgeItemRouter version=0
UT-EXT-15: GetKnowledgeItemRouter 404 → KNOWLEDGE_ITEM_NOT_FOUND
UT-EXT-16: RecordMemoryRouter idempotency_key 校验
UT-EXT-17: RecordMemoryRouter content > 8192
UT-EXT-18: RecordMemoryRouter 重复 idempotency_key → 返回原 memory_id
UT-EXT-19: QueryMemoryRouter 参数校验
UT-EXT-20: QueryMemoryRouter visibility=AGENT_PRIVATE
UT-EXT-21: QueryMemoryRouter include_expired=True
UT-EXT-22: QueryMemoryRouter min_confidence > 1.0
```

#### 11.2.13 `tests/mtls/` (UT-MT-01~18 · 18 ID)

```
UT-MT-01: build_server_ssl_context 成功（临时 cert fixture）
UT-MT-02: tls.crt 缺失 → MtlsConfigError
UT-MT-03: tls.key 缺失 → MtlsConfigError
UT-MT-04: tls.key mode != 0600 → MtlsConfigError
UT-MT-05: SSLContext min_version = TLSv1_3
UT-MT-06: SSLContext verify_mode = CERT_REQUIRED
UT-MT-07: extract_spiffe_id URI SAN 解析成功
UT-MT-08: extract_spiffe_id 无 SPIFFE SAN → None
UT-MT-09: validate_spiffe_id trust_domain 匹配
UT-MT-10: validate_spiffe_id trust_domain 不匹配 → SpiffeIdFormatError
UT-MT-11: SpiffeIdFormatError URI 不是 spiffe:// 前缀
UT-MT-12: SpiffeIdFormatError path 为空
UT-MT-13: CertHotReloader start 启动后台 task
UT-MT-14: CertHotReloader stop 幂等
UT-MT-15: CertHotReloader _reload_if_expired 证书 < 24h
UT-MT-16: CertHotReloader atomic_replace 新旧 context 切换
UT-MT-17: CertHotReloader 失败回退旧 context
UT-MT-18: CertHotReloader metric cert_reload_failures_total 上报
```

#### 11.2.14 `tests/observability/` (UT-OB-01~30 · 30 ID)

```
UT-OB-01: A2aMetrics 15 指标注册
UT-OB-02: superteam_a2a_rpc_total Counter
UT-OB-03: superteam_a2a_rpc_duration_seconds Histogram
UT-OB-04: superteam_a2a_circuit_breaker_state Gauge
UT-OB-05: superteam_a2a_retry_total Counter
UT-OB-06: superteam_a2a_discovery_watch_reconnects_total
UT-OB-07: superteam_a2a_agent_card_cache_hits_total
UT-OB-08: superteam_a2a_cert_reload_failures_total
UT-OB-09: superteam_a2a_extension_router_dispatch_total
UT-OB-10: superteam_a2a_request_body_bytes Histogram
UT-OB-11: superteam_a2a_response_body_bytes Histogram
UT-OB-12: superteam_python_event_loop_lag_seconds Histogram
UT-OB-13: superteam_python_thread_offload_queue_depth Gauge
UT-OB-14: init_tracing 显式 provider 注入
UT-OB-15: init_tracing 不污染全局
UT-OB-16: tracer(name) 返回 OTel Tracer
UT-OB-17: OTel BatchSpanProcessor 启动
UT-OB-18: OTel Resource service.name 设置
UT-OB-19: OTel sample_ratio 应用
UT-OB-20: OTel traceparent 透传
UT-OB-21: configure_logging structlog setup
UT-OB-22: configure_logging json_format=True
UT-OB-23: configure_logging 6 必含字段
UT-OB-24: 敏感字段 api_key 过滤
UT-OB-25: 敏感字段 memory_content 过滤
UT-OB-26: trace_id 注入 log
UT-OB-27: EventLoopMonitor start 启动 task
UT-OB-28: EventLoopMonitor stop 幂等
UT-OB-29: EventLoopMonitor 采样 lag
UT-OB-30: EventLoopMonitor metric 上报
```

#### 11.2.15 `tests/utils/offload_test.py` (UT-UT-01~10 · 10 ID)

```
UT-UT-01: offload_cpu 简单函数
UT-UT-02: offload_cpu 阻塞函数
UT-UT-03: offload_cpu 异常传播
UT-UT-04: offload_cpu 取消传播
UT-UT-05: offload_cpu 限制器 capacity
UT-UT-06: offload_cpu 并发安全
UT-UT-07: ThreadPoolStats current_threads
UT-UT-08: ThreadPoolStats idle_threads
UT-UT-09: ThreadPoolStats total_tasks_processed
UT-UT-10: ThreadPoolStats metric 上报
```

#### 11.2.16 `tests/integration/` (IT-A2A-01~15 · 15 ID)

```
IT-A2A-01: kind 集群启动 A2A Core
IT-A2A-02: A2AClient 真实调用 A2A Core
IT-A2A-03: mTLS 真实握手
IT-A2A-04: cert-manager 颁发证书
IT-A2A-05: AgentCard 拉取过 mTLS
IT-A2A-06: build_server_ssl_context 集成
IT-A2A-07: 证书过期自动 reload
IT-A2A-08: 证书 reload 失败不中断
IT-A2A-09: 证书 hot reload 期间请求不失败
IT-A2A-10: EndpointSlice watch reconnect 后继续接收事件
IT-A2A-11: 多 namespace watch RBAC 正确
IT-A2A-12: NetworkPolicy 限制 egress
IT-A2A-13: Prometheus 15 指标抓取
IT-A2A-14: OTel trace 导出到 collector
IT-A2A-15: memory_route 集成（fake handler，不 import memory）
```

#### 11.2.17 `tests/conformance/` (CF-A2A-01~22 · 22 ID · 继承 L2-1)

```
CF-A2A-01 ~ CF-A2A-05: envelope 5 case（camelCase / id 三类型 / params 三类型 / 序列化 round-trip / 时间字段）
CF-A2A-06 ~ CF-A2A-17: 12 method 各自 case（标准 3 method + 项目扩展 4 method + cancelTask 1 placeholder + 错误路径 4）
CF-A2A-18 ~ CF-A2A-22: 5 错误码 case（标准 + A2A 域 + Knowledge + Memory + project 范围）
```

#### 11.2.18 `tests/e2e/` (E2E-A2A-01~05 · 5 ID)

```
E2E-A2A-01: hello-agent 启动 → sendMessage → 收到 Task
E2E-A2A-02: knowledge_service 启动 → queryKnowledge → 返回结果
E2E-A2A-03: memory_backend 启动 → recordMemory → queryMemory → 找到记录
E2E-A2A-04: mTLS 真实握手 + SPIFFE ID 提取
E2E-A2A-05: chaos 故障注入（EndpointSlice 消失 → 重新发现）
```

#### 11.2.19 `tests/contract/` (CT-A2A-01~05 · 5 ID · 见 §10.2)

#### 11.2.20 `tests/property/` (PROP-001~005 · 5 ID)

```
PROP-001: 任意 JSON-RPC request 序列化反序列化 round-trip
PROP-002: 任意 QueryKnowledgeRequest 不崩溃
PROP-003: 任意 RecordMemoryRequest 不崩溃
PROP-004: 任意 AgentCard JSON Schema 2020-12 valid
PROP-005: 任意错误码枚举值唯一
```

#### 11.2.21 `tests/http_mock/` (HTTP-001~008 · 8 ID)

```
HTTP-001: A2AClient.send_message timeout → A2ATimeoutError
HTTP-002: A2AClient.send_message cancel → A2ACancelledError
HTTP-003: A2AClient.send_message 5xx → retry
HTTP-004: A2AClient.send_message mTLS cert invalid → A2AAuthError
HTTP-005: A2AClient.query_knowledge 404 → KNOWLEDGE_SCOPE_NOT_FOUND
HTTP-006: A2AClient.record_memory 重复 idempotency_key → 返回原 memory_id
HTTP-007: Retry-After 头 → 退避时间尊重
HTTP-008: Circuit OPEN → CircuitOpenError 不发起请求
```

**测试 ID 总数**：7 + 15 + 15 + 7 + 22 + 5 + 14 + 10 + 15 + 21 + 5 + 22 + 18 + 30 + 10 + 15 + 22 + 5 + 5 + 5 + 8 = **276 ID**（包含 L3-2 在 L2-1 100 ID 基础上扩展为 276 ID 矩阵；含 UT 5 类扩展 ID + observability 30 ID + IT 15 ID + E2E 5 ID + Contract 5 ID 等 L3-2 Python 重写新增项）

**注意**：上述 276 ID 是 L3-2 在 L2-1 100 ID 基础上扩展后的完整 ID 矩阵（突破原 100+ 目标因 L3-2 Python 落地增加 cert hot reload / observability / IT / E2E / Contract 5 个新维度），与 L3-1 Operator Core 218 ID + 4 验收清单 95 ID 同等级别。L3-2 评审时按此矩阵逐项验收。

### 11.3 conformance 套件接入（ADR-0005 §11.2 + 继承 L2-1 Spec §11.3）

- SDK 提供 `a2a.conformance` 子包（具体路径 L3-2 实测，参考 [a2aproject/a2a-python conformance](https://github.com/a2aproject/a2a-python/tree/main/tests/conformance)）
- **CI 必跑**：`pytest tests/conformance/ -v --tb=short`
- **标准 method 100% 覆盖**（sendMessage / getTask / Agent Card）
- **项目扩展 method 100% 覆盖**（4 extension router）
- **CF-A2A 测试 ID 22 个**（见 §11.2.17）

**conformance 套件启动流程**：
```bash
# 安装 SDK
uv add a2a-sdk --dev
# 复制 SDK conformance 套件到 tests/conformance/
cp -r $(python -c "import a2a.conformance; print(a2a.conformance.__path__[0])") tests/conformance/sdk/
# 跑 conformance
pytest tests/conformance/ -v
```

### 11.4 静态门禁（CI 必跑 · 继承 L2-1 Spec §11.4）

```bash
# L4 CI 必跑（顺序敏感：先 format → check → type → security）
uv sync --frozen
ruff format --check .
ruff check .
ruff check --select ST-A2A-BOUNDARY .  # 自定义规则：禁止业务层 import a2a
pyright packages/a2a-core
bandit -r packages/a2a-core/src
pip-audit --strict
import-linter --contracts packages/a2a-core/contracts  # 自研 boundary 锁
vulture packages/a2a-core/src  # 死代码检测
interrogate packages/a2a-core/src  # docstring 覆盖率 ≥ 80%
```

**Ruff 自定义规则 `ST-A2A-BOUNDARY` 检测**：
- `^import a2a` → 报错（业务层必须经 `superteam_a2a.a2a`）
- `^from a2a import` → 报错
- **例外**：`packages/a2a-core/src/superteam_a2a/a2a/upstream.py`（boundary 模块）
- **例外**：`packages/a2a-core/src/superteam_a2a/a2a/upstream_types.py`（项目私有 DTO）

**import-linter contracts**：
- `a2a.upstream` 不得 import 业务层任何符号
- `a2a.*`（除 upstream）不得 import 业务层任何符号
- 业务层只允许 `from superteam_a2a.a2a import ...`

**interrogate 配置**：
- `fail-under = 80`（docstring 覆盖率 ≥ 80%）
- `exclude = tests,docs`
- `ignore-magic = true`

### 11.5 性能预算（L1 v0.2.0 Arch §11.5 · L2-1 Spec §11.5）

| 指标 | 目标值 | 测量工具 | 备注 |
|------|--------|----------|------|
| 1 KiB A2A loopback p50/p95/p99 | < 5ms / < 20ms / < 50ms | `pytest-benchmark` | 包含 mTLS 握手 |
| Pydantic validation overhead | < 1ms | `pytest-benchmark` | 4 method request + 4 method response |
| Agent Card cache hit | < 0.5ms | `pytest-benchmark` | TTL 内命中 |
| EndpointSlice watch invalidation | < 100ms | kind E2E | watch 事件触发 → 缓存失效 |
| event-loop lag p99 | < 50ms | Prometheus histogram | 后台 task 调度延迟 |
| cert hot reload atomic switch | < 50ms | `pytest-benchmark` | atomic 替换 + httpx 池重建 |
| A2AClient first-byte | < 100ms | `pytest-benchmark` | 冷启动 + mTLS 握手 |
| Retry 3 attempts total | < 5s | `pytest-benchmark` | 含退避 |

**性能测试文件**：`tests/performance/test_a2a_bench.py`（用 `pytest-benchmark` 自动跑）

---

---

## 12. Helm values 完整 schema（继承 L2-1 Spec §12）

### 12.1 a2aCore 段（A2aCoreConfig Pydantic model · 继承 L2-1 Spec §12.1）

```yaml
# deploy/helm/a2a-core/values.yaml
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

**A2aCoreConfig Pydantic model**（与 L3-1 `HelmValues` 同模式 · 在 `a2a_core/config.py`）：

```python
# packages/a2a-core/src/superteam_a2a/a2a/config.py
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class ImageConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repository: str = "superteam-a2a/a2a-core"
    tag: str = "v0.2.0"
    pullPolicy: str = Field(default="IfNotPresent", pattern="^(Always|IfNotPresent|Never)$")


class PythonConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workers: int = Field(default=1, ge=1, le=1)  # const
    eventLoop: str = Field(default="uvloop", pattern="^(uvloop|asyncio)$")
    httpParser: str = Field(default="httptools", pattern="^(httptools|h11)$")
    cpuOffloadWorkers: int = Field(default=8, ge=1, le=64)
    eventLoopLagThresholdMs: int = Field(default=50, ge=10, le=1000)


class ResourcesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requests: dict[str, str]  # {"cpu": "500m", "memory": "512Mi"}
    limits: dict[str, str]    # {"cpu": "2000m", "memory": "2Gi"}


class MtlsHotReloadConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    intervalSeconds: int = Field(default=30, ge=10, le=3600)
    timeoutSeconds: int = Field(default=5, ge=1, le=60)


class MtlsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    certDir: Path = Path("/etc/tls")
    minVersion: str = Field(default="1.3", pattern="^(1\\.[23])$")
    spiffeRequired: bool = True
    trustDomain: str = "superteam-a2a.local"
    hotReload: MtlsHotReloadConfig = MtlsHotReloadConfig()


class ServiceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    port: int = Field(default=8080, ge=1, le=65535)
    targetPort: int = Field(default=8080, ge=1, le=65535)


class MetricsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    path: str = "/metrics"


class TracingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    otlpEndpoint: str | None = None
    sampleRatio: float = Field(default=1.0, ge=0.0, le=1.0)


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = Field(default="json", pattern="^(json|text)$")


class ObservabilityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metrics: MetricsConfig = MetricsConfig()
    tracing: TracingConfig = TracingConfig()
    logging: LoggingConfig = LoggingConfig()


class CertWatcherConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intervalSeconds: int = Field(default=30, ge=10, le=3600)
    timeoutSeconds: int = Field(default=5, ge=1, le=60)


class A2aCoreConfig(BaseSettings):
    """A2A Core Helm values 完整 schema（继承 L2-1 Spec §12.1）。"""
    model_config = SettingsConfigDict(
        env_prefix="A2A_CORE_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="forbid",
    )
    replicaCount: int = Field(default=1, ge=1, le=1)  # const
    image: ImageConfig = ImageConfig()
    python: PythonConfig = PythonConfig()
    resources: ResourcesConfig
    mtls: MtlsConfig = MtlsConfig()
    service: ServiceConfig = ServiceConfig()
    observability: ObservabilityConfig = ObservabilityConfig()
    certWatcher: CertWatcherConfig = CertWatcherConfig()
    terminationGracePeriodSeconds: int = Field(default=60, ge=10, le=600)
```

**values.schema.json 自动生成**（与 L3-1 `values.schema.json` 同模式 · CI 必跑）：
```bash
python -c "from superteam_a2a.a2a.config import A2aCoreConfig; print(A2aCoreConfig.model_json_schema())" \
  > deploy/helm/a2a-core/values.schema.json
```

### 12.2 Pod Security（K8s 1.28+ restricted profile · 继承 L2-1 Spec §12.2）

```yaml
# deploy/helm/a2a-core/templates/deployment.yaml 片段
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

**关键约束**：
- `runAsNonRoot: true` + `runAsUser: 65534` (nobody) — K8s restricted profile 必填
- `readOnlyRootFilesystem: true` + `certDir` 单独 volumeMount — cert 热更新可写
- `capabilities.drop: ["ALL"]` + `allowPrivilegeEscalation: false` — 最小权限

### 12.3 RBAC（ServiceAccount + ClusterRole · 继承 L2-1 Spec §12.3）

```yaml
# deploy/helm/a2a-core/templates/clusterrole.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: superteam-a2a-a2a-core
rules:
  # K8s Service / EndpointSlice watch（Discovery 必须）
  - apiGroups: [""]
    resources: ["endpointslices"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["services"]
    verbs: ["get", "list", "watch"]
  # 配置（CertWatcher / ConfigMap 加载）
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get"]
    resourceNames: ["superteam-a2a-config"]
  # 事件（K8s Events 记录）
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["create", "patch"]
---
# deploy/helm/a2a-core/templates/clusterrolebinding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: superteam-a2a-a2a-core
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: superteam-a2a-a2a-core
subjects:
  - kind: ServiceAccount
    name: superteam-a2a-a2a-core
    namespace: {{ .Release.Namespace }}
```

**RBAC 边界**：
- **不**给 secrets 权限（L3-2 不读 secrets，cert 由 cert-manager 挂载）
- **不**给 pods / deployments 权限（L3-2 不 reconcile，CRD lifecycle 由 L3-1 Operator 负责）
- **不**给 cluster-wide list（仅必要 resourceNames）

### 12.4 9 Helm 模板清单（与 §1.3 9 模板一致）

| 模板 | 用途 | 与 L2-1 Spec §12 对应 |
|------|------|------------------------|
| `Chart.yaml` | Helm chart 元数据 | (新增) |
| `values.yaml` | 默认 Helm values（开发环境）| §12.1 |
| `values.schema.json` | JSON Schema（从 A2aCoreConfig 自动生成）| (新增) |
| `deployment.yaml` | A2A Core Deployment（单容器 + Uvicorn 单 worker）| §12.1 + §12.2 |
| `service.yaml` | Service（8443 mTLS + 9090 metrics）| §12.1 |
| `serviceaccount.yaml` | ServiceAccount | §12.3 |
| `secret-tls.yaml` | cert-manager 注解（tls.crt / tls.key / ca.crt）| §12.1 mtls |
| `networkpolicy.yaml` | NetworkPolicy（限制 Pod egress）| §12.2 |
| `prometheusrule.yaml` | 15 指标告警规则 | §11.1 |
| `servicemonitor.yaml` | ServiceMonitor（15 指标抓取）| §11.1 |
| `podmonitor.yaml` | PodMonitor（补充 runtime 4 指标）| §11.1 |

**完整 9 + 2 = 11 文件**（values.yaml + values.schema.json + Chart.yaml + 8 模板）

---

---

## 13. 生命周期契约（时序图 · 继承 L2-1 Spec §13）

> ⚠️ **占位章节** —— 后续 #52+ 会话补完。
>
> **本节将展开**：
> - 13.1 启动时序（lifespan 5 阶段：observability init → mtls context build → cert hot reload start → agent card cache warmup → server start）
> - 13.2 稳态（steady state · 6 method 路由 + ExtensionRouter dispatch + metrics/trace 持续采集）
> - 13.3 关闭时序（SIGTERM → lifespan.shutdown 6 阶段逆序）
> - 13.4 证书热更新时序（每 5min 检查 + atomic 替换 + 失败回退）
>
> **基线引用**：[L2-1 Spec v0.2.0 §13](../../spec/L2-module-specs/L2-a2a-protocol.md)

---

## 14. 验收清单（v0.2 · Python-first · 继承 L2-1 Spec §14）

> ⚠️ **占位章节** —— 后续 #52+ 会话补完。
>
> **本节将展开**：
> - 14.1 模块完整性（30 文件清单 + 6 method + 4 endpoint + 24 error code + 15 指标）
> - 14.2 Python-first 硬约束（ADR-0005 + 宪法 v0.5.0）
> - 14.3 可观测性 / 安全 / 性能
> - 14.4 上游追踪
> - 14.5 与其他文档一致性
> - 14.6 跨文档同步
>
> **基线引用**：[L2-1 Spec v0.2.0 §14](../../spec/L2-module-specs/L2-a2a-protocol.md)

---

## 15. 开放问题（移交 L3-2 Spec / v0.5+ · 继承 L2-1 Spec §15）

> ⚠️ **占位章节** —— 后续 #52+ 会话补完。
>
> **本节将展开**：
> - 15.1 继承自 L2-1 Spec v0.2.0 §15 的 15 项开放问题（v0.2 收敛 80%）
> - 15.2 L3-2 Python 重写新增开放问题（预估 5-8 项 · pyright strict / a2a-sdk version / httpx async pool tuning / cert hot reload atomic 等）
>
> **基线引用**：[L2-1 Spec v0.2.0 §15](../../spec/L2-module-specs/L2-a2a-protocol.md)

---

## 附录 A：跨模块引用清单（v0.2-draft 骨架稿 · 后续 #51+ 补完）

### A.1 L1 引用

| L1 文档 | 引用章节 | 用途 |
|---------|----------|------|
| [L1 Architecture v0.2.0](../../design/L1-architecture.md) | §3.4 通信层 | A2A Core 在 L1 中的位置 + 与 Operator/Adapter/Knowledge/Memory 的边界 |
| [L1 Spec v0.2.0](../../spec/L1-system-spec.md) | §5 + §15 + §16 | wire contract（envelope / Task FSM / 15 指标 metric name） |

### A.2 L2 引用

| L2 文档 | 引用章节 | 用途 |
|---------|----------|------|
| [L2-1 A2A Protocol Spec v0.2.0](../../spec/L2-module-specs/L2-a2a-protocol.md) | §1-§15 + 附录 A/B | **L3-2 上游约束权威**；7 子包 + 6 method + 4 endpoint + 24 error code + 15 指标 + 100 测试 ID |
| [L2-1 A2A Protocol Design v0.2.0](../../design/L2-modules/L2-a2a-protocol.md) | §3-§14 | 7 子包设计决策 + ExtensionRouter Protocol 设计 + 单进程原则 + mTLS 设计 |
| [L2-2 Operator Core Spec v0.2.0](../../spec/L2-module-specs/L2-operator-core.md) | §6 Leader Election | A2A Core 在 Operator 编排下与 admission webhook 共 Pod + 4 Controller reconcile |
| [L2-3 Adapter Spec v0.2.0](../../spec/L2-module-specs/L2-adapter.md) | §1-§15 | Adapter SDK 通过 A2AClient 调用 A2A Core 6 method |
| [L2-4 Knowledge/Memory Spec v0.2.0](../../spec/L2-module-specs/L2-knowledge-memory.md) | §1-§15 | Knowledge Service / Memory backend 实现 4 extension router + 调用 A2A Core 注册表 |

### A.3 ADR / Constitution 引用

| ADR / 宪法 | 章节 | 用途 |
|------------|------|------|
| [ADR-0002 Knowledge 管理设计](../adr/0002-knowledge-design.md) | §2 + §3 | 4 级 scope + 7 错误码（-32400 ~ -32406）|
| [ADR-0003 Memory 设计](../adr/0003-memory-design.md) | §4 + §6 | 5 维可见性矩阵 + 6 错误码（-32500 ~ -32505）+ recordMemory idempotency |
| [ADR-0005 Python-first 技术栈](../adr/0005-python-first-technology-stack.md) | §3.2 + §6 + §8 + §9.1 + §13.1 | A2A Core 模块映射 + 单进程原则 + 异步 SDK 门禁 + mTLS + uv workspace 布局 |
| [CONSTITUTION v0.5.0](../../../CONSTITUTION.md) | §3.8 + §6 + §7 + §9.7 + §13.6 + §16 | Python-first + mTLS + 可观测性 + 静态质量 + 上游追踪 + 会话管理 |

### A.4 配套 Spec 引用（L3 同级）

| L3 文档 | 引用章节 | 用途 |
|---------|----------|------|
| [L3-1 Operator Core 文件级 Spec v0.2-draft](./L3-operator-core.md) | §1.3 文件清单 + §2 包结构 | A2A Core 与 Operator 同 Pod 部署 + 4 Controller reconcile A2A Core 生命周期 |
| L3-3 Adapter SDK 文件级 Spec | (待起草) | Adapter SDK 通过 A2AClient 调用 6 method |
| L3-4 Hello Agent 文件级 Spec | (待起草) | Hello Agent 实现 4 extension router + Adapter 集成 |
| L3-5 Knowledge Service 文件级 Spec | (待起草) | Knowledge Service 实现 2 extension router（queryKnowledge + getKnowledgeItem）|
| L3-6 Memory backend 文件级 Spec | (待起草) | Memory backend 实现 2 extension router（recordMemory + queryMemory）|

### A.5 归档引用

| 归档文档 | 章节 | 用途 |
|---------|------|------|
| [L3-a2a-core-spec-v0.1-draft-go-baseline.md](../../archive/pre-python-2026-07-24/L3-a2a-core-spec-v0.1-draft-go-baseline.md) | §1-§10（1446 行） | Go baseline 完整结构参照（仅 wire contract / 业务语义 / 状态机 / RBAC / metric name 不变部分）|

---

## 附录 B：ADR / Constitution 引用矩阵（占位 · 后续 #52+ 补完）

> ⚠️ **占位附录** —— 后续 #51+ 会话补完。
>
> **本附录将展开 5 子表**：
> - B.1 架构（ADR-0005 §3.2 + 宪法 §3.8）
> - B.2 接口（ADR-0005 §8 + 宪法 §13.6）
> - B.3 可见性（ADR-0002/0003 + 宪法 §7）
> - B.4 安全（ADR-0005 §9.1 + 宪法 §6）
> - B.5 性能（L1 v0.2.0 Arch §11.5 + ADR-0005 §6.1/6.3）
> - B.6 测试（ADR-0005 §11 + 宪法 §9.7）
>
> **基线引用**：[L3-1 Operator Core Spec v0.2-draft 附录 B](./L3-operator-core.md) + [L2-1 Spec v0.2.0 附录 B](../../spec/L2-module-specs/L2-a2a-protocol.md)
