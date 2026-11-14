# Label-audit rubric (both raters, independently)

**Question.** For each failing generated test, decide what caused the failure on the **buggy** version, using only the
packet: the test, the failure on the buggy version, the focal method's Javadoc and the developer's fix (shown buggy →
fixed). The execution label and any model output are hidden. Do not confer until both sheets are complete.

| Decision | Use it when |
|---|---|
| **PF** (program fault) | The test's expectation matches the intended behaviour (as the fix and the Javadoc show it), and the failure on the buggy version comes from the code the fix changes. The same test would pass once the fix is applied. |
| **TF** (test fault) | The test fails for a reason the fix does not address: a wrong expected value, invalid set-up, API misuse, or a dependence on the environment (time zone, locale, ordering). It would fail on the fixed version as well. |
| **AMB** (ambiguous) | The evidence cannot decide, or both are true: the faulty code causes the failure and the test's own expectation contradicts the fixed behaviour. Explain in the notes. Use it sparingly. |

Also record a **confidence** (1 = guess, 2 = fairly sure, 3 = certain) and, for anything not obvious, a short note.

## Worked examples (from the held-out split, not part of the audit; execution label shown)

### PF: Chart_24, `GrayPaintScale.getPaint`

- Failure on the buggy version: `java.lang.IllegalArgumentException` — `Color parameter outside of expected range: Red Green Blue` at `Paint paint = scale.getPaint(5.0);`
- PF. The test asks for the paint of a value below the lower bound. The buggy method computes the grey level from the raw value, which goes negative, so `new Color` throws. The fix computes it from the clamped value `v`; the same test passes on the fixed version.

### PF: Chart_17, `TimeSeries.clone`

- Failure on the buggy version: `java.lang.IllegalArgumentException` — `Requires start <= end.` at `TimeSeries cloned = (TimeSeries) series.clone();`
- PF. Cloning a series throws `Requires start <= end` because the buggy `clone()` calls `createCopy(0, getItemCount() - 1)`, which fails on an empty series. The fix restores `super.clone()` with a deep copy, and the test passes.

### TF: Chart_3, `TimeSeries.createCopy`

- Failure on the buggy version: `java.lang.AssertionError` — `expected:<1> but was:<0>` at `assertEquals(1, copy.getItemCount());`
- TF. The test expects one item in `createCopy(1, 1)` and gets none. The fix only resets `minY`/`maxY` in the copy; it does not touch how items are copied, and the test fails the same way on the fixed version. The expectation, not the fault, is wrong.

### TF: Time_3, `MutableDateTime.addHours`

- Failure on the buggy version: `java.lang.AssertionError` — `null` at `assertTrue(dt.getYear() >= 2024);`
- TF. The test adds 8,760 hours to 2023-01-01T00:00Z and expects the year to be 2024. That instant is still 31 December 2023 in a time zone west of UTC, and Defects4J runs its tests in America/Los_Angeles; the fix (dropping the `amount != 0` guards) is unrelated. The expectation depends on the time zone.

### AMB: Compress_8, `TarUtils.parseOctal`

- Failure on the buggy version: `java.lang.AssertionError` — `expected:<9> but was:<83>` at `assertEquals(9L, TarUtils.parseOctal(buffer, 0, buffer.length));`
- Execution label AMB, but a careful rater decides TF. 0000123 in octal is 83, so the expected value 9 is wrong whatever the fault; the fixed version fails as well, with a different signature, which is why the rule says AMB. Use AMB only when the evidence genuinely cannot decide.

### AMB: Csv_4, `CSVParser.getHeaderMap`

- Failure on the buggy version: `java.lang.NullPointerException` — `null` at `Map<String, Integer> headerMap = parser.getHeaderMap();`
- AMB (a genuine mixed case). On the buggy version `getHeaderMap()` throws a NullPointerException when no header is defined; the fix makes it return `null` instead. The failure is caused by the faulty code, but the test's own expectation (an empty map) contradicts the fixed behaviour too, so it fails on both versions in different places.


## Procedure

1. Read this rubric. 2. Do the 10 **calibration** items alone (`calibration_rater_X.csv`). Then compare your sheet
with the other rater's and discuss your disagreements using this rubric only. Open `CALIBRATION_KEY.md` only after
that discussion, and do not change the rubric or any judgement to match it. 3. Do the 71 **audit** items
(`label_audit_rater_X.csv`) alone, in the packet order, without conferring. 4. Return the CSV. Scoring:
`python scripts/analysis/label_audit.py`.
