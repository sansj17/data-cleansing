Status: ready-for-agent

# Spec: Cleanse the supplier database before ERP migration

## Problem Statement

We inherited a legacy supplier database ahead of an ERP (Enterprise Resource Planning) migration. It cannot be loaded as is. The Vendor records contain 12 groups of Duplicate Vendors (30 records), Country spelled 15 ways for 3 values, Payment Terms spelled 16 ways for 3 values, 25 non-ISO dates, 27 missing or malformed Tax IDs, and 14 invalid emails. 22 Purchase Orders and 11 Invoices are Orphans, and 36 further Invoices hang off orphaned Purchase Orders. 9 Invoices repeat another Invoice exactly. The migration team cannot tell which Vendor is the real one, what money is at stake, or what is safe to load, and they must not lose any record along the way.

## Solution

Produce a cleansed copy of the data and leave the raw tables untouched. Every raw row ends up in exactly one place: loaded as is, loaded after standardisation, merged into a Surviving Vendor, or set aside in Quarantine with a reason. Rows that need a human decision go on a review list. A reconciliation proves the row counts add up, and rerunning the profiling checks shows zero for every issue that was fixed.

## User Stories

1. As a migration lead, I want the raw tables left untouched, so that I can always go back to what we inherited.
2. As a migration lead, I want cleansed data written to separate clean tables, so that the load source is unambiguous.
3. As a migration lead, I want every raw row accounted for in exactly one outcome, so that I can prove nothing was lost.
4. As a migration lead, I want a reconciliation that adds up per table, so that I can sign off the load.
5. As a migration lead, I want a before and after count for each issue, so that I can report progress to the steering group.
6. As a data steward, I want each group of Duplicate Vendors merged into one Surviving Vendor, so that the ERP has one record per real supplier.
7. As a data steward, I want the Surviving Vendor chosen by most Purchase Orders, then oldest creation date, then lowest vendor ID, so that the choice is predictable and defensible.
8. As a data steward, I want a mapping from every old vendor ID to its Surviving Vendor, so that any old reference can be traced.
9. As a data steward, I want the Purchase Orders of merged-away vendors re-pointed to the Surviving Vendor, so that no spend is split across duplicates.
10. As a data steward, I want a merged Vendor to be active if any record in its group was active, so that a live supplier is never loaded as inactive.
11. As a data steward, I want a merged Vendor to take the earliest creation date in its group, so that its history is not understated.
12. As a data steward, I want vendors merged automatically only when their normalised names match and their Tax IDs agree, so that two different companies are never merged by mistake.
13. As a data steward, I want a pair with a blank or conflicting Tax ID to go on a review list instead of merging, so that a person decides.
14. As a data steward, I want pairs that only have similar names (for example Bright and Wright Trading) to go on the review list and never merge automatically, so that near-misses are looked at.
15. As a data steward, I want legal suffix variants (Corp, Corporation, Inc, LLC, Ltd, Co) and letter case ignored when comparing names, so that obvious variants are found.
16. As a data steward, I want vendor names set to Title Case with a standard legal suffix, so that the ERP shows consistent names.
17. As a data steward, I want every Country value converted to the ISO two-letter code (US, CA, MX), so that country filters and tax rules work.
18. As a data steward, I want every Payment Terms value converted to NET30, NET45 or NET60, so that payment runs use one vocabulary.
19. As a data steward, I want every creation date converted to a real date in year-month-day form, so that dates sort and compare correctly.
20. As a data steward, I want a value I cannot parse to be blanked and flagged, not guessed, so that no wrong value enters the ERP.
21. As a data steward, I want a truncated or invalid email blanked and flagged, so that no payment notice goes to a wrong address.
22. As a data steward, I want a list of every flagged value with its vendor and reason, so that the business can fix them.
23. As an accounts payable manager, I want Vendors with a blank or malformed Tax ID to still load, so that open Purchase Orders are not blocked.
24. As an accounts payable manager, I want those Vendors flagged as tax ID pending, so that I can see which need fixing.
25. As an accounts payable manager, I want payment to a tax ID pending Vendor blocked until the Tax ID is fixed, so that we do not pay an unverified entity.
26. As an accounts payable manager, I want a list of tax ID pending Vendors with their Purchase Order totals, so that I can prioritise the fixes by spend.
27. As an accounts payable manager, I want orphaned Purchase Orders and Invoices set aside in Quarantine and never deleted, so that no financial record disappears.
28. As an accounts payable manager, I want Invoices of orphaned Purchase Orders quarantined too, so that nothing is loaded that points at a missing parent.
29. As an accounts payable manager, I want every quarantined row to carry a reason, so that I know how to resolve it.
30. As an accounts payable manager, I want the amount and the unpaid amount in Quarantine reported, so that I know the financial exposure.
31. As an accounts payable manager, I want repeated Invoices (same Purchase Order, date and amount) reduced to one, so that we do not pay twice.
32. As an accounts payable manager, I want the paid copy kept, otherwise the lowest invoice ID, so that payment status is not lost.
33. As an accounts payable manager, I want the extra copies quarantined with the reason possible duplicate, so that I can confirm them before they are discarded.
34. As an auditor, I want every merge, flag and quarantine decision traceable to a rule, so that I can explain any record.
35. As an auditor, I want the Purchase Orders for inactive Vendors reported and left unchanged, so that history is not rewritten.
36. As an auditor, I want money totals before and after to match once quarantined amounts are included, so that no amount vanishes.
37. As a developer, I want each cleansing rule written test-first, so that each rule is proven.
38. As a developer, I want the cleansing to be repeatable and give the same result on every run, so that the result is reliable.
39. As a developer, I want the cleansing to run on a small crafted dataset in tests, so that edge cases are cheap to cover.
40. As a developer, I want the profiling checks to report zero for fixed issues after cleansing, so that regressions are caught.
41. As a presenter, I want before and after metrics and a view of where every record went, so that the outcome is easy to show.

## Implementation Decisions

- **One entry point.** The cleansing is an ordered set of SQL rules, one per rule, run in a fixed order against a DuckDB connection. Input is the raw tables (vendors, purchase orders, invoices); output is new tables. The raw tables are never modified.
- **Output tables.** Clean tables hold the loadable vendors, purchase orders and invoices. Quarantine tables hold set-aside rows, each with a reason. A vendor mapping table holds old vendor ID to Surviving Vendor ID. A review table holds items needing a human decision (vendor pairs, unparseable values).
- **Order of rules.** Standardise vendor fields, then detect and merge Duplicate Vendors, then re-point Purchase Orders, then quarantine Orphans, then quarantine repeated Invoices, then flag tax ID pending Vendors. Standardisation comes first because name matching relies on standardised names.
- **Surviving Vendor.** The record in a group with the most Purchase Orders. Ties go to the oldest creation date, then the lowest vendor ID. Cleaned fields come from the standardisation rules, not from the survivor's raw values. The merged Vendor is active if any record in the group was active, and takes the earliest creation date in the group.
- **Merge condition.** Automatic only when normalised names are equal (case, punctuation and legal suffix ignored) and the valid Tax IDs agree. A blank or conflicting Tax ID, or a similar-name-only match, goes to the review table and is not merged.
- **Standard forms.** Country is an ISO two-letter code (US, CA, MX). Payment Terms are NET30, NET45 or NET60. Creation date is a date type in year-month-day form. Names are Title Case with the suffix Corp. A value that cannot be parsed is set to empty, flagged and listed in the review table; the Vendor is still loaded.
- **Orphans.** Orphaned Purchase Orders are quarantined, and so are the Invoices that hang off them. Orphaned Invoices are quarantined. Nothing is deleted. Orphan status is judged after merging, so a Purchase Order re-pointed to a Surviving Vendor is not an Orphan.
- **Repeated Invoices.** Within a set of Invoices sharing Purchase Order, date and amount, keep the paid one, otherwise the lowest invoice ID. Quarantine the others with the reason possible duplicate.
- **Tax ID.** A blank or malformed Tax ID does not block loading. The Vendor is flagged tax ID pending, and payment is blocked for it. The flag appears in the clean vendor output.
- **Left alone.** Purchase Orders for inactive Vendors and Purchase Orders dated before a Vendor's creation date are loaded as they are and reported only. The earliest-creation-date rule for merged Vendors will resolve many of the latter.
- **Reconciliation.** Per table, rows in the raw table equal loaded rows plus merged-away rows plus quarantined rows. Money totals reconcile the same way.
- **Glossary.** The terms Surviving Vendor and Quarantine are added to the project glossary.

## Testing Decisions

- **Good test.** Asserts only on external behaviour: what is in the clean, quarantine, mapping and review tables after the cleansing runs. It does not check how a rule is written or the order of SQL statements.
- **One seam.** The cleansing run (ordered rules against a DuckDB connection). Each rule gets tests that build a few crafted rows in an in-memory database, run the cleansing, and assert on the output tables.
- **Per rule.** Tests are written before the rule. Each covers the happy path and at least one edge case: tie-breaks for the survivor, a blank Tax ID in a group, a similar-name pair that must not merge, a Purchase Order whose vendor was merged away, an Invoice orphaned only through its Purchase Order, a paid and an unpaid repeated Invoice.
- **Invariants on the real database.** One test runs on the real database and checks the reconciliation (every raw row in exactly one outcome, money totals match). It also checks that no two active vendors share a valid Tax ID, that every loaded Purchase Order references a loaded Vendor, and that every loaded Country value is a valid two-letter code.
- **Prior art.** The repo has a script that re-detects the planted problems with SQL and compares counts to the expected values, and a profiling query file. The profiling queries should return zero for fixed issues after cleansing. There are no existing automated tests.

## Out of Scope

- Loading data into the ERP, or any ERP-specific field mapping.
- Fixing Tax IDs, emails or other values the business must supply. They are flagged and listed only.
- Deciding the review-list cases (blank-Tax-ID pairs, similar-name pairs). The spec produces the list, not the decisions.
- Currency conversion between USD, CAD and MXN.
- Changing the raw schema, such as adding foreign keys to the raw tables.
- Correcting Purchase Orders for inactive Vendors or dated before the Vendor existed, beyond the merged creation date.

## Further Notes

- "Unparseable value is blanked, flagged and listed, and the Vendor is still loaded" is my reading of the agreed rule that such a row goes to the review list and is not loaded with a guess. Say if you meant the whole Vendor should be held back.
- The counts in this spec come from the profiling queries run on the inherited database. The cleansing should be written against the rules, not against these numbers.
- No triage label vocabulary is configured, so readiness is recorded as a status line at the top.
