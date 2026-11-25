#!/usr/bin/env python3
"""Smoke test for a live inkling2-lane: health, one real completion, optional deny check.

Usage:
  python3 smoke_test.py                       # against the relay on 127.0.0.1:8003
  python3 smoke_test.py --host 192.168.1.50   # against the 5090 box from a LAN peer
  python3 smoke_test.py --expect-deny         # run from OUTSIDE ALLOW_NETS: asserts the drop
  python3 smoke_test.py --selftest            # offline checks of this script (no network)

Exit codes: 0 all checks passed, 1 a check failed, 2 lane unreachable / usage.
"""
import argparse
import json
import socket
import sys
import time
import urllib.error
import urllib.request

MODEL = "inkling-2-mini-abliterated"


def build_url(host, port, path):
    return "http://%s:%d%s" % (host, port, path)


def build_payload(model, max_tokens=8):
    return json.dumps({
        "model": model,
        "stream": False,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": "Reply with the single word: ready"}],
    }).encode()


def check_health(base, timeout=3):
    try:
        with urllib.request.urlopen(base + "/health", timeout=timeout) as r:
            return r.status == 200, "health HTTP %d" % r.status
    except urllib.error.HTTPError as e:
        return e.code == 200, "health HTTP %d" % e.code
    except Exception as e:
        return False, "health unreachable: %s" % e


def check_completion(base, model, timeout=60):
    req = urllib.request.Request(
        base + "/v1/chat/completions", data=build_payload(model),
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
    except Exception as e:
        return False, "completion failed: %s" % e
    wall = time.time() - t0
    try:
        d = json.loads(body)
        text = d["choices"][0]["message"]["content"]
        usage = d.get("usage", {})
        tok = usage.get("completion_tokens", 0)
    except Exception as e:
        return False, "bad completion body (%s): %r" % (e, body[:120])
    ok = isinstance(text, str) and text != ""
    return ok, "completion %.2fs, %d out tok, reply %r" % (wall, tok, text[:40])


def check_expect_deny(host, port, timeout=5):
    """Assert the relay drops us: only meaningful OUTSIDE ALLOW_NETS."""
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
    except OSError as e:
        return False, "nothing listens on %s:%d (%s) - cannot verify deny" % (host, port, e)
    base = "http://%s:%d" % (host, port)
    try:
        with urllib.request.urlopen(base + "/health", timeout=timeout) as r:
            return False, "expected DENY but got HTTP %d (am I inside ALLOW_NETS?)" % r.status
    except urllib.error.HTTPError as e:
        return False, "expected DENY but got HTTP %d" % e.code
    except Exception as e:
        return True, "connection accepted then dropped, as expected (%s)" % type(e).__name__


def selftest():
    p = json.loads(build_payload(MODEL))
    assert p["model"] == MODEL and p["temperature"] == 0 and p["stream"] is False
    assert p["messages"][0]["role"] == "user"
    assert build_url("127.0.0.1", 8003, "/health") == "http://127.0.0.1:8003/health"
    assert build_url("192.168.1.50", 8003, "/v1/chat/completions").endswith("/v1/chat/completions")
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    dead_port = s.getsockname()[1]
    s.close()
    ok, msg = check_expect_deny("127.0.0.1", dead_port, timeout=2)
    assert not ok and "cannot verify" in msg, msg
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8003)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--expect-deny", action="store_true",
                    help="assert the relay drops this client (run from outside ALLOW_NETS)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        selftest()
        return 0

    base = "http://%s:%d" % (args.host, args.port)
    print("smoke:", base, "model:", args.model)

    if args.expect_deny:
        ok, msg = check_expect_deny(args.host, args.port)
        print(("PASS " if ok else "FAIL ") + msg)
        return 0 if ok else 1

    ok, msg = check_health(base)
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        return 2
    ok, msg = check_completion(base, args.model)
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        return 1
    print("hint: deny path is checked from a peer outside ALLOW_NETS: "
          "python3 smoke_test.py --host %s --expect-deny" % args.host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
