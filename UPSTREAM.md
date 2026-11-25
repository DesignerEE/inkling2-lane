# UPSTREAM.md — pinned revisions for the verified run (2026-11-22)

This repo is the deployment layer only. Everything below is third-party; this
file pins exactly what the verified numbers were produced with, so the results
in [`results/`](results/) stay reproducible after upstream moves on.

## Engine

- **Repo:** https://github.com/satellitedown/inkling-2-mini-abliterated-ingine
- **Deployed commit (used for all verified runs):**
  `306eaa8a90c9840f042a59d565f6dc4536bbb5ea` (2026-11-21)
- Upstream HEAD moved after verification: `556acc7cf427` (2026-11-22) pins the
  newer HF release `cea73d67cd0e`. Re-running `setup.sh --update` picks that up;
  to reproduce the verified run exactly, check out the deployed commit above.

## Weights

- **Repo:** https://huggingface.co/satellitedown/Inkling-2-Mini-abliterated-ingine
- **Pinned revision (as recorded by the engine's `runtime-manifest.json`):**
  `afd44de1d9cb5da68f1c251ca4f198e0517c72e0` (2026-11-21)
- The manifest carries per-file **sha256** for every artifact (~20.2 GB total:
  19 GB NVFP4/MXFP8 safetensors + 636 MB DSpark drafter + template/config).
  The installer re-downloads only when the pinned revision changes.
- Base model (reference): https://huggingface.co/thinkingmachines/Inkling-2-Mini
  (26.4B total / 3.4B active, looped core).

## Toolchain and hardware (observed on the serving box)

- **CUDA:** the installer builds against its own **private CUDA 13.4 toolkit**
  (`setup.sh`); a system `nvcc` is not required.
- **Driver requirement:** NVIDIA driver for CUDA 13, **580 or newer**.
  Observed during the verified run: **620.70.06**.
- **GPU:** NVIDIA GeForce **RTX 5090 32 GB**, selected with `INGINE_GPU=0`.
- **Platform:** Linux x86_64. Model download ≈ 20.2 GB, software ≈ 3 GB.

## Claude Code proxy (alternative client path)

- **Repo:** https://github.com/1rgs/claude-code-proxy
- **Not pinned:** the clone used for the Claude Code measurements was not
  retained on the box. Pin it at clone time (`git rev-parse HEAD`) if you need
  an exact reproduction of those numbers.

## How these pins were collected

Audit of the serving box on 2026-11-25: deployed engine clone `git log`, the
engine's `runtime-manifest.json` (weights revision + sha256 list), `nvidia-smi`,
and upstream commit history on GitHub / Hugging Face. Bench raw output from
2026-11-22: [`results/`](results/).
