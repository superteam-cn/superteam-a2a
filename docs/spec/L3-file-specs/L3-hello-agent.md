# L3 文件级 Spec：Hello Agent（参考实现 · Python 无框架）

> **模块定位**：C-5 Hello Agent（无框架参考实现 · v0.1 · 单一 Pod / 单 Python 进程 / 单 Uvicorn worker）
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-5（Hello Agent，见 L1 Architecture §4.3）
> **代码位置**：`agents/hello/src/superteam_a2a/hello/`（**ADR-0005 §13.1 uv workspace 布局**）
> **版本**：**v0.2-draft**（2026-07-28 #58 起 Python 重写 + L3-1 v0.2.0 #56 + L3-2 v0.2.0 #54 + L3-3 v0.2-draft-skeleton #57/#57-§3-6 已通过；L3 阶段 3/4 启动）
> **状态**：✅ **v0.2-draft 骨架稿已落地**（#58 本次骨架 + §0-§2 + 附录 A 占位 + 附录 B 占位；§3-§10 + 附录 A 完整版 + 附录 B 5 子表 留待补完）
> **上游约束**：[L1 Architecture v0.2.0 §3.5.1 Hello Agent](../../design/L1-architecture.md)（C-5 · 单 Pod / 单 Python 进程 / 单 Uvicorn worker · 直接实现 A2A 协议端点）+ [L1 Spec v0.2.0 §5 hello-agent 示例](../../spec/L1-system-spec.md)（framework: "custom" / image + adapter 镜像说明）+ [ADR-0005 §3.5 Hello Agent 模块映射](../../adr/0005-python-first-technology-stack.md)（uv workspace 独立仓库）+ [L3-1 Operator Core v0.2.0 §3.1 Agent Controller + §7 RBAC/Helm 9 模板](../../spec/L3-file-specs/L3-operator-core.md)（CRD wire sync）+ [L3-2 A2A Core v0.2.0 §6 A2AClient + §5 ASGI server + §9 15 指标 + §10 24 错误码](../../spec/L3-file-specs/L3-a2a-core.md)（wire 复用）
> **本 Spec 目的**：将 L1 Architecture §3.5.1 描述的 **Hello Agent（无框架参考实现）** 落地为 **文件级 Python 代码契约**——单一文件 + Dockerfile + Helm chart + E2E 演示 — 是 L4 实施阶段（开发者打开 IDE 即可对照写代码）或 v0.1 端到端冒烟测试的直接输入。
> **配套 Spec**：[L3-1 Operator Core 文件级 Spec v0.2.0](./L3-operator-core.md)（2026-07-28 #56 评审通过）/ [L3-2 A2A Core Library 文件级 Spec v0.2.0](./L3-a2a-core.md)（2026-07-28 #54 评审通过 · [评审报告](../../reviews/l3-2-a2a-core-spec-review.md)）/ [L3-3 Adapter SDK 文件级 Spec v0.2-draft-skeleton](./L3-adapter-sdk.md)（2026-07-28 #57/#57-§3-6）/ [L3-5 Knowledge Service 文件级 Spec](./L3-knowledge-service.md)（待起草）/ [L3-6 Memory backend 文件级 Spec](./L3-memory-backend.md)（待起草）
> **配套 Review**：[L3-4 Hello Agent Spec 评审报告](../../reviews/l3-4-hello-agent-spec-review.md)（下一会话创建）

---

## 0. 阅读指南

- **读者**：L4 实施工程师（写 Hello Agent 10-50 行 Python 代码）、E2E 测试工程师（跑通 hello-agent + 另一个 agent 通信）、Demo 演示者
- **必读章节**：§1（模块使命 + 单一文件 + Dockerfile + Helm chart）/ §2（Python 包结构 + 镜像基线）/ 附录 A（跨模块引用清单）/ 附录 B（ADR / Constitution 5 子表追溯矩阵）
- **评审入口**：附录 A 6 子表 + 附录 B 5 子表 + 5 文件级契约 + ∼12 测试 ID 互相回链
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

---

## 附录 A：跨模块引用清单（v0.2-draft 占位）

**说明**：本附录为 v0.2-draft 骨架占位，§3-§10 补完时同步展开 6 子表（L1 / L2 / ADR / Constitution / 配套 L3 / 归档基线）。

| 子表 | 目标文档 | 引用条数 | 状态 |
|------|----------|---------:|------|
| A.1 L1 | `docs/design/L1-architecture.md` §3.5.1 + §4.3 C-5 + `docs/spec/L1-system-spec.md` §5 hello-agent YAML | 待补完 | 占位 |
| A.2 L2 | 无直接 L2 上游（无 Hello Agent L2 模块）；仅 L3-1+L3-2 wire 约束 | 待补完 | 占位 |
| A.3 ADR | `docs/adr/0005-python-first-technology-stack.md` §3.5 + §13.1 | 待补完 | 占位 |
| A.4 Constitution | `docs/CONSTITUTION.md` v0.5.0 §3.4 单进程 + §3.7 Python-first + §6 mTLS + §9.7 静态质量 | 待补完 | 占位 |
| A.5 配套 L3 | L3-1 Operator Core v0.2.0 + L3-2 A2A Core v0.2.0 + L3-3 Adapter SDK v0.2-draft-skeleton | 待补完 | 占位 |
| A.6 归档基线 | 无前置 baseline（Hello Agent v0.1 Go 已在 L1 v0.1.0 中描述；待归档） | 待补完 | 占位 |

---

## 附录 B：ADR / Constitution 引用矩阵（v0.2-draft 占位）

**说明**：本附录为 v0.2-draft 骨架占位，§3-§10 补完时同步展开 5 子表（架构与部署 / 接口与生命周期 / 错误处理 / 安全 / 可观测性与测试）。每条 MUST/SHOULD/MAY 强度分级 + 引用 ADR 章节 + 引用 Constitution 章节。

| 子表 | 主题 | 引用条数 | 状态 |
|------|------|---------:|------|
| B.1 架构与部署 | ADR-0005 §3.5 + 宪法 §3.4 + §3.8 | 待补完 | 占位 |
| B.2 接口与生命周期 | L3-2 §5 ASGI server + §6 A2AClient + L3-1 §3.1 Agent Controller | 待补完 | 占位 |
| B.3 错误处理 | L3-2 §10 24 错误码 enum + 宪法 §15.5 | 待补完 | 占位 |
| B.4 安全 | 宪法 §3.4 单进程 + §6 mTLS（cert-manager v0.5+ 启用 · v0.1 简化） | 待补完 | 占位 |
| B.5 可观测性与测试 | L3-2 §9 4 runtime 指标 + 宪法 §7 + §9.7 | 待补完 | 占位 |

---

## 文档元数据与后续入口

### M.1 版本与状态

| 字段 | 值 |
|---|---|
| 版本 | **v0.2-draft** |
| 状态 | ✅ §0-§2 + 附录 A/B 占位 完整；§3-§10 + 附录 A 完整版 + 附录 B 5 子表 **待补完** |
| 上游 | L1 Architecture v0.2.0 §3.5.1 + L1 Spec v0.2.0 §5 |
| 同级已通过 | L3-1 Operator Core v0.2.0 (#56) + L3-2 A2A Core v0.2.0 (#54) |
| 同级进行中 | L3-3 Adapter SDK v0.2-draft-skeleton (#57) |
| 评审报告 | `docs/reviews/l3-4-hello-agent-spec-review.md`（下一会话创建） |
| 当前变更边界 | 仅本 Spec v0.2-draft；独立评审前不进入 L4 实施 |

### M.2 落地记录

| 日期 / 会话 | 增量 | 结果 |
|---|---|---|
| 2026-07-28 #56 | L3-1 v0.2.0 通过 | L3 阶段 1/4 完成 |
| 2026-07-28 #57 | L3-3 v0.2-draft-skeleton 骨架 + §3-§6 补完 | L3 阶段 2/4 进行中 |
| 2026-07-28 #58（本会话） | L3-4 v0.2-draft 骨架 + 5 文件级契约 + 8 边界规则 + 镜像基线 + 4 runtime 指标 | §0-§2 + 附录 A/B 占位；§3-§10 待补完 → v0.2-draft-full |

### M.3 下一会话固定入口

1. **补完 L3-4 §3-§10 + 完整附录 A + 附录 B**（建议单会话完成，避免 §16.1 双会话通讯成本）：
   - §3 `agent.py` 核心 ASGI app（50 行 · 2 method 路由 + JSON-RPC 解析 + structlog）
   - §4 `card.py` AgentCard JSON 生成（40 行 · /well-known/agent.json 端点）
   - §5 `observability.py` 4 runtime 指标 + /healthz / /readyz（80 行 · 复用 L3-2）
   - §6 Helm chart 7 模板完整契约（deployment + configmap + serviceaccount + networkpolicy + servicemonitor）
   - §7 E2E 演示场景（kubectl apply + 发送 Message + 校验 pong）
   - §8 测试策略 + 工具链（5 UT + 2 E2E + 4 static gate + Dockerfile）
   - §9 验收清单（12 ID + 8 部署交付 + 5 评审归档）
   - §10 开放问题（5 项 · 继承 L1 + Spec 新增 0 = 5 项）
   - 附录 A 6 子表
   - 附录 B 5 子表
2. **升级 v0.2-draft-full**（完整版升级）：头部版本 v0.2-draft → v0.2-draft-full + 状态行 + 落地记录新增 + 入口更新。
3. **独立评审 L3-4 v0.2-draft-full**：创建 `docs/reviews/l3-4-hello-agent-spec-review.md`，按 §A-§P / 10 维度核验 §9 的 12 ID + 5 文件级契约 + 附录 B 五表（参照 L3-1 #56 评审模板 700 行 / 55KB）。
4. **评审通过 + §F 6 步同步 + git commit**（参照 L3-1 #56 + L3-2 #54 commit 模板）。
5. **L3-5 Knowledge Service / L3-6 Memory backend 启动**（L3 阶段 4/4 · 基于 L2-4 v0.2.0 Spec）。

---

> **签署**：本 L3-4 Hello Agent 文件级 Spec Python v0.2-draft 由 #58 起，依据 [L1 Architecture v0.2.0 §3.5.1 + §4.3 C-5](../../design/L1-architecture.md)、[L1 Spec v0.2.0 §5 hello-agent YAML 示例](../../spec/L1-system-spec.md)、[L3-1 Operator Core v0.2.0 §3.1 + §7](../../spec/L3-file-specs/L3-operator-core.md)、[L3-2 A2A Core v0.2.0 §5 + §6 + §9 + §10](../../spec/L3-file-specs/L3-a2a-core.md)、[L3-3 Adapter SDK v0.2-draft-skeleton](./L3-adapter-sdk.md)、[ADR-0005](../../adr/0005-python-first-technology-stack.md) 与 Constitution v0.5.0 编写。**当前骨架稿仅具备进入独立评审的准备条件；§3-§10 + 完整附录 A/B 补完后才能进入独立评审。**
