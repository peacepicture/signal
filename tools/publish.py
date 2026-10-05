#!/usr/bin/env python3
"""Put a finished edition on the site and record it in memory.

Scheduled runs cannot push to GitHub: an unattended session is not allowed to
modify a shared resource. So a run publishes its edition as a page, with its
memory entry embedded in it (tools/memory.py embed), and the publisher, a
session with push access, files it here:

    python3 tools/publish.py <slug> <YYYY-MM-DD> <downloaded-edition.html>

It checks the page is complete and self-contained, writes it to
<slug>/<date>.html, records the embedded memory entry, and runs build.py.
Committing and pushing is left to the caller. Safe to run twice.
"""

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("memory", ROOT / "tools" / "memory.py")
memory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory)


def main(argv):
    if len(argv) != 4:
        sys.exit(__doc__)
    slug, day, src = argv[1], argv[2], Path(argv[3])
    memory.pub(slug)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        sys.exit("publish.py: date must be YYYY-MM-DD")
    page = src.read_text(encoding="utf-8")

    problems = []
    if "</html>" not in page[-400:].lower():
        problems.append("page does not end with </html>; it may be truncated")
    rel = [m for m in re.findall(r'(?:src|href)="([^"#]+)"', page)
           if not re.match(r"(https?:|data:|mailto:|/)", m)]
    if rel:
        problems.append(f"relative asset paths would break on the site: {rel[:5]}")
    if problems:
        sys.exit("publish.py: refusing to publish:\n  - " + "\n  - ".join(problems))

    entry = memory.extract_entry(page)
    dest = ROOT / slug / f"{day}.html"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(page, encoding="utf-8")
    print(f"publish.py: wrote {dest.relative_to(ROOT)}")

    if entry is None:
        print("publish.py: NO embedded memory entry. Write one by hand from the page "
              f"(python3 tools/memory.py schema {slug}) and run memory.py add.")
    else:
        if entry.get("date") != day:
            print(f"publish.py: note: entry date {entry.get('date')} differs from {day}; using {day}")
            entry["date"] = day
        entry.pop("publication", None)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
        memory.add(slug, f.name)

    subprocess.run([sys.executable, str(ROOT / "build.py")], check=True)


if __name__ == "__main__":
    main(sys.argv)
