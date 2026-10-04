-- Event days vs ordinary days. Index of an event day = chain revenue that day / the average revenue of ordinary days (no event) with the same weekday in the same year.
-- Event days are the days with event_name_1 (4 days also carry a second event; they count once, under their first event).
WITH t AS (SELECT d, sum(rev_c) / 100.0 AS rev FROM daily GROUP BY d),
j AS (SELECT c.d, c.year, c.wday, c.event_name_1, c.event_type_1, t.rev FROM t JOIN days c USING (d)),
base AS (SELECT year, wday, avg(rev) AS base_rev FROM j WHERE event_name_1 IS NULL GROUP BY ALL),
e AS (SELECT j.*, j.rev / b.base_rev AS idx FROM j JOIN base b USING (year, wday) WHERE j.event_name_1 IS NOT NULL)
SELECT event_type_1 AS event_type, count(*) AS event_days, avg(idx) AS mean_index, median(idx) AS median_index,
       avg(idx) FILTER (WHERE event_name_1 <> 'Christmas') AS mean_index_without_christmas
FROM e GROUP BY event_type_1 ORDER BY mean_index DESC;
