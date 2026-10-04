-- Revenue per state (CA 4 stores, TX 3, WI 3) and per store.
SELECT state_id, count(DISTINCT store_id) AS stores, sum(rev_c) / 100.0 AS revenue, sum(rev_c) / sum(sum(rev_c)) OVER () AS revenue_share,
       sum(rev_c) / 100.0 / count(DISTINCT store_id) AS revenue_per_store, sum(units) AS units
FROM daily GROUP BY state_id ORDER BY revenue DESC;
