# Phase 5 LAUNCH submission checklist

This is the **operational playbook** for actually submitting superteam-a2a v0.1.0 to public launch surfaces. Drafts live in `docs/launch/`; this file tracks **when and how** to submit each.

## v0.1.0 status (2026-08-16)

- ✅ GitHub Release published: <https://github.com/superteam-cn/superteam-a2a/releases/tag/v0.1.0>
- ✅ Repository topics (11): kubernetes, ai-agents, a2a, google-a2a, operator, kopf, langchain, autogen, crewai, python, pydantic
- ✅ Description updated
- ✅ Homepage URL set to docs site
- ✅ Doc site auto-deployed via `.github/workflows/docs.yml` → `https://superteam-cn.github.io/superteam-a2a/`
- ✅ Issue templates: bug, feature, spec-deviation, framework-adapter, good-first-issue
- ✅ Visual assets (2026-09-03 · PR #71 squash merged @ `9f92701`): og-image.png + cover-ph.png + cover-devto.png + demo.gif (storyboard placeholder)
- ⏳ Real demo.mp4 — pending asciinema recording (`bash scripts/record_demo.sh`)

## Submission timeline

We don't want to spam. **14 channels across 7 days**, starting with the highest-quality audience first and spacing each submission by 30-60 min to avoid overlap.

| Day | Channel | Draft | When to submit | Owner | Status |
|---|---|---|---|---|---|
| 1 | GitHub Discussions "Show and tell" | `docs/launch/discussions-show-and-tell-draft.md` | Tue 8:00 ET | maintainer | � pending |
| 1 | Twitter/X thread | `docs/launch/twitter-thread-draft.md` | Tue 7:00 PT (US west peak) | maintainer | � pending |
| 1 | Reddit r/kubernetes | `docs/launch/reddit-kubernetes-draft.md` | Tue 9:00 ET | maintainer | ⏳ pending |
| 2 | Product Hunt | `docs/launch/product-hunt-draft.md` | Wed 8:00 PT (PH peak) | maintainer | ⏳ pending |
| 2 | dev.to | `docs/launch/devto-draft.md` | Wed 10:00 ET | maintainer | ⏳ pending |
| 3 | Hacker News (Show HN) | `docs/launch/show-hn-draft.md` | Thu 8:00 ET (HN peak) | maintainer | ⏳ pending |
| 3 | Reddit r/programming | `docs/launch/reddit-programming-draft.md` | Thu 9:00 ET | maintainer | ⏳ pending |
| 4 | Reddit r/Python | `docs/launch/reddit-python-draft.md` | Fri 10:00 ET | maintainer | � pending |
| 4 | 掘金 (Juejin) | `docs/launch/juejin-draft.md` | Fri 10:00 CST | maintainer | � pending |
| 5 | 知乎 (Zhihu) | `docs/launch/zhihu-draft.md` | Sat 10:00 CST | maintainer | ⏳ pending |
| 5 | SegmentFault | `docs/launch/segmentfault-draft.md` | Sat 14:00 CST | maintainer | ⏳ pending |
| 6 | OSCHINA | `docs/launch/oschina-draft.md` | Sun 9:00 CST | maintainer | ⏳ pending |
| 6 | InfoQ | `docs/launch/infoq-draft.md` | Sun 14:00 CST | maintainer | ⏳ pending |
| 7 | Discord / Slack (5 communities) | `docs/launch/community-channels-drafts.md` | Mon 12:00 ET | maintainer | ⏳ pending |

## Per-channel playbook

### GitHub Discussions → Show and tell

1. Web: <https://github.com/superteam-cn/superteam-a2a/settings/discussions> → enable Discussions
2. Web: create categories: Show and tell, Help wanted, Q&A, Announcements, General
3. Web: pin a "Welcome" thread pointing to CONTRIBUTING.md + good-first-issue label
4. Post: copy `docs/launch/discussions-show-and-tell-draft.md` body into a new discussion in "Show and tell"
5. Pin the discussion for 7 days

### Twitter/X thread

1. Open <https://x.com/compose/post> or use Typefully for scheduling
2. Paste each of the 7 tweets from `docs/launch/twitter-thread-draft.md` in order
3. Pin the first tweet to your profile for 24 hours
4. Quote-tweet the thread at +30 min with the demo GIF (once recorded)
5. Quote-tweet at +60 min with the BM25 benchmark screenshot

### Reddit r/kubernetes

1. Open <https://www.reddit.com/r/kubernetes/submit?type=TEXT>
2. Title: **"Show & Tell: superteam-a2a — multi-framework agent orchestration on K8s via Google A2A protocol"** (no emoji)
3. Body: copy `docs/launch/reddit-kubernetes-draft.md`
4. Flair: **Project** + **Open Source**
5. Important: do **NOT** include emojis in the title (Reddit bans emoji titles)
6. Engage with comments for the first 4 hours (Reddit algorithm)

### Product Hunt

1. Open <https://www.producthunt.com/posts/new>
2. Tagline: **"Multi-framework AI agents on K8s via Google A2A"** (52 chars)
3. Short description: copy from `docs/launch/product-hunt-draft.md`
4. Topics: Open Source, Kubernetes, Developer Tools, AI, Tech
5. Cover image: <https://github.com/superteam-cn/superteam-a2a/raw/head/docs/launch/cover-ph.png> (✅ 240×240 committed @ `9f92701`)
6. **Immediately after submission**: paste the maker comment from the draft file as your first comment
7. Engage with every comment for 24 hours

### dev.to

1. Open <https://dev.to/new>
2. Title: **"Building a Kubernetes-native agent platform: lessons from shipping v0.1.0 in 6 weeks"**
3. Body: copy `docs/launch/devto-draft.md`
4. Tags: `kubernetes`, `opensource`, `python`, `ai`, `k8s`
5. Canonical URL: <https://github.com/superteam-cn/superteam-a2a/blob/main/docs/launch/devto-draft.md>
6. Cover image: <https://github.com/superteam-cn/superteam-a2a/raw/head/docs/launch/cover-devto.png> (✅ 1000×420 committed @ `9f92701`)

### Hacker News (Show HN)

1. Open <https://news.ycombinator.com/submit>
2. Title: **"Show HN: superteam-a2a – Multi-framework agent orchestration on Kubernetes"** (no emoji)
3. URL: <https://github.com/superteam-cn/superteam-a2a> (NOT the docs site — HN prefers the actual project)
4. **First comment immediately after submission**: copy the "Try it" + "Numbers" sections from `docs/launch/show-hn-draft.md` as your reply-to-comments blurb
5. Submit Tue–Thu 8:00–10:00 ET (HN peak). Friday/Saturday are dead zones.
6. Engage with comments for the first 6 hours — HN algorithm punishes unattended Show HN posts
7. If flagged: do NOT defend in the comments. Reply politely, link to facts.

### Reddit r/programming

1. Open <https://www.reddit.com/r/programming/submit?type=TEXT>
2. Title: copy from `docs/launch/reddit-programming-draft.md` (no emoji)
3. Body: copy from `docs/launch/reddit-programming-draft.md`
4. Flair: **Show & Tell** if available, else **Project**
5. Engage for 4 hours
6. Do NOT cross-link to other channels in the post (looks spammy)

### Reddit r/Python

1. Open <https://www.reddit.com/r/Python/submit?type=TEXT>
2. Title: copy from `docs/launch/reddit-python-draft.md` (no emoji)
3. Body: copy from `docs/launch/reddit-python-draft.md`
4. Schedule for **Thursday or Friday** 10:00 ET (don't compete with r/programming same day)
5. Be ready for Pydantic / async / kopf questions — have concrete answers

### 掘金 (Juejin)

1. Open <https://juejin.cn/post-editor/new>
2. Title: **"6 周从 0 到 v0.1.0：基于 K8s 的多 Agent 编排平台 superteam-a2a 实战"**
3. Body: copy `docs/launch/juejin-draft.md`
4. Tags: `Kubernetes`, `Python`, `开源`, `AI`
5. Category: 后端 (Backend)

### 知乎 (Zhihu)

1. Open <https://www.zhihu.com/pillar/create> (专栏) OR answer a relevant question
2. Title: **"从 0 到 v0.1.0：基于 Kubernetes 构建多 Agent 编排平台 superteam-a2a 的 6 周实践"**
3. Body: copy `docs/launch/zhihu-draft.md`
4. Topic tag: `Kubernetes`, `AI Agent`, `开源`
5. Recommended posting time: Saturday 10:00 CST (知乎 algorithm has 24h boost for new posts)

### SegmentFault

1. Open <https://segmentfault.com/write>
2. Title: copy from `docs/launch/segmentfault-draft.md`
3. Body: copy from `docs/launch/segmentfault-draft.md`
4. Tags: `Kubernetes`, `Python`, `开源`, `AI`
5. Category: 后端 / 云计算
6. Post Saturday afternoon 14:00 CST

### OSCHINA

1. Open <https://my.oschina.net/admin/blogs> (资讯) OR <https://www.oschina.net/question/add?type=news>
2. Title: **"superteam-a2a v0.1.0 发布：Kubernetes 原生多 Agent 编排平台"**
3. Body: copy `docs/launch/oschina-draft.md`
4. Tags: kubernetes, python, ai, 开源
5. Post Sunday morning 9:00 CST

### InfoQ

1. Submit via <https://www.infoq.cn/write> (审核较严, also consider editors@infoq.com)
2. Title: copy from `docs/launch/infoq-draft.md`
3. Abstract: 200 字以内 (use the 摘要 section)
4. Body: copy from `docs/launch/infoq-draft.md`
5. Author signature: `CoderZhangfujiang（Zach Zhang）` with GitHub link
6. Post Sunday afternoon 14:00 CST

### Discord / Slack (5 communities)

1. See `docs/launch/community-channels-drafts.md` for all 5 tailored messages
2. Posting order (Mon, 30 min apart):
   - 12:00 ET — Kubernetes Slack `#show-and-tell`
   - 12:30 ET — AI Agents Discord `#project-showcase`
   - 13:00 ET — r/kubernetes Discord `#show-and-tell`
   - 13:30 ET — CNCF Slack `#K8s-Operators`
   - 14:00 ET — LangChain Discord `#showcase`
3. Engage for 4 hours per channel

## Tracking

Create a tracking issue like `#121 Phase 5 LAUNCH submissions` and check off each channel as it goes live.

## Post-launch monitoring (week 1)

- GitHub stars target: 50+
- HN ranking target: front page (top 30) for 4+ hours
- Product Hunt ranking target: top 10 of the day
- Cross-post discussion target: 10+ meaningful comments across channels
- Issue target: 5+ new issues (bug reports + feature requests)
- PR target: 2+ community PRs (good-first-issue tags)

## Things to do **after** first wave of submissions

- [ ] Add a "Users" section to README once 3+ orgs publicly use it
- [ ] Write a "Stargazers over time" chart using <https://star-history.com>
- [ ] Plan Phase 5.5: address top-3 issues from launch feedback
- [ ] Plan Phase 6: v1.0 GA based on community input

## When NOT to submit

- Don't submit on a Friday (HN algorithm + community engagement lowest)
- Don't submit on a holiday weekend
- Don't submit before 6 CI workflows are green (they are as of #118)
- Don't submit without testing the install path on a fresh machine (do it on a clean `kind` cluster first)
- Don't submit two channels within 30 min of each other (audiences overlap)

## Current submission status

✅ = done · ⏳ = scheduled · 🔴 = blocked · 🚫 = cancelled

- ⏳ GitHub Discussions "Show and tell"
- ⏳ Twitter/X thread
- ⏳ Reddit r/kubernetes
- ⏳ Product Hunt
- ⏳ dev.to
- ⏳ Hacker News Show HN
- ⏳ Reddit r/programming
- ⏳ Reddit r/Python
- ⏳ 掘金
- ⏳ 知乎
- ⏳ SegmentFault
- ⏳ OSCHINA
- ⏳ InfoQ
- ⏳ Discord / Slack (5 communities)

## Assets that must be created before submission

- [ ] `docs/launch/cover-ph.png` (Product Hunt cover, 240×240)
- [ ] `docs/launch/cover-devto.png` (dev.to cover, 1000×420)
- [ ] `docs/launch/demo.mp4` (60-90s demo video per `docs/launch/demo-video-script.md`)
- [ ] YouTube + Bilibili mirror of `demo.mp4`
- [ ] Architecture diagram (regenerated from current code)
- [ ] BM25 benchmark screenshot (`pytest -k bm25 -v` output)

Blocking assets: **0** for text channels · **3** for Product Hunt / dev.to / Twitter (cover images + demo video)
