#!/bin/sh
set -eu
compiler=/opt/polymojo/.pixi/envs/default/bin/mojo
# Mojo 1.2.0 itself requires x86-64-v3. The driver target is a separate choice:
# fix it here so building on a newer CPU does not introduce host-only instructions.
# The adapter has no target-CPU option, so MOJO_COMMAND uses this wrapper.
case "${1:-}" in
build)
  shift
  exec "$compiler" build --target-triple x86_64-unknown-linux-gnu --target-cpu x86-64-v3 "$@"
  ;;
*) exec "$compiler" "$@" ;;
esac
