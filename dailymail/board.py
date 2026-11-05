"""Render this Hebrew month's Tanakh reading plan as a calendar image (PNG)."""
import io
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
from pyluach import dates

from plugins import tanakh as T

from .core import WEEKDAYS, MONTHS
from .helpers import heb, month_length

HEB_WEEKDAYS = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]  # Sunday first
_FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu",
              "/usr/share/fonts/truetype/noto", "/usr/share/fonts/opentype/noto"]
_FONT_NAMES = {False: ["DejaVuSans.ttf", "NotoSansHebrew-Regular.ttf"],
               True: ["DejaVuSans-Bold.ttf", "NotoSansHebrew-Bold.ttf"]}

BG, INK, MUTED, LINE = "#faf6ef", "#2b2118", "#8a7b6a", "#d9cdbb"
CELL_FILL, DONE_FILL, EMPTY_FILL, SHABBAT_FILL = "#ffffff", "#e3f1de", "#efe9de", "#fbf2d9"
ACCENT = "#c2570c"


def _font_path(bold: bool) -> str:
    env = os.environ.get("BOARD_FONT_BOLD" if bold else "BOARD_FONT")
    if env:
        return env
    for d in _FONT_DIRS:
        for n in _FONT_NAMES[bold]:
            if (Path(d) / n).exists():
                return str(Path(d) / n)
    if shutil.which("fc-match"):  # any installed font that has Hebrew
        out = subprocess.run(["fc-match", "-f", "%{file}", f":lang=he{':bold' if bold else ''}"],
                             capture_output=True, text=True).stdout.strip()
        if out:
            return out
    raise RuntimeError("No Hebrew font found: install fonts-dejavu-core or set BOARD_FONT / BOARD_FONT_BOLD")


def _font(size: int, bold: bool = False):
    return ImageFont.truetype(_font_path(bold), size, layout_engine=ImageFont.Layout.BASIC)


def _vis(text: str) -> str:
    return get_display(text)  # logical -> visual order for right-to-left text


def _text_rtl(draw, right: int, y: int, text: str, font, fill):
    draw.text((right, y), _vis(text), font=font, fill=fill, anchor="ra")


def month_plan(config: dict, day: str | None = None):
    """(hebrew year, month, [per-day dict]) for the Hebrew month containing `day` (default today)."""
    tz = ZoneInfo(config.get("timezone", "UTC"))
    today = datetime.fromisoformat(day).date() if day else datetime.now(tz).date()
    hd = dates.HebrewDate.from_pydate(today)
    length = month_length(hd)
    opts = next((dict(e) for e in config.get("plugins", []) if e.get("type") == "tanakh"), {})
    difficulty, tol = opts.get("difficulty"), opts.get("tolerance", T.TOLERANCE)
    cum = T.cumulative(difficulty)

    days = []
    for n in range(1, length + 1):
        greg = dates.HebrewDate(hd.year, hd.month, n).to_pydate()
        a, b = T.boundary(n - 1, length, cum, tol), T.boundary(n, length, cum, tol)
        days.append({
            "n": n, "greg": greg, "today": greg == today,
            "chapters": b - a, "ends_book": b in T.BOOK_ENDS,
            "lines": [" ".join(T.label(*g)) for g in T.groups(a, b)],
        })
    return hd, days


def render_board(config: dict, day: str | None = None) -> bytes:
    hd, days = month_plan(config, day)
    S = 2                                   # supersampling for crisp text
    cw, pad, margin = 250 * S, 12 * S, 28 * S
    f_title, f_sub = _font(34 * S, True), _font(18 * S)
    f_wd, f_day = _font(18 * S, True), _font(26 * S, True)
    f_greg, f_line = _font(15 * S), _font(18 * S)
    line_h, head_h = 25 * S, 40 * S

    first_col = (days[0]["greg"].weekday() + 1) % 7        # Sunday = 0
    cells = [None] * first_col + days
    cells += [None] * (-len(cells) % 7)
    rows = [cells[i:i + 7] for i in range(0, len(cells), 7)]
    row_h = [head_h + max([len(c["lines"]) for c in r if c] or [1]) * line_h + 2 * pad for r in rows]

    width = 7 * cw + 2 * margin
    title_h, wd_h, foot_h = 110 * S, 36 * S, 50 * S
    height = margin + title_h + wd_h + sum(row_h) + foot_h
    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)

    month = f"{hd.month_name(hebrew=True)} {hd.hebrew_year()}"
    g0, g1 = days[0]["greg"], days[-1]["greg"]
    sub = f"{g0.day} ב{MONTHS[g0.month - 1]} – {g1.day} ב{MONTHS[g1.month - 1]} {g1.year}"
    _text_rtl(d, width - margin, margin, f"תנ״ך · {month}", f_title, INK)
    _text_rtl(d, width - margin, margin + 52 * S, sub, f_sub, MUTED)

    top = margin + title_h
    for col in range(7):                    # column 0 is Sunday, drawn on the right
        right = width - margin - col * cw
        d.text((right - cw // 2, top + wd_h // 2), _vis(HEB_WEEKDAYS[col]),
               font=f_wd, fill=MUTED, anchor="mm")
    y = top + wd_h
    for r, h in zip(rows, row_h):
        for col, c in enumerate(r):
            right = width - margin - col * cw
            box = (right - cw, y, right, y + h)
            if c is None:
                d.rectangle(box, fill=EMPTY_FILL, outline=LINE, width=S)
                continue
            fill = DONE_FILL if c["ends_book"] else SHABBAT_FILL if col == 6 else CELL_FILL
            d.rectangle(box, fill=fill, outline=LINE, width=S)
            _text_rtl(d, right - pad, y + pad, heb(c["n"]), f_day, ACCENT if c["today"] else INK)
            d.text((right - cw + pad, y + pad + 8 * S), f"{c['greg'].day}/{c['greg'].month}",
                   font=f_greg, fill=MUTED, anchor="la")
            ty = y + pad + head_h
            for line in c["lines"]:
                _text_rtl(d, right - pad, ty, line, f_line, INK)
                ty += line_h
            if c["today"]:
                d.rectangle(box, outline=ACCENT, width=4 * S)
        y += h

    d.rectangle((width - margin - 16 * S, y + 16 * S, width - margin, y + 32 * S),
                fill=DONE_FILL, outline=LINE, width=S)
    _text_rtl(d, width - margin - 24 * S, y + 12 * S, "היום מסתיים בסוף ספר", f_sub, MUTED)

    out = io.BytesIO()
    img.resize((width // S, height // S), Image.LANCZOS).save(out, "PNG", optimize=True)
    return out.getvalue()
