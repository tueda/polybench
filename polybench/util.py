"""Common utility routines."""

import contextlib
import os
from pathlib import Path
from typing import Iterator, Union


def bytes2human(n: int) -> str:
    """Convert `n` bytes into a human readable string.

    >>> bytes2human(10000)
    '9.8K'
    >>> bytes2human(100001221)
    '95.4M'
    """
    # http://code.activestate.com/recipes/578019
    symbols = ("K", "M", "G", "T", "P", "E", "Z", "Y")
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return "%.1f%s" % (value, s)
    return "%sB" % n


@contextlib.contextmanager
def pushd(new_dir: Union[Path, str]) -> Iterator[None]:
    """Pushd/popd context."""
    # https://stackoverflow.com/a/13847807/9105334
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)
