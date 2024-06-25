#!/bin/bash
set -eu
set -o pipefail

. "$(cd -- "$(dirname -- "$0")" && pwd)/0.2.0.sh"

run030() {
  run020 "$@"
}

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  return
fi

run030() {
  local nvars
  nvars=$1
  shift
  run020 \
    --output-directory "$result_dir/$output_dir/$(printf "%02d" "$nvars")" \
    --nvars "$nvars" \
    --nproblems 200 \
    --max-nterms 50 \
    "$@"
}

run030 1 --type trivial-gcd --exp-dist uniform
run030 1 --type nontrivial-gcd --exp-dist uniform
run030 1 --type trivial-factor --exp-dist uniform
run030 1 --type nontrivial-factor --exp-dist uniform

run030 2 --type trivial-gcd --exp-dist uniform
run030 2 --type nontrivial-gcd --exp-dist uniform
run030 2 --type trivial-factor --exp-dist uniform
run030 2 --type nontrivial-factor --exp-dist uniform

run030 2 --type trivial-gcd --exp-dist sharp
run030 2 --type nontrivial-gcd --exp-dist sharp
run030 2 --type trivial-factor --exp-dist sharp
run030 2 --type nontrivial-factor --exp-dist sharp

run030 3 --type trivial-gcd --exp-dist uniform
run030 3 --type nontrivial-gcd --exp-dist uniform
run030 3 --type trivial-factor --exp-dist uniform
run030 3 --type nontrivial-factor --exp-dist uniform

run030 3 --type trivial-gcd --exp-dist sharp
run030 3 --type nontrivial-gcd --exp-dist sharp
run030 3 --type trivial-factor --exp-dist sharp
run030 3 --type nontrivial-factor --exp-dist sharp

run030 4 --type trivial-gcd --exp-dist uniform
run030 4 --type nontrivial-gcd --exp-dist uniform
run030 4 --type trivial-factor --exp-dist uniform
run030 4 --type nontrivial-factor --exp-dist uniform

run030 4 --type trivial-gcd --exp-dist sharp
run030 4 --type nontrivial-gcd --exp-dist sharp
run030 4 --type trivial-factor --exp-dist sharp
run030 4 --type nontrivial-factor --exp-dist sharp

run030 5 --type trivial-gcd --exp-dist uniform
run030 5 --type nontrivial-gcd --exp-dist uniform
run030 5 --type trivial-factor --exp-dist uniform
run030 5 --type nontrivial-factor --exp-dist uniform

run030 5 --type trivial-gcd --exp-dist sharp
run030 5 --type nontrivial-gcd --exp-dist sharp
run030 5 --type trivial-factor --exp-dist sharp
run030 5 --type nontrivial-factor --exp-dist sharp

run030 6 --type trivial-gcd --exp-dist uniform
run030 6 --type nontrivial-gcd --exp-dist uniform
run030 6 --type trivial-factor --exp-dist uniform
run030 6 --type nontrivial-factor --exp-dist uniform

run030 6 --type trivial-gcd --exp-dist sharp
run030 6 --type nontrivial-gcd --exp-dist sharp
run030 6 --type trivial-factor --exp-dist sharp
run030 6 --type nontrivial-factor --exp-dist sharp

run030 7 --type trivial-gcd --exp-dist uniform
run030 7 --type nontrivial-gcd --exp-dist uniform
run030 7 --type trivial-factor --exp-dist uniform
run030 7 --type nontrivial-factor --exp-dist uniform

run030 7 --type trivial-gcd --exp-dist sharp
run030 7 --type nontrivial-gcd --exp-dist sharp
run030 7 --type trivial-factor --exp-dist sharp
run030 7 --type nontrivial-factor --exp-dist sharp

run030 8 --type trivial-gcd --exp-dist uniform
run030 8 --type nontrivial-gcd --exp-dist uniform
run030 8 --type trivial-factor --exp-dist uniform
run030 8 --type nontrivial-factor --exp-dist uniform

run030 8 --type trivial-gcd --exp-dist sharp
run030 8 --type nontrivial-gcd --exp-dist sharp
run030 8 --type trivial-factor --exp-dist sharp
run030 8 --type nontrivial-factor --exp-dist sharp
