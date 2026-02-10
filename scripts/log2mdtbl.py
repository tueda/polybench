"""Generate a Markdown table from a log file."""

from __future__ import annotations

import fileinput
from typing import Sequence


def extract_rows(file_input: fileinput.FileInput[str]) -> list[tuple[str, str]]:
    """Extract key-value pairs from the input."""
    rows = []
    tools = set()

    for line in file_input:
        a = line.split("[", 1)
        s = a[1].strip()
        a = s.split("]", 1)
        level = a[0].strip()
        a = a[1].strip().split(" ", 1)
        category = a[0].strip()
        s = a[1].strip()
        if level == "INFO" and category == "Environment":
            a = s.split("=", 1)
            k = a[0].strip()
            v = a[-1].strip()
            rows.append((k, v))
        elif level == "INFO" and category not in ("Bench", "Config"):
            if category not in tools:
                tools.add(category)
                rows.append((category, s))

    return rows


def md_table(rows: Sequence[tuple[str, str]]) -> str:
    """Generate a Markdown table from rows of key-value pairs."""
    key_width = max(len(k) for k, _ in rows)
    value_width = max(len(v) for _, v in rows)

    def format_row(k: str, v: str) -> str:
        return f"| {k:<{key_width}} | {v:<{value_width}} |"

    return "\n".join(
        [format_row(k, v) for k, v in rows[:1]]
        + [f"| {'-'*key_width} | {'-'*value_width} |"]
        + [format_row(k, v) for k, v in rows[1:]]
    )


def main() -> None:
    """Entry point."""
    rows = extract_rows(fileinput.input(encoding="utf-8"))
    if rows:
        print(md_table([("", "")] + rows))


if __name__ == "__main__":
    main()
