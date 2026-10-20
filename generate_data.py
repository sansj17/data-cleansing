"""Build suppliers.duckdb and answer_key.json (synthetic data, seed 42)."""

import json
import random
import re
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import duckdb
from faker import Faker

SEED = 42
ROOT = Path(__file__).parent
rng = random.Random(SEED)
Faker.seed(SEED)
fake = Faker()

WORDS = ["Industries", "Logistics", "Supply", "Systems", "Holdings", "Trading", "Partners"]
SUFFIXES = ["Inc", "Ltd", "LLC", "Corp", "Co."]
TERMS = ["NET30", "NET45", "NET60"]
COUNTRY_VARIANTS = {
    "CA": ["Canada", "CAN", "ca", "Can."],
    "US": ["USA", "United States", "us", "U.S.A."],
    "MX": ["Mexico", "Méx", "MEX", "mx"],
}
BAD_EMAILS = ["ap@acme", "billing.acme.com", "n/a", "ap acme@x.com", "ap@@acme.com"]


def rand_date(a: date, b: date) -> date:
    return a + timedelta(days=rng.randrange((b - a).days + 1))


def money(cents: int) -> Decimal:
    return Decimal(cents) / 100


_cores: set[str] = set()
_taxes: set[str] = set()


def new_core() -> str:
    while True:
        core = f"{fake.last_name()} {rng.choice(WORDS)}"
        if core.lower() not in _cores:
            _cores.add(core.lower())
            return core


def new_tax() -> str:
    while True:
        tax = f"{rng.randrange(10, 100)}-{rng.randrange(10**7):07d}"
        if tax not in _taxes:
            _taxes.add(tax)
            return tax


def new_vendor(name: str, core: str, tax: str, country: str, cluster: int | None) -> dict:
    return {
        "vendor_name": name,
        "tax_id": tax,
        "country": country,
        "email": f"ap@{re.sub(r'\W', '', core.lower())}.com",
        "payment_terms": rng.choice(TERMS),
        "status": "active" if rng.random() < 0.9 else "inactive",
        "created_date": rand_date(date(2015, 1, 1), date(2022, 12, 31)),
        "cluster": cluster,
    }


def build_vendors() -> tuple[list[dict], list[dict]]:
    rows, clusters = [], []
    # P1: 6 clusters of 3 + 6 of 2 = 12 clusters, 30 rows
    for n, size in enumerate([3] * 6 + [2] * 6):
        core, tax, country = new_core(), new_tax(), rng.choice(list(COUNTRY_VARIANTS))
        variants = [f"{core} Corp", f"{core} Corporation", f"{core.upper()} CORP."]
        rows += [new_vendor(v, core, tax, country, n) for v in rng.sample(variants, size)]
    for _ in range(170):
        core = new_core()
        rows.append(
            new_vendor(f"{core} {rng.choice(SUFFIXES)}", core, new_tax(), rng.choice(list(COUNTRY_VARIANTS)), None)
        )
    rng.shuffle(rows)
    for i, r in enumerate(rows, 1):
        r["vendor_id"] = i
    for n in range(12):
        members = [r for r in rows if r["cluster"] == n]
        survivor = min(members, key=lambda r: r["vendor_id"])
        survivor["status"] = "active"  # the intended survivor is the lowest id, kept active
        clusters.append(
            {
                "tax_id": survivor["tax_id"],
                "survivor": survivor["vendor_id"],
                "members": [r["vendor_id"] for r in members],
            }
        )
    return rows, clusters


def plant_vendor_problems(rows: list[dict]) -> dict:
    key: dict = {}
    singles = [r for r in rows if r["cluster"] is None]

    p3 = rng.sample(singles, 18)
    for i, r in enumerate(p3):
        r["tax_id"] = None if i < 9 else ""
    p4 = rng.sample([r for r in singles if r not in p3], 9)
    for r in p4:
        r["tax_id"] = rng.choice(
            [
                f"{rng.randrange(10**9):09d}",
                f"{rng.randrange(10, 100)}-{rng.randrange(10**5):05d}",
                f"AB-{rng.randrange(10**7):07d}",
                f"{rng.randrange(10, 100)}-{rng.randrange(10**7):07d}X",
            ]
        )
    p2 = rng.sample(rows, 40)
    for r in p2:
        r["country"] = rng.choice(COUNTRY_VARIANTS[r["country"]])
    p5 = rng.sample(rows, 14)
    for r in p5:
        r["email"] = rng.choice(BAD_EMAILS)
    p6 = rng.sample(rows, 35)
    for r in p6:
        n = r["payment_terms"][3:]
        r["payment_terms"] = rng.choice([f"Net {n}", f"N{n}", f"{n} days", f"net-{n}", f"NET {n}"])
    p7 = rng.sample(rows, 25)
    for r in p7:
        d = r["created_date"].replace(day=rng.randrange(13, 29))  # day > 12 keeps formats unambiguous
        r["created_date"] = d.strftime(rng.choice(["%m/%d/%Y", "%d-%b-%Y", "%Y.%m.%d"]))

    for r in rows:
        if isinstance(r["created_date"], date):
            r["created_date"] = r["created_date"].isoformat()
    for pid, group in {"P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6, "P7": p7}.items():
        key[pid] = sorted(r["vendor_id"] for r in group)
    return key


def build_orders(vendors: list[dict], clusters: list[dict]) -> tuple[list[tuple], list[int], list[int]]:
    nonsurvivors = [m for c in clusters for m in c["members"] if m != c["survivor"]]
    healthy = [r["vendor_id"] for r in vendors if r["vendor_id"] not in nonsurvivors]
    sources = (
        [("ok", rng.choice(healthy)) for _ in range(718)]
        + [("dup", v) for v in nonsurvivors + rng.choices(nonsurvivors, k=42)]  # every duplicate gets >= 1 PO
        + [("orphan", 9001 + i) for i in range(22)]
    )
    rng.shuffle(sources)
    pos, p8, p10 = [], [], []
    for po_id, (kind, vendor_id) in enumerate(sources, 1):
        pos.append(
            (po_id, vendor_id, rand_date(date(2020, 1, 1), date(2024, 12, 31)), money(rng.randrange(5_000, 500_000)), rng.choice(["CAD", "USD", "MXN"]))
        )
        {"orphan": p8, "dup": p10}.get(kind, []).append(po_id)
    return pos, p8, p10


def build_invoices(pos: list[tuple]) -> tuple[list[tuple], list[int]]:
    kinds = ["ok"] * 1489 + ["orphan"] * 11
    rng.shuffle(kinds)
    invoices, p9 = [], []
    for inv_id, kind in enumerate(kinds, 1):
        if kind == "orphan":
            p9.append(inv_id)
            row = (99_000 + len(p9), rand_date(date(2020, 1, 1), date(2025, 3, 1)), money(rng.randrange(5_000, 500_000)))
        else:
            po = rng.choice(pos)
            amount = (po[3] * Decimal(rng.choice(["0.25", "0.5", "1"]))).quantize(Decimal("0.01"))
            row = (po[0], po[2] + timedelta(days=rng.randrange(5, 61)), amount)
        invoices.append((inv_id, *row, rng.random() < 0.7))
    return invoices, p9


def main() -> None:
    vendors, clusters = build_vendors()
    key = plant_vendor_problems(vendors)
    key["P1"] = {"rows": sorted(m for c in clusters for m in c["members"]), "clusters": clusters}
    pos, key["P8"], key["P10"] = build_orders(vendors, clusters)
    invoices, key["P9"] = build_invoices(pos)

    db_path = ROOT / "suppliers.duckdb"
    db_path.unlink(missing_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute(
        """
        CREATE TABLE vendors (vendor_id INTEGER PRIMARY KEY, vendor_name VARCHAR, tax_id VARCHAR,
            country VARCHAR, email VARCHAR, payment_terms VARCHAR, status VARCHAR, created_date VARCHAR);
        CREATE TABLE purchase_orders (po_id INTEGER PRIMARY KEY, vendor_id INTEGER, po_date DATE,
            amount DECIMAL(12,2), currency VARCHAR);
        CREATE TABLE invoices (invoice_id INTEGER PRIMARY KEY, po_id INTEGER, invoice_date DATE,
            amount DECIMAL(12,2), paid BOOLEAN);
        """
    )
    cols = ["vendor_id", "vendor_name", "tax_id", "country", "email", "payment_terms", "status", "created_date"]
    con.executemany("INSERT INTO vendors VALUES (?,?,?,?,?,?,?,?)", [[r[c] for c in cols] for r in sorted(vendors, key=lambda r: r["vendor_id"])])
    con.executemany("INSERT INTO purchase_orders VALUES (?,?,?,?,?)", pos)
    con.executemany("INSERT INTO invoices VALUES (?,?,?,?,?)", invoices)
    con.close()

    (ROOT / "answer_key.json").write_text(json.dumps(dict(sorted(key.items(), key=lambda kv: int(kv[0][1:]))), indent=2))
    print(f"wrote {db_path.name}: {len(vendors)} vendors, {len(pos)} purchase orders, {len(invoices)} invoices")


if __name__ == "__main__":
    main()
