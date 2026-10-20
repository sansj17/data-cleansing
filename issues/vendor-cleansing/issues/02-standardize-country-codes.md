# 02: Standardize country codes

**What to build:** Every Vendor's Country in the clean output is the ISO two-letter code (`US`, `CA` or `MX`), whatever spelling the raw record used. A value that cannot be recognised is blanked, flagged and listed for review, and the Vendor is still loaded.

**Blocked by:** 01 (Cleansing run with clean copies and row reconciliation)

**Status:** resolved

- [x] Known variants map to the right code, including different case, abbreviations, full names and accented spellings (for example United States, USA, U.S.A., us, Canada, Can., CAN, Mexico, Méx, mx)
- [x] A value that is already a valid code is unchanged
- [x] An unrecognisable value becomes empty, is flagged, and appears in the review table with the Vendor and the reason
- [x] The Vendor with an unrecognisable value is still loaded
- [x] Every Country in the clean vendor output is a valid two-letter code or empty-and-flagged
- [x] Reconciliation from ticket 01 still passes
