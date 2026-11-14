# E9 — frontier judge (Claude Sonnet 5.5): D-entry draft for the authors' decision

**Status: NOT APPROVED. Nothing has been called, no key has been handled, and no code for it exists yet.** If approved,
E9 is a **deviation from the study's zero-API-cost rule** (D-21) and is labelled as such everywhere; it is exploratory,
never replaces M1 and never feeds back into any committed result. Rendered by `scripts/paper/build_numbers.py`.

## Proposed D-entry text (to be committed, with hashes, before any call)

> **D-E9 (draft).** *Deviation from the zero-API-cost rule (D-21), authors' decision of <date>.* Exploratory frontier
> judge: **Claude Sonnet 5.5** (`claude-sonnet-5-5`), arms **J1 and DEB** at **S1**, D1-test, the
> {{fcost:scored_instances}} scored instances (D-70 set), **one replicate**, through the **Message Batches API**. Prompts:
> the frozen set `local_m1b` byte for byte; evidence packages identical to M1's; the JSON output schema enforced with
> structured outputs. **Hard spend cap: US$ 8.00** for the whole experiment (below). Hypotheses fixed now, before any
> call: **H9-1** ΔF1(DEB − J1) > 0; **H9-2** MCC(DEB) > 0 (95% bug-level CI excludes 0); Sonnet − M1 per arm reported,
> not tested. Exploratory; no multiplicity family with M1's tests. Deviations from the frozen local protocol (below)
> are listed in every output.

## Settings, confirmed from the official documentation

Source: Claude Sonnet 5.5 migration guide, `https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide`,
read on 2026-11-03.

| Setting | E9 value | Why |
|---|---|---|
| Thinking | `thinking: {"type": "between_tools"}` | `{"type": "disabled"}` returns a 400 on Sonnet 5.5; `between_tools` is the documented way to turn up-front thinking off, and without tools the response contains only text. M1 ran with thinking off. |
| Effort | `output_config.effort: "high"` | `between_tools` is accepted only at `low`, `medium` and `high`; `high` is the documented default. Fixed for the whole run. |
| Sampling | none sent | `temperature`, `top_p` and `top_k` return a 400 on Sonnet 5.5. **Deviation:** the frozen T = 0.7, top-p 1.0 cannot be applied; the model's default sampling is used. |
| Seeds | none | no per-call seed on the API. **Deviation:** samples are not seed-reproducible. |
| Output format | structured outputs (`output_config.format`, the frozen JSON schema) | forced `tool_choice` (`any`/`tool`) returns a 400; structured outputs enforce the schema without tools. **Deviation:** local runs used Ollama's `format`. |
| Max output | 512 tokens | as frozen. |
| Refusals | `stop_reason: "refusal"` scored INVALID (→ TF, primary policy), counted and reported | **no server-side fallback**: a fallback to another model would change the judge mid-run. |
| Batching | Message Batches API, 50% list price | DEB's calls depend on each other, so DEB runs as three batches in sequence (round-1 advocates, round-2 rebuttals, adjudicator); J1 is one batch. |

## Cost and the hard cap

Measured tokens per instance (M1's tokenizer): J1 {{fcost:tokens_per_instance_measured_M1:J1:input@0}} in /
{{fcost:tokens_per_instance_measured_M1:J1:output@0}} out; DEB {{fcost:tokens_per_instance_measured_M1:DEB:input@0}} in /
{{fcost:tokens_per_instance_measured_M1:DEB:output@0}} out. At Sonnet 5.5's Batch API rates
({{fcost:models:claude-sonnet-5-5:price_batch_input@2}} / {{fcost:models:claude-sonnet-5-5:price_batch_output@2}} USD per million
tokens, read from {{fcost:price_source:url}} on {{fcost:price_source:accessed}}), one replicate of J1 + DEB is estimated
at **US$ {{fcost:models:claude-sonnet-5-5:usd_one_replicate_batch@2}}** (standard rate:
US$ {{fcost:models:claude-sonnet-5-5:usd_one_replicate@2}}). The cap leaves room for a different tokenizer and longer
outputs; thinking is off, so no thinking tokens are expected.

**Cap enforcement (three layers):**
1. *Pre-flight:* before each batch, its worst case (every request at its real input length, counted locally, plus the
   full 512 output tokens, at batch rates) is added to the spend so far; the batch is not submitted if the total would
   exceed US$ 8.00.
2. *Between batches:* actual spend is recomputed from each batch's returned `usage`; the next batch starts only if
   actual + its worst case ≤ cap.
3. *Account level (the authors set it, not the code):* a monthly spend limit on the Anthropic Console workspace used
   for E9, set at or below the cap, so no code fault can exceed it.

## Logging (as for the local runs)

Every request and response goes to its own call log (`data/raw/llm_calls_frontier/claude-sonnet-5-5.jsonl`, never the
frozen one): request key, model, full messages and system prompt, thinking/effort/output_config, max_tokens; full
response content, `stop_reason`, `stop_details`, `usage` (input, output, cache tokens), the model string returned,
the message id, the batch id and custom_id, the computed cost, and the UTC time. Decisions are written in the
committed decision schema to `results/runs_frontier/E9_SONNET55_D1TEST/`, with `leakage_rejections.jsonl` from the
same guard (no package can leave the machine unchecked). The API key is set by the authors as `ANTHROPIC_API_KEY` in
their own shell; it is never written to a file, a log or the repository.

## What would still have to be built and tested (after approval, before any call)

- An Anthropic batch backend for the client (`src/triage/`), with the cap guard and the call log above, tested against
  fakes only (no network), including: cap refusal, refusal stop reason, malformed JSON, batch expiry, partial results.
- Scope entry (`configs/local_scope.json`) for E9 only; an experiment JSON; hashes of every new file in the D-entry.
- A dry run that builds every request and prints the pre-flight worst case, with no network call.

**Decision requested:** approve E9 as above (including the US$ 8.00 cap and the deviations), change it, or decline.
