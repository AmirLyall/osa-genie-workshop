# NC OSA Genie Workshop

One-hour Genie lunch and learn for business users at the NC Office of the State Auditor, Tue, Nov 10, 2026, 12:00 to 1:00 PM ET.

| File | What it is |
|---|---|
| `index.html`, `styles.css`, `app.js` | The workshop guide attendees follow. Static, so open `index.html` directly or host it anywhere. |
| `setup.html` | Setup steps for the OSA data team. |
| `facilitator.html` | Presenter prep and run of show. |
| `osa_genie_workshop_setup.py` | Databricks notebook (SOURCE format). Builds `<catalog>.osa_pcard_review` (6 synthetic tables with descriptions), creates or updates the **OSA P-Card Review (Workshop)** Genie Agent, optionally shares both with a group, and runs a self-test. |
| `osa_pcard_test_sample.csv` | 60-row synthetic test workpaper for the file-upload demo. |

Notebook widgets: `catalog` (required), `schema` (default `osa_pcard_review`), `warehouse_id` (blank = auto), `share_with_group`, `agent_title`. Fixed seed, so every workspace gets the same numbers. Re-running overwrites the tables and updates the agent in place.

All data is synthetic and for training only.
