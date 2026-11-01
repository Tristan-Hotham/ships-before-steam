"""Reddit collage (r/dataisbeautiful style): every logbook passage on a light world map, coloured by nation, with ocean,
wind-belt and route labels placed automatically on the clearest open sea near where they belong (each label is tried at
many positions inside a box and put where its footprint covers the least voyage ink, land and other labels), a full
legend, a chart of passages by decade and nation, key numbers and credits.
Run: python3 reddit/collage.py   (after code/01 to 05)
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
from figlib import *
import matplotlib.patheffects as pe
import matplotlib.colors as mcol

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "reddit", "ships_before_steam.png")
BG, SEA, LANDC, COAST = "#F8F4EB", "#E3ECEE", "#ECE4D3", "#CBC1AC"
NATS = list(NAT_LAB)
DPI = 200
W_IN, H_IN = 14.0, 11.6
PS = passages()
rng = np.random.default_rng(3)
order = rng.permutation(len(PS))

fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI, facecolor=BG)
MAP = [0.0, .245, 1.0, .6]
ax = fig.add_axes(MAP); ax.set_axis_off()
outline(ax, fc=SEA, ec="#C2CFD2", lw=.7, lat_min=-90, lat_max=90)
draw_land(ax, fc=LANDC, ec=COAST, lw=.35)
segs, cols = [], []
for k in order:
    p = PS[k]
    for s in cable_segments([np.column_stack([p["lon"], p["lat"]])], step=1.0):
        segs.append(s); cols.append(NAT_COL[p["nat"]])
ax.add_collection(LineCollection(segs, colors=cols, linewidths=.42, alpha=.17, zorder=3, capstyle="round"))
# set view
xs, ys = [], []
for lo in np.linspace(-180, 180, 73):
    for la in (-66, 80):
        x, y = proj(lo, la); xs.append(float(x)); ys.append(float(y))
x0, x1 = proj(CUT + .01, 0)[0], proj(CUT + 359.99, 0)[0]
ax.set_xlim(float(x0) * 1.002, float(x1) * 1.002); ax.set_ylim(min(ys), max(ys))
ax.set_aspect("equal", adjustable="datalim")

# ---------- ink and land masks of the map as drawn ----------
fig.canvas.draw()
buf = np.asarray(fig.canvas.buffer_rgba())[..., :3].astype(float) / 255
Hp, Wp = buf.shape[:2]
hsv = mcol.rgb_to_hsv(buf)
ink = (hsv[..., 1] > .30) & (np.abs(buf - np.array(mcol.to_rgb(SEA))).sum(-1) > .08) & (np.abs(buf - np.array(mcol.to_rgb(LANDC))).sum(-1) > .08)
land = np.abs(buf - np.array(mcol.to_rgb(LANDC))).sum(-1) < .05
taken = np.zeros((Hp, Wp), bool)
if os.environ.get("INK_DUMP"):
    from PIL import Image as _I
    _I.fromarray(np.dstack([ink * 255, land * 120, np.zeros_like(ink)]).astype(np.uint8)).save(os.environ["INK_DUMP"]); raise SystemExit
ren = fig.canvas.get_renderer()
halo = [pe.withStroke(linewidth=3.6, foreground=SEA)]


def place(s, box, on_land=False, avoid_ink=True, **kw):
    """Try the label at a grid of positions inside box (lon0, lon1, lat0, lat1); keep the clearest."""
    best = None
    boxes = box if isinstance(box, list) else [box]
    cand = [(lo, la) for b in boxes for lo in np.linspace(b[0], b[1], 14) for la in np.linspace(b[2], b[3], 10)]
    for lo, la in cand:
        if True:
            x, y = proj(lo, la)
            t = ax.text(float(x), float(y), s, **kw)
            bb = t.get_window_extent(renderer=ren).expanded(1.06, 1.15); t.remove()
            c0, c1 = int(max(0, bb.x0)), int(min(Wp, bb.x1)); r0, r1 = int(max(0, Hp - bb.y1)), int(min(Hp, Hp - bb.y0))
            if c1 <= c0 or r1 <= r0 or bb.x0 < 0 or bb.x1 > Wp: continue
            area = (c1 - c0) * (r1 - r0)
            si = ink[r0:r1, c0:c1].sum() / area; sl = land[r0:r1, c0:c1].sum() / area; st = taken[r0:r1, c0:c1].sum() / area
            score = (si if avoid_ink else 0) + (0 if on_land else 1.5 * sl) + 10 * st
            if best is None or score < best[0]:
                best = (score, lo, la, (r0, r1, c0, c1), si, sl)
    sc, lo, la, (r0, r1, c0, c1), si, sl = best
    x, y = proj(lo, la)
    t = ax.text(float(x), float(y), s, zorder=10, path_effects=halo, **kw)
    taken[r0:r1, c0:c1] = True
    REPORT.append((s.replace("\n", " ")[:38], round(si, 3), round(sl, 3)))
    return t


REPORT = []
OC = dict(ha="center", va="center", fontsize=11, color="#2C5A80", family=SER, style="italic")
place("A T L A N T I C   O C E A N", (-35, -10, -56, -48), fontsize=11.5, ha="center", va="center", color="#2C5A80", family=SER, style="italic")
place("I N D I A N\nO C E A N", (60, 95, -14, 0), linespacing=1.6, **OC)
place("P A C I F I C   O C E A N", (-160, -120, -25, 10), **OC)
place("S O U T H E R N   O C E A N", (100, 150, -64, -57), **OC)
WB = dict(ha="left", va="center", fontsize=10.5, color=FG, weight="bold")
WS = dict(ha="left", va="top", fontsize=8.4, color=MUT, linespacing=1.3)
inv = ax.transData.inverted()


def mark(bb):
    taken[int(max(0, Hp - bb.y1)):int(min(Hp, Hp - bb.y0)), int(max(0, bb.x0)):int(min(Wp, bb.x1))] = True


def sub_under(t, sub):
    x, y = t.get_position(); bb = t.get_window_extent(renderer=ren)
    _, ylow = inv.transform((0, bb.y0 - 4))
    t2 = ax.text(x, ylow, sub, zorder=10, path_effects=halo, **WS)
    b2 = t2.get_window_extent(renderer=ren).expanded(1.04, 1.1); mark(b2)
    REPORT.append((sub[:38], float(ink[int(Hp - b2.y1):int(Hp - b2.y0), int(b2.x0):int(b2.x1)].mean()), float(land[int(Hp - b2.y1):int(Hp - b2.y0), int(b2.x0):int(b2.x1)].mean())))


def wind_glyph(t, to_deg):
    """A small arrow left of the label, pointing where the wind blows (to_deg clockwise from north); none if None."""
    bb = t.get_window_extent(renderer=ren); cx, cy = bb.x0 - 26, (bb.y0 + bb.y1) / 2
    if to_deg is None:
        p = inv.transform((cx, cy)); ax.scatter([p[0]], [p[1]], s=26, facecolor="none", edgecolor=FG, lw=1.3, zorder=11)
    else:
        r = np.radians(to_deg); dx, dy = 15 * np.sin(r), 15 * np.cos(r)
        a0 = inv.transform((cx - dx, cy - dy)); a1 = inv.transform((cx + dx, cy + dy))
        ax.annotate("", xy=a1, xytext=a0, arrowprops=dict(arrowstyle="-|>", color=FG, lw=1.6, mutation_scale=11, shrinkA=0, shrinkB=0), zorder=11)
    mark(matplotlib.transforms.Bbox([[cx - 20, cy - 20], [cx + 20, cy + 20]]))


# wind belts are global: label them as a column in the open eastern Pacific, at their own latitudes, with the wind's direction
for name, sub, lat, to in (("Westerlies", "the road home", 44, 90), ("Horse latitudes", "light and variable", 31, None),
                           ("North-east trades", "steady, the road out", 17, 225), ("Doldrums", "calms and squalls", 5, None),
                           ("South-east trades", "steady, from the south-east", -13, 315), ("Westerlies", "", -40, 90)):
    t = place(name, [(-158, -128, lat - 1.5, lat + 1.5)], **WB)
    wind_glyph(t, to)
    if sub: sub_under(t, sub)
t = place("Roaring forties", (25, 55, -52, -46), **WB); wind_glyph(t, 90); sub_under(t, "westerly gales")
t = place("Monsoons", (58, 70, 6, 15), **WB)
RT = dict(ha="left", va="center", fontsize=9.2, color=FG, linespacing=1.35)
place("The Brouwer route: Dutch ships\nrun east near 40° S, then north to Java", (75, 110, -58, -48), **RT)
place(f"Cook's Resolution reaches\n{abs(round(R['famous']['resolution']['min_lat']))}° S, 30 January 1774", (-160, -110, -62, -50), **RT)


def leader_label(s, box, target, **kw):
    """Label in clear sea with a thin leader to the route; the leader must not cross another label."""
    t = place(s, box, **kw)
    bb = t.get_window_extent(renderer=ren)
    tx, ty = ax.transData.transform(proj(*target))
    sx = min(max(tx, bb.x0), bb.x1); sy = bb.y0 - 3 if ty < bb.y0 else bb.y1 + 3
    n = 200; xs_ = np.linspace(sx, tx, n); ys_ = np.linspace(sy, ty, n)
    hit = sum(taken[int(Hp - y), int(x)] for x, y in zip(xs_[8:-4], ys_[8:-4]) if 0 <= int(Hp - y) < Hp and 0 <= int(x) < Wp)
    assert hit == 0, ("leader crosses a label", s)
    p0 = inv.transform((sx, sy)); p1 = inv.transform((tx, ty))
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=FG, lw=.9, zorder=9, solid_capstyle="round")
    ax.scatter([p1[0]], [p1[1]], s=22, color=FG, edgecolor="white", lw=.9, zorder=11)


print("label checks (text, share of footprint on voyage ink, on land):")
for r in REPORT: print("  ", r)
assert all(r[1] < .15 and r[2] < .12 for r in REPORT), "a label sits on dense lines or land"

# ---------- title block ----------
fig.text(.03, .965, "Ships before steam", fontproperties=DISP, fontsize=44, color=FG, va="top")
fig.text(.03, .887, f"Every passage in {R['n_tracks']:,} British, Dutch, Spanish and French logbook records, {R['year_min']} to {R['year_max']}: "
         f"{R['n_passages']:,} passages, {R['n_obs']:,} noon positions", fontsize=12.2, color=FG, va="top")
fig.text(.03, .865, "Ships could not sail where they liked: they ran out with the trade winds, looped home on the westerlies and raced east along the roaring forties.",
         fontsize=10.2, color=MUT, va="top")
# key numbers, top right
KN = [(f"{round(R['dur']['nl_batavia']['median'])} days", "median voyage from home waters\nto Batavia (" + f"{R['dur']['nl_batavia']['n']} voyages)"),
      (f"{round(R['volta_shift_30'])}° further west", "where homebound ships crossed\n30° N than outbound ones"),
      (f"{round(R['wind']['agree']['share45_steady'] * 100)}%", "of 5° squares where logbook winds\npoint within 45° of today's")]
for i, (big, small_) in enumerate(KN):
    x = .47 + i * .16
    fig.text(x, .962, big, fontproperties=DISPB, fontsize=19, color=["#EE7A12", "#24557F", "#C2272D"][i], va="top")
    fig.text(x, .93, small_, fontsize=8.4, color=MUT, va="top", linespacing=1.35)

# ---------- bottom row: legend, chart, notes ----------
lg = fig.add_axes([.03, .045, .22, .18]); lg.set_axis_off(); lg.set_xlim(0, 1); lg.set_ylim(0, 1)
lg.text(0, .97, "Ship's nation", fontsize=10.5, color=FG, weight="bold", va="top")
lg.text(1, .97, "passages", fontsize=8.6, color=MUT, va="top", ha="right")
LGL = {"other": "Other: American, Swedish,\nDanish and Hamburg ships"}
for i, k in enumerate(NATS):
    y = .79 - i * .16
    lg.plot([0, .1], [y, y], color=NAT_COL[k], lw=4, solid_capstyle="round")
    lg.text(.14, y, LGL.get(k, NAT_LAB[k]), fontsize=9.6, color=FG, va="center", linespacing=1.2)
    lg.text(1.0, y, f"{R['nation'][k]['passages']:,}", fontsize=9.6, color=FG, va="center", ha="right")
# inset: the volta do mar
ins = fig.add_axes([.585, .03, .19, .158]); ins.set_axis_off()
outline(ins, fc=SEA, ec="#C2CFD2", lw=.5); draw_land(ins, fc=LANDC, ec=COAST, lw=.3)
def _es(p):
    la, lo = p["lat"], p["lon"]
    return (la[(lo > -30) & (lo < 15)].max(initial=-99) > 36) and (la[(lo > -60) & (lo < 30)].min(initial=99) < -5)
for south, c, z in ((True, "#C2272D", 3), (False, "#24557F", 4)):
    sg = [s_ for p in PS if _es(p) and ((p["lat"][-1] < p["lat"][0]) == south) for s_ in cable_segments([np.column_stack([p["lon"], p["lat"]])], step=1.0)]
    ins.add_collection(LineCollection(sg, colors=c, linewidths=.3, alpha=.16, zorder=z))
xs_, ys_ = zip(*[tuple(map(float, proj(lo, la))) for lo in np.linspace(-62, 20, 20) for la in (-40, 54)])
ins.set_xlim(min(xs_), max(xs_)); ins.set_ylim(min(ys_), max(ys_)); ins.set_aspect("equal", adjustable="datalim")
fig.text(.585, .222, "Out and home: the volta do mar", fontsize=10, color=FG, weight="bold", va="top")
fig.add_artist(plt.Line2D([.587, .603], [.2, .2], color="#C2272D", lw=3)); fig.text(.607, .2, "outbound", fontsize=8.4, color=FG, va="center")
fig.add_artist(plt.Line2D([.665, .681], [.2, .2], color="#24557F", lw=3)); fig.text(.685, .2, "homebound", fontsize=8.4, color=FG, va="center")
ch = fig.add_axes([.29, .065, .265, .135], facecolor=BG)
C = R["coverage"]; xx = np.arange(len(C)); acc = np.zeros(len(C))
for k in NATS:
    v = np.array([c["passages"][k] for c in C]); ch.bar(xx, v, bottom=acc, color=NAT_COL[k], width=.78); acc += v
ch.set_xticks(xx); ch.set_xticklabels([f"{c['decade']}s" for c in C], fontsize=8.2, rotation=0)
for lab in ch.get_xticklabels()[1::2]: lab.set_visible(False)
style(ch); ch.tick_params(labelsize=8.2)
ch.set_title("Passages by decade and nation:\nwhat survives, not all shipping", fontsize=10, color=FG, loc="left", pad=8, weight="bold")
nt = fig.add_axes([.795, .045, .19, .18]); nt.set_axis_off()
notes = ("Each line joins one ship's daily noon\npositions, mostly by dead reckoning.\n"
         "Spanish logbooks are mostly 1760s to\n1790s, Dutch mostly after 1820, British\nend in the 1820s. Navies dominate;\n"
         "Portuguese, American and most\nmerchant ships are missing.")
nt.text(0, 1, "Read with care", fontsize=10.5, color=FG, weight="bold", va="top")
nt.text(0, .84, notes, fontsize=8.6, color=MUT, va="top", linespacing=1.4)
fig.add_artist(plt.Line2D([.03, .97], [.238, .238], color=RULE, lw=1))
fig.text(.03, .014, "Data: CLIWOC v2.1 logbook database (Garcia-Herrera et al. 2005), UCM and KNMI; GeoJSON: F. Correoso (cliwoc_vis); Natural Earth.",
         fontsize=8, color=MUT)
fig.text(.97, .014, "maps.tristanhotham.com/ships-before-steam  ·  Dr Tristan Hotham", fontsize=8.6, color=FG, ha="right", weight="bold")
fig.savefig(OUT, dpi=DPI, facecolor=BG)
plt.close(fig)
from PIL import Image
im = Image.open(OUT); print(OUT, im.size, os.path.getsize(OUT) // 1024, "KB")
assert im.size[0] >= 2400
