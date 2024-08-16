"""reFORM Solver."""

from pathlib import Path
from typing import Optional, Sequence

from ..prob import ProblemSet
from ..solver import Result, Solver


class ReformSolver(Solver):
    """reFORM Solver."""

    _name = "reFORM"

    def _prepare(self, problems: ProblemSet) -> Optional[str]:
        if problems.problem_type not in ("gcd",):
            return None

        # Cargo build.

        self.copy_resources()

        if not self.run([*self.cargo_command, "build", "--release"]):
            self.logger.warning("Note: reFORM requires rust>=1.36")
            return None

        # TODO: Extract the version from Cargo.toml.
        version = "0.1.0-fix-serialize"

        rustc_version = self.rustc_version
        return version + (f", {rustc_version}" if rustc_version else "")

    def _solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        variables = ",".join(problems.variables)
        log_file = Path(".") / "output.csv"
        args = [variables, str(self.problem_file), str(log_file)]
        if not self.run(
            [
                *self.cargo_command,
                "run",
                f"--manifest-path={self._build_dir}/Cargo.toml",
                "--release",
                "--",
                *args,
            ]
        ):
            return None
        return self.parse_csv_log(log_file)


Solver.register_solver(ReformSolver)
