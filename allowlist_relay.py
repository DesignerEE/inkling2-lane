#!/usr/bin/env python3
"""TCP relay with a peer-IP allowlist. Env: ALLOW_NETS (comma list), LISTEN_PORT, UPSTREAM."""
import asyncio, ipaddress, os, sys

ALLOW = [ipaddress.ip_network(n.strip()) for n in os.environ.get(
    "ALLOW_NETS", "127.0.0.0/8").split(",") if n.strip()]  # add your LAN, e.g. 192.168.1.0/24
LISTEN = ("0.0.0.0", int(os.environ.get("LISTEN_PORT", "8003")))
UPSTREAM = ("127.0.0.1", int(os.environ.get("UPSTREAM_PORT", "8004")))

async def pipe(r, w):
    try:
        while True:
            data = await r.read(65536)
            if not data:
                break
            w.write(data)
            await w.drain()
    except Exception:
        pass
    finally:
        try:
            w.close()
        except Exception:
            pass

async def handle(reader, writer):
    peer = writer.get_extra_info("peername")
    ip = peer[0] if peer else "?"
    try:
        ok = any(ipaddress.ip_address(ip) in net for net in ALLOW)
    except ValueError:
        ok = False
    if not ok:
        sys.stderr.write(f"DENY {ip}\n")
        writer.close()
        return
    try:
        ur, uw = await asyncio.open_connection(*UPSTREAM)
    except Exception as e:
        sys.stderr.write(f"UPSTREAM-FAIL {e}\n")
        writer.close()
        return
    await asyncio.gather(pipe(reader, uw), pipe(ur, writer))

async def main():
    srv = await asyncio.start_server(handle, *LISTEN, reuse_address=True)
    sys.stderr.write(f"allowlist relay {LISTEN} -> {UPSTREAM} allow={[str(n) for n in ALLOW]}\n")
    await srv.serve_forever()

asyncio.run(main())
