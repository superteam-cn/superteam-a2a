"""Hello Agent · card.py 测试 · HELLO-CARD-001（1 UT）。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ============================================================================
# 路径前置
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HA_SRC = _REPO_ROOT / "services" / "hello-agent" / "src"
_HA_PATH = str(_HA_SRC)
if _HA_PATH not in sys.path:
    sys.path.insert(0, _HA_PATH)

from superteam_a2a.hello_agent.card import (  # noqa: E402
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    build_agent_card,
    reset_agent_card_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    """autouse fixture: 每个测试前清 lru_cache（避免 base_url 残留）。"""
    reset_agent_card_cache()
    yield
    reset_agent_card_cache()


# ============================================================================
# HELLO-CARD-001 · build_agent_card + lru_cache 单例 + base_url 覆盖
# ============================================================================


def test_build_agent_card_lru_cache_and_base_url_override():
    """HELLO-CARD-001: build_agent_card @lru_cache 单例 + base_url 覆盖字段。

    验证：
    - 默认 url = "http://localhost:8080"
    - 二次调用同名 → 返回同一实例（lru_cache 单例）
    - base_url 覆盖后 url 字段更新
    - skills 包含 echo + capabilities 全关闭 + provider organization 正确
    """
    card_default = build_agent_card()
    assert card_default.url == "http://localhost:8080"
    assert card_default.name == "hello-agent"
    assert card_default.version == "0.1.0"

    # lru_cache 单例：相同参数返回同一对象
    card_default_again = build_agent_card()
    assert card_default_again is card_default

    # base_url 覆盖（独立缓存条目）
    card_custom = build_agent_card(base_url="https://hello-agent.example.com")
    assert card_custom.url == "https://hello-agent.example.com"
    assert card_custom is not card_default  # 不同缓存条目

    # skills + capabilities + provider 验证
    skill_ids = [s.id for s in card_custom.skills]
    assert "echo" in skill_ids
    assert card_custom.capabilities.streaming is False
    assert card_custom.capabilities.push_notifications is False
    assert card_custom.provider is not None
    assert card_custom.provider.organization == "superteam-a2a contributors"


def test_agent_card_pydantic_models_validate():
    """HELLO-CARD-001 补充：AgentCard 子模型 Pydantic 校验。

    验证 AgentSkill / AgentCapabilities / AgentProvider / AgentCard 全部可独立构造。
    """
    skill = AgentSkill(id="x", name="X", description="x skill", tags=["t1"])
    assert skill.id == "x"
    assert skill.tags == ["t1"]

    caps = AgentCapabilities(streaming=True, push_notifications=True)
    assert caps.streaming is True
    assert caps.push_notifications is True

    provider = AgentProvider(organization="org", url="https://org.example")
    assert provider.organization == "org"

    card = AgentCard(
        name="custom-agent",
        version="1.2.3",
        description="custom",
        url="http://localhost:9000",
        capabilities=caps,
        skills=[skill],
        provider=provider,
    )
    assert card.name == "custom-agent"
    assert card.version == "1.2.3"
    assert len(card.skills) == 1
