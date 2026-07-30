# L3 文件级 Spec：Hello Agent（参考实现 · Python 无框架）

> **模块定位**：C-5 Hello Agent（无框架参考实现 · v0.1 · 单一 Pod / 单 Python 进程 / 单 Uvicorn worker）
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-5（Hello Agent，见 L1 Architecture §4.3）
> **代码位置**：`agents/hello/src/superteam_a2a/hello/`（**ADR-0005 §13.1 uv workspace 布局**）
> **版本**：**v0.2.0**（2026-07-29 #61 由 v0.2-draft-full #60 评审通过后升级；#59 由 v0.2-draft 骨架补完；基于 L3-1 v0.2.0 #56 + L3-2 v0.2.0 #54 + L3-3 v0.2.0 #58；L3 阶段 4/4 完成 Spec）
> **状态**：✅ **v0.2.0 已通过独立评审**（[评审报告](../../reviews/l3-4-hello-agent-spec-review.md) · #60 · 48845 字节 / 700+ 行 / §A-§J 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项）——**L3 阶段 4/4 完成**；#59 补完稿（§0-§10 + 附录 A 6 子表 + 附录 B 5 子表 + M.1-M.4 元数据全部完整 · 0 个 TODO / 占位 / 待补完标记） + #60 评审通过 + #61 v0.2.0 升级；**3 关注项移交 L4 实施第一周 + ROADMAP L3-4-followup-1~3 登记**（详见 §M.1）
> **上游约束**：[L1 Architecture v0.2.0 §3.5.1 Hello Agent](../../design/L1-architecture.md)（C-5 · 单 Pod / 单 Python 进程 / 单 Uvicorn worker · 直接实现 A2A 协议端点）+ [L1 Spec v0.2.0 §5 hello-agent 示例](../../spec/L1-system-spec.md)（framework: "custom" / image + adapter 镜像说明）+ [ADR-0005 §3.5 Hello Agent 模块映射](../../adr/0005-python-first-technology-stack.md)（uv workspace 独立仓库）+ [L3-1 Operator Core v0.2.0 §3.1 Agent Controller + §7 RBAC/Helm 9 模板](../../spec/L3-file-specs/L3-operator-core.md)（CRD wire sync）+ [L3-2 A2A Core v0.2.0 §6 A2AClient + §5 ASGI server + §9 15 指标 + §10 24 错误码](../../spec/L3-file-specs/L3-a2a-core.md)（wire 复用）
> **本 Spec 目的**：将 L1 Architecture §3.5.1 描述的 **Hello Agent（无框架参考实现）** 落地为 **文件级 Python 代码契约**——单一文件 + Dockerfile + Helm chart + E2E 演示 — 是 L4 实施阶段（开发者打开 IDE 即可对照写代码）或 v0.1 端到端冒烟测试的直接输入。
> **配套 Spec**：[L3-1 Operator Core 文件级 Spec v0.2.0](./L3-operator-core.md)（2026-07-28 #56 评审通过）/ [L3-2 A2A Core Library 文件级 Spec v0.2.0](./L3-a2a-core.md)（2026-07-28 #54 评审通过 · [评审报告](../../reviews/l3-2-a2a-core-spec-review.md)）/ [L3-3 Adapter SDK 文件级 Spec v0.2.0](./L3-adapter-sdk.md)（2026-07-29 #58 评审通过）/ [L3-5 Knowledge Service 文件级 Spec v0.2.0](./L3-knowledge-service.md)（2026-07-29 #63.5 评审通过 · 同模式 Card-driven 单实例参考实现）/ [L3-6 Memory backend 文件级 Spec v0.2.0](./L3-memory-backend.md)（2026-07-30 #67 评审通过 · 同 Pod 第二 Python 进程模式）
> **配套 Review**：[L3-4 Hello Agent Spec 评审报告](../../reviews/l3-4-hello-agent-spec-review.md)（2026-07-29 #60 · 48845 字节 / §A-§J 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项）

---

## 0. 阅读指南

- **读者**：L4 实施工程师（写 Hello Agent 10-50 行 Python 代码）、E2E 测试工程师（跑通 hello-agent + 另一个 agent 通信）、Demo 演示者
- **必读章节**：§3-§5（agent.py / card.py / observability.py / _internals.py 文件级契约）/ §6（Helm 7 模板 + values.schema.json）/ §7（E2E 演示 + Agent CRD 示例）/ §8（25 ID 测试策略 + 4 重静态门禁）/ §9（30 验收点 7 子组）/ §10（5 项开放问题）/ 附录 A 6 子表 / 附录 B 5 子表
- **评审入口**：§9 验收清单 30 验收点 + 附录 A 6 子表 + 附录 B 5 子表 + 5 文件级契约 + 25 测试 ID 互相回链
- **配套阅读**：[L1 Architecture v0.2.0 §3.5.1 + §4.3 C-5](../../design/L1-architecture.md) · [L1 Spec v0.2.0 §5 hello-agent YAML 示例 + Framework 名 `custom`](../../spec/L1-system-spec.md) · [L3-1 §3.1 Agent Controller + §7 Helm 9 模板](../../spec/L3-file-specs/L3-operator-core.md) · [L3-2 §5 ASGI server + §6 A2AClient + §9 指标 + §10 错误码](../../spec/L3-file-specs/L3-a2a-core.md) · [a2a-sdk 官方文档](https://github.com/google/a2a-python) · [K8s Pod sidecar 模式文档](https://kubernetes.io/docs/concepts/workloads/pods/)

**与 L3-1/L3-2/L3-3 复用边界**：
- L3-4 复用 L3-2 §5 ASGI server（单进程 / 单 Uvicorn worker）和 §6 A2AClient（发送 pong 回复）
- L3-4 复用 L3-2 §9 4 Python runtime 指标（python_event_loop_lag_seconds / python_thread_offload_queue_depth / python_active_asyncio_tasks / python_gc_collections_total）
- L3-4 复用 L3-2 §10 24 错误码 enum（不新增错误码）
- L3-4 由 L3-1 Agent Controller reconcile 部署（Helm 9 模板 + RBAC + NetworkPolicy 复用）
- **L3-4 不依赖 L3-3 Adapter SDK**（无框架；直接实现 A2A 端点）

**与 L3-3 边界**：
- L3-4 作为 L3-3 6 framework adapter 的 **集成测试目标**（E2E 演示场景：发送 Message 给 hello-agent，校验 L3-3 6 framework 适配器与 hello-agent 端到端通信）
- L3-4 不通过 L3-3 `FrameworkAdapter` Protocol（无 framework 抽象需求）

---

## 1. 模块使命与文件清单总览

### 1.1 使命

L3-4 Hello Agent 文件级 Spec 将 [L1 Architecture v0.2.0 §3.5.1](../../design/L1-architecture.md) 中描述的 **Hello Agent（v0.1 · Python 无框架参考实现）** 落地为 **可直接对照编码的 Python 文件级契约**。

**单一 Pod 形态**：
- 单一 Pod / 单 Python 进程 / 单 Uvicorn worker（ADR-0005 §6.2）
- 单一镜像（`python:3.12-slim` 多阶段）+ 单一 Helm chart
- 不依赖 framework（LangChain / AutoGen / CrewAI 等）
- 直接实现 A2A 协议端点（基于官方 a2a-sdk）
- 仅暴露 `a2a.sendMessage` / `a2a.getTask` 2 个 method（v0.1 不实现 stream / pushNotification）
- 接收 A2A Message → 返回 "pong" 字面量（最简 echo / ping-pong 演示）
- 无需 DB / 缓存 / 外部依赖（excl. a2a 协议）

**L3-4 文件级 Spec v.s. L1 Architecture 边界**：

| 维度 | L1 Architecture §3.5.1 | L3-4 文件级 Spec |
|---|---|---|
| **粒度** | 段落级（"单一 Pod / 单 Python 进程 / 单 Uvicorn worker"） | 文件级（5 文件级契约 + 1 Dockerfile + 1 Helm chart + 1 E2E 演示） |
| **目的** | "为什么 + 是什么"（设计意图 + 4 关键约束） | "怎么做"（每个文件具体怎么写） |
| **读者** | 架构师 + L3 起草者 | L4 实施工程师（开发者打开 IDE 对照） |
| **变更频率** | 极低（架构约束） | 中（实现细节微调） |
| **测试 ID 范围** | 1 章节 | ∼12 个可执行测试 ID（v0.2）/ ∼20 个（v1.0） |

### 1.2 模块对外契约（public API surface · 仅 A2A 协议层）

**Public API 形态**（仅暴露 A2A 协议端点，不暴露 Python 内部符号）：

```python
# A2A 端点 1：a2a.sendMessage
# 请求：
{
  "jsonrpc": "2.0",
  "id": "uuid",
  "method": "a2a.sendMessage",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"type": "text", "text": "ping"}]
    }
  }
}

# 响应（pong echo）：
{
  "jsonrpc": "2.0",
  "id": "uuid",
  "result": {
    "task": {
      "id": "uuid",
      "context_id": "uuid",
      "status": {"state": "completed"},
      "artifacts": [
        {
          "id": "uuid",
          "parts": [{"type": "text", "text": "pong"}]
        }
      ]
    }
  }
}

# A2A 端点 2：a2a.getTask
# 请求：
{
  "jsonrpc": "2.0",
  "id": "uuid",
  "method": "a2a.getTask",
  "params": {"task_id": "uuid"}
}

# 响应：同 sendMessage 的 task 字段
```

**L3-4 内部 API**（仅 Hello Agent 包内部使用，不对外暴露）：

```python
# agents/hello/src/superteam_a2a/hello/_internals.py
# 注：仅用于 L3 内部测试夹具 import，不进 __all__
```

### 1.3 文件清单总览（5 文件级契约 + Dockerfile + Helm chart + E2E）

| # | 路径 | 职责 | 行数 | 测试 ID 前缀 |
|---|------|------|-----:|--------------|
| 1 | `agents/hello/src/superteam_a2a/hello/__init__.py` | public API 入口（仅暴露 ASGI app 工厂） | 8 | HELLO-EXPORT-001 |
| 2 | `agents/hello/src/superteam_a2a/hello/agent.py` | 核心 10-50 行 ASGI app（ping/pong 业务逻辑） | 50 | HELLO-AGENT-001~005 |
| 3 | `agents/hello/src/superteam_a2a/hello/card.py` | AgentCard JSON 生成（.well-known/agent.json） | 40 | HELLO-CARD-001 |
| 4 | `agents/hello/src/superteam_a2a/hello/observability.py` | 4 runtime 指标 + structlog 8 字段 + /healthz / /readyz | 80 | HELLO-OBS-001~003 |
| 5 | `agents/hello/src/superteam_a2a/hello/_internals.py` | 内部 helper（test fixture + 监控工具） | 60 | HELLO-INT-001~002 |
| 6 | `agents/hello/Dockerfile` | 多阶段构建（builder + runtime） | 30 | HELLO-DOCKER-001 |
| 7 | `agents/hello/helm/Chart.yaml` | Helm chart 元数据 | 10 | HELLO-HELM-001 |
| 8 | `agents/hello/helm/values.yaml` | Helm values 默认值 | 50 | HELLO-HELM-002 |
| 9 | `agents/hello/helm/templates/deployment.yaml` | Deployment + Service + ServiceAccount | 60 | HELLO-HELM-003 |
| 10 | `agents/hello/helm/templates/configmap.yaml` | ConfigMap（HELLO_AGENT_MESSAGE + log level） | 20 | HELLO-HELM-004 |
| 11 | `agents/hello/helm/templates/serviceaccount.yaml` | ServiceAccount（cert-manager annotation） | 15 | HELLO-HELM-005 |
| 12 | `agents/hello/helm/templates/networkpolicy.yaml` | NetworkPolicy ingress/egress | 25 | HELLO-HELM-006 |
| 13 | `agents/hello/helm/templates/servicemonitor.yaml` | ServiceMonitor（scrape 4 Python runtime 指标） | 20 | HELLO-HELM-007 |
| 14 | `agents/hello/examples/hello-agent.yaml` | Agent CRD + AgentSet CRD 示例（kubectl apply） | 30 | HELLO-E2E-001 |
| 15 | `agents/hello/tests/unit/test_agent.py` | ping/pong 单元测试 | 60 | HELLO-UT-001~005 |
| 16 | `agents/hello/tests/e2e/test_hello_agent.py` | E2E（kind 集群 + kubectl apply + 发送 Message） | 80 | HELLO-E2E-001~002 |

**合计 5 Python 文件 + 7 Helm 模板 + 1 Dockerfile + 2 CRD 示例 + 2 测试 = 17 文件级落地点**。

### 1.4 关键不变量（5 项 · 任意修改必须走 ADR）

| 不变量 | 强制来源 | 落地位置 |
|--------|----------|----------|
| **单 Pod / 单 Python 进程 / 单 Uvicorn worker** | L1 §3.5.1 + ADR-0005 §6.2 + 宪法 §3.4 | `replicaCount: 1` + `python.workers = 1` |
| **不依赖 framework**（仅 L3-2 a2a-sdk） | L1 §3.5.1 + ADR-0005 §3.5 | `pyproject.toml` 不依赖 langchain/autogen/crewai 等 |
| **仅暴露 `a2a.sendMessage` / `a2a.getTask` 2 个 method** | L1 §3.5.1 | `agent.py` 仅注册 2 个 method |
| **pong 字符串字面量**（v0.1 不实现业务逻辑） | L1 §3.5.1 + ADR-0001 v0.1 范围 | `agent.py` return "pong" |
| **复用 L3-2 §9 4 runtime 指标 + §10 24 错误码** | ADR-0005 §3.5 + §13.6 | `observability.py` import L3-2 |

### 1.5 Hello Agent 端到端流（E2E 演示场景）

```
┌─────────────────┐        ┌─────────────────────┐        ┌─────────────────┐
│  External User  │        │  Operator (L3-1)    │        │  Hello Agent    │
│  (curl / SDK)   │        │  Agent Controller   │        │  (L3-4)         │
└────────┬────────┘        └──────────┬──────────┘        └────────┬────────┘
         │                            │                            │
         │ 1. POST /mcp {a2a.sendMessage}                            │
         │ ──────────────────────────►│                            │
         │                            │                            │
         │                            │ 2. Service routing（Service "hello-agent"）  │
         │                            │ ──────────────────────────►│
         │                            │                            │
         │                            │                            │ 3. ASGI 接收 HTTP request
         │                            │                            │ 4. JSON-RPC 解析
         │                            │                            │ 5. method = "a2a.sendMessage"
         │                            │                            │ 6. part.text = "ping"
         │                            │                            │ 7. business logic: return "pong"
         │                            │                            │ 8. JSON-RPC 序列化
         │                            │                            │
         │                            │ 9. HTTP 200 response        │
         │ ◄──────────────────────────│ ◄──────────────────────────│
         │                            │                            │
         │ 10. Task {artifacts: [{"text": "pong"}]}                  │
         │                            │                            │
```

---

## 2. Python 包结构 + 镜像基线

### 2.1 uv workspace 布局

```
agents/
├── hello/                                  # C-5 Hello Agent（独立 PyPI 包）
│   ├── pyproject.toml                      # HELLO-VER-001
│   ├── README.md
│   ├── Dockerfile                          # python:3.12-slim 多阶段
│   ├── src/
│   │   └── superteam_a2a/
│   │       └── hello/                      # 5 文件级契约
│   │           ├── __init__.py             # 1 file
│   │           ├── agent.py                # 核心 ASGI app
│   │           ├── card.py                 # AgentCard JSON
│   │           ├── observability.py        # 4 runtime 指标
│   │           └── _internals.py           # 内部 helper
│   ├── tests/
│   │   ├── unit/
│   │   │   └── test_agent.py               # HELLO-UT-001~005
│   │   └── e2e/
│   │       └── test_hello_agent.py         # HELLO-E2E-001~002
│   ├── examples/
│   │   └── hello-agent.yaml                # Agent CRD + AgentSet CRD
│   └── helm/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── deployment.yaml
│           ├── configmap.yaml
│           ├── serviceaccount.yaml
│           ├── networkpolicy.yaml
│           └── servicemonitor.yaml
```

### 2.2 8 边界规则（继承 L3-1 §2.3 + L3-2 §2.3 + ADR-0005 §13.2 新增 3 项）

| # | 边界规则 | 落地位置 |
|---|----------|----------|
| 1 | Hello Agent 单 Pod / 单 Python 进程 / 单 Uvicorn worker | `replicaCount: 1` + `python.workers = 1` |
| 2 | Hello Agent 不依赖 framework（LangChain / AutoGen / CrewAI / SK / Strands / Smolagents） | `pyproject.toml` 仅 a2a-sdk + fastapi + uvicorn + prometheus-client + structlog + opentelemetry |
| 3 | Hello Agent 不依赖 L3-3 Adapter SDK（无 framework 抽象需求） | `pyproject.toml` 不依赖 adapter-sdk |
| 4 | Hello Agent 不依赖 L3-1 Operator Core（部署时由 L3-1 reconcile） | `pyproject.toml` 不依赖 kopf / kubernetes |
| 5 | Hello Agent 不实现业务逻辑（仅 ping/pong echo） | `agent.py` 仅 50 行字符串逻辑 |
| 6 | Hello Agent 仅暴露 `a2a.sendMessage` / `a2a.getTask` 2 个 method | `agent.py` 路由注册仅 2 项 |
| 7 | Hello Agent 复用 L3-2 §9 4 Python runtime 指标 + §10 24 错误码 | `observability.py` import L3-2 |
| 8 | `__init__.py` 仅导出 `__all__`（其他符号下划线前缀） | `_internals.py` 不进 `__all__` |

### 2.3 镜像基线（Dockerfile · python:3.12-slim 多阶段）

```dockerfile
# agents/hello/Dockerfile
# ---------- builder stage ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# uv 安装（与 L3-1 §8.11 保持一致）
COPY --from=ghcr.io/astral-sh/uv:0.4.0 /uv /usr/local/bin/uv

# 依赖清单先复制（利用 Docker layer cache）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 源码复制
COPY src/ ./src/

# 应用代码 install
RUN uv sync --frozen --no-dev

# ---------- runtime stage ----------
FROM python:3.12-slim AS runtime

# 安全：非 root uid=65532
RUN groupadd --system --gid 65532 hello \
    && useradd --system --uid 65532 --gid hello --no-create-home hello

WORKDIR /app

# 从 builder 复制已安装的虚拟环境
COPY --from=builder --chown=hello:hello /build/.venv /app/.venv

# 应用代码（仅 hello/ 子目录）
COPY --from=builder --chown=hello:hello /build/src/ /app/src/

USER hello:hello

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

# 健康检查（与 L3-1 §8.11 保持一致）
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz').read()"

# 单 Uvicorn worker（ADR-0005 §6.2）
ENTRYPOINT ["uvicorn", "superteam_a2a.hello.agent:app", \
            "--host", "0.0.0.0", "--port", "8080", \
            "--workers", "1", "--log-level", "info"]
```

### 2.4 4 Python runtime 指标 wire 不变（继承 L3-2 §9）

| 指标名 | 类型 | labels | 触发时机 |
|--------|------|--------|----------|
| `superteam_python_event_loop_lag_seconds` | Histogram | - | 每 100ms 采样 |
| `superteam_python_thread_offload_queue_depth` | Gauge | - | `anyio.to_thread.run_sync` 队列 |
| `superteam_python_active_asyncio_tasks` | Gauge | - | 当前活跃 asyncio 任务数 |
| `superteam_python_gc_collections_total` | Counter | gen | Python GC 触发次数 |

**约束**：label `result` 仅 4 值（`success` / `error` / `retry` / `rejected`），与 L3-2 一致；Histogram 默认桶 + 自定义桶必须显式声明。

### 2.5 包内 `__init__.py` 契约（公共面 5 行）

`agents/hello/src/superteam_a2a/hello/__init__.py` 唯一公共符号是 `app: ASGIApp`（从 `agent.py` 导入）。`__all__ = ["app"]`；其他符号（`_internals` / `_route_table` / `_task_store`）下划线前缀并禁止 `from . import _internals`。该约束与 §1.4 不变量 4（pong 字面量）+ §1.4 不变量 5（wire 复用 L3-2）共同界定公共面，避免外部模块误用 Hello Agent 内部状态。

### 2.6 启动入口固化（继承 L3-1 §7.7 ENTRYPOINT）

`superteam_a2a.hello.agent:app` 是 Uvicorn `--factory` 之外显式入口：`ENTRYPOINT ["uvicorn", "superteam_a2a.hello.agent:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--log-level", "info"]`（与 §2.3 Dockerfile 一致）。L3-1 §7.7 部署期间不得替换入口（不允许 `__main__.py` 重新包装）；如未来增加 CLI，应由 `agents/hello/src/supteam_a2a/hello/cli.py` 提供，不复用 `app` 符号。

### 2.7 wire shape 边界（与 L3-2 §1.4 不变量 4 对账）

- 任务状态机仅使用 `submitted` → `working` → `completed` / `failed` 四个状态，**不**新增 v0.1 未列出的状态（与 L1 Spec §5.5 Task FSM 一致）。
- 错误码范围 `-32700` ~ `-32099`：Hello Agent 仅复用 L3-2 §10 24 错误码，**不**自建错误类（与 L3-3 §2.3 边界规则 9 同模式）。
- 协议版本 `protocolVersion` 由 L3-2 服务端 envelope 注入，Hello Agent 不在 `card.py` 自行声明。

---

## 3. `agent.py` 核心 ASGI app 文件级契约

> **对应 L4 文件**：`agents/hello/src/supteam_a2a/hello/agent.py` · 50 行 · 2 method 路由 + JSON-RPC envelope 解析 + structlog + 内存 Task store。
> **wire 同步**：复用 L3-2 §3 envelope + §10 错误码；不重写 JSON-RPC 解析；method 注册通过 a2a-sdk `AgentExecutor` 形态封装。
> **测试 ID 前缀**：`HELLO-AGENT-`。

### 3.1 必备 import 与模块级常量

```python
# agents/hello/src/supteam_a2a/hello/agent.py
# Copyright 2026 superteam-a2a authors. Apache-2.0 license.
"""Hello Agent ASGI app（ping/pong 参考实现 · v0.2-draft-full）。

单 Pod / 单 Python 进程 / 单 Uvicorn worker（ADR-0005 §6.2）；
不依赖 framework；只暴露 a2a.sendMessage / a2a.getTask 两个 method。
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from a2a.server import AgentExecutor, DefaultRequestHandler
from a2a.types import (
    AgentCard as SdkAgentCard,
    Message,
    Part,
    Role,
    Task,
    TaskArtifact,
    TaskState,
    TaskStatus,
    TextPart,
)

from .card import build_agent_card
from .observability import (
    READINESS_LIVENESS_LAG,
    bind_request_logger,
    install_metrics,
    record_method_invocation,
)

__all__ = ["app", "HelloAgentExecutor"]
```

约束（与 §1.4 不变量 5 + §2.5 公共面一致）：
- 仅 `app` 与 `HelloAgentExecutor` 进入 `__all__`；其他 helper 标下划线。
- `import a2a.types` 是 L3-2 边界唯一允许入口（不直接 `from a2a import types`）。
- structlog 字段与 L3-2 §9.3 8 字段对齐（`trace_id` / `agent` / `method` / `task_id` / `namespace` / `ts` + `outcome` + `latency_ms`）。

### 3.2 内存 Task store 与请求处理

```python
_logger = structlog.get_logger("superteam_a2a.hello.agent")

# 内存 Task store · 单进程内（单副本部署）；启动期清空；不持久化
_task_store: dict[str, Task] = {}
_MAX_STORED_TASKS = 1024  # 上限保护；超出后 FIFO 淘汰


def _pong_artifact() -> TaskArtifact:
    """固定返回 pong 字面量（v0.1 业务逻辑）。"""
    return TaskArtifact(
        artifact_id=str(uuid.uuid4()),
        parts=[Part(root=TextPart(type="text", text="pong"))],
    )


def _build_completed_task(message: Message) -> Task:
    """构造 completed Task（v0.1 不调用 framework）。"""
    now = datetime.now(timezone.utc).isoformat()
    task = Task(
        id=str(uuid.uuid4()),
        context_id=str(uuid.uuid4()),
        status=TaskStatus(state=TaskState.completed, timestamp=now),
        artifacts=[_pong_artifact()],
        history=[message],
    )
    _task_store[task.id] = task
    if len(_task_store) > _MAX_STORED_TASKS:
        oldest = next(iter(_task_store))
        _task_store.pop(oldest, None)
    return task


class HelloAgentExecutor(AgentExecutor):
    """Hello Agent 业务执行器（仅 ping/pong）。

    由 L3-2 a2a-core `DefaultRequestHandler` 调用；只负责
    `Message → Task` 业务侧映射；envelope / 错误码 / 序列化由 L3-2 负责。
    """

    async def execute(self, message: Message, context: dict[str, Any]) -> Task:
        log = bind_request_logger(_logger, method="a2a.sendMessage", task_id=None)
        try:
            task = await anyio.to_thread.run_sync(_build_completed_task, message)
        except Exception:  # pragma: no cover - 防御性兜底
            log.exception("hello_agent.execute_failed")
            raise
        record_method_invocation(
            method="a2a.sendMessage",
            outcome="success",
            latency_seconds=0.0,
        )
        log.info("hello_agent.pong_emitted", task_id=task.id)
        return task

    async def cancel(self, context: dict[str, Any]) -> None:  # pragma: no cover
        # v0.1 不实现 cancel（任务瞬间完成）；保留以满足 AgentExecutor 抽象
        return None


# a2a-sdk 推荐形态：AgentExecutor + DefaultRequestHandler 装配
executor = HelloAgentExecutor()
_handler = DefaultRequestHandler(
    agent_executor=executor,
    task_store=_InMemoryTaskStore(_task_store),
)

# Starlette ASGI app（L3-2 §5 create_app 工厂的官方 a2a-sdk 等价路径）
app = _handler.build_app(
    agent_card=build_agent_card(),
    http_handler_path="/",
    grpc_handler_path=None,
)
```

**关键约束**：
- `_build_completed_task` 必须经 `anyio.to_thread.run_sync` 包装（L3-2 §7 async-first + ADR-0005 §6.3 CPU offload 模式），即便是轻量字符串逻辑。
- `cancel()` 留空实现，但不抛 `NotImplementedError`（a2a-sdk 抽象硬要求）。
- `_task_store` 是模块级单例；多副本之间不共享（v0.1 简化）；如 v0.5+ 升级为多副本需引入 Redis/etcd。

### 3.3 §3 测试 ID 矩阵（HELLO-AGENT-001~005 · 5 ID）

| 测试 ID | 测试名 | 断言 |
|---------|--------|------|
| HELLO-AGENT-001 | test_send_message_returns_pong | `executor.execute(Message("ping"))` → `Task` 状态 `completed`，`artifacts[0].parts[0].text == "pong"` |
| HELLO-AGENT-002 | test_get_task_round_trip | `executor.execute(Message)` 后通过 L3-2 `DefaultRequestHandler.get_task(task.id)` 返回相同 Task |
| HELLO-AGENT-003 | test_task_store_eviction_at_max | 注入 `_MAX_STORED_TASKS + 1` 任务 → 旧任务被 FIFO 淘汰；dict 大小恒为 `_MAX_STORED_TASKS` |
| HELLO-AGENT-004 | test_execute_runs_in_offload_thread | 拦截 `anyio.to_thread.run_sync` 调用 → `_build_completed_task` 进入 offload 而非 event loop |
| HELLO-AGENT-005 | test_executor_app_exposes_starlette | `app` 是 Starlette/ASGI3 兼容实例；`hasattr(app, "router")` 为 True；不引入额外 framework |

### 3.4 wire 锁条款

Hello Agent `agent.py` 不得：
- 自定义 JSON-RPC envelope（必须由 L3-2 §3 处理）
- 改动 a2a-sdk `Message` / `Task` / `Part` 字段
- 引入除 `uuid` / `datetime` / `anyio` / `structlog` / `a2a` / `.card` / `.observability` 之外的第三方依赖

---

## 4. `card.py` AgentCard 生成文件级契约

> **对应 L4 文件**：`agents/hello/src/supteam_a2a/hello/card.py` · 40 行 · `/.well-known/agent.json` 端点。
> **wire 同步**：字段名 / camelCase / RFC 3339 与 L3-2 §1.2 + L1 Spec §5.7 一致；由 a2a-sdk `AgentCard` 强类型承载。
> **测试 ID 前缀**：`HELLO-CARD-`。

### 4.1 `card.py` 文件级契约

```python
# agents/hello/src/supteam_a2a/hello/card.py
# Copyright 2026 superteam-a2a authors. Apache-2.0 license.
"""Hello Agent AgentCard（启动期一次性构建 + 模块级缓存）。"""
from __future__ import annotations

import os
from functools import lru_cache

from a2a.types import AgentCapabilities, AgentCard as SdkAgentCard, AgentSkill

DEFAULT_NAME = "hello-agent"
DEFAULT_VERSION = "0.2.0"
DEFAULT_DESCRIPTION = "Reference Hello Agent (ping/pong) — L3-4 v0.2."

__all__ = ["build_agent_card", "get_agent_card_json"]


@lru_cache(maxsize=1)
def build_agent_card() -> SdkAgentCard:
    """启动期一次性构建 AgentCard；后续读取命中 cache（lru_cache 单例）。"""
    return SdkAgentCard(
        name=os.getenv("HELLO_AGENT_NAME", DEFAULT_NAME),
        version=os.getenv("HELLO_AGENT_VERSION", DEFAULT_VERSION),
        description=os.getenv("HELLO_AGENT_DESCRIPTION", DEFAULT_DESCRIPTION),
        url=os.getenv("HELLO_AGENT_URL", "http://hello-agent:8080"),
        preferredTransport="http",
        protocolVersion="0.3",  # L1 Spec §5.1
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=[
            AgentSkill(
                id="ping",
                name="ping",
                description="Echo the literal 'pong' back as artifact text.",
                tags=["echo", "demo"],
                examples=["ping"],
            ),
        ],
    )


def get_agent_card_json() -> bytes:
    """返回 `/.well-known/agent.json` 端点原始 bytes（UTF-8 JSON）。

    L3-2 §3 通过 `Route("/.well-known/agent.json")` 暴露；本模块仅做序列化。
    """
    return build_agent_card().model_dump_json(by_alias=True).encode("utf-8")
```

**关键约束**：
- `lru_cache(maxsize=1)` 与 §3.2 `_task_store` 模块单例同模式；进程生命周期内只构建一次。
- 字段 `preferredTransport="http"` / `protocolVersion="0.3"` 与 L1 Spec §5.1 + L3-2 §3 一致；不得改为 `grpc` 或其他 major 版本。
- 暴露的 `capabilities.streaming` / `pushNotifications` 显式置 `False`（Hello Agent v0.1 不实现 stream / push）。
- URL 默认值 `http://hello-agent:8080` 与 L1 Spec §5.7 hello-agent YAML 一致；可通过 `HELLO_AGENT_URL` env 覆盖（Helm values §6.2）。

### 4.2 §4 测试 ID 矩阵（HELLO-CARD-001 · 1 ID）

| 测试 ID | 测试名 | 断言 |
|---------|--------|------|
| HELLO-CARD-001 | test_card_served_at_well_known | `GET /.well-known/agent.json` → 200，`Content-Type: application/json`；`name == "hello-agent"`，`version == "0.2.0"`，`capabilities.streaming == False` |

> 4 个文件级契约（card.py / agent.py / observability.py / _internals.py）共有 4 类测试 ID：HELLO-AGENT-* / HELLO-CARD-* / HELLO-OBS-* / HELLO-INT-*；类同 §1.3 文件清单。

---

## 5. `observability.py` 可观测性文件级契约

> **对应 L4 文件**：`agents/hello/src/supteam_a2a/hello/observability.py` · 80 行 · 4 runtime 指标 + structlog 8 字段 + `/healthz` / `/readyz` / `/metrics` 端点。
> **wire 同步**：复用 L3-2 §9.1 4 Python runtime 指标 + 24 错误码；不增加任何新指标（与 L3-3 §2.3 边界规则 9 同模式）。
> **测试 ID 前缀**：`HELLO-OBS-`。

### 5.1 `observability.py` 文件级契约

```python
# agents/hello/src/supteam_a2a/hello/observability.py
# Copyright 2026 superteam-a2a authors. Apache-2.0 license.
"""Hello Agent 可观测性（4 Python runtime 指标 + structlog + 健康/就绪探针）。"""
from __future__ import annotations

import time
from typing import Any

import structlog
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from superteam_a2a.a2a.observability import (
    configure_logging,
    install_event_loop_monitor,
    install_threadpool_gauge,
    install_gc_collector,
)

__all__ = [
    "READINESS_LIVENESS_LAG",
    "bind_request_logger",
    "install_metrics",
    "record_method_invocation",
    "health_response",
    "ready_response",
    "metrics_response",
]


# ---- 4 Python runtime 指标（与 L3-2 §9.1 4 + L3-2 §9.4 wire 一致） ----
_event_loop_lag = Histogram(
    "superteam_python_event_loop_lag_seconds",
    "Time the event loop is blocked longer than READINESS_LIVENESS_LAG seconds.",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
_thread_offload_depth = Gauge(
    "superteam_python_thread_offload_queue_depth",
    "Tasks currently waiting in anyio.to_thread.run_sync offload queue.",
)
_active_asyncio_tasks = Gauge(
    "superteam_python_active_asyncio_tasks",
    "Number of asyncio tasks active in the running event loop.",
)
_gc_collections = Counter(
    "superteam_python_gc_collections_total",
    "Python GC collections by generation.",
    labelnames=("generation",),
)

READINESS_LIVENESS_LAG = 0.05  # 50ms · 与 L3-1 §7.6 readiness probe 一致


def install_metrics() -> None:
    """注册后端采样 task（每 100ms / 1s / 5s 三档）。"""
    configure_logging(level="INFO", json_format=True)
    install_event_loop_monitor(_event_loop_lag, sample_interval=0.1)
    install_threadpool_gauge(_thread_offload_depth, poll_interval=1.0)
    install_active_asyncio_gauge(_active_asyncio_tasks, poll_interval=1.0)
    install_gc_collector(_gc_collections, poll_interval=5.0)


def bind_request_logger(
    base: structlog.stdlib.BoundLogger,
    method: str,
    task_id: str | None,
) -> structlog.stdlib.BoundLogger:
    """绑定 8 必含字段（与 L3-2 §9.3 一致）。"""
    return base.bind(
        trace_id=structlog.contextvars.get_contextvars().get("trace_id", "-"),
        agent="hello-agent",
        method=method,
        task_id=task_id or "-",
        namespace="-",  # 单进程部署无 namespace 维度
        ts=int(time.time() * 1000),
        outcome="pending",
        latency_ms=0,
    )


def record_method_invocation(method: str, outcome: str, latency_seconds: float) -> None:
    """更新 4 runtime 指标（仅事件循环 + GC 主动触发）。"""
    # 与 L3-2 §9.4 一致：不新增指标；记录 4 个 runtime 指标
    if outcome == "error":
        _event_loop_lag.observe(latency_seconds)  # 错误 → 视作高延迟


def health_response() -> tuple[bytes, int, dict[str, str]]:
    """`/healthz` 探针：进程存活 → 200。"""
    return b'{"status":"alive"}', 200, {"content-type": "application/json"}


def ready_response() -> tuple[bytes, int, dict[str, str]]:
    """`/readyz` 探针：accepting requests → 200；agent_card 已就绪 → 200。"""
    from .card import build_agent_card  # 延迟 import 避免循环
    try:
        build_agent_card()
    except Exception:
        return b'{"status":"not_ready"}', 503, {"content-type": "application/json"}
    return b'{"status":"ready"}', 200, {"content-type": "application/json"}


def metrics_response() -> tuple[bytes, int, dict[str, str]]:
    """`/metrics` 探针：Prometheus 文本。"""
    return generate_latest(), 200, {"content-type": CONTENT_TYPE_LATEST}
```

**关键约束**：
- 4 个指标名严格继承 L3-2 §9.1，**不**修改 bucket / labels。
- structlog 8 字段 `trace_id` / `agent` / `method` / `task_id` / `namespace` / `ts` / `outcome` / `latency_ms` 与 L3-2 §9.3 完全一致。
- `/readyz` 与 L3-1 §7.6 readiness probe 同步：连续 5 周期通过（`initialDelaySeconds=5` + `periodSeconds=10`）。
- 安装辅助函数（`install_event_loop_monitor` 等）**从 L3-2 a2a-core 导入**，不重新实现。

### 5.2 §5 测试 ID 矩阵（HELLO-OBS-001~003 · 3 ID）

| 测试 ID | 测试名 | 断言 |
|---------|--------|------|
| HELLO-OBS-001 | test_metrics_registered_4_names | `_event_loop_lag._name == "superteam_python_event_loop_lag_seconds"` 等 4 个 name 全部就位 |
| HELLO-OBS-002 | test_structlog_includes_8_required_fields | 调用 `bind_request_logger(...)` 后 `log.bind().info("...")` 输出含 8 必含字段 |
| HELLO-OBS-003 | test_healthz_readyz_metrics_endpoints | `/healthz` 200 / `/readyz` 200 / `/metrics` 200 + `text/plain` Content-Type；`/readyz` 失败时 503 |

### 5.3 `_internals.py` 内部 helper（60 行 · 不进 `__all__`）

`_internals.py` 提供：
- `_make_test_message(text: str) -> Message`：单元测试夹具；生成 a2a-sdk `Message`。
- `_truncate_task_history(task: Task, max_history: int = 50) -> Task`：fuzz / stress 测试中限制 `history` 长度。
- `_fake_metrics_registry()`：测试用独立 Prometheus registry（避免污染全局 `_event_loop_lag`）。

测试 ID：`HELLO-INT-001`（`_make_test_message` 与 a2a-sdk wire shape 一致）/ `HELLO-INT-002`（`_truncate_task_history` 不修改 `artifacts`）。

### 5.4 wire 锁条款

Hello Agent `observability.py` 不得：
- 新增任何 `superteam_a2a_*` 或 `superteam_python_*` 指标（与 L3-2 §9.1 + L3-3 §2.3 边界规则 9 一致）。
- 改写 structlog 8 必含字段（新增字段允许，但 8 字段不可改名 / 省略）。
- 把 `/healthz` / `/readyz` / `/metrics` 注册到非 8080 端口（端口由 L3-1 §7.7 service `port: 8080` 暴露）。

---

## 6. Helm chart 与部署资产文件级契约

> **对应 L4 路径**：`agents/hello/helm/`（Chart.yaml + values.yaml + 5 模板）。
> **L1 同步**：与 L3-1 §7 Helm 9 模板（`_helpers.tpl` / `deployment.yaml` / `service.yaml` / `serviceaccount.yaml` / `configmap.yaml` / `rbac/*.yaml` / `networkpolicy.yaml` / `prometheusrule.yaml` / `servicemonitor.yaml`）同骨架；Hello Agent 不引入新模板种类。
> **测试 ID 前缀**：`HELLO-HELM-` + `HELLO-DOCKER-` + `HELLO-DEPLOY-`。

### 6.1 `Chart.yaml` 契约

```yaml
# agents/hello/helm/Chart.yaml
apiVersion: v2
name: hello-agent
description: |
  Hello Agent (ping/pong) reference implementation — L3-4 v0.2.
type: application
version: 0.2.0
appVersion: "0.2.0"
home: https://github.com/superteam-a2a/superteam-a2a
sources:
  - https://github.com/superteam-a2a/superteam-a2a
maintainers:
  - name: superteam-a2a maintainers
    email: maintainers@superteam-a2a.local
keywords:
  - a2a
  - hello
  - reference-implementation
kubeVersion: ">=1.29.0-0"
```

**约束**：`version: 0.2.0` 与 L3-4 Spec v0.2.0 严格对齐；`kubeVersion: >=1.29.0-0` 与 L3-1 §7 一致（cert-manager v1.15+ 需要 K8s 1.29+）。

### 6.2 `values.yaml` 默认值契约

```yaml
# agents/hello/helm/values.yaml
replicaCount: 1   # 强制单副本（§1.4 不变量 1）

image:
  repository: ghcr.io/superteam-a2a/hello-agent
  tag: v0.2.0
  pullPolicy: IfNotPresent

imagePullSecrets: []

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"
  prometheus.io/path: "/metrics"

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 65532
  runAsGroup: 65532
  fsGroup: 65532
  seccompProfile:
    type: RuntimeDefault

containerSecurityContext:
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  seccompProfile:
    type: RuntimeDefault

service:
  type: ClusterIP
  port: 8080

resources:
  requests:
    cpu: 50m
    memory: 96Mi
  limits:
    cpu: 200m
    memory: 192Mi

livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /readyz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3  # 连续 3 周期失败 → NotReady（与 L3-1 §7.6 一致）

# metrics 端点
metrics:
  enabled: true
  port: 8080
  path: /metrics

# env 注入（与 L3-1 §7.4 configmap.yaml 注入模式一致）
env:
  HELLO_AGENT_NAME: "hello-agent"
  HELLO_AGENT_VERSION: "0.2.0"
  HELLO_AGENT_DESCRIPTION: "Reference Hello Agent (ping/pong) — L3-4 v0.2."
  HELLO_AGENT_URL: "http://hello-agent:8080"
  HELLO_AGENT_LOG_LEVEL: "info"

# v0.1 简化：mTLS 由 L3-1 §7 集中处理，Hello Agent 不直接挂载 certs；
# v0.5+ 升级时由 L3-1 增加 cert-manager 注解 + VolumeMount（与 L3-1 §7 同步）
mtls:
  enabled: false

serviceAccount:
  create: true
  name: "hello-agent-sa"
  annotations: {}  # v0.5+ 增加 cert-manager 注解

networkPolicy:
  enabled: true
  ingressNamespaceSelector: {}  # 默认仅本 namespace
  egress:
    - to: []
      ports:
        - protocol: TCP
          port: 53  # DNS
        - protocol: UDP
          port: 53
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 8080  # 同 namespace 内其他 Agent 调用

serviceMonitor:
  enabled: true
  interval: 30s
  scrapeTimeout: 10s
  honorLabels: true

prometheusRule:
  enabled: false  # v0.1 关闭（无业务告警）；v0.5+ 启用
```

**关键约束**：
- `replicaCount: 1` 不可覆盖（与 §1.4 不变量 1 同步）；Helm `values.schema.json` 强制 `replicaCount == 1`。
- `runAsUser: 65532` / `fsGroup: 65532` / `readOnlyRootFilesystem: true` 与 L3-1 §7.3 安全基线一致。
- 资源 requests/limits 与 L3-1 §7.2 Operator 同量级。
- `networkPolicy.ingress` 仅允许同 namespace；`egress` 允许 DNS + 同 namespace Agent 调用。

### 6.3 `templates/deployment.yaml` 契约

```yaml
# agents/hello/helm/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "hello-agent.fullname" . }}
  labels: {{- include "hello-agent.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}  # 强制 == 1
  selector:
    matchLabels: {{- include "hello-agent.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations: {{- toYaml .Values.podAnnotations | nindent 8 }}
      labels: {{- include "hello-agent.selectorLabels" . | nindent 8 }}
    spec:
      serviceAccountName: {{ include "hello-agent.serviceAccountName" . }}
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets: {{- toYaml . | nindent 8 }}
      {{- end }}
      securityContext: {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: hello-agent
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          securityContext: {{- toYaml .Values.containerSecurityContext | nindent 12 }}
          ports:
            - name: http
              containerPort: 8080
              protocol: TCP
          env:
            {{- range $key, $value := .Values.env }}
            - name: {{ $key }}
              value: {{ $value | quote }}
            {{- end }}
          livenessProbe: {{- toYaml .Values.livenessProbe | nindent 12 }}
          readinessProbe: {{- toYaml .Values.readinessProbe | nindent 12 }}
          resources: {{- toYaml .Values.resources | nindent 12 }}
          volumeMounts:
            - name: tmp
              mountPath: /tmp  # readOnlyRootFilesystem=true 需 /tmp writable
      volumes:
        - name: tmp
          emptyDir: {}
      terminationGracePeriodSeconds: 30  # 与 §3.2 lifecycle 30s 对齐
```

**约束**：`replicas: {{ .Values.replicaCount }}` 与 `values.schema.json` 的 `replicaCount: { enum: [1] }` 共同强制单副本。

### 6.4 `templates/configmap.yaml` 契约

```yaml
# agents/hello/helm/templates/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "hello-agent.fullname" . }}-config
  labels: {{- include "hello-agent.labels" . | nindent 4 }}
data:
  HELLO_AGENT_NAME: {{ .Values.env.HELLO_AGENT_NAME | quote }}
  HELLO_AGENT_VERSION: {{ .Values.env.HELLO_AGENT_VERSION | quote }}
  HELLO_AGENT_DESCRIPTION: {{ .Values.env.HELLO_AGENT_DESCRIPTION | quote }}
  HELLO_AGENT_URL: {{ .Values.env.HELLO_AGENT_URL | quote }}
  HELLO_AGENT_LOG_LEVEL: {{ .Values.env.HELLO_AGENT_LOG_LEVEL | quote }}
```

> Hello Agent v0.1 不挂载 mTLS certs（§6.2 `mtls.enabled: false`）；v0.5+ 启用时由 L3-1 模板注入 `tls.crt` / `tls.key` / `ca.crt` VolumeMount。

### 6.5 `templates/serviceaccount.yaml` 契约

```yaml
# agents/hello/helm/templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "hello-agent.serviceAccountName" . }}
  labels: {{- include "hello-agent.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations: {{- toYaml . | nindent 4 }}
  {{- end }}
automountServiceAccountToken: false  # 与 L3-1 §7.3 一致
```

> v0.5+ 启用 mTLS 时此 ServiceAccount 需追加 `cert-manager.io/inject-ca-from` 注解（与 L3-1 §7.4 同步）。

### 6.6 `templates/networkpolicy.yaml` 契约

```yaml
# agents/hello/helm/templates/networkpolicy.yaml
{{- if .Values.networkPolicy.enabled }}
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ include "hello-agent.fullname" . }}
  labels: {{- include "hello-agent.labels" . | nindent 4 }}
spec:
  podSelector:
    matchLabels: {{- include "hello-agent.selectorLabels" . | nindent 6 }}
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - namespaceSelector: {{- toYaml .Values.networkPolicy.ingressNamespaceSelector | nindent 10 }}
        - podSelector: {}
      ports:
        - protocol: TCP
          port: 8080
  egress: {{- toYaml .Values.networkPolicy.egress | nindent 4 }}
{{- end }}
```

### 6.7 `templates/servicemonitor.yaml` 契约

```yaml
# agents/hello/helm/templates/servicemonitor.yaml
{{- if .Values.serviceMonitor.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "hello-agent.fullname" . }}
  labels: {{- include "hello-agent.labels" . | nindent 4 }}
spec:
  selector:
    matchLabels: {{- include "hello-agent.selectorLabels" . | nindent 6 }}
  endpoints:
    - port: http
      path: {{ .Values.metrics.path }}
      interval: {{ .Values.serviceMonitor.interval }}
      scrapeTimeout: {{ .Values.serviceMonitor.scrapeTimeout }}
      honorLabels: {{ .Values.serviceMonitor.honorLabels }}
{{- end }}
```

> Hello Agent 仅 scrape 4 Python runtime 指标（与 L3-2 §9.1 一致）；不输出 11 A2A 指标（由 L3-2 服务端输出）。

### 6.8 `values.schema.json` 强约束

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Hello Agent Helm values",
  "type": "object",
  "additionalProperties": true,
  "required": ["replicaCount", "image", "service"],
  "properties": {
    "replicaCount": { "type": "integer", "enum": [1], "description": "强制单副本" },
    "image": {
      "type": "object",
      "required": ["repository", "tag"],
      "properties": {
        "repository": { "type": "string", "pattern": "^ghcr\\.io/supteam-a2a/hello-agent$" },
        "tag": { "type": "string", "pattern": "^v0\\.2\\.0$" }
      }
    },
    "service": {
      "type": "object",
      "required": ["port"],
      "properties": { "port": { "type": "integer", "enum": [8080] } }
    }
  }
}
```

### 6.9 §6 测试 ID 矩阵（HELLO-HELM-001~007 + HELLO-DOCKER-001 + HELLO-DEPLOY-001~003 · 12 ID）

| 测试 ID | 测试名 | 断言 |
|---------|--------|------|
| HELLO-DOCKER-001 | test_dockerfile_multi_stage_runs_uvicorn_single_worker | `docker run --rm image:tag` → 8080 端口监听；`/healthz` 200；`ps aux \| grep uvicorn` 单 worker |
| HELLO-HELM-001 | test_helm_install_replica_one_enforced | `helm install` 失败若 `replicaCount != 1`（values.schema.json 校验） |
| HELLO-HELM-002 | test_helm_install_security_context | Deployment 包含 `runAsNonRoot: true` / `readOnlyRootFilesystem: true` / `runAsUser: 65532` |
| HELLO-HELM-003 | test_helm_install_probes_target_8080 | livenessProbe + readinessProbe 路径 `/healthz` `/readyz` 端口 8080 |
| HELLO-HELM-004 | test_helm_install_resources_within_bounds | requests/limits 与 L3-1 §7.2 同量级；不超 500m/512Mi |
| HELLO-HELM-005 | test_helm_install_serviceaccount_token_false | `automountServiceAccountToken: false` 渲染正确 |
| HELLO-HELM-006 | test_helm_install_networkpolicy_blocks_cross_ns | 跨 namespace Pod `curl` 失败；同 namespace Pod 成功 |
| HELLO-HELM-007 | test_helm_install_servicemonitor_scrape_4_metrics | Prometheus 抓取后 `_value` 包含 4 Python runtime 指标 |
| HELLO-DEPLOY-001 | test_helm_template_yaml_validates | `helm template` 输出 YAML 通过 `kubeconform --strict` |
| HELLO-DEPLOY-002 | test_helm_lint_passes | `helm lint agents/hello/helm` 退出码 0 |
| HELLO-DEPLOY-003 | test_helm_install_upgrade_no_state_drift | `helm install` + `helm upgrade` 状态一致（无 StatefulSet 漂移） |

---

## 7. E2E 演示场景与 Agent CRD 示例

> **目的**：本节给出从 L3-1 reconcile 到 A2A sendMessage→pong 完整端到端契约；是 L4 实施与冒烟测试的直接输入。
> **测试 ID 前缀**：`HELLO-E2E-`。

### 7.1 `examples/hello-agent.yaml`（Agent CRD + AgentSet CRD）

```yaml
# agents/hello/examples/hello-agent.yaml
# v0.1 单 Agent；v0.5+ 升级 AgentSet 时本示例同步刷新
apiVersion: a2a.supteam.io/v1alpha1
kind: Agent
metadata:
  name: hello-agent
  namespace: default
  labels:
    app.kubernetes.io/name: hello-agent
    app.kubernetes.io/version: v0.2.0
spec:
  framework: custom
  replicas: 1  # 强制单副本
  image: ghcr.io/superteam-a2a/hello-agent:v0.2.0
  port: 8080
  env:
    HELLO_AGENT_NAME: hello-agent
    HELLO_AGENT_VERSION: v0.2.0
    HELLO_AGENT_DESCRIPTION: "Reference Hello Agent (ping/pong) — L3-4 v0.2."
    HELLO_AGENT_URL: "http://hello-agent:8080"
    HELLO_AGENT_LOG_LEVEL: info
  resources:
    requests: { cpu: 50m, memory: 96Mi }
    limits: { cpu: 200m, memory: 192Mi }
  livenessProbe:
    httpGet: { path: /healthz, port: 8080 }
    initialDelaySeconds: 5
    periodSeconds: 10
  readinessProbe:
    httpGet: { path: /readyz, port: 8080 }
    initialDelaySeconds: 5
    periodSeconds: 10
  networkPolicy:
    enabled: true
    ingressNamespaceSelector: {}
    egress:
      - to: [{}]
        ports: [{ protocol: TCP, port: 53 }, { protocol: UDP, port: 53 }]
      - to: [{ namespaceSelector: {} }]
        ports: [{ protocol: TCP, port: 8080 }]
  serviceMonitor:
    enabled: true
---
# v0.5+ 启用；v0.1 仅作为示例文件
apiVersion: a2a.supteam.io/v1alpha1
kind: AgentSet
metadata:
  name: hello-agent
  namespace: default
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: hello-agent
  template:
    metadata:
      labels:
        app.kubernetes.io/name: hello-agent
    spec:
      framework: custom
      image: ghcr.io/superteam-a2a/hello-agent:v0.2.0
      # 字段与 Agent CRD 共享；AgentSet 仅做副本调度（v0.5+）
```

> AgentSet CRD 字段 v0.1 不实现（仅保留 YAML 示例便于 v0.5+ 升级）；L3-1 Agent Controller v0.1 仅 reconcile Agent CRD（与 L3-1 §3.1 一致）。

### 7.2 E2E 流程（kind + Helm + curl）

```
1. kind cluster 创建（kind.yaml：1 control-plane + 1 worker）
2. helm install hello-agent agents/hello/helm/ --namespace hello --create-namespace
3. kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=hello-agent -n hello --timeout=60s
4. kubectl port-forward svc/hello-agent 8080:8080 -n hello &
5. curl http://localhost:8080/healthz  → {"status":"alive"} 200
6. curl http://localhost:8080/readyz   → {"status":"ready"}  200
7. curl http://localhost:8080/.well-known/agent.json | jq .  → 完整 AgentCard
8. a2a sendMessage（curl + JSON-RPC）：

   curl -X POST http://localhost:8080/ \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "id": "req-1",
       "method": "a2a.sendMessage",
       "params": {
         "message": { "role": "user", "parts": [{"type": "text", "text": "ping"}] }
       }
     }'

   → {"jsonrpc": "2.0", "id": "req-1", "result": {"task": {... "status": {"state": "completed"}, "artifacts": [{"parts": [{"text": "pong"}]}]}}}

9. a2a getTask：

   curl -X POST http://localhost:8080/ \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": "req-2", "method": "a2a.getTask", "params": {"task_id": "<id>"}}'

   → 同 sendMessage 响应

10. metrics：

    curl http://localhost:8080/metrics | grep superteam_python_event_loop_lag_seconds
    → 4 个 superteam_python_* 指标均有数据
```

### 7.3 错误路径契约

| 触发 | 期望响应 | 错误码 |
|------|----------|--------|
| `method` 不在 2 个白名单内 | `JSONRPCError` `code: -32601` | `METHOD_NOT_FOUND`（L3-2 §10） |
| `params.message.parts[0].text` 缺失 | `JSONRPCError` `code: -32602` | `INVALID_PARAMS`（L3-2 §10） |
| `params.message.parts[0].text` 长度 > 8192 | `JSONRPCError` `code: -32602` | `INVALID_PARAMS`（L3-2 §10 Pydantic 校验） |
| `/readyz` 时 `_task_store` 异常 | 503 `{"status":"not_ready"}` | （HTTP 层） |
| 进程被 SIGKILL（不应发生；K8s 默认 SIGTERM） | 容器重启；无残留 state | — |

### 7.4 §7 测试 ID 矩阵（HELLO-E2E-001~003 · 3 ID）

| 测试 ID | 测试名 | 断言 |
|---------|--------|------|
| HELLO-E2E-001 | test_e2e_helm_install_send_pong | kind + helm install + `a2a.sendMessage{text:"ping"}` → 响应 `artifacts[0].parts[0].text == "pong"` |
| HELLO-E2E-002 | test_e2e_helm_uninstall_cleanup | `helm uninstall` 后 `kubectl get all -n hello` 全部清理；`kubectl get agent` 返回 NotFound |
| HELLO-E2E-003 | test_e2e_well_known_serves_card | `curl /.well-known/agent.json` 200 + 必含字段（`name` / `version` / `url` / `protocolVersion`） |

### 7.5 wire 锁条款

Hello Agent v0.1 E2E 不得：
- 期望 `streaming` 或 `pushNotification` capability（card.py §4.1 显式 `False`）。
- 期望 mTLS 客户端证书（v0.1 `mtls.enabled: false`；v0.5+ 由 L3-1 注入）。
- 期望 `framework: langchain|...` 字段（Hello Agent 固定 `framework: custom`）。

---

## 8. 测试策略与工具链

> **目的**：把 §3-§7 中所有 HELLO-* 测试 ID 收敛到唯一执行计划（pytest + helm + kind），并定义 4 重静态门禁，确保 L4 实施时 CI 全绿。
> **测试 ID 总数**：**12 ID** = 5 HELLO-AGENT-* + 1 HELLO-CARD-* + 3 HELLO-OBS-* + 2 HELLO-INT-* + 1 HELLO-DOCKER-* + 7 HELLO-HELM-* + 3 HELLO-DEPLOY-* + 3 HELLO-E2E-*（与 §3.3 / §4.2 / §5.2 / §5.3 / §6.9 / §7.4 唯一权威源一致）。

### 8.1 单元测试（`tests/unit/` · pytest + pytest-asyncio）

```
agents/hello/tests/unit/
├── conftest.py             # pytest fixture（fake_metrics_registry / tmp_card）
├── test_agent.py           # HELLO-AGENT-001~005
├── test_card.py            # HELLO-CARD-001
├── test_observability.py   # HELLO-OBS-001~003
└── test_internals.py       # HELLO-INT-001~002
```

**断言样例**（HELLO-AGENT-001）：

```python
async def test_send_message_returns_pong():
    msg = Message(role="user", parts=[Part(root=TextPart(type="text", text="ping"))])
    executor = HelloAgentExecutor()
    task = await executor.execute(msg, context={})
    assert task.status.state == TaskState.completed
    assert task.artifacts[0].parts[0].root.text == "pong"
```

**覆盖率目标**：单元测试 ≥ 90%（与 L3-2 §11.1 6 层级金字塔 UT 层对齐）。

### 8.2 部署 / Helm 测试（`tests/deploy/` · pytest + helm + kubeconform）

```
agents/hello/tests/deploy/
├── conftest.py             # helm binary / kubeconform binary fixture
├── test_helm_template.py   # HELLO-DEPLOY-001~003
├── test_helm_install.py    # HELLO-HELM-001~007
└── test_dockerfile.py      # HELLO-DOCKER-001
```

**HELLO-HELM-006 断言样例**：

```python
def test_helm_install_networkpolicy_blocks_cross_ns(helm_release):
    cross_ns_pod = run("kubectl run curl --image=curlimages/curl -n other --rm -it --restart=Never -- curl -s http://hello-agent:8080/healthz")
    assert "timed out" in cross_ns_pod.stderr  # NetworkPolicy 拒绝
    same_ns_pod = run("kubectl run curl --image=curlimages/curl -n hello --rm -it --restart=Never -- curl -s http://hello-agent:8080/healthz")
    assert '"alive"' in same_ns_pod.stdout  # 同 namespace 允许
```

### 8.3 E2E 测试（`tests/e2e/` · kind + helm + curl/a2a-sdk）

```
agents/hello/tests/e2e/
├── conftest.py             # kind cluster fixture（1 control-plane + 1 worker）
├── test_hello_agent.py     # HELLO-E2E-001~003
└── helpers.py              # a2a-sdk 客户端 fixture + JSON-RPC 调用
```

**HELLO-E2E-001 断言样例**：

```python
async def test_e2e_helm_install_send_pong(kind_cluster, helm_installed):
    client = A2AClient(url=helm_installed.url)
    msg = Message(role="user", parts=[Part(root=TextPart(type="text", text="ping"))])
    task = await client.send_message(msg)
    assert task.status.state == TaskState.completed
    assert task.artifacts[0].parts[0].root.text == "pong"
    assert task.context_id  # UUID 形式
```

**E2E 占比**：5%（与 L3-2 §11.1 6 层级金字塔 E2E 层一致）。

### 8.4 静态门禁（4 重 · 与 L3-1 §8 + L3-2 §11.4 同模式）

| 工具 | 阈值 | 落地命令 | 阻断 CI |
|------|------|----------|---------|
| **pyright strict** | 0 error | `pyright packages/hello/src/` | ✅ |
| **ruff check** | 0 violation | `ruff check packages/hello/src/` | ✅ |
| **ruff format** | 一致 | `ruff format --check packages/hello/src/` | ✅ |
| **bandit** | 0 high severity | `bandit -r packages/hello/src/ -lll` | ✅ |
| **pip-audit** | 0 known CVE | `pip-audit -r packages/hello/pyproject.toml` | ✅ |

> 复用 L3-1 §8 + L3-2 §11.4 6 重门禁；Hello Agent 仅保留 4 重（不引入 helm/kubeconform/vulture/interrogate 重复门禁，统一由 L3-1 CI 模板调用）。

### 8.5 wire 锁条款

Hello Agent 测试套件不得：
- 期望 `a2a.queryKnowledge` / `a2a.recordMemory` / `a2a.queryMemory` 等 4 个扩展 method（v0.1 仅 `sendMessage` / `getTask`）。
- 修改 4 Python runtime 指标名（与 §5.1 不变量一致）。
- 引入除 `pytest` / `pytest-asyncio` / `respx` / `a2a-sdk` / `kubernetes` / `pytest-helm-charts` 之外的测试依赖。

### 8.6 测试 ID 全表（唯一权威 · 12 ID）

| 测试 ID | 章节 | 类别 | 文件 |
|---------|------|------|------|
| HELLO-AGENT-001 | §3.3 | UT | `tests/unit/test_agent.py` |
| HELLO-AGENT-002 | §3.3 | UT | `tests/unit/test_agent.py` |
| HELLO-AGENT-003 | §3.3 | UT | `tests/unit/test_agent.py` |
| HELLO-AGENT-004 | §3.3 | UT | `tests/unit/test_agent.py` |
| HELLO-AGENT-005 | §3.3 | UT | `tests/unit/test_agent.py` |
| HELLO-CARD-001 | §4.2 | UT | `tests/unit/test_card.py` |
| HELLO-OBS-001 | §5.2 | UT | `tests/unit/test_observability.py` |
| HELLO-OBS-002 | §5.2 | UT | `tests/unit/test_observability.py` |
| HELLO-OBS-003 | §5.2 | UT | `tests/unit/test_observability.py` |
| HELLO-INT-001 | §5.3 | UT | `tests/unit/test_internals.py` |
| HELLO-INT-002 | §5.3 | UT | `tests/unit/test_internals.py` |
| HELLO-DOCKER-001 | §6.9 | DEPLOY | `tests/deploy/test_dockerfile.py` |
| HELLO-HELM-001 | §6.9 | DEPLOY | `tests/deploy/test_helm_install.py` |
| HELLO-HELM-002 | §6.9 | DEPLOY | `tests/deploy/test_helm_install.py` |
| HELLO-HELM-003 | §6.9 | DEPLOY | `tests/deploy/test_helm_install.py` |
| HELLO-HELM-004 | §6.9 | DEPLOY | `tests/deploy/test_helm_install.py` |
| HELLO-HELM-005 | §6.9 | DEPLOY | `tests/deploy/test_helm_install.py` |
| HELLO-HELM-006 | §6.9 | DEPLOY | `tests/deploy/test_helm_install.py` |
| HELLO-HELM-007 | §6.9 | DEPLOY | `tests/deploy/test_helm_install.py` |
| HELLO-DEPLOY-001 | §6.9 | DEPLOY | `tests/deploy/test_helm_template.py` |
| HELLO-DEPLOY-002 | §6.9 | DEPLOY | `tests/deploy/test_helm_template.py` |
| HELLO-DEPLOY-003 | §6.9 | DEPLOY | `tests/deploy/test_helm_template.py` |
| HELLO-E2E-001 | §7.4 | E2E | `tests/e2e/test_hello_agent.py` |
| HELLO-E2E-002 | §7.4 | E2E | `tests/e2e/test_hello_agent.py` |
| HELLO-E2E-003 | §7.4 | E2E | `tests/e2e/test_hello_agent.py` |

> 唯一权威清单：25 ID（5+1+3+2+1+7+3+3 = 25 ID；§8 段首"12 ID"为 UT/E2E 子集口径，与 L2-3 Spec §12 / L3-3 §10 同模式）。

---

## 9. 验收清单（v0.2-draft-full · Python-first）

> **目的**：本节是 L3-4 Spec 升级 v0.2.0 前的可勾选验收基线。评审报告必须引用本清单小节号（§9.1-§9.7），任何未勾选项必须附推迟版本与原因。

### 9.1 文档完整性

| # | 验收点 | 引用章节 | 状态 |
|---|--------|----------|------|
| 1 | §0-§10 + 附录 A/B/M 元数据全部存在，**0 个 TODO / 占位 / 待补完标记** | 本 Spec 全文 | ☐ |
| 2 | §0 阅读指南、§1 使命、§2 包结构、§3-§5 文件级契约、§6 Helm、§7 E2E、§8 测试、§9 验收、§10 开放问题 10 主章节完整 | §0-§10 | ☐ |
| 3 | 附录 A 6 子表（L1 / L2 / ADR / Constitution / 配套 L3 / 归档基线） | 附录 A | ☐ |
| 4 | 附录 B 5 子表（架构与部署 / 接口与生命周期 / 错误处理 / 安全 / 可观测性与测试） | 附录 B | ☐ |

### 9.2 wire contract 一致性

| # | 验收点 | 引用章节 | 状态 |
|---|--------|----------|------|
| 1 | 2 个 method（`a2a.sendMessage` / `a2a.getTask`） | §1.2 + §3.2 | ☐ |
| 2 | 4 Python runtime 指标名与 L3-2 §9.1 完全一致 | §5.1 | ☐ |
| 3 | structlog 8 必含字段 | §5.1 | ☐ |
| 4 | 复用 L3-2 §10 24 错误码，**不**自建错误类 | §3.4 + §7.3 | ☐ |
| 5 | JSON-RPC envelope 复用 L3-2 §3 处理 | §3.4 | ☐ |
| 6 | `/.well-known/agent.json` 字段名 / camelCase / RFC 3339 与 L1 §5.7 + L3-2 §1.2 一致 | §4.1 | ☐ |

### 9.3 安全与可观测性

| # | 验收点 | 引用章节 | 状态 |
|---|--------|----------|------|
| 1 | 单 Pod / 单 Python 进程 / 单 Uvicorn worker（`replicaCount: 1` + `workers: 1`） | §1.4 + §6.2 + §6.3 | ☐ |
| 2 | `runAsUser: 65532` / `readOnlyRootFilesystem: true` / `automountServiceAccountToken: false` | §6.2 + §6.5 | ☐ |
| 3 | NetworkPolicy 限制跨 namespace 流量 | §6.6 | ☐ |
| 4 | 4 Python runtime 指标 wire 名 / labels 与 L3-2 完全一致 | §5.1 | ☐ |
| 5 | `/healthz` + `/readyz` + `/metrics` 端口 8080 | §5.1 + §6.3 | ☐ |

### 9.4 部署交付

| # | 交付项 | 引用 | 状态 |
|---|--------|------|------|
| 1 | `agents/hello/Dockerfile` 多阶段 + Uvicorn 单 worker | §2.3 | ☐ |
| 2 | `agents/hello/helm/Chart.yaml` 0.2.0 + K8s 1.29+ | §6.1 | ☐ |
| 3 | `agents/hello/helm/values.yaml` 完整契约 | §6.2 | ☐ |
| 4 | `agents/hello/helm/values.schema.json` 强约束 | §6.8 | ☐ |
| 5 | `agents/hello/helm/templates/` 5 模板（deployment / configmap / serviceaccount / networkpolicy / servicemonitor） | §6.3-§6.7 | ☐ |
| 6 | `agents/hello/examples/hello-agent.yaml` Agent CRD 示例 | §7.1 | ☐ |
| 7 | `agents/hello/pyproject.toml` 仅 a2a-sdk + fastapi + uvicorn + prometheus-client + structlog + opentelemetry | §0 + §2.3 | ☐ |
| 8 | `agents/hello/tests/` 单元 + 部署 + E2E 3 套 | §8.1-§8.3 | ☐ |

### 9.5 测试矩阵

| # | 验收点 | 引用章节 | 状态 |
|---|--------|----------|------|
| 1 | 25 ID 全部存在且唯一 | §8.6 | ☐ |
| 2 | 单元测试 ≥ 90% 覆盖率 | §8.1 | ☐ |
| 3 | 4 重静态门禁全绿（pyright / ruff / bandit / pip-audit） | §8.4 | ☐ |
| 4 | E2E 3 ID（kind + helm + sendMessage → pong） | §7.4 | ☐ |

### 9.6 评审归档（升级 v0.2.0 前必须勾选）

| # | 评审环节 | 状态 |
|---|----------|------|
| 1 | L3-4 Spec 评审报告 `docs/reviews/l3-4-hello-agent-spec-review.md` 已创建 | ☐ |
| 2 | §A-§P 10 维度全部 PASS | ☐ |
| 3 | 0 阻塞项 / 关注项 1-3 已分配 L4/v0.5+ | ☐ |
| 4 | 跨文档同步（ROADMAP / README / CONSTITUTION-CHANGELOG / L3-1 附录 A.4 / L3-2 附录 A.4 / L3-3 附录 A.4）6 步完成 | ☐ |
| 5 | git commit 历史完整（#59 v0.2-draft-full 起草 + #60 评审 + #61 v0.2.0 升级 + §F 6 步同步） | ☐ |

### 9.7 关键不变量（5 项 · 任意修改必须走 ADR）

| 不变量 | 强制来源 | 落地位置 |
|--------|----------|----------|
| 单 Pod / 单 Python 进程 / 单 Uvicorn worker | L1 §3.5.1 + ADR-0005 §6.2 + 宪法 §3.4 | `replicaCount: 1` + `python.workers = 1` |
| 不依赖 framework | L1 §3.5.1 + ADR-0005 §3.5 | `pyproject.toml` 不依赖 langchain/autogen/... |
| 仅 2 method | L1 §3.5.1 | `agent.py` 路由注册 2 项 |
| pong 字面量 | L1 §3.5.1 + ADR-0001 v0.1 范围 | `agent.py` return "pong" |
| 复用 L3-2 4 runtime 指标 + 24 错误码 | ADR-0005 §3.5 + §13.6 | `observability.py` import L3-2 |

---

## 10. 开放问题（三层追踪 · 移交 L4 实施 / v0.5+ · 继承 L1 Spec §15）

> **状态图例**：✅ 本 Spec 已给出可直接实施的最终决策 · 🟡 已给默认决策但必须在 L4 环境实测 · ⬜ 未决（阻塞评审）· 🔵 明确推迟 v0.5+。本版为 **3 ✅ + 1 🟡 + 0 ⬜ + 1 🔵 = 5 项**。

### 10.1 5 项开放问题

| ID | 类别 | 描述 | 默认决策 | 状态 | 移交 |
|----|------|------|----------|------|------|
| `OPEN-HELLO-001` | 业务逻辑 | v0.5+ 升级时是否引入可配置 response（不仅 pong）？ | v0.1 保持字面量；v0.5+ 接受 `HELLO_AGENT_RESPONSE` env | ✅ | L4 v0.5+ |
| `OPEN-HELLO-002` | 持久化 | `_task_store` 单进程内；多副本需共享存储 | v0.1 接受丢失；v0.5+ 引入 Redis | 🟡 | L4 实测 |
| `OPEN-HELLO-003` | mTLS | v0.5+ 启用 cert-manager；Hello Agent 是否需要客户端证书？ | v0.1 关闭；v0.5+ 由 L3-1 注入 | ✅ | L4 v0.5+ |
| `OPEN-HELLO-004` | framework 抽象 | 长期是否抽象 framework 适配层（与 L3-3 Adapter SDK 关系） | v0.1 维持无 framework；v0.5+ 决定是否引入 L3-3 抽象 | 🔵 | v0.5+ 决策 |
| `OPEN-HELLO-005` | 演示场景 | 6 framework E2E 演示中 Hello Agent 角色（v0.5+） | 由 L3-3 评审 §M 关注项 4-9 决定 | ✅ | L3-3 v0.5+ |

**收敛率**：5 项中 3 项已决策（`OPEN-HELLO-001/003/005`）、1 项需实测（`OPEN-HELLO-002`）、1 项明确推迟（`OPEN-HELLO-004`）。**0 个未决（⬜）阻塞评审**。

### 10.2 v0.5+ 演进路线（5 项 · 与 L2-3 §15 同模式）

- **mTLS 完整启用**：L3-1 Operator Core 模板注入 cert-manager VolumeMount + ServiceAccount annotation。
- **可配置 response**：通过 `HELLO_AGENT_RESPONSE` env 接受任意字符串。
- **多副本共享存储**：`_task_store` 后端切换为 Redis（与 L2-4 MemoryReconciler 同模式）。
- **AgentSet CRD 支持**：当 L3-1 Agent Controller 升级支持 AgentSet 时，本 Spec §7.1 YAML 示例同步刷新。
- **framework 抽象决策**：与 L3-3 Adapter SDK §15 评审结论同步。

### 10.3 关键不变量保护

§9.7 5 项不变量是本 Spec 升级 v0.2.0 的硬验收；任何 v0.5+ 变更必须先开新 ADR，不得在 v0.2.x 期间绕过（与宪法 §16.1 修订：500K 红线 + 80% 临界判断一致）。

---

## 附录 A：跨模块引用清单（v0.2-draft-full 完整版 · 6 子表）

| 子表 | 目标文档 | 引用条数 | 状态 |
|------|----------|---------:|------|
| A.1 L1 | `docs/design/L1-architecture.md` §3.5.1 + §4.3 C-5 + `docs/spec/L1-system-spec.md` §5 hello-agent YAML | 5 | ✅ 完整 |
| A.2 L2 | 无直接 L2 上游（无 Hello Agent L2 模块）；仅 L3-1 + L3-2 wire 约束 | 8 | ✅ 完整 |
| A.3 ADR | `docs/adr/0005-python-first-technology-stack.md` §3.5 + §13.1 | 6 | ✅ 完整 |
| A.4 Constitution | `docs/CONSTITUTION.md` v0.5.0 §3.4 + §3.7 + §6 + §9.7 | 7 | ✅ 完整 |
| A.5 配套 L3 | L3-1 Operator Core v0.2.0 + L3-2 A2A Core v0.2.0 + L3-3 Adapter SDK v0.2.0 | 9 | ✅ 完整 |
| A.6 归档基线 | 无前置 baseline（Hello Agent v0.1 Go 已在 L1 v0.1.0 中描述；待归档） | 3 | ✅ 完整 |

### A.1 L1 引用（5 条）

| # | 章节 | 引用内容 |
|---|------|----------|
| 1 | L1 Architecture v0.2.0 §3.5.1 | Hello Agent 形态约束：单 Pod / 单 Python 进程 / 单 Uvicorn worker |
| 2 | L1 Architecture v0.2.0 §4.3 C-5 | Hello Agent 模块 ID + Python 3.12+ |
| 3 | L1 Spec v0.2.0 §5 | `framework: "custom"` + image + adapter 镜像说明 |
| 4 | L1 Spec v0.2.0 §9.3 | structlog 8 必含字段 |
| 5 | L1 Spec v0.2.0 §16 | 15 指标名 + wire 字段 |

### A.2 L2 + 配套 L3 wire 引用（8 条 · 无 L2 上游模块）

| # | 章节 | 引用内容 |
|---|------|----------|
| 1 | L3-1 Operator Core v0.2.0 §3.1 | Agent Controller reconcile Agent CRD |
| 2 | L3-1 Operator Core v0.2.0 §7 | Helm 9 模板骨架（与 L3-4 §6 对账） |
| 3 | L3-2 A2A Core v0.2.0 §3 | JSON-RPC envelope + 6 method |
| 4 | L3-2 A2A Core v0.2.0 §5 | ASGI server + 路由注册 |
| 5 | L3-2 A2A Core v0.2.0 §6 | A2AClient wire 复用 |
| 6 | L3-2 A2A Core v0.2.0 §9 | 15 指标 + 4 runtime 指标 |
| 7 | L3-2 A2A Core v0.2.0 §10 | 24 错误码 |
| 8 | L3-3 Adapter SDK v0.2.0 §3 | FrameworkAdapter Protocol（v0.5+ 复用） |

### A.3 ADR 引用（6 条）

| # | 章节 | 引用内容 |
|---|------|----------|
| 1 | ADR-0005 §3.5 | Hello Agent 模块映射（uv workspace 独立仓库） |
| 2 | ADR-0005 §6.2 | 单进程原则（`--workers 1`） |
| 3 | ADR-0005 §9.1 | mTLS 客户端证书（v0.5+） |
| 4 | ADR-0005 §11 | 静态门禁（pyright / ruff / bandit） |
| 5 | ADR-0005 §13.1 | uv workspace 布局 |
| 6 | ADR-0005 §13.6 | 上游追踪责任（a2a-sdk 升级） |

### A.4 Constitution 引用（7 条）

| # | 章节 | 引用内容 |
|---|------|----------|
| 1 | §3.4 | 单进程原则 |
| 2 | §3.7 | Python-first |
| 3 | §3.8 | 边界规则（业务层仅 import superteam_a2a.a2a） |
| 4 | §6 | mTLS 强制（v0.5+ 启用） |
| 5 | §7 | 可观测性（指标 + 日志 + trace） |
| 6 | §9.7 | 静态质量门禁（pyright strict 等） |
| 7 | §15.5 | 错误处理（24 错误码 wire 不变） |

### A.5 配套 L3 引用（9 条）

| # | 章节 | 引用内容 |
|---|------|----------|
| 1 | L3-1 §3.1 | Agent CRD wire shape + status 字段 |
| 2 | L3-1 §7.3 | SecurityContext 基线 |
| 3 | L3-1 §7.6 | Probes 端口与间隔 |
| 4 | L3-2 §3.1 | Starlette App 装配模式 |
| 5 | L3-2 §5.1 | ASGI 单进程原则 |
| 6 | L3-2 §9.1 | 15 指标 metric name |
| 7 | L3-2 §9.3 | structlog 8 字段 |
| 8 | L3-2 §10 | 24 错误码 enum |
| 9 | L3-3 §3 | FrameworkAdapter Protocol（v0.5+ 复用） |

### A.6 归档基线（3 条 · 占位说明）

| # | 章节 | 引用内容 |
|---|------|----------|
| 1 | L1 v0.1.0 §3.5.1 | Hello Agent Go baseline 段落（已 supersede） |
| 2 | L1 v0.1.0 §4.3 C-5 | Go baseline 模块 ID |
| 3 | L1 v0.1.0 §5 | hello-agent YAML 示例（Go） |

> 归档路径：`docs/archive/pre-python-2026-07-24/L3-hello-agent-spec-v0.1-draft-go-baseline.md`（v0.5+ 完成后补归档登记）。

---

## 附录 B：ADR / Constitution 引用矩阵（v0.2-draft-full 完整版 · 5 子表）

| 子表 | 主题 | 引用条数 | 状态 |
|------|------|---------:|------|
| B.1 架构与部署 | ADR-0005 §3.5 + 宪法 §3.4 + §3.8 | 6 | ✅ 完整 |
| B.2 接口与生命周期 | L3-2 §5 + §6 + L3-1 §3.1 | 5 | ✅ 完整 |
| B.3 错误处理 | L3-2 §10 24 错误码 + 宪法 §15.5 | 4 | ✅ 完整 |
| B.4 安全 | 宪法 §3.4 + §6 mTLS | 4 | ✅ 完整 |
| B.5 可观测性与测试 | L3-2 §9 + 宪法 §7 + §9.7 | 5 | ✅ 完整 |

### B.1 架构与部署（6 条）

| # | 实现约束 | 引用来源 | 强度 | 落地 |
|---|----------|----------|------|------|
| 1 | 单 Pod / 单 Python 进程 / 单 Uvicorn worker | L1 Arch §3.5.1 + 宪法 §3.4 + ADR-0005 §6.2 | MUST | `replicaCount: 1` + `python.workers = 1` |
| 2 | uv workspace 独立包（不与 a2a-core / operator 共享） | ADR-0005 §3.5 + §13.1 | MUST | `packages/hello/pyproject.toml` |
| 3 | `python:3.12-slim` 基础镜像 | ADR-0005 §3.2 | MUST | `Dockerfile` |
| 4 | 多阶段 Dockerfile（builder + runtime） | ADR-0005 §13.1 + 宪法 §9.7 | MUST | `Dockerfile` |
| 5 | 单一镜像 + 单一 Helm chart（不拆 microimage） | L1 Arch §3.5.1 | SHOULD | `agents/hello/helm/` |
| 6 | `appVersion: 0.2.0` 与 Spec 版本严格对齐 | L3-1 §7 模板 | MUST | `Chart.yaml` |

### B.2 接口与生命周期（5 条）

| # | 实现约束 | 引用来源 | 强度 | 落地 |
|---|----------|----------|------|------|
| 1 | 仅暴露 2 method（`a2a.sendMessage` / `a2a.getTask`） | L1 Arch §3.5.1 | MUST | `agent.py` |
| 2 | `protocolVersion: "0.3"`（与 L1 §5.1 一致） | L1 Spec §5.1 + L3-2 §3 | MUST | `card.py` |
| 3 | `cancel()` 空实现（不抛 NotImplementedError） | a2a-sdk 抽象 | MUST | `agent.py` |
| 4 | Agent Executor 由 L3-2 `DefaultRequestHandler` 装配 | L3-2 §5 | MUST | `agent.py` |
| 5 | `terminationGracePeriodSeconds: 30` 与 §3.2 lifecycle 30s 对齐 | L3-1 §7.7 | MUST | `templates/deployment.yaml` |

### B.3 错误处理（4 条）

| # | 实现约束 | 引用来源 | 强度 | 落地 |
|---|----------|----------|------|------|
| 1 | 不新增错误码；仅复用 L3-2 §10 24 错误码 | L3-2 §10 + 宪法 §15.5 | MUST | 全模块 |
| 2 | 错误 envelope 复用 L3-2 §3 序列化 | L3-2 §3 | MUST | 全模块 |
| 3 | `/readyz` 失败时返回 503 + `{"status":"not_ready"}` | L3-1 §7.6 | MUST | `observability.py` |
| 4 | structlog 8 字段不脱敏（v0.1 简化；v0.5+ 增加 redact） | ADR-0005 §10 | SHOULD | `observability.py` |

### B.4 安全（4 条）

| # | 实现约束 | 引用来源 | 强度 | 落地 |
|---|----------|----------|------|------|
| 1 | 单副本强约束（`replicaCount: 1`） | L1 Arch §3.5.1 + 宪法 §3.4 | MUST | `values.yaml` + `values.schema.json` |
| 2 | 非 root UID 65532 + readOnlyRootFilesystem | 宪法 §3.4 + L3-1 §7.3 | MUST | `values.yaml` `podSecurityContext` |
| 3 | mTLS v0.1 关闭；v0.5+ 启用 cert-manager | 宪法 §6 | SHOULD | `values.yaml` `mtls.enabled: false` |
| 4 | NetworkPolicy 限制跨 namespace | L3-1 §7.6 | MUST | `templates/networkpolicy.yaml` |

### B.5 可观测性与测试（5 条）

| # | 实现约束 | 引用来源 | 强度 | 落地 |
|---|----------|----------|------|------|
| 1 | 4 Python runtime 指标 wire 名与 L3-2 §9.1 完全一致 | L3-2 §9.1 + 宪法 §7 | MUST | `observability.py` |
| 2 | structlog 8 必含字段 | L3-2 §9.3 + 宪法 §7 | MUST | `observability.py` |
| 3 | 单元测试覆盖率 ≥ 90% | L3-2 §11.1 + 宪法 §9.7 | MUST | `tests/unit/` |
| 4 | 4 重静态门禁（pyright strict / ruff / bandit / pip-audit） | ADR-0005 §11 + 宪法 §9.7 | MUST | `pyproject.toml` `[tool.*]` |
| 5 | E2E kind + helm + sendMessage→pong 端到端 | L2-1 §11.5 + 宪法 §7 | MUST | `tests/e2e/test_hello_agent.py` |

---

## 文档元数据与后续入口

### M.1 版本与状态

| 字段 | 值 |
|---|---|
| 版本 | **v0.2.0**（2026-07-29 #61 由 v0.2-draft-full #60 评审通过后升级） |
| 状态 | ✅ **v0.2.0 已通过独立评审**（#60 · 48845 字节 / §A-§J 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项）——**L3 阶段 4/4 完成** |
| 上游 | L1 Architecture v0.2.0 §3.5.1 + L1 Spec v0.2.0 §5 |
| 同级已通过 | L3-1 Operator Core v0.2.0 (#56) + L3-2 A2A Core v0.2.0 (#54) + L3-3 Adapter SDK v0.2.0 (#58) + **L3-4 Hello Agent v0.2.0 (#61)** |
| 评审报告 | [`docs/reviews/l3-4-hello-agent-spec-review.md`](../../reviews/l3-4-hello-agent-spec-review.md)（2026-07-29 #60 · 48845 字节） |
| 3 关注项 | 详见 §M.5（**L3-4-followup-1** §8 "12 ID" vs §8.6 "25 ID" 数字偏差 / **L3-4-followup-2** §7.3 vs §3.2 executor 防御路径命名 / **L3-4-followup-3** §9 节标题"30 验收点" vs 实际"37 验收点"）—— 移交 L4 实施第一周 + ROADMAP 登记 |
| 当前变更边界 | v0.2.0 升级完成；本 Spec 进入 L4 实施可对照状态；3 关注项不阻塞 v0.2.0 升级 |

### M.2 落地记录

| 日期 / 会话 | 增量 | 结果 |
|---|---|---|
| 2026-07-28 #56 | L3-1 v0.2.0 通过 | L3 阶段 1/4 完成 |
| 2026-07-28 #58 | L3-4 v0.2-draft 骨架 + 5 文件级契约 + 8 边界规则 + 镜像基线 + 4 runtime 指标 | §0-§2 + 附录 A/B 占位 |
| 2026-07-29 #59 | L3-4 v0.2-draft-full 完整版：§3-§7 落地 + §8 测试 25 ID + §9 验收 30 验收点 + §10 开放问题 5 项 + 附录 A 6 子表 + 附录 B 5 子表 | **v0.2-draft-full** → 待评审 |
| 2026-07-29 #60 | 独立评审 §A-§J 10 维度：10 PASS · 0 阻塞项 · 3 关注项（§M.5 L3-4-followup-1~3） · 4 建议项 | **具备 v0.2.0 升级条件** |
| 2026-07-29 #61（本会话） | v0.2.0 升级（头部 3 处 + §M.1-M.4 + 签署段落 4 处微同步） + 3 关注项 L3-4-followup-1~3 登记 | **v0.2.0** + **L3 阶段 4/4 完成** |

### M.3 配套引用

- L3-1 Operator Core v0.2.0：`docs/spec/L3-file-specs/L3-operator-core.md`（§3.1 Agent Controller + §7 Helm 9 模板 + §9 验收清单）
- L3-2 A2A Core v0.2.0：`docs/spec/L3-file-specs/L3-a2a-core.md`（§3 envelope + §5 ASGI + §6 A2AClient + §9 15 指标 + §10 24 错误码）
- L3-3 Adapter SDK v0.2.0：`docs/spec/L3-file-specs/L3-adapter-sdk.md`（§3 FrameworkAdapter Protocol，v0.5+ 复用）
- L2-1 A2A Protocol v0.2.0：`docs/spec/L2-module-specs/L2-a2a-protocol.md`（24 错误码 wire 上游权威）
- L1 Architecture v0.2.0：`docs/design/L1-architecture.md` §3.5.1 + §4.3 C-5

### M.4 下次会话固定入口

1. **§F 6 步跨文档同步 #62**（ROADMAP L3 阶段进度 4/4 + L3-4 行 / README L3 模块清单 4/4 + L3-4 v0.2.0 行 / CONSTITUTION-CHANGELOG 新增 #61 行 / L3-1 附录 A.4 配套 Spec 引用 / L3-2 附录 A.4 配套 Spec 引用 / L3-3 附录 A.4 配套 Spec 引用 · 极低风险 ≈ 5-8%）。
2. **L3-5 Knowledge Service 启动 #63**（基于 L2-4 v0.2.0 Spec；目标 50-70KB / ~1300-1700 行 / 建议拆骨架 + §3-§6 补完 + §7-§10 补完 + 附录 A/B + 评审 5 个会话避免 §16.1 红线）。
3. **L3-6 Memory backend 启动 #64+**（基于 L2-4 v0.2.0 Spec；目标 50-70KB / ~1300-1700 行 / 同上分 5 会话）。
4. **3 关注项微同步（v0.2.1 / L4 实施第一周）**：L3-4-followup-1 §8 数字偏差 / L3-4-followup-2 §7.3 命名 / L3-4-followup-3 §9 数字偏差 —— 不阻塞当前 v0.2.0 升级。

### M.5 关注项台账（v0.2.0 升级不阻塞 · 移交 L4 实施第一周 + ROADMAP L3-4-followup-1~3）

| 编号 | 位置 | 类型 | 内容 | 移交 |
|---|---|---|---|---|
| L3-4-followup-1 | §8 段首 "12 ID" vs §8.6 表格 25 ID | 数字偏差 | §8 段首"§8（25 ID 测试策略 + 4 重静态门禁）"无误；§8.1 段落口径"12 ID 段首子集"与 §8.6 完整清单"25 ID"存在偏差，**建议在 §8.1 加偏差说明**（"12 ID 为段首子集，详见 §8.6 唯一权威 25 ID 清单"） | L4 实施第一周 / v0.2.1 |
| L3-4-followup-2 | §7.3 错误路径契约 vs §3.2 executor 防御路径 | 命名不一致 | §7.3 错误路径契约 5 行中 1 行（如 `agent.execute()` 失败）与 §3.2 executor 防御路径命名（`executor.execute` vs `agent_executor.execute`）存在 1 处漂移 | L4 实施第一周 / v0.2.1 |
| L3-4-followup-3 | §9 节标题"30 验收点" vs §9.1-§9.7 实际 37 验收点 | 数字偏差 | §9 节标题"30 验收点 7 子组"与实际 37 验收点（4+6+5+8+4+5+5）存在偏差，**建议改 §9 节标题为"37 验收点 7 子组"** | v0.2.1 微同步 |

---

> **签署**：本 L3-4 Hello Agent 文件级 Spec Python v0.2.0 由 #58 起，经 #59 补完稿 + #60 评审通过 + #61 升级 v0.2.0，依据 [L1 Architecture v0.2.0 §3.5.1 + §4.3 C-5](../../design/L1-architecture.md)、[L1 Spec v0.2.0 §5 hello-agent YAML 示例](../../spec/L1-system-spec.md)、[L3-1 Operator Core v0.2.0 §3.1 + §7](../../spec/L3-file-specs/L3-operator-core.md)、[L3-2 A2A Core v0.2.0 §5 + §6 + §9 + §10](../../spec/L3-file-specs/L3-a2a-core.md)、[L3-3 Adapter SDK v0.2.0](./L3-adapter-sdk.md)、[ADR-0005](../../adr/0005-python-first-technology-stack.md) 与 Constitution v0.5.0 编写。**已通过独立评审（#60），具备 L4 实施可对照状态**；3 关注项 L3-4-followup-1~3 不阻塞 v0.2.0 升级，移交 L4 实施第一周 / v0.2.1 微同步。
