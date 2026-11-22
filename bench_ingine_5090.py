#!/usr/bin/env python3
"""Acceptance bench for ingine on RTX 5090. Usage: python3 bench_ingine_5090.py {plain|spec|queue}"""
import json, sys, time, urllib.request, statistics, subprocess, os

PORT = 8003
URL = f"http://127.0.0.1:{PORT}/v1/chat/completions"
MODEL = "inkling-2-mini-abliterated"
WORKLOADS = {
    "code": "Complete this Python module: implement an LRU cache class with get/put/size methods, O(1) operations, type hints and docstrings. Then write unit tests.",
    "prose": "Write 300 words about looped transformer architectures.",
    "copy": "Repeat the following text verbatim, then stop: The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs. How vexingly quick daft zebras jump. Sphinx of black quartz, judge my vow. Two driven jocks help fax my big quiz. The five boxing wizards jump quickly.",
}

def gen(prompt, n=512):
    body = json.dumps({"model": MODEL, "stream": False, "temperature": 0,
                       "max_tokens": n, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    d = json.loads(urllib.request.urlopen(req, timeout=900).read())
    wall = time.time() - t0
    usage = d.get("usage", {})
    ct = usage.get("completion_tokens", 0)
    return ct, wall

def health():
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=3)
        return True
    except Exception:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/v1/models", timeout=3)
            return True
        except Exception:
            return False

def vram():
    out = subprocess.run("nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits",
                         shell=True, capture_output=True, text=True).stdout.strip()
    return [l for l in out.splitlines() if l]

def main(mode):
    if not health():
        print("SERVER DOWN"); sys.exit(2)
    print("VRAM:", vram())
    results = {}
    for name, prompt in WORKLOADS.items():
        gen(prompt, 200); gen(prompt, 200)   # warmup discarded
        tps = []
        for r in range(3):
            ct, wall = gen(prompt, 512)
            tps.append(ct / wall)
        results[name] = {"median": round(statistics.median(tps), 1), "runs": [round(x, 1) for x in tps]}
        print(f"{name}: {results[name]['median']} t/s  {results[name]['runs']}", flush=True)
    if mode == "queue":
        import concurrent.futures as cf
        def one(_):
            t0 = time.time()
            try:
                ct, wall = gen(WORKLOADS["code"], 128)
                return ("ok", round(ct/wall, 1), round(time.time()-t0, 1))
            except Exception as e:
                return ("err", str(e)[:40], round(time.time()-t0, 1))
        for n in (2, 6):
            with cf.ThreadPoolExecutor(n) as ex:
                print(f"queue {n}:", list(ex.map(one, range(n))))
        return
    out = os.path.expanduser(f"~/ingine-accept-{mode}.json")
    json.dump(results, open(out, "w"), indent=1)
    print("saved", out)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "plain")
