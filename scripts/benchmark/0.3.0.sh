#!/bin/bash
set -eu
set -o pipefail

. "$(cd -- "$(dirname -- "$0")" && pwd)/0.2.0.sh"

run030() {
  local nvars
  nvars=$1
  shift
  run020 \
    --output-directory "$result_dir/$output_dir/$(printf "%02d" "$nvars")" \
    --nvars "$nvars" \
    --nproblems 200 \
    --max-nterms 50 \
    --timeout 21600 \
    "$@"
}

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  return
fi

run030 5 --type trivial-gcd --exp-dist uniform
run030 5 --type nontrivial-gcd --exp-dist uniform
run030 5 --type trivial-factor --exp-dist uniform
run030 5 --type nontrivial-factor --exp-dist uniform

run030 5 --type trivial-gcd --exp-dist sharp
run030 5 --type nontrivial-gcd --exp-dist sharp
run030 5 --type trivial-factor --exp-dist sharp
run030 5 --type nontrivial-factor --exp-dist sharp

run030 8 --type trivial-gcd --exp-dist uniform
run030 8 --type nontrivial-gcd --exp-dist uniform
run030 8 --type trivial-factor --exp-dist uniform
run030 8 --type nontrivial-factor --exp-dist uniform

run030 8 --type trivial-gcd --exp-dist sharp
run030 8 --type nontrivial-gcd --exp-dist sharp
run030 8 --type trivial-factor --exp-dist sharp
run030 8 --type nontrivial-factor --exp-dist sharp
