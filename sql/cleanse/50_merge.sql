-- Merge Duplicate Vendors: same normalised name (case, punctuation and legal suffix ignored) AND the same valid Tax ID.
CREATE OR REPLACE TEMP TABLE merge_groups AS
SELECT vendor_id,
       first_value(vendor_id) OVER (PARTITION BY name_key, tax_id ORDER BY po_count DESC, created ASC NULLS LAST, vendor_id ASC) AS surviving_vendor_id,
       count(*) OVER (PARTITION BY name_key, tax_id) AS group_size
FROM (
  -- shortcut: only ISO creation dates are compared, other formats sort last, until ticket 03 standardises dates
  SELECT v.vendor_id, v.tax_id,
         CASE WHEN regexp_matches(v.created_date, '^\d{4}-\d{2}-\d{2}$') THEN v.created_date::DATE END AS created,
         trim(regexp_replace(regexp_replace(lower(v.vendor_name), '[.,]', '', 'g'),
                             '\s+(corporation|corp|incorporated|inc|company|co|limited|ltd|llc)$', '')) AS name_key,
         (SELECT count(*) FROM purchase_orders p WHERE p.vendor_id = v.vendor_id) AS po_count
  FROM clean_vendors v
  WHERE regexp_matches(v.tax_id, '^\d{2}-\d{7}$')
);

UPDATE vendor_map SET surviving_vendor_id = g.surviving_vendor_id
FROM merge_groups g
WHERE g.group_size > 1 AND g.vendor_id = vendor_map.old_vendor_id;

UPDATE clean_purchase_orders SET vendor_id = m.surviving_vendor_id
FROM vendor_map m
WHERE m.old_vendor_id = clean_purchase_orders.vendor_id;

DELETE FROM clean_vendors WHERE vendor_id IN (SELECT old_vendor_id FROM vendor_map WHERE old_vendor_id <> surviving_vendor_id);

-- The merged vendor is active if any record in its group was, and takes the earliest creation date in the group.
-- shortcut: only ISO creation dates count, until ticket 03 standardises dates
UPDATE clean_vendors SET
  status = CASE WHEN EXISTS (SELECT 1 FROM vendors r JOIN vendor_map m ON m.old_vendor_id = r.vendor_id
                             WHERE m.surviving_vendor_id = clean_vendors.vendor_id AND r.status = 'active')
                THEN 'active' ELSE status END,
  created_date = coalesce((SELECT min(r.created_date) FROM vendors r JOIN vendor_map m ON m.old_vendor_id = r.vendor_id
                           WHERE m.surviving_vendor_id = clean_vendors.vendor_id
                             AND regexp_matches(r.created_date, '^\d{4}-\d{2}-\d{2}$')), created_date);
