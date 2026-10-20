"""Re-detect every planted problem in suppliers.duckdb with SQL and compare to the spec and answer_key.json."""

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).parent
EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
DUP = "tax_id IN (SELECT tax_id FROM vendors WHERE tax_id ~ '^\\d{2}-\\d{7}$' GROUP BY 1 HAVING count(*) > 1)"

# problem -> (expected count, query returning the affected primary keys)
CHECKS = {
    "P1": (30, f"SELECT vendor_id FROM vendors WHERE {DUP}"),
    "P2": (40, "SELECT vendor_id FROM vendors WHERE country NOT IN ('CA','US','MX')"),
    "P3": (18, "SELECT vendor_id FROM vendors WHERE tax_id IS NULL OR trim(tax_id) = ''"),
    "P4": (9, "SELECT vendor_id FROM vendors WHERE trim(tax_id) <> '' AND NOT regexp_matches(tax_id, '^\\d{2}-\\d{7}$')"),
    "P5": (14, f"SELECT vendor_id FROM vendors WHERE NOT regexp_matches(email, '{EMAIL}')"),
    "P6": (35, "SELECT vendor_id FROM vendors WHERE payment_terms NOT IN ('NET30','NET45','NET60')"),
    "P7": (25, "SELECT vendor_id FROM vendors WHERE NOT regexp_matches(created_date, '^\\d{4}-\\d{2}-\\d{2}$')"),
    "P8": (22, "SELECT po_id FROM purchase_orders WHERE vendor_id NOT IN (SELECT vendor_id FROM vendors)"),
    "P9": (11, "SELECT invoice_id FROM invoices WHERE po_id NOT IN (SELECT po_id FROM purchase_orders)"),
    "P10": (
        60,
        f"""SELECT po_id FROM purchase_orders WHERE vendor_id IN (
            SELECT vendor_id FROM vendors WHERE {DUP}
              AND vendor_id <> (SELECT min(v.vendor_id) FROM vendors v WHERE v.tax_id = vendors.tax_id))""",
    ),
}


def main() -> int:
    con = duckdb.connect(str(ROOT / "suppliers.duckdb"), read_only=True)
    key = json.loads((ROOT / "answer_key.json").read_text())
    failed = 0
    for pid, (expected, sql) in CHECKS.items():
        found = sorted(r[0] for r in con.execute(sql).fetchall())
        keyed = key[pid]["rows"] if pid == "P1" else key[pid]
        ok = len(found) == expected and found == sorted(keyed)
        failed += not ok
        print(f"{pid:<4} expected={expected:<3} found={len(found):<3} key_match={found == sorted(keyed)}  {'OK' if ok else 'FAIL'}")
    clusters = con.execute(f"SELECT count(DISTINCT tax_id) FROM vendors WHERE {DUP}").fetchone()[0]
    print(f"P1 clusters: {clusters} (expected 12)")
    failed += clusters != 12
    for t, n in [("vendors", 200), ("purchase_orders", 800), ("invoices", 1500)]:
        got = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"{t}: {got} (expected {n})")
        failed += got != n
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
