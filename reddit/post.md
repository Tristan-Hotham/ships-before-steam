## Title

[OC] Ships before steam: 6,524 voyages from real 18th and 19th century logbooks. Homebound ships crossed 30° N 18° further west than outbound ones, looping round with the wind

## Body

Every day at noon, officers on sailing ships logged their position and the wind. The CLIWOC project digitised 260,631 of those entries from British, Dutch, Spanish and French logbooks, and I drew every one as a line (6,524 passages, 1662 to 1855, coloured by nation). The routes follow the wind: out past Africa with the north-east trades, home in a big loop west past the Azores (the 'volta do mar'), and east across the southern Indian Ocean near 40° S to Java (the Dutch 'Brouwer route'; median Dutch crossing of 75° E at 38° S). The median voyage from European home waters to Batavia took 102 days. The logbook winds still hold up: averaged over 5° squares they point within 45° of today's average wind in 97% of squares. Caveats: this is a sample of surviving, mostly naval logbooks; Spanish logs are mostly from 1760 to 1799, Dutch mostly after 1820, British end in the 1820s, and Portuguese, American and most merchant ships are missing. Interactive map with a decade slider and the winds: https://maps.tristanhotham.com/ships-before-steam/

## Source comment

Source: CLIWOC v2.1, Climatological Database for the World's Oceans (García-Herrera et al. 2005, Climatic Change), released by Universidad Complutense de Madrid and KNMI; GeoJSON by Francisco Correoso (github.com/kikocorreoso/cliwoc_vis). Wind benchmark: NCEP/NCAR Reanalysis 1 monthly means, 1991 to 2020. Land: Natural Earth. Passages cut where a log is silent for more than 10 days; lines join daily noon positions (mostly dead reckoning).

Tools: Python (numpy, shapely, pyproj, matplotlib); Leaflet for the interactive map. Text, figures and derived data CC BY 4.0.

Interactive version: https://maps.tristanhotham.com/ships-before-steam/
Paper: {https://doi.org/10.5281/zenodo.23857610}
Blog post: {https://blog.tristanhotham.com/2026/10/31/ships-before-steam/}
