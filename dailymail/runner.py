"""Orchestration: config -> plugins -> sections -> email."""
import os
import smtplib
import ssl
import sys
import traceback
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from .core import REGISTRY, Context, Section
from .render import render


def _fill(template: str, fields: dict) -> str:
    try:
        return template.format(**fields)
    except KeyError as e:
        sys.exit(f"config.yml: unknown placeholder {e} (available: {', '.join(fields)})")


def _send(msg):
    host, port = os.environ.get("SMTP_HOST", "smtp.gmail.com"), int(os.environ.get("SMTP_PORT", 465))
    with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as s:
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)


def build_sections(ctx: Context) -> list[Section]:
    sections = []
    for entry in ctx.config.get("plugins", []):
        opts = dict(entry)
        kind = opts.pop("type")
        try:
            result = REGISTRY[kind](ctx, **opts)
        except Exception:      # one broken plugin must not cancel the whole email
            print(f"plugin '{kind}' failed:", file=sys.stderr)
            traceback.print_exc()
            continue
        if result is None:
            continue
        sections += result if isinstance(result, list) else [result]
    return sections


def run(config_path: Path, day: str | None = None, preview: bool = False):
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    now = datetime.now(ZoneInfo(config.get("timezone", "UTC")))
    if day:
        now = datetime.fromisoformat(day).replace(hour=6, tzinfo=now.tzinfo)
    ctx = Context(now=now, config=config)

    sections = build_sections(ctx)
    if not sections:
        sys.exit("nothing to send: no plugin produced a section")

    header = config.get("header", {})
    subject = _fill(config.get("subject", "{iso}"), ctx.fields)
    html, text = render(
        sections,
        _fill(header.get("title", "{iso}"), ctx.fields),
        _fill(header.get("subtitle", ""), ctx.fields),
        lang=config.get("language", "en"),
        rtl=config.get("direction", "ltr") == "rtl",
    )

    if preview:
        Path("preview.html").write_text(html, encoding="utf-8")
        print(subject)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"], msg["From"], msg["To"] = subject, os.environ["SMTP_USER"], os.environ["MAIL_TO"]
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    _send(msg)


def run_board(config_path: Path, day: str | None = None, preview: bool = False):
    """Render the month's reading calendar as a PNG and email it (or write board.png)."""
    from .board import month_plan, render_board

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    png = render_board(config, day)
    if preview:
        Path("board.png").write_bytes(png)
        print("wrote board.png")
        return
    hd, _ = month_plan(config, day)
    month = f"{hd.month_name(hebrew=True)} {hd.hebrew_year()}"

    msg = MIMEMultipart("related")
    msg["Subject"], msg["From"], msg["To"] = f"לוח תנ״ך · {month}", os.environ["SMTP_USER"], os.environ["MAIL_TO"]
    body = MIMEMultipart("alternative")
    body.attach(MIMEText(f"לוח הקריאה של {month} מצורף כתמונה.", "plain", "utf-8"))
    body.attach(MIMEText('<div dir="rtl"><img src="cid:board" style="max-width:100%"></div>', "html", "utf-8"))
    msg.attach(body)
    img = MIMEImage(png, "png")
    img.add_header("Content-ID", "<board>")
    img.add_header("Content-Disposition", "inline", filename="board.png")
    msg.attach(img)
    _send(msg)
