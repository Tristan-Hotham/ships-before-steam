"""Step 12. QA: open index.html in Chromium (Playwright) at 1280 px and 390 px, record console errors and save screenshots
to qa/. The build container cannot reach the Leaflet CDN, Esri tiles or web fonts: Leaflet is served from a local copy
(LEAFLET_DIST) and the rest is left blank. Also checks every built text file for dashes and banned words.
Run: python3 code/12_qa.py
"""
import os, re, sys, threading, http.server, functools, glob
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

LEAF = os.environ.get("LEAFLET_DIST", "/tmp/claude-0/-home-claude/9791f396-0812-550b-8fd1-2ad33918f115/scratchpad/node_modules/leaflet/dist")
QA = os.path.join(ROOT, "qa"); os.makedirs(QA, exist_ok=True)
PORT = 8871


def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    s = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT))
    threading.Thread(target=s.serve_forever, daemon=True).start(); return s


def route(r):
    u = r.request.url
    if "cdnjs.cloudflare.com" in u and "leaflet" in u:
        f = "leaflet.css" if u.endswith(".css") else "leaflet.js"
        return r.fulfill(status=200, body=open(os.path.join(LEAF, f), "rb").read(), headers={"Content-Type": "text/css" if f.endswith("css") else "application/javascript"})
    if u.startswith(f"http://127.0.0.1:{PORT}"):
        return r.continue_()
    return r.abort()


def run():
    srv = serve(); errs = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        for name, vw, vh in (("desktop", 1280, 900), ("phone", 390, 844)):
            pg = br.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=1 if vw > 500 else 2)
            pg.on("console", lambda m, n=name: errs.append((n, m.type, m.text)) if m.type == "error" and "ERR_FAILED" not in m.text and "Failed to load resource" not in m.text else None)
            pg.on("pageerror", lambda e, n=name: errs.append((n, "pageerror", str(e))))
            pg.route("**/*", route)
            pg.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load")
            pg.wait_for_function("window.READY === true", timeout=30000); pg.wait_for_timeout(1500)
            pg.screenshot(path=f"{QA}/{name}_top.png")
            pg.locator("#atlas").scroll_into_view_if_needed(); pg.wait_for_timeout(1200)
            pg.locator("#atlas").screenshot(path=f"{QA}/{name}_map.png")
            pg.evaluate("decIn.value = 4; decIn.oninput(); 0"); pg.wait_for_timeout(800)
            pg.locator("#atlas").screenshot(path=f"{QA}/{name}_1770s.png")
            pg.evaluate("decIn.value = 0; decIn.oninput(); 0")
            for k in ("brouwer", "volta", "correos", "windsJJA", "endeavour", "resolution"):
                pg.evaluate(f"FOCUS['{k}'][1](); restyle(); 0"); pg.wait_for_timeout(1300)
                pg.locator("#atlas").screenshot(path=f"{QA}/{name}_focus_{k}.png")
            pg.evaluate("FOCUS.all[1](); LY.season='all'; LY.today = true; applyLayers(); 0"); pg.wait_for_timeout(1200)
            pg.locator("#map").screenshot(path=f"{QA}/{name}_today.png")
            pg.evaluate("LY.today = false; applyLayers(); 0")
            pg.locator(".lyrBtn").click(); pg.wait_for_timeout(400)
            pg.locator("#map").screenshot(path=f"{QA}/{name}_layers.png")
            pg.locator(".lyrBtn").click()
            pg.locator("#q").fill("Batavia"); pg.wait_for_timeout(500)
            pg.screenshot(path=f"{QA}/{name}_search.png")
            pg.keyboard.press("Enter"); pg.wait_for_timeout(1200)
            pg.locator("#atlas").screenshot(path=f"{QA}/{name}_search_pick.png")
            pg.locator("#q").fill("")
            pg.evaluate("clearSel(); 0")
            # click a line in the middle of the South Atlantic
            pg.evaluate("map.setView([-20, -20], 4); 0"); pg.wait_for_timeout(900)
            box = pg.locator("#map").bounding_box(); pg.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2); pg.wait_for_timeout(900)
            pg.locator("#atlas").screenshot(path=f"{QA}/{name}_click.png")
            for sel in ("#voltaChart", "#brouwerChart", "#durChart", "#beltChart", "#routeTable", "#covChart", "#covTable", "#modChart"):
                pg.locator(sel).scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                pg.locator(sel).screenshot(path=f"{QA}/{name}_{sel[1:]}.png")
            assert pg.locator("#map .mfs-btn").count() == 1, "no full-screen button"
            pg.locator("#map").scroll_into_view_if_needed(); pg.locator("#map .mfs-btn").click(); pg.wait_for_timeout(900)
            pg.screenshot(path=f"{QA}/{name}_fullscreen.png")
            pg.locator("#map .mfs-btn").click(); pg.wait_for_timeout(400)
            sw = pg.evaluate("document.documentElement.scrollWidth"); assert sw <= vw + 1, (name, "horizontal scroll", sw)
            pg.close()
        pg = br.new_page(viewport={"width": 1280, "height": 900}, color_scheme="dark"); pg.route("**/*", route)
        pg.on("pageerror", lambda e: errs.append(("dark", "pageerror", str(e))))
        pg.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load"); pg.wait_for_function("window.READY === true", timeout=30000); pg.wait_for_timeout(1200)
        pg.screenshot(path=f"{QA}/dark_top.png"); pg.locator("#atlas").scroll_into_view_if_needed(); pg.wait_for_timeout(1000); pg.locator("#atlas").screenshot(path=f"{QA}/dark_map.png")
        pg.locator("#beltChart").scroll_into_view_if_needed(); pg.wait_for_timeout(300); pg.locator("#beltChart").screenshot(path=f"{QA}/dark_beltChart.png")
        br.close()
    srv.shutdown()
    print("console errors:", errs if errs else "none")
    for f in [os.path.join(ROOT, "index.html"), os.path.join(ROOT, "README.md"), *glob.glob(os.path.join(ROOT, "release", "blog", "*.html")),
              *glob.glob(os.path.join(ROOT, "release", "blog", "*.json")), *glob.glob(os.path.join(ROOT, "release", "zenodo", "*.json")),
              *glob.glob(os.path.join(ROOT, "reddit", "*.md")), *glob.glob(os.path.join(ROOT, "release", "paper", "*.tex"))]:
        if not os.path.exists(f):
            continue
        s = open(f, encoding="utf-8").read()
        if f.endswith(".html"):
            s = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", s, flags=re.S)
        if f.endswith(".md"):
            s = re.sub(r"(?m)^\|[-|: ]+\|$", "", s)
        if f.endswith(".tex"):
            s = re.sub(r"(?m)^%.*$", "", s).replace("\\-\\-", "")
        for bad in ("\u2014", "\u2013", "D" + "SIT", "D" + "CMS", "civil serv", "Civil Serv"):
            assert bad not in s, (f, bad)
        if not f.endswith(".tex"):
            assert "--" not in s, (f, "--")
    print("text checks passed")
    assert not errs


if __name__ == "__main__":
    run()
