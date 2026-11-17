"""Maakt Pinterest-plaatjes (1000x1500) in site/pins/ en upload-bestanden in pinterest/.
Gebruik: python3 tools/pins.py   (na node tools/build.mjs)
"""
import csv, datetime, html, json, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
items = json.loads((ROOT / "tools/pin-list.json").read_text())["items"]
img_dir = ROOT / "site/pins"; img_dir.mkdir(parents=True, exist_ok=True)
csv_dir = ROOT / "pinterest"; csv_dir.mkdir(exist_ok=True)
BASE = "https://welkedresscode.nl"

T = {
  "nl": {"kicker": "Dresscode", "kicker_occ": "Outfit-tips", "sub": "Wat trek je aan? Tips voor man & vrouw", "men": "Man", "women": "Vrouw",
         "often": "Vaak gevraagd", "board_code": "Dresscodes uitgelegd", "board_occ": "Wat trek je aan? Outfit-tips",
         "kw": "dresscode, {t}, wat trek je aan, outfit man, outfit vrouw, kledingadvies"},
  "en": {"kicker": "Dress code", "kicker_occ": "Outfit guide", "sub": "What to wear: tips for men & women", "men": "Men", "women": "Women",
         "often": "Common dress codes", "board_code": "Dress codes explained", "board_occ": "What to wear: outfit guides",
         "kw": "dress code, {t}, what to wear, men's outfit, women's outfit, style guide"},
}

def trim(s, n):
    return s if len(s) <= n else s[: s.rfind(" ", 0, n - 1)] + "…"

TPL = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;box-sizing:border-box}
body{width:1000px;height:1500px;background:#faf8f5;font-family:Georgia,'Times New Roman',serif;color:#1d1b19;padding:80px 70px 60px;display:flex;flex-direction:column}
.k{font:600 26px system-ui,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#7a4b2a}
h1{font-weight:normal;font-size:__FS__px;line-height:1.05;letter-spacing:-.015em;margin-top:18px}
.sub{font-size:34px;color:#77706a;margin-top:18px}
.figs{display:flex;gap:26px;margin:44px 0 36px;justify-content:center}
.figs svg{width:405px;height:auto;display:block}
.tips{display:grid;grid-template-columns:1fr 1fr;gap:30px}
.lbl{font:600 22px system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#7a4b2a;margin-bottom:8px}
.tips p{font-size:28px;line-height:1.35}
.foot{margin-top:auto;display:flex;justify-content:space-between;align-items:center;border-top:2px solid #e3ddd5;padding-top:26px;font:500 28px system-ui,sans-serif;color:#77706a}
.foot b{color:#1d1b19;font-weight:600}
</style></head><body>
<div class="k">__K__</div><h1>__T__</h1><div class="sub">__S__</div>
<div class="figs">__M____W__</div>
<div class="tips">__TIPS__</div>
<div class="foot"><b>welkedresscode.nl</b><span>__F__</span></div>
</body></html>"""

rows = {"nl": [], "en": []}
start = datetime.date.today() + datetime.timedelta(days=1)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1000, "height": 1500})
    for it in items:
        l, t = it["l"], T[it["l"]]
        title = it["title"]
        fs = 96 if len(title) < 16 else 78 if len(title) < 26 else 62
        if it["kind"] == "code":
            tips = f'<div><div class="lbl">{t["men"]}</div><p>{html.escape(trim(it["m"], 110))}</p></div><div><div class="lbl">{t["women"]}</div><p>{html.escape(trim(it["w"], 110))}</p></div>'
            k, sub, foot = t["kicker"], t["sub"], ("Dresscodes A–Z" if l == "nl" else "Dress codes A–Z")
        else:
            tips = f'<div><div class="lbl">{t["men"]}</div><p>{html.escape(trim(it["m"], 110))}</p></div><div><div class="lbl">{t["women"]}</div><p>{html.escape(trim(it["w"], 110))}</p></div>'
            k, sub, foot = t["kicker_occ"], " · ".join(it["codes"]), ("Tips voor man & vrouw" if l == "nl" else "Tips for men & women")
        doc = (TPL.replace("__FS__", str(fs)).replace("__K__", html.escape(k)).replace("__T__", html.escape(title))
               .replace("__S__", html.escape(sub)).replace("__M__", it["svgM"]).replace("__W__", it["svgW"])
               .replace("__TIPS__", tips).replace("__F__", html.escape(foot)))
        pg.set_content(doc)
        pg.screenshot(path=str(img_dir / it["file"]), type="jpeg", quality=84)
        n = len(rows[l])
        when = datetime.datetime.combine(start + datetime.timedelta(days=n % 13), datetime.time(9 + (n // 13) * 2 % 12, 0))
        desc = trim(f'{it["u"]} {t["men"]}: {it["m"]} {t["women"]}: {it["w"]}', 480)
        rows[l].append({
            "Title": trim((f'{"Dresscode" if l == "nl" else "Dress code"}: {title} – {"wat trek je aan?" if l == "nl" else "what to wear"}' if it["kind"] == "code" else title), 100),
            "Media URL": f'{BASE}/pins/{it["file"]}',
            "Pinterest board": t["board_code"] if it["kind"] == "code" else t["board_occ"],
            "Thumbnail": "",
            "Description": desc,
            "Link": it["link"],
            "Publish date": when.strftime("%Y-%m-%dT%H:%M:%S"),
            "Keywords": t["kw"].format(t=title.lower()),
        })
    b.close()

for l, rs in rows.items():
    old = csv_dir / f"pinterest-{l}.csv"
    if old.exists():
        seen = {r["Title"] for r in csv.DictReader(open(old, encoding="utf-8"))}
        fresh = [r for r in rs if r["Title"] not in seen]
        if fresh:
            with open(csv_dir / f"pinterest-{l}-nieuw.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(fresh[0].keys())); w.writeheader(); w.writerows(fresh)
            print(l, len(fresh), "nieuwe pins in", f"pinterest-{l}-nieuw.csv")
    with open(old, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0].keys()))
        w.writeheader(); w.writerows(rs)
print({l: len(r) for l, r in rows.items()}, "pins; afbeeldingen in site/pins, upload-bestanden in pinterest/")
