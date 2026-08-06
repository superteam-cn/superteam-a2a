"""AdmissionValidatorImpl unit tests · ADMISSION-UT-001/002/003。

Phase 1 MVP 最小集验证：
- ADMISSION-UT-001：validate 正常路径（content + decay_days 校验通过）
- ADMISSION-UT-002：content keys > 20 → MEMORY_INVALID_CONTENT
- ADMISSION-UT-003：decay_days > 3650 → MEMORY_DECAY_DAYS_EXCEEDED
- 额外：异常原样透传契约（不重映射）
"""

from __future__ import annotations

import sys
from pathlib import Path

# 路径前置
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

import pytest  # noqa: E402
from superteam_a2a.knowledge_memory import (  # noqa: E402
    Memory,
    MemoryContractError,
    MemoryErrorCode,
    ObjectMeta,
)
from superteam_a2a.knowledge_memory.handlers.admission_validator import (  # noqa: E402
    AdmissionValidatorImpl,
)
from superteam_a2a.operator.models.memory import (  # noqa: E402
    AgentReference,
    MemorySpec,
    ScopeReference,
)


def _make_memory(
    *,
    name: str = "mem-1",
    namespace: str = "default",
    content: dict[str, str] | None = None,
    decay_days: int = 30,
) -> Memory:
    """构造测试用 Memory。

    Phase 1 admission 校验测试需要构造 schema 边界值（如 content>20, decay_days>3650）。
    MemorySpec 默认 max_length=20 / le=3650，因此用 model_construct 绕过 schema 校验，
    直接构造 Memory 实例。Runtime validator 才是测试目标。
    """
    if content is None:
        content = {"k": "v"}
    spec = MemorySpec.model_construct(
        scope_ref=ScopeReference(name="industry-ai"),
        agent_ref=AgentReference(name="hello-agent-sa"),
        content=content,
        summary="test",
        decay_days=decay_days,
    )
    return Memory.model_construct(
        metadata=ObjectMeta(name=name, namespace=namespace),
        spec=spec,
        api_version="memory.superteam-a2a.io/v1alpha1",
        kind="Memory",
    )


async def test_admission_ut_001_validate_normal_path():
    """ADMISSION-UT-001 · validate 正常路径 · content + decay_days 校验通过。

    默认 content keys=1 + decay_days=30 → 不抛错。
    """
    validator = AdmissionValidatorImpl()
    memory = _make_memory()
    # validate 正常路径无返回
    await validator.validate(memory, timeout=0.050)


async def test_admission_ut_002_content_exceeds_20_keys():
    """ADMISSION-UT-002 · content keys > 20 → MEMORY_INVALID_CONTENT。

    验证错误码精确匹配 L2-4 §9.1 权威名 · 不漂移。
    """
    validator = AdmissionValidatorImpl()
    content = {f"key-{i}": f"value-{i}" for i in range(21)}
    memory = _make_memory(content=content)
    with pytest.raises(MemoryContractError) as exc_info:
        await validator.validate(memory, timeout=0.050)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_INVALID_CONTENT
    assert "content keys > 20" in str(exc_info.value)


async def test_admission_ut_003_decay_days_exceeds_3650():
    """ADMISSION-UT-003 · decay_days > 3650 → MEMORY_DECAY_DAYS_EXCEEDED。"""
    validator = AdmissionValidatorImpl()
    memory = _make_memory(decay_days=3651)
    with pytest.raises(MemoryContractError) as exc_info:
        await validator.validate(memory, timeout=0.050)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_DECAY_DAYS_EXCEEDED
    assert "decay_days > 3650" in str(exc_info.value)


async def test_admission_existing_memory_backend_error_passes_through():
    """契约 · MemoryBackendError / MemoryContractError 原样透传（不重映射）。

    §6.4 step 5 不变量：caller 异常禁止内部 catch 重映射。
    """
    validator = AdmissionValidatorImpl()
    memory = _make_memory(content={f"k{i}": "v" for i in range(25)})
    # 抛出 MemoryContractError（is-a MemoryBackendError）
    with pytest.raises(MemoryContractError) as exc_info:
        await validator.validate(memory, timeout=0.050)
    # code 必须是权威枚举成员 · 不被重映射
    assert isinstance(exc_info.value.code, MemoryErrorCode)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_INVALID_CONTENT


async def test_admission_content_exactly_20_keys_passes():
    """边界 · content keys = 20（边界值 · 不抛错）。

    § 校验严格 > 20 → = 20 通过。
    """
    validator = AdmissionValidatorImpl()
    content = {f"key-{i}": f"value-{i}" for i in range(20)}
    memory = _make_memory(content=content)
    await validator.validate(memory, timeout=0.050)


async def test_admission_decay_days_exactly_3650_passes():
    """边界 · decay_days = 3650（边界值 · 不抛错）。"""
    validator = AdmissionValidatorImpl()
    memory = _make_memory(decay_days=3650)
    await validator.validate(memory, timeout=0.050)


async def test_admission_conforms_to_protocol():
    """AdmissionValidatorImpl 与 reconciler AdmissionValidatorProtocol 协议一致。

    runtime_checkable Protocol 用法 + validate 签名 (memory, *, timeout) 一致。
    """
    from superteam_a2a.knowledge_memory.reconciler.memory_reconciler import (
        AdmissionValidatorProtocol,
    )

    validator = AdmissionValidatorImpl()
    # runtime_checkable Protocol 允许 isinstance 检查
    assert isinstance(validator, AdmissionValidatorProtocol)
