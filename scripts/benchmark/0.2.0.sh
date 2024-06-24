#!/bin/bash
set -eu
set -o pipefail

if [ $# -eq 0 ]; then
  echo "Usage: $(basename -- "${BASH_SOURCE[0]}") <output-directory>" >&2
  exit 1
fi

output_dir=$1

root_path=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && cd ../.. &>/dev/null && pwd)

cd "$root_path"

if [ -d "../polybench-result" ]; then
  result_path=$(cd "$root_path" &>/dev/null && cd ../polybench-result &>/dev/null && pwd)
else
  echo "!!!!! ../polybench-result not found !!!!!" >&2
  result_path=$root_path
fi

./run.sh --build-only --all --debug

default_args='--nproblems 50 --nwarmups 10 --exp-dist uniform --nvars 5 --max-nterms 30 --max-degree 30 --max-coeff 16384 --seed 42 --timeout 3600'

# shellcheck disable=SC2086
./run.sh --type trivial-gcd --all --output-directory "$result_path/$output_dir" --plot-suffixes png $default_args

# shellcheck disable=SC2086
./run.sh --type nontrivial-gcd --all --output-directory "$result_path/$output_dir" --plot-suffixes png $default_args

# shellcheck disable=SC2086
./run.sh --type trivial-factor --all --output-directory "$result_path/$output_dir" --plot-suffixes png $default_args

# shellcheck disable=SC2086
./run.sh --type nontrivial-factor --all --output-directory "$result_path/$output_dir" --plot-suffixes png $default_args
