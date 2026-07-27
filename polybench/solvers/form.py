"""FORM Solver."""

import os
import platform
import shutil
from pathlib import Path
from typing import Optional, Sequence, cast

from ..prob import ProblemSet
from ..solver import Result, Solver, SolverSetupError


class FormSolver(Solver):
    """FORM Solver."""

    _name = "FORM"
    _env_var = "FORM_COMMAND"

    def _find_form(self) -> Optional[str]:
        env_cmd = self._env_var

        if env_cmd in os.environ:
            return shutil.which(os.environ[env_cmd])

        form = shutil.which("form")

        if form:
            return form

        # Try to download the released binary.

        version = "5.0.1"
        if platform.system() == "Linux" and platform.machine() == "x86_64":
            distname = f"form-{version}-x86_64-linux"
            sha256 = "46118fac055a39bd0ff8cd014d61ad7aa1dc0c2fb33603f33de2e632f13175c7"
        elif platform.system() == "Linux" and platform.machine() == "arm64":
            distname = f"form-{version}-arm64-linux"
            sha256 = "1d6c7adece00eef2b9329c1cce936eba1e80eb117b95c5621f9ec3aeb9c0c6f2"
        elif platform.system() == "Darwin" and platform.machine() == "x86_64":
            distname = f"form-{version}-x86_64-osx"
            sha256 = "92e951fd5398f7a1ad03dc74877fb85e4a41de37eb7f5b714766d4f1d2da47c9"
        elif platform.system() == "Darwin" and platform.machine() == "arm64":
            distname = f"form-{version}-arm64-osx"
            sha256 = "b7054bcf84cb52a18c865ad6a5a862f16ee0450542165e9601ae1e576c6ace8a"
        else:
            return None

        url = (
            "https://github.com/vermaseren/form/releases/download"
            f"/v{version}/{distname}.tar.gz"
        )

        formpath = self.build_dir / distname / "form"

        if not formpath.exists():
            tarpath = self.download(url, sha256, self.build_dir)

            if not tarpath:
                return None

            shutil.unpack_archive(
                str(tarpath), self.build_dir  # str() needed for Python 3.6
            )

            if not formpath.exists():
                return None

        return str(formpath)

    def _prepare(self, problems: ProblemSet) -> Optional[str]:
        if problems.problem_type not in ("gcd", "factor"):
            return None

        form = self._find_form()

        if not form:
            raise SolverSetupError("executable not found")

        output = self.get_output([form, "-v"])

        if output:
            for s in output:
                if "FORM" in s:
                    return s

        raise SolverSetupError("failed to get version")

    def _solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        # Write a FORM program.

        form_file = Path(".") / "program.frm"

        with form_file.open("w") as f:

            def print2(s: str) -> None:
                print(s, file=f)

            print2("#-")
            print2(f"S {','.join(problems.variables)};")

            for p in problems:
                if p.problem_type == "gcd":
                    print2(f"#$p = {p.p};")
                    print2(f"#$q = {p.q};")
                    print2("#message")
                    print2("#reset timer")
                    print2("#$r = gcd_($p, $q);")
                    print2('#write "`TIMER_\'"')
                    print2("#message")
                    print2('#write "`$r\'"')
                elif p.problem_type == "factor":
                    print2(f"#$p = {p.p};")
                    print2("#message")
                    print2("#reset timer")
                    print2("#factdollar $p")
                    print2('#write "`TIMER_\'"')
                    print2("#message")
                    print2('#write "`$p[0]\'"')
                    print2("#do i=1,`$p[0]'")
                    print2("#message")
                    print2("#write \"`$p[`i']'\"")
                    print2("#enddo")
                else:
                    raise ValueError(f"unsupported problem type: {p.problem_type}")

            print2("#message")
            print2("#message")
            print2(".end")

        # Run FORM.

        form = self._find_form()

        if not form:
            return None

        if not self.run([form, "-l", form_file]):
            return None

        # Parse the log file.

        form_log_file = Path(".") / "program.log"
        log_file = Path(".") / "output.csv"

        if not self._convert_log(form_log_file, log_file, problems.problem_type):
            return None

        return self.parse_csv_log(log_file)

    def _convert_log(self, src_path: Path, dest_path: Path, mode: str) -> bool:
        if not src_path.exists():
            return False

        with src_path.open() as f:
            lines = iter(f.readlines())

        def get_next_entry() -> Optional[str]:
            s = next(lines, None)
            if s is None or s.startswith("~~~"):
                return None
            result = s.strip()
            while True:
                s = next(lines, None)
                if s is None or s.startswith("~~~"):
                    break
                result += s.strip()
            return result

        # Discard the first entry.
        if get_next_entry() is None:
            return False

        if mode == "gcd":
            with dest_path.open("w") as f:
                while True:
                    t = get_next_entry()
                    a = get_next_entry()
                    if t is None or a is None or not t.isdigit():
                        break
                    print(f"{max(int(t), 1) / 1000},{a}", file=f)
        elif mode == "factor":
            with dest_path.open("w") as f:
                while True:
                    t = get_next_entry()
                    n = get_next_entry()
                    if t is None or n is None or not t.isdigit() or not n.isdigit():
                        break
                    aa = [get_next_entry() for _ in range(int(n))]
                    if any(a is None for a in aa):
                        break
                    print(
                        f"{max(int(t), 1) / 1000}"
                        f",{','.join(cast(Sequence[str], aa))}",
                        file=f,
                    )
        else:
            return False

        return True


Solver.register_solver(FormSolver)
