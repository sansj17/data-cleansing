# 01: Cleansing run with clean copies and row reconciliation

**What to build:** The tracer slice. Running the cleansing takes the raw Vendor, Purchase Order and Invoice tables and produces clean tables (a faithful copy for now), plus empty Quarantine, vendor mapping and review tables. A reconciliation proves every raw row is accounted for in exactly one outcome. No cleansing rule exists yet; later tickets each add one rule on top of this path.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] The raw tables are never modified by a run
- [x] A run on an empty set of crafted rows and on a small crafted set both complete and produce the clean, Quarantine, mapping and review tables
- [x] Running twice gives the same result (repeatable)
- [x] Reconciliation: per table, raw rows = loaded rows + merged-away rows + quarantined rows, and a test fails if a row is lost or counted twice
- [x] Money totals reconcile the same way for Purchase Orders and Invoices
- [x] Tests build crafted rows in memory, run the cleansing and assert only on the output tables
