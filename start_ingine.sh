#!/bin/bash
# Start ingine (loopback 8004) + allowlist relay (0.0.0.0:8003, LAN only). Idempotent.
set -u
cd "$HOME/ingine-repo" || exit 1
pkill -x ingine-serve 2>/dev/null; sleep 2
nohup env CUDA_VISIBLE_DEVICES="${INGINE_GPU:-0}" \
  ./native/build-install/apps/serve/ingine-serve --engine \
  --model-dir "$HOME/inkling-abliterated-ingine" \
  --ablation "$HOME/inkling-abliterated-ingine/inkling-2-mini-abliterated.safetensors" \
  --max-ctx 262144 --dense-fp8 --kv-fp8 --spec --spec-threshold 0.8 \
  --host 127.0.0.1 --port 8004 > /tmp/ingine_loopback.log 2>&1 &
for i in $(seq 90); do curl -sf -m 2 http://127.0.0.1:8004/health >/dev/null 2>&1 && break; sleep 2; done
curl -sf -m 2 http://127.0.0.1:8004/health >/dev/null 2>&1 || { echo "ingine health FAILED"; exit 2; }
bash "$HOME/start_relay.sh"
