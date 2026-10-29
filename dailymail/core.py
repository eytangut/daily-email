"""Framework core: what plugins receive (Context) and return (Section)."""
from dataclasses import dataclass
from datetime import date, datetime
from functools import cached_property

from pyluach import dates

WEEKDAYS = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
MONTHS = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
          "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]


@dataclass
class Item:
    """One row inside a card."""
    label: str
    value: str = ""
    url: str | None = None


@dataclass
class Section:
    """One card in the email. Only `title` is required; use whichever parts you need."""
    title: str
    items: list[Item] | None = None
    text: str = ""                           # free paragraph
    subtitle: str = ""                       # small line under the title
    meta: str = ""                           # small text opposite the title
    progress: tuple[int, int] | None = None  # (current, total) -> progress bar
    color: str = "brown"                     # brown | blue | green | plum


@dataclass
class Context:
    """Everything a plugin may need to know about the run."""
    now: datetime            # timezone-aware
    config: dict

    @property
    def today(self) -> date:
        return self.now.date()

    @cached_property
    def hebrew(self):
        """pyluach HebrewDate for today (year, month, day, month_name(), ...)."""
        return dates.HebrewDate.from_pydate(self.today)

    @cached_property
    def fields(self) -> dict:
        """Values usable as {placeholders} in config templates."""
        hd, t = self.hebrew, self.today
        month = hd.month_name(hebrew=True)
        return {
            "heb_day": hd.hebrew_day(), "heb_month": month, "heb_year": hd.hebrew_year(),
            "heb_date": f"{hd.hebrew_day()} ב{month} {hd.hebrew_year()}",
            "weekday": WEEKDAYS[t.weekday()],
            "greg_date": f"{t.day} ב{MONTHS[t.month - 1]} {t.year}",
            "iso": t.isoformat(),
        }


REGISTRY: dict = {}


def register(name: str):
    """@register("name") exposes `build(ctx, **options)` as plugin type "name" in config.yml.
    build returns a Section, a list of Sections, or None (nothing to show today)."""
    def wrap(fn):
        REGISTRY[name] = fn
        return fn
    return wrap
