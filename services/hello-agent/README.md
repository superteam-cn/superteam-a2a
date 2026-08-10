# superteam-a2a Hello Agent Service

Phase 4 PR-1 最小化 Hello Agent 实装（starlette ASGI + 单进程 8080 端口 + 4 Python runtime 指标）。

## 端点

- `GET /.well-known/agent.json` — AgentCard JSON
- `POST /a2a/sendMessage` — A2A message → 返回 Task(artifacts: "pong")
- `GET /healthz` — liveness
- `GET /readyz` — readiness
- `GET /metrics` — Prometheus format（4 Python runtime 指标 + 默认）

## 设计约束

- 单进程 / 端口 8080（与 services/knowledge-memory-service/ 同架构）
- 5 文件级契约：`__init__.py` + `agent.py` + `card.py` + `observability.py` + `_internals.py`
- 不依赖 google-a2a-sdk（推迟到 PR-2 之后）
- 4 指标（python_gc_objects_collected_total / process_cpu_seconds_total / process_resident_memory_bytes / process_open_fds）