-- Revenue per store: share, per-day average, average price per unit and the FOODS share of the store's revenue.
SELECT store_id, state_id, sum(rev_c) / 100.0 AS revenue, sum(rev_c) / sum(sum(rev_c)) OVER () AS revenue_share, sum(units) AS units,
       sum(rev_c) / 100.0 / (SELECT count(*) FROM days) AS revenue_per_day, sum(rev_c) / 100.0 / sum(units) AS revenue_per_unit,
       sum(CASE WHEN cat_id = 'FOODS' THEN rev_c END) / sum(rev_c) AS foods_share,
       rank() OVER (ORDER BY sum(rev_c) DESC) AS rank_revenue
FROM daily GROUP BY store_id, state_id ORDER BY revenue DESC;
