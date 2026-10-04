-- Revenue per calendar year. 2011 (from 29 Jan) and 2016 (to 22 May) are partial, so growth is shown per day and only between complete years.
WITH y AS (
  SELECT c.year, count(DISTINCT c.d) AS days, sum(d.rev_c) / 100.0 AS revenue, sum(d.units) AS units
  FROM daily d JOIN days c USING (d) GROUP BY c.year)
SELECT year, days, revenue, units, revenue / days AS revenue_per_day, revenue / units AS revenue_per_unit,
       CASE WHEN days >= 365 AND lag(days) OVER (ORDER BY year) >= 365 THEN revenue / days / (lag(revenue) OVER (ORDER BY year) / lag(days) OVER (ORDER BY year)) - 1 END AS growth_per_day_vs_prev_year,
       CASE WHEN days >= 365 AND lag(days) OVER (ORDER BY year) >= 365 THEN units / days / (lag(units) OVER (ORDER BY year) / lag(days) OVER (ORDER BY year)) - 1 END AS unit_growth_per_day_vs_prev_year
FROM y ORDER BY year;
