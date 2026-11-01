# Ships before steam

Real ships' logbooks from 1750 to 1850, drawn as voyage lines: the trade-wind highways of the age of sail. 6,524 passages and 259,522 daily positions from 1,973 British, Dutch, Spanish and French logbook records in the CLIWOC database (1662 to 1855), with the great sailing routes, voyage times, the busiest routes by nation, the winds the officers wrote down compared with a modern climatology, and an honest account of what the sample leaves out.

Interactive page: https://maps.tristanhotham.com/ships-before-steam/
Paper: https://doi.org/10.5281/zenodo.23857610
Blog post: https://blog.tristanhotham.com/2026/10/31/ships-before-steam/

## Headline results

- The volta do mar: ships sailing between Europe and the South Atlantic crossed 30° N at a median of 18° W outbound and 36° W homebound, 18° further west. At 38° N, 66% of homebound crossings passed the longitudes of the Azores (35° W to 20° W), against 2% of outbound ones. Both crossed the equator far out, at a median of 23° W outbound.
- The Brouwer route: 323 Dutch eastbound crossings of 75° E had a median latitude of 38° S, 100% south of 30° S; British ships, bound mostly for India, turned north sooner (median 15° S at 90° E against 34° S for the Dutch).
- Voyage times: home waters to Batavia took a median of 102 days (219 voyages): 176 days before 1820 (15 voyages) and 101 from 1820. Cape to Batavia 52 days, home waters to India 133, to the Caribbean 38; Spanish mail packets to Puerto Rico 38, Havana to Spain 81.
- Busiest routes: home waters and Batavia (252 legs, 236 Dutch), home waters and the Cape (242), the Cape and Batavia (103), home waters and Suriname (60).
- Winds: averaged in 5° squares, the logbook winds point within 45° of the NCEP/NCAR reanalysis (1991 to 2020) in 97% of the 318 squares where the modern wind is steady (median difference 9°). 73% of Atlantic winds at 10° to 25° N came from between north and east; 7.9% of entries at 0° to 5° N were calm or variable, 2.9 times the trade-wind rate.
- Sampling: Dutch records hold 44% of positions, British 35%, Spanish 17%, French 3%; 52% of records are naval. 97% of Spanish positions are from 1760 to 1799, 67% of Dutch from 1820 on, and British records end in 1829.

## Coverage by nation and decade (passages)

| Decade | British | Dutch | Spanish | French | Other | All | Daily positions |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1750s | 429 | 130 | 2 | 60 | 7 | 628 | 21,586 |
| 1760s | 457 | 136 | 121 | 39 | 0 | 753 | 26,499 |
| 1770s | 435 | 95 | 465 | 51 | 0 | 1,046 | 42,591 |
| 1780s | 300 | 171 | 180 | 90 | 0 | 741 | 30,193 |
| 1790s | 441 | 116 | 158 | 17 | 7 | 739 | 29,045 |
| 1800s | 400 | 45 | 7 | 0 | 2 | 454 | 18,553 |
| 1810s | 87 | 96 | 5 | 7 | 1 | 196 | 8,192 |
| 1820s | 117 | 261 | 17 | 0 | 0 | 395 | 13,072 |
| 1830s | 0 | 442 | 5 | 13 | 0 | 460 | 19,736 |
| 1840s | 0 | 773 | 9 | 0 | 0 | 782 | 33,025 |
| 1850s | 0 | 316 | 0 | 0 | 0 | 316 | 16,106 |

14 passages start before 1750. Full table: `data/coverage_by_decade.csv`.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`); loads `data/voyages.json`, `data/wind_arrows.json` and `data/today_2deg.png`. |
| `header.png` | Social card, 1200 x 630. |
| `data/logbooks.csv` | 1,973 CLIWOC logbook records: ship, nation, operator group, company, ship type, recorded from and to, archive, first and last day, positions (298 KB). |
| `data/passages.csv`, `data/passages.geojson` | 6,524 passages: dates, days, positions, km, start and end place; the GeoJSON has every daily position (5,173 KB). |
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

- Passages: each CLIWOC record (a ship and voyage identifier) sorted by date, one position a day, 63 lone spikes removed (over 600 km from both neighbours that are close together), cut where the log is silent for more than 10 days or the next position implies over 450 km a day; passages need 3 or more positions.
- Nations and operators: CLIWOC nationality; operator from the company field (Royal Navy, East India Company, VOC, Dutch navy and admiralties, MCC, Hudson's Bay Company and so on). Spanish records have no company: packet boats and mail frigates are counted as mail packets, ships of the line, frigates, corvettes and brigs as navy (an inference from ship type).
- Places, legs and voyages: 42 circles and boxes (`code/ports.py`), one box for European home waters (47.5° to 56.5° N, 11° W to 9.5° E). Legs join consecutive places in a record (island ports of call passed over; no silence over 30 days). Voyages for timing run from the last position at the start to the first at the destination, with calls allowed and no silence over 45 days.
- Crossings: interpolated between consecutive daily positions. Europe and South Atlantic passages have a position north of 36° N (30° W to 15° E) and one south of 5° S (60° W to 30° E).
- Winds: CLIWOC directions (from), 361 = calm, 362 = variable. Unit vectors averaged in 5° squares with at least 25 entries; benchmark = NCEP/NCAR Reanalysis 1 long-term monthly means (1991 to 2020) interpolated to each entry's place and month and averaged the same way.
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

Hotham, T. (2026) Ships before steam: the trade-wind highways of the age of sail in British, Dutch, Spanish and French logbooks, 1750 to 1850. Zenodo. https://doi.org/10.5281/zenodo.23857610

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
