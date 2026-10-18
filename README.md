# Inference platform

A reproducible, GitOps-managed Kubernetes inference platform, built incrementally
with vLLM, llm-d, and LMCache. **Status as of 2026-10-18: one vLLM replica is
deployed and serving real inference through a private OpenAI-compatible API.**
Manual Git config change/revert, storage-preserving stop/start, and a quiescent
K3s SQLite + token backup are verified under issue #7. The llm-d router is a
registered manual, non-cascading Argo Application with a committed render that
passes local render, policy and schema checks, but it has **not** been synced or
exercised on the cluster. Smoke timings are not benchmarks; full restore, live
llm-d routing and LMCache remain pending.

## Current status

- **Working:** K3s, NVIDIA GPU allocation, Argo CD, and vLLM v0.31.0 serving
  `Qwen/Qwen3-1.7B` on one RTX 3090. The live deployment was Ready (1/1, zero
  restarts), and the vLLM Argo Application was Synced/Healthy on 2026-10-18.
- **Verified:** real streaming responses, a fresh chat-completion request returning
  HTTP 200, and pod replacement with retained model weights and no re-download.
  The 20 GiB model PVC is Bound using a Retain-policy volume. Cluster/storage
  reboot survival was verified before serving deployment.
- **Recovery-verified (issue #7):** a manual Git config change and clean revert
  (`MAX_NUM_SEQS` 4→3→4), storage-preserving stop/start (`replicas` 1→0→1 with
  cached-weight reuse from the retained PVC and no re-download), and a quiescent
  K3s SQLite + paired-token backup with encrypted off-host transfer and a
  disposable SQLite integrity check. See the
  [version/evidence record](docs/versions.md#observed-rollback-stopstart-and-sqlite-backup--issue-7-2026-10-18).
- **Private access only:** ClusterIP Service and loopback port-forwarding; no
  public inference endpoint. Argo sync is manual, not automatic.
- **Registered, not deployed:** the llm-d router child Application
  (`apps/llmd/application.yaml` → `apps/llmd/overlays/single-replica`) and the
  pinned GAIE v1.5.0 `InferencePool` CRD (`bootstrap/llmd/crds.yaml`) are
  committed. CRD admission, the `llmd` Argo sync and routed SSE against the real
  backend are **pending live execution**.
- **Still planned:** full K3s restore rehearsal and token bootstrap/decryption,
  two replicas/GPU sharing, llm-d routing, LMCache, serving-workload reboot
  survival, load tests, and benchmarks. Long-run stability has not been verified.
  This is a lab deployment, not a production-readiness claim.

The root Argo Application has a known cosmetic OutOfSync difference caused by an
empty `syncPolicy: {}`; the vLLM child is healthy. See the
[version/evidence record](docs/versions.md#observed-gitops-bootstrap-and-first-serving--issue-6)
and [milestones](docs/milestones.md) for deployment evidence and limitations.

## Use the deployed model

Follow the [private-access procedure](docs/recovery.md#approval-and-private-access)
to configure verified TLS/private cluster access. Select the target explicitly
when forwarding the Service from your management client:

```sh
kubectl --kubeconfig "$KUBECONFIG_PRIVATE" --context "$CONTEXT" \
  -n inference port-forward --address 127.0.0.1 svc/vllm 8000:8000
```

Keep that terminal running. Configure an OpenAI-compatible client with base URL
`http://127.0.0.1:8000/v1` and model `Qwen/Qwen3-1.7B`, or run the streaming
smoke test in another terminal:

```sh
python3 scripts/smoke-test.py
```

The direct `svc/vllm` port-forward above is unchanged. To exercise the llm-d
router instead (only after the `llmd` Application is deployed and its CRD is
admitted), forward the router Service and require the gateway's routed-response
header with a bounded timeout:

```sh
kubectl --kubeconfig "$KUBECONFIG_PRIVATE" --context "$CONTEXT" \
  -n inference port-forward --address 127.0.0.1 svc/llmd-epp 8081:80
python3 scripts/smoke-test.py --base-url http://127.0.0.1:8081 --require-routed --timeout 30
```

`--require-routed` fails unless the response carries
`x-went-into-resp-headers: true`; the printed JSON summary reports `routed` and
`server`. That header is EPP's response-path signal only — full real-backend
attribution also correlates the request in the live `vllm` pod
(`kubectl -n inference logs` / `/metrics`). This routed path has **not** been
executed against the cluster yet.

## Reproduce on another host

1. Read the [platform requirements](docs/architecture.md).
2. Follow the [Ubuntu Desktop installation guide](docs/host-installation.md), or
   supply an existing Linux host meeting the same requirements.
3. Complete [network access and host bootstrap](docs/bootstrap.md).
4. Run `bash scripts/preflight.sh` **on the Linux GPU host**.
5. Record actual versions and evidence, then follow the [GitOps guide](docs/gitops.md)
   to validate prerequisites and manually deploy the pinned stack.

After the runtime installation and pinned image pull have been separately approved,
run `sudo bash scripts/validate-cuda.sh` on the Linux GPU host. It uses K3s bundled
containerd, the fixed vLLM image digest, and NVIDIA runtime to check the literal
CUDA float32 matrix result `[[58,64],[139,154]]`. It downloads no models and pulls
no images. Success is one schema-1 JSON record with actual PyTorch/CUDA versions;
missing GPU, incorrect/malformed output, or runner failure is nonzero with stderr
diagnostics and no success stdout. Python 3 standard library is required on the
host. `--runner /path/to/executable` is the argv-safe test seam, not shell text;
fake-runner unit tests do not prove hardware execution. Concurrent runs use the
same disposable container name and are not supported.

Ubuntu Server is **not required**. Ubuntu Desktop is an installation option, not
a dependency of the platform. Disk layout, dual boot, usernames, IP addresses,
and the management computer are operator-specific and are not baked into workloads.

## Serving path

Current:

```text
Private client → loopback port-forward → vLLM (Qwen3-1.7B)
                                          └── one NVIDIA GPU + persistent model cache
```

Planned:

```text
Private client → llm-d gateway/scheduler → vLLM A or vLLM B
                                           └── one shared NVIDIA GPU
                                               optional LMCache CPU tier later
```

The initial validation target is a single RTX 3090 (24 GB VRAM) with 128 GB host
RAM. Two replicas on it demonstrate routing and lifecycle behavior, **not**
independent GPU scaling or GPU fault isolation. Other hosts need their own
capacity and compatibility validation.

See [milestones](docs/milestones.md) and the [version/evidence record](docs/versions.md).
No model weights, credentials, installation images, or raw host inventories belong in Git.

## GitOps deployment

[GitOps guide](docs/gitops.md): `bootstrap/`, `infra/`, and `apps/` follow the
[k8s-crossplane layout](https://github.com/mujak27/k8s-crossplane). A pinned Argo CD
bootstrap and single-replica vLLM configuration have been deployed and observed.
Both Applications still require manual sync without pruning; merging changes does
not authorize deployment. See the version/evidence record for host, GPU, storage and serving
results and their limits. Manual Git rollback, stop/start and a quiescent
SQLite/token backup were verified under issue #7; full restore remains pending.

[Operations and recovery](docs/recovery.md) covers private access, approval-gated
Git rollback and stop/start, SQLite/token backup, and untested restore preparation.

[llm-d qualification sources](docs/llmd-preparation.md) and the separate
[CPU-only simulator](docs/llmd-simulator.md) now cover the registered real router
Application; the simulator candidate remains unregistered. Source checks and the
committed render do not establish pinned EPP/Envoy acceptance, live CRD admission
or runtime compatibility.

## Local checks

```sh
python3 -m pip install -r requirements-dev.txt
bash -n scripts/preflight.sh scripts/validate-manifests.sh scripts/validate-cuda.sh
# First acquire the approved source artifacts separately; see llm-d qualification.
bash scripts/render-llmd.sh
bash scripts/render-llmd-sim.sh
python3 -m unittest discover -s tests -v
bash scripts/validate-manifests.sh
python3 scripts/validate-llmd.py --candidate real
python3 scripts/validate-llmd.py --candidate sim
git diff --check
```

Manifest checks need kubectl and kubeconform; versions and schema limitations
are documented in the GitOps guide. No configured cluster is contacted. The
GAIE `InferencePool` schema is extracted from the committed
`bootstrap/llmd/crds.yaml`, and `python3 scripts/validate-llmd.py --candidate real`
also fails if the committed `apps/llmd/base/rendered.yaml` drifts from a fresh
chart render.

Host installation is manual and intentionally does not automate partitioning,
flashing, reboots, or firewall changes. Container CUDA computation and Kubernetes
GPU allocation passed on the reference host; they remain separate acceptance
gates for each new host. Those results do not establish rollback or recovery acceptance.
