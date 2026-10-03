#!/usr/bin/env python3
"""Editorial memory for Signal, The Kabul Ledger and Load Factor.

Every scheduled run starts with no memory of the last one. This file gives it
one. Each publication keeps memory/<slug>.json: what every edition covered,
which stories are still worth following, which explainers have been taught,
which headlines, section titles and charts have already been used.

    python3 tools/memory.py brief  <slug>               before research: what to avoid, what to follow up
    python3 tools/memory.py check  <slug> <edition.html> before publishing: flags anything that echoes recent editions
    python3 tools/memory.py schema <slug>               prints a blank entry to fill in
    python3 tools/memory.py add    <slug> <entry.json>  after publishing: records the edition

slug is one of: signal, kabulledger, loadfactor
"""

import difflib
import html
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEM = ROOT / "memory"
BASE = "https://markfaizi.dev"

PUBS = {
    "signal": {
        "name": "Signal", "window": 6, "max_followups": 3, "fixed_sections": False,
        "themes": ["rates-bonds", "oil-energy-war", "us-macro", "ai-safety-agents", "ai-regulation",
                   "ai-money", "ai-infrastructure", "ai-products-research", "security-breaches",
                   "consumer-tech", "deals-corporate", "crypto", "science-space", "global-economy"],
    },
    "kabulledger": {
        "name": "The Kabul Ledger", "window": 4, "max_followups": 1, "fixed_sections": True,
        "themes": ["trade-transit", "prices-livelihoods", "money-banking", "aid", "state-budget",
                   "returnees-labour", "resources-energy", "water-climate"],
        "areas": ["plumbing", "earn-and-spend", "trade-and-resources"],
    },
    "loadfactor": {
        "name": "Load Factor", "window": 4, "max_followups": 1, "fixed_sections": True,
        "themes": ["risk-guarantees", "results-ownership", "regulation", "demand-distribution",
                   "supply-operations", "ai", "insolvency"],
        "areas": ["unit-economics", "distribution-demand", "regulation-risk-money", "ai-integration"],
        "methods": ["companies-house", "atol-register", "abta-membership", "brochure-terms"],
        "companies_house_every_days": 30,
    },
}

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STOP = set("""a an the and or but of to in on at for with by from as is are was were be been it its
this that these those than then into over after before about again not no now new more most its
their there they them his her our your you we he she will would can could has have had do does
did one two three four five six seven eight nine ten per cent percent""".split())


# ------------------------------------------------------------------ storage

def die(msg):
    sys.exit(f"memory.py: {msg}")


def pub(slug):
    if slug not in PUBS:
        die(f"unknown publication '{slug}' (use one of: {', '.join(PUBS)})")
    return PUBS[slug]


def load(slug):
    pub(slug)
    p = MEM / f"{slug}.json"
    if not p.exists():
        return {"publication": slug, "editions": [], "threads": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save(slug, mem):
    MEM.mkdir(exist_ok=True)
    mem["editions"].sort(key=lambda e: e["date"])
    (MEM / f"{slug}.json").write_text(json.dumps(mem, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def d(s):
    return date.fromisoformat(s)


def short(s):
    return s[5:] if s else "—"


# ------------------------------------------------------------------ text similarity

def norm(s):
    s = html.unescape(s).lower()
    s = re.sub(r"[’']", "", s)
    return " ".join(re.sub(r"[^a-z0-9$%. ]+", " ", s).split())


def words(s):
    return {w for w in norm(s).split() if len(w) > 2 and w not in STOP}


def similar(a, b):
    """Return a 0–1 score: the larger of sequence similarity and content-word overlap."""
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    seq = difflib.SequenceMatcher(None, na, nb).ratio()
    wa, wb = words(a), words(b)
    jac = len(wa & wb) / len(wa | wb) if wa and wb else 0.0
    return max(seq, jac)


# ------------------------------------------------------------------ schema / add

def template(slug):
    p = pub(slug)
    t = {
        "date": "YYYY-MM-DD",
        "title": f"{p['name'].replace('The ', '')} — D Month",
        "lede": "The edition's opening sentence(s), exactly as published.",
        "lead_theme": f"one of: {', '.join(p['themes'])}",
        "sections": [] if p["fixed_sections"] else ["Section title as published", "..."],
        "items": [{
            "slug": "short-story-id-reused-across-editions",
            "theme": f"one of: {', '.join(p['themes'])}",
            "kind": "new | followup",
            "headline": "Headline as published",
            "gist": "One line with the key fact or figure, so a later run knows where the story stood.",
        }],
        "visuals": ["one short line per chart or diagram, e.g. 'yield curve, Monday v Friday, line chart'"],
        "watch": [{"text": "What the edition told readers to watch", "due": "YYYY-MM-DD or null"}],
        "threads_open": [{"slug": "story-id", "question": "What is unresolved and worth checking",
                          "next_check": "YYYY-MM-DD or null"}],
        "threads_closed": ["story-id of any thread this edition resolved"],
    }
    if "areas" in p:
        t["explainer"] = {"area": f"one of: {', '.join(p['areas'])}", "topic": "What the explainer taught, in one line"}
    if "methods" in p:
        t["method"] = f"one of: {', '.join(p['methods'])} (the colophon's check-it-yourself note)"
        t["companies_house"] = {"company": "Operator looked up this edition, or set the whole field to null",
                                "finding": "What the filings showed"}
    return t


def validate(slug, e):
    p = pub(slug)
    errs = []
    def need(k, typ):
        if k not in e:
            errs.append(f"missing '{k}'")
        elif not isinstance(e[k], typ):
            errs.append(f"'{k}' should be {typ.__name__}")
    for k, typ in [("date", str), ("title", str), ("lede", str), ("lead_theme", str), ("sections", list),
                   ("items", list), ("visuals", list), ("watch", list), ("threads_open", list),
                   ("threads_closed", list)]:
        need(k, typ)
    if errs:
        return errs
    if not DATE_RE.match(e["date"]):
        errs.append("date must be YYYY-MM-DD")
    if e["lead_theme"] not in p["themes"]:
        errs.append(f"lead_theme '{e['lead_theme']}' is not one of {p['themes']}")
    if not e["items"]:
        errs.append("items is empty")
    for i, it in enumerate(e["items"]):
        for k in ("slug", "theme", "kind", "headline"):
            if not it.get(k):
                errs.append(f"items[{i}] missing '{k}'")
        if it.get("slug") and not SLUG_RE.match(it["slug"]):
            errs.append(f"items[{i}].slug '{it['slug']}' must be lowercase-with-hyphens")
        if it.get("theme") and it["theme"] not in p["themes"]:
            errs.append(f"items[{i}].theme '{it['theme']}' is not one of {p['themes']}")
        if it.get("kind") not in ("new", "followup"):
            errs.append(f"items[{i}].kind must be 'new' or 'followup'")
    for i, t in enumerate(e["threads_open"]):
        if not t.get("slug") or not SLUG_RE.match(t["slug"]) or not t.get("question"):
            errs.append(f"threads_open[{i}] needs a lowercase-hyphen 'slug' and a 'question'")
        nc = t.get("next_check")
        if nc and not DATE_RE.match(nc):
            errs.append(f"threads_open[{i}].next_check must be YYYY-MM-DD or null")
    if "areas" in p:
        ex = e.get("explainer")
        if not isinstance(ex, dict) or ex.get("area") not in p["areas"] or not ex.get("topic"):
            errs.append(f"explainer needs 'area' (one of {p['areas']}) and 'topic'")
    if "methods" in p:
        if e.get("method") not in p["methods"]:
            errs.append(f"method must be one of {p['methods']}")
        ch = e.get("companies_house", None)
        if ch is not None and not (isinstance(ch, dict) and ch.get("company")):
            errs.append("companies_house must be null or have a 'company'")
    return errs


def add(slug, path):
    e = json.loads(Path(path).read_text(encoding="utf-8"))
    errs = validate(slug, e)
    if errs:
        die("entry rejected:\n  - " + "\n  - ".join(errs))
    e["url"] = f"{BASE}/{slug}/{e['date']}"
    mem = load(slug)
    mem["editions"] = [x for x in mem["editions"] if x["date"] != e["date"]] + [e]

    threads = {t["slug"]: t for t in mem["threads"]}
    covered = {it["slug"] for it in e["items"]}
    for s in covered:
        if s in threads and threads[s]["status"] == "open":
            threads[s]["last_seen"] = e["date"]
    for t in e["threads_open"]:
        old = threads.get(t["slug"], {})
        threads[t["slug"]] = {
            "slug": t["slug"], "question": t["question"], "status": "open",
            "opened": old.get("opened", e["date"]), "last_seen": e["date"],
            "next_check": t.get("next_check"),
        }
    for s in e["threads_closed"]:
        if s in threads:
            threads[s]["status"] = "closed"
            threads[s]["closed"] = e["date"]
    cutoff = (d(e["date"]) - timedelta(days=120)).isoformat()
    mem["threads"] = sorted(
        (t for t in threads.values() if t["status"] == "open" or t.get("closed", "9999") >= cutoff),
        key=lambda t: t["slug"])

    # keep detail for the last 60 editions; older ones keep only what freshness checks need
    eds = sorted(mem["editions"], key=lambda x: x["date"])
    for old in eds[:-60]:
        for k in ("visuals", "watch", "threads_open", "threads_closed"):
            old.pop(k, None)
        for it in old.get("items", []):
            it.pop("gist", None)
    mem["editions"] = eds
    save(slug, mem)
    print(f"memory.py: recorded {slug} {e['date']} — {len(e['items'])} items, "
          f"{sum(1 for t in mem['threads'] if t['status'] == 'open')} open threads")


# ------------------------------------------------------------------ brief

def brief(slug, today=None):
    p = pub(slug)
    mem = load(slug)
    today = today or date.today()
    eds = sorted(mem["editions"], key=lambda e: e["date"])
    if not eds:
        print(f"MEMORY BRIEF · {p['name']}\nNo editions recorded yet. Everything is fresh.")
        return
    win = eds[-p["window"]:]
    last = eds[-1]
    out = []
    w = out.append
    w(f"MEMORY BRIEF · {p['name']} · for the edition of {today.isoformat()}")
    w(f"Last edition: {last['date']}  \"{last['title']}\"  {last.get('url', '')}")
    w(f"Recent window: the last {len(win)} editions, {win[0]['date']} to {win[-1]['date']}")

    # leads
    w("\nLEAD THEME OF RECENT EDITIONS")
    for e in reversed(win):
        first = e["sections"][0] if e.get("sections") else e["items"][0]["headline"]
        w(f"  {e['date']}  {e['lead_theme']:<20} {first}")
    leads = [e["lead_theme"] for e in win]
    if len(leads) >= 2 and leads[-1] == leads[-2]:
        w(f"  -> '{leads[-1]}' led the last two editions. Lead with a different theme this time.")
    top = max(set(leads), key=leads.count)
    if leads.count(top) >= max(3, len(leads) // 2 + 1):
        w(f"  -> '{top}' led {leads.count(top)} of the last {len(leads)}. Readers have had it on the front page enough.")

    # theme frequency
    w("\nTHEMES: editions in the window that touched each one")
    counts = {t: sum(1 for e in win if any(i["theme"] == t for i in e["items"])) for t in p["themes"]}
    for t, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        flag = ""
        if p["fixed_sections"] and n == len(win) and len(win) >= 3:
            # narrow publications (3-4 items): a theme in every edition crowds out everything else
            flag = "  OVERWORKED: in every recent edition. Cover only a real turn, briefly"
        elif n == 0:
            flag = "  untouched lately: look here first"
        w(f"  {t:<22} {n}/{len(win)}{flag}")

    # stories covered
    w("\nSTORIES ALREADY TOLD in the window (return only as a labelled follow-up with a real development since 'last')")
    stories = {}
    for e in win:
        for it in e["items"]:
            s = stories.setdefault(it["slug"], {"n": 0, "first": e["date"]})
            s["n"] += 1
            s.update(last=e["date"], headline=it["headline"], gist=it.get("gist", ""), url=e.get("url", ""))
    for slug_, s in sorted(stories.items(), key=lambda kv: (-kv[1]["n"], kv[1]["last"]), reverse=False):
        rep = f"x{s['n']}" if s["n"] > 1 else "  "
        w(f"  {slug_:<30} {rep:<3} last {short(s['last'])}  \"{s['headline']}\"")
        if s["gist"]:
            w(f"  {'':<34} where it stood: {s['gist']}")
    w(f"  At most {p['max_followups']} follow-up item(s) this edition. Everything else must be a story not listed above.")

    # threads
    open_t = [t for t in mem["threads"] if t["status"] == "open"]
    if open_t:
        w("\nOPEN THREADS: follow-up candidates. DUE means the check date has arrived; look these up first")
        def key(t):
            nc = t.get("next_check")
            due = nc and d(nc) <= today
            return (0 if due else 1, nc or "9999", t["slug"])
        for t in sorted(open_t, key=key):
            nc = t.get("next_check")
            tag = "DUE " if nc and d(nc) <= today else "    "
            w(f"  {tag}{t['slug']:<30} opened {short(t['opened'])}  last {short(t['last_seen'])}  check {short(nc)}")
            w(f"      {t['question']}")
        stale = [t for t in open_t if (today - d(t["last_seen"])).days > 60 and not t.get("next_check")]
        if stale:
            w("  Threads untouched for 60+ days with no check date: close them in threads_closed unless they moved: "
              + ", ".join(t["slug"] for t in stale))

    # watch list
    if last.get("watch"):
        w(f"\nLAST EDITION'S WATCH LIST ({last['date']}): find out what happened, report it in a line if it did")
        for x in last["watch"]:
            due = f"  [{x['due']}]" if x.get("due") else ""
            w(f"  - {x['text']}{due}")

    # explainers
    if "areas" in p:
        w("\nEXPLAINERS ALREADY TAUGHT (never repeat a topic)")
        used = [(e["date"], e["explainer"]) for e in eds if e.get("explainer")]
        for dt, ex in reversed(used[-12:]):
            w(f"  {dt}  {ex['area']:<22} {ex['topic']}")
        last_use = {a: None for a in p["areas"]}
        for dt, ex in used:
            last_use[ex["area"]] = dt
        order = sorted(p["areas"], key=lambda a: last_use[a] or "0000")
        nxt = order[0]
        w(f"  Least recently used area: {nxt} ({'never used' if not last_use[nxt] else 'last ' + last_use[nxt]}). "
          f"Default to it unless the news makes another area clearly more useful.")

    if "methods" in p:
        used = [(e["date"], e["method"]) for e in eds if e.get("method")]
        last_m = {m: None for m in p["methods"]}
        for dt, m in used:
            last_m[m] = dt
        order = sorted(p["methods"], key=lambda m: last_m[m] or "0000")
        w("\nCHECK-IT-YOURSELF METHODS (colophon): " + ", ".join(f"{m} {short(last_m[m])}" for m in p["methods"]))
        w(f"  Next: {order[0]}")
        ch = [(e["date"], e["companies_house"]) for e in eds if e.get("companies_house")]
        if ch:
            dt, c = ch[-1]
            due = d(dt) + timedelta(days=p["companies_house_every_days"])
            looked = sorted({c2["company"] for _, c2 in ch})
            w(f"COMPANIES HOUSE: last {dt} ({c['company']}). Due again by {due.isoformat()}"
              f"{' (DUE NOW)' if due <= today else ''}. Operators already examined: {', '.join(looked)}. Pick a different one.")
        else:
            w("COMPANIES HOUSE: never done. Due now.")

    # form
    if not p["fixed_sections"]:
        secs = []
        for e in reversed(win):
            secs += e.get("sections", [])
        w("\nSECTION TITLES USED RECENTLY (do not reuse or near-copy)")
        w("  " + " · ".join(dict.fromkeys(secs)))
    w("\nRECENT LEDES (do not reuse the opening move, e.g. starting with the same subject, number or construction)")
    for e in reversed(win):
        w(f"  {short(e['date'])}  {e['lede'][:150]}")
    vis = [(e["date"], v) for e in reversed(win) for v in e.get("visuals", [])]
    if vis:
        w("\nVISUALS USED RECENTLY (choose different chart forms and subjects where you can)")
        for dt, v in vis[:14]:
            w(f"  {short(dt)}  {v}")

    w("\nBefore publishing: python3 tools/memory.py check " + slug + " <edition.html>")
    print("\n".join(out))


# ------------------------------------------------------------------ check

def extract(page):
    page = re.sub(r"<(script|style|svg)[\s\S]*?</\1>", "", page, flags=re.I)
    def texts(tag):
        out = []
        for m in re.finditer(rf"<{tag}\b[^>]*>([\s\S]*?)</{tag}>", page, flags=re.I):
            inner = re.sub(r'<span[^>]*class="[^"]*\b(dek|kicker|when|eyebrow|tag)\b[^"]*"[^>]*>[\s\S]*?</span>', "", m[1])
            t = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", inner)).split())
            if t:
                out.append(t)
        return out
    lede = re.search(r'<p[^>]*class="lede"[^>]*>([\s\S]*?)</p>', page, flags=re.I)
    lede = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", lede[1])).split()) if lede else ""
    return {"h2": texts("h2"), "h3": texts("h3"), "lede": lede}


def check(slug, path):
    p = pub(slug)
    mem = load(slug)
    page = Path(path).read_text(encoding="utf-8")
    m = re.search(r"<title>([^<]*)</title>", page)
    this_date = None
    fn = re.match(r"(\d{4}-\d{2}-\d{2})", Path(path).name)
    if fn:
        this_date = fn[1]
    win = [e for e in sorted(mem["editions"], key=lambda e: e["date"]) if e["date"] != this_date][-p["window"]:]
    got = extract(page)
    flags = []
    FIXED = {"the week", "the fortnight", "how it works", "by the numbers", "what to watch", "the week ahead",
             "week ahead", "a note on the figures"}

    if not p["fixed_sections"]:
        for h in got["h2"]:
            if norm(h) in FIXED:
                continue
            for e in win:
                for s in e.get("sections", []):
                    if similar(h, s) >= 0.8:
                        flags.append(f"SECTION  \"{h}\"  ~ {e['date']} \"{s}\"")
    for h in got["h3"]:
        if norm(h) in FIXED:
            continue
        best = None
        for e in win:
            for it in e["items"]:
                sc = similar(h, it["headline"])
                if sc >= 0.6 and (best is None or sc > best[0]):
                    best = (sc, e["date"], it["headline"], it["slug"])
        if best:
            flags.append(f"HEADLINE \"{h}\"  ~ {best[1]} \"{best[2]}\" ({best[3]}, similarity {best[0]:.2f})")
    if got["lede"]:
        lw = norm(got["lede"]).split()[:4]
        for e in win:
            if similar(got["lede"], e["lede"]) >= 0.5:
                flags.append(f"LEDE     too close to {e['date']}: \"{e['lede'][:90]}\"")
            elif lw and norm(e["lede"]).split()[:4] == lw:
                flags.append(f"LEDE     opens with the same words as {e['date']}: \"{' '.join(lw)}…\"")

    title = m[1] if m else Path(path).name
    if not flags:
        print(f"memory.py check: {title}: nothing echoes the last {len(win)} editions.")
        return
    print(f"memory.py check: {title}: {len(flags)} possible repeat(s) against the last {len(win)} editions")
    for f in flags:
        print("  " + f)
    print("Rewrite these, or keep a flagged headline only if it is a labelled follow-up written in new words.")
    sys.exit(1)


# ------------------------------------------------------------------ cli

def main(argv):
    if len(argv) < 3 or argv[1] not in ("brief", "check", "add", "schema"):
        print(__doc__)
        sys.exit(2)
    cmd, slug = argv[1], argv[2]
    pub(slug)
    if cmd == "brief":
        today = date.fromisoformat(argv[3]) if len(argv) > 3 else None
        brief(slug, today)
    elif cmd == "schema":
        print(json.dumps(template(slug), indent=1, ensure_ascii=False))
    elif cmd == "add":
        if len(argv) < 4:
            die("usage: add <slug> <entry.json>")
        add(slug, argv[3])
    elif cmd == "check":
        if len(argv) < 4:
            die("usage: check <slug> <edition.html>")
        check(slug, argv[3])


if __name__ == "__main__":
    main(sys.argv)
