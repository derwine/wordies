#!/bin/sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

cd "$ROOT_DIR"

echo "Running Wordies regression checks..."
python3 -m py_compile main.py src/*.py tests/*.py
poetry run python -m unittest discover -s tests -v
