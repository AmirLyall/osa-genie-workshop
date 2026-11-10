# NC OSA Genie Workshop

One-hour Genie lunch and learn for business users at the NC Office of the State Auditor, Tue, Nov 10, 2026, 12:00 to 1:00 PM ET.

| File | What it is |
|---|---|
| `index.html`, `styles.css`, `app.js` | The workshop guide attendees follow. Static, so open `index.html` directly or host it anywhere. |
| `setup.html` | Setup steps for OSA's Databricks workspace administrators. |
| `facilitator.html` | Presenter prep and run of show. |
| `osa_genie_workshop_setup.py` | Databricks notebook (SOURCE format). Loads `<catalog>.osa_pcard_review` (6 synthetic tables with descriptions). Access grants are done by hand, see `setup.html`. Attendees create their own Genie Agents from these tables during the workshop. |
| `osa_pcard_test_sample.csv` | 60-row synthetic test workpaper for the file-upload demo. |

Notebook widgets: `catalog` (required, or set `DEFAULT_CATALOG`) and `schema` (default `osa_pcard_review`). Fixed seed, so every workspace gets the same numbers. Re-running only overwrites tables the notebook created.

All data is synthetic and for training only.
