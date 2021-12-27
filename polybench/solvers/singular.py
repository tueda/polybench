"""Singular Solver."""

import os
import shutil
from pathlib import Path
from typing import Optional, Sequence

from ..prob import ProblemSet
from ..solver import Result, Solver


class SingularSolver(Solver):
    """Singular Solver."""

    _name = "Singular"
    _env_var = "SINGULAR_COMMAND"

    def _find_singular(self) -> Optional[str]:
        env_cmd = self._env_var

        if env_cmd in os.environ:
            return shutil.which(os.environ[env_cmd])

        return shutil.which("Singular")

    def _prepare(self, problems: ProblemSet) -> Optional[str]:
        if problems.problem_type not in ("gcd", "factor"):
            return None

        singular = self._find_singular()

        if not singular:
            return None

        output = self.get_output([singular, "-v"], input="")

        if not output:
            return None

        return output[0]

    def _solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        # Write the Singular program file.

        input_file = Path(".") / "input.c"

        with input_file.open("w") as f:

            def print2(s: str) -> None:
                print(s, file=f)

            # NOTE: Singular 4-2-1 renamed "poly.lib." to "polylib.lib".
            print2('LIB "poly.lib";')
            print2('LIB "polylib.lib";')
            print2("short=0;")
            print2('system("--ticks-per-sec",1000);')
            print2(f"ring R = 0, ({', '.join(problems.variables)}), dp;")
            print2('link f = ":w output.csv";')

            for p in problems:
                if p.problem_type == "gcd":
                    print2(f"poly p = {p.p};")
                    print2(f"poly q = {p.q};")
                    print2("int t1 = timer;")
                    print2("poly r = gcd(p, q) * gcd(content(p), content(q)));")
                    print2("int t2 = timer;")
                    print2("int t = t2 - t1;")
                    print2('fprintf(f, "%s,%s", t, r);')
                elif p.problem_type == "factor":
                    print2(f"poly p = {p.p};")
                    print2("int t1 = timer;")
                    print2("list l = factorize(p);")
                    print2("int t2 = timer;")
                    print2("int t = t2 - t1;")
                    print2('string s = "";')
                    print2("for (int i = 1; i <= size(l[1]); i++) {")
                    print2('  s = s + sprintf(",(%s)^%s", l[1][i], l[2][i]);')
                    print2("}")
                    print2('fprintf(f, "%s%s", t, s);')
                else:
                    raise ValueError(
                        f"unsupported problem type: {problems.problem_type}"
                    )

            print2("close(f);")

        # Run Singular.

        singular = self._find_singular()

        if not singular:
            return None

        if not self.run([singular, input_file], input=""):
            return None

        # Parse the log file.

        log_file = Path(".") / "output.csv"

        return self.parse_csv_log(log_file, time_scaling=0.001)


Solver.register_solver(SingularSolver)
