"""Scope resolver 业务逻辑层 · 4 级 scope 解析.

PR-4c plan §2.3 · L3-5 §3.1 + L3-6 §3 + ADR-0002 §3.

提供两个核心组件：
- ScopeResolver · 4 级 scope resolver 主类（validate_parent + resolve_chain + resolve_scope）
- traverse_scope_chain · scope 继承链遍历函数（4 级校验 + self-reference + max_depth）
- ScopeCache + InMemoryScopeCache · scope 缓存接口 + 内存实现

宪法 §17 SOLID：
- SRP：resolver.py 主类 + chain.py 遍历函数 + matrix.py（visibility）策略表单一职责
- OCP：通过 ScopeCache / VisibilityMatrix 协议注入扩展（不修改核心方法）
- LSP：InMemoryScopeCache 是 ScopeCache 子类，可替换
- DIP：依赖 Protocol 接口（ScopeCache），不依赖具体 K8s client 实现
- ISP：Protocol 接口最小化（get / add）
- CRP：构造参数注入（scope_cache）
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.scope_resolver.chain import traverse_scope_chain
from superteam_a2a.knowledge_memory.scope_resolver.resolver import (
    InMemoryScopeCache,
    ScopeCache,
    ScopeResolver,
)

__all__ = [
    "InMemoryScopeCache",
    "ScopeCache",
    "ScopeResolver",
    "traverse_scope_chain",
]
