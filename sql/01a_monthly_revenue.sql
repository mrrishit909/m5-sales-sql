-- Revenue (units x that week's price) per calendar month and category. Jan 2011 starts on the 29th and May 2016 stops on the 22nd, so "full" marks the 64 complete months.
SELECT strftime(date_trunc('month', c.date), '%Y-%m') AS month, d.cat_id, count(DISTINCT c.d) AS days,
       count(DISTINCT c.d) = date_diff('day', date_trunc('month', min(c.date)), date_trunc('month', min(c.date)) + INTERVAL 1 MONTH) AS full_month,
       sum(d.rev_c) / 100.0 AS revenue, sum(d.units) AS units
FROM daily d JOIN days c USING (d)
GROUP BY ALL
ORDER BY month, cat_id;
