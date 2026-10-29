polybench
=========

[![Test](https://github.com/tueda/polybench/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/tueda/polybench/actions?query=branch:main)
[![PyPI version](https://badge.fury.io/py/polybench.svg)](https://pypi.org/project/polybench/)

Multivariate polynomial arithmetic benchmark tests.

Many scientific and engineering applications utilise multivariate polynomial
arithmetic in their algorithms and solutions. Here we provide a set of
benchmark tests for often-used operations in multivariate polynomial
arithmetic:

- Greatest common divisor
- Factorisation


Requirements
------------

- [Python](https://www.python.org/) >= 3.6.1

You also need at least one or more tools to be benchmarked.
They are (in alphabetical order):

- [Fermat](https://home.bway.net/lewis/)
- [FLINT](https://flintlib.org/): automatically downloaded via [vcpkg](https://vcpkg.io/)
  (requires [CMake](https://cmake.org/) >= 3.15, a C compiler and the Make utility;
  see also [vcpkg dependencies](https://learn.microsoft.com/en-us/vcpkg/concepts/supported-hosts#dependencies)).
- [FORM](https://www.nikhef.nl/~form/):
  if not available in the system, then
  a [release binary](https://github.com/vermaseren/form/releases)
  will be automatically downloaded.
- [Mathematica](https://www.wolfram.com/mathematica/):
  indeed, [Free Wolfram Engine for Developers](https://www.wolfram.com/engine/) is sufficient to run.
- [Poly Mojo](https://github.com/Spellbound-Mojo/poly_mojo):
  automatically installed with its matching Mojo compiler via [Pixi](https://pixi.sh/)
  on Linux x86-64; see [Poly Mojo setup](#poly-mojo-setup) below.
- [reFORM](https://reform.readthedocs.io/en/latest/):
  automatically downloaded
  (requires [Rust](https://www.rust-lang.org/) >= 1.36).
- [Rings](https://rings.readthedocs.io/en/latest/):
  automatically downloaded
  (requires [JDK](https://www.oracle.com/technetwork/java/) >= 8).
- [Singular](https://www.singular.uni-kl.de/)
- [Symbolica](https://symbolica.io/):
  version 3.0.1, automatically downloaded
  (requires [Rust](https://www.rust-lang.org/) >= 1.96),
  running in [restricted mode](https://symbolica.io/docs/get_started.html#license).
  Built with optimization level 3, full link-time optimization, one codegen unit,
  and `target-cpu=native`, with Symbolica's default faster allocator and GMP backend.
  The executable is optimized for the build machine; rebuild it on each benchmark
  machine. Set `RUSTFLAGS` to override the CPU settings when needed.


Getting started
---------------

Clone this repository and try to run the `run.sh` script:

```sh
git clone https://github.com/tueda/polybench.git
cd polybench
./run.sh --all
```

When starting the script for the first time, it automatically sets up
a virtual environment for required Python packages so that it will not dirty
your environment. Some of the tools are provided as libraries registered in
public package registries, so the first run takes some time to download,
compile and link them with test binaries. After testing, a CSV file and
comparison plots will be generated.

For practical benchmarking, configuration parameters should be set
adequately. See the help message shown by

```sh
./run.sh --help
```

You can also use [pip](https://pip.pypa.io/en/stable/),
[pipx](https://pipxproject.github.io/pipx/),
[Poetry](https://python-poetry.org/)
or [Docker](https://www.docker.com/) with this repository.
Installation with `pip(x) install` or `poetry install` makes a command
`polybench` available, which acts as the `run.sh` script described above.
```sh
pip install polybench
polybench --all
python -m polybench --all  # alternative way to launch
```
```sh
pipx install polybench
polybench --all
```
```sh
git clone https://github.com/tueda/polybench.git
cd polybench
poetry install
poetry run polybench --all
```
```sh
docker build -t polybench:latest https://github.com/tueda/polybench.git
docker run -it --rm polybench:latest
./run.sh --all
```


Poly Mojo setup
--------------

The `--polymojo` backend measures ordinary integer GCD and factorisation.
`--polymojocertified` measures the operation together with certificate construction
and checks every certificate before accepting a result. Its CSV time excludes
verification; per-case `compute_ns` and `verification_ns` are saved in
`certificate-timings.json` inside the solver output directory when using
`--keep-temp`. Compilation, input parsing and output serialisation are untimed.
The ordinary factorisation API still constructs some evidence internally.
Its factorisation certificate checks recomposition; polybench's existing checks
also compare products and factor counts with other backends.

Install [Pixi](https://pixi.sh/), then run from the polybench checkout:

```sh
./run.sh --polymojo --polymojocertified --keep-temp \
  --type nontrivial-gcd --nvars 2 --max-degree 3 --max-nterms 4
```

The adapter automatically installs precompiled **Poly Mojo 1.0.2**, **APN Mojo
1.0.2**, and their matching **Mojo 1.2.0** compiler on Linux x86-64. The backend's
[manifest and lockfile](polybench/solvers/polymojo/pixi.toml) pin the package builds.
Both modes share the environment and cached drivers under `build/polymojo-shared`;
no shell activation, package-path configuration, or library source build is needed.
Installation and driver compilation happen before benchmark timers start.

For source development, `POLY_MOJO_PATH` can instead point to an absolute directory
containing precompiled `poly.mojoc`, `polynomials.mojoc` and `apn_mojo.mojoc` files.
With this override, activate the matching Mojo environment and optionally select
its compiler with `MOJO_COMMAND`; Pixi installation is bypassed.

Changing the compiler, runtime location, driver source or package contents
invalidates the driver cache. Package hashes and compiler details are saved in
`provenance.json` with `--keep-temp`. To run other backends without installing
Poly Mojo, use `--all --no-polymojo --no-polymojocertified`.


Example
-------

|                |                                                                      |
| -------------- | -------------------------------------------------------------------- |
| platform       | Linux-5.15.0-84-generic-x86_64-with-glibc2.29                        |
| python_version | 3.8.10.final.0 (64 bit)                                              |
| cpu_brand      | 12th Gen Intel(R) Core(TM) i9-12900                                  |
| cpu_count      | 16 (logical: 24)                                                     |
| total_memory   | 62.6GB                                                               |
| FLINT          | flint 3.5.0, gcc-11 (GNU) 11.5.0                                     |
| FORM           | FORM 5.0.1 (Jun 24 2026, v5.0.1)                                     |
| Mathematica    | 15.0.0 for Linux x86 (64-bit) (May 26, 2026)                         |
| reFORM         | 0.1.0-fix-serialize, rustc 1.97.1 (8bab26f4f 2026-07-14)             |
| Rings          | 2.5.8, JVM: 11.0.20.1 (Ubuntu 11.0.20.1+1-post-Ubuntu-0ubuntu120.04) |
| Singular       | Singular for x86_64-Linux version 4.4.1 (44100, 64 bit) Jan 2025     |
| Symbolica      | 2.2.0, rustc 1.97.1 (8bab26f4f 2026-07-14)                           |

![nontrivial-gcd](https://raw.githubusercontent.com/tueda/polybench-result/refs/heads/main/0.4.3/05/0002.figures/summary.png)

![nontrivial-factor](https://raw.githubusercontent.com/tueda/polybench-result/refs/heads/main/0.4.3/05/0004.figures/summary.png)

Additional benchmark results are available [here](https://github.com/tueda/polybench-result/tree/main).


Development
-----------

```bash
# Initialisation
poetry install
poetry run pre-commit install

# Linting and testing
poetry run pre-commit run --all-files
poetry run pytest

# Linting and testing for Cargo subproject
cd path/to/project
cargo fmt
cargo clippy
cargo test

# Linting and testing for Gradle subproject
cd path/to/project
./gradlew spotlessApply
./gradlew check

# Test run
./run.sh <options>  # for example, --all

# Release a new version
./scripts/make-release.sh <new_version>  # for example, 0.3.0rc1
```


License
-------

[MIT](https://github.com/tueda/polybench/blob/main/LICENSE)
