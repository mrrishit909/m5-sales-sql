-- Revenue and units by department. Rank by units and rank by revenue differ: the data is units sold, not dollars; dollars need the price.
WITH x AS (
  SELECT d.dept_id, d.cat_id, sum(d.units) AS units, sum(d.rev_c) / 100.0 AS revenue FROM daily d GROUP BY ALL),
n AS (SELECT dept_id, count(DISTINCT item_id) AS items FROM series GROUP BY dept_id)
SELECT x.dept_id, x.cat_id, n.items, x.units, x.revenue, x.revenue / sum(x.revenue) OVER () AS revenue_share, x.units / sum(x.units) OVER () AS unit_share,
       x.revenue / x.units AS revenue_per_unit,
       rank() OVER (ORDER BY x.revenue DESC) AS rank_revenue, rank() OVER (ORDER BY x.units DESC) AS rank_units
FROM x JOIN n USING (dept_id)
ORDER BY x.revenue DESC;
