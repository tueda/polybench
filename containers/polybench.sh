#!/bin/sh
# Ignore a checkout or polybench.py in the current directory; retain that cwd
# for relative output paths. User options may override the prepared build tree.
exec /usr/bin/python3 -P -m polybench --build-directory /cache/build "$@"
