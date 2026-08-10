"""superteam-a2a Hello Agent Service · Phase 4 PR-1 最小化实装。

单进程 ASGI server（端口 8080）+ 4 Python runtime 指标 + A2A AgentCard。
"""

from superteam_a2a.hello_agent.agent import create_app

__version__ = "0.1.0"

__all__ = ["__version__", "create_app"]
