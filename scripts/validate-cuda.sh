#!/usr/bin/env bash
# Run on the approved Linux GPU host; the image must already be pulled.
set -euo pipefail
exec python3 - "$@" <<'PY'
import argparse
import json
import subprocess
import sys

parser = argparse.ArgumentParser(description="Assert a real CUDA matrix product; no model downloads.")
parser.add_argument("--runner", default="/usr/local/bin/k3s", help="executable path (test seam, not shell text)")
args = parser.parse_args()
image = "docker.io/vllm/vllm-openai@sha256:c1c9f6fd5c109ba7f0546a59f5b2f15fb87f64c77782e90a27b648b42a8e67c3"
payload = r'''
import json
import sys
try:
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    torch.backends.cuda.matmul.allow_tf32 = False
    a = torch.tensor([[1, 2, 3], [4, 5, 6]], dtype=torch.float32, device="cuda:0")
    b = torch.tensor([[7, 8], [9, 10], [11, 12]], dtype=torch.float32, device="cuda:0")
    c = a @ b
    if not (a.is_cuda and b.is_cuda and c.is_cuda):
        raise RuntimeError("operation did not execute on CUDA tensors")
    torch.cuda.synchronize()
    got = c.cpu().tolist()
    if got != [[58.0, 64.0], [139.0, 154.0]]:
        raise RuntimeError("CUDA result mismatch")
    print(json.dumps({"schema": 1, "status": "pass", "operation": "float32_matmul_2x3_3x2", "cuda": True, "result": got, "torch": torch.__version__, "torch_cuda": torch.version.cuda}, separators=(",", ":")))
except Exception as exc:
    print("CUDA validation failed: " + str(exc), file=sys.stderr)
    sys.exit(1)
'''
command = [
    args.runner, "ctr", "--namespace", "k8s.io", "run", "--rm",
    "--platform", "linux/amd64", "--runtime", "io.containerd.runc.v2",
    "--runc-binary", "/usr/bin/nvidia-container-runtime",
    "--runc-systemd-cgroup", "--cgroup", "system.slice:inference-issue4:cuda",
    "--cpus", "2", "--memory-limit", "4294967296",
    "--env", "NVIDIA_VISIBLE_DEVICES=0",
    "--env", "NVIDIA_DRIVER_CAPABILITIES=compute,utility",
    image, "inference-issue4-cuda", "python3", "-c", payload,
]
try:
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    record = json.loads(completed.stdout)
    if (not isinstance(record, dict)
            or type(record.get("schema")) is not int or record["schema"] != 1
            or record.get("status") != "pass"
            or record.get("operation") != "float32_matmul_2x3_3x2"
            or any(not isinstance(record.get(key), str) or not record[key].strip()
                   for key in ("torch", "torch_cuda"))):
        raise ValueError("expected one schema-1 CUDA pass record with versions")
    if record.get("cuda") is not True or record.get("result") != [[58.0, 64.0], [139.0, 154.0]]:
        raise ValueError("missing CUDA execution or unexpected numerical result")
    print(json.dumps(record, separators=(",", ":")))
except (OSError, ValueError, subprocess.CalledProcessError) as exc:
    if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
        print(exc.stderr, file=sys.stderr, end="")
    print("CUDA validation failed: " + str(exc), file=sys.stderr)
    sys.exit(1)
PY
