#!/usr/bin/env bash
# Offline rendering only: kubectl kustomize never contacts the Kubernetes API.
set -euo pipefail
exec python3 -B "$(dirname "$0")/render-llmd.py" --candidate sim "$@"
