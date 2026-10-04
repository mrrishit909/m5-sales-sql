-- The same at series level: each item x store has its own zero share over its priced days. How many series are mostly zeros?
WITH z AS (
  SELECT s.cat_id, f.sid, sum((f.price_c IS NOT NULL)::INT) AS priced_days, sum((f.price_c IS NOT NULL AND f.units = 0)::INT) AS zero_days
  FROM fact f JOIN series s USING (sid) GROUP BY ALL HAVING sum((f.price_c IS NOT NULL)::INT) > 0)
SELECT coalesce(cat_id, 'ALL') AS cat_id, count(*) AS series, median(zero_days::DOUBLE / priced_days) AS median_zero_share,
       avg((zero_days::DOUBLE / priced_days >= 0.5)::INT) AS share_series_half_zero_or_more,
       avg((zero_days::DOUBLE / priced_days >= 0.8)::INT) AS share_series_80pct_zero_or_more,
       avg((zero_days::DOUBLE / priced_days < 0.1)::INT) AS share_series_under_10pct_zero
FROM z GROUP BY GROUPING SETS ((cat_id), ()) ORDER BY cat_id;
