"""Entry point."""

import sys

import colorama

# Call deinit() before importing pretty_errors because Colorama can't handle
# multiple calls of init().
# See: https://github.com/tartley/colorama/issues/205
colorama.deinit()

import pretty_errors  # noqa: E402

from . import main  # noqa: E402


def entry_point() -> None:
    """Entry point."""

    def fix_stderr_color(color: bool) -> None:
        if not color:
            pretty_errors.mono()
        pretty_errors.output_stderr = sys.stderr

    main.main(stderr_color_hook=fix_stderr_color)


if __name__ == "__main__":
    entry_point()
