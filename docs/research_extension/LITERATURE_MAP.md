# Literature map (searched 2026-11-11)

> **Corrected by `LITERATURE_VERIFICATION_FULLTEXT.md` (same day):** e-Otter++ uses candidate patches to select
> failing tests, so the novelty claim is narrowed; Becker et al. is submitted, not accepted; Metallaxis, not MUSE,
> is the ancestor of the decoupled observable; TestAgent uses three-voter unanimity to keep failing tests.

How this was built: two read-only literature scouts ran web searches and fetched publisher, arXiv and proceedings
pages; the lead researcher ran three further verification searches. Nothing here is cited from a title alone.
**Read** codes say what was actually opened: **F** full text (long pages partly), **A** abstract page, **S** search-result
summary only, **M** recalled from memory and not re-fetched this session. Entries marked S or M must be opened
before they are cited in the paper. Status: PR peer-reviewed, PP preprint.

Limits of this search: ACM DL and IEEE Xplore full texts were not opened; most rows rest on abstracts or search
summaries; one usage limit interrupted the scouts mid-run. Absence of a hit is not proof of absence.

## 1. Closest work on the task itself: is a failing generated test right or wrong?

| Work | Status | What it does | Evaluation | Read | Relation to this project |
|---|---|---|---|---|---|
| Wang, Zhong, Wen, Liu. *Multi-agent Assisted Automatic Test Generation for Java JSON Libraries*. APSEC 2025. arXiv:2410.09414 | PR | A GPT-4o "Test Validator" labels failing generated tests good (real library bug) or bad, few-shot with and without chain of thought, 3-query majority vote | 43 hand-labelled fastjson tests; accuracy 72.1% / 69.8%; near chance on exception failures; chain of thought did not help | F | **Same judgement as the paper's J1/SC arms**, tiny scale, hand labels, no fixed-version ground truth. Must be cited; not in `references.bib` |
| Becker, Chen, Cochran, …, Harman et al. *Just-in-Time Catching Test Generation at Meta*. FSE 2026 industry track (per Meta's blog). arXiv:2601.22832 | PR (venue from a blog) | Tests designed to fail on a diff. A rule-based assessor (15 false-positive patterns) plus LLM judges: Llama-3.3-70B log-probability and the median of three families (Llama, Gemini 3 Pro, Claude Sonnet 4). Judges read test, trace, diff and inferred intent | 22,126 tests; >98% precision at flagging false positives on 600 hand-analysed weak catches; ≈70% review-load cut; recall not measured | F | **Collides with the three-family ensemble behind KUU**. Their judges read a fixed package; no execution labels; lost bugs unmeasured. Must be cited |
| Zhao, Zhou, Cohen. *Evaluating and Mitigating the Misguidance Effect of Buggy Code in LLM-Generated Unit Tests*. ISSTA 2026. arXiv:2607.22883 | PR | Buggy code steers LLMs to bug-confirming tests; Defects4J, 318 focal methods, 11 LLMs; four execution labels (effective, misguided, false positive, true negative) | Replacing code with an LLM-written spec helps; 15–21% of specs keep the defect | F | Source of the frame and the label rule (already cited). No triage step |
| Mathews, Nagappan. *Design choices made by LLM-based test generators prevent them from finding bugs*. arXiv:2412.14137 | PP | Pass-seeking generators reject bug-revealing tests | 287 buggy student programs; CoverAgent rejected 470 and CoverUp 400 bug-revealing tests | F | The motivating harm. Counts bugs lost; proposes no triage |
| Konstantinou, Degiovanni, Papadakis. *Can we find bugs using LLM-generated oracles?* (v1: *Do LLMs generate test oracles that capture the actual or the expected program behaviour?*). arXiv:2410.21136 | PP | LLMs classify and generate oracles on correct and buggy code, 24 Java repositories | LLM oracles mostly capture actual behaviour; classification is worse than generation | A | The same judgement on assertions, before execution. Supports the paper's "judges are weak" finding |
| Hao, Lan, Zhang, Guo, Zhang. *Is This a Bug or an Obsolete Test?* ECOOP 2013. DOI 10.1007/978-3-642-39038-8_25 | PR | Classify regression-test failures as product bug or obsolete test with a decision tree on failure features | numbers not verified | S | Classical precedent for the binary task on developer tests |
| Pacheco, Ernst. *Eclat: Automatic Generation and Classification of Test Inputs*. ECOOP 2005. DOI 10.1007/11531142_22 | PR | Classify generated inputs as fault-revealing or illegal with an operational model inferred from passing runs | — | S | Precedent: uses observed behaviour as the reference, so it cannot flag a wrong reference |
| Herzig, Nagappan. *Empirically Detecting False Test Alarms Using Association Rules*. ICSE 2015. DOI 10.1109/ICSE.2015.133; Jiang et al., ICSE 2017. DOI 10.1109/ICSE.2017.71 | PR | False-alarm and cause classification for developer-written system tests | precision 0.85–0.90 (Herzig) | S | Already cited; CI-side precedent |
| Shang et al. *A Large-scale Empirical Study on Fine-tuning LLMs for Unit Testing*. ISSTA 2025. arXiv:2412.16620 | PR | Fine-tuned LLMs on Defects4J bug detection | precision 0.00–0.74%; ≈135 failing tests reviewed per bug | S | Workload baseline for the developer-effort argument |

## 2. Signals that could decide the case

| Work | Status | Signal | Read | Relation |
|---|---|---|---|---|
| Moon, Kim, Kim, Yoo. *Ask the Mutants: Mutating Faulty Programs for Fault Localization* (MUSE). ICST 2014, pp. 153–162 | PR | A mutant that turns a failing test into a passing one marks the faulty statement. Assumes the failing test is right | S (authors' PDF and proceedings record found) | **Method ancestor of the selected contribution.** Same observable, opposite question: MUSE asks *where*, given the test is right; we ask *whether* the test is right |
| Papadakis, Le Traon. *Metallaxis-FL: mutation-based fault localization*. STVR 2015 | PR | Mutants killed mostly by failing tests localise the fault | S | Same family as MUSE |
| Jahangirova, Clark, Harman, Tonella. *Test Oracle Assessment and Improvement* (OASIs). ISSTA 2016 | PR | Test generation exposes oracle false positives, mutation exposes false negatives, a human confirms | S | Closest use of mutation on *oracle quality*; in-code assertions, human in the loop, no blame decision |
| Kang, Yoon, Yoo. *Large Language Models are Few-shot Testers* (LIBRO). ICSE 2023. arXiv:2209.11515 | PR | Agreement among generated tests ranks bug-reproducing candidates; needs a bug report | S | Cross-generation agreement; the repository found this signal uninformative on real faults (AUROC 0.513, D-118) |
| Chen et al. *CodeT*. ICLR 2023. arXiv:2207.10397 | PR | Dual execution agreement between sampled programs and sampled tests | S | Agreement between populations of code and tests; selects code, does not assign blame |
| Li et al. *Nuances are the Key* (Differential Prompting). ASE 2023. arXiv:2304.11686; Liu et al. *TrickCatcher*. ACL 2025. arXiv:2404.10304 | PR | Reference versions re-derived from inferred intent, then differential testing | S / A | Program-side re-derivation on small programs; variants inherit bugs |
| Xu, Wang, Briand, Liu. *CANDOR*. arXiv:2506.02943 | PP | A panel of reasoning LLMs judges tentative oracles; curator takes consensus | S | Cross-model consensus at generation time |
| Taherkhani et al. *VALTEST*. arXiv:2411.08254; *ConVerTest*. arXiv:2602.10522 | PP | Token-entropy features or consistency voting predict test validity | A | Validity without diagnosis; assumes correct code |
| Hossain, Taylor, Dwyer. *Doc2OracLL*. FSE 2025. arXiv:2412.09360 | PR | Javadoc as the source of expected behaviour | S | Bears on RQ2's null result |
| Li, Yu, Yuan. *Escaping the Self-Repair Trap*. ASE 2026. arXiv:2608.05917 | PR | Iterative self-repair weakens oracles; static plus retrieved dynamic context | A | Already cited; runtime state used for *generation* |
| Long, Zhao, Wang. *LogicHunter*. arXiv:2607.06195 | PP | A ReAct "agentic oracle" retrieves docs, navigates source and inspects runtime state; precision 91.17% vs 29.27% best passive | A | Closest analogue of an evidence-gathering judge, in another domain (agent frameworks) |
| Amusuo et al. *FalseCrashReducer*. arXiv:2510.02185 | PP | Is a fuzzing crash the driver's fault or the project's? Crash-validation agent | S | Harness-versus-program blame for C/C++ fuzz drivers |
| Kang, Chen, Yoo, Lou. *AutoSD*. EMSE 30:45 (2025). arXiv:2304.02195 | PR | Hypothesise, run debugger scripts, conclude; assumes the test is right | S | Method ancestor for agentic evidence gathering |

## 3. Decision methods: abstention, risk control, cascades

| Work | Status | Guarantee and assumption | Read | Relation |
|---|---|---|---|---|
| Tong, Feng, Li. *Neyman-Pearson classification algorithms and NP receiver operating characteristics*. Science Advances 4(2), 2018. DOI 10.1126/sciadv.aao1659 | PR | P(type-I error > α) ≤ δ for any scoring classifier, i.i.d. class-0 sample; needs n₀ ≥ log δ / log(1−α) | S | **An i.i.d. version of "bound the share of bug-revealing tests discarded" is exactly this.** Any risk-controlled discard rule must be framed as its application |
| Geifman, El-Yaniv. *Selective classification for deep neural networks*. NIPS 2017 | PR | Selective risk ≤ r* with probability 1−δ | M | Already cited; same machinery, symmetric risk |
| Bates et al. *Distribution-free, risk-controlling prediction sets*. JACM 2021; Angelopoulos et al. *Learn then Test*. Ann. Appl. Stat. 2025; *Conformal risk control*. ICLR 2024 | PR | High-probability or expectation control of a monotone risk; i.i.d. / exchangeable | M / S / A | The general recipes |
| Dunn, Wasserman, Ramdas. *Distribution-free prediction sets for two-layer hierarchical models*. JASA 2023; Lee, Barber, Willett. arXiv:2306.06342 | PR / PP | Coverage with exchangeable groups | S / A | The cluster layer a bug-level guarantee needs |
| Jung, Brahman, Choi. *Trust or Escalate: LLM judges with provable guarantees for human agreement*. ICLR 2025. arXiv:2407.18370 | PR | Fixed-sequence testing with exact binomial bounds; cascade of judges, each calibrated at δ/|M|; 392–500 calibration items | F (v1) | **Pre-empts a generic "calibrated cascade of LLM judges"**; symmetric risk, no clustering, not SE |
| Wang, Arora, Xie et al. *Requirements-augmented generation for trustworthy acceptance testing of LLM-based software* (REAG). ASE 2026. arXiv:2608.12970 | PR | Confidence-calibrated cascade of LLM judges with accept / escalate / abstain, "backed by conformal risk control" | A | **Conformal cascade of judges inside SE**, on verdicts about LLM-app outputs. The paper a reviewer is most likely to raise against a risk-controlled cascade |
| Jeong, Kim, Park. *Towards functional correctness of code models with selective generation*. ICML 2026. arXiv:2505.13553 | PR | FDR control among non-abstained code outputs | A | Selective prediction with guarantees for code generation |
| Shahini, Metzger, Pohl. *An empirical study on just-in-time conformal defect prediction*. MSR 2024 | PR | Standard conformal validity | S | Conformal prediction already used in SE classification |
| Chen, Zaharia, Zou. *FrugalGPT*. arXiv:2305.05176 | PP (TMLR unverified) | none | M | Already cited; cascade pattern |

Small-sample floor (derived by the methods scout from the binomial bound, Learn-then-Test fixed-sequence form): with
zero observed losses on *n* exchangeable bug clusters, the smallest certifiable loss rate is α = 1 − δ^(1/n).
At δ = 0.05: n = 20 → 0.139, 40 → 0.072, 60 → 0.049. D1-test has 22 bugs with a bug-revealing test.

## 4. Background already in the paper

Oracle problem (Barr et al., TSE 2015), Defects4J (Just et al., ISSTA 2014), GitBug-Java (Silva et al., MSR 2024),
debate (Du et al., ICML 2024), self-consistency (Wang et al., ICLR 2023), TestART, ChatAssert, TaRGET, MACO,
JSTestCraft, JavaOracle, Maddila et al. All are in `paper/references.bib` and were checked against Crossref by the
original study (`paper/verification/REFERENCE_VERIFICATION.md`); they were not re-verified here.

## 5. Not found or not verified

- "MITGen / Less is more: failing test generation with LLMs" and "When AI-generated unit tests validate bugs" were not
  found under those exact titles by the scout. Both are in `references.bib` (`li2026mitgen`, `mathews2026validate`)
  with Crossref checks from the original study; the second is very likely the journal version of the Mathews and
  Nagappan preprint above. Reconcile before submission.
- TestAgent (arXiv:2607.09101): a search summary says it keeps valid failure-inducing tests; the abstract does not
  say so; full text unread. Check before claiming novelty for an end-to-end evaluation.
- No work was found that uses conformal prediction or risk control for flaky-test classification, patch correctness,
  or static-analysis alert triage with a recall guarantee (one or two searches each).
- Venue of Becker et al. rests on a company blog; TOGLL's venue on a researchr listing; several 2026 preprints were
  read at abstract level only.
