#!/bin/bash
#
# Make a release.
#
# Usage:
#   make-release.sh
#   make-release.sh NEW-VERSION
#   make-release.sh NEW-VERSION NEW-DEV-VERSION
#
# Script Core Version: 2025.12.03
#
set -euo pipefail

### Project-specific configuration ###

# Tag prefix.
v=''

# pre_version_message <current_version_number> <version_number> <dev_version_number>:
# a hook function to print some message before bumping the version number.
pre_version_message() {
  echo 'Please make sure that CHANGELOG.md is up-to-date.'
  echo 'You can use the output of the following command:'
  echo
  echo "  git-chglog --next-tag $v$2"
  echo
}

# get_current_version: prints the current version.
get_current_version() {
  poetry version -s
}

# get_next_version <current_version_number>: prints the next version.
get_next_version() {
  local next_version
  poetry version patch >/dev/null
  next_version=$(poetry version -s)
  git restore pyproject.toml
  echo "$next_version"
}

# get_next_dev_version <current_version_number> <next_version_number>: prints the next dev-version.
get_next_dev_version() {
  local next_dev_version
  poetry version "$2" >/dev/null
  poetry version prepatch >/dev/null
  next_dev_version=$(poetry version -s)
  git restore pyproject.toml
  echo "$next_dev_version"
}

# version_bump <version_number>: a hook function to bump the version for documents.
version_bump() {
  dev_version_bump $1
}

# dev_version_bump <dev_version_number>: a hook function to bump the version for code.
dev_version_bump() {
  poetry version "$1"
}

# release_commit_message <version_number>: generates the commit message for a release version.
release_commit_message() {
  echo "chore(release): bump version to $1"
}

# dev_commit_message <version_number>: generates the commit message for a development version.
dev_commit_message() {
  echo "chore: bump version to $1"
}

### Project-independent logic ###

# Trap ERR to print the stack trace when a command fails.
# See: https://gist.github.com/ahendrix/7030300
_errexit() {
  local err=$?
  set +o xtrace
  local code="${1:-1}"
  echo "Error in ${BASH_SOURCE[1]}:${BASH_LINENO[0]}: '${BASH_COMMAND}' exited with status $err" >&2
  # Print out the stack trace described by $FUNCNAME
  if [ ${#FUNCNAME[@]} -gt 2 ]; then
    echo 'Traceback:' >&2
    for ((i=1;i<${#FUNCNAME[@]}-1;i++)); do
      echo "  [$i]: at ${BASH_SOURCE[$i+1]}:${BASH_LINENO[$i]} in function ${FUNCNAME[$i]}" >&2
    done
  fi
  echo "Exiting with status ${code}" >&2
  exit "${code}"
}
trap '_errexit' ERR
set -o errtrace

# abort <message>: aborts the program with the given message.
abort() {
  echo "error: $*" 1>&2
  exit 1
}

# is_clean: checks if the working repository is clean (untracked files are ignored).
is_clean() {
  git diff --quiet && git diff --cached --quiet
}

# sed_i: portable sed -i for GNU/BSD.
# Usage: sed_i <options...> <script> <file>
# Note: works only with a single file.
sed_i() {
  local file="${!#}"
  local temp="$file.$$.$RANDOM"
  if sed "$@" >"$temp"; then
    mv "$temp" "$file"
  else
    rm -f "$temp"
    return 1
  fi
}

# check_file_changed <file> <expected_added_lines_count> <expected_deleted_lines_count>
check_file_changed() {
  local stat added_lines_count deleted_lines_count
  stat=$(git diff --numstat "$1")
  if [[ $stat =~ ([0-9]+)[[:blank:]]+([0-9]+) ]]; then
    added_lines_count="${BASH_REMATCH[1]}"
    deleted_lines_count="${BASH_REMATCH[2]}"
  else
    added_lines_count=0
    deleted_lines_count=0
  fi
  if [[ $added_lines_count != "$2" || $deleted_lines_count != "$3" ]]; then
    abort "$1 changed unexpectedly: $added_lines_count added, $deleted_lines_count deleted (expected: $2 added, $3 deleted)"
  fi
}

# Require the git command.
command -v git >/dev/null || abort 'git not available'

# Stop if the working directory is dirty.
is_clean || abort 'working directory is dirty'

# Ensure that we are in the project root.
cd "$(git rev-parse --show-toplevel)"

# Determine the current version.
current_version=$(get_current_version)
[[ -n $current_version ]] || abort 'current version not determined'

# Determine the next version.
if [[ $# == 0 ]]; then
  next_version=$(get_next_version "$current_version")
  [[ -n $next_version ]] || abort 'next version not determined'
else
  next_version=$1
fi

# Determine the next dev-version.
if [[ $# -lt 2 ]]; then
  next_dev_version=$(get_next_dev_version "$current_version" "$next_version")
  [[ -n $next_dev_version ]] || abort 'next dev-version not determined'
else
  next_dev_version=$2
fi

# Print the versions.
pre_version_message "$current_version" "$next_version" "$next_dev_version"
echo 'This script will bump the version number.'
echo "  current commit      : $(git rev-parse --short HEAD)"
echo "  current version     : $current_version"
echo "  next version        : $next_version"
echo "  next dev-version    : $next_dev_version"

# Abort if the next version tag already exists.
if git rev-parse -q --verify "refs/tags/$v$next_version" >/dev/null; then
  abort "tag already exists: $v$next_version"
fi

# User confirmation.
while :; do
  read -r -p 'ok? (y/N): ' yn
  case "$yn" in
    [yY]*)
      break
      ;;
    [nN]*)
      echo 'Aborted' >&2
      exit 1
      ;;
    *)
      ;;
  esac
done

# Bump the version.
version_bump "$next_version"
git commit -a -m "$(release_commit_message "$next_version")"
git tag "$v$next_version"
dev_version_bump "$next_dev_version"
git commit -a -m "$(dev_commit_message "$next_dev_version")"

# Completed. Print summary.
echo "A release tag $v$next_version was successfully created."
echo "The current development version is now $next_dev_version"
echo
echo "To push it to the origin:"
echo "  git push origin $v$next_version"
