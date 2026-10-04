-- Setup (not exported). Three steps:
-- 1. series: one row per item x store (30,490), with an integer key.
-- 2. cal: the calendar, one row per day; d = the day number (d_1 = Sat 2011-01-29); week_no = the order of Walmart's weeks (wm_yr_wk is not consecutive across years).
-- 3. fact: UNPIVOT the 1,941 wide day columns into one row per series and day (59.2 million rows) and join the weekly price.
--    Money is kept in integer cents (units x cents), so every revenue sum is exact. price_c is NULL when the file has no price for that item, store and week:
--    M5 only lists a price from the week an item is first sold, so a missing price means "not yet on sale" (see 10_data_quality).
CREATE TABLE series AS
SELECT row_number() OVER (ORDER BY id)::INTEGER AS sid, id, item_id, dept_id, cat_id, store_id, state_id FROM wide;

CREATE TABLE cal AS
SELECT substr(d, 3)::SMALLINT AS d, date, wm_yr_wk, dense_rank() OVER (ORDER BY wm_yr_wk)::SMALLINT AS week_no, weekday, wday, month, year,
       event_name_1, event_type_1, event_name_2, event_type_2, snap_CA, snap_TX, snap_WI
FROM cal_raw;

CREATE TABLE prices AS
SELECT s.sid, p.wm_yr_wk, (p.sell_price * 100)::INTEGER AS price_c
FROM prices_raw p JOIN series s ON s.item_id = p.item_id AND s.store_id = p.store_id;

CREATE TABLE long_sales AS
SELECT sid, substr(d, 3)::SMALLINT AS d, units::SMALLINT AS units
FROM (SELECT s.sid, w.* EXCLUDE (id, item_id, dept_id, cat_id, store_id, state_id) FROM wide w JOIN series s ON s.id = w.id)
UNPIVOT (units FOR d IN (COLUMNS('d_\d+')));

CREATE TABLE fact AS
SELECT l.sid, l.d, c.wm_yr_wk, c.week_no, l.units, p.price_c, l.units::BIGINT * p.price_c AS rev_c
FROM long_sales l JOIN cal c ON c.d = l.d LEFT JOIN prices p ON p.sid = l.sid AND p.wm_yr_wk = c.wm_yr_wk;

DROP TABLE long_sales;
DROP TABLE wide;

-- days: the 1,941 days that have sales (the calendar file runs 28 days longer, to the end of the forecast horizon).
-- daily: sales per day, department and store (136,000 rows): every question about time, place or department reads this small table.
CREATE TABLE days AS SELECT * FROM cal WHERE d <= 1941;

CREATE TABLE daily AS
SELECT f.d, s.dept_id, s.cat_id, s.store_id, s.state_id, sum(f.units) AS units, sum(f.rev_c) AS rev_c
FROM fact f JOIN series s USING (sid)
GROUP BY ALL;

-- item_rev: revenue and units per item (summed over its 10 stores); series_stats: per item x store.
CREATE TABLE item_rev AS
SELECT s.item_id, s.dept_id, s.cat_id, sum(f.units) AS units, sum(f.rev_c) AS rev_c
FROM fact f JOIN series s USING (sid)
GROUP BY ALL;
