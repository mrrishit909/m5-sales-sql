-- The SNAP-day effect (SNAP = US food-stamp benefits, paid on set days of the month, which differ by state: the calendar has one 0/1 flag per state).
-- Per state and category: average daily revenue of that state's stores on its SNAP days vs its other days (raw_ratio), and the same ratio taken weekday by weekday
-- and averaged over the 7 weekdays (matched_ratio) so a different mix of Saturdays cannot drive it. Association only: SNAP days sit early in the month, the same days as many paydays.
WITH t AS (
  SELECT d.state_id, d.cat_id, d.d, sum(d.rev_c) / 100.0 AS rev, sum(d.units) AS units FROM daily d GROUP BY ALL),
j AS (
  SELECT t.state_id, t.cat_id, c.wday, CASE t.state_id WHEN 'CA' THEN c.snap_CA WHEN 'TX' THEN c.snap_TX ELSE c.snap_WI END AS snap, t.rev, t.units
  FROM t JOIN days c USING (d)),
a AS (SELECT state_id, cat_id, snap, count(*) AS days, avg(rev) AS avg_rev, avg(units) AS avg_units FROM j GROUP BY ALL),
w AS (SELECT state_id, cat_id, wday, avg(rev) FILTER (WHERE snap = 1) / avg(rev) FILTER (WHERE snap = 0) AS r, avg(units) FILTER (WHERE snap = 1) / avg(units) FILTER (WHERE snap = 0) AS ru
      FROM j GROUP BY ALL),
m AS (SELECT state_id, cat_id, avg(r) AS matched_ratio, avg(ru) AS matched_units_ratio FROM w GROUP BY ALL)
SELECT s1.state_id, s1.cat_id, s1.days AS snap_days, s0.days AS other_days, s1.avg_rev AS snap_avg_revenue, s0.avg_rev AS other_avg_revenue,
       s1.avg_rev / s0.avg_rev AS raw_ratio, m.matched_ratio, m.matched_units_ratio
FROM a s1 JOIN a s0 ON s1.state_id = s0.state_id AND s1.cat_id = s0.cat_id AND s1.snap = 1 AND s0.snap = 0
JOIN m ON m.state_id = s1.state_id AND m.cat_id = s1.cat_id
ORDER BY s1.state_id, s1.cat_id;
