# 08: Quarantine repeated invoices

**What to build:** Invoices that repeat another Invoice exactly (same Purchase Order, date and amount) are reduced to one in the clean output, so we do not pay twice. The extra copies go to Quarantine as possible duplicates, never deleted.

**Blocked by:** 07 (Quarantine orphaned purchase orders and invoices)

**Status:** ready-for-agent

- [ ] In a set of repeated Invoices, the paid one is kept; if none or all are paid, the lowest invoice ID is kept
- [ ] The other Invoices in the set are quarantined with the reason possible duplicate
- [ ] A set where a copy is paid and the lowest ID is unpaid keeps the paid copy
- [ ] Invoices that differ in Purchase Order, date or amount are not treated as repeats
- [ ] An Invoice already quarantined as an orphan is not counted again (a row is in exactly one outcome)
- [ ] Reconciliation from ticket 01 still passes, including money totals
