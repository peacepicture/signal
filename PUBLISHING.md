# How this site publishes

`markfaizi.dev` is an Azure Static Web App served straight from this repo's
`main` branch. There is no build step: the repo tree *is* the URL tree, so a
file at `signal/2026-09-28.html` is served at `markfaizi.dev/signal/2026-09-28`.
Azure resolves extensionless paths by appending `.html`, so no `.html` ever
needs to appear in a link.

```
index.html                  markfaizi.dev            CV, edited by hand
404.html                    (any missing page)
staticwebapp.config.json    Azure routing + headers

signal/index.html           markfaizi.dev/signal            latest edition
signal/2026-09-28.html      markfaizi.dev/signal/2026-09-28 permalink
signal/archive.html         markfaizi.dev/signal/archive    generated

kabulledger/...             markfaizi.dev/kabulledger       same shape
loadfactor/...              markfaizi.dev/loadfactor        same shape
```

## Publishing an edition

Three recurring tasks write here — Signal (Mon & Thu), The Kabul Ledger
(Sundays), Load Factor (1st & 15th). Each run does the same four things:

1. Save the edition as `<section>/<YYYY-MM-DD>.html`, a byte-for-byte copy of
   the page that was published. Use the date the edition covers.
2. Run `python3 build.py`.
3. Commit and push to `main`.
4. Link to the **dated permalink** from the email, never to `/<section>`.

### Why the permalink matters

`/signal` always serves whichever edition is newest. An email sent today that
links to `/signal` would show a reader the wrong edition a week later. So the
email links to `/signal/2026-09-28`, which never changes. Use `/signal` only
where "the current edition" is what's meant — the CV, the archive page.

## What build.py does

For each publication folder it copies the newest `YYYY-MM-DD.html` to
`index.html`, then regenerates `archive.html` from the files present. It reads
each edition's `<title>` for the archive listing and otherwise leaves editions
untouched. It never writes the root `index.html`.

It is idempotent — running it twice gives the same result as running it once —
so a publishing run can always just call it rather than reasoning about state.
Adding a publication means adding one entry to `SECTIONS` in `build.py`.

## Deployment

Pushing to `main` triggers `.github/workflows/azure-static-web-apps-*.yml`,
which uploads the repo root. A push is live in roughly two to three minutes.
`cache-control` is 300 seconds, so a new edition appears within five minutes
even to a reader who just looked.

## Notes

- Editions are stored exactly as published. The pages are self-contained —
  inline CSS, inline SVG, fonts from Google's CDN, no relative asset paths —
  so they work unchanged at any depth and need no rewriting when moved.
- `/signal/index.html` duplicates the newest dated file. That is deliberate:
  50KB of duplication buys a front page that cannot break, instead of a
  config rewrite that has to be edited on every publish.
- The repo is public. Anything committed here is readable by anyone.
