#!/usr/bin/env bash
# record_demo.sh — Phase 5 LAUNCH 真实 demo 录制脚本
#
# 按 docs/launch/demo-video-script.md 录制 60-90s 真实 demo
# 输出 demo.cast → demo.gif (1280x720 ≤60s) + demo.mp4 (高画质版本)
#
# Prerequisites (一次性安装):
#   brew install asciinema agg ffmpeg
#   # 或
#   uv tool install asciinema  (Python 版)
#   cargo install agg  # 推荐 · 新版 asciicast2gif 替代
#
# 用法:
#   bash scripts/record_demo.sh

set -euo pipefail

DEMO_NAME="${DEMO_NAME:-superteam-a2a-demo}"
CLUSTER_NAME="${CLUSTER_NAME:-superteam-a2a-demo}"
HELLO_AGENT_IMAGE="${HELLO_AGENT_IMAGE:-superteam-a2a/hello-agent:dev}"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "==> Step 1/8 · kind create cluster $CLUSTER_NAME"
if kind get clusters 2>/dev/null | grep -q "^$CLUSTER_NAME$"; then
  echo "Cluster $CLUSTER_NAME already exists, reusing"
else
  kind create cluster --name "$CLUSTER_NAME"
fi

echo "==> Step 2/8 · docker build hello-agent"
docker buildx build -t "$HELLO_AGENT_IMAGE" services/hello-agent/ \
  --load --provenance=false

echo "==> Step 3/8 · kind load docker-image"
kind load docker-image "$HELLO_AGENT_IMAGE" --name "$CLUSTER_NAME"

echo "==> Step 4/8 · helm install hello-agent"
helm install hello-agent helm/hello-agent/ \
  --set image.repository="$HELLO_AGENT_IMAGE%:*" \
  --set image.tag=dev

echo "==> Step 5/8 · wait 30s for pods"
sleep 30
kubectl get pods -A
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=hello-agent -n default --timeout=60s

echo "==> Step 6/8 · asciinema record demo.cast"
echo "    Will run these commands (per demo-video-script.md scenes 0:25-0:55):"
echo "      kubectl get agentsets"
echo "      kubectl get agentset lc-1 -o yaml | head -20"
echo "      kubectl port-forward svc/hello-agent 8080:8080 &"
echo "      curl -s localhost:8080/.well-known/agent.json | jq"
echo "      curl -X POST localhost:8080/jsonrpc -d '{...}' | jq"
echo "      kill %1 (port-forward)"
echo
echo "    Starting recording now (Ctrl-D to end) ..."
cd "$WORKDIR"
asciinema rec demo.cast \
  --title "superteam-a2a demo" \
  --cols 120 --rows 30 \
  --command "bash -c '
    set -e
    echo \"\$ kubectl get agentsets\"
    kubectl get agentsets
    sleep 1
    echo
    echo \"\$ kubectl get agentset lc-1 -o yaml | head -20\"
    kubectl get agentset lc-1 -o yaml | head -20
    sleep 1
    echo
    echo \"\$ kubectl port-forward svc/hello-agent 8080:8080 &\"
    kubectl port-forward svc/hello-agent 8080:8080 >/dev/null 2>&1 &
    PF_PID=\$!
    sleep 3
    echo
    echo \"\$ curl -s localhost:8080/.well-known/agent.json | jq\"
    curl -s localhost:8080/.well-known/agent.json | jq
    sleep 1
    echo
    echo \"\$ curl -X POST localhost:8080/jsonrpc -d ...\"
    curl -s -X POST localhost:8080/jsonrpc \
      -H 'Content-Type: application/json' \
      -d '{\"jsonrpc\":\"2.0\",\"method\":\"message/send\",\"params\":{\"message\":{\"role\":\"user\",\"parts\":[{\"text\":\"hello from superteam-a2a\"}]}},\"id\":\"1\"}' | jq
    echo
    echo \"\$ kill port-forward\"
    kill \$PF_PID 2>/dev/null || true
    echo
    echo \"Demo complete.\"
    sleep 2
  '"

echo "==> Step 7/8 · convert demo.cast → demo.gif (1280x720)"
agg "$WORKDIR/demo.cast" "$WORKDIR/demo.gif" \
  --theme monokai \
  --font-size 16 \
  --line-height 1.4 \
  --padding 20 \
  --cols 120 --rows 30

# downscale to 1280x720
ffmpeg -y -i "$WORKDIR/demo.gif" \
  -vf "scale=1280:720:flags=lanczos" \
  docs/launch/demo.gif

echo "==> Step 8/8 · convert demo.gif → demo.mp4 (high-quality)"
ffmpeg -y -i "$WORKDIR/demo.gif" \
  -c:v libx264 -pix_fmt yuv420p \
  -crf 18 -preset slow \
  -movflags +faststart \
  docs/launch/demo.mp4

echo
echo "Done. Outputs:"
echo "  docs/launch/demo.gif  (1280x720, ≤60s, for Twitter quote-tweets)"
echo "  docs/launch/demo.mp4  (1920x1080, 60-90s, for YouTube/Bilibili)"
echo
echo "Verify:"
echo "  file docs/launch/demo.gif"
echo "  file docs/launch/demo.mp4"
echo
echo "Optional cleanup:"
echo "  kind delete cluster --name $CLUSTER_NAME"
