"""Hello Agent · Dockerfile lint + build 静态验证 · HELLO-DOCKER-001（10 UT）。

依据 Phase 4 PR-2 plan §2.1 + §4 + §7 测试策略：
- 不依赖 docker daemon（仅静态分析 Dockerfile 内容）
- 10 项断言覆盖 PR-2 §4 验收清单 #1 的全部规格
- pytest function-based · 无 setup/teardown · 直接断言

5 项关键不变量验证（PR-2 §6）：
1. Card-driven 单实例（Dockerfile 不涉及 · Helm schema enum 强约束）
2. Python-first 边界（base image = python:3.12-slim）
3. observability 4 指标（uvicorn 启动时自动加载 observability.py）
4. wire contract（Hello Agent 不涉及 MEMORY_*）
5. 单进程 8080 端口（EXPOSE 8080 + uvicorn --port 8080 + --factory）
"""

from __future__ import annotations

import re
from pathlib import Path

# ============================================================================
# 路径常量（workspace 根定位 · 不依赖 docker daemon）
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DOCKERFILE = _REPO_ROOT / "services" / "hello-agent" / "Dockerfile"
_DOCKERIGNORE = _REPO_ROOT / "services" / "hello-agent" / ".dockerignore"


# ============================================================================
# Helpers
# ============================================================================


def _read_dockerfile() -> str:
    """读取 Dockerfile 内容（存在性已由前置断言保证）。"""
    return _DOCKERFILE.read_text(encoding="utf-8")


def _read_dockerignore() -> str:
    """读取 .dockerignore 内容（存在性已由前置断言保证）。"""
    return _DOCKERIGNORE.read_text(encoding="utf-8")


# ============================================================================
# HELLO-DOCKER-001 · Dockerfile 静态验证（10 项断言）
# ============================================================================


def test_hello_docker_001_dockerfile_exists() -> None:
    """HELLO-DOCKER-001 :: 文件存在性。

    验证：services/hello-agent/Dockerfile 文件存在。
    """
    assert _DOCKERFILE.is_file(), f"Dockerfile not found: {_DOCKERFILE}"
    assert _DOCKERFILE.stat().st_size > 0, "Dockerfile is empty"


def test_hello_docker_001_multistage() -> None:
    """HELLO-DOCKER-001 :: multi-stage 验证。

    验证：Dockerfile 包含 ≥ 2 个 FROM 指令（builder + runtime）。
    PR-2 §2.1 要求 multi-stage pattern（隔离编译工具 + 镜像体积最小化）。
    """
    content = _read_dockerfile()
    from_count = len(re.findall(r"^FROM\s+", content, re.MULTILINE))
    assert from_count >= 2, (
        f"Expected multi-stage Dockerfile (≥ 2 FROM), got {from_count} FROM statements"
    )


def test_hello_docker_001_python_base() -> None:
    """HELLO-DOCKER-001 :: base image 验证。

    验证：至少 1 个 stage 使用 python:3.12-slim 作为 base image。
    关键不变量 #2 Python-first 边界（0 系统级依赖）。
    """
    content = _read_dockerfile()
    assert "python:3.12-slim" in content, (
        "Expected base image 'python:3.12-slim' (Python-first 关键不变量 #2)"
    )


def test_hello_docker_001_uv_install() -> None:
    """HELLO-DOCKER-001 :: uv 安装验证。

    验证：Dockerfile 包含 uv 安装步骤（COPY from ghcr.io/astral-sh/uv 或 pip install uv）。
    PR-2 §2.1 要求 uv 作为 Python 包管理器。
    """
    content = _read_dockerfile()
    # 两种合法形式：Astral official image COPY 或 pip install uv
    has_uv_copy = bool(re.search(r"ghcr\.io/astral-sh/uv", content))
    has_pip_uv = bool(re.search(r"pip\s+install\s+uv", content))
    assert has_uv_copy or has_pip_uv, (
        "Expected uv installation (ghcr.io/astral-sh/uv COPY or 'pip install uv')"
    )


def test_hello_docker_001_non_root_user() -> None:
    """HELLO-DOCKER-001 :: non-root user 验证。

    验证：Dockerfile 包含 USER 指令（非 root · UID 1000 或 hello user）。
    关键不变量 #5 单进程 8080 端口 + Pod Security Standards restricted profile。
    """
    content = _read_dockerfile()
    # 必须包含 USER 指令
    assert re.search(r"^USER\s+", content, re.MULTILINE), (
        "Expected USER directive (non-root · restricted SecurityContext)"
    )
    # USER 指令应指向 non-root（UID 1000 或 hello user）
    user_match = re.search(r"^USER\s+(\S+)", content, re.MULTILINE)
    assert user_match is not None
    user_target = user_match.group(1)
    # 接受格式：1000:1000 / hello:hello / 1000 / hello
    is_non_root = (
        "1000" in user_target
        or "hello" in user_target
        or user_target.startswith("nonroot")
    )
    assert is_non_root, f"USER target '{user_target}' should be non-root (UID 1000 or hello user)"


def test_hello_docker_001_expose_8080() -> None:
    """HELLO-DOCKER-001 :: EXPOSE 8080 验证。

    验证：Dockerfile 包含 EXPOSE 8080 指令。
    关键不变量 #5 单进程 8080 端口。
    """
    content = _read_dockerfile()
    assert re.search(r"^EXPOSE\s+8080\s*$", content, re.MULTILINE), (
        "Expected 'EXPOSE 8080' directive (单进程 8080 端口 关键不变量 #5)"
    )


def test_hello_docker_001_healthcheck() -> None:
    """HELLO-DOCKER-001 :: HEALTHCHECK 验证。

    验证：Dockerfile 包含 HEALTHCHECK 指令 + 引用 /healthz 路由。
    PR-2 §2.4 双探针 + observability.py healthz 实现（L3-4 §6 契约）。
    """
    content = _read_dockerfile()
    assert re.search(r"^HEALTHCHECK\s+", content, re.MULTILINE), (
        "Expected HEALTHCHECK directive (L3-4 §6 契约 + observability.py healthz)"
    )
    assert "/healthz" in content, (
        "HEALTHCHECK must reference /healthz endpoint (observability.py healthz 实现)"
    )


def test_hello_docker_001_uv_sync_workspace() -> None:
    """HELLO-DOCKER-001 :: uv sync workspace 跨包依赖验证。

    验证：`uv sync` 命令包含 --all-packages / --frozen / --all-extras 之一。
    PR-2 §5 风险 #7 缓解：workspace 跨包依赖（superteam-a2a-a2a-core）必须显式声明。
    """
    content = _read_dockerfile()
    # 匹配实际 RUN 的 `uv sync` 命令（跳过注释行 · `^[ \t]*RUN[ \t]+uv[ \t]+sync`）
    uv_sync_match = re.search(r"^\s*RUN\s+uv\s+sync([^\n]*)$", content, re.MULTILINE)
    assert uv_sync_match is not None, (
        "Expected 'RUN uv sync ...' command in Dockerfile builder stage"
    )
    uv_sync_args = uv_sync_match.group(1)
    # 必须包含 --all-packages（workspace 跨包依赖）
    assert "--all-packages" in uv_sync_args, (
        f"uv sync must include --all-packages for workspace cross-package deps "
        f"(PR-2 §5 风险 #7). Got: uv sync{uv_sync_args}"
    )
    # 建议包含 --frozen（严格使用 uv.lock）
    assert "--frozen" in uv_sync_args, (
        f"uv sync should include --frozen (宪法 §13.6 依赖锁定). Got: uv sync{uv_sync_args}"
    )


def test_hello_docker_001_uvicorn_entrypoint() -> None:
    """HELLO-DOCKER-001 :: uvicorn ENTRYPOINT 验证。

    验证：ENTRYPOINT 包含 uvicorn + create_app + --port 8080 + --factory（避免 shell 形式）。
    关键不变量 #5 单进程 8080 端口 + agent.py create_app factory function。
    """
    content = _read_dockerfile()
    # 1. ENTRYPOINT 必须存在
    entrypoint_match = re.search(r"^ENTRYPOINT\s+(.+)$", content, re.MULTILINE)
    assert entrypoint_match is not None, "Expected ENTRYPOINT directive"
    entrypoint = entrypoint_match.group(1)
    # 2. ENTRYPOINT 必须是 exec form（JSON array），避免 shell 形式（signal propagation 问题）
    assert entrypoint.startswith("["), (
        f"ENTRYPOINT must be exec form (JSON array), got: {entrypoint}"
    )
    # 3. 必须包含 uvicorn + create_app + --port 8080 + --factory
    assert "uvicorn" in entrypoint, "ENTRYPOINT must invoke uvicorn"
    assert "create_app" in entrypoint, (
        "ENTRYPOINT must reference create_app factory (agent.py line 81)"
    )
    assert "--port" in entrypoint, (
        "ENTRYPOINT must include --port flag (单进程 8080 端口 关键不变量 #5)"
    )
    assert "8080" in entrypoint, (
        "ENTRYPOINT must include port 8080 (单进程 8080 端口 关键不变量 #5)"
    )
    assert "--factory" in entrypoint, (
        "ENTRYPOINT must include --factory flag (create_app is factory function)"
    )


def test_hello_docker_001_dockerignore_exists() -> None:
    """HELLO-DOCKER-001 :: .dockerignore 验证。

    验证：.dockerignore 文件存在 + 排除 .venv / __pycache__ / .git / tests / *.pyc。
    减少 build context 大小 + 避免敏感文件泄漏到镜像。
    """
    assert _DOCKERIGNORE.is_file(), f".dockerignore not found: {_DOCKERIGNORE}"
    assert _DOCKERIGNORE.stat().st_size > 0, ".dockerignore is empty"

    content = _read_dockerignore()

    # 必须排除的条目（按 PR-2 §4 验收清单 #1 规格）
    # 注意：*.pyc 可用 glob `*.pyc` 或字符类 `*.py[cod]` 覆盖
    required_excludes = {
        ".venv": [
            r"(^|\s)\.venv($|/|\s)",
            "Virtual env (避免 ~100MB .venv 复制到 build context)",
        ],
        "__pycache__": [
            r"(^|\s)__pycache__($|/|\s)",
            "Python bytecode cache (避免 .pyc 污染镜像)",
        ],
        ".git": [
            r"(^|\s)\.git($|/|\s)",
            "Git metadata (避免 .git 泄漏到镜像)",
        ],
        "tests": [
            r"(^|\s)tests($|/|\s)",
            "Tests directory (避免测试代码污染 runtime 镜像)",
        ],
        ".pyc": [
            # 接受 `*.pyc` 直接模式 或 `*.py[cod]` 字符类（涵盖 .pyc/.pyo/.pyd）
            r"(^|\s)\*\.pyc($|/|\s)",
            r"(^|\s)\*\.py\[cod\]($|/|\s)",
            "Python compiled files (*.pyc / *.pyo / *.pyd)",
        ],
    }
    for pattern, spec in required_excludes.items():
        # spec 是 [regex, reason] 或 [regex1, regex2, reason]
        patterns = spec[:-1]
        reason = spec[-1]
        matched = any(
            re.search(p, content, re.MULTILINE) is not None for p in patterns
        )
        assert matched, (
            f".dockerignore must exclude '{pattern}' ({reason}). "
            f"Accepted patterns: {patterns}"
        )
