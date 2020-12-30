"""Mathematica Solver."""

import os
import shutil
from pathlib import Path
from typing import Optional, Sequence

from ..prob import ProblemSet
from ..solver import Result, Solver


class MathematicaSolver(Solver):
    """Mathematica Solver."""

    _name = "Mathematica"
    _env_var = "WOLFRAMSCRIPT_COMMAND"

    def _find_wolframscript(self) -> Optional[str]:
        env_cmd = self._env_var

        if env_cmd in os.environ:
            return shutil.which(os.environ[env_cmd])

        return shutil.which("wolframscript")

    def _prepare(self, problems: ProblemSet) -> Optional[str]:
        if problems.problem_type not in ("gcd", "factor"):
            return None

        wolframscript = self._find_wolframscript()

        if not wolframscript:
            return None

        version = self.get_output([wolframscript, "-code", "$Version"])

        if not version:
            return None

        return version[0]

    def _solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        # Write a Mathematica program.

        mma_file = Path(".") / "program.m"

        with mma_file.open("w") as f:

            def print2(s: str) -> None:
                print(s, file=f)

            if problems.problem_type == "gcd":
                print2('s = OpenWrite["output.csv"];')
                print2(
                    """
                        DoGCD[p_, q_] := Module[{r, t, a},
                            r = Timing[PolynomialGCD[p, q]];
                            t = r[[1]] // ToString;
                            a = r[[2]] // InputForm // ToString;
                            a = StringReplace[a, " " -> ""];
                            WriteLine[s, t <> "," <> a];
                        ];
                    """
                )

                for p in problems:
                    print2(f"p = {p.p};")
                    print2(f"q = {p.q};")
                    print2("DoGCD[p, q];")

                print2("Close[s];")
            elif problems.problem_type == "factor":
                print2('s = OpenWrite["output.csv"];')
                print2(
                    """
                        DoFactor[p_] := Module[{r, t, a, x1, x2},
                            r = Timing[Factor[p]];
                            t = r[[1]] // ToString;
                            a = DeleteCases[List @@ (r[[2]] * x1 * x2), x1 | x2];
                            a = a // InputForm // ToString;
                            a = StringReplace[a, " " -> ""];
                            a = StringReplace[a, "{" -> ""];
                            a = StringReplace[a, "}" -> ""];
                            WriteLine[s, t <> "," <> a];
                        ];
                    """
                )

                for p in problems:
                    print2(f"p = {p.p};")
                    print2("DoFactor[p];")

                print2("Close[s];")
            else:
                raise ValueError(f"unsupported problem type: {problems.problem_type}")

        # Run Mathematica.

        wolframscript = self._find_wolframscript()

        if not wolframscript:
            return None

        if not self.run([wolframscript, "-file", mma_file]):
            return None

        # Parse the log file.

        log_file = Path(".") / "output.csv"

        return self.parse_csv_log(log_file)


Solver.register_solver(MathematicaSolver)
