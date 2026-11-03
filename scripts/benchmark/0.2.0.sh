#!/bin/bash
set -eu
set -o pipefail

if [ $# -eq 0 ]; then
  cat >&2 <<END
Usage: $(basename -- "$0") <output-directory>

Environment variables:
  POLYBENCH_COMMAND
    Command to run polybench.
    Default: ./run.sh when unset or empty.

  POLYBENCH_OPTIONS
    Additional options for polybench, separated by whitespace.
    Default: --no-polymojocertified when unset.
    An empty string adds no options.

  POLYBENCH_RESULT_DIR
    Parent directory for results.
    Relative paths are resolved from the repository root.
    Default: ../polybench-result relative to the repository root,
             if present; otherwise the repository root itself.
END
  exit 1
fi

output_dir=$1
root_dir=$(cd -- "$(dirname -- "$0")" &>/dev/null && cd ../.. &>/dev/null && pwd)

cd "$root_dir" || {
  echo "$root_dir not found" >&2
  exit 1
}

polybench_command="${POLYBENCH_COMMAND:-./run.sh}"

read -r -a polybench_options <<<"${POLYBENCH_OPTIONS---no-polymojocertified}"

if [ -n "${POLYBENCH_RESULT_DIR:-}" ]; then
  result_dir="$POLYBENCH_RESULT_DIR"
elif [ -d "../polybench-result" ]; then
  result_dir=$(cd "$root_dir" &>/dev/null && cd ../polybench-result &>/dev/null && pwd)
else
  echo "!!!!! ../polybench-result not found !!!!!" >&2
  result_dir=$root_dir
fi

"$polybench_command" --build-only --all --debug "${polybench_options[@]}"

run020() {
  "$polybench_command" --all --output-directory "$result_dir/$output_dir" \
    --plot-suffixes png "${polybench_options[@]}" \
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
