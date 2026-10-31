#!/bin/sh
set -eu
fail() {
  echo "polybench container: $*" >&2
  exit 1
}
cd /work
jobs=${BUILD_JOBS:-$(nproc)}
case "$jobs" in '' | *[!0-9]* | 0) fail 'BUILD_JOBS must be a positive integer' ;; esac
export CARGO_BUILD_JOBS="$jobs" CMAKE_BUILD_PARALLEL_LEVEL="$jobs" VCPKG_MAX_CONCURRENCY="$jobs"
export GRADLE_OPTS="${GRADLE_OPTS:-} -Dorg.gradle.workers.max=$jobs"

mkdir -p "$HOME"
# CMake configure_file chmods this header even when its contents are unchanged.
# An arbitrary Docker UID may write the directory but cannot chmod root's file.
# Replace just that file, retaining its time so dependent objects stay current.
header=/cache/build/flint/build/version.h
if test -f "$header" && test "$(stat -c %u "$header")" != "$(id -u)"; then
  temporary=$(mktemp "${header}.XXXXXX")
  cp --preserve=mode,timestamps --no-preserve=ownership "$header" "$temporary"
  mv "$temporary" "$header"
fi

case "${1:-}" in
'' | -*) set -- polybench "$@" ;;
esac
exec "$@"
