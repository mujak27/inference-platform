"""Exercise preflight control flow without a GPU or touching a cluster."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preflight.sh"


class PreflightTests(unittest.TestCase):
    def run_script(self, system="Linux", gpu_status=0, args=(), missing=None):
        with tempfile.TemporaryDirectory(prefix="inference-preflight-") as folder:
            commands = {
                "uname": f"echo {system}",
                "nvidia-smi": f"echo mock-gpu; exit {gpu_status}",
            }
            for name in ("date", "cat", "lscpu", "free", "df", "lsblk", "ip", "timedatectl"):
                commands[name] = "echo mock-inventory"
            for name, body in commands.items():
                if name == missing:
                    continue
                path = Path(folder) / name
                path.write_text(f"#!/bin/bash\n{body}\n")
                path.chmod(0o700)
            return subprocess.run(
                ["/bin/bash", str(SCRIPT), *args],
                env={**os.environ, "PATH": folder},
                capture_output=True,
                text=True,
                check=False,
            )

    def test_rejects_management_mac(self):
        result = self.run_script(system="Darwin")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Linux GPU host", result.stderr)
        self.assertNotIn("PASS", result.stdout)

    def test_inventory_success_does_not_claim_gpu_compute_validation(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("milestone 0 is NOT verified", result.stdout)
        self.assertIn("PENDING: CUDA computation", result.stdout)
        self.assertIn("PENDING: Kubernetes GPU allocation", result.stdout)

    def test_gpu_driver_failure_is_actionable(self):
        result = self.run_script(gpu_status=1)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL: GPU and loaded-driver visibility", result.stdout)
        self.assertNotIn("PASS", result.stdout)

    def test_missing_command_fails_but_continues_inventory(self):
        result = self.run_script(missing="lscpu")
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing command lscpu", result.stdout)
        self.assertIn("mock-gpu", result.stdout)

    def test_help(self):
        result = self.run_script(args=("--help",))
        self.assertEqual(result.returncode, 0)
        self.assertIn("Read-only", result.stdout)

    def test_unknown_argument(self):
        result = self.run_script(args=("--install",))
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
