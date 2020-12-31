"""Problems for benchmarking."""

import functools
import itertools
import math
import random
from typing import Any, Iterator, Sequence

from typing_extensions import Literal

from .poly import Polynomial


@functools.lru_cache(maxsize=128)
def variables(n_vars: int) -> Sequence[str]:
    """Return a set of variables."""
    return tuple(f"x{i + 1}" for i in range(n_vars))


ExponentsDistribution = Literal["uniform", "sharp"]


# Unfortunately {typing/typing_extensions}.get_args is not available in Python 3.6.
# Instead, we make a function to extract the members.
def get_exponents_distribution_args() -> Sequence[str]:
    """Return ``typing.get_args(ExponentsDistribution)``."""
    return ("uniform", "sharp")


def random_polynomial(
    *,
    exp_dist: ExponentsDistribution,
    n_vars: int,
    min_n_terms: int,
    max_n_terms: int,
    min_degree: int,
    max_degree: int,
    min_coeff: int,
    max_coeff: int,
) -> Polynomial:
    """Return a random polynomial."""
    coeff_max_trial = 10
    poly_max_trial = 100

    if n_vars < 1:
        raise ValueError(f"n_vars ({n_vars}) must be >= 1")

    if max_n_terms < 1:
        raise ValueError(f"max_n_terms ({max_n_terms}) must be >= 1")

    if max_degree < 1:
        raise ValueError(f"max_degree ({max_degree}) must be >= 1")

    if max_coeff < 1:
        raise ValueError(f"max_coeff ({max_coeff}) must be >= 1")

    if min_n_terms < 1:
        raise ValueError(f"min_n_terms ({min_n_terms}) must be >= 1")

    if min_n_terms > max_n_terms:
        raise ValueError(
            f"min_n_terms ({min_n_terms}) must be <= max_n_terms ({max_n_terms})"
        )

    if min_degree < 0:
        raise ValueError(f"min_degree ({min_degree}) must be >= 0")

    if min_degree > max_degree:
        raise ValueError(
            f"min_degree ({min_degree}) must be <= max_degree ({max_degree})"
        )

    if min_coeff > max_coeff:
        raise ValueError(f"min_coeff ({min_coeff}) must be <= max_coeff ({max_coeff})")

    xx = variables(n_vars)
    indices = tuple(range(n_vars))
    cum_weights = None

    if exp_dist == "uniform":
        pass
    elif exp_dist == "sharp":
        if n_vars >= 2:
            # distribution: a exp(b x)
            a = max(min_degree, 0.1)  # avoids max_degree / 0
            b = 1 / (n_vars - 1) * math.log(max_degree / a)
            weight = [a * math.exp(b * i) for i in range(n_vars)]
            random.shuffle(weight)
            cum_weights = tuple(itertools.accumulate(weight))
    else:
        raise ValueError(f"unknown exp_dist: {exp_dist}")

    def random_coeff() -> int:
        """Return a coefficient randomly."""
        for _ in range(coeff_max_trial):
            n = random.randint(min_coeff, max_coeff)
            if n != 0:
                return n
        return 1

    def random_monomial() -> str:
        """Return a monomial randomly."""
        c = random_coeff()
        if c < 0:
            result = f"-{-c}"
        else:
            result = f"+{c}"

        n = random.randint(min_degree, max_degree)
        exponents = random.choices(indices, cum_weights=cum_weights, k=n)
        exponents.sort()
        for i, group in itertools.groupby(exponents):
            x = xx[i]
            p = len(tuple(group))
            result += f"*{x}"
            if p != 1:
                result += f"^{p}"

        return result

    n_terms = random.randint(min_n_terms, max_n_terms)

    for _ in range(poly_max_trial):
        poly_str = "".join(random_monomial() for _ in range(n_terms))

        # We guarantee that the result is non-zero.
        poly = Polynomial(poly_str)
        if poly:
            return poly

    raise RuntimeError("failed to generate a random polynomial")


ProblemTypeInput = Literal[
    "trivial-gcd", "nontrivial-gcd", "trivial-factor", "nontrivial-factor"
]


ProblemType = Literal["gcd", "factor"]


# Unfortunately {typing/typing_extensions}.get_args is not available in Python 3.6.
# Instead, we make a function to extract the members.
def get_problem_type_input_args() -> Sequence[str]:
    """Return ``typing.get_args(ProblemTypeInput)``."""
    return ("trivial-gcd", "nontrivial-gcd", "trivial-factor", "nontrivial-factor")


def problem_type_from_input(type_input: ProblemTypeInput) -> ProblemType:
    """Convert `ProblemTypeInput` into `ProblemType`."""
    if type_input in ("trivial-gcd", "nontrivial-gcd"):
        return "gcd"
    if type_input in ("trivial-factor", "nontrivial-factor"):
        return "factor"
    raise ValueError(f"type_input: {type_input}")


class Problem:
    """Problem.

    A problem to be solved, which is:
    a `gcd` problem to solve ``PolynomialGCD(problem.p, problem.q)`` or
    a `factor` problem to solve `Factor(problem.p)`.
    """

    def __init__(self, *, problem_type: ProblemTypeInput, **kwargs: Any) -> None:
        """Construct a problem."""

        def rand_poly() -> Polynomial:
            # We assume that all required parameters are given in `kwargs`.
            return random_polynomial(**kwargs)

        if problem_type == "trivial-gcd":
            a = rand_poly()
            b = rand_poly()
            c = rand_poly()
            d = rand_poly()
            self.p = a * b  # most likely trivial
            self.q = c * d
        elif problem_type == "nontrivial-gcd":
            a = rand_poly()
            b = rand_poly()
            g = rand_poly()
            self.p = a * g  # gcd is expected to be g
            self.q = b * g
        elif problem_type == "trivial-factor":
            a = rand_poly()
            b = rand_poly()
            c = rand_poly()
            self.p = a * b + c  # most likely trivial
        elif problem_type == "nontrivial-factor":
            a = rand_poly()
            b = rand_poly()
            self.p = a * b  # factored as a and b

        self.problem_type = problem_type_from_input(problem_type)

    def __str__(self) -> str:
        """Return the string representation."""
        if self.problem_type == "gcd":
            return f"gcd({self.p},{self.q})"
        if self.problem_type == "factor":
            return f"factor({self.p})"
        return repr(self)


class ProblemSet:
    """Set of problems."""

    def __init__(
        self,
        *,
        problem_type: ProblemTypeInput,
        n_warmups: int,
        n_problems: int,
        seed: int,
        **kwargs: Any,
    ):
        """Construct a set of problems."""
        assert "n_vars" in kwargs  # noqa: S101  # We assume this.
        n_vars = int(kwargs["n_vars"])

        self._problem_type = problem_type_from_input(problem_type)
        self._n_vars = n_vars
        self._n_warmups = n_warmups
        self._n_problems = n_problems
        self._seed = seed

        random.seed(seed)  # Fix the seed here for reproducibility.

        self._problems = [
            Problem(problem_type=problem_type, **kwargs)
            for _ in range(n_warmups + n_problems)
        ]

    def __len__(self) -> int:
        """Return the total number of the problems (including warm-ups)."""
        return len(self._problems)

    def __iter__(self) -> Iterator[Problem]:
        """Return the iterator."""
        return self._problems.__iter__()

    def __getitem__(self, i: int) -> Problem:
        """Return a result."""
        return self._problems[i]

    @property
    def problem_type(self) -> ProblemType:
        """Return the problem type."""
        return self._problem_type

    @property
    def n_vars(self) -> int:
        """Return the number of variables."""
        return self._n_vars

    @property
    def variables(self) -> Sequence[str]:
        """Return the variables."""
        return variables(self._n_vars)

    @property
    def n_warmups(self) -> int:
        """Return the number of warm-ups."""
        return self._n_warmups

    @property
    def n_problems(self) -> int:
        """Return the number of problems."""
        return self._n_problems

    @property
    def seed(self) -> int:
        """Return the random seed."""
        return self._seed
