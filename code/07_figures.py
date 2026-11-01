"""Step 7. Figures: header.png (1200 x 630), blog figures (release/blog/b_*.png) and paper figures (release/paper/f_*.png).
Every number drawn comes from data/results.json or the WORK files written by steps 1 to 5.
Run: python3 code/07_figures.py
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import *
import matplotlib.patheffects as pe

R = jload(f"{DATA}/results.json")
BLOG = os.path.join(ROOT, "release", "blog"); PAPER = os.path.join(ROOT, "release", "paper")
for d in (BLOG, PAPER): os.makedirs(d, exist_ok=True)
BG, SEA, LANDC, COAST = "#F7F3EA", "#E2EBEC", "#EDE6D6", "#CFC6B2"
NATS = list(NAT_LAB)
PS = passages()
rng = np.random.default_rng(7)
order = rng.permutation(len(PS))
SEG = {}
for k in order:
    p = PS[k]
    SEG.setdefault(p["i"], cable_segments([np.column_stack([p["lon"], p["lat"]])], step=1.0))
halo = [pe.withStroke(linewidth=3.2, foreground=BG)]


def lines(ax, sel=lambda p: True, col=lambda p: NAT_COL[p["nat"]], lw=.35, alpha=.16, z=3):
    segs, cols = [], []
    for k in order:
        p = PS[k]
        if not sel(p): continue
        c = col(p)
        for s in SEG[p["i"]]:
            segs.append(s); cols.append(c)
    ax.add_collection(LineCollection(segs, colors=cols, linewidths=lw, alpha=alpha, zorder=z, capstyle="round"))
    return len(segs)


def world_ax(fig, rect, lat_min=-75, lat_max=84, lon_min=-180, lon_max=180):
    ax = fig.add_axes(rect); ax.set_axis_off()
    outline(ax, fc=SEA, ec="#C4D0D3", lw=.6, lat_min=-90, lat_max=90)
    draw_land(ax, fc=LANDC, ec=COAST, lw=.35)
    return ax


def set_view(ax, lon0, lon1, lat0, lat1):
    xs, ys = [], []
    for lo in np.linspace(lon0, lon1, 30):
        for la in np.linspace(lat0, lat1, 30):
            x, y = proj(lo, la); xs.append(float(x)); ys.append(float(y))
    ax.set_xlim(min(xs), max(xs)); ax.set_ylim(min(ys), max(ys)); ax.set_aspect("equal")


def txt(ax, lon, lat, s, **kw):
    x, y = proj(lon, lat)
    kw.setdefault("path_effects", halo)
    return ax.text(float(x), float(y), s, **kw)


def legend_nat(ax, x, y, dy=.055, fs=10, short=False):
    for i, k in enumerate(NATS):
        ax.plot([x, x + .035], [y - i * dy] * 2, color=NAT_COL[k], lw=3, transform=ax.transAxes, solid_capstyle="round")
        ax.text(x + .045, y - i * dy, NAT_SHORT[k] if short else NAT_LAB[k], transform=ax.transAxes, va="center", fontsize=fs, color=FG)


# ---------- world map of all passages ----------
def world(path, w=12, h=6.6, title=True):
    fig = plt.figure(figsize=(w, h), facecolor=BG)
    ax = world_ax(fig, [0, 0, 1, .92 if title else 1])
    lines(ax)
    set_view(ax, -180, 180, -72, 84)
    for nm, lo, la in (("ATLANTIC\nOCEAN", -38, 30), ("INDIAN\nOCEAN", 78, -5), ("PACIFIC OCEAN", -140, 2), ("SOUTHERN OCEAN", 60, -62)):
        txt(ax, lo, la, nm, ha="center", va="center", fontsize=9, color=COOL, family=SER, style="italic", alpha=.8)
    if title:
        fig.text(.012, .955, f"Every logbook passage, {R['year_min']} to {R['year_max']}: {R['n_passages']:,} passages, {R['n_obs']:,} daily positions", fontsize=13, color=FG, fontproperties=DISPB)
    legend_nat(ax, .015, .34, fs=9.5, short=True)
    fig.text(.99, .012, "Data: CLIWOC v2.1 (Garcia-Herrera et al. 2005). Lines join daily noon positions.", ha="right", fontsize=7.5, color=MUT)
    save(fig, path)


world(f"{BLOG}/b_world.png"); world(f"{PAPER}/f_world.png")

# ---------- volta do mar ----------
def volta(path):
    P = jload(f"{WORK}/passages.json")
    fig = plt.figure(figsize=(10, 7.2), facecolor=BG)
    ax = world_ax(fig, [0, 0, .66, 1])
    def es(p):
        la = p["lat"]; lo = p["lon"]
        return (la[(lo > -30) & (lo < 15)].max(initial=-99) > 36) and (la[(lo > -60) & (lo < 30)].min(initial=99) < -5)
    ESP = {p["i"]: es(p) for p in PS}
    south = lambda p: p["lat"][-1] < p["lat"][0]
    lines(ax, sel=lambda p: ESP[p["i"]] and south(p), col=lambda p: "#C2272D", lw=.45, alpha=.18)
    lines(ax, sel=lambda p: ESP[p["i"]] and not south(p), col=lambda p: "#24557F", lw=.45, alpha=.18, z=4)
    set_view(ax, -62, 22, -42, 55)
    V = R["volta"]
    for L in (30,):
        x0, y0 = proj(-62, L); x1, y1 = proj(22, L)
        ax.plot([float(x0), float(x1)], [float(y0), float(y1)], color=FG, lw=.6, ls=(0, (4, 3)), zorder=5)
        txt(ax, -61, L + 1, "30° N", fontsize=9, color=FG)
        for d, c in (("out", "#C2272D"), ("home", "#24557F")):
            x, y = proj(V[str(L)][d]["median_lon"], L)
            ax.scatter([float(x)], [float(y)], s=70, color=c, edgecolor="white", lw=1.2, zorder=7)
    txt(ax, -8, 1, "Outbound:\nsouth along\nAfrica", fontsize=10, color="#9E1E24", ha="left", weight="bold")
    txt(ax, -61, 11, "Homebound:\nthe volta do mar,\na loop west", fontsize=10, color="#1B4467", ha="left", weight="bold")
    fig.text(.72, .925, f"{R['euro_south_n']:,} crossings of 30° N\nby ships between Europe\nand the South Atlantic", fontsize=10, color=MUT)
    # side histogram
    hx = fig.add_axes([.72, .1, .26, .66], facecolor=BG)
    H = R["hist"]; lo = H["lat30_out"]["lo"]; st = H["lat30_out"]["step"]
    xs = lo + st * np.arange(len(H["lat30_out"]["n"])) + st / 2
    hx.barh(xs + 1.1, H["lat30_out"]["n"], height=2.1, color="#C2272D", label=f"Outbound ({H['lat30_out']['total']})")
    hx.barh(xs - 1.1, H["lat30_home"]["n"], height=2.1, color="#24557F", label=f"Homebound ({H['lat30_home']['total']})")
    hx.set_ylim(-55, 0); hx.set_yticks([-50, -40, -30, -20, -10, 0]); hx.set_yticklabels(["50° W", "40° W", "30° W", "20° W", "10° W", "0°"])
    style(hx, axis="x"); hx.set_xlabel("crossings of 30° N", fontsize=9, color=MUT)
    hx.legend(frameon=False, fontsize=8.5, loc="lower right")
    hx.set_title(f"Median crossing:\nout {abs(round(V['30']['out']['median_lon']))}° W, home {abs(round(V['30']['home']['median_lon']))}° W", fontsize=10, color=FG, loc="left")
    save(fig, path)


volta(f"{BLOG}/b_volta.png"); volta(f"{PAPER}/f_volta.png")

# ---------- Brouwer route ----------
def brouwer(path):
    fig = plt.figure(figsize=(11, 6.6), facecolor=BG)
    ax = world_ax(fig, [0, 0, 1, 1])
    lines(ax, sel=lambda p: p["nat"] == "british", lw=.45, alpha=.18)
    lines(ax, sel=lambda p: p["nat"] == "dutch", lw=.45, alpha=.2, z=4)
    set_view(ax, 8, 122, -52, 26)
    for X in (75,):
        x0, y0 = proj(X, -52); x1, y1 = proj(X, 26)
        ax.plot([float(x0), float(x1)], [float(y0), float(y1)], color=FG, lw=.6, ls=(0, (4, 3)), zorder=5)
        txt(ax, X + .6, 22, "75° E", fontsize=9, color=FG)
    B = R["brouwer"]["75"]
    for k, c in (("dutch", "#EE7A12"), ("british", "#C2272D")):
        x, y = proj(75, B[k]["median_lat"]); ax.scatter([float(x)], [float(y)], s=80, color=c, edgecolor="white", lw=1.3, zorder=7)
    txt(ax, 76.5, B["dutch"]["median_lat"] - 3.5, f"Dutch median {abs(round(B['dutch']['median_lat']))}° S", fontsize=9.5, color="#B65A08", weight="bold")
    txt(ax, 76.5, B["british"]["median_lat"] + 2.2, f"British median {abs(round(B['british']['median_lat']))}° S", fontsize=9.5, color="#9E1E24", weight="bold")
    txt(ax, 40, -47.5, "Roaring forties: westerly gales", fontsize=10, color=FG, ha="center", style="italic")
    txt(ax, 109, -7.6, "Batavia", fontsize=9.5, color=FG, ha="left", weight="bold")
    txt(ax, 21, -30.5, "Cape of\nGood Hope", fontsize=9.5, color=FG, ha="left", weight="bold")
    legend_nat(ax, .02, .95, fs=9)
    save(fig, path)


brouwer(f"{BLOG}/b_brouwer.png"); brouwer(f"{PAPER}/f_brouwer.png")

# ---------- voyage times ----------
DR = [("nl_batavia", "dutch"), ("batavia_nl", "dutch"), ("nl_cape", "dutch"), ("cape_batavia", "dutch"), ("nl_suriname", "dutch"), ("channel_india", "british"),
      ("channel_caribbean", "british"), ("spain_puertorico", "spanish"), ("havana_spain", "spanish"), ("spain_plate", "spanish"), ("plate_spain", "spanish")]


def durations(path):
    rows = [(k, n) for k, n in DR if R["dur"][k]["n"] >= 5]
    fig, ax = plt.subplots(figsize=(10, 6.2), facecolor=BG); ax.set_facecolor(BG)
    for i, (k, n) in enumerate(rows):
        d = R["dur"][k]; y = len(rows) - i; c = NAT_COL[n]
        ax.plot([d["min"], min(d["max"], 270)], [y, y], color=c, lw=1.2, alpha=.7)
        ax.add_patch(plt.Rectangle((d["q1"], y - .22), d["q3"] - d["q1"], .44, color=c, alpha=.35, lw=0))
        ax.scatter([d["median"]], [y], s=60, color=c, edgecolor="white", lw=1.2, zorder=3)
        ax.text(d["median"], y + .3, f"{round(d['median'])}", ha="center", fontsize=9, color=FG, weight="bold")
        if d["max"] > 270: ax.text(270, y - .42, f"to {round(d['max'])}", ha="right", fontsize=8, color=MUT)
    ax.set_yticks([len(rows) - i for i in range(len(rows))]); ax.set_yticklabels([f"{R['dur'][k]['label']} ({R['dur'][k]['n']})" for k, _ in rows], fontsize=9.5)
    ax.set_xlim(0, 272); ax.set_xlabel("days from last position at the start to first position at the destination", color=MUT, fontsize=9.5)
    style(ax, axis="x")
    ax.set_title("Voyage times: median (dot), middle half (bar), fastest to slowest (line)", fontsize=11, color=FG, loc="left")
    fig.tight_layout(); save(fig, path)


durations(f"{BLOG}/b_durations.png"); durations(f"{PAPER}/f_durations.png")

# ---------- winds: arrows map and belts ----------
G = jload(f"{WORK}/wind_grids.json")


def arrows(ax, cells, scale=5.4e5, lw=1.1):
    for c in cells:
        frm = np.radians(c["from"]); to = frm + np.pi
        x, y = proj(c["lon"], c["lat"]); x, y = float(x), float(y)
        L = scale * max(.15, c["steady"])
        dx, dy = np.sin(to) * L / 2, np.cos(to) * L / 2
        f = c["force"] if c["force"] is not None else 6
        t = min(1, max(0, (f - 3) / 7)); col = (0.27 + (0.47 - 0.27) * t, 0.47 * (1 - t) + 0.08 * t, 0.63 * (1 - t) + 0.12 * t)
        ax.annotate("", xy=(x + dx, y + dy), xytext=(x - dx, y - dy), arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, mutation_scale=7.5, shrinkA=0, shrinkB=0), zorder=6)


def winds(path):
    fig = plt.figure(figsize=(12, 9.4), facecolor=BG)
    ax = world_ax(fig, [0, .36, 1, .62])
    lines(ax, col=lambda p: "#9AA6AD", lw=.3, alpha=.08)
    arrows(ax, G["all"])
    set_view(ax, -100, 160, -62, 70)
    fig.text(.012, .975, "The logbook winds: mean direction in each 5° square (length: steadiness; colour: blue light, red strong)", fontsize=11.5, color=FG, fontproperties=DISPB)
    for nm, lo, la in (("North-east trades", -40, 19), ("South-east trades", -12, -16), ("Westerlies", -28, 47), ("Roaring forties", 75, -47), ("Doldrums", -24, 4.5)):
        txt(ax, lo, la, nm, fontsize=9.5, color=FG, ha="center", weight="bold")
    bx = fig.add_axes([.07, .06, .9, .27], facecolor=BG)
    B = sorted(R["wind"]["belts"]["atlantic"], key=lambda r: r["lat0"])
    xm = [(r["lat0"] + r["lat1"]) / 2 for r in B]
    bx.axhline(0, color=MUT, lw=.8)
    bx.plot(xm, [r["ncep_unit_u"] for r in B], color=MUT, ls=(0, (4, 3)), lw=2, label="Modern reanalysis (NCEP/NCAR, monthly means)")
    bx.plot(xm, [r["u"] for r in B], color=COOL, lw=2.4, marker="o", ms=4, label="Logbooks (average of daily winds)")
    bx.set_xlim(-62, 62); bx.set_ylim(-1.05, 1.05); style(bx)
    bx.set_xticks([-60, -40, -20, 0, 20, 40, 60]); bx.set_xticklabels(["60° S", "40° S", "20° S", "0°", "20° N", "40° N", "60° N"])
    bx.set_ylabel("west-to-east part\n(+ from west, - from east)", fontsize=9, color=MUT)
    bx.legend(frameon=False, fontsize=9, loc="upper center", ncol=2)
    bx.set_title("Atlantic, 70° W to 20° E, by 5° latitude band", fontsize=10, color=FG, loc="left")
    save(fig, path)


winds(f"{BLOG}/b_winds.png"); winds(f"{PAPER}/f_winds.png")


def monsoon(path):
    fig = plt.figure(figsize=(12, 5), facecolor=BG)
    for j, (sk, ttl) in enumerate((("djf", "December to February"), ("jja", "June to August"))):
        ax = world_ax(fig, [j * .5, 0, .5, .9])
        arrows(ax, G[sk], scale=4.2e5, lw=1.1)
        set_view(ax, 35, 115, -30, 28)
        fig.text(j * .5 + .02, .93, ttl, fontsize=12, color=FG, fontproperties=DISPB)
    save(fig, path)


monsoon(f"{PAPER}/f_monsoon.png")

# ---------- coverage ----------
def coverage(path):
    C = R["coverage"]
    fig, ax = plt.subplots(figsize=(10, 4.8), facecolor=BG); ax.set_facecolor(BG)
    x = np.arange(len(C)); acc = np.zeros(len(C))
    for k in NATS:
        v = np.array([c["obs"][k] for c in C]); ax.bar(x, v, bottom=acc, color=NAT_COL[k], width=.78, label=NAT_LAB[k]); acc += v
    ax.set_xticks(x); ax.set_xticklabels([f"{c['decade']}s" for c in C], fontsize=9.5)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v / 1000)}k" if v else "0"))
    style(ax); ax.set_ylabel("daily positions", color=MUT)
    ax.legend(frameon=False, fontsize=9, ncol=3, loc="upper right")
    ax.set_title("Who kept the records: daily logbook positions by decade and nation", fontsize=11, color=FG, loc="left")
    fig.tight_layout(); save(fig, path)


coverage(f"{BLOG}/b_coverage.png"); coverage(f"{PAPER}/f_coverage.png")

# ---------- then and now ----------
def thennow(path):
    Gd = np.load(f"{WORK}/grid2.npz"); sail, ais = Gd["sail"], Gd["ais"]
    NX = 180
    fig = plt.figure(figsize=(12, 6.4), facecolor=BG)
    for j, (vals, ttl, cmap) in enumerate(((sail, "Logbook passages, 1750 to 1850", "Reds"), (ais, "Ship traffic today (AIS index, 2015 to 2021)", "Blues"))):
        ax = world_ax(fig, [0, .49 - j * .48, 1, .43])
        v = vals.reshape(90, 180); pos = np.sort(v[v > 0])
        rank = lambda val: np.searchsorted(pos, val) / len(pos)          # percentile among squares with any traffic
        cm = plt.get_cmap(cmap)
        polys, cols = [], []
        for r in range(90):
            for c in range(180):
                if v[r, c] <= 0: continue
                lo0, la0 = -180 + 2 * c, -90 + 2 * r
                if lo0 >= CUT and lo0 + 2 > CUT + 360: continue
                xs, ys = proj([lo0, lo0 + 2, lo0 + 2, lo0], [la0, la0, la0 + 2, la0 + 2])
                if np.ptp(xs) > 1e6: continue
                polys.append(np.column_stack([xs, ys])); cols.append(cm(.12 + .88 * rank(v[r, c]) ** 2.2))
        ax.add_collection(PatchCollection([MPoly(p) for p in polys], facecolors=cols, edgecolors="none", zorder=3))
        draw_land(ax, fc=LANDC, ec=COAST, lw=.3)
        set_view(ax, -180, 180, -70, 80)
        fig.text(.02, .95 - j * .48, ttl, fontsize=12.5, color=FG, fontproperties=DISPB)
    fig.text(.99, .005, "Both summed over 2° squares; colour: rank among squares with any traffic. AIS: World Bank and IMF Global Shipping Traffic Density (CC BY 4.0).", ha="right", fontsize=8, color=MUT)
    save(fig, path)


thennow(f"{BLOG}/b_thennow.png"); thennow(f"{PAPER}/f_thennow.png")

# ---------- header 1200 x 630 ----------
def header():
    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
    ax = world_ax(fig, [.30, 0, .70, 1])
    lines(ax, lw=.3, alpha=.2)
    set_view(ax, -100, 150, -60, 72)
    fig.text(.035, .80, "Ships", fontproperties=DISP, fontsize=60, color=FG)
    fig.text(.035, .68, "before", fontproperties=DISP, fontsize=60, color=FG)
    fig.text(.035, .56, "steam", fontproperties=DISP, fontsize=60, color="#B5332A")
    fig.text(.037, .46, f"{R['n_passages']:,} passages from real\nlogbooks, {R['year_min']} to {R['year_max']}", fontsize=13, color=FG, linespacing=1.4)
    for i, k in enumerate(NATS[:4]):
        fig.patches.append(plt.Rectangle((.037, .325 - i * .045), .03, .009, color=NAT_COL[k], transform=fig.transFigure, figure=fig))
        fig.text(.075, .32 - i * .045, NAT_SHORT[k], fontsize=12, color=FG)
    fig.text(.037, .05, "maps.tristanhotham.com/ships-before-steam", fontsize=10, color=MUT)
    fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)


header()
print("figures done:", sorted(os.listdir(BLOG)), sorted(f for f in os.listdir(PAPER) if f.endswith(".png")))
