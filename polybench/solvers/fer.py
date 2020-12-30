"""Fermat Solver."""

import os
import re
import shutil
import time
from pathlib import Path
from typing import Dict, Optional, Sequence

from ..prob import ProblemSet
from ..solver import Result, Solver


class FermatSolver(Solver):
    """Fermat Solver."""

    _name = "Fermat"
    _env_var = "FERMAT_COMMAND"

    def _find_fermat(self) -> Optional[str]:
        env_cmd = self._env_var

        if env_cmd in os.environ:
            return shutil.which(os.environ[env_cmd])

        # Maybe one can try to download the binary from the website when unavailable,
        # but probably it leads to license troubles...

        return shutil.which("fer64")

    def _prepare(self, problems: ProblemSet) -> Optional[str]:
        if problems.problem_type not in ("gcd",):
            return None

        fermat = self._find_fermat()

        if not fermat:
            return None

        output = self.get_output(fermat, input="&q")

        if not output:
            return None

        for line in output:
            m = re.match(r"^(.*version.*)\(c\)", line)
            if m:
                return m.group(1)

        return None

    def _solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        # Write the input file.

        input_file = Path(".") / "input"

        with input_file.open("w") as f:

            def print2(s: str) -> None:
                print(s, file=f)

            if problems.problem_type == "gcd":
                print2("start := &T;")
                print2("&(S=output);")
                print2("&(U=1);")
                print2("&s;")
                print2("&(U=0);")
                print2("@(start);")

                for x in problems.variables:
                    print2(f"&(J={x});")

                for p in problems:
                    print2(f"p := {p.p};")
                    print2(f"q := {p.q};")
                    print2("t1 := &T;")
                    print2("r := GCD(p, q);")
                    print2("t2 := &T;")
                    print2("t := t2 - t1;")
                    print2("@(p, q, t1, t2);")
                    print2("&(U=1);")
                    print2("&s;")
                    print2("&(U=0);")
                    print2("@(r, t);")

                print2("end := &T;")
                print2("&(U=1);")
                print2("&s;")
                print2("&x;")
            else:
                raise ValueError(f"unsupported problem type: {problems.problem_type}")

        # Run Fermat.

        fermat = self._find_fermat()

        if not fermat:
            return None

        t1 = time.time()

        if not self.run(fermat, input="&(R=input);"):
            return None

        t2 = time.time()

        # Parse the log file.

        output_file = Path(".") / "output"
        log_file = Path(".") / "output.csv"

        if not self._convert_log(output_file, log_file, problems.problem_type, t2 - t1):
            return None

        return self.parse_csv_log(log_file)

    def _convert_log(
        self, src_path: Path, dest_path: Path, mode: str, total_time: float
    ) -> bool:
        # The normalization of timings (&T) seems rather unclear in the manual.
        # A code example in the manual assumes 60 ticks = 1 second, while the actual
        # measurement gives 1 tick = 1 microsecond on Linux x86_64.
        # As a workaround, we adjust it by the total elapsed time.

        if not src_path.exists():
            return False

        with src_path.open() as f:
            text = f.read()

        data_list = re.findall(r"scalars:(.*?);;", text, re.DOTALL)

        def parse_data(data: str) -> Dict[str, str]:
            a = data.split(";")
            result = {}
            for s in a:
                m = re.match(r"^(.*):=(.*)$", s, re.DOTALL)
                if m:
                    name = m.group(1).strip()
                    value = m.group(2).replace("\n", "").strip()
                    result[name] = value
            return result

        entries = [parse_data(s) for s in data_list]

        if len(entries) < 2:
            return False

        if "start" not in entries[0]:
            return False

        if "end" not in entries[-1]:
            return False

        try:
            t1 = float(entries[0]["start"])
            t2 = float(entries[-1]["end"])
            dt = max(t2 - t1, 1)
            time_unit = total_time / dt
            self.logger.debug(f"1 tick = {time_unit:.6e} sec")
        except ValueError:
            return False

        if mode == "gcd":
            with dest_path.open("w") as f:
                for entry in entries[1:-1]:
                    if "t" not in entry or "r" not in entry:
                        return False
                    try:
                        t = float(entry["t"])
                        a = entry["r"]
                    except ValueError:
                        return False
                    print(f"{t * time_unit},{a}", file=f)
        else:
            return False

        return True


Solver.register_solver(FermatSolver)
