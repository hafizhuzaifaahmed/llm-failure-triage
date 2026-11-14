# Instructions for rater C

You are rater C in a label audit of failing generated unit tests. You work alone.

Files in this folder:

- `LABEL_AUDIT_RUBRIC.md` — the rubric. Read it first. Its decisions are PF, TF and AMB; use them exactly as defined.
- `packets_rater_C.pdf` — your blind packet: the rubric again, then **Part 1: 10 calibration items** (CAL01–CAL10),
  then **Part 2: 71 audit items** in your order (01.–71.). Each item shows the generated test, the failure on the buggy
  version, the focal method's Javadoc and the developer's fix (buggy → fixed).
- `calibration_rater_C.csv` — fill one row per calibration item.
- `label_audit_rater_C.csv` — fill one row per audit item (the `order` column matches the packet numbering).

For every item: decide **PF**, **TF** or **AMB**; give a **confidence** of 1 (guess), 2 (fairly sure) or 3 (certain);
add a one-sentence **note** whenever the decision is not obvious. Fill only the `decision`, `confidence` and `notes`
columns; keep every other column, the header, the row order and the CSV format unchanged.

Differences from the human procedure: there is no second rater to compare with and no answer key, so step 2 of the
rubric's procedure does not apply to you. Do the calibration items first, then the audit items, in order.

Use only what is in this folder. Do not try to open any other file or use any other source.
