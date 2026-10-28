"""Require completed, cross-checked Poly Mojo results in CI."""

import argparse
import csv
import math
import re
from pathlib import Path
from typing import Sequence


def validate_results(
    directory: Path, backends: Sequence[str], batches: int, cases: int
) -> None:
    """Reject skipped backends, incomplete output and comparison failures."""
    files = sorted(directory.glob("[0-9]*.csv"))
    if len(files) != batches:
        raise ValueError(f"expected {batches} result files in {directory}")
    for path in files:
        with path.open(newline="") as stream:
            reader = csv.DictReader(stream)
            if not set(backends).issubset(reader.fieldnames or ()):
                raise ValueError(f"missing backend results: {path}")
            rows = list(reader)
        if len(rows) != cases:
            raise ValueError(f"expected {cases} measured cases: {path}")
        for row in rows:
            for backend in backends:
                duration = float(row[backend])
                if not math.isfinite(duration) or duration < 0:
                    raise ValueError(f"invalid {backend} timing: {path}")
        log = path.with_suffix(".log").read_text(encoding="utf-8")
        if re.search(r"\[\s*ERROR\s*\]\s+Check\b", log):
            raise ValueError(f"backend comparison failed: {path.with_suffix('.log')}")


def main() -> None:
    """Check the standard benchmark CSVs and their comparison logs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("backends", nargs="+")
    parser.add_argument("--batches", type=int, default=4)
    parser.add_argument("--cases", type=int, default=50)
    args = parser.parse_args()
    validate_results(args.directory, args.backends, args.batches, args.cases)


if __name__ == "__main__":
    main()
