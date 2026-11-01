"""Step 3. Logbook winds: averaged on a grid, by latitude belt, and against a modern benchmark.

CLIWOC gives each daily observation a wind direction in degrees (the direction the wind blows FROM, translated from
the officers' compass points), with 361 = calm and 362 = variable, and a wind force in m/s translated from the
logbook's words (Beaufort-style terms). Here:
  * GRID: in each 5 degree square (and season), the vector mean of unit vectors pointing where the wind blew TO;
    'steadiness' is the length of that mean (1 = always the same direction, 0 = no prevailing direction). Squares need
    at least MIN_OBS directional observations. Force is the mean m/s where recorded.
  * BELTS: by 5 degree latitude band in the Atlantic (70 W to 20 E) and the Indian Ocean (20 E to 115 E): share of
    observations with an easterly component, mean west-to-east component, and share calm or variable.
  * BENCHMARK: NCEP/NCAR Reanalysis 1 long-term monthly mean near-surface winds (1991 to 2020) interpolated to every
    observation's place and calendar month, then averaged in the same squares with the same month mix. The angle
    between the logbook mean and the benchmark mean in each square measures agreement.
Outputs: WORK/winds.json; data/wind_grid.csv, data/wind_belts.csv; data/wind_arrows.json (page).
Run: python3 code/03_winds.py
"""
import os, sys, csv
import numpy as np, netCDF4
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

CELL, MIN_OBS = 5, 25
O = dict(np.load(f"{WORK}/obs.npz"))
lon, lat, wd, ws, mon, yr = O["lon"], O["lat"], O["wd"], O["ws"], O["month"], O["year"]
valid = np.isfinite(wd)
dirn = valid & (wd >= 1) & (wd <= 360)          # 0 does not occur as a direction code here
calm = valid & (wd == 361); var = valid & (wd == 362)
print("observations", len(wd), "with direction", dirn.sum(), "calm", calm.sum(), "variable", var.sum(), "no wind", (~valid).sum())
th = np.radians(wd)
u = np.where(dirn, -np.sin(th), np.nan)          # unit vector the wind blows TOWARDS (east, north)
v = np.where(dirn, -np.cos(th), np.nan)

# ---------- NCEP benchmark at each observation (bilinear in space, the observation's calendar month) ----------
U = netCDF4.Dataset(f"{NCEP}/uwnd.mon.ltm.nc")["uwnd"][:].filled(np.nan)
V = netCDF4.Dataset(f"{NCEP}/vwnd.mon.ltm.nc")["vwnd"][:].filled(np.nan)
glat = np.arange(90, -90.1, -2.5); glon = np.arange(0, 360, 2.5)


def ncep_at(lo, la, mo):
    x = (np.mod(lo, 360)) / 2.5; y = (90 - la) / 2.5
    x0 = np.floor(x).astype(int); y0 = np.clip(np.floor(y).astype(int), 0, 71)
    fx = x - x0; fy = y - y0; x1 = (x0 + 1) % 144; x0 = x0 % 144; y1 = y0 + 1; m = mo - 1
    out = []
    for A in (U, V):
        out.append(A[m, y0, x0] * (1 - fx) * (1 - fy) + A[m, y0, x1] * fx * (1 - fy) + A[m, y1, x0] * (1 - fx) * fy + A[m, y1, x1] * fx * fy)
    return out


nu, nv = ncep_at(lon, lat, mon)
nspd = np.hypot(nu, nv)

SEASONS = {"all": list(range(1, 13)), "djf": [12, 1, 2], "jja": [6, 7, 8]}
ix = np.floor((lon + 180) / CELL).astype(int); iy = np.floor((lat + 90) / CELL).astype(int)
nx, ny = 360 // CELL, 180 // CELL
ix = np.clip(ix, 0, nx - 1); iy = np.clip(iy, 0, ny - 1)
cid = iy * nx + ix


def agg(mask):
    k = cid[mask]
    n = np.bincount(k, minlength=nx * ny)
    su = np.bincount(k, weights=u[mask], minlength=nx * ny); sv = np.bincount(k, weights=v[mask], minlength=nx * ny)
    # NCEP direction-only (unit vectors at each observation) and full vectors
    nuu = np.where(nspd[mask] > 0, nu[mask] / nspd[mask], 0); nvv = np.where(nspd[mask] > 0, nv[mask] / nspd[mask], 0)
    snu = np.bincount(k, weights=nu[mask], minlength=nx * ny); snv = np.bincount(k, weights=nv[mask], minlength=nx * ny)
    wsm = mask & np.isfinite(ws)
    nws = np.bincount(cid[wsm], minlength=nx * ny); sws = np.bincount(cid[wsm], weights=ws[wsm], minlength=nx * ny)
    return n, su, sv, snu, snv, nws, sws


def ang(a_u, a_v, b_u, b_v):
    d = np.degrees(np.arctan2(a_u, a_v) - np.arctan2(b_u, b_v))
    return np.abs((d + 180) % 360 - 180)


grids, rows = {}, []
for sk, months in SEASONS.items():
    m = dirn & np.isin(mon, months)
    n, su, sv, snu, snv, nws, sws = agg(m)
    mc = np.isin(mon, months) & (calm | var)
    ncv = np.bincount(cid[mc], minlength=nx * ny)
    cells = []
    for c in np.where(n >= MIN_OBS)[0]:
        mu, mv = su[c] / n[c], sv[c] / n[c]; R = float(np.hypot(mu, mv))
        bu, bv = snu[c] / n[c], snv[c] / n[c]
        frm = (np.degrees(np.arctan2(-mu, -mv)) + 360) % 360       # direction it blew FROM
        rec = {"lon": -180 + (c % nx) * CELL + CELL / 2, "lat": -90 + (c // nx) * CELL + CELL / 2, "n": int(n[c]),
               "from": round(float(frm), 1), "steady": round(R, 3), "u": round(float(mu), 3), "v": round(float(mv), 3),
               "force": round(float(sws[c] / nws[c]), 1) if nws[c] >= 10 else None,
               "calm_var": round(float(ncv[c] / (n[c] + ncv[c])), 3),
               "ncep_u": round(float(bu), 2), "ncep_v": round(float(bv), 2), "ncep_speed": round(float(np.hypot(bu, bv)), 2),
               "diff": round(float(ang(mu, mv, bu, bv)), 1)}
        cells.append(rec)
        rows.append([sk] + [rec[k] for k in ("lon", "lat", "n", "from", "steady", "force", "calm_var", "ncep_u", "ncep_v", "diff")])
    grids[sk] = cells
    print(sk, "cells", len(cells))

# agreement (all seasons): squares with a steady benchmark wind (mean vector >= 3 m/s), weighted equally and by observations
G = grids["all"]
steadyc = [c for c in G if c["ncep_speed"] >= 3]
diffs = np.array([c["diff"] for c in steadyc]); wts = np.array([c["n"] for c in steadyc])
alld = np.array([c["diff"] for c in G]); allw = np.array([c["n"] for c in G])
agree = {"cells": len(G), "cells_steady": len(steadyc),
         "share45_steady": float((diffs <= 45).mean()), "share30_steady": float((diffs <= 30).mean()), "median_steady": float(np.median(diffs)),
         "share45_steady_obs": float(wts[diffs <= 45].sum() / wts.sum()),
         "share45_all": float((alld <= 45).mean()), "median_all": float(np.median(alld)), "share45_all_obs": float(allw[alld <= 45].sum() / allw.sum())}
# observation level: each daily wind against the benchmark at that place and month
oo = dirn & (nspd >= 3)
d_obs = ang(u[oo], v[oo], nu[oo], nv[oo])
agree["obs_n"] = int(oo.sum()); agree["obs_share45"] = float((d_obs <= 45).mean()); agree["obs_share90"] = float((d_obs <= 90).mean())
agree["obs_median"] = float(np.median(d_obs))
print("agreement", agree)

# ---------- belts ----------
OCEANS = {"atlantic": (-70, 20), "indian": (20, 115)}
belts = {}
brow = []
for ok, (a, b) in OCEANS.items():
    inb = (lon >= a) & (lon < b)
    if ok == "atlantic":
        inb &= ~((lat > 30) & (lon > -6))        # leave out the Mediterranean and Europe's coasts
    out = []
    for la0 in range(-60, 65, 5):
        mb = inb & (lat >= la0) & (lat < la0 + 5)
        md = mb & dirn
        if md.sum() < 200: continue
        e = (wd[md] > 0) & (wd[md] < 180)                     # wind from an easterly point
        rec = {"lat0": la0, "lat1": la0 + 5, "n": int(md.sum()), "east_share": float(e.mean()), "u": float(np.mean(u[md])), "v": float(np.mean(v[md])),
               "calm_var": float((mb & (calm | var)).sum() / (mb & valid).sum()), "calm": float((mb & calm).sum() / (mb & valid).sum()),
               "ncep_u": float(np.nanmean(nu[md])), "ncep_unit_u": float(np.nanmean(np.where(nspd[md] > 0, nu[md] / nspd[md], 0))),
               "force": float(np.nanmean(ws[mb & np.isfinite(ws)])) if (mb & np.isfinite(ws)).sum() > 50 else None}
        out.append(rec)
        brow.append([ok, la0, la0 + 5, rec["n"], round(rec["east_share"], 3), round(rec["u"], 3), round(rec["v"], 3), round(rec["calm_var"], 3),
                     round(rec["ncep_u"], 2), round(rec["ncep_unit_u"], 3), round(rec["force"], 2) if rec["force"] else ""])
    belts[ok] = out
    print(ok)
    for r in out:
        print(f"  {r['lat0']:4d} n={r['n']:6d} east={r['east_share']:.2f} u={r['u']:+.2f} ncep_unit_u={r['ncep_unit_u']:+.2f} calmvar={r['calm_var']:.3f} force={r['force']}")
cor = np.corrcoef([r["u"] for o in belts.values() for r in o], [r["ncep_unit_u"] for o in belts.values() for r in o])[0, 1]
print("belt correlation of logbook and benchmark west-east component:", round(cor, 3))

# named belts (the wiki-style textbook belts) as simple boxes
def box_share(lo0, lo1, la0, la1, d0, d1, months=None):
    m = dirn & (lon >= lo0) & (lon < lo1) & (lat >= la0) & (lat < la1)
    if months: m &= np.isin(mon, months)
    w = wd[m]
    s = ((w >= d0) & (w <= d1)) if d0 < d1 else ((w >= d0) | (w <= d1))
    return {"n": int(m.sum()), "share": float(s.mean())}


named = {
    "ne_trades": box_share(-60, -15, 10, 25, 0, 90),          # from N to E
    "se_trades": box_share(-35, 10, -25, -5, 90, 180),        # from E to S
    "forties": box_share(20, 110, -48, -36, 180, 360),        # from S through W to N
    "westerlies_n": box_share(-50, -10, 40, 52, 180, 360),
    "monsoon_djf": box_share(55, 90, 5, 20, 0, 90, [12, 1, 2]),
    "monsoon_jja": box_share(55, 90, 5, 20, 180, 270, [6, 7, 8]),
    "se_trades_indian": box_share(55, 100, -25, -10, 90, 180),
}
# doldrums: the Atlantic band with the most calms and variable winds
atl = belts["atlantic"]
dold = max([r for r in atl if -10 <= r["lat0"] <= 15], key=lambda r: r["calm_var"])
named["doldrums"] = {"lat0": dold["lat0"], "lat1": dold["lat1"], "calm_var": dold["calm_var"],
                     "calm_var_trades": float(np.mean([r["calm_var"] for r in atl if r["lat0"] in (10, 15, -15, -20)]))}
print("named", named)

W = {"n_obs": int(len(wd)), "n_dir": int(dirn.sum()), "n_calm": int(calm.sum()), "n_var": int(var.sum()), "n_none": int((~valid).sum()),
     "n_force": int(np.isfinite(ws).sum()), "agree": agree, "belts": belts, "belt_corr": float(cor), "named": named, "cell": CELL, "min_obs": MIN_OBS,
     "grid_cells": {k: len(v) for k, v in grids.items()}}
jsave(W, f"{WORK}/winds.json")
jsave({k: [[c["lon"], c["lat"], c["from"], c["steady"], c["n"], c["force"], c["calm_var"], c["diff"]] for c in v] for k, v in grids.items()}, f"{DATA}/wind_arrows.json")
jsave(grids, f"{WORK}/wind_grids.json")
with open(f"{DATA}/wind_grid.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["season", "lon_centre", "lat_centre", "observations", "mean_direction_from_deg", "steadiness", "mean_force_ms",
                                   "share_calm_or_variable", "ncep_u_ms", "ncep_v_ms", "angle_to_ncep_deg"]); w.writerows(rows)
with open(f"{DATA}/wind_belts.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["ocean", "lat_from", "lat_to", "observations", "share_easterly", "mean_unit_u", "mean_unit_v", "share_calm_or_variable",
                                   "ncep_mean_u_ms", "ncep_mean_unit_u", "mean_force_ms"]); w.writerows(brow)
