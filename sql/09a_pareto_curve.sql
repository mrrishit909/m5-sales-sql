-- Concentration of revenue over the 3,049 items (summed over stores): cumulative share of revenue held by the top p% of items, p = 0..100.
-- Items are ranked by revenue, ties by item_id; the top p% is the first ceil(p/100 x 3049) items.
WITH r AS (SELECT item_id, rev_c, row_number() OVER (ORDER BY rev_c DESC, item_id) AS rk, count(*) OVER () AS n, sum(rev_c) OVER () AS tot FROM item_rev),
c AS (SELECT rk, n, tot, sum(rev_c) OVER (ORDER BY rk) AS cum FROM r),
p AS (SELECT unnest(range(0, 101)) AS pct)
SELECT p.pct AS top_pct_of_items, ceil(p.pct / 100.0 * (SELECT any_value(n) FROM c))::INT AS items,
       coalesce((SELECT cum FROM c WHERE rk = ceil(p.pct / 100.0 * c.n)), 0) / (SELECT any_value(tot) FROM c) AS cumulative_revenue_share
FROM p, (SELECT any_value(n) AS n FROM c) c ORDER BY p.pct;
