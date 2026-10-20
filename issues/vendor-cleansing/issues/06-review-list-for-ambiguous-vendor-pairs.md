# 06: Review list for ambiguous vendor pairs

**What to build:** Vendor pairs that look related but are not safe to merge automatically appear on a review list for a person to decide. Nothing on this list is merged or changed. The list says why each pair is there.

**Blocked by:** 05 (Merge duplicate vendors and re-point purchase orders)

**Status:** ready-for-agent

- [ ] A pair with the same normalised name where one Tax ID is blank is listed with the reason blank Tax ID
- [ ] A pair with the same normalised name but conflicting Tax IDs is listed with the reason conflicting Tax ID
- [ ] A pair with only similar names (for example Bright Trading Corp and Wright Trading Corp) is listed with the reason similar name only, and is never merged
- [ ] Pairs already merged by ticket 05 are not listed
- [ ] Both Vendors of a listed pair stay loaded and unchanged
- [ ] Each entry shows both vendor IDs and names, the reason, and the Purchase Order count of each side
- [ ] Reconciliation from ticket 01 still passes
