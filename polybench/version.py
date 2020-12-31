"""Version information."""

from pathlib import Path
from typing import cast

import importlib_metadata
import toml


def _get_version(pyproject_toml: Path) -> str:
    data = toml.load(pyproject_toml)
    return cast(str, data["tool"]["poetry"]["version"])


try:
    # This is valid only if the package has been installed.
    __version__ = cast(str, importlib_metadata.version(__name__.rsplit(".", 1)[0]))
except importlib_metadata.PackageNotFoundError:
    # The package is not installed. Assume that there is pyproject.toml.
    __version__ = _get_version(Path(__file__).parent.parent / "pyproject.toml")
