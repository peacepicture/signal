#!/usr/bin/env python3
"""Regenerate the site's navigation pages from the editions on disk.

Each publication lives in its own folder. An edition is a file named
YYYY-MM-DD.html -- a byte-for-byte copy of that day's published page.
This script does two things per folder, and nothing else:

  1. copies the newest edition to index.html, so /signal serves the latest
  2. regenerates archive.html, listing every edition newest first

It never touches the editions themselves, and never touches the root
index.html (the CV). Running it twice produces the same result as once,
so a publishing run can always just call it.

    python3 build.py
"""

import re
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SECTIONS = [
    {
        "slug": "signal",
        "name": "Signal",
        "cadence": "Mondays and Thursdays",
        "blurb": "Technology, AI and finance. What happened, and why the "
                 "numbers mean what they mean.",
    },
    {
        "slug": "kabulledger",
        "name": "The Kabul Ledger",
        "cadence": "Sundays",
        "blurb": "Afghanistan's economy for readers outside it. Half news, "
                 "half mechanism, because the news makes no sense without "
                 "the plumbing.",
    },
    {
        "slug": "loadfactor",
        "name": "Load Factor",
        "cadence": "1st and 15th of the month",
        "blurb": "The business of escorted and guided touring -- who makes "
                 "money, how, and where the risk sits.",
    },
]

EDITION_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.html$")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)


def editions(folder: Path):
    """Every edition in a folder, newest first."""
    found = []
    for path in sorted(folder.glob("*.html")):
        m = EDITION_RE.match(path.name)
        if m:
            found.append((date(int(m[1]), int(m[2]), int(m[3])), path))
    return sorted(found, key=lambda pair: pair[0], reverse=True)


def title_of(path: Path, fallback: str) -> str:
    m = TITLE_RE.search(path.read_text(encoding="utf-8", errors="replace"))
    return " ".join(m[1].split()) if m else fallback


def long_date(d: date) -> str:
    return d.strftime(f"%A {d.day} %B %Y")


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


ARCHIVE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{name} — archive</title>
<meta name="description" content="Every edition of {name}, newest first.">
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


def main() -> None:
    for sec in SECTIONS:
        folder = ROOT / sec["slug"]
        if not folder.is_dir():
            print(f"  skip {sec['slug']}/ (no such folder)")
            continue

        found = editions(folder)
        if not found:
            print(f"  skip {sec['slug']}/ (no editions yet)")
            continue

        newest_date, newest_path = found[0]

        # 1. the newest edition becomes the folder's front page
        index = folder / "index.html"
        newest_bytes = newest_path.read_bytes()
        if not index.exists() or index.read_bytes() != newest_bytes:
            shutil.copyfile(newest_path, index)
            print(f"  {sec['slug']}/index.html <- {newest_path.name}")

        # 2. the archive page lists everything
        rows = "\n".join(
            '  <li><a href="/{slug}/{stem}"><span class="t">{title}</span>'
            '<span class="d">{when}</span></a></li>'.format(
                slug=sec["slug"],
                stem=path.stem,
                title=esc(title_of(path, sec["name"])),
                when=long_date(d),
            )
            for d, path in found
        )

        latest = (
            '<a class="latest" href="/{slug}">'
            '<span class="lk">Current edition</span>'
            '<span class="lt">{title}</span></a>'
        ).format(slug=sec["slug"], title=esc(title_of(newest_path, sec["name"])))

        count = f"{len(found)} edition" + ("s" if len(found) != 1 else "")

        html = ARCHIVE_TEMPLATE.format(
            name=esc(sec["name"]),
            blurb=esc(sec["blurb"]),
            cadence=esc(sec["cadence"]),
            count=count,
            latest=latest,
            rows=rows,
        )
        archive = folder / "archive.html"
        if not archive.exists() or archive.read_text(encoding="utf-8") != html:
            archive.write_text(html, encoding="utf-8")
            print(f"  {sec['slug']}/archive.html ({count})")

    print("build.py: done")


if __name__ == "__main__":
    main()
