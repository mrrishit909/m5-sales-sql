"""Step 5: the independent check. Recompute every table in results/ with plain Python (csv, loops, dictionaries, statistics.median: no DuckDB, no SQL,
no pandas) by streaming the raw CSVs once, and require it to equal what the SQL wrote. Counts must match exactly, other numbers to a relative 1e-9.

    ./venv/bin/python check.py      (about 3-6 minutes, under 1 GB: nothing is held per item x day except one 1,941-integer row at a time)
"""
import calendar
import csv
import statistics
from array import array
from collections import defaultdict
from datetime import date
from math import ceil
from pathlib import Path

HERE = Path(__file__).parent
R = HERE / "results"
DATA = HERE / "data"
ND = 1941                                                  # days with sales
n_ok = 0


def close(a, b):
    return abs(a - b) <= 1e-9 * max(1.0, abs(b))


def read(name):
    with open(R / f"{name}.csv") as f:
        return list(csv.reader(f))


def num_or_none(s):
    return None if s == "" else float(s)


def compare(name, expected, key_cols=0):
    """expected: list of rows (lists). Strings must be equal, numbers close; None means an empty CSV cell."""
    global n_ok
    got = read(name)[1:]
    assert len(got) == len(expected), f"{name}: {len(got)} rows in results, {len(expected)} recomputed"
    for g, e in zip(got, expected):
        assert len(g) == len(e), f"{name}: width {len(g)} vs {len(e)}"
        for gv, ev in zip(g, e):
            if ev is None:
                assert gv == "", f"{name}: expected empty, got {gv}"
            elif isinstance(ev, str):
                assert gv == ev, f"{name}: {gv!r} != {ev!r}"
            else:
                if isinstance(ev, bool):
                    assert gv == str(ev), f"{name}: {gv} != {ev}"
                else:
                    assert gv != "" and close(float(gv), float(ev)), f"{name}: results {gv} vs recount {ev!r}"
            n_ok += 1


def compare_metrics(name, metrics):
    global n_ok
    got = {k: float(v) for k, v in read(name)[1:]}
    assert set(got) == set(metrics), f"{name}: metric names differ: {set(got) ^ set(metrics)}"
    for k, v in metrics.items():
        assert close(got[k], v), f"{name}.{k}: results {got[k]} vs recount {v!r}"
        n_ok += 1


# ---------------------------------------------------------------- calendar
cal = list(csv.DictReader(open(DATA / "calendar.csv")))
weekord = {w: i + 1 for i, w in enumerate(sorted({int(r["wm_yr_wk"]) for r in cal}))}      # Walmart week number -> 1, 2, 3 ...
days = []                                                  # index 0..1940
for r in cal[:ND]:
    y, m, dd = map(int, r["date"].split("-"))
    days.append({"date": date(y, m, dd), "year": y, "month": m, "week": weekord[int(r["wm_yr_wk"])], "weekday": r["weekday"], "wday": int(r["wday"]),
                 "event": r["event_name_1"], "etype": r["event_type_1"], "snap": {"CA": r["snap_CA"] == "1", "TX": r["snap_TX"] == "1", "WI": r["snap_WI"] == "1"}})
assert all(x["week"] == i // 7 + 1 for i, x in enumerate(days)), "weeks are not 7-day blocks starting at d_1"   # lets the loop below work in blocks
LASTW = days[-1]["week"]                                   # 278
assert LASTW == 278 and ND - 7 * 277 == 2
wk_of_day = [x["week"] for x in days]

# ---------------------------------------------------------------- prices: one small array per item x store, indexed by week number, cents (0 = no price)
prices = {}
price_rows = dup_rows = after_end = 0
with open(DATA / "sell_prices.csv") as f:
    rd = csv.reader(f)
    next(rd)
    for store, item, wk, p in rd:
        whole, _, frac = p.partition(".")
        assert len(frac) <= 2
        cents = int(whole) * 100 + int(frac.ljust(2, "0"))
        arr = prices.get((store, item))
        if arr is None:
            arr = prices[(store, item)] = array("i", [0]) * (max(weekord.values()) + 1)
        w = weekord[int(wk)]
        if arr[w]:
            dup_rows += 1
        arr[w] = cents
        price_rows += 1
        if w > LASTW:
            after_end += 1

# ---------------------------------------------------------------- one pass over the sales: item x store rows
daily_u = defaultdict(lambda: [0] * ND)                    # (dept, store) -> units per day
daily_r = defaultdict(lambda: [0] * ND)                    # (dept, store) -> revenue in cents per day
item = {}                                                  # item -> [revenue cents, units, dept, cat]
series_rev = []
dept_items = defaultdict(set)
cells = defaultdict(lambda: [0, 0, 0, 0])                  # cat -> [cells, unpriced, priced zero, sold]
zero_share = defaultdict(list)                             # cat -> per series zero share over priced days
pc = {c: [0, 0, 0, 0, 0.0] for c in ("ALL", "FOODS", "HOBBIES", "HOUSEHOLD")}     # price pairs: n, changed, cut, rise, sum abs change
cls = [[0, 0, 0, 0] for _ in range(5)]                     # price-change class: pairs, units, prev units, units up
dq = defaultdict(float)
n_series = 0
with open(DATA / "sales_train_evaluation.csv") as f:
    rd = csv.reader(f)
    head = next(rd)
    assert head[6:] == [f"d_{i}" for i in range(1, ND + 1)]
    for row in rd:
        _id, item_id, dept, cat, store, state = row[:6]
        units = row[6:]
        arr = prices[(store, item_id)]
        n_series += 1
        du, dr = daily_u[(dept, store)], daily_r[(dept, store)]
        wu = [0] * (LASTW + 1)
        tu = tr = sold_priced = bad = 0
        first_sale = 0
        for d, u in enumerate(units):
            if u != "0":
                u = int(u)
                w = wk_of_day[d]
                p = arr[w]
                tu += u
                wu[w] += u
                du[d] += u
                if p:
                    dr[d] += u * p
                    tr += u * p
                    sold_priced += 1
                else:
                    bad += 1
                if not first_sale:
                    first_sale = w
        priced_w = [w for w in range(1, LASTW + 1) if arr[w]]
        dq["never_priced"] += not priced_w
        assert priced_w, "a series without any price needs its own handling"
        priced_cells = 7 * len(priced_w) - (5 if LASTW in priced_w else 0)       # the last week has only 2 days
        c = cells[cat]
        for k, v in enumerate((ND, ND - priced_cells, priced_cells - sold_priced, sold_priced + bad)):
            c[k] += v
        z = (priced_cells - sold_priced) / priced_cells
        zero_share[cat].append(z)
        zero_share["ALL"].append(z)
        dq["units_no_price"] += bad
        dq["never_sold"] += tu == 0
        dq["from_week_1"] += priced_w[0] == 1
        dq["after_week_1"] += priced_w[0] > 1
        dq["first_price_is_first_sale"] += priced_w[0] == first_sale
        dq["sale_before_price"] += first_sale < priced_w[0]
        dq["price_gap"] += len(priced_w) < priced_w[-1] - priced_w[0] + 1
        dq["priced_to_last"] += priced_w[-1] == LASTW
        # price changes, complete weeks 2..277 with a price in this and the previous week
        for w in range(2, 278):
            p, q = arr[w], arr[w - 1]
            if p and q:
                for key in ("ALL", cat):
                    a = pc[key]
                    a[0] += 1
                    a[1] += p != q
                    a[2] += p < q
                    a[3] += p > q
                    if p != q:
                        a[4] += abs(p / q - 1)
                k = 0 if p * 10 <= q * 9 else 1 if p < q else 2 if p == q else 3 if p * 10 < q * 11 else 4
                x = cls[k]
                x[0] += 1
                x[1] += wu[w]
                x[2] += wu[w - 1]
                x[3] += wu[w] > wu[w - 1]
        rec = item.setdefault(item_id, [0, 0, dept, cat])
        rec[0] += tr
        rec[1] += tu
        series_rev.append(tr)
        dept_items[dept].add(item_id)
assert n_series == 30490

DEPTS = sorted(dept_items)
CAT_OF = {d: d.split("_")[0] for d in DEPTS}
STORES = sorted({s for _, s in daily_u})
STATE_OF = {s: s.split("_")[0] for s in STORES}
CATS = ["FOODS", "HOBBIES", "HOUSEHOLD"]


def day_total(keyf=lambda d, s: True, rev=True):
    src = daily_r if rev else daily_u
    out = [0] * ND
    for (d, s), arr_ in src.items():
        if keyf(d, s):
            for i, v in enumerate(arr_):
                out[i] += v
    return out


tot_r, tot_u = day_total(), day_total(rev=False)

# ---------------------------------------------------------------- 01a monthly revenue by category
by = defaultdict(lambda: [0, 0])
ndays = defaultdict(set)
for cat in CATS:
    cr, cu = day_total(lambda d, s, cat=cat: CAT_OF[d] == cat), day_total(lambda d, s, cat=cat: CAT_OF[d] == cat, rev=False)
    for i, x in enumerate(days):
        k = (f"{x['year']}-{x['month']:02d}", cat)
        by[k][0] += cr[i]
        by[k][1] += cu[i]
        ndays[k].add(i)
exp = [[m, c, len(ndays[(m, c)]), len(ndays[(m, c)]) == calendar.monthrange(int(m[:4]), int(m[5:]))[1], by[(m, c)][0] / 100, by[(m, c)][1]] for (m, c) in sorted(by)]
compare("01a_monthly_revenue", exp)

# ---------------------------------------------------------------- 01b yearly
ys = {}
for i, x in enumerate(days):
    a = ys.setdefault(x["year"], [0, 0, 0])
    a[0] += 1
    a[1] += tot_r[i]
    a[2] += tot_u[i]
exp = []
for y in sorted(ys):
    n, r_, u_ = ys[y]
    full = n >= 365 and y - 1 in ys and ys[y - 1][0] >= 365
    g = (r_ / n) / (ys[y - 1][1] / ys[y - 1][0]) - 1 if full else None
    gu = (u_ / n) / (ys[y - 1][2] / ys[y - 1][0]) - 1 if full else None
    exp.append([float(y), n, r_ / 100, u_, r_ / 100 / n, r_ / 100 / u_, g, gu])
exp = [[int(r[0])] + r[1:] for r in exp]
compare("01b_yearly_revenue", exp)

# ---------------------------------------------------------------- 02 weekday
wd = {}
for i, x in enumerate(days):
    a = wd.setdefault((x["wday"], x["weekday"]), [0, 0, 0])
    a[0] += 1
    a[1] += tot_r[i]
    a[2] += tot_u[i]
avg = {k: v[1] / v[0] / 100 for k, v in wd.items()}
mean_avg = sum(avg.values()) / 7
compare("02_weekday", [[k[1], v[0], avg[k], v[2] / v[0], avg[k] / mean_avg] for k, v in sorted(wd.items())])

# ---------------------------------------------------------------- 03a departments
drev = defaultdict(int)
dun = defaultdict(int)
for (d, s), arr_ in daily_r.items():
    drev[d] += sum(arr_)
for (d, s), arr_ in daily_u.items():
    dun[d] += sum(arr_)
T_R, T_U = sum(drev.values()), sum(dun.values())
order = sorted(DEPTS, key=lambda d: -drev[d])
rk_u = {d: i + 1 for i, d in enumerate(sorted(DEPTS, key=lambda d: -dun[d]))}
compare("03a_departments", [[d, CAT_OF[d], len(dept_items[d]), dun[d], drev[d] / 100, drev[d] / T_R, dun[d] / T_U, drev[d] / 100 / dun[d], i + 1, rk_u[d]] for i, d in enumerate(order)])
assert T_R == sum(tot_r)

# ---------------------------------------------------------------- 03b category by year
exp = []
cat_year = defaultdict(int)
for cat in CATS:
    cr = day_total(lambda d, s, cat=cat: CAT_OF[d] == cat)
    for i, x in enumerate(days):
        if 2012 <= x["year"] <= 2015:
            cat_year[(str(x["year"]), cat)] += cr[i]
        cat_year[("all", cat)] += cr[i]
for per in sorted({k[0] for k in cat_year}):
    t = sum(cat_year[(per, c)] for c in CATS)
    for c in CATS:
        exp.append([per, c, cat_year[(per, c)] / 100, cat_year[(per, c)] / t])
compare("03b_category_by_year", exp)

# ---------------------------------------------------------------- 04a stores, 04b states
srev = {s: sum(sum(a) for (d, st), a in daily_r.items() if st == s) for s in STORES}
sun = {s: sum(sum(a) for (d, st), a in daily_u.items() if st == s) for s in STORES}
sfood = {s: sum(sum(a) for (d, st), a in daily_r.items() if st == s and CAT_OF[d] == "FOODS") for s in STORES}
order = sorted(STORES, key=lambda s: -srev[s])
compare("04a_stores", [[s, STATE_OF[s], srev[s] / 100, srev[s] / T_R, sun[s], srev[s] / 100 / ND, srev[s] / 100 / sun[s], sfood[s] / srev[s], i + 1] for i, s in enumerate(order)])
st_rev = defaultdict(int)
st_un = defaultdict(int)
st_n = defaultdict(int)
for s in STORES:
    st_rev[STATE_OF[s]] += srev[s]
    st_un[STATE_OF[s]] += sun[s]
    st_n[STATE_OF[s]] += 1
compare("04b_states", [[st, st_n[st], st_rev[st] / 100, st_rev[st] / T_R, st_rev[st] / 100 / st_n[st], st_un[st]] for st in sorted(st_rev, key=lambda k: -st_rev[k])])

# ---------------------------------------------------------------- 05 SNAP
exp = []
for st in ("CA", "TX", "WI"):
    for cat in CATS:
        rv = day_total(lambda d, s, st=st, cat=cat: STATE_OF[s] == st and CAT_OF[d] == cat)
        un = day_total(lambda d, s, st=st, cat=cat: STATE_OF[s] == st and CAT_OF[d] == cat, rev=False)
        g = {1: [], 0: []}
        per_w = defaultdict(lambda: {1: [0, 0, 0], 0: [0, 0, 0]})
        for i, x in enumerate(days):
            sn = int(x["snap"][st])
            g[sn].append(rv[i] / 100)
            a = per_w[x["wday"]][sn]
            a[0] += 1
            a[1] += rv[i] / 100
            a[2] += un[i]
        m1, m0 = sum(g[1]) / len(g[1]), sum(g[0]) / len(g[0])
        rs = [(w[1][1] / w[1][0]) / (w[0][1] / w[0][0]) for w in per_w.values()]
        us = [(w[1][2] / w[1][0]) / (w[0][2] / w[0][0]) for w in per_w.values()]
        exp.append([st, cat, len(g[1]), len(g[0]), m1, m0, m1 / m0, sum(rs) / 7, sum(us) / 7])
compare("05_snap", exp)

# ---------------------------------------------------------------- 06 events
tot_d = [v / 100 for v in tot_r]
base_acc = defaultdict(lambda: [0.0, 0])
for i, x in enumerate(days):
    if not x["event"]:
        a = base_acc[(x["year"], x["wday"])]
        a[0] += tot_d[i]
        a[1] += 1
ev = []
for i, x in enumerate(days):
    if x["event"]:
        b = base_acc[(x["year"], x["wday"])]
        ev.append((x["event"], x["etype"], tot_d[i] / (b[0] / b[1])))
bt = defaultdict(list)
for name, typ, idx in ev:
    bt[typ].append((name, idx))
rows = []
for typ, lst in bt.items():
    xs = [i for _, i in lst]
    nc = [i for n_, i in lst if n_ != "Christmas"]
    rows.append([typ, len(xs), sum(xs) / len(xs), statistics.median(xs), sum(nc) / len(nc)])
rows.sort(key=lambda r: -r[2])
compare("06a_event_types", rows)
bn = defaultdict(list)
typ_of = {}
for name, typ, idx in ev:
    bn[name].append(idx)
    typ_of[name] = typ
rows = [[n_, typ_of[n_], len(v), sum(v) / len(v)] for n_, v in bn.items()]
rows.sort(key=lambda r: (-r[3], r[0]))
compare("06b_events", rows)

# ---------------------------------------------------------------- 07 price changes
exp = []
for key in ("ALL", "FOODS", "HOBBIES", "HOUSEHOLD"):
    n, ch, cut, rise, s_ = pc[key]
    exp.append([key, n, ch / n, cut / n, rise / n, s_ / ch])
compare("07a_price_changes", exp)
names = ["1 cut 10% or more", "2 cut under 10%", "3 unchanged", "4 rise under 10%", "5 rise 10% or more"]
compare("07b_price_vs_units", [[names[k], x[0], x[1] / x[2], x[3] / x[0]] for k, x in enumerate(cls)])

# ---------------------------------------------------------------- 08 intermittency
exp = []
tot_cells = [sum(cells[c][k] for c in CATS) for k in range(4)]
for key in ("ALL", "FOODS", "HOBBIES", "HOUSEHOLD"):
    n, unp, pz, sold = tot_cells if key == "ALL" else cells[key]
    exp.append([key, n, unp / n, pz / n, sold / n, (n - sold) / n, pz / (n - unp)])
compare("08a_intermittency", exp)
exp = []
for key in ("ALL", "FOODS", "HOBBIES", "HOUSEHOLD"):
    z = zero_share[key]
    exp.append([key, len(z), statistics.median(z), sum(v >= 0.5 for v in z) / len(z), sum(v >= 0.8 for v in z) / len(z), sum(v < 0.1 for v in z) / len(z)])
compare("08b_series_zero_share", exp)

# ---------------------------------------------------------------- 09 concentration
N = len(item)
ranked = sorted(item.items(), key=lambda kv: (-kv[1][0], kv[0]))
cum = [0]
for _, v in ranked:
    cum.append(cum[-1] + v[0])
TOT = cum[-1]
ceil_pct = lambda pct, n: -(-pct * n // 100)               # ceil(pct/100 x n) in integers
compare("09a_pareto_curve", [[pct, ceil_pct(pct, N), cum[ceil_pct(pct, N)] / TOT] for pct in range(101)])
by_units = sorted(item.items(), key=lambda kv: (-kv[1][1], kv[0]))
k10 = ceil_pct(10, N)
top_rev = {k for k, _ in ranked[:k10]}
top_units = {k for k, _ in by_units[:k10]}
sr = sorted(series_rev, reverse=True)                       # ties are equal values, so the order of tied series cannot change a share
m = {"items": N, "items_without_any_revenue": sum(v[0] == 0 for v in item.values()),
     "top_1pct_items_share": cum[ceil_pct(1, N)] / TOT, "top_10pct_items_share": cum[k10] / TOT, "top_20pct_items_share": cum[ceil_pct(20, N)] / TOT,
     "bottom_50pct_items_share": (TOT - cum[N // 2]) / TOT,
     "items_for_50pct_revenue": next(i for i in range(1, N + 1) if 2 * cum[i] >= TOT), "items_for_80pct_revenue": next(i for i in range(1, N + 1) if 5 * cum[i] >= 4 * TOT),
     "series_top_10pct_share": sum(sr[:ceil_pct(10, len(sr))]) / sum(sr),
     "overlap_top10_units_vs_revenue": len(top_rev & top_units) / k10, "top_item_share": ranked[0][1][0] / TOT}
for cat in CATS:
    rs_ = sorted((v[0] for v in item.values() if v[3] == cat), reverse=True)
    m[f"top_10pct_share_{cat}"] = sum(rs_[:ceil_pct(10, len(rs_))]) / sum(rs_)
compare_metrics("09b_pareto_summary", m)

# ---------------------------------------------------------------- 10 data quality
chain_zero = sum(v == 0 for v in tot_u)
store_tot = defaultdict(lambda: [0] * ND)
for (d, s), arr_ in daily_u.items():
    a = store_tot[s]
    for i, v in enumerate(arr_):
        a[i] += v
sz = [(s, i) for s, a in store_tot.items() for i, v in enumerate(a) if v == 0]
xmas = [i for i, x in enumerate(days) if x["date"].month == 12 and x["date"].day == 25]
cells_all = n_series * ND
m = {"series_item_store": n_series, "cells_item_store_day": cells_all, "days_with_sales": ND, "cells_with_units_but_no_price": dq["units_no_price"],
     "cells_unpriced_share": tot_cells[1] / cells_all, "series_never_sold": dq["never_sold"], "series_never_priced": dq["never_priced"],
     "series_priced_from_week_1": dq["from_week_1"], "series_priced_after_week_1": dq["after_week_1"],
     "series_first_priced_week_is_first_sale_week": dq["first_price_is_first_sale"], "series_first_sale_before_first_priced_week": dq["sale_before_price"],
     "series_with_price_gap_after_launch": dq["price_gap"], "series_priced_to_last_week": dq["priced_to_last"], "price_rows_in_file": price_rows,
     "price_rows_duplicate_keys": dup_rows, "price_rows_after_sales_end": after_end, "calendar_days_after_sales_end": len(cal) - ND,
     "last_week_days": sum(1 for x in days if x["week"] == LASTW), "chain_days_with_zero_units": chain_zero, "store_days_with_zero_units": len(sz),
     "store_days_zero_units_on_dec25": sum(1 for _, i in sz if i in xmas), "store_days_on_dec25": len(xmas) * len(STORES),
     "event_days": sum(1 for x in days if x["event"]), "total_units": T_U, "total_revenue": T_R / 100, "revenue_per_unit": T_R / 100 / T_U}
compare_metrics("10_data_quality", m)

print(f"check.py: {n_ok} recomputed numbers agree with results/")
