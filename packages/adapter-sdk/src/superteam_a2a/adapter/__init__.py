"""superteam-a2a Adapter SDK (C-3).

framework-neutral adapter 模板 · typing.Protocol 契约 · Python-native framework 同进程 plugin。
依据 L2-3 Adapter Design v0.2.0 + ADR-0005 §3.3 + 宪法 v0.6.0 §17 SOLID。

Phase 5 LAUNCH 实装（#118 2026-08-16）：
- Adapter Protocol：framework-neutral contract · A2A Message ↔ framework native 调用
- AgentCard Protocol：framework 元数据 → A2A AgentCard
- FrameworkAdapter Protocol：组合 Adapter + AgentCard · framework adapter 入口
- HelloAdapter：参考实现 · 不依赖任何外部 framework SDK · 永远 PASS
- 错误码：Adapter 扩展错误 -32001 ~ -32099（保留给 framework adapter 使用）

宪法 §17 SOLID 应用：
- SRP：Adapter Protocol 只负责 message 翻译 · AgentCard Protocol 只负责 card 转换
- OCP：FrameworkAdapter Protocol 通过组合扩展 · 不修改核心契约
- LSP：HelloAdapter / LangChainAdapter / AutoGenAdapter 互相可替换
- DIP：依赖 Protocol 接口 · 不依赖 framework SDK 具体类型
- ISP：Adapter / AgentCard Protocol 最小化 · 各自独立
- CRP：构造参数注入（framework_config + card_metadata）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

__version__ = "0.1.0"

# Adapter 扩展错误码范围（-32099 ~ -32001 · L2-3 §5.2）
# JSON-RPC 错误码负数约定：START = 范围下界（更负数）= -32099
#                          END   = 范围上界（较不负数）= -32001
ADAPTER_ERROR_CODE_RANGE_START: int = -32099
ADAPTER_ERROR_CODE_RANGE_END: int = -32001


@dataclass(frozen=True)
class A2AMessage:
    """A2A protocol message (subset)."""

    role: str  # "user" / "agent"
    parts: tuple[dict[str, Any], ...]  # [{"type": "text", "text": "..."}]


@dataclass(frozen=True)
class FrameworkResult:
    """Framework native call result (subset)."""

    content: str
    metadata: dict[str, Any]


@runtime_checkable
class Adapter(Protocol):
    """Framework-neutral Adapter protocol · SRP (single responsibility: message translation).

    实现此 Protocol 的类负责把 A2A Message 翻译为 framework native 调用 + 返回结果。
    """

    framework_name: str

    async def invoke(self, message: A2AMessage) -> FrameworkResult:
        """Translate A2A message → framework native call → return result."""
        ...


@runtime_checkable
class AgentCard(Protocol):
    """Framework-neutral AgentCard protocol · SRP (card metadata conversion).

    实现此 Protocol 的类负责把 framework 元数据转换为 A2A AgentCard（JSON）。
    """

    framework_name: str
    name: str
    description: str

    def to_a2a_card(self) -> dict[str, Any]:
        """Return A2A AgentCard JSON dict (per A2A spec §3)."""
        ...


@runtime_checkable
class FrameworkAdapter(Protocol):
    """组合 Adapter + AgentCard · CRP (构造参数注入).

    framework adapter 入口 · 集成 Adapter 翻译能力 + AgentCard 元数据。
    """

    adapter: Adapter
    card: AgentCard

    async def handle_message(self, message: A2AMessage) -> FrameworkResult:
        """End-to-end: receive A2A message → translate → invoke → return."""
        ...


class HelloAdapter:
    """Hello Adapter · 参考实现 · SRP + DIP 应用.

    不依赖任何外部 framework SDK · 永远 PASS · 用于演示 adapter SDK 使用方式。
    framework_name = "hello"
    """

    framework_name = "hello"

    def __init__(self, greeting: str = "Hello from superteam-a2a") -> None:
        self._greeting = greeting

    async def invoke(self, message: A2AMessage) -> FrameworkResult:
        text = next(
            (p["text"] for p in message.parts if p.get("type") == "text"),
            "",
        )
        return FrameworkResult(
            content=f"{self._greeting} · received: {text}",
            metadata={"adapter": "hello", "role": message.role},
        )


class HelloAgentCard:
    """Hello AgentCard · 参考实现 · SRP + OCP 应用.

    不依赖 framework SDK · 永远 PASS · 用于演示 AgentCard protocol.
    """

    framework_name = "hello"
    name = "Hello Agent"
    description = "Reference Hello Agent · always replies with greeting + echo."

    def to_a2a_card(self) -> dict[str, Any]:
        """Return A2A spec §3 compliant AgentCard JSON."""
        return {
            "name": self.name,
            "description": self.description,
            "url": "http://hello-agent:8080/",
            "version": "0.1.0",
            "capabilities": {"streaming": False},
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "skills": [
                {
                    "id": "hello_echo",
                    "name": "Echo",
                    "description": self.description,
                },
            ],
        }


class HelloFrameworkAdapter:
    """Hello FrameworkAdapter · 组合 HelloAdapter + HelloAgentCard · LSP 应用.

    framework_name = "hello" · 是 HelloAdapter / HelloAgentCard 的 subtype · 可替换。
    """

    def __init__(self, greeting: str = "Hello from superteam-a2a") -> None:
        self.adapter = HelloAdapter(greeting=greeting)
        self.card = HelloAgentCard()

    async def handle_message(self, message: A2AMessage) -> FrameworkResult:
        return await self.adapter.invoke(message)


__all__ = [
    "ADAPTER_ERROR_CODE_RANGE_END",
    "ADAPTER_ERROR_CODE_RANGE_START",
    "A2AMessage",
    "Adapter",
    "AgentCard",
    "FrameworkAdapter",
    "FrameworkResult",
    "HelloAdapter",
    "HelloAgentCard",
    "HelloFrameworkAdapter",
]
