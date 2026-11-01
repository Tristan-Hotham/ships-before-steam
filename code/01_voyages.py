"""Step 1. Read the CLIWOC GeoJSON, rebuild each ship track as dated daily positions, clean it, and cut it into passages.

A feature in cliwoc1.json is one CLIWOC ship/logbook ID; it can hold several voyages and run for years. Here:
  * tracks split at the antimeridian by the GeoJSON's author are joined again (the inserted +-180 points are dropped);
  * observations are sorted by date; exact duplicate days are dropped;
  * single positions that jump away and back (more than 600 km from both neighbours while the neighbours are close)
    are treated as transcription slips and dropped (counted in results);
  * a track is cut into PASSAGES wherever the log is silent for more than 10 days or the next position implies more
    than 450 km a day (about 10 knots for 24 hours, faster than a sailing ship's daily run); passages with fewer than
    3 positions are dropped.
Outputs: WORK/obs.npz (every kept observation), WORK/tracks.json and WORK/passages.json, data/passages.csv.
Run: python3 code/01_voyages.py
"""
import os, sys, csv, datetime as dt
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

GAP_DAYS, MAX_KM_DAY, SPIKE_KM, MIN_PTS = 10, 450, 600, 3
src = jload(f"{CLIWOC}/cliwoc1.json")["features"]
P_ = lambda p, k: p.get(k)
K = {"nat": "Nationality of ship and crew", "c1": "Ship nationality", "ship": "Ship name", "type": "Type of ship; e.g. schooner, barque, frigate",
     "company": "Company", "from": "Place where the ship departed from", "to": "Place where the ship sailed to", "id": "ID of the logbook",
     "inst": "Institute name where the logbook is stored", "instc": "Institute country where the logbook is stored",
     "date": "Date and time (UTC)", "wd": "Wind direction (°)", "ws": "Wind speed (m/s)", "anch": "Anchored"}


def arr(p, k, n, cast):
    v = p.get(K[k])
    if not isinstance(v, list):
        v = [v] * n
    assert len(v) == n, (k, len(v), n)
    out = []
    for x in v:
        try:
            out.append(cast(x))
        except (TypeError, ValueError):
            out.append(np.nan)
    return np.array(out, float)


tracks, obs = [], {k: [] for k in ("track", "passage", "t", "lon", "lat", "wd", "ws", "anch", "month", "year")}
passages = []
stats = {"features": len(src), "multi_joined": 0, "dup_days": 0, "spikes": 0, "short_dropped": 0, "obs_raw": 0, "bad_date": 0}
for fi, f in enumerate(src):
    p = f["properties"]; g = f["geometry"]
    if g["type"] == "LineString":
        co = g["coordinates"]
    else:                       # rejoin parts cut at the antimeridian: drop the inserted +-180 end points
        stats["multi_joined"] += 1
        parts = g["coordinates"]; co = []
        for i, part in enumerate(parts):
            pp = list(part)
            if i > 0 and abs(pp[0][0]) == 180: pp = pp[1:]
            if i < len(parts) - 1 and abs(pp[-1][0]) == 180: pp = pp[:-1]
            co += pp
    dates = p[K["date"]]
    if not isinstance(dates, list):
        dates = [dates] * len(co)
    if len(dates) != len(co):
        # a crossing point at exactly +-180 can survive; fall back to dropping +-180 points that are not original
        co2 = [c for c in co if abs(c[0]) != 180]
        assert len(co2) == len(dates), (fi, len(co), len(co2), len(dates))
        co = co2
    n = len(co); stats["obs_raw"] += n
    lon = np.array([c[0] for c in co], float); lat = np.array([c[1] for c in co], float)
    t = []
    for s in dates:
        y, m, d = int(s[:4]), int(s[5:7]), int(s[8:10])
        h = 12 if s[11:] == "Unknown" else int(s[11:13])
        t.append(dt.datetime(y, m, d).toordinal() + h / 24)
    t = np.array(t)
    wd = arr(p, "wd", n, int); ws = arr(p, "ws", n, float); an = arr(p, "anch", n, int)
    o = np.argsort(t, kind="stable")
    lon, lat, t, wd, ws, an = lon[o], lat[o], t[o], wd[o], ws[o], an[o]
    keep = np.ones(n, bool)
    keep[1:] &= np.floor(t[1:]) != np.floor(t[:-1])            # one observation per calendar day (first of the day)
    stats["dup_days"] += int((~keep).sum())
    lon, lat, t, wd, ws, an = lon[keep], lat[keep], t[keep], wd[keep], ws[keep], an[keep]
    # spikes: a lone position far from both neighbours that are themselves close together
    while len(t) >= 3:
        d1 = hav(lon[:-2], lat[:-2], lon[1:-1], lat[1:-1]); d2 = hav(lon[1:-1], lat[1:-1], lon[2:], lat[2:]); d3 = hav(lon[:-2], lat[:-2], lon[2:], lat[2:])
        bad = np.where((d1 > SPIKE_KM) & (d2 > SPIKE_KM) & (d3 < 0.5 * np.minimum(d1, d2)))[0] + 1
        if not len(bad): break
        stats["spikes"] += len(bad)
        m = np.ones(len(t), bool); m[bad] = False
        lon, lat, t, wd, ws, an = lon[m], lat[m], t[m], wd[m], ws[m], an[m]
    nat_raw = p.get(K["nat"]) or {"NL": "DUTCH", "UK": "BRITISH", "ES": "SPANISH", "FR": "FRENCH"}.get(p.get(K["c1"]), None)
    nat = NAT_MAP.get(nat_raw, "other")
    comp = p.get(K["company"]); stype = p.get(K["type"])
    grp = group_of(nat_raw, comp, stype)
    ti = len(tracks)
    tracks.append({"i": ti, "id": p.get(K["id"]), "ship": (p.get(K["ship"]) or "Unnamed").strip(), "nat": nat, "nat_raw": nat_raw or "",
                   "company": comp or "", "company_label": COMPANY_LAB.get(comp, (comp or "").title()), "group": grp,
                   "type": (stype or "").strip(), "from": p.get(K["from"]) or "", "to": p.get(K["to"]) or "",
                   "archive": p.get(K["inst"]) or "", "archive_country": p.get(K["instc"]) or "",
                   "n_obs": int(len(t)), "t0": float(t[0]) if len(t) else None, "t1": float(t[-1]) if len(t) else None})
    if len(t) == 0:
        continue
    # passages
    gap = np.diff(t); step = hav(lon[:-1], lat[:-1], lon[1:], lat[1:])
    cut = np.where((gap > GAP_DAYS) | (step / np.maximum(gap, 1) > MAX_KM_DAY))[0] + 1
    for seg in np.split(np.arange(len(t)), cut):
        if len(seg) < MIN_PTS:
            stats["short_dropped"] += 1
            continue
        pi = len(passages)
        s = seg
        km = float(hav(lon[s][:-1], lat[s][:-1], lon[s][1:], lat[s][1:]).sum())
        d0 = dt.date.fromordinal(int(t[s[0]])); d1 = dt.date.fromordinal(int(t[s[-1]]))
        passages.append({"i": pi, "track": ti, "n": int(len(s)), "t0": float(t[s[0]]), "t1": float(t[s[-1]]),
                         "start": d0.isoformat(), "end": d1.isoformat(), "year": d0.year, "decade": d0.year // 10 * 10,
                         "days": int(t[s[-1]] - t[s[0]]), "km": round(km),
                         "lon0": float(lon[s[0]]), "lat0": float(lat[s[0]]), "lon1": float(lon[s[-1]]), "lat1": float(lat[s[-1]])})
        obs["track"] += [ti] * len(s); obs["passage"] += [pi] * len(s)
        obs["t"] += list(t[s]); obs["lon"] += list(lon[s]); obs["lat"] += list(lat[s]); obs["wd"] += list(wd[s]); obs["ws"] += list(ws[s])
        obs["anch"] += list(an[s])
        obs["month"] += [dt.date.fromordinal(int(x)).month for x in t[s]]; obs["year"] += [dt.date.fromordinal(int(x)).year for x in t[s]]

O = {k: np.array(v) for k, v in obs.items()}
np.savez_compressed(f"{WORK}/obs.npz", **O)
stats.update({"tracks": len(tracks), "passages": len(passages), "obs": int(len(O["t"]))})
jsave(tracks, f"{WORK}/tracks.json"); jsave(passages, f"{WORK}/passages.json"); jsave(stats, f"{WORK}/stats01.json", indent=1)
print(stats)
print("years", O["year"].min(), O["year"].max())
