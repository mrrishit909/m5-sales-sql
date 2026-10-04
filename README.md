# Where does a Walmart's revenue actually come from?

The M5 Forecasting data, a Walmart sales database of 3,049 items in 10 stores in California, Texas and Wisconsin from January 2011 to May 2016, analysed
entirely in SQL (DuckDB). Six questions:
- how much was sold, and how did revenue (units x the weekly price) move by month, year, weekday, category, department and store;
- how much do SNAP (food-benefit) days lift sales, state by state, and do events and holidays matter;
- how often does a price change, and what happens to units when it does;
- how many item-days sell nothing (intermittent demand), counting only the days an item was actually on sale;
- how concentrated revenue is: what the top 10% of items earn;
- what the files get wrong or leave out: sales are units not dollars, and a price exists only from the week an item first sells.

The questions follow DataCamp's "Analyzing Motorcycle Part Sales" project (SQL on a multi-warehouse sales database: revenue by time, product line and location). The course
database is a course file, so this one runs on the M5 competition's real Walmart data.

Build log: https://mrrishit909.github.io/projects/m5-sales-sql/

## Data

M5 Forecasting - Accuracy dataset, from the Makridakis Open Forecasting Center (University of Nicosia) and Walmart, as released on Zenodo (record 12636070,
https://zenodo.org/records/12636070, DOI 10.5281/zenodo.12636070), licence CC BY 4.0 (checked on the record). Cite: Makridakis, Spiliotis and Assimakopoulos (2022), "The M5
competition: Background, organization, and implementation", International Journal of Forecasting 38(4). Files used: `sales_train_evaluation.csv` (units sold, 30,490 item x store
series, days d_1 to d_1941: 29 Jan 2011 to 22 May 2016), `calendar.csv` (dates, events, SNAP flags per state) and `sell_prices.csv` (6,841,121 weekly prices). The zip is
48 MB (450 MB unzipped); `download.py` fetches it and checks its md5 (details in `results/pull.json`); it is not committed. Item names are hashed (HOBBIES_1_001), so items cannot be named.

```
./venv/bin/pip install duckdb pandas matplotlib certifi      # in a venv
./venv/bin/python download.py    # data/*
./venv/bin/python run_sql.py     # results/*.csv from sql/*.sql  (about a minute, under 3 GB)
./venv/bin/python check.py       # about 30 seconds
./venv/bin/python charts.py
```

## Steps

1. **Download** the zip from Zenodo and verify its checksum.
2. **Set up** (`sql/00_setup.sql`): `UNPIVOT` the 1,941 day columns into one row per item x store x day (59,181,090 rows), join the calendar and the weekly price, and keep money in integer
   cents (units x price in cents), so every revenue total is exact. Two small summary tables (`daily`, by day x department x store, and `item_rev`) feed most questions.
3. **Queries** (`sql/`, one file per question, using CTEs, window functions, `FILTER`, `GROUPING SETS`, `LAG`, `RANK` and `MEDIAN`):
   - `01a`, `01b`: revenue by month and category, and by year; `02`: by weekday;
   - `03a`, `03b`: departments (revenue against units) and category shares by year; `04a`, `04b`: stores and states;
   - `05_snap`: sales on SNAP days against other days, raw and weekday by weekday, for each state and category (the non-food categories are the placebo);
   - `06a`, `06b`: event days against ordinary days of the same weekday and year;
   - `07a`, `07b`: how often prices change, and units against price change;
   - `08a`, `08b`: zero-sale cells, overall and per series; `09a`, `09b`: the Pareto curve and summary; `10_data_quality`: the counts behind the traps.
4. **Check.** `check.py` streams the raw CSVs once in plain Python (no SQL, no DuckDB, no pandas) and requires all 2,151 numbers to equal the SQL results.
5. **Charts.**

## Results

- **The business.** $191.6M of revenue (units x weekly price) on 66.9 million units, $2.86 a unit. Revenue per day grew 10.3% in 2013, 5.4% in 2014 and 12.0% in 2015,
  while units per day changed by +9.2%, -0.4% and +5.4%: the revenue per unit went from $2.71 (2012) to $3.07 (2015). Monthly revenue went from $1.93M (February 2011) to $4.07M (April 2016).
- **The week.** Saturday and Sunday are 20.8% and 21.4% above the average day; Wednesday is the lowest, at 13% below.
- **Categories and departments.** Foods are 58.0% of revenue, household 29.8% and hobbies 12.2%; the foods share fell from 60.7% in 2012 to 55.2% in 2015. FOODS_3 alone is 37.8% of revenue and 49.2% of units.
  By units FOODS_1 outsells HOUSEHOLD_2 (5,190,400 against 3,041,237); by revenue HOUSEHOLD_2 is ahead ($15.0M against $13.2M): $4.93 a unit against $2.54.
- **Stores.** CA_3 is the largest, $32.7M (17.1%); CA_4 the smallest, $12.5M (6.5%). California has 44.9% of revenue with 4 stores, Texas 28.8% and Wisconsin 26.4% with 3 each.
- **SNAP days.** Comparing the same weekdays, foods sell 10.7% more on a SNAP day in California, 17.5% in Texas and 33.0% in Wisconsin; household goods 3.5%, 2.7% and 3.5% more, hobbies 3.3%, 2.2% and 2.1%.
- **Events.** Against an ordinary day of the same weekday and year, 25 of the 30 named events are within 15%. The exceptions: Christmas 0.00, Thanksgiving 0.69, New Year 0.72, Mother's day 0.84; above, Labor Day 1.29. On 25 December 24 of the 50 store-days have no sales at all.
- **Prices.** Of 6,658,181 consecutive priced weeks of an item in a store, 1.17% saw a price change (0.50% cuts, 0.67% rises), by 25% on average. Units in the week of a cut of 10% or more were 1.20 times the week before; of a rise of 10% or more, 1.14 times; unchanged prices, 1.00. Rises and cuts both come with more units, so this is no price elasticity.
- **Intermittent demand.** 68.0% of the 59,181,090 item-store-day cells sold nothing, but 20.8% of the cells are before the item had a price. Counting only priced days, 59.6% sold nothing (foods 51.1%, household 64.6%, hobbies 71.5%). The median series sold nothing on 63.4% of its priced days; 67.4% of series have at least half zero days, 24.3% at least 80%, and only 2.0% under 10%.
- **Concentration.** The top 1% of items (31 items) earn 11.2% of revenue, the top 10% (305 items) 42.8%, the top 20% 59.4%; the bottom half 14.7%. Half of revenue takes 421 items, 80% takes 1,269 (41.6% of items): milder than 80/20. Of the top 10% by units, only 53.8% are also in the top 10% by revenue.
- **The traps.** Units are not dollars: the department ranking changes and the item ranking more so (above). Prices exist only from the week an item is first sold: 19,558 of 30,490 series are priced after week 1, 0 cells have units without a price, and 30,346 series are priced exactly from their first sale week (144 were priced earlier and sold later). No series has a gap in its price after launch, and all 30,490 are priced to the end.

## Not done, and caveats

- This is 10 stores of one retailer in 3 states and 3,049 items, not "Walmart" as a whole, and the items are hashed, so no item can be named. It is the M5 competition's sales file, not a transaction log.
- Revenue is units x the weekly list price. Coupons, markdowns not in the price file and SNAP tender are not in it, and there are no costs, so it is sales, not profit.
- The SNAP comparison is an association: SNAP days sit early in the month, which is also payday for many shoppers. The non-food categories show how much of the lift is the calendar alone (2% to 4%), not the benefit. No causal claim.
- Price changes coincide with demand shocks, so units against price change is not an elasticity; no model was fitted.
- January 2011 starts on the 29th and May 2016 stops on the 22nd, so monthly and yearly figures use complete months or per-day averages; 2011 and 2016 are partial years. The last week of the sales file has two days.
- The calendar and price files run 28 days and 121,960 price rows past the sales (the competition's forecast period): ignored. No forecasting here; that is another project.
