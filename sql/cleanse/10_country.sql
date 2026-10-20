-- Country -> ISO two-letter code. Spelling is compared without case, accents, dots or surrounding spaces.
CREATE OR REPLACE TEMP TABLE country_lookup AS
SELECT * FROM (VALUES
  ('us', 'US'), ('usa', 'US'), ('united states', 'US'), ('united states of america', 'US'),
  ('ca', 'CA'), ('can', 'CA'), ('canada', 'CA'),
  ('mx', 'MX'), ('mex', 'MX'), ('mexico', 'MX')
) AS t(spelling, code);

UPDATE clean_vendors SET country = l.code
FROM country_lookup l
WHERE l.spelling = lower(trim(replace(strip_accents(clean_vendors.country), '.', '')));

-- Anything still not a valid code is unrecognisable: list it for review, blank it, and keep the vendor.
INSERT INTO review_items
SELECT 'vendors', vendor_id, 'country', country, 'unrecognised country' FROM clean_vendors
WHERE country IS NOT NULL AND country NOT IN ('US', 'CA', 'MX');

UPDATE clean_vendors SET country = NULL WHERE country IS NOT NULL AND country NOT IN ('US', 'CA', 'MX');
