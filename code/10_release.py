"""Step 10. Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo), Reddit post (reddit/post.md).
Numbers written into alt text and the post are checked against results.json here.
Run: python3 code/10_release.py
"""
import os, re, sys, zipfile, json as _json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = jload(f"{DATA}/results.json"); D = R["dur"]; V = R["volta"]
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Ships_Before_Steam"

# ---------- numbers in alt text ----------
assert (round(V["30"]["out"]["median_lon"]), round(V["30"]["home"]["median_lon"])) == (-18, -36)
assert 95 <= D["nl_batavia"]["median"] <= 105 and round(D["batavia_nl"]["median"]) == 110 and round(D["nl_cape"]["median"]) == 85
assert [round(D[k]["median"]) for k in ("cape_batavia", "nl_suriname", "channel_india", "channel_caribbean", "spain_puertorico", "havana_spain", "spain_plate")] == [52, 35, 133, 38, 38, 81, 70]
assert R["n_obs_raw"] > 250000

# ---------- blog ----------
post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read(), R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, used
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
for ln in post.splitlines():
    if "{{IMG|" in ln:
        assert ln.startswith("{{IMG|") and ln.endswith("}}"), ln
assert not re.search(r"\{\{(?!IMG\||DOI_URL\}\}|BLOG_URL\}\}|DOI\}\})", post)
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
visible_text_ok(vis, "blog")
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Ships before steam: the trade-wind highways of the age of sail, drawn from real logbooks",
        "slug": "ships-before-steam",
        "excerpt": f"{R['n_passages']:,} passages from British, Dutch, Spanish and French ships' logbooks, 1750 to 1850. Drawn as lines, they show ships running out with the trade winds, looping home past the Azores and racing east through the roaring forties to Java.",
        "seo_description": "Real ships' logbooks from 1750 to 1850 drawn as voyage lines: the trade winds, the volta do mar, the Brouwer route and how long voyages took.",
        "tags": ["age of sail", "ships logbooks", "CLIWOC", "trade winds", "maritime history", "maps", "data visualisation", "history"],
        "header_alt": f"Title card reading 'Ships before steam' beside a world map of thousands of thin voyage lines coloured by nation, red British, orange Dutch, gold Spanish and blue French, crowding the Atlantic, rounding the Cape and crossing the southern Indian Ocean to Java. Text: {R['n_passages']:,} passages from real logbooks, {R['year_min']} to {R['year_max']}."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# ---------- Zenodo ----------
Zd = f"{REL}/zenodo"; os.makedirs(Zd, exist_ok=True)
for fn in os.listdir(Zd):
    os.remove(os.path.join(Zd, fn))
os.link(f"{REL}/paper/{NAME}.pdf", f"{Zd}/{NAME}.pdf")
zp = f"{Zd}/ships-before-steam_code_and_data.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"ships-before-steam/{d}/{fn}")
    for fn in ("README.md", "LICENSE", "reddit/collage.py"):
        z.write(os.path.join(ROOT, fn), f"ships-before-steam/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("\\emph{", "").replace("}", "")
zmeta = {"title": "Ships Before Steam: The Trade-Wind Highways of the Age of Sail in British, Dutch, Spanish and French Logbooks, 1750 to 1850",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE_URL}\">{PAGE_URL}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/ships-before-steam/}}.</p>"
                        "<p>Data: CLIWOC v2.1 (García-Herrera et al. 2005, Climatic Change 73, 1 to 12), released by the Universidad Complutense de Madrid and KNMI, "
                        "via the GeoJSON by Francisco Correoso (github.com/kikocorreoso/cliwoc_vis); openly published research data for which no formal licence was found, credited in full. "
                        "NCEP/NCAR Reanalysis 1 (public domain). World Bank and IMF Global Shipping Traffic Density (CC BY 4.0). Natural Earth (public domain). "
                        "This study's text, figures and derived data: CC BY 4.0. Code: MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["age of sail", "ships' logbooks", "CLIWOC", "trade winds", "maritime history", "historical climatology", "volta do mar", "Brouwer route", "data visualisation"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE_URL, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://github.com/kikocorreoso/cliwoc_vis", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "notes": AI}
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
visible_text_ok(s, "meta")
jsave(zmeta, f"{Zd}/metadata.json", indent=2)

# ---------- Reddit post ----------
pm = f"""## Title

[OC] Ships before steam: {R['n_passages']:,} voyages from real 18th and 19th century logbooks. Homebound ships crossed 30° N {round(R['volta_shift_30'])}° further west than outbound ones, looping round with the wind

## Body

Every day at noon, officers on sailing ships logged their position and the wind. The CLIWOC project digitised {R['n_obs_raw']:,} of those entries from British, Dutch, Spanish and French logbooks, and I drew every one as a line ({R['n_passages']:,} passages, {R['year_min']} to {R['year_max']}, coloured by nation). The routes follow the wind: out past Africa with the north-east trades, home in a big loop west past the Azores (the 'volta do mar'), and east across the southern Indian Ocean near 40° S to Java (the Dutch 'Brouwer route'; median Dutch crossing of 75° E at {abs(round(R['brouwer']['75']['dutch']['median_lat']))}° S). The median voyage from European home waters to Batavia took {round(D['nl_batavia']['median'])} days. The logbook winds still hold up: averaged over 5° squares they point within 45° of today's average wind in {round(R['wind']['agree']['share45_steady'] * 100)}% of squares. Caveats: this is a sample of surviving, mostly naval logbooks; Spanish logs are mostly from 1760 to 1799, Dutch mostly after 1820, British end in the 1820s, and Portuguese, American and most merchant ships are missing. Interactive map with a decade slider and the winds: {PAGE_URL}

## Source comment

Source: CLIWOC v2.1, Climatological Database for the World's Oceans (García-Herrera et al. 2005, Climatic Change), released by Universidad Complutense de Madrid and KNMI; GeoJSON by Francisco Correoso (github.com/kikocorreoso/cliwoc_vis). Wind benchmark: NCEP/NCAR Reanalysis 1 monthly means, 1991 to 2020. Land: Natural Earth. Passages cut where a log is silent for more than 10 days; lines join daily noon positions (mostly dead reckoning).

Tools: Python (numpy, shapely, pyproj, matplotlib); Leaflet for the interactive map. Text, figures and derived data CC BY 4.0.

Interactive version: {PAGE_URL}
Paper: {{https://doi.org/10.5281/zenodo.23857610}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/ships-before-steam/}}
"""
visible_text_ok(pm, "post")
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(pm)
print("blog words", words, "; figures", len(used), "; zenodo", sorted(os.listdir(Zd)), os.path.getsize(zp) // 1024, "KB zip")
