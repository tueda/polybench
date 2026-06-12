#!/bin/bash
#
# Create a new release.
#
# Usage:
#   make-release.sh
#   make-release.sh NEW-VERSION
#   make-release.sh NEW-VERSION NEW-DEV-VERSION
#
# Project-independent script core version: 2026.05.23
#
set -euo pipefail

### Project-specific configuration ###

# Tag prefix.
v=''

# pre_version_message <current_version_number> <version_number> <dev_version_number>:
# a hook function that prints a message before updating the version.
pre_version_message() {
  echo 'Please make sure that CHANGELOG.md is up-to-date.'
  echo 'You can use the output of the following command:'
  echo
  echo "  git cliff --unreleased --tag $v$2"
  echo
}

# get_current_version: prints the current version.
get_current_version() {
  poetry version -s 2>/dev/null
}

# get_next_version <current_version_number>: prints the next version.
get_next_version() {
  if command -v git-cliff >/dev/null 2>&1; then
    git-cliff --bumped-version 2>/dev/null
  else
    local next_version
    poetry version patch >/dev/null 2>/dev/null
    next_version=$(poetry version -s 2>/dev/null)
    git restore pyproject.toml
    echo "$next_version"
  fi
}

# get_next_dev_version <current_version_number> <next_version_number>:
# prints the next development version.
get_next_dev_version() {
  local next_dev_version
  poetry version "$2" >/dev/null 2>&1
  poetry version prepatch >/dev/null 2>&1
  next_dev_version=$(poetry version -s 2>/dev/null)
  git restore pyproject.toml
  echo "$next_dev_version"
}

# version_bump <version_number>: sets the release version.
version_bump() {
  dev_version_bump "$1"
}

# dev_version_bump <dev_version_number>: sets the development version.
dev_version_bump() {
  poetry version "$1" >/dev/null 2>&1
}

# release_commit_message <version_number>: generates the release commit message.
release_commit_message() {
  echo "chore(release): $1"
}

# dev_commit_message <dev_version_number>: generates the development-version commit message.
dev_commit_message() {
  echo "chore(version): set version to $1"
}

### Project-independent logic ###

# spell-checker: ignore numstat, toplevel

# Trap ERR to print a stack trace when a command fails.
# See: https://gist.github.com/ahendrix/7030300
_errexit() {
  local err=$?
  set +o xtrace
  local code="${1:-1}"
  echo "Error in ${BASH_SOURCE[1]}:${BASH_LINENO[0]}: '${BASH_COMMAND}' exited with status $err" >&2
  # Print a stack trace from $FUNCNAME.
  if [ ${#FUNCNAME[@]} -gt 2 ]; then
    echo 'Traceback:' >&2
    for ((i = 1; i < ${#FUNCNAME[@]} - 1; i++)); do
      echo "  [$i]: at ${BASH_SOURCE[$i + 1]}:${BASH_LINENO[$i]} in function ${FUNCNAME[$i]}" >&2
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

# is_clean: checks if the working tree is clean (untracked files are ignored).
is_clean() {
  git diff --quiet && git diff --cached --quiet
}

# sed_i: portable implementation of sed -i for GNU and BSD.
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

# Ensure that the git command is available.
command -v git >/dev/null || abort 'git not available'

# Abort if the working tree is dirty.
is_clean || abort 'working tree is dirty'

# Ensure that we are in the project root.
cd "$(git rev-parse --show-toplevel)"

# Determine the current version.
current_version=$(get_current_version)
[[ -n $current_version ]] || abort 'could not determine current version'

# Determine the next version.
if [[ $# == 0 ]]; then
  next_version=$(get_next_version "$current_version")
  [[ -n $next_version ]] || abort 'could not determine next version'
else
  next_version=$1
fi

# Determine the next development version.
if [[ $# -lt 2 ]]; then
  next_dev_version=$(get_next_dev_version "$current_version" "$next_version")
  [[ -n $next_dev_version ]] || abort 'could not determine next development version'
else
  next_dev_version=$2
fi

# Print the versions.
pre_version_message "$current_version" "$next_version" "$next_dev_version"
echo 'This script will create a release and bump the development version.'
echo "  current commit           : $(git rev-parse --short HEAD)"
echo "  current version          : $current_version"
echo "  next version             : $next_version"
echo "  next development version : $next_dev_version"

# Abort if the next version tag already exists.
if git rev-parse -q --verify "refs/tags/$v$next_version" >/dev/null; then
  abort "tag already exists: $v$next_version"
fi

# User confirmation.
while :; do
  read -r -p 'Proceed? (y/N): ' yn
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

# Create the release and bump the development version.
version_bump "$next_version"
git commit -a -m "$(release_commit_message "$next_version")"
git tag "$v$next_version"
dev_version_bump "$next_dev_version"
git commit -a -m "$(dev_commit_message "$next_dev_version")"

# Print a completion summary.
echo "Release tag $v$next_version was successfully created."
echo "The current development version is now $next_dev_version."
echo
echo "To push the release tag to origin:"
echo "  git push origin $v$next_version"
