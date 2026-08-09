# Phase 2 PR-4.1.1 — E2E unskip + image build 实施计划 · v0.1-draft

| 字段 | 值 |
|---|---|
| 文档版本 | v0.1-draft（2026-08-09）|
| 上游 Spec | L3-6 v0.2.1 + ADR-0006 v1.0 + Phase 2 spike plan v1.0 + PR-25 (kind E2E 基础设施) + PR-27 (chart 完整化) |
| 起点 | main HEAD `ac46cd0`（PR #25/#26/#27 merged · 4 E2E skip）|
| 主 Agent 水位 | 5-8% 直接执行 · 模板+测试机械工作 · Subagent 接力成本 > 主 Agent 收益 |
| 周期 | 1 PR · 预计 1-2 小时 |

---

## §0 阅读指南

本文档为 Phase 2 PR-4.1.1（chart 完整化后启用 4 skipped E2E）实施计划。

**§F 同步状态**：PR 合并后追加 L3-6 §M.2 + ADR-0006 §M-5 + ROADMAP Phase 2 收口。

---

## §1 目标与不在范围

### §1.1 目标（PR-4.1.1 收口定义）

1. **e2e-envtest workflow 补 image build step**（docker buildx + kind load docker-image + values override local tag）· 当前 helm install 会 ImagePullBackOff
2. **main.py 加 kopf health endpoints**（`liveness_endpoint` + `readiness_endpoint`）· 当前 pod liveness 失败 → helm install --wait 超时
3. **LEADER-E2E-002 实装**（helm install rc=2 backend=k8s + leader pod + kill + 30s switchover）· 仅 helm + kubectl 不需 A2A
4. **LIFECYCLE-E2E-001/002 实装**（apply Memory CRD → 60s timer → status.phase="Bound" / delete → finalize → status.phase="Released"）· 仅 kubectl 不需 A2A
5. **H-RM/H-QM-E2E-001 skip message 更新**为「Phase 3 OPEN-MEMORY-002 A2A HTTP server required」（非本 PR 范围）

### §1.2 不在范围（明确剔除 · spike plan §1.2 + Phase 3 候选）

- ❌ A2A HTTP server (JSON-RPC `recordMemory`/`queryMemory`) 实装 → Phase 3 OPEN-MEMORY-002
- ❌ H-RM/H-QM A2A JSON-RPC E2E → 待 A2A HTTP server 实装后
- ❌ Vector DB / K8sBackend / 多副本生产 → v0.5+ 决策
- ❌ cert-manager 启用 → 默认保持 tls.enabled=false

---

## §2 关键决策（4 项）

### §2.1 kopf health endpoint 选型

- **方案**：使用 kopf 内置 `liveness_endpoint` + `readiness_endpoint` 参数（避免引入额外 aiohttp server）
- **理由**：kopf 1.44+ 内置 aiohttp 服务器（基于 `_kits/webhacks.py` + `_cogs/helpers/aiohttpcaps.py`）· 最小依赖
- **endpoint 路径**：`/_/health`（liveness）/ `/_/ready`（readiness）· **必须更新 deployment.yaml 探针路径以匹配 kopf 默认**（如 kopf 默认不匹配，则改为 `/_/health` + `/_/ready`）
- **风险**：kopf 默认路径与 L3-6 §9.2 line 1288-1289 描述 `/healthz` + `/readyz` 不一致 → 需要确认 kopf 实际默认

### §2.2 Docker image build + load 策略

- **方案**：在 e2e-envtest workflow 加 docker buildx step + kind load docker-image + helm install --set image.tag=<sha>+local
- **理由**：避免引入 GHCR push 依赖（CI 不应写 registry）· kind load docker-image 把本地 image 加载到 kind 节点
- **image tag 策略**：使用 `local:e2e-<github.run_id>` 标识 + helm values override `image.tag=local:e2e-<run_id>` + `image.pullPolicy=Never`

### §2.3 LEADER-E2E-002 验证范围

- **验证步骤**：
  1. helm install --set replicaCount=2 --set leaderElection.backend=k8s
  2. kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=knowledge-memory-service --timeout=90s
  3. kubectl get pods -l ... -o jsonpath 提取 leader pod（持 Lease）
  4. kubectl delete pod <leader-pod>
  5. kubectl wait --for=condition=ready pod ... --timeout=30s（验证新 leader）
- **关键不变量**：K8sLeaseLeaderElector 30s 续约 + 30s 内 leader 切换（L3-6 §4.1）

### §2.4 LIFECYCLE-E2E-001 验证范围

- **验证步骤**：
  1. kubectl apply -f memory-cr.yaml（含 4 必填字段：scopeRef/agentRef/content/summary）
  2. kubectl wait --for=jsonpath='{.status.phase}'=Bound --timeout=90s
  3. assert status.observedGeneration == metadata.generation
- **关键不变量**：MemoryReconcilerService 60s timer tick（L3-6 §4.1）· production 60s 不可改（spike plan §2.10）

---

## §3 详细步骤

### §3.1 Step 1 · e2e-envtest.yml image build（5 步）

```yaml
- name: Build Docker image
  run: |
    docker buildx build \
      -f services/knowledge-memory-service/Dockerfile \
      -t local:e2e-${{ github.run_id }} \
      --load \
      .

- name: Load image into kind
  run: kind load docker-image local:e2e-${{ github.run_id }} --name e2e-${{ github.run_id }}

- name: Helm install (with local image override)
  run: |
    if [ -f "helm/knowledge-memory-service/templates/deployment.yaml" ]; then
      helm install kmem helm/knowledge-memory-service/ \
        --namespace superteam-a2a-system --create-namespace \
        --set image.repository=local \
        --set image.tag=e2e-${{ github.run_id }} \
        --set image.pullPolicy=Never \
        --wait --timeout 120s
    fi
```

### §3.2 Step 2 · main.py kopf health endpoints

```python
def main() -> None:
    """kopf operator 启动入口 + health/readiness HTTP endpoints."""
    kopf.run(
        memo=_build_memo(),
        liveness_endpoint="http://0.0.0.0:8080/_/health",
        readiness_endpoint="http://0.0.0.0:8080/_/ready",
    )
```

**注**：路径 `_/health` + `_/ready` 是 kopf 默认 · **需要 deployment.yaml 探针路径同步更新**

### §3.3 Step 3 · deployment.yaml 探针路径同步

```yaml
livenessProbe:
  httpGet:
    path: /_/health    # kopf 默认 · was /healthz
    port: 8080
readinessProbe:
  httpGet:
    path: /_/ready     # kopf 默认 · was /readyz
    port: 8080
```

### §3.4 Step 4 · LEADER-E2E-002 实装（tests/e2e/.../test_leader_election.py）

```python
@pytest.mark.e2e
def test_leader_e2e_002_k8s_lease_spike(kind_cluster, chart_status):
    if not chart_status[0]:
        pytest.skip(f"chart incomplete: {chart_status[1]}")
    
    # helm install rc=2 backend=k8s
    subprocess.run(["helm", "install", "kmem", str(CHART_PATH), ...], check=True)
    
    # wait pods ready
    subprocess.run(["kubectl", "wait", "--for=condition=ready", "pod", "-l", ..., "--timeout=120s"], check=True)
    
    # identify leader pod (持有 Lease)
    leader_pod = subprocess.run(["kubectl", "get", "pods", "-o", "jsonpath=..."]).stdout
    
    # kill leader
    subprocess.run(["kubectl", "delete", "pod", leader_pod], check=True)
    
    # wait new leader within 30s
    subprocess.run(["kubectl", "wait", ..., "--timeout=30s"], check=True)
    
    # verify new leader pod name != old leader
    new_leader = subprocess.run(["kubectl", "get", "pods", ...]).stdout
    assert new_leader != leader_pod
```

### §3.5 Step 5 · LIFECYCLE-E2E-001 实装（tests/e2e/.../test_memory_lifecycle.py）

```python
@pytest.mark.e2e
def test_lifecycle_e2e_001_apply_to_bound(kind_cluster, chart_status, e2e_namespace):
    if not chart_status[0]:
        pytest.skip(f"chart incomplete: {chart_status[1]}")
    
    # apply Memory CRD with required fields
    cr_yaml = f"""
apiVersion: memory.superteam-a2a.io/v1alpha1
kind: Memory
metadata:
  name: e2e-test-mem
  namespace: {e2e_namespace}
spec:
  scopeRef: {{name: "default"}}
  agentRef: {{name: "default"}}
  content: {{key1: "value1"}}
  summary: "E2E test memory"
"""
    apply_memory_cr(cr_yaml)
    
    # wait 60s + buffer for kopf operator 60s timer + reconcile
    subprocess.run(["kubectl", "wait", "--for=jsonpath='{.status.phase}'=Bound", 
                    "memory", "e2e-test-mem", "-n", e2e_namespace,
                    "--timeout=120s"], check=True)
    
    # verify observedGeneration set
    observed_gen = subprocess.run(["kubectl", "get", "memory", "-o", "jsonpath=..."]).stdout
    assert int(observed_gen) >= 1
```

### §3.6 Step 6 · H-RM/H-QM test skip message 更新

```python
# tests/e2e/knowledge_memory/test_handle_record_memory.py + test_handle_query_memory.py
pytest.skip(
    "H-RM-E2E-001 / H-QM-E2E-001 deferred to Phase 3 · "
    "A2A HTTP JSON-RPC server not implemented (OPEN-MEMORY-002) · "
    "Phase 2 PR-4.1.1 仅启用 LEADER + LIFECYCLE E2E"
)
```

---

## §4 验证矩阵

| ID | 验证 | 期望 |
|---|---|---|
| VAL-PR-4.1.1-001 | helm lint + e2e-envtest.yml yaml 语法 | PASS |
| VAL-PR-4.1.1-002 | main.py pyright | 0 errors |
| VAL-PR-4.1.1-003 | main.py ruff check + format | All checks passed |
| VAL-PR-4.1.1-004 | 既有 179 tests PASS 无回归 | 179 passed |
| VAL-PR-4.1.1-005 | LEADER-E2E-001 in-process | PASS（既有） |
| VAL-PR-4.1.1-006 | LIFECYCLE-E2E-001/002 + LEADER-E2E-002 + H-RM/H-QM skip | 3 passed (kind) + 2 skipped (Windows) + 1 passed (LEADER-E2E-001) |

---

## §5 不在范围 · Phase 3 候选

| ID | 描述 | 触发条件 |
|---|---|---|
| OPEN-MEMORY-002 | A2A HTTP server (JSON-RPC recordMemory/queryMemory) | Phase 3 启动决策 |
| H-RM-E2E-001 | A2A recordMemory E2E（待 A2A HTTP server）| Phase 3 |
| H-QM-E2E-001 | A2A queryMemory E2E（待 A2A HTTP server）| Phase 3 |

---

## §6 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| kopf 默认路径与 L3-6 spec 不一致 | 中 | 中 | Step 2 + Step 3 同步更新 deployment.yaml 探针路径 + 文档化 kopf 路径选择 |
| Docker buildx 在 ubuntu-latest runner 不可用 | 低 | 高 | 验证 `docker buildx` 默认安装 · 否则 fallback docker build |
| kind load docker-image 失败（image 太大）| 低 | 中 | Dockerfile 已 multi-stage · 镜像应 < 500MB |
| helm install --wait 90s 不够（kopf 启动慢）| 中 | 中 | timeout 加到 120s + readinessProbe initialDelaySeconds 调到 10s |
| LEADER 30s 切换不满足（L3-6 §4.1 60s 续约）| 低 | 中 | 验证 Lease leaseDuration 30s + renewDeadline 15s · 可能需覆盖 values |

---

## §7 §F 同步清单（PR 合并后）

- [ ] `docs/adr/0006-memory-transport.md` §M-5：Phase 2 PR-4.1.1 E2E 启用记录
- [ ] `docs/spec/L3-file-specs/L3-memory-backend.md` §M.2：L4-Phase2 PR-4.1.1 行追加
- [ ] `ROADMAP.md`：Phase 2 5/5 → 5/5+1 完成
- [ ] `README.md`：e2e-envtest workflow 启用状态更新
- [ ] `CONSTITUTION-CHANGELOG.md`：本 PR 宪法兼容性确认（§3.4/§6/§7/§9.7/§13.1/§14.5）
- [ ] `MEMORY.md` + `docs/sessions/session-2026-08-09-cont90-pr-4-1-1-e2e-unskip.md`

---

## §8 下次会话入口

启动 PR-4.1.1 实施时，按本文档 §3 步骤顺序执行：
1. Step 1: e2e-envtest.yml image build
2. Step 2: main.py kopf health endpoints
3. Step 3: deployment.yaml 探针路径同步
4. Step 4: LEADER-E2E-002 实装
5. Step 5: LIFECYCLE-E2E-001/002 实装
6. Step 6: H-RM/H-QM skip message 更新
7. 验证（§4 矩阵）+ commit + push + PR #28

参考：docs/phase2/l4-phase2-spike-plan.md §3.4 + docs/spec/L3-file-specs/L3-memory-backend.md §9.2