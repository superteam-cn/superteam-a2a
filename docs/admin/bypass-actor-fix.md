# Branch Protection Bypass Actors 配置指南（项目发起人 web 端 admin）

> **状态**：2026-08-11 #100 · ⚠️ **需项目发起人 web 端 admin 操作** · gh CLI 仅能读取 Ruleset，无法修改 bypass_actors（GitHub API 限制 · 与 `branch-protection-fix.md` ⑭ 同一限制）。
>
> **2026-08-11 修正**：原 Issue #43 描述误称 bypass_actors 在 "Require a pull request before merging" 区块下 · **实际位置是 Ruleset 顶层字段**（在 Rules 列表下方 · "Bypass modifiers" 区块）。

---

## §1 当前 Ruleset 状态（gh CLI 验证 · 2026-08-11）

```json
{
  "id": 20232954,
  "name": "main-protection",
  "enforcement": "active",
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "pull_request", ... },
    { "type": "required_status_checks", ... },
    { "type": "required_linear_history" },
    { "type": "required_deployments", ... }
  ],
  "bypass_actors": [
    {
      "actor_id": 5,
      "actor_type": "RepositoryRole",
      "bypass_mode": "always"
    }
  ],
  "current_user_can_bypass": "always"
}
```

**当前 bypass_actors**：

| actor_id | actor_type | bypass_mode | 说明 |
|---|---|---|---|
| 5 | RepositoryRole | always | admin 角色 · 含项目发起人本人 |

**关键事实**：

- ✅ 项目发起人本人（CoderZhangfujiang）作为 admin **已经是 bypass actor**（`current_user_can_bypass: "always"`）
- ✅ 这就是 #100 项目发起人 `gh pr review --approve` 成功的原因（bypass approval check）
- ❌ `dependabot[bot]` **不是** admin · 仍需添加为 bypass actor

---

## §2 为什么需要添加 dependabot[bot]

**背景**：`.github/workflows/dependabot-auto-merge.yml` 原第 28-33 行 `gh pr review --approve` 必然失败：

> `GitHub Actions is not permitted to approve pull requests.`

GitHub API 硬性限制：Actions bot 永远不能 approve PR（防止 self-approval bypass Branch Protection）。

**解决方案**：让 `dependabot[bot]` 成为 bypass actor → Dependabot PR 自动跳过 approval 检查 → workflow 仅触发 `gh pr merge --auto --squash` → **0 人工干预**。

**配套修改**（已完成 · commit `052681d`）：删除 workflow approve step。

---

## §3 项目发起人 web 端 admin 操作步骤

### 步骤 1 · 打开 Ruleset 设置

访问：https://github.com/superteam-cn/superteam-a2a/rules/20232954

或：

仓库 → `Settings` → `Rules` → `Rulesets` → 点 `main-protection`

### 步骤 2 · 滚动到 Ruleset 编辑页面底部

**关键**：bypass_actors **不在** Rules 列表内 · **不在** "Require a pull request before merging" 区块下 · **在页面更下方**的独立区块。

页面结构（从上到下）：

```
1. Enforcement status（Active / Disabled）
2. Target branches（main）
3. Rules（6 个 rule 区块）
   - Restrict deletions
   - Require linear history
   - Require deployments to succeed
   - Require a pull request before merging  ← ❌ 不在这里
   - Require status checks to pass
   - Block force pushes
4. **Bypass modifiers**  ← ✅ 在这里
```

### 步骤 3 · 添加 bypass actor

1. 在 "Bypass modifiers" 区块点击 **"Add bypass"** 或 **"+ Add actor"**
2. 搜索框输入 `dependabot` 或 `dependabot[bot]`
3. 选择 **"dependabot[bot]"**（GitHub 自动识别）
4. **Bypass mode** 选择 **`Always`**（Dependabot PR 始终 bypass）
5. （可选）选择 `Pull requests only`（仅 PR bypass，不影响其他）
6. 点击 **Save**

### 步骤 4 · 验证

```bash
gh api repos/superteam-cn/superteam-a2a/rulesets/20232954 \
  --jq '.bypass_actors'
```

**预期返回**：

```json
[
  {"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"},
  {"actor_id": 49699353, "actor_type": "Bot", "bypass_mode": "always", "actor_display_name": "dependabot[bot]"}
]
```

### 步骤 5 · 测试 Dependabot PR 自动 merge

等待 Dependabot 下次创建 PR（~1-2 周内）：

- Bypass actor 生效后，Dependabot PR 应自动 squash merge
- 无需项目发起人手动 approve
- 验证命令：`gh pr list --label dependencies --state all --limit 5`

---

## §4 配套修改（已完成）

### 4.1 `.github/workflows/dependabot-auto-merge.yml`

commit `052681d` · 1 file / 7 deletions(-)

**删除**：第 28-33 行 "Approve patch / minor updates" step

```yaml
- name: Approve patch / minor updates
  if: steps.metadata.outputs.update-type == 'version-update:semver-patch' || ...
  run: gh pr review --approve "$PR_URL"
  ...
```

**保留**：第 28-33 行 "Enable auto-merge (squash) for patch / minor" step（修改后行号）

### 4.2 为什么删除是安全的

- Dependabot PR：bypass actor → approval 不需要 → workflow 只需触发 auto-merge
- 人类 PR：workflow `if: github.event.pull_request.user.login == 'dependabot[bot]'` 条件不满足 → 整个 job 跳过 → **不受影响**
- patch / minor 之外的版本：保留 "Comment on major update" step（仅 GITHUB_STEP_SUMMARY，不影响 PR）

---

## §5 紧急回滚（如果 B 方案有问题）

### 5.1 移除 dependabot[bot] bypass actor

1. 访问 https://github.com/superteam-cn/superteam-a2a/rules/20232954
2. 滚动到 "Bypass modifiers" 区块
3. 找到 `dependabot[bot]` actor
4. 点击 **Remove** 或 trash icon
5. 保存

### 5.2 恢复 workflow approve step（git revert）

```bash
git revert 052681d
git push origin main
```

恢复后 Dependabot PR workflow 仍会失败（Actions bot 限制），需要项目发起人手动 `gh pr review --approve`。

---

## §6 为什么 gh CLI 不能直接改

GitHub REST API **不允许 PUT 替换 Ruleset 的 bypass_actors 列表**（只读 · 与 required_status_checks 同一限制）· 唯一修改路径是 web 端 admin UI。

```bash
# ❌ 这些命令都会失败
gh api -X PUT repos/superteam-cn/superteam-a2a/rulesets/20232954 \
  --input ruleset-with-dependabot.json
# → 422 Unprocessable Entity / bypass_actors 是只读

gh pr review --approve "$PR_URL"
# → GitHub Actions is not permitted to approve pull requests
```

---

## §7 历史跟踪

- **#100**（2026-08-11）：3 Dependabot PR（#39 #40 #41）workflow 失败 → 项目发起人手动 `gh pr review --approve` 解决（bypass actor RepositoryRole 5 = admin 自身）· 3 PR squash merged · commit `052681d` 删除 workflow approve step
- **#99**（2026-08-11）：⑭ BP required_status_checks 修复（admin UI · Issue #42 closed）· 与 B 方案同一窗口
- **#98**（2026-08-10）：Phase 4 PR-1 Hello Agent Step 1 完整收口（PR #38 merged）

---

> **建议**：项目发起人立即访问 https://github.com/superteam-cn/superteam-a2a/rules/20232954 滚动到 "Bypass modifiers" 区块添加 `dependabot[bot]` · 配合 commit `052681d` workflow 修改 · 未来 Dependabot PR 完全自动化 0 人工干预。
