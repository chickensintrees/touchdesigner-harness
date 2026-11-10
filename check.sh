#!/usr/bin/env bash
# Harness checks that run anywhere (no TouchDesigner needed).
# Live checks inside TD are tdh.check(...); see the td-verify skill.
set -euo pipefail
cd "$(dirname "$0")"

# On Windows, `python3` is often the Microsoft Store stub (exits 49), so find
# an interpreter that actually runs.
PY=""
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
    PY="$candidate"; break
  fi
done
if [ -z "$PY" ]; then
  echo "no working Python found (tried python3, python, py)" >&2
  exit 1
fi

if command -v ruff >/dev/null 2>&1; then
  ruff check td tests
else
  echo "ruff not installed; skipping lint" >&2
fi
"$PY" -m pytest -q
