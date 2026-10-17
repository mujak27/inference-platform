import importlib.util
import json
from pathlib import Path
import re
import subprocess
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render(path):
    output = subprocess.check_output(["kubectl", "kustomize", path], cwd=ROOT, text=True)
    return [item for item in yaml.safe_load_all(output) if item]


class GitOpsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workload = render("apps/vllm/overlays/single-replica")
        cls.control = render("infra")

    def resource(self, kind):
        return next(item for item in self.workload if item["kind"] == kind)

    def test_every_application_is_manual_and_non_cascading(self):
        root = yaml.safe_load((ROOT / "bootstrap/root-app.yaml").read_text())
        apps = [root] + [item for item in self.control if item["kind"] == "Application"]
        self.assertEqual(len(apps), 2)
        for app in apps:
            self.assertNotIn("automated", app["spec"]["syncPolicy"])
            self.assertFalse(app["metadata"].get("finalizers"))
            self.assertEqual(app["spec"]["source"]["targetRevision"], "main")
            self.assertTrue((ROOT / app["spec"]["source"]["path"]).is_dir())

    def test_pins_and_configuration_references(self):
        deployment = self.resource("Deployment")
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        self.assertRegex(container["image"], r"@sha256:[0-9a-f]{64}$")
        config = self.resource("ConfigMap")
        self.assertEqual(container["envFrom"][0]["configMapRef"]["name"], config["metadata"]["name"])
        for name in re.findall(r"\$\((\w+)\)", " ".join(container["args"])):
            self.assertIn(name, config["data"])
        self.assertRegex(config["data"]["MODEL_REVISION"], r"^[0-9a-f]{40}$")
        self.assertIn("--tokenizer-revision=$(MODEL_REVISION)", container["args"])

    def test_single_gpu_no_surge_and_bounded_shared_memory(self):
        deployment = self.resource("Deployment")
        self.assertEqual(deployment["spec"]["replicas"], 1)
        self.assertEqual(deployment["spec"]["strategy"]["rollingUpdate"], {"maxSurge": 0, "maxUnavailable": 1})
        pod = deployment["spec"]["template"]["spec"]
        container = pod["containers"][0]
        for resource in ("requests", "limits"):
            self.assertEqual(container["resources"][resource]["nvidia.com/gpu"], "1")
        shm = next(volume for volume in pod["volumes"] if volume["name"] == "shm")
        self.assertEqual(shm["emptyDir"], {"medium": "Memory", "sizeLimit": "2Gi"})
        for probe in ("startupProbe", "readinessProbe"):
            self.assertEqual(container[probe]["httpGet"]["path"], "/health")

    def test_service_and_storage_are_private_and_retained(self):
        self.assertEqual(self.resource("Service")["spec"]["type"], "ClusterIP")
        labels = self.resource("Deployment")["spec"]["template"]["metadata"]["labels"]
        self.assertEqual(self.resource("Service")["spec"]["selector"], labels)
        for kind in ("Namespace", "PersistentVolumeClaim"):
            options = self.resource(kind)["metadata"]["annotations"]["argocd.argoproj.io/sync-options"]
            self.assertIn("Prune=false", options)
            self.assertIn("Delete=false", options)
        self.assertNotIn("Secret", [item["kind"] for item in self.workload])

    def test_schema_extraction_requires_expected_crds(self):
        with self.assertRaisesRegex(ValueError, "lacks"):
            load_script("argocd-schemas").extract([])

    def test_schema_extraction_uses_served_version(self):
        documents = [{"kind": "CustomResourceDefinition", "spec": {
            "group": "argoproj.io", "names": {"kind": kind}, "versions": [{
                "name": "v1alpha1", "served": True,
                "schema": {"openAPIV3Schema": {"type": "object"}},
            }],
        }} for kind in ("Application", "AppProject")]
        schemas = load_script("argocd-schemas").extract(documents)
        self.assertEqual(schemas["application"], {"type": "object"})


class StreamTests(unittest.TestCase):
    def test_incremental_content_and_done(self):
        event = lambda text: b"data: " + json.dumps({"choices": [{"delta": {"content": text}}]}).encode() + b"\n"
        stream = load_script("smoke-test").content_chunks([event("Hello"), event(" GPU"), b"data: [DONE]\n"])
        self.assertEqual(next(stream), "Hello")
        self.assertEqual(next(stream), " GPU")
        self.assertEqual(list(stream), [])

    def test_truncated_stream_fails(self):
        with self.assertRaisesRegex(ValueError, "without"):
            list(load_script("smoke-test").content_chunks([]))

    def test_server_error_fails(self):
        with self.assertRaisesRegex(ValueError, "error"):
            list(load_script("smoke-test").content_chunks([b'data: {"error": "unhealthy"}\n']))
