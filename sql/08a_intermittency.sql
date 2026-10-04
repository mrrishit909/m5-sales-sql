-- Intermittent demand: the share of item x store x day cells with zero sales. Three kinds of cell: no price yet (not on sale), priced but sold nothing, sold something.
-- "Zero share" over all cells overstates the intermittency because it counts days before an item existed; the honest figure counts only priced days.
SELECT coalesce(s.cat_id, 'ALL') AS cat_id, count(*) AS cells,
       avg((f.price_c IS NULL)::INT) AS share_unpriced, avg((f.price_c IS NOT NULL AND f.units = 0)::INT) AS share_priced_zero, avg((f.units > 0)::INT) AS share_sold,
       avg((f.units = 0)::INT) AS zero_share_all_cells,
       sum((f.price_c IS NOT NULL AND f.units = 0)::INT)::DOUBLE / sum((f.price_c IS NOT NULL)::INT) AS zero_share_priced_cells
FROM fact f JOIN series s USING (sid)
GROUP BY GROUPING SETS ((s.cat_id), ())
ORDER BY cat_id;
