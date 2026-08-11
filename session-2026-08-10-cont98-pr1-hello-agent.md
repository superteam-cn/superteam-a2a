# #98 — Phase 4 PR-1 Hello Agent Step 1 完整收口 + A 选项 P0 启动（主 Agent + Subagent 接力 · 2026-08-10）

## 概要

Phase 3 完整收口后启动 Phase 4：用户选 A 选项（P0 全部 · Hello Agent + branch-protection + Knowledge Service 端到端 · 6-8 周集中）。

**本次会话 #98 交付**：
1. ✅ 6 项目 labels 创建（phase1/phase2/phase3/phase4/e2e/memory）
2. ✅ branch-protection-fix 文档化（⑭ 关注项 · 项目发起人 web 端 admin）
3. ✅ L3-4 + L3-5 Spec 调研（Subagent 完整画像）
4. ✅ docs/phase4/pr1-hello-agent-impl-plan.md（8 节 + M.1-M.6）
5. ✅ Hello Agent 完整实装（5 文件 + 22 测试 ID）
6. ✅ commit `b92d1a8` on `feat/phase4-pr1-hello-agent-step1` · 17 files / +1723 / -1
7. ✅ PR #38 创建（open @ `b92d1a8` · 等 CI 6 项 check + 项目发起人合并）

## A 选项 P0 全部 · 5 PR 序列

| PR | 标题 | 工作量 | 状态 |
|---|---|---|---|
| **#98 PR-1** | **Hello Agent Step 1**（5 Python 文件 + 22 测试 ID）| 2 周 | **🟡 open (#38)** |
| #99 PR-2 | Hello Agent Step 2（Dockerfile + 7 Helm + kind E2E） | 1 周 | ⏳ |
| #100 PR-3 | Knowledge Service Step 1（8 CRD types + 4 shared + 测试）| 1.5 周 | ⏳ |
| #101 PR-4 | Knowledge Service Step 2（12 service + 4 A2A handler + 23 错误码） | 2 周 | ⏳ |
| #102 PR-5 | Knowledge Service Step 3（7 Helm + RBAC + kind E2E）| 1 周 | ⏳ |

**Phase 4 总工作量**：~3700 行 / 5 PR / 6-8 周集中（2h/day）

## 关键发现与决策

### ⚠️ 关键设计调整 · 不依赖 google-a2a-sdk

原 L3-4 Spec 假设依赖 Google A2A SDK（a2a-sdk）· 实测发现：

1. **`a2a-sdk` 完全没安装**（uv workspace 0 依赖）
2. **`packages/a2a-core/src/superteam_a2a/a2a/__init__.py` 是 placeholder stub**（仅 8 行 + `__version__`）
3. L4-Step4 #80 实装了 `InProcessContext` 等基础结构（`MemoryBackendInProcessServiceImpl`），但 a2a-core 协议层仍是 stub

**调整方案**：PR-1 实装**最小化 Hello Agent**（starlette + Pydantic + uvicorn · 与 `services/knowledge-memory-service/` 完全一致架构）· 不依赖 google-a2a-sdk · 后续 PR-2 之后才考虑 a2a-core 实装。

### 🪟 Windows 兼容性 · `_PsutilProcessCollector` fallback

prometheus_client 默认 `ProcessCollector` 仅在 Linux /proc 可用 · Windows/macOS 缺失 `process_cpu_seconds_total` 等 4 指标。

**修复**：observability.py 实现 `_PsutilProcessCollector` 自动注册替换默认 · Linux 走默认路径 · Windows/macOS 走 psutil 路径（psutil 加为 dev dep）· `process_open_fds` Windows 退化为 `num_handles`。

### ⏰ Branch Protection ⑭ mismatch

Ruleset `main-protection` 当前 required_status_checks 4 项（`ci/lint ci/test/test ci`）与 ci.yml 实际 job name `Lint / Type-check / Test (Python 3.12)` 不匹配 · CI 失败未阻断 merge。

**修复**：项目发起人 web 端 admin 修改 required status checks · `docs/admin/branch-protection-fix.md` 文档化操作步骤 · gh CLI 受 GitHub REST API 限制（不允许 PUT 修改 contexts）。

## 实装细节

### 5 文件级契约

| 文件 | 行数 | 关键职责 |
|---|---|---|
| `__init__.py` | 10 | 导出 `create_app` |
| `agent.py` | 105 | ASGI app + 2 主路由（`.well-known/agent.json` + `/a2a/sendMessage`）|
| `card.py` | 112 | AgentCard Pydantic + `@lru_cache` |
| `observability.py` | 260 | 4 metrics + structlog + Windows fallback `_PsutilProcessCollector` |
| `_internals.py` | 184 | 单进程 `_task_store` FIFO 1024 + 业务核心 `handle_send_message` |

### 22 测试 ID

```
tests/unit/hello_agent/
  test_agent.py         (6 UT · agent handler + sendMessage + Task return)
  test_card.py          (2 UT · AgentCard schema + lru_cache)
  test_observability.py (3 UT · structlog 8 fields + metrics endpoint + 4 metrics)
  test_internals.py     (4 UT · SendMessagePayload + _task_store + InvalidParamsError)
tests/deploy/
  test_hello_helm_template.py (7 UT · helm template rendering mock)
```

### uv workspace 集成

- 根 `pyproject.toml` `[tool.uv.workspace]` members +1（`services/hello-agent`）
- `[tool.uv.sources]` +1（`superteam-a2a-hello-agent-service`）
- `[dependency-groups] dev` +1（`psutil>=5.9,<7` Windows fallback）
- `[tool.pyright] extraPaths` +1
- `[tool.pytest.ini_options] pythonpath` +1

## TestClient 实测（无 uvicorn · 直接 starlette）

```
GET /.well-known/agent.json: 200 name=hello-agent version=0.1.0
POST /a2a/sendMessage: 200 task_id=a1e5c3d2... state=completed text=pong
GET /healthz: 200 {"status": "healthy"}
GET /readyz: 200 {"status": "ready"}
GET /metrics: 200 metrics_count=20 (4 指标聚合 + 默认 Python 指标)
```

## 验证

```
pytest tests/unit/hello_agent tests/deploy/test_hello_helm_template.py → 22 passed in 0.29s
pytest tests/unit tests/conformance → 263 passed in 1.20s
ruff check . → All checks passed!
ruff format --check . → 173 files already formatted
pyright services/hello-agent/src tests/unit/hello_agent tests/deploy → 0 errors, 75 warnings
```

## 5 项关键不变量 100% 保持

1. **Card-driven 单实例**（`replicaCount: 1` · Helm schema enum 强约束推迟到 PR-2）
2. **Python-first 边界**（不依赖 google-a2a-sdk · L3-2 a2a-core stub 保持）
3. **observability 4 指标**（严格 4 项 · 含 Windows fallback · 不混入 L3-5 25 Memory 指标）
4. **wire contract**（Hello Agent 不涉及 12 MEMORY_* · 0 错误码定义）
5. **单进程 8080 端口**（uvicorn 端口 8080 · 端口独占）

## MEMORY.md 更新

- 头部状态行：#97 → #98（PR-1 Hello Agent Step 1）
- PR 编号：37 → 38
- 测试：241 → 263（PR-1 新增 22）
- session 编号 #98 + 6 labels 创建 + BP fix 文档化
- 下一里程碑 #99 PR-2 Hello Agent Step 2（Dockerfile + 7 Helm 模板）

## 下一里程碑 #99 PR-2

- 工作量：1 周
- 内容：Dockerfile + 7 Helm 模板（Chart.yaml + values.yaml + values.schema.json + deployment + configmap + serviceaccount + networkpolicy + servicemonitor）+ kind cluster E2E（HELLO-E2E-001~003）
- 起点：PR #38 merged 后
- 关注点：Dockerfile 多阶段 builder + psutil runtime 依赖 + replicaCount=1 schema enum 强约束