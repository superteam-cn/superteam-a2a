"""main.py _build_memo() 装配验证 · L4-Phase1-Step5 收口。

验证 _build_memo() 返回 6 个 memo key · 类型符合期望。

注意：main.py 顶层装饰器 @kopf.on.* / @kopf.timer 在 collection 时会触发
kopf 注册要求（names 不全 → TypeError）。本测试用 mock kopf 模块避免
实际注册，仅调用 _build_memo() 装配验证。

PR-4a 修复：污染隔离移至 tests/unit/knowledge_memory/conftest.py 的
autouse fixture，避免污染其他测试（test_admission_5step.py + test_admission_webhook.py）。
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# ============================================================================
# Mock kopf BEFORE importing main · 装饰器注册时返回原函数
# ============================================================================

_KOPF_MOCK = MagicMock()


def _identity_decorator(*_args, **_kwargs):
    """返回 identity decorator: 返回原函数不做修改。"""

    def _wrap(fn):
        return fn

    return _wrap


for _name in ("on.create", "on.update", "on.delete", "timer", "on.resume", "on.startup"):
    setattr(_KOPF_MOCK, _name, _identity_decorator)
_KOPF_MOCK.run = MagicMock()
sys.modules["kopf"] = _KOPF_MOCK

# 路径前置（与 api/conftest.py 保持一致）
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

from superteam_a2a.knowledge_memory import (  # noqa: E402
    AdmissionValidatorImpl,
    BM25Index,
    InMemoryBackend,
    K8sBackend,
    MemoryBackendInProcessServiceImpl,
    MemoryReconcilerService,
    SystemClock,
)
from superteam_a2a.knowledge_memory.backend.clock import Clock  # noqa: E402
from superteam_a2a.knowledge_memory.backend.protocol import MemoryBackend  # noqa: E402
from superteam_a2a.knowledge_memory.main import _build_backend, _build_memo  # noqa: E402

EXPECTED_KEYS = frozenset(
    {
        "clock",
        "memory_backend",
        "memory_admission_validator",
        "memory_index",
        "memory_in_process_service",
        "memory_reconciler",
    }
)


def test_build_memo_returns_expected_keys() -> None:
    """_build_memo() 返回 6 memo key · 无多无少。"""
    memo = _build_memo()
    assert set(memo.keys()) == EXPECTED_KEYS


def test_build_memo_clock_is_system_clock() -> None:
    """clock key 是 SystemClock 实例（满足 Clock Protocol）。"""
    memo = _build_memo()
    assert isinstance(memo["clock"], SystemClock)
    assert isinstance(memo["clock"], Clock)


def test_build_memo_backend_is_in_memory_backend() -> None:
    """memory_backend 是 InMemoryBackend 实例（满足 MemoryBackend Protocol）。"""
    memo = _build_memo()
    assert isinstance(memo["memory_backend"], InMemoryBackend)
    assert isinstance(memo["memory_backend"], MemoryBackend)


def test_build_memo_admission_validator_is_admission_validator_impl() -> None:
    """memory_admission_validator 是 AdmissionValidatorImpl 实例。"""
    memo = _build_memo()
    assert isinstance(memo["memory_admission_validator"], AdmissionValidatorImpl)


def test_build_memo_index_is_bm25_index() -> None:
    """memory_index 是 BM25Index 实例。"""
    memo = _build_memo()
    assert isinstance(memo["memory_index"], BM25Index)


def test_build_memo_in_process_service_wires_admission() -> None:
    """memory_in_process_service 装配 admission（非 None）+ backend。"""
    memo = _build_memo()
    service = memo["memory_in_process_service"]
    assert isinstance(service, MemoryBackendInProcessServiceImpl)
    assert service._backend is memo["memory_backend"]
    assert service._admission is memo["memory_admission_validator"]


def test_build_memo_reconciler_wires_all_five_dependencies() -> None:
    """memory_reconciler 装配 backend + leader + clock + admission + index。"""
    memo = _build_memo()
    reconciler = memo["memory_reconciler"]
    assert isinstance(reconciler, MemoryReconcilerService)
    assert reconciler.backend is memo["memory_backend"]
    assert reconciler.clock is memo["clock"]
    assert reconciler.admission is memo["memory_admission_validator"]
    assert reconciler.index is memo["memory_index"]


def test_build_memo_clock_is_single_instance() -> None:
    """§M-1.5 Clock 单实例：reconciler.clock 与 memo["clock"] 同对象。"""
    memo = _build_memo()
    assert memo["memory_reconciler"].clock is memo["clock"]


def test_build_memo_is_idempotent() -> None:
    """_build_memo() 多次调用产生独立 memo dict（不共享可变状态）。"""
    memo_a = _build_memo()
    memo_b = _build_memo()
    assert memo_a.keys() == memo_b.keys()
    assert memo_a["memory_backend"] is not memo_b["memory_backend"]
    assert memo_a["memory_reconciler"] is not memo_b["memory_reconciler"]


# ============================================================================
# L4-Phase3 PR-2: backend selection tests (helm values.yaml backend.type)
# ============================================================================


def test_build_backend_in_process_returns_in_memory_backend() -> None:
    """backend_type='in_process' -> InMemoryBackend instance."""
    backend = _build_backend(backend_type="in_process")
    assert isinstance(backend, InMemoryBackend)
    assert isinstance(backend, MemoryBackend)


def test_build_backend_k8s_returns_k8s_backend() -> None:
    """backend_type='k8s' -> K8sBackend instance (production backend)."""
    backend = _build_backend(backend_type="k8s")
    assert isinstance(backend, K8sBackend)
    assert isinstance(backend, MemoryBackend)


def test_build_backend_unknown_type_falls_back_to_in_memory() -> None:
    """Unknown backend_type -> falls back to InMemoryBackend (defense-in-depth)."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # main.py emits a UserWarning for unknown type
        backend = _build_backend(backend_type="unknown")
    assert isinstance(backend, InMemoryBackend)
