#!/bin/bash
set -eu
set -o pipefail

python3=${PYTHON_COMMAND:-python3}

if $python3 -c 'import sys; exit(0 if sys.version_info < (3, 6, 1) else 1)'; then
  echo 'This script is only for use with Python 3.6.1 or later' >&2
  exit 1
fi

# Ensure required packages.

root_path="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

if [[ -f /.dockerenv ]] && [[ ! -v CI ]]; then
  # Inside a Docker container (assumed to be created from the Dockerfile).
  # The required packages have been installed via Poetry.
  venv_python3=$python3
else
  # Use a virtual environment.

  venv_path=$root_path/.venv
  venv_python3=$venv_path/bin/python3

  if [[ ! -d $venv_path ]]; then
    echo 'Initializing virtualenv...'
    $python3 -m venv "$venv_path"
    $venv_python3 -m pip install --upgrade pip
    $venv_python3 -m pip install poetry
    (
      cd $root_path
      $venv_python3 -m poetry config --local virtualenvs.in-project true
      $venv_python3 -m poetry install --no-dev --no-interaction --no-root
    )
  fi
fi

# Run the main script.

export PYTHONPATH=${PYTHONPATH:+${PYTHONPATH}:}$root_path

$venv_python3 -m polybench --build-dir "$root_path/build" "$@"
