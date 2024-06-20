"""FLINT Solver."""

from typing import Optional, Sequence

from ..prob import ProblemSet
from ..solver import Result, Solver


class FlintSolver(Solver):
    """FLINT Solver."""

    _name = "FLINT"

    def _prepare(self, problems: ProblemSet) -> Optional[str]:
        if problems.problem_type not in ("gcd",):
            return None

        self.copy_resources()

        if not self.run([*self.cmake_command, "-S", ".", "-B", "build"]):
            return None

        if not self.run([*self.cmake_command, "--build", "build"]):
            return None

        return None

    def _solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        return None


Solver.register_solver(FlintSolver)
