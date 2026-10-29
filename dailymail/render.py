"""Sections -> email-safe HTML (+ plain text). Layout lives here and only here."""
from html import escape

# accent, soft tint, text on tint
PALETTES = {
    "brown": ("#8a5a2b", "#f4ebdb", "#68401c"),
    "blue":  ("#2f5d8a", "#e5eef7", "#234a6f"),
    "green": ("#3f6b4a", "#e4efe6", "#2f5538"),
    "plum":  ("#7a4a7a", "#f2e7f2", "#5f385f"),
}

CSS = """
@media (prefers-color-scheme: dark) {
  .bg { background:#17161a !important; }
  .card { background:#222126 !important; border-color:#33313a !important; }
  .tx { color:#f1eee8 !important; }
  .mu { color:#a39f95 !important; }
  .ac { color:#e4cba6 !important; }
  .ln { border-color:#33313a !important; }
  .tr { background:#33313a !important; }
  .pill { background:#38343c !important; color:#f1eee8 !important; }
}
"""

SANS = "'Heebo','Assistant',Arial,Helvetica,sans-serif"
SERIF = "'Frank Ruhl Libre','David Libre',David,'Times New Roman',serif"


def _card(s, end: str) -> str:
    accent, tint, ink = PALETTES.get(s.color, PALETTES["brown"])
    head = (
        f'<tr><td style="padding:22px 24px 0;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'<td class="ac" style="font:700 15px {SANS};color:{accent};letter-spacing:.3px;">{escape(s.title)}</td>'
        f'<td class="mu" align="{end}" style="font:13px {SANS};color:#8c877c;">{escape(s.meta)}</td>'
        f'</tr></table>'
        + (f'<div class="mu" style="font:13px {SANS};color:#8c877c;margin-top:2px;">{escape(s.subtitle)}</div>'
           if s.subtitle else "")
        + '</td></tr>'
    )
    bar = ""
    if s.progress:
        cur, tot = s.progress
        pct = max(1, min(100, round(cur / tot * 100)))
        bar = (
            f'<tr><td style="padding:14px 24px 4px;">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td width="{pct}%" style="background:{accent};height:5px;border-radius:5px;font-size:0;line-height:0;">&nbsp;</td>'
            f'<td class="tr" style="background:#ece6d9;height:5px;border-radius:5px;font-size:0;line-height:0;">&nbsp;</td>'
            f'</tr></table></td></tr>'
        )
    text = (f'<tr><td class="tx" style="padding:12px 24px 4px;font:16px/1.6 {SANS};color:#2b2a27;">'
            f'{escape(s.text).replace(chr(10), "<br>")}</td></tr>') if s.text else ""
    rows = ""
    for it in s.items or []:
        val = escape(it.value)
        if it.url and val:
            val = f'<a href="{escape(it.url)}" style="color:{ink};text-decoration:none;">{val}</a>'
        label = escape(it.label)
        if it.url and not it.value:
            label = f'<a href="{escape(it.url)}" style="color:inherit;text-decoration:none;">{label}</a>'
        pill = (f'<span class="pill" style="display:inline-block;background:{tint};color:{ink};font:700 16px {SANS};'
                f'padding:5px 14px;border-radius:999px;">{val}</span>') if val else ""
        rows += (
            f'<tr><td class="ln tx" style="padding:13px 0;border-top:1px solid #eee8db;font:17px {SANS};color:#2b2a27;">{label}</td>'
            f'<td class="ln" align="{end}" style="padding:9px 0;border-top:1px solid #eee8db;">{pill}</td></tr>'
        )
    items = (f'<tr><td style="padding:10px 24px 14px;"><table role="presentation" width="100%" '
             f'cellpadding="0" cellspacing="0">{rows}</table></td></tr>') if rows else '<tr><td style="padding:0 0 14px;"></td></tr>'
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" class="card" '
        f'style="background:#fffefb;border:1px solid #eee8db;border-radius:18px;margin-top:14px;">'
        f'{head}{bar}{text}{items}</table>'
    )


def render(sections, title: str, subtitle: str, *, lang: str = "he", rtl: bool = True):
    end = "left" if rtl else "right"
    preheader = " · ".join(f"{i.label} {i.value}".strip() for s in sections for i in (s.items or []))[:120]
    cards = "".join(_card(s, end) for s in sections)
    html = f"""<!doctype html>
<html lang="{escape(lang)}" dir="{'rtl' if rtl else 'ltr'}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark"><meta name="supported-color-schemes" content="light dark">
<style>{CSS}</style></head>
<body class="bg" style="margin:0;background:#f5f1e8;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" class="bg" style="background:#f5f1e8;"><tr>
<td align="center" style="padding:28px 14px 36px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;">
<tr><td style="padding:0 6px 6px;">
<div class="tx" style="font:700 34px/1.25 {SERIF};color:#2b2a27;">{escape(title)}</div>
<div class="mu" style="font:14px {SANS};color:#8c877c;margin-top:4px;">{escape(subtitle)}</div>
</td></tr>
<tr><td>{cards}</td></tr>
</table></td></tr></table></body></html>"""

    lines = [f"{title} · {subtitle}"]
    for s in sections:
        lines.append(f"\n{s.title}" + (f" ({s.meta})" if s.meta else ""))
        if s.text:
            lines.append(s.text)
        lines += [f"  {i.label} {i.value}".rstrip() + (f"\n  {i.url}" if i.url else "") for i in s.items or []]
    return html, "\n".join(lines)
