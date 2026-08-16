# Phase 5 LAUNCH submission checklist

This is the **operational playbook** for actually submitting superteam-a2a v0.1.0 to public launch surfaces. Drafts live in `docs/launch/`; this file tracks **when and how** to submit each.

## v0.1.0 status (2026-08-16)

- ✅ GitHub Release published: <https://github.com/superteam-cn/superteam-a2a/releases/tag/v0.1.0>
- ✅ Repository topics (11): kubernetes, ai-agents, a2a, google-a2a, operator, kopf, langchain, autogen, crewai, python, pydantic
- ✅ Description updated
- ✅ Homepage URL set to docs site
- ✅ Doc site auto-deployed via `.github/workflows/docs.yml` → `https://superteam-cn.github.io/superteam-a2a/`
- ✅ Issue templates: bug, feature, spec-deviation, framework-adapter, good-first-issue

## Submission timeline

We don't want to spam. Schedule one channel per day, starting with the highest-quality audience first:

| Day | Channel | Draft | When to submit | Owner | Status |
|---|---|---|---|---|---|
| 1 | GitHub Discussions "Show and tell" | `docs/launch/show-hn-draft.md` | Tue 8:00 ET (HN peak) | maintainer | ⏳ pending |
| 1 | Reddit r/kubernetes | `docs/launch/reddit-kubernetes-draft.md` | Tue 9:00 ET | maintainer | ⏳ pending |
| 2 | dev.to | `docs/launch/devto-draft.md` | Wed 10:00 ET | maintainer | ⏳ pending |
| 3 | Hacker News (Show HN) | `docs/launch/show-hn-draft.md` (edited for HN) | Thu 8:00 ET (HN peak) | maintainer | ⏳ pending |
| 4 | 掘金 (Juejin) | `docs/launch/juejin-draft.md` | Fri 10:00 CST | maintainer | ⏳ pending |
| 5 | Discord / Slack (Kubernetes, AI agents) | announce channel | Sat 12:00 ET | maintainer | ⏳ pending |

## Per-channel playbook

### GitHub Discussions → Show and tell

1. Web: <https://github.com/superteam-cn/superteam-a2a/settings/discussions> → enable Discussions
2. Web: enable categories: Show and tell, Help wanted, Q&A, Announcements
3. Web: pin "Welcome" thread pointing to CONTRIBUTING.md + good-first-issue label
4. Post: copy `docs/launch/show-hn-draft.md` into a new discussion in "Show and tell"

### Reddit r/kubernetes

1. Open <https://www.reddit.com/r/kubernetes/submit?type=TEXT>
2. Title: **"Show & Tell: superteam-a2a — multi-framework agent orchestration on K8s via Google A2A protocol"**
3. Body: copy `docs/launch/reddit-kubernetes-draft.md`
4. Flair: **Project** + **Open Source**
5. Important: do **NOT** include emojis in the title (Reddit bans emoji titles)
6. Engage with comments for the first 4 hours (Reddit algorithm)

### dev.to

1. Open <https://dev.to/new>
2. Title: **"Building a Kubernetes-native agent platform: lessons from shipping v0.1.0 in 6 weeks"**
3. Body: copy `docs/launch/devto-draft.md`
4. Tags: `kubernetes`, `opensource`, `python`, `ai`, `k8s`
5. Canonical URL: <https://github.com/superteam-cn/superteam-a2a/blob/main/docs/launch/devto-draft.md>
6. Cover image: <https://github.com/superteam-cn/superteam-a2a/raw/head/docs/launch/cover-devto.png> (TODO: create)

### Hacker News (Show HN)

1. Open <https://news.ycombinator.com/submit>
2. Title: **"Show HN: superteam-a2a – Multi-framework agent orchestration on Kubernetes"** (no emoji)
3. URL: <https://github.com/superteam-cn/superteam-a2a> (NOT the docs site — HN prefers the actual project)
4. **First comment immediately after submission**: copy the "Try it" + "Numbers" sections from `docs/launch/show-hn-draft.md` as your reply-to-comments blurb
5. Submit Tue–Thu 8:00–10:00 ET (HN peak). Friday/Saturday are dead zones.
6. Engage with comments for the first 6 hours — HN algorithm punishes unattended Show HN posts
7. If flagged: do NOT defend in the comments. Reply politely, link to facts.

### 掘金 (Juejin)

1. Open <https://juejin.cn/post-editor/new>
2. Title: **"6 周从 0 到 v0.1.0：基于 K8s 的多 Agent 编排平台 superteam-a2a 实战"**
3. Body: copy `docs/launch/juejin-draft.md`
4. Tags: `Kubernetes`, `Python`, `开源`, `AI`
5. Category: 后端 (Backend)

### Discord / Slack

| Community | Invite | Day |
|---|---|---|
| Kubernetes Slack | <https://slack.k8s.io/> | Sat |
| AI Agents Discord | (search) | Sat |
| r/kubernetes Discord | (search) | Sat |
| Cloud Native Computing Foundation Slack | <https://slack.cncf.io/> | Sat |

Post: **"v0.1.0 of superteam-a2a just shipped — 6 CRDs, 474 tests, single-process knowledge+memory backend, 50ms fail-closed admission. Apache 2.0. <https://github.com/superteam-cn/superteam-a2a>"**

## Tracking

Create a tracking issue like `#121 Phase 5 LAUNCH submissions` and check off each channel as it goes live.

## Post-launch monitoring (week 1)

- GitHub stars target: 50+
- HN ranking target: front page (top 30) for 4+ hours
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

## Current submission status

✅ = done · ⏳ = scheduled · 🔴 = blocked · 🚫 = cancelled

- ⏳ GitHub Discussions "Show and tell"
- ⏳ Reddit r/kubernetes
- ⏳ dev.to
- ⏳ Hacker News Show HN
- ⏳ 掘金
- ⏳ Discord / Slack communities