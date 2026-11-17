// Bouwt de statische site in /site vanuit src/app.html.
// Gebruik: node tools/build.mjs   (daarna: python3 tools/og.py voor deelplaatjes)
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUT = path.join(ROOT, "site");
const BASE = "https://welkedresscode.nl";
const SITE = "Welke dresscode";

const app = fs.readFileSync(path.join(ROOT, "src/app.html"), "utf8");
const script = app.match(/<script>([\s\S]*)<\/script>/)[1];
const dataPart = script.split("const out=")[0];
const ctx = {};
vm.runInNewContext(dataPart + "\n;this.R={CODES,LOOKS,UI,figureSVG,norm};", ctx);
const { CODES, LOOKS, UI, figureSVG, norm } = ctx.R;

const esc = s => String(s).replace(/[&<>"]/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
const slug = s => norm(s).replace(/ /g, "-");
const nameOf = (c, l) => (l === "en" ? c.ne || c.n : c.n);
const pathOf = (c, l) => (l === "en" ? "/en/" : "/") + slug(nameOf(c, l)) + "/";
const ogOf = (c, l) => `/og/${l}-${slug(nameOf(c, l))}.jpg`;
const trim = (s, n) => (s.length <= n ? s : s.slice(0, s.lastIndexOf(" ", n - 1)) + "…");

// controle: unieke slugs en complete LOOKS
for (const l of ["nl", "en"]) {
  const seen = new Set();
  for (const c of CODES) {
    const p = pathOf(c, l);
    if (seen.has(p)) throw new Error("Dubbele slug: " + p);
    seen.add(p);
    if (!LOOKS[c.n]) throw new Error("Geen illustratie voor: " + c.n);
  }
}

const FAVICON = "data:image/svg+xml," + encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#7a4b2a"/><path d="M16 16 L6 10 L6 22Z M16 16 L26 10 L26 22Z" fill="#faf8f5"/><circle cx="16" cy="16" r="3" fill="#faf8f5"/></svg>`);

function card(c, l) {
  const t = UI[l], [u, m, w] = c[l], name = nameOf(c, l), L = LOOKS[c.n], idx = CODES.indexOf(c);
  const figs = `<div class="figs">${figureSVG("m", L[0], idx, esc(t.im + " " + name))}${figureSVG("w", L[1], idx, esc(t.iw + " " + name))}</div>`;
  return `<div class="card"><h2>${esc(name)}</h2><p>${esc(u)}</p>${figs}
    <div class="lbl">${t.men}</div><p>${esc(m)}</p>
    <div class="lbl">${t.women}</div><p>${esc(w)}</p></div>`;
}

function page({ l, title, desc, canonical, alt, og, body, ld, noindex, data }) {
  const t = UI[l];
  const head = [
    `<title>${esc(title)}</title>`,
    `<meta name="description" content="${esc(desc)}">`,
    noindex ? `<meta name="robots" content="noindex">` : `<link rel="canonical" href="${BASE}${canonical}">`,
    ...(alt ? [`<link rel="alternate" hreflang="nl" href="${BASE}${alt.nl}">`, `<link rel="alternate" hreflang="en" href="${BASE}${alt.en}">`, `<link rel="alternate" hreflang="x-default" href="${BASE}${alt.nl}">`] : []),
    `<link rel="icon" href="${FAVICON}">`,
    `<meta name="theme-color" content="#faf8f5">`,
    `<meta property="og:site_name" content="${SITE}">`,
    `<meta property="og:type" content="website">`,
    `<meta property="og:locale" content="${l === "en" ? "en_GB" : "nl_NL"}">`,
    `<meta property="og:title" content="${esc(title)}">`,
    `<meta property="og:description" content="${esc(desc)}">`,
    canonical ? `<meta property="og:url" content="${BASE}${canonical}">` : "",
    `<meta property="og:image" content="${BASE}${og || "/og/" + l + "-home.jpg"}">`,
    `<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">`,
    `<meta name="twitter:card" content="summary_large_image">`,
    ld ? `<script type="application/ld+json">${JSON.stringify(ld).replace(/</g, "\\u003c")}</script>` : "",
  ].filter(Boolean).join("\n");
  const attrs = Object.entries({ lang: l, ...data }).map(([k, v]) => ` data-${k}="${esc(v)}"`).join("");
  let html = app
    .replace('<html lang="nl">', `<html lang="${l}">`)
    .replace(/<title>[\s\S]*?<\/title>/, head)
    .replace("<body>", `<body${attrs}>`)
    .replace('<h1 id="title"></h1>', `<h1 id="title">${esc(t.title)}</h1>`)
    .replace(`data-l="nl" lang="nl"`, `data-l="nl" lang="nl" aria-pressed="${l === "nl"}"`)
    .replace(`data-l="en" lang="en"`, `data-l="en" lang="en" aria-pressed="${l === "en"}"`)
    .replace('spellcheck="false">', `spellcheck="false" placeholder="${esc(t.ph)}" aria-label="${esc(t.label)}"${data.code ? ` value="${esc(nameOf(CODES.find(c => c.n === data.code), l))}"` : ""}>`)
    .replace('<div id="out" aria-live="polite"></div>', `<div id="out" aria-live="polite">${body || ""}</div>`)
    .replace('<a id="all" href="/alle-dresscodes/">Alle dresscodes</a>', `<a id="all" href="${t.allUrl}">${t.all}</a>`);
  return html;
}

function write(rel, html) {
  const f = path.join(OUT, rel);
  fs.mkdirSync(path.dirname(f), { recursive: true });
  fs.writeFileSync(f, html);
}

// opnieuw beginnen (deelplaatjes in /site/og blijven staan)
for (const e of fs.existsSync(OUT) ? fs.readdirSync(OUT) : []) if (e !== "og") fs.rmSync(path.join(OUT, e), { recursive: true });

const urls = [];
const HOME = {
  nl: { title: "Welke dresscode? Uitleg van 50 dresscodes voor man en vrouw", desc: "Typ een dresscode en zie direct wat je aantrekt: van black tie en cocktail tot smart casual. Met uitleg en illustraties voor mannen en vrouwen." },
  en: { title: "What does this dress code mean? 50 dress codes explained", desc: "Type a dress code and instantly see what to wear: from black tie and cocktail to smart casual. With explanations and illustrations for men and women." },
};
const ALL = {
  nl: { title: "Alle dresscodes op een rij | Welke dresscode", desc: "Overzicht van 50 dresscodes, van white tie tot festival. Klik voor uitleg en voorbeelden voor man en vrouw.", h: "Alle dresscodes" },
  en: { title: "All dress codes at a glance | Welke dresscode", desc: "Overview of 50 dress codes, from white tie to festival. Click for explanations and examples for men and women.", h: "All dress codes" },
};
const FAQ = {
  nl: n => [[`Wat betekent dresscode ${n}?`, 0], [`Wat draag je als man bij dresscode ${n}?`, 1], [`Wat draag je als vrouw bij dresscode ${n}?`, 2]],
  en: n => [[`What does the ${n} dress code mean?`, 0], [`What should men wear for ${n}?`, 1], [`What should women wear for ${n}?`, 2]],
};

for (const l of ["nl", "en"]) {
  const t = UI[l];
  // home
  write(l === "en" ? "en/index.html" : "index.html", page({
    l, title: HOME[l].title, desc: HOME[l].desc, canonical: t.home, alt: { nl: "/", en: "/en/" }, data: { home: "1" },
    ld: { "@context": "https://schema.org", "@type": "WebSite", name: SITE, url: BASE + t.home, inLanguage: l },
  }));
  urls.push({ loc: t.home, alt: { nl: "/", en: "/en/" }, pr: "1.0" });

  // per dresscode
  for (const c of CODES) {
    const name = nameOf(c, l), [u] = c[l];
    const alt = { nl: pathOf(c, "nl"), en: pathOf(c, "en") };
    const desc = trim(u + (l === "en" ? " What to wear for men and women." : " Zo kleed je je als man en vrouw."), 158);
    const ld = [
      { "@context": "https://schema.org", "@type": "FAQPage", inLanguage: l,
        mainEntity: FAQ[l](name).map(([q, i]) => ({ "@type": "Question", name: q, acceptedAnswer: { "@type": "Answer", text: c[l][i] } })) },
      { "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: [
        { "@type": "ListItem", position: 1, name: SITE, item: BASE + t.home },
        { "@type": "ListItem", position: 2, name: ALL[l].h, item: BASE + t.allUrl },
        { "@type": "ListItem", position: 3, name, item: BASE + pathOf(c, l) } ] },
    ];
    write(pathOf(c, l).slice(1) + "index.html", page({
      l, title: t.pt(name), desc, canonical: pathOf(c, l), alt, og: ogOf(c, l), body: card(c, l), ld, data: { code: c.n },
    }));
    urls.push({ loc: pathOf(c, l), alt, pr: "0.8" });
  }

  // overzicht
  const sorted = [...CODES].sort((a, b) => nameOf(a, l).localeCompare(nameOf(b, l), l));
  const list = `<div class="card"><h2>${ALL[l].h}</h2><ul class="all">${sorted.map(c => `<li><a href="${pathOf(c, l)}">${esc(nameOf(c, l))}</a></li>`).join("")}</ul></div>`;
  write(t.allUrl.slice(1) + "index.html", page({
    l, title: ALL[l].title, desc: ALL[l].desc, canonical: t.allUrl, alt: { nl: UI.nl.allUrl, en: UI.en.allUrl }, body: list, data: { page: "all" },
  }));
  urls.push({ loc: t.allUrl, alt: { nl: UI.nl.allUrl, en: UI.en.allUrl }, pr: "0.6" });
}

// 404
write("404.html", page({
  l: "nl", title: "Pagina niet gevonden | Welke dresscode", desc: HOME.nl.desc, noindex: true,
  body: `<p class="muted">Deze pagina bestaat niet (meer). Typ hierboven een dresscode. / This page doesn't exist. Type a dress code above.</p>`, data: { page: "404" },
}));

// sitemap + robots
const today = new Date().toISOString().slice(0, 10);
fs.writeFileSync(path.join(OUT, "sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n` +
  urls.map(u => `<url><loc>${BASE}${u.loc}</loc><lastmod>${today}</lastmod><priority>${u.pr}</priority>` +
    `<xhtml:link rel="alternate" hreflang="nl" href="${BASE}${u.alt.nl}"/><xhtml:link rel="alternate" hreflang="en" href="${BASE}${u.alt.en}"/><xhtml:link rel="alternate" hreflang="x-default" href="${BASE}${u.alt.nl}"/></url>`).join("\n") +
  `\n</urlset>\n`);
fs.writeFileSync(path.join(OUT, "robots.txt"), `User-agent: *\nAllow: /\n\nSitemap: ${BASE}/sitemap.xml\n`);

// lijst voor de deelplaatjes
fs.writeFileSync(path.join(ROOT, "tools/og-list.json"), JSON.stringify({
  items: [
    ...["nl", "en"].map(l => ({ file: `${l}-home.jpg`, title: UI[l].title, sub: l === "en" ? "50 dress codes explained for men and women" : "50 dresscodes uitgelegd voor man en vrouw", m: figureSVG("m", LOOKS["Cocktail"][0], 9, ""), w: figureSVG("w", LOOKS["Cocktail"][1], 9, "") })),
    ...["nl", "en"].flatMap(l => CODES.map((c, i) => ({ file: `${l}-${slug(nameOf(c, l))}.jpg`, title: nameOf(c, l), sub: l === "en" ? "What to wear?" : "Wat trek je aan?",
      m: figureSVG("m", LOOKS[c.n][0], i, ""), w: figureSVG("w", LOOKS[c.n][1], i, "") }))),
  ],
}));

console.log(`Klaar: ${urls.length} pagina's + 404, sitemap en robots.txt in /site`);
