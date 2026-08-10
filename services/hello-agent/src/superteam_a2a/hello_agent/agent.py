"""Hello Agent · 核心 ASGI app（starlette + AgentCard + sendMessage 路由）。

L3-4 §1 + §2 文件级契约（~50 行核心）：
- create_app() factory：构造 starlette app · 注入 observability
- GET /.well-known/agent.json · 返回 AgentCard
- POST /a2a/sendMessage · 接收 A2A message → 返回 Task(artifacts: "pong")
- 异常：InvalidParamsError → 400 · 其他 → 500

5 项关键不变量（PR-1 验证）：
1. Card-driven 单实例（replicaCount=1 · PR-2 Helm schema enum）
2. Python-first 边界（不依赖 google-a2a-sdk · 5 依赖 pydantic/starlette/uvicorn/prometheus/structlog）
3. observability 4 指标（observability.py 严格 4 项）
4. wire contract 不变（Hello Agent 不涉及 MEMORY_* · 0 错误码定义）
5. 单进程 8080 端口（uvicorn 单进程 · 端口独占）
"""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from superteam_a2a.hello_agent._internals import (
    InvalidParamsError,
    handle_send_message,
)
from superteam_a2a.hello_agent.card import build_agent_card
from superteam_a2a.hello_agent.observability import bind_metrics_to_app

# ============================================================================
# A2A 路由 handlers
# ============================================================================


async def agent_card_endpoint(request: Request) -> JSONResponse:
    """GET /.well-known/agent.json · 返回 AgentCard JSON。

    L3-4 §4 契约：name + version + description + url + capabilities + skills + provider。
    """
    card = build_agent_card()
    return JSONResponse(card.model_dump(mode="json"))


async def send_message_endpoint(request: Request) -> Response:
    """POST /a2a/sendMessage · 接收 A2A message → 返回 Task(artifacts: "pong")。

    5 步契约（L3-4 §6）：
    1. await request.json() 解析 body
    2. handle_send_message(payload) 业务核心（_internals.py）
    3. 成功 → 200 + Task dict
    4. InvalidParamsError → 400 + {"error": "invalid_params", "detail": ...}
    5. 其他异常 → 500 + {"error": "internal_error", "detail": ...}
    """
    try:
        payload = await request.json()
    except Exception as exc:
        return JSONResponse(
            {"error": "invalid_json", "detail": str(exc)},
            status_code=400,
        )
    try:
        task = handle_send_message(payload=payload)
    except InvalidParamsError as exc:
        return JSONResponse(
            {"error": "invalid_params", "detail": exc.message},
            status_code=400,
        )
    except Exception as exc:
        return JSONResponse(
            {"error": "internal_error", "detail": str(exc)},
            status_code=500,
        )
    return JSONResponse(task, status_code=200)


# ============================================================================
# App factory
# ============================================================================


def create_app() -> Starlette:
    """构造 starlette App · AgentCard + sendMessage + observability 路由全注册。

    5 路由（端口 8080 共享）：
    - GET /.well-known/agent.json → agent_card_endpoint
    - POST /a2a/sendMessage → send_message_endpoint
    - GET /healthz → observability.healthz（bind_metrics_to_app 注入）
    - GET /readyz → observability.readyz（bind_metrics_to_app 注入）
    - GET /metrics → observability.metrics_endpoint（bind_metrics_to_app 注入）

    Returns:
        Starlette ASGI app（uvicorn 直接 serve）
    """
    app = Starlette(
        debug=False,
        routes=[
            Route("/.well-known/agent.json", agent_card_endpoint, methods=["GET"]),
            Route("/a2a/sendMessage", send_message_endpoint, methods=["POST"]),
        ],
    )
    bind_metrics_to_app(app)
    return app


__all__ = ["create_app"]
