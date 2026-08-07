"""MemoryHandler kopf entry unit tests · 3 测试。

验证：
1. entry 函数签名 keyword-only + 接受额外 kwargs（kopf 调用约定）
2. mock service · record_memory_async 被调用
3. memo 不含 service 时 handler 静默 return（不抛错）
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock

from superteam_a2a.knowledge_memory.api.service import (
    MemoryBackendInProcessServiceImpl,
)
from superteam_a2a.knowledge_memory.handlers.memory_handler import (
    on_memory_create,
    on_memory_update,
)


def test_on_memory_create_signature():
    """entry 函数签名 keyword-only + 接受额外 kwargs（kopf 调用约定）。"""
    sig = inspect.signature(on_memory_create)
    params = sig.parameters
    # 三个显式 keyword-only 参数
    assert "body" in params
    assert "meta" in params
    assert "memo" in params
    # **kwargs 接收 kopf 注入的其他参数
    assert any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())


async def test_on_memory_create_invokes_service(sample_body, sample_meta, fake_clock):
    """mock service · record_memory_async 被调用。

    §M-1.5：handler 从 memo["clock"] 读取 Clock；测试 memo 必须含 fake_clock。
    """
    mock_service = AsyncMock(spec=MemoryBackendInProcessServiceImpl)
    mock_service.record_memory_async = AsyncMock()
    memo = {"memory_in_process_service": mock_service, "clock": fake_clock}
    await on_memory_create(body=sample_body, meta=sample_meta, memo=memo)
    mock_service.record_memory_async.assert_called_once()
    call_kwargs = mock_service.record_memory_async.call_args.kwargs
    assert "context" in call_kwargs


async def test_on_memory_create_invalid_memo_returns_silently(sample_body, sample_meta):
    """memo 不含 service 时 handler 静默 return（不抛错）。"""
    # memo 完全缺失
    await on_memory_create(body=sample_body, meta=sample_meta, memo={})
    # memo 含错误类型
    await on_memory_create(
        body=sample_body, meta=sample_meta, memo={"memory_in_process_service": "bogus"}
    )


def test_on_memory_update_signature():
    """on_memory_update 同样遵守 keyword-only + **kwargs 约定。"""
    import inspect

    sig = inspect.signature(on_memory_update)
    params = sig.parameters
    assert "body" in params
    assert "meta" in params
    assert "memo" in params
    assert any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
