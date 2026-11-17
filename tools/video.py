"""Korte staande video's (1080x1920, 15 s) voor TikTok, Reels en Shorts.
Gebruik: python3 tools/video.py OUTMAP slug1 slug2 ...   (na node tools/build.mjs)
De slugs zijn bestandsnamen uit tools/pin-list.json zonder taal en extensie, bijv. black-tie of dresscode-gala.
"""
import html, json, pathlib, subprocess, sys, os
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
want = sys.argv[2:]
items = {it["file"][3:-4]: it for it in json.loads((ROOT / "tools/pin-list.json").read_text())["items"] if it["l"] == "nl"}

CSS = """*{margin:0;box-sizing:border-box}
body{width:1080px;height:1920px;background:#faf8f5;font-family:Georgia,'Times New Roman',serif;color:#1d1b19;overflow:hidden;position:relative}
.k{font:600 40px system-ui,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#7a4b2a}
h1{font-weight:normal;letter-spacing:-.015em;line-height:1.04}
.url{font:600 46px system-ui,sans-serif;color:#1d1b19}
.muted{color:#77706a}
svg{display:block;height:auto}
"""

def page(body):
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"

def fs(t, big=150):
    n = len(t)
    return big if n < 14 else int(big * .8) if n < 24 else int(big * .62) if n < 40 else int(big * .5)

def scenes(it):
    occ = it["kind"] == "occ"
    title = it["title"] if occ else it["title"] + "?"
    kicker = "Outfit-tips" if occ else "Wat betekent dresscode"
    hook = page(f"""<div style="padding:220px 150px 0 90px"><div class="k">{kicker}</div>
      <h1 style="font-size:{fs(title)}px;margin-top:30px">{html.escape(title)}</h1>
      <p class="muted" style="font-size:54px;margin-top:36px">Uitleg in 15 seconden</p></div>
      <div style="position:absolute;bottom:400px;left:0;right:0;display:flex;gap:30px;justify-content:center;padding-right:60px">
      <div style="width:360px">{it['svgM']}</div><div style="width:360px">{it['svgW']}</div></div>""")
    def person(lbl, svg, text):
        return page(f"""<div style="padding:150px 150px 0 90px"><div class="k">{html.escape(title if occ else it['title'])}</div>
          <h1 style="font-size:104px;margin-top:16px">{lbl}</h1></div>
          <div style="display:flex;justify-content:center;margin:34px 60px 0 0"><div style="width:400px">{svg}</div></div>
          <p style="font-size:{56 if len(text) < 120 else 48}px;line-height:1.3;padding:36px 150px 0 90px">{html.escape(text)}</p>""")
    outro = page(f"""<div style="padding:220px 150px 0;text-align:center"><div class="k">Twijfel je over een dresscode?</div>
      <h1 style="font-size:100px;margin-top:36px">Typ hem in en zie direct wat je aantrekt</h1>
      <div class="url" style="margin-top:70px">welkedresscode.nl</div>
      <p class="muted" style="font-size:44px;margin-top:20px">70 dresscodes en gelegenheden</p></div>
      <div style="position:absolute;bottom:400px;left:0;right:0;display:flex;gap:30px;justify-content:center;padding-right:60px">
      <div style="width:330px">{it['svgM']}</div><div style="width:330px">{it['svgW']}</div></div>""")
    return [(hook, 3.6), (person("Voor mannen", it["svgM"], it["m"]), 4.6), (person("Voor vrouwen", it["svgW"], it["w"]), 4.6), (outro, 3.2)]

FADE = .4
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    for slug in want:
        it = items[slug]; tmp = out / f"_{slug}"; tmp.mkdir(exist_ok=True)
        sc = scenes(it); imgs = []
        for i, (doc, _) in enumerate(sc):
            pg.set_content(doc); f = tmp / f"s{i}.png"; pg.screenshot(path=str(f)); imgs.append(f)
        # één encode per video, met crossfades binnen het bestand
        args = ["ffmpeg", "-y", "-loglevel", "error"]
        for f, (_, d) in zip(imgs, sc):
            args += ["-framerate", "30", "-loop", "1", "-t", str(d), "-i", str(f)]
        chain, last, t = [], "[0:v]", 0
        for i in range(1, len(sc)):
            t += sc[i - 1][1] - FADE
            lbl = f"[x{i}]"
            chain.append(f"{last}[{i}:v]xfade=transition=slideleft:duration={FADE}:offset={t:.2f}{lbl}")
            last = lbl
        chain.append(f"{last}format=yuv420p[v]")
        tmpout = out / f"{slug}.tmp.mp4"
        args += ["-filter_complex", ";".join(chain), "-map", "[v]", "-r", "30", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                 "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(tmpout)]
        subprocess.run(args, check=True)
        os.replace(tmpout, out / f"{slug}.mp4")
        for f in imgs: f.unlink()
        tmp.rmdir()
        print("klaar:", slug)
    b.close()
