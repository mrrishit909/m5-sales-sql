-- Data-quality counts (metric, value): what the files contain and the traps a first pass walks into.
WITH sp AS (
  SELECT sid, sum(units) AS units, min(week_no) FILTER (WHERE price_c IS NOT NULL) AS first_priced_week, max(week_no) FILTER (WHERE price_c IS NOT NULL) AS last_priced_week,
         count(DISTINCT week_no) FILTER (WHERE price_c IS NOT NULL) AS priced_weeks,
         min(week_no) FILTER (WHERE units > 0) AS first_sale_week
  FROM fact GROUP BY sid)
SELECT 'series_item_store' AS metric, count(*)::DOUBLE AS value FROM sp
UNION ALL SELECT 'cells_item_store_day', count(*) FROM fact
UNION ALL SELECT 'days_with_sales', count(*) FROM days
UNION ALL SELECT 'cells_with_units_but_no_price', count(*) FROM fact WHERE units > 0 AND price_c IS NULL
UNION ALL SELECT 'cells_unpriced_share', avg((price_c IS NULL)::INT) FROM fact
UNION ALL SELECT 'series_never_sold', count(*) FROM sp WHERE units = 0
UNION ALL SELECT 'series_never_priced', count(*) FROM sp WHERE first_priced_week IS NULL
UNION ALL SELECT 'series_priced_from_week_1', count(*) FROM sp WHERE first_priced_week = 1
UNION ALL SELECT 'series_priced_after_week_1', count(*) FROM sp WHERE first_priced_week > 1
UNION ALL SELECT 'series_first_priced_week_is_first_sale_week', count(*) FROM sp WHERE first_priced_week = first_sale_week
UNION ALL SELECT 'series_first_sale_before_first_priced_week', count(*) FROM sp WHERE first_sale_week < first_priced_week
UNION ALL SELECT 'series_with_price_gap_after_launch', count(*) FROM sp WHERE priced_weeks < last_priced_week - first_priced_week + 1
UNION ALL SELECT 'series_priced_to_last_week', count(*) FROM sp WHERE last_priced_week = 278
UNION ALL SELECT 'price_rows_in_file', count(*) FROM prices_raw
UNION ALL SELECT 'price_rows_duplicate_keys', count(*) - (SELECT count(*) FROM (SELECT DISTINCT store_id, item_id, wm_yr_wk FROM prices_raw)) FROM prices_raw
UNION ALL SELECT 'price_rows_after_sales_end', count(*) FROM prices_raw p WHERE p.wm_yr_wk > (SELECT max(wm_yr_wk) FROM days)
UNION ALL SELECT 'calendar_days_after_sales_end', count(*) FROM cal WHERE d > 1941
UNION ALL SELECT 'last_week_days', count(*) FROM days WHERE week_no = 278
UNION ALL SELECT 'chain_days_with_zero_units', count(*) FROM (SELECT d FROM daily GROUP BY d HAVING sum(units) = 0)
UNION ALL SELECT 'store_days_with_zero_units', count(*) FROM (SELECT d, store_id FROM daily GROUP BY d, store_id HAVING sum(units) = 0)
UNION ALL SELECT 'store_days_zero_units_on_dec25', count(*) FROM (SELECT d, store_id FROM daily GROUP BY d, store_id HAVING sum(units) = 0) z JOIN days c USING (d) WHERE month(c.date) = 12 AND day(c.date) = 25
UNION ALL SELECT 'store_days_on_dec25', count(*) FROM (SELECT DISTINCT d, store_id FROM daily) z JOIN days c USING (d) WHERE month(c.date) = 12 AND day(c.date) = 25
UNION ALL SELECT 'event_days', count(*) FROM days WHERE event_name_1 IS NOT NULL
UNION ALL SELECT 'total_units', sum(units) FROM daily
UNION ALL SELECT 'total_revenue', sum(rev_c) / 100.0 FROM daily
UNION ALL SELECT 'revenue_per_unit', sum(rev_c) / 100.0 / sum(units) FROM daily;
