# Launch Engagement Playbook — superteam-a2a v0.1.0

> **Audience**: maintainer (Zach) + any contributor helping during launch
>
> **Window**: 30 days from launch (2026-08-16 → 2026-09-15)
>
> **Status**: ✅ ready to execute after the 7-day rollout in [submission-checklist.md](./submission-checklist.md)

This playbook covers what to do **after** the first wave of submissions. It's organized by day (1, 7, 30) with concrete actions and templates.

---

## Day 1 (Day of first launch post)

### Hours 0-4: Active engagement

- [ ] Stay online for 4 hours after first channel post
- [ ] Reply to every comment within 10 minutes
- [ ] Pin a "Try it locally" comment with `CONTRIBUTING.md` link
- [ ] Post a "Day 1 stats" comment at hour 4 (test count, install success rate, issues filed)

### Hours 4-24: Maintain presence

- [ ] Check channels every 2 hours
- [ ] Reply within 30 minutes during waking hours
- [ ] Convert good feedback into issues (don't just acknowledge)
- [ ] Thank every new GitHub stargazer (heart reaction, no comment)

### Day 1 success criteria

| Metric | Target | Stretch |
|---|---|---|
| Channels live | 5+ | 10+ |
| GitHub stars | 30+ | 50+ |
| Comments responded | 100% | 100% |
| Issues filed | 3+ | 5+ |
| First PR | 0 (early) | 1+ (stretch) |

### Day 1 templates

**Reply to "how do I install"**:

> Great question. Five-minute local install: `git clone` + `uv sync` + `kind create cluster` + `helm install`. Full steps in [CONTRIBUTING.md](https://github.com/superteam-cn/superteam-a2a/blob/main/CONTRIBUTING.md). If you hit a snag, please file an issue — we're actively polishing the install path.

**Reply to "is this production-ready"**:

> Short answer: core protocol runtime yes, framework adapters no. v0.1.0 ships the Hello Agent as a reference. v0.5 will ship LangChain/AutoGen/CrewAI adapters. If you want to influence the adapter API, now is the best moment — file an issue or open a PR against `docs/sdk/`.

**Reply to skeptical pushback ("why another agent framework?")**:

> Fair pushback. superteam-a2a isn't trying to be an agent framework — it's the **cluster runtime** that lets existing frameworks (LangChain, AutoGen, CrewAI, etc.) discover and call each other over Google's A2A protocol. Think of it as the "k8s + service mesh" layer for agent fleets, not as a competitor to LangChain itself.

**Reply to bug report**:

> Thanks for the report. Can you share: (1) `kubectl version`, (2) `uv --version`, (3) the exact command + error output, (4) `git rev-parse HEAD`. Filing as #NNN — will triage within 24h.

---

## Day 2-3: Triage and respond

### Daily routine

- [ ] Morning (8:00 ET): review overnight comments + issues
- [ ] Midday (12:00 ET): post Day N+1 stats, post next channel
- [ ] Evening (18:00 ET): reply to remaining comments, prep next day

### Issue triage rules

- **`bug`**: reproduce locally within 24h, label with severity (P0/P1/P2/P3)
- **`feature`**: label with area (adapter / workflow / observability / docs), link to ADR if architectural
- **`spec-deviation`**: investigate, file PR or close with explanation
- **`framework-adapter`**: encourage PR, offer to pair
- **`good-first-issue`**: assign to community contributor if possible

### Triage template

> Triage of #NNN:
> - **Severity**: P1 / P2 / P3
> - **Reproducible**: yes / no / partially
> - **Root cause**: ...
> - **Fix plan**: ...
> - **ETA**: v0.1.1 / v0.2.0 / backlog

### Day 3 success criteria

| Metric | Target |
|---|---|
| All channels live | 14/14 |
| Issues triaged within 24h | 100% |
| Comments replied within 24h | 95%+ |
| Bug fixes shipped | 1-2 |
| New community PRs merged | 1+ |

---

## Day 7: First retrospective

### What to measure

- [ ] GitHub stars (target: 50+)
- [ ] GitHub forks (target: 5+)
- [ ] Issues filed (target: 10+)
- [ ] Issues closed (target: 50%+)
- [ ] PRs from community (target: 2+)
- [ ] Discord/Slack members (target: 30+ across 5 communities)
- [ ] HN ranking peak (target: front page for 4+ hours)
- [ ] PH ranking (target: top 10 of the day)

### What to write

Write a "Week 1 Retrospective" post:

- What surprised us
- What worked
- What broke
- Top 3 issues from community feedback
- Top 3 feature requests
- Plan for Week 2

Post to GitHub Discussions "Announcements" + link from Twitter.

### Day 7 actions

- [ ] Cut a **v0.1.1 patch release** if any P0/P1 bugs were fixed
- [ ] Update [ROADMAP.md](../../ROADMAP.md) with community-validated priorities
- [ ] Pin a "Week 1 stats" comment on the original HN/Reddit posts
- [ ] Send a thank-you message in each Discord community

---

## Day 14: Mid-launch checkpoint

### What to assess

- [ ] Is the install path smooth? (look for install-failure issues)
- [ ] Are adapter SDK users succeeding? (look for SDK-related issues)
- [ ] Is the documentation complete? (look for "where do I find X" questions)
- [ ] Are there common misconceptions? (look for repeated questions)

### Mid-launch actions

- [ ] Write a "Common Pitfalls" doc based on Week 1-2 issues
- [ ] Add the most-asked questions to FAQ (see [faq.md](./faq.md))
- [ ] Identify top 3 community contributors → invite to `@superteam-a2a/contributors` mention
- [ ] Schedule a community call if interest is high

---

## Day 30: First minor release + Phase 5.5 plan

### What to ship

- [ ] **v0.1.1 patch release** (bug fixes from launch feedback)
- [ ] **v0.2.0-alpha.0** preview (if any v0.2 features are ready)
- [ ] **Phase 5.5 plan** document — top 3 priorities based on community input

### Phase 5.5 candidates (pick top 3)

- LangChain adapter (if not done by community)
- Install-path polish (based on most-common install failure)
- One CRD improvement based on spec-deviation reports
- Documentation expansion based on FAQ
- Performance improvements (if admission p95 drifts above 50ms)

### Day 30 announcement

Post to GitHub Discussions "Announcements" + Twitter:

> 30 days since v0.1.0 launch: [N] stars, [N] forks, [N] issues filed, [N] community PRs merged. Top priorities for Phase 5.5: [...] Thanks to [@user1, @user2, ...] for the contributions!

---

## Templates

### "Week 1 stats" comment

```markdown
Week 1 stats for superteam-a2a v0.1.0:

� **Numbers**
- GitHub stars: [N] (target: 50+)
- Forks: [N]
- Issues filed: [N] (target: 10+)
- Issues closed: [N] ([%])
- Community PRs merged: [N] (target: 2+)

✅ **What worked**
- [Most-installed-framework or most-engaging-channel]
- [Highest-rated aspect]

⚠️ **What broke**
- [Most common install failure]
- [Most surprising bug]

🎯 **Top 3 priorities for Week 2**
1. [P1 fix]
2. [P2 improvement]
3. [P3 polish]

Thanks to [@user1, @user2, @user3] for the contributions!
```

### Issue template (when filing on behalf of user)

```markdown
## Reported by
@username on [channel] on [date]

## Problem
[Exact problem from report]

## Reproduction
[Steps from report]

## Environment
- OS: [reported]
- k8s version: [reported]
- uv version: [reported]
- superteam-a2a: main HEAD `[sha]`

## Triage
- Severity: P1 / P2 / P3
- Reproducible: yes / no
- Fix plan: ...
```

### PR review checklist (for community PRs)

- [ ] 4 static gates pass (ruff check, ruff format, pyright, pytest)
- [ ] 2 dynamic gates pass (CodeQL python, CodeQL actions)
- [ ] Test coverage for new code
- [ ] Documentation updated if user-facing
- [ ] CHANGELOG entry (we don't have one yet — start with this PR)
- [ ] No regressions in baseline (474/474 → still 474+)

---

## What NOT to do during launch

- ❌ Don't argue with skeptics. Link to facts, stay calm.
- ❌ Don't delete posts that get downvoted. Reddit punishes deletions.
- ❌ Don't promise features publicly without an ADR.
- ❌ Don't merge PRs that don't pass the 4 static + 2 dynamic gates.
- ❌ Don't ship a v0.1.1 with breaking changes (that's v0.2.0 territory).
- ❌ Don't get into Twitter fights with competing projects.
- ❌ Don't ignore questions for >24 hours. Silence = bad signal.

---

## Resources

- [submission-checklist.md](./submission-checklist.md) — pre-launch
- [faq.md](./faq.md) — answers to expected questions
- [cover-image-specs.md](./cover-image-specs.md) — visual assets
- [og-image-spec.md](./og-image-spec.md) — social preview
- [demo-video-script.md](./demo-video-script.md) — demo video production
- [CONTRIBUTING.md](../../CONTRIBUTING.md) — contributor guide
- [GitHub Discussions](https://github.com/superteam-cn/superteam-a2a/discussions) — community

---

<sub>Maintainer action: print this playbook or save as a pinned Discussions thread. Review at Day 7 + Day 30. Adjust based on what actually happens.</sub>
