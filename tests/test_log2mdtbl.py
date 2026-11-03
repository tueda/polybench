"""Tests for converting benchmark logs to Markdown rows."""

import runpy
from pathlib import Path
from typing import Callable, Iterable, List, Sequence, Tuple, cast

script = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/log2mdtbl.py")
)
extract_rows = cast(
    Callable[[Iterable[str]], List[Tuple[str, str]]], script["extract_rows"]
)
md_table = cast(Callable[[Sequence[Tuple[str, str]]], str], script["md_table"])


def line(category: str, message: str, level: str = "INFO") -> str:
    return "2026-10-29 18:42:57 [{:^8}] {:12}{}\n".format(level, category, message)


def test_polymojo_builds_after_preparation() -> None:
    lines = [
        line("Environment", "platform = Linux"),
        line("PolyMojo", "Preparing pinned Poly Mojo packages with Pixi"),
        line("PolyMojo", "Reusing shared driver for 5 variables"),
        line("PolyMojo", "Poly Mojo build abc; Mojo 1.2.0; plain"),
        line("PolyMojoCertified", "Reusing shared driver for 5 variables"),
        line("PolyMojoCertified", "Poly Mojo build abc; Mojo 1.2.0; certified"),
    ]
    assert extract_rows(lines) == [
        ("platform", "Linux"),
        ("PolyMojo", "Poly Mojo build abc; Mojo 1.2.0; plain"),
        ("PolyMojoCertified", "Poly Mojo build abc; Mojo 1.2.0; certified"),
    ]


def test_missing_build_and_legacy_logs() -> None:
    lines = [
        line("Environment", "platform = Linux"),
        line("Config", "x = y"),
        line("PolyMojo", "Preparing pinned Poly Mojo packages with Pixi"),
        line("PolyMojoCertified", "Reusing shared driver for 5 variables"),
        line("FLINT", "FLINT 3.0"),
        line("FLINT", "1.0 sec"),
        line("Other", "ignored", "WARNING"),
    ]
    rows = extract_rows(lines)
    assert rows == [("platform", "Linux"), ("FLINT", "FLINT 3.0")]
    assert "| FLINT" in md_table([("", "")] + rows)
