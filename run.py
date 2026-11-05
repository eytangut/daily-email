"""python run.py                          send today's email
python run.py --preview [YYYY-MM-DD]     write preview.html instead of sending
python run.py --board [YYYY-MM-DD]       email this month's reading calendar as an image
python run.py --board --preview [DATE]   write board.png instead of sending"""
import sys
from pathlib import Path

import plugins  # noqa: F401  (registers every plugin)
from dailymail.runner import run, run_board

args = [a for a in sys.argv[1:] if not a.startswith("--")]
day = args[0] if args and args[0] else None
config = Path(__file__).with_name("config.yml")
if "--board" in sys.argv:
    run_board(config, day=day, preview="--preview" in sys.argv)
else:
    run(config, day=day, preview="--preview" in sys.argv)
