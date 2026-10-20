# 04: Flag tax-ID-pending vendors

**What to build:** A Vendor with a blank or malformed Tax ID is not blocked from migration. It loads in the clean output flagged as tax ID pending, with payment marked as blocked until the Tax ID is fixed. The business can see which Vendors need fixing and how much spend each carries.

**Blocked by:** 01 (Cleansing run with clean copies and row reconciliation)

**Status:** ready-for-agent

- [ ] A Vendor with a missing (empty or null) Tax ID is loaded, flagged tax ID pending, and payment-blocked
- [ ] A Vendor with a malformed Tax ID (for example 9 digits with no dash, `46-6406756X`, `49-23627`) is handled the same way
- [ ] A Vendor with a valid Tax ID is not flagged and not payment-blocked
- [ ] The malformed value is not corrected or guessed
- [ ] The Purchase Orders of a tax ID pending Vendor are loaded normally
- [ ] A listing of tax ID pending Vendors with their Purchase Order count and total is available
- [ ] Reconciliation from ticket 01 still passes
