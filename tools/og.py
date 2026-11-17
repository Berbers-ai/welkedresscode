"""Maakt deelplaatjes (1200x630) voor WhatsApp/social in site/og/.
Gebruik: python3 tools/og.py   (na node tools/build.mjs)
"""
import json, pathlib, html
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "tools/og-list.json").read_text())
out = ROOT / "site/og"
out.mkdir(parents=True, exist_ok=True)

TPL = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;box-sizing:border-box}
body{width:1200px;height:630px;background:#faf8f5;display:flex;align-items:center;padding:0 70px;gap:60px;font-family:Georgia,'Times New Roman',serif;color:#1d1b19}
.txt{flex:1}
.k{font:600 22px system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#7a4b2a;margin-bottom:22px}
h1{font-weight:normal;font-size:__FS__px;line-height:1.08;letter-spacing:-.01em}
p{font-size:34px;color:#77706a;margin-top:22px}
.u{font:500 24px system-ui,sans-serif;color:#77706a;margin-top:46px}
.figs{display:flex;gap:18px}
.figs svg{width:250px;height:auto;display:block}
</style></head><body><div class="txt"><div class="k">Dresscode</div><h1>__T__</h1><p>__S__</p><div class="u">welkedresscode.nl</div></div>
<div class="figs">__M____W__</div></body></html>"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 630})
    for it in data["items"]:
        t = it["title"]
        fs = 76 if len(t) < 14 else 64 if len(t) < 22 else 54
        doc = (TPL.replace("__FS__", str(fs)).replace("__T__", html.escape(t)).replace("__S__", html.escape(it["sub"]))
               .replace("__M__", it["m"]).replace("__W__", it["w"]))
        pg.set_content(doc)
        pg.screenshot(path=str(out / it["file"]), type="jpeg", quality=82)
    b.close()
print(f"{len(data['items'])} deelplaatjes in site/og")
