-- The same index for each named event (mean over its yearly occurrences in the sales period).
WITH t AS (SELECT d, sum(rev_c) / 100.0 AS rev FROM daily GROUP BY d),
j AS (SELECT c.d, c.year, c.wday, c.event_name_1, c.event_type_1, t.rev FROM t JOIN days c USING (d)),
base AS (SELECT year, wday, avg(rev) AS base_rev FROM j WHERE event_name_1 IS NULL GROUP BY ALL)
SELECT j.event_name_1 AS event_name, any_value(j.event_type_1) AS event_type, count(*) AS occurrences, avg(j.rev / b.base_rev) AS mean_index
FROM j JOIN base b USING (year, wday) WHERE j.event_name_1 IS NOT NULL
GROUP BY j.event_name_1 ORDER BY mean_index DESC, event_name;
