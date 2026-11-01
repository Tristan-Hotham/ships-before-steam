"""Step 5. Collect every number used anywhere into data/results.json, write the clean data tables, and the page data.
Outputs: data/results.json, data/logbooks.csv, data/passages.csv, data/coverage_by_decade.csv, data/passages.geojson,
data/voyages.json and data/site.json (page).
Run: python3 code/05_results.py
"""
import os, sys, csv, datetime as dt, collections as C
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from ports import PORTS

T = jload(f"{WORK}/tracks.json"); P = jload(f"{WORK}/passages.json"); S1 = jload(f"{WORK}/stats01.json")
RT = jload(f"{WORK}/routes.json"); W = jload(f"{WORK}/winds.json"); M = jload(f"{WORK}/modern.json"); V = jload(f"{WORK}/voyages.json")
O = dict(np.load(f"{WORK}/obs.npz")); LAB = np.load(f"{WORK}/portlab.npy")
keys = list(PORTS)
natk = list(NAT_LAB)
lon, lat, t, tr, pa, yr = O["lon"], O["lat"], O["t"], O["track"], O["passage"], O["year"]
R = {}

# ---------- the record ----------
R["n_tracks"] = len([x for x in T if x["n_obs"]]); R["n_features"] = S1["features"]
R["n_logbook_ids"] = len({x["id"] for x in T})
R["n_passages"] = len(P); R["n_obs"] = int(len(t)); R["n_obs_raw"] = S1["obs_raw"]
R["clean"] = {"spikes": S1["spikes"], "dup_days": S1["dup_days"], "short_dropped": S1["short_dropped"], "multi_joined": S1["multi_joined"]}
R["year_min"] = int(yr.min()); R["year_max"] = int(yr.max())
R["share_obs_1750_1854"] = float(((yr >= 1750) & (yr <= 1854)).mean())
R["n_obs_before_1750"] = int((yr < 1750).sum()); R["n_obs_after_1850"] = int((yr > 1850).sum())
km = sum(p["km"] for p in P); R["km_total"] = km; R["times_round_earth"] = km / 40075
R["median_passage_days"] = float(np.median([p["days"] for p in P]))
R["median_daily_km"] = float(np.median(hav(lon[:-1], lat[:-1], lon[1:], lat[1:])[(pa[1:] == pa[:-1]) & (np.diff(t) <= 1.5) & (np.diff(t) >= .5)]))

# nations
nat_obs = C.Counter(T[i]["nat"] for i in tr.tolist())
R["nation"] = {}
for k in natk:
    tt = [x for x in T if x["nat"] == k and x["n_obs"]]
    pp = [p for p in P if T[p["track"]]["nat"] == k]
    ys = [p["year"] for p in pp]
    dec = C.Counter(p["decade"] for p in pp)
    R["nation"][k] = {"label": NAT_LAB[k], "tracks": len(tt), "passages": len(pp), "obs": nat_obs[k], "share_obs": nat_obs[k] / len(t),
                      "first_year": min(ys), "last_year": max(ys), "peak_decade": max(dec.items(), key=lambda z: z[1])[0]}
R["nation_order"] = natk
R["n_other_tracks"] = R["nation"]["other"]["tracks"]
R["share_obs_big3"] = sum(R["nation"][k]["share_obs"] for k in ("british", "dutch", "spanish"))

# coverage by decade (passages by their first day; observation days by their own date)
decs = list(range(1750, 1860, 10))
cov = []
for d in decs:
    row = {"decade": d, "passages": {}, "obs": {}}
    for k in natk:
        row["passages"][k] = sum(1 for p in P if p["decade"] == d and T[p["track"]]["nat"] == k)
        row["obs"][k] = int(((yr // 10 * 10) == d)[np.array([T[i]["nat"] == k for i in range(len(T))])[tr]].sum())
    row["total_passages"] = sum(row["passages"].values()); row["total_obs"] = sum(row["obs"].values())
    cov.append(row)
R["coverage"] = cov
R["n_passages_before_1750"] = sum(1 for p in P if p["year"] < 1750)
best = max(cov, key=lambda r: r["total_obs"]); R["busiest_decade"] = {"decade": best["decade"], "obs": best["total_obs"]}
low = min([r for r in cov if r["decade"] < 1850], key=lambda r: r["total_obs"]); R["thinnest_decade"] = {"decade": low["decade"], "obs": low["total_obs"]}
sp = {r["decade"]: r["obs"]["spanish"] for r in cov}
R["spanish_1760_1799_share"] = sum(sp[d] for d in (1760, 1770, 1780, 1790)) / R["nation"]["spanish"]["obs"]
du = {r["decade"]: r["obs"]["dutch"] for r in cov}
R["dutch_1820_share"] = sum(du[d] for d in (1820, 1830, 1840, 1850)) / R["nation"]["dutch"]["obs"]
br = {r["decade"]: r["obs"]["british"] for r in cov}
R["british_pre1800_share"] = sum(br[d] for d in decs if d < 1800) / R["nation"]["british"]["obs"]
R["british_after_1830_obs"] = sum(br[d] for d in decs if d >= 1830)
R["french_tracks"] = R["nation"]["french"]["tracks"]

# operators and archives
g = C.Counter(x["group"] for x in T if x["n_obs"])
R["groups"] = {k: g.get(k, 0) for k, _ in GROUPS}
cc = C.Counter(x["company"] for x in T if x["n_obs"] and x["company"])
R["companies"] = [{"code": k, "label": COMPANY_LAB.get(k, k.title()), "tracks": n} for k, n in cc.most_common()]
R["company_n"] = {k: cc.get(k, 0) for k in ("RN", "EIC", "VOC", "MAR", "ADM", "MCC", "WHA", "HUDSON BAY COMPANY")}
R["company_n"]["RN_all"] = cc.get("RN", 0) + cc.get("ROYAL NAVY", 0)
R["company_n"]["VOC_all"] = cc.get("VOC", 0) + cc.get("VOC-Z", 0)
R["navy_share"] = g["navy"] / R["n_tracks"]
ar = C.Counter(x["archive"] for x in T if x["n_obs"] and x["archive"])
ARCH = {"NATIONAL MARITIME MUSEUM": "National Maritime Museum, Greenwich", "NATIONAAL ARCHIEF OF THE NETHERLANDS": "Nationaal Archief, The Hague",
        "KONINKLIJK NEDERLANDS METEOROLOGISCH INSTITUUT": "KNMI (Royal Netherlands Meteorological Institute), De Bilt",
        "ARCHIVO GENERAL DE INDIAS": "Archivo General de Indias, Seville", "ARCHIVO DEL MUSEO NAVAL MADRID": "Archivo del Museo Naval, Madrid",
        "BRITISH LIBRARY": "British Library, London", "CENTRE D'ACCUEIL ET DE RECHERCHE DES ARCH. NATION.": "Archives nationales, Paris",
        "RIJKSARCHIEF ZEELAND": "Zeeuws Archief, Middelburg", "PUBLIC RECORD OFFICE": "Public Record Office (The National Archives), London"}
R["archives"] = [{"name": ARCH.get(k, k.title()), "tracks": n} for k, n in ar.most_common(9)]
R["n_archives"] = len(ar)
stm = [x for x in T if any(k in x["type"].upper() for k in ("STOOM", "STEAM"))]
R["steam"] = {"tracks": len(stm), "first_year": min(dt.date.fromordinal(int(x["t0"])).year for x in stm), "ships": sorted({x["ship"].title() for x in stm})}

# where: oceans (rough boxes) and extremes
def share(m): return float(m.mean())
R["where"] = {"atlantic": share((lon > -100) & (lon < 20) & ~((lat > 30) & (lon > -6))), "indian": share((lon >= 20) & (lon < 120) & (lat < 31)),
              "pacific": share((lon >= 120) | (lon <= -70) & ~((lon > -100) & (lat > 8))),
              "south_lat": float(lat.min()), "north_lat": float(lat.max())}
iS = int(np.argmin(lat)); iN = int(np.argmax(lat))
R["southmost"] = {"ship": T[int(tr[iS])]["ship"].title(), "date": dt.date.fromordinal(int(t[iS])).isoformat(), "lat": float(lat[iS]), "year": int(yr[iS])}
R["northmost"] = {"ship": T[int(tr[iN])]["ship"].title(), "date": dt.date.fromordinal(int(t[iN])).isoformat(), "lat": float(lat[iN]), "year": int(yr[iN]),
                  "nat": T[int(tr[iN])]["nat"], "company": T[int(tr[iN])]["company_label"]}

# famous voyages present in the record
def track_of(name, y0, y1=None):
    for x in T:
        if x["ship"] == name and x["t0"] and dt.date.fromordinal(int(x["t0"])).year >= y0 and dt.date.fromordinal(int(x["t0"])).year <= (y1 or y0):
            return x
FAM = {"endeavour": ("ENDEAVOUR", 1768, None, "Cook's first voyage"), "resolution": ("RESOLUTION", 1772, None, "Cook's second voyage"),
       "boussole": ("LA BOUSSOLE", 1785, None, "La Pérouse's expedition")}
R["famous"] = {}
for k, (nm, y0, y1, what) in FAM.items():
    x = track_of(nm, y0, y1)
    m = tr == x["i"]
    R["famous"][k] = {"track": x["i"], "ship": nm.title(), "what": what, "obs": int(m.sum()), "start": dt.date.fromordinal(int(t[m].min())).isoformat(),
                      "end": dt.date.fromordinal(int(t[m].max())).isoformat(), "min_lat": float(lat[m].min()), "year": dt.date.fromordinal(int(t[m].min())).year}
R["famous"]["resolution"]["min_lat_date"] = dt.date.fromordinal(int(t[tr == R["famous"]["resolution"]["track"]][np.argmin(lat[tr == R["famous"]["resolution"]["track"]])])).isoformat()
mal = [x for x in T if x["ship"] in ("ATREVIDA Y DESCUBIERTA", "LA DESCUBIERTA Y ATREVIDA", "LA ATREVIDA") or (x["ship"] == "LA DESCUBIERTA" and x["t0"] and dt.date.fromordinal(int(x["t0"])).year < 1800)]
R["famous"]["malaspina"] = {"tracks": [x["i"] for x in mal], "n": len(mal), "obs": int(np.isin(tr, [x["i"] for x in mal]).sum())}

# ---------- routes, durations, crossings ----------
R["legs"] = RT["legs"]
R["routes_top"] = [{"a": r["a"], "b": r["b"], "a_label": r["a_label"], "b_label": r["b_label"], "n": r["n"], "by": r["by"], "lead": r["lead"],
                    "median_days": r["median_days"]} for r in RT["routes"][:12]]
R["routes_by_nation"] = RT["by_nation_routes"]
R["dur"] = RT["durations"]
R["volta"] = RT["volta"]
R["brouwer"] = RT["brouwer"]
R["volta_shift_30"] = R["volta"]["30"]["out"]["median_lon"] - R["volta"]["30"]["home"]["median_lon"]
R["volta_shift_30_km"] = float(hav(R["volta"]["30"]["home"]["median_lon"], 30, R["volta"]["30"]["out"]["median_lon"], 30))
R["volta_shift_20"] = R["volta"]["20"]["out"]["median_lon"] - R["volta"]["20"]["home"]["median_lon"]
R["euro_south_n"] = R["volta"]["30"]["out"]["n"] + R["volta"]["30"]["home"]["n"]
db = R["dur"]["nl_batavia"]
R["nlb_speedup"] = 1 - db["median_post1820"] / db["median_pre1820"]
R["nlb_share_cape"] = db["n_via_cape"] / db["n"]
R["cape_batavia_speedup"] = 1 - R["dur"]["cape_batavia"]["median_post1820"] / R["dur"]["cape_batavia"]["median_pre1820"]

# ---------- winds ----------
R["wind"] = {k: W[k] for k in ("n_obs", "n_dir", "n_calm", "n_var", "n_none", "n_force", "agree", "belt_corr", "named", "cell", "min_obs", "grid_cells")}
R["wind"]["share_dir"] = W["n_dir"] / W["n_obs"]
R["wind"]["belts"] = W["belts"]
atl = {r["lat0"]: r for r in W["belts"]["atlantic"]}; ind = {r["lat0"]: r for r in W["belts"]["indian"]}
R["wind"]["atl_east_15"] = atl[15]["east_share"]; R["wind"]["atl_east_m15"] = atl[-15]["east_share"]
R["wind"]["ind_west_m40"] = 1 - ind[-40]["east_share"]
R["wind"]["atl_force_0"] = atl[0]["force"]; R["wind"]["ind_force_m40"] = ind[-40]["force"]
R["wind"]["calm_ratio"] = W["named"]["doldrums"]["calm_var"] / W["named"]["doldrums"]["calm_var_trades"]
# where easterlies give way to westerlies (first band poleward of the trades with a mean west-to-east component)
def flip(rows, south):
    rows = sorted(rows, key=lambda r: -r["lat0"] if south else r["lat0"])
    seen_e = False
    for r in rows:
        if (r["lat0"] < 0) != south: continue
        if r["u"] < 0: seen_e = True
        elif seen_e: return r["lat0"] if not south else r["lat1"]
R["wind"]["flip_n_atl"] = flip(W["belts"]["atlantic"], False); R["wind"]["flip_s_atl"] = flip(W["belts"]["atlantic"], True)
R["wind"]["flip_s_ind"] = flip(W["belts"]["indian"], True)
nb = [r for o in W["belts"].values() for r in o]
R["wind"]["n_belts"] = len(nb)
R["wind"]["sign_agree"] = sum(1 for r in nb if np.sign(r["u"]) == np.sign(r["ncep_unit_u"])) / len(nb)

# ---------- modern ----------
R["modern"] = M
R["modern"]["south_indian_ratio"] = M["region"]["south_indian"]["sail_share"] / max(M["region"]["south_indian"]["ais_share"], 1e-9)

# histograms for the page and figures (from data/crossings.csv)
rows = list(csv.DictReader(open(f"{DATA}/crossings.csv", encoding="utf-8")))
def hist(line, dirn=None, nat=None, lo=-60, hi=0, step=5):
    v = [float(r["crossing_at_degrees"]) for r in rows if r["line"] == line and (dirn is None or r["direction"] == dirn) and (nat is None or r["nation"] == nat)]
    h, e = np.histogram(v, bins=np.arange(lo, hi + step, step))
    return {"lo": lo, "step": step, "n": h.tolist(), "total": len(v)}
R["hist"] = {"lat30_out": hist("lat30", "out"), "lat30_home": hist("lat30", "home"),
             "lat0_out": hist("lat0", "out", lo=-45, hi=10), "lat0_home": hist("lat0", "home", lo=-45, hi=10),
             "lon75_dutch": hist("lon75E", nat="Dutch", lo=-50, hi=0, step=2.5), "lon75_british": hist("lon75E", nat="British", lo=-50, hi=0, step=2.5)}
R["ports_n"] = len(PORTS)
MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
dlong = lambda iso: f"{int(iso[8:10])} {MON[int(iso[5:7]) - 1]} {iso[:4]}"
R["famous"]["resolution"]["min_lat_day"] = dlong(R["famous"]["resolution"]["min_lat_date"])
R["northmost"]["day"] = dlong(R["northmost"]["date"])
cur = sorted(dt.date.fromordinal(int(x["t0"])).year for x in T if x["ship"] == "CURACAO" and x["t0"])
R["steam"]["curacao_year"] = cur[0]
R["retrieved"] = "2026"
jsave(R, f"{DATA}/results.json", indent=1)

# ---------- clean data ----------
with open(f"{DATA}/logbooks.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["record", "cliwoc_logbook_id", "ship", "nation", "nationality_as_recorded", "operator_group", "company_code", "company", "ship_type",
                "voyage_from_as_recorded", "voyage_to_as_recorded", "archive", "archive_country", "first_day", "last_day", "positions"])
    for x in T:
        if not x["n_obs"]: continue
        w.writerow([x["i"], x["id"], x["ship"], NAT_SHORT[x["nat"]], x["nat_raw"], GROUP_LAB[x["group"]], x["company"], x["company_label"], x["type"],
                    x["from"], x["to"], x["archive"], x["archive_country"], dt.date.fromordinal(int(x["t0"])).isoformat(), dt.date.fromordinal(int(x["t1"])).isoformat(), x["n_obs"]])
first_idx = {}; last_idx = {}
for j, p_ in enumerate(pa.tolist()):
    first_idx.setdefault(p_, j); last_idx[p_] = j
place = lambda j: PORTS[keys[LAB[j]]][0] if LAB[j] >= 0 else ""
with open(f"{DATA}/passages.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["passage", "record", "ship", "nation", "operator_group", "start", "end", "days", "positions", "km", "start_lon", "start_lat", "end_lon", "end_lat", "start_place", "end_place"])
    for p in P:
        x = T[p["track"]]
        w.writerow([p["i"], p["track"], x["ship"], NAT_SHORT[x["nat"]], GROUP_LAB[x["group"]], p["start"], p["end"], p["days"], p["n"], p["km"],
                    round(p["lon0"], 2), round(p["lat0"], 2), round(p["lon1"], 2), round(p["lat1"], 2), place(first_idx[p["i"]]), place(last_idx[p["i"]])])
with open(f"{DATA}/coverage_by_decade.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["decade"] + [f"passages_{k}" for k in natk] + [f"position_days_{k}" for k in natk])
    for r in cov:
        w.writerow([r["decade"]] + [r["passages"][k] for k in natk] + [r["obs"][k] for k in natk])

# GeoJSON of passages (daily positions, 2 decimals, longitudes unwrapped across 180 so lines do not jump)
def unwrap(lo):
    lo = np.array(lo, float)
    return lo[0] + np.concatenate([[0], np.cumsum(((np.diff(lo) + 180) % 360) - 180)])
feats = []
coords_by_p = {}
order = np.argsort(pa, kind="stable")
bounds = np.searchsorted(pa[order], np.arange(len(P) + 1))
for p in P:
    idx = order[bounds[p["i"]]:bounds[p["i"] + 1]]
    idx = idx[np.argsort(t[idx], kind="stable")]
    lo = unwrap(lon[idx]); la = lat[idx]
    coords_by_p[p["i"]] = (lo, la)
    x = T[p["track"]]
    feats.append({"type": "Feature", "properties": {"passage": p["i"], "ship": x["ship"], "nation": NAT_SHORT[x["nat"]], "operator": GROUP_LAB[x["group"]],
                                                    "company": x["company_label"], "start": p["start"], "end": p["end"], "days": p["days"]},
                  "geometry": {"type": "LineString", "coordinates": [[round(a, 2), round(b, 2)] for a, b in zip(lo, la)]}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/passages.geojson")

# ---------- page data ----------
dec_keys = ["pre"] + [str(d) for d in decs]
def dec_ix(y):
    return 0 if y < 1750 else min(len(decs), (y - 1750) // 10 + 1)
import string
cw = lambda v: string.capwords((v or "").lower()).replace(" Of ", " of ").replace(" De ", " de ").replace(" Del ", " del ")
gk = [k for k, _ in GROUPS]
tracks_out = [[cw(x["ship"]), natk.index(x["nat"]), gk.index(x["group"]), x["company_label"], cw(x["type"]), cw(x["archive"]), x["id"],
               cw(x["from"]), cw(x["to"])] for x in T]

pas_out = []
for p in P:
    lo, la = coords_by_p[p["i"]]
    q = np.round(np.column_stack([lo, la]) * 10).astype(int)
    d = np.vstack([q[:1], np.diff(q, axis=0)]).ravel().tolist()
    pas_out.append([p["track"], p["start"], p["days"], p["km"], dec_ix(p["year"]), place(first_idx[p["i"]]), place(last_idx[p["i"]]), d])
jsave({"t": tracks_out, "p": pas_out}, f"{DATA}/voyages.json")
site = {"nations": [[k, NAT_SHORT[k], NAT_LAB[k], NAT_COL[k]] for k in natk], "groups": [[k, l] for k, l in GROUPS],
        "decades": dec_keys, "famous": {k: v.get("track", v.get("tracks")) for k, v in R["famous"].items()},
        "ports": {k: [v[0], v[1], v[2]] for k, v in PORTS.items()}}
jsave(site, f"{DATA}/site.json")
print("voyages.json", os.path.getsize(f"{DATA}/voyages.json") // 1024, "KB; passages.geojson", os.path.getsize(f"{DATA}/passages.geojson") // 1024, "KB")
print({k: (v["tracks"], v["passages"], v["obs"], round(v["share_obs"], 3), v["first_year"], v["last_year"]) for k, v in R["nation"].items()})
print("groups", R["groups"], "steam", R["steam"]["tracks"], R["steam"]["first_year"])
print("where", R["where"], R["southmost"], R["northmost"])
print("famous", R["famous"])
print("wind flips", R["wind"]["flip_n_atl"], R["wind"]["flip_s_atl"], R["wind"]["flip_s_ind"], "sign agree", R["wind"]["sign_agree"])
print("busiest decade", R["busiest_decade"], "thinnest", R["thinnest_decade"], "spanish 1760-99", R["spanish_1760_1799_share"], "dutch 1820+", R["dutch_1820_share"], "british pre1800", R["british_pre1800_share"])
print("km", km, R["times_round_earth"], "daily km", R["median_daily_km"])
