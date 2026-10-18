#!/usr/bin/env bash
# Offline rendering only: requires an already acquired, checksum-pinned chart.
set -euo pipefail
exec python3 -B "$(dirname "$0")/render-llmd.py" --candidate real "$@"
