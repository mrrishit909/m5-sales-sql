"""Steps 2-4: load the M5 CSVs into DuckDB (a file under data/), run sql/00_setup.sql (long table: one row per item, store and day,
joined to the calendar and the weekly prices), then every other sql/*.sql file, writing each result to results/<file name>.csv.

    ./venv/bin/python run_sql.py            (about 5-10 minutes, under 3 GB of memory: the long table has 59 million rows)
"""
from pathlib import Path

import duckdb

HERE = Path(__file__).parent
DATA = HERE / "data"
DB = DATA / "m5.duckdb"
N_DAYS = 1941                                              # d_1 ... d_1941 in sales_train_evaluation.csv (2011-01-29 ... 2016-05-22)


def main():
    DB.unlink(missing_ok=True)
    con = duckdb.connect(str(DB))
    con.execute("SET memory_limit = '2500MB'; SET threads = 1; SET preserve_insertion_order = false")
    con.execute(f"SET temp_directory = '{DATA / 'tmp'}'")
    types = {"id": "VARCHAR", "item_id": "VARCHAR", "dept_id": "VARCHAR", "cat_id": "VARCHAR", "store_id": "VARCHAR", "state_id": "VARCHAR"}
    types |= {f"d_{i}": "SMALLINT" for i in range(1, N_DAYS + 1)}
    con.execute("CREATE TABLE wide AS SELECT * FROM read_csv(?, header = true, types = ?)", [str(DATA / "sales_train_evaluation.csv"), types])
    con.execute("CREATE TABLE cal_raw AS SELECT * FROM read_csv(?, header = true, types = {'event_name_1': 'VARCHAR', 'event_type_1': 'VARCHAR', 'event_name_2': 'VARCHAR', 'event_type_2': 'VARCHAR'})", [str(DATA / "calendar.csv")])
    con.execute("CREATE TABLE prices_raw AS SELECT * FROM read_csv(?, header = true, types = {'sell_price': 'DECIMAL(7,2)'})", [str(DATA / "sell_prices.csv")])
    for f in sorted((HERE / "sql").glob("*.sql")):
        if f.name.startswith("00_"):
            con.execute(f.read_text())                      # setup: tables, nothing to export
            print(f.name, "done", flush=True)
            continue
        out = HERE / "results" / f"{f.stem}.csv"
        con.execute(f.read_text()).fetchdf().to_csv(out, index=False)
        print(f"{f.name:30s} -> {out.name}", flush=True)
    con.close()


if __name__ == "__main__":
    main()
