# Draft paper subsection — "Model Selection and Configuration Protocol"

*Draft text for the authors; not inserted into `paper/`. Filled after the Step 6 freeze (2026-11-01;
`configs/local_models.FROZEN.json`, text SHA-256 c07f4e15…10e9). Besides the bracketed values, two sentences were
rewritten because the original wording presupposed outcomes that did not happen: the M1 gate sentence (M1 failed
G-d; D-48, D-50, D-52) and the generator-candidate clause (selection was sequential and Qwen3.5-35B-A3B was never
tried as G; D-44). A threat-to-validity sentence on F1 versus MCC was added (D-54).*

---

**Model selection and configuration protocol.** All language models were open-weight models served locally
by Ollama 0.40.13 on a single laptop GPU (NVIDIA RTX 5070 Ti, 12 GB VRAM; 31 GB RAM), so the study incurred
no API cost. Model choices were made on the development split only (Cli, Gson, Jsoup; 39 focal methods);
held-out instances, seeded faults and held-out execution outcomes were never used for any selection, prompt
revision or threshold. Every candidate was first loaded alone with an explicit 8,192-token context to record
its digest, quantization, licence, GPU residency, throughput, JSON-schema validity and thinking controls,
using synthetic prompts that contain no study data. Judges had to be fully GPU-resident at that context;
the generator could be partly offloaded to system memory because it runs once.

The test generator G was selected sequentially (Gemma 4 26B A4B first; Qwen3.5-35B-A3B only if it failed) by
pre-specified criteria in priority order — compilation and execution reliability, assertion validity on the fixed version, line and branch
coverage, and uniqueness and stability across generations — with 5-percentage-point tolerance bands, subject
to the Phase-2 yield gate (program-fault instances at least 3% of executed tests); the program-fault yield was
reported but never maximised. Gemma 4 26B A4B passed (compilation and execution reliability 0.60, focal-method bootstrap 95% CI 0.45–0.73; fixed-version assertion validity 0.73;
program-fault yield 5.0%; focal line/branch coverage 71.8%/64.7%) and was selected (Q4_K_M, manifest digest
001e5daf…), so the second candidate was not evaluated. The primary judge
M1 was then fixed by a family-separation rule as the candidate from the other model family, Qwen3.5 9B (Q4_K_M, digest 56671c2a…), and the second
judge M2, Gemma 4 12B (Q4_K_M, digest 6114515d…), was used only for the cross-model robustness analysis. Because M2 shares a family with G,
self-preference cannot be excluded in that analysis. On a 55-instance, 12-bug development pilot, M1
passed the gates on output validity (100% of single-judge, 99.7% of self-consistency and 100% of debate outputs
schema-valid), evidence citation (100% of decisions cite evidence; 99.5% of cited items exist) and the F1 sanity
range, but **failed** the gate requiring single-judge PF-F1 above both trivial baselines: F1 0.350 (MCC −0.03)
against 0.642 (MCC 0.36) for the rule-based baseline and 0.553 (MCC 0.00) for keep-all; difference −0.29,
bug-level bootstrap 95% CI [−0.51, +0.60]. Self-consistency (F1 0.333, MCC 0.01) and debate (F1 0.267, MCC 0.03)
were also at chance. The failure persisted across five pre-registered prompt-revision rounds, an 8-bit
quantization and the other model family, and an audit of the judge inputs, label mapping and rationales found no
pipeline defect; the judge reasoned from the exception message and the Javadoc and did not cite the stack frames
the rule-based baseline uses. M1 was therefore kept and the failure is reported as a finding rather than masked by
further selection. Because F1 on the program-fault class hides chance level on a 1:2 sample (keep-all reaches
F1 0.55 at MCC 0), MCC and its bug-level CI are reported beside every F1.

Thinking modes were disabled for all primary comparisons (Qwen: `think=false`; Gemma: thinking token omitted)
and verified in every response; all generated tokens, including any thinking-channel output, were logged and
used for token matching. All arms within a comparison used the same model weights, quantization, context
length (8,192 tokens, prompt plus output), output limit (512 tokens), temperature (0.7) and top-p (1.0), with a
per-call seed. Runtime version, model and weight digests, server settings, decoding parameters, seeds and
prompt hashes were frozen in a single configuration file before any held-out run. Repeating 49 development
judgements with identical seeds changed 0% of labels at temperature 0 and 0% at temperature 0.7 (all
response texts were byte-identical), which
bounds the contribution of runtime non-determinism.

These models are much smaller than the proprietary and API-served models assumed in the original design
(a DeepSeek-V3-family judge, a Qwen3-family judge and GPT-4.1 as generator); results characterise triage with locally deployable models and are not
claimed to transfer to larger models.
