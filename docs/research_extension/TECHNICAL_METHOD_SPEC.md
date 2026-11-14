# Technical method specification: whole-method dependence probes (WDP)

Version 4, 2026-11-14 (version 2 amended on the authors' conditional approval; version 3 on their review of
freeze commit `3c59196`; version 4 on their review of re-freeze commit `1b8e667`, which they did not approve;
changes are listed in sections 10, 11 and 12). Status: **implemented and run on the development
split only (`WDP_D1_DEV`, engineering); no retrospective evaluation run exists.** Any result from it on existing data is **exploratory**:
it was designed after the pilot's and the confirmation's labels and probe outcomes were known. Its runs on existing
data are **retrospective evaluation runs**. It is internally version-controlled only; it is **not externally
preregistered** and must never be described as OSF-registered. It changes nothing in the registered confirmation
(OSF kp79c).

## 1. Motivation, from the audit

The confirmation left one of CFP's two observables standing: a failure that no first-order edit of the method under
test changes (`decoupled`) was a wrong test in 135 of 136 cases. Three facts about it
(`CONFIRMATION_INDEPENDENT_AUDIT.md` §4):

1. Both bug-revealing tests it has ever flagged (`Codec_13` in the pilot, `Math_59` in the confirmation) fail in a
   way that obviously depends on the method under test. The six operators simply have no edit that touches the
   relevant code, so every mutant is silent. The flag conflates "the failure does not depend on this method" with
   "our edits could not reach what it depends on".
2. The flag needs ten compiled mutants. 125 of 572 confirmation tests have fewer, and 102 of those (19 PF, 83 TF)
   have no mutant that changes the failure: they are undecided only because of the minimum.
3. The flag fires mostly where an exception is raised outside the method under test, which suggests that much of
   the signal is simply that the test never gets to the method.

WDP asks the underlying question with interventions that replace the whole method: **does this failure change when
the method under test is replaced wholesale, and is the method entered at all?**

## 2. Definitions

Let `t` be a failing generated test of focal method `m` on the buggy program `P`. Let `σ(P, t)` be the failure
record used by the registered engine: (outcome type, exception class, failing test line) plus the normalised
message digest (`triage_ext.ledger.signature`, `message_digest`).

### 2.1 Interventions (on `m` only; callees are never touched)

The whole body of `m`, from its opening brace to its closing brace, is replaced. The signature is untouched.

| Variant | Applies when the declared return type is | New body |
|---|---|---|
| `X-THROW` | any | entry marker, then `throw new java.lang.Error("__WDP__");` (exact text below) |
| `X-RET` | `void` | `{ }` |
| `X-RET` | `boolean` | `{ return false; }` and `{ return true; }` |
| `X-RET` | `byte`, `short`, `int`, `long`, `float`, `double` | `{ return 0; }` and `{ return 1; }` |
| `X-RET` | `char` | `{ return ' '; }` and `{ return 'A'; }` |
| `X-RET` | `String` or `java.lang.String` | `{ return ""; }` and `{ return "A"; }` |
| `X-RET` | anything else (reference, array, generic, boxed) | `{ return null; }` |

`X-THROW` body, exactly (one line in the source; fully qualified names so that no class of the program can shadow
them; identifiers chosen not to collide with parameters):

```java
{ try { java.lang.String __wdp_m = java.lang.System.getenv("WDP_MARKER"); if (__wdp_m != null) { new java.io.File(__wdp_m).createNewFile(); } } catch (java.lang.Throwable __wdp_t) { } throw new java.lang.Error("__WDP__"); }
```

- **Entry marker.** Each `X-THROW` run of each test gets its own fresh path in the environment variable
  `WDP_MARKER`. If the method is entered, the file is created before the throw. The marker is a direct observation
  of entry that does not depend on the thrown error reaching the test runner. An environment variable is used
  because a test cannot clear it.
- `java.lang.Error` is thrown because `catch (Exception e)` does not intercept it. A test or program code that
  catches `Throwable` or `Error`, or that calls the method on another thread, can still intercept it; that is what
  the marker and the screen of section 2.3 are for.
- The return-value replacements follow Niedermayr et al. (2016, Table 1) and Vera-Pérez et al. (Table 1), with
  `null` for every non-String reference and array type. `X-THROW` and its marker are defined here.
- A variant that does not compile is dropped and counted. At most three variants per method.

### 2.2 Outcome of one variant for one test

Classified by the registered engine's unchanged function `triage_ext.ledger.classify(baseline, run, rerun)`:
`SAME`, `SHIFT`, `FLIP` (a pass that repeats), `ERR` (timeout, harness error, a pass that does not repeat).
`CHANGED` means `SHIFT` or `FLIP`.

### 2.3 Per-test observables

- `x_throw` ∈ {SAME, CHANGED, ERR, NA} (NA: variant not compiled or instance excluded).
- `entered` ∈ {true, false, null}: the marker file exists after the `X-THROW` run (null when `x_throw` is NA).
- `surfaced`: the `X-THROW` run's recorded exception class is `java.lang.Error` and its message contains
  `__WDP__` (used only for the consistency check of section 5, item 8).
- `x_ret` = the list of classes of the compiled `X-RET` variants.
- `fo` ∈ {CHANGED, SILENT, UNUSABLE}, from the existing first-order ledger record for `t`
  (`summary`), whatever its number of compiled mutants. CHANGED: `summary.coupled` is exactly true (at least
  one FLIP or SHIFT). SILENT: the summary is present, not excluded, and `summary.coupled` is exactly false.
  UNUSABLE: anything else (no record, an excluded record, a `coupled` field that is not a boolean). An absent
  first-order observation is never read as "no first-order edit changed the failure".
- `swallow_risk` (static, from the test class source with comments and string literals removed): true if any of
  1. a `catch` clause whose parameter types include `Throwable` or `Error` (simple or `java.lang.`-qualified,
     with or without `final`, including inside a multi-catch);
  2. `expected = Throwable.class` or `expected = Error.class` in an annotation;
  3. `assertThrows(`, `expectThrows(` or `.expect(` whose first argument is `Throwable.class` or `Error.class`.

  `AssertionError`, `Exception` and a `throws Throwable` clause do not set it.

**Record validity.** Every present WDP record is checked before anything else is read from it. The first
condition that holds gives the code.

| # | Code | Condition | Applies to |
|---|---|---|---|
| 1 | `malformed:bad_shape` | the record is not an object; or `excluded` is neither null nor a non-empty string; or `variants` is not a list of objects; or some variant's `id` is not a string or its `compiled` is not a boolean | every record |
| 2 | `malformed:unknown_class` | **any** variant, compiled or not, carries a `class` that is neither null nor one of SAME, SHIFT, FLIP, ERR | every record |
| 3 | `malformed:uncompiled_with_class` | a variant with `compiled` false carries a non-null `class` | every record |
| 4 | `malformed:variant_ids` | the variant ids are not: exactly one `X-THROW`, plus at most two others drawn without repetition from `X-RET-1`, `X-RET-2` | non-excluded records |
| 5 | `malformed:compiled_not_run` | a variant with `compiled` true has a null `class` | non-excluded records |
| 6 | `malformed:entered_missing` | the `X-THROW` variant has a class and `entered` is not a boolean | non-excluded records |
| 7 | `malformed:surfaced_missing` | the `X-THROW` variant has a class and `surfaced` is not a boolean | non-excluded records |
| 8 | `malformed:marker_inconsistent` | `surfaced` is true and `entered` is not true | non-excluded records |
| 9 | `malformed:swallow_risk_missing` | `swallow_risk` is not a boolean | non-excluded records |

A missing, malformed or inconsistent record **fails closed**: it is level ND with its code, whatever the
first-order ledger says; it can never be level U, RI, WS or FS; and no certificate acts on it. A missing entry
observation is never read as "no entry".

### 2.4 Dependence level (a total, deterministic function that never raises; first matching line wins)

Validity comes first: no level other than ND is assigned from a record that is missing or malformed.

| Order | Condition | Level | ND reason code | Meaning |
|---|---|---|---|---|
| 1 | there is no WDP record | **ND** | `excluded:no_record` | fails closed |
| 2 | the WDP record is malformed (section 2.3, record validity) | **ND** | `malformed:<code>` | fails closed |
| 3 | `fo` = CHANGED | **FS** first-order sensitive | — | some single edit changes the failure (the registered "coupled"). Reached only with a present, valid WDP record |
| 4 | the WDP record is excluded | **ND** | `excluded:<name>` | no verdict; the base rule decides |
| 5 | `fo` = UNUSABLE | **ND** | `first_order_unusable` | whether a single edit changes the failure is not known; fails closed |
| 6 | `x_throw` ∈ {ERR, NA} | **ND** | `x_throw_err`, `x_throw_na` | no verdict |
| 7 | any `X-RET` variant is ERR | **ND** | `x_ret_err` | no verdict |
| 8 | some `X-RET` variant is CHANGED | **WS** whole-method sensitive | — | the failure changes when the method's behaviour is replaced, but no first-order edit shows it |
| 9 | `x_throw` = CHANGED and at least one `X-RET` variant compiled | **RI** entered, insensitive | — | the throw changed the failure, and the failure is identical under every fixed-return replacement tried |
| 10 | `x_throw` = CHANGED and no `X-RET` variant compiled | **ND** | `no_x_ret` | insensitivity not established |
| 11 | `x_throw` = SAME and `entered` = true | **ND** | `throw_swallowed` | the method was entered and its throw did not alter the failure record: something intercepted it. No inference is drawn |
| 12 | `x_throw` = SAME and `swallow_risk` = true | **ND** | `swallow_risk` | the test contains a construct that could intercept the throw; kept as a second guard in case the marker was not written |
| 13 | `x_throw` = SAME **and** `entered` is exactly false **and** `swallow_risk` is exactly false **and** every compiled `X-RET` is SAME | **U** no entry observed, throw-invariant | — | see below |
| 14 | anything else (no earlier row matched) | **ND** | `malformed:unclassifiable` | fails closed. Level U is assigned by row 13 only, by positive match, never by default |

**Necessary conditions, stated on the raw inputs** (they follow from the table and are what the tests assert
directly, independently of the table's order):

- Level **U** implies all of: the WDP record is an object and is not excluded; it has exactly one `X-THROW`
  variant, compiled, with class SAME; every other variant is either compiled with class SAME or uncompiled with a
  null class; no variant carries a class outside SAME, SHIFT, FLIP, ERR; `entered` is exactly false; `surfaced`
  is exactly false; `swallow_risk` is exactly false; and the first-order summary is present, not excluded, with
  `coupled` exactly false.
- Level **RI** implies the same conditions on shape, on the other variants, on `swallow_risk` being a boolean and
  on the first-order summary, with the `X-THROW` class SHIFT or FLIP and at least one compiled `X-RET` variant.
- Level **WS** implies a valid, non-excluded record, a first-order summary that is SILENT, and at least one
  compiled `X-RET` variant with class SHIFT or FLIP.
- Level **FS** implies a present, valid WDP record and a first-order summary whose `coupled` is exactly true.

**What level U is.** U is an **operational observation**, not a proof of non-reachability. It records that, in the
probe run in which the method under test writes an entry marker and throws on entry, (a) no marker was written,
(b) the failure record was identical to the baseline, (c) the failure record was identical under every
fixed-return replacement, (d) no first-order edit changed it, and (e) the test source holds no construct that
would intercept a `Throwable` or `Error`. The paper and every table describe U in those words ("no entry observed
and throw-invariant"). It must not be written as "the test cannot reach the method" or "unreachable".

Relation to the registered flag: `decoupled` = (at least ten compiled mutants) ∧ no FLIP or SHIFT, so every
decoupled test falls in U, RI, WS or ND. WDP splits the registered flag into those four and gives a level to tests below the
ten-mutant minimum.

### 2.5 Certificates (pure functions of the base label and the level)

```
CD-U (base, level)  = TEST_FAULT if level == U          else base     # primary
CD-UR(base, level)  = TEST_FAULT if level in {U, RI}    else base     # secondary, riskier
```

There is no keep certificate. CK is not carried forward (the confirmation gives no support for it).
Base rules are unchanged: KUU, 2-of-3, keep-all. Level ND never triggers a certificate, whatever its reason.

Why CD-U is the primary and not CD-UR. At level RI a bug-revealing test is possible whenever the faulty behaviour
coincides with the replacement: a `void` method that wrongly does nothing, or a method that wrongly returns `null`.
Faults of omission are common (Pearson et al. 2017 report 30% of fixes as omissions). At level U the remaining
routes to a lost bug are a fault outside the method the test was generated for, and the residual cases of
section 7.

## 3. Algorithm

```
for each focal method m with at least one failing test:            # one overlay set per method
    locate m's text in the buggy class source (exactly one occurrence, as the engine does)
    compile the unmodified class (identity overlay); on failure -> exclusion "focal_recompile_failed"
    R <- declared return type of m (tokens before the method name, annotations/modifiers/type parameters removed)
    variants <- [X-THROW] + X-RET(R)                               # at most 3
    compile each variant into its own overlay; drop non-compiling ones
    for each failing test t of m:
        swallow_risk <- screen(test class source)                  # section 2.3; computed even if t is excluded
        compile t alone; on failure -> exclusion "test_compile_failed"
        base <- run t on the identity overlay (30 s)
        if signature(base) != signature(stored buggy run) or base passes -> exclusion "baseline_not_reproduced"
        for each compiled variant v:
            if v is X-THROW: marker <- fresh path under the per-test scratch directory (must not exist)
            run <- run t on overlay(v) (10 s), with WDP_MARKER=marker in the environment for X-THROW
            if run passes: rerun once (for X-THROW with a second fresh marker path)
            class[v] <- ledger.classify(base, run, rerun)
            if v is X-THROW: entered <- marker (of the first run) exists; surfaced <- exception/message test
        write {instance_id, focal_id, return_type, swallow_risk, entered, surfaced,
               variants: [{id, body_sha, compiled, class, outcome, exception, failing_test_line, message_digest}],
               baseline, excluded, seconds}
level(t), reason(t) <- section 2.4 from this record and the existing first-order ledger record
```

Architecture: a new package `src/triage_dep/` (`interventions.py` pure text; `screen.py` pure text; `wdp.py`
engine; `levels.py` pure level and certificate functions) that **imports** `triage_ext.probe` (`load_meta`,
`read_source`, `locate`, `compile_overlay`, `SOURCE_LEVELS`, `SCRATCH`), `triage_ext.mutate` (`tokenize`,
`_body_start`) and `triage_ext.ledger`. Because the engine's `run_test` cannot pass an environment variable, the
new engine has its own run function, a copy of `triage_ext.probe.run_test` that differs only in accepting an
extra environment mapping; a unit test asserts that the two return identical records for a run without a marker.
No file under `src/triage_ext/` is edited. A new driver `scripts/extension/run_wdp_tranche.py` mirrors
`run_probes_tranche.py`'s arguments and allow-list.

## 4. Inputs and outputs

| | |
|---|---|
| Reads | buggy checkout through the engine's three metadata keys; `instances.jsonl` fields `instance_id, focal_id, bug_name, impl, focal_class, method, candidate_id`; frame `file`; candidate `package, class_name`; execution fields `method, source_class, compile_b, runs_b` |
| Never reads | the fixed version, `label_side/`, any label file, developer tests, judge decisions |
| Writes | `results/extension/wdp/<RUN>/ledger.jsonl`, `run_meta.json` (commit, UTC start, counts, variant table hash) |
| Analysis reads | WDP ledgers, first-order ledgers, labels, votes (labels are read only by the analysis script) |
| Model calls | none |

## 5. Invariants (each backed by a test)

1. Prediction-time boundary: the new package has no path to the fixed version, labels or developer tests (a source
   scan, as `tests/extension/test_boundary.py` does for the engine).
2. `tests/extension/test_freeze.py` still passes; `git diff` on every path in `cfp_frozen.json` is empty.
3. The checkout is never modified; overlays and marker files live under the engine's scratch directory and are
   removed per method.
4. `level()` is total and deterministic and never raises: one unit test per row of section 2.4, plus an
   exhaustive enumeration of its inputs (including a missing `entered`, a missing `swallow_risk`, an unknown
   class, a missing record and an inconsistent marker) asserting exactly one of FS, ND, WS, RI, U and, for ND,
   exactly one reason code; and asserting that every malformed input is ND with a `malformed:` code.
   From version 4 the tests do not rely on an oracle written from the table: they assert the **necessary
   conditions** of section 2.4 directly on the raw inputs (if the level is U, RI, WS or FS, the stated conditions
   hold), over an enumeration that puts wrong types, unknown classes, duplicates and unexpected ids on compiled
   and uncompiled variants alike, over a seeded random fuzz of arbitrary JSON-like records and first-order
   summaries, and with one regression test per row of the table in section 12.
5. A pass counts only if it repeats.
6. Body replacement leaves the signature byte-identical and yields exactly one method body (text-level tests on
   methods with nested braces, string literals containing braces, generics, `throws` clauses, annotations,
   array return types).
7. **Level U is never assigned when `entered` is true or `swallow_risk` is true** (unit tests on `level()`, and an
   end-to-end toy fixture: a test that calls the method inside `try { … } catch (Throwable t) { }` and then fails
   elsewhere must come out ND `throw_swallowed`; the same with the call made on another thread must come out ND
   `throw_swallowed`; a test that fails before calling the method must come out U; a test that calls the method,
   ignores the result and fails elsewhere must come out RI).
8. **Marker consistency, over every raw ledger record.** In every record of every WDP ledger, whatever its label
   (PF, TF, AMB) and whether or not it enters any table, `surfaced` true implies `entered` true. The analysis
   script checks this on the raw ledgers before it reads a label or computes anything; a single violation makes it
   stop without writing a result. The level function applies the same rule per record
   (`malformed:marker_inconsistent`), so a violating record could not be level U even if the check were bypassed.
9. The static screen fires on each construct of section 2.3 and on none of the listed negatives, including the
   same words inside comments and string literals.
10. Re-running a seeded sample of 30 instances yields identical levels and reason codes.

## 6. What a level licenses, and what it does not

| Level | Licensed statement | Not licensed |
|---|---|---|
| U | "With the method under test replaced by one that records entry and throws, no entry was recorded and the failure was identical; it was also identical under every fixed-return replacement and every single edit." | "unreachable"; "the test cannot be about this method"; that the program is correct; that the test is worthless (it may reveal a fault elsewhere) |
| RI | "Making the method throw changed the failure; the failure was identical under each fixed-return replacement tried." | that the method is correct (an omission fault looks the same) |
| WS | "The failure changes when the method's behaviour is replaced; no first-order edit of the six operators shows it." | that the test is right |
| FS | "A single edit changes the failure." | that the test is right (flip did not replicate as evidence) |
| ND | nothing; the reason code is reported | any inference about fault side |

A changed failure is never called a repair, and no level is evidence that a test is right.

## 7. Limitations known before any run

- **Interception of the throw.** A test or program code that catches `Throwable` or `Error`, or runs the method on
  another thread, hides `X-THROW`. Handling: the entry marker (row 11) and the static screen (row 12) both send such
  tests to ND. Residual risk: the marker cannot be written (for example a security manager denies file creation)
  **and** the interception is in program code rather than in the test source. Invariant 8 detects a broken marker
  whenever any throw surfaces in the same run.
- **Entry is recorded for this body only.** The method is located by exact text and replaced in one class. A test
  that executes an override in a subclass, or an overload, does not enter this body; level U is then literally
  true and says the test did not execute the method it was generated for.
- **Determinism.** U assumes the execution up to the first entry is the same in the baseline and probe runs. A
  nondeterministic test can violate this; the engine's baseline-reproduction check and invariant 10 limit it.
- A fault in a constructor, static initialiser or another fix-changed method can make a bug-revealing test level U.
- Reference return types have a single replacement (`null`); a method that wrongly returns `null` is
  indistinguishable from its replacement at level RI.
- The static screen is textual and conservative: it can send a harmless test to ND, which lowers yield and never
  discards a test.
- Message digests ignore differences beyond 2,000 characters and object hash codes (inherited from the engine).
- One benchmark, one language, one generator; tests were generated for fix-changed methods or their classmates.
- The evaluation is retrospective. The design used knowledge of both lost bugs.

## 8. Falsifiers (fixed now)

The method is unsupported by its own evaluation if any of the following holds on the confirmation tests:

1. `Math_59`'s decoupled bug-revealing test is level U (prediction: WS). Same for `Codec_13` on the pilot.
2. KUU + CD-U loses a bug that KUU keeps.
3. The share of level U among bug-revealing tests is not lower than among wrong tests.
4. KUU + CD-U does not discard more wrong tests than KUU (interval for the TNR difference includes zero).

Either of 1 or 2 alone is sufficient to withdraw the certificate. Items 3 and 4 make it useless rather than unsafe.
The ladder itself (how the registered flag splits into U, RI, WS and ND with its reasons) is a descriptive result
and is reported whatever the outcome, provided the run passes its quality checks
(`OPUS_EXECUTION_BRIEF.md` §5 and §6).

## 9. Cost

Per method: one identity compilation and at most three variant compilations. Per failing test: one test
compilation, one baseline run, at most three variant runs and at most three re-runs. The registered engine uses up
to 80 compilations per method and 80 runs per test. No GPU, no model, nothing leaves the machine.

## 10. Amendments in version 2 (2026-11-13, before any implementation or run)

Made on the authors' conditional approval; none was informed by a WDP result, because none exists.

| # | Change | Reason |
|---|---|---|
| 1 | `X-THROW` now writes an entry marker before throwing; new observable `entered` | version 1 inferred non-entry from an unchanged failure record; a caught `Throwable` or `Error` would have produced the same record |
| 2 | New static observable `swallow_risk` | second guard, independent of the marker |
| 3 | Level function: rows 8 and 9 added; U additionally requires `entered` = false and no `swallow_risk`; ND carries a reason code | conservative handling: an intercepted or interceptable throw never yields U |
| 4 | Level U renamed from "unreached" to "no entry observed, throw-invariant" and defined as an operational observation | it is not a proof of non-reachability |
| 5 | Invariants 7 to 9 and the toy end-to-end fixture | tests for changes 1 to 3 |
| 6 | "held-out runs" replaced by "retrospective evaluation runs" | accurate status of the data |

## 11. Amendments in version 3 (2026-11-13, after the authors' review of freeze commit `3c59196`)

Made before any retrospective evaluation run exists; none was informed by an evaluation result. The development
run (118 tests, no label read) produced no malformed record, no ND and no marker violation, so none of these
changes alters any level it recorded. `3c59196` is preserved as the original implementation snapshot.

| # | Change | Reason |
|---|---|---|
| 1 | Record validity defined (section 2.3); new row 2b; malformed records are ND with a `malformed:` code | version 2 left a record with an unchanged failure and a missing entry observation without a row; the implementation raised an error. The authors require that malformed or inconsistent records fail closed and never receive level U |
| 2 | Row 10 states `entered` "exactly false"; new row 11 catches everything else as ND | level U by positive match only |
| 3 | A missing WDP record is ND `excluded:no_record` | same |
| 4 | Invariant 4: the level function never raises | consequence of 1 to 3 |
| 5 | Invariant 8: marker consistency is checked over every raw ledger record, AMB included, and a violation stops the analysis | version 2's check ran only over the scored rows |

Unchanged: the intervention variants, the classification of a variant's outcome, the static screen, the
certificates, the primary outcome, the safety constraint, the criterion and every acceptance threshold.

## 12. Amendments in version 4 (2026-11-14, after the authors' review of re-freeze commit `1b8e667`)

Row numbers quoted in sections 10 and 11 are those of versions 2 and 3; the table of section 2.4 is renumbered
in this version.

The authors did not approve `1b8e667`. They found two defects in its level function; both were reproduced, and
six further malformed inputs of the same kind were found to receive level U or FS. No retrospective evaluation run
exists, so no result informed these changes. `3c59196` and `1b8e667` are preserved as snapshots.

| # | Defect in `1b8e667` | Cause | Change |
|---|---|---|---|
| 1 | An uncompiled variant carrying an unknown class escaped validation, and the record could be level U (authors' finding) | version 3 limited the unknown-class rule to compiled variants, and the level function ignores uncompiled variants | validity rule 2 covers **every** variant; rule 3 makes any class on an uncompiled variant malformed |
| 2 | A missing or malformed record with first-order coupling was level FS (authors' finding) | version 3 put the first-order row before the validity rows, contradicting its own statement that malformed records are ND | validity rows come first (rows 1 and 2); FS is reached only with a present, valid record |
| 3 | An uncompiled variant carrying SHIFT, a duplicate `X-THROW`, a variant with an unexpected id, a `compiled` or `surfaced` field of the wrong type: level U or WS | no schema for the record | validity rules 1, 3, 4, 5, 7 |
| 4 | A missing or excluded first-order summary was read as "no edit changed the failure", so the record could be level U | version 3 defined a missing first-order record as not changed | `fo` has three states; UNUSABLE is ND `first_order_unusable` (row 5); U, RI and WS require SILENT |
| 5 | Tests enumerated the table and compared with an oracle written from the same table, so they shared its gaps | — | tests assert the necessary conditions above directly on raw inputs, over an enumeration and a seeded fuzz of malformed records, plus one regression test per case of this table |

Unchanged: the intervention variants, the classification of a variant's outcome, the static screen, the
certificates, the primary outcome, the safety constraint, the criterion, every acceptance threshold, and the
engine files. On the development ledger (118 valid records) every level must be the same as before; that is
checked before the new freeze.

Considered and left out, to keep the change to one source file: cross-checking each variant's recorded class
against its stored outcome, exception, failing line and message digest. It would be a further integrity check on
level U and can be added later with the authors' approval.
