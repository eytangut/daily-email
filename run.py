"""python run.py                          send today's email
python run.py --preview [YYYY-MM-DD]     write preview.html instead of sending"""
import sys
from pathlib import Path

import plugins  # noqa: F401  (registers every plugin)
from dailymail.runner import run

args = [a for a in sys.argv[1:] if not a.startswith("--")]
run(Path(__file__).with_name("config.yml"), day=args[0] if args else None,
    preview="--preview" in sys.argv)
