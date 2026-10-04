-- Association between a price change and the change in weekly units (not an elasticity: shops cut prices on purpose, weak weeks invite cuts, and units drift back to their mean).
-- Class of the week-on-week price change; ratio = units this week / units the week before, summed over all pairs in the class.
SELECT CASE WHEN p.price_c <= p.prev_price * 0.9 THEN '1 cut 10% or more'
            WHEN p.price_c < p.prev_price THEN '2 cut under 10%'
            WHEN p.price_c = p.prev_price THEN '3 unchanged'
            WHEN p.price_c < p.prev_price * 1.1 THEN '4 rise under 10%'
            ELSE '5 rise 10% or more' END AS price_change, count(*) AS week_pairs,
       sum(p.units)::DOUBLE / sum(p.prev_units) AS units_ratio_vs_prev_week,
       avg((p.units > p.prev_units)::INT) AS share_units_up
FROM pairs p
WHERE p.prev_week = p.week_no - 1
GROUP BY ALL ORDER BY 1;
