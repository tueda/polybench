#!/bin/bash
set -eu
set -o pipefail

if [ $# -eq 0 ]; then
  echo "Usage: $(basename -- "$0") <output-directory>" >&2
  exit 1
fi

output_dir=$1
root_dir=$(cd -- "$(dirname -- "$0")" &>/dev/null && cd ../.. &>/dev/null && pwd)

cd "$root_dir" || { echo "$root_dir not found" >&2; exit 1; }

if [ -d "../polybench-result" ]; then
  result_dir=$(cd "$root_dir" &>/dev/null && cd ../polybench-result &>/dev/null && pwd)
else
  echo "!!!!! ../polybench-result not found !!!!!" >&2
  result_dir=$root_dir
fi

./run.sh --build-only --all --debug

run020() {
  ./run.sh --all --output-directory "$result_dir/$output_dir" --plot-suffixes png \
    --type trivial-gcd \
    --nproblems 50 \
    --nwarmups 10 \
    --exp-dist uniform \
    --nvars 5 \
    --max-nterms 30 \
    --max-degree 30 \
    --max-coeff 16384 \
    --seed 42 \
    --timeout 3600 \
    "$@"
}

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  return
fi

run020 --type trivial-gcd
run020 --type nontrivial-gcd
run020 --type trivial-factor
run020 --type nontrivial-factor
