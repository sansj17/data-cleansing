-- Start every run from the raw tables; the raw tables themselves are never written.
-- vendor_map lists every raw vendor: an unmerged vendor maps to itself, a merged-away one to its Surviving Vendor.
DROP TABLE IF EXISTS clean_vendors;
DROP TABLE IF EXISTS clean_purchase_orders;
DROP TABLE IF EXISTS clean_invoices;
DROP TABLE IF EXISTS quarantine_purchase_orders;
DROP TABLE IF EXISTS quarantine_invoices;
DROP TABLE IF EXISTS vendor_map;
DROP TABLE IF EXISTS review_items;

CREATE TABLE clean_vendors AS SELECT * FROM vendors;
CREATE TABLE clean_purchase_orders AS SELECT * FROM purchase_orders;
CREATE TABLE clean_invoices AS SELECT * FROM invoices;
CREATE TABLE quarantine_purchase_orders AS SELECT *, ''::VARCHAR AS reason FROM purchase_orders WHERE false;
CREATE TABLE quarantine_invoices AS SELECT *, ''::VARCHAR AS reason FROM invoices WHERE false;
CREATE TABLE vendor_map AS SELECT vendor_id AS old_vendor_id, vendor_id AS surviving_vendor_id FROM vendors;
CREATE TABLE review_items (table_name VARCHAR, record_id INTEGER, field VARCHAR, raw_value VARCHAR, reason VARCHAR);
