"""Optional utilities for plugin authors."""
from pyluach import dates

_LETTERS = [(400, "ת"), (300, "ש"), (200, "ר"), (100, "ק"), (90, "צ"), (80, "פ"),
            (70, "ע"), (60, "ס"), (50, "נ"), (40, "מ"), (30, "ל"), (20, "כ"),
            (10, "י"), (9, "ט"), (8, "ח"), (7, "ז"), (6, "ו"), (5, "ה"),
            (4, "ד"), (3, "ג"), (2, "ב"), (1, "א")]


def heb(n: int) -> str:
    """Hebrew numeral with geresh/gershayim: 15 -> ט״ו, 5 -> ה׳."""
    s = ""
    for v, ch in _LETTERS:
        if n in (15, 16):
            s += "טו" if n == 15 else "טז"
            n = 0
        while n >= v:
            s += ch
            n -= v
    return s + "׳" if len(s) == 1 else s[:-1] + "״" + s[-1]


def month_length(hd) -> int:
    """Days (29 or 30) in the Hebrew month of the given pyluach date."""
    try:
        dates.HebrewDate(hd.year, hd.month, 30)
        return 30
    except ValueError:
        return 29


def split_evenly(total: int, day: int, days: int) -> tuple[int, int]:
    """Slice [start, end) of `total` units that belongs to `day` (1-based) out of `days`."""
    return (day - 1) * total // days, day * total // days
