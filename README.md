polybench
=========

[![Test](https://github.com/tueda/polybench/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/tueda/polybench/actions?query=branch:master)
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
  (requires [CMake](https://cmake.org/) >= 3.15, a C compiler and the Make utility).
- [FORM](https://www.nikhef.nl/~form/):
  if not available in the system, then
  a [release binary](https://github.com/vermaseren/form/releases)
  will be automatically downloaded.
- [Mathematica](https://www.wolfram.com/mathematica/):
  indeed, [Free Wolfram Engine for Developers](https://www.wolfram.com/engine/) is sufficient to run.
- [reFORM](https://reform.readthedocs.io/en/latest/):
  automatically downloaded
  (requires [Rust](https://www.rust-lang.org/) >= 1.36).
- [Rings](https://rings.readthedocs.io/en/latest/):
  automatically downloaded
  (requires [JDK](https://www.oracle.com/technetwork/java/) >= 8).
- [Singular](https://www.singular.uni-kl.de/)


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


Example
-------

|                |                                                                 |
|----------------|-----------------------------------------------------------------|
| platform       | Linux-3.10.0-957.21.3.el7.x86_64-x86_64-with-glibc2.23          |
| python_version | 3.9.9.final.0 (64 bit)                                          |
| cpu_brand      | Intel(R) Xeon(R) Gold 6248 CPU @ 2.50GHz                        |
| cpu_count      | 40                                                              |
| total_memory   | 754.6GB                                                         |
| FORM           | FORM 4.2.1 (Nov 21 2018, v4.2.1) 64-bits                        |
| Mathematica    | 13.0.0 for Linux x86 (64-bit) (December 10, 2021)               |
| reFORM         | 0.1.0-fix-serialize, rustc 1.56.1                               |
| Rings          | 2.5.8, JVM: 17.0.1 (Homebrew 17.0.1+1)                          |
| Singular       | Singular for x86_64-Linux version 4.2.1 (4210, 64 bit) May 2021 |

![nontrivial-gcd](https://github.com/tueda/polybench-result/raw/b31989da7eef19faf127bac177ad8d89a7e51e2c/0.2.0/0002.figures/summary.png)

![nontrivial-gcd](https://github.com/tueda/polybench-result/raw/b31989da7eef19faf127bac177ad8d89a7e51e2c/0.2.0/0004.figures/summary.png)

ReFORM has no factorization functionality.
Mathematica exceeded the timeout of 60 minutes for the "nontrivial-factor" test.


License
-------

[MIT](https://github.com/tueda/polybench/blob/master/LICENSE)
