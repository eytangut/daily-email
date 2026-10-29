# daily-email

A small framework that emails you one digest every morning from GitHub Actions.
Each **plugin** contributes one or more cards; `config.yml` decides which plugins run and how the mail is titled.

## Setup
1. Push this folder to a (private) repo.
2. Add secrets `SMTP_USER`, `SMTP_PASS` (Gmail app password), `MAIL_TO`.
3. Actions -> "Daily email" -> Run workflow.

Preview locally: `python run.py --preview 2026-10-29`, then open `preview.html`.

## Writing a plugin
Create `plugins/hello.py`:

```python
from dailymail import Item, Section, register

@register("hello")
def build(ctx, title="Hello", color="blue", name="world", **_):
    # ctx.today (date), ctx.now (aware datetime), ctx.hebrew (pyluach date), ctx.config
    return Section(title=title, color=color, text=f"Hi {name}, today is {ctx.today}.",
                   items=[Item("Label", "Value", "https://example.com")])
```

Enable it in `config.yml`:

```yaml
plugins:
  - type: hello
    name: Dana
```

`build` may return a `Section`, a list of them, or `None` (skip today). All parts of
`Section` except `title` are optional: `items`, `text`, `subtitle`, `meta`, `progress=(3, 30)`, `color`.
A plugin that raises is logged and skipped; the rest of the email still goes out.
`dailymail.helpers` has `heb()` (Hebrew numerals), `month_length()` and `split_evenly()`.
