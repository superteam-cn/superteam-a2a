"""Agent Card JSON schema + GET /.well-known/agent.json endpoint · A2A spec §5.1。

PR-4c plan §2.1 + §2.5：
- build_agent_card() · 構造符合 A2A spec §5.1 的 Card dict（name + description + url + version +
  capabilities + skills + authentication）
- agent_card_endpoint(request) · starlette Request handler · 返回 JSONResponse

不变量（PR-4c §6）：
- 字段名严格匹配 wire contract（L1-system-spec §5.2 + A2A spec §5.1）
- 4 skills：queryKnowledge + getKnowledgeItem + recordMemory + queryMemory
- capabilities 不暴露内部细节（streaming=false + pushNotifications=false + stateTransitionHistory=false）
- authentication.schemes = ["Bearer"]（PR-5 Helm ingress 接入）
"""

from __future__ import annotations

from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

# ============================================================================
# Agent Card 字段常量（A2A spec §5.1 + wire contract L1-system-spec §5.2）
# ============================================================================

AGENT_CARD_NAME = "superteam-a2a-knowledge-memory-service"
AGENT_CARD_DESCRIPTION = (
    "Knowledge + Memory A2A service for superteam-a2a · 4 JSON-RPC methods"
    " (recordMemory / queryMemory / queryKnowledge / getKnowledgeItem)"
    " + BM25 inverted index + 4-level scope resolver + 5-dim visibility matrix."
)
AGENT_CARD_URL = "http://knowledge-memory-service:8080"
AGENT_CARD_VERSION = "0.1.0"
AGENT_CARD_PROTOCOL_VERSION = "0.3"

# 4 skills（A2A spec §5.1 skill = id + name + description + inputSchema + outputSchema）
AGENT_CARD_SKILLS: tuple[dict[str, str], ...] = (
    {
        "id": "queryKnowledge",
        "name": "queryKnowledge",
        "description": "BM25 full-text search across knowledge items (PR-4c BM25 inverted index).",
        "inputModes": "text",
        "outputModes": "text",
    },
    {
        "id": "getKnowledgeItem",
        "name": "getKnowledgeItem",
        "description": (
            "Fetch a single KnowledgeItem by (namespace, name) with superseded_by chain walk."
        ),
        "inputModes": "text",
        "outputModes": "text",
    },
    {
        "id": "recordMemory",
        "name": "recordMemory",
        "description": (
            "Write a Memory CRD with 50ms admission fail-closed (PR-4a AdmissionValidatorImpl)."
        ),
        "inputModes": "text",
        "outputModes": "text",
    },
    {
        "id": "queryMemory",
        "name": "queryMemory",
        "description": (
            "Query Memory records with scope/visibility filter (PR-4a + PR-4b industry pre-check)."
        ),
        "inputModes": "text",
        "outputModes": "text",
    },
)

# 4 endpoint 暴露（A2A discovery · PR-4c §2.1）
AGENT_CARD_ENDPOINTS: tuple[dict[str, str], ...] = (
    {"path": "/.well-known/agent.json", "method": "GET", "description": "Agent Card discovery"},
    {"path": "/jsonrpc", "method": "POST", "description": "JSON-RPC 2.0 dispatcher"},
    {"path": "/healthz", "method": "GET", "description": "Liveness probe (kopf replacement)"},
    {"path": "/readyz", "method": "GET", "description": "Readiness probe (kopf replacement)"},
    {"path": "/metrics", "method": "GET", "description": "Prometheus metrics endpoint"},
)


def build_agent_card() -> dict[str, Any]:
    """構造 A2A spec §5.1 Agent Card dict（wire JSON shape 不变）。

    返回 dict 结构与 L1-system-spec §5.2 + A2A spec §5.1 严格一致：
    - name / description / url / version / protocolVersion
    - capabilities { streaming / pushNotifications / stateTransitionHistory }
    - skills [4 项 · id + name + description + inputModes + outputModes]
    - authentication { schemes: ["Bearer"] }
    - endpoints [5 项 · path + method + description]

    不变量：
    - 字段名严格 snake_case（wire JSON · populate_by_name 双向映射）
    - 4 skills 顺序固定（queryKnowledge + getKnowledgeItem + recordMemory + queryMemory）
    - capabilities 全部 false（v0.1 不暴露内部细节）
    """
    return {
        "name": AGENT_CARD_NAME,
        "description": AGENT_CARD_DESCRIPTION,
        "url": AGENT_CARD_URL,
        "version": AGENT_CARD_VERSION,
        "protocolVersion": AGENT_CARD_PROTOCOL_VERSION,
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "skills": [
            {
                "id": skill["id"],
                "name": skill["name"],
                "description": skill["description"],
                "inputModes": [skill["inputModes"]],
                "outputModes": [skill["outputModes"]],
            }
            for skill in AGENT_CARD_SKILLS
        ],
        "authentication": {"schemes": ["Bearer"]},
        "endpoints": list(AGENT_CARD_ENDPOINTS),
    }


async def agent_card_endpoint(request: Request) -> JSONResponse:
    """GET /.well-known/agent.json · starlette Request handler。

    返回 JSONResponse + status_code=200 + content-type=application/json。
    与 A2A spec §5.1 discovery 路径严格一致（/.well-known/agent.json）。
    """
    return JSONResponse(build_agent_card())


__all__ = [
    "AGENT_CARD_DESCRIPTION",
    "AGENT_CARD_ENDPOINTS",
    "AGENT_CARD_NAME",
    "AGENT_CARD_PROTOCOL_VERSION",
    "AGENT_CARD_SKILLS",
    "AGENT_CARD_URL",
    "AGENT_CARD_VERSION",
    "agent_card_endpoint",
    "build_agent_card",
]
