"""FLINT Solver."""

from pathlib import Path
from typing import Optional, Sequence

from ..prob import ProblemSet
from ..solver import Result, Solver


class FlintSolver(Solver):
    """FLINT Solver."""

    _name = "FLINT"

    def _find_executable(self) -> str:
        s = f"{self._build_dir}/build/polybench-flint"
        s1 = s + ".exe"
        if Path(s1).exists():
            s = s1
        return s

    def _prepare(self, problems: ProblemSet) -> Optional[str]:
        if problems.problem_type not in ("gcd", "factor"):
            return None

        # CMake build.

        self.copy_resources()

        if not self.run(
            [
                *self.cmake_command,
                "-S",
                ".",
                "-B",
                "build",
                "-DCMAKE_BUILD_TYPE=Release",
            ]
        ):
            return None

        if not self.run([*self.cmake_command, "--build", "build"]):
            return None

        # Check the FLINT version.
        output = self.get_output([self._find_executable(), "-v"])
        if output:
            return output[0]

        raise RuntimeError("failed to get FLINT version")

    def _solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        variables = ",".join(problems.variables)
        log_file = Path(".") / "output.csv"
        args = [variables, str(self.problem_file), str(log_file)]
        if not self.run([self._find_executable(), *args]):
            return None
        return self.parse_csv_log(log_file)


Solver.register_solver(FlintSolver)
