# Defense deck — content source

Rendered by `scripts/paper/build_numbers.py` into `docs/paper/DEFENSE_DECK.md`; `scripts/paper/build_deck.py` lays the
rendered text out as `paper/DEFENSE_DECK.pptx`. Every number is a key in `docs/paper/NUMBERS_MAP.csv`, so the deck
cannot disagree with the paper. Format: `## <slide id>`, then `field: value` lines (a field may repeat), then
`notes:` and the speaker script up to the next `##`. Chart values are comma-separated, in category order.

Plain-English rules for this deck: every headline is a sentence; acronyms are spelled out (the glossary slide lists
the few names we keep); one key number per slide (`stat:`), with a "Why we did this" box (`why:`). Tests, confidence
intervals and multiple-testing corrections are on the backup slides (`## stats_*`). Story order: lost bugs → truth →
the judges barely help → why → our rule → proof on unseen bugs → limits → takeaways.

## title
kicker: Advanced AI · Phase 3/4 defense
title: Can an AI tell a broken test from a real bug?
subtitle: Program fault or test fault? Evaluating and improving AI triage of generated unit tests
authors: Hafiz Huzaifa Ahmed · Saad Ilyas
affiliation: FAST-NUCES Islamabad
notes:
Good morning. When an AI writes a unit test and the test fails, either the test is wrong or the program has a bug. We asked whether an AI judge can tell which, checked its answers against the truth from running code, and then built a simple rule that stops good tests being thrown away. One line to remember: throwing failing tests away throws away real bugs.

## hook
kicker: The problem in one example
title: Throwing away failing tests throws away real bugs
code: // Defects4J Chart_24 · GrayPaintScale.getPaint
code: Paint paint = scale.getPaint(5.0);
failure: java.lang.IllegalArgumentException: Color parameter outside of expected range: Red Green Blue
verdict: This test found a real bug. The developer's fix changes exactly this line, and then the test passes.
stat: {{e8:summary:DEB|S1:pf_lost@0}} of {{e6b:pf_prevalence:PF}}
statlabel: bug-finding tests that the best planned AI judge (thinking off) still threw away
why: Test generators repair or delete every failing test. We wanted to know how many real bugs that costs.
notes:
This is a test an AI wrote for the JFreeChart library. It fails. A generator that repairs or deletes every failing test removes it, but here the failure is the bug: the developer's fix changes exactly this line, and the same test then passes. The number on the right is the point: even our best planned AI judge, with thinking off, threw away {{e8:summary:DEB|S1:pf_lost@0}} of {{e6b:pf_prevalence:PF}} tests like this one. Likely question: is the example cherry-picked? It is the rubric's worked example; the {{e8:summary:DEB|S1:pf_lost@0}}-of-{{e6b:pf_prevalence:PF}} figure covers every held-out bug.

## problem
kicker: Why this is hard
title: Tests that find bugs are rare, so a filter has to find a few needles in a haystack
stat: {{zhao:subsets:all_D1:share_effective_pct@2}}%
statlabel: of our generated tests reveal the bug (Zhao et al. report {{cit:zhao lo}}–{{cit:zhao hi}}% for six generators)
bullet: Generators run their own tests, and most failures are the test's own fault
bullet: Repair-everything and delete-everything both remove the rare test that found a bug
bullet: A filter must keep tests that found a bug and drop tests that are simply wrong
why: Because real bugs are rare, a filter can look accurate while missing most of them. That is why we count lost bugs, not only accuracy.
notes:
Generated tests fail often, and almost every failure is the test's fault. Only {{zhao:subsets:all_D1:share_effective_pct@2}} percent of our generated tests reveal the bug, in line with Zhao et al. So the filter looks for a needle in a haystack, and an overall accuracy score can hide that it misses the needles. Likely question: why not just keep everything? Keeping everything is one of our baselines, and it is surprisingly hard to beat.

## glossary
kicker: Words we use
title: A few names we keep, and what they mean
term: Bug-finding test | fails on the buggy program and passes on the fixed one (a "program fault")
term: Wrong test | fails on both versions: the test itself is wrong (a "test fault")
term: Judge | an AI model asked "is the program or the test at fault?"
term: One judge · Majority of five · Debate | ask once; ask five times and take the majority; two AIs argue and a third decides
term: F1 | a 0–1 score for catching bug-finding tests; it flatters "keep everything"
term: Agreement score (MCC) | −1 to 1; 0 means no better than chance
term: Keep unless unanimous (KUU) | our rule: three AI families must all say "wrong test" before a test is thrown away
term: Frontier AI | a large commercial model, here Claude Sonnet 5.5
term: D1 · D2 | real Defects4J bugs · seeded bugs: one-line changes to fixed code, which no AI can have seen as bugs
term: Fixed in advance | the plan and its tests written into our version-controlled decision log before the data were looked at; internal provenance, not an external registry
why: The rest of the talk uses these words and avoids other abbreviations.
notes:
Six words carry the talk. A bug-finding test fails on the buggy program and passes on the fixed one; a wrong test fails on both. F1 is the usual score, but it flatters the do-nothing policy of keeping everything, so we also report the agreement score, where zero is chance. D2 is our set of seeded bugs, which no AI can have seen during training. Likely question: why not just accuracy? Because bug-finding tests are a third or less of the sample, so accuracy rewards ignoring them.

## gap
kicker: What was missing
title: To our knowledge, no one had checked these AI judges against the truth from running the code
card: Accuracy | Earlier work scored triage by precision, small hand audits or stand-ins | RQ1 How often is the judge right, and how many bug-finding tests does it lose?
card: Documentation | Earlier work assumed the judge had a specification | RQ2 Does Javadoc or a written contract help the judge?
card: Debate | Gains from several AIs were reported without equal budgets | RQ3 Does debate beat asking one AI five times, at the same cost?
card: A safer rule | Added after the first results; its tests were written down first | RQ4 Can a rule that needs all judges to agree lose fewer bugs, and can hard cases go to a bigger AI?
why: Each research question answers one gap; the fourth grew out of what the first three showed.
notes:
Three gaps from the literature, one question each, and a fourth question we added after the first results. Say it plainly: research question four came after the primary study, but every test for it was fixed in advance in the version-controlled decision log before the data it uses were collected. Likely question: what about JSTestCraft? It audits recall on a sample; we compare with it on the "earlier papers" slide.

## framework
kicker: How we measured the truth
title: We let the code decide what is true, not a person or an AI
step: Real bug | buggy and fixed versions
step: Test generator | writes tests from the buggy code
step: Run twice | on both versions
step: Label | bug-finding = fails on buggy, passes on fixed
step: AI judges | one judge · majority · debate · baselines
step: Score | labels joined only at the end
stat: {{sum:leakage_abort_exclusions:n_per_level:S1}}
statlabel: held-out failures from {{r3:D1:n_bugs}} real bugs, with {{sum:prevalence:PF}} bug-finding tests
why: If a person or an AI decided the labels, the judges would be graded by another opinion. Running the code removes that.
notes:
Read the diagram left to right. Every failing generated test runs on the buggy and the fixed version. If it fails on the buggy one and passes on the fixed one, it found the bug. No model and no person decides that label, and the judges' answers meet it only at scoring. Everything was frozen before we touched the held-out bugs. Likely question: is the fixed version really correct? It is the developer's own fix; we exclude the rare tests that fail on both versions for different reasons, and including them barely moves the results.

## arms
kicker: How we asked the AI
title: We asked the AI judge in three ways, each given the same budget
arm: One judge | ask once | {{cost:arms:J1:calls_per_instance@0}} call
arm: Majority of five | ask five times, take the majority | {{cost:arms:SC:calls_per_instance@0}} calls
arm: Majority, matched words | the same, matched to debate's length | {{cost:arms:SC-T:calls_per_instance@0}} calls
arm: Debate | two AIs argue for two rounds, a third decides | {{cost:arms:DEB:calls_per_instance@0}} calls
baseline: Keep everything · Delete everything · A fixed rule
levels: Information levels: code only · plus Javadoc · plus a written contract
stat: {{cost:arms:DEB:calls_per_instance@0}} calls
statlabel: for both debate and majority voting, so any difference comes from the method, not from more computing
why: Earlier work compared several AIs against one without equal budgets. Matching the budget is the only fair test.
notes:
Three ways to ask, and three simple baselines. Debate and majority voting both make {{cost:arms:DEB:calls_per_instance@0}} calls, and the matched version also uses as many words as debate, so if debate wins, it is the method and not more computing. Likely question: is the budget really matched? The calls are identical, and the matched version uses {{d1:SC-T|S1:consumed_tokens_per_instance@0}} tokens against debate's {{d1:DEB|S1:consumed_tokens_per_instance@0}}.

## f1
kicker: Finding 1 · research question 1
title: With thinking off, the AI judges barely beat simply keeping every failing test
chart: F1 | {{d1:KA:f1}}, {{d1:R0:f1}}, {{d1:J1|S1:f1}}, {{d1:SC|S1:f1}}, {{d1:DEB|S1:f1}}
chart: Agreement score (MCC) | {{d1:KA:mcc}}, {{d1:R0:mcc}}, {{d1:J1|S1:mcc}}, {{d1:SC|S1:mcc}}, {{d1:DEB|S1:mcc}}
cats: Keep all, Fixed rule, One judge, Majority, Debate
stat: {{d1:DEB|S1:f1}} vs {{d1:KA:f1}}
statlabel: F1 of the best planned judge (debate, thinking off) against keeping everything. Its agreement score, {{d1:DEB|S1:mcc}}, shows a weak but real signal
why: We compared with keeping everything because a filter is only useful if it beats doing nothing.
notes:
F1 first: debate reaches {{d1:DEB|S1:f1}}, keeping everything {{d1:KA:f1}}. On F1 alone the thinking-off judges look useless. The agreement score tells the real story: keeping everything scores zero by construction, debate {{d1:DEB|S1:mcc}}, so there is a signal, just a weak one. None of our five tests fixed in advance was significant; the backup slide "statistics, slides 8 to 11" has them. Likely question: then what did you find? The next four slides say where the signal comes from.

## evidence
kicker: Why 1 · research question 2
title: The judge reads the failure message; documentation does not help
chart: With the failure message | {{d1:J1|S1:f1}}, {{d1:SC|S1:f1}}, {{d1:DEB|S1:f1}}
chart: Without it | {{d1:J1|S1|noF:f1}}, {{d1:SC|S1|noF:f1}}, {{d1:DEB|S1|noF:f1}}
cats: One judge, Majority, Debate
stat: {{d1:J1|S1|noF:mcc}}
statlabel: agreement score of the one-shot judge once the failure message is removed: chance level
why: To find out what the judge actually uses, we removed one piece of information at a time.
notes:
We removed the failure message and stack trace from the prompt. Every way of asking drops, and the one-shot and majority judges fall to chance. This argues against the judge recalling the benchmark (exploratory, one replicate). Javadoc, by contrast, did not help: code alone gave the best score for every way of asking. Likely question: isn't it odd that documentation hurts? Javadoc describes intent, not the failure, and with a small judge extra text dilutes the one clue it uses.

## debate
kicker: Why 2 · research question 3
title: Debate is no better than majority voting, and it changes from run to run
chart: Change in F1 across three runs | {{rn:noise:J1:f1:range}}, {{rn:noise:SC:f1:range}}, {{rn:noise:DEB:f1:range}}, {{e9:deb_run_to_run_spread:sonnet:f1:range}}
cats: One judge (small), Majority (small), Debate (small), Debate (frontier AI)
stat: {{rn:noise:DEB:f1:range}}
statlabel: how much the small debate's F1 moved between three identical runs ({{rn:noise:DEB:f1:per_replicate:0}} / {{rn:noise:DEB:f1:per_replicate:1}} / {{rn:noise:DEB:f1:per_replicate:2}})
why: Debate is popular, so we gave it a fair fight: the same budget as voting, and three repeated runs.
notes:
At equal budget, debate's advantage over majority voting is small and not significant. And debate is unstable: across three identical runs its F1 moved by {{rn:noise:DEB:f1:range}}, against {{e9:deb_run_to_run_spread:sonnet:f1:range}} for the frontier AI. So a single debate run tells you little. Likely question: how big a difference could you detect? About {{mde:tests:H3a:mde_alpha_005@2}} in F1, far above anything we observed; the statistics backup has it.

## thinking
kicker: Why 2b · research question 3 · confirmed against debate on unseen bugs (D-130, D-131)
title: Letting one judge reason first helped more than debate or voting, but it still fails its quality gate
chart: Agreement score (MCC) on unseen seeded bugs | {{d2:J1|S1:mcc}}, {{d2:SC|S1:mcc}}, {{d2:DEB|S1:mcc}}, {{tk:d2:descriptive:ThinkingM1J1:mcc}}
cats: One judge (thinking off), Majority of five, Debate, One judge (thinking on)
stat: {{tk:d2:descriptive:ThinkingM1J1:mcc}} vs {{tk:d2:descriptive:M1DEB:mcc}}
statlabel: agreement score with thinking on, against debate; {{tk:d2:confirmatory:HT-2:pf_lost_thinking@int}} vs {{tk:d2:confirmatory:HT-2:pf_lost_deb@int}} bug-finding tests lost; both held after correction. It still failed its quality gate (F1 {{tk:gate:G_d_detail:J1_f1}} vs {{tk:gate:G_d_detail:R0_f1}})
why: The same small AI has a "thinking" switch. We tested whether reasoning inside one call does what extra calls were meant to do.
notes:
Every planned arm ran with the judge's thinking mode off. With it on, one call of the same 9B model reached an agreement score of {{tk:d2:descriptive:ThinkingM1J1:mcc}} on the seeded bugs against debate's {{tk:d2:descriptive:M1DEB:mcc}}, and lost {{tk:d2:confirmatory:HT-2:pf_lost_thinking@int}} bug-finding tests against {{tk:d2:confirmatory:HT-2:pf_lost_deb@int}}. Both hypotheses were fixed in advance in the version-controlled decision log before those calls, and both held after correction. On the real bugs, three runs gave balanced accuracy {{tk:d1:summary:ba:min}} to {{tk:d1:summary:ba:max}}. Say the limits out loud: it failed the same quality gate as every small judge, it was not token-matched to debate (it happened to use fewer tokens), it is one model, and the finding came after the main study. Likely question: why not just let one judge think? Backup question 30.

## ceiling
kicker: Why 3 · the size of the judge
title: A much larger AI does far better, which points to the small judge, not the method, as the limit
chart: Small local judge (9B) | {{d1:J1|S1:f1}}, {{d1:DEB|S1:f1}}
chart: Claude Sonnet 5.5 | {{e9:summary:J1|S1|SON:f1}}, {{e9:summary:DEB|S1|SON:f1}}
cats: One judge, Debate
stat: {{e9:summary:DEB|S1|SON:f1}}
statlabel: F1 of the frontier AI's debate on the same failures. On seeded bugs it cannot have seen as bugs, it did not drop
why: A reference point tells us whether the task is hard or our judge is small. We ran the frontier AI as a reference, not as our method.
notes:
We ran Claude Sonnet 5.5 on the same failures as a reference point. It is not a replication: a different runtime and default sampling. Debate reaches {{e9:summary:DEB|S1|SON:f1}}, and here debate does beat a single call. So debate can help once the judge is capable; with a small judge, capability is the limit, and turning on its reasoning (previous slide) is one way to raise it. Say the caveat out loud: Sonnet very likely saw Defects4J in training. On the seeded bugs, which it cannot have seen, its agreement score was {{e9b:summary:DEB|S1|SON:mcc}}, no drop. Likely question: didn't Sonnet just memorise Defects4J? Backup question 21.

## cost
kicker: The clue
title: Three different AIs voting together lost far fewer bug-finding tests than our main judge's debate or voting
chart: Bug-finding tests lost (of {{e6b:pf_prevalence:PF}}) | {{d1:DA:pf_lost@0}}, {{e8:summary:SC|S1:pf_lost@0}}, {{e8:summary:DEB|S1:pf_lost@0}}, {{e8:summary:VOTE3|S1:pf_lost@0}}
cats: Delete all, Majority, Debate, Three-family vote
stat: {{e8:summary:VOTE3|S1:pf_lost@0}} of {{e6b:pf_prevalence:PF}}
statlabel: bug-finding tests lost by a vote across three AI families, against {{e8:summary:DEB|S1:pf_lost@0}} for debate
why: Different AI families make different mistakes. If they rarely fail on the same test, needing all of them to agree should protect bugs.
notes:
Debate threw away {{e8:summary:DEB|S1:pf_lost@0}} of {{e6b:pf_prevalence:PF}} bug-finding tests. A vote across three model families lost only {{e8:summary:VOTE3|S1:pf_lost@0}}. That observation is where our rule comes from, which is why the rule counts as post hoc on these real bugs and had to be tested again on new ones. Likely question: where is the break-even? Debate beats keeping everything only while one missed bug costs less than {{xd:D1:DEB:breakeven_vs_KA@1}} wrong tests kept.

## kuu
kicker: Our rule · research question 4
title: Throw a failing test away only when three different AIs all say the test is wrong
judge: Qwen 3.5 · 9B
judge: Gemma 4 · 12B
judge: Ministral 3 · 14B
rule: Do all three say "the test is wrong"?
yes: Throw it away
no: Keep it (also if any answer is unusable)
property: Nothing to tune · one call per AI · keeps by default
origin: The rule was defined after the vote on real bugs (post hoc there) and then tested once on unseen seeded bugs, under a plan written down first (D-95).
why: Losing a real bug costs more than keeping a wrong test, so the safe default is to keep, and to throw away only on strong evidence.
notes:
Our rule, keep unless unanimous, is one sentence. Ask one AI from each of three families. Throw the test away only if all three say the test is wrong; otherwise, including any unusable answer, keep it. There is nothing to tune. In JSTestCraft's vote a majority out-votes a dissenting judge; in ours, dissent is a reason to keep. It is a safety rule, not a better classifier. Likely question: why three families? Families make different mistakes; agreement across them is strong evidence the test is wrong.

## kuu_d2
kicker: Tested on unseen bugs · fixed in advance (D-95)
title: On new seeded bugs, our rule lost {{kuu2:summary:KUU|S1:pf_lost@0}} bug-finding tests where debate lost {{kuu2:summary:DEB|S1:pf_lost@0}}
chart: Bug-finding tests lost (of {{kuu2:pf_prevalence:PF}}) | {{kuu2:summary:DEB|S1:pf_lost@0}}, {{kuu2:summary:KUU|S1:pf_lost@0}}
cats: Debate (small judge), Our rule
stat: {{kuu2:summary:KUU|S1:pf_lost@0}} of {{kuu2:pf_prevalence:PF}}
statlabel: bug-finding tests lost by our rule, while its F1 still beat keeping everything ({{kuu2:summary:KUU|S1:f1}} vs {{kuu2:summary:KA:f1}})
why: A rule found on one data set must be tested on data it has never seen, with the test written down first.
notes:
The seeded bugs are {{kuu2:n_instances}} failures from {{kuu2:n_bugs}} bugs, judged with fresh calls. Our rule lost {{kuu2:summary:KUU|S1:pf_lost@0}} of {{kuu2:pf_prevalence:PF}} bug-finding tests; debate lost {{kuu2:summary:DEB|S1:pf_lost@0}}. And it still beat keeping everything on F1. Both tests fixed in advance held; the statistics backup gives them. Be honest about the price: its agreement score, {{kuu2:summary:KUU|S1:mcc}}, is below debate's {{kuu2:summary:DEB|S1:mcc}}. It is a safety rule, not a better classifier. Likely question: are seeded bugs easier? Probably, which is why the real bugs remain the main evidence.

## tradeoff
kicker: The key method slide · seeded bugs (D-113, descriptive)
title: Every rule trades wrong tests removed against bugs lost; ours loses few bugs with nothing tuned
image: paper/figures/deck_rates.png
stat: {{pareto:D2:points:KUU|S1:pf_lost@0}} vs {{pareto:D2:points:TAU|S1:pf_lost@0}}
statlabel: bug-finding tests lost by our rule (nothing tuned) and by debate with a tuned "only if 100% sure" cut-off, which remove about the same share of wrong tests
why: A cautious rule always loses little, so a fair comparison puts every rule on the same two rates, which do not depend on how many wrong tests there are, and marks which ones were tuned.
notes:
This is the slide to remember. Across, the share of bug-finding tests a rule loses: further right is worse. Up, the share of wrong tests it removes: higher is better, so the best corner is top left. Neither rate depends on the mix of right and wrong failures, which is why the paper uses this view. The thinking-off single-model judges sit top right: they remove about three quarters of the wrong tests but lose over a third of the bug-finding ones (debate loses {{rv11:D2:rules:DEB|S1:pf_loss_rate@pct0}}). Our rule sits bottom left: it loses {{rv11:D2:rules:KUU|S1:pf_loss_rate@pct0}} and removes {{rv11:D2:rules:KUU|S1:tnr@pct0}} of wrong tests, at the same place as debate with an "only if 100 percent sure" cut-off, but that cut-off was tuned on development data and our rule has nothing tuned. Escalation moves our rule up towards the frontier AI ({{rv11:D2:rules:CAS|S1:tnr@pct0}} removed, {{rv11:D2:rules:CAS|S1:pf_loss_rate@pct0}} lost). The share-discarded view is in the paper's appendix. Likely question: couldn't any cautious rule sit there? Yes, which is why the tuned one is marked.

## kuung
kicker: The obvious objection, tested · fixed in advance (D-109)
title: Without the generator's own AI family on the panel, the rule still lost only {{kuung:D2:summary:KUUNG|S1:pf_lost@0}} bug-finding test
chart: Bug-finding tests lost (of {{kuu2:pf_prevalence:PF}}) | {{kuung:D2:summary:DEB|S1:pf_lost@0}}, {{kuung:D2:summary:KUU|S1:pf_lost@0}}, {{kuung:D2:summary:KUUNG|S1:pf_lost@0}}
cats: Debate (small judge), Our rule, Our rule without Gemma
stat: {{kuung:D2:summary:KUUNG|S1:pf_lost@0}} of {{kuu2:pf_prevalence:PF}}
statlabel: bug-finding tests lost once Gemma, the test writer's own family, was replaced by Llama 3.1. The price: it throws away fewer failures ({{kuung:D2:summary:KUUNG|S1:share_discarded@pct0}} vs {{kuung:D2:summary:KUU|S1:share_discarded@pct0}})
why: A bigger Gemma model wrote the tests, so the Gemma judge might be reluctant to blame them. We replaced it and ran the rule again before claiming anything.
notes:
A fair objection: one of our three judges, Gemma, comes from the same family as the AI that wrote the tests, and it rarely calls those tests wrong. Without it, the remaining pair lost {{loo:D2:summary:M1_E6B|S1:pf_lost@0}} tests instead of {{loo:D2:summary:KUU|S1:pf_lost@0}}. So we replaced Gemma with a fourth family, Llama 3.1, chosen on development data by the same rules as before, wrote the tests down, and ran it. It lost {{kuung:D2:summary:KUUNG|S1:pf_lost@0}} bug-finding test and no whole bug, and both tests fixed in advance held. Llama is not a lenient judge: it misses {{kuungm:D2:kuung:NG:miss_rate_on_pf}} of bug-finding tests, against Gemma's {{kuungm:D2:kuu:M2:miss_rate_on_pf}} (post hoc). The price is that it throws away fewer failures. Likely question: so is the same-family judge irrelevant? It is not needed for the protection: the panel without it kept the protection too.

## cascade
kicker: Our rule, extended · fixed in advance (D-105)
title: Hard cases can go to a bigger AI; the easy ones never leave our machine
judge: Qwen 3.5 · 9B
judge: Gemma 4 · 12B
judge: Ministral 3 · 14B
rule: Do all three agree?
discard: All say "wrong test": throw away
keep: All say "found a bug": keep
escalate: Any disagreement or unusable answer
frontier: The frontier AI's debate decides (no answer: keep)
stat: {{cas2:escalation:share_escalated@pct0}}
statlabel: of failing tests sent to the bigger AI; the rest never leave the machine
origin: The cascade and its tests were committed (D-105) before any call to the frontier AI on the seeded bugs.
why: A local-first design keeps most of the code private and pays for the big AI only where the small ones disagree.
notes:
This extends the rule. If the three local AIs agree, that decides. Any disagreement, including an unusable answer, goes to the frontier AI's debate; if that answer is missing, we keep the test. On the seeded bugs half of the failing tests were escalated, so the other half never left the machine. We do not claim it is the cheapest option: the frontier AI asked once about every test costs less in dollars, but sends every test off the machine. Local computing is not free either: about {{pareto:D2:points:CAS|S1:local_gpu_s_per_instance@1}} seconds of graphics-card time per test. Likely question: was this designed on the test data? No; it was fixed in advance in the version-controlled decision log before the frontier AI saw a single seeded bug.

## cascade_d2
kicker: The cascade on unseen bugs · fixed in advance (D-105)
title: Sending half the cases to the bigger AI nearly doubles the agreement score, but does not match using it everywhere
chart: Agreement score (MCC) | {{cas2:summary:KUU|S1:mcc}}, {{cas2:summary:CAS|S1:mcc}}, {{cas2:summary:DEB|S1|SON:mcc}}
chart: F1 | {{cas2:summary:KUU|S1:f1}}, {{cas2:summary:CAS|S1:f1}}, {{cas2:summary:DEB|S1|SON:f1}}
cats: Our rule alone, Rule + escalation, Frontier AI on every test
stat: {{cas2:summary:KUU|S1:mcc}} → {{cas2:summary:CAS|S1:mcc}}
statlabel: agreement score of our rule alone and with escalation. It lost {{cas2:summary:CAS|S1:pf_lost@0}} bug-finding tests; the frontier AI everywhere lost {{cas2:summary:DEB|S1|SON:pf_lost@0}}. Fully local, with the thinking judge as the second tier (post hoc): {{lc:D2:runs:62:local_cascade:mcc}}, {{lc:D2:runs:62:local_cascade:pf_lost@0}} lost
why: We wanted to know how much accuracy the cheap local tier can recover by escalating only its disagreements.
notes:
The result fixed in advance on the seeded bugs. The agreement score rose from {{cas2:summary:KUU|S1:mcc}} to {{cas2:summary:CAS|S1:mcc}}: the first hypothesis held. The second did not: against the frontier AI used on every test, the cascade's F1 is lower and we could not show it is "no worse". Say it plainly: escalation recovers most of the big AI's accuracy, not all of it, and gives back some of the rule's protection ({{cas2:summary:CAS|S1:pf_lost@0}} lost against {{cas2:summary:KUU|S1:pf_lost@0}}). Post hoc, with the thinking-enabled small judge as the second tier instead of the frontier AI, nothing leaves the machine: agreement score {{lc:D2:runs:62:local_cascade:mcc}}, {{lc:D2:runs:62:local_cascade:pf_lost@0}} bug-finding tests lost, against the frontier cascade's {{lc:D2:comparators:Sonnetcascade:mcc}} and {{lc:D2:comparators:Sonnetcascade:pf_lost@0}}; safer, less accurate, and it needs fresh bugs to confirm. Likely question: which should a practitioner use? The rule alone when missed bugs dominate the cost; the cascade when wrong tests kept matter too; the fully local version when code may not leave the machine.

## base
kicker: Against earlier papers
title: Our numbers differ from earlier papers for five stated reasons, and agree where the designs meet
row: Language | JSTestCraft: JavaScript | Java, Defects4J
row: Where labels come from | hand audits or an AI's opinion | running the code on both versions
row: Judge size | large paid models | small local model (frontier reference: debate {{e9:summary:DEB|S1|SON:f1}})
row: Task and score | test-generation quality | failure filtering, F1 and agreement score
row: How common bugs are | rarely reported | {{sum:prevalence:pf_prevalence@pct}} of our failures are bug-finding
agree: Zhao et al.: tests that find the bug {{cit:zhao lo}}–{{cit:zhao hi}}%, ours {{zhao:subsets:all_D1:share_effective_pct@2}}%
agree: JSTestCraft: a vote keeps most bug-finding tests (ours keeps {{e8:summary:VOTE3|S1:recall@pct0}})
agree: JavaOracle: debate gives up real findings ({{cit:javaoracle tp before}} → {{cit:javaoracle tp after}})
why: The panel will ask why our scores look lower than published ones; each difference has a stated cause.
notes:
Five reasons our numbers differ, one per row: language, where labels come from, judge size, the task and score, and how common bugs are. Where the designs meet, we agree: our share of bug-finding tests overlaps Zhao's range, a cross-family vote keeps most bug-finding tests as JSTestCraft's does, and debate gives up real findings as JavaOracle reports. Likely question: why not reproduce Zhao exactly? Their package ships the pipeline but not the generated tests (D-98).

## threats
kicker: Limits
title: What our results cannot show
threat: Small sample | {{sum:prevalence:PF}} bug-finding tests on real bugs; only large effects are detectable
threat: Memory of the benchmark | removing the failure message and the seeded bugs argue against it; a newer benchmark was not run
threat: Small judges | findings are for thinking off; with it on one did better but failed its gate; frontier AI: reference only
threat: One test writer | a second generator failed its selection checks, so only one was used
threat: Label check | two raters agreed at κ {{aud2:raters:kappa}}, but they are the authors, saw the fix, and used development data only
threat: Cost | local computing is not priced: about {{pareto:D2:points:KUU|S1:local_gpu_s_per_instance@1}} graphics-card seconds per test for our rule
why: Every choice was written down before we looked, and every change is a dated, numbered decision.
notes:
Six limits, each with what we did about it. The sample is small, so small effects stay unproven. The label check was done by the two of us, who had seen the developer's fix, on development data only; it still tests the labelling rule, which is mechanical and identical on both data splits. Local computing is not free, and we report graphics-card seconds beside dollars. Likely question: did you tune anything on the test data? No; models, prompts and thresholds were frozen on development data.

## contributions
kicker: What we contribute
title: A way to measure, a safer rule, and three findings
contrib: A way to measure | Labels from running each failing test on the buggy and fixed versions, with no person or AI in the loop; a frozen plan, fixed in advance in the version-controlled decision log; every number recomputable from the call log
contrib: A safer rule | Keep unless unanimous: lost {{kuu2:summary:KUU|S1:pf_lost@0}} of {{kuu2:pf_prevalence:PF}} bug-finding tests on unseen bugs (debate {{kuu2:summary:DEB|S1:pf_lost@0}}), {{kuung:D2:summary:KUUNG|S1:pf_lost@0}} without the same-family AI; escalation keeps half the tests local
contrib: Three findings | With thinking off, the failure message carries the signal and debate does not beat voting; one judge's reasoning helped more than debate or voting (confirmed against debate; failed its gate); a much larger AI is far more accurate and steady
why: Each contribution can be reused on its own: the measuring method, the rule, or the findings.
notes:
Three contributions, in this order. The way to measure, which anyone can reuse. The safer rule, which we proposed and then tested under a plan written down first, including the panel without the same-family AI. And the findings, which tell a practitioner where the signal is. Likely question: what is new beyond measurement? Research question four: the rule and the cascade.

## takeaways
kicker: Takeaways
title: Keep failing tests by default, and throw one away only when different AIs all agree
take: Keep failing tests by default: throwing them away costs real bugs
take: Throw a test away only when three AI families agree; send disagreements to a bigger AI if you can
take: Give the judge the failure message, not more documentation
take: Turn on the judge's reasoning before adding debate or voting rounds (one model so far, and it still failed its gate), and never trust a single debate run
notes:
Four takeaways for anyone building a test generator. Keep by default. Throw away only when independent AIs agree. Put the failure in the prompt. And with small judges, turn on reasoning before adding calls: it helped more than debate or voting, though it still failed its quality gate. Thank you; we are happy to take questions.

## stats_a
kicker: Backup · statistics behind slides 8–11
title: The planned tests on real bugs, with confidence intervals and corrections
line: Debate F1 {{d1:DEB|S1:f1}} vs keep-all {{d1:KA:f1}}; debate agreement score {{d1:DEB|S1:mcc}}, 95% CI {{d1:DEB|S1:mcc_ci95}}
line: Five confirmatory F1 tests, Holm-corrected: none supported (debate − majority p Holm {{conf:f1:H3a:p_holm}})
line: Debate − majority ΔF1 {{conf:f1:H3a:delta}}, 95% CI {{conf:f1:H3a:ci95}}; smallest detectable difference ≈ {{mde:tests:H3a:mde_alpha_005@2}}
line: Javadoc (S1 − S0) ΔF1 {{conf:f1:H2a:delta}}, p Holm {{conf:f1:H2a:p_holm}}
line: Without the failure message: agreement score {{d1:J1|S1|noF:mcc}} (one judge) and {{d1:SC|S1|noF:mcc}} (majority)
line: Frontier AI: debate − one judge ΔF1 {{e9:hypotheses:H9-1:delta}} {{e9:hypotheses:H9-1:ci95}}, p Holm {{e9:hypotheses:H9-1:p_holm}}
notes:
Use this slide only if the panel asks for the tests behind the main slides. Every interval is a bug-level bootstrap; Holm corrects the five confirmatory tests together.

## stats_b
kicker: Backup · statistics behind slides 14–18
title: The tests on seeded bugs, fixed in advance, with confidence intervals and corrections
line: Our rule vs keep-all: ΔF1 {{kuu2:hypotheses:H10-1:delta}} {{kuu2:hypotheses:H10-1:ci95}}, p Holm {{kuu2:hypotheses:H10-1:p_holm}}; fewer losses than debate, p Holm {{kuu2:hypotheses:H10-2:p_holm}}
line: Without the same-family AI: ΔF1 vs keep-all {{kuung:D2:hypotheses:H13-1:delta}} {{kuung:D2:hypotheses:H13-1:ci95}}, p Holm {{kuung:D2:hypotheses:H13-1:p_holm}}; whole bugs lost vs debate {{kuung:D2:hypotheses:H13-2:delta@0}} {{kuung:D2:hypotheses:H13-2:ci95@ci0}}, p Holm {{kuung:D2:hypotheses:H13-2:p_holm}}
line: Agreement score without vs with the same-family AI: {{kuung:D2:kuung_minus_kuu_mcc:delta}} {{kuung:D2:kuung_minus_kuu_mcc:ci95}} (not significant)
line: Escalation vs rule alone: Δ agreement score {{cas2:hypotheses:H12-1:delta}} {{cas2:hypotheses:H12-1:ci95}}, p Holm {{cas2:hypotheses:H12-1:p_holm}} (supported)
line: Escalation vs frontier AI everywhere: ΔF1 {{cas2:hypotheses:H12-2:delta}}, 95% CI {{cas2:hypotheses:H12-2:ci95}}: "no worse by 0.05" not shown
line: Error diversity: two families share a miss {{ed:D2:comparison:mean_cross_family_lift@1}}× as often as chance predicts; three samples of one model {{ed:D2:comparison:mean_within_family_lift@1}}×
notes:
Use this slide only if the panel asks for the tests behind the rule and the cascade. All six were fixed in advance in the version-controlled decision log before the calls they use, which is internal provenance, not an external registration; on real bugs the rule is post hoc and labelled so.

## stats_c
kicker: Backup · analyses added after review (post hoc or exploratory)
title: On rates that ignore the mix, our rule trades accuracy for safety
line: Seeded bugs: the rule keeps {{rv11:D2:rules:KUU|S1:tpr@2}} of bug-revealing tests but removes only {{rv11:D2:rules:KUU|S1:tnr@2}} of wrong ones; balanced accuracy {{rv11:D2:rules:KUU|S1:ba}} vs debate {{rv11:D2:rules:DEB|S1:ba}} and escalation {{rv11:D2:rules:CAS|S1:ba}}
line: All judgeable wrong tests on real bugs ({{rv2:tf296:n_tf_judged}}): the rule removes {{rv2:tf296:rules:KUU:all:tnr@2}}; {{rv2:tf296:rules:KUU:all:false_alarms_per_kept_pf@1}} wrong tests per real one kept at the real mix (no triage {{rv2:tf296:rules:Keepall:all:false_alarms_per_kept_pf@1}})
line: As a ranking, the rule's vote count matches debate (AUROC {{rv13:D2:rules:KUU|S1:auroc}} vs {{rv13:D2:rules:DEB|S1:auroc}}); cheap failure features alone {{rv14:lopo:features:auroc}}
line: Debate varies from run to run: F1 range {{rv2:deb8:spread:f1:range}} over {{rv2:deb8:n_replicates}} runs; with thinking on, the same small judge beat debate on seeded bugs (MCC {{tk:d2:descriptive:ThinkingM1J1:mcc}} vs {{tk:d2:descriptive:M1DEB:mcc}}; {{tk:d2:confirmatory:HT-2:pf_lost_thinking@int}} vs {{tk:d2:confirmatory:HT-2:pf_lost_deb@int}} bug-revealing tests lost; confirmed) but failed its quality gate (question 30)
line: Every local judge failed its own quality gate ({{der:local judges failing G-d@int}} of {{der:local judges gated}}); a 0.08 debate gain would need about {{rv18:tests:H3a:by_mde:0.08:bugs_alpha_005}} bugs
notes:
Use this slide if the panel asks whether the rule is really better. Answer: it is safer, not more accurate. Every number here was added after review and is post hoc or exploratory, except the thinking judge's seeded-bug result, which was tested with two hypotheses fixed in advance (question 30); none changes a confirmatory verdict of the original design. Details: paper Appendix G.
