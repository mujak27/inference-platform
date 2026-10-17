"""Public command contract tests; fake runners do not establish GPU execution."""

import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate-cuda.sh"
PASS = {
    "schema": 1,
    "status": "pass",
    "operation": "float32_matmul_2x3_3x2",
    "cuda": True,
    "result": [[58.0, 64.0], [139.0, 154.0]],
    "torch": "test-torch",
    "torch_cuda": "test-cuda",
}


class ValidateCudaTests(unittest.TestCase):
    def run_script(self, output, status=0, diagnostic=""):
        with tempfile.TemporaryDirectory(prefix="inference-cuda-") as folder:
            runner = Path(folder) / "runner with spaces"
            runner.write_text(
                "#!/bin/bash\n"
                "printf '%s' " + shlex.quote(output) + "\n"
                "printf '%s' " + shlex.quote(diagnostic) + " >&2\n"
                f"exit {status}\n"
            )
            runner.chmod(0o700)
            return subprocess.run(
                ["bash", str(SCRIPT), "--runner", str(runner)],
                capture_output=True, text=True, check=False,
            )

    def test_verified_runner_result_is_one_success_record(self):
        result = self.run_script(json.dumps(PASS))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("\n"), 1)
        self.assertEqual(json.loads(result.stdout), PASS)
        self.assertEqual(result.stderr, "")

    def test_missing_gpu_or_wrong_result_cannot_claim_success(self):
        for change in ({"cuda": False}, {"result": [[0, 0], [0, 0]]}):
            with self.subTest(change=change):
                result = self.run_script(json.dumps({**PASS, **change}))
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn("CUDA validation failed", result.stderr)

    def test_malformed_missing_or_wrong_schema_output_fails_closed(self):
        invalid = ["", "not-json", "null", "[]", "{}", json.dumps(PASS) * 2]
        for change in ({"schema": True}, {"schema": 2}, {"status": "fail"},
                       {"operation": "other"}, {"torch": ""}, {"torch_cuda": None}):
            invalid.append(json.dumps({**PASS, **change}))
        for output in invalid:
            with self.subTest(output=output):
                result = self.run_script(output)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn("CUDA validation failed", result.stderr)

    def test_nonzero_runner_suppresses_even_valid_success_output(self):
        result = self.run_script(json.dumps(PASS), status=7, diagnostic="CUDA unavailable\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("CUDA unavailable", result.stderr)

    def test_launch_failure_does_not_evaluate_shell_text(self):
        with tempfile.TemporaryDirectory(prefix="inference-cuda-") as folder:
            marker = Path(folder) / "must-not-exist"
            result = subprocess.run(
                ["bash", str(SCRIPT), "--runner", f"missing; touch {marker}"],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("CUDA validation failed", result.stderr)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
