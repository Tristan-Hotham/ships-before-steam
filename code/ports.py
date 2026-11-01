"""Named ports and anchorages used to find voyages between places. Each is a circle (lon, lat, radius in degrees of
latitude; the longitude radius is widened by 1/cos(lat)) or, for coasts, a box. A logbook position inside one counts as
'at' that place. Coordinates are approximate harbour positions; radii are generous because logbooks often start or stop
a day or two off the coast."""

# key: (label, kind, geometry)
PORTS = {
    # European home waters
    "home": ("Home waters (North Sea, Channel and approaches)", "box", (-11.0, 47.5, 9.5, 56.5)),
    "coruna": ("La Coruña and Ferrol", "circle", (-8.35, 43.4, 0.8)),
    "lisbon": ("Lisbon", "circle", (-9.25, 38.7, 0.7)),
    "cadiz": ("Cádiz", "circle", (-6.35, 36.5, 0.75)),
    "gibraltar": ("Gibraltar", "circle", (-5.35, 36.1, 0.35)),
    "toulon": ("Toulon", "circle", (5.9, 43.1, 0.6)),
    "cartagena_es": ("Cartagena (Spain)", "circle", (-0.98, 37.6, 0.5)),
    # Atlantic islands
    "madeira": ("Madeira", "circle", (-16.9, 32.7, 0.6)),
    "canaries": ("Canary Islands", "circle", (-15.6, 28.3, 1.2)),
    "capeverde": ("Cape Verde Islands", "circle", (-23.6, 15.9, 1.2)),
    "sthelena": ("St Helena", "circle", (-5.72, -15.95, 0.6)),
    "ascension": ("Ascension", "circle", (-14.4, -7.95, 0.5)),
    # Americas
    "halifax": ("Halifax", "circle", (-63.55, 44.6, 0.8)),
    "newyork": ("New York", "circle", (-74.0, 40.5, 0.8)),
    "hudson": ("Hudson Bay (York Factory)", "circle", (-92.4, 57.0, 2.5)),
    "havana": ("Havana", "circle", (-82.35, 23.15, 0.9)),
    "veracruz": ("Veracruz", "circle", (-96.1, 19.2, 0.9)),
    "puertorico": ("Puerto Rico", "circle", (-66.1, 18.45, 0.8)),
    "jamaica": ("Jamaica", "circle", (-76.8, 17.95, 0.8)),
    "antigua": ("Antigua and the Leewards", "circle", (-61.8, 17.1, 0.8)),
    "barbados": ("Barbados", "circle", (-59.6, 13.1, 0.8)),
    "curacao": ("Curaçao", "circle", (-68.95, 12.1, 0.7)),
    "suriname": ("Suriname", "circle", (-55.2, 5.9, 1.0)),
    "rio": ("Rio de Janeiro", "circle", (-43.15, -22.95, 0.8)),
    "plate": ("River Plate (Montevideo, Buenos Aires)", "circle", (-57.0, -35.0, 1.6)),
    "callao": ("Callao (Lima)", "circle", (-77.2, -12.05, 0.9)),
    "valparaiso": ("Valparaíso", "circle", (-71.65, -33.0, 0.8)),
    # Africa
    "goldcoast": ("Gold Coast and Bight of Benin", "box", (-3.5, 3.5, 3.5, 7.0)),
    "angola": ("Loango and Angola coast", "box", (8.5, -10.0, 13.5, -3.5)),
    "cape": ("Cape of Good Hope (Table Bay, False Bay)", "circle", (18.45, -34.0, 1.0)),
    "mauritius": ("Mauritius", "circle", (57.5, -20.15, 0.8)),
    # Asia
    "bombay": ("Bombay", "circle", (72.8, 18.9, 1.0)),
    "ceylon": ("Ceylon (Colombo, Point de Galle, Trincomalee)", "box", (79.3, 5.6, 81.8, 9.0)),
    "madras": ("Madras", "circle", (80.3, 13.1, 1.0)),
    "bengal": ("Bengal (Hooghly)", "circle", (88.0, 21.4, 1.2)),
    "padang": ("Padang", "circle", (100.35, -0.95, 0.8)),
    "batavia": ("Batavia and the Sunda Strait", "circle", (106.8, -6.05, 1.0)),
    "sunda": ("Sunda Strait", "circle", (105.3, -6.4, 1.1)),
    "manila": ("Manila", "circle", (120.9, 14.55, 0.9)),
    "canton": ("Canton (Pearl River)", "circle", (113.6, 22.2, 1.2)),
    "nagasaki": ("Nagasaki (Deshima)", "circle", (129.85, 32.75, 0.8)),
    "sydney": ("Sydney (Port Jackson)", "circle", (151.25, -33.85, 0.9)),
}
# Places merged when counting routes (a ship 'at' the Sunda Strait is on its way in or out of Batavia).
MERGE = {"sunda": "batavia", "gibraltar": "cadiz"}
HOME = {"home", "coruna", "lisbon", "cadiz", "gibraltar", "toulon", "cartagena_es"}
