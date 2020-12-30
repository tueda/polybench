"""Rings Solver."""

import re
from typing import Optional, Sequence

from ..prob import ProblemSet
from ..solver import Result, Solver


class RingsSolver(Solver):
    """Rings Solver."""

    _name = "Rings"

    def _prepare(self, problems: ProblemSet) -> Optional[str]:
        if problems.problem_type not in ("gcd", "factor"):
            return None

        # Gradle build.

        self.copy_resources()

        if not self.run([*self.gradlew_command, "classes"]):
            self.logger.warning("Note: Rings requires JDK>=8")
            return None

        # Look for "rings: 'x.y.z'" in build.gradle.

        gradle_file = self.build_dir / "build.gradle"

        for line in gradle_file.read_text().splitlines():
            m = re.search(r"rings\s*:\s*\'(\d+\.\d+\.\d+)\'", line)
            if m:
                version = m.group(1)
                jvm_version = self.jvm_version
                return version + (f", {jvm_version}" if jvm_version else "")

        raise RuntimeError("failed to get Rings version")

    def _solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        variables = ",".join(problems.variables)
        log_file = self.output_dir / "output.csv"  # Path(".") doesn't work
        args = [variables, str(self.problem_file), str(log_file)]
        args_as_one = " ".join(f'"{a}"' for a in args)
        if not self.run([*self.gradlew_command, "run", "--args", args_as_one]):
            return None
        return self.parse_csv_log(log_file)


Solver.register_solver(RingsSolver)
