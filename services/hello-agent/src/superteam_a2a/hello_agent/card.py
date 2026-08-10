"""Hello Agent · AgentCard Pydantic model + build_agent_card()。

L3-4 §1.2 + §4 文件级契约：
- AgentCard（name + version + description + url + capabilities + skills + provider + version）
- build_agent_card() @lru_cache 单例（避免重复构造）
- GET /.well-known/agent.json 路由直接 model_dump(mode="json")

A2A AgentCard schema（Google A2A 协议 §1 well-known endpoint）：
- name: Agent name (e.g. "hello-agent")
- version: SemVer
- description: 简短描述
- url: Agent URL（默认 http://localhost:8080）
- capabilities: streaming / pushNotifications 开关（v0.1 关闭）
- skills: 1 个 Echo skill（ping → pong）
- provider: organization info
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field


class AgentSkill(BaseModel):
    """A2A AgentCard skill 子结构（L3-4 §4 最小化：1 Echo skill）。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="skill id 唯一标识")
    name: str = Field(..., description="skill 名称")
    description: str = Field(..., description="skill 简短描述")
    tags: list[str] = Field(default_factory=list, description="skill 标签")


class AgentCapabilities(BaseModel):
    """A2A AgentCard capabilities 子结构（L3-4 §4 v0.1 全关闭）。"""

    model_config = ConfigDict(extra="forbid")

    streaming: bool = Field(default=False, description="v0.1 不支持 stream")
    push_notifications: bool = Field(default=False, description="v0.1 不支持 pushNotification")


class AgentProvider(BaseModel):
    """A2A AgentCard provider 子结构（L3-4 §4 organization info）。"""

    model_config = ConfigDict(extra="forbid")

    organization: str = Field(..., description="organization name")
    url: str = Field(..., description="organization URL")


class AgentCard(BaseModel):
    """A2A AgentCard 完整结构（L3-4 §4 + Google A2A 协议 §1）。

    wire format 字段名遵循 camelCase（alias）；Python 字段名 snake_case（populate_by_name=True）。
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    name: str = Field(..., description="Agent name")
    version: str = Field(..., description="Agent semver")
    description: str = Field(..., description="Agent description")
    url: str = Field(..., description="Agent endpoint URL")
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    skills: list[AgentSkill] = Field(default_factory=list)
    provider: AgentProvider | None = Field(default=None)


@lru_cache(maxsize=1)
def build_agent_card(*, base_url: str = "http://localhost:8080") -> AgentCard:
    """构造默认 AgentCard 单例（@lru_cache 避免重复构造）。

    base_url 用于覆盖 url 字段（测试 + Helm template 渲染时注入真实 Service URL）。
    """
    return AgentCard(
        name="hello-agent",
        version="0.1.0",
        description="superteam-a2a Hello Agent · Phase 4 PR-1 最小化实装 · ping → pong",
        url=base_url,
        capabilities=AgentCapabilities(),
        skills=[
            AgentSkill(
                id="echo",
                name="echo",
                description="Echo skill · 接收 ping → 返回 pong",
                tags=["echo", "ping-pong", "hello-world"],
            ),
        ],
        provider=AgentProvider(
            organization="superteam-a2a contributors",
            url="https://github.com/superteam-cn/superteam-a2a",
        ),
    )


def reset_agent_card_cache() -> None:
    """测试辅助：清空 lru_cache 单例（让 base_url 重新生效）。

    不导出到 __all__（test fixture 使用）。
    """
    build_agent_card.cache_clear()


__all__ = [
    "AgentCapabilities",
    "AgentCard",
    "AgentProvider",
    "AgentSkill",
    "build_agent_card",
]
