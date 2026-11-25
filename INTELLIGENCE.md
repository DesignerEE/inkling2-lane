# INTELLIGENCE.md — how Inkling 2 Mini scores on the intelligence indices

Everything in this file is **third-party evaluation data**, collected from
public sources on 2026-11-25. Nothing here was produced by this repo's bench —
our own lane measurements (tok/s, prefill, VRAM) live in
[`results/`](results/). The distinction matters: the numbers below say how
*smart* the model is; the numbers in `results/` say how *fast this lane serves
it*. Vendor-reported scores are marked; the Artificial Analysis index is an
independent evaluation.

Snapshot dates: Artificial Analysis leaderboard observed **2026-11-20**;
articles gathered 2026-11-21/22. Scores move as evaluators re-run; check the
sources below for the live values.

## Artificial Analysis Intelligence Index v5.0.1

The headline comparative metric. AA's index equally weights knowledge work,
coding, science, and general tasks ([methodology](https://artificialanalysis.ai/methodology/intelligence-benchmarking)).

| model | AA Intelligence Index v5.0.1 | notes |
|---|---|---|
| **Inkling 2 Mini** | **20.1** | 26.4B total / 3.4B active (5.4B with loops), ~20 GB |
| Qwen3.8-27B (xhigh) | 20.1 | dense 27B — the closest competitor, exact tie |
| Nanbeige4.3-33B | 20 | tie at displayed precision |
| Inkling 2 Small | 31 | same family, 594B / 17B — Mini is 11 points below |
| MiMo V2.6 Pro | 30 | larger open-weight class |
| Kimi K3.1 Pro | 46 | larger open-weight class |
| Claude Fable 5.2 | 65 | frontier, for scale |
| GPT-6.2 Astra | 62 | frontier, for scale |
| Gemini 4 Neon | 61 | frontier, for scale |
| Muse Glimmer | 6 | same-size class |
| Google Gemma 4 31B (reasoning) | 4 | same-size class |

Reading: Mini does not beat its weight class on raw intelligence — it *ties*
the strongest dense peer (Qwen3.8-27B) while using 3.4B active parameters
instead of 27B, and runs at a fraction of the cost and latency (below). AA's
small-model ranking places Nanbeige first and Mini second despite the equal
displayed score.

## Cost and speed per AA index task (hosted runs, first-party pricing)

The comparison that makes the tie interesting — same index score, very
different economics ([AA launch assessment](https://artificialanalysis.ai/articles/inkling-2-mini)):

| metric | Inkling 2 Mini | Qwen3.8-27B | Inkling 2 Small |
|---|---|---|---|
| cost per index task | $0.59 | $3.53 | $1.18 |
| minutes per index task | 9.0 | 38.2 | 21.2 |
| output speed | 280 tok/s | 53 tok/s | 118 tok/s |
| time to first answer token | 9.7 s | 144.1 s | 39.7 s |
| output tokens per index task | ~152 K | ~110 K | not compared |

- At the same index score Mini costs **~6x less** and finishes **~4x faster**
  per task than Qwen3.8-27B, on roughly **2.8x less compute**
  ([VentureBeat](https://venturebeat.com/technology/thinking-machines-wows-with-inkling-2-mini-looped-transformer-model-that-runs-locally-on-laptops)).
- Honesty note: Mini reaches that score with **~38% more output tokens**
  (152 K vs 110 K per task) — its per-token speed, not token frugality, drives
  the wall-clock win.
- AA's hosted timings use the evaluator's own providers at Thinking Machines'
  API pricing ($0.15 in / $0.50 out per 1M); on this lane the marginal cost
  per token is zero, which is a different (better) economics than the table.
- One secondary source ([eesel](https://www.eesel.ai/blog/inkling-2-mini))
  lists 34.5 min/task for Qwen; the AA assessment and most coverage say 38.2.
  We report 38.2.

## Other published benchmarks

Vendor-reported (Thinking Machines model card) unless marked independent.
Column "peer" = Qwen3.8-27B, the closest competitor.

| benchmark | Inkling 2 Mini | peer | nature |
|---|---|---|---|
| DeepSWE v1.1 | 48.2% | 42.2% | vendor-reported |
| SWE-bench Verified (bash only) | 79.2% | 77.8% | vendor-reported |
| SWE-bench Pro v2 (Hard) | 77.9% | 73.8% | vendor-reported |
| Terminal Bench v2.1 | 71.6% | 73.0% | vendor-reported |
| MCP Atlas (tool use) | 82.7% | 77.3% | vendor-reported |
| LongBench v2 | 66.9 | 52.3 | vendor-reported |
| ScreenSpot Pro | 76.5 | 57.6 | vendor-reported |
| MMMU Pro | 74.9 | 76.3 | vendor-reported |
| AutomationBench v1.0.6 | 41.8% | 48.2% | vendor-reported |
| Vals Index v2.2 | 46.5% | not listed | independent (Vals AI) |
| ARC-AGI-2 | 49.3% | not listed | independent (ARC Prize) |
| Intelligence per watt (DGX Spark) | 0.703 | 0.430 (Qwen3.6-35B-A3B) | independent (Stanford run, reported by NewsCrawler) |

Caveats on the vendor table:

- SWE-bench Verified 79.2 vs 77.8 is **within single-run noise** (95% CI
  roughly ±3.5 pp at n≈500). Treat it as a tie, not a lead. The gaps on
  DeepSWE, MCP Atlas, LongBench v2, and ScreenSpot Pro are wider than that
  noise band.
- All vendor numbers are measured on the **full-precision reference model**,
  not on the quantized (NVFP4/MXFP8) checkpoint this lane serves.

## Where it trails (published caveats)

- **Factual recall and hallucination.** Non-hallucination rate 63.4% vs 71.4%
  (Qwen3.8-27B); AA-Omniscience -8.6 vs -6.4. The model card itself warns it
  "is more likely than larger models to state incorrect information with
  confidence."
- **Multi-turn and multi-constraint work.** MultiChallenge 50.0 (peer ahead);
  weaker on complex multi-condition instructions.
- **AutomationBench** 41.8% vs 48.2%.
- **Against its own family:** 11 AA index points below Inkling 2 Small (20.1
  vs 31); the card calls Mini "less capable than Small across most of our
  evaluations".

## Provenance and caveats for this repo

- This lane serves the **abliterated** checkpoint
  (satellitedown/Inkling-2-Mini-abliterated-ingine), which removes refusals
  and may behave differently from the base model the evaluators scored.
- AA scores carry one decimal where the leaderboard displays rounded values
  (20 shown as 20.1 in AA's model listings); the tie with Qwen3.8-27B holds at
  both precisions.
- Where this model sits: **top of the compact open-weight class on agentic
  and coding evaluations at frontier-adjacent cost efficiency**, not a
  frontier-reasoning replacement. AA 20.1 vs Claude Fable 5.2's 65 is the
  honest distance.

## Sources

- AA leaderboard: https://artificialanalysis.ai/leaderboards/models
- AA launch assessment: https://artificialanalysis.ai/articles/inkling-2-mini
- AA model pages: https://artificialanalysis.ai/models/inkling-2-mini
- Model card (vendor table): https://huggingface.co/thinkingmachines/Inkling-2-Mini
- Kingy comparison + AA/Val snapshot: https://kingy.ai/blog/inkling-2-mini/
- eesel Mini vs Small vs Qwen table: https://www.eesel.ai/blog/inkling-2-mini
- BenchLeader launch measurements: https://www.benchleader.com/models/inkling-2-mini
- VentureBeat economics: https://venturebeat.com/technology/thinking-machines-wows-with-inkling-2-mini-looped-transformer-model-that-runs-locally-on-laptops
- OpenRouter AA breakdown (Finance 35.3 / Strategy & Ops 35.2 / Legal 31.0 / Engineering 27.6 / Economics 33.0): https://openrouter.ai/thinkingmachines/inkling-2-mini
