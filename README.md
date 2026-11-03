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

You also need at least one tool to be benchmarked.
They are (in alphabetical order):

- [Fermat](https://home.bway.net/lewis/):
  uses `fer64` on `PATH` by default; set `FERMAT_COMMAND` to specify a different executable.
- [FLINT](https://flintlib.org/): automatically downloaded and built via [vcpkg](https://vcpkg.io/)
  (requires [CMake](https://cmake.org/) >= 3.15, a C compiler and the Make utility;
  see also [vcpkg dependencies](https://learn.microsoft.com/en-us/vcpkg/concepts/supported-hosts#dependencies)).
- [FORM](https://www.nikhef.nl/~form/):
  uses `form` on `PATH` by default, downloading
  a [release binary](https://github.com/vermaseren/form/releases) if not found;
  set `FORM_COMMAND` to specify a different executable.
- [Mathematica](https://www.wolfram.com/mathematica/):
  [Free Wolfram Engine for Developers](https://www.wolfram.com/engine/) is sufficient to run.
  Uses `wolframscript` on `PATH` by default; set `WOLFRAMSCRIPT_COMMAND` to specify
  a different WolframScript executable.
- [Poly Mojo](https://github.com/Spellbound-Mojo/poly_mojo):
  `--polymojo` measures ordinary integer GCD and factorisation;
  `--polymojocertified` includes certificate construction in the measured operation
  and verifies each certificate, but excludes verification time from the reported
  measurement. Poly Mojo and its matching Mojo compiler are automatically
  downloaded via [Pixi](https://pixi.sh/) (required on `PATH`); the included
  configuration targets Linux x86-64. To use existing precompiled packages instead
  of this setup, set `POLY_MOJO_PATH` to an absolute directory containing `poly.mojoc`,
  `polynomials.mojoc`, and `apn_mojo.mojoc`. In this case the matching compiler
  defaults to `mojo` on `PATH` and can be selected with `MOJO_COMMAND`. In either
  case, a polybench benchmark program is built using the packages.
- [reFORM](https://reform.readthedocs.io/en/latest/):
  automatically downloaded and built
  (requires [Rust](https://www.rust-lang.org/) >= 1.36).
- [Rings](https://rings.readthedocs.io/en/latest/):
  automatically downloaded; the benchmark program is built
  (requires [JDK](https://www.oracle.com/technetwork/java/) >= 8).
- [Singular](https://www.singular.uni-kl.de/):
  uses `Singular` on `PATH` by default; set `SINGULAR_COMMAND` to specify a different executable.
- [Symbolica](https://symbolica.io/):
  automatically downloaded and built
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


Docker
------

The [Dockerfile](https://github.com/tueda/polybench/blob/main/Dockerfile) supports only `linux/amd64/v3`.

Build the image:

```sh
docker build --platform linux/amd64/v3 -t polybench .
```

Containers start in `/work`. Run with results kept inside the disposable
container:

```sh
docker run --rm polybench --all
```

To save results in the current directory on the host, mount it at `/work` and
use your UID/GID:

```sh
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" polybench --all
```

To start a shell with the same environment, use either:

```sh
docker run --rm -it polybench bash

docker run --rm -it --user "$(id -u):$(id -g)" -v "$PWD:/work" polybench bash
```

The image includes prepared solvers and Poly Mojo's 5- and 8-variable drivers;
other variable counts compile offline when first used in a container.

Fermat and Mathematica/Wolfram Engine are not included.

### Fermat

To use a host installation of Fermat, mount its directory and set
`FERMAT_COMMAND`. For example:

```sh
docker run --rm \
  -v /path/to/fermat-installation:/opt/fermat:ro \
  -e FERMAT_COMMAND=/opt/fermat/fer64 \
  polybench --fermat
```

### Wolfram Engine

To use a host installation of Wolfram Engine, mount WolframScript and the
Engine, and retain a separate directory for the container's license.
Use your host UID/GID for both activation and subsequent runs so that the
license files remain accessible. For example, with Wolfram Engine 15.0:

```sh
mkdir -p wolfram-license

docker run --rm -it --user "$(id -u):$(id -g)" \
  -v /opt/Wolfram/WolframScript:/opt/Wolfram/WolframScript:ro \
  -v /usr/local/Wolfram/WolframEngine/15.0:/usr/local/Wolfram/WolframEngine/15.0:ro \
  -v "$PWD/wolfram-license:/home/polybench/.WolframEngine/Licensing" \
  -e WOLFRAMSCRIPT_KERNELPATH=/usr/local/Wolfram/WolframEngine/15.0/Executables/WolframKernel \
  polybench /opt/Wolfram/WolframScript/bin/wolframscript -activate

docker run --rm --user "$(id -u):$(id -g)" \
  -v /opt/Wolfram/WolframScript:/opt/Wolfram/WolframScript:ro \
  -v /usr/local/Wolfram/WolframEngine/15.0:/usr/local/Wolfram/WolframEngine/15.0:ro \
  -v "$PWD/wolfram-license:/home/polybench/.WolframEngine/Licensing" \
  -e WOLFRAMSCRIPT_KERNELPATH=/usr/local/Wolfram/WolframEngine/15.0/Executables/WolframKernel \
  -e WOLFRAMSCRIPT_COMMAND=/opt/Wolfram/WolframScript/bin/wolframscript \
  polybench --mathematica
```

See [Wolfram's official Docker instructions](https://hub.docker.com/r/wolframresearch/wolframengine)
for activation and licensing details.


Example
-------

|                |                                                                              |
| -------------- | ---------------------------------------------------------------------------- |
| platform       | Linux-5.15.0-84-generic-x86_64-with-glibc2.39 (in Docker)                    |
| os_description | Ubuntu 24.04.4 LTS                                                           |
| python_version | 3.12.3.final.0 (64 bit)                                                      |
| cpu_brand      | 12th Gen Intel(R) Core(TM) i9-12900                                          |
| cpu_count      | 16 (logical: 24)                                                             |
| total_memory   | 62.6GB                                                                       |
| FLINT          | flint 3.6.0, cc (GNU) 13.3.0                                                 |
| FORM           | FORM 5.0.2 (Sep 16 2026, v5.0.2)                                             |
| Mathematica    | 15.0.0 for Linux x86 (64-bit) (May 26, 2026)                                 |
| PolyMojo       | Poly Mojo build 234ff4d0ac6c; Mojo 1.2.0 (2016d0cd); plain                   |
| reFORM         | 0.1.0-fix-serialize, rustc 1.99.1 (58cf8f9c3 2026-10-13)                     |
| Rings          | 2.5.8, JVM: 21.0.12.1 (Ubuntu 21.0.12.1+1-1-24.04.4-Ubuntu)                  |
| Singular       | Singular for x86_64-Linux version 4.4.1 (44105, 64 bit) Jan 20 2025 11:50:12 |
| Symbolica      | 3.0.1, rustc 1.99.1 (58cf8f9c3 2026-10-13)                                   |

![nontrivial-gcd](https://raw.githubusercontent.com/tueda/polybench-result/refs/heads/main/0.5.0/05/0002.figures/summary.png)

![nontrivial-factor](https://raw.githubusercontent.com/tueda/polybench-result/refs/heads/main/0.5.0/05/0004.figures/summary.png)

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
