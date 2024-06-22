"""Routines for making comparison plots."""

import itertools
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame

from .prob import ProblemSet
from .solver import Result


def write_csv(
    csv_file: Path, problems: ProblemSet, results: Dict[str, Sequence[Result]]
) -> None:
    """Write the given results into a CSV file."""
    data: Dict[str, Union[Sequence[int], Sequence[float]]] = {}
    data.update(
        {"problem_number": list(range(problems.n_warmups + 1, len(problems) + 1))}
    )
    data.update(
        {
            name: [r.time for r in res[problems.n_warmups :]]
            for name, res in results.items()
        }
    )
    df = pd.DataFrame(data)

    df.to_csv(csv_file, index=False)


def get_supported_filetypes() -> Sequence[str]:
    """Return the list of supported file formats."""
    return tuple(plt.gcf().canvas.get_supported_filetypes().keys())


def make_plots(
    csv_file: Path,
    output_dir: Path,
    suffix: str = ".pdf",
    *,
    title: Optional[str] = None,
) -> None:
    """Create comparison plots from the given CSV file."""
    df = pd.read_csv(csv_file)

    names = [s for s in df.columns if s != "problem_number"]

    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"summary{suffix}"
    make_summary_plot(df, names, output_file, title=title)

    for x, y in itertools.combinations(names, 2):
        output_file = output_dir / f"{x}_vs_{y}{suffix}"
        make_comparison_plot(df, x, y, output_file, title=title)


def make_summary_plot(
    df: DataFrame,
    names: Sequence[str],
    output_file: Path,
    *,
    title: Optional[str] = None,
) -> None:
    """Create a summary plot for the given data."""
    data = [df[name] for name in names]

    all_t = [t for t in sum((list(x) for x in data), []) if t != 0]

    min_t = 10 ** np.floor(np.log10(min(all_t)))
    max_t = 10 ** np.ceil(np.log10(max(all_t)))
    t_range = [min_t / 1.5, max_t * 1.5]

    fig, ax = plt.subplots()

    ax.boxplot(
        data,
        showmeans=True,
        sym=".",
        flierprops={"markeredgecolor": "red"},
        meanprops={"marker": "*"},
    )

    if title:
        ax.set_title(title, fontsize=10)

    ax.set_xticklabels(names, rotation=45)
    ax.set_ylabel("Elapsed time (s)")
    ax.set_ylim(t_range)
    ax.set_yscale("log")
    ax.yaxis.grid()

    fig.tight_layout()
    fig.savefig(output_file)
    plt.close()


def make_comparison_plot(
    df: DataFrame,
    x_name: str,
    y_name: str,
    output_file: Path,
    title: Optional[str] = None,
) -> None:
    """Create a comparison plot for the given two solvers."""
    x_points = df[x_name]
    y_points = df[y_name]

    all_t = [t for t in tuple(x_points) + tuple(y_points) if t != 0]

    min_t = 10 ** np.floor(np.log10(min(all_t)))
    max_t = 10 ** np.ceil(np.log10(max(all_t)))
    t_range = [min_t / 1.5, max_t * 1.5]

    fig, ax = plt.subplots()

    if title:
        ax.set_title(title, fontsize=10)

    ax.set_xlabel(f"{x_name} elapsed time (s)")
    ax.set_ylabel(f"{y_name} elapsed time (s)")

    ax.set_xlim(t_range)
    ax.set_ylim(t_range)

    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.set_aspect("equal")
    ax.grid()

    ax.plot(t_range, t_range, "--", color="gray")
    ax.scatter(x_points, y_points, color="pink", alpha=0.5, edgecolors="red")

    fig.tight_layout()
    fig.savefig(output_file)
    plt.close()
