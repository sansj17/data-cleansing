# 03: Standardize payment terms, creation dates, names and emails

**What to build:** The rest of the Vendor fields are cleaned in the clean output. Payment Terms become `NET30`, `NET45` or `NET60`. Creation dates become real dates. Vendor names are Title Case with a standard legal suffix (`Corp`). An invalid or truncated email is blanked and flagged. Anything that cannot be parsed is blanked, flagged and listed for review, and the Vendor is still loaded.

**Blocked by:** 01 (Cleansing run with clean copies and row reconciliation)

**Status:** ready-for-agent

- [ ] Payment Terms variants (for example net-60, 60 days, N30, NET 30, Net 45) map to the three standard values
- [ ] Creation dates in mixed formats (for example 2020.05.17, 11/16/2018, 15-Mar-2021) become real dates; valid ISO dates are unchanged
- [ ] An unparseable Payment Terms or date value becomes empty, is flagged, and appears in the review table with a reason
- [ ] Names in ALL CAPS become Title Case, and Corporation, Corp. and CORP all become `Corp`; the other legal suffixes (Inc, LLC, Ltd, Co.) are standardised consistently
- [ ] An invalid email (for example `ap@acme`) becomes empty, is flagged, and is listed for review; a valid email is unchanged
- [ ] Vendors with a blanked field are still loaded
- [ ] Reconciliation from ticket 01 still passes
