"""Symbolica Solver."""

from pathlib import Path
from typing import Optional, Sequence

import toml

from ..prob import ProblemSet
from ..solver import Result, Solver


class SymbolicaSolver(Solver):
    """Symbolica Solver."""

    _name = "Symbolica"

    def _prepare(self, problems: ProblemSet) -> Optional[str]:
        if problems.problem_type not in ("gcd", "factor"):
            return None

        # Cargo build.

        self.copy_resources()

        if not self.run([*self.cargo_command, "build", "--release"]):
            self.logger.warning("Note: Symbolica requires rust>=1.73")
            return None

        version = (
            toml.load("Cargo.toml").get("dependencies", {}).get("symbolica")
        )  # type: str
        rustc_version = self.rustc_version
        return version + (f", {rustc_version}" if rustc_version else "")

    def _solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        variables = ",".join(problems.variables)
        log_file = Path(".") / "output.csv"
        args = [variables, str(self.problem_file), str(log_file)]
        if not self.run(
            [
                f"{self._build_dir}/target/release/polybench-symbolica",
                *args,
            ]
        ):
            return None
        return self.parse_csv_log(log_file)


Solver.register_solver(SymbolicaSolver)
