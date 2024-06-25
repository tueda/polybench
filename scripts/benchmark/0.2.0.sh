#!/bin/bash
set -eu
set -o pipefail

. "$(cd -- "$(dirname -- "$0")" && pwd)/_base.bash"

run020 --type trivial-gcd
run020 --type nontrivial-gcd
run020 --type trivial-factor
run020 --type nontrivial-factor
