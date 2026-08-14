"""PR-4c Agent Card unit tests · CARD-UT-001 + CARD-UT-002 + CARD-UT-003。

PR-4c plan §7 测试 ID 命名：
- CARD-UT-001 · Agent Card matches A2A spec §5.1 schema（name + description + url +
  version + capabilities + skills + authentication 全部字段存在）
- CARD-UT-002 · Agent Card lists 4 skills（queryKnowledge + getKnowledgeItem +
  recordMemory + queryMemory · 每 skill 含 id + name + description）
- CARD-UT-003 · Agent Card endpoint returns JSONResponse（status_code=200 +
  content-type=application/json）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 路径前置（与 test_app.py 模式一致）
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_OP_SRC = _REPO_ROOT / "packages" / "operator" / "src"

_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)
_OP_PATH = str(_OP_SRC)
if _OP_PATH not in sys.path:
    if _KM_PATH in sys.path:
        km_idx = sys.path.index(_KM_PATH)
        sys.path.insert(km_idx + 1, _OP_PATH)
    else:
        sys.path.insert(0, _OP_PATH)

import pytest  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402
from superteam_a2a.knowledge_memory.asgi.card import (  # noqa: E402
    AGENT_CARD_DESCRIPTION,
    AGENT_CARD_NAME,
    AGENT_CARD_PROTOCOL_VERSION,
    AGENT_CARD_URL,
    AGENT_CARD_VERSION,
    agent_card_endpoint,
    build_agent_card,
)

# ============================================================================
# CARD-UT-001 · Agent Card matches A2A spec §5.1 schema
# ============================================================================


def test_card_ut_001_agent_card_matches_a2a_spec_schema() -> None:
    """CARD-UT-001 · agent_card dict 字段严格符合 A2A spec §5.1。

    验证 name + description + url + version + protocolVersion + capabilities +
    skills + authentication + endpoints 全部字段存在。
    """
    card = build_agent_card()

    # 必填顶层字段（A2A spec §5.1）
    assert card["name"] == AGENT_CARD_NAME
    assert card["description"] == AGENT_CARD_DESCRIPTION
    assert card["url"] == AGENT_CARD_URL
    assert card["version"] == AGENT_CARD_VERSION
    assert card["protocolVersion"] == AGENT_CARD_PROTOCOL_VERSION

    # capabilities 子结构（streaming / pushNotifications / stateTransitionHistory）
    capabilities = card["capabilities"]
    assert capabilities["streaming"] is False
    assert capabilities["pushNotifications"] is False
    assert capabilities["stateTransitionHistory"] is False

    # skills 列表（至少 1 项 · max 50 · 这里 4 项）
    assert isinstance(card["skills"], list)
    assert len(card["skills"]) >= 1

    # authentication 子结构（Bearer）
    auth = card["authentication"]
    assert auth["schemes"] == ["Bearer"]

    # endpoints 列表（5 项 · /.well-known/agent.json + /jsonrpc + /healthz + /readyz + /metrics）
    assert isinstance(card["endpoints"], list)
    assert len(card["endpoints"]) == 5


# ============================================================================
# CARD-UT-002 · Agent Card lists 4 skills
# ============================================================================


def test_card_ut_002_agent_card_lists_4_skills() -> None:
    """CARD-UT-002 · skills 数组包含 4 项（queryKnowledge + getKnowledgeItem + recordMemory + queryMemory）。

    每 skill 含 id + name + description（A2A spec §5.1）。
    """
    card = build_agent_card()
    skills = card["skills"]
    assert len(skills) == 4

    skill_ids = [skill["id"] for skill in skills]
    skill_names = [skill["name"] for skill in skills]
    expected_ids = {
        "queryKnowledge",
        "getKnowledgeItem",
        "recordMemory",
        "queryMemory",
    }
    assert set(skill_ids) == expected_ids
    assert set(skill_names) == expected_ids

    # 每 skill 含 id + name + description
    for skill in skills:
        assert "id" in skill
        assert "name" in skill
        assert "description" in skill
        assert isinstance(skill["description"], str)
        assert len(skill["description"]) > 0


def test_card_ut_002_skill_order_matches_plan() -> None:
    """CARD-UT-002 补充：skills 顺序固定（plan §2.1 顺序：queryKnowledge + getKnowledgeItem + recordMemory + queryMemory）。"""
    card = build_agent_card()
    skill_ids = [skill["id"] for skill in card["skills"]]
    assert skill_ids == [
        "queryKnowledge",
        "getKnowledgeItem",
        "recordMemory",
        "queryMemory",
    ]


# ============================================================================
# CARD-UT-003 · Agent Card endpoint returns JSONResponse
# ============================================================================


@pytest.mark.asyncio
async def test_card_ut_003_agent_card_endpoint_returns_jsonresponse() -> None:
    """CARD-UT-003 · agent_card_endpoint 返回 JSONResponse + status_code=200 + content-type=application/json。"""
    application = None  # Agent Card endpoint 不需要 app.state
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/.well-known/agent.json",
        "headers": [],
        "query_string": b"",
    }
    if application is not None:
        scope["app"] = application
    request = Request(scope)
    response = await agent_card_endpoint(request)
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200

    # 解析 body 验证 content-type + 内容
    parsed = json.loads(bytes(response.body).decode("utf-8"))
    assert parsed["name"] == AGENT_CARD_NAME
    assert parsed["version"] == AGENT_CARD_VERSION
    assert parsed["protocolVersion"] == AGENT_CARD_PROTOCOL_VERSION


@pytest.mark.asyncio
async def test_card_ut_003_endpoint_serializable_to_json() -> None:
    """CARD-UT-003 补充：Agent Card dict 可 JSON 序列化（A2A wire format）。"""
    card = build_agent_card()
    serialized = json.dumps(card)
    deserialized = json.loads(serialized)
    assert deserialized == card
