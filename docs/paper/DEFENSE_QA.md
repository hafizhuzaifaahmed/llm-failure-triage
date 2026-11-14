<!-- generated from docs/paper/src/DEFENSE_QA.src.md by scripts/paper/build_numbers.py; every number is in docs/paper/NUMBERS_MAP.csv -->
# Defense Q&A — the 29 hardest questions (D-82; updated with E6a, E6b, E8, E9, KUU, KUU-NG)

Rendered by `scripts/paper/build_numbers.py`; every number resolves from `docs/paper/NUMBERS_MAP.csv`.

**1. Your judge is a 9B local model. Isn't the study just measuring a weak judge?**
Partly, and the paper says so. The 9B judge's one-shot F1 is 0.460 (MCC 0.174), and the 12B
judge M2 scored higher on every arm (DEB on D1-test: +0.217, 95% CI
[0.109, 0.314]). The contribution is the measurement protocol and the evidence findings, which
were measured for M1 with thinking off (the ablation was not run for other judges); we do not claim the absolute numbers transfer to frontier models. A frontier reference judge (E9, Claude Sonnet 5.5)
reached DEB F1 0.823 on the same instances, so model size matters a great deal.

**2. Nothing was significant. What did you actually find?**
No confirmatory test survived Holm (smallest p_Holm 0.116, H2a). The sensitivity analysis shows why:
at 80% power this design detects ΔF1 of about 0.17 for DEB vs SC and
0.27 for J1 vs R0. What the data do show is that the failure evidence carries the signal:
without it J1 and SC fall to chance (MCC 0.031 and −0.004). Later tests, each fixed in advance in the version-controlled decision
log, were supported: H6-2 (debate above chance with a third-family judge, MCC 0.337), KUU's two on D2, the cascade over
KUU, KUU-NG's two, and the thinking judge over debate (HT-1, HT-2); most are sanity or safety checks, not evidence
that one planned architecture beats another.

**3. Isn't DEB just keep-all?**
On F1 it nearly is: DEB 0.511 against keep-all's 0.506. That is exactly why we report MCC: keep-all
has MCC 0, DEB 0.267 (95% CI [0.126, 0.405]), and DEB rejects
89.3 test faults per replicate that keep-all would keep.

**4. How valid are the labels?**
They are execution-based: PF means the test fails deterministically on the buggy version and passes on the fixed one;
no human or LLM decides them. Ambiguous double failures are excluded, and counting them as PF or TF moves DEB's F1 to
0.513 or 0.493. A two-rater blind audit (D-108) covered 71 development-split instances: all 21 PF and
50 of 89 TF, none held out (D-45).
- **Human–human:** κ 0.936, 95% bug-level CI [0.638, 1.000].
- **Consensus against the execution label:** 97.2% agreement,
  κ 0.934.
- **Where they differed:** both items were labelled TF by execution and judged PF by the raters, so the label errs, if
  at all, towards calling a bug-revealing test faulty.
- **LLM rater (secondary, D-84):** a blind Claude Opus 5.5 rater, sealed until both human sheets were committed,
  agreed with the human consensus at κ 0.903.

The audit sample is from the development split, not the held-out test.

**5. Defects4J is in every model's training data. Isn't this memorisation?**
Two checks argue against it. Removing the failure evidence brings J1 and SC to chance, so the decisions depend on the
package, not on recall of the benchmark; and on seeded faults (D2), whose fixes no model can have seen, DEB still has MCC
0.392. The external benchmark (D3) was not run, which we list as a limitation. The frontier reference
judge (E9) is the exception: see question 21.

**6. Your comparison with the base papers is unfair.**
Agreed, and the paper says no improvement over a base paper can be computed: the published figures (JSTestCraft's
audited recall 68.75%*, JavaOracle's precision 0.889*) use other
languages, labels and models. The fair comparisons are the re-implemented baselines on identical instances, where DEB
exceeds the rule baseline's F1 by +0.245.

**7. Javadoc made things worse. Isn't that implausible?**
It is what the data show, and we report it as a trend, not a finding: ΔF1 −0.050 (95% CI
[−0.091, −0.006], p 0.023, p_Holm 0.116), and S0 was best for every arm. The mixed
model's S0 odds ratio is 1.315 with an interval that includes 1
([0.904, 1.969]). One untested reading: documentation gives the judge material to
defend the test's expectation.

**8. Did you tune anything on the test set?**
No. Prompts, decoding, thresholds and the analysis were frozen on the development split before any held-out call
(D-57), and every later choice is a dated D-entry recorded before the result it governs. The development gate even
failed — one-shot F1 0.350 against R0's 0.642 — and we kept the judge and
reported it rather than re-selecting.

**9. Why both F1 and MCC?**
Because F1 on the positive class rewards a constant answer: at PF prevalence 0.339 keep-all
scores F1 0.506 with MCC 0. MCC tells chance from signal; F1 is kept because the original design fixed it in advance.

**10. Is the debate really budget-matched?**
SC and DEB both make 5 calls per instance; DEB consumed
9,188 tokens per instance against SC's 9,551,
and the token-matched arm SC-T (9,550) changes nothing: DEB − SC-T ΔF1
+0.047 ([−0.059, 0.168]).

**11. Could the judge have seen the answer in the prompt?**
Every package is checked against per-instance forbidden strings before the call; 4
D1 instances were blocked and excluded from every arm at that level. On D2, the guard's match was the injected mutated
line itself in 5 of 8 blocked instances — genuine leaks that
were stopped.

**12. 177 instances is small.**
Yes: 177 scored instances from 60 bugs, set by the real PF
yield, not by choice. The sensitivity table quantifies what that size can and cannot detect, and the external plan
sizes the follow-ups against it.

**13. The 35B judge looks better. Why isn't it a result?**
It ran after all primary work, with flash attention off, partial GPU offload and a waived memory gate (D-78). DEB was
completed later (E6a); its SC was stopped by the memory rule after 5 decisions and not
retried (D-89). On 177 instances DEB reached F1 0.644 against M1's
0.511 (+0.133, [0.018, 0.247]). It is labelled
exploratory everywhere, ran under different conditions and fed nothing back.

**14. M2 is from the same family as the generator. Self-preference?**
It cannot be excluded. A third-family judge (Ministral 3 14B, E6b) was added to probe it: M2 scored above it in every
arm (DEB ΔF1 −0.135, [−0.223, −0.039]),
which is consistent with family affinity but also with M2 simply being a different model. M1, a different family from
the generator, stays the confirmatory judge.

**15. Would anyone use this in practice?**
Only where false alarms are costly relative to missed bugs. Exploratory cost analysis: DEB is cheaper than keep-all only
while a missed bug costs less than 3.0 false alarms (on the judged sample;
7.3 at the natural prevalence). And its confidence is not usable as is: stated
0.95 against an accuracy of 0.67 (ECE
0.28).

**16. You re-implemented JSTestCraft's three-LLM vote. Does voting across families help?**
Not significantly. A budget-matched majority of one fresh call each from M1, M2 and E6b reached F1
0.614 against SC3's 0.463 (H8-1 +0.150,
[0.024, 0.279], p 0.021 before and 0.063 after Holm); VOTE5
against SC and DEB was not significant either. What changed clearly is recall: the vote lost
6 of 60 bug-revealing tests where SC lost
36. It is also close to its best member, M2 alone (fresh J1 F1 0.606).

**17. Did anything go wrong in the later runs?**
Three things, all disclosed with a D-entry before any affected number was read. The gate script crashed on a
leakage-abort bookkeeping gap and was fixed with a regression test (D-86). A unit test, run while a candidate was still
registered, made 17 unplanned calls on D1-test; they were quarantined unread, are used nowhere, and the
held-out run is now refused for any candidate that selection did not choose (D-87). The 35B's SC hit the memory rule and
was not retried (D-89).

**18. Why do your numbers differ from the base papers?**
Five reasons: language (JSTestCraft is JavaScript), label source (we execute each test on the fixed version; they audit
or judge), judge size (they use API models; our frontier reference, Claude Sonnet 5.5, reaches DEB F1
0.823 on our data), task and metric (several base papers measure generation, not triage), and
prevalence. Where the designs meet we agree: our effective-test share 1.94%
overlaps Zhao et al.'s range, a cross-family vote keeps recall high as JSTestCraft's does, and debate trades away true
positives as JavaOracle's does. Zhao et al.'s package has no generated tests, so their tests could not be re-run here.

**19. How noisy is a single run?**
For M1, J1 and SC are stable (F1 range 0.042 and 0.065 across three replicates) but
DEB is not (0.221: 0.525 / 0.614 /
0.393), so a single-replicate DEB comparison across judges is within noise. That is why E9
ran DEB three times; Sonnet's range was 0.024. When the bootstrap also resamples
replicates (D-106), the confirmatory intervals widen by up to 1.6×, and no
verdict changes.

**20. What is new beyond measurement?**
RQ4 and its answer. Keep unless unanimous (KUU): discard a failure only when three judge families agree it is a test
fault. It has no tuned parameter, and it is a safety rule, not a better classifier. RQ4 was added after the primary
study; its tests were fixed in advance in the version-controlled decision log before any of their calls (D-95, D-105, D-109), which is internal provenance, not an external registration. KUU was defined after the D1 vote (post hoc on D1) and tested once on unseen D2 under D-95.
On D2 it lost
4 of 154 bug-revealing tests against debate's
56 and beat keep-all's F1 (p Holm 0.019); its cost is a
slightly lower MCC (0.356 vs 0.392). A panel with no judge from the
generator's family (KUU-NG) lost 1 (question 27).

**21. Didn't Sonnet just memorise Defects4J?**
It may have. Its training data very likely include Defects4J and its fixes, so its D1-test score (DEB F1
0.823) may be inflated, and we call it a reference point, not a result. E9b (D-104) tests this
on the D2 seeded faults, whose fixes no model can have seen. Sonnet's DEB MCC there was 0.788
against 0.734 on D1, so there is no drop. Both hypotheses fixed in advance hold:
MCC above zero, and above M1's by +0.396. D2 mutates the fixed code, so it cannot rule out
knowledge of the original source. Our local judges' findings do not depend on Sonnet.

**22. Isn't KUU just a voting threshold?**
In mechanics, yes: it is a 3-of-3 threshold. What makes it a method is what the threshold rests on and what it adds.
- **The votes come from three different model families.** On D2, two families share a miss
  2.1 times as often as independence predicts. Three samples of one model share
  a miss 7.7 times as often, and unanimity across families lost
  4 bug-revealing tests where unanimity within one model would have lost
  18.
- **It escalates instead of out-voting.** In JSTestCraft's vote a majority out-votes a dissenting judge; unanimity
  treats dissent as a reason to keep. Disagreements can then go to a frontier judge, which raised MCC from
  0.356 to 0.666 while only 50% of the
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
- **H12-1 is supported.** Cascade MCC is above KUU's (Δ +0.311).
- **H12-2 is not.** F1 Δ −0.046 against Sonnet on every instance, 95% CI
  [−0.081, −0.018], so non-inferiority at −0.05 is not shown.

**24. Isn't KUU's success guaranteed by where it sits on the trade-off?**
Partly, yes. A rule that discards little will lose little, so we compared rules at similar discard rates on D2
(D-106, post hoc):
- **KUU** discards 13% and loses
  4 bug-revealing tests.
- **M1's debate at confidence 100** discards 14%
  and loses 6.
- **Unanimity over five samples of one model** discards more and loses
  10 (M1) or 11
  (M2), with a higher MCC.

So KUU's advantage at its operating point is small. The case for it is that it needs no tuned threshold, and that
escalation then lifts its MCC.

**25. Is the cascade worth it against simply running the frontier judge once?**
Not on MCC per dollar. On D2:

| Option | Frontier cost | MCC | Bugs with no bug-revealing test kept |
|---|---|---|---|
| Sonnet J1 on every instance | US$ 1.18 | 0.687 | 7 |
| Cascade to Sonnet DEB | US$ 3.22 | 0.666 | 2 |
| Cascade to Sonnet J1 | US$ 0.58 | 0.606 | 4 |

The cascade's value is in the last column: fewer bugs lost, which is the cost the study cares about. It is not
cost-dominant, and we do not claim it is. Its argument is local-first operation: only the escalated
50% of failures leaves the machine, against 100% for any frontier-everywhere
option. Local compute is not free either: the local tier used 8.0
GPU-seconds per instance on one laptop GPU, which no dollar figure prices.

**26. Would any of this work at a realistic prevalence?**
Precision would be low. At an assumed 5% bug-revealing share, the D2 rates give:
- KUU 0.065;
- the cascade 0.160;
- Sonnet's debate 0.271.

Most kept failures would still be test faults. These rules suit a triage stage whose job is not to lose bugs, ahead of
a human or a repair step, not one that must deliver only real faults.

**27. Isn't KUU just the lenient same-family judge vetoing discards?**
No. It was a fair worry, so we tested it with a panel fixed in advance that has no generator-family judge (KUU-NG,
D-109): M1, E6b and a fourth family, llama3.1:8b-instruct-q4_K_M, chosen on the development split, with fresh calls.
- **On D2 it lost 1 bug-revealing test** and no bug entirely, against
  10 bugs for M1's debate (H13-2 supported, p Holm
  <0.001), and its F1 beat keep-all's (H13-1, p Holm 0.003).
  D1 agrees.
- **The new judge is not lenient.** Its miss rate on bug-revealing tests is 0.318,
  against M2's 0.065 (post hoc, D-111). So the protection is consistent with families
disagreeing, not with one reluctant judge.
- **The price:** KUU-NG discards 7% of failures against KUU's
  13%, and its MCC is lower (0.288 vs
  0.356, not significant).

The earlier leave-one-out analysis (D-107, post hoc) is why we asked. M2 shares the generator's family and seldom calls a
bug-revealing test faulty (miss rate 0.065 on D2). Leaving one judge out on D2:
- **Without M2** (M1 + E6b): 16 bug-revealing tests lost against KUU's
  4.
- **Pairs that include M2:** M1 + M2 loses 6, M2 + E6b loses
  5.

In that judge set, much of the protection was M2's veto. KUU-NG shows a third family can supply it instead.

**28. Where does KUU sit against every other rule?**
The trade-off figure (D-110, post hoc, descriptive) plots each rule's share of failures discarded against its share of
bug-revealing tests lost. On D2:
- **Single-model arms** discard about half of the failures and lose a third or more of the bug-revealing tests (M1
  debate: 53% discarded, 56 lost).
- **KUU** sits in the low-loss corner (13%,
  4 lost), beside debate at confidence 100
  (14%, 6 lost), the only point whose
  threshold was tuned.
- **The cascade** reaches the frontier judge's region (38%,
  15 lost, against Sonnet debate's
  42% and 13).

No thinking-disabled local rule reaches that region on its own. Two local points come close: the thinking-enabled M1 judge (32% discarded and 8 lost; D-131) and the fully local cascade (27% and 6; post hoc, D-132); both lose fewer bug-revealing tests than the cascade but remove fewer test faults.

**29. Your label audit was done by the authors, who had seen the fix. Isn't it biased?**
It could be, and the paper says so. The raters are the authors, they saw the developer's fix, and the sample is
development-split only. The audit is still informative because the labelling rule is mechanical and identical on both
splits: it asks whether that rule matches an informed reading of the fix, and it did on
97.2% of items. A sealed LLM rater agreed with the human consensus at κ
0.903. An independent, held-out audit would be stronger.

**30. Why not just let one judge think?**
On seeded faults that would have done better than any planned arm of the same model: with its thinking mode on, M1's
one-shot judge reached MCC 0.659 against debate's 0.392 and
lost 8 bug-revealing tests against 56,
both confirmed after Holm with hypotheses fixed in advance in the version-controlled decision log (D-130, D-131). Three things
stop it being the answer. It failed its development gate (F1 0.312 against R0's
0.642), like every local judge. It still loses more bug-revealing tests than KUU
(8 against 4 on D2), so it does not
replace the safety rule. And the 12B M2's debate scored about as high on D1-test (MCC 0.571, against
0.513–0.601 over three thinking runs), so the claim holds for this judge's own
arms.

It was also not token-matched to debate; it happened to use fewer tokens
(6,753 against 9,188 per D1-test instance). The
honest reading is that for small judges, reasoning inside one call did what orchestration was meant to do.

**31. Why was thinking disabled in the original design?**
Because reasoning modes inflate tokens and change the object of study: the methodology-change register written when the study moved to local models (row L-8 of `docs/local_models/METHODOLOGY_CHANGE_IMPACT.md`, 31 Oct) and the selection protocol's thinking-mode section (`docs/local_models/MODEL_SELECTION_PROTOCOL.md`) set thinking off for every primary comparison, consistent with the original design's "no step-by-step reasoning" output contract. The protocol also checks it on every call: a non-empty thinking channel counts as an invalid answer. There is no separate decision-log entry for it; the frozen configuration records `think: false` for every model (`configs/local_models.FROZEN.json`).

**32. The thinking judge failed your gate but wins on held-out data. Is your gate meaningless, or are you ignoring it when it suits you?**
Neither. The gate is a point-estimate check on a 55-instance development pilot (D-23) whose interval is too wide to rank judges (paired difference, thinking J1 minus R0 in F1, on the instances both scored: −0.315, 95% CI [−0.67, 0.68]; `results/revision/runs/REV_THINK_DEV_M1/dev_gates.json`), and 4 of 4 local judges failed it (D-127). We did not ignore it: D-130 fixed in advance that the gate is a reported check, not a stopping rule, and the paper states the failure beside every thinking claim, so what it means here is that no small judge is validated for use on its own.

**33. The thinking finding came after the main study. Isn't the abstract headlining a post hoc result?**
It was found post hoc, on D1-test (D-129), and the abstract says so ("found on the real faults"). The headline is the confirmation: before any D2 call, D-130 fixed two hypotheses against debate, one Holm family, and the wording the paper would use for either outcome; both held (MCC 0.659 against 0.392, p_Holm <0.001; D-131, `results/revision/think_followup.json`). That is the same procedure RQ4 followed, and like RQ4 it is fixed in advance in the version-controlled decision log, not externally registered, so the journal plan asks for a registered replication (J-G1, J-L1).

**34. One model with thinking. Why should this generalise?**
It may not, and we do not claim it does: only Qwen 3.5 9B was run with thinking on (D-126, D-130), against one generator, on Java and Defects4J. What we have is consistency within that model: three D1-test runs gave balanced accuracy 0.771–0.817, and the D2 confirmation held on seeded faults (`results/revision/think_followup.json`). Other families with a thinking mode, and a token-matched comparison, are untested and in the journal plan (J-T1, J-E2).

**35. If one thinking judge gets close to the cascade, what is KUU still for?**
Safety: on D2, KUU kept 6 bug-revealing tests the thinking judge threw away and lost 2 it kept (`results/revision/think_followup.json`), and it has nothing tuned. Putting the thinking judge behind KUU's unanimity as the second tier (post hoc, D-132, `results/revision/local_cascade.json`) lost 6 bug-revealing tests and 0 bugs against the thinking judge's 8 and 2, with nothing leaving the machine, at a lower balanced accuracy (0.765 against 0.810). So KUU is the layer that protects bugs; the thinking judge is the better classifier.

**36. Does the thinking judge still depend on the failure message, as your A4 ablation showed for the non-thinking arms?**
Untested. The A4 ablation (failure section removed) was run only for the planned thinking-disabled arms (E4, `results/heldout/analysis_final/D1_M1/`); no thinking run without the failure section exists. It is in the journal plan (J-T2), with the same ablation rule and the thinking configuration of D-130.

**37. Your D2 confirmation is on seeded mutants. Why trust it for real bugs?**
D2 was built so that no model could have memorised its faults (D-62 to D-64), which is what a confirmation needs, but single-line mutants are not real faults, and the paper says D2 "controls contamination but does not replace fresh real faults". On the real faults the evidence is exploratory and consistent: three D1-test runs gave balanced accuracy 0.771–0.817 against debate's eight-run best of 0.710 (D-131). A confirmation on fresh real faults is the first item of the journal plan (J-L1, J-C2).

**38. Your label audit used the authors as raters on development data. Why trust the labels?**
The labels do not come from the audit: they come from running each test on the buggy and fixed versions, a mechanical rule with no person or AI in it, identical on every split (paper Section 3). The audit (D-45) tests that rule: two raters agreed at κ 0.936 on 71 development items and their consensus matched the execution label on 97.2%, and a sealed LLM rater agreed with them at κ 0.903 (D-84, D-108; `results/audit/label_audit_scores.json`). Relabelling up to 10% of TF assertion failures left the order of the rules unchanged (D-121), and an independent blind audit is in the journal plan (J-D1).

*AI use (asked every time):* an AI assistant implemented the pipeline, ran the experiments and drafted text under the
authors' direction; every number is generated from committed outputs; the paper's declaration says so, and the authors
are responsible for all of it.
