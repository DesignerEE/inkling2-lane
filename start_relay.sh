#!/bin/bash
set -u
pkill -f allowlist_relay 2>/dev/null || true
sleep 1
nohup python3 "$HOME/allowlist_relay.py" > /tmp/allowlist_relay.log 2>&1 &
sleep 2
tail -2 /tmp/allowlist_relay.log
curl -s -m 2 http://127.0.0.1:8003/health -o /dev/null -w "local relay:%{http_code}\n"
