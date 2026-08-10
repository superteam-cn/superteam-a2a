"""starlette /metrics 端点 binding（HELM-DEPLOY-007 验证项）。

调用 bind_metrics_to_app(app) 后注册 GET /metrics 路由，generate_latest() 返回
prometheus text format 0.0.4（CONTENT_TYPE_LATEST）。
"""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route


async def metrics_endpoint(request: Request) -> Response:
    """GET /metrics · prometheus text format 0.0.4 输出（25 指标聚合）。

    prometheus_client.generate_latest() 默认从全局 REGISTRY 读取所有已注册指标。
    同步 I/O 极少（纯内存读 + encode）· 微秒级 · 不阻塞 asyncio event loop。
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def bind_metrics_to_app(app: object) -> None:
    """注册 GET /metrics route 到 starlette app（plan §3.1 复用 8080 端口）。

    与 healthz / jsonrpc_* 同端口（D 方案单进程）· ServiceMonitor port=http 自动发现。
    """
    # app 必须有 routes 属性（starlette 协议）
    app.routes.append(  # type: ignore[attr-defined]
        Route("/metrics", metrics_endpoint, methods=["GET"])
    )
