"""Step 9. README.md and LICENSE from data/results.json. 10.5281/zenodo.23857610, https://doi.org/10.5281/zenodo.23857610 and https://blog.tristanhotham.com/2026/10/31/ships-before-steam/ are left for the publisher.
Run: python3 code/09_readme.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = jload(f"{DATA}/results.json"); D = R["dur"]; V = R["volta"]; B = R["brouwer"]; Wd = R["wind"]; M = R["modern"]; N = R["nation"]
lw = lambda v: fmt(v, "lonw"); ls = lambda v: fmt(v, "lats"); pc = lambda v: fmt(v, "pct")
size = lambda f: f"{os.path.getsize(os.path.join(DATA, f)) // 1024:,} KB"

readme = f"""# Ships before steam

Real ships' logbooks from 1750 to 1850, drawn as voyage lines: the trade-wind highways of the age of sail. {R['n_passages']:,} passages and {R['n_obs']:,} daily positions from {R['n_tracks']:,} British, Dutch, Spanish and French logbook records in the CLIWOC database ({R['year_min']} to {R['year_max']}), with the great sailing routes, voyage times, the busiest routes by nation, the winds the officers wrote down compared with a modern climatology, and an honest account of what the sample leaves out.

Interactive page: {PAGE_URL}
Paper: {{https://doi.org/10.5281/zenodo.23857610}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/ships-before-steam/}}

## Headline results

- The volta do mar: ships sailing between Europe and the South Atlantic crossed 30° N at a median of {lw(V['30']['out']['median_lon'])} outbound and {lw(V['30']['home']['median_lon'])} homebound, {round(R['volta_shift_30'])}° further west. At 38° N, {pc(V['azores38']['home']['share'])} of homebound crossings passed the longitudes of the Azores (35° W to 20° W), against {pc(V['azores38']['out']['share'])} of outbound ones. Both crossed the equator far out, at a median of {lw(V['0']['out']['median_lon'])} outbound.
- The Brouwer route: {B['75']['dutch']['n']} Dutch eastbound crossings of 75° E had a median latitude of {ls(B['75']['dutch']['median_lat'])}, {pc(B['75']['dutch']['share_south30'])} south of 30° S; British ships, bound mostly for India, turned north sooner (median {ls(B['90']['british']['median_lat'])} at 90° E against {ls(B['90']['dutch']['median_lat'])} for the Dutch).
- Voyage times: home waters to Batavia took a median of {round(D['nl_batavia']['median'])} days ({D['nl_batavia']['n']} voyages): {round(D['nl_batavia']['median_pre1820'])} days before 1820 ({D['nl_batavia']['n_pre1820']} voyages) and {round(D['nl_batavia']['median_post1820'])} from 1820. Cape to Batavia {round(D['cape_batavia']['median'])} days, home waters to India {round(D['channel_india']['median'])}, to the Caribbean {round(D['channel_caribbean']['median'])}; Spanish mail packets to Puerto Rico {round(D['spain_puertorico']['median'])}, Havana to Spain {round(D['havana_spain']['median'])}.
- Busiest routes: home waters and Batavia ({R['routes_top'][0]['n']} legs, {R['routes_top'][0]['by']['dutch']} Dutch), home waters and the Cape ({R['routes_top'][1]['n']}), the Cape and Batavia ({R['routes_top'][2]['n']}), home waters and Suriname ({R['routes_top'][3]['n']}).
- Winds: averaged in 5° squares, the logbook winds point within 45° of the NCEP/NCAR reanalysis (1991 to 2020) in {pc(Wd['agree']['share45_steady'])} of the {Wd['agree']['cells_steady']} squares where the modern wind is steady (median difference {round(Wd['agree']['median_steady'])}°). {pc(Wd['named']['ne_trades']['share'])} of Atlantic winds at 10° to 25° N came from between north and east; {fmt(Wd['named']['doldrums']['calm_var'], 'pct1')} of entries at 0° to 5° N were calm or variable, {Wd['calm_ratio']:.1f} times the trade-wind rate.
- Sampling: Dutch records hold {pc(N['dutch']['share_obs'])} of positions, British {pc(N['british']['share_obs'])}, Spanish {pc(N['spanish']['share_obs'])}, French {pc(N['french']['share_obs'])}; {pc(R['navy_share'])} of records are naval. {pc(R['spanish_1760_1799_share'])} of Spanish positions are from 1760 to 1799, {pc(R['dutch_1820_share'])} of Dutch from 1820 on, and British records end in {N['british']['last_year']}.

## Coverage by nation and decade (passages)

| Decade | British | Dutch | Spanish | French | Other | All | Daily positions |
|---|---:|---:|---:|---:|---:|---:|---:|
""" + "\n".join(f"| {c['decade']}s | " + " | ".join(f"{c['passages'][k]:,}" for k in R['nation_order']) + f" | {c['total_passages']:,} | {c['total_obs']:,} |" for c in R["coverage"]) + f"""

{R['n_passages_before_1750']} passages start before 1750. Full table: `data/coverage_by_decade.csv`.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`); loads `data/voyages.json`, `data/wind_arrows.json` and `data/today_2deg.png`. |
| `header.png` | Social card, 1200 x 630. |
| `data/logbooks.csv` | {R['n_tracks']:,} CLIWOC logbook records: ship, nation, operator group, company, ship type, recorded from and to, archive, first and last day, positions ({size('logbooks.csv')}). |
| `data/passages.csv`, `data/passages.geojson` | {R['n_passages']:,} passages: dates, days, positions, km, start and end place; the GeoJSON has every daily position ({size('passages.geojson')}). |
| `data/voyage_durations.csv` | Every timed voyage on the routes studied, with calls on the way. |
| `data/routes.csv` | Legs between named places by nation, both directions. |
| `data/crossings.csv` | Interpolated crossings of 0°, 20° N, 30° N (Europe and South Atlantic passages) and of 40°, 60°, 75° and 90° E (eastbound, southern Indian Ocean). |
| `data/wind_grid.csv`, `data/wind_belts.csv`, `data/wind_arrows.json` | Logbook winds by 5° square and season with the modern benchmark; by 5° latitude band in the Atlantic and Indian Oceans. |
| `data/grid_2deg.csv`, `data/today_2deg.png` | Passages per 2° square by nation, and today's AIS traffic index per 2° square (share of world total; image for the page). |
| `data/coverage_by_decade.csv` | Passages and daily positions by decade and nation. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json` | Page settings (nations, operators, ports). |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source, blog figures and post, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Passages: each CLIWOC record (a ship and voyage identifier) sorted by date, one position a day, {R['clean']['spikes']} lone spikes removed (over 600 km from both neighbours that are close together), cut where the log is silent for more than 10 days or the next position implies over 450 km a day; passages need 3 or more positions.
- Nations and operators: CLIWOC nationality; operator from the company field (Royal Navy, East India Company, VOC, Dutch navy and admiralties, MCC, Hudson's Bay Company and so on). Spanish records have no company: packet boats and mail frigates are counted as mail packets, ships of the line, frigates, corvettes and brigs as navy (an inference from ship type).
- Places, legs and voyages: {R['ports_n']} circles and boxes (`code/ports.py`), one box for European home waters (47.5° to 56.5° N, 11° W to 9.5° E). Legs join consecutive places in a record (island ports of call passed over; no silence over 30 days). Voyages for timing run from the last position at the start to the first at the destination, with calls allowed and no silence over 45 days.
- Crossings: interpolated between consecutive daily positions. Europe and South Atlantic passages have a position north of 36° N (30° W to 15° E) and one south of 5° S (60° W to 30° E).
- Winds: CLIWOC directions (from), 361 = calm, 362 = variable. Unit vectors averaged in 5° squares with at least {Wd['min_obs']} entries; benchmark = NCEP/NCAR Reanalysis 1 long-term monthly means (1991 to 2020) interpolated to each entry's place and month and averaged the same way.
- Today: World Bank and IMF Global Shipping Traffic Density overview raster (sampled pixels), summed over 2° squares only.
- Caveats: a sample of surviving, archived, digitised and mostly naval logbooks from four countries, uneven by decade; dead-reckoning positions joined by straight lines; generous port circles; translated wind terms; a modern reanalysis as benchmark; a sampled AIS raster.

## How to rerun

Needs Python 3 with numpy, scipy, shapely, pyproj, netCDF4, matplotlib, fontTools and Pillow; xelatex and pdfinfo; Playwright with Chromium for the QA step. Raw inputs are read in place (paths in `code/common.py`, overridable with `SBS_CLIWOC`, `SBS_NCEP`, `SBS_AIS`, `SBS_GEO`): `cliwoc1.json` from github.com/kikocorreoso/cliwoc_vis, the NCEP files `uwnd.mon.ltm.nc` and `vwnd.mon.ltm.nc` (sigma 0.995) from NOAA PSL, the World Bank ship density overview `shipdensity_global_ovr_4501x2125_int32le.bin.gz` and Natural Earth land. Intermediate files go to `SBS_WORK` (default `/home/claude/work/ships-before-steam`).

```
python3 code/01_voyages.py     # tracks, cleaning, passages
python3 code/02_routes.py      # ports, legs, voyage times, crossings
python3 code/03_winds.py       # wind grid, belts, benchmark
python3 code/04_modern.py      # 2 degree squares, today's traffic
python3 code/05_results.py     # results.json, data tables, page data
python3 code/06_build_site.py  # index.html (and checks on every fact stated in words)
python3 code/07_figures.py     # header, blog and paper figures
python3 code/08_paper.py       # paper PDF
python3 code/09_readme.py      # README and LICENSE
python3 code/10_release.py     # blog post, Zenodo files, Reddit post
python3 reddit/collage.py      # collage
python3 code/12_qa.py          # screenshots and text checks
```

## Sources and licences

Licence of this study's outputs: text, figures and derived data CC BY 4.0; code MIT.

- CLIWOC: García-Herrera, R., Können, G.P., Wheeler, D.A., Prieto, M.R., Jones, P.D. and Koek, F.B. (2005) CLIWOC: a climatological database for the world's oceans 1750 to 1854. Climatic Change 73, 1 to 12. Database version 2.1, released by the Universidad Complutense de Madrid (UCM) and the Royal Netherlands Meteorological Institute (KNMI), with the University of Sunderland, the University of East Anglia, INCIHUSA (Argentina) and the National Maritime Museum.
- GeoJSON of CLIWOC voyages: Francisco Correoso, cliwoc_vis, https://github.com/kikocorreoso/cliwoc_vis (derived from the CLIWOC21 GeoPackage at https://stvno.github.io/page/cliwoc/).
- **Check terms:** I could not verify a licence for CLIWOC. It is openly published research data, credited here in full; the derived positions in `data/` are shared for research reuse with that credit. Before redistributing or reusing the logbook positions, please check the terms of the original CLIWOC releases (UCM and KNMI) and of the cliwoc_vis repository.
- NCEP/NCAR Reanalysis 1 long-term monthly means, NOAA Physical Sciences Laboratory (Kalnay et al. 1996, Bulletin of the American Meteorological Society 77, 437 to 471). Public domain.
- World Bank, Global Shipping Traffic Density (https://datacatalog.worldbank.org/search/dataset/0037580), IMF and World Bank from AIS data 2015 to 2021 (Cerdeiro et al. 2020, IMF Working Paper 20/57). CC BY 4.0. Used only summed over 2° squares.
- Wikipedia, 'Age of Sail' and 'Trade winds' (CC BY-SA 4.0), for background only.
- Natural Earth land and coastlines (public domain). Base map tiles on the page © Esri.

## Citation

Hotham, T. (2026) Ships before steam: the trade-wind highways of the age of sail in British, Dutch, Spanish and French logbooks, 1750 to 1850. Zenodo. {{https://doi.org/10.5281/zenodo.23857610}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
visible_text_ok(re.sub(r"(?m)^\|[-|: ]+\|$", "", readme), "README")
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and derived data (data/, release/, reddit/, header.png)

Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/.
Credit: Tristan Hotham (2026), Ships before steam. The logbook positions and winds derive from CLIWOC v2.1
(Garcia-Herrera et al. 2005; UCM and KNMI) via the GeoJSON by Francisco Correoso (kikocorreoso/cliwoc_vis): openly published
research data for which no formal licence was found. Please credit CLIWOC and check its original terms before reusing the
positions. Today's ship traffic index derives from the World Bank and IMF Global Shipping Traffic Density (CC BY 4.0).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
print("README.md", len(readme), "chars; LICENSE written")
