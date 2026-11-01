"""Step 8. Paper PDF: fill code/paper_template.tex from data/results.json, write release/paper/Hotham_Ships_Before_Steam.tex
and compile it with xelatex (figures from step 7 in release/paper/). The DOI line keeps the publisher's 10.5281/zenodo.23857610
placeholder unless SBS_DOI is set.
Run: python3 code/08_paper.py
"""
import os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Ships_Before_Steam"
DOI = os.environ.get("SBS_DOI", "")
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def ffmt(v, f):
    if f == "pct": return f"{round(v * 100)}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "pct2": return f"{v * 100:.2f}\\%"
    if f in (None, "raw"): return tex(v)
    return fmt(v, f)


def sub(m):
    k = m.group(1)
    if k == "DOI":
        return DOI or "10.5281/zenodo.23857610"
    if k.startswith("TABLE_"):
        return m.group(0)
    return ffmt(get(R, k), m.group(3))


C = R["coverage"]; NK = R["nation_order"]
rows = [f"{c['decade']}s & " + " & ".join(f"{c['passages'][k]:,}" for k in NK) + f" & {c['total_passages']:,} & {c['total_obs']:,}\\\\" for c in C]
TCOV = ("\\begin{table}[tbp]\\centering\\small\\caption{Passages by decade (of their first day) and nation, and daily positions by decade. "
        f"{R['n_passages_before_1750']} passages before 1750 are not shown.}}\\label{{tab:coverage}}"
        "\\begin{tabular}{lrrrrrrr}\\toprule Decade & British & Dutch & Spanish & French & Other & All & Positions\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table}")
DK = ["nl_batavia", "batavia_nl", "nl_cape", "cape_batavia", "nl_suriname", "channel_india", "india_channel", "channel_caribbean", "channel_namerica",
      "spain_puertorico", "spain_havana", "havana_spain", "spain_plate", "plate_spain"]
drows = []
for k in DK:
    d = R["dur"][k]
    if not d["n"]: continue
    drows.append(f"{tex(d['label'])} & {d['n']} & {round(d['median'])} & {round(d['q1'])} to {round(d['q3'])} & {round(d['min'])} & {d['first_year']} to {d['last_year']}\\\\")
TDUR = ("\\begin{table}[tbp]\\centering\\small\\caption{Voyage times in days, from the last position at the start to the first at the destination.}\\label{tab:dur}"
        "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{6.4cm}rrrrr}\\toprule Route & Voyages & Median & Middle half & Fastest & Years\\\\\\midrule\n" + "\n".join(drows) + "\n\\bottomrule\\end{tabular}\\end{table}")
src = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
out = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", sub, src).replace("{{TABLE_COVERAGE}}", TCOV).replace("{{TABLE_DUR}}", TDUR)
assert "{{" not in out.replace("10.5281/zenodo.23857610", ""), re.findall(r"\{\{[^}]*\}\}", out)[:5]
body = re.sub(r"(?m)^%.*$", "", out)
for bad in ("\u2014", "\u2013", "D" + "SIT", "D" + "CMS"):
    assert bad not in body, bad
assert "--" not in body
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/{NAME}.tex", "w", encoding="utf-8").write(out)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
pdf = f"{OUT}/{NAME}.pdf"
assert os.path.exists(pdf), r.stdout[-3000:]
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
print(NAME, n, "pages")
assert 8 <= n <= 15, n
for ext in ("aux", "log", "out"):
    if os.path.exists(f"{OUT}/{NAME}.{ext}"):
        os.remove(f"{OUT}/{NAME}.{ext}")
