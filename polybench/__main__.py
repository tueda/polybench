"""Entry point."""

import sys

import colorama

# Call deinit() before importing pretty_errors because Colorama can't handle
# multiple calls of init().
# See: https://github.com/tartley/colorama/issues/205
# Note that colorama.init() is called in colorlog imported in __init__
# before this point.
colorama.deinit()

import pretty_errors  # noqa: E402

from . import main  # noqa: E402


def _fix_color(color: bool) -> None:
    if not color:
        pretty_errors.mono()
    pretty_errors.output_stderr = sys.stderr


if __name__ == "__main__":
    main(stderr_color_hook=_fix_color)
