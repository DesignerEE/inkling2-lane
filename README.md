# inkling2-lane

A production recipe for serving **Inkling 2 Mini (abliterated)** on a single
**RTX 5090 32 GB** and wiring it into **Kimi Code** (or any OpenAI-compatible
client) — exactly as we run it, verified 2026-11-22.

This repository contains the **deployment layer only**: the launcher, a LAN
allowlist relay, the client config block, and the acceptance bench. The engine
and the weights are third-party and are **not** included here:

- Engine: [`satellitedown/inkling-2-mini-abliterated-ingine`](https://github.com/satellitedown/inkling-2-mini-abliterated-ingine)
  — a C++/CUDA inference engine for `sm_120a` (Blackwell), shipped with an
  installer that pins the CUDA 13.4 toolkit and downloads the checkpoint.
- Weights: [`satellitedown/Inkling-2-Mini-abliterated-ingine`](https://huggingface.co/satellitedown/Inkling-2-Mini-abliterated-ingine)
  on Hugging Face — 19 GB NVFP4/MXFP8 safetensors plus the 636 MB DSpark drafter.
- Base model: `thinkingmachines/Inkling-2-Mini` — 26.4B total / 3.4B active,
  looped core (layers 6–17) executed 3 times per token.

## What is in this repo

- `start_ingine.sh` — starts `ingine-serve` on `127.0.0.1:8004` with the
  production flags, then starts the relay. Idempotent.
- `start_relay.sh` + `allowlist_relay.py` — a plain TCP relay
  `0.0.0.0:8003 -> 127.0.0.1:8004` with a peer-IP allowlist (env `ALLOW_NETS`,
  default loopback only). Streams pass through unchanged, so SSE works.
- `config-snippet.toml` — the Kimi Code provider + model block.
- `bench_ingine_5090.py` — the acceptance bench (`plain` / `spec` / `queue`).

## Quick start

1. Install the engine and download the weights with the upstream installer
   (`bash setup.sh` → option 1). The model lands in `~/inkling-abliterated-ingine`.
2. Start the lane:

   ```bash
   INGINE_GPU=0 ALLOW_NETS=127.0.0.0/8,192.168.1.0/24 bash start_ingine.sh
   ```

   `INGINE_GPU` selects the card (index or `GPU-<uuid>`; default `0`). The
   engine binds loopback only; the relay exposes it to the networks you list.
3. Sanity-check: `python3 bench_ingine_5090.py spec`.
4. Merge `config-snippet.toml` into `~/.kimi-code/config.toml`, point
   `base_url` at your box, reload the client.

## Why a relay

The engine listens on loopback. The relay is the only network-facing piece:
it accepts TCP only from `ALLOW_NETS` peers, logs `DENY <ip>` for everyone
else, and keeps the engine unreachable from the outside world.

## Measured on RTX 5090 32 GB (2026-11-22)

- plain: code 320.9 / prose 321.2 / copy 322.1 tok/s
- spec (DSpark, threshold 0.8): code 540.8 / prose 384.2 / copy 645.8 tok/s
- VRAM: 23.8 GB at start; 26.5 GB after a 142K-token prompt
- needle test at 142K: found; prefill ~8551 tok/s
- deterministic by seed (byte-identical repeats)
- thinking: by default reasoning goes to `reasoning_content`; send
  `chat_template_kwargs: {"enable_thinking": false}` for a clean `content`

## Caveats

- Kernels are built for `sm_120a`: Blackwell compute capability 12.0 only
  (RTX 5090 validated; PRO 6000/5000/4500 are untested upstream).
- One stream per GPU: 2 concurrent requests OK, 6 → 5 served + one HTTP 503.
- Pass the ablation sidecar explicitly (`--ablation ...`); without it the
  engine serves the unabliterated original.
- Upstream terms apply to the engine and the weights — see their repositories.

## License

Apache-2.0 for the files in this repository (see `LICENSE`). The engine and
the weights keep their own upstream licenses.
