"""Hello Agent · agent.py 测试 · HELLO-AGENT-001~005（5 UT）。

依据 Phase 4 PR-1 plan §2.1 + L3-4 §1 + §6 业务核心契约：
- TestClient in-process HTTP · 5 路由全验证
- agent_card_endpoint · send_message_endpoint · create_app factory
- 异常路径（invalid JSON / InvalidParamsError / Task 包含 "pong"）
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

# ============================================================================
# 路径前置（services/hello-agent/src 在 sys.path 最前）
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HA_SRC = _REPO_ROOT / "services" / "hello-agent" / "src"
_HA_PATH = str(_HA_SRC)
if _HA_PATH not in sys.path:
    sys.path.insert(0, _HA_PATH)

from superteam_a2a.hello_agent import create_app  # noqa: E402
from superteam_a2a.hello_agent._internals import (  # noqa: E402
    reset_task_store,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def app():
    """构造 starlette app（每次 fixture 重建）。"""
    reset_task_store()
    return create_app()


@pytest.fixture
def client(app):
    """TestClient 实例。"""
    return TestClient(app)


@pytest.fixture
def valid_send_payload() -> dict:
    """标准 sendMessage payload（A2A message with text part）。"""
    return {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": "ping"}],
        },
    }


# ============================================================================
# HELLO-AGENT-001 · create_app factory · 5 路由注册成功
# ============================================================================


def test_create_app_returns_starlette_with_5_routes(app):
    """HELLO-AGENT-001: create_app() 返回 Starlette 实例 + 5 路由注册。

    5 路由：
    - GET /.well-known/agent.json
    - POST /a2a/sendMessage
    - GET /healthz
    - GET /readyz
    - GET /metrics
    """
    from starlette.applications import Starlette

    assert isinstance(app, Starlette)
    paths = [getattr(route, "path", "") for route in app.routes]
    assert "/.well-known/agent.json" in paths
    assert "/a2a/sendMessage" in paths
    assert "/healthz" in paths
    assert "/readyz" in paths
    assert "/metrics" in paths


# ============================================================================
# HELLO-AGENT-002 · GET /.well-known/agent.json · 返回 AgentCard
# ============================================================================


def test_agent_card_endpoint_returns_card(client):
    """HELLO-AGENT-002: GET /.well-known/agent.json 返回 AgentCard JSON。

    验证：name="hello-agent" + version + skills 包含 echo。
    """
    response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "hello-agent"
    assert data["version"] == "0.1.0"
    assert "description" in data
    assert "url" in data
    assert "capabilities" in data
    assert "skills" in data
    skill_ids = [s["id"] for s in data["skills"]]
    assert "echo" in skill_ids


# ============================================================================
# HELLO-AGENT-003 · POST /a2a/sendMessage happy path · 返回 "pong" Task
# ============================================================================


def test_send_message_happy_path_returns_pong(client, valid_send_payload):
    """HELLO-AGENT-003: POST /a2a/sendMessage 接收合法 payload → 返回 Task(artifacts: "pong")。

    验证：
    - status_code == 200
    - response 含 id + context_id + status.state="completed"
    - artifacts 含 parts[0].text="pong"
    """
    response = client.post("/a2a/sendMessage", json=valid_send_payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "context_id" in data
    assert data["status"]["state"] == "completed"
    assert len(data["artifacts"]) >= 1
    assert data["artifacts"][0]["parts"][0]["text"] == "pong"


# ============================================================================
# HELLO-AGENT-004 · POST /a2a/sendMessage 校验失败 · 400 + invalid_params
# ============================================================================


def test_send_message_invalid_payload_returns_400(client):
    """HELLO-AGENT-004: sendMessage payload 缺 message.parts → 400 + invalid_params。"""
    bad_payload = {"message": {"role": "user", "parts": []}}  # 空 parts 违反 min_length=1
    response = client.post("/a2a/sendMessage", json=bad_payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "invalid_params"


def test_send_message_missing_message_field_returns_400(client):
    """HELLO-AGENT-004 补充：顶层缺 message 字段 → 400 + invalid_params。"""
    response = client.post("/a2a/sendMessage", json={"foo": "bar"})
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "invalid_params"


# ============================================================================
# HELLO-AGENT-005 · POST /a2a/sendMessage JSON 解析失败 · 400 + invalid_json
# ============================================================================


def test_send_message_invalid_json_returns_400(client):
    """HELLO-AGENT-005: sendMessage body 非 JSON → 400 + invalid_json。"""
    response = client.post(
        "/a2a/sendMessage",
        content=b"not-valid-json{{",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "invalid_json"
