# Defense Q&A — the 29 hardest questions (D-82; updated with E6a, E6b, E8, E9, KUU, KUU-NG)

Rendered by `scripts/paper/build_numbers.py`; every number resolves from `docs/paper/NUMBERS_MAP.csv`.

**1. Your judge is a 9B local model. Isn't the study just measuring a weak judge?**
Partly, and the paper says so. The 9B judge's one-shot F1 is {{d1:J1|S1:f1}} (MCC {{d1:J1|S1:mcc}}), and the 12B
judge M2 scored higher on every arm (DEB on D1-test: +{{r3:D1:m2_minus_m1:DEB:f1:delta@abs}}, 95% CI
{{r3:D1:m2_minus_m1:DEB:f1:ci95}}). The contribution is the measurement protocol and the evidence findings, which
were measured for M1 with thinking off (the ablation was not run for other judges); we do not claim the absolute numbers transfer to frontier models. A frontier reference judge (E9, Claude Sonnet 5.5)
reached DEB F1 {{e9:summary:DEB|S1|SON:f1}} on the same instances, so model size matters a great deal.

**2. Nothing was significant. What did you actually find?**
No confirmatory test survived Holm (smallest p_Holm {{conf:f1:H2a:p_holm}}, H2a). The sensitivity analysis shows why:
at 80% power this design detects ΔF1 of about {{mde:tests:H3a:mde_alpha_005@2}} for DEB vs SC and
{{mde:tests:H1:mde_alpha_005@2}} for J1 vs R0. What the data do show is that the failure evidence carries the signal:
without it J1 and SC fall to chance (MCC {{d1:J1|S1|noF:mcc}} and {{d1:SC|S1|noF:mcc}}). Later tests, each fixed in advance in the version-controlled decision
log, were supported: H6-2 (debate above chance with a third-family judge, MCC {{e6b:hypotheses:H6-2:mcc}}), KUU's two on D2, the cascade over
KUU, KUU-NG's two, and the thinking judge over debate (HT-1, HT-2); most are sanity or safety checks, not evidence
that one planned architecture beats another.

**3. Isn't DEB just keep-all?**
On F1 it nearly is: DEB {{d1:DEB|S1:f1}} against keep-all's {{d1:KA:f1}}. That is exactly why we report MCC: keep-all
has MCC {{d1:KA:mcc}}, DEB {{d1:DEB|S1:mcc}} (95% CI {{d1:DEB|S1:mcc_ci95}}), and DEB rejects
{{d1:DEB|S1:TN@1}} test faults per replicate that keep-all would keep.

**4. How valid are the labels?**
They are execution-based: PF means the test fails deterministically on the buggy version and passes on the fixed one;
no human or LLM decides them. Ambiguous double failures are excluded, and counting them as PF or TF moves DEB's F1 to
{{sum:sensitivity_f1:AMB_as_PF:DEB|S1:f1}} or {{sum:sensitivity_f1:AMB_as_TF:DEB|S1:f1}}. A two-rater blind audit (D-108) covered {{aud:n_items}} development-split instances: all {{aud:labels:PF}} PF and
{{aud:labels:TF}} of {{aud:dev_split_labels:TF}} TF, none held out (D-45).
- **Human–human:** κ {{aud2:raters:kappa}}, 95% bug-level CI {{aud2:raters:kappa_ci95_bug_bootstrap}}.
- **Consensus against the execution label:** {{aud2:consensus_vs_execution:agreement@pct1}} agreement,
  κ {{aud2:consensus_vs_execution:kappa_pf_tf}}.
- **Where they differed:** both items were labelled TF by execution and judged PF by the raters, so the label errs, if
  at all, towards calling a bug-revealing test faulty.
- **LLM rater (secondary, D-84):** a blind Claude Opus 5.5 rater, sealed until both human sheets were committed,
  agreed with the human consensus at κ {{aud2:llm_rater_secondary_D84:consensus_vs_C:kappa}}.

The audit sample is from the development split, not the held-out test.

**5. Defects4J is in every model's training data. Isn't this memorisation?**
Two checks argue against it. Removing the failure evidence brings J1 and SC to chance, so the decisions depend on the
package, not on recall of the benchmark; and on seeded faults (D2), whose fixes no model can have seen, DEB still has MCC
{{d2:DEB|S1:mcc}}. The external benchmark (D3) was not run, which we list as a limitation. The frontier reference
judge (E9) is the exception: see question 21.

**6. Your comparison with the base papers is unfair.**
Agreed, and the paper says no improvement over a base paper can be computed: the published figures (JSTestCraft's
audited recall {{cit:jstestcraft recall}}%*, JavaOracle's precision {{cit:javaoracle precision}}*) use other
languages, labels and models. The fair comparisons are the re-implemented baselines on identical instances, where DEB
exceeds the rule baseline's F1 by {{der:d1 DEB-R0 f1}}.

**7. Javadoc made things worse. Isn't that implausible?**
It is what the data show, and we report it as a trend, not a finding: ΔF1 {{conf:f1:H2a:delta}} (95% CI
{{conf:f1:H2a:ci95}}, p {{conf:f1:H2a:p}}, p_Holm {{conf:f1:H2a:p_holm}}), and S0 was best for every arm. The mixed
model's S0 odds ratio is {{glmmb:models:PF_recall:terms:1:odds_ratio}} with an interval that includes 1
({{glmmb:models:PF_recall:terms:1:or_ci95_bootstrap}}). One untested reading: documentation gives the judge material to
defend the test's expectation.

**8. Did you tune anything on the test set?**
No. Prompts, decoding, thresholds and the analysis were frozen on the development split before any held-out call
(D-57), and every later choice is a dated D-entry recorded before the result it governs. The development gate even
failed — one-shot F1 {{devgate:G_d_detail:J1_f1}} against R0's {{devgate:G_d_detail:R0_f1}} — and we kept the judge and
reported it rather than re-selecting.

**9. Why both F1 and MCC?**
Because F1 on the positive class rewards a constant answer: at PF prevalence {{sum:prevalence:pf_prevalence}} keep-all
scores F1 {{d1:KA:f1}} with MCC 0. MCC tells chance from signal; F1 is kept because the original design fixed it in advance.

**10. Is the debate really budget-matched?**
SC and DEB both make {{cost:arms:DEB:calls_per_instance@0}} calls per instance; DEB consumed
{{d1:DEB|S1:consumed_tokens_per_instance@0}} tokens per instance against SC's {{d1:SC|S1:consumed_tokens_per_instance@0}},
and the token-matched arm SC-T ({{d1:SC-T|S1:consumed_tokens_per_instance@0}}) changes nothing: DEB − SC-T ΔF1
{{sum:sc_t_check:delta}} ({{sum:sc_t_check:ci95}}).

**11. Could the judge have seen the answer in the prompt?**
Every package is checked against per-instance forbidden strings before the call; {{sum:leakage_abort_exclusions:counts_labelled:S1|full:instances}}
D1 instances were blocked and excluded from every arm at that level. On D2, the guard's match was the injected mutated
line itself in {{der:d2 aborts mutated line}} of {{der:d2 aborted instances}} blocked instances — genuine leaks that
were stopped.

**12. {{sum:leakage_abort_exclusions:n_per_level:S1}} instances is small.**
Yes: {{sum:leakage_abort_exclusions:n_per_level:S1}} scored instances from {{r3:D1:n_bugs}} bugs, set by the real PF
yield, not by choice. The sensitivity table quantifies what that size can and cannot detect, and the external plan
sizes the follow-ups against it.

**13. The 35B judge looks better. Why isn't it a result?**
It ran after all primary work, with flash attention off, partial GPU offload and a waived memory gate (D-78). DEB was
completed later (E6a); its SC was stopped by the memory rule after {{x35o:decisions_by_arm:SC}} decisions and not
retried (D-89). On {{e6a:n_instances}} instances DEB reached F1 {{e6a:summary:35B:DEB:f1}} against M1's
{{e6a:summary:M1:DEB:f1}} ({{e6a:35b_minus:DEB 35B-M1:f1:delta}}, {{e6a:35b_minus:DEB 35B-M1:f1:ci95}}). It is labelled
exploratory everywhere, ran under different conditions and fed nothing back.

**14. M2 is from the same family as the generator. Self-preference?**
It cannot be excluded. A third-family judge (Ministral 3 14B, E6b) was added to probe it: M2 scored above it in every
arm (DEB ΔF1 {{e6b:family_check:e6b_minus:DEB E6B-M2:f1:delta}}, {{e6b:family_check:e6b_minus:DEB E6B-M2:f1:ci95}}),
which is consistent with family affinity but also with M2 simply being a different model. M1, a different family from
the generator, stays the confirmatory judge.

**15. Would anyone use this in practice?**
Only where false alarms are costly relative to missed bugs. Exploratory cost analysis: DEB is cheaper than keep-all only
while a missed bug costs less than {{xd:D1:DEB:breakeven_vs_KA@1}} false alarms (on the judged sample;
{{xd:D1:DEB:breakeven_vs_KA_natural@1}} at the natural prevalence). And its confidence is not usable as is: stated
{{xd:D2:calibration:DEB:mean_confidence@2}} against an accuracy of {{xd:D2:calibration:DEB:accuracy@2}} (ECE
{{xd:D2:calibration:DEB:ece@2}}).

**16. You re-implemented JSTestCraft's three-LLM vote. Does voting across families help?**
Not significantly. A budget-matched majority of one fresh call each from M1, M2 and E6b reached F1
{{e8:summary:VOTE3|S1:f1}} against SC3's {{e8:summary:SC3|S1:f1}} (H8-1 {{e8:hypotheses:H8-1:delta}},
{{e8:hypotheses:H8-1:ci95}}, p {{e8:hypotheses:H8-1:p}} before and {{e8:hypotheses:H8-1:p_holm}} after Holm); VOTE5
against SC and DEB was not significant either. What changed clearly is recall: the vote lost
{{e8:summary:VOTE3|S1:pf_lost@0}} of {{e6b:pf_prevalence:PF}} bug-revealing tests where SC lost
{{e8:summary:SC|S1:pf_lost@0}}. It is also close to its best member, M2 alone (fresh J1 F1 {{e8:fresh_j1:M2:f1}}).

**17. Did anything go wrong in the later runs?**
Three things, all disclosed with a D-entry before any affected number was read. The gate script crashed on a
leakage-abort bookkeeping gap and was fixed with a regression test (D-86). A unit test, run while a candidate was still
registered, made {{q87:calls}} unplanned calls on D1-test; they were quarantined unread, are used nowhere, and the
held-out run is now refused for any candidate that selection did not choose (D-87). The 35B's SC hit the memory rule and
was not retried (D-89).

**18. Why do your numbers differ from the base papers?**
Five reasons: language (JSTestCraft is JavaScript), label source (we execute each test on the fixed version; they audit
or judge), judge size (they use API models; our frontier reference, Claude Sonnet 5.5, reaches DEB F1
{{e9:summary:DEB|S1|SON:f1}} on our data), task and metric (several base papers measure generation, not triage), and
prevalence. Where the designs meet we agree: our effective-test share {{zhao:subsets:all_D1:share_effective_pct@2}}%
overlaps Zhao et al.'s range, a cross-family vote keeps recall high as JSTestCraft's does, and debate trades away true
positives as JavaOracle's does. Zhao et al.'s package has no generated tests, so their tests could not be re-run here.

**19. How noisy is a single run?**
For M1, J1 and SC are stable (F1 range {{rn:noise:J1:f1:range}} and {{rn:noise:SC:f1:range}} across three replicates) but
DEB is not ({{rn:noise:DEB:f1:range}}: {{rn:noise:DEB:f1:per_replicate:0}} / {{rn:noise:DEB:f1:per_replicate:1}} /
{{rn:noise:DEB:f1:per_replicate:2}}), so a single-replicate DEB comparison across judges is within noise. That is why E9
ran DEB three times; Sonnet's range was {{e9:deb_run_to_run_spread:sonnet:f1:range}}. When the bootstrap also resamples
replicates (D-106), the confirmatory intervals widen by up to {{rv:two_level_bootstrap:1:widening_factor@1}}×, and no
verdict changes.

**20. What is new beyond measurement?**
RQ4 and its answer. Keep unless unanimous (KUU): discard a failure only when three judge families agree it is a test
fault. It has no tuned parameter, and it is a safety rule, not a better classifier. RQ4 was added after the primary
study; its tests were fixed in advance in the version-controlled decision log before any of their calls (D-95, D-105, D-109), which is internal provenance, not an external registration. KUU was defined after the D1 vote (post hoc on D1) and tested once on unseen D2 under D-95.
On D2 it lost
{{kuu2:summary:KUU|S1:pf_lost@0}} of {{kuu2:pf_prevalence:PF}} bug-revealing tests against debate's
{{kuu2:summary:DEB|S1:pf_lost@0}} and beat keep-all's F1 (p Holm {{kuu2:hypotheses:H10-1:p_holm}}); its cost is a
slightly lower MCC ({{kuu2:summary:KUU|S1:mcc}} vs {{kuu2:summary:DEB|S1:mcc}}). A panel with no judge from the
generator's family (KUU-NG) lost {{kuung:D2:summary:KUUNG|S1:pf_lost@0}} (question 27).

**21. Didn't Sonnet just memorise Defects4J?**
It may have. Its training data very likely include Defects4J and its fixes, so its D1-test score (DEB F1
{{e9:summary:DEB|S1|SON:f1}}) may be inflated, and we call it a reference point, not a result. E9b (D-104) tests this
on the D2 seeded faults, whose fixes no model can have seen. Sonnet's DEB MCC there was {{e9b:summary:DEB|S1|SON:mcc}}
against {{e9b:sonnet_d1_minus_d2_mcc:DEB:mcc_d1}} on D1, so there is no drop. Both hypotheses fixed in advance hold:
MCC above zero, and above M1's by {{e9b:hypotheses:H11-2:delta}}. D2 mutates the fixed code, so it cannot rule out
knowledge of the original source. Our local judges' findings do not depend on Sonnet.

**22. Isn't KUU just a voting threshold?**
In mechanics, yes: it is a 3-of-3 threshold. What makes it a method is what the threshold rests on and what it adds.
- **The votes come from three different model families.** On D2, two families share a miss
  {{ed:D2:comparison:mean_cross_family_lift@1}} times as often as independence predicts. Three samples of one model share
  a miss {{ed:D2:comparison:mean_within_family_lift@1}} times as often, and unanimity across families lost
  {{ed:D2:kuu_loss:observed@0}} bug-revealing tests where unanimity within one model would have lost
  {{ed:D2:within_family:M1:unanimous_loss@0}}.
- **It escalates instead of out-voting.** In JSTestCraft's vote a majority out-votes a dissenting judge; unanimity
  treats dissent as a reason to keep. Disagreements can then go to a frontier judge, which raised MCC from
  {{cas2:summary:KUU|S1:mcc}} to {{cas2:summary:CAS|S1:mcc}} while only {{cas2:escalation:share_escalated@pct0}} of the
  failures left the machine.
- **It needs no tuned threshold.** Debate's confidence-100 rule reaches a similar point, but its threshold was set on
  the development split.
- **It is scored against execution labels with every call counted**, unlike JSTestCraft's majority vote.

On its own, KUU is a conservative operating point: its MCC is below debate's.

**23. Was the cascade designed on the test set?**
No. The cascade and its hypotheses were committed (D-105) before any frontier call on D2, so its D2 result is a test fixed in advance (status F, not part of the original confirmatory family) and its D1 result post hoc. The sequence:
1. KUU came from the D1 vote, so D1 is post hoc and labelled so.
2. The cascade and its two hypotheses were written and committed (D-105) before E9b sent any request.
3. E9b's D2 decisions are what the cascade's fixed-in-advance test uses.

The code was run only on synthetic logs before that commit. The result is mixed, and we report it as such:
- **H12-1 is supported.** Cascade MCC is above KUU's (Δ {{cas2:hypotheses:H12-1:delta}}).
- **H12-2 is not.** F1 Δ {{cas2:hypotheses:H12-2:delta}} against Sonnet on every instance, 95% CI
  {{cas2:hypotheses:H12-2:ci95}}, so non-inferiority at −0.05 is not shown.

**24. Isn't KUU's success guaranteed by where it sits on the trade-off?**
Partly, yes. A rule that discards little will lose little, so we compared rules at similar discard rates on D2
(D-106, post hoc):
- **KUU** discards {{rv:operating_points_d2:summary:KUU|S1:share_discarded@pct0}} and loses
  {{rv:operating_points_d2:summary:KUU|S1:pf_lost@0}} bug-revealing tests.
- **M1's debate at confidence 100** discards {{rv:operating_points_d2:summary:M1DEBtau100|S1:share_discarded@pct0}}
  and loses {{rv:operating_points_d2:summary:M1DEBtau100|S1:pf_lost@0}}.
- **Unanimity over five samples of one model** discards more and loses
  {{rv:operating_points_d2:summary:M1SC5U|S1:pf_lost@0}} (M1) or {{rv:operating_points_d2:summary:M2SC5U|S1:pf_lost@0}}
  (M2), with a higher MCC.

So KUU's advantage at its operating point is small. The case for it is that it needs no tuned threshold, and that
escalation then lifts its MCC.

**25. Is the cascade worth it against simply running the frontier judge once?**
Not on MCC per dollar. On D2:

| Option | Frontier cost | MCC | Bugs with no bug-revealing test kept |
|---|---|---|---|
| Sonnet J1 on every instance | US$ {{rv:frontier_d2:rows:Sonnet J1, every instance:frontier_usd@2}} | {{rv:frontier_d2:rows:Sonnet J1, every instance:mcc}} | {{rv:frontier_d2:rows:Sonnet J1, every instance:bugs_with_no_pf_kept@0}} |
| Cascade to Sonnet DEB | US$ {{rv:frontier_d2:rows:Cascade to Sonnet DEB:frontier_usd@2}} | {{rv:frontier_d2:rows:Cascade to Sonnet DEB:mcc}} | {{rv:frontier_d2:rows:Cascade to Sonnet DEB:bugs_with_no_pf_kept@0}} |
| Cascade to Sonnet J1 | US$ {{rv:frontier_d2:rows:Cascade to Sonnet J1:frontier_usd@2}} | {{rv:frontier_d2:rows:Cascade to Sonnet J1:mcc}} | {{rv:frontier_d2:rows:Cascade to Sonnet J1:bugs_with_no_pf_kept@0}} |

The cascade's value is in the last column: fewer bugs lost, which is the cost the study cares about. It is not
cost-dominant, and we do not claim it is. Its argument is local-first operation: only the escalated
{{cas2:escalation:share_escalated@pct0}} of failures leaves the machine, against 100% for any frontier-everywhere
option. Local compute is not free either: the local tier used {{pareto:D2:points:CAS|S1:local_gpu_s_per_instance@1}}
GPU-seconds per instance on one laptop GPU, which no dollar figure prices.

**26. Would any of this work at a realistic prevalence?**
Precision would be low. At an assumed 5% bug-revealing share, the D2 rates give:
- KUU {{rv:deployment_precision:D2:rules:KUU|S1:precision_at_0.05}};
- the cascade {{rv:deployment_precision:D2:rules:CAS|S1:precision_at_0.05}};
- Sonnet's debate {{rv:deployment_precision:D2:rules:DEB|S1|SON:precision_at_0.05}}.

Most kept failures would still be test faults. These rules suit a triage stage whose job is not to lose bugs, ahead of
a human or a repair step, not one that must deliver only real faults.

**27. Isn't KUU just the lenient same-family judge vetoing discards?**
No. It was a fair worry, so we tested it with a panel fixed in advance that has no generator-family judge (KUU-NG,
D-109): M1, E6b and a fourth family, {{kuungsel:selected}}, chosen on the development split, with fresh calls.
- **On D2 it lost {{kuung:D2:summary:KUUNG|S1:pf_lost@0}} bug-revealing test** and no bug entirely, against
  {{kuung:D2:summary:DEB|S1:bugs_lost@0}} bugs for M1's debate (H13-2 supported, p Holm
  {{kuung:D2:hypotheses:H13-2:p_holm}}), and its F1 beat keep-all's (H13-1, p Holm {{kuung:D2:hypotheses:H13-1:p_holm}}).
  D1 agrees.
- **The new judge is not lenient.** Its miss rate on bug-revealing tests is {{kuungm:D2:kuung:NG:miss_rate_on_pf}},
  against M2's {{kuungm:D2:kuu:M2:miss_rate_on_pf}} (post hoc, D-111). So the protection is consistent with families
disagreeing, not with one reluctant judge.
- **The price:** KUU-NG discards {{kuung:D2:summary:KUUNG|S1:share_discarded@pct0}} of failures against KUU's
  {{kuung:D2:summary:KUU|S1:share_discarded@pct0}}, and its MCC is lower ({{kuung:D2:summary:KUUNG|S1:mcc}} vs
  {{kuung:D2:summary:KUU|S1:mcc}}, not significant).

The earlier leave-one-out analysis (D-107, post hoc) is why we asked. M2 shares the generator's family and seldom calls a
bug-revealing test faulty (miss rate {{ed:D2:miss_rate:M2:est}} on D2). Leaving one judge out on D2:
- **Without M2** (M1 + E6b): {{loo:D2:summary:M1_E6B|S1:pf_lost@0}} bug-revealing tests lost against KUU's
  {{loo:D2:summary:KUU|S1:pf_lost@0}}.
- **Pairs that include M2:** M1 + M2 loses {{loo:D2:summary:M1_M2|S1:pf_lost@0}}, M2 + E6b loses
  {{loo:D2:summary:M2_E6B|S1:pf_lost@0}}.

In that judge set, much of the protection was M2's veto. KUU-NG shows a third family can supply it instead.

**28. Where does KUU sit against every other rule?**
The trade-off figure (D-110, post hoc, descriptive) plots each rule's share of failures discarded against its share of
bug-revealing tests lost. On D2:
- **Single-model arms** discard about half of the failures and lose a third or more of the bug-revealing tests (M1
  debate: {{pareto:D2:points:DEB|S1:share_discarded@pct0}} discarded, {{pareto:D2:points:DEB|S1:pf_lost@0}} lost).
- **KUU** sits in the low-loss corner ({{pareto:D2:points:KUU|S1:share_discarded@pct0}},
  {{pareto:D2:points:KUU|S1:pf_lost@0}} lost), beside debate at confidence 100
  ({{pareto:D2:points:TAU|S1:share_discarded@pct0}}, {{pareto:D2:points:TAU|S1:pf_lost@0}} lost), the only point whose
  threshold was tuned.
- **The cascade** reaches the frontier judge's region ({{pareto:D2:points:CAS|S1:share_discarded@pct0}},
  {{pareto:D2:points:CAS|S1:pf_lost@0}} lost, against Sonnet debate's
  {{pareto:D2:points:DEB|S1|SON:share_discarded@pct0}} and {{pareto:D2:points:DEB|S1|SON:pf_lost@0}}).

No thinking-disabled local rule reaches that region on its own. Two local points come close: the thinking-enabled M1 judge ({{tk:d2:descriptive:ThinkingM1J1:share_discarded@pct0}} discarded and {{tk:d2:descriptive:ThinkingM1J1:pf_lost@int}} lost; D-131) and the fully local cascade ({{lc:D2:runs:62:local_cascade:share_discarded@pct0}} and {{lc:D2:runs:62:local_cascade:pf_lost@0}}; post hoc, D-132); both lose fewer bug-revealing tests than the cascade but remove fewer test faults.

**29. Your label audit was done by the authors, who had seen the fix. Isn't it biased?**
It could be, and the paper says so. The raters are the authors, they saw the developer's fix, and the sample is
development-split only. The audit is still informative because the labelling rule is mechanical and identical on both
splits: it asks whether that rule matches an informed reading of the fix, and it did on
{{aud2:consensus_vs_execution:agreement@pct1}} of items. A sealed LLM rater agreed with the human consensus at κ
{{aud2:llm_rater_secondary_D84:consensus_vs_C:kappa}}. An independent, held-out audit would be stronger.

**30. Why not just let one judge think?**
On seeded faults that would have done better than any planned arm of the same model: with its thinking mode on, M1's
one-shot judge reached MCC {{tk:d2:descriptive:ThinkingM1J1:mcc}} against debate's {{tk:d2:descriptive:M1DEB:mcc}} and
lost {{tk:d2:confirmatory:HT-2:pf_lost_thinking@int}} bug-revealing tests against {{tk:d2:confirmatory:HT-2:pf_lost_deb@int}},
both confirmed after Holm with hypotheses fixed in advance in the version-controlled decision log (D-130, D-131). Three things
stop it being the answer. It failed its development gate (F1 {{tk:gate:G_d_detail:J1_f1}} against R0's
{{tk:gate:G_d_detail:R0_f1}}), like every local judge. It still loses more bug-revealing tests than KUU
({{tk:d2:descriptive:ThinkingM1J1:pf_lost@int}} against {{tk:d2:descriptive:KUU:pf_lost@int}} on D2), so it does not
replace the safety rule. And the 12B M2's debate scored about as high on D1-test (MCC {{d1m2:DEB|S1:mcc}}, against
{{tk:d1:summary:mcc:min}}–{{tk:d1:summary:mcc:max}} over three thinking runs), so the claim holds for this judge's own
arms.

It was also not token-matched to debate; it happened to use fewer tokens
({{tk:d1:summary:tokens_per_instance:mean@0}} against {{tk:deb_tokens_per_instance_D1@0}} per D1-test instance). The
honest reading is that for small judges, reasoning inside one call did what orchestration was meant to do.

**31. Why was thinking disabled in the original design?**
Because reasoning modes inflate tokens and change the object of study: the methodology-change register written when the study moved to local models (row L-8 of `docs/local_models/METHODOLOGY_CHANGE_IMPACT.md`, 31 Oct) and the selection protocol's thinking-mode section (`docs/local_models/MODEL_SELECTION_PROTOCOL.md`) set thinking off for every primary comparison, consistent with the original design's "no step-by-step reasoning" output contract. The protocol also checks it on every call: a non-empty thinking channel counts as an invalid answer. There is no separate decision-log entry for it; the frozen configuration records `think: false` for every model (`configs/local_models.FROZEN.json`).

**32. The thinking judge failed your gate but wins on held-out data. Is your gate meaningless, or are you ignoring it when it suits you?**
Neither. The gate is a point-estimate check on a {{tk:gate:n_instances@int}}-instance development pilot (D-23) whose interval is too wide to rank judges (paired difference, thinking J1 minus R0 in F1, on the instances both scored: {{tk:gate:G_d_detail:delta}}, 95% CI {{tk:gate:G_d_detail:delta_ci95_bug_bootstrap@ci2}}; `results/revision/runs/REV_THINK_DEV_M1/dev_gates.json`), and {{der:local judges failing G-d@int}} of {{der:local judges gated}} local judges failed it (D-127). We did not ignore it: D-130 fixed in advance that the gate is a reported check, not a stopping rule, and the paper states the failure beside every thinking claim, so what it means here is that no small judge is validated for use on its own.

**33. The thinking finding came after the main study. Isn't the abstract headlining a post hoc result?**
It was found post hoc, on D1-test (D-129), and the abstract says so ("found on the real faults"). The headline is the confirmation: before any D2 call, D-130 fixed two hypotheses against debate, one Holm family, and the wording the paper would use for either outcome; both held (MCC {{tk:d2:descriptive:ThinkingM1J1:mcc}} against {{tk:d2:descriptive:M1DEB:mcc}}, p_Holm {{tk:d2:confirmatory:HT-1:p_holm}}; D-131, `results/revision/think_followup.json`). That is the same procedure RQ4 followed, and like RQ4 it is fixed in advance in the version-controlled decision log, not externally registered, so the journal plan asks for a registered replication (J-G1, J-L1).

**34. One model with thinking. Why should this generalise?**
It may not, and we do not claim it does: only Qwen 3.5 9B was run with thinking on (D-126, D-130), against one generator, on Java and Defects4J. What we have is consistency within that model: three D1-test runs gave balanced accuracy {{tk:d1:summary:ba:min}}–{{tk:d1:summary:ba:max}}, and the D2 confirmation held on seeded faults (`results/revision/think_followup.json`). Other families with a thinking mode, and a token-matched comparison, are untested and in the journal plan (J-T1, J-E2).

**35. If one thinking judge gets close to the cascade, what is KUU still for?**
Safety: on D2, KUU kept {{tk:d2:kuu_vs_thinking:pf_lost_by_thinking_kept_by_kuu@int}} bug-revealing tests the thinking judge threw away and lost {{tk:d2:kuu_vs_thinking:pf_lost_by_kuu_kept_by_thinking@int}} it kept (`results/revision/think_followup.json`), and it has nothing tuned. Putting the thinking judge behind KUU's unanimity as the second tier (post hoc, D-132, `results/revision/local_cascade.json`) lost {{lc:D2:runs:62:local_cascade:pf_lost@0}} bug-revealing tests and {{lc:D2:runs:62:local_cascade:bugs_lost@0}} bugs against the thinking judge's {{lc:D2:runs:62:thinking_alone:pf_lost@0}} and {{lc:D2:runs:62:thinking_alone:bugs_lost@0}}, with nothing leaving the machine, at a lower balanced accuracy ({{lc:D2:runs:62:local_cascade:ba}} against {{lc:D2:runs:62:thinking_alone:ba}}). So KUU is the layer that protects bugs; the thinking judge is the better classifier.

**36. Does the thinking judge still depend on the failure message, as your A4 ablation showed for the non-thinking arms?**
Untested. The A4 ablation (failure section removed) was run only for the planned thinking-disabled arms (E4, `results/heldout/analysis_final/D1_M1/`); no thinking run without the failure section exists. It is in the journal plan (J-T2), with the same ablation rule and the thinking configuration of D-130.

**37. Your D2 confirmation is on seeded mutants. Why trust it for real bugs?**
D2 was built so that no model could have memorised its faults (D-62 to D-64), which is what a confirmation needs, but single-line mutants are not real faults, and the paper says D2 "controls contamination but does not replace fresh real faults". On the real faults the evidence is exploratory and consistent: three D1-test runs gave balanced accuracy {{tk:d1:summary:ba:min}}–{{tk:d1:summary:ba:max}} against debate's eight-run best of {{tk:d1:deb_eight_runs:ba:max}} (D-131). A confirmation on fresh real faults is the first item of the journal plan (J-L1, J-C2).

**38. Your label audit used the authors as raters on development data. Why trust the labels?**
The labels do not come from the audit: they come from running each test on the buggy and fixed versions, a mechanical rule with no person or AI in it, identical on every split (paper Section 3). The audit (D-45) tests that rule: two raters agreed at κ {{aud2:raters:kappa}} on {{aud:n_items}} development items and their consensus matched the execution label on {{aud2:consensus_vs_execution:agreement@pct1}}, and a sealed LLM rater agreed with them at κ {{aud2:llm_rater_secondary_D84:consensus_vs_C:kappa}} (D-84, D-108; `results/audit/label_audit_scores.json`). Relabelling up to 10% of TF assertion failures left the order of the rules unchanged (D-121), and an independent blind audit is in the journal plan (J-D1).

*AI use (asked every time):* an AI assistant implemented the pipeline, ran the experiments and drafted text under the
authors' direction; every number is generated from committed outputs; the paper's declaration says so, and the authors
are responsible for all of it.
