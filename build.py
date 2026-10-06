#!/usr/bin/env python3
"""Regenerate everything on the site that is derived rather than written.

Each publication lives in its own folder. An edition is a file named
YYYY-MM-DD.html -- the page as it was published. For each folder this script:

  1. writes a managed <head> block into every edition: title, description,
     canonical URL, favicons and the Open Graph tags that make a link show a
     preview card in WhatsApp, iMessage, Slack, LinkedIn and the rest
  2. copies the newest edition to index.html, so /signal serves the latest
  3. regenerates archive.html, listing every edition newest first

It also writes the same head block into the CV (index.html) and 404.html,
and regenerates sitemap.xml.

The head block sits between <!-- site-head:start --> and <!-- site-head:end -->
markers. Anything inside the markers is rewritten on every run; everything
outside them is left alone. Running the script twice gives the same result as
running it once, so a publishing run can always just call it.

    python3 build.py
"""

import html
import re
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "https://markfaizi.dev"

SITE = {
    "title": "Mark Faizi · Data analyst",
    "description": "Data analyst working on competitor analysis, CRM "
                   "and automation that saves businesses time and money.",
    "site_name": "Mark Faizi",
    "icon": "site",
    "theme": ("#ECEBE6", "#131210"),
    "og_alt": "Mark Faizi, data analyst. Competitor analysis, CRM and "
              "automation.",
}

SECTIONS = [
    {
        "slug": "signal",
        "name": "Signal",
        "cadence": "Mondays and Thursdays",
        "blurb": "Technology, AI and finance. What happened, and why the "
                 "numbers mean what they mean.",
        "theme": ("#EDEAE7", "#141110"),
        "og_alt": "Signal: technology, AI and markets. Mondays and Thursdays "
                  "at markfaizi.dev/signal.",
    },
    {
        "slug": "kabulledger",
        "name": "The Kabul Ledger",
        "cadence": "Sundays",
        "blurb": "Afghanistan's economy for readers outside it. Half news, "
                 "half mechanism, because the news makes no sense without "
                 "the plumbing.",
        "theme": ("#EEEAE1", "#14120F"),
        "og_alt": "The Kabul Ledger: a weekly reading of Afghanistan's "
                  "economy, at markfaizi.dev/kabulledger.",
    },
    {
        "slug": "loadfactor",
        "name": "Load Factor",
        "cadence": "1st and 15th of the month",
        "blurb": "The business of escorted and guided touring -- who makes "
                 "money, how, and where the risk sits.",
        "theme": ("#ECEDE9", "#101311"),
        "og_alt": "Load Factor: the business of escorted touring, "
                  "fortnightly at markfaizi.dev/loadfactor.",
    },
]

EDITION_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.html$")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
LEDE_RE = re.compile(r'<p[^>]*class="lede"[^>]*>(.*?)</p>', re.I | re.S)
HEAD_RE = re.compile(r"<head[^>]*>", re.I)
BLOCK_RE = re.compile(r"\n?<!-- site-head:start.*?<!-- site-head:end -->\n?", re.S)


# ---------------------------------------------------------------- helpers

def editions(folder: Path):
    """Every edition in a folder, newest first."""
    found = []
    for path in folder.glob("*.html"):
        m = EDITION_RE.match(path.name)
        if m:
            found.append((date(int(m[1]), int(m[2]), int(m[3])), path))
    return sorted(found, key=lambda pair: pair[0], reverse=True)


def plain(fragment: str) -> str:
    """HTML fragment -> one line of plain text."""
    text = re.sub(r"<[^>]+>", "", fragment)
    return " ".join(html.unescape(text).split())


def clip(text: str, limit: int = 200) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:—-")
    return cut + "…"


def title_of(source: str, fallback: str) -> str:
    m = TITLE_RE.search(source)
    return plain(m[1]) if m else fallback


def lede_of(source: str, fallback: str) -> str:
    m = LEDE_RE.search(source)
    return clip(plain(m[1])) if m else fallback


def long_date(d: date) -> str:
    return d.strftime(f"%A {d.day} %B %Y")


def attr(text: str) -> str:
    return html.escape(text, quote=True)


def head_block(*, title, description, url, icon, theme, og_type, og_alt,
               site_name, published=None, with_title=True, noindex=False):
    light, dark = theme
    lines = ["<!-- site-head:start · written by build.py, edits inside are overwritten -->"]
    if with_title:
        lines.append(f"<title>{html.escape(title)}</title>")
    lines += [
        f'<meta name="description" content="{attr(description)}">',
    ]
    if noindex:
        lines.append('<meta name="robots" content="noindex">')
    if url:
        lines.append(f'<link rel="canonical" href="{url}">')
    lines += [
        f'<link rel="icon" href="/assets/{icon}/icon.svg" type="image/svg+xml">',
        f'<link rel="icon" href="/assets/{icon}/icon-32.png" sizes="32x32" type="image/png">',
        f'<link rel="apple-touch-icon" href="/assets/{icon}/apple-touch-icon.png">',
        '<link rel="manifest" href="/site.webmanifest">',
        f'<meta name="theme-color" content="{light}" media="(prefers-color-scheme: light)">',
        f'<meta name="theme-color" content="{dark}" media="(prefers-color-scheme: dark)">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:site_name" content="{attr(site_name)}">',
        f'<meta property="og:title" content="{attr(title)}">',
        f'<meta property="og:description" content="{attr(description)}">',
    ]
    if url:
        lines.append(f'<meta property="og:url" content="{url}">')
    lines += [
        f'<meta property="og:image" content="{BASE}/assets/{icon}/og.png">',
        '<meta property="og:image:type" content="image/png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{attr(og_alt)}">',
        '<meta property="og:locale" content="en_GB">',
    ]
    if published:
        lines.append(f'<meta property="article:published_time" content="{published.isoformat()}">')
    lines += [
        '<meta name="twitter:card" content="summary_large_image">',
        "<!-- site-head:end -->",
    ]
    return "\n".join(lines)


def with_block(source: str, block: str) -> str:
    """Return source with the managed block placed right after <head>."""
    source = BLOCK_RE.sub("", source, count=1)
    m = HEAD_RE.search(source)
    if not m:
        raise SystemExit("build.py: page has no <head> tag")
    return source[:m.end()] + "\n" + block + "\n" + source[m.end():]


def write_if_changed(path: Path, text: str, label: str) -> None:
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
        print(f"  {label}")


# ---------------------------------------------------------------- archive page

ARCHIVE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..600;1,6..72,300..500&family=Spectral:ital,wght@1,400&family=IBM+Plex+Mono:wght@400;500;600&family=Chakra+Petch:wght@600;700&display=swap">
<style>
:root{{
  --font-display:"TimeBurner","Chakra Petch","Eurostile","Bahnschrift","Trebuchet MS",sans-serif;
  --font-body:"Newsreader","Iowan Old Style",Georgia,serif;
  --font-editorial:"Spectral",Georgia,"Times New Roman",serif;
  --font-mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,monospace;
  --paper:#EDEBE7;--card:#F6F5F2;--ink:#15140F;--ink-soft:#56534A;--ink-faint:#7D7970;
  --accent:#2E3F6B;--second:#9A6B2F;--rule:#C9C5BD;color-scheme:light;
}}
@media (prefers-color-scheme:dark){{
  :root:not([data-theme="light"]){{
    --paper:#131210;--card:#1E1C19;--ink:#EBE8E2;--ink-soft:#A39E95;--ink-faint:#837E75;
    --accent:#8CA6DE;--second:#D3A258;--rule:#36332D;color-scheme:dark;
  }}
}}
:root[data-theme="dark"]{{
  --paper:#131210;--card:#1E1C19;--ink:#EBE8E2;--ink-soft:#A39E95;--ink-faint:#837E75;
  --accent:#8CA6DE;--second:#D3A258;--rule:#36332D;color-scheme:dark;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--font-body);
  font-size:20px;line-height:1.62;font-weight:380;-webkit-text-size-adjust:100%;
  -webkit-font-smoothing:antialiased}}
.wrap{{max-width:760px;margin:0 auto;padding:0 24px}}
a{{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}}
a:focus-visible{{outline:2px solid var(--accent);outline-offset:3px}}
.up{{font-family:var(--font-mono);font-size:13px;letter-spacing:.09em;text-transform:uppercase;
  display:inline-block;padding-block:34px 0;color:var(--ink-soft);text-decoration:none}}
.up:hover{{color:var(--accent)}}
header{{padding-block:16px 18px;border-bottom:2px solid var(--ink)}}
h1{{font-family:var(--font-display);font-weight:700;text-transform:uppercase;
  font-size:clamp(2.1rem,6.6vw,3.3rem);line-height:.96;letter-spacing:.035em;margin:0}}
.blurb{{font-family:var(--font-editorial);font-style:italic;font-size:1.16rem;
  color:var(--ink-soft);margin:14px 0 0;max-width:54ch}}
.meta{{font-family:var(--font-mono);font-size:13px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--ink-faint);margin:16px 0 0;display:flex;flex-wrap:wrap;gap:6px 20px}}
.latest{{display:block;background:var(--card);border:1px solid var(--rule);
  border-left:3px solid var(--second);padding:20px 22px;margin:30px 0 40px;
  text-decoration:none;color:inherit}}
.latest:hover{{border-left-color:var(--accent)}}
.latest .lk{{font-family:var(--font-mono);font-size:12px;letter-spacing:.13em;
  text-transform:uppercase;color:var(--second);display:block;margin-bottom:7px;font-weight:600}}
.latest .lt{{font-family:var(--font-display);font-weight:700;font-size:1.3rem;
  letter-spacing:.02em;display:block;color:var(--ink)}}
h2{{font-family:var(--font-display);font-weight:700;text-transform:uppercase;
  font-size:.92rem;letter-spacing:.14em;color:var(--second);margin:0 0 4px}}
ol{{list-style:none;margin:0;padding:0;border-top:1px solid var(--rule)}}
li{{border-bottom:1px solid var(--rule)}}
li a{{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;
  gap:4px 18px;padding:15px 2px;text-decoration:none;color:inherit}}
li a:hover{{background:var(--card)}}
li .t{{font-weight:500;font-size:1.08rem}}
li .d{{font-family:var(--font-mono);font-size:13px;letter-spacing:.05em;
  color:var(--ink-faint);white-space:nowrap}}
footer{{font-family:var(--font-mono);font-size:12.5px;letter-spacing:.05em;
  color:var(--ink-faint);padding-block:24px 50px;margin-top:38px;border-top:2px solid var(--ink)}}
@media (max-width:560px){{
  body{{font-size:19px}}
  .wrap{{padding:0 16px}}
  .up,.meta,li .d,footer{{font-size:13px}}
  .blurb{{font-size:1.1rem}}
}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important;animation:none!important}}}}
</style>
</head>
<body>
<div class="wrap">
<a class="up" href="/">&larr; markfaizi.dev</a>
<header>
  <h1>{name}</h1>
  <p class="blurb">{blurb}</p>
  <div class="meta"><span>{cadence}</span><span>{count}</span></div>
</header>
{latest}
<h2>Archive</h2>
<ol>
{rows}
</ol>
<footer>{name} · markfaizi.dev · {count}</footer>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------- build

def build_root_pages(sitemap):
    """The CV and the 404 page get the site-wide head block."""
    cv = ROOT / "index.html"
    if cv.exists():
        block = head_block(
            title=SITE["title"], description=SITE["description"], url=f"{BASE}/",
            icon=SITE["icon"], theme=SITE["theme"], og_type="profile",
            og_alt=SITE["og_alt"], site_name=SITE["site_name"])
        write_if_changed(cv, with_block(cv.read_text(encoding="utf-8"), block), "index.html (CV) head")
        sitemap.append((f"{BASE}/", None))

    nf = ROOT / "404.html"
    if nf.exists():
        block = head_block(
            title="Not found · markfaizi.dev", description=SITE["description"], url=None,
            icon=SITE["icon"], theme=SITE["theme"], og_type="website",
            og_alt=SITE["og_alt"], site_name=SITE["site_name"], noindex=True)
        write_if_changed(nf, with_block(nf.read_text(encoding="utf-8"), block), "404.html head")


def build_section(sec, sitemap):
    folder = ROOT / sec["slug"]
    if not folder.is_dir():
        print(f"  skip {sec['slug']}/ (no such folder)")
        return
    found = editions(folder)
    if not found:
        print(f"  skip {sec['slug']}/ (no editions yet)")
        return

    titles = {}
    # 1. head block in every edition
    for d, path in found:
        source = path.read_text(encoding="utf-8")
        title = title_of(source, f"{sec['name']} — {d.day} {d.strftime('%B')}")
        titles[path] = title
        url = f"{BASE}/{sec['slug']}/{path.stem}"
        block = head_block(
            title=title, description=lede_of(source, sec["blurb"]), url=url,
            icon=sec["slug"], theme=sec["theme"], og_type="article",
            og_alt=sec["og_alt"], site_name=f"{sec['name']} · markfaizi.dev",
            published=d)
        write_if_changed(path, with_block(source, block), f"{sec['slug']}/{path.name} head")
        sitemap.append((url, d))

    # 2. newest edition becomes the front page (canonical stays the permalink)
    newest_date, newest_path = found[0]
    index = folder / "index.html"
    if not index.exists() or index.read_bytes() != newest_path.read_bytes():
        shutil.copyfile(newest_path, index)
        print(f"  {sec['slug']}/index.html <- {newest_path.name}")

    # 3. archive
    rows = "\n".join(
        f'  <li><a href="/{sec["slug"]}/{path.stem}"><span class="t">{html.escape(titles[path])}</span>'
        f'<span class="d">{long_date(d)}</span></a></li>'
        for d, path in found)
    latest = (f'<a class="latest" href="/{sec["slug"]}"><span class="lk">Current edition</span>'
              f'<span class="lt">{html.escape(titles[newest_path])}</span></a>')
    count = f"{len(found)} edition" + ("s" if len(found) != 1 else "")
    page = ARCHIVE_TEMPLATE.format(
        name=html.escape(sec["name"]), blurb=html.escape(sec["blurb"]),
        cadence=html.escape(sec["cadence"]), count=count, latest=latest, rows=rows)
    url = f"{BASE}/{sec['slug']}/archive"
    block = head_block(
        title=f"{sec['name']} · Archive", description=f"Every edition of {sec['name']}. {sec['blurb']}",
        url=url, icon=sec["slug"], theme=sec["theme"], og_type="website",
        og_alt=sec["og_alt"], site_name=f"{sec['name']} · markfaizi.dev")
    write_if_changed(folder / "archive.html", with_block(page, block), f"{sec['slug']}/archive.html ({count})")
    sitemap.append((url, newest_date))


def build_sitemap(entries):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, d in entries:
        lastmod = f"<lastmod>{d.isoformat()}</lastmod>" if d else ""
        lines.append(f"  <url><loc>{url}</loc>{lastmod}</url>")
    lines.append("</urlset>")
    write_if_changed(ROOT / "sitemap.xml", "\n".join(lines) + "\n", f"sitemap.xml ({len(entries)} urls)")


def main() -> None:
    sitemap = []
    build_root_pages(sitemap)
    for sec in SECTIONS:
        build_section(sec, sitemap)
    build_sitemap(sitemap)
    print("build.py: done")


if __name__ == "__main__":
    main()
