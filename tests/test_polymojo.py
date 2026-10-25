import functools
import json
import logging
import operator
import platform
import shutil
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pytest

from polybench.poly import Polynomial
from polybench.prob import ProblemSet, ProblemTypeInput
from polybench.solver import Solver, SolverSetupError
from polybench.solvers import polymojo


def problems(kind: ProblemTypeInput = "nontrivial-gcd", n_vars: int = 2) -> ProblemSet:
    return ProblemSet(
        problem_type=kind,
        n_warmups=1,
        n_problems=2,
        seed=42,
        exp_dist="uniform",
        n_vars=n_vars,
        min_n_terms=2,
        max_n_terms=4,
        min_degree=1,
        max_degree=3,
        min_coeff=-100,
        max_coeff=100,
    )


@pytest.mark.parametrize(
    "expression", ["0", "1", "-7", "3*x1^2*x2-11*x2+19", f"{2**256}*x1^3-x2^4"]
)
def test_integer_record_roundtrip(expression: str) -> None:
    polynomial = Polynomial(expression)
    variables = ("x1", "x2")
    text = polymojo._polynomial_record(polynomial, variables)
    assert polymojo._polynomial_from_record(text, variables) == polynomial


@pytest.mark.parametrize(
    "kind", ["trivial-gcd", "nontrivial-gcd", "trivial-factor", "nontrivial-factor"]
)
@pytest.mark.parametrize("distribution", ["uniform", "sharp"])
def test_generated_input_roundtrip(kind: ProblemTypeInput, distribution: str) -> None:
    generated = ProblemSet(
        problem_type=kind,
        exp_dist=distribution,
        n_warmups=1,
        n_problems=2,
        seed=42,
        n_vars=3,
        min_n_terms=2,
        max_n_terms=4,
        min_degree=1,
        max_degree=3,
        min_coeff=-100,
        max_coeff=100,
    )
    for problem in generated:
        inputs = (
            (problem.p, problem.q) if generated.problem_type == "gcd" else (problem.p,)
        )
        for polynomial in inputs:
            record = polymojo._polynomial_record(polynomial, generated.variables)
            assert (
                polymojo._polynomial_from_record(record, generated.variables)
                == polynomial
            )


def packed(expression: str) -> str:
    record = polymojo._polynomial_record(Polynomial(expression), ("x1", "x2"))
    return str(len(record.encode("ascii"))) + "\n" + record


def test_factor_units_multiplicities_and_verification_time() -> None:
    generated = problems("nontrivial-factor")
    row = "2000\n7000\n-6\n2\n2\n" + packed("x1+2") + "1\n" + packed("x2-1")
    results, timings = polymojo._parse_results("3\n" + row * 3, generated)
    assert results[0].time == 0.000002
    assert functools.reduce(
        operator.mul, results[0].answer, Polynomial(1)
    ) == Polynomial("-6*(x1+2)^2*(x2-1)")
    assert timings[0] == polymojo._Timing(0, True, 2000, 7000)
    assert timings[1] == polymojo._Timing(1, False, 2000, 7000)


def test_gcd_preserves_integer_content() -> None:
    row = "100\n0\n1\n1\n1\n" + packed("2*x1+2")
    results, _ = polymojo._parse_results("3\n" + row * 3, problems())
    assert results[0].answer == [Polynomial("2*x1+2")]


@pytest.mark.parametrize("value", ["0", "1", "-7"])
def test_constant_factorization(value: str) -> None:
    row = "100\n0\n" + value + "\n0\n"
    results, _ = polymojo._parse_results("3\n" + row * 3, problems("nontrivial-factor"))
    assert results[0].answer == [Polynomial(value)]


@pytest.mark.parametrize(
    "bad",
    [
        "2\n",
        "3\n-1\n0\n",
        "3\n1\n-1\n",
        "3\n1\n0\n1\n-1\n",
        "3\n1\n0\n1\n1\n0\n",
        "3\n1\n0\n1\n1\n1\n1000\nshort",
        "3\n1\n0\n1\n1\n1\n-1\n",
        "3\n",
        "3",
        "é\n",
        "3\n" + "1\n0\n1\n0\n" * 3 + "trailing",
    ],
)
def test_malformed_driver_output_fails(bad: str) -> None:
    with pytest.raises(
        ValueError,
        match="number of results|negative|multiplicity|truncated|non-ASCII|trailing",
    ):
        polymojo._parse_results(bad, problems())


@pytest.mark.parametrize(
    "suffix",
    [
        "-1\n",  # Negative axis count.
        "2\n0\n0\n0\n",  # Repeated axis.
        "1\n2\n0\n",  # Unknown axis.
        "1\n0\n-1\n",  # Negative term count.
        "1\n0\n1\n-1\n",  # Negative monomial size.
        "1\n0\n1\n1\n1\n1\n1\n",  # Axis outside the declared axes.
        "1\n0\n1\n1\n0\n0\n1\n",  # Zero exponent.
        "1\n0\n1\n2\n0\n1\n0\n2\n1\n",  # Repeated monomial axis.
    ],
)
def test_malformed_polynomial_fails(suffix: str) -> None:
    with pytest.raises(ValueError, match="negative|invalid"):
        polymojo._polynomial_from_record(
            "POLYNOMIALS 1\nSPARSE\nZZ\n1\n" + suffix, ("x1", "x2")
        )


def test_unknown_input_variable_fails() -> None:
    with pytest.raises(ValueError, match="unexpected factor"):
        polymojo._polynomial_record(Polynomial("x3"), ("x1", "x2"))


def solvers(tmp_path: Path) -> Sequence[polymojo.PolyMojoSolver]:
    args = (
        "case",
        tmp_path / "build",
        tmp_path / "output",
        logging.getLogger("test"),
        120,
    )
    return polymojo.PolyMojoSolver(*args), polymojo.PolyMojoCertifiedSolver(*args)


def test_registration() -> None:
    classes = Solver.get_solver_classes()
    assert polymojo.PolyMojoSolver in classes
    assert polymojo.PolyMojoCertifiedSolver in classes


@pytest.fixture
def compiler(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    include = tmp_path / "packages with spaces"
    include.mkdir()
    for name in polymojo.PACKAGES:
        (include / name).write_bytes(name.encode("ascii"))
    monkeypatch.setenv("POLY_MOJO_PATH", str(include))
    monkeypatch.delenv("MOJO_COMMAND", raising=False)
    monkeypatch.setenv("MODULAR_HOME", "/runtime/one")
    monkeypatch.setattr(shutil, "which", lambda name: "/compiler/mojo")
    state: Dict[str, Any] = {
        "version": "Mojo test toolchain",
        "include": include,
        "builds": [],
    }

    def version(self: Solver, command: Sequence[str]) -> Sequence[str]:
        return [str(state["version"])]

    def compile_driver(self: Solver, command: Sequence[str], **kwargs: Any) -> bool:
        state["builds"].append(command)
        Path(command[-1]).write_bytes(b"compiled driver")
        return True

    monkeypatch.setattr(polymojo.PolyMojoSolver, "get_output", version)
    monkeypatch.setattr(polymojo.PolyMojoSolver, "run", compile_driver)
    return state


def test_modes_share_driver_and_package_snapshot(
    tmp_path: Path, compiler: Dict[str, Any]
) -> None:
    plain, certified = solvers(tmp_path)
    plain.prepare(problems())
    certified.prepare(problems())
    assert len(compiler["builds"]) == 1
    assert plain._binary == certified._binary
    for name in polymojo.PACKAGES:
        assert (plain._binary.parent / "include" / name).read_bytes() == name.encode(
            "ascii"
        )
    plain.prepare(problems(n_vars=3))
    assert len(compiler["builds"]) == 2


@pytest.mark.parametrize(
    "changed",
    [
        "binary",
        "package",
        "compiler",
        "compiler_path",
        "runtime",
        "platform",
        "source",
        "manifest",
    ],
)
def test_cache_invalidation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    compiler: Dict[str, Any],
    changed: str,
) -> None:
    plain = solvers(tmp_path)[0]
    source = tmp_path / "driver.mojo"
    source.write_text("original driver")
    monkeypatch.setattr(polymojo, "SOURCE", source)
    plain.prepare(problems())
    if changed == "binary":
        plain._binary.write_bytes(b"replaced executable")
    elif changed == "package":
        (compiler["include"] / polymojo.PACKAGES[0]).write_bytes(b"rebuilt package")
    elif changed == "compiler":
        compiler["version"] = "new Mojo toolchain"
    elif changed == "compiler_path":
        monkeypatch.setattr(shutil, "which", lambda name: "/replacement/mojo")
    elif changed == "runtime":
        monkeypatch.setenv("MODULAR_HOME", "/runtime/two")
    elif changed == "platform":
        monkeypatch.setattr(platform, "machine", lambda: "another-architecture")
    elif changed == "source":
        source.write_text("changed driver")
    else:
        (plain._binary.parent / "manifest.json").write_text("[]")
    plain.prepare(problems())
    assert len(compiler["builds"]) == 2


@pytest.mark.parametrize(
    "missing", ["environment", "relative", "package", "compiler", "version"]
)
def test_unavailable_dependencies_raise_setup_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    compiler: Dict[str, Any],
    missing: str,
) -> None:
    if missing == "environment":
        monkeypatch.delenv("POLY_MOJO_PATH")
    elif missing == "relative":
        monkeypatch.setenv("POLY_MOJO_PATH", "relative/path")
    elif missing == "package":
        (compiler["include"] / polymojo.PACKAGES[0]).unlink()
    elif missing == "compiler":
        monkeypatch.setattr(shutil, "which", lambda name: None)
    else:
        monkeypatch.setattr(polymojo.PolyMojoSolver, "get_output", lambda *args: None)
    with pytest.raises(SolverSetupError):
        solvers(tmp_path)[0].prepare(problems())


def test_failed_build_is_not_cached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, compiler: Dict[str, Any]
) -> None:
    plain = solvers(tmp_path)[0]
    monkeypatch.setattr(polymojo.PolyMojoSolver, "run", lambda *args, **kwargs: False)
    with pytest.raises(SolverSetupError, match="build failed"):
        plain.prepare(problems())
    assert not list((tmp_path / "build/polymojo-shared").glob("*/manifest.json"))


def test_solve_runs_binary_and_preserves_separate_timings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, compiler: Dict[str, Any]
) -> None:
    certified = solvers(tmp_path)[1]
    generated = problems()
    certified.prepare(generated)
    commands: List[Sequence[Any]] = []

    def run(self: Solver, command: Sequence[Any]) -> bool:
        commands.append(command)
        assert Path(command[2]).read_text().startswith("3\n")
        row = "100\n200\n1\n1\n1\n" + packed("1")
        Path(command[3]).write_text("3\n" + row * 3)
        return True

    monkeypatch.setattr(polymojo.PolyMojoSolver, "run", run)
    result = certified.solve(generated)
    assert result is not None
    assert len(result) == 3
    assert result[0].time == 1e-7
    assert commands[0][0] == certified._binary
    assert commands[0][-1] == "certified"
    saved = json.loads((certified.output_dir / "certificate-timings.json").read_text())
    assert saved["records"][0]["verification_ns"] == 200
    provenance = json.loads((certified.output_dir / "provenance.json").read_text())
    assert provenance["inputs"]["compiler"] == compiler["version"]


@pytest.mark.parametrize("failure", ["exit", "missing", "malformed"])
def test_solver_failure_is_not_a_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    compiler: Dict[str, Any],
    failure: str,
) -> None:
    plain = solvers(tmp_path)[0]
    plain.prepare(problems())

    def run(self: Solver, command: Sequence[Any]) -> bool:
        if failure == "malformed":
            Path(command[3]).write_text("incomplete output\n")
        return failure != "exit"

    monkeypatch.setattr(polymojo.PolyMojoSolver, "run", run)
    assert plain.solve(problems()) is None
