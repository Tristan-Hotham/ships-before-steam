"""Shared paths and helpers for the ships-before-steam study ("Ships before steam").

Raw inputs (read in place, never copied into the repo):
  CLIWOC   /home/claude/newdata/raw8/cliwoc/cliwoc1.json: CLIWOC v2.1 logbook observations (Climatological Database for
           the World's Oceans 1750 to 1850; Garcia-Herrera et al. 2005; releases by UCM and KNMI) as a GeoJSON of ship
           tracks, one LineString per CLIWOC ship/logbook ID with daily arrays (date, wind direction, wind force in m/s,
           anchored, rain, fog, ...), built by Francisco Correoso (github.com/kikocorreoso/cliwoc_vis) from the CLIWOC21
           GeoPackage at stvno.github.io/page/cliwoc/. Also wiki_Age_of_Sail.json and wiki_Trade_winds.json.
  NCEP     /home/claude/newdata/raw2/wind/uwnd.mon.ltm.nc, vwnd.mon.ltm.nc: NCEP/NCAR Reanalysis 1 long-term monthly mean
           surface (sigma 0.995) winds, 2.5 degree grid (NOAA PSL; Kalnay et al. 1996), used as a modern benchmark.
  AIS      /home/claude/newdata/raw6/shipdensity/shipdensity_global_ovr_4501x2125_int32le.bin.gz: overview (0.08 degree,
           sampled pixels) of the World Bank / IMF Global Shipping Traffic Density raster, 2015 to 2021, CC BY 4.0. Only
           used summed over 2 degree squares.
  GEO      Natural Earth 50m land and countries (public domain).
Intermediates are written to WORK (outside the repo)."""
import json, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIWOC = os.environ.get("SBS_CLIWOC", "/home/claude/newdata/raw8/cliwoc")
NCEP = os.environ.get("SBS_NCEP", "/home/claude/newdata/raw2/wind")
AIS = os.environ.get("SBS_AIS", "/home/claude/newdata/raw6/shipdensity/shipdensity_global_ovr_4501x2125_int32le.bin.gz")
GEO = os.environ.get("SBS_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("FONT_DIR", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.environ.get("SBS_WORK", "/home/claude/work/ships-before-steam")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "ships-before-steam"
PAGE_URL = "https://maps.tristanhotham.com/ships-before-steam/"
REPO = "https://github.com/Tristan-Hotham/ships-before-steam"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
CREDIT = ("CLIWOC v2.1 (Garcia-Herrera et al. 2005), released by Universidad Complutense de Madrid and KNMI; "
          "GeoJSON by Francisco Correoso (kikocorreoso/cliwoc_vis)")

# Nations: the four big archives plus everyone else. Colours are used on the page, in figures and in the collage.
NATIONS = [("british", "British", "#C2272D"),
           ("dutch", "Dutch", "#EE7A12"),
           ("spanish", "Spanish", "#B58A00"),
           ("french", "French", "#2457A6"),
           ("other", "Other (American, Swedish, Danish, Hamburg)", "#3E8E7E")]
NAT_COL = {k: c for k, _, c in NATIONS}
NAT_LAB = {k: l for k, l, _ in NATIONS}
NAT_SHORT = {"british": "British", "dutch": "Dutch", "spanish": "Spanish", "french": "French", "other": "Other"}
NAT_MAP = {"BRITISH": "british", "DUTCH": "dutch", "SPANISH": "spanish", "FRENCH": "french"}

# Operators (filter groups), from the Company field and, for Spain, the ship type.
GROUPS = [("eic", "East India companies"),
          ("navy", "Navies"),
          ("correo", "Spanish mail packets"),
          ("chartered", "Other chartered companies"),
          ("merchant", "Merchants and whalers"),
          ("unknown", "Not recorded")]
GROUP_LAB = dict(GROUPS)
COMPANY_LAB = {"RN": "Royal Navy", "ROYAL NAVY": "Royal Navy", "EIC": "English East India Company",
               "VOC": "Dutch East India Company (VOC)", "VOC-Z": "Dutch East India Company (VOC), Zeeland chamber",
               "MAR": "Dutch navy (Marine)", "ADM": "Dutch admiralties", "MCC": "Middelburgsche Commercie Compagnie",
               "WIC": "Dutch West India Company", "MER": "Dutch merchant ship", "WHA": "Dutch whaler",
               "HUDSON BAY COMPANY": "Hudson's Bay Company", "SWEDISH EAST INDIA COMPANY": "Swedish East India Company",
               "OIC": "Danish Asiatic Company", "PARTICULIER": "Private owner", "MERCHANT NAVY": "Merchant ship",
               "THOMAS BROUW EN ZN.": "Thomas Brouw en Zn.", "A. VAN HOBOKEN & ZN. TE ROTTERDAM.": "A. van Hoboken en Zn., Rotterdam",
               "H. V. RIJCKEVORSEL, ROTTERDAM": "H. van Rijckevorsel, Rotterdam"}


def group_of(nation_raw, company, shiptype):
    c = (company or "").upper()
    t = (shiptype or "").upper()
    if c in ("EIC", "VOC", "VOC-Z", "SWEDISH EAST INDIA COMPANY", "OIC"):
        return "eic"
    if c in ("RN", "ROYAL NAVY", "MAR", "ADM"):
        return "navy"
    if c in ("MCC", "WIC", "HUDSON BAY COMPANY"):
        return "chartered"
    if c in ("MER", "WHA", "PARTICULIER", "MERCHANT NAVY") or c in ("THOMAS BROUW EN ZN.", "A. VAN HOBOKEN & ZN. TE ROTTERDAM.", "H. V. RIJCKEVORSEL, ROTTERDAM"):
        return "merchant"
    if nation_raw == "SPANISH":
        if t.startswith("PAQUEBOT") or "CORREO" in t:
            return "correo"
        if t in ("NAVÍO", "NAVIO", "FRAGATA", "CORVETA", "BERGANTIN", "CHAMBEQUÍN", "POLACRA", "FALUCHO"):
            return "navy"
    if (nation_raw == "BRITISH") and t in ("1ST RATE", "2ND RATE", "3RD RATE", "4TH RATE", "5TH RATE", "6TH RATE", "SLOOP"):
        return "navy"
    return "unknown"


def dash(v):
    """House style: no em or en dashes, no double hyphens, in anything written to data/."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[\u2013\u2014]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" \u2014 ", ", ").replace("\u2014", ", ").replace(" \u2013 ", ", ").replace("\u2013", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, (list, tuple)):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def _np(o):
    import numpy as np
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.bool_): return bool(o)
    if isinstance(o, np.ndarray): return o.tolist()
    raise TypeError(type(o))


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"), default=_np)


def jload(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "pct2": return f"{v * 100:.2f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "deg":                                   # signed longitude/latitude-free degrees
        return f"{round(v)}°"
    if f == "lonw":                                  # longitude as 'NN° W' or 'NN° E'
        return f"{abs(round(v))}° {'W' if v < 0 else 'E'}"
    if f == "lats":                                  # latitude as 'NN° S' or 'NN° N'
        return f"{abs(round(v))}° {'S' if v < 0 else 'N'}"
    raise ValueError(f)


def fill(text, R, keep=("DOI", "DOI_URL", "BLOG_URL", "IMG")):
    """Replace {{path|fmt}} tokens from results.json, leaving the publisher's placeholders alone."""
    def rep(m):
        k = m.group(1)
        if k in keep or k.startswith("IMG"):
            return m.group(0)
        return fmt(get(R, k), m.group(3))
    return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", rep, text)


def visible_text_ok(s, where=""):
    for bad in ("\u2014", "\u2013", "--", "D" + "SIT", "D" + "CMS", "civil serv", "Civil Serv"):
        assert bad not in s, (where, bad)


def hav(lon1, lat1, lon2, lat2):
    """Great-circle distance in km (numpy friendly)."""
    import numpy as np
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(lon2 - lon1); dp = p2 - p1
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
