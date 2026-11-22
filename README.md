```text
+============================================================================+
|   _  _  _  _  __ _     _  _  _   ___  ___      _      _    _  _  ___       |
|  | || \| || |/ /| |   | || \| | / __||_  )    | |    /_\  | \| || __|      |
|  | || .` || ' < | |__ | || .` || (_ | / / --- | |__ / _ \ | .` || _|       |
|  |_||_|\_||_|\_\|____||_||_|\_| \___|/___|    |____/_/ \_\|_|\_||___|      |
+=== inkling2-lane :: Inkling 2 Mini on 1x RTX 5090 32 GB ===================+
```

A production recipe for serving **Inkling 2 Mini** on a single
**RTX 5090 32 GB** and wiring it into **Kimi Code** (provider `inkling-lane`,
or any OpenAI-compatible client) -- exactly as we run it, verified 2026-11-22.
This repository contains the **deployment layer only** (launcher, LAN allowlist
relay, client config block, acceptance bench); the engine and weights are
third-party and are **not** included here.

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
3. Sanity-check: `python3 bench_ingine_5090.py spec`.
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

## Caveats

- Kernels are built for `sm_120a`: Blackwell compute capability 12.0 only
  (RTX 5090 validated; PRO 6000/5000/4500 are untested upstream).
- One stream per GPU: 2 concurrent requests OK, 6 -> 5 served + one HTTP 503.
- Upstream terms apply to the engine and the weights -- see their repositories.

## License

Apache-2.0 for the files in this repository (see `LICENSE`). The engine and
the weights keep their own upstream licenses.
