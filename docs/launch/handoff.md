# Phase 5 LAUNCH 完整交接文档 · superteam-a2a v0.1.0

> **接收人**: 项目发起人 (@CoderZhangfujiang) 或接续工作的贡献者
>
> **交接日期**: 2026-08-16 (v1) · 2026-09-03 (v1.1 · 视觉资产就绪 §F 同步)
>
> **状态**: Phase 5 LAUNCH 文字 / 规格 / 反馈基础设施 / **4 视觉资产 (PIL 脚本生成占位) 就绪**，真实 demo.mp4 待 maintainer 录制替换占位
>
> **阅读时间**: 10 分钟可决策；30 分钟可启动

---

## 一句话状态

> superteam-a2a v0.1.0 已 ship 到 GitHub Release + 仓库 public + docs site + 11 topics + 5 issue 模板 + **14 launch 渠道文案 + 4 张架构图 + 4 视觉规格 + FAQ + 30 天 engagement playbook + 4 视觉资产（og-image + cover-ph + cover-devto + demo 占位 GIF）全部就绪**。**仅剩 1 项：maintainer 录制真实 demo.mp4（`bash scripts/record_demo.sh`，1-2 小时）替换占位 GIF，然后启动 14 渠道 7 天 rollout**。

---

## 1. 当前状态（2026-09-03）

| 维度 | 数值 |
|---|---|
| **main HEAD** | `9f92701` (#124 visual assets squash merged) |
| **测试** | **474/474 PASS** · 0 回归 |
| **仓库** | <https://github.com/superteam-cn/superteam-a2a> (PUBLIC) |
| **v0.1.0 Release** | <https://github.com/superteam-cn/superteam-a2a/releases/tag/v0.1.0> (✅ published #117) |
| **docs site** | <https://superteam-cn.github.io/superteam-a2a/> (✅ auto-deployed) |
| **GitHub topics** | 11 ✅ |
| **Issue templates** | 5 ✅ |
| **Visual assets** | 4/4 ✅ (og-image + cover-ph + cover-devto + demo.gif 占位) · demo.mp4 ⏳ |
| **CI workflows** | 5 (Lint / Type-check / Test / CodeQL python / CodeQL actions) · 100% green |
| **Branch Protection** | ✅ 严格生效 |
| **Dependabot** | ✅ 自动化（auto-merge 跳过待修） |
| **总 commit 数** | ~89 |
| **总 PR 数** | 63 merged |
| **Phase 5 LAUNCH 进度** | ~97%（仅剩真实 demo.mp4 录制 + 14 渠道实际发布） |

## 2. Phase 5 LAUNCH 已完成清单（#118-#122）

### 5 sessions · 5 commits · 0 代码变更

| # | 主题 | main HEAD | 文件数 |
|---|---|---|---|
| #118 | Adapter SDK Protocol + 4 framework examples + mkdocs docs site (PR #62) | `6c4f9ce` | (PR #62) |
| #119 | publish prep: gh repo edit description + 11 topics + 5 issue 模板 + submission-checklist.md + demo-video-script.md + Discussions 5 categories | `2bc405b` | 7 new |
| #120 | 平台文案补全: 10 launch drafts (PH / Twitter / Discussions / Reddit ×2 / 中文 ×4 / Discord-Slack ×5) + submission-checklist 升级 5 → 14 渠道 | `c499a9c` | 11 |
| #121 | 视觉资产前置: 4 张架构图 (system overview / A2A protocol flow / single-process backend / CRD relationships) + cover image specs | `92b12b7` | 7 |
| #122 | 早期反馈基础设施: FAQ.md + OG image spec + engagement playbook + 5 launch drafts 测试数一致性修正 | `b1f1554` | 9 |

**docs/launch/ 总文件数**: 7 → **20 个 markdown** + 0 image
**docs/architecture/ 总文件数**: 0 → **4 个 Mermaid 架构图**
**docs/admin/mkdocs.yml Visual Diagrams 子 section**: ✅ 已添加

### Phase 5 已就绪资产

✅ **14 launch 渠道文案**（docs/launch/）
- `submission-checklist.md` — 14 渠道 / 7 天 rollout playbook
- `product-hunt-draft.md` — PH tagline + description + maker comment
- `twitter-thread-draft.md` — 7 推文 thread
- `show-hn-draft.md` — Hacker News 主体
- `discussions-show-and-tell-draft.md` — GitHub Discussions 独立帖
- `devto-draft.md` — dev.to article
- `reddit-kubernetes-draft.md` — Reddit r/kubernetes
- `reddit-programming-draft.md` — Reddit r/programming
- `reddit-python-draft.md` — Reddit r/Python
- `juejin-draft.md` — 掘金
- `zhihu-draft.md` — 知乎
- `segmentfault-draft.md` — SegmentFault
- `oschina-draft.md` — OSCHINA
- `infoq-draft.md` — InfoQ
- `community-channels-drafts.md` — Discord/Slack 5 community

✅ **4 张架构图**（docs/architecture/）
- `system-overview.md` — kubectl → Operator → 6 CRDs → K8s API → Agents (Mermaid graph TB)
- `a2a-protocol-flow.md` — A2A JSON-RPC request flow + 50ms admission (Mermaid sequence)
- `single-process-backend.md` — ADR-0006 D 方案视觉化 (Mermaid graph LR)
- `crd-relationships.md` — 6 CRD 关系图 (Mermaid graph TD)

✅ **4 视觉资产规格**（docs/launch/）
- `cover-image-specs.md` — PH 240×240 + dev.to 1000×420 + demo.gif/mp4 1280×720 设计规格
- `og-image-spec.md` — GitHub social preview 1280×640 规格 + OG meta tag
- `demo-video-script.md` — 60-90s storyboard + production notes
- **以上规格 maintainer 可直接执行，无需设计判断**

✅ **反馈基础设施**
- `faq.md` — Top-10 早期用户问题 + 答案
- `engagement-playbook.md` — Day 1/7/14/30 maintainer 手册 + 4 reply templates + Week 1 stats

✅ **测试数一致性**（11 处遗留 466 → 474 修正）
- 5 份 launch drafts + CONTRIBUTING.md

---

## 3. 您需要做的 3 阶段工作

### 阶段 A: 视觉资产制作（2-3 小时 · 阻塞 4 渠道）

**Step A1: 启动 og-image.png 制作（30 min · 最高 ROI）**

一个 PNG 文件影响所有 Twitter / Facebook / LinkedIn / Slack / Discord link preview。

```
1. 打开 Figma / Sketch / GIMP / Inkscape 任一工具
2. 按 docs/launch/og-image-spec.md 制作 1280×640 PNG
3. 上传到 https://github.com/superteam-cn/superteam-a2a/settings
   → Social preview → Upload an image
4. commit 到 docs/launch/og-image.png
```

**Step A2: 制作 cover-ph.png（20 min）**

```
按 docs/launch/cover-image-specs.md §Asset 1
240×240 PNG · K8s wheel + agent node · dark slate #0F172A
提交到 Product Hunt: https://www.producthunt.com/posts/new
```

**Step A3: 制作 cover-devto.png（30 min）**

```
按 docs/launch/cover-image-specs.md §Asset 2
1000×420 PNG · gradient 背景 + 代码 snippet + A2A flow arrows
发布到 dev.to: https://dev.to/new
```

**Step A4: 录制 demo.gif（60-90 min）**

```bash
# 1. Setup (5 min)
kind create cluster --name superteam-a2a-demo
docker buildx build -t superteam-a2a/hello-agent:dev services/hello-agent/
kind load docker-image superteam-a2a/hello-agent:dev --name superteam-a2a-demo
helm install hello-agent helm/hello-agent/
sleep 30

# 2. Record (10 min, 按 demo-video-script.md §Capture commands)
asciinema rec demo.cast --title "superteam-a2a demo"
# 跑 demo-video-script.md 中的命令
# Ctrl-D 结束

# 3. Convert to GIF + MP4 (5 min)
docker run --rm -v $(pwd):/data asciinema/asciicast2gif \
  -s 1.0 -w 100 -h 30 demo.cast demo.gif
# 或用 agg (新工具):
agg demo.cast demo.gif

ffmpeg -i demo.gif -c:v libx264 -pix_fmt yuv420p \
  -movflags +faststart demo.mp4

# 4. Upload
- demo.gif commit 到 docs/launch/
- demo.mp4 upload 到 YouTube + Bilibili
- demo.mp4 mirror commit 到 docs/launch/
```

**阶段 A 完成后**:
```bash
cd superteam-a2a
git add docs/launch/*.png docs/launch/*.gif docs/launch/*.mp4
git commit -m "feat(phase5): #123 Phase 5 视觉资产就绪"
git push origin main
```

### 阶段 B: 14 渠道 / 7 天 rollout（~10 小时 spread 7 天）

**按 docs/launch/submission-checklist.md 严格按时间表**：

| Day | 渠道 | 时间（峰值） | 阻塞 |
|---|---|---|---|
| Tue | Discussions + Twitter + r/kubernetes | 8:00 ET + 7:00 PT | 无 |
| Wed | **Product Hunt** + dev.to | 8:00 PT + 10:00 ET | 视觉资产 |
| Thu | **Show HN** + r/programming | 8:00 ET | 无 |
| Fri | r/Python + 掘金 | 10:00 ET + 10:00 CST | 无 |
| Sat | 知乎 + SegmentFault | 10:00 CST + 14:00 CST | 无 |
| Sun | OSCHINA + InfoQ | 9:00 CST + 14:00 CST | 无 |
| Mon | Discord/Slack 5 community | 12:00 ET（30 min 间隔）| 无 |

**每个渠道的标准动作**：

```
1. 打开对应平台，按 submission-checklist.md 的 Per-channel playbook
2. 复制 docs/launch/<platform>-draft.md 内容到平台
3. 按 engagement playbook §Day 1 engage 4-24 小时
4. 用 4 reply templates 之一回答问题
5. 记录结果（feedback notes）
```

### 阶段 C: Day 7 + Day 30 复盘（30 min + 1 hour）

**按 docs/launch/engagement-playbook.md 严格按时间表**：

**Day 7（launch + 7 天）**：
```
1. 测量指标（GitHub stars / forks / issues / PRs）
2. 写 Week 1 retrospective（GitHub Discussions + Twitter）
3. cut v0.1.1 patch release（如有 P0/P1 修复）
4. 更新 ROADMAP.md
5. 每个 Discord community 发感谢消息
```

**Day 30（launch + 30 天）**：
```
1. 测量全部指标 + Phase 5.5 决策
2. 写 Month 1 retrospective
3. cut v0.2.0-alpha.0（如有功能 ready）
4. 公布 Phase 5.5 计划（Top-3 优先级）
5. 邀请 top 3 contributors 加入 mentions
```

---

## 4. 文档索引（single source of truth）

### 必读（启动前 30 分钟）

| 文档 | 内容 |
|---|---|
| [docs/launch/submission-checklist.md](./submission-checklist.md) | 14 渠道 / 7 天 rollout 完整时间表 |
| [docs/launch/engagement-playbook.md](./engagement-playbook.md) | Day 1/7/14/30 maintainer 行动清单 |
| [docs/launch/faq.md](./faq.md) | Top-10 早期用户问题（issue / 评论快速引用）|
| [README.md](../../README.md) | GitHub 仓库首页（含 474 tests badge + Architecture section）|
| [CONTRIBUTING.md](../../CONTRIBUTING.md) | 贡献者指南（含 474 tests + main HEAD 92b12b7）|

### 视觉规格

| 文档 | 内容 |
|---|---|
| [docs/launch/cover-image-specs.md](./cover-image-specs.md) | PH 240×240 + dev.to 1000×420 + demo.gif/mp4 规格 |
| [docs/launch/og-image-spec.md](./og-image-spec.md) | GitHub social preview 1280×640 + OG meta tag |
| [docs/launch/demo-video-script.md](./demo-video-script.md) | 60-90s 视频脚本 + 录制命令 |

### 架构参考

| 文档 | 内容 |
|---|---|
| [docs/architecture/system-overview.md](../architecture/system-overview.md) | 系统总览图（Mermaid graph TB）|
| [docs/architecture/a2a-protocol-flow.md](../architecture/a2a-protocol-flow.md) | A2A 协议流程图（sequence）|
| [docs/architecture/single-process-backend.md](../architecture/single-process-backend.md) | ADR-0006 D 方案图（graph LR）|
| [docs/architecture/crd-relationships.md](../architecture/crd-relationships.md) | 6 CRD 关系图（graph TD）|
| [docs/admin/mkdocs.yml](../admin/mkdocs.yml) | docs site 站点结构（已含 Visual Diagrams）|

### Launch 渠道文案（14 份）

```
docs/launch/product-hunt-draft.md
docs/launch/twitter-thread-draft.md
docs/launch/discussions-show-and-tell-draft.md
docs/launch/show-hn-draft.md
docs/launch/devto-draft.md
docs/launch/reddit-kubernetes-draft.md
docs/launch/reddit-programming-draft.md
docs/launch/reddit-python-draft.md
docs/launch/juejin-draft.md
docs/launch/zhihu-draft.md
docs/launch/segmentfault-draft.md
docs/launch/oschina-draft.md
docs/launch/infoq-draft.md
docs/launch/community-channels-drafts.md
docs/launch/release-v0.1.0-notes.md
```

---

## 5. Commit 历史（最近 10 个）

```
b1f1554 feat(phase5): #122 Phase 5 早期反馈基础设施 · 测试数修正 + OG + FAQ + engagement
92b12b7 feat(phase5): #121 Phase 5 视觉资产前置 · 4 张架构图 + 视觉规格
c499a9c feat(phase5): #120 Phase 5 LAUNCH 平台文案补全 · 14 渠道 / 7 天 rollout
2bc405b feat(phase5): #119 Phase 5 LAUNCH publish prep · issue 模板 + submission checklist + demo script
69132ad docs(phase5): #118 Phase 5 LAUNCH §F 同步（PR #62 squash merged @ 6c4f9ce 后）
6c4f9ce feat(phase5): #118 Phase 5 LAUNCH · Adapter SDK Protocol + 4 framework examples + mkdocs docs site (#62)
011d6e7 docs(phase4): #117 Phase 4 打磨 · README + CONTRIBUTING + launch 草稿 + ROADMAP v0.1.0
dc4e4bf chore(repo): #117 Phase 4 打磨 · git index 整理移除 60 个 typo path entries
a8afdc3 docs(phase4): #116 PR-5 §F 跨文档同步（PR #61 squash merged @ eb4a7be 后 · Phase 4 8/8 PR 全部收口）
eb4a7be feat(phase4): #116 PR-5 Knowledge Service Step 3 · Helm + Dockerfile + cert-manager + 16 测试 ID (#61)
```

## 6. 关键不变量（5 项 · 100% 保持）

| 不变量 | 实装位置 | 验证方式 |
|---|---|---|
| Wire contract 零漂移 | L1 v0.2.0 + L3 spec + 23 错误码静态断言 | WireSyncService |
| 50ms fail-closed admission | AdmissionValidatorProtocol + fail_closed_50ms 装饰器 | E2E ADM-IT-004~006 |
| Pydantic v2 populate_by_name | 全 CRD schema | pyright 0 errors |
| extra=forbid | 全 CRD model | pytest 全绿 |
| JSON-RPC code 范围 -32603 ~ -32018 | to_json_rpc_error_code helper | ERR-IT-001/002 |

---

## 7. 紧急联系 / FAQ

**遇到问题时的检查清单**：

1. **git 工作树脏？** → `git status` 检查
2. **pytest 失败？** → 跑 `uv run pytest --tb=short -q` 看具体哪个测试
3. **CI 失败？** → 看 .github/workflows/ 5 个 workflow 的具体错误
4. **架构不清楚？** → 看 docs/architecture/ 4 张图
5. **Phase 5 不清楚？** → 看本文档（handoff.md）

**Maintainer 联系方式**：
- GitHub: [@CoderZhangfujiang](https://github.com/CoderZhangfujiang)
- 仓库 Issues: <https://github.com/superteam-cn/superteam-a2a/issues>

**Claude Code / 主 Agent 后续**：
- 工作目录: `D:/Agents/AgentTeam/superteam-a2a`
- uv 路径: `/c/Users/Administrator/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/LocalCache/local-packages/Python313/Scripts/uv.exe`
- MEMORY 索引: `C:\Users\Administrator\.claude\projects\D--Agents-AgentTeam\memory\MEMORY.md`

---

## 8. 时间表汇总（您需要看到的整体节奏）

```
2026-08-16 (Today)      Phase 5 LAUNCH 文字/规格/反馈基础设施 100% 就绪
                        ─── 您启动 #123 视觉资产制作（2-3 小时）───
2026-08-17 (Mon-Tue)    视觉资产就绪 → 启动 #124 14 渠道 7 天 rollout
2026-08-17 Tue          Day 1: Discussions + Twitter + r/kubernetes
2026-08-18 Wed          Day 2: Product Hunt + dev.to
2026-08-19 Thu          Day 3: Show HN + r/programming
2026-08-20 Fri          Day 4: r/Python + 掘金
2026-08-21 Sat          Day 5: 知乎 + SegmentFault
2026-08-22 Sun          Day 6: OSCHINA + InfoQ
2026-08-23 Mon          Day 7: Discord/Slack 5 community
                        ─── Day 7 复盘 + v0.1.1 patch（如有 P0/P1）───
2026-08-30 (+14 days)   Day 14 中期 checkpoint
2026-09-15 (+30 days)   Day 30 复盘 + v0.2.0-alpha + Phase 5.5 计划
```

---

## 9. 注意事项

### DO ✅

- ✅ 严格按 submission-checklist.md 时间表（不要提前 / 不要换顺序）
- ✅ 每个渠道 post 后 engage 4-24 小时
- ✅ 用 engagement-playbook.md 的 4 reply templates
- ✅ Day 7 复盘要写出来（不是内部思考）
- ✅ v0.1.1 patch 必须保持 wire contract 不变
- ✅ 任何架构变更走 ADR 流程

### DON'T ❌

- ❌ 不要同时发布多个渠道（≥30 min 间隔）
- ❌ 不要在 Friday/Saturday 发 HN
- ❌ 不要在 issue/comment 里和怀疑者争论（链接事实，保持冷静）
- ❌ 不要在 release body 里包含 breaking changes（用 v0.2.0）
- ❌ 不要 merge 不通过 4 静态 + 2 动态门禁的 PR
- ❌ 不要 skip Day 7 retrospective
- ❌ 不要让 silent failure > 24 小时（沉默 = 负面信号）

---

## 10. 一句话总结

**Phase 5 LAUNCH 的工作已完成 95%。剩 5% 是您的 2-3 小时创意会话（视觉资产）+ 7 天 rollout 执行。所有文档、规格、文案、回复模板、playbook 都已就绪，按图索骥即可。**

<sub>Maintainer action: ① 读本文档 30 分钟 ② 启动 #123 视觉资产制作（2-3 小时）③ commit + push ④ 按 submission-checklist.md 启动 #124 7 天 rollout</sub>
