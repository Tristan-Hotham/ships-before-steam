"""Step 2. Ports, voyages, durations and the great sailing routes.

  * Every kept position is labelled with the named port or anchorage it lies in (code/ports.py), if any.
  * VISITS are runs of positions at one place; a LEG is the time from the last position at one place to the first
    position at the next different place on the same ship track, provided the log is never silent for more than
    LEG_GAP days in between. Island ports of call (Madeira, the Canaries, Cape Verde, St Helena, Ascension) are passed
    over, so a leg runs between the places ships sailed from and to. Legs give the busiest routes by nation (both
    directions counted together).
  * VOYAGES for durations (for example the Netherlands to Batavia) run from the last position in the home port to
    the first position at the destination, with calls on the way allowed (Atlantic islands, the Cape, Rio, Iberian
    ports, Mauritius) but no return home, no other destination first and no silence longer than VOY_GAP days.
  * Latitude and meridian CROSSINGS (interpolated between daily positions) describe the routes: where ships between
    Europe and the South Atlantic crossed 20 and 30 degrees N going out and coming home (the volta do mar), where they
    crossed the equator, and how far south eastbound ships crossed the Indian Ocean (the Brouwer route).
Outputs: WORK/routes.json; data/routes.csv, data/voyage_durations.csv, data/crossings.csv.
Run: python3 code/02_routes.py
"""
import os, sys, csv, datetime as dt
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from ports import PORTS, MERGE, HOME

LEG_GAP, VOY_GAP, VOY_MAX = 30, 45, 420
CALLS = {"madeira", "canaries", "capeverde", "sthelena", "ascension"}   # ports of call on the way, not route ends
ON_THE_WAY = CALLS | {"cape", "rio", "coruna", "cadiz", "lisbon", "mauritius", "puertorico", "home"}   # calls allowed inside a voyage
O = dict(np.load(f"{WORK}/obs.npz"))
T = jload(f"{WORK}/tracks.json"); P = jload(f"{WORK}/passages.json")
lon, lat, t, tr, pa = O["lon"], O["lat"], O["t"], O["track"], O["passage"]
N = len(t)

# ---------- port labels ----------
keys = list(PORTS)
lab = np.full(N, -1)
for k_i, k in enumerate(keys):
    _, kind, g = PORTS[k]
    if kind == "box":
        m = (lon >= g[0]) & (lon <= g[2]) & (lat >= g[1]) & (lat <= g[3])
    else:
        x0, y0, r = g
        m = ((lat - y0) ** 2 + ((lon - x0) * np.cos(np.radians(y0))) ** 2) <= r * r
    lab[m & (lab < 0)] = k_i
mk = np.array([keys.index(MERGE.get(k, k)) for k in keys])
labm = np.where(lab >= 0, mk[np.maximum(lab, 0)], -1)
print("positions at a named place:", (labm >= 0).sum(), "of", N)

# ---------- per track: visits and legs ----------
legs = []        # (track, a, b, tA, tB)
order = np.lexsort((t, tr))
starts = np.searchsorted(tr[order], np.arange(len(T)))
ends = np.searchsorted(tr[order], np.arange(len(T)), side="right")
track_idx = {}
for ti in range(len(T)):
    idx = order[starts[ti]:ends[ti]]
    if not len(idx):
        continue
    track_idx[ti] = idx
    L = labm[idx]; tt = t[idx]
    # visits
    vis = []
    for j in range(len(idx)):
        if L[j] < 0: continue
        if vis and vis[-1][0] == L[j] and not np.any((L[vis[-1][2] + 1:j] >= 0) & (L[vis[-1][2] + 1:j] != L[j])):
            vis[-1][2] = j          # still at the same place (positions in between at sea or unlabelled)
            if tt[j] - tt[vis[-1][1]] > 0: pass
        else:
            vis.append([L[j], j, j])
    T[ti]["_vis"] = vis
    vr = [x for x in vis if keys[x[0]] not in CALLS]          # islands where ships called on the way are not route ends
    for (a, ja0, ja1), (b, jb0, jb1) in zip(vr[:-1], vr[1:]):
        if a == b: continue
        seg = tt[ja1:jb0 + 1]
        if len(seg) < 2 or np.diff(seg).max() > LEG_GAP: continue
        if tt[jb0] - tt[ja1] < 1: continue
        legs.append((ti, keys[a], keys[b], float(tt[ja1]), float(tt[jb0]), int(jb0 - ja1 + 1)))
print("legs", len(legs))

# busiest routes by nation (both directions together)
route_n = {}
for ti, a, b, ta, tb, n in legs:
    nat = T[ti]["nat"]; key = tuple(sorted((a, b)))
    d = route_n.setdefault(key, {"n": 0, "by": {}, "days": [], "ab": 0, "ba": 0})
    d["n"] += 1; d["by"][nat] = d["by"].get(nat, 0) + 1; d["days"].append(tb - ta)
    d["ab" if (a, b) == key else "ba"] += 1
routes = []
for (a, b), d in route_n.items():
    lead = max(d["by"].items(), key=lambda x: x[1])
    routes.append({"a": a, "b": b, "a_label": PORTS[a][0], "b_label": PORTS[b][0], "n": d["n"], "a_to_b": d["ab"], "b_to_a": d["ba"],
                   "by": d["by"], "lead": lead[0], "median_days": float(np.median(d["days"]))})
routes.sort(key=lambda r: -r["n"])
for r in routes[:25]:
    print(f"{r['n']:4d} {r['a_label'][:28]:28s} {r['b_label'][:28]:28s} {r['by']} {r['median_days']:.0f}d")
by_nation_routes = {}
for nat in NAT_LAB:
    rr = sorted([r for r in routes if r["by"].get(nat)], key=lambda r: -r["by"][nat])[:6]
    by_nation_routes[nat] = [{"a": r["a"], "b": r["b"], "a_label": r["a_label"], "b_label": r["b_label"], "n": r["by"][nat]} for r in rr]
    print(nat, [(r["a"], r["b"], r["n"]) for r in by_nation_routes[nat]])

# ---------- voyages with calls allowed: durations ----------
def voyages(origins, dests, nats=None, groups=None):
    out = []
    for ti, idx in track_idx.items():
        if nats and T[ti]["nat"] not in nats: continue
        if groups and T[ti]["group"] not in groups: continue
        vis = T[ti]["_vis"]; tt = t[idx]
        for i, (a, ja0, ja1) in enumerate(vis):
            if keys[a] not in origins: continue
            for b, jb0, jb1 in vis[i + 1:]:
                kb = keys[b]
                if kb in origins and kb not in dests:
                    break                     # back home first
                if kb not in dests and kb not in ON_THE_WAY:
                    break                     # went somewhere else first (for example Batavia before the Cape)
                if kb in dests:
                    seg = tt[ja1:jb0 + 1]
                    dur = tt[jb0] - tt[ja1]
                    if len(seg) >= 2 and np.diff(seg).max() <= VOY_GAP and 1 <= dur <= VOY_MAX:
                        calls = [PORTS[keys[c]][0] for c, _, _ in vis[i + 1:] if c != a and c != b][:0]
                        via = sorted({keys[c] for c, j0, _ in vis[i + 1:] if ja1 < j0 < jb0})
                        out.append({"track": ti, "ship": T[ti]["ship"], "nat": T[ti]["nat"], "group": T[ti]["group"], "company": T[ti]["company"],
                                    "from": keys[a], "to": kb, "depart": dt.date.fromordinal(int(tt[ja1])).isoformat(),
                                    "arrive": dt.date.fromordinal(int(tt[jb0])).isoformat(), "year": dt.date.fromordinal(int(tt[ja1])).year,
                                    "days": round(float(dur), 1), "via": via, "max_gap": float(np.diff(seg).max())})
                    break
    return out


SPAIN = {"cadiz", "coruna"}
VOY = {
    "nl_batavia": ("Home waters to Batavia", {"home"}, {"batavia"}, {"dutch"}),
    "batavia_nl": ("Batavia to home waters", {"batavia"}, {"home"}, {"dutch"}),
    "nl_cape": ("Home waters to the Cape", {"home"}, {"cape"}, {"dutch"}),
    "cape_batavia": ("Cape to Batavia", {"cape"}, {"batavia"}, {"dutch"}),
    "channel_india": ("Home waters to India (Bombay, Madras, Bengal)", {"home"}, {"bombay", "madras", "bengal"}, {"british"}),
    "india_channel": ("India to home waters", {"bombay", "madras", "bengal"}, {"home"}, {"british"}),
    "channel_caribbean": ("Home waters to the Caribbean", {"home"}, {"barbados", "antigua", "jamaica"}, {"british"}),
    "caribbean_channel": ("Caribbean to home waters", {"barbados", "antigua", "jamaica"}, {"home"}, {"british"}),
    "channel_namerica": ("Home waters to Halifax and New York", {"home"}, {"halifax", "newyork"}, {"british"}),
    "spain_havana": ("Cádiz or La Coruña to Havana", SPAIN, {"havana"}, {"spanish"}),
    "havana_spain": ("Havana to Cádiz or La Coruña", {"havana"}, SPAIN, {"spanish"}),
    "spain_plate": ("Cádiz or La Coruña to the River Plate", SPAIN, {"plate"}, {"spanish"}),
    "plate_spain": ("River Plate to Cádiz or La Coruña", {"plate"}, SPAIN, {"spanish"}),
    "spain_puertorico": ("Cádiz or La Coruña to Puerto Rico", SPAIN, {"puertorico"}, {"spanish"}),
    "nl_suriname": ("Home waters to Suriname", {"home"}, {"suriname"}, {"dutch"}),
}
dur = {}
allv = []
for k, (label, a, b, nats) in VOY.items():
    v = voyages(a, b, nats)
    d = np.array([x["days"] for x in v])
    rec = {"label": label, "n": len(v)}
    if len(v):
        yrs = np.array([x["year"] for x in v])
        rec.update({"median": float(np.median(d)), "q1": float(np.percentile(d, 25)), "q3": float(np.percentile(d, 75)),
                    "min": float(d.min()), "max": float(d.max()), "first_year": int(yrs.min()), "last_year": int(yrs.max())})
        fast = v[int(np.argmin(d))]; rec["fastest"] = {"ship": fast["ship"], "days": fast["days"], "year": fast["year"]}
        rec["by_decade"] = {str(dd): {"n": int((yrs // 10 * 10 == dd).sum()), "median": float(np.median(d[yrs // 10 * 10 == dd]))} for dd in sorted(set((yrs // 10 * 10).tolist()))}
        calls_cape = np.array(["cape" in x["via"] for x in v])
        rec["n_via_cape"] = int(calls_cape.sum())
        for era, lo, hi in (("pre1820", 0, 1819), ("post1820", 1820, 9999)):
            m = (yrs >= lo) & (yrs <= hi)
            rec[f"n_{era}"] = int(m.sum()); rec[f"median_{era}"] = float(np.median(d[m])) if m.sum() else None
        via = {}
        for x in v:
            for c in x["via"]: via[c] = via.get(c, 0) + 1
        rec["via"] = dict(sorted(via.items(), key=lambda z: -z[1])[:5])
    dur[k] = rec
    for x in v: x["route"] = k
    allv += v
    print(f"{k:18s} n={rec['n']:3d} median={rec.get('median', 0):6.1f} pre1820={rec.get('median_pre1820')} post1820={rec.get('median_post1820')} n_pre={rec.get('n_pre1820')} via={rec.get('via')}")

# ---------- crossings ----------
def crossings_lat(L, lonmin, lonmax):
    """All crossings of latitude L by consecutive daily positions within a passage: (passage, lon at crossing, +1 north / -1 south, t)."""
    same = pa[1:] == pa[:-1]
    a, b = lat[:-1], lat[1:]
    m = same & (((a < L) & (b >= L)) | ((a >= L) & (b < L))) & (np.abs(lon[1:] - lon[:-1]) < 30)
    i = np.where(m)[0]
    f = (L - lat[i]) / (lat[i + 1] - lat[i])
    x = lon[i] + f * (lon[i + 1] - lon[i])
    s = np.sign(lat[i + 1] - lat[i])
    k = (x >= lonmin) & (x <= lonmax)
    return pa[i][k], x[k], s[k], t[i][k]


def crossings_lon(X, latmin, latmax):
    same = pa[1:] == pa[:-1]
    a, b = lon[:-1], lon[1:]
    m = same & (((a < X) & (b >= X)) | ((a >= X) & (b < X))) & (np.abs(b - a) < 30)
    i = np.where(m)[0]
    f = (X - lon[i]) / (lon[i + 1] - lon[i])
    y = lat[i] + f * (lat[i + 1] - lat[i])
    s = np.sign(lon[i + 1] - lon[i])
    k = (y >= latmin) & (y <= latmax)
    return pa[i][k], y[k], s[k], t[i][k]


# passages between Europe and the South Atlantic: a position north of 36 N in the eastern Atlantic and one south of 5 S
pmaxlat = np.full(len(P), -99.0); pminlat = np.full(len(P), 99.0)
np.maximum.at(pmaxlat, pa, np.where((lon > -30) & (lon < 15), lat, -99))
np.minimum.at(pminlat, pa, np.where((lon > -60) & (lon < 30), lat, 99))
euro_south = (pmaxlat > 36) & (pminlat < -5)
print("Europe and South Atlantic passages:", euro_south.sum())
volta = {}
cross_rows = []
for L in (30, 20, 0):
    pp, x, s, tt = crossings_lat(L, -60, 0)
    k = euro_south[pp]
    rec = {}
    for dirn, sv in (("out", -1), ("home", 1)):
        m = k & (s == sv)
        xs = x[m]
        rec[dirn] = {"n": int(m.sum()), "median_lon": float(np.median(xs)), "q1": float(np.percentile(xs, 25)), "q3": float(np.percentile(xs, 75))}
        for pi_, xx in zip(pp[m], xs):
            cross_rows.append({"kind": f"lat{L}", "dir": dirn, "passage": int(pi_), "nat": T[P[pi_]["track"]]["nat"], "value": round(float(xx), 2)})
    volta[str(L)] = rec
    print(f"lat {L}: out median lon {rec['out']['median_lon']:.1f} (n {rec['out']['n']}); home {rec['home']['median_lon']:.1f} (n {rec['home']['n']})")
# Home-bound ships passing near the Azores (crossing 38 N between 35 W and 20 W) versus outbound
pp, x, s, tt = crossings_lat(38, -60, 0)
k = euro_south[pp]
az = {d: {"n": int((k & (s == sv)).sum()), "azores": int((k & (s == sv) & (x > -35) & (x < -20)).sum()), "median_lon": float(np.median(x[k & (s == sv)]))}
      for d, sv in (("out", -1), ("home", 1))}
for d in az: az[d]["share"] = az[d]["azores"] / az[d]["n"]
volta["azores38"] = az
print("38N azores", az)

# Brouwer route: eastbound crossings of 75 E south of the equator, by nation; and where Dutch ships bound for Java crossed
brouwer = {}
for X in (40, 60, 75, 90):
    pp, y, s, tt = crossings_lon(X, -60, 0)
    m = s > 0
    rec = {}
    for nat in ("dutch", "british", "french", "spanish"):
        mm = m & np.array([T[P[q]["track"]]["nat"] == nat for q in pp])
        if mm.sum() >= 5:
            rec[nat] = {"n": int(mm.sum()), "median_lat": float(np.median(y[mm])), "share_south30": float((y[mm] < -30).mean()),
                        "share_south35": float((y[mm] < -35).mean())}
            for q, yy in zip(pp[mm], y[mm]):
                cross_rows.append({"kind": f"lon{X}E", "dir": "east", "passage": int(q), "nat": nat, "value": round(float(yy), 2)})
    brouwer[str(X)] = rec
    print("lon", X, {k: (v["n"], round(v["median_lat"], 1), round(v["share_south30"], 2)) for k, v in rec.items()})

# Dutch voyages Netherlands to Batavia: how far south did they run their easting (minimum latitude between the Cape and Java)?
nlb = [v for v in allv if v["route"] in ("nl_batavia", "cape_batavia")]
south = []
for v in nlb:
    idx = track_idx[v["track"]]
    t0 = dt.date.fromisoformat(v["depart"]).toordinal(); t1 = dt.date.fromisoformat(v["arrive"]).toordinal() + 1
    m = (t[idx] >= t0) & (t[idx] <= t1) & (lon[idx] > 30) & (lon[idx] < 100)
    if m.sum() >= 5:
        south.append(float(lat[idx][m].min()))
south = np.array(south)
brouwer["dutch_java_minlat"] = {"n": int(len(south)), "median": float(np.median(south)), "share_south35": float((south < -35).mean()),
                               "share_south30": float((south < -30).mean())}
print("Dutch to Java: southernmost latitude in Indian Ocean", brouwer["dutch_java_minlat"])

jsave({"legs": len(legs), "routes": routes, "by_nation_routes": by_nation_routes, "durations": dur, "volta": volta, "brouwer": brouwer,
       "n_at_port": int((labm >= 0).sum())}, f"{WORK}/routes.json")
np.save(f"{WORK}/portlab.npy", labm)

# ---------- clean data files ----------
with open(f"{DATA}/routes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["place_a", "place_b", "legs", "a_to_b", "b_to_a", "british", "dutch", "spanish", "french", "other", "median_days"])
    for r in routes:
        w.writerow([r["a_label"], r["b_label"], r["n"], r["a_to_b"], r["b_to_a"]] + [r["by"].get(k, 0) for k in NAT_LAB] + [round(r["median_days"], 1)])
with open(f"{DATA}/voyage_durations.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["route", "ship", "nation", "operator", "company", "from", "to", "depart", "arrive", "days", "calls_on_the_way"])
    for v in sorted(allv, key=lambda v: (v["route"], v["depart"])):
        w.writerow([VOY[v["route"]][0], v["ship"], NAT_SHORT[v["nat"]], GROUP_LAB[v["group"]], v["company"], PORTS[v["from"]][0], PORTS[v["to"]][0],
                    v["depart"], v["arrive"], v["days"], "; ".join(PORTS[c][0] for c in v["via"])])
with open(f"{DATA}/crossings.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["line", "direction", "passage_id", "nation", "crossing_at_degrees"])
    for r in cross_rows:
        w.writerow([r["kind"], r["dir"], r["passage"], NAT_SHORT[r["nat"]], r["value"]])
jsave(allv, f"{WORK}/voyages.json")
