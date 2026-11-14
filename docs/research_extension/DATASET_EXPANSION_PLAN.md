# Dataset expansion plan

Nothing here has been run. Estimates are marked as such; measured figures cite their source.

## 1. Why more data is the binding constraint

D1-test holds 60 bug-revealing tests in 22 bugs. Zero losses on 22 bugs leave a 95% upper bound of 12.7% on the
bug-loss rate; a confirmatory test of any rule needs several times as many bugs (`EXPERIMENT_BLUEPRINT.md` §4).

## 2. Tranches, in order

| Tranche | Content | New bugs (estimate) | Cost | Blocker |
|---|---|---|---|---|
| T1 | The 78 focal methods the per-project cap of 25 excluded (53 defects), 3 generations each | ≈9 bugs with a PF test, ≈24 PF tests (extrapolated from 22 bugs / 195 methods) | Generation ≈3–4 h of GPU for 234 generations (rate measured on dev for E7a: ≈1.5 h per 117); execution several hours in WSL | author approval for compute; no test runs while the generator is loaded (D-64) |
| T2 | 3 → 9 generations for all 312 frame methods | unknown; PF yield per extra generation is the thing to measure (J-A3) | ≈6× T1's generation time | as T1 |
| T3 | Control failures: non-buggy public methods of the same classes | none by construction; measures how often a flip exists where no bug does | as T1 | needs a frame rule for control methods, fixed before generation |
| T4 | A second test generator | — | days | no candidate has passed generator selection (D-100, D-102) |
| T5 | Bugs fixed after every model's release | — | days; ≥350 GB for a GitBug-Java-style setup | no benchmark newer than the 2026 models identified (D-103) |

Target for a confirmatory claim: at least 60 bugs with a bug-revealing test in the sealed set.

## 3. Split and leakage rules

- Every tranche is **sealed**: generation, execution and labelling finish, labels go to a new label file, and the
  commit is recorded, before any probe or judge reads an instance.
- T1 methods belong to projects already in dev or held-out. The split unit stays the bug; a method inherits its
  project's split. Dev-project methods (Cli, Gson, Jsoup) in T1 may be used for engineering; held-out-project methods
  are confirmation data only.
- The probe engine and the rules are pinned to a commit before T1's labels exist.
- The existing leakage guard is rebuilt for the new instances with the same code (`data/leakage_guard`), and a
  probe report (Stage B) must pass it before it can enter a package.
- The original label files, samples and runs are not edited; new files carry a tranche suffix.

## 4. Label taxonomy (a separate target, never a replacement)

The execution label stays the primary label. An audit taxonomy is added beside it, fixed before rating:

| Code | Meaning | Execution label it refines |
|---|---|---|
| A-PF | the test is right; the failure is the benchmark's fault | PF |
| A-OTHER | the test is right; the failure is a real fault the patch does not touch | TF or AMB |
| A-ORACLE | the expected value or expected exception is wrong | TF |
| A-SETUP | the arrangement or API use is wrong; the method under test never sees valid input | TF |
| A-ENV | harness, environment or resource problem | TF |
| A-UNRES | raters cannot decide from the material | any |

Protocol (extends J-D1): at least two raters who are not authors; packets without the fix, the fixed-version outcome
or any model output; held-out items with TF assertion failures oversampled 2:1; Cohen's κ with a bug-level interval.
The probe's `decoupled` flag makes a checkable prediction against this taxonomy: decoupled failures should be A-SETUP
or A-ENV. Needs author approval (external raters).

## 5. Lifecycle outcome

Per policy, after a repair stage rewrites or deletes every discarded test: bugs with at least one bug-revealing test
left, and tests a developer must read. This is J-F5; it needs a repair model and re-execution (about a week).

## 6. Licences, privacy, reproducibility

- Defects4J subjects are open source under their own licences; the study's `DATA_LICENSE.md` already covers
  redistribution of generated tests and execution records. New tranches follow it.
- No personal data. The probe sends nothing off the machine.
- Each tranche records generator digest, prompt hash, seeds, Ollama version, JDK and Defects4J versions, as the
  frozen configuration does.

## 7. What can start without approval and what cannot

| Action | Status |
|---|---|
| Re-running probes or analyses on existing data | allowed (zero calls) |
| T1 generation and execution on the frozen server | **needs the authors**: hours of GPU and a study-server session |
| Stage B local judge calls | **needs the authors**: study-server session |
| External raters, OSF registration, paid frontier calls | **needs the authors** (not approved in pass 2, D-130) |
