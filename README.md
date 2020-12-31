polybench
=========

[![Test](https://github.com/tueda/polybench/workflows/Test/badge.svg?branch=master)](https://github.com/tueda/polybench/actions?query=branch:master)
[![PyPI](https://img.shields.io/pypi/v/polybench)](https://pypi.python.org/pypi/polybench)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/tueda/polybench.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/tueda/polybench/context:python)

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
- [FORM](https://www.nikhef.nl/~form/):
  if not available in the system, then
  a [release binary](https://github.com/vermaseren/form/releases)
  will be automatically downloaded.
- [Mathematica](https://www.wolfram.com/mathematica/)
- [reFORM](https://reform.readthedocs.io/en/latest/):
  automatically downloaded
  (requires [Rust](https://www.rust-lang.org/) >= 1.36).
- [Rings](https://ringsalgebra.io/):
  automatically downloaded
  (requires [JDK](https://www.oracle.com/technetwork/java/) >= 8).
- [Singular](https://www.singular.uni-kl.de/)


Get started
-----------

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

You can also use [Poetry](https://python-poetry.org/)
or [Docker](https://www.docker.com/) with this repository.


License
-------

[MIT](https://github.com/tueda/polybench/blob/master/LICENSE)
