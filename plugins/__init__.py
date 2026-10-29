"""Every .py file here is imported automatically: drop in a file, add it to config.yml."""
import importlib
import pkgutil

for _m in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_m.name}")
