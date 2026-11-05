"""Regenerate plugins/tanakh_verses.json (verses per chapter) from Sefaria.

    python scripts/fetch_verses.py

The result is committed, so the daily email never needs the network; run this only if you
want to refresh the data. Sefaria's shape API returns the verse count of every chapter.
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plugins.tanakh import BOOKS  # noqa: E402

out = {}
for _he, en, n in BOOKS:
    url = "https://www.sefaria.org/api/shape/" + urllib.parse.quote(en.replace("_", " "))
    with urllib.request.urlopen(url, timeout=30) as r:
        chapters = json.load(r)[0]["chapters"]
    assert len(chapters) == n, f"{en}: expected {n} chapters, got {len(chapters)}"
    out[en] = chapters
    print(en, sum(chapters))

(Path(__file__).resolve().parents[1] / "plugins" / "tanakh_verses.json").write_text(
    json.dumps(out, separators=(",", ":")), encoding="utf-8")
