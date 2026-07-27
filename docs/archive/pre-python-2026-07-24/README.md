# Go Baseline 归档目录（pre-python-2026-07-24）

> 📦 **本目录归档 2026-07-24 Python-first 全栈迁移（ADR-0005）之前的所有 Go baseline 设计/Spec 文档**
>
> 创建日期：2026-07-24
> 归档原因：ADR-0005 触发 L2-1~L2-4 Python v0.2 重写；按 #21 教训（L2-1 Go Spec v0.1.0 原内容被覆盖丢失）建立归档机制，避免后续 Python 重写覆盖事故
> 治理依据：[CONSTITUTION.md](../../../CONSTITUTION.md) v0.5.0 §3.8 Python-first + [ADR-0005](../../adr/0005-python-first-technology-stack.md) §3.1 + §13.1

---

## 归档文件清单

| 文件 | 版本 | 来源 | 大小 | 评审日期 |
|------|------|------|------|----------|
| [L2-operator-core-design-v0.1.0-go-baseline.md](./L2-operator-core-design-v0.1.0-go-baseline.md) | **v0.1.0** Go baseline | `docs/design/L2-modules/L2-operator-core.md` 原文件 | ~21KB / 521 行 | 2026-07-24 |
| [L2-operator-core-spec-v0.1.0-go-baseline.md](./L2-operator-core-spec-v0.1.0-go-baseline.md) | **v0.1.0** Go baseline | `docs/spec/L2-module-specs/L2-operator-core.md` 原文件 | ~52KB / 1213 行 | 2026-07-24 |
| [L3-operator-core-spec-v0.1-draft-go-baseline.md](./L3-operator-core-spec-v0.1-draft-go-baseline.md) | **v0.1-draft** Go baseline（**未评审**） | `docs/spec/L3-file-specs/L3-operator-core.md` 原文件 | ~75KB / 1886 行 | 2026-07-27 |
| [L3-a2a-core-spec-v0.1-draft-go-baseline.md](./L3-a2a-core-spec-v0.1-draft-go-baseline.md) | **v0.1-draft** Go baseline（**未评审**） | `docs/spec/L3-file-specs/L3-a2a-core.md` 原文件 | ~62KB / 1446 行 | 2026-07-27 |

---

## git 提交历史（ADR-0005 Python 重写后 · 2026-07-27 起）

> **目的**：登记本目录归档文件在 #46 起 `git init` 后是否仍被引用 + 后续 Python 重写是否导致覆盖丢失事故。**未在此登记的 commit = 引用本目录归档但未覆盖**。

| Commit | 说明 | 覆盖丢失 | 引用模式 |
|--------|------|----------|----------|
| `64b6147` | docs: initial commit · 45 sessions pre-L3-1 Spec v0.2.0 boundary | 无 | 仅历史存档 |
| `da78c5c` | feat(L3-1): §7 observability + RBAC + Helm values 文件级 Spec | 无 | 引用 L3-1 Go baseline 历史 |
| `fad1556` | feat(L3-1): §8 testing + toolchain 文件级 Spec | 无 | 引用 L3-1 Go baseline 历史 |
| `400f978` | feat(L3-1): §9 acceptance 验收清单 文件级 Spec | 无 | 引用 L3-1 Go baseline 历史 |
| 计划中 | feat(L3-2): Python v0.2-draft 骨架稿（**即将覆盖** `docs/spec/L3-file-specs/L3-a2a-core.md`） | ⚠️ Go baseline 即将丢失（本目录保留副本） | 与 #21/#34/#38 模式一致 |

> ⚠️ **L2-1 Go Spec v0.1.0 已在 #21 会话丢失**（被 L2-1 Python Spec v0.2-draft 覆盖事故），未及时归档——本目录不再补录 L2-1 Go baseline（已无原文件可归档）
>
> ⚠️ **L2-3 Go Design + Spec v0.1.0 已在 #34 会话丢失**（被 L2-3 Python Design v0.2-draft 覆盖事故，与 L2-1 模式相同）—— 本目录不再补录 L2-3 Go baseline；仅 [`docs/reviews/l2-3-adapter-review.md`](../../reviews/l2-3-adapter-review.md)（2026-07-24 通过，Go baseline 评审）作为历史参照
>
> ⚠️ **L2-4 Go Design + Spec v0.1.0 已在 #38 会话丢失**（被 L2-4 Python Design v0.2-draft 覆盖事故，与 L2-1 / L2-3 模式相同）—— 本目录不再补录 L2-4 Go baseline；仅 [`docs/reviews/l2-4-knowledge-memory-review.md`](../../reviews/l2-4-knowledge-memory-review.md)（2026-07-24 通过，Go baseline 评审；49KB / 626 行 / §A-§G 10 维度）作为历史参照

---

## 归档原则

1. **不删除原文件**：原文件路径 `docs/design/L2-modules/L2-operator-core.md` 与 `docs/spec/L2-module-specs/L2-operator-core.md` **保留**，仅在原文件顶部追加归档头 + ADR-0005 supersede 指针（已在 2026-07-24 由 #22 同步完成）
2. **副本完整性**：归档副本是原文件 2026-07-24 评审通过时的完整快照，**不**包含后续 Python 重写的内容
3. **Python 实现依据**：
   - **禁止**引用 Go baseline 作为 Python 实现依据（实现栈不一致）
   - **允许**引用 Go baseline 的 **wire contract / 业务语义 / 状态机 / RBAC / metric name** 等不变部分
4. **新增引用**：后续 Python 重写过程中如需引用本目录，必须明确标注 "wire contract only" 或 "业务语义 only"

---

## 关联文档

- **ADR-0005 Python-first**：[`docs/adr/0005-python-first-technology-stack.md`](../../adr/0005-python-first-technology-stack.md) — Python-first 全栈迁移决策（§3.1 Operator Core 模块映射 + §7 单进程原则 + §13.1 OTel/指标迁移）
- **L1 v0.2.0 Architecture**：[`docs/design/L1-architecture.md`](../../design/L1-architecture.md) — 评审通过 2026-07-24（[评审](../../reviews/l1-python-stack-migration-review.md)）；§3.2 编排层 + §4 核心组件（C-1 Operator / C-2 A2A Core / C-3 Adapter SDK）
- **L1 v0.2.0 Spec**：[`docs/spec/L1-system-spec.md`](../../spec/L1-system-spec.md) — §2-§4 CRD + §7 状态机 + §9-§10 资源/限流 + §16 Prometheus 指标
- **L2-1 A2A Protocol v0.2.0**：[`docs/design/L2-modules/L2-a2a-protocol.md`](../../design/L2-modules/L2-a2a-protocol.md) + [Spec](../../spec/L2-module-specs/L2-a2a-protocol.md) — 2026-07-24 Python 重写评审通过（[评审](../../reviews/l2-1-a2a-protocol-review.md)）；**L2-2 依赖此模块**
- **L2-2 Operator Core Python 设计 v0.2-draft**：[`docs/design/L2-modules/L2-operator-core.md`](../../design/L2-modules/L2-operator-core.md) — 待 #23 会话起草（替换为 Python-first 实现栈）
- **CONSTITUTION v0.5.0**：[`CONSTITUTION.md`](../../../CONSTITUTION.md) §3.8 Python-first + §16 会话与上下文管理

---

## L2-2 Python 重写交付清单（待 #23+ 完成）

- [ ] L2-2 设计 v0.2-draft Python（30-40KB / ~700-900 行）
- [ ] L2-2 Spec v0.2-draft Python（30-40KB / ~800-1000 行）
- [ ] L2-2 评审 v0.2（10 维度）
- [ ] 升级双文档 v0.2-draft → v0.2.0 + 跨文档同步（F.1-F.6 6 步 + L2-1/L2-3/L2-4 Spec 附录 A）

---

> 状态：🟡 1/4 项完成（归档已建立；L2-2 设计/Spec/评审待办）
> 下次会话入口：L2-2 Operator Core Python 设计 v0.2-draft 起草（参考 L2-1 Python 设计 44KB / L2-3 设计 32KB 规模）