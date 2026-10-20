# 07: Quarantine orphaned purchase orders and invoices

**What to build:** Records that point to a parent that does not exist are set aside in Quarantine with a reason, never deleted, and are left out of the clean output. This covers Purchase Orders with no Vendor, Invoices with no Purchase Order, and Invoices whose Purchase Order was itself quarantined. Orphans are judged after the merge, so a Purchase Order re-pointed to a Surviving Vendor is not an Orphan.

**Blocked by:** 05 (Merge duplicate vendors and re-point purchase orders)

**Status:** ready-for-agent

- [ ] A Purchase Order whose Vendor does not exist (before or after the merge) is quarantined with the reason orphaned purchase order
- [ ] A Purchase Order that was re-pointed to a Surviving Vendor is not quarantined
- [ ] An Invoice whose Purchase Order does not exist is quarantined with the reason orphaned invoice
- [ ] An Invoice whose Purchase Order was quarantined is quarantined with the reason parent purchase order orphaned
- [ ] No orphaned or indirectly orphaned row appears in the clean output
- [ ] Every quarantined row keeps all its original values and carries a reason
- [ ] Nothing is deleted from the raw tables
- [ ] The total and the unpaid amount of Invoices in Quarantine can be read from the output
- [ ] Every loaded Purchase Order references a loaded Vendor, and every loaded Invoice references a loaded Purchase Order
- [ ] Reconciliation from ticket 01 still passes
