"""L4-Phase4 PR-4c ASGI server 入口 · starlette + uvicorn + 4 JSON-RPC method + Agent Card。

依据 docs/phase4/pr4c-knowledge-service-step2c-plan.md §2.1 + §2.5：
- app · Starlette Application 装配（lifespan + 5 routes）
- routes · JSON-RPC 2.0 dispatcher（4 method 路由 + envelope 包装）
- card · Agent Card JSON schema（A2A spec §5.1）

D 方案单进程（ADR-0006 v1.0 Accepted）· uvicorn worker=1 · 与 kopf 共享 asyncio loop。
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.asgi.app import create_app
from superteam_a2a.knowledge_memory.asgi.card import (
    agent_card_endpoint,
    build_agent_card,
)
from superteam_a2a.knowledge_memory.asgi.routes import jsonrpc_dispatch

__all__ = [
    "agent_card_endpoint",
    "build_agent_card",
    "create_app",
    "jsonrpc_dispatch",
]
