#!/bin/bash
# Start claude-code-proxy (Anthropic /v1/messages -> OpenAI /v1/chat/completions).
# Usage: bash start_claude_proxy.sh [CCP_DIR]   (default: /content/ccp)
# Prereq: git clone https://github.com/1rgs/claude-code-proxy.git "$CCP_DIR"
#         and claude-code-proxy.env copied to "$CCP_DIR/.env".
set -u
CCP_DIR="${1:-/content/ccp}"
cd "$CCP_DIR" || { echo "no $CCP_DIR - clone the proxy first"; exit 1; }
test -f .env || { echo "no .env - copy claude-code-proxy.env first"; exit 1; }

# Upstream maps only haiku/sonnet to BIG/SMALL_MODEL; Claude Code's default is
# opus, which would fall through to the real Anthropic API. Map opus too.
if grep -q '"sonnet" in clean_v.lower()' server.py; then
  sed -i 's/"sonnet" in clean_v\.lower()/any(k in clean_v.lower() for k in ("sonnet", "opus"))/g' server.py
  echo "patched: opus mapping added"
fi

pkill -9 -f uvicorn 2>/dev/null; sleep 1
nohup uv run uvicorn server:app --host 127.0.0.1 --port "${PORT:-3456}" > /content/ccp.log 2>&1 &
for i in $(seq 40); do
  curl -sf -m 2 "http://127.0.0.1:${PORT:-3456}/" >/dev/null 2>&1 && { echo "proxy UP :${PORT:-3456}"; exit 0; }
  sleep 1
done
echo "proxy FAILED - see /content/ccp.log"; exit 2
