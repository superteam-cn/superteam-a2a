# Pull Request

## Summary

<!-- 一段话讲清楚：什么变了、为什么变、影响范围。 -->

## What's Inside

<!-- 列出本 PR 包含的实质内容（按 L4 步骤 / Spec 段落 / ADR 编号组织）。 -->
-
-

## Architecture Decisions

<!-- 如本 PR 涉及 ADR / 宪法 / Spec 变更，请填表。 -->
| 决策 ID | 类型     | 状态    | 标题 / 链接 |
|---------|----------|---------|-------------|
| ADR-XXXX| new/rev  | draft / v1.0 推荐 / Accepted | [title](docs/adr/XXXX-*.md) |
| §X.Y    | spec 增删 | n/a    | description |
| OPEN-XXX-XXX | close | n/a   | reason      |

## 不变量保持

<!-- 按宪法 v0.5.0 §16.1 + L2-4 v0.2.0 §9.1 错误码权威名 + ADR-0006 架构门禁。 -->
- [ ] wire contract（API/CRD schema 向后兼容或已记录 break）
- [ ] 12 MEMORY_* 错误码与 L2-4 v0.2.0 §9.1 权威名 100% 一致（0 漂移）
- [ ] Knowledge / Memory 单进程架构（ADR-0006 D 方案 Accepted）
- [ ] uv workspace 结构（packages/* + services/* + agents/*）
- [ ] 单原子 commit（不与无关变更混在一起）
- [ ] 未直接落 main（经 feature 分支 + PR 流程）
- [ ] 水位 < 30% / 单文件 < 30KB（§16.1 红线）

## File-level 摘要

<!-- 跑 `git show --stat` 并粘贴，或手填。 -->
```text
 <files> | <ins> + / <del> -
```

## Test Plan

<!-- 必填：列出本 PR 验证步骤。 -->
- [ ] `uv run ruff check .` 0 error
- [ ] `uv run pyright` 0 error
- [ ] `uv run pytest tests/ -v` 全绿
- [ ] `yamllint .` 0 error（Helm/manifests/GitHub workflows）
- [ ] `markdownlint **/*.md` 0 error
- [ ] `uv lock --check` 一致
- [ ] (L4 PR 必填) `kind create cluster` + `helm install` 冒烟
- [ ] (L4 PR 必填) webhook 50ms 端到端时延验证（OPEN-L1-002）

## Open Questions

<!-- 本 PR 仍存疑 / 留作 follow-up 的事项。 -->
- [ ] OPEN-XXX-XXX — description

## Reference

<!-- 关联 issue / spec / ADR / 评审 / 外部文档。 -->
- Closes #<issue>
- Refs: docs/spec/L1-system-spec.md §X / docs/spec/L3-file-specs/L3-<module>.md §Y
- Refs: docs/adr/000X-<name>.md
- Refs: docs/constitution/CONSTITUTION.md §X
- Review: docs/reviews/l3-X-<module>-spec-review.md

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
