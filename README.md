```text
+============================================================================+
|   _  _  _  _  __ _     _  _  _   ___  ___      _      _    _  _  ___       |
|  | || \| || |/ /| |   | || \| | / __||_  )    | |    /_\  | \| || __|      |
|  | || .` || ' < | |__ | || .` || (_ | / / --- | |__ / _ \ | .` || _|       |
|  |_||_|\_||_|\_\|____||_||_|\_| \___|/___|    |____/_/ \_\|_|\_||___|      |
+=== inkling2-lane :: Inkling 2 Mini on 1x RTX 5090 32 GB ===================+
```

[![test](https://github.com/DesignerEE/inkling2-lane/actions/workflows/test.yml/badge.svg)](https://github.com/DesignerEE/inkling2-lane/actions/workflows/test.yml)

**A production lane for local agentic coding: Inkling 2 Mini on 1x RTX 5090 32 GB.**

Serve a 26.4B-parameter coding model from one GPU on your desk, wire it into
**Kimi Code** or **Claude Code**, and keep every token inside your LAN.
No cloud in the path, no per-token bill, and the engine never touches the
network. Measured on 2026-11-22:

```text
+============================================================================+
| ONE GPU, ONE LAN :: measured 2026-11-22                                    |
+----------------------------------------------------------------------------+
| decode   320.9-322.1 tok/s plain      384.2-645.8 tok/s with DSpark        |
| prefill  8551 tok/s                   needle found at 142K context         |
| VRAM     23.8 / 32 GB at start        2.0 s agentic task (Claude Code)     |
| control  deterministic by seed        256K context in the client config    |
+============================================================================+
```

[Watch the 2-minute demo](https://github.com/DesignerEE/inkling2-lane/releases/download/v1.0/inkling2-demo-v01.mp4)
to see the lane, the relay, and the numbers above in motion.

This repository contains the **deployment layer only** (launcher, LAN allowlist
relay, client config block, acceptance bench); the engine and weights are
third-party and are **not** included here.

## Why this matters

- **Agentic coding without the cloud.** Kimi Code and Claude Code run against
  this lane end to end. A measured agentic tool task (create a file, run it,
  report the output) finishes in 2.0 seconds, entirely on your own hardware.
- **Zero marginal cost per token.** After the GPU, every token is free. For
  agent loops that burn thousands of tokens per task, that changes the economics
  of how often you can afford to let an agent work.
- **Safe by default.** The engine listens on loopback only. The allowlist relay
  is the single network-facing piece: it accepts TCP only from the networks you
  list, drops everyone else, and logs each denial. The pattern works for any
  OpenAI-compatible stack, not just this engine.
- **A recipe, not just code.** Launcher, relay, client configs, and an
  acceptance bench that measures the lane instead of trusting a README. Every
  number above comes from that bench.

## Who this is for

- Teams and homelabs that want an OpenAI-compatible coding endpoint without
  sending the codebase to an external API.
- Builders wiring agents (Kimi Code, Claude Code, custom OpenAI clients) to
  local hardware over a LAN.
- Anyone with Blackwell hardware who wants a measured, reproducible starting
  point instead of a weekend of flags.

## How it compares

- **Against the intelligence indices.** Artificial Analysis Intelligence
  Index v5.0.1: **20.1** — an exact tie with the dense Qwen3.8-27B, at 3.4B
  active parameters and ~6x lower cost / ~4x faster per index task. Full
  comparative scorecard (index standings, cost per task, where it trails, and
  sources): [`INTELLIGENCE.md`](INTELLIGENCE.md).
- **Cloud coding APIs.** They buy frontier-model quality; this lane buys data
  locality and a zero token bill on hardware you already own. The model is
  26.4B total / 3.4B active: fast and capable for everyday agentic work, not a
  frontier-reasoning replacement.
- **Rolling your own server.** This checkpoint is published in ingine's
  NVFP4/MXFP8 format for its runtime, so llama.cpp or vLLM do not pick it up as
  a generic model file. This repo is the production layer around that stack:
  launch flags, LAN exposure control, client configs, and an acceptance bench.
- **Other local engines.** ingine ships sm_120a kernels for this model class.
  The recipe pins exactly what to run, and the bench shows what it measures.

## Architecture & why a relay

```text
+----------------+       +--------------------+           +------------------+
| Kimi Code /    |  LAN  | allowlist relay    | 127.0.0.1 | ingine-serve     |
| OpenAI client  |------>| 0.0.0.0:8003       |---------->| 127.0.0.1:8004   |
| (inkling-lane) |  SSE  | ALLOW_NETS filter  | loopback  | NVFP4 / MXFP8    |
+----------------+       +---------+----------+           +--------+---------+
                                   |                               |
                                   v (not in ALLOW_NETS)           v
                            [ DENY <ip> ]                 +------------------+
                            conn dropped                  | RTX 5090 32 GB   |
                                                          | sm_120a / CUDA   |
                                                          +------------------+
```

The engine listens on loopback (`127.0.0.1:8004`). The relay is the only
network-facing piece: it accepts TCP only from `ALLOW_NETS` peers, logs
`DENY <ip>` for everyone else, passes streams through unchanged so SSE works,
and keeps the engine unreachable from the outside world.

## What is in this repo

- `start_ingine.sh` -- starts `ingine-serve` on `127.0.0.1:8004` with the
  production flags, then starts the relay. Idempotent.
- `start_relay.sh` + `allowlist_relay.py` -- plain TCP relay
  `0.0.0.0:8003 -> 127.0.0.1:8004` with a peer-IP allowlist (env `ALLOW_NETS`,
  default loopback only). Streams pass through unchanged, so SSE works.
- `config-snippet.toml` -- the Kimi Code provider (`inkling-lane`) + model block.
- `bench_ingine_5090.py` -- the acceptance bench (`plain` / `spec` / `queue`).
- `results/` -- archived bench output: the receipts behind the measured numbers.
- `UPSTREAM.md` -- pinned upstream revisions and toolchain for the verified run.
- `smoke_test.py` -- one-command lane check: health, one real completion,
  optional deny-path check (`--expect-deny`, run from outside `ALLOW_NETS`).
- `tests/` -- stdlib-only relay tests (allow, DENY, SSE passthrough,
  fail-closed); run in CI on every push.

## Quick start

1. Install the engine and download the weights with the upstream installer
   (`bash setup.sh` -> option 1). The model lands in the installer's model
   directory (see the installer output).
2. Start the lane:

   ```bash
   INGINE_GPU=0 ALLOW_NETS=127.0.0.0/8,192.168.1.0/24 bash start_ingine.sh
   ```

   `INGINE_GPU` selects the card (index or `GPU-<uuid>`; default `0`). The
   engine binds loopback only; the relay exposes it to the networks you list.
3. Sanity-check the lane: `python3 smoke_test.py` (health + one real
   completion), then measure it: `python3 bench_ingine_5090.py spec`.
4. Merge `config-snippet.toml` into `~/.kimi-code/config.toml`, point
   `base_url` at your box, reload the client.

## Upstream stack & looped core

- Engine: [`satellitedown/inkling-2-mini-abliterated-ingine`](https://github.com/satellitedown/inkling-2-mini-abliterated-ingine)
  -- a C++/CUDA inference engine for `sm_120a` (Blackwell), shipped with an
  installer that pins the CUDA 13.4 toolkit and downloads the checkpoint.
- Weights: [`satellitedown/Inkling-2-Mini-abliterated-ingine`](https://huggingface.co/satellitedown/Inkling-2-Mini-abliterated-ingine)
  on Hugging Face -- 19 GB NVFP4/MXFP8 safetensors plus the 636 MB DSpark drafter.
- Base model: `thinkingmachines/Inkling-2-Mini` -- 26.4B total / 3.4B active,
  looped core (layers 6-17) executed 3 times per token.

```text
+============================================================================+
| LOOPED CORE :: thinkingmachines/Inkling-2-Mini (26.4B total / 3.4B active) |
+============================================================================+
   tokens                                                         logits
     |                                                              ^
     v                                                              |
+----------+  prelude   +--- pass 1 -->+-------------+  after  +----------+
| Layers   |  output    |              | Layers 6-17 |  3x     | Layers   |
| 0 - 5    |------------+--- pass 2 -->| looped core |-------->| 18 - 23  |
| prelude  |            |              | 3x / token  |         | exit     |
+----------+            +--- pass 3 -->+-------------+         +----------+
                        ^
                        +-- each pass starts from prelude output (not chained)
```

## Measured on RTX 5090 32 GB (2026-11-22)

Raw bench output behind these numbers: [`results/`](results/).
Pinned upstream revisions for the verified run: [`UPSTREAM.md`](UPSTREAM.md).

```text
+============================================================================+
| DECODE SPEED :: RTX 5090 32 GB (tok/s, verified 2026-11-22)                |
+----------------------------------------------------------------------------+
| plain  code  | ================                   | 320.9 tok/s            |
| plain  prose | ================                   | 321.2 tok/s            |
| plain  copy  | ================                   | 322.1 tok/s            |
| -------------+------------------------------------+----------------------- |
| spec*  code  | ###########################        | 540.8 tok/s            |
| spec*  prose | ###################                | 384.2 tok/s            |
| spec*  copy  | ################################   | 645.8 tok/s            |
|                0         200       400       600  700                      |
| *spec = DSpark drafter, threshold 0.8                                      |
+----------------------------------------------------------------------------+
| VRAM METER   :: RTX 5090 32 GB (1 char = 1 GB, : = partial GB)             |
| at start     [#######################:........]  23.8 / 32 GB              |
| after 142K   [##########################:.....]  26.5 / 32 GB              |
+============================================================================+
```

- Needle test at 142K: found; prefill `~8551 tok/s`.
- Deterministic by seed (byte-identical repeats).
- Thinking: by default reasoning goes to `reasoning_content`; send
  `chat_template_kwargs: {"enable_thinking": false}` for a clean `content`.

## Alternative client: Claude Code

```text
+------------+  Anthropic /v1/messages  +-------------------------+
| claude CLI |------------------------->| claude-code-proxy :3456 |
+------------+                          +------------+------------+
                                                     | OpenAI
             +----------+    +--------------------+  | /v1/chat/completions
             | RTX 5090 |<---| ingine-serve :8004 |<-+
             +----------+    +--------------------+
```

1. Clone https://github.com/1rgs/claude-code-proxy.git into `ccp`, copy
   `claude-code-proxy.env` to `ccp/.env`, and run `bash start_claude_proxy.sh`
   (both files are in this repo; the script applies a 2-line patch that maps
   Claude Code's default `opus` model name to the local model -- upstream maps
   only `haiku`/`sonnet`).
2. Set `ANTHROPIC_BASE_URL=http://127.0.0.1:3456`,
   `ANTHROPIC_AUTH_TOKEN=sk-local`, and
   `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` (no Anthropic API key needed).

```text
+============================================================================+
| CLAUDE CODE :: end-to-end via proxy on RTX 5090 (2026-11-22)               |
+----------------------------------------------------------------------------+
| exact-reply prompt                                             | 1.3 s     |
| agentic tool task (create hello.py, run it, report the output) | 2.0 s     |
+----------------------------------------------------------------------------+
| workload  | ttft | api  | out tok | t/s | notes                          |
| code      | 1.1s | 5.3s |    1087 | 204 | 9 agentic turns (code+tests)   |
| prose 30w | 1.4s | 5.8s |     547 |  94 | 300-word essay                 |
| copy      | 0.4s | 0.4s |      68 | 197 | verbatim echo                  |
| tool rnd  | 1.1s | 2.2s |      61 |  -- | 5 turns, create+run file       |
+----------------------------------------------------------------------------+
| t/s = result-text tokens / api seconds; thinking tokens are not counted   |
| by the proxy stream, so these are lower bounds of the true decode rate.   |
+============================================================================+
```

- Under `root`, Claude Code refuses `--dangerously-skip-permissions` -- use
  `--allowedTools "Bash Read Write Edit"` instead.
- The model thinks by default (reasoning goes to `reasoning_content`), so
  budget `max_tokens` accordingly.
- Every model name (`opus`/`sonnet`/`haiku`) resolves to the local model.

## Caveats

- Kernels are built for `sm_120a`: Blackwell compute capability 12.0 only
  (RTX 5090 validated; PRO 6000/5000/4500 are untested upstream).
- One stream per GPU: 2 concurrent requests OK, 6 -> 5 served + one HTTP 503.
- Upstream terms apply to the engine and the weights -- see their repositories.

## License

Apache-2.0 for the files in this repository (see `LICENSE`). The engine and
the weights keep their own upstream licenses.
