#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <module> [args...]"
  echo "Example: $0 tests.basic_app_test"
  exit 1
fi

python -m "$@"