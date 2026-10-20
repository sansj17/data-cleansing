# 09: Before-and-after report

**What to build:** A report that shows the outcome of the cleansing on the real inherited database, so the migration lead can sign off the load. It shows, for each issue, the count before and after, where every record went, and what money is set aside.

**Blocked by:** 04 (Flag tax-ID-pending vendors), 06 (Review list for ambiguous vendor pairs), 08 (Quarantine repeated invoices)

**Status:** ready-for-agent

- [ ] A run on the real database satisfies the reconciliation for Vendors, Purchase Orders and Invoices, including money totals
- [ ] Rerunning the profiling checks on the clean output shows zero for every issue that was fixed (country, payment terms, creation dates, Duplicate Vendors, Orphans, repeated Invoices)
- [ ] Issues deliberately left in place are reported with their counts: tax ID pending Vendors, invalid emails blanked, Purchase Orders for inactive Vendors
- [ ] Per table, the report shows how many rows were loaded, merged away and quarantined
- [ ] The amount and the unpaid amount in Quarantine are reported
- [ ] The tax ID pending list shows each Vendor with its Purchase Order count and total
- [ ] The review list is reported with its count by reason
- [ ] The report reads from the output tables only, not from the raw numbers in this ticket
