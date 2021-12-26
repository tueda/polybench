#!/bin/bash
#
# Make a release tag.
#
# Usage:
#   make-release.sh
#   make-release.sh NEW-VERSION
#   make-release.sh NEW-VERSION NEW-DEV-VERSION

set -eu
set -o pipefail

# Trap ERR to print the stack trace when a command fails.
# See: https://gist.github.com/ahendrix/7030300
function errexit() {
  local err=$?
  set +o xtrace
  local code="${1:-1}"
  echo "Error in ${BASH_SOURCE[1]}:${BASH_LINENO[0]}: '${BASH_COMMAND}' exited with status $err" >&2
  # Print out the stack trace described by $FUNCNAME
  if [ ${#FUNCNAME[@]} -gt 2 ]; then
    echo "Traceback:" >&2
    for ((i=1;i<${#FUNCNAME[@]}-1;i++)); do
      echo "  [$i]: at ${BASH_SOURCE[$i+1]}:${BASH_LINENO[$i]} in function ${FUNCNAME[$i]}" >&2
    done
  fi
  echo "Exiting with status ${code}" >&2
  exit "${code}"
}
trap 'errexit' ERR
set -o errtrace

# pre_version_message <current_version_number> <version_number> <dev_version_number>:
# a hook function to print some message before bumping the version number.
function pre_version_message() {
  echo 'Please make sure that CHANGELOG is up-to-date.'
  echo 'You can use the output of the following command:'
  echo
  echo "  git-chglog --next-tag $2"
  echo
}

# version_bump <version_number>: a hook function to bump the version for documents.
function version_bump() {
  dev_version_bump $1
}

# dev_version_bump <dev_version_number>: a hook function to bump the version for code.
function dev_version_bump() {
  :
}

# Check if the working repository is clean (untracked files are ignored).
{
  [[ $(git diff --stat) == '' ]] && [[ $(git diff --stat HEAD) == '' ]]
} || {
  echo 'error: working directory is dirty' >&2
  exit 1
}

# Ensure that we are in the project root.
cd $(git rev-parse --show-toplevel)

# Determine the current and next versions.
current_version=$(poetry version -s)
next_version=patch
next_dev_version=prepatch
if [[ $# -ge 2 ]]; then
  next_version=$1
  next_dev_version=$2
elif [[ $# -eq 1 ]]; then
  next_version=$1
fi
poetry version $next_version >/dev/null
next_version=$(poetry version -s)
poetry version $next_dev_version >/dev/null
next_dev_version=$(poetry version -s)
git restore pyproject.toml

# Print the versions and confirm if they are fine.
pre_version_message $current_version $next_version $next_dev_version
echo 'This script will bump the version number.'
echo "  current commit      : $(git rev-parse --short HEAD)"
echo "  current version     : $current_version"
echo "  next version        : $next_version"
echo "  next dev-version    : $next_dev_version"
while :; do
  read -p 'ok? (y/N): ' yn
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
poetry version $next_version
version_bump $next_version
git commit -a -m "chore(release): bump version to $next_version"
git tag $next_version
poetry version $next_dev_version
dev_version_bump $next_dev_version
git commit -a -m "chore: bump version to $next_dev_version"

# Completed. Show some information.
echo "A release tag $next_version was successfully created."
echo "The current development version is now $next_dev_version"
echo "To push it to the origin:"
echo "  git push origin $next_version"
