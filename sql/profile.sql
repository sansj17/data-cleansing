-- Profiling queries: one row per check, returns (check, affected_rows)
SELECT 'vendors: null/empty tax_id' AS "check", count(*) AS n FROM vendors WHERE tax_id IS NULL OR trim(tax_id) = ''
UNION ALL SELECT 'vendors: malformed tax_id', count(*) FROM vendors WHERE trim(tax_id) <> '' AND NOT regexp_matches(tax_id, '^\d{2}-\d{7}$')
UNION ALL SELECT 'vendors: tax_id shared by >1 vendor', count(*) FROM vendors WHERE tax_id ~ '^\d{2}-\d{7}$' AND tax_id IN (SELECT tax_id FROM vendors GROUP BY 1 HAVING count(*) > 1)
UNION ALL SELECT 'vendors: non-ISO country', count(*) FROM vendors WHERE country NOT IN ('CA','US','MX')
UNION ALL SELECT 'vendors: invalid email', count(*) FROM vendors WHERE NOT regexp_matches(email, '^[^@\s]+@[^@\s]+\.[^@\s]+$')
UNION ALL SELECT 'vendors: non-standard payment_terms', count(*) FROM vendors WHERE payment_terms NOT IN ('NET30','NET45','NET60')
UNION ALL SELECT 'vendors: non-ISO created_date', count(*) FROM vendors WHERE NOT regexp_matches(created_date, '^\d{4}-\d{2}-\d{2}$')
UNION ALL SELECT 'purchase_orders: orphaned (no vendor)', count(*) FROM purchase_orders WHERE vendor_id NOT IN (SELECT vendor_id FROM vendors)
UNION ALL SELECT 'invoices: orphaned (no PO)', count(*) FROM invoices WHERE po_id NOT IN (SELECT po_id FROM purchase_orders);


-- ===== Extended profile (null rates, near-duplicates, orphans, inconsistencies) =====
-- Each statement is independent; run with: duckdb -readonly suppliers.duckdb < sql/profile.sql

-- 1. Null / blank rate per column: (table, column, rows, blank, blank_pct)
SELECT 'vendors' AS tbl, c AS col, count(*) AS n_rows,
       count(*) FILTER (WHERE v IS NULL OR trim(v) = '') AS n_blank,
       round(100.0 * count(*) FILTER (WHERE v IS NULL OR trim(v) = '') / count(*), 1) AS blank_pct
FROM vendors, LATERAL (VALUES
  ('vendor_name', vendor_name), ('tax_id', tax_id), ('country', country), ('email', email),
  ('payment_terms', payment_terms), ('status', status), ('created_date', created_date)) AS t(c, v)
GROUP BY c
UNION ALL SELECT 'purchase_orders', c, count(*), count(*) FILTER (WHERE v IS NULL), round(100.0 * count(*) FILTER (WHERE v IS NULL) / count(*), 1)
FROM purchase_orders, LATERAL (VALUES
  ('vendor_id', vendor_id::VARCHAR), ('po_date', po_date::VARCHAR), ('amount', amount::VARCHAR), ('currency', currency)) AS t(c, v)
GROUP BY c
UNION ALL SELECT 'invoices', c, count(*), count(*) FILTER (WHERE v IS NULL), round(100.0 * count(*) FILTER (WHERE v IS NULL) / count(*), 1)
FROM invoices, LATERAL (VALUES
  ('po_id', po_id::VARCHAR), ('invoice_date', invoice_date::VARCHAR), ('amount', amount::VARCHAR), ('paid', paid::VARCHAR)) AS t(c, v)
GROUP BY c
ORDER BY 1, 5 DESC, 2;

-- 2. Near-duplicate vendors: same name once case, punctuation and legal suffix are normalised
CREATE OR REPLACE TEMP VIEW vendor_norm AS
SELECT vendor_id, vendor_name, tax_id,
       trim(regexp_replace(regexp_replace(lower(vendor_name), '[.,]', '', 'g'),
                           '\s+(corporation|corp|incorporated|inc|company|co|limited|ltd|llc)$', '')) AS name_key
FROM vendors;

SELECT 'vendors: in a same-normalised-name group' AS "check", count(*) AS n
FROM vendor_norm WHERE name_key IN (SELECT name_key FROM vendor_norm GROUP BY 1 HAVING count(*) > 1)
UNION ALL SELECT 'vendors: distinct normalised-name groups with >1 record', count(*)
FROM (SELECT name_key FROM vendor_norm GROUP BY 1 HAVING count(*) > 1)
UNION ALL SELECT 'vendors: surplus records (would be removed on merge)', coalesce(sum(c - 1), 0)
FROM (SELECT count(*) AS c FROM vendor_norm GROUP BY name_key HAVING count(*) > 1)
UNION ALL SELECT 'vendors: valid tax_id shared by >1 record (groups)', count(*)
FROM (SELECT tax_id FROM vendors WHERE regexp_matches(tax_id, '^\d{2}-\d{7}$') GROUP BY 1 HAVING count(*) > 1)
UNION ALL SELECT 'vendors: name-pairs with jaro-winkler > 0.93 (typo candidates, review)', count(*)
FROM vendors a JOIN vendors b ON a.vendor_id < b.vendor_id
 AND jaro_winkler_similarity(lower(a.vendor_name), lower(b.vendor_name)) > 0.93;

-- 2b. The groups themselves (the merge worklist)
SELECT name_key, count(*) AS records, list(vendor_id ORDER BY vendor_id) AS vendor_ids,
       count(DISTINCT tax_id) AS distinct_tax_ids
FROM vendor_norm GROUP BY name_key HAVING count(*) > 1 ORDER BY records DESC, name_key;

-- 3. Orphans: counts, money at stake, and whether duplicates split the activity
SELECT 'purchase_orders: orphaned' AS "check", count(*) AS n, coalesce(sum(amount), 0) AS amount
FROM purchase_orders WHERE vendor_id NOT IN (SELECT vendor_id FROM vendors)
UNION ALL SELECT 'purchase_orders: distinct missing vendor_ids', count(DISTINCT vendor_id), NULL
FROM purchase_orders WHERE vendor_id NOT IN (SELECT vendor_id FROM vendors)
UNION ALL SELECT 'invoices: orphaned', count(*), coalesce(sum(amount), 0)
FROM invoices WHERE po_id NOT IN (SELECT po_id FROM purchase_orders)
UNION ALL SELECT 'invoices: distinct missing po_ids', count(DISTINCT po_id), NULL
FROM invoices WHERE po_id NOT IN (SELECT po_id FROM purchase_orders)
UNION ALL SELECT 'invoices: transitively orphaned (PO exists, its vendor does not)', count(*), coalesce(sum(i.amount), 0)
FROM invoices i JOIN purchase_orders p USING (po_id) WHERE p.vendor_id NOT IN (SELECT vendor_id FROM vendors)
UNION ALL SELECT 'vendors: no purchase orders', count(*), NULL
FROM vendors WHERE vendor_id NOT IN (SELECT vendor_id FROM purchase_orders)
UNION ALL SELECT 'purchase_orders: no invoices', count(*), NULL
FROM purchase_orders WHERE po_id NOT IN (SELECT po_id FROM invoices);

-- 4. Inconsistent representations: distinct spellings behind each value
SELECT 'country' AS col, count(DISTINCT country) AS distinct_spellings, 3 AS expected FROM vendors
UNION ALL SELECT 'payment_terms', count(DISTINCT payment_terms), 3 FROM vendors
UNION ALL SELECT 'status', count(DISTINCT status), 2 FROM vendors
UNION ALL SELECT 'currency', count(DISTINCT currency), 3 FROM purchase_orders;

-- 4b. Other rule violations
SELECT 'vendors: created_date not ISO (yyyy-mm-dd)' AS "check", count(*) AS n FROM vendors WHERE NOT regexp_matches(created_date, '^\d{4}-\d{2}-\d{2}$')
UNION ALL SELECT 'vendors: name not in Title Case (ALL CAPS)', count(*) FROM vendors WHERE vendor_name = upper(vendor_name)
UNION ALL SELECT 'vendors: name has leading/trailing space', count(*) FROM vendors WHERE vendor_name <> trim(vendor_name)
UNION ALL SELECT 'vendors: email domain does not match vendor name', count(*) FROM vendors
 WHERE regexp_matches(email, '^[^@\s]+@[^@\s]+\.[^@\s]+$')
   AND split_part(split_part(email, '@', 2), '.', 1) <> regexp_replace(lower(split_part(vendor_name, ' ', 1) || coalesce(split_part(vendor_name, ' ', 2), '')), '[^a-z]', '', 'g')
UNION ALL SELECT 'purchase_orders: amount <= 0', count(*) FROM purchase_orders WHERE amount <= 0
UNION ALL SELECT 'invoices: amount <= 0', count(*) FROM invoices WHERE amount <= 0
UNION ALL SELECT 'invoices: dated before their PO', count(*) FROM invoices i JOIN purchase_orders p USING (po_id) WHERE i.invoice_date < p.po_date
UNION ALL SELECT 'invoices: amount exceeds PO amount', count(*) FROM invoices i JOIN purchase_orders p USING (po_id) WHERE i.amount > p.amount
UNION ALL SELECT 'invoices: duplicate (same po_id, date, amount)', coalesce(sum(c - 1), 0)
FROM (SELECT count(*) AS c FROM invoices GROUP BY po_id, invoice_date, amount HAVING count(*) > 1)
UNION ALL SELECT 'purchase_orders: dated before vendor created_date', count(*) FROM purchase_orders p JOIN vendors v USING (vendor_id)
 WHERE regexp_matches(v.created_date, '^\d{4}-\d{2}-\d{2}$') AND p.po_date < v.created_date::DATE
UNION ALL SELECT 'purchase_orders: for an inactive vendor', count(*) FROM purchase_orders p JOIN vendors v USING (vendor_id) WHERE v.status = 'inactive'
UNION ALL SELECT 'any date in the future', (SELECT count(*) FROM purchase_orders WHERE po_date > current_date) + (SELECT count(*) FROM invoices WHERE invoice_date > current_date);
