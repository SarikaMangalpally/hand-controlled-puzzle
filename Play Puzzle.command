#!/bin/zsh
set -eu
cd -- "$(dirname -- "$0")"
export PYTHONPATH="$PWD/src"
exec .venv/bin/python -m puzzle
