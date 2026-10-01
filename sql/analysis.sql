-- 03-supplychain-retail — order pipeline & concentration in SQL.
-- Loads: data/processed/transactions.csv -> `tx` (invoice, stockcode, quantity, price, country, invoicedate).

-- Order-level rollup & revenue
CREATE OR REPLACE TEMP TABLE orders AS
SELECT invoice,
       MIN(invoicedate) AS date,
       SUM(CASE WHEN quantity < 0 THEN NULL ELSE quantity * price END) AS revenue
FROM tx GROUP BY invoice;

-- KPIs: AOV, returns share, concentration by SKU top-20
SELECT
  (SELECT ROUND(AVG(revenue), 2) FROM orders WHERE revenue > 0) AS aov,
  (SELECT ROUND(SUM(CASE WHEN quantity < 0 THEN quantity * price END)
        / SUM(ABS(quantity * price)) * 100, 1)
   FROM tx) AS returns_value_share_pct;

-- Top-20 SKU revenue share (concentration risk)
WITH sku AS (
  SELECT stockcode, SUM(quantity * price) AS rev FROM tx
  WHERE quantity > 0 GROUP BY stockcode ORDER BY rev DESC
),
total AS (SELECT SUM(quantity * price) AS t FROM tx WHERE quantity > 0)
SELECT ROUND(100.0 * (SELECT SUM(rev) FROM (SELECT rev FROM sku LIMIT 20)) / (SELECT t FROM total), 1)
       AS top20_share_pct;

-- Revenue by country (market concentration)
SELECT country, ROUND(SUM(quantity * price), 0) AS revenue
FROM tx WHERE quantity > 0 GROUP BY country ORDER BY revenue DESC;
