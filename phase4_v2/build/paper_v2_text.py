"""Text of the `_v2` manuscript edits (P7a). Used by make_paper_v2.py; every number is a \\V{key} resolved by
build_numbers_v2.py. The WDP paragraph reports the retrospective evaluation (D-151, D-152): exploratory, not externally
preregistered; its numbers come from results/extension/wdp/wdp_analysis.json."""

STATUS_WDP = (r"exploratory; retrospective; protocol frozen internally in Git before the runs; not externally "
              r"preregistered; designed after the confirmation outcomes were known")

TITLE = r"""\title[LLM Failure Triage and a Registered Test of Mutation Evidence]{Program Fault or Test Fault? LLM Triage of Failing Generated Unit Tests and a Registered Test of Mutation Evidence}"""

ABSTRACT = r"""\abstract{LLM test generators produce many failing tests, and most repair or discard every one, removing tests that expose real faults. Deciding whether a failing generated test is wrong or has found a bug is the question this paper studies. We first measure LLM triage against labels from re-running each failing test on the fixed version of its Defects4J program: on a held-out split of \V{der:test methods} focal methods, a local 9B judge's five-call debate reached F1 \V{d1:DEB|S1:f1} against keep-all's \V{d1:KA:f1}, none of five confirmatory tests survived Holm correction, and judge-only rules (voting, debate, cross-family unanimity, escalation) traded lost bug-revealing tests against kept wrong tests along one curve. We then tested, in a study registered before any of its data existed (OSF \V{osf:osf_id}), whether re-running a failing test on single-edit variants of the method under test tells which side is at fault. On \V{cc:population:instances} fresh failing tests from \V{cc:population:bugs} unseen real bugs, an edit that makes the test pass was no more frequent for bug-revealing tests than for wrong ones (difference \V{cc:family:C1:difference@signed}, 95\% CI \V{cc:family:C1:ci95}) or for failures on methods the fix did not change; an exploratory pilot had suggested \V{pil:flags:flip:diff_PF_minus_TF@signed}. A failure that no edit changes was a wrong test in \V{cc:family:C2:TF_flagged} of \V{dv:dec flagged} cases (difference \V{cc:family:C2:difference@signed}, 95\% CI \V{cc:family:C2:ci95}), but only in one of two sampling frames and mostly in two projects. Rules built on these outcomes were inconclusive after correction, and one lost a bug. The only execution-based signal that survived concerns whether the failure depends on the method under test at all, and an effect of \V{pil:flags:flip:diff_PF_minus_TF} in a pilot with \V{pil:scored:bugs_with_PF} bugs and known labels did not survive a registered test.}"""

KEYWORDS = r"""\keywords{failure triage, LLM-based test generation, test oracle, mutation analysis, registered confirmation, replication, Defects4J}"""

RQ4 = r"""\item \textbf{RQ4.} How far do judge-only rules go, and what is the strongest keep-heavy baseline? This question was exploratory in the original study; its hypotheses were fixed in advance in the version-controlled decision log before any of their calls, which is internal provenance, not an external preregistration (Appendix~\ref{app:trace}). Keep-unless-unanimous (KUU) is treated as a baseline, not as a method.
\item \textbf{RQ5} (confirmatory, registered). On fresh real faults, do single-edit counterfactual outcomes of the method under test differ between bug-revealing and wrong failing tests? (C1, a passing edit; C2, no edit changes the failure.)
\item \textbf{RQ6} (confirmatory, registered; underpowered by the registered planning). Do rules built on those outcomes improve a base rule without losing bugs? (C3, C4 and the bugs-lost outcome.)
\item \textbf{RQ7} (exploratory). Where does the decoupling signal hold (frame, project, failure type), and what is it?"""

INTRO_CONTRIB = r"""Failure triage has been studied before~\cite{liu2026jstestcraft,maddila2026agentic,fu2026javaoracle,herzig2015alarms,jiang2017alarm}, as has oracle corruption by repair~\cite{mathews2026validate,zhao2026misguidance,li2026selfrepair}, and multi-judge voting and escalation are established~\cite{wang2025json,becker2026jit,zhang2026testagent}. The contributions are empirical, and each names its evidence status:"""

CONTRIB_1 = r"""\item \emph{Measurement (existing):} an execution-grounded evaluation of LLM failure triage on repository-level Java against buggy/fixed labels --- labels from running each failing generated test on both versions, with no human or LLM judgement in the loop, a protocol frozen before any held-out call, and lost bug-revealing tests and lost bugs counted as outcomes;"""

CONTRIB_2 = r"""\item \emph{Judge-only rules as one trade-off (existing, reframed):} voting, debate, cross-family unanimity and escalation occupy one curve of lost bug-revealing tests against removed wrong tests; KUU is its keep-heavy end and serves as the baseline (on D2 it lost \V{kuu2:summary:KUU|S1:pf_lost@0} of \V{kuu2:pf_prevalence:PF} bug-revealing tests where debate lost \V{kuu2:summary:DEB|S1:pf_lost@0}), not as a method;"""

CONTRIB_3 = r"""\item \emph{A registered confirmation with a control group (confirmatory, registered, OSF \V{osf:osf_id}):} on \V{cc:population:instances} fresh failing tests in \V{cc:population:bugs} bugs, \V{cc:population:bugs_with_PF} of them with a bug-revealing test, and \V{cc:control:instances} control failures, (i) a single edit that makes the test pass is \emph{not} more frequent for bug-revealing tests (\V{cc:family:C1:difference@signed}, \V{cc:family:C1:ci95}); the pilot's \V{pil:flags:flip:diff_PF_minus_TF} is excluded, and the rate is \V{cc:control:flip_rate_PF_in_F1F2@3}, \V{cc:control:flip_rate_TF_in_F1F2@3} and \V{cc:control:flip_rate_TF@3} for right tests, wrong tests and control failures alike; (ii) a failure that no single edit changes is more frequent for wrong tests in the pooled analysis (\V{cc:family:C2:difference@signed}, \V{cc:family:C2:ci95}, Holm $p$ \V{cc:family:C2:p_holm@4}); \V{cc:family:C2:TF_flagged} of \V{dv:dec flagged} such failures are wrong tests; the effect is absent in one sampling frame and \V{arow:jackson dec tf} of the \V{cc:family:C2:TF_flagged} lie in two projects; (iii) the two certificate rules are inconclusive after correction, and one of them lost one bug of \V{cc:population:bugs_with_PF};
\item \emph{What the surviving signal is (exploratory):} frame and project concentration, failure type, the ten-mutant minimum and the two lost bugs as edits the operators could not make; a direct whole-method dependence check, evaluated retrospectively (exploratory), removed \V{wdp:primary:paired:TNR:difference@signed} more wrong tests than KUU without losing a bug, mostly as an entry check and mostly in one frame and two projects (Section~\ref{sec:surviving})."""

ROADMAP = r"""Section~\ref{sec:related} reviews related work, Section~\ref{sec:method} the design of the measurement and Section~\ref{sec:setup} its setup. Section~\ref{sec:results} reports the measurement, Section~\ref{sec:comparison} compares it with the base papers and Section~\ref{sec:ablation} the ablations. Section~\ref{sec:probes} defines the counterfactual program probes and their pilot, Section~\ref{sec:confirm} reports the registered confirmation as registered, and Section~\ref{sec:surviving} the exploratory analysis of what survived. Section~\ref{sec:discussion} discusses findings, limitations and threats, and Section~\ref{sec:conclusion} concludes. The evidence status of every result is in Table~\ref{tab:status} (Appendix~\ref{app:registration}). The study reports a registered confirmation in which one of two hypothesised signals failed and the other held with strong qualifiers."""

RELATED_MUTATION = r"""\paragraph{Mutation outcomes, patches and test validity.} Running first-order edits of a program against a failing test is the mechanism of mutation-based fault localization (MUSE~\cite{moon2014muse}, Metallaxis~\cite{papadakis2015metallaxis}) and of unified debugging (ProFL~\cite{lou2020profl}), whose CleanFix and NoneFix outcomes correspond to our flip and decoupled observables. Those techniques take the failing test as valid and infer where the fault is. We ask the question they presuppose; the executions are theirs, and only the question differs. e-Otter++~\cite{ahmed2026eotter} keeps candidate reproduction tests that fail on the original code and pass on at least one LLM-generated patch derived from the issue. It requires an issue report and selects among candidates; it does not label a test wrong. We did not reproduce it. A flip is a mutation outcome, not a repair: prior work shows that a single-edit plausible patch is usually not the developer's fix~\cite{ghanbari2019prapr,qi2015plausibility}, and our confirmation shows it is not evidence that the test is right either. Real faults are rarely reversed by one mutant~\cite{pearson2017fl}, and many are not coupled to any mutant the usual operators produce~\cite{just2014mutants}. Whole-method replacement is extreme mutation as used to find pseudo-tested methods~\cite{niedermayr2016will,vera2018pseudo}, applied there to passing test suites. Judge-only triage with several LLM voters is established: a validator taking the majority of three queries~\cite{wang2025json}, three judges combined by median in an industrial pipeline (a preprint)~\cite{becker2026jit}, and a unanimity rule that keeps a failing test only if three voters call it a real defect (a preprint)~\cite{zhang2026testagent}. Table~\ref{tab:positioning} positions the closest neighbours; it records only what the cited texts were read for.

\begin{table*}[t]
\caption{Positioning against the closest mutation- and patch-based work (descriptive; no published figure is compared with ours). ``Read'': depth at which the cited text was read for this table (full, or the named parts).}\label{tab:positioning}
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabularx}{\textwidth}{@{}l Y Y Y Y l@{}}
\toprule
Work & Variants & Required input & Failing test assumed & Inference & Read \\
\midrule
MUSE~\cite{moon2014muse} & first-order mutants & faulty program, failing and passing tests & right (program faulty by premise) & where the fault is & full \\
Metallaxis~\cite{papadakis2015metallaxis} & first-order mutants (any change of test output) & same & verdict taken as given & where the fault is & part \\
ProFL~\cite{lou2020profl} & first-order patches of a repair tool & buggy program, failing suite, all tests on all patches & the suite is the oracle & where the fault is (CleanFix, NoisyFix, NoneFix, NegFix) & part \\
e-Otter++~\cite{ahmed2026eotter} & LLM patches derived from the issue & issue text, repository, candidate tests, patches & should fail on the old code & which candidate test to return & part \\
Pseudo-tested methods~\cite{niedermayr2016will,vera2018pseudo} & whole-body replacement & passing test suite & -- (applied to passing suites) & whether the suite notices & full; part \\
Judge triage~\cite{wang2025json,becker2026jit,zhang2026testagent} & none & one failing run & -- & a verdict from reading & full; part; full \\
\midrule
This study & first-order mutants of the method under test & buggy program, the failing test & none: it is in question & which side is at fault, per test & -- \\
\bottomrule
\end{tabularx}
\end{table*}"""

CASCADE_OLD = r"""The measured arms lose bug-revealing tests, so we add a triage rule built on three principles."""
CASCADE_NEW = r"""The measured arms lose bug-revealing tests, so we also evaluate a judge-only rule built on three principles; multi-judge voting, unanimity and escalation are established patterns~\cite{wang2025json,becker2026jit,zhang2026testagent}, and in this paper the rule serves as the keep-heavy baseline, not as a proposed method."""

NEW_SECTIONS = r"""%% =====================================================================================
\section{Counterfactual Program Probes: Hypotheses and Pilot}\label{sec:probes}

\paragraph{Definitions.} Let $t$ fail on $P_B$ with focal method $m$. The probe engine compiles up to \V{cfz:parameters:max_mutants_per_focal} first-order mutants of $m$ and its same-class callees (operators ROR, AOR, COR, LVR, NEG, STD), runs $t$ on each mutant in a fresh JVM with the mutant ahead of the classpath, and classifies each run against the unmodified failure: FLIP (the test passes, and passes again on a re-run), SHIFT (it fails differently: outcome, exception, failing line or normalised message), SAME, or ERR. A test has a \emph{flip} if some mutant flips it, and is \emph{decoupled} if at least \V{cfz:parameters:min_compiled_mutants_for_decoupling} mutants compiled and none flipped or shifted it. Two certificate rules act on a base rule's label: the keep certificate (CK) keeps a test with a flip that breaks no passing sibling test (\emph{rcf}), and the decoupled-discard certificate (CD) discards a decoupled test. The engine reads only the buggy version; it never sees the fixed version, labels or developer tests (verified by inspection and by a source scan; Section~\ref{sec:confirm}).

\paragraph{Pilot (exploratory).} On the D1-test split, \V{pil:scored:PF} \PF{} and \V{pil:scored:TF} \TF{} tests from \V{pil:scored:bugs_with_PF} bugs with a bug-revealing test, a flip occurred for \V{pil:flags:flip:rate_PF} of bug-revealing tests and \V{pil:flags:flip:rate_TF} of wrong tests (difference \V{pil:flags:flip:diff_PF_minus_TF@signed}, \V{pil:flags:flip:diff_ci95}), and \V{pil:flags:decoupled:TF_flagged} of the \V{pil:flags:decoupled:n_flagged} decoupled tests were wrong (decoupled rate among \TF{} minus among \PF{}: \V{dv:pilot c2@signed}). These estimates are exploratory: the labels were known when the rules were written, the sample held \V{pil:scored:bugs_with_PF} bugs with a bug-revealing test, and one design amendment (callee mutants) was made after the first look. A confirmation on fresh data was therefore required before any claim. Table~\ref{tab:pilotconf} sets the pilot beside the confirmation.

\begin{table}[t]
\caption{Pilot beside the confirmation: tests with a flip and decoupled tests, by execution label. Pilot: exploratory (D1-test, labels known). Confirmation: confirmatory, registered (OSF \V{osf:osf_id}).}\label{tab:pilotconf}
\footnotesize
\begin{tabular}{@{}l r r r r@{}}
\toprule
 & \multicolumn{2}{c}{Flip} & \multicolumn{2}{c}{Decoupled} \\
Sample & \PF{} & \TF{} & \PF{} & \TF{} \\
\midrule
Pilot & \V{pil:flags:flip:PF_flagged}/\V{pil:scored:PF} & \V{pil:flags:flip:TF_flagged}/\V{pil:scored:TF} & \V{pil:flags:decoupled:PF_flagged}/\V{pil:scored:PF} & \V{pil:flags:decoupled:TF_flagged}/\V{pil:scored:TF} \\
Confirmation & \V{cc:family:C1:PF_flagged}/\V{cc:family:C1:PF} & \V{cc:family:C1:TF_flagged}/\V{cc:family:C1:TF} & \V{cc:family:C2:PF_flagged}/\V{cc:family:C2:PF} & \V{cc:family:C2:TF_flagged}/\V{cc:family:C2:TF} \\
\bottomrule
\end{tabular}
\end{table}

%% =====================================================================================
\section{Registered Confirmation}\label{sec:confirm}

\paragraph{Registration and what it covers.} The confirmation was registered on OSF (\V{osf:osf_id}, \V{osf:registered_utc}) before any of its tests was generated. The governing text is the attached document and the frozen code it contains; the registration's template fields were reworded at deposit and their reconciliation with the attached document is pending. Registered: hypotheses C1 (flip rate among \PF{} minus among \TF{}), C2 (decoupled rate among \TF{} minus among \PF{}), C3 (balanced accuracy of KUU + CD minus KUU) and C4 (\PF{} tests lost by 2-of-3 + CK minus 2-of-3), tested as one Holm family at $\alpha=0.05$ with a bug-level cluster bootstrap (\V{cc:resamples} resamples, seed \V{cc:seed@id}); the bugs-lost outcome with exact bounds; a control group; secondary analyses; and a list of results that would count against the method. Results in this section are confirmatory and registered, and are printed as registered; the few exploratory remarks added beside them are marked as such.

\paragraph{Frames and control group.} Only bugs the original study never generated for are used: none of the \V{atx:frame bugs} frame bugs is among the \V{atx:orig bugs} bugs labelled in the original study. Frame F1 holds the original frame's methods of unseen bugs; frame F2 holds fix-changed public or protected methods whose only exclusion from the original frame was that no bug-triggering test invokes them by name; the control group (CTRL) holds, per bug, one method in the same class that the fix did not change. A control method is a method the developer's patch did not change. It is not known to be free of defects.

\paragraph{Sealing order.} Commit and log times (UTC, 13 November 2026) record the order: labels committed at \V{atx:t labels} (commit \texttt{1a58e54}), first probe run started at \V{atx:t probe}, probe ledgers committed at \V{atx:t ledger} (\texttt{b332305}), first judge vote at \V{atx:t vote}, analysis committed at \V{atx:t analysis} (\texttt{3b017f2}). The labels and ledgers were committed before the steps that followed them; a commit time shows the order of recording, not when a file was written or read. The probe engine has no code path to the fixed version, to labels or to developer tests; this was verified by inspection and by a source scan, three of whose patterns were found to be ineffective (they contain literal backspace characters and cannot match), while a direct search found none of the names they target.

\paragraph{Population.} Table~\ref{tab:flow} gives the flow. \V{cc:population:bugs} of the \V{atx:frame bugs} frame bugs produced a scored failing test; \V{cc:population:bugs_with_PF} of them have a bug-revealing test.

\begin{table}[t]
\caption{Population flow of the confirmation (registered data). Calls: generation calls; failing: labelled failing tests; scored: \PF{} and \TF{} (AMB excluded as registered).}\label{tab:flow}
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}l r r r r r r@{}}
\toprule
Tranche & Calls & Failing & \PF{} & \TF{} & AMB & Bugs (with \PF) \\
\midrule
F1 & \V{cman:tranches:F1:generation_calls} & \V{dsf1:instances} & \V{dsf1:labels:PF} & \V{dsf1:labels:TF} & \V{dsf1:labels:AMB} & \V{cf1:population:bugs} (\V{cf1:population:bugs_with_PF}) \\
F2 & \V{cman:tranches:F2:generation_calls} & \V{dsf2:instances} & \V{dsf2:labels:PF} & \V{dsf2:labels:TF} & \V{dsf2:labels:AMB} & \V{cf2:population:bugs} (\V{cf2:population:bugs_with_PF}) \\
CTRL & \V{cman:tranches:CTRL:generation_calls} & \V{dsct:instances} & \V{cc:control:PF} & \V{dsct:labels:TF} & -- & \V{cc:control:bugs} (--) \\
\midrule
All & \V{cman:generation_calls_total} & & & & & \\
\bottomrule
\end{tabular}
\end{table}

\paragraph{Deviations and unmet planning.} \V{cc:population:bugs_with_PF} bugs carry a bug-revealing test; the registration expected \V{atx:plan lo} to \V{atx:plan hi} and classified C1 as adequately powered from a simulation at \V{atx:plan lo} or more (decision D-145, recorded before any hypothesis was computed). The registered readings are applied unchanged, but the reading of a non-supported C1 as evidence against the claim rests on a planning assumption this sample does not meet. Line endings were normalised for the pipeline's frozen-path check under WSL before any test was executed (D-144). \V{dv:voteless} packages (\V{dv:voteless tf} \TF{}, \V{dv:voteless pf} \PF) were refused by the leakage guard for all three judges and are excluded from C3 and C4 only, as registered.

\begin{table*}[t]
\caption{The registered family (confirmatory, registered; one Holm family, $\alpha=0.05$; bug-level bootstrap, \V{cc:resamples} resamples, seed \V{cc:seed@id}). Printed as registered.}\label{tab:family}
\footnotesize
\begin{tabularx}{\textwidth}{@{}l Y r l r r Y@{}}
\toprule
 & Quantity & Estimate & 95\% CI & $p$ & $p_\mathrm{Holm}$ & Registered reading \\
\midrule
C1 & $P(\text{flip}\mid\PF)-P(\text{flip}\mid\TF)$ (\V{cc:family:C1:PF_flagged}/\V{cc:family:C1:PF} \PF, \V{cc:family:C1:TF_flagged}/\V{cc:family:C1:TF} \TF) & \V{cc:family:C1:difference@signed} & \V{cc:family:C1:ci95} & \V{cc:family:C1:p@4} & \V{cc:family:C1:p_holm@4} & not supported (adequately powered by the planning: counts against the method; see D-145) \\
C2 & $P(\text{dec}\mid\TF)-P(\text{dec}\mid\PF)$ (\V{cc:family:C2:PF_flagged}/\V{cc:family:C2:PF} \PF, \V{cc:family:C2:TF_flagged}/\V{cc:family:C2:TF} \TF) & \V{cc:family:C2:difference@signed} & \V{cc:family:C2:ci95} & \V{cc:family:C2:p@4} & \V{cc:family:C2:p_holm@4} & supported \\
C3 & balanced accuracy, KUU + CD minus KUU & \V{cc:family:C3:difference@signed} & \V{cc:family:C3:ci95} & \V{cc:family:C3:p@4} & \V{cc:family:C3:p_holm@4} & not supported: inconclusive (underpowered by the planning) \\
C4 & \PF{} lost, 2-of-3 + CK minus 2-of-3 & \V{cc:family:C4:difference@signed} & \V{cc:family:C4:ci95} & \V{cc:family:C4:p@4} & \V{cc:family:C4:p_holm@4} & not supported: inconclusive (underpowered by the planning) \\
\bottomrule
\end{tabularx}
\end{table*}

\paragraph{C1: the flip did not replicate.} The flip rate was \V{dv:flip rate pf@3} for bug-revealing tests and \V{dv:flip rate tf@3} for wrong tests (Table~\ref{tab:family}); the difference \V{cc:family:C1:difference@signed} has the interval \V{cc:family:C1:ci95}, which excludes the pilot's estimate (\V{pil:flags:flip:diff_PF_minus_TF}) and includes half of it (\V{dv:pilot half@3}). The registered reading is ``not supported; counts against the method'', with the D-145 qualifier. The realized interval's half-width (\V{dv:c1 halfwidth@3}) is what the planning expected at \V{atx:plan lo} bugs, so the shortfall did not widen it beyond plan. This is not proof that no flip effect exists: a small positive effect is not excluded. The flip rate among control failures, \V{cc:control:flip_rate_TF@3}, interval \V{cc:control:flip_rate_TF_ci95}, lies with those of wrong tests (\V{cc:control:flip_rate_TF_in_F1F2@3}) and bug-revealing tests (\V{cc:control:flip_rate_PF_in_F1F2@3}); a single small edit makes a failing generated test pass about equally often whichever side is at fault.

\paragraph{C2: decoupling held, with limits.} In the pooled registered analysis a failure that no edit changes was more frequent for wrong tests (\V{cc:family:C2:difference@signed}, \V{cc:family:C2:ci95}, $p_\mathrm{Holm}$ \V{cc:family:C2:p_holm@4}): \V{cc:family:C2:TF_flagged} of the \V{dv:dec flagged} decoupled tests are wrong. The registered per-frame analysis (secondary analysis 7) gives \V{cf1:family:C2:difference@signed} \V{cf1:family:C2:ci95@ci2} in F1 and \V{cf2:family:C2:difference@signed} \V{cf2:family:C2:ci95@ci2} in F2; per-frame limits are printed to two decimals because bootstrap limits carry Monte Carlo error (exploratory, from the audit: across seeds, the standard deviation of a per-frame C1 upper limit is \V{atx:seed sd f1@3} in F1 and \V{atx:seed sd f2@3} in F2). The effect is therefore not reproduced in F1. Its concentration in two projects is an exploratory finding (Section~\ref{sec:surviving}): \V{arow:jackson dec tf} of the \V{cc:family:C2:TF_flagged} decoupled wrong tests lie in JacksonDatabind and JacksonCore, and without both projects the estimate is \V{atx:noJ est@signed} \V{atx:noJ ci}. The registered estimate is not an effect size that transfers across frames or projects.

\paragraph{C3, C4 and the rules.} Holm $p$ comes first: C3 has $p_\mathrm{Holm}$ \V{cc:family:C3:p_holm@4} (unadjusted \V{cc:family:C3:p@4}) and is inconclusive; its gain arises in F2 (\V{cf2:family:C3:difference@signed}) rather than F1 (\V{cf1:family:C3:difference@signed}) and came with one lost bug. C4 is inconclusive ($p_\mathrm{Holm}$ \V{cc:family:C4:p_holm@4}); the keep certificate's evidence (rcf) was set for \V{cc:secondary:rcf_in_place_of_flip:PF_flagged} of \V{cc:population:PF} bug-revealing tests and \V{cc:secondary:rcf_in_place_of_flip:TF_flagged} of \V{cc:population:TF} wrong tests (\V{dv:rcf rate pf@3} against \V{dv:rcf rate tf@3}), so this sample gives it no support. Table~\ref{tab:rules} leads with TPR, TNR and bugs lost; balanced accuracy, which hides a lost bug, comes last. KUU is the baseline: it lost no bug; adding CD raised TNR by \V{dv:kuu cd dtnr@3} and lost one bug (\texttt{Math\_59}).

\begin{table*}[t]
\caption{Decision rules on the \V{cc:rules:instances_with_three_votes} tests with three judge votes (\V{cc:rules:PF} \PF; reported, not tested, except through C3 and C4). Bound: exact one-sided 95\% upper bound on the bug-loss rate.}\label{tab:rules}
\footnotesize
\begin{tabular}{@{}l r r r r r r@{}}
\toprule
Rule & TPR & TNR & \PF{} lost & Bugs lost / with \PF & Bound & Bal.\ acc. \\
\midrule
KUU (baseline) & \V{cc:rules:KUU:TPR@3} & \V{cc:rules:KUU:TNR@3} & \V{cc:rules:KUU:PF_lost} & \V{cc:rules:KUU:bugs_lost} / \V{cc:rules:KUU:bugs_with_PF} & \V{cc:rules:KUU:upper95_bug_loss_rate@3} & \V{cc:rules:KUU:BA@3} \\
KUU + CD & \V{cc:rules:KUU+CD:TPR@3} & \V{cc:rules:KUU+CD:TNR@3} & \V{cc:rules:KUU+CD:PF_lost} & \V{cc:rules:KUU+CD:bugs_lost} / \V{cc:rules:KUU+CD:bugs_with_PF} & \V{cc:rules:KUU+CD:upper95_bug_loss_rate@3} & \V{cc:rules:KUU+CD:BA@3} \\
2-of-3 & \V{cc:rules:2-of-3:TPR@3} & \V{cc:rules:2-of-3:TNR@3} & \V{cc:rules:2-of-3:PF_lost} & \V{cc:rules:2-of-3:bugs_lost} / \V{cc:rules:2-of-3:bugs_with_PF} & \V{cc:rules:2-of-3:upper95_bug_loss_rate@3} & \V{cc:rules:2-of-3:BA@3} \\
2-of-3 + CK & \V{cc:rules:2-of-3+CK:TPR@3} & \V{cc:rules:2-of-3+CK:TNR@3} & \V{cc:rules:2-of-3+CK:PF_lost} & \V{cc:rules:2-of-3+CK:bugs_lost} / \V{cc:rules:2-of-3+CK:bugs_with_PF} & \V{cc:rules:2-of-3+CK:upper95_bug_loss_rate@3} & \V{cc:rules:2-of-3+CK:BA@3} \\
KUU + CK + CD & \V{cc:rules:KUU+CK+CD:TPR@3} & \V{cc:rules:KUU+CK+CD:TNR@3} & \V{cc:rules:KUU+CK+CD:PF_lost} & \V{cc:rules:KUU+CK+CD:bugs_lost} / \V{cc:rules:KUU+CK+CD:bugs_with_PF} & \V{cc:rules:KUU+CK+CD:upper95_bug_loss_rate@3} & \V{cc:rules:KUU+CK+CD:BA@3} \\
2-of-3 + CK + CD & \V{cc:rules:2-of-3+CK+CD:TPR@3} & \V{cc:rules:2-of-3+CK+CD:TNR@3} & \V{cc:rules:2-of-3+CK+CD:PF_lost} & \V{cc:rules:2-of-3+CK+CD:bugs_lost} / \V{cc:rules:2-of-3+CK+CD:bugs_with_PF} & \V{cc:rules:2-of-3+CK+CD:upper95_bug_loss_rate@3} & \V{cc:rules:2-of-3+CK+CD:BA@3} \\
keep-all + CD & \V{cc:rules:keep-all+CD:TPR@3} & \V{cc:rules:keep-all+CD:TNR@3} & \V{cc:rules:keep-all+CD:PF_lost} & \V{cc:rules:keep-all+CD:bugs_lost} / \V{cc:rules:keep-all+CD:bugs_with_PF} & \V{cc:rules:keep-all+CD:upper95_bug_loss_rate@3} & \V{cc:rules:keep-all+CD:BA@3} \\
\bottomrule
\end{tabular}
\end{table*}

\paragraph{Control group (reported, not tested).} \V{cc:control:instances} control failures from \V{cc:control:bugs} bugs, all labelled \TF; none revealed the fault. Flip rate \V{cc:control:flip_rate_TF@3} \V{cc:control:flip_rate_TF_ci95}; decoupled rate \V{cc:control:decoupled_rate_TF@3}. These failures are on methods the fix did not change, in classes that needed a fix; they are not defect-free code.

\paragraph{Registered secondary analyses.} None replaces a primary result (Table~\ref{tab:secondary}). Leaving one of \V{dv:lopo projects} projects out moves C1 between \V{dv:lopo c1 min@signed} and \V{dv:lopo c1 max@signed} and C2 between \V{dv:lopo c2 min@signed} and \V{dv:lopo c2 max@signed}; the lower end of C2 is JacksonDatabind removed, with the exploratory interval \V{atx:noJDB ci}.

\begin{table}[t]
\caption{Registered secondary analyses (confirmatory status: registered, reported; not part of the Holm family).}\label{tab:secondary}
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}l r l r r@{}}
\toprule
Analysis & Est. & 95\% CI & \PF{} & \TF{} \\
\midrule
rcf for flip & \V{cc:secondary:rcf_in_place_of_flip:difference@signed} & \V{cc:secondary:rcf_in_place_of_flip:ci95} & \V{cc:secondary:rcf_in_place_of_flip:PF_flagged} & \V{cc:secondary:rcf_in_place_of_flip:TF_flagged} \\
guarded decoupling & \V{cc:secondary:guarded_decoupling:difference@signed} & \V{cc:secondary:guarded_decoupling:ci95} & \V{cc:secondary:guarded_decoupling:PF_flagged} & \V{cc:secondary:guarded_decoupling:TF_flagged} \\
clean-operator flip & \V{cc:secondary:clean_operator_flip:difference@signed} & \V{cc:secondary:clean_operator_flip:ci95} & \V{cc:secondary:clean_operator_flip:PF_flagged} & \V{cc:secondary:clean_operator_flip:TF_flagged} \\
focal-body-only flip & \V{cc:secondary:focal_body_only_flip:difference@signed} & \V{cc:secondary:focal_body_only_flip:ci95} & \V{cc:secondary:focal_body_only_flip:PF_flagged} & \V{cc:secondary:focal_body_only_flip:TF_flagged} \\
shared flip & \V{cc:secondary:shared_flip:difference@signed} & \V{cc:secondary:shared_flip:ci95} & \V{cc:secondary:shared_flip:PF_flagged} & \V{cc:secondary:shared_flip:TF_flagged} \\
\bottomrule
\end{tabular}
\end{table}

\paragraph{The registration's counting-against list.} (1) C1 not supported: yes, with the D-145 qualifier. (2) C2 significant in the opposite direction, or its interval wholly below the pilot's estimate (\V{dv:pilot c2}): no. (3) A certificate raising the bugs lost above its base rule by more than one bug: no (KUU + CD lost one more than KUU). (4) A control flip rate close to the bug-revealing flip rate: the registration sets no numeric threshold for ``close''; the three rates are \V{cc:control:flip_rate_TF@3} (control), \V{cc:control:flip_rate_TF_in_F1F2@3} (wrong tests) and \V{cc:control:flip_rate_PF_in_F1F2@3} (bug-revealing tests), and the bug-revealing rate lies inside the control interval. Marking item 4 ``yes'' is a reading, not a computation.

%% =====================================================================================
\section{What the Surviving Signal Is (Exploratory)}\label{sec:surviving}

Everything in this section is exploratory: it was chosen after the confirmation outcomes were known, and its intervals and counts come from the independent audit's scripts, which recomputed every registered quantity from raw records and matched it (Appendix~\ref{app:registration}).

\paragraph{Frame and project concentration.} Decoupling fired for \V{dv:f1 dec tf rate@3} of wrong tests in F1 and \V{dv:f2 dec tf rate@3} in F2; the frames differ by more than sampling noise (F2 minus F1 \V{atx:het ci}). The two Jackson projects hold \V{arow:jackson tf} wrong tests and only \V{arow:jackson pf} bug-revealing tests, and \V{arow:jackson dec tf} of the \V{cc:family:C2:TF_flagged} decoupled wrong tests; \V{atx:top bugs n} bugs hold \V{atx:top bugs dec} of the \V{dv:dec flagged} decoupled tests. Without both projects the estimate is \V{atx:noJ est@signed} \V{atx:noJ ci} on \V{atx:noJ n} tests; resampling the \V{atx:projboot n} projects instead of bugs gives \V{atx:projboot ci} (indicative only); project-stratified weights give \V{atx:mh@signed}. The flag's precision held (\V{cc:family:C2:TF_flagged} of \V{dv:dec flagged}); how often it fires did not transfer across samples.

\paragraph{Failure type.} F1's wrong tests are \V{dv:f1 tf assert share@pct0} assertion failures; F2's are \V{dv:f2 tf exc share@pct0} exceptions. Decoupling lives where an exception is raised outside the method under test (Table~\ref{tab:failtype}). It is not a restatement of the stack trace: discarding every exception not raised in the method under test would remove \V{atx:stack pf} bug-revealing and \V{atx:stack tf} wrong tests, the flag \V{cc:family:C2:PF_flagged} and \V{cc:family:C2:TF_flagged}.

\begin{table}[t]
\caption{Decoupled tests by failure type and deepest stack frame, by label (exploratory; F1 and F2 pooled). Cells: tests / decoupled.}\label{tab:failtype}
\footnotesize
\begin{tabular}{@{}l r r@{}}
\toprule
Failure & \PF{} & \TF{} \\
\midrule
assertion failure & \V{dv:ft assert pf} / \V{dv:ft assert pfdec} & \V{dv:ft assert tf} / \V{dv:ft assert tfdec} \\
exception (deepest frame: method under test) & \V{atx:ft focal pf} / \V{atx:ft focal pfdec} & \V{atx:ft focal tf} / \V{atx:ft focal tfdec} \\
exception (other program code) & \V{atx:ft main pf} / \V{atx:ft main pfdec} & \V{atx:ft main tf} / \V{atx:ft main tfdec} \\
exception (the test) & \V{atx:ft test pf} / \V{atx:ft test pfdec} & \V{atx:ft test tf} / \V{atx:ft test tfdec} \\
\bottomrule
\end{tabular}
\end{table}

\paragraph{The ten-mutant minimum.} \V{arow:few all} tests have fewer than \V{cfz:parameters:min_compiled_mutants_for_decoupling} compiled mutants, so the flag can never be set for them (\V{arow:few pf} bug-revealing, \V{arow:few tf} wrong). \V{atx:minshield pf} bug-revealing and \V{atx:minshield tf} wrong tests have fewer than ten mutants and no mutant that changes the failure: they escape the certificate only through the minimum, which therefore does safety work. Among tests that could be flagged the contrast is \V{atx:elig est@signed} \V{atx:elig ci}.

\paragraph{The two lost bugs are operator gaps.} The one decoupled bug-revealing test of the confirmation, \texttt{Math\_59} (\texttt{FastMath.max(float,float)}, an assertion failure), had exactly \V{arow:math59 ncomp} compiled mutants; the pilot's lost bug, \texttt{Codec\_13}, was a replaced call. Both are faults no edit of the six operators can touch, so every mutant is silent although the failure plainly depends on the method. The flag conflates ``the failure does not depend on this method'' with ``our edits could not reach what it depends on''.

\paragraph{Qualifiers to C1.} One bug, \texttt{Lang\_57}, supplies \V{arow:lang57 pf} of the \V{cc:population:PF} bug-revealing tests (\V{dv:lang57 share@pct0}), and its method has no compilable mutant, so those tests can never flip; this is the registered handling and is conservative. Setting aside tests with no mutant, the flip rates are \V{dv:nomut pf rate@3} (\PF) and \V{dv:nomut tf rate@3} (\TF); in F1, the frame built by the pilot's own rule, \V{dv:nomut f1 pf rate@3} and \V{dv:nomut f1 tf rate@3}. As a ranking score the share of mutants that flip has AUROC \V{atx:auroc flip} (pilot: \V{pil:auroc_flip_fraction}). In the pilot, \V{atx:pilot chart flip} of its \V{pil:flags:flip:PF_flagged} flipping bug-revealing tests were in Chart (\V{atx:pilot chart flip} of \V{atx:pilot chart pf}), and Math had \V{atx:pilot math flip} of \V{atx:pilot math pf}; the pilot effect was concentrated in one project that contributes no bug-revealing test to the confirmation.

\paragraph{Votes and the flag overlap.} Of the \V{cc:family:C2:TF_flagged} decoupled wrong tests, \V{atx:dec unanimous} already had three test-fault votes and are discarded by KUU without the probe; CD adds \V{dv:cd added}. The number of program-fault votes as a score has AUROC \V{atx:auroc votes}; placing decoupled tests last raises it to \V{atx:auroc votes dec}.

\paragraph{Interval method.} With \V{cc:population:bugs_with_PF} bugs carrying the bug-revealing tests, percentile cluster-bootstrap intervals are approximate. A delete-one-bug jackknife with a normal interval gives C1 \V{atx:jk c1 ci} and C2 \V{atx:jk c2 ci}; neither changes a reading. Only bugs are resampled; projects are a second level of clustering that no registered interval reflects.

%% WDP (D-151, D-152): retrospective evaluation; exploratory; every number from results/extension/wdp/wdp_analysis.json.
\paragraph{Whole-method dependence probes: retrospective evaluation (exploratory).} Status: \emph{""" + STATUS_WDP + r"""}. The two operator gaps suggest asking the underlying question directly: does a failure change when the method under test is replaced wholesale, and is the method entered at all? The check replaces the method's body by one that records entry and throws, and by fixed-return bodies following the pseudo-tested-methods literature~\cite{niedermayr2016will,vera2018pseudo}, and orders each failing test on a ladder. Its last level, ``no entry observed and throw-invariant'' (U), is an operational entry check: it is never proof that a test cannot reach the method, and it is not evidence of a mutation effect. Protocol, code and criterion were frozen before four retrospective runs on the pilot, F1, F2 and control tests (decisions D-147 to D-151); the runs used tests whose labels were already known, and the rule was designed after the two lost bugs were seen. Discarding level-U failures beside KUU removed \V{wdp:primary:paired:TNR:difference@signed} more wrong tests than KUU (95\% CI \V{wdp:primary:paired:TNR:ci95}; Table~\ref{tab:wdp}) with no bug-revealing test and no bug lost; the pilot gave \V{wdp:secondary:1_pilot:paired:TNR:difference@signed} \V{wdp:secondary:1_pilot:paired:TNR:ci95} with no additional bug lost. No bug-revealing test reached level U (\V{wdp:secondary:3_level_U_by_label:CONF-all:U:PF_flagged} of \V{wdp:secondary:3_level_U_by_label:CONF-all:U:PF}; pilot \V{wdp:secondary:3_level_U_by_label:PILOT-all:U:PF_flagged} of \V{wdp:secondary:3_level_U_by_label:PILOT-all:U:PF}), against \V{wdp:secondary:3_level_U_by_label:CONF-all:U:TF_flagged} of \V{wdp:secondary:3_level_U_by_label:CONF-all:U:TF} wrong tests, and the decoupled bug-revealing tests of \texttt{Math\_59} and \texttt{Codec\_13} are level \V{dv:wdp math59 level} and \V{dv:wdp codec13 level}. Over the \V{wdp:pooled_bound:bugs_with_PF} bugs with a bug-revealing test, the one-sided 95\% upper bound on additional bug loss is \V{wdp:pooled_bound:upper95@3}; this bound is optimistic, because the rule was designed with knowledge of these bugs. The gain is concentrated: level U flagged \V{wdp:secondary:9_heterogeneity:F2:level_U_by_label:U:TF_flagged} of \V{wdp:secondary:9_heterogeneity:F2:level_U_by_label:U:TF} wrong tests in F2 but \V{wdp:secondary:9_heterogeneity:F1:level_U_by_label:U:TF_flagged} of \V{wdp:secondary:9_heterogeneity:F1:level_U_by_label:U:TF} in F1, and without the two Jackson projects the gain is \V{wdp:secondary:9_heterogeneity:without_Jackson:primary:paired:TNR:difference@signed} \V{wdp:secondary:9_heterogeneity:without_Jackson:primary:paired:TNR:ci95}. Of the \V{wdp:secondary:4_ladder:registered_decoupled:CONF:TF:n} wrong tests the registered certificate flagged, \V{wdp:secondary:4_ladder:registered_decoupled:CONF:TF:U} are level U: most of the surviving signal is an entry check, obtainable with one extra execution per test, rather than a mutation effect. A fresh registered test on tests no probe or judge has seen is required before any claim beyond this sample.

\begin{table}[t]
\caption{Whole-method dependence probes on the \V{wdp:populations:CONF-votes:instances} confirmation tests with three votes (\V{wdp:populations:CONF-votes:PF} bug-revealing, \V{wdp:populations:CONF-votes:bugs_with_PF} bugs with one). Exploratory, retrospective, not externally preregistered. KUU is the baseline; KUU + CD is the registered certificate. Bound: exact one-sided 95\% upper bound on the bug-loss rate.}\label{tab:wdp}
\footnotesize
\begin{tabular*}{\columnwidth}{@{\extracolsep{\fill}}lrrrr@{}}
\toprule
Rule & TPR & TNR & Bugs lost & Bound \\
\midrule
KUU & \V{wdp:secondary:6_rules:CONF-votes:KUU:TPR@3} & \V{wdp:secondary:6_rules:CONF-votes:KUU:TNR@3} & \V{wdp:secondary:6_rules:CONF-votes:KUU:bugs_lost} & \V{wdp:secondary:6_rules:CONF-votes:KUU:upper95_bug_loss_rate@3} \\
KUU + CD & \V{wdp:secondary:6_rules:CONF-votes:KUU+CD:TPR@3} & \V{wdp:secondary:6_rules:CONF-votes:KUU+CD:TNR@3} & \V{wdp:secondary:6_rules:CONF-votes:KUU+CD:bugs_lost} & \V{wdp:secondary:6_rules:CONF-votes:KUU+CD:upper95_bug_loss_rate@3} \\
KUU + CD-U & \V{wdp:secondary:6_rules:CONF-votes:KUU+CD-U:TPR@3} & \V{wdp:secondary:6_rules:CONF-votes:KUU+CD-U:TNR@3} & \V{wdp:secondary:6_rules:CONF-votes:KUU+CD-U:bugs_lost} & \V{wdp:secondary:6_rules:CONF-votes:KUU+CD-U:upper95_bug_loss_rate@3} \\
\bottomrule
\end{tabular*}
\end{table}

\paragraph{Stage B (designed before the confirmation outcomes; pre-specified, unregistered, not run).} A plan to put the probe report into the judge's prompt, with a shuffled-report control, was written before the confirmation outcomes were known and was not run: two of its report's three lines describe flips, which carried no signal here (Appendix~\ref{app:registration}).

%% =====================================================================================
"""

DISCUSSION_NEW = r"""\paragraph{Why the pilot overstated the flip.} The pilot held \V{pil:scored:bugs_with_PF} bugs with a bug-revealing test, its labels were known when the rules were written, and half of its flipping bug-revealing tests came from one project (Chart) that contributes none to the confirmation. A pilot of that size and provenance can produce an effect of \V{pil:flags:flip:diff_PF_minus_TF} that a sealed test reduces to \V{cc:family:C1:difference@signed}.

\paragraph{What blind single edits cannot show.} A flip needs an edit that happens to produce the test's expected value; real faults are rarely of that form, and wrong tests are made to pass by deleting or forcing behaviour as easily as right ones. Issue-conditioned patches, as in e-Otter++~\cite{ahmed2026eotter}, carry information about the intended behaviour that blind edits do not; its success and our null for blind edits are consistent, and we did not reproduce it. The observable that survived is the negative one: a failure insensitive to every edit of the method under test was almost always a wrong test, which is a statement about dependence on the method, not about its correctness.

\paragraph{What a practitioner can use today.} Do not keep a test because some edit makes it pass. A failure that no edit of the method under test changes is very likely a wrong test, but expect that check to fire unevenly across projects and frames, and budget for an occasional lost bug: as a conservative pre-filter beside a keep-heavy rule it has a measured cost (one bug of \V{cc:population:bugs_with_PF} here), not a verdict."""

GAPS = r"""\paragraph{Were the gaps and objectives met?} G1: triage is measured against execution labels; the confirmatory effects of the measurement are inconclusive at this size. G2: specifications gave no gain. G3: the equal-budget debate advantage is small and not significant. RQ4: judge-only rules lie on one trade-off curve, and KUU is its keep-heavy end, used here as a baseline. RQ5: the flip observable did not replicate; the decoupling observable was supported in the pooled registered analysis, not in F1. RQ6: both certificate rules are inconclusive after correction. RQ7: the surviving signal is concentrated by frame, project and failure type (exploratory)."""

THREATS_CONFIRM = r"""\paragraph{Threats specific to the registered confirmation.} \textit{Statistical conclusion.} \V{cc:population:bugs_with_PF} bugs carry a bug-revealing test against a planned \V{atx:plan lo}--\V{atx:plan hi}, and one of them holds \V{dv:lang57 share@pct0} of those tests; C2 to C4 are underpowered as registered; C1's interval has the planned width for \V{atx:plan lo} bugs and excludes the pilot's effect but not half of it; percentile cluster-bootstrap intervals with few clusters are approximate, and bootstrap limits carry Monte Carlo error. Bugs are resampled, projects are not; the project concentration and the estimate without the two Jackson projects are reported. \textit{Internal.} The ten-mutant minimum decides \V{atx:minshield pf} bug-revealing and \V{atx:minshield tf} wrong tests; frame F2 differs from the pilot's frame and is shown separately; \V{dv:voteless} packages refused by the leakage guard are excluded from C3 and C4 only. \textit{Construct.} \TF{} means ``fails identically on the fixed version'', so a test revealing a second real fault is labelled \TF; no independent audit of \TF{} labels exists for the confirmation (the labels were recomputed from the raw runs: \V{atx:labels recomputed} of \V{atx:a6 records} equal). Control methods are methods the fix did not change, in classes that needed a fix. Balanced accuracy hides a lost bug, so bugs lost and TPR/TNR lead every rule table. \textit{External.} One benchmark, one language, one generator, tests aimed at fix-changed methods or their classmates; the benchmark is likely in the models' training data (the probe uses no model). No patch-based validator was run on the same tests. \textit{Reporting.} The exploratory analyses were chosen after the confirmation; each carries its label, and the registered tables are printed unchanged and first. The registration's template fields were reworded at deposit and their reconciliation with the attached document is pending; the attached frozen bundle governs."""

CONCLUSION = r"""Against execution-based buggy/fixed labels, LLM judges with thinking disabled reached F1 \V{d1:DEB|S1:f1} at best against keep-all's \V{d1:KA:f1}, and judge-only rules lie on one curve whose keep-heavy end, KUU, served as the baseline. In a registered confirmation on \V{cc:population:instances} fresh failing tests, an edit that makes a failing test pass was not evidence that the test is right: the flip did not replicate (\V{cc:family:C1:difference@signed}, \V{cc:family:C1:ci95}). A failure that no edit changes was a wrong test in \V{cc:family:C2:TF_flagged} of \V{dv:dec flagged} cases, precise where it fires, but it fires unevenly, in one sampling frame and mostly in two projects. Next: a registered test of a direct dependence check on tests no probe or judge has seen, an LLM-patch arm without an issue report, an independent label audit, and, if a graded signal appears, the Stage B design."""

APPENDIX_REG = r"""\section{Registration, evidence status and the independent audit}\label{app:registration}
\setcounter{table}{0}\setcounter{figure}{0}% numbering restarts in each appendix

\paragraph{Evidence status.} Table~\ref{tab:status} gives the status of every kind of result in this paper.

\begin{table*}[!htb]
\caption{Evidence status of the results in this paper.}\label{tab:status}
\footnotesize
\begin{tabularx}{\textwidth}{@{}l Y@{}}
\toprule
Result & Status \\
\midrule
RQ1--RQ3 (measurement) & confirmatory family of the original study, protocol frozen before held-out calls (internal provenance) \\
RQ4 (judge-only rules; KUU) & fixed in advance in the decision log on D2, post hoc on D1; KUU is a baseline \\
C1--C4, rule table, control group, registered secondary analyses (Section~\ref{sec:confirm}) & confirmatory, registered (OSF \V{osf:osf_id}) \\
Pilot (Section~\ref{sec:probes}) & exploratory \\
Audit analyses (Section~\ref{sec:surviving}) & exploratory \\
Stage B & designed before the confirmation outcomes; pre-specified, unregistered, not run \\
Whole-method dependence probes (Section~\ref{sec:surviving}) & """ + STATUS_WDP + r""" \\
\bottomrule
\end{tabularx}
\end{table*}

\paragraph{Independent audit.} A read-only audit recomputed every registered count, estimate, interval, $p$-value, Holm adjustment, rule row and bound from the per-tranche raw records with code that imports no project module, and found no discrepancy; with the registered seed it reproduces every registered interval to four decimals, and with other seeds the per-frame limits differ in the second decimal (Monte Carlo error). Further checks: labels recomputed from the raw runs (\V{atx:labels recomputed} of \V{atx:a6 records} equal); ledger flags recomputed from each record's mutant list (\V{atx:a6 mismatches} mismatches in \V{atx:a6 records} records); the \V{atx:a7 sources} sources of the concatenated analysis inputs match their recorded hashes; and \V{atx:a8 pass} sealing-chronology checks pass. The audit's own wording was corrected once, after a replication found it had overstated the agreement of its different-seed per-frame intervals.

\paragraph{Stage B (designed, not run).} Stage B would show the probe report to the judge, against a shuffled-report control at matched budgets. It was designed before the confirmation outcomes were known and is unregistered and not run: two of the report's three lines describe flips, which carried no signal, and the third restates a rule that costs nothing to apply outside the model.
"""

EDITS = [
    ("SUB", r"%% Rebuild: python scripts/paper/build_numbers.py && latexmk -pdf PHASE4_RESEARCH_PAPER.tex (in paper/)",
     r"%% _v2 (P7a): built by scripts/paper/make_paper_v2.py from PHASE4_RESEARCH_PAPER.tex; numbers from scripts/paper/build_numbers_v2.py." "\n"
     r"%% Rebuild: python scripts/paper/make_paper_v2.py && python scripts/paper/build_numbers_v2.py && latexmk -pdf PHASE4_RESEARCH_PAPER_v2.tex (in paper/)"),
    ("SUB", r"\input{generated/numbers.tex}", r"\input{generated/numbers_v2.tex}"),
    ("LINE", r"\title[", TITLE),
    ("LINE", r"\abstract{", ABSTRACT),
    ("LINE", r"\keywords{", KEYWORDS),
    ("LINE", r"\item \textbf{RQ4.}", RQ4),
    ("LINE", r"This work does not claim to be the first study", INTRO_CONTRIB),
    ("LINE", r"\item \emph{Framework:}", CONTRIB_1),
    ("LINE", r"\item \emph{Method (RQ4):}", CONTRIB_2),
    ("LINE", r"\item \emph{Findings:}", CONTRIB_3),
    ("LINE", r"Section~\ref{sec:related} reviews related work", ROADMAP),
    ("APPEND", r"\paragraph{Debate, self-consistency and evaluation reliability.}", RELATED_MUTATION),
    ("LINE", r"\section{Proposed Methodology}\label{sec:method}", r"\section{Study Design of the Measurement}\label{sec:method}"),
    ("LINE", r"\subsection{Keep-unless-unanimous with disagreement escalation}\label{sec:cascade}",
     r"\subsection{Judge-only baseline rules: keep unless unanimous and escalation}\label{sec:cascade}"),
    ("SUB", CASCADE_OLD, CASCADE_NEW),
    ("LINE", r"\subsection{RQ4: keep unless unanimous and disagreement escalation}\label{sec:kuu}",
     r"\subsection{RQ4: judge-only rules as operating points, and KUU as the baseline}\label{sec:kuu}"),
    ("LINE", r"\section{Comparison with Base Papers and State of the Art}\label{sec:comparison}",
     r"\section{Comparison with Base Papers}\label{sec:comparison}"),
    ("SUB", r"beside our methods on identical", r"beside our arms on identical"),
    ("BEFORE", r"\section{Discussion}\label{sec:discussion}", NEW_SECTIONS.rstrip("\n")),
    ("APPEND", r"\paragraph{Practical value of KUU is limited.}", DISCUSSION_NEW),
    ("LINE", r"\paragraph{Were the gaps and objectives met?}", GAPS),
    ("APPEND", r"\textit{Construct.} The fixed version is an operational reference", THREATS_CONFIRM),
    ("LINE", r"Against execution-based buggy/fixed labels and with thinking disabled", CONCLUSION),
    ("BEFORE", r"\section{Artifact traceability}\label{app:trace}", APPENDIX_REG.rstrip("\n")),
    ("SUB", r"\bibliography{references}", r"\bibliography{references_v2}"),
]

NEW_BIB = r"""
% ---- added for the _v2 manuscript (P7a). Fields are limited to those recorded as verified in
% ---- docs/research_extension/UPDATED_NOVELTY_AND_CONTRIBUTION_ASSESSMENT.md and LITERATURE_VERIFICATION_FULLTEXT.md;
% ---- given names are omitted where those records give surnames only.
@inproceedings{moon2014muse,
  author    = {Moon and Kim and Kim and Yoo},
  title     = {Ask the Mutants: Mutating Faulty Programs for Fault Localization},
  booktitle = {IEEE International Conference on Software Testing, Verification and Validation (ICST)},
  pages     = {153--162},
  year      = {2014}
}
@article{papadakis2015metallaxis,
  author    = {Papadakis and {Le Traon}},
  title     = {Metallaxis-{FL}: mutation-based fault localization},
  journal   = {Software Testing, Verification and Reliability},
  volume    = {25},
  number    = {5--7},
  pages     = {605--628},
  year      = {2015},
  doi       = {10.1002/stvr.1509}
}
@inproceedings{lou2020profl,
  author    = {Lou and Ghanbari and Li and Zhang and Zhang and Hao and Zhang},
  title     = {Can Automated Program Repair Refine Fault Localization? A Unified Debugging Approach},
  booktitle = {ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)},
  year      = {2020},
  note      = {arXiv:1910.01270}
}
@inproceedings{ahmed2026eotter,
  author    = {Ahmed and Ganhotra and Shinnar and Hirzel},
  title     = {Heterogeneous Prompting and Execution Feedback for {SWE} Issue Test Generation and Selection},
  booktitle = {48th IEEE/ACM International Conference on Software Engineering (ICSE)},
  year      = {2026},
  doi       = {10.1145/3744916.3787837}
}
@inproceedings{ghanbari2019prapr,
  author    = {Ghanbari and Benton and Zhang},
  title     = {Practical Program Repair via Bytecode Mutation},
  booktitle = {ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)},
  pages     = {19--30},
  year      = {2019},
  doi       = {10.1145/3293882.3330559}
}
@inproceedings{qi2015plausibility,
  author    = {Qi and Long and Achour and Rinard},
  title     = {An Analysis of Patch Plausibility and Correctness for Generate-and-Validate Patch Generation Systems},
  booktitle = {ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)},
  year      = {2015}
}
@inproceedings{pearson2017fl,
  author    = {Pearson and Campos and Just and Fraser and Abreu and Ernst and Pang and Keller},
  title     = {Evaluating and improving fault localization},
  booktitle = {IEEE/ACM International Conference on Software Engineering (ICSE)},
  year      = {2017}
}
@inproceedings{just2014mutants,
  author    = {Just and Jalali and Inozemtseva and Ernst and Holmes and Fraser},
  title     = {Are Mutants a Valid Substitute for Real Faults in Software Testing?},
  booktitle = {ACM SIGSOFT International Symposium on Foundations of Software Engineering (FSE)},
  pages     = {654--665},
  year      = {2014}
}
@inproceedings{niedermayr2016will,
  author    = {Niedermayr and Juergens and Wagner},
  title     = {Will my tests tell me if {I} break this code?},
  booktitle = {International Workshop on Continuous Software Evolution and Delivery (CSED), at ICSE 2016},
  year      = {2016},
  doi       = {10.1145/2896941.2896944}
}
@article{vera2018pseudo,
  author    = {Vera-P{\'e}rez and Danglot and Monperrus and Baudry},
  title     = {A Comprehensive Study of Pseudo-tested Methods},
  journal   = {Empirical Software Engineering},
  year      = {2018},
  doi       = {10.1007/s10664-018-9653-2},
  note      = {arXiv:1807.05030; final volume not verified}
}
@misc{wang2025json,
  author    = {Wang and Zhong and Wen and Liu},
  title     = {Multi-agent Assisted Automatic Test Generation for {Java} {JSON} Libraries},
  year      = {2025},
  note      = {APSEC 2025; arXiv:2410.09414}
}
@misc{becker2026jit,
  author    = {Becker and others},
  title     = {Just-in-Time Catching Test Generation at {Meta}},
  year      = {2026},
  note      = {Preprint, arXiv:2601.22832}
}
@misc{zhang2026testagent,
  author    = {Zhang and Shang and Gu and Zhou and Fang and Chen and Xiao},
  title     = {Multi-Agent {LLM} Collaboration for Unit Test Generation via Human-Testing-Inspired Workflows},
  year      = {2026},
  note      = {Preprint, arXiv:2607.09101}
}
"""
