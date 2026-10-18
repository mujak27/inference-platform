import http.client
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
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
        self.assertEqual({app["metadata"]["name"] for app in apps}, {"root", "vllm", "llmd"})
        for app in apps:
            self.assertNotIn("automated", app["spec"]["syncPolicy"])
            self.assertFalse(app["metadata"].get("finalizers"))
            self.assertEqual(app["spec"]["source"]["targetRevision"], "main")
            self.assertTrue((ROOT / app["spec"]["source"]["path"]).is_dir())

    def test_llmd_single_replica_overlay_and_project_whitelist(self):
        llmd_workload = render("apps/llmd/overlays/single-replica")
        deployment = next(item for item in llmd_workload if item["kind"] == "Deployment")
        self.assertEqual(deployment["metadata"]["name"], "llmd-epp")
        self.assertEqual(deployment["spec"]["replicas"], 1)
        service = next(item for item in llmd_workload if item["kind"] == "Service")
        self.assertEqual(service["metadata"]["name"], "llmd-epp")
        self.assertEqual(service["spec"]["type"], "ClusterIP")
        self.assertIn({"name": "http", "port": 80, "protocol": "TCP", "targetPort": 8081},
                      service["spec"]["ports"])
        pool = next(item for item in llmd_workload if item["kind"] == "InferencePool")
        self.assertEqual(pool["metadata"]["name"], "llmd")
        self.assertEqual(pool["spec"]["selector"]["matchLabels"], {"app.kubernetes.io/name": "vllm"})
        self.assertEqual(pool["spec"]["targetPorts"], [{"number": 8000}])
        self.assertEqual(pool["spec"]["endpointPickerRef"]["failureMode"], "FailClose")
        role = next(item for item in llmd_workload if item["kind"] == "Role")
        self.assertEqual(role["metadata"]["name"], "llmd-discovery")
        # Across both rendered overlays the pool selector must match exactly the
        # single real vllm Deployment (replicas 1) and no other Deployment.
        selector = pool["spec"]["selector"]["matchLabels"]
        deployments = [item for item in self.workload + llmd_workload if item["kind"] == "Deployment"]
        matched = [item for item in deployments
                   if selector.items() <= item["spec"]["template"]["metadata"]["labels"].items()]
        self.assertEqual([item["metadata"]["name"] for item in matched], ["vllm"])
        self.assertEqual(matched[0]["spec"]["replicas"], 1)
        self.assertEqual(len(deployments), 2)
        project = yaml.safe_load((ROOT / "infra/inference-project.yaml").read_text())
        self.assertEqual(project["spec"]["destinations"],
                         [{"server": "https://kubernetes.default.svc", "namespace": "inference"}])
        self.assertEqual(project["spec"]["clusterResourceWhitelist"], [{"group": "", "kind": "Namespace"}])
        whitelist = {(item["group"], item["kind"]) for item in project["spec"]["namespaceResourceWhitelist"]}
        self.assertTrue({("", "ServiceAccount"), ("rbac.authorization.k8s.io", "Role"),
                         ("rbac.authorization.k8s.io", "RoleBinding"),
                         ("inference.networking.k8s.io", "InferencePool")} <= whitelist)

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
        self.assert_supported_replicas(deployment)
        self.assertEqual(deployment["spec"]["strategy"]["rollingUpdate"], {"maxSurge": 0, "maxUnavailable": 1})
        pod = deployment["spec"]["template"]["spec"]
        self.assertEqual(pod["runtimeClassName"], "nvidia")
        container = pod["containers"][0]
        for resource in ("requests", "limits"):
            self.assertEqual(container["resources"][resource]["nvidia.com/gpu"], "1")
        shm = next(volume for volume in pod["volumes"] if volume["name"] == "shm")
        self.assertEqual(shm["emptyDir"], {"medium": "Memory", "sizeLimit": "2Gi"})
        for probe in ("startupProbe", "readinessProbe"):
            self.assertEqual(container[probe]["httpGet"]["path"], "/health")

    def assert_supported_replicas(self, deployment):
        self.assertIn(deployment["spec"]["replicas"], (0, 1))

    def test_rendered_stop_start_replica_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "workload.yaml").write_text(yaml.safe_dump_all(self.workload))
            path = Path(directory) / "kustomization.yaml"
            for count in (0, 1, 2):
                with self.subTest(replicas=count):
                    path.write_text(yaml.safe_dump({
                        "apiVersion": "kustomize.config.k8s.io/v1beta1",
                        "kind": "Kustomization",
                        "resources": ["workload.yaml"],
                        "replicas": [{"name": "vllm", "count": count}],
                    }))
                    deployment = next(item for item in render(directory) if item["kind"] == "Deployment")
                    self.assertEqual(deployment["spec"]["replicas"], count)
                    if count == 2:
                        with self.assertRaises(AssertionError):
                            self.assert_supported_replicas(deployment)
                    else:
                        self.assert_supported_replicas(deployment)

    def test_serving_candidate_and_parameters(self):
        container = self.resource("Deployment")["spec"]["template"]["spec"]["containers"][0]
        self.assertEqual(container["image"], "vllm/vllm-openai:v0.31.0@sha256:c1c9f6fd5c109ba7f0546a59f5b2f15fb87f64c77782e90a27b648b42a8e67c3")
        self.assertEqual(container["command"], ["vllm", "serve"])
        self.assertEqual(self.resource("ConfigMap")["data"], {
            "MODEL_ID": "Qwen/Qwen3-1.7B",
            "MODEL_REVISION": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
            "SERVED_MODEL_NAME": "Qwen/Qwen3-1.7B",
            "DTYPE": "float16",
            "TENSOR_PARALLEL_SIZE": "1",
            "MAX_MODEL_LEN": "4096",
            "MAX_NUM_SEQS": "4",
            "GPU_MEMORY_UTILIZATION": "0.80",
        })
        for argument in (
            "$(MODEL_ID)", "--revision=$(MODEL_REVISION)",
            "--tokenizer-revision=$(MODEL_REVISION)",
            "--served-model-name=$(SERVED_MODEL_NAME)", "--dtype=$(DTYPE)",
            "--tensor-parallel-size=$(TENSOR_PARALLEL_SIZE)",
            "--max-model-len=$(MAX_MODEL_LEN)", "--max-num-seqs=$(MAX_NUM_SEQS)",
            "--gpu-memory-utilization=$(GPU_MEMORY_UTILIZATION)",
            "--enable-prefix-caching",
        ):
            self.assertIn(argument, container["args"])

    def test_lab_security_and_persistent_cache(self):
        pod = self.resource("Deployment")["spec"]["template"]["spec"]
        self.assertFalse(pod["automountServiceAccountToken"])
        self.assertEqual(pod["securityContext"]["seccompProfile"], {"type": "RuntimeDefault"})
        container = pod["containers"][0]
        self.assertFalse(container["securityContext"]["allowPrivilegeEscalation"])
        self.assertEqual(container["securityContext"]["capabilities"]["drop"], ["ALL"])
        self.assertIn({"name": "HF_HOME", "value": "/models/huggingface"}, container["env"])
        self.assertIn({"name": "models", "mountPath": "/models"}, container["volumeMounts"])
        cache = next(volume for volume in pod["volumes"] if volume["name"] == "models")
        self.assertEqual(cache["persistentVolumeClaim"]["claimName"], self.resource("PersistentVolumeClaim")["metadata"]["name"])
        self.assertEqual(self.resource("PersistentVolumeClaim")["spec"]["storageClassName"], "local-path-retain")
        self.assertEqual(self.resource("PersistentVolumeClaim")["spec"]["resources"]["requests"]["storage"], "20Gi")

    def test_service_and_storage_are_private_and_retained(self):
        self.assertEqual(self.resource("Service")["spec"]["type"], "ClusterIP")
        labels = self.resource("Deployment")["spec"]["template"]["metadata"]["labels"]
        self.assertEqual(self.resource("Service")["spec"]["selector"], labels)
        for kind in ("Namespace", "PersistentVolumeClaim"):
            options = self.resource(kind)["metadata"]["annotations"]["argocd.argoproj.io/sync-options"]
            self.assertIn("Prune=false", options)
            self.assertIn("Delete=false", options)
        self.assertNotIn("Secret", [item["kind"] for item in self.workload])

    def test_service_discovery_does_not_poison_vllm_port(self):
        # The workload's own ClusterIP Service is named vllm, so the kubelet
        # injects VLLM_PORT=<proto>://<addr>:<port> into every pod in the
        # namespace. vLLM parses VLLM_PORT and rejects the URI form, crashing
        # the container after model load. Pod-specified environment variables
        # take precedence over service-derived ones.
        pod = self.resource("Deployment")["spec"]["template"]["spec"]
        explicit = {env["name"]: env.get("value") for env in pod["containers"][0].get("env", [])}
        injected = {}
        if pod.get("enableServiceLinks", True):
            for service in (item for item in self.workload if item["kind"] == "Service"):
                prefix = service["metadata"]["name"].upper().replace("-", "_")
                port = service["spec"]["ports"][0]
                injected[f"{prefix}_PORT"] = f"{port.get('protocol', 'TCP').lower()}://<addr>:{port['port']}"
        self.assertEqual({**injected, **explicit}.get("VLLM_PORT", "8000"), "8000")

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
    def response_headers(self, content_type="text/event-stream", **headers):
        message = http.client.HTTPMessage()
        message["Content-Type"] = content_type
        for name, value in headers.items():
            message[name.replace("_", "-")] = value
        return message

    def test_response_headers_require_sse_and_optionally_routed_proxy(self):
        check = load_script("smoke-test").check_response_headers
        with self.assertRaisesRegex(ValueError, "SSE"):
            check(self.response_headers(content_type="application/json"))
        self.assertEqual(check(self.response_headers(server="uvicorn")),
                         {"routed": False, "server": "uvicorn"})
        for headers in ({"server": "uvicorn"},
                        {"server": "envoy", "x_went_into_resp_headers": "false"}):
            with self.subTest(headers=headers):
                with self.assertRaisesRegex(ValueError, "routed"):
                    check(self.response_headers(**headers), require_routed=True)
        self.assertEqual(check(self.response_headers(server="uvicorn", x_went_into_resp_headers="true"),
                               require_routed=True),
                         {"routed": True, "server": "uvicorn"})

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
