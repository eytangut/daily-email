"""Tanakh: all 929 chapters over the current Hebrew month (Psalms weigh 1/3 each, Ps. 119 double),
days ending at book ends when close."""
from bisect import bisect_left

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

# Reading weight of each chapter, in thirds of a normal chapter: a normal chapter is 3,
# a Psalm is 1 (short), and Psalm 119 is 6 (double).
PSALMS = next(i for i, (_, en, _n) in enumerate(BOOKS) if en == "Psalms")


def _weight(book: int, ch: int) -> int:
    if book != PSALMS:
        return 3
    return 6 if ch == 119 else 1


# CUM[i] = weight of the first i chapters, so a day's load is CUM[end] - CUM[start].
CUM = [0]
for _b, _c in CHAPTERS:
    CUM.append(CUM[-1] + _weight(_b, _c))

# A day may end at a book's end if that is within this many normal chapters of the even
# split (by weight). With ~28 weighted chapters/day this keeps days within roughly +-25%.
TOLERANCE = 7


def boundary(k: int, days: int, tolerance: int = TOLERANCE) -> int:
    """Chapter index where day k ends (day k+1 starts); boundary(0)=0, boundary(days)=929.

    The even split is made by reading weight, not chapter count. It then snaps to the
    nearest book end within `tolerance` normal chapters. The same function gives each
    day's start and the previous day's end, so days never overlap or leave gaps, and
    since every boundary is anchored to the even split (not to the previous day) the
    deviation never accumulates over the month. Tolerance must stay below half a day's
    weight so boundaries remain in order.
    """
    if k <= 0:
        return 0
    if k >= days:
        return len(CHAPTERS)
    nominal = k * CUM[-1] // days
    near = [e for e in BOOK_ENDS if abs(CUM[e] - nominal) <= tolerance * 3]
    if near:
        return min(near, key=lambda e: (abs(CUM[e] - nominal), e))
    i = bisect_left(CUM, nominal)  # nearest chapter boundary by weight
    return i if i == 0 or CUM[i] - nominal <= nominal - CUM[i - 1] else i - 1


@register("tanakh")
def build(ctx, title="תנ״ך", color="brown", tolerance=TOLERANCE, **_):
    hd = ctx.hebrew
    length = month_length(hd)
    start, end = boundary(hd.day - 1, length, tolerance), boundary(hd.day, length, tolerance)

    groups = []  # [book index, first chapter, last chapter]
    for book, ch in CHAPTERS[start:end]:
        if groups and groups[-1][0] == book:
            groups[-1][2] = ch
        else:
            groups.append([book, ch, ch])

    items = []
    for book, a, b in groups:
        he, en, _n = BOOKS[book]
        ref = f"{en}.{a}" + (f"-{b}" if b != a else "")
        value = heb(a) if a == b else f"{heb(a)}–{heb(b)}"
        items.append(Item(he, value, f"https://www.sefaria.org/{ref}?lang=he"))

    return Section(
        title=title, items=items, color=color,
        subtitle=f"{end - start} פרקים להיום",
        meta=f"יום {heb(hd.day)} מתוך {heb(length)}",
        progress=(hd.day, length),
    )
