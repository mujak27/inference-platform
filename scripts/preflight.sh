#!/usr/bin/env bash
# Read-only host inventory; container compute and Kubernetes are separate gates.
set -uo pipefail

if [[ $# -gt 0 ]]; then
  if [[ $# -eq 1 && "$1" == --help ]]; then
    echo 'Usage: bash scripts/preflight.sh'
    echo 'Run on the Linux GPU host. Read-only; no sudo, installation, or cluster access.'
    exit 0
  fi
  echo 'Usage: bash scripts/preflight.sh' >&2
  exit 2
fi

if [[ $(uname -s) != Linux ]]; then
  echo 'FAIL: run this script on the Linux GPU host, not the management client.' >&2
  exit 1
fi

failed=0
check() {
  local label=$1
  shift
  printf '\n## %s\n' "$label"
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'FAIL: missing command %s; install its host package and rerun.\n' "$1"
    failed=1
  elif ! "$@"; then
    printf 'FAIL: %s; inspect the error above and rerun after resolving it.\n' "$label"
    failed=1
  fi
}

printf 'Host inventory (not CUDA/cluster validation)\n'
check 'UTC collection time' date -u '+%Y-%m-%dT%H:%M:%SZ'
check 'OS release' cat /etc/os-release
check 'Kernel and architecture' uname -srmo
check 'CPU' lscpu
check 'Host memory' free -h
check 'Filesystem capacity (root)' df -hT /
check 'Block devices (no serials)' lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
check 'Network addresses (review before sharing)' ip -br address
check 'Routes' ip route
check 'Clock synchronization' timedatectl show -p NTPSynchronized
check 'GPU and loaded-driver visibility' nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv
check 'GPU processes and display usage' nvidia-smi

printf '\nPENDING: CUDA computation inside a pinned container.\n'
printf 'PENDING: Kubernetes GPU allocation and device-plugin validation.\n'
printf 'PENDING: runtime/driver compatibility and available workload capacity review.\n'
if [[ $failed -ne 0 ]]; then
  echo 'FAIL: one or more host inventory checks failed; this is not a ready host.'
else
  echo 'PASS: host inventory commands only; milestone 0 is NOT verified.'
fi
exit "$failed"
