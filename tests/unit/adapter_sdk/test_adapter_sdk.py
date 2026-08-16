"""Adapter SDK unit tests · Phase 5 LAUNCH (#118 2026-08-16).

测试 §17 SOLID 6 原则应用:
- SRP: Adapter 只负责 message 翻译 · AgentCard 只负责 card 转换
- OCP: HelloAdapter 通过 Protocol 扩展 · 不修改核心
- LSP: HelloFrameworkAdapter 是 FrameworkAdapter subtype · 可替换
- DIP: 不依赖 framework SDK 具体类型
- ISP: Adapter / AgentCard Protocol 各自最小化
- CRP: HelloFrameworkAdapter 构造参数注入 greeting
"""

from __future__ import annotations

import pytest
from superteam_a2a.adapter import (
    ADAPTER_ERROR_CODE_RANGE_END,
    ADAPTER_ERROR_CODE_RANGE_START,
    A2AMessage,
    Adapter,
    AgentCard,
    FrameworkAdapter,
    FrameworkResult,
    HelloAdapter,
    HelloAgentCard,
    HelloFrameworkAdapter,
)


def test_adapter_sdk_001_version() -> None:
    """ADAPTER-UT-001 · __version__ = '0.1.0'."""
    from superteam_a2a.adapter import __version__

    assert __version__ == "0.1.0"


def test_adapter_sdk_002_adapter_protocol_is_runtime_checkable() -> None:
    """ADAPTER-UT-002 · Adapter Protocol 是 runtime_checkable · HelloAdapter 满足协议."""
    hello = HelloAdapter()
    assert isinstance(hello, Adapter)
    assert hello.framework_name == "hello"


def test_adapter_sdk_003_agent_card_protocol() -> None:
    """ADAPTER-UT-003 · AgentCard Protocol · HelloAgentCard 满足协议."""
    card = HelloAgentCard()
    assert isinstance(card, AgentCard)
    a2a_card = card.to_a2a_card()
    assert a2a_card["name"] == "Hello Agent"
    assert "skills" in a2a_card
    assert len(a2a_card["skills"]) >= 1


def test_adapter_sdk_004_framework_adapter_composition() -> None:
    """ADAPTER-UT-004 · FrameworkAdapter = Adapter + AgentCard · 构造参数注入."""
    adapter = HelloFrameworkAdapter(greeting="Hi")
    assert isinstance(adapter, FrameworkAdapter)
    assert adapter.adapter.framework_name == "hello"
    assert adapter.card.framework_name == "hello"


@pytest.mark.asyncio
async def test_adapter_sdk_005_hello_adapter_invoke() -> None:
    """ADAPTER-UT-005 · HelloAdapter.invoke 翻译 A2A Message → 返回 FrameworkResult."""
    hello = HelloAdapter(greeting="Hi")
    msg = A2AMessage(role="user", parts=({"type": "text", "text": "world"},))
    result = await hello.invoke(msg)
    assert isinstance(result, FrameworkResult)
    assert "Hi" in result.content
    assert "world" in result.content


@pytest.mark.asyncio
async def test_adapter_sdk_006_framework_adapter_end_to_end() -> None:
    """ADAPTER-UT-006 · HelloFrameworkAdapter.handle_message 端到端测试."""
    adapter = HelloFrameworkAdapter(greeting="Hello")
    msg = A2AMessage(role="user", parts=({"type": "text", "text": "Phase 5"},))
    result = await adapter.handle_message(msg)
    assert "Hello" in result.content
    assert "Phase 5" in result.content


def test_adapter_sdk_007_error_code_range() -> None:
    """ADAPTER-UT-007 · Adapter 扩展错误码范围 -32001 ~ -32099 (L2-3 §5.2).

    JSON-RPC 错误码负数范围: -32099 (more negative) → -32001 (less negative).
    """
    assert ADAPTER_ERROR_CODE_RANGE_START == -32099
    assert ADAPTER_ERROR_CODE_RANGE_END == -32001
    # START 范围下界（更负数）< END 范围上界（较不负数）
    assert ADAPTER_ERROR_CODE_RANGE_START < ADAPTER_ERROR_CODE_RANGE_END


def test_adapter_sdk_008_solid_lsp_substitutability() -> None:
    """ADAPTER-UT-008 · LSP 应用: HelloFrameworkAdapter 可替换为 mock FrameworkAdapter."""

    # Mock 实现满足 Protocol · 证明 LSP 可替换性
    class MockAdapter:
        framework_name = "mock"

        async def invoke(self, message: A2AMessage) -> FrameworkResult:
            return FrameworkResult(content="mocked", metadata={})

    class MockAgentCard:
        framework_name = "mock"
        name = "Mock"
        description = "Mock card"

        def to_a2a_card(self) -> dict:
            return {"name": "Mock", "description": "Mock card"}

    class MockFrameworkAdapter:
        def __init__(self) -> None:
            self.adapter = MockAdapter()
            self.card = MockAgentCard()

        async def handle_message(self, message: A2AMessage) -> FrameworkResult:
            return await self.adapter.invoke(message)

    mock = MockFrameworkAdapter()
    assert isinstance(mock, FrameworkAdapter)
    # 与 HelloFrameworkAdapter 同 protocol 但不同实现
    assert mock.adapter.framework_name == "mock"
    assert HelloFrameworkAdapter().adapter.framework_name == "hello"
