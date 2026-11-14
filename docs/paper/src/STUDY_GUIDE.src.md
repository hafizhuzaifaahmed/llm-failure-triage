# Study guide: the whole study in plain English

This guide is for the two authors, to read before the defense. `scripts/paper/build_numbers.py` renders it, so every
number below comes from `docs/paper/NUMBERS_MAP.csv`, the same source as the paper. "D-xx" points to the dated entry in
`docs/tracking/DECISIONS.md` where a decision was written down before the result it governs was computed; rules defined after seeing data
(KUU on D1, the fully local cascade on D2) are labelled post hoc.
Part 3 defines every term.

---

## Part 1 — the story in one page

**The problem.**
- When an AI writes unit tests, many of them fail.
- Most failures are the test's own fault: a wrong expected value, or a misused API. A few failures are real bugs in the
  program, and those are the valuable ones.
- Today's test generators either repair or delete every failing test, so they also throw away the rare test that found
  a real bug.
- Only {{zhao:subsets:all_D1:share_effective_pct@2}}% of our generated tests reveal the bug, in line with Zhao et al.'s
  {{cit:zhao lo}}–{{cit:zhao hi}}%.

**The question.** Can an AI "judge" read a failing test and say whether the program or the test is wrong? And does it
help to give the judge documentation (Javadoc), or to make several AI calls argue (debate)?

**How we measured truth without trusting anyone's opinion.**
- We used Defects4J, a collection of real Java bugs, each with the buggy version and the developer's fixed version.
- We ran every failing generated test on both versions. If it fails on the buggy version and passes on the fixed one,
  it found the bug (a "program fault", PF). If it fails on both, the test itself is wrong (a "test fault", TF).
- No person and no AI decides these labels. They come from running code.
- Two of us later checked a sample by hand and agreed with the labels on
  {{aud2:consensus_vs_execution:agreement@pct1}} of items.

**What we tested.** On {{sum:leakage_abort_exclusions:n_per_level:S1}} failures from {{r3:D1:n_bugs}} real bugs that the
models were never tuned on, a small local AI judge (9 billion parameters, its thinking mode off) decided each failure
four ways:
- once (J1);
- by majority of five tries (SC);
- by a five-call debate (DEB);
- against three simple baselines: keep everything, discard everything, and a fixed rule.

**What we found.**
1. **With thinking off, the judges barely beat keeping everything.** Debate reached F1 {{d1:DEB|S1:f1}}, against {{d1:KA:f1}} for keeping
   everything. A fairer score, MCC, shows a weak but real signal: {{d1:DEB|S1:mcc}}, where 0 is chance.
2. **None of the five tests fixed in advance reached significance.** The sample can only detect large effects.
3. **The failure message is what the judge actually uses.** Without it, the one-shot and voting judges fall to chance (exploratory, one replicate). Javadoc showed no
   detectable benefit.
4. **With thinking off, the judges throw away about half the bug-revealing tests.** Debate discarded {{e8:summary:DEB|S1:pf_lost@0}} of
   {{e6b:pf_prevalence:PF}} bug-revealing tests.
5. **A frontier AI (Claude Sonnet 5.5) is far better** (debate F1 {{e9:summary:DEB|S1|SON:f1}}). It did not drop on
   faults it cannot have seen as bugs (D2 cannot exclude knowledge of the original code).
6. **Turning on the small judge's reasoning helped more than debate or voting** (confirmed against debate; not
   token-matched). With its thinking mode on, one call
   of the same 9B model reached MCC {{tk:d2:descriptive:ThinkingM1J1:mcc}} on the unseen seeded bugs against debate's
   {{tk:d2:descriptive:M1DEB:mcc}}, and lost {{tk:d2:confirmatory:HT-2:pf_lost_thinking@int}} bug-revealing tests
   against {{tk:d2:confirmatory:HT-2:pf_lost_deb@int}}; both hypotheses were fixed in advance in the version-controlled
   decision log and held after Holm (D-130, D-131). It still failed its development gate (F1
   {{tk:gate:G_d_detail:J1_f1}} against {{tk:gate:G_d_detail:R0_f1}}), and the finding came after the main study.

**Our method.**
- **Keep unless unanimous (KUU).** Ask three judges from different AI families; throw a failure away only if all three
  say it is the test's fault.
- **Tested on unseen seeded bugs (D2), it lost {{kuu2:summary:KUU|S1:pf_lost@0}} of {{kuu2:pf_prevalence:PF}}
  bug-revealing tests**, where debate lost {{kuu2:summary:DEB|S1:pf_lost@0}}.
- **Escalation (the cascade).** Sending the cases where the three disagree to the frontier AI raised the agreement score
  from {{cas2:summary:KUU|S1:mcc}} to {{cas2:summary:CAS|S1:mcc}}. Only half the cases left the machine. It did not
  match the frontier AI used on every case.
- **Fully local (post hoc, D-132).** With the thinking-enabled small judge as the second tier instead of the frontier
  AI, nothing leaves the machine. On D2 it lost {{lc:D2:runs:62:local_cascade:pf_lost@0}} bug-revealing tests and
  {{lc:D2:runs:62:local_cascade:bugs_lost@0}} bugs (the frontier cascade {{lc:D2:comparators:Sonnetcascade:pf_lost@0}}
  and {{lc:D2:comparators:Sonnetcascade:bugs_lost@0}}), but its balanced accuracy was lower
  ({{lc:D2:runs:62:local_cascade:ba}} against {{lc:D2:comparators:Sonnetcascade:ba}}). It was defined after D2 was
  seen, so it needs fresh bugs to confirm.
- **The worry, and its answer.** Much of KUU's protection came from the judge in the generator's own family (D-107).
  So we built a panel without that family (KUU-NG, D-109) and wrote its tests down before running it. On D2 it lost
  {{kuung:D2:summary:KUUNG|S1:pf_lost@0}} bug-revealing test and no whole bug. The idea survives; the price is that it
  throws away fewer failures ({{kuung:D2:summary:KUUNG|S1:share_discarded@pct0}} against
  {{kuung:D2:summary:KUU|S1:share_discarded@pct0}}).
- **What KUU is, and is not.** It is a safety rule with nothing tuned. It is not a better classifier: its MCC is below
  debate's. The cascade's case is that it runs locally first, not that it is cheapest; the fully local version keeps every
  failure on the machine at the price of removing fewer wrong tests.

---

## Part 2 — every major decision

Each entry gives five things:
- **Decided:** what we decided.
- **Why:** the reason.
- **Rejected:** the alternative we turned down.
- **Evidence:** what supports it.
- **Q / A:** the question a reviewer will likely ask, with a two-sentence answer.

### 1. Dataset and frame (Defects4J 3.0.1, Zhao et al.'s frame)
- **Decided:** use Defects4J's real bugs, and pick methods the way Zhao et al. did: methods the fix changed that exist in
  both versions.
- **Why:** each bug has a buggy and a fixed version, which is what lets us label failures by running code.
- **Rejected:** GitHub projects without fixed versions. Those would need human labels.
- **Evidence:** the frame was rebuilt to {{split:frame_methods}} methods, against their {{split:reference_frame_zhao:methods}}.
- **Q:** "Why not your own benchmark?"
  **A:** Defects4J is the standard with a known fix for every bug. We also built a seeded-bug set (D2) to check that the
  results are not memorisation.

### 2. Local open-weight models instead of paid APIs (D-21)
- **Decided:** run every model on our own laptop GPU with Ollama.
- **Why:** zero API cost, full control, and exact reproducibility of every call.
- **Rejected:** the API models planned in Phase 2 (DeepSeek, GPT-4.1).
- **Evidence:** every call is logged and replayable.
- **Q:** "Aren't small local models too weak?"
  **A:** Yes, which is why we added stronger judges (a 12B, a 35B and the frontier Sonnet) as robustness checks. Each
  is reported beside the main judge, and all of them scored above it.

### 3. Choosing the test generator (D-22, D-44)
- **Decided:** Gemma 4 26B writes the tests.
- **Why:** it passed the bars fixed in advance on the development split (D-22): enough tests run, enough pass on the fixed
  version, and enough reveal bugs.
- **Rejected:** choosing a generator by preference; the choice followed the bars fixed in advance.
- **Evidence:** D-44's selection record.
- **Q:** "One generator only?"
  **A:** We tried to add a second, from another family (E7a), but neither candidate passed the same bars (D-102). This is
  a stated limitation.

### 4. Keeping M1 after it failed its gate (D-50, D-52)
- **Decided:** keep Qwen 3.5 9B as the main judge although it did not beat the simple rule on the development pilot.
- **Why:** the pre-written fallback ladder ran out (D-50). We chose to keep M1 and report the failure only after a
  bounded audit found no pipeline bug (D-51, D-52).
- **Rejected:** swapping judges after seeing results, which would have been a post hoc choice.
- **Evidence:** D-50 to D-52. On the held-out data M1 scored above the rule, though not significantly.
- **Q:** "So your main results describe a weak judge?"
  **A:** Yes, and the paper says so. That is why the stronger judges are reported beside it.

### 5. The 2:1 test-fault to program-fault sample (D-53)
- **Decided:** keep every program-fault failure and sample test faults at about two per program fault.
- **Why:** real bugs are rare. Without this we would have too few program faults to measure anything.
- **Rejected:** the natural mix, about one program fault in twenty failures.
- **Evidence:** the sampling weights let us report precision at the natural mix too.
- **Q:** "Doesn't that inflate your scores?"
  **A:** F1 depends on the mix, which is why we report MCC and the natural-mix precision. At a realistic 5% bug rate,
  precision is low for every rule, and we say so.

### 6. Execution labels (the framework)
- **Decided:** a failure is a program fault only if the test fails on the buggy version and passes on the fixed one.
- **Why:** no opinion is involved, and the label never passes through an AI.
- **Rejected:** human or AI labelling, which is what most prior work uses.
- **Evidence:** the human audit agreed on {{aud2:consensus_vs_execution:agreement@pct1}} of items.
- **Q:** "The fixed version may not be correct."
  **A:** True; it is an operational reference. The audit and the ambiguous-case sensitivity analysis show that this
  changes little.

### 7. Excluding ambiguous double failures (AMB)
- **Decided:** drop failures that fail on both versions for different reasons.
- **Why:** their label is genuinely unclear.
- **Rejected:** forcing them into PF or TF.
- **Evidence:** counting them either way moves debate's F1 only to {{sum:sensitivity_f1:AMB_as_PF:DEB|S1:f1}} or
  {{sum:sensitivity_f1:AMB_as_TF:DEB|S1:f1}}.
- **Q:** "Aren't these the hardest cases?"
  **A:** Possibly, so we report both ways. Neither changes a conclusion.

### 8. MCC beside F1 (D-54, D-74)
- **Decided:** report MCC (an agreement score from −1 to 1, where 0 is chance) next to F1 everywhere.
- **Why:** F1 alone rewards "keep everything" ({{d1:KA:f1}}), which has no skill at all.
- **Rejected:** F1 alone.
- **Evidence:** keep-all's MCC is 0. Re-running the tests fixed in advance on MCC changes no verdict (D-106).
- **Q:** "Did you switch metrics?"
  **A:** No. F1 stayed the primary metric fixed in advance for the five tests, and MCC was added before any held-out call.

### 9. Holm correction and the five confirmatory tests
- **Decided:** fix five tests in advance and correct their p-values together (Holm).
- **Why:** testing many things inflates false positives.
- **Rejected:** uncorrected p-values.
- **Evidence:** none survived. The design detects only differences of about {{mde:tests:H3a:mde_alpha_005@2}} F1 for
  debate against repeated voting.
- **Q:** "So you found nothing?"
  **A:** We found the effects are smaller than this sample can detect. "Inconclusive" is the honest word, not "no
  effect".

### 10. Bootstrap by bug
- **Decided:** compute confidence intervals by resampling whole bugs, not single tests.
- **Why:** tests of the same bug are related, and resampling them separately would make the intervals too narrow.
- **Rejected:** a per-test bootstrap.
- **Evidence:** also resampling the replicates widens the intervals by up to
  {{rv:two_level_bootstrap:1:widening_factor@1}} times, and no verdict changes (D-106).
- **Q:** "What about run-to-run noise?"
  **A:** Debate's F1 varied by {{rn:noise:DEB:f1:range}} across three runs. We report that, and it is why single-run
  debate comparisons are treated as noise.

### 11. D2, the seeded-bug set (D-62 to D-64)
- **Decided:** create new bugs by changing one line of each fixed method (a "mutant"), then test the judges on them.
- **Why:** no model can have seen these exact bugs or their fixes, though it may know the original code.
- **Rejected:** relying on Defects4J alone.
- **Evidence:** debate stays above chance on D2 (MCC {{d2:DEB|S1:mcc}}).
- **Q:** "A model that memorised the original code could spot the changed line."
  **A:** Correct. D2 rules out memorising the fixes, not knowing the original code, and we say so.

### 12. Leakage guard (D-70)
- **Decided:** block any prompt that contains the answer (bug ids, lines only in the fix), and drop blocked items from
  every comparison.
- **Why:** to keep the test fair.
- **Rejected:** letting the guard silently remove items from one arm only.
- **Evidence:** {{sum:leakage_abort_exclusions:counts_labelled:S1|full:instances}} D1 items were removed at S1.
- **Q:** "Did the guard ever catch a real leak?"
  **A:** Yes, on D2 it caught the mutated line itself. That is exactly what it is for.

### 13. Robustness judges (M2, the 35B, E6b)
- **Decided:** re-run with a 12B judge from the generator's family (M2), a 35B, and a judge from a third family
  (Ministral, E6b).
- **Why:** to see whether the findings depend on one model.
- **Rejected:** one judge only.
- **Evidence:** all scored above M1. Debate stayed above chance with the third family.
- **Q:** "Why are these not your main results?"
  **A:** They were added after the main study and run once each, so they are robustness checks, labelled as such.

### 14. The three-family vote (E8)
- **Decided:** re-implement JSTestCraft's idea of a vote across three model families.
- **Why:** it is the closest published idea to ours.
- **Rejected:** a vote within one model.
- **Evidence:** the vote lost far fewer bug-revealing tests ({{e8:summary:VOTE3|S1:pf_lost@0}} against debate's
  {{e8:summary:DEB|S1:pf_lost@0}}). That observation led to KUU.
- **Q:** "Isn't KUU just JSTestCraft?"
  **A:** A majority out-votes a dissenting judge; unanimity treats dissent as a reason to keep. That difference is what
  protects the bugs.

### 15. The frontier reference (E9) and its memorisation check (E9b)
- **Decided:** run Claude Sonnet 5.5 once as a reference point, then again on the seeded bugs.
- **Why:** to show how far a much stronger model goes, and whether that comes from memory.
- **Rejected:** treating Sonnet as a main result. Its sampling cannot be fixed, so it is not a replication.
- **Evidence:** debate F1 {{e9:summary:DEB|S1|SON:f1}} on D1. On D2 its MCC was {{e9b:summary:DEB|S1|SON:mcc}}, higher than
  on D1. The two runs cost US$ {{e9:spend_usd@2}} and {{e9b:spend_usd@2}}.
- **Q:** "Didn't Sonnet just memorise Defects4J?"
  **A:** It may know the code, but it did as well or better on bugs whose fixes it cannot have seen.

### 16. KUU, keep unless unanimous (D-95)
- **Decided:** discard a failure only when three judges from different families all say "test fault".
- **Why:** keep by default, because a lost bug costs more than a false alarm.
- **Rejected:** majority voting, and confidence thresholds that need tuning.
- **Evidence:** fixed in advance in the version-controlled decision log on D2 (not registered externally). It lost {{kuu2:summary:KUU|S1:pf_lost@0}} of {{kuu2:pf_prevalence:PF}} where debate
  lost {{kuu2:summary:DEB|S1:pf_lost@0}}, and F1 was above keep-all.
- **Q:** "Isn't that guaranteed by discarding little?"
  **A:** Partly. A tuned single-judge threshold does nearly as well (D-106). KUU's case is that it needs no tuned
  parameter.

### 17. Error diversity (D-105)
- **Decided:** measure whether judges from different families make different mistakes.
- **Why:** to explain why unanimity across families works.
- **Rejected:** assuming it.
- **Evidence:** two families share a miss {{ed:D2:comparison:mean_cross_family_lift@1}} times as often as chance predicts.
  Three tries of one model share a miss {{ed:D2:comparison:mean_within_family_lift@1}} times as often.
- **Q:** "Is that really about families?"
  **A:** It compares different models with repeated tries of one model, so "consistent with diversity" is the right
  phrase. We did not isolate family alone.

### 18. The cascade (D-105)
- **Decided:** if the three judges disagree, ask the frontier AI's debate; if it gives no answer, keep the test.
- **Why:** to recover accuracy cheaply, paying the frontier AI only where the local judges disagree.
- **Rejected:** sending everything to the frontier AI.
- **Evidence:** MCC rose to {{cas2:summary:CAS|S1:mcc}}; {{cas2:escalation:share_escalated@pct0}} of cases left the
  machine. Non-inferiority to the frontier AI on every case was not shown.
- **Q:** "Isn't the frontier AI alone cheaper?"
  **A:** Its one-shot judge is cheaper at a similar score, but it sends every failure off the machine and loses more
  bugs. We claim local-first operation, not lower cost.

### 19. The label audit (D-45, D-84, D-108)
- **Decided:** two raters judge {{aud:n_items}} failures blind, with a sealed AI third rater.
- **Why:** to check that the automated labels match human judgement.
- **Rejected:** no audit.
- **Evidence:** the raters agreed at κ {{aud2:raters:kappa}}. Their consensus matched the execution label on
  {{aud2:consensus_vs_execution:agreement@pct1}} of items.
- **Q:** "The raters are the authors, saw the fix, and rated development items only."
  **A:** All true and stated in the paper. The labelling rule is mechanical and the same on both splits, so checking it
  against an informed human reading on the development split still tests the rule itself.

### 20. Leave-one-judge-out (D-107)
- **Decided:** recompute KUU without each judge in turn.
- **Why:** to check whether one judge carries it.
- **Rejected:** reporting only the full panel.
- **Evidence:** without M2 (the generator's family) the pair lost {{loo:D2:summary:M1_E6B|S1:pf_lost@0}} rather than
  {{loo:D2:summary:KUU|S1:pf_lost@0}}.
- **Q:** "Isn't KUU just the friendly same-family judge vetoing discards?"
  **A:** On that panel, largely yes. KUU-NG (decision 21) shows a third family can do the same job.

### 21. KUU-NG: a panel with no generator-family judge (D-109)
- **Decided:** replace M2 with a judge from a fourth family, chosen on the dev split by the same rules as E6b, and run
  KUU again with fresh calls on D1-test and D2. Two hypotheses, written down before any call: it beats keep-all on F1
  (H13-1), and it loses fewer whole bugs than M1's debate (H13-2).
- **Why:** decision 20 showed KUU's protection might rest on a judge reluctant to blame its sibling's tests.
- **Rejected:** arguing the point without data, or dropping KUU.
- **Evidence:** phi4 failed the first check (it did not fit fully on the GPU), so the fallback,
  {{kuungsel:selected}}, was used. On D2: F1 {{kuung:D2:summary:KUUNG|S1:f1}} against keep-all's
  {{kuung:D2:summary:KA:f1}} (p Holm {{kuung:D2:hypotheses:H13-1:p_holm}}); {{kuung:D2:summary:KUUNG|S1:bugs_lost@0}}
  bugs lost against {{kuung:D2:summary:DEB|S1:bugs_lost@0}} for debate (p Holm {{kuung:D2:hypotheses:H13-2:p_holm}}).
  Both hold on D1 too. The new judge is not lenient: it misses {{kuungm:D2:kuung:NG:miss_rate_on_pf}} of bug-revealing
  tests, against M2's {{kuungm:D2:kuu:M2:miss_rate_on_pf}} (post hoc, D-111).
- **Q:** "So is the same-family judge irrelevant?"
  **A:** Not irrelevant: without it the panel discards fewer failures and its MCC is a little lower, though not
  significantly. But the protection itself does not need it: the panel without it kept the protection too.

### 22. The trade-off figure (D-110)
- **Decided:** plot every rule by the share of failures it throws away against the share of bug-revealing tests it
  loses, and mark the one rule whose threshold was tuned. It replaces the bar chart of E1 in the main text.
- **Why:** a single score like F1 hides the trade-off the study is about: throwing away work against losing bugs.
- **Rejected:** more F1 tables.
- **Evidence:** on D2, KUU throws away {{pareto:D2:points:KUU|S1:share_discarded@pct0}} and loses
  {{pareto:D2:points:KUU|S1:pf_lost@0}}; debate with a confidence-100 threshold throws away
  {{pareto:D2:points:TAU|S1:share_discarded@pct0}} and loses {{pareto:D2:points:TAU|S1:pf_lost@0}}, but that threshold
  was tuned on the dev split. The cascade reaches the frontier AI's region; no thinking-disabled local rule does on its own, and the
  thinking-enabled judge ({{tk:d2:descriptive:ThinkingM1J1:share_discarded@pct0}} discarded and {{tk:d2:descriptive:ThinkingM1J1:pf_lost@int}} lost; D-131) and the fully local cascade ({{lc:D2:runs:62:local_cascade:share_discarded@pct0}} and {{lc:D2:runs:62:local_cascade:pf_lost@0}}; post hoc, D-132) come close.
- **Q:** "Couldn't any cautious rule sit in that corner?"
  **A:** Yes, which is why the figure marks tuning. KUU gets there with nothing tuned, and the figure is labelled post
  hoc and descriptive.

### 23. Adding RQ4 and reframing the method
- **Decided:** add a fourth research question about KUU and the cascade, retitle the paper "Evaluating and Improving",
  and describe KUU as a safety rule and the cascade as local-first.
- **Why:** the method grew out of the measurement, and the paper should say so openly.
- **Rejected:** presenting KUU as if it had been planned from the start, or claiming the cascade is the cheapest option.
- **Evidence:** RQ4's tests were written down before their calls (D-95, D-105, D-109). Only
  {{cas2:escalation:share_escalated@pct0}} of failures leave the machine under the cascade. Sonnet's one-shot judge on
  every case is cheaper in dollars, but sends every failure out.
- **Q:** "Isn't adding a research question after the results a form of p-hacking?"
  **A:** Each RQ4 test was fixed in advance in the version-controlled decision log before the calls it uses, so no test was chosen after seeing its own data. But
  the choice of what to test next was made after earlier results, one follow-up at a time, and the commits are our own
  repository, not an external registration. That is why the paper asks for one fresh-data replication registered on
  OSF before any call.

---

### 24. Rates that do not depend on the mix (D-113)
- **Decided:** report, for every rule, the share of bug-revealing tests it keeps (TPR), the share of wrong tests it
  removes (TNR) and their average (balanced accuracy), with a figure on those two rates for D1 and D2 on one scale.
- **Why:** F1 changes when program faults are more or less common, and our two datasets differ in that (one in three
  failures on D1, more than half on D2), so F1 cannot be compared across them.
- **Rejected:** comparing F1 or MCC between D1 and D2.
- **Evidence:** on D2, KUU keeps {{rv11:D2:rules:KUU|S1:tpr@2}} of bug-revealing tests but removes only
  {{rv11:D2:rules:KUU|S1:tnr@2}} of wrong tests; its balanced accuracy ({{rv11:D2:rules:KUU|S1:ba}}) is below debate's
  ({{rv11:D2:rules:DEB|S1:ba}}).
- **Q:** "So is KUU worse than debate?"
  **A:** On accuracy, yes. KUU is a safety rule: it gives up accuracy to keep bugs. If bugs are rare (5%), a developer
  still sees about {{rv11:D2:rules:KUU|S1:at_prevalence:0.0500:false_alarms_per_kept_pf@0}} wrong tests for each real
  one KUU keeps, against {{rv11:D2:rules:KA:at_prevalence:0.0500:false_alarms_per_kept_pf@0}} with no triage.

### 25. Triage as a ranking (D-114)
- **Decided:** treat each judge's confidence, or a panel's vote count, as a score and ask what a developer finds by
  reading the top 10, 20 or 30% of failures, counting both tests and distinct bugs.
- **Why:** developers read failures in some order; a ranking can defer the doubtful ones instead of deleting them.
- **Evidence:** the KUU panel's vote count ranks about as well as debate's confidence (AUROC
  {{rv13:D2:rules:KUU|S1:auroc}} vs {{rv13:D2:rules:DEB|S1:auroc}} on D2). The frontier AI's top 20% on D2 are all
  bug-revealing, yet they cover fewer distinct bugs than a random 20%, because they cluster in a few bugs.
- **Q:** "Why count bugs and not tests?" **A:** A developer needs one revealing test per bug; ten for the same bug
  add little.

### 26. Trained baselines (D-115)
- **Decided:** train simple logistic regressions, tested by leaving one project out, on cheap failure features with
  and without the three judges' votes.
- **Why:** a reviewer asked whether a learned rule beats KUU, and whether the LLMs add anything over plain features.
- **Evidence:** the plain failure features barely beat chance (AUROC {{rv14:lopo:features:auroc}}); a learned
  weighting of the votes reaches balanced accuracy {{rv14:lopo:votes:ba}} but keeps fewer bug-revealing tests (TPR
  {{rv14:lopo:votes:tpr}}) than KUU ({{rv11:D1:rules:KUU|S1:tpr}}).
- **Q:** "Then why not use the learned rule?" **A:** It sits elsewhere on the same trade-off and needs training data
  with labels; KUU needs none. Which point is better depends on the cost of a lost bug.

### 27. Judging every held-out wrong test and the extra local runs (D-123 to D-127)
- **Decided:** judge the {{der:tf176 n}} held-out wrong tests that the 1:2 sample had left out ({{rv2:tf296:n_tf_judged}} of {{der:d1 test TF labelled}}
  could be judged in all), so false alarms can be counted at the real mix; and repeat debate five more times to see
  how much it varies.
- **Why:** the {{sum:prevalence:judged_sample_prevalence_by_dataset:D1:TF}} sampled wrong tests may not represent all
  {{der:d1 test TF labelled}}, and three debate runs differed a lot.
- **Rejected:** re-sampling the wrong tests (it would change the frozen sample), and reading the single thinking-on
  run as a finding (it was exploratory; entry 28 tests it properly).
- **Evidence:** KUU removes {{rv2:tf296:rules:KUU:all:tnr@2}} of all judged wrong tests and keeps
  {{rv2:tf296:rules:KUU:all:false_alarms_per_kept_pf@1}} per bug-revealing test kept at the real mix. Debate's F1 across
  {{rv2:deb8:n_replicates}} runs ranges over {{rv2:deb8:spread:f1:range}}. With its thinking mode switched on, the same small
  judge (one run) reached balanced accuracy {{rv2:think:heldout:60:ba}} and lost only {{rv2:think:heldout:60:FN@0}} of
  {{sum:prevalence:PF}} bug-revealing tests, so our main results describe the model with thinking off (followed up in entry 28).
- **Q:** "Do the small judges pass their own quality gate?" **A:** No. {{der:local judges failing G-d@int}} of
  {{der:local judges gated}} failed it, so the null results about Javadoc and debate describe weak judges.

### 28. Testing the thinking judge like KUU (D-130, D-131)
- **Decided:** follow up the one exploratory thinking-enabled run the way KUU was followed up: check its development
  gate, then test it on D2 against debate with two hypotheses fixed in advance in the version-controlled decision log before any D2 call (better
  MCC; fewer bug-revealing tests lost; one Holm family), then run D1-test twice more. The paper's wording for both
  possible outcomes was fixed in the same entry, before the result.
- **Why:** one run on the data where it was found cannot carry a headline, and a reviewer would ask whether "one
  judge that thinks" makes the whole architecture question moot.
- **Rejected:** (a) reporting the single D1 run as a finding, because it was found on those data; (b) token-matching
  it to debate, because the thinking length cannot be fixed in advance, so the paper says plainly that it is not
  token-matched; (c) dropping the follow-up when the gate failed, because the gate is a check that D-130 said would be
  reported, not a stopping rule.
- **Evidence:** the gate failed (F1 {{tk:gate:G_d_detail:J1_f1}} against R0's {{tk:gate:G_d_detail:R0_f1}} on the
  {{tk:gate:n_instances@int}}-instance pilot; {{tk:gate:G_a_valid_rate:J1@pct1}} valid outputs). On D2 both hypotheses
  held after Holm: MCC {{tk:d2:descriptive:ThinkingM1J1:mcc}} against debate's {{tk:d2:descriptive:M1DEB:mcc}} (Δ
  {{tk:d2:confirmatory:HT-1:delta}} {{tk:d2:confirmatory:HT-1:ci95}}), and {{tk:d2:confirmatory:HT-2:pf_lost_thinking@int}}
  against {{tk:d2:confirmatory:HT-2:pf_lost_deb@int}} bug-revealing tests lost; the verdict holds whichever way the
  {{tk:d2:capped@int}} outputs cut off by the cap are scored. Over three D1-test runs its balanced accuracy was
  {{tk:d1:summary:ba:min}}–{{tk:d1:summary:ba:max}}. KUU still keeps
  {{tk:d2:kuu_vs_thinking:pf_lost_by_thinking_kept_by_kuu@int}} bug-revealing tests that the thinking judge loses.
- **Q:** "So is the debate study pointless?" **A:** No, but it is scoped. With thinking off, debate did not beat
  self-consistency; with thinking on, one call beat debate. For small judges the gain came from reasoning inside one
  call, not from orchestrating several. The thinking judge still failed its gate and loses more bugs than KUU, so it is
  a better classifier, not a safety rule.

### 29. A fully local cascade (D-132, post hoc)
- **Decided:** score one more rule, with zero new calls: the cascade with its second tier replaced by the logged
  thinking-enabled small judge, so that no failure leaves the machine. Unanimous votes of the three families decide;
  disagreements go to the thinking judge, and an unusable or cut-off answer keeps the test. Exactly one rule, written
  into the decision log before it was computed.
- **Why:** the thinking judge alone came close to the frontier cascade on D2 ({{tk:d2:descriptive:ThinkingM1J1:ba}}
  against {{lc:D2:comparators:Sonnetcascade:ba}} balanced accuracy), so a panel would ask whether the frontier tier is
  needed at all.
- **Rejected:** trying several tie rules or second-tier judges (that would be tuning on D2, which has been seen), and
  calling the result a test (D2 is no longer unseen, so it is post hoc).
- **Evidence:** on D2 it lost {{lc:D2:runs:62:local_cascade:pf_lost@0}} bug-revealing tests and
  {{lc:D2:runs:62:local_cascade:bugs_lost@0}} bugs, against {{lc:D2:comparators:Sonnetcascade:pf_lost@0}} and
  {{lc:D2:comparators:Sonnetcascade:bugs_lost@0}} for the frontier cascade, but reached balanced accuracy
  {{lc:D2:runs:62:local_cascade:ba}} against {{lc:D2:comparators:Sonnetcascade:ba}} (difference
  {{lc:D2:runs:62:local_minus_sonnet_cascade:ba:delta}}, 95% CI {{lc:D2:runs:62:local_minus_sonnet_cascade:ba:ci95}}).
  On the real bugs, over the three thinking runs, it reached {{lc:D1:range:local_cascade:ba:min}}–{{lc:D1:range:local_cascade:ba:max}}.
- **Q:** "So is the frontier tier needed?" **A:** For accuracy, yes: it removes more wrong tests. For privacy and for
  keeping bugs, the fully local version did better here. It is post hoc and needs fresh bugs (journal plan J-L1).

## Part 2b — questions the thinking result invites

The same answers as DEFENSE_QA questions 31 to 38; each claim names the decision entry or result file it rests on.

**1. Why was thinking disabled in the original design?**
Because reasoning modes inflate tokens and change the object of study: the methodology-change register written when the study moved to local models (row L-8 of `docs/local_models/METHODOLOGY_CHANGE_IMPACT.md`, 31 Oct) and the selection protocol's thinking-mode section (`docs/local_models/MODEL_SELECTION_PROTOCOL.md`) set thinking off for every primary comparison, consistent with the original design's "no step-by-step reasoning" output contract. The protocol also checks it on every call: a non-empty thinking channel counts as an invalid answer. There is no separate decision-log entry for it; the frozen configuration records `think: false` for every model (`configs/local_models.FROZEN.json`).

**2. The thinking judge failed your gate but wins on held-out data. Is your gate meaningless, or are you ignoring it when it suits you?**
Neither. The gate is a point-estimate check on a {{tk:gate:n_instances@int}}-instance development pilot (D-23) whose interval is too wide to rank judges (paired difference, thinking J1 minus R0 in F1, on the instances both scored: {{tk:gate:G_d_detail:delta}}, 95% CI {{tk:gate:G_d_detail:delta_ci95_bug_bootstrap@ci2}}; `results/revision/runs/REV_THINK_DEV_M1/dev_gates.json`), and {{der:local judges failing G-d@int}} of {{der:local judges gated}} local judges failed it (D-127). We did not ignore it: D-130 fixed in advance that the gate is a reported check, not a stopping rule, and the paper states the failure beside every thinking claim, so what it means here is that no small judge is validated for use on its own.

**3. The thinking finding came after the main study. Isn't the abstract headlining a post hoc result?**
It was found post hoc, on D1-test (D-129), and the abstract says so ("found on the real faults"). The headline is the confirmation: before any D2 call, D-130 fixed two hypotheses against debate, one Holm family, and the wording the paper would use for either outcome; both held (MCC {{tk:d2:descriptive:ThinkingM1J1:mcc}} against {{tk:d2:descriptive:M1DEB:mcc}}, p_Holm {{tk:d2:confirmatory:HT-1:p_holm}}; D-131, `results/revision/think_followup.json`). That is the same procedure RQ4 followed, and like RQ4 it is fixed in advance in the version-controlled decision log, not externally registered, so the journal plan asks for a registered replication (J-G1, J-L1).

**4. One model with thinking. Why should this generalise?**
It may not, and we do not claim it does: only Qwen 3.5 9B was run with thinking on (D-126, D-130), against one generator, on Java and Defects4J. What we have is consistency within that model: three D1-test runs gave balanced accuracy {{tk:d1:summary:ba:min}}–{{tk:d1:summary:ba:max}}, and the D2 confirmation held on seeded faults (`results/revision/think_followup.json`). Other families with a thinking mode, and a token-matched comparison, are untested and in the journal plan (J-T1, J-E2).

**5. If one thinking judge gets close to the cascade, what is KUU still for?**
Safety: on D2, KUU kept {{tk:d2:kuu_vs_thinking:pf_lost_by_thinking_kept_by_kuu@int}} bug-revealing tests the thinking judge threw away and lost {{tk:d2:kuu_vs_thinking:pf_lost_by_kuu_kept_by_thinking@int}} it kept (`results/revision/think_followup.json`), and it has nothing tuned. Putting the thinking judge behind KUU's unanimity as the second tier (post hoc, D-132, `results/revision/local_cascade.json`) lost {{lc:D2:runs:62:local_cascade:pf_lost@0}} bug-revealing tests and {{lc:D2:runs:62:local_cascade:bugs_lost@0}} bugs against the thinking judge's {{lc:D2:runs:62:thinking_alone:pf_lost@0}} and {{lc:D2:runs:62:thinking_alone:bugs_lost@0}}, with nothing leaving the machine, at a lower balanced accuracy ({{lc:D2:runs:62:local_cascade:ba}} against {{lc:D2:runs:62:thinking_alone:ba}}). So KUU is the layer that protects bugs; the thinking judge is the better classifier.

**6. Does the thinking judge still depend on the failure message, as your A4 ablation showed for the non-thinking arms?**
Untested. The A4 ablation (failure section removed) was run only for the planned thinking-disabled arms (E4, `results/heldout/analysis_final/D1_M1/`); no thinking run without the failure section exists. It is in the journal plan (J-T2), with the same ablation rule and the thinking configuration of D-130.

**7. Your D2 confirmation is on seeded mutants. Why trust it for real bugs?**
D2 was built so that no model could have memorised its faults (D-62 to D-64), which is what a confirmation needs, but single-line mutants are not real faults, and the paper says D2 "controls contamination but does not replace fresh real faults". On the real faults the evidence is exploratory and consistent: three D1-test runs gave balanced accuracy {{tk:d1:summary:ba:min}}–{{tk:d1:summary:ba:max}} against debate's eight-run best of {{tk:d1:deb_eight_runs:ba:max}} (D-131). A confirmation on fresh real faults is the first item of the journal plan (J-L1, J-C2).

**8. Your label audit used the authors as raters on development data. Why trust the labels?**
The labels do not come from the audit: they come from running each test on the buggy and fixed versions, a mechanical rule with no person or AI in it, identical on every split (paper Section 3). The audit (D-45) tests that rule: two raters agreed at κ {{aud2:raters:kappa}} on {{aud:n_items}} development items and their consensus matched the execution label on {{aud2:consensus_vs_execution:agreement@pct1}}, and a sealed LLM rater agreed with them at κ {{aud2:llm_rater_secondary_D84:consensus_vs_C:kappa}} (D-84, D-108; `results/audit/label_audit_scores.json`). Relabelling up to 10% of TF assertion failures left the order of the rules unchanged (D-121), and an independent blind audit is in the journal plan (J-D1).

## Part 3 — glossary

| Term | Meaning |
|---|---|
| **AMB** | Ambiguous: a test that fails on both versions for different reasons; excluded. |
| **Ablation** | Removing one part (e.g. the failure message) to see how much it matters. |
| **Bootstrap** | Estimating uncertainty by resampling the data many times. |
| **Bug lost** | A bug none of whose bug-revealing tests was kept. |
| **Cascade** | Local unanimous votes decide; disagreements go to the frontier AI. |
| **CI (confidence interval)** | The range the true value plausibly lies in (95%). |
| **D1 / D1-test** | Real Defects4J bugs; the held-out part the models were never tuned on. |
| **D2** | Seeded bugs: one-line changes to fixed methods. |
| **DEB (debate)** | Two AI "advocates" argue for two rounds; a third call decides. Five calls. |
| **Defects4J** | A public collection of real Java bugs with buggy and fixed versions. |
| **Dev split** | Data used to develop and tune; never used for final results. |
| **E-numbers (E1–E9b)** | The experiments, numbered in the order planned. |
| **Error diversity** | Different judges making mistakes on different items. |
| **Escalation** | Sending a disagreement to a stronger judge. |
| **F1** | A score from 0 to 1 balancing caught bugs and false alarms; depends on how common bugs are. |
| **Frontier AI** | A large commercial model (here Claude Sonnet 5.5). |
| **Gate (G-a, G-b)** | A pass/fail check, fixed in advance, that a model must meet on the dev split. |
| **Holm** | A correction that keeps several tests from producing false positives. |
| **J1** | One judge call. |
| **κ (kappa)** | Agreement between raters beyond chance; 1 is perfect, 0 is chance. |
| **GPU-second** | One second of the local graphics card's time; how we report local cost. |
| **Keep-all / discard-all** | Baselines that keep, or delete, every failing test. |
| **KUU** | Keep unless unanimous: discard only when three judges of different families all say test fault. |
| **KUU-NG** | KUU with no judge from the generator's family. |
| **Leakage guard** | A check that blocks prompts containing the answer. |
| **Local-first** | Doing the work on our own machine and sending out only the hard cases. |
| **M1 / M2 / E6b** | The judges: Qwen 3.5 9B (main), Gemma 4 12B, Ministral 3 14B. |
| **MCC** | An agreement score from −1 to 1; 0 is chance; fair when classes are unbalanced. |
| **MDE** | The smallest effect the study could reliably detect. |
| **Mutant** | A copy of the code with one deliberate change. |
| **Non-inferiority** | Showing a method is not worse than another by more than a margin. |
| **p-value** | How surprising a result would be if there were no real effect. |
| **PF / TF** | Program fault (the test found a real bug) / test fault (the test is wrong). |
| **Pareto / trade-off figure** | A plot showing what each rule gives up for what it gains. |
| **Post hoc** | Defined after seeing the data; reported as such. |
| **Fixed in advance** | Written into the version-controlled decision log (`docs/tracking/DECISIONS.md`, git history) before the data were seen: internal provenance, not an external registration, so we never call it pre-registered. |
| **Thinking mode** | A switch in some models (here Qwen 3.5) that lets the model reason in hidden text before it answers. Off in every planned arm; on in the follow-up judge (D-126, D-130). It costs more output tokens and can be cut off by the output cap. |
| **TPR / TNR** | Share of bug-revealing tests kept / share of wrong tests removed; neither depends on the mix. |
| **Balanced accuracy** | The average of TPR and TNR; 0.5 is chance. |
| **AUROC** | How well a score ranks bug-revealing tests above wrong ones; 0.5 is chance, 1 is perfect. |
| **RQ** | Research question. RQ1–RQ3 are the planned ones; RQ4 (KUU and the cascade) came after. |
| **Tuned parameter** | A number chosen by looking at data, such as a confidence threshold. KUU has none. |
| **Prevalence** | How common program faults are in a sample. |
| **R0** | A fixed rule: program fault if the failure is a non-assertion error in main code. |
| **Replicate** | One complete repeat of a run. |
| **S0 / S1 / S2** | What the judge sees: code only / plus Javadoc / plus an inferred contract. |
| **SC (repeated voting)** | Five tries of the same judge, majority wins. |
| **SC-T** | Repeated voting matched to debate's token budget. |
| **Seeded bug** | A bug we introduced on purpose (D2). |
| **τ = 100** | Debate discards only when it states confidence 100; tuned on the dev split. |
