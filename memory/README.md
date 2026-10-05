# Editorial memory

Every scheduled run starts with no memory of the one before. This folder is
that memory. Each publication keeps one file — `signal.json`,
`kabulledger.json`, `loadfactor.json` — recording what every edition covered:
its stories, lead theme, section titles, lede, explainer, charts, watch list
and the open threads worth coming back to.

`tools/memory.py` reads and writes it. Never edit the JSON by hand.

## Every run, in order

1. **Before research**, run `python3 tools/memory.py brief <slug>` and read
   all of it. It lists what was told recently, what is overworked, which
   threads are due a follow-up, what the last edition promised to watch, and
   which explainers, headlines, section titles and charts are already used.
2. **Research and write** with the rules below.
3. **Before publishing**, run
   `python3 tools/memory.py check <slug> <edition.html>`. It flags section
   titles, headlines and ledes that echo recent editions. Rewrite what it
   flags. A flagged headline may stay only on a labelled follow-up, and only
   in new words.
4. **Before publishing the artifact**, run `python3 tools/memory.py schema <slug>`
   for a blank entry, fill it in for the edition you are about to publish,
   save it outside the repo (for example `/tmp/entry.json`), then run
   `python3 tools/memory.py embed <slug> /tmp/entry.json <edition.html>`. It
   validates the entry, refuses a bad one with a reason, and writes it into
   the page as a hidden JSON block. Publish that page. Do not commit or push:
   scheduled runs cannot write to the repo, and the publisher records the
   entry from the page (see PUBLISHING.md).

## The freshness rules

**1. New first.** Most of every edition is stories the reader has not seen
here. Signal carries at most three follow-ups among its 8–12 items. The Kabul
Ledger and Load Factor carry at most one among their three or four. Every
other item must be a story missing from the brief's "already told" list.

**2. A follow-up needs news.** A story comes back only when something has
happened since the date the brief shows: a decision, an outcome, a new
figure. Give it the kicker "Follow-up", open with what changed, recap the
background in one sentence, and link the earlier edition's permalink (the
brief gives the URL). Never re-explain it from scratch.

**3. Close the loop.** Check every item on the last edition's watch list and
every thread the brief marks DUE. Where something happened, report it in a
line — in a short "Since last time" note under the lede, or inside the item it
belongs to. Where nothing happened, leave it out. Do not carry the same watch
item forward edition after edition; drop it until it moves.

**4. Rotate the front page.** Do not lead with the theme that led the last two
editions. For Signal, routine market levels belong in the tape strip; markets
earn a section only when they did something a reader would mention to a
friend.

**5. Go where we have not been.** Themes the brief marks "untouched lately" are
the first place to look. Signal in particular should look beyond the United
States: Europe, China, Japan, India, the Gulf, emerging markets.

**6. Teach something new.** The Kabul Ledger and Load Factor never repeat an
explainer topic. Default to the least recently used area the brief names,
unless the news makes another area clearly more useful. Load Factor's
check-it-yourself method and Companies House operator rotate the same way.

**7. Fresh form.** Do not reuse a recent section title, headline wording, the
lede's opening move, or a chart form the brief lists. Same house style, new
shapes inside it.

**8. Record honestly.** When continuing a story, reuse its slug from the brief.
Give a new story a short new slug. Open a thread for anything unresolved and
worth checking, with a check date when one exists. Close threads that resolved
or went quiet.
