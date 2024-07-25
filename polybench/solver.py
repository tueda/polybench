"""Solver."""

import filecmp
import hashlib
import os
import shutil
import subprocess
import urllib
import urllib.error
import urllib.request
import uuid
from logging import Logger
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence, Type, Union

import importlib_resources

from .poly import Polynomial
from .prob import ProblemSet
from .util import pushd


class Result(NamedTuple):
    """Result of a problem."""

    time: float  # in seconds
    answer: Sequence[Polynomial]


class Solver:
    """Abstract solver."""

    debug = False

    # Things that must be overridden in subclasses.

    _name = "None"  # Must be a unique name (without spaces).
    _env_var = ""  # Environment variable to be used (optional).

    def _prepare(self, problems: ProblemSet) -> Optional[str]:
        # Prepare this solver for the given problems and return the version string
        # from the underlying executable/library. Typically, the solver checks the
        # availability of executables, or download/build executables in `build_dir`,
        # which is the current working directory when this method is called.
        raise NotImplementedError

    def _solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        # Solve the given problems and return the results. If the underlying executable
        # has a programming language that is versatile enough, then the easiest way is
        # to generate a program in the language that creates a CSV file for the results
        # and use `parse_csv_log` (example: `MathematicaSolver`). When this method is
        # called, the current working directory is set to `output_dir` and
        # `problem_file` is accessible. One can also use files in `build_dir`.
        raise NotImplementedError

    # Common interface.

    def __init__(
        self,
        job_id: str,
        build_dir: Path,
        output_dir: Path,
        logger: Logger,
        timeout: int,
    ) -> None:
        """Construct a solver."""
        self._job_id = job_id
        self._build_dir = build_dir / self.name.lower()
        self._output_dir = output_dir / f"{job_id}.{self.name.lower()}"
        self._logger = logger.getChild(self.name)
        self._timeout = timeout

        self._problem_file = Path("undefined")  # set later

    def prepare(self, problems: ProblemSet) -> Optional[str]:
        """Prepare for the problems and return the version string if available."""
        with pushd(self.build_dir):
            result = self._prepare(problems)
        if result:
            result = result.strip()
        return result

    def solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        """Solve the given set of problems."""
        with pushd(self.output_dir):
            return self._solve(problems)

    @property
    def name(self) -> str:
        """Return the solver name."""
        return self._name

    @property
    def job_id(self) -> str:
        """Return the job id."""
        return self._job_id

    @property
    def build_dir(self) -> Path:
        """Return the build directory."""
        self._build_dir.mkdir(parents=True, exist_ok=True)
        return self._build_dir

    @property
    def output_dir(self) -> Path:
        """Return the output directory."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        return self._output_dir

    @property
    def logger(self) -> Logger:
        """Return the logger."""
        return self._logger

    @property
    def timeout(self) -> int:
        """Return the timeout."""
        return self._timeout

    @property
    def problem_file(self) -> Path:
        """Return the file containing the problems."""
        return self._problem_file

    # Solver registration.

    _solver_classes: List[Type["Solver"]] = []

    @classmethod
    def register_solver(cls, solver_class: Type["Solver"]) -> None:
        """Register a solver class."""
        cls._solver_classes.append(solver_class)

    @classmethod
    def get_solver_classes(cls) -> Sequence[Type["Solver"]]:
        """Return all the solver classes."""
        from . import solvers  # noqa: F401

        return tuple(cls._solver_classes)

    @classmethod
    def create_solvers(
        cls,
        *,
        job_id: str,
        build_dir: Path,
        output_dir: Path,
        logger: Logger,
        timeout: int,
    ) -> Sequence["Solver"]:
        """Construct defined solvers."""
        from . import solvers  # noqa: F401

        return tuple(
            c(job_id, build_dir, output_dir, logger, timeout)
            for c in cls._solver_classes
        )

    # Helper methods for subclasses.

    def _run(
        self,
        args: Union[str, Path, Sequence[Union[str, Path, int, float]]],
        *,
        input: Optional[str] = None,  # noqa: A002
        timeout: Optional[int] = None,
        capture_output: bool = False,
    ) -> Optional["subprocess.CompletedProcess[str]"]:
        if isinstance(args, (tuple, list)):
            new_args = [str(a) for a in args]
        else:
            new_args = [str(args)]

        try:
            if self.debug:
                redirect = None
            else:
                redirect = subprocess.DEVNULL

            p = subprocess.run(  # noqa: S603
                new_args,
                input=input,
                stdout=subprocess.PIPE if capture_output else redirect,
                stderr=redirect,
                universal_newlines=True,
                timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            self.logger.warning(f"{e}: {new_args}")
            return None

        if p.returncode != 0:
            self.logger.warning(f"{new_args} returned a non-zero code: {p.returncode}")

        return p

    DEFAULT_TIMEOUT = -1729

    def run(
        self,
        args: Union[str, Path, Sequence[Union[str, Path, int, float]]],
        *,
        input: Optional[str] = None,  # noqa: A002
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> bool:
        """Run a command."""
        if timeout == Solver.DEFAULT_TIMEOUT:
            timeout = self.timeout
        p = self._run(args, input=input, timeout=timeout)
        return p is not None and p.returncode == 0

    def get_output(
        self,
        args: Union[str, Path, Sequence[Union[str, Path, int, float]]],
        *,
        input: Optional[str] = None,  # noqa: A002
        timeout: Optional[int] = 10,
    ) -> Optional[Sequence[str]]:
        """Run a (short) command and return the output in the stdout."""
        p = self._run(args, input=input, timeout=timeout, capture_output=True)

        if p is None:
            return None

        if p.returncode != 0:
            return None

        return p.stdout.splitlines()

    @staticmethod
    def sha256(path: Path) -> str:
        """Return the SHA256 hash value of the given file."""
        hash_algorithm = hashlib.sha256()

        with path.open("rb") as f:
            while True:
                chunk = f.read(2048 * hash_algorithm.block_size)
                if len(chunk) == 0:
                    break

                hash_algorithm.update(chunk)

        return hash_algorithm.hexdigest()

    def download(self, url: str, sha256: str, path: Path) -> Optional[Path]:
        """Download a file."""
        if path.is_dir():
            path = path / Path(url).name

        if path.exists():
            if self.sha256(path) == sha256:
                return path

        try:
            with urllib.request.urlopen(url) as f:  # noqa: S310
                data = f.read()
        except urllib.error.URLError as e:
            self.logger.warning(f"{e}: {url}")
            return None

        # Use the "write-new-then-rename" idiom.

        temp_filename = f"{path}.tmp{uuid.uuid4()}"

        with open(temp_filename, "wb") as f:
            f.write(data)

        os.replace(temp_filename, path)

        h = self.sha256(path)

        if h == sha256:
            return path

        self.logger.warning(f"SHA256 mismatch: {url}, expected: {sha256}, actual: {h}")

        return None

    def copy_resources(
        self, name: Optional[str] = None, dest_dir: Optional[Path] = None
    ) -> None:
        """Copy resource files into the given directory."""
        if name is None:
            name = self.name.lower()
        if dest_dir is None:
            dest_dir = Path(".")

        resources = importlib_resources.files("polybench.solvers")
        for p in resources.iterdir():
            if p.is_dir() and p.name == name:
                self._copy_resources_impl(p, dest_dir)
                return

        raise RuntimeError(f"resources not found: {name}")

    def _copy_resources_impl(self, src_dir: Path, dest_dir: Path) -> None:
        for p in src_dir.iterdir():
            q = dest_dir / p.name
            if p.is_dir():
                self._copy_resources_impl(p, q)
            else:
                if not q.exists() or not filecmp.cmp(p, q):
                    self.logger.debug(f"copy {p.resolve()} -> {q.resolve()}")
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, q)

    @property
    def cmake_command(self) -> Sequence[str]:
        """Return the CMake command."""
        return [shutil.which("cmake") or "cmake"]

    @property
    def gradlew_command(self) -> Sequence[str]:
        """Return the gradlew command."""
        # We assume that the gradlew script exists in `build_dir` (typically prepared
        # by using ``copy_resources()``).
        if os.name == "nt":
            gradlew_cmd = "gradlew.bat"
        else:
            gradlew_cmd = "gradlew"

        gradlew = self._build_dir / gradlew_cmd

        if not gradlew.exists():
            raise RuntimeError(f"{gradlew} not found")

        return [str(gradlew), "-p", str(self._build_dir)]

    @property
    def cargo_command(self) -> Sequence[str]:
        """Return the cargo command."""
        return [shutil.which("cargo") or "cargo"]

    @property
    def jvm_version(self) -> Optional[str]:
        """Return the JVM version."""
        output = self.get_output([*self.gradlew_command, "-version"])

        if output:
            for s in output:
                if s.find("JVM:") >= 0:
                    return "JVM: " + s[4:].strip()

        return None

    @property
    def rustc_version(self) -> Optional[str]:
        """Return the rustc version."""
        # Here we use "--release", which should be the same flag as the complication
        # to avoid unnecessary debug complication.
        output = self.get_output(
            [*self.cargo_command, "rustc", "--release", "--", "--version"]
        )

        if output:
            for s in output:
                if s.startswith("rustc"):
                    return s.strip()

        return None

    def parse_csv_log(
        self, log_file: Path, time_scaling: float = 1.0
    ) -> Optional[Sequence[Result]]:
        """Parse results in the given log file.

        Parse results in the log file written as a CSV file and return the results.
        Each row must contain information of a result of a problem: the timing
        (in seconds, float) at the first column, and the answer in the rest of the row.
        For example, ``time,gcd`` for `gcd` problems and
        ``time,factor1,factor2,...,factorN`` for `factor` problems.
        """
        if not log_file.exists():
            return None

        with log_file.open() as f:
            lines = f.readlines()

        results = []

        for line in lines:
            a = line.split(",")
            a = [x for x in a if x]
            if len(a) < 2:
                return None
            try:
                results.append(
                    Result(float(a[0]) * time_scaling, [Polynomial(x) for x in a[1:]])
                )
            except ValueError:
                self.logger.warning(f"failed to parse a row: {line}")
                return None

        return tuple(results)
