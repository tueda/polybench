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
  run020 \
    --nproblems 200 \
    --max-nterms 50 \
    "$@"
}

run030 --type trivial-gcd
run030 --type nontrivial-gcd
run030 --type trivial-factor
run030 --type nontrivial-factor

run030 --type trivial-gcd --exp-dist uniform
run030 --type nontrivial-gcd --exp-dist uniform
run030 --type trivial-factor --exp-dist uniform
run030 --type nontrivial-factor --exp-dist uniform
