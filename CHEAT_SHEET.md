# Presenter cheat sheet

Never open `answer_key.json` in the session. Before: `uv run python generate_data.py && uv run python check_data.py`, then `/setup-matt-pocock-skills` (issue tracker = local files, `issues/`).

| Step                    | Prompt to type                                                                                                                                                                                                                                                                |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Understand (8 min)   | `We inherited suppliers.duckdb ahead of an ERP migration. Inspect the schema and sample rows, then use /domain-modeling to write a GLOSSARY.md of the domain terms. Then use diagram-design to draw an ER diagram, saved to diagrams/er.html.`                                |
| 2. Profile (7 min)      | `Profile the data quality in suppliers.duckdb: null rates, near-duplicate vendors, orphaned records, inconsistent values. Save the queries to sql/profile.sql and report counts. Then use diagram-design to draw a fishbone of likely root causes in diagrams/fishbone.html.` |
| 3. Decide rules (5 min) | `/grill-me` on the cleansing plan: which record survives a merge, delete vs quarantine orphans, does a missing tax ID block migration. Then `/to-spec` and `/to-tickets` (local files in issues/).`                                                                           |
| 4. Fix (10 min)         | `/tdd` on the issue "standardize country codes", then on "merge duplicate vendors and re-point purchase orders". Rules: never delete (quarantine*\* with a reason), raw tables untouched (clean*\* outputs), every rule has a test in tests/test_rules.py.`                   |
| 5. Results (5 min)      | `Compute before/after metrics from raw vs clean_* and quarantine_* tables. Then use diagram-design to draw a Sankey of raw rows flowing into clean, merged, or quarantined, in diagrams/sankey.html.`                                                                         |
| 6. Wrap-up (2 min)      | `/handoff`                                                                                                                                                                                                                                                                    |

Afterwards (presenter only): compare the agent's findings against `answer_key.json`; `uv run python check_data.py` confirms the planted counts.

Timing notes: generate + check takes under 1 s; profile.sql runs in about 0.1 s. Everything else is agent time, so rehearse it once to confirm the budget.
