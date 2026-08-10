# Branch Protection Ruleset 修正指南（项目发起人 web 端 admin）

> **状态**：2026-08-10 #98 · ⚠️ **需项目发起人 web 端 admin 操作** · gh CLI 仅能读取 Ruleset 内容，无法直接修改 required_status_checks（GitHub API 限制）。

---

## §1 当前 Ruleset 状态

| 字段 | 值 |
|---|---|
| Ruleset name | `main-protection` |
| Ruleset ID | `20232954` |
| Target | `refs/heads/main` |
| Enforcement | `active`（生效中）|
| Source type | `Repository` |
| Created | 2026-08-02T19:37:29+08:00 |
| Last updated | 2026-08-03T21:40:19+08:00 |

---

## §2 ⚠️ ⑭ 关键问题 · required_status_checks 名称 mismatch

Ruleset 当前 `required_status_checks.contexts` 字段：

```json
[
  {"context": "ci"},
  {"context": "lint ci"},
  {"context": "test"},
  {"context": "test ci"}
]
```

但 `.github/workflows/ci.yml`（PR #31 #32 #33 修复后）实际生成的 check name 是：

```
Lint / Type-check / Test (Python 3.12)
```

**结论**：4 个 required check name 在 ci.yml 中**找不到对应 step** · 当前 PR merge 实际未触发 CI failure 自动阻断（即使 CI 失败也不会阻挡 merge）。

**PR-1/PR-2/PR-3/PR-4 全部能合并**（无自动阻断）+ 项目发起人手动合并 · 不是 Branch Protection 真正生效。

---

## §3 项目发起人 web 端 admin 操作步骤

### 步骤 1 · 打开 Ruleset 设置

访问：https://github.com/superteam-cn/superteam-a2a/rules/20232954

或：

仓库 → `Settings` → `Rules` → `Rulesets` → 点 `main-protection`

### 步骤 2 · 修改 required status checks

1. 找到 `Require status checks to pass before merging` 区块
2. 在 `Required checks` 列表中**删除**以下 4 项：
   - `ci`
   - `lint ci`
   - `test`
   - `test ci`
3. **新增** 1 项：
   - `Lint / Type-check / Test (Python 3.12)`（**精确匹配 ci.yml 实际 check name**）

### 步骤 3 · 推荐额外配置

- [ ] ✅ `Require branches to be up to date before merging`
- [ ] ✅ `Require conversation resolution before merging`
- [ ] ✅ `Require linear history`（强制 rebase 或 squash）
- [ ] ✅ `Require deployments to succeed before merging`（如有 deployment 环境）
- [ ] ✅ `Do not allow bypassing the above settings`（防止 admin 绕过）

### 步骤 4 · 验证

打开一个测试 PR · 检查 PR 页面底部"Checks"区域显示：

```
✅ Lint / Type-check / Test (Python 3.12) — Required
```

---

## §4 当前 PR merge 状态（2026-08-10）

| PR | 标题 | CI 实际状态 | merge 状态 |
|---|---|---|---|
| #30 | PR-1 A2A HTTP JSON-RPC server | ✅ SUCCESS（5 + 1 SKIPPED） | ✅ merged |
| #34 | PR-2 K8sBackend 完整实装 | ✅ SUCCESS | ✅ merged |
| #35 | PR-3 25 指标 ServiceMonitor | ✅ SUCCESS | ✅ merged |
| #36 | PR-4 H-RM/H-QM-E2E 实装 | ✅ SUCCESS | ✅ merged |
| #37 | PR-5 文档同步 | ✅ SUCCESS | ✅ merged |

**5 SUCCESS 实际未触发阻断**（check name 不匹配 Ruleset required_status_checks）· 项目发起人手动合并所有 PR。

---

## §5 修正时间窗口

- **不紧急**：当前 PR merge 都成功 · 0 CI failure
- **建议时机**：#98-99 Phase 4 PR 启动前（避免新 PR CI 失败被阻断）
- **阻塞** ：本次会话 #98-99 实装将**首次在严格 BP 下**提交 · 建议立即修正

---

## §6 gh CLI 操作（仅供参考 · 当前 API 限制）

GitHub REST API **不允许**直接修改 Ruleset 的 required_status_checks context 列表（只能完整替换 rules 数组）。如需 CLI 操作：

```bash
# 1. 导出当前 Ruleset（含全部规则）
gh api repos/superteam-cn/superteam-a2a/rulesets/20232954 > /tmp/ruleset-current.json

# 2. 修改 required_status_checks.contexts 字段
# （需手动编辑 JSON：把 4 个 ci/lint ci/test/test ci 替换为 1 个 "Lint / Type-check / Test (Python 3.12)"）

# 3. PUT 整个 Ruleset
gh api -X PUT repos/superteam-cn/superteam-a2a/rulesets/20232954 \
  --input /tmp/ruleset-fixed.json
```

但实际**GitHub REST API 不允许通过 PUT 替换 status checks contexts**（只读）· **唯一可行路径是 web 端 admin UI**。

---

## §7 历史跟踪

- #92 关注项 ⑭ 首次发现：2026-08-06 · Branch Protection check 名称 mismatch
- #93 验证：仓库 public 化后 Code Security 解决 · 但 ⑭ 未解决
- #97 PR #36 PR #37 合并验证：CI 5 SUCCESS 实际未阻断（check mismatch）· 项目发起人手动合并
- #98 本文档创建：明确项目发起人 web 端 admin 操作步骤

---

> **建议**：项目发起人立即访问 https://github.com/superteam-cn/superteam-a2a/rules/20232954 修改 required status checks · 避免未来 Phase 4 大量 PR 在严格 BP 下被错误阻断。