"""Solver implementations."""

from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules

# Load all modules.

for _, module_name, _ in iter_modules(  # type: ignore[assignment]
    [str(Path(__file__).resolve().parent)]
):
    import_module(f"{__name__}.{module_name}")
