# Session checklists — E6b, E6a, E8, E7a (D-82)

**Status: not approved. No model call until the authors write "approved" for the experiment in question.** Rendered by
`scripts/paper/build_numbers.py`; projected hours come from `results/planning/external_projection.json` (measured times,
duty factor {{proj:duty_factor@2}}). The frozen protocol is unchanged and M1 stays the confirmatory judge.

## Before the first session (after approval, CPU only, no model call)

- [ ] Approval recorded in DECISIONS as the D-82 outcome line for the experiment (who, date, which experiment).
- [ ] Build each experiment the D-76 way: own profile file (port, server env, log, call-log and session-log
      directories, never the frozen ones), experiment JSON, scope entry in `configs/local_scope.json`; tests against
      fakes only; hashes of every new file recorded in a D-entry **before** any model is loaded.
- [ ] E6b (purpose: a third model family for E8 and the family-affinity check, not a stronger judge): pull the
      candidates in the D-82 order, fixed in advance in the version-controlled decision log (authors' permission, 3 Nov), record digests and licences;
      MODEL_SELECTION_PROTOCOL Step 1 on
      synthetic probes only.
- [ ] Full test suite green; `logs/STOP` absent; `git status` clean; tag the commit (`pre-E6b`, `pre-E8`, …).

## Night 4 Nov — E6b (dev gate + D1-test) then E6a session 1

Projected: E6b {{proj:proposals:E6b_second_family_judge:gpu_h_total@1}} GPU-h (dev gate included), E6a session 1 about
half of {{proj:proposals:E6a_35b_complete:gpu_h_total@1}} GPU-h. Night box: {{proj:sessions_h:night:0@0}}–{{proj:sessions_h:night:1@0}} h.

**Start**
- [ ] `wsl --shutdown`; no other GPU or heavy CPU work; laptop on mains power, sleep disabled.
- [ ] Frozen server: `session_check --start` passes (Ollama {{frozen:runtime:version}}, frozen digests), then `session_check --end` (frozen session closed before any other server starts).
- [ ] E6b: start its own server/profile; Step 1 record; dev gate (J1/SC/DEB on the development pilot); G-a/G-b must pass, G-d is reported.
- [ ] Only if G-a/G-b pass: E6b J1 → SC → DEB on D1-test S1, one replicate, stopping rule armed (RAM check every 25 calls, latency median of last 50 > 3× feasibility median, crash/hang 900 s, time box).
- [ ] Then E6a session 1: stop the E6b server; start the 35b profile (D-76/D-78); run SC until the session cap (below the {{proj:proposals:E6a_35b_complete:calls_before_slowdown_measured}} calls measured before the D-78 slowdown).

**Stop**
- [ ] Every runner exited cleanly (`run_status.json`), or a STOP marker names the reason; no retry, no setting change.
- [ ] Stop the experiment servers; restart the frozen server; `session_check --start` passes; `--end`.
- [ ] Commit outputs (decisions, leakage rejections, call logs, session logs, outcome JSON); D-entry outcome line; PROGRESS row.

## Day 5 Nov — E8 then E6a session 2

E8 approved by the authors (3 Nov) **on condition** that E6b selects a judge and commits its D1-test run; if E6b
selects none, E8 is reported as not run, with the reason.

Projected: E8 {{proj:proposals:E8_three_llm_vote:gpu_h_total@1}} GPU-h; E6a session 2 the rest of
{{proj:proposals:E6a_35b_complete:gpu_h_total@1}} GPU-h. Day box: {{proj:sessions_h:day@0}} h.

**Start**
- [ ] As above (frozen check, then close); E8 needs the E6b judge selected and its D1-test run committed.
- [ ] E8: VOTE3/VOTE5 batched by model (one model loaded at a time: M1 batch, M2 batch, E6b batch); SC3 needs no call.
- [ ] E6a session 2: restart the 35b server fresh; finish SC; DEB for the instances the D-78 stop did not reach.

**Stop**
- [ ] As above; then run the committed analysis scripts (no new statistic), Holm within each experiment's family, label E6a exploratory.

## Night 6 Nov — E7a (optional; only if E6 and E8 are done by 7 Nov)

Projected: {{proj:proposals:E7a_second_generator:gpu_h_total@1}} GPU-h (generation + re-judging; execution on CPU in WSL,
run after generation, never during it).

**Start**
- [ ] Generator candidate (third family) selected on dev by D-22 before the session; frozen labelling and sampling code; WSL started only for the execution step.

**Stop**
- [ ] As above; dataset and sample built with the D-53/D-64 rules; M1 J1/SC/DEB judging; analysis with the committed scripts.

## Frontier judge — cost estimate only (nothing called)

The study's zero-API-cost rule stands; this is for the authors' decision. J1 + DEB on the {{fcost:scored_instances}}
scored D1-test instances, from the measured tokens per instance (J1 {{fcost:tokens_per_instance_measured_M1:J1:input@0}}
in / {{fcost:tokens_per_instance_measured_M1:J1:output@0}} out; DEB {{fcost:tokens_per_instance_measured_M1:DEB:input@0}}
in / {{fcost:tokens_per_instance_measured_M1:DEB:output@0}} out), at Anthropic's list prices read from
{{fcost:price_source:url}} on {{fcost:price_source:accessed}}:

| Model | $ / M in | $ / M out | 1 replicate | 3 replicates | 1 replicate, Batch API |
|---|---|---|---|---|---|
| Claude Sonnet 5.5 | {{fcost:models:claude-sonnet-5-5:price_input@2}} | {{fcost:models:claude-sonnet-5-5:price_output@2}} | ${{fcost:models:claude-sonnet-5-5:usd_one_replicate@2}} | ${{fcost:models:claude-sonnet-5-5:usd_three_replicates@2}} | ${{fcost:models:claude-sonnet-5-5:usd_one_replicate_batch@2}} |
| Claude Opus 5.5 | {{fcost:models:claude-opus-5-5:price_input@2}} | {{fcost:models:claude-opus-5-5:price_output@2}} | ${{fcost:models:claude-opus-5-5:usd_one_replicate@2}} | ${{fcost:models:claude-opus-5-5:usd_three_replicates@2}} | ${{fcost:models:claude-opus-5-5:usd_one_replicate_batch@2}} |
| Claude Fable 5.1 | {{fcost:models:claude-fable-5-1:price_input@2}} | {{fcost:models:claude-fable-5-1:price_output@2}} | ${{fcost:models:claude-fable-5-1:usd_one_replicate@2}} | ${{fcost:models:claude-fable-5-1:usd_three_replicates@2}} | ${{fcost:models:claude-fable-5-1:usd_one_replicate_batch@2}} |

Caveats: the token counts come from M1's tokenizer; thinking tokens are billed as output and are not included (they
cannot be fully disabled on Claude Opus 5.5 or Claude Sonnet 5.5), so treat these as lower bounds. Only Anthropic
models were priced, because only their pricing page was checked here; a non-Anthropic candidate needs its price read
from its provider's official page first. TODO (authors): decide whether a paid frontier judge is in scope at all.
