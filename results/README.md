# results/ — raw acceptance bench output

Archived output of `bench_ingine_5090.py`, copied unchanged from the serving
box. These are the receipts behind every number in the README.

| file | mode | recorded |
|---|---|---|
| `ingine-accept-plain.json` | `plain` (no drafter) | 2026-11-22 10:24 (box local) |
| `ingine-accept-spec.json` | `spec` (DSpark drafter, threshold 0.8) | 2026-11-22 10:26 (box local) |

Each file maps a workload (`code`, `prose`, `copy`) to `median` tok/s and the
per-run values behind it (`runs`, 3 runs per workload). Workload prompts are
defined in `bench_ingine_5090.py`; each run is one `POST /v1/chat/completions`
with `temperature=0`, `max_tokens=512`, counted as completion tokens over wall
time, served through the relay on `127.0.0.1:8003`.

To re-run on a live lane:

```bash
python3 bench_ingine_5090.py plain   # writes ~/ingine-accept-plain.json
python3 bench_ingine_5090.py spec    # writes ~/ingine-accept-spec.json
```

Notes:

- `queue` mode (concurrency behavior: 2 concurrent OK, 6 -> 5 served + one
  HTTP 503) prints to stdout and does not write a JSON archive; that claim is
  recorded in the README narrative only.
- VRAM readings in the README (`23.8 GB` at start, `26.5 GB` after 142K) come
  from the same bench script's `nvidia-smi` sampling plus the needle run.
- Hardware and pinned upstream revisions for these runs: see
  [`UPSTREAM.md`](../UPSTREAM.md).
