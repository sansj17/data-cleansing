"""Cleansing rules, tested at one seam: cleanse.run(con) reads the raw tables and writes clean_*, quarantine_*, vendor_map and review_items."""

import duckdb
import pytest

from cleanse import run


@pytest.fixture
def con():
    c = duckdb.connect(":memory:")
    c.execute("""
        CREATE TABLE vendors (vendor_id INTEGER PRIMARY KEY, vendor_name VARCHAR, tax_id VARCHAR, country VARCHAR,
                              email VARCHAR, payment_terms VARCHAR, status VARCHAR, created_date VARCHAR);
        CREATE TABLE purchase_orders (po_id INTEGER PRIMARY KEY, vendor_id INTEGER, po_date DATE, amount DECIMAL(12,2), currency VARCHAR);
        CREATE TABLE invoices (invoice_id INTEGER PRIMARY KEY, po_id INTEGER, invoice_date DATE, amount DECIMAL(12,2), paid BOOLEAN);
    """)
    return c


def add_vendor(con, vendor_id, name="Acme Corp", tax_id="11-1111111", country="US", status="active", created="2020-01-01"):
    con.execute("INSERT INTO vendors VALUES (?, ?, ?, ?, 'ap@acme.com', 'NET30', ?, ?)",
                [vendor_id, name, tax_id, country, status, created])


def add_po(con, po_id, vendor_id, amount=100):
    con.execute("INSERT INTO purchase_orders VALUES (?, ?, '2021-01-01', ?, 'USD')", [po_id, vendor_id, amount])


def add_invoice(con, invoice_id, po_id, amount=100, paid=True):
    con.execute("INSERT INTO invoices VALUES (?, ?, '2021-02-01', ?, ?)", [invoice_id, po_id, amount, paid])


def count(con, sql):
    return con.execute(sql).fetchone()[0]


def raw_snapshot(con):
    return [con.execute(f"SELECT * FROM {t} ORDER BY 1").fetchall() for t in ("vendors", "purchase_orders", "invoices")]


# --- 01: the run itself -------------------------------------------------------

def test_run_leaves_raw_tables_untouched(con):
    add_vendor(con, 1, country="Canada")
    add_po(con, 10, 1)
    add_invoice(con, 100, 10)
    before = raw_snapshot(con)
    run(con)
    assert raw_snapshot(con) == before


def test_run_is_repeatable(con):
    add_vendor(con, 1)
    add_po(con, 10, 1)
    run(con)
    first = con.execute("SELECT * FROM clean_vendors ORDER BY vendor_id").fetchall()
    run(con)
    assert con.execute("SELECT * FROM clean_vendors ORDER BY vendor_id").fetchall() == first


def test_every_raw_row_has_exactly_one_outcome(con):
    add_vendor(con, 1)
    add_vendor(con, 2, name="Other Inc", tax_id="22-2222222")
    add_po(con, 10, 1, 250)
    add_po(con, 11, 2, 50)
    add_invoice(con, 100, 10, 250)
    run(con)
    merged_away = count(con, "SELECT count(*) FROM vendor_map WHERE old_vendor_id <> surviving_vendor_id")
    assert count(con, "SELECT count(*) FROM vendors") == count(con, "SELECT count(*) FROM clean_vendors") + merged_away
    assert count(con, "SELECT count(*) FROM purchase_orders") == (
        count(con, "SELECT count(*) FROM clean_purchase_orders") + count(con, "SELECT count(*) FROM quarantine_purchase_orders"))
    assert count(con, "SELECT count(*) FROM invoices") == (
        count(con, "SELECT count(*) FROM clean_invoices") + count(con, "SELECT count(*) FROM quarantine_invoices"))
    assert count(con, "SELECT sum(amount) FROM purchase_orders") == (
        count(con, "SELECT sum(amount) FROM clean_purchase_orders") + count(con, "SELECT coalesce(sum(amount), 0) FROM quarantine_purchase_orders"))


def test_run_on_empty_raw_tables_produces_empty_outputs(con):
    run(con)
    for t in ("clean_vendors", "clean_purchase_orders", "clean_invoices", "quarantine_purchase_orders",
              "quarantine_invoices", "vendor_map", "review_items"):
        assert count(con, f"SELECT count(*) FROM {t}") == 0


def test_invoice_money_reconciles(con):
    add_vendor(con, 1)
    add_po(con, 10, 1)
    add_invoice(con, 100, 10, 40)
    add_invoice(con, 101, 10, 60, paid=False)
    run(con)
    assert count(con, "SELECT sum(amount) FROM invoices") == (
        count(con, "SELECT sum(amount) FROM clean_invoices") + count(con, "SELECT coalesce(sum(amount), 0) FROM quarantine_invoices"))


# --- 02: standardize country codes ---------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("US", "US"), ("us", "US"), ("USA", "US"), ("U.S.A.", "US"), ("United States", "US"),
    ("CA", "CA"), ("ca", "CA"), ("CAN", "CA"), ("Can.", "CA"), ("Canada", "CA"),
    ("MX", "MX"), ("mx", "MX"), ("MEX", "MX"), ("Mexico", "MX"), ("Méx", "MX"), ("  Mexico ", "MX"),
])
def test_country_variants_become_iso_codes(con, raw, expected):
    add_vendor(con, 1, country=raw)
    run(con)
    assert count(con, "SELECT country FROM clean_vendors WHERE vendor_id = 1") == expected


def test_unrecognisable_country_is_blanked_listed_and_vendor_still_loaded(con):
    add_vendor(con, 1, country="Atlantis")
    add_vendor(con, 2, country="US", name="Other Inc", tax_id="22-2222222")
    run(con)
    assert count(con, "SELECT count(*) FROM clean_vendors WHERE vendor_id = 1") == 1
    assert count(con, "SELECT country FROM clean_vendors WHERE vendor_id = 1") is None
    assert con.execute("SELECT table_name, record_id, field, raw_value FROM review_items").fetchall() == [
        ("vendors", 1, "country", "Atlantis")]


def test_every_clean_country_is_valid_or_blank(con):
    for i, c in enumerate(["USA", "Can.", "Méx", "Narnia", "mx"], start=1):
        add_vendor(con, i, country=c, name=f"Vendor {i} Corp", tax_id=f"1{i}-111111{i}")
    run(con)
    assert count(con, "SELECT count(*) FROM clean_vendors WHERE country IS NOT NULL AND country NOT IN ('US','CA','MX')") == 0


# --- 05: merge duplicate vendors and re-point purchase orders --------------------

def add_duplicates(con):
    """Three spellings of one company, same Tax ID. Vendor 3 has the most POs."""
    add_vendor(con, 1, name="Fowler Trading Corporation", tax_id="24-0419610")
    add_vendor(con, 2, name="FOWLER TRADING CORP.", tax_id="24-0419610")
    add_vendor(con, 3, name="Fowler Trading Corp", tax_id="24-0419610")
    add_po(con, 10, 1)
    add_po(con, 11, 2)
    add_po(con, 12, 3)
    add_po(con, 13, 3)


def test_name_variants_with_same_tax_id_merge_into_the_vendor_with_most_purchase_orders(con):
    add_duplicates(con)
    run(con)
    assert con.execute("SELECT vendor_id FROM clean_vendors").fetchall() == [(3,)]
    assert con.execute("SELECT old_vendor_id, surviving_vendor_id FROM vendor_map ORDER BY 1").fetchall() == [(1, 3), (2, 3), (3, 3)]


def test_purchase_orders_of_merged_away_vendors_are_re_pointed_and_none_lost(con):
    add_duplicates(con)
    run(con)
    assert con.execute("SELECT po_id, vendor_id FROM clean_purchase_orders ORDER BY po_id").fetchall() == [
        (10, 3), (11, 3), (12, 3), (13, 3)]


def test_survivor_tie_on_purchase_orders_goes_to_oldest_created_date(con):
    add_vendor(con, 1, name="Hill Partners Corp", tax_id="30-7090293", created="2019-04-06")
    add_vendor(con, 2, name="HILL PARTNERS CORP.", tax_id="30-7090293", created="2015-06-27")  # oldest, higher id
    add_po(con, 10, 1)
    add_po(con, 11, 2)
    run(con)
    assert con.execute("SELECT vendor_id FROM clean_vendors").fetchall() == [(2,)]


def test_survivor_tie_on_purchase_orders_and_date_goes_to_lowest_vendor_id(con):
    add_vendor(con, 7, name="Hill Partners Corp", tax_id="30-7090293", created="2019-04-06")
    add_vendor(con, 5, name="HILL PARTNERS CORP.", tax_id="30-7090293", created="2019-04-06")
    run(con)
    assert con.execute("SELECT vendor_id FROM clean_vendors").fetchall() == [(5,)]


def test_merged_vendor_is_active_if_any_record_was_and_takes_the_earliest_created_date(con):
    add_vendor(con, 1, name="Doyle Industries Corp", tax_id="39-1694522", status="inactive", created="2022-02-13")  # survivor: most POs
    add_vendor(con, 2, name="DOYLE INDUSTRIES CORP.", tax_id="39-1694522", status="active", created="2017-05-08")
    add_po(con, 10, 1)
    add_po(con, 11, 1)
    add_po(con, 12, 2)
    run(con)
    assert con.execute("SELECT vendor_id, status, created_date FROM clean_vendors").fetchall() == [(1, "active", "2017-05-08")]


def test_merged_status_is_inactive_when_every_record_was_inactive(con):
    add_vendor(con, 1, name="Doyle Industries Corp", tax_id="39-1694522", status="inactive")
    add_vendor(con, 2, name="DOYLE INDUSTRIES CORP.", tax_id="39-1694522", status="inactive")
    run(con)
    assert con.execute("SELECT status FROM clean_vendors").fetchall() == [("inactive",)]


@pytest.mark.parametrize("tax_a, tax_b", [
    ("30-7090293", "99-9999999"),  # conflicting valid Tax IDs
    ("30-7090293", ""),            # one blank
    ("", ""),                      # both blank
    (None, None),                  # both null
    ("123456789", "123456789"),    # same malformed value is not a valid Tax ID
])
def test_same_name_without_agreeing_valid_tax_ids_is_not_merged(con, tax_a, tax_b):
    add_vendor(con, 1, name="Hill Partners Corp", tax_id=tax_a)
    add_vendor(con, 2, name="HILL PARTNERS CORP.", tax_id=tax_b)
    run(con)
    assert count(con, "SELECT count(*) FROM clean_vendors") == 2


def test_similar_name_only_is_not_merged(con):
    add_vendor(con, 1, name="Bright Trading Corp", tax_id="30-7090293")
    add_vendor(con, 2, name="Wright Trading Corp", tax_id="30-7090293")
    run(con)
    assert count(con, "SELECT count(*) FROM clean_vendors") == 2


def test_reconciliation_holds_after_a_merge(con):
    add_duplicates(con)
    add_vendor(con, 4, name="Other Inc", tax_id="22-2222222")
    add_po(con, 14, 4, 75)
    add_invoice(con, 100, 12, 100)
    run(con)
    merged_away = count(con, "SELECT count(*) FROM vendor_map WHERE old_vendor_id <> surviving_vendor_id")
    assert merged_away == 2
    assert count(con, "SELECT count(*) FROM vendors") == count(con, "SELECT count(*) FROM clean_vendors") + merged_away
    assert count(con, "SELECT sum(amount) FROM purchase_orders") == count(con, "SELECT sum(amount) FROM clean_purchase_orders")


# --- invariants on the real inherited database (copied into memory; the file is never written) ---

@pytest.fixture(scope="module")
def real(tmp_path_factory):
    import shutil
    from pathlib import Path
    db = Path(__file__).parent.parent / "suppliers.duckdb"
    if not db.exists():
        pytest.skip("suppliers.duckdb not generated")
    copy = tmp_path_factory.mktemp("real") / "suppliers.duckdb"  # a copy: another process may hold a lock on the original
    shutil.copy(db, copy)
    c = duckdb.connect(":memory:")
    c.execute(f"ATTACH '{copy}' AS src (READ_ONLY)")
    for t in ("vendors", "purchase_orders", "invoices"):
        c.execute(f"CREATE TABLE {t} AS SELECT * FROM src.{t}")
    run(c)
    return c


def test_real_db_every_vendor_has_one_outcome(real):
    merged_away = count(real, "SELECT count(*) FROM vendor_map WHERE old_vendor_id <> surviving_vendor_id")
    assert count(real, "SELECT count(*) FROM vendors") == count(real, "SELECT count(*) FROM clean_vendors") + merged_away
    assert count(real, "SELECT count(*) FROM clean_vendors") == 182  # 200 vendors minus 18 surplus duplicates


def test_real_db_every_country_is_valid_or_blank(real):
    assert count(real, "SELECT count(*) FROM clean_vendors WHERE country IS NOT NULL AND country NOT IN ('US','CA','MX')") == 0


def test_real_db_no_two_active_vendors_share_a_valid_tax_id(real):
    assert count(real, """SELECT count(*) FROM (SELECT tax_id FROM clean_vendors
                          WHERE status = 'active' AND regexp_matches(tax_id, '^\\d{2}-\\d{7}$') GROUP BY 1 HAVING count(*) > 1)""") == 0


def test_real_db_merging_leaves_no_purchase_order_without_its_vendor_except_raw_orphans(real):
    assert count(real, """SELECT count(*) FROM clean_purchase_orders p
                          WHERE p.vendor_id NOT IN (SELECT vendor_id FROM clean_vendors)
                            AND p.vendor_id IN (SELECT vendor_id FROM vendors)""") == 0


def test_real_db_no_purchase_order_or_money_is_lost(real):
    assert count(real, "SELECT count(*) FROM purchase_orders") == count(real, "SELECT count(*) FROM clean_purchase_orders")
    assert count(real, "SELECT sum(amount) FROM purchase_orders") == count(real, "SELECT sum(amount) FROM clean_purchase_orders")
