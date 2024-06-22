"""Main routines."""

import argparse
import functools
import logging
import operator
import platform
import re
import shutil
import statistics
import sys
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, List, NamedTuple, Optional, Sequence, Set, cast

import colorama
import cpuinfo
import psutil

from . import plot
from .poly import Polynomial
from .prob import (
    ExponentsDistribution,
    ProblemSet,
    ProblemTypeInput,
    get_exponents_distribution_args,
    get_problem_type_input_args,
)
from .solver import Result, Solver
from .util import bytes2human

Logger = logging.Logger

# Call deinit() before importing colorlog because Colorama can't handle
# multiple calls of init().
# See: https://github.com/tartley/colorama/issues/205
colorama.deinit()

import colorlog  # noqa: E402


def next_job_id(output_dir: Path) -> str:
    """Return the next job id."""
    # The ids are of form "0001", "0002", ...
    # Such ids are used for naming log files "0001.log" etc.
    # We look for the first id that haven't been used in the output directory.

    def make_job_id(n: int) -> str:
        return f"{n:0>4}"

    n = 1

    if output_dir.is_dir():
        existing_job_ids = {
            f.name.split(".", maxsplit=1)[0] for f in output_dir.glob("*.*")
        }
        while make_job_id(n) in existing_job_ids:
            n += 1

    return make_job_id(n)


def config_log(logger: Logger, **kwargs: Any) -> None:
    """Log the configurations."""
    env_logger = logger.getChild("Environment")

    env_logger.info(f"platform = {platform.platform()}")

    cpu_info = cpuinfo.get_cpu_info()
    fields = [("python_version", ""), ("brand_raw", "cpu_brand")]
    for key, display_name in fields:
        if key in cpu_info:
            value = re.sub(r"\s\s+", " ", cpu_info[key])
            if display_name:
                env_logger.info(f"{display_name} = {value}")
            else:
                env_logger.info(f"{key} = {value}")

    cpu_count = psutil.cpu_count(logical=False)
    logical_cpu_count = psutil.cpu_count(logical=True)

    if isinstance(cpu_count, int) and isinstance(logical_cpu_count, int):
        if cpu_count == logical_cpu_count:
            env_logger.info(f"cpu_count = {cpu_count}")
        else:
            env_logger.info(f"cpu_count = {cpu_count} (logical: {logical_cpu_count})")

    env_logger.info(f"total_memory = {bytes2human(psutil.virtual_memory().total)}B")

    config_logger = logger.getChild("Config")
    for key, value in kwargs.items():
        config_logger.info(f"{key} = {value}")


def prepare_solvers(
    solvers: Sequence[Solver], problems: ProblemSet
) -> Sequence[Solver]:
    """Make the solvers prepare for the problems and return available solvers."""
    available_solvers = []

    for s in solvers:
        v = s.prepare(problems)
        if v:
            available_solvers.append(s)
            s.logger.info(v)
        else:
            s.logger.warning("not available")

    return tuple(available_solvers)


class SolverResult(NamedTuple):
    """Result from a solver."""

    name: str
    res: Sequence[Result]
    output_dir: Path


def run_solvers(
    solvers: Sequence[Solver],
    problems: ProblemSet,
    *,
    job_id: str,
    output_dir: Path,
    plot_title: str,
    plot_suffixes: Sequence[str],
    logger: Logger,
    keep_temp: bool = False,
) -> None:
    """Run the solvers for the given set of problems."""
    # Log for problems.

    problem_file = output_dir / f"{job_id}.problems.log"

    with problem_file.open(mode="w") as f:
        for p in problems:
            print(p, file=f)

    # Run solvers.

    def get_timing_information(results: Sequence[Result], n_warmups: int) -> str:
        """Return the timing information as a string."""
        times = [r.time for r in results][n_warmups:]
        if len(times) == 0:
            return ""
        if len(times) == 1:
            return f" ({times[0]:.3f} sec)"
        mean = statistics.mean(times)
        stdev = statistics.stdev(times, mean)
        max_t, max_i = max((t, i) for i, t in enumerate(times))
        return (
            f" (mean: {mean:.3f} sec,"
            f" SD: {stdev:.3f} sec,"
            f" slowest: {max_t:.3f} sec on Prob. {max_i + 1 + n_warmups})"
        )

    results: List[SolverResult] = []

    for s in solvers:
        s._problem_file = problem_file  # Yes, this is ugly.
        t1 = time.time()
        r = s.solve(problems)
        t2 = time.time()
        if r and len(r) == len(problems):
            results.append(SolverResult(s.name, r, s._output_dir))
            s.logger.info(
                f"{t2 - t1:.3f} sec{get_timing_information(r, problems.n_warmups)}"
            )
        else:
            s.logger.error("failed")

    # Check the consistency of the obtained results.

    check_logger = logger.getChild("Check")

    wrong: Set[str] = set()

    def count_factors(pp: Sequence[Polynomial]) -> int:
        n = 0
        m = 0
        for p in pp:
            n_terms = len(p)
            if n_terms == 0:
                return 0
            elif n_terms == 1:
                if not p.is_unit:
                    m += 1
            else:
                n += 1
        if m >= 1:
            n += 1
        return n

    if problems.problem_type == "gcd":
        # The GCD must be given as a single polynomial.
        for name, res, _ in results:
            for i, ri in enumerate(res):
                if len(ri.answer) != 1:
                    check_logger.error(f"{name}:{i + 1}: wrong answer")
                    wrong.add(name)
        # The GCD must be the same up to a multiplicative unit.
        if len(results) >= 2:
            for i in range(len(problems)):
                pp0 = results[0].res[i].answer
                if len(pp0) != 1:
                    continue
                p0 = pp0[0]
                for j in range(1, len(results)):
                    ppj = results[j].res[i].answer
                    if len(ppj) != 1:
                        continue
                    pj = ppj[0]
                    if not p0.equals_without_unit(pj):
                        name0 = results[0].name
                        namej = results[j].name
                        check_logger.error(
                            f"{name0}:{namej}:{i + 1}: inconsistent answers"
                        )
                        wrong.add(name0)
                        wrong.add(namej)
    elif problems.problem_type == "factor":
        # The product of the factorized polynomials must equal the original polynomial.
        for name, res, _ in results:
            for i, ri in enumerate(res):
                product = functools.reduce(operator.mul, ri.answer, Polynomial(1))
                if problems[i].p != product:
                    check_logger.error(f"{name}:{i + 1}: wrong answer")
                    wrong.add(name)
        # The number of factorized polynomials must match,
        # excluding any single-term polynomials.
        if len(results) >= 2:
            for i in range(len(problems)):
                pp0 = results[0].res[i].answer
                n0 = count_factors(pp0)
                for j in range(1, len(results)):
                    ppj = results[j].res[i].answer
                    nj = count_factors(ppj)
                    if n0 != nj:
                        name0 = results[0].name
                        namej = results[j].name
                        check_logger.error(
                            f"{name0}:{namej}:{i + 1}: inconsistent answers"
                        )
                        wrong.add(name0)
                        wrong.add(namej)

    # Remove the solver's output directory only if succeeded.

    if not keep_temp:
        for name, _, path in results:
            if name not in wrong and path.exists():
                shutil.rmtree(path)

    if results:
        # Write the timings into a CSV file.

        output_csv_file = output_dir / f"{job_id}.csv"

        plot.write_csv(
            output_csv_file, problems, {name: res for name, res, _ in results}
        )

        logger.info(f"output_csv_file = {output_csv_file}")

        # Generate plots.

        plot_output_dir = output_csv_file.with_suffix(".figures")

        if plot_suffixes:
            for suffix in plot_suffixes:
                plot.make_plots(
                    output_csv_file, plot_output_dir, "." + suffix, title=plot_title
                )

            logger.info(f"figures are in {plot_output_dir}")


def main(
    *,
    args: Optional[Sequence[str]] = None,
    stderr_color_hook: Optional[Callable[[bool], None]] = None,
) -> None:
    """Entry point."""
    # First, parse the arguments.

    if args is None:
        args = sys.argv[1:]

    defined_problem_types = get_problem_type_input_args()
    defined_exp_dists = get_exponents_distribution_args()

    parser = argparse.ArgumentParser(prog="polybench")
    parser.add_argument(
        "--type",
        default="nontrivial-gcd",
        choices=defined_problem_types,
        help="set the type of the problems:"
        " trivial-gcd [gcd(a*b,c*d)],"
        " nontrivial-gcd [gcd(a*g,b*g)],"
        " trivial-factor [factor(a*b+c)]"
        " or nontrivial-factor [factor(a*b)]"
        " (default: nontrivial-gcd)",
        metavar="TYPE",
    )
    parser.add_argument(
        "--nproblems",
        default=50,
        type=int,
        help="set the number of problems (default: 50)",
        metavar="N",
    )
    parser.add_argument(
        "--nwarmups",
        default=10,
        type=int,
        help="set the number of warm-up problems (default: 10)",
        metavar="N",
    )
    parser.add_argument(
        "--exp-dist",
        default="uniform",
        choices=defined_exp_dists,
        help="set the exponents distribution: uniform or sharp (default: uniform)",
        metavar="DIST",
    )
    parser.add_argument(
        "--nvars",
        default=5,
        type=int,
        help="set the number of variables (default: 5)",
        metavar="N",
    )
    parser.add_argument(
        "--min-nterms",
        default=None,
        type=int,
        help="set the minimum number of terms in a basic-block polynomial"
        " (default: max-nterms * 0.75)",
        metavar="N",
    )
    parser.add_argument(
        "--max-nterms",
        default=30,
        type=int,
        help="set the maximum number of terms in a basic-block polynomial"
        " (default: 30)",
        metavar="N",
    )
    parser.add_argument(
        "--min-degree",
        default=None,
        type=int,
        help="set the minimum degree of basic-block polynomials"
        " (default: max-degree * 0.75 for exp-dist=uniform, 0 for exp-dist=sharp)",
        metavar="N",
    )
    parser.add_argument(
        "--max-degree",
        default=30,
        type=int,
        help="set the maximum degree of basic-block polynomials (default: 30)",
        metavar="N",
    )
    parser.add_argument(
        "--min-coeff",
        default=None,
        type=int,
        help="set the minimum coefficient (default: - max_coeff)",
        metavar="N",
    )
    parser.add_argument(
        "--max-coeff",
        default=2**14,
        type=int,
        help="set the maximum coefficient (default: 2^14)",
        metavar="N",
    )
    parser.add_argument(
        "--build-directory",
        default=None,
        type=str,
        help="set the build directory (default: build)",
        metavar="DIR",
    )
    parser.add_argument(
        "--output-directory",
        default=None,
        type=str,
        help="set the output directory (default: output)",
        metavar="DIR",
    )
    parser.add_argument(
        "--plot-suffixes",
        default="pdf",
        type=str,
        help="comma separated list of plot file suffixes (default: pdf; "
        f"supported suffixes: {', '.join(plot.get_supported_filetypes())})",
        metavar="SUFFIX1,SUFFIX2,...",
    )
    parser.add_argument(
        "--seed",
        default=42,
        type=int,
        help="set the random seed (default: 42)",
        metavar="N",
    )
    parser.add_argument(
        "--timeout",
        default=60 * 60,
        type=int,
        help="set the timeout in seconds (default: 1 hour)",
        metavar="N",
    )
    parser.add_argument(
        "--color",
        default="auto",
        choices=["auto", "always", "never"],
        help="specify whether to use color for the terminal output:"
        " auto, always or never (default: auto)",
        metavar="MODE",
    )
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="build executables but skip actual benchmarks",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="don't delete temporary files",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable the debug mode",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="run all solvers",
    )
    for c in Solver.get_solver_classes():
        name = c._name
        if c._env_var:
            extra_info = f" (environment variable: {c._env_var})"
        else:
            extra_info = ""
        parser.add_argument(
            f"--{name.lower()}",
            action="append_const",
            const=f"{name}",
            help=f"run {name} solver{extra_info}",
            dest="solvers",
        )

    opts = parser.parse_args(args=args)

    # Initialise colours in the terminal before other things.
    color = cast(str, opts.color)
    strip: Optional[bool] = None  # for "auto"
    if color == "always":
        strip = False
    elif color == "never":
        strip = True
    colorama.deinit()  # See: https://github.com/tartley/colorama/issues/205
    old_stderr = sys.stderr  # must be the original one
    colorama.init(strip=strip)
    if stderr_color_hook:
        stderr_color_hook(old_stderr == sys.stderr)

    problem_type = cast(ProblemTypeInput, opts.type)
    n_problems = cast(int, opts.nproblems)
    n_warmups = cast(int, opts.nwarmups)
    exp_dist = cast(ExponentsDistribution, opts.exp_dist)
    n_vars = cast(int, opts.nvars)
    max_n_terms = cast(int, opts.max_nterms)
    max_degree = cast(int, opts.max_degree)
    max_coeff = cast(int, opts.max_coeff)
    seed = cast(int, opts.seed)
    timeout = cast(int, opts.timeout)
    build_only = cast(bool, opts.build_only)
    keep_temp = cast(bool, opts.keep_temp)
    debug = cast(bool, opts.debug)

    if opts.min_nterms is not None:
        min_n_terms = cast(int, opts.min_nterms)
    else:
        min_n_terms = max(int(max_n_terms * 0.75), 1)

    if opts.min_degree is not None:
        min_degree = cast(int, opts.min_degree)
    else:
        if exp_dist == "uniform":
            min_degree = max(int(max_degree * 0.75), 0)
        else:
            min_degree = 0

    if opts.min_coeff is not None:
        min_coeff = cast(int, opts.min_coeff)
    else:
        min_coeff = -max_coeff

    if opts.build_directory is not None:
        build_dir = Path(opts.build_directory)
    else:
        build_dir = Path(".") / "build"

    build_dir = build_dir.resolve()

    if opts.output_directory is not None:
        output_dir = Path(opts.output_directory)
    else:
        output_dir = Path(".") / "output"

    output_dir = output_dir.resolve()

    plot_suffixes = cast(str, opts.plot_suffixes).split(",")
    plot_suffixes = list(OrderedDict.fromkeys(plot_suffixes))  # remove duplicates
    plot_suffixes = [s for s in plot_suffixes if s]  # remove empty suffixes

    supported_suffixes = plot.get_supported_filetypes()
    if any(s not in supported_suffixes for s in plot_suffixes):
        unsupported_suffixes = [s for s in plot_suffixes if s not in supported_suffixes]
        raise ValueError(f"unsupported file format: {', '.join(unsupported_suffixes)}")

    if not opts.solvers and not opts.all:
        raise ValueError(
            "no solvers specified. You need to specify at least one solver to be run. "
            "You can use --all option to run all solvers available"
        )

    # Create problems.

    problems = ProblemSet(
        problem_type=problem_type,
        n_warmups=n_warmups,
        n_problems=n_problems,
        seed=seed,
        exp_dist=exp_dist,
        n_vars=n_vars,
        min_n_terms=min_n_terms,
        max_n_terms=max_n_terms,
        min_degree=min_degree,
        max_degree=max_degree,
        min_coeff=min_coeff,
        max_coeff=max_coeff,
    )

    # Set up the logger.

    job_id = next_job_id(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / f"{job_id}.log"

    logger = logging.getLogger(__name__).getChild("Bench")

    if debug:
        logger.setLevel(logging.DEBUG)
        Solver.debug = True
    else:
        logger.setLevel(logging.INFO)

    def name_filter(record: logging.LogRecord) -> bool:
        record.name = record.name.split(".")[-1]
        return True

    stream_handler = colorlog.StreamHandler()
    stream_handler.addFilter(name_filter)
    stream_handler.setFormatter(
        colorlog.ColoredFormatter(
            "{log_color}[{levelname:^8}] {name:12}{reset}{message_log_color}{message}",
            style="{",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={
                "message": {"WARNING": "yellow", "ERROR": "red", "CRITICAL": "red"}
            },
        )
    )
    logger.addHandler(stream_handler)

    logger.info(f"log_file = {log_file}")  # Before the log file is opened.

    log_file_handler = logging.FileHandler(log_file)
    log_file_handler.addFilter(name_filter)
    log_file_handler.setFormatter(
        logging.Formatter(
            "{asctime} [{levelname:^8}] {name:12}{message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(log_file_handler)

    # Create solvers.

    solvers = Solver.create_solvers(
        job_id=job_id,
        build_dir=build_dir,
        output_dir=output_dir,
        logger=logger,
        timeout=timeout,
    )

    if opts.solvers:
        unknown_solvers = [
            s for s in opts.solvers if all(s.lower() != t.name.lower() for t in solvers)
        ]

        if unknown_solvers:
            raise ValueError(f"unknown solvers specified: {unknown_solvers}")

    if not opts.all:
        solvers = [
            s for s in solvers if any(s.name.lower() == t.lower() for t in opts.solvers)
        ]

    # Title for plots.

    plot_title = (
        f"{problem_type} ({exp_dist}, # vars = {n_vars}, "
        f"max degrees = {max_degree}, max # terms = {max_n_terms})"
    )

    # Do benchmarks.

    config_log(
        logger,
        problem_type=problem_type,
        n_warmups=n_warmups,
        n_problems=n_problems,
        exp_dist=exp_dist,
        n_vars=n_vars,
        min_n_terms=min_n_terms,
        max_n_terms=max_n_terms,
        min_degree=min_degree,
        max_degree=max_degree,
        min_coeff=min_coeff,
        max_coeff=max_coeff,
        build_dir=build_dir,
        output_dir=output_dir,
        job_id=job_id,
        seed=seed,
        timeout=timeout,
        build_only=build_only,
        keep_temp=keep_temp,
        debug=debug,
    )

    solvers = prepare_solvers(solvers, problems)

    if solvers and not build_only:
        run_solvers(
            solvers,
            problems,
            job_id=job_id,
            output_dir=output_dir,
            plot_title=plot_title,
            plot_suffixes=plot_suffixes,
            logger=logger,
            keep_temp=keep_temp,
        )
