-- Category share of revenue in each complete calendar year (2012-2015) and over the whole period.
WITH y AS (SELECT c.year::VARCHAR AS period, d.cat_id, sum(d.rev_c) / 100.0 AS revenue FROM daily d JOIN days c USING (d) WHERE c.year BETWEEN 2012 AND 2015 GROUP BY ALL
           UNION ALL SELECT 'all', cat_id, sum(rev_c) / 100.0 FROM daily GROUP BY cat_id)
SELECT period, cat_id, revenue, revenue / sum(revenue) OVER (PARTITION BY period) AS share FROM y ORDER BY period, cat_id;
