-- Pareto numbers (metric, value): top shares of items, items needed for half and 80% of revenue, and the same for the 30,490 item x store series.
-- The unit ranking is not the revenue ranking: overlap_top10_units_vs_revenue = how many of the top 10% of items by units are also in the top 10% by revenue.
WITH r AS (SELECT item_id, rev_c, units, row_number() OVER (ORDER BY rev_c DESC, item_id) AS rk, row_number() OVER (ORDER BY units DESC, item_id) AS rku, count(*) OVER () AS n, sum(rev_c) OVER () AS tot FROM item_rev),
c AS (SELECT *, sum(rev_c) OVER (ORDER BY rk) AS cum FROM r),
top AS (SELECT any_value(n) AS n, any_value(tot) AS tot FROM c),
s AS (SELECT sid, sum(rev_c) AS rev_c FROM fact GROUP BY sid),
sr AS (SELECT rev_c, row_number() OVER (ORDER BY rev_c DESC, sid) AS rk, count(*) OVER () AS n, sum(rev_c) OVER () AS tot FROM s),
cat AS (SELECT cat_id, item_id, rev_c, row_number() OVER (PARTITION BY cat_id ORDER BY rev_c DESC, item_id) AS rk, count(*) OVER (PARTITION BY cat_id) AS n, sum(rev_c) OVER (PARTITION BY cat_id) AS tot FROM item_rev)
SELECT 'items' AS metric, n::DOUBLE AS value FROM top
UNION ALL SELECT 'items_without_any_revenue', count(*) FROM item_rev WHERE rev_c = 0
UNION ALL SELECT 'top_1pct_items_share', sum(rev_c) FILTER (WHERE rk <= ceil(0.01 * n)) / any_value(tot) FROM c
UNION ALL SELECT 'top_10pct_items_share', sum(rev_c) FILTER (WHERE rk <= ceil(0.10 * n)) / any_value(tot) FROM c
UNION ALL SELECT 'top_20pct_items_share', sum(rev_c) FILTER (WHERE rk <= ceil(0.20 * n)) / any_value(tot) FROM c
UNION ALL SELECT 'bottom_50pct_items_share', sum(rev_c) FILTER (WHERE rk > floor(0.50 * n)) / any_value(tot) FROM c
UNION ALL SELECT 'items_for_50pct_revenue', min(rk) FILTER (WHERE cum >= 0.5 * tot) FROM c
UNION ALL SELECT 'items_for_80pct_revenue', min(rk) FILTER (WHERE cum >= 0.8 * tot) FROM c
UNION ALL SELECT 'series_top_10pct_share', sum(rev_c) FILTER (WHERE rk <= ceil(0.10 * n)) / any_value(tot) FROM sr
UNION ALL SELECT 'overlap_top10_units_vs_revenue', count(*) FILTER (WHERE rk <= ceil(0.10 * n) AND rku <= ceil(0.10 * n)) / ceil(0.10 * any_value(n)) FROM c
UNION ALL SELECT 'top_10pct_share_' || cat_id, sum(rev_c) FILTER (WHERE rk <= ceil(0.10 * n)) / any_value(tot) FROM cat GROUP BY cat_id
UNION ALL SELECT 'top_item_share', max(rev_c) / any_value(tot) FROM c;
