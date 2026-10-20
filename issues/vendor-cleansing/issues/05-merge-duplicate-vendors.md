# 05: Merge duplicate vendors and re-point purchase orders

**What to build:** Groups of Duplicate Vendors collapse into one Surviving Vendor each, and the Purchase Orders of the merged-away Vendors point to the Surviving Vendor. A mapping records every old vendor ID and the Surviving Vendor it went to. Vendors merge automatically only when the normalised names match and the valid Tax IDs agree.

**Blocked by:** 02 (Standardize country codes), 03 (Standardize payment terms, creation dates, names and emails)

**Status:** resolved

- [x] Vendors whose names are equal once case, punctuation and legal suffix are ignored, and whose valid Tax IDs agree, are merged into one Surviving Vendor
- [x] The Surviving Vendor is the one with the most Purchase Orders, then the oldest creation date, then the lowest vendor ID (each tie-break tested)
- [x] The Surviving Vendor's fields come from the cleaned values, not the raw survivor's values
- [x] The merged Vendor is active if any record in the group was active
- [x] The merged Vendor takes the earliest creation date in the group
- [x] Every merged-away vendor ID appears in the mapping with its Surviving Vendor; a Vendor that is not merged maps to itself or is absent by a documented rule
- [x] Purchase Orders of merged-away Vendors are re-pointed to the Surviving Vendor and none are lost
- [x] Two Vendors with the same name but conflicting Tax IDs, or one blank Tax ID, are not merged
- [x] Afterwards no two active clean Vendors share a valid Tax ID
- [x] Reconciliation from ticket 01 still passes, with merged-away rows counted as their own outcome

## Notes

- Done with a shortcut: the survivor tie-break and the merged creation date only consider ISO dates; other formats sort last until ticket 03 standardises dates. The shortcut is marked in the rule file.
- Every raw vendor appears in the mapping (an unmerged vendor maps to itself). Merged-away vendors are those where the two IDs differ.
