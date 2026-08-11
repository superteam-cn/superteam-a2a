"""superteam-a2a tests/deploy 骨架（L4 Phase 4 PR-1）。

DEPLOY 测试层：镜像 Dockerfile + helm template 渲染（实际部署推迟到 PR-2）。

pytest 配置在根 pyproject.toml [tool.pytest.ini_options] · 本目录通过显式路径调用
（python -m uv run pytest tests/deploy/test_hello_helm_template.py）。
"""
