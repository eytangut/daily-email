"""Tanakh: all 929 chapters, spread evenly over the current Hebrew month."""
from dailymail import Item, Section, register
from dailymail.helpers import heb, month_length, split_evenly

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


@register("tanakh")
def build(ctx, title="תנ״ך", color="brown", **_):
    hd = ctx.hebrew
    length = month_length(hd)
    start, end = split_evenly(len(CHAPTERS), hd.day, length)

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
