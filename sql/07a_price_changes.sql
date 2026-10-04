-- Price changes: for each item x store, compare the price of a week with the price of the week before (both weeks priced, complete 7-day weeks only, weeks 1-277).
-- Prices exist only from the week an item is first sold, so a series' first priced week has no earlier price to compare with.
CREATE OR REPLACE TEMP TABLE wk AS
SELECT f.sid, f.week_no, any_value(f.price_c) AS price_c, sum(f.units) AS units
FROM fact f WHERE f.price_c IS NOT NULL AND f.week_no <= 277 GROUP BY f.sid, f.week_no;

CREATE OR REPLACE TEMP TABLE pairs AS
SELECT sid, week_no, price_c, units, lag(price_c) OVER w AS prev_price, lag(units) OVER w AS prev_units, lag(week_no) OVER w AS prev_week
FROM wk WINDOW w AS (PARTITION BY sid ORDER BY week_no);

SELECT coalesce(s.cat_id, 'ALL') AS cat_id, count(*) AS week_pairs, avg((p.price_c <> p.prev_price)::INT) AS share_changed,
       avg((p.price_c < p.prev_price)::INT) AS share_cut, avg((p.price_c > p.prev_price)::INT) AS share_rise,
       avg(abs(p.price_c / p.prev_price - 1)) FILTER (WHERE p.price_c <> p.prev_price) AS mean_abs_change_when_changed
FROM pairs p JOIN series s USING (sid)
WHERE p.prev_week = p.week_no - 1
GROUP BY GROUPING SETS ((s.cat_id), ())
ORDER BY cat_id;
