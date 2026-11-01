"""Step 6. Build index.html from code/page_template.html and code/fullscreen_snippet.html. Every number in the text is a
{{path|format}} token filled from data/results.json; facts stated in words (here and in the paper, blog, collage and
post) are checked by the asserts below. 10.5281/zenodo.23857610, https://doi.org/10.5281/zenodo.23857610 and https://blog.tristanhotham.com/2026/10/31/ships-before-steam/ are left for the publisher.
Run: python3 code/06_build_site.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = jload(f"{DATA}/results.json")
N = R["nation"]; D = R["dur"]; Vt = R["volta"]; B = R["brouwer"]; Wd = R["wind"]; M = R["modern"]

# ---------- facts stated in words ----------
assert [k for k, _ in sorted(N.items(), key=lambda kv: -kv[1]["obs"])][:4] == ["dutch", "british", "spanish", "french"]
assert N["british"]["last_year"] < 1830 and N["spanish"]["obs"] > N["french"]["obs"]
assert R["year_min"] < 1750 and R["year_max"] > 1850
assert Vt["30"]["home"]["median_lon"] < Vt["30"]["out"]["median_lon"] - 10            # homebound well west of outbound
assert Vt["20"]["home"]["median_lon"] < Vt["20"]["out"]["median_lon"]
assert -30 < Vt["0"]["out"]["median_lon"] < -15                                        # equator crossed well out in the Atlantic
assert Vt["azores38"]["home"]["share"] > 0.5 > Vt["azores38"]["out"]["share"]
assert B["75"]["dutch"]["median_lat"] < -35 and B["75"]["dutch"]["share_south30"] > 0.95
assert B["90"]["british"]["median_lat"] > B["90"]["dutch"]["median_lat"] + 10           # British peel off north sooner
assert B["dutch_java_minlat"]["median"] < -38
assert all(v > 0 for v in R["hist"]["lon75_dutch"]["n"][3:7])
assert D["nl_batavia"]["median_pre1820"] > 1.5 * D["nl_batavia"]["median_post1820"]
assert D["cape_batavia"]["median_pre1820"] > D["cape_batavia"]["median_post1820"]
assert D["nl_batavia"]["n_pre1820"] < 20                                                # "rest on few voyages"
assert D["havana_spain"]["median"] > D["spain_puertorico"]["median"]
assert R["routes_top"][0]["a"] == "batavia" and R["routes_top"][0]["b"] == "home" and R["routes_top"][0]["lead"] == "dutch"
assert R["routes_top"][1]["a"] == "cape" and R["routes_top"][1]["b"] == "home"
assert (R["routes_top"][2]["a"], R["routes_top"][2]["b"]) == ("batavia", "cape") and (R["routes_top"][3]["a"], R["routes_top"][3]["b"]) == ("home", "suriname")
assert (R["routes_top"][4]["a"], R["routes_top"][4]["b"]) == ("goldcoast", "home")
assert R["where"]["atlantic"] > R["where"]["indian"] > R["where"]["pacific"]
dutch_r = {(r["a"], r["b"]) for r in R["routes_by_nation"]["dutch"][:6]}
assert ("home", "suriname") in dutch_r and ("goldcoast", "home") in dutch_r
sp_r = {x for r in R["routes_by_nation"]["spanish"][:6] for x in (r["a"], r["b"])}
assert {"coruna", "cadiz", "puertorico", "havana", "plate"} <= sp_r
br_r = {x for r in R["routes_by_nation"]["british"][:6] for x in (r["a"], r["b"])}
assert {"cape", "barbados", "ceylon"} <= br_r
assert R["groups"]["navy"] / R["n_tracks"] > 0.5                                        # navies dominate
assert R["thinnest_decade"]["decade"] == 1810
assert Wd["named"]["doldrums"]["lat0"] == 0 and Wd["calm_ratio"] > 2
assert Wd["named"]["ne_trades"]["share"] > .6 and Wd["named"]["se_trades"]["share"] > .6 and Wd["named"]["forties"]["share"] > .6
assert Wd["named"]["monsoon_jja"]["share"] > .5 and Wd["named"]["monsoon_djf"]["share"] > .5
assert Wd["ind_force_m40"] > 1.8 * Wd["atl_force_0"]                                     # "nearly twice the calms"
assert Wd["ind_force_m40"] < 2.2 * Wd["atl_force_0"]
assert M["region"]["red_sea"]["sail_share"] < 0.0005 < 0.01 < M["region"]["red_sea"]["ais_share"] and M["region"]["malacca"]["sail_share"] < 0.0005
assert M["region"]["south_indian"]["sail_share"] > 50 * M["region"]["south_indian"]["ais_share"]
assert R["famous"]["resolution"]["min_lat"] < -71 and R["famous"]["resolution"]["min_lat_day"] == "30 January 1774"
assert R["northmost"]["ship"] == "Racehorse" and R["northmost"]["year"] == 1773
assert R["steam"]["curacao_year"] == 1827 and R["steam"]["first_year"] == 1827
assert R["n_other_tracks"] < 10


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    assert not re.search(r"\{\{(?!DOI\}\}|DOI_URL\}\}|BLOG_URL\}\})", html), re.findall(r"\{\{[^}]*\}\}", html)[:5]
    J_ = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J_(R)).replace("/*SITE*/", J_(jload(f"{DATA}/site.json")))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    visible_text_ok(vis, "page")
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
