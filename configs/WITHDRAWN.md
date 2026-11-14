# Withdrawn configuration files (D-21)

The study ran on local open-weight models served by Ollama only; API spend was zero. The following files belong to
the paid-API design that was withdrawn on 2026-10-31 (D-21) **before any study call**. They are kept, unchanged, only
because the legacy client code and its unit tests still read them; no experiment in this repository used them.

| File | What it was | Status |
|---|---|---|
| `providers.json` | OpenRouter provider pins and list prices (X-01, D-18) | withdrawn, never used for a study call |
| `budget.pilot.PROPOSED.json` | proposed paid-pilot budget | withdrawn, never approved or used |
| `_superseded_pricing.json` | earlier price table | superseded |
| `budget.example.json` | example budget for the paid client | example only |
| `local_models.json` | the pre-freeze working model configuration | superseded by `local_models.FROZEN.json` (D-57) |
| `local_scope.PRE_HELDOUT.json` | the scope before the held-out run was approved | superseded by `local_scope.json` (D-59) |

The configuration that governs every reported result is `local_models.FROZEN.json` (D-57), with the exploratory
35b profile `expl_35b.json` (D-76, D-78).
