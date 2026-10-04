-- Average chain-wide revenue and units per day, by weekday (all 1,941 days; Christmas Day counts as a near-zero Thursday/Friday/...). Index: 1.00 = the average day.
WITH t AS (SELECT d, sum(rev_c) AS rev_c, sum(units) AS units FROM daily GROUP BY d),
w AS (SELECT c.weekday, c.wday, count(*) AS days, avg(t.rev_c) / 100.0 AS avg_revenue, avg(t.units) AS avg_units FROM t JOIN days c USING (d) GROUP BY c.weekday, c.wday)
SELECT weekday, days, avg_revenue, avg_units, avg_revenue / (SELECT sum(avg_revenue) / 7 FROM w) AS revenue_index
FROM w ORDER BY wday;
