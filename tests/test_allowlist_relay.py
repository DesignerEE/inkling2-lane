#!/usr/bin/env python3
"""Black-box tests for allowlist_relay.py (stdlib only, loopback only, no GPU).

Run: python3 -m unittest discover -s tests -v

Covered: default allowlist (loopback), explicit CIDR lists, DENY path (close +
log + upstream never contacted), SSE-style incremental passthrough, upstream
failure, fail-closed on invalid or empty ALLOW_NETS. The relay is exercised as
a subprocess because it runs its server at import time.
"""
import os
import socket
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RELAY = REPO / "allowlist_relay.py"
T = 8.0


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Upstream(threading.Thread):
    """Scripted TCP server standing in for ingine-serve."""

    def __init__(self, chunks, delay=0.0):
        super().__init__(daemon=True)
        self.chunks = chunks
        self.delay = delay
        self.received = b""
        self.port = free_port()
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", self.port))
        self.sock.listen(4)
        self.start()

    def run(self):
        try:
            self.sock.settimeout(T)
            conn, _ = self.sock.accept()
        except OSError:
            return
        conn.settimeout(T)
        try:
            self.received = conn.recv(65536)
            for c in self.chunks:
                conn.sendall(c)
                if self.delay:
                    time.sleep(self.delay)
        except OSError:
            pass
        finally:
            try:
                conn.shutdown(socket.SHUT_WR)
            except OSError:
                pass
            time.sleep(0.2)
            conn.close()

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


class Relay:
    """allowlist_relay.py subprocess with captured stderr lines."""

    def __init__(self, allow_nets=None, upstream_port=None):
        self.port = free_port()
        env = dict(os.environ)
        env["LISTEN_PORT"] = str(self.port)
        env["UPSTREAM_PORT"] = str(upstream_port if upstream_port else free_port())
        if allow_nets is None:
            env.pop("ALLOW_NETS", None)
        else:
            env["ALLOW_NETS"] = allow_nets
        self.lines = []
        self._banner = threading.Event()
        self.proc = subprocess.Popen(
            [sys.executable, str(RELAY)], env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        self._t = threading.Thread(target=self._pump, daemon=True)
        self._t.start()

    def _pump(self):
        for line in self.proc.stderr:
            self.lines.append(line.rstrip("\n"))
            if "allowlist relay" in line:
                self._banner.set()

    def wait_banner(self, timeout=T):
        if not self._banner.wait(timeout):
            raise RuntimeError("relay did not start: %r" % self.lines[-5:])

    def wait_exit(self, timeout=T):
        return self.proc.wait(timeout=timeout)

    def stderr_text(self):
        return "\n".join(self.lines)

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        if self.proc.stderr:
            self.proc.stderr.close()


def connect(port):
    s = socket.create_connection(("127.0.0.1", port), timeout=T)
    s.settimeout(T)
    return s


def recv_all(sock, limit=1 << 20):
    out = b""
    try:
        while len(out) < limit:
            data = sock.recv(65536)
            if not data:
                break
            out += data
    except (socket.timeout, OSError):
        pass
    return out


class TestRelay(unittest.TestCase):
    def tearDown(self):
        for name in ("relay", "up"):
            obj = getattr(self, name, None)
            if obj is not None:
                obj.close() if isinstance(obj, Upstream) else obj.stop()
                setattr(self, name, None)

    def test_default_allowlist_passes_bytes_loopback(self):
        self.up = Upstream([b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello"])
        self.relay = Relay(upstream_port=self.up.port)
        self.relay.wait_banner()
        with connect(self.relay.port) as s:
            s.sendall(b"GET /health HTTP/1.1\r\nHost: x\r\n\r\n")
            got = recv_all(s)
        self.assertEqual(got, b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello")
        self.assertTrue(self.up.received.startswith(b"GET /health"))

    def test_cidr_list_parses_and_allows(self):
        self.up = Upstream([b"ok"])
        self.relay = Relay(allow_nets=" 127.0.0.0/8 , 192.168.1.0/24 ",
                           upstream_port=self.up.port)
        self.relay.wait_banner()
        self.assertIn("127.0.0.0/8", self.relay.stderr_text())
        self.assertIn("192.168.1.0/24", self.relay.stderr_text())
        with connect(self.relay.port) as s:
            s.sendall(b"ping")
            self.assertEqual(recv_all(s), b"ok")

    def test_deny_unlisted_peer_closes_and_logs(self):
        self.up = Upstream([b"should-not-arrive"])
        self.relay = Relay(allow_nets="10.0.0.0/8", upstream_port=self.up.port)
        self.relay.wait_banner()
        with connect(self.relay.port) as s:
            s.sendall(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
            got = recv_all(s)
        self.assertEqual(got, b"")
        self.assertIn("DENY 127.0.0.1", self.relay.stderr_text())
        time.sleep(0.3)
        self.assertEqual(self.up.received, b"", "denied peer must never reach upstream")

    def test_empty_allowlist_denies_everyone(self):
        self.up = Upstream([b"x"])
        self.relay = Relay(allow_nets="", upstream_port=self.up.port)
        self.relay.wait_banner()
        with connect(self.relay.port) as s:
            s.sendall(b"hi")
            self.assertEqual(recv_all(s), b"")
        self.assertIn("DENY 127.0.0.1", self.relay.stderr_text())

    def test_sse_chunks_pass_through_incrementally(self):
        self.up = Upstream(
            [b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n\r\ndata: one\n\n",
             b"data: two\n\n"],
            delay=0.5)
        self.relay = Relay(upstream_port=self.up.port)
        self.relay.wait_banner()
        with connect(self.relay.port) as s:
            s.sendall(b"GET /v1/stream HTTP/1.1\r\nHost: x\r\n\r\n")
            first = s.recv(65536)
            self.assertIn(b"data: one", first)
            self.assertNotIn(b"two", first, "first chunk must arrive before the second is sent")
            rest = recv_all(s)
        self.assertIn(b"data: two", rest)

    def test_upstream_fail_closes_gracefully(self):
        self.relay = Relay(upstream_port=free_port())  # nothing listening there
        self.relay.wait_banner()
        with connect(self.relay.port) as s:
            s.sendall(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
            self.assertEqual(recv_all(s), b"")
        self.assertIn("UPSTREAM-FAIL", self.relay.stderr_text())

    def test_invalid_allow_nets_fails_closed(self):
        self.relay = Relay(allow_nets="garbage")
        rc = self.relay.wait_exit()
        self.assertNotEqual(rc, 0, "invalid ALLOW_NETS must refuse to start")


if __name__ == "__main__":
    unittest.main()
