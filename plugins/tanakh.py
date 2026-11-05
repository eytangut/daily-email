"""Tanakh: all 929 chapters over the current Hebrew month.

Days are balanced by verse count (data from Sefaria, plugins/tanakh_verses.json) times a
per-book difficulty multiplier from config.yml, and prefer to end at the end of a book.
The email still shows chapters.
"""
import json
from bisect import bisect_left
from pathlib import Path

from dailymail import Item, Section, register
from dailymail.helpers import heb, month_length

# (Hebrew name, Sefaria name, chapters) -- totals 929
BOOKS = [
    ("בראשית", "Genesis", 50), ("שמות", "Exodus", 40), ("ויקרא", "Leviticus", 27),
    ("במדבר", "Numbers", 36), ("דברים", "Deuteronomy", 34),
    ("יהושע", "Joshua", 24), ("שופטים", "Judges", 21),
    ("שמואל א׳", "I_Samuel", 31), ("שמואל ב׳", "II_Samuel", 24),
    ("מלכים א׳", "I_Kings", 22), ("מלכים ב׳", "II_Kings", 25),
    ("ישעיהו", "Isaiah", 66), ("ירמיהו", "Jeremiah", 52), ("יחזקאל", "Ezekiel", 48),
    ("הושע", "Hosea", 14), ("יואל", "Joel", 4), ("עמוס", "Amos", 9),
    ("עובדיה", "Obadiah", 1), ("יונה", "Jonah", 4), ("מיכה", "Micah", 7),
    ("נחום", "Nahum", 3), ("חבקוק", "Habakkuk", 3), ("צפניה", "Zephaniah", 3),
    ("חגי", "Haggai", 2), ("זכריה", "Zechariah", 14), ("מלאכי", "Malachi", 3),
    ("תהילים", "Psalms", 150), ("משלי", "Proverbs", 31), ("איוב", "Job", 42),
    ("שיר השירים", "Song_of_Songs", 8), ("רות", "Ruth", 4), ("איכה", "Lamentations", 5),
    ("קהלת", "Ecclesiastes", 12), ("אסתר", "Esther", 10), ("דניאל", "Daniel", 12),
    ("עזרא", "Ezra", 10), ("נחמיה", "Nehemiah", 13),
    ("דברי הימים א׳", "I_Chronicles", 29), ("דברי הימים ב׳", "II_Chronicles", 36),
]
CHAPTERS = [(i, c) for i, (_, _, n) in enumerate(BOOKS) for c in range(1, n + 1)]
assert len(CHAPTERS) == 929

# Cumulative chapter counts at which a book ends (the last one is 929).
BOOK_ENDS = []
_total = 0
for _he, _en, _n in BOOKS:
    _total += _n
    BOOK_ENDS.append(_total)

# Verses per chapter, per book (cached from Sefaria; regenerate with scripts/fetch_verses.py).
VERSES = json.loads((Path(__file__).with_name("tanakh_verses.json")).read_text(encoding="utf-8"))
for _he, _en, _n in BOOKS:
    assert len(VERSES[_en]) == _n, f"verse data for {_en} does not match its chapter count"

# A day may end at a book's end if that is within this fraction of a day's reading load
# from the even split. Must stay below 0.5 so the boundaries remain in order.
TOLERANCE = 0.25


def cumulative(difficulty: dict | None = None) -> list[float]:
    """CUM[i] = reading weight of the first i chapters: verses * the book's multiplier."""
    difficulty = difficulty or {}
    unknown = set(difficulty) - {en for _, en, _ in BOOKS}
    if unknown:
        raise ValueError(f"difficulty: unknown book(s) {sorted(unknown)}")
    cum = [0.0]
    for book, ch in CHAPTERS:
        en = BOOKS[book][1]
        cum.append(cum[-1] + VERSES[en][ch - 1] * float(difficulty.get(en, 1.0)))
    return cum


def boundary(k: int, days: int, cum: list[float], tolerance: float = TOLERANCE) -> int:
    """Chapter index where day k ends (day k+1 starts); boundary(0)=0, boundary(days)=929.

    Starts from the even split by weight, then snaps to the nearest book end within
    `tolerance` of a day's load. The same function gives each day's start and the previous
    day's end, so days never overlap or leave gaps, and since every boundary is anchored to
    the even split (not to the previous day) the deviation never accumulates in the month.
    """
    if k <= 0:
        return 0
    if k >= days:
        return len(CHAPTERS)
    day_weight = cum[-1] / days
    nominal = k * day_weight
    near = [e for e in BOOK_ENDS if abs(cum[e] - nominal) <= tolerance * day_weight]
    if near:
        return min(near, key=lambda e: (abs(cum[e] - nominal), e))
    i = bisect_left(cum, nominal)  # nearest chapter boundary by weight
    return i if i == 0 or cum[i] - nominal <= nominal - cum[i - 1] else i - 1


def day_range(day: int, days: int, difficulty: dict | None = None,
              tolerance: float = TOLERANCE) -> tuple[int, int]:
    """Slice [start, end) of CHAPTERS to read on `day` (1-based) of a `days`-day month."""
    cum = cumulative(difficulty)
    return boundary(day - 1, days, cum, tolerance), boundary(day, days, cum, tolerance)


def groups(start: int, end: int) -> list[list[int]]:
    """Consecutive chapters grouped by book: [[book index, first chapter, last chapter], ...]."""
    out = []
    for book, ch in CHAPTERS[start:end]:
        if out and out[-1][0] == book:
            out[-1][2] = ch
        else:
            out.append([book, ch, ch])
    return out


def label(book: int, a: int, b: int) -> tuple[str, str]:
    """(Hebrew book name, chapter text) for a group, e.g. ('בראשית', 'א׳–כ״ח')."""
    return BOOKS[book][0], heb(a) if a == b else f"{heb(a)}–{heb(b)}"


@register("tanakh")
def build(ctx, title="תנ״ך", color="brown", difficulty=None, tolerance=TOLERANCE, **_):
    hd = ctx.hebrew
    length = month_length(hd)
    start, end = day_range(hd.day, length, difficulty, tolerance)

    items = []
    for book, a, b in groups(start, end):
        en = BOOKS[book][1]
        ref = f"{en}.{a}" + (f"-{b}" if b != a else "")
        items.append(Item(BOOKS[book][0], label(book, a, b)[1], f"https://www.sefaria.org/{ref}?lang=he"))

    return Section(
        title=title, items=items, color=color,
        subtitle=f"{end - start} פרקים להיום",
        meta=f"יום {heb(hd.day)} מתוך {heb(length)}",
        progress=(hd.day, length),
    )
