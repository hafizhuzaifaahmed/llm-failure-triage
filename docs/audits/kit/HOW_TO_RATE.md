# How to rate — a guide for the two raters

You are checking, by hand, whether our automatic labels are right. Each item is a unit test that a model wrote and
that failed. You decide **why it failed**: because the program has a bug (PF), because the test itself is wrong (TF),
or because you cannot tell (AMB). Nobody shows you our label or any model's answer, so your judgement is independent.
It takes about four to five hours in total, split over several sittings.

There are two raters, **A** and **B**. Agree between you who is A and who is B, and use only your own letter's files.

## 1. Your files

All files are in this folder:

```
C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\docs\audits\kit\
```

| What | Rater A | Rater B |
|---|---|---|
| The packet (read it) | `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\docs\audits\kit\packets_rater_A.pdf` | `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\docs\audits\kit\packets_rater_B.pdf` |
| Calibration sheet (10 rows to fill) | `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\docs\audits\kit\calibration_rater_A.csv` | `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\docs\audits\kit\calibration_rater_B.csv` |
| Audit sheet (71 rows to fill) | `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\docs\audits\kit\label_audit_rater_A.csv` | `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\docs\audits\kit\label_audit_rater_B.csv` |

Shared by both of you:

- The rubric (the rules, also printed at the start of each packet):
  `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\docs\audits\kit\LABEL_AUDIT_RUBRIC.md`
- The calibration key (open it **only** at the step that says so):
  `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\docs\audits\kit\CALIBRATION_KEY.md`

**Do not open:**
- anything with `rater_C` in its name;
- the `llm_rater` folder;
- `LLM_RATER_SEAL.json`;
- anything under `data\ground_truth_store`.

Those files belong to a sealed third rater or hold the answers. Opening them would spoil the audit.

## 2. Reading the packet

Open your PDF in any PDF reader (Microsoft Edge is fine: right-click the file → *Open with* → *Microsoft Edge*). The
packet has the rubric, then **Part 1** (calibration items CAL01–CAL10), then **Part 2** (audit items, numbered in
your own order). Each item shows four things:

1. **Generated test** — the test the model wrote.
2. **Failure on the buggy version** — what went wrong when the test ran on the buggy program, and the line where it
   failed.
3. **Javadoc of the focal method** — the method's documentation, if it has any. It tells you what the method is
   supposed to do.
4. **Developer's fix** — the real fix, as a diff. Lines starting with `-` are the buggy code that was removed; lines
   starting with `+` are the corrected code that replaced them.

The question for every item: *if the developer's fix were applied, would this test pass?* If yes, the program was at
fault. If it would still fail, the test was at fault.

## 3. The three decisions

| Write | Meaning | Short example (from the rubric) |
|---|---|---|
| `PF` | **Program fault.** The test expects the right behaviour, and it fails because of the code the fix changes. With the fix, it would pass. | *Chart_24:* the test asks for the colour of a value below the lower bound. The buggy method uses the raw value, goes negative and throws; the fix clamps the value. The test passes on the fixed version → PF. |
| `TF` | **Test fault.** The test fails for a reason the fix does not touch: a wrong expected value, a bad set-up, misuse of the API, or a dependence on time zone, language or ordering. It would fail on the fixed version too. | *Time_3:* the test adds 8,760 hours to 1 Jan 2023 (UTC) and expects 2024. In the Los Angeles time zone the tests run in, that is still 31 Dec 2023. The fix is unrelated → TF. |
| `AMB` | **Ambiguous.** The evidence cannot decide, or both are true at once. Use it rarely, and always write a note. | *Csv_4:* the buggy method crashes (the bug), but the test also expects an empty map while the fixed method returns nothing at all, so the test is wrong as well → AMB. |

Rubric tip: a wrong expected value usually means TF, even when the method is also buggy. Ask whether the fix alone
would make the test pass.

## 4. Confidence and notes

For each item also write a **confidence**:

- `1` = a guess;
- `2` = fairly sure;
- `3` = certain.

Write a short **note** (one line is enough) whenever:
- you chose `AMB`;
- your confidence is `1`;
- the reason is not obvious from the failure message.

For example: "expected value wrong: 0000123 octal is 83, not 9". Leave the note empty for clear-cut items.

## 5. Filling in the sheet (Excel is fine)

1. Double-click your CSV; it opens in Excel. Each row is one item.
2. Fill three columns per row:
   - `decision`: exactly `PF`, `TF` or `AMB`;
   - `confidence`: `1`, `2` or `3`;
   - `notes`: free text, commas allowed.
3. Do not change the first row (the column names). Do not add, delete or sort rows or columns. In the audit sheet,
   the `order` column matches the item numbers in your packet; the `audit_id` column must stay as it is.
4. Save with **File → Save As → "CSV UTF-8 (Comma delimited) (\*.csv)"**, keeping the **same file name in the same
   folder**. If Excel warns that some features may be lost, choose *Keep current format* / *Yes*.
5. Close Excel after saving; an open file is locked and cannot be collected.

You can save part-way and continue in a later sitting.

## 6. The order of work

**Step 1 — Calibration, alone.**
- Read the rubric.
- Do the 10 calibration items (CAL01–CAL10) by yourself, in your calibration sheet.
- Do not talk about them yet.

**Step 2 — Compare with each other.**
- When both calibration sheets are done, sit together and go through the items where you disagree.
- Argue only from the rubric.
- Do not edit your saved sheets; this step is practice.

**Step 3 — Open the key.**
- Only after that discussion, open `CALIBRATION_KEY.md` to see the execution labels for the 10 calibration items.
- Do not change the rubric, and do not change any of your calibration answers to match it.
- Note for yourself what you misread.

**Step 4 — The 71 audit items, alone. No conferring at all.**
- Rate Part 2 of your packet in your audit sheet, in the packet's order.
- Do not discuss any audit item with the other rater, or with anyone else, until **both** audit sheets are complete
  and saved.
- Do not look anything up beyond the packet.

Suggested sittings (take a break between them; about 3–4 minutes per item):

| Sitting | Work | Rows |
|---|---|---|
| 1 | Steps 1–3 (calibration, comparison, key), then audit items 1–24 | calibration 1–10, audit 1–24 |
| 2 | Audit items 25–48 | audit 25–48 |
| 3 | Audit items 49–71, then a last check that every row has a decision and a confidence | audit 49–71 |

## 7. When you are done

- Save both sheets in place (same names, same folder, CSV UTF-8) and tell the authors.
- Optionally, once **both** audit sheets are saved, the two of you may meet to discuss the items you disagreed on and
  record an agreed decision for each in a new file. Do not edit your own sheets afterwards.
  - File: `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\docs\audits\kit\label_audit_consensus.csv`
  - Columns: `audit_id,decision`
  - If you skip this, items where you disagree are reported as unresolved.
- What happens next:
  1. The sheets are committed as they are.
  2. The sealed third rater (a language model, set up before any human rating) is unsealed.
  3. The scoring script compares everything with the hidden labels:
     `python scripts/analysis/label_audit.py`
  4. The paper, the Phase 3 report and the defense notes then report three things:
     - how often the two of you agree (Cohen's κ);
     - how often your decisions match the execution labels;
     - where they differ, and why.
