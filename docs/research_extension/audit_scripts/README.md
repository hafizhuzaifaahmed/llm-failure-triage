# Audit scripts (read-only)

Used for `CONFIRMATION_INDEPENDENT_AUDIT.md` on 2026-11-13. They import no project module.

    python docs/research_extension/audit_scripts/audit_recompute.py . <rows.json>     # registered quantities from tranche records; writes rows.json
    python docs/research_extension/audit_scripts/audit_robustness.py <rows.json>      # project, frame, eligibility and ranking checks (exploratory)
    python docs/research_extension/audit_scripts/audit_pilot.py .                     # pilot by project; frame overlap

Write `rows.json` outside the frozen paths (for example under `results/extension/audit/`).

Added after the P1 replication (2026-11-13):

    python docs/research_extension/audit_scripts/audit_seedcheck.py <rows.json>       # registered seed reproduced independently; spread over 20 other seeds
    python docs/research_extension/audit_scripts/audit_labels_full.py . <out.json>    # fresh label rule on every labelled instance (derived from scripts/extension/audit/a2_labels.py)
