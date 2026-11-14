# Revision report — external-venue readiness pass (D-80, 2026-11-03)

> **Superseded in part by D-81** (`docs/paper/REVISION_REPORT_D81.md`): the keep-all margin sentence and the A4 "every arm at chance" wording below were corrected. This report keeps the D-80 text as it was.

Rendered by `scripts/paper/build_numbers.py`; every number below resolves from `docs/paper/NUMBERS_MAP.csv`. Changed text is shown as LaTeX source with the values substituted. No model call; no change to data, runs, frozen configuration, prompts, thresholds, hypotheses or confirmatory results.

## Summary of changes

1. **Post hoc sensitivity (MDE) analysis** — `scripts/analysis/mde_sensitivity.py` → `results/heldout/analysis_final/D1_M1/tables/mde_sensitivity.json`. The bootstrap ΔF1 sample of each confirmatory test is rebuilt and checked to reproduce `confirmatory.json` (Δ, 95% CI, p) exactly; MDE = (z₁₋α/₂ + z₀.₈) × SE at α = {{mde:alpha@2}} and at the Holm α for the smallest p ({{mde:alpha_holm_smallest_p@2}}). New Table (Threats) and one sentence in Statistical conclusion validity. Not observed power.

   | H | n (bugs) | ΔF1 | SE | MDE α=0.05 | MDE α=0.01 |
   |---|---|---|---|---|---|
   | H1 | {{mde:tests:H1:n_instances}} ({{mde:tests:H1:n_bugs}}) | {{mde:tests:H1:delta}} | {{mde:tests:H1:se_bootstrap}} | {{mde:tests:H1:mde_alpha_005}} | {{mde:tests:H1:mde_alpha_holm_min}} |
   | H2a | {{mde:tests:H2a:n_instances}} ({{mde:tests:H2a:n_bugs}}) | {{mde:tests:H2a:delta}} | {{mde:tests:H2a:se_bootstrap}} | {{mde:tests:H2a:mde_alpha_005}} | {{mde:tests:H2a:mde_alpha_holm_min}} |
   | H2b | {{mde:tests:H2b:n_instances}} ({{mde:tests:H2b:n_bugs}}) | {{mde:tests:H2b:delta}} | {{mde:tests:H2b:se_bootstrap}} | {{mde:tests:H2b:mde_alpha_005}} | {{mde:tests:H2b:mde_alpha_holm_min}} |
   | H3a | {{mde:tests:H3a:n_instances}} ({{mde:tests:H3a:n_bugs}}) | {{mde:tests:H3a:delta}} | {{mde:tests:H3a:se_bootstrap}} | {{mde:tests:H3a:mde_alpha_005}} | {{mde:tests:H3a:mde_alpha_holm_min}} |
   | H3b | {{mde:tests:H3b:n_instances}} ({{mde:tests:H3b:n_bugs}}) | {{mde:tests:H3b:delta}} | {{mde:tests:H3b:se_bootstrap}} | {{mde:tests:H3b:mde_alpha_005}} | {{mde:tests:H3b:mde_alpha_holm_min}} |

2. **Cost and latency per arm from the call logs** — `scripts/analysis/cost_latency_s1.py` → `results/heldout/analysis_final/D1_M1/tables/cost_latency_s1.json` (every call key looked up in the frozen call log; sums cross-checked against the decision records). New Table B3 (Appendix B) and one sentence in RQ3: DEB used {{cost:deb_over_j1:tokens@1}}× J1's tokens and {{cost:deb_over_j1:median_wall@1}}× its median wall time for an F1 gain of {{der:d1 DEB-J1 f1}}.

   | Arm | Calls | In tokens | Out tokens | Median s | P90 s |
   |---|---|---|---|---|---|
   | J1 | {{cost:arms:J1:calls_per_instance@0}} | {{cost:arms:J1:input_tokens_per_instance@0}} | {{cost:arms:J1:output_tokens_per_instance@0}} | {{cost:arms:J1:wall_s_median@2}} | {{cost:arms:J1:wall_s_p90@2}} |
   | SC | {{cost:arms:SC:calls_per_instance@0}} | {{cost:arms:SC:input_tokens_per_instance@0}} | {{cost:arms:SC:output_tokens_per_instance@0}} | {{cost:arms:SC:wall_s_median@2}} | {{cost:arms:SC:wall_s_p90@2}} |
   | SC-T | {{cost:arms:SC-T:calls_per_instance@0}} | {{cost:arms:SC-T:input_tokens_per_instance@0}} | {{cost:arms:SC-T:output_tokens_per_instance@0}} | {{cost:arms:SC-T:wall_s_median@2}} | {{cost:arms:SC-T:wall_s_p90@2}} |
   | DEB | {{cost:arms:DEB:calls_per_instance@0}} | {{cost:arms:DEB:input_tokens_per_instance@0}} | {{cost:arms:DEB:output_tokens_per_instance@0}} | {{cost:arms:DEB:wall_s_median@2}} | {{cost:arms:DEB:wall_s_p90@2}} |

3. **Framing** — abstract and conclusion now lead with (a) no LLM arm exceeds keep-all's F1 by more than {{der:d1 best S1 LLM - KA f1@abs}} (the best S1 arm is {{der:d1 best S1 LLM is DEB}}), with MCC above chance but weak; (b) failure evidence is the component that matters; (c) the larger and cross-family judges score higher but are single-replicate or exploratory. The DEB−SC difference is always given with its interval. Note: no paired test of an LLM arm against keep-all exists in the committed analysis, so the text states the F1 margin and its size relative to the intervals, and does not claim a significance test.
4. **Softened absolute claims** — every changed sentence is listed below.
5. **Title** — unchanged in the .tex; two shorter options below.
6. **"Changes after Phase 2"** — kept in this course version; `docs/paper/EXTERNAL_VERSION_NOTES.md` records that the external version drops it.
7. **External submission plan** — `docs/paper/EXTERNAL_SUBMISSION_PLAN.md` (proposals only, nothing run).
8. **Checks** — PDF rebuilt; main text through the Conclusion ends on page 13; numbers-map check run (every value resolved, published figures verified against their sources).

## Title options (12 words or fewer; the .tex title is unchanged)

- **A.** Program Fault or Test Fault? Evaluating LLM Triage Against Buggy/Fixed Ground Truth
- **B.** Small Local LLMs as Failure Triage Judges for Generated Unit Tests

## Sentences changed: softened absolute claims (item 4)

**Introduction, G1**

- before: \textbf{G1}: no study measures how accurately
- after: \textbf{G1}: to our knowledge, no study has measured how accurately

**Introduction, G2**

- before: \textbf{G2}: specification is assumed rather than varied, although
- after: \textbf{G2}: in the studies we reviewed, specification is assumed rather than varied, although

**Introduction, G3**

- before: self-consistency~\cite{wang2023selfconsistency}, has not been applied to triage.
- after: self-consistency~\cite{wang2023selfconsistency}, has, to our knowledge, not been applied to triage.

**Related Work, test generation**

- before: These studies score success against the current code version, so none measures whether the tests expose faults in it.
- after: These studies score success against the current code version; to our knowledge, none of them measures whether the tests expose faults in it.

**Related Work, test repair**

- before: none evaluates on buggy/fixed pairs.
- after: to our knowledge, none of these evaluates on buggy/fixed pairs.

**Related Work, triage and specification**

- before: no study varies the specification given to a triage decision.
- after: we are not aware of a study that varies the specification given to a triage decision.

## Sentences changed: framing (item 3)

**Abstract (rewritten: framing a-c, softened claims)**

- before:

  > \abstract{LLM-based test generators produce many tests that fail when executed, and most generators repair or discard every failing test, which also removes tests that expose real faults. Existing LLM triage stages have been evaluated through precision, small manual audits or proxies, never against independent buggy/fixed ground truth on repository-level Java code; the specification available to the judge has not been varied, and multi-agent gains have not been budget-matched. This study scores LLM failure triage against labels obtained by re-running each failing generated test on the fixed version of the same Defects4J program. On a held-out split of {{der:test methods}} focal methods from {{der:n test projects}} projects, {{sum:prevalence:judged_sample_prevalence_by_dataset:D1:PF}} program-fault and {{sum:prevalence:judged_sample_prevalence_by_dataset:D1:TF}} test-fault failures were judged by a locally served 9B open-weight model under a one-shot judge, five-sample self-consistency (also token-matched) and a five-call adversarial debate, against keep-all, discard-all and rule-based baselines at three specification levels. Debate reached F1 {{d1:DEB|S1:f1}} (MCC {{d1:DEB|S1:mcc}}) against {{d1:R0:f1}} (MCC {{d1:R0:mcc}}) for the rule-based baseline and {{d1:KA:f1}} (MCC {{d1:KA:mcc}}) for keep-all. None of the five confirmatory tests was significant after Holm correction (one-shot judge versus rule baseline: $\Delta$F1 {{conf:f1:H1:delta}}, $p_\mathrm{Holm}$ {{conf:f1:H1:p_holm}}). Removing the failure evidence changed F1 by {{abl:J1|S1|noF-J1|S1:delta}} (one-shot) to {{abl:SC|S1|noF-SC|S1:delta}} (self-consistency); Javadoc did not help ($\Delta$F1 {{conf:f1:H2a:delta}}); debate ranked first by MCC under both judges and both datasets, and a 12B judge raised its F1 to {{d1m2:DEB|S1:f1}}, although that judge shares the generator's model family. Triage with small local judges is only modestly better than chance, and its evidence, not its architecture, carries most of the signal.}

- after:

  > \abstract{LLM-based test generators produce many tests that fail when executed, and most generators repair or discard every failing test, which also removes tests that expose real faults. To our knowledge, LLM triage stages have been evaluated through precision, small manual audits or proxies rather than against independent buggy/fixed ground truth on repository-level Java code, without varying the judge's specification or matching the budgets of multi-agent and single-agent arms. This study scores LLM failure triage against labels obtained by re-running each failing generated test on the fixed version of the same Defects4J program. On a held-out split of {{der:test methods}} focal methods from {{der:n test projects}} projects, {{sum:prevalence:judged_sample_prevalence_by_dataset:D1:PF}} program-fault and {{sum:prevalence:judged_sample_prevalence_by_dataset:D1:TF}} test-fault failures were judged by a locally served 9B open-weight model under a one-shot judge, five-sample self-consistency (also token-matched) and a five-call adversarial debate, against keep-all, discard-all and rule-based baselines at three specification levels. No LLM arm exceeded keep-all's F1 ({{d1:KA:f1}}) by more than {{der:d1 best S1 LLM - KA f1@abs}}, and MCC places the arms above chance but weak (debate {{d1:DEB|S1:mcc}}, 95\% CI {{d1:DEB|S1:mcc_ci95}}); none of the five confirmatory tests was significant after Holm correction. Removing the failure evidence lowered F1 for every arm, by {{abl:DEB|S1|noF-DEB|S1:delta@abs}} to {{abl:SC|S1|noF-SC|S1:delta@abs}}, while Javadoc did not help ($\Delta$F1 {{conf:f1:H2a:delta}}). A 12B cross-family judge and an exploratory 35B judge scored higher (debate F1 {{d1m2:DEB|S1:f1}}; {{x35:summary:35B:DEB:f1}} against M1's {{x35:summary:M1:DEB:f1}} on the same instances), but each ran a single replicate, so these gains are exploratory. With small local judges, the failure evidence, not the architecture, carries most of the signal.}

**Conclusion (rewritten: framing a-c)**

- before:

  > This study scored LLM failure triage of generated unit tests against execution-based buggy/fixed labels, with a frozen protocol, held-out projects and locally served open-weight judges. The 9B judge separated program faults from test faults only modestly better than chance, with most of its signal coming from the failure evidence; Javadoc did not help, an inferred specification did not either, and an adversarial debate ranked first by MCC across datasets and judges without a significant advantage over self-consistency at equal budget. No confirmatory hypothesis was supported after correction. Future work should repeat the confirmatory tests with larger judges from a family other than the generator's, on a larger held-out sample, add an external benchmark (D3), and study cost-sensitive thresholds such as the lower self-consistency vote threshold, which traded precision for recall.

- after:

  > This study scored LLM failure triage of generated unit tests against execution-based buggy/fixed labels with a frozen protocol and local open-weight judges. No LLM arm exceeded keep-all's F1 by more than {{der:d1 best S1 LLM - KA f1@abs}}, MCC placed the arms above chance but low, and no confirmatory hypothesis was supported after correction; the post hoc sensitivity analysis shows that the sample could detect only large differences between arms. The component that mattered was the failure evidence: without it, every arm fell to chance. Javadoc and an inferred specification did not help, and debate's advantage over self-consistency was consistent in direction but not significant (H3a $\Delta$F1 {{conf:f1:H3a:delta}}, 95\% CI {{conf:f1:H3a:ci95}}). The 12B and exploratory 35B judges scored higher on a single replicate, so their gains are exploratory. Future work should repeat the confirmatory tests with a stronger judge from another family than the generator's on a larger held-out sample, add an external benchmark (D3), and study cost-sensitive vote thresholds.

## Text added (items 1–2)

**Results, RQ3 (new sentence)**

```latex
Measured from the call logs (Table~\ref{tab:cost}), DEB made {{cost:arms:DEB:calls_per_instance@0}} calls per instance against J1's {{cost:arms:J1:calls_per_instance@0}}, consumed {{cost:deb_over_j1:tokens@1}} times its tokens and {{cost:deb_over_j1:median_wall@1}} times its median wall time ({{cost:arms:DEB:wall_s_median@1}}\,s vs {{cost:arms:J1:wall_s_median@1}}\,s) for an F1 gain over J1 of {{der:d1 DEB-J1 f1}}, a difference no confirmatory test covers.

\subsection{Confirmatory tests}
```

**Threats, Statistical conclusion (new sentence)**

```latex
\textit{Statistical conclusion.} The sample is small ({{sum:prevalence:PF}} \PF{} instances at S1), and ablations and E5 have one replicate. A post hoc sensitivity analysis (Table~\ref{tab:mde}; not observed power) shows that at {{mde:power@pct0}} power and $\alpha={{mde:alpha@2}}$ the design could detect F1 differences of about {{mde:tests:H2a:mde_alpha_005@2}}--{{mde:tests:H2b:mde_alpha_005@2}} for the specification contrasts but only {{mde:tests:H3a:mde_alpha_005@2}} for DEB versus SC and {{mde:tests:H1:mde_alpha_005@2}} for J1 versus R0, and every observed difference is smaller than its MDE.
```

**Threats (new Table: MDE)**

```latex
\begin{table}[t]
\caption{Post hoc sensitivity analysis (not observed power): minimum detectable $\Delta$F1 at {{mde:power@pct0}} power, $\mathrm{MDE}=(z_{1-\alpha/2}+z_{{{mde:power@1}}})\,\mathrm{SE}$, SE: standard deviation of the bug-level bootstrap $\Delta$F1, at $\alpha={{mde:alpha@2}}$ and at the Holm $\alpha$ for the smallest $p$ ({{mde:alpha_holm_smallest_p@2}}).}\label{tab:mde}
\footnotesize\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{@{}l c c c c c@{}}
\toprule
H & $n$ (bugs) & $\Delta$F1 & SE & MDE$_{{{mde:alpha@2}}}$ & MDE$_{{{mde:alpha_holm_smallest_p@2}}}$ \\
\midrule
H1 & {{mde:tests:H1:n_instances}} ({{mde:tests:H1:n_bugs}}) & {{mde:tests:H1:delta}} & {{mde:tests:H1:se_bootstrap}} & {{mde:tests:H1:mde_alpha_005}} & {{mde:tests:H1:mde_alpha_holm_min}} \\
H2a & {{mde:tests:H2a:n_instances}} ({{mde:tests:H2a:n_bugs}}) & {{mde:tests:H2a:delta}} & {{mde:tests:H2a:se_bootstrap}} & {{mde:tests:H2a:mde_alpha_005}} & {{mde:tests:H2a:mde_alpha_holm_min}} \\
H2b & {{mde:tests:H2b:n_instances}} ({{mde:tests:H2b:n_bugs}}) & {{mde:tests:H2b:delta}} & {{mde:tests:H2b:se_bootstrap}} & {{mde:tests:H2b:mde_alpha_005}} & {{mde:tests:H2b:mde_alpha_holm_min}} \\
H3a & {{mde:tests:H3a:n_instances}} ({{mde:tests:H3a:n_bugs}}) & {{mde:tests:H3a:delta}} & {{mde:tests:H3a:se_bootstrap}} & {{mde:tests:H3a:mde_alpha_005}} & {{mde:tests:H3a:mde_alpha_holm_min}} \\
H3b & {{mde:tests:H3b:n_instances}} ({{mde:tests:H3b:n_bugs}}) & {{mde:tests:H3b:delta}} & {{mde:tests:H3b:se_bootstrap}} & {{mde:tests:H3b:mde_alpha_005}} & {{mde:tests:H3b:mde_alpha_holm_min}} \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Limitations, deviations and threats to validity}
```

**Appendix B (new Table: cost and latency)**

```latex
\begin{table}[h]
\caption{Cost and latency per arm from the call logs, D1-test, S1, judge M1, {{cost:scored_instances}} scored instances $\times$ {{cost:arms:DEB:replicates}} replicates. Tokens: mean per instance; wall time per instance (calls run one at a time). API cost: zero.}\label{tab:cost}
\footnotesize\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{@{}l c c c c c@{}}
\toprule
Arm & Calls & In tokens & Out tokens & Median (s) & P90 (s) \\
\midrule
J1 & {{cost:arms:J1:calls_per_instance@0}} & {{cost:arms:J1:input_tokens_per_instance@0}} & {{cost:arms:J1:output_tokens_per_instance@0}} & {{cost:arms:J1:wall_s_median@2}} & {{cost:arms:J1:wall_s_p90@2}} \\
SC & {{cost:arms:SC:calls_per_instance@0}} & {{cost:arms:SC:input_tokens_per_instance@0}} & {{cost:arms:SC:output_tokens_per_instance@0}} & {{cost:arms:SC:wall_s_median@2}} & {{cost:arms:SC:wall_s_p90@2}} \\
SC-T & {{cost:arms:SC-T:calls_per_instance@0}} & {{cost:arms:SC-T:input_tokens_per_instance@0}} & {{cost:arms:SC-T:output_tokens_per_instance@0}} & {{cost:arms:SC-T:wall_s_median@2}} & {{cost:arms:SC-T:wall_s_p90@2}} \\
DEB & {{cost:arms:DEB:calls_per_instance@0}} & {{cost:arms:DEB:input_tokens_per_instance@0}} & {{cost:arms:DEB:output_tokens_per_instance@0}} & {{cost:arms:DEB:wall_s_median@2}} & {{cost:arms:DEB:wall_s_p90@2}} \\
\bottomrule
\end{tabular}
\end{table}
\end{appendices}
```

