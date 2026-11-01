"""Step 4. Where the logbook ships sailed, square by square, and a rough comparison with shipping today.

  * SAIL: each passage's daily positions are joined by straight lines (in longitude and latitude, densified to 0.2
    degree steps) and the distinct passages crossing each 2 degree square are counted, in total and by nation.
  * TODAY: the World Bank / IMF Global Shipping Traffic Density (AIS positions, 2015 to 2021). The file here is the
    0.08 degree overview, which samples single pixels of the full raster, so a pixel on its own says little; summed
    over the roughly 600 samples in a 2 degree square it is a fair index of AIS traffic there. Satellite and coastal
    receivers differ, so the index is a rough guide, not a measurement.
  * Comparison over sea squares that either record touches: rank correlation, the share of the sail record and of
    today's traffic in a few named regions, and how much of today's busiest tenth of squares no logbook ship crossed.
Outputs: WORK/modern.json; data/grid_2deg.csv; data/today_2deg.png (Web Mercator image for the page's layer).
Run: python3 code/04_modern.py
"""
import os, sys, csv, gzip, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

C = 2
NX, NY = 360 // C, 180 // C
O = dict(np.load(f"{WORK}/obs.npz")); T = jload(f"{WORK}/tracks.json"); P = jload(f"{WORK}/passages.json")
lon, lat, pa = O["lon"], O["lat"], O["passage"]
natk = list(NAT_LAB)
pnat = np.array([natk.index(T[p["track"]]["nat"]) for p in P])

# ---------- sail: distinct passages per square ----------
same = pa[1:] == pa[:-1]
i = np.where(same & (np.abs(lon[1:] - lon[:-1]) < 180))[0]
cells_by_nat = np.zeros((len(natk), NY * NX))
seen = set()
for j in i:
    a0, b0, a1, b1 = lon[j], lat[j], lon[j + 1], lat[j + 1]
    n = max(1, int(math.ceil(max(abs(a1 - a0), abs(b1 - b0)) / 0.2)))
    f = np.linspace(0, 1, n + 1)
    xs = a0 + (a1 - a0) * f; ys = b0 + (b1 - b0) * f
    cx = np.clip(((xs + 180) // C).astype(int), 0, NX - 1); cy = np.clip(((ys + 90) // C).astype(int), 0, NY - 1)
    p = int(pa[j])
    for c in set((cy * NX + cx).tolist()):
        if (p, c) not in seen:
            seen.add((p, c)); cells_by_nat[pnat[p], c] += 1
sail = cells_by_nat.sum(0)
print("squares crossed by a logbook ship:", int((sail > 0).sum()))

# ---------- today: AIS sums per square ----------
H, W = 2125, 4501
A = np.frombuffer(gzip.open(AIS).read(), dtype="<i4").reshape(H, W).astype(np.float64)
assert A.min() >= 0
dx, dy = 360 / W, 170 / H
alon = -180 + (np.arange(W) + .5) * dx
alat = 85 - (np.arange(H) + .5) * dy
ci = np.minimum(((alon + 180) // C).astype(int), NX - 1); ri = np.minimum(((alat + 90) // C).astype(int), NY - 1)
RI, CI = np.meshgrid(ri, ci, indexing="ij")
flat = (RI * NX + CI).ravel()
ais = np.bincount(flat, weights=A.ravel(), minlength=NX * NY)
ais_share = ais / ais.sum()
print("AIS squares with traffic:", int((ais > 0).sum()))

both = (sail > 0) | (ais > 0)
from scipy.stats import spearmanr
rho = float(spearmanr(sail[both], ais[both]).correlation)
top = ais >= np.quantile(ais[ais > 0], 0.9)
top_nosail = float(((sail == 0) & top).sum() / top.sum())
top_nosail_share = float(ais[(sail == 0) & top].sum() / ais[top].sum())
sail_share = sail / sail.sum()
cx_ = -180 + (np.arange(NY * NX) % NX) * C + C / 2; cy_ = -90 + (np.arange(NY * NX) // NX) * C + C / 2
REG = {"south_indian": ("Southern Indian Ocean, 35 to 50 S", (20, 115, -50, -35)),
       "red_sea": ("Red Sea and Gulf of Aden", (32, 52, 11, 30)),
       "malacca": ("Strait of Malacca and Singapore", (95, 105, -1, 8)),
       "north_pacific": ("North Pacific, 20 to 55 N", (-180, -120, 20, 56)),
       "south_atlantic_mid": ("South Atlantic, 0 to 40 S, 30 W to 5 E", (-30, 5, -40, 0)),
       "st_helena": ("St Helena and Ascension seas", (-20, 0, -20, -5))}
region = {}
for k, (labl, (x0, x1, y0, y1)) in REG.items():
    m = (cx_ > x0) & (cx_ < x1) & (cy_ > y0) & (cy_ < y1)
    region[k] = {"label": labl, "sail_share": float(sail_share[m].sum()), "ais_share": float(ais_share[m].sum())}
    print(f"{labl:40s} sail {100 * region[k]['sail_share']:5.1f}%  today {100 * region[k]['ais_share']:5.1f}%")
print("rho", round(rho, 3), "top tenth with no sail", round(top_nosail, 3), round(top_nosail_share, 3))

# busiest sail squares
order = np.argsort(-sail)[:10]
busiest = [{"lon": float(cx_[c]), "lat": float(cy_[c]), "n": int(sail[c]), "by": {natk[k]: int(cells_by_nat[k, c]) for k in range(len(natk)) if cells_by_nat[k, c]}} for c in order]
print(busiest[:5])

with open(f"{DATA}/grid_2deg.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["lon_centre", "lat_centre", "passages", "british", "dutch", "spanish", "french", "other", "ais_index_share"])
    for c in np.where(both)[0]:
        w.writerow([cx_[c], cy_[c], int(sail[c])] + [int(cells_by_nat[k, c]) for k in range(len(natk))] + [f"{ais_share[c]:.3e}"])

# ---------- page image: today's AIS index, 2 degree squares, Web Mercator ----------
S = 1024
ys = np.arange(S) + .5
mlat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * ys / S))))
mlon = -180 + (np.arange(S) + .5) * 360 / S
rr = np.clip(((mlat + 90) // C).astype(int), 0, NY - 1); cc = np.clip(((mlon + 180) // C).astype(int), 0, NX - 1)
G = ais.reshape(NY, NX)
V = G[rr][:, cc]
L = np.log10(1 + V)
pos = L[L > 0]
lo, hi = np.quantile(pos, 0.05), np.quantile(pos, 0.995)
t = np.clip((L - lo) / (hi - lo), 0, 1)
ramp = np.array([[205, 220, 226], [140, 176, 196], [80, 122, 160], [42, 72, 120], [20, 34, 74]], float)
s = t * (len(ramp) - 1); a0 = np.minimum(len(ramp) - 2, s.astype(int)); uu = (s - a0)[..., None]
rgb = ramp[a0] * (1 - uu) + ramp[a0 + 1] * uu
alpha = np.where(V > 0, 60 + 170 * t, 0)
alpha[np.abs(mlat) > 85] = 0
Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA").save(f"{DATA}/today_2deg.png", optimize=True)
print("today_2deg.png", os.path.getsize(f"{DATA}/today_2deg.png") // 1024, "KB")

jsave({"cell": C, "sail_squares": int((sail > 0).sum()), "ais_squares": int((ais > 0).sum()), "rho": rho, "top_nosail": top_nosail,
       "top_nosail_share": top_nosail_share, "top_n": int(top.sum()), "region": region, "busiest": busiest}, f"{WORK}/modern.json")
np.savez_compressed(f"{WORK}/grid2.npz", sail=sail, by=cells_by_nat, ais=ais)
