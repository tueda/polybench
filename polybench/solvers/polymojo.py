"""Poly Mojo solvers for ordinary and certified integer polynomial operations."""

import hashlib
import json
import os
import platform
import re
import shutil
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional, Sequence, Tuple

from ..poly import Polynomial
from ..prob import ProblemSet
from ..solver import Result, Solver, SolverSetupError

SOURCE = Path(__file__).with_suffix("") / "driver.mojo"
PACKAGES = ("apn_mojo.mojoc", "polynomials.mojoc", "poly.mojoc")


def _polynomial_record(poly: Polynomial, variables: Sequence[str]) -> str:
    """Encode an expanded integer polynomial in Poly Mojo's sparse format."""
    terms: Dict[Tuple[int, ...], int] = {}
    indices = {name: i for i, name in enumerate(variables)}
    text = str(poly)
    tokens = re.findall(r"[+-]?[^+-]+", text)
    if "".join(tokens) != text:
        raise ValueError("unexpected expanded polynomial syntax")
    for token in tokens:
        coefficient = -1 if token.startswith("-") else 1
        powers = [0] * len(variables)
        for factor in token.lstrip("+-").split("*"):
            if re.fullmatch(r"[0-9]+", factor):
                coefficient *= int(factor)
                continue
            match = re.fullmatch(r"(x[0-9]+)(?:\^([0-9]+))?", factor)
            if not match or match[1] not in indices:
                raise ValueError(f"unexpected factor: {factor}")
            powers[indices[match[1]]] += int(match[2] or "1")
        key = tuple(powers)
        terms[key] = terms.get(key, 0) + coefficient
    terms = {
        powers: coefficient for powers, coefficient in terms.items() if coefficient
    }
    lines = [
        "POLYNOMIALS 1",
        "SPARSE",
        "ZZ",
        "1",
        str(len(variables)),
        *map(str, range(len(variables))),
        str(len(terms)),
    ]
    for exponents, coefficient in sorted(terms.items()):
        nonzero = [
            (axis, exponent) for axis, exponent in enumerate(exponents) if exponent
        ]
        lines.append(str(len(nonzero)))
        for axis, exponent in nonzero:
            lines.extend((str(axis), str(exponent)))
        lines.append(str(coefficient))
    return "\n".join(lines) + "\n"


class _Reader:
    def __init__(self, text: str) -> None:
        # Every interchange field is ASCII, so character and byte lengths agree.
        try:
            text.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("non-ASCII driver output") from error
        self.text = text
        self.position = 0

    def line(self) -> str:
        """Read a newline-terminated field."""
        end = self.text.find("\n", self.position)
        if end < 0:
            raise ValueError("truncated driver output")
        value = self.text[self.position : end]
        self.position = end + 1
        return value

    def number(self) -> int:
        """Read an integer field."""
        return int(self.line())

    def count(self) -> int:
        """Read a nonnegative count or duration."""
        value = self.number()
        if value < 0:
            raise ValueError("negative count or duration")
        return value

    def record(self) -> str:
        """Read a polynomial preceded by its byte length."""
        size = self.count()
        end = self.position + size
        if end > len(self.text):
            raise ValueError("truncated polynomial")
        text = self.text[self.position : end]
        self.position = end
        return text

    def finish(self) -> None:
        """Reject unconsumed output."""
        if self.position != len(self.text):
            raise ValueError("trailing driver output")


def _polynomial_from_record(record: str, variables: Sequence[str]) -> Polynomial:
    """Decode a sparse integer polynomial without losing large coefficients."""
    reader = _Reader(record)
    if [reader.line() for _ in range(4)] != ["POLYNOMIALS 1", "SPARSE", "ZZ", "1"]:
        raise ValueError("unexpected polynomial record header")
    axes = [reader.number() for _ in range(reader.count())]
    if len(set(axes)) != len(axes) or any(a < 0 or a >= len(variables) for a in axes):
        raise ValueError("invalid polynomial axes")
    terms = []
    for _ in range(reader.count()):
        monomial = []
        seen = set()
        for _ in range(reader.count()):
            axis, exponent = reader.number(), reader.number()
            if axis not in axes or axis in seen or exponent < 1:
                raise ValueError("invalid monomial")
            seen.add(axis)
            monomial.append(f"{variables[axis]}^{exponent}")
        coefficient = reader.number()
        terms.append("*".join([str(coefficient), *monomial]))
    reader.finish()
    return Polynomial("+".join(terms) if terms else "0")


class _Timing(NamedTuple):
    problem: int
    warmup: bool
    compute_ns: int
    verification_ns: int


def _parse_results(
    text: str, problems: ProblemSet
) -> Tuple[Sequence[Result], Sequence[_Timing]]:
    """Keep certificate verification outside the reported operation time."""
    reader = _Reader(text)
    if reader.count() != len(problems):
        raise ValueError("wrong number of results")
    results = []
    timings = []
    for i in range(len(problems)):
        compute_ns, check_ns = reader.count(), reader.count()
        unit, count = reader.number(), reader.count()
        answer = []
        if unit != 1 or count == 0:
            answer.append(Polynomial(unit))
        for _ in range(count):
            exponent = reader.number()
            if exponent < 1:
                raise ValueError("invalid factor multiplicity")
            factor = _polynomial_from_record(reader.record(), problems.variables)
            answer.append(
                factor if exponent == 1 else Polynomial(f"({factor})^{exponent}")
            )
        results.append(Result(compute_ns / 1e9, answer))
        timings.append(_Timing(i, i < problems.n_warmups, compute_ns, check_ns))
    reader.finish()
    return results, timings


class PolyMojoSolver(Solver):
    """Benchmark ordinary Poly Mojo operations using precompiled packages."""

    _name = "PolyMojo"
    _env_var = "POLY_MOJO_PATH"
    _mode = "plain"
    _binary: Path
    _provenance: Dict[str, Any]

    def _prepare(self, problems: ProblemSet) -> Optional[str]:
        if problems.problem_type not in ("gcd", "factor"):
            return None
        try:
            return self._prepare_driver(problems)
        except OSError as error:
            raise SolverSetupError(f"failed to prepare Poly Mojo: {error}") from error

    def _prepare_driver(self, problems: ProblemSet) -> str:
        package_path = os.environ.get(self._env_var)
        if not package_path:
            raise SolverSetupError(
                "set POLY_MOJO_PATH to the precompiled package directory"
            )
        include = Path(package_path).expanduser()
        if not include.is_absolute():
            raise SolverSetupError("POLY_MOJO_PATH must be an absolute path")
        for name in PACKAGES:
            if not (include / name).is_file():
                raise SolverSetupError(f"missing precompiled package: {include / name}")
        mojo = shutil.which(os.environ.get("MOJO_COMMAND", "mojo"))
        if not mojo:
            raise SolverSetupError(
                "Mojo executable not found; set MOJO_COMMAND or PATH"
            )
        mojo = str(Path(mojo).resolve())
        version = self.get_output([mojo, "--version"])
        if not version:
            raise SolverSetupError("failed to get Mojo version")

        flags = ["--num-threads", "1", "-O3", "-D", f"NVARS={problems.n_vars}"]
        inputs: Dict[str, Any] = {
            "schema": 1,
            "source_sha256": self.sha256(SOURCE),
            "compiler": version[0],
            "compiler_path": mojo,
            "modular_home": os.environ.get("MODULAR_HOME", ""),
            "platform": [platform.system(), platform.machine()],
            "packages": {name: self.sha256(include / name) for name in PACKAGES},
            "flags": flags,
        }
        key = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
        folder = self.build_dir.parent / "polymojo-shared" / key
        folder.mkdir(parents=True, exist_ok=True)
        binary, manifest = folder / "driver", folder / "manifest.json"
        cached: Dict[str, Any] = {}
        try:
            cached = json.loads(manifest.read_text(encoding="utf-8"))
            reused = (
                isinstance(cached, dict)
                and cached.get("inputs") == inputs
                and cached.get("binary_sha256") == self.sha256(binary)
            )
        except (OSError, ValueError):
            reused = False
        if not reused:
            if manifest.exists():
                manifest.unlink()
            # Compile against a private snapshot, even if the user rebuilds the
            # original packages while the benchmark is running.
            snapshot = folder / "include"
            snapshot.mkdir(exist_ok=True)
            for name in PACKAGES:
                shutil.copyfile(str(include / name), str(snapshot / name))
                if self.sha256(snapshot / name) != inputs["packages"][name]:
                    raise SolverSetupError("Poly Mojo packages changed during setup")
            pending = folder / "driver.tmp"
            command = [
                mojo,
                "build",
                *flags,
                "-I",
                str(snapshot),
                str(SOURCE),
                "-o",
                str(pending),
            ]
            self.logger.info(f"Building shared driver for {problems.n_vars} variables")
            if not self.run(command, timeout=1800):
                if pending.exists():
                    pending.unlink()
                raise SolverSetupError("Mojo driver build failed")
            if self.sha256(SOURCE) != inputs["source_sha256"]:
                pending.unlink()
                raise SolverSetupError("Mojo driver source changed during setup")
            pending.replace(binary)
            cached = {"inputs": inputs, "binary_sha256": self.sha256(binary)}
            temporary = manifest.with_suffix(".tmp")
            temporary.write_text(json.dumps(cached, indent=2) + "\n", encoding="utf-8")
            temporary.replace(manifest)
        else:
            self.logger.info(f"Reusing shared driver for {problems.n_vars} variables")
        self._binary, self._provenance = binary, cached
        return f"Poly Mojo build {key[:12]}; {version[0]}; {self._mode}"

    def _solve(self, problems: ProblemSet) -> Optional[Sequence[Result]]:
        pieces = [f"{len(problems)}\n"]
        for problem in problems:
            polys = (
                (problem.p, problem.q)
                if problems.problem_type == "gcd"
                else (problem.p,)
            )
            for polynomial in polys:
                record = _polynomial_record(polynomial, problems.variables)
                pieces.append(f"{len(record.encode('ascii'))}\n{record}")
        input_file = Path("input.records").resolve()
        output_file = Path("output.records").resolve()
        input_file.write_text("".join(pieces), encoding="ascii")
        if output_file.exists():
            output_file.unlink()
        # Run the linked executable directly so a timeout terminates the solver,
        # without leaving a compiler or package-manager wrapper running.
        if not self.run(
            [self._binary, problems.problem_type, input_file, output_file, self._mode]
        ):
            return None
        try:
            results, timings = _parse_results(
                output_file.read_text(encoding="ascii"), problems
            )
        except (OSError, ValueError) as error:
            self.logger.warning(f"invalid Poly Mojo output: {error}")
            return None
        Path("certificate-timings.json").write_text(
            json.dumps(
                {"mode": self._mode, "records": [t._asdict() for t in timings]},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        Path("provenance.json").write_text(
            json.dumps(self._provenance, indent=2) + "\n", encoding="utf-8"
        )
        return results


class PolyMojoCertifiedSolver(PolyMojoSolver):
    """Benchmark certificate construction and check every returned certificate."""

    _name = "PolyMojoCertified"
    _mode = "certified"


Solver.register_solver(PolyMojoSolver)
Solver.register_solver(PolyMojoCertifiedSolver)
