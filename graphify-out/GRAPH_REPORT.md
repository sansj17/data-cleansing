# Graph Report - data-cleansing  (2026-10-20)

## Corpus Check
- Corpus is ~12,577 words - fits in a single context window. You may not need a graph.

## Summary
- 157 nodes · 319 edges · 12 communities (8 shown, 4 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Tests and Fixtures
- Runner and Data Scripts
- Spec and Tickets
- Case Study and Data Model
- Glossary and Agent Config
- Fishbone Root Causes
- Sankey Row Flow
- Init Rule and Output Tables
- Profile Queries
- Project Root

## God Nodes (most connected - your core abstractions)
1. `Spec: Cleanse Supplier Database` - 24 edges
2. `run()` - 20 edges
3. `Case Study: Supplier Database Cleansing Demo` - 17 edges
4. `add_vendor()` - 16 edges
5. `count()` - 15 edges
6. `Supplier Payables Glossary` - 15 edges
7. `Supplier Data Fishbone` - 15 edges
8. `Effect: data fails basic quality checks before migration` - 12 edges
9. `add_po()` - 9 edges
10. `Supplier Row Flow Sankey` - 8 edges

## Surprising Connections (you probably didn't know these)
- `No foreign keys: 33 orphans` --semantically_similar_to--> `Orphan`  [INFERRED] [semantically similar]
  diagrams/fishbone.html → GLOSSARY.md
- `Planted problems P1-P10` --references--> `Supplier Data Fishbone`  [INFERRED]
  CASE_STUDY.md → diagrams/fishbone.html
- `Cleansing principles: never delete, raw untouched, every rule tested` --conceptually_related_to--> `Never delete: quarantine with reason`  [INFERRED]
  CASE_STUDY.md → issues/vendor-cleansing/spec.md
- `vendors (200 rows)` --semantically_similar_to--> `vendors table`  [INFERRED] [semantically similar]
  diagrams/er.html → CASE_STUDY.md
- `purchase_orders (800 rows)` --semantically_similar_to--> `purchase_orders table`  [INFERRED] [semantically similar]
  diagrams/er.html → CASE_STUDY.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Demo pipeline: glossary, diagrams, spec, tickets** — glossary, diagrams_er, diagrams_fishbone, issues_vendor_cleansing_spec, diagrams_sankey [INFERRED 0.85]
- **Every raw row ends in one outcome** — issues_vendor_cleansing_spec_reconciliation, glossary_quarantine, glossary_surviving_vendor, issues_vendor_cleansing_spec_review_table [INFERRED 0.85]

## Communities (12 total, 4 thin omitted)

### Community 0 - "Tests and Fixtures"
Cohesion: 0.15
Nodes (31): run(), add_duplicates(), add_invoice(), add_po(), add_vendor(), con(), count(), raw_snapshot() (+23 more)

### Community 1 - "Runner and Data Scripts"
Cohesion: 0.14
Nodes (11): main(), build_invoices(), build_orders(), build_vendors(), main(), money(), new_core(), new_tax() (+3 more)

### Community 2 - "Spec and Tickets"
Cohesion: 0.19
Nodes (16): Issue 01: Cleansing run and reconciliation, Issue 02: Standardize country codes, Issue 03: Standardize payment terms, dates, names, emails, Issue 04: Flag tax-ID-pending vendors, Issue 05: Merge duplicate vendors and re-point POs, Issue 06: Review list for ambiguous vendor pairs, Issue 07: Quarantine orphaned POs and invoices, Issue 08: Quarantine repeated invoices (+8 more)

### Community 3 - "Case Study and Data Model"
Cohesion: 0.18
Nodes (18): Case Study: Supplier Database Cleansing Demo, answer_key.json (presenter only), Cathryn Lavery diagram-design, generate_data.py (seed 42), invoices table, Matt Pocock skills, Planted problems P1-P10, purchase_orders table (+10 more)

### Community 4 - "Glossary and Agent Config"
Cohesion: 0.19
Nodes (16): CLAUDE.md Agent Skills Config, Domain Docs Guide, Issue Tracker: Local Markdown, Supplier Payables Glossary, Country, Currency, Duplicate Vendor, Invoice (+8 more)

### Community 5 - "Fishbone Root Causes"
Cohesion: 0.29
Nodes (13): Supplier Data Fishbone, ALL-CAPS name variants: 12, Free-text country: 15 spellings, Dates stored as text: 25 non-ISO, Effect: data fails basic quality checks before migration, Truncated emails: 14, Inactive vendors get POs: 66, No duplicate check: 18 surplus (+5 more)

### Community 6 - "Sankey Row Flow"
Cohesion: 0.39
Nodes (8): Supplier Row Flow Sankey, Clean: 2,413 rows, Loaded: 2,482 rows, Merged away: 18 vendor rows, Orphan, still loaded: 22 POs + 47 invoices, Quarantined: 0 rows, Raw tables: 200 vendors, 800 POs, 1,500 invoices, Quarantine

### Community 7 - "Init Rule and Output Tables"
Cohesion: 0.25
Nodes (7): clean_invoices, clean_purchase_orders, clean_vendors, quarantine_invoices, quarantine_purchase_orders, review_items, vendor_map

## Knowledge Gaps
- **3 isolated node(s):** `data-cleansing`, `Tech stack: uv, DuckDB, Python, pytest`, `Relationships not enforced: no foreign keys`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 26 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Case Study: Supplier Database Cleansing Demo` connect `Case Study and Data Model` to `Spec and Tickets`, `Fishbone Root Causes`, `Sankey Row Flow`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Spec: Cleanse Supplier Database` (e.g. with `Case Study: Supplier Database Cleansing Demo` and `Issue Tracker: Local Markdown`) actually correct?**
  _`Spec: Cleanse Supplier Database` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `data-cleansing`, `Tech stack: uv, DuckDB, Python, pytest`, `Relationships not enforced: no foreign keys` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Runner and Data Scripts` be split into smaller, more focused modules?**
  _Cohesion score 0.13846153846153847 - nodes in this community are weakly interconnected._
- **Why does `Spec: Cleanse Supplier Database` connect `Spec and Tickets` to `Case Study and Data Model`, `Glossary and Agent Config`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Case Study: Supplier Database Cleansing Demo` (e.g. with `Spec: Cleanse Supplier Database` and `Presenter Cheat Sheet`) actually correct?**
  _`Case Study: Supplier Database Cleansing Demo` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Why does `Supplier Data Fishbone` connect `Fishbone Root Causes` to `Case Study and Data Model`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._