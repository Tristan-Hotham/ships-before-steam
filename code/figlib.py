"""Shared drawing helpers for the figures, the header and the collage: fonts, colours, an Equal Earth world centred on
LON0 (the cut falls in the Pacific), land from Natural Earth, and voyage lines split at the cut."""
import os, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Polygon as MPoly
from pyproj import Transformer
from shapely.geometry import shape, box
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": 900, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Black.ttf")
    instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": 700, "opsz": 48, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Bold.ttf")
for f in ["IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(FONTS, f))
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SER, MONO = "Source Serif 4", "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 11})
BG, FG, MUT, RULE, PAPER = "#F5F4EF", "#13222E", "#5A6670", "#DCE0DC", "#FCFCFA"
SEA, LANDC, COAST = "#E4ECEE", "#E9E5DA", "#C9C3B4"
HOT, COOL = "#D9482B", "#1F5F8B"
LON0 = 15.0
CUT = LON0 - 180          # -170
FWD = Transformer.from_crs(4326, f"+proj=eqearth +lon_0={LON0} +datum=WGS84 +units=m +no_defs", always_xy=True)


def proj(lon, lat):
    lon = np.asarray(lon, float); lat = np.asarray(lat, float)
    lon = np.where(lon < CUT, lon + 360, lon)
    return FWD.transform(lon - 0, lat)


def wrap(lon):
    lon = np.asarray(lon, float)
    return np.where(lon < CUT, lon + 360, lon)


def cable_segments(lines, step=0.5):
    """Lines in lon/lat -> list of projected xy arrays, split at the cut, densified so they curve with the projection."""
    out = []
    for ln in lines:
        a = np.array(ln, float)
        if len(a) < 2:
            continue
        pts = [a[0]]
        for p, q in zip(a[:-1], a[1:]):
            n = max(1, int(np.ceil(np.hypot(*(q - p)) / step)))
            for t in np.linspace(0, 1, n + 1)[1:]:
                pts.append(p + (q - p) * t)
        a = np.array(pts)
        lo = wrap(((a[:, 0] + 180) % 360) - 180); la = a[:, 1]
        br = np.where(np.abs(np.diff(lo)) > 180)[0]
        for seg in np.split(np.arange(len(lo)), br + 1):
            if len(seg) >= 2:
                x, y = FWD.transform(lo[seg], la[seg]); out.append(np.column_stack([x, y]))
    return out


_LAND = None


def land_polys():
    """Natural Earth 50m land, cut at 170° W and wrapped, as projected rings (list of arrays: exterior first, holes after)."""
    global _LAND
    if _LAND is not None:
        return _LAND
    L = jload(f"{GEO}/ne_50m_land.geojson")["features"]
    g = unary_union([shape(f["geometry"]).buffer(0) for f in L])
    west = g.intersection(box(-180, -90, CUT, 90)); east = g.intersection(box(CUT, -90, 180, 90))
    from shapely import affinity
    g2 = unary_union([east, affinity.translate(west, 360, 0)])
    out = []
    for poly in getattr(g2, "geoms", [g2]):
        if poly.geom_type != "Polygon" or poly.area < 0.02:
            continue
        def dens(coords):
            a = np.array(coords)
            pts = [a[0]]
            for p, q in zip(a[:-1], a[1:]):
                n = max(1, int(np.ceil(np.hypot(*(q - p)) / 1.0)))
                for t in np.linspace(0, 1, n + 1)[1:]:
                    pts.append(p + (q - p) * t)
            a = np.array(pts); x, y = FWD.transform(a[:, 0], np.clip(a[:, 1], -89.9, 89.9)); return np.column_stack([x, y])
        rings = [dens(poly.exterior.coords)] + [dens(r.coords) for r in poly.interiors]
        e = rings[0]
        if np.ptp(e[:, 0]) > 2e7 and np.ptp(e[:, 1]) < 3e5:     # thin slivers left along the cut
            continue
        out.append(rings)
    _LAND = out
    return out


_COAST = None


def coast_segments():
    """Natural Earth 50m coastlines (land outlines before cutting), split at the cut like the cables."""
    global _COAST
    if _COAST is None:
        L = jload(f"{GEO}/ne_50m_land.geojson")["features"]
        rings = []
        for f in L:
            g = shape(f["geometry"])
            for p in getattr(g, "geoms", [g]):
                if p.area >= 0.02:
                    rings.append([(x, max(-89.9, min(89.9, y))) for x, y in p.exterior.coords])
        _COAST = cable_segments(rings, step=1.0)
    return _COAST


def draw_land(ax, fc=LANDC, ec=COAST, lw=.4, z=1):
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    for rings in land_polys():
        verts = np.concatenate(rings); codes = []
        for r in rings:
            codes += [Path.MOVETO] + [Path.LINETO] * (len(r) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec="none", lw=0, zorder=z))
    if ec and lw:
        ax.add_collection(LineCollection(coast_segments(), colors=ec, linewidths=lw, zorder=z + .1))


def outline(ax, fc=SEA, ec="#B9C6CA", lw=.8, z=0, lat_min=-90, lat_max=90):
    lat = np.linspace(lat_min, lat_max, 200)
    xl, yl = FWD.transform(np.full_like(lat, LON0 - 179.999), lat)
    xr, yr = FWD.transform(np.full_like(lat, LON0 + 179.999), lat[::-1])
    poly = np.column_stack([np.concatenate([xl, xr]), np.concatenate([yl, yr])])
    ax.add_patch(MPoly(poly, closed=True, fc=fc, ec=ec, lw=lw, zorder=z))
    return poly


def style(ax, grid=True, axis="y"):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(MUT)
    ax.tick_params(colors=FG, labelsize=10)
    if grid: ax.grid(axis=axis, color=RULE, lw=.8); ax.set_axisbelow(True)


def passages():
    """Every passage as (nation key, group, decade, start year, lon array (unwrapped), lat array), from WORK."""
    import numpy as np
    O = dict(np.load(f"{WORK}/obs.npz")); T = jload(f"{WORK}/tracks.json"); P = jload(f"{WORK}/passages.json")
    pa, t = O["passage"], O["t"]
    order = np.lexsort((t, pa)); b = np.searchsorted(pa[order], np.arange(len(P) + 1))
    out = []
    for p in P:
        idx = order[b[p["i"]]:b[p["i"] + 1]]
        lo = O["lon"][idx]; lo = lo[0] + np.concatenate([[0], np.cumsum(((np.diff(lo) + 180) % 360) - 180)])
        x = T[p["track"]]
        out.append({"i": p["i"], "nat": x["nat"], "group": x["group"], "year": p["year"], "track": p["track"], "lon": lo, "lat": O["lat"][idx]})
    return out


def save(fig, path, dpi=200):
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
